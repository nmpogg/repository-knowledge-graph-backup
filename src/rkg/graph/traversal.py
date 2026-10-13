"""Deterministic BFS subgraph traversal (AC-RKG-009 / AC-RKG-060)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from rkg.domain.models import Edge, EdgeType, Entity, EntityType
from rkg.graph.access import load_entities, load_entity, require_readable_snapshot
from rkg.graph.errors import InvalidBudgetError
from rkg.graph.ids import logical_entity_id
from rkg.storage._util import EDGE_REL_TABLE, fetch_all
from rkg.storage.connection import Storage
from rkg.storage.errors import NotFoundError

Direction = Literal["incoming", "outgoing", "both"]

TRUNC_DEPTH = "depth_limit"
TRUNC_NODES = "max_nodes"
TRUNC_EDGES = "max_edges"


@dataclass(frozen=True, slots=True)
class SubgraphResult:
    repository_id: str
    snapshot_id: str
    root_id: str
    nodes: tuple[Entity, ...]
    edges: tuple[Edge, ...]
    truncated: bool
    truncation_reasons: tuple[str, ...]
    depth: int
    max_nodes: int
    max_edges: int


@dataclass(frozen=True, slots=True)
class _LoadedEdge:
    edge: Edge


def _validate_traversal_budget(depth: int, max_nodes: int, max_edges: int) -> None:
    if not (0 <= depth <= 6):
        raise InvalidBudgetError("depth must be between 0 and 6")
    if not (1 <= max_nodes <= 200 and 1 <= max_edges <= 400):
        raise InvalidBudgetError("node/edge budget outside API limits")


def _normalize_edge_types(
    edge_types: tuple[str | EdgeType, ...] | list[str | EdgeType] | None,
) -> frozenset[str] | None:
    if edge_types is None:
        return None
    if len(edge_types) == 0:
        return frozenset()
    return frozenset(e.value if isinstance(e, EdgeType) else str(e) for e in edge_types)


def _load_snapshot_edges(
    storage: Storage,
    *,
    repository_id: str,
    snapshot_id: str,
    allowed_types: frozenset[str] | None,
) -> list[_LoadedEdge]:
    loaded: list[_LoadedEdge] = []
    for edge_type, rel in EDGE_REL_TABLE.items():
        if allowed_types is not None and edge_type not in allowed_types:
            continue
        rows = fetch_all(
            storage.conn,
            f"MATCH (a)-[r:{rel}]->(b) "
            f"WHERE r.snapshot_id = $sid "
            f"RETURN r.edge_id, r.rule, r.evidence_ids, a.id, b.id "
            f"ORDER BY r.edge_id ASC",
            {"sid": snapshot_id},
        )
        for edge_id, rule, evidence_ids, src_phys, tgt_phys in rows:
            src_phys_s = str(src_phys)
            tgt_phys_s = str(tgt_phys)
            source_id = (
                repository_id
                if src_phys_s == repository_id
                else logical_entity_id(src_phys_s, snapshot_id)
            )
            target_id = (
                repository_id
                if tgt_phys_s == repository_id
                else logical_entity_id(tgt_phys_s, snapshot_id)
            )
            ev = tuple(str(x) for x in (evidence_ids or []))
            loaded.append(
                _LoadedEdge(
                    edge=Edge(
                        id=str(edge_id),
                        snapshot_id=snapshot_id,
                        type=EdgeType(edge_type),
                        source_id=source_id,
                        target_id=target_id,
                        rule=str(rule),
                        evidence_ids=ev,
                    )
                )
            )
    loaded.sort(
        key=lambda item: (
            item.edge.type.value,
            item.edge.source_id,
            item.edge.target_id,
            item.edge.id,
        )
    )
    return loaded


def _neighbors(
    edges: list[_LoadedEdge],
    node_id: str,
    direction: Direction,
) -> list[tuple[Edge, str]]:
    """Return (edge, other_id) candidates in deterministic edge order."""
    out: list[tuple[Edge, str]] = []
    for item in edges:
        edge = item.edge
        if direction in ("outgoing", "both") and edge.source_id == node_id:
            out.append((edge, edge.target_id))
        elif direction in ("incoming", "both") and edge.target_id == node_id:
            out.append((edge, edge.source_id))
    return out


def traverse_subgraph(
    storage: Storage,
    repository_id: str,
    snapshot_id: str | None,
    root_id: str,
    *,
    direction: Direction = "both",
    edge_types: tuple[str | EdgeType, ...] | list[str | EdgeType] | None = None,
    depth: int = 4,
    max_nodes: int = 50,
    max_edges: int = 100,
    view: Literal["neighborhood", "flow"] = "neighborhood",
    include_structure: bool = False,
    include_dependencies: bool = False,
) -> SubgraphResult:
    """BFS with visited-set cycle handling and deterministic expansion order."""
    if direction not in ("incoming", "outgoing", "both"):
        raise ValueError("direction must be incoming|outgoing|both")
    if view not in ("neighborhood", "flow"):
        raise ValueError("invalid_request")
    _validate_traversal_budget(depth, max_nodes, max_edges)
    allowed = _normalize_edge_types(edge_types)

    snap = require_readable_snapshot(storage, repository_id, snapshot_id)
    with storage.pin_reader(repository_id, snap.id):
        try:
            root = load_entity(storage, repository_id, snap.id, root_id)
        except NotFoundError:
            raise NotFoundError("root entity not found in snapshot") from None

        by_id = {e.id: e for e in load_entities(storage, repository_id, snap.id)}
        edges = _load_snapshot_edges(
            storage,
            repository_id=repository_id,
            snapshot_id=snap.id,
            allowed_types=None if view == "flow" else allowed,
        )

        flow = view == "flow" and root.type not in (
            EntityType.DIRECTORY,
            EntityType.SOURCE_UNIT,
            EntityType.NAMESPACE,
        )
        upstream = root.type in (
            EntityType.DATA_RESOURCE,
            EntityType.MESSAGE_CHANNEL,
            EntityType.CONFIGURATION,
            EntityType.EXTERNAL_DEPENDENCY,
        )
        # UI navigation Endpoint (OQ-RKG-007): open depends_on for config/external
        # call chains. HTTP API Endpoints keep prior defaults (reads/writes only
        # unless include_dependencies is set).
        root_attrs = dict(root.attributes)
        navigation_root = root.type == EntityType.ENDPOINT and (
            root_attrs.get("kind") == "navigation"
            or root.framework_kind == "react-router"
        )

        def neighbors(node_id: str) -> list[tuple[Edge, str]]:
            if not flow:
                return [
                    (edge, other)
                    for edge, other in _neighbors(edges, node_id, direction)
                    if allowed is None or edge.type.value in allowed
                ]
            node = by_id[node_id]
            # Navigation UI→API: page SourceUnit (Nuxt pages) may carry depends_on
            # to composables; expand it like a Callable. HTTP API roots unchanged.
            expandable = node.type == EntityType.CALLABLE or (
                navigation_root and node.type == EntityType.SOURCE_UNIT
            )
            if node_id != root.id and not expandable:
                return []
            kinds = {EdgeType.CALLS, EdgeType.HANDLED_BY}
            if not upstream or node_id == root.id:
                kinds.update(
                    {
                        EdgeType.READS,
                        EdgeType.WRITES,
                        EdgeType.PUBLISHES,
                        EdgeType.CONSUMES,
                    }
                )
            if (
                include_dependencies
                or (upstream and node_id == root.id)
                or navigation_root
            ):
                kinds.add(EdgeType.DEPENDS_ON)
            if node_id == root.id and root.type == EntityType.TYPE:
                kinds.update({EdgeType.CONTAINS, EdgeType.MAPS_TO})
            return [
                (edge, other)
                for edge, other in _neighbors(
                    edges, node_id, "incoming" if upstream else "outgoing"
                )
                if edge.type in kinds
                and (allowed is None or edge.type.value in allowed)
                and other in by_id
                and (
                    edge.type != EdgeType.CONTAINS
                    or by_id[other].type == EntityType.CALLABLE
                )
            ]

        nodes: dict[str, Entity] = {root.id: root}
        selected_edges: dict[str, Edge] = {}
        reasons: set[str] = set()
        frontier = [root.id]
        stop = False

        for _layer in range(depth):
            if stop or not frontier:
                break
            next_frontier: list[str] = []
            seen_next: set[str] = set()
            for node_id in frontier:
                if stop:
                    break
                for edge, other in neighbors(node_id):
                    if edge.id in selected_edges:
                        continue
                    if len(selected_edges) >= max_edges:
                        reasons.add(TRUNC_EDGES)
                        stop = True
                        break

                    other_is_repo = other == repository_id
                    if not other_is_repo and other not in by_id:
                        continue

                    if other_is_repo:
                        selected_edges[edge.id] = edge
                        continue

                    if other not in nodes and len(nodes) >= max_nodes:
                        reasons.add(TRUNC_NODES)
                        stop = True
                        break

                    selected_edges[edge.id] = edge
                    if other not in nodes:
                        nodes[other] = by_id[other]
                        if other not in seen_next:
                            next_frontier.append(other)
                            seen_next.add(other)
            frontier = next_frontier

        # Depth truncation: frontier still has expandable neighbors.
        if not stop and frontier:
            for node_id in frontier:
                for edge, other in neighbors(node_id):
                    if edge.id in selected_edges:
                        continue
                    if other == repository_id or other in by_id:
                        reasons.add(TRUNC_DEPTH)
                        break
                if TRUNC_DEPTH in reasons:
                    break

        if flow and include_structure:
            # Ownership is an overlay: parents never expand semantic neighbors.
            pending = list(sorted(nodes))
            visited: set[str] = set()
            while pending:
                child = pending.pop(0)
                if child in visited:
                    continue
                visited.add(child)
                for edge, parent in _neighbors(edges, child, "incoming"):
                    if edge.type != EdgeType.CONTAINS or parent not in by_id:
                        continue
                    if edge.id in selected_edges:
                        continue
                    if len(selected_edges) >= max_edges:
                        reasons.add(TRUNC_EDGES)
                        continue
                    if parent not in nodes and len(nodes) >= max_nodes:
                        reasons.add(TRUNC_NODES)
                        continue
                    nodes[parent] = by_id[parent]
                    selected_edges[edge.id] = edge
                    pending.append(parent)

        # Cycles: revisiting via another path must not duplicate nodes/edges.
        ordered_nodes = tuple(
            sorted(nodes.values(), key=lambda n: (n.type.value, n.qualified_name, n.id))
        )
        ordered_edges = tuple(
            sorted(
                selected_edges.values(),
                key=lambda e: (e.type.value, e.source_id, e.target_id, e.id),
            )
        )
        valid_edges = tuple(
            e
            for e in ordered_edges
            if (e.source_id == repository_id or e.source_id in nodes)
            and (e.target_id == repository_id or e.target_id in nodes)
        )

        return SubgraphResult(
            repository_id=repository_id,
            snapshot_id=snap.id,
            root_id=root.id,
            nodes=ordered_nodes,
            edges=valid_edges,
            truncated=bool(reasons),
            truncation_reasons=tuple(sorted(reasons)),
            depth=depth,
            max_nodes=max_nodes,
            max_edges=max_edges,
        )
