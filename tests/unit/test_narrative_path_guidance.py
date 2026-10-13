"""Grounded path hints prevent sibling concatenation and skipped call prefixes."""

from dataclasses import replace

from tests.unit.test_conversation_narrative import fixture

from rkg.conversations.narrative import narrative_guidance, validate_narrative
from rkg.domain.models import Edge, EdgeType, Entity, EntityType


def candidates(context, relations=("calls",), direction="outgoing"):
    paths = narrative_guidance(context, relations, direction)["candidate_paths"]
    for path in paths:
        value = {
            "status": "answered",
            "root_id": context.root_id,
            "sections": [
                {
                    "relation": path["relation"],
                    "direction": direction,
                    "paths": [
                        {"anchor_id": path["anchor_id"], "edge_ids": path["edge_ids"]}
                    ],
                }
            ],
        }
        validate_narrative(value, context, relations, direction)
    return paths


def test_siblings_are_separate_and_indirect_prefix_is_complete():
    context = fixture()
    context = replace(
        context,
        edges=context.edges
        + (Edge("ac", "snap", EdgeType.CALLS, "a", "c", "calls", ("ev",)),),
    )
    paths = candidates(context)
    assert {tuple(p["edge_ids"]) for p in paths} == {("ab",), ("ac",), ("ab", "bc")}


def test_incoming_call_paths_follow_reverse_edges():
    paths = candidates(fixture(), direction="incoming")
    assert {tuple(p["edge_ids"]) for p in paths} == {("ca",), ("ca", "bc")}


def test_access_relation_is_last_outgoing_and_first_incoming():
    context = fixture()
    table = Entity("t", "repo", "snap", EntityType.DATA_RESOURCE, "table", "table")
    context = replace(
        context,
        nodes=context.nodes + (table,),
        edges=context.edges
        + (Edge("bt", "snap", EdgeType.READS, "b", "t", "reads", ("ev",)),),
    )
    assert [p["edge_ids"] for p in candidates(context, ("reads",))] == [["ab", "bt"]]
    incoming = candidates(replace(context, root_id="t"), ("reads",), "incoming")
    assert {tuple(p["edge_ids"]) for p in incoming} == {
        ("bt",),
        ("bt", "ab"),
        ("bt", "ab", "ca"),
    }


def test_endpoint_connector_is_excluded_and_consumes_depth():
    context = fixture()
    endpoint = Entity("ep", "repo", "snap", EntityType.ENDPOINT, "endpoint", "endpoint")
    context = replace(
        context,
        root_id="ep",
        nodes=context.nodes + (endpoint,),
        edges=context.edges
        + (Edge("handler", "snap", EdgeType.HANDLED_BY, "ep", "a", "route", ("ev",)),),
    )
    paths = candidates(context)
    assert all(p["anchor_id"] == "a" and "handler" not in p["edge_ids"] for p in paths)
    shallow = replace(context, budget=replace(context.budget, depth=2))
    assert [p["edge_ids"] for p in candidates(shallow)] == [["ab"]]
    assert candidates(replace(context, budget=replace(context.budget, depth=1))) == []


def test_unsupported_and_foreign_edges_are_not_suggested():
    context = fixture()
    context = replace(
        context,
        edges=context.edges
        + (
            Edge(
                "unsupported", "snap", EdgeType.CALLS, "a", "c", "calls", ("missing",)
            ),
            Edge("foreign", "other", EdgeType.CALLS, "a", "c", "calls", ("ev",)),
        ),
    )
    assert {tuple(p["edge_ids"]) for p in candidates(context)} == {
        ("ab",),
        ("ab", "bc"),
    }


def test_witness_uses_alternative_prefix_to_avoid_terminal_cycle():
    context = fixture()
    d = Entity("d", "repo", "snap", EntityType.CALLABLE, "d", "app.d")
    context = replace(
        context,
        nodes=context.nodes + (d,),
        edges=(
            Edge("ac", "snap", EdgeType.CALLS, "a", "c", "calls", ("ev",)),
            Edge("cb", "snap", EdgeType.CALLS, "c", "b", "calls", ("ev",)),
            Edge("bc", "snap", EdgeType.CALLS, "b", "c", "calls", ("ev",)),
            Edge("ad", "snap", EdgeType.CALLS, "a", "d", "calls", ("ev",)),
            Edge("db", "snap", EdgeType.CALLS, "d", "b", "calls", ("ev",)),
        ),
    )
    paths = candidates(context)
    assert ["ad", "db", "bc"] in [p["edge_ids"] for p in paths]
    assert paths == candidates(replace(context, edges=tuple(reversed(context.edges))))
