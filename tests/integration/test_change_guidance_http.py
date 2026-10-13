"""Advice is persisted and replayed through the existing conversation API."""

from fastapi.testclient import TestClient

from rkg.api import create_app
from rkg.ingestion import LocalSourcePolicy
from rkg.llm import MockProvider
from tests.integration.test_change_guidance import indexed as indexed


def test_change_advice_http_replay_history_and_sources(indexed, tmp_path):
    store, repo, sid = indexed
    provider = MockProvider([])
    app = create_app(
        store,
        LocalSourcePolicy((tmp_path,)),
        session_token="synthetic-local-session",
        provider=provider,
    )
    with TestClient(
        app,
        base_url="http://127.0.0.1",
        headers={"X-RKG-Session": "synthetic-local-session"},
    ) as client:
        created = client.post(
            "/api/v1/conversations",
            json={
                "repository_id": repo,
                "snapshot_id": sid,
            },
        )
        assert created.status_code == 201
        conv = created.json()
        route = f"/api/v1/conversations/{conv['conversation_id']}/turns"
        body = {
            "question": "Muốn sửa OrderService.checkout thì sửa file nào, dòng nào?",
            "client_request_id": "advice",
            "expected_revision": conv["revision"],
        }
        response = client.post(route, json=body)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "answered"
        assert "app/services/order_service.py" in data["answer"]
        assert data["citations"] and not provider.requests
        assert client.post(route, json=body).json() == data
        history = client.get(route).json()
        assert any(t["answer"] == data["answer"] for t in history["items"])
        citation = client.get(f"{route}/{data['turn_id']}/citations/0")
        assert citation.status_code == 200
        assert citation.json()["snapshot_id"] == sid
