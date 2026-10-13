"""Complete directed retrieval on stored graphs, including cycles and noise."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from rkg.conversations.narrative import narrative_guidance, validate_narrative
from rkg.domain import edge_id, evidence_id
from rkg.domain.context import context_json
from rkg.domain.models import Edge, EdgeType, Entity, EntityType, Evidence, FactBatch
from rkg.graph import publish_fact_batch
from rkg.graph.related import build_related_context
from rkg.storage import Storage
from tests.integration.graph_helpers import publish_meta


@pytest.fixture
def graph(tmp_path):
    with Storage(tmp_path / "graph") as store:
        repo = store.create_repository(
            display_name="related",
            source_type="local",
            source_locator="RKG.synthetic.fixture.v1",
        )
        snap = SimpleNamespace(id="snap-related")
        nodes = [
            Entity(str(i), repo.id, snap.id, EntityType.CALLABLE, str(i), f"f{i}")
            for i in range(230)
        ]
        nodes += [
            Entity("ep", repo.id, snap.id, EntityType.ENDPOINT, "ep", "ep"),
            Entity("table", repo.id, snap.id, EntityType.DATA_RESOURCE, "t", "t"),
            Entity("noise", repo.id, snap.id, EntityType.CALLABLE, "noise", "noise"),
            Entity("other", repo.id, snap.id, EntityType.CALLABLE, "other", "other"),
        ]
        ev = Evidence(
            evidence_id(snap.id, "app/fixture.py", 1, 2, "RKG.synthetic.fixture.v1"),
            snap.id,
            "app/fixture.py",
            1,
            2,
            "RKG.synthetic.fixture.v1",
        )

        def edge(key, kind, source, target):
            return Edge(
                edge_id(snap.id, kind, source, target),
                snap.id,
                kind,
                source,
                target,
                "RKG.synthetic.fixture.v1",
                (ev.id,),
            )

        edges = [edge(f"c{i}", EdgeType.CALLS, str(i), str(i + 1)) for i in range(229)]
        edges += [
            edge("handler", EdgeType.HANDLED_BY, "ep", "0"),
            edge("cycle", EdgeType.CALLS, "229", "0"),
            edge("read", EdgeType.READS, "229", "table"),
            edge("noise", EdgeType.CALLS, "0", "noise"),
            edge("otherread", EdgeType.READS, "other", "table"),
        ]
        publish_fact_batch(
            store,
            FactBatch(repo.id, snap.id, tuple(nodes), tuple(edges), (ev,)),
            publish_meta(),
        )
        yield store, repo.id, snap.id


def test_endpoint_retrieves_deep_calls_without_other_table_users(graph):
    context = build_related_context(*graph, "ep", edge_types=("calls",))
    assert len(context.nodes) == 232
    assert len(context.edges) == 232
    assert not context.truncated
    assert context.budget.depth is None
    assert {n.id for n in context.nodes}.isdisjoint({"table", "other"})
    assert context.evidence
    assert len(context_json(context)) > 20000
    assert context == build_related_context(*graph, "ep", edge_types=("calls",))


def test_reads_prunes_dead_call_branches_and_keeps_deep_paths(graph):
    context = build_related_context(*graph, "ep", edge_types=("reads",))
    ids = {n.id for n in context.nodes}
    assert {"ep", "0", "229", "table"} <= ids
    assert ids.isdisjoint({"noise", "other"})
    assert all(e.source_id != "other" and e.target_id != "noise" for e in context.edges)
    guidance = narrative_guidance(context, ("reads",))
    assert len(guidance["candidate_paths"]) == 1
    candidate = guidance["candidate_paths"][0]
    assert len(candidate["edge_ids"]) == 230
    value = {
        "status": "answered",
        "root_id": "ep",
        "sections": [
            {
                "relation": "reads",
                "direction": "outgoing",
                "paths": [
                    {
                        "anchor_id": candidate["anchor_id"],
                        "edge_ids": candidate["edge_ids"],
                    }
                ],
            }
        ],
    }
    assert validate_narrative(value, context, ("reads",), "outgoing")


def test_incoming_reads_follows_callers_not_other_outgoing_branches(graph):
    context = build_related_context(
        *graph, "table", edge_types=("reads",), direction="incoming"
    )
    assert {"0", "229", "other", "table"} <= {n.id for n in context.nodes}
    assert {n.id for n in context.nodes}.isdisjoint({"noise", "ep"})
    assert not context.truncated


def test_unbounded_narrative_accepts_more_than_eight_facts(graph):
    context = build_related_context(*graph, "0", edge_types=("calls",))
    # A compact branching graph tests schema array and distinct-edge ceilings.
    edges = tuple(
        replace(e, source_id="0")
        for e in context.edges
        if e.type == EdgeType.CALLS and e.target_id not in {"0", "noise"}
    )
    context = replace(context, edges=edges)
    value = {
        "status": "answered",
        "root_id": "0",
        "sections": [
            {
                "relation": "calls",
                "direction": "outgoing",
                "paths": [{"anchor_id": "0", "edge_ids": [e.id]} for e in edges],
            }
        ],
    }
    assert len(validate_narrative(value, context, ("calls",), "outgoing")) == 229


@pytest.mark.parametrize(
    ("query", "method", "path", "relations"),
    [
        ("", "POST", "/api/v1/auth/logout", ("calls",)),
        ("", "POST", "/api/v1/auth/login", ("handled_by",)),
        ("", "POST", "/api/v1/orders", ("calls",)),
    ],
)
def test_soopi_complete_context_and_grounded_turn(
    tmp_path, query, method, path, relations
):
    import json
    from pathlib import Path

    from rkg.conversations import create_conversation, submit_grounded_turn
    from rkg.graph.search import lookup_entities
    from rkg.ingestion import LocalSourcePolicy
    from rkg.jobs import IndexCoordinator
    from rkg.llm import MockProvider

    source = Path(__file__).resolve().parents[2] / "repo-test/soopi"
    with Storage(tmp_path / "soopi-graph") as store:
        repo = store.create_repository(
            display_name="fixture",
            source_type="local",
            source_locator=str(source),
            app_module="app.main",
            app_symbol="app",
        )
        job = IndexCoordinator(store, LocalSourcePolicy((source,))).run(repo.id)
        assert job.status in {"succeeded", "succeeded_with_warnings"}
        sid = store.get_repository(repo.id).active_snapshot_id
        page = lookup_entities(
            store,
            repo.id,
            sid,
            query=query,
            entity_type="Endpoint",
            method=method,
            path=path,
        )
        assert page.total == 1
        root = page.items[0]
        context = build_related_context(
            store,
            repo.id,
            sid,
            root.id,
            edge_types=(*relations, "calls")
            if relations == ("handled_by",)
            else relations,
        )
        guidance = narrative_guidance(context, relations)
        assert guidance["candidate_paths"] and not context.truncated
        values = []
        for relation in relations:
            paths = [
                {"anchor_id": p["anchor_id"], "edge_ids": p["edge_ids"]}
                for p in guidance["candidate_paths"]
                if p["relation"] == relation
            ]
            if paths:
                values.append(
                    {"relation": relation, "direction": "outgoing", "paths": paths}
                )
        provider = MockProvider(
            [{"status": "answered", "root_id": root.id, "sections": values}]
        )
        conv = create_conversation(store, repository_id=repo.id, snapshot_id=sid)
        relation_text = (
            "gọi những hàm nào" if relations == ("calls",) else "được xử lý bởi hàm nào"
        )
        result = submit_grounded_turn(
            store,
            conv.id,
            question=f"{method} {path} {relation_text}?",
            client_request_id="complete",
            expected_revision=1,
            provider=provider,
        )
        assert result.submission.turn.status == "answered"
        assert result.submission.turn.citations
        payload = json.loads(provider.requests[0].messages[-1]["content"])
        assert len(payload["nodes"]) == len(context.nodes)
        assert len(payload["facts"]) == len(context.edges)
        assert result.submission.turn.response_metadata["retrieval_truncated"] is False
