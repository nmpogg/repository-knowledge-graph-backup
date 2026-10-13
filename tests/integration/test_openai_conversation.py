"""Configured provider through real API/storage with synthetic remote HTTP responses."""

import json

import pytest
from fastapi.testclient import TestClient

from rkg.api import create_app
from rkg.conversations import create_conversation
from rkg.ingestion import LocalSourcePolicy
from rkg.llm import OpenAIProvider, OpenRouterProvider
from rkg.storage import Storage
from tests.integration.graph_helpers import seed_cycle_graph


@pytest.mark.parametrize(
    "name,provider_type",
    [("openai", OpenAIProvider), ("openrouter", OpenRouterProvider)],
)
@pytest.mark.parametrize("enabled", [False, True])
def test_configured_provider_capabilities_and_greeting(
    tmp_path, monkeypatch, name, provider_type, enabled
):
    monkeypatch.setenv("RKG_LLM_PROVIDER", name)
    monkeypatch.setenv(
        "OPENAI_API_KEY", "synthetic" if name != "openai" or enabled else ""
    )
    monkeypatch.setenv(
        "OPENROUTER_API_KEY", "synthetic" if name != "openrouter" or enabled else ""
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("Capabilities/greeting must not call provider HTTP")

    monkeypatch.setattr(
        "urllib.request.OpenerDirector.open",
        lambda _opener, *args, **kwargs: forbidden(*args, **kwargs),
    )
    with Storage(tmp_path / "synthetic.kuzu") as store:
        repo, sid, _ = seed_cycle_graph(store)
        conv = create_conversation(store, repository_id=repo, snapshot_id=sid)
        app = create_app(
            store, LocalSourcePolicy((tmp_path,)), session_token="synthetic"
        )
        assert isinstance(app.state.provider, provider_type)
        with TestClient(app, base_url="http://127.0.0.1") as client:
            cap = client.get("/api/v1/conversations/capabilities")
            assert cap.status_code == 200 and cap.json()["provider_enabled"] == enabled
            result = client.post(
                f"/api/v1/conversations/{conv.id}/turns",
                headers={"X-RKG-Session": "synthetic"},
                json={
                    "question": "hello",
                    "client_request_id": "greeting",
                    "expected_revision": 1,
                },
            )
            assert result.status_code == (200 if enabled else 503)
            if not enabled:
                assert result.json()["error"]["code"] == "llm_disabled"


def test_openai_grounded_answer_replay_and_refusal_preserve_state(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("RKG_LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-openai")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
    calls = []
    refuse = [False]

    class Response:
        def __init__(self, data):
            self.data = data

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def read(self, size):
            return json.dumps(self.data).encode()

    def remote(req, timeout):
        assert req.full_url == "https://api.openai.com/v1/chat/completions"
        assert req.get_header("Authorization") == "Bearer synthetic-openai"
        payload = json.loads(req.data)
        assert "provider" not in payload and "usage" not in payload
        assert payload["store"] is False and timeout is None
        calls.append(payload["response_format"]["json_schema"]["name"])
        context = json.loads(payload["messages"][-1]["content"])
        root = context["root_id"]
        edge = next(
            f
            for f in context["facts"]
            if f["source_id"] == root and f["type"] == "calls"
        )
        value = {
            "status": "answered",
            "root_id": root,
            "sections": [
                {
                    "relation": "calls",
                    "direction": "outgoing",
                    "paths": [{"anchor_id": root, "edge_ids": [edge["id"]]}],
                }
            ],
        }
        message = {"content": json.dumps(value)}
        if refuse[0]:
            message["refusal"] = "synthetic-refusal"
        return Response({"choices": [{"finish_reason": "stop", "message": message}]})

    monkeypatch.setattr(
        "urllib.request.OpenerDirector.open",
        lambda _opener, *args, **kwargs: remote(*args, **kwargs),
    )
    with Storage(tmp_path / "synthetic.kuzu") as store:
        repo, sid, batch = seed_cycle_graph(store)
        conv = create_conversation(store, repository_id=repo, snapshot_id=sid)
        root = next(e for e in batch.entities if e.qualified_name == "app.cycle.a")
        app = create_app(
            store, LocalSourcePolicy((tmp_path,)), session_token="synthetic"
        )
        with TestClient(app, base_url="http://127.0.0.1") as client:
            route = f"/api/v1/conversations/{conv.id}"
            body = {
                "question": "What does app.cycle.a call?",
                "root_id": root.id,
                "client_request_id": "answer",
                "expected_revision": 1,
            }
            response = client.post(
                route + "/turns", headers={"X-RKG-Session": "synthetic"}, json=body
            )
            assert response.status_code == 200, response.json()
            answer = response.json()
            assert (
                answer["status"] == "answered"
                and answer["claims"]
                and answer["citations"]
            )
            assert calls == ["rkg_narrative_v1"]
            replay = client.post(
                route + "/turns", headers={"X-RKG-Session": "synthetic"}, json=body
            )
            assert replay.json() == answer and len(calls) == 1
            for index, citation in enumerate(answer["citations"]):
                source = client.get(
                    route + f"/turns/{answer['turn_id']}/citations/{index}"
                )
                assert source.status_code == 200
                assert source.json()["evidence"]["id"] == citation["evidence_id"]
            state = store.get_conversation(conv.id).state
            refuse[0] = True
            body.update(
                client_request_id="refused",
                expected_revision=store.get_conversation(conv.id).revision,
            )
            failed = client.post(
                route + "/turns", headers={"X-RKG-Session": "synthetic"}, json=body
            )
            assert failed.status_code == 502
            assert failed.json()["error"]["code"] == "llm_malformed_response"
            assert store.get_conversation(conv.id).state == state
