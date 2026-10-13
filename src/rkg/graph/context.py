"""Bounded context assembly with safe truncation (AC-RKG-010 / AC-RKG-060)."""

from __future__ import annotations

from collections.abc import Callable

from rkg.domain.context import context_json
from rkg.domain.models import ContextBudget, ContextPackage, Edge, Entity, Evidence
from rkg.graph.access import diagnostic_summary, load_evidence_by_ids
from rkg.graph.errors import InvalidBudgetError
from rkg.graph.traversal import (
    TRUNC_DEPTH,
    TRUNC_EDGES,
    TRUNC_NODES,
    Direction,
    traverse_subgraph,
)
from rkg.storage.connection import Storage

CONTEXT_SCHEMA_VERSION = "v1"
TRUNC_CHARS = "max_chars"


def build_context(
    storage: Storage,
    repository_id: str,
    snapshot_id: str | None,
    root_id: str,
    *,
    direction: Direction = "outgoing",
    edge_types: tuple[str, ...] | list[str] | None = None,
    depth: int = 4,
    max_nodes: int = 50,
    max_edges: int = 100,
    max_chars: int = 20000,
    view: str = "neighborhood",
    include_structure: bool = False,
    include_dependencies: bool = False,
) -> ContextPackage:
    """Assemble a deterministic ContextPackage; never includes raw source/secrets."""
    try:
        budget = ContextBudget(depth, max_nodes, max_edges, max_chars)
    except ValueError as exc:
        raise InvalidBudgetError(str(exc)) from exc

    graph = traverse_subgraph(
        storage,
        repository_id,
        snapshot_id,
        root_id,
        direction=direction,
        edge_types=edge_types,
        depth=budget.depth,
        max_nodes=budget.max_nodes,
        max_edges=budget.max_edges,
        view=view,
        include_structure=include_structure,
        include_dependencies=include_dependencies,
    )

    evidence_ids: set[str] = set()
    for edge in graph.edges:
        evidence_ids.update(edge.evidence_ids)
    evidence = tuple(load_evidence_by_ids(storage, graph.snapshot_id, evidence_ids))
    summary = diagnostic_summary(storage, graph.snapshot_id)

    package = ContextPackage(
        schema_version=CONTEXT_SCHEMA_VERSION,
        repository_id=graph.repository_id,
        snapshot_id=graph.snapshot_id,
        root_id=graph.root_id,
        nodes=graph.nodes,
        edges=graph.edges,
        evidence=evidence,
        diagnostic_summary=summary,
        truncated=graph.truncated,
        truncation_reasons=graph.truncation_reasons,
        budget=budget,
    )
    return _apply_char_budget(package)


def _apply_char_budget(package: ContextPackage) -> ContextPackage:
    rendered = context_json(package)
    if len(rendered) <= package.budget.max_chars:
        return package

    nodes = list(package.nodes)
    edges = list(package.edges)
    evidence = list(package.evidence)
    reasons = set(package.truncation_reasons)
    reasons.add(TRUNC_CHARS)

    def fits(candidate: tuple[list[Entity], list[Edge], list[Evidence]]) -> bool:
        return (
            len(context_json(_rebuild(package, *candidate, reasons)))
            <= package.budget.max_chars
        )

    def smallest_fit[T](
        count: int, candidate: Callable[[int], T], accepts: Callable[[T], bool]
    ) -> T:
        # Each prefix removes more data, so a binary search keeps the exact
        # first fitting prefix without re-rendering every intermediate graph.
        empty = candidate(0)
        if accepts(empty) or count == 0:
            return empty
        largest = candidate(count)
        if not accepts(largest):
            return largest
        low, high = 1, count
        while low < high:
            middle = (low + high) // 2
            if accepts(candidate(middle)):
                high = middle
            else:
                low = middle + 1
        return candidate(low)

    # Drop nodes first (stable reverse order: type, qualified_name, id), keep root.
    removable = sorted(
        (n for n in nodes if n.id != package.root_id),
        key=lambda n: (n.type.value, n.qualified_name, n.id),
        reverse=True,
    )

    def without_nodes(count: int) -> tuple[list[Entity], list[Edge], list[Evidence]]:
        removed = {node.id for node in removable[:count]}
        remaining_nodes = [node for node in nodes if node.id not in removed]
        node_ids = {node.id for node in remaining_nodes}
        remaining_edges = [
            edge
            for edge in edges
            if (edge.source_id == package.repository_id or edge.source_id in node_ids)
            and (edge.target_id == package.repository_id or edge.target_id in node_ids)
        ]
        keep_evidence = {
            evidence_id for edge in remaining_edges for evidence_id in edge.evidence_ids
        }
        remaining_evidence = [item for item in evidence if item.id in keep_evidence]
        return remaining_nodes, remaining_edges, remaining_evidence

    nodes, edges, evidence = smallest_fit(len(removable), without_nodes, fits)

    # If still over budget, strip evidence then edges farthest from integrity rules.
    if not fits((nodes, edges, evidence)):
        retained = smallest_fit(
            len(evidence),
            lambda count: evidence[: len(evidence) - count],
            lambda items: fits((nodes, edges, items)),
        )
        evidence = retained

    if not fits((nodes, edges, evidence)):

        def without_edges(count: int) -> tuple[list[Edge], list[Evidence]]:
            remaining_edges = edges[: len(edges) - count]
            keep_evidence = {
                evidence_id
                for edge in remaining_edges
                for evidence_id in edge.evidence_ids
            }
            remaining_evidence = [item for item in evidence if item.id in keep_evidence]
            return remaining_edges, remaining_evidence

        edges, evidence = smallest_fit(
            len(edges),
            without_edges,
            lambda pair: fits((nodes, *pair)),
        )

    return _rebuild(package, nodes, edges, evidence, reasons)


def _rebuild(
    base: ContextPackage,
    nodes: list[Entity],
    edges: list[Edge],
    evidence: list[Evidence],
    reasons: set[str],
) -> ContextPackage:
    return ContextPackage(
        schema_version=base.schema_version,
        repository_id=base.repository_id,
        snapshot_id=base.snapshot_id,
        root_id=base.root_id,
        nodes=tuple(
            sorted(nodes, key=lambda n: (n.type.value, n.qualified_name, n.id))
        ),
        edges=tuple(
            sorted(edges, key=lambda e: (e.type.value, e.source_id, e.target_id, e.id))
        ),
        evidence=tuple(
            sorted(evidence, key=lambda e: (e.file_path, e.start_line, e.id))
        ),
        diagnostic_summary=base.diagnostic_summary,
        truncated=bool(reasons),
        truncation_reasons=tuple(sorted(reasons)),
        budget=base.budget,
    )


# Re-export truncation reason constants for tests/docs.
__all__ = [
    "CONTEXT_SCHEMA_VERSION",
    "TRUNC_CHARS",
    "TRUNC_DEPTH",
    "TRUNC_EDGES",
    "TRUNC_NODES",
    "build_context",
]
