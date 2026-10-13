import pytest

from rkg.conversations import create_conversation, submit_grounded_turn
from rkg.llm import MockProvider
from rkg.storage import Storage
from tests.integration.graph_helpers import seed_cycle_graph


def response(root, anchor, edge_ids):
    return {
        "status": "answered",
        "root_id": root,
        "sections": [
            {
                "relation": "calls",
                "direction": "outgoing",
                "paths": [{"anchor_id": anchor, "edge_ids": edge_ids}],
            }
        ],
    }


@pytest.fixture
def graph(tmp_path):
    with Storage(tmp_path / "narrative.kuzu") as store:
        repo, sid, batch = seed_cycle_graph(store)
        conv = create_conversation(store, repository_id=repo, snapshot_id=sid)
        a = next(e for e in batch.entities if e.qualified_name == "app.cycle.a")
        endpoint = next(
            e for e in batch.entities if e.qualified_name == "app.cycle.get_orders"
        )
        ab = next(
            e for e in batch.edges if e.type.value == "calls" and e.source_id == a.id
        )
        bc = next(
            e
            for e in batch.edges
            if e.type.value == "calls" and e.source_id == ab.target_id
        )
        yield store, conv, a, endpoint, ab, bc


def test_endpoint_handler_bridge_and_indirect_exact_citations(graph):
    store, conv, a, endpoint, ab, bc = graph
    value = response(endpoint.id, a.id, [ab.id, bc.id])
    value["sections"][0]["paths"].insert(0, {"anchor_id": a.id, "edge_ids": [ab.id]})
    provider = MockProvider([value])
    result = submit_grounded_turn(
        store,
        conv.id,
        question="GET /orders/{id} calls what?",
        client_request_id="bridge",
        expected_revision=1,
        provider=provider,
    )
    turn = result.submission.turn
    assert turn.status == "answered"
    assert "GET /orders/{id} is handled by a" in turn.answer
    assert "directly" in turn.answer and "indirectly" in turn.answer
    assert "GET /orders/{id} calls a" not in turn.answer
    assert len(turn.claims) == 3
    assert provider.requests[0].schema_name == "rkg_narrative_v1"
    for claim in turn.claims:
        for index in claim["citation_indexes"]:
            assert turn.citations[index]["edge_id"] == claim["edge_id"]
    assert turn.response_metadata["subject"]["entity_id"] == endpoint.id


@pytest.mark.parametrize("kind", ["old", "disconnected", "foreign", "free_prose"])
def test_malformed_selection_no_salvage_or_repair(graph, kind):
    store, conv, a, _, ab, bc = graph
    value = response(a.id, a.id, [ab.id])
    if kind == "old":
        value = {"status": "answered", "edge_ids": [ab.id]}
    if kind == "disconnected":
        value = response(a.id, a.id, [bc.id])
    if kind == "foreign":
        value["sections"][0]["paths"].append(
            {"anchor_id": a.id, "edge_ids": ["foreign"]}
        )
    if kind == "free_prose":
        value["answer"] = "invented statement"
    provider = MockProvider([value])
    result = submit_grounded_turn(
        store,
        conv.id,
        question="What does a call?",
        root_id=a.id,
        client_request_id=kind,
        expected_revision=1,
        provider=provider,
    )
    assert result.submission.turn.error_code == "llm_malformed_response"
    assert not result.submission.turn.claims
    assert len(provider.requests) == 1
    assert result.submission.conversation.state == conv.state


def test_endpoint_prompt_contains_handler_anchors_and_complete_graph_limits(graph):
    import json

    store, conv, a, endpoint, ab, bc = graph
    provider = MockProvider([response(endpoint.id, a.id, [ab.id])])
    result = submit_grounded_turn(
        store,
        conv.id,
        question="endpoint get_orders dang goi nhung func nao",
        client_request_id="explicit-guidance",
        expected_revision=1,
        provider=provider,
    )
    assert result.submission.turn.status == "answered"
    payload = json.loads(provider.requests[0].messages[-1]["content"])
    anchor = next(
        item for item in payload["allowed_anchors"] if item["anchor_id"] == a.id
    )
    assert anchor["relations"] == ["calls"]
    assert anchor["connector_id"]
    assert anchor["max_path_edges"] == len(payload["nodes"])
    assert not any(
        item["anchor_id"] == endpoint.id for item in payload["allowed_anchors"]
    )
    assert payload["path_limits"]["max_distinct_edges"] == len(payload["facts"])
    assert {tuple(p["edge_ids"]) for p in payload["candidate_paths"]} == {
        (ab.id,),
        (ab.id, bc.id),
    }
    assert all(p["anchor_id"] == a.id for p in payload["candidate_paths"])
    assert "root_id" in provider.requests[0].messages[0]["content"]


@pytest.mark.parametrize(
    "kind,stage,reason",
    [
        ("schema", "narrative", "invalid_schema"),
        ("foreign_edge", "narrative", "invalid_schema"),
    ],
)
def test_failed_narrative_logs_only_safe_stage_reason(
    graph, caplog, kind, stage, reason
):
    import logging

    store, conv, a, endpoint, ab, _ = graph
    value = response(endpoint.id, a.id, [ab.id])
    if kind == "schema":
        value["answer"] = "synthetic-private-provider-output"
    else:
        value["sections"][0]["paths"][0]["edge_ids"] = [
            "synthetic-private-foreign-reference"
        ]
    with caplog.at_level(logging.INFO, logger="rkg.conversation"):
        result = submit_grounded_turn(
            store,
            conv.id,
            question="endpoint get_orders dang goi nhung func nao",
            client_request_id="rejected-" + kind,
            expected_revision=1,
            provider=MockProvider([value]),
        )
    assert result.submission.turn.error_code == "llm_malformed_response"
    assert result.submission.conversation.state == conv.state
    assert f"stage={stage} reason={reason}" in caplog.text
    assert "synthetic-private" not in caplog.text
    assert "dang goi" not in caplog.text


@pytest.mark.parametrize(
    "kind,reason",
    [("exception", "provider_failure"), ("wrong_shape", "response_shape")],
)
def test_unexpected_provider_failure_has_staged_warning_without_sensitive_text(
    graph, caplog, kind, reason
):
    import logging

    store, conv, _, _, _, _ = graph

    class BrokenProvider:
        enabled = True
        calls = 0

        def complete(self, request, budget):
            self.calls += 1
            if kind == "exception":
                raise RuntimeError("synthetic-private-error-content")
            return None

    provider = BrokenProvider()
    with caplog.at_level(logging.WARNING, logger="rkg.conversation"):
        result = submit_grounded_turn(
            store,
            conv.id,
            question="endpoint get_orders dang goi nhung func nao",
            client_request_id="unexpected-" + kind,
            expected_revision=1,
            provider=provider,
        )
    assert result.submission.turn.error_code == "provider_failed"
    assert result.submission.conversation.state == conv.state
    assert provider.calls == 1
    assert f"stage=narrative reason={reason} error_code=provider_failed" in caplog.text
    assert "synthetic-private" not in caplog.text and "dang goi" not in caplog.text
