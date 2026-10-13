import pytest
from fastapi.testclient import TestClient

from rkg.api import create_app
from rkg.conversations import create_conversation
from rkg.graph.access import mark_snapshot_unavailable
from rkg.ingestion import LocalSourcePolicy
from rkg.llm import MockProvider
from rkg.storage import Storage
from tests.integration.graph_helpers import seed_cycle_graph


@pytest.fixture
def graph(tmp_path):
    with Storage(tmp_path / "contract.kuzu") as store:
        repo, sid, batch = seed_cycle_graph(store)
        conv = create_conversation(store, repository_id=repo, snapshot_id=sid)
        app = create_app(
            store,
            LocalSourcePolicy((tmp_path,)),
            session_token="synthetic-session",
            provider=MockProvider([]),
        )
        with TestClient(app, base_url="http://127.0.0.1") as client:
            yield store, client, repo, sid, batch, conv, app


def post(client, conv, question="hello", locale=None, key="greeting", root=None):
    return client.post(
        "/api/v1/conversations/" + conv.id + "/turns",
        headers={"X-RKG-Session": "synthetic-session"},
        json={
            "question": question,
            "client_request_id": key,
            "expected_revision": conv.revision,
            "ui_locale": locale,
            "root_id": root,
        },
    )


def test_capabilities_and_persisted_locale_replay(graph):
    store, client, _, _, _, conv, app = graph
    cap = client.get("/api/v1/conversations/capabilities")
    assert cap.status_code == 200
    assert set(cap.json()["features"]) == {
        "ui_locale",
        "response_metadata_v1",
        "exact_citation_lookup",
        "history_unavailable",
    }
    assert cap.json()["provider_enabled"] is True
    app.state.provider = MockProvider([])
    current = store.get_conversation(conv.id)
    greeting = post(client, current, question="hello", locale="en", key="hello")
    assert greeting.status_code == 200
    body = greeting.json()
    assert body["response_metadata"]["language"] == "en"
    replay = post(client, current, question="hello", locale="en", key="hello")
    assert replay.json()["response_metadata"] == body["response_metadata"]
    history = client.get("/api/v1/conversations/" + conv.id + "/turns").json()
    assert history["items"][-1]["response_metadata"] == body["response_metadata"]


def test_invalid_locale_writes_nothing_and_unavailable_opt_in(graph):
    store, client, _, sid, _, conv, _ = graph
    invalid = post(client, conv, locale="fr")
    assert invalid.status_code == 422
    assert store.get_conversation(conv.id).revision == 1
    hello = post(client, conv)
    assert hello.status_code == 200
    mark_snapshot_unavailable(store, sid)
    assert client.get("/api/v1/conversations/" + conv.id + "/turns").status_code == 410
    response = client.get(
        "/api/v1/conversations/" + conv.id + "/turns?include_unavailable=true"
    )
    assert response.status_code == 200
    assert response.json()["snapshot_available"] is False
    assert len(response.json()["items"]) == 1
    assert response.json()["candidate_entities"] == []
    assert response.json()["conversation"]["snapshot_id"] == sid


def test_exact_source_uses_cited_evidence_not_target_entity(graph):
    store, client, _, sid, batch, conv, app = graph
    a = next(e for e in batch.entities if e.qualified_name == "app.cycle.a")
    edge = next(
        e for e in batch.edges if e.type.value == "calls" and e.source_id == a.id
    )
    app.state.provider = MockProvider(
        [
            {
                "status": "answered",
                "root_id": a.id,
                "sections": [
                    {
                        "relation": "calls",
                        "direction": "outgoing",
                        "paths": [{"anchor_id": a.id, "edge_ids": [edge.id]}],
                    }
                ],
            }
        ]
    )
    result = post(client, conv, question="What does a call?", key="source", root=a.id)
    assert result.status_code == 200
    turn = result.json()["turn_id"]
    route = "/api/v1/conversations/" + conv.id + "/turns/" + turn + "/citations/"
    source = client.get(route + "0")
    assert source.status_code == 200
    assert source.json()["evidence"]["id"] == edge.evidence_ids[0]
    assert source.json()["snapshot_id"] == sid
    assert set(source.json()["evidence"]) == {
        "id",
        "file_path",
        "provenance",
        "start_line",
        "end_line",
        "rule",
    }
    assert client.get(route + str(len(result.json()["citations"]))).status_code == 404
    assert client.get(route + "-1").status_code == 422
    assert client.get(route + "not_an_index").status_code == 422
    other = create_conversation(
        store, repository_id=conv.repository_id, snapshot_id=sid
    )
    assert client.get(route.replace(conv.id, other.id) + "0").status_code == 404
    mark_snapshot_unavailable(store, sid)
    assert client.get(route + "0").status_code == 410


