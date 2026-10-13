"""Search / traversal / context services — AC-RKG-009/010/036/060."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rkg.domain import EntityType, context_json
from rkg.domain.models import EdgeType
from rkg.graph import (
    NoActiveSnapshotError,
    NotFoundError,
    SnapshotUnavailableError,
    build_context,
    publish_fact_batch,
    search_entities,
    traverse_subgraph,
)
from rkg.graph.access import mark_snapshot_unavailable
from rkg.graph.context import TRUNC_CHARS
from rkg.graph.traversal import TRUNC_DEPTH, TRUNC_EDGES, TRUNC_NODES
from rkg.storage import Storage
from tests.integration.graph_helpers import publish_meta, seed_cycle_graph
from tests.integration.storage_helpers import simple_batch


@pytest.fixture
def store(tmp_path: Path) -> Storage:
    storage = Storage(tmp_path / "rkg.kuzu")
    yield storage
    storage.close()


def test_ac036_search_match_order_paging_and_snapshot_isolation(
    store: Storage,
) -> None:
    repo_a, snap_a, batch_a = seed_cycle_graph(store, locator="/allowed/cycle-a")
    repo_b = store.create_repository(
        display_name="Other",
        source_type="local",
        source_locator="/allowed/cycle-b",
    )
    batch_b = simple_batch(repo_b.id, "snap-other")
    publish_fact_batch(store, batch_b, publish_meta())

    # Name collision: Callable "a" and Type "a" — both match q="a".
    page = search_entities(store, repo_a, snap_a, q="a", offset=0, limit=10)
    names = [(e.type.value, e.qualified_name, e.id) for e in page.items]
    assert names == sorted(names)
    assert {e.name for e in page.items} >= {"a"}
    assert all(e.snapshot_id == snap_a for e in page.items)

    # Endpoint method+path match (case-insensitive substring).
    by_path = search_entities(store, repo_a, snap_a, q="get /orders")
    assert any(e.type == EntityType.ENDPOINT for e in by_path.items)
    assert all(
        "orders" in (dict(e.attributes).get("path") or "") for e in by_path.items
    )

    typed = search_entities(
        store, repo_a, snap_a, q="a", entity_type=EntityType.TYPE
    )
    assert typed.total == 1
    assert typed.items[0].qualified_name == "app.cycle.Helper"

    # Paging boundaries — no duplicates / omissions across pages.
    full = search_entities(store, repo_a, snap_a, offset=0, limit=100)
    first = search_entities(store, repo_a, snap_a, offset=0, limit=2)
    second = search_entities(store, repo_a, snap_a, offset=2, limit=2)
    combined = list(first.items) + list(second.items)
    assert [e.id for e in combined] == [e.id for e in full.items[:4]]
    assert len({e.id for e in combined}) == len(combined)

    # Snapshot isolation: search on A never returns B entities.
    other = search_entities(store, repo_b.id, batch_b.snapshot_id, q="main")
    assert all(e.snapshot_id == batch_b.snapshot_id for e in other.items)
    assert all(e.repository_id == repo_b.id for e in other.items)
    assert not any(e.id in {x.id for x in batch_a.entities} for e in other.items)


def test_ac009_traversal_cycle_direction_filter_deterministic(store: Storage) -> None:
    repo, snap, batch = seed_cycle_graph(store)
    by_q = {e.qualified_name: e for e in batch.entities}
    root = by_q["app.cycle.a"]

    first = traverse_subgraph(
        store,
        repo,
        snap,
        root.id,
        direction="outgoing",
        edge_types=("calls",),
        depth=6,
        max_nodes=50,
        max_edges=100,
    )
    second = traverse_subgraph(
        store,
        repo,
        snap,
        root.id,
        direction="outgoing",
        edge_types=("calls",),
        depth=6,
        max_nodes=50,
        max_edges=100,
    )
    assert [n.id for n in first.nodes] == [n.id for n in second.nodes]
    assert [e.id for e in first.edges] == [e.id for e in second.edges]
    # Cycle remains finite: three callables, three call edges.
    assert {n.qualified_name for n in first.nodes} == {
        "app.cycle.a",
        "app.cycle.b",
        "app.cycle.c",
    }
    assert len(first.edges) == 3
    assert all(e.type == EdgeType.CALLS for e in first.edges)
    node_ids = {n.id for n in first.nodes}
    for edge in first.edges:
        assert edge.source_id in node_ids
        assert edge.target_id in node_ids

    incoming = traverse_subgraph(
        store,
        repo,
        snap,
        root.id,
        direction="incoming",
        edge_types=("calls",),
        depth=1,
        max_nodes=50,
        max_edges=100,
    )
    assert {n.qualified_name for n in incoming.nodes} == {"app.cycle.a", "app.cycle.c"}

    filtered = traverse_subgraph(
        store,
        repo,
        snap,
        by_q["app.cycle.get_orders"].id,
        direction="outgoing",
        edge_types=("handled_by",),
        depth=1,
        max_nodes=50,
        max_edges=100,
    )
    assert {e.type for e in filtered.edges} == {EdgeType.HANDLED_BY}
    assert any(n.qualified_name == "app.cycle.a" for n in filtered.nodes)

    deep = traverse_subgraph(
        store,
        repo,
        snap,
        root.id,
        direction="outgoing",
        edge_types=("calls",),
        depth=0,
        max_nodes=50,
        max_edges=100,
    )
    assert deep.nodes[0].id == root.id
    assert deep.edges == ()
    assert TRUNC_DEPTH in deep.truncation_reasons or deep.truncated

    tiny = traverse_subgraph(
        store,
        repo,
        snap,
        root.id,
        direction="outgoing",
        edge_types=("calls",),
        depth=6,
        max_nodes=2,
        max_edges=100,
    )
    assert len(tiny.nodes) <= 2
    assert TRUNC_NODES in tiny.truncation_reasons

    edge_cap = traverse_subgraph(
        store,
        repo,
        snap,
        root.id,
        direction="outgoing",
        edge_types=("calls",),
        depth=6,
        max_nodes=50,
        max_edges=1,
    )
    assert len(edge_cap.edges) <= 1
    assert TRUNC_EDGES in edge_cap.truncation_reasons


def test_ac010_context_deterministic_budget_and_no_secrets(store: Storage) -> None:
    repo, snap, batch = seed_cycle_graph(store)
    root = next(e for e in batch.entities if e.qualified_name == "app.cycle.get_orders")

    first = build_context(
        store,
        repo,
        snap,
        root.id,
        direction="outgoing",
        edge_types=("handled_by", "calls"),
        depth=4,
        max_nodes=50,
        max_edges=100,
        max_chars=20000,
    )
    second = build_context(
        store,
        repo,
        snap,
        root.id,
        direction="outgoing",
        edge_types=("handled_by", "calls"),
        depth=4,
        max_nodes=50,
        max_edges=100,
        max_chars=20000,
    )
    assert context_json(first) == context_json(second)
    data = json.loads(context_json(first))
    assert data["schema_version"] == "v1"
    assert data["root_id"] == root.id
    assert data["snapshot_id"] == snap
    assert "secret" not in context_json(first).lower()
    assert data["diagnostic_summary"].get("warning") == 1
    assert first.root_id in {n.id for n in first.nodes}
    node_ids = {n.id for n in first.nodes}
    for edge in first.edges:
        assert edge.source_id == repo or edge.source_id in node_ids
        assert edge.target_id == repo or edge.target_id in node_ids

    tight = build_context(
        store,
        repo,
        snap,
        root.id,
        direction="outgoing",
        edge_types=("handled_by", "calls"),
        depth=4,
        max_nodes=50,
        max_edges=100,
        max_chars=2000,
    )
    assert len(context_json(tight)) <= 2000
    assert tight.truncated
    assert TRUNC_CHARS in tight.truncation_reasons
    assert tight.root_id in {n.id for n in tight.nodes}


def test_ac060_guards_no_active_unavailable_identity(store: Storage) -> None:
    empty = store.create_repository(
        display_name="Empty",
        source_type="local",
        source_locator="/allowed/empty",
    )
    with pytest.raises(NoActiveSnapshotError) as no_active:
        search_entities(store, empty.id, None, q="x")
    assert no_active.value.code == "no_active_snapshot"

    repo, snap, batch = seed_cycle_graph(
        store, locator="/allowed/guards", snapshot_id="snap-guards-1"
    )
    mark_snapshot_unavailable(store, snap)
    with pytest.raises(SnapshotUnavailableError) as unavailable:
        traverse_subgraph(store, repo, snap, batch.entities[0].id)
    assert unavailable.value.code == "snapshot_unavailable"

    repo2, snap2, batch2 = seed_cycle_graph(
        store, locator="/allowed/guards-2", snapshot_id="snap-cycle-guards-2"
    )
    with pytest.raises(NotFoundError):
        traverse_subgraph(store, repo2, snap2, "missing-entity-id")
    with pytest.raises(NotFoundError):
        search_entities(store, repo2, "not-a-snapshot")
    foreign = store.create_repository(
        display_name="Foreign",
        source_type="local",
        source_locator="/allowed/foreign",
    )
    with pytest.raises(NotFoundError):
        # Ownership mismatch must not leak cross-repo snapshot.
        search_entities(store, foreign.id, snap2)


def test_ac036_endpoint_method_path_query(store: Storage) -> None:
    repo, snap, _batch = seed_cycle_graph(
        store, locator="/allowed/method-path", snapshot_id="snap-method-path"
    )
    hits = search_entities(store, repo, snap, q="POST /orders")
    assert hits.total >= 1
    assert all(e.type == EntityType.ENDPOINT for e in hits.items)
    assert hits.items[0].name == "post_orders"


def test_ac036_navigation_endpoint_path_query(store: Storage) -> None:
    """UI navigation routes are searchable by path without an HTTP method."""
    repo, snap, _batch = seed_cycle_graph(
        store, locator="/allowed/nav-path", snapshot_id="snap-nav-path"
    )
    hits = search_entities(store, repo, snap, q="/orders", entity_type=EntityType.ENDPOINT)
    names = {item.qualified_name for item in hits.items}
    assert "navigation:/orders" in names
    # HTTP POST /orders remains distinct from navigation:/orders.
    nav_only = [item for item in hits.items if item.qualified_name == "navigation:/orders"]
    assert len(nav_only) == 1
    assert dict(nav_only[0].attributes).get("kind") == "navigation"
    assert dict(nav_only[0].attributes).get("method") is None


def test_seeded_graph_entities_and_edges_match_batch_contract(store: Storage) -> None:
    """Layer-3 graph assert: published facts are readable exactly as seeded."""
    repo, snap, batch = seed_cycle_graph(
        store, locator="/allowed/seed-assert", snapshot_id="snap-seed-assert"
    )
    by_q = {entity.qualified_name: entity for entity in batch.entities}
    for entity in batch.entities:
        page = search_entities(
            store, repo, snap, q=entity.qualified_name, entity_type=entity.type
        )
        assert any(item.id == entity.id for item in page.items)
        assert all(item.snapshot_id == snap for item in page.items)
        assert all(item.repository_id == repo for item in page.items)

    root = by_q["app.cycle.a"]
    graph = traverse_subgraph(
        store,
        repo,
        snap,
        root.id,
        direction="outgoing",
        edge_types=("calls",),
        depth=1,
        max_nodes=20,
        max_edges=20,
    )
    expected = {
        edge.id
        for edge in batch.edges
        if edge.type == EdgeType.CALLS and edge.source_id == root.id
    }
    assert expected <= {edge.id for edge in graph.edges}
    assert {node.id for node in graph.nodes} >= {
        root.id,
        by_q["app.cycle.b"].id,
    }

    ctx = build_context(
        store,
        repo,
        snap,
        by_q["app.cycle.get_orders"].id,
        direction="outgoing",
        edge_types=("handled_by", "calls"),
        depth=2,
        max_nodes=50,
        max_edges=100,
        max_chars=20000,
    )
    assert ctx.snapshot_id == snap
    assert ctx.repository_id == repo
    assert by_q["app.cycle.get_orders"].id in {node.id for node in ctx.nodes}
    assert by_q["app.cycle.a"].id in {node.id for node in ctx.nodes}
    for edge in ctx.edges:
        assert edge.snapshot_id == snap
        assert edge.evidence_ids


def test_ac060_context_ownership_mismatch_is_not_found(store: Storage) -> None:
    repo, snap, batch = seed_cycle_graph(
        store, locator="/allowed/ctx-own", snapshot_id="snap-ctx-own"
    )
    foreign = store.create_repository(
        display_name="Foreign",
        source_type="local",
        source_locator="/allowed/ctx-foreign",
    )
    root = batch.entities[0]
    with pytest.raises(NotFoundError):
        build_context(store, foreign.id, snap, root.id)
