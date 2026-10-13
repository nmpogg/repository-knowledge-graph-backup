"""Restart/replay through the real HTTP boundary and bounded narrative profile."""

import pytest
from fastapi.testclient import TestClient

from rkg.api import create_app
from rkg.conversations import create_conversation
from rkg.ingestion import LocalSourcePolicy
from rkg.storage import Storage
from tests.browser.chatbot_fixture import NarrativeFixtureProvider
from tests.integration.graph_helpers import seed_cycle_graph


@pytest.mark.parametrize(
    "padding", ["", " synthetic" * 7000], ids=["short-question", "large-question"]
)
@pytest.mark.parametrize("selection", ["normal", "padded-ascii", "padded-arabic"])
def test_restart_preserves_clarification_intent_and_exact_sources(
    tmp_path, padding, selection
):
    db = tmp_path / "restart.kuzu"
    provider = NarrativeFixtureProvider()
    with Storage(db) as store:
        repo, sid, batch = seed_cycle_graph(store)
        conv = create_conversation(store, repository_id=repo, snapshot_id=sid)
        app = create_app(
            store,
            LocalSourcePolicy((tmp_path,)),
            session_token="synthetic",
            provider=provider,
        )
        with TestClient(app, base_url="http://127.0.0.1") as client:
            route = f"/api/v1/conversations/{conv.id}"
            question = "What does `a` call?" + padding
            clarify = client.post(
                route + "/turns",
                headers={"X-RKG-Session": "synthetic"},
                json={
                    "question": question,
                    "ui_locale": "vi",
                    "client_request_id": "initial",
                    "expected_revision": 1,
                },
            )
            assert clarify.status_code == 200
            assert clarify.json()["status"] == "needs_clarification"
            state = store.get_conversation(conv.id).state
            assert state["pending_intent"]["question"] == question
            assert state["pending_intent"]["language"] == "en"
            assert provider.calls == 0
    # A fresh connection and API instance must resume the durable original intent.
    with Storage(db) as store:
        app = create_app(
            store,
            LocalSourcePolicy((tmp_path,)),
            session_token="synthetic",
            provider=provider,
        )
        with TestClient(app, base_url="http://127.0.0.1") as client:
            current = store.get_conversation(conv.id)
            greeting = client.post(
                route + "/turns",
                headers={"X-RKG-Session": "synthetic"},
                json={
                    "question": "alo",
                    "client_request_id": "greeting",
                    "expected_revision": current.revision,
                },
            )
            assert greeting.status_code == 200
            assert store.get_conversation(conv.id).state == state
            assert provider.calls == 0
            history = client.get(route + "/turns").json()
            a = next(e for e in batch.entities if e.qualified_name == "app.cycle.a")
            ordered = [e["id"] for e in history["candidate_entities"]]
            assert a.id in ordered
            if selection != "normal":
                invalid = client.post(
                    route + "/turns",
                    headers={"X-RKG-Session": "synthetic"},
                    json={
                        "question": "9" * 5000,
                        "client_request_id": "oversized-ordinal",
                        "expected_revision": history["conversation"]["revision"],
                    },
                )
                assert invalid.status_code == 200
                assert invalid.json()["status"] == "needs_clarification"
                assert store.get_conversation(conv.id).state == state
                assert provider.calls == 0
                history = client.get(route + "/turns").json()
                assert [e["id"] for e in history["candidate_entities"]] == ordered
            ordinal = str(ordered.index(a.id) + 1)
            if selection == "padded-ascii":
                ordinal = "0" * 5000 + ordinal
            elif selection == "padded-arabic":
                ordinal = "٠" * 5000 + "".join(chr(ord("٠") + int(d)) for d in ordinal)
            body = {
                "question": ordinal,
                "root_id": a.id,
                "ui_locale": "vi",
                "client_request_id": "selection",
                "expected_revision": history["conversation"]["revision"],
            }
            response = client.post(
                route + "/turns", headers={"X-RKG-Session": "synthetic"}, json=body
            )
            assert response.status_code == 200
            answer = response.json()
            assert answer["status"] == "answered"
            assert answer["resolved_question"] == question
            assert answer["response_metadata"]["language"] == "en"
            assert provider.calls == 1
            replay = client.post(
                route + "/turns", headers={"X-RKG-Session": "synthetic"}, json=body
            )
            assert replay.json() == answer
            assert provider.calls == 1
            stored = client.get(route + "/turns").json()["items"][-1]
            assert stored["response_metadata"] == answer["response_metadata"]
            for index, citation in enumerate(answer["citations"]):
                source = client.get(
                    route + f"/turns/{answer['turn_id']}/citations/{index}"
                )
                assert source.status_code == 200
                assert source.json()["evidence"]["id"] == citation["evidence_id"]
                assert source.json()["snapshot_id"] == sid
            assert not store.get_conversation(conv.id).state["pending_candidate_ids"]