def test_replay_and_history_read_stored_partial_flags(graph):
    from rkg.conversations.service import ProviderResult, submit_turn

    store, client, _, _, batch, conv, _ = graph
    a = batch.entities[0]
    metadata = {
        "version": 1,
        "language": "vi",
        "kind": "answer",
        "subject": {
            "entity_id": a.id,
            "type": a.type.value,
            "name": a.name,
            "qualified_name": a.qualified_name,
            "method": None,
            "path": None,
        },
        "coverage": "partial",
        "retrieval_truncated": False,
        "history_truncated": True,
        "limitations": ["history_truncated"],
        "insufficient_reason": None,
    }
    stored = submit_turn(
        store,
        conv.id,
        question="sample",
        client_request_id="partial",
        expected_revision=1,
        provider=lambda _: ProviderResult(
            status="answered", answer="synthetic", response_metadata=metadata
        ),
    )
    replay = post(client, stored.conversation, question="sample", key="partial")
    assert replay.status_code == 200
    assert replay.json()["history_truncated"] is True
    assert replay.json()["limitations"] == ["history_truncated"]
    history = client.get("/api/v1/conversations/" + conv.id + "/turns").json()
    assert history["items"][0]["response_metadata"] == metadata
    conflict = post(
        client, stored.conversation, question="sample", locale="en", key="partial"
    )
    assert conflict.status_code == 409


def test_exact_source_rejects_unsafe_location_and_filesystem_has_null_lines(graph):
    store, client, _, sid, batch, conv, app = graph
    a = next(e for e in batch.entities if e.qualified_name == "app.cycle.a")
    edge = next(
        e for e in batch.edges if e.type.value == "calls" and e.source_id == a.id
    )
    app.state.provider = MockProvider(
        [
            {
                "status": "answered",
                "root_id": a.id,
                "sections": [
                    {
                        "relation": "calls",
                        "direction": "outgoing",
                        "paths": [{"anchor_id": a.id, "edge_ids": [edge.id]}],
                    }
                ],
            }
        ]
    )
    result = post(
        client, conv, question="What does a call?", key="safe-source", root=a.id
    )
    route = (
        "/api/v1/conversations/"
        + conv.id
        + "/turns/"
        + result.json()["turn_id"]
        + "/citations/0"
    )
    for path in ["/private/calls.py", "../calls.py", "C:\\private\\calls.py"]:
        store.conn.execute(
            "MATCH (e:Evidence {id:$id, snapshot_id:$sid}) SET e.file_path=$path",
            {"id": edge.evidence_ids[0], "sid": sid, "path": path},
        )
        assert client.get(route).status_code == 404
    store.conn.execute(
        "MATCH (e:Evidence {id:$id, snapshot_id:$sid}) "
        "SET e.file_path=$path,e.rule=$rule",
        {
            "id": edge.evidence_ids[0],
            "sid": sid,
            "path": "app/calls.py",
            "rule": "RKG.structure.contains.v1",
        },
    )
    source = client.get(route).json()["evidence"]
    assert source["provenance"] == "filesystem"
    assert source["start_line"] is None and source["end_line"] is None
