"""Actual indexed fixture and HTTP flow, without preselected subject IDs."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from rkg.api import create_app
from rkg.ingestion import LocalSourcePolicy
from rkg.jobs import IndexCoordinator
from rkg.llm import MockProvider
from rkg.storage import Storage


class CandidateProvider:
    enabled = True

    def __init__(self):
        self.requests = []

    def complete(self, request, budget):
        self.requests.append(request)
        assert request.schema_name == "rkg_narrative_v1"
        payload = json.loads(request.messages[-1]["content"])
        paths = []
        used = set()
        for p in payload["candidate_paths"]:
            merged = used | set(p["edge_ids"])
            if len(merged) <= 8 and len(paths) < 8:
                paths.append({"anchor_id": p["anchor_id"], "edge_ids": p["edge_ids"]})
                used = merged
        response = {
            "status": "answered" if paths else "insufficient_evidence",
            "root_id": payload["root_id"],
            "sections": [{"relation": "calls", "direction": "outgoing", "paths": paths}]
            if paths
            else [],
        }
        return MockProvider([response]).complete(request, budget)


@pytest.fixture(scope="module")
def indexed(tmp_path_factory):
    source = Path(__file__).resolve().parents[2] / "repo-test/soopi"
    with Storage(tmp_path_factory.mktemp("natural-api") / "graph") as store:
        repo = store.create_repository(
            display_name="natural",
            source_type="local",
            source_locator=str(source),
            app_module="app.main",
            app_symbol="app",
        )
        job = IndexCoordinator(store, LocalSourcePolicy((source,))).run(repo.id)
        assert job.status in {"succeeded", "succeeded_with_warnings"}
        yield store, source, repo.id, store.get_repository(repo.id).active_snapshot_id


@pytest.mark.parametrize(
    "question",
    [
        "logout dang goi nhung gi, no nam o dau",
        "logout đang gọi những hàm nào, nó nằm ở đâu?",
        "What does logout call and where is it defined?",
        "endpoint logout dang goi nhung gi, no nam o dau",
    ],
)
def test_real_snapshot_natural_calls_and_location_http(indexed, question):
    store, source, repo, sid = indexed
    provider = CandidateProvider()
    app = create_app(
        store,
        LocalSourcePolicy((source,)),
        session_token="local-natural-token",
        provider=provider,
    )
    with TestClient(
        app,
        base_url="http://127.0.0.1",
        headers={"X-RKG-Session": "local-natural-token"},
    ) as client:
        created = client.post(
            "/api/v1/conversations", json={"repository_id": repo, "snapshot_id": sid}
        )
        assert created.status_code == 201
        conv = created.json()
        route = f"/api/v1/conversations/{conv['conversation_id']}/turns"
        first = client.post(
            route,
            json={
                "question": question,
                "client_request_id": "natural",
                "expected_revision": 1,
                "ui_locale": "vi",
            },
        )
        assert first.status_code == 200
        data = first.json()
        if data["status"] == "needs_clarification":
            assert not provider.requests
            choices = data["candidate_entities"]
            ordinal = next(
                i + 1 for i, e in enumerate(choices) if e["type"] == "Endpoint"
            )
            second = client.post(
                route,
                json={
                    "question": str(ordinal),
                    "client_request_id": "choose",
                    "expected_revision": data["revision"],
                    "ui_locale": "vi",
                },
            )
            assert second.status_code == 200
            data = second.json()
        assert data["status"] == "answered"
        assert "app/api/v1/endpoints/auth.py:" in data["answer"]
        assert data["response_metadata"]["subject"]["type"] == "Endpoint"
        assert data["claims"] and data["citations"]
        assert len(provider.requests) == 1
        exact = client.get(route + f"/{data['turn_id']}/citations/0")
        assert exact.status_code == 200
        where = client.post(
            route,
            json={
                "question": "no nam o dau",
                "client_request_id": "where-followup",
                "expected_revision": data["revision"],
                "ui_locale": "en",
            },
        )
        assert where.status_code == 200 and where.json()["status"] == "answered"
        assert "app/api/v1/endpoints/auth.py:" in where.json()["answer"]
        assert where.json()["response_metadata"]["language"] == "vi"
        assert len(provider.requests) == 1


class PlannedCandidateProvider(CandidateProvider):
    def complete(self, request, budget):
        if request.schema_name == "rkg_read_plan_v2":
            self.requests.append(request)
            payload = json.loads(request.messages[-1]["content"])
            assert payload["bound_relation_types"] == ["calls"]
            assert payload["source_location_requested"] is True
            assert request.schema["properties"]["relation_types"]["items"]["enum"] == [
                "calls"
            ]
            return MockProvider(
                [
                    {
                        "mode": "search",
                        "query": "logout",
                        "candidate_index": 0,
                        "entity_type": "Endpoint",
                        "direction": "outgoing",
                        "relation_types": ["calls"],
                    }
                ]
            ).complete(request, budget)
        return super().complete(request, budget)


def test_paraphrase_without_literal_name_uses_one_constrained_read_plan(indexed):
    store, source, repo, sid = indexed
    provider = PlannedCandidateProvider()
    app = create_app(
        store,
        LocalSourcePolicy((source,)),
        session_token="local-natural-token",
        provider=provider,
    )
    with TestClient(
        app,
        base_url="http://127.0.0.1",
        headers={"X-RKG-Session": "local-natural-token"},
    ) as client:
        conv = client.post(
            "/api/v1/conversations", json={"repository_id": repo, "snapshot_id": sid}
        ).json()
        route = f"/api/v1/conversations/{conv['conversation_id']}/turns"
        response = client.post(
            route,
            json={
                "question": "Chức năng đăng xuất gọi những hàm nào, nó nằm ở đâu?",
                "client_request_id": "paraphrase",
                "expected_revision": 1,
                "ui_locale": "vi",
            },
        )
        assert response.status_code == 200 and response.json()["status"] == "answered"
        assert "app/api/v1/endpoints/auth.py:" in response.json()["answer"]
        assert [r.schema_name for r in provider.requests] == [
            "rkg_read_plan_v2",
            "rkg_narrative_v1",
        ]
