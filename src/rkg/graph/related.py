"""Complete question-directed context, without traversal or size ceilings."""

from collections import defaultdict, deque

from rkg.domain.models import ContextBudget, ContextPackage, EdgeType, EntityType
from rkg.graph.access import (
    diagnostic_summary,
    load_entities,
    load_entity,
    load_evidence_by_ids,
    require_readable_snapshot,
)
from rkg.graph.observation import observe_context
from rkg.graph.traversal import Direction, _load_snapshot_edges
from rkg.storage.connection import Storage

_BEHAVIOR = {"calls", "reads", "writes", "publishes", "consumes", "depends_on"}


def build_related_context(
    storage: Storage,
    repository_id: str,
    snapshot_id: str,
    root_id: str,
    *,
    direction: Direction = "outgoing",
    edge_types: tuple[str, ...] | None = None,
) -> ContextPackage:
    """Follow call chains and requested relations, never expand terminal resources.

    Incoming queries follow the requested relation first, then its callers.
    Outgoing queries follow calls before the requested relation. Endpoints seed
    their handlers without turning retrieval into an undirected component scan.
    """
    if direction not in {"incoming", "outgoing"}:
        raise ValueError("direction must be incoming|outgoing")
    snap = require_readable_snapshot(storage, repository_id, snapshot_id)
    with storage.pin_reader(repository_id, snap.id):
        root = load_entity(storage, repository_id, snap.id, root_id)
        entities = {n.id: n for n in load_entities(storage, repository_id, snap.id)}
        requested = (
            set(edge_types)
            if edge_types is not None
            else {kind.value for kind in EdgeType}
        )
        allowed = requested | ({"calls"} if requested & _BEHAVIOR else set())
        if root.type == EntityType.ENDPOINT:
            allowed.add("handled_by")
        loaded = _load_snapshot_edges(
            storage,
            repository_id=repository_id,
            snapshot_id=snap.id,
            allowed_types=frozenset(allowed),
        )
        adjacency = defaultdict(list)
        connectors = []
        for item in loaded:
            edge = item.edge
            if (
                edge.source_id not in entities and edge.source_id != repository_id
            ) or edge.target_id not in entities:
                continue
            if edge.type.value == "handled_by" and edge.source_id == root.id:
                connectors.append(edge)
            start, end = (
                (edge.source_id, edge.target_id)
                if direction == "outgoing"
                else (edge.target_id, edge.source_id)
            )
            adjacency[start].append((edge, end))

        selected = {}
        queue = deque([(root.id, False)])
        if root.type == EntityType.ENDPOINT and requested - {
            "handled_by",
            "depends_on",
        }:
            for edge in connectors:
                selected[edge.id] = edge
                queue.append((edge.target_id, False))
        visited = set()
        while queue:
            current, started = queue.popleft()
            if (current, started) in visited:
                continue
            visited.add((current, started))
            for edge, end in adjacency[current]:
                kind = edge.type.value
                if current == root.id and root.type == EntityType.ENDPOINT:
                    if kind not in requested & {"handled_by", "depends_on"}:
                        continue
                elif direction == "incoming":
                    if kind not in ({"calls"} if started else requested):
                        continue
                elif kind not in allowed - {"handled_by"}:
                    continue
                selected[edge.id] = edge
                if end == repository_id:
                    continue
                if direction == "incoming" and requested & _BEHAVIOR:
                    queue.append((end, True))
                elif direction == "outgoing" and kind == "calls":
                    queue.append((end, True))
                elif kind in {"contains", "imports", "inherits_from"}:
                    queue.append((end, True))

        # For a specific non-call question, discard call branches that never
        # reach a requested relation. Keep all converging paths and cycles on
        # branches that do lead to supporting facts.
        if direction == "outgoing" and "calls" not in requested:
            useful = {
                e.source_id for e in selected.values() if e.type.value in requested
            }
            reverse_calls = defaultdict(list)
            for edge in selected.values():
                if edge.type.value == "calls":
                    reverse_calls[edge.target_id].append(edge.source_id)
            pending = deque(useful)
            while pending:
                for parent in reverse_calls[pending.popleft()]:
                    if parent not in useful:
                        useful.add(parent)
                        pending.append(parent)
            selected = {
                key: edge
                for key, edge in selected.items()
                if edge.type.value in requested
                or edge.type.value == "calls"
                and edge.target_id in useful
                or edge.type.value == "handled_by"
                and edge.target_id in useful
            }
        node_ids = {root.id}
        evidence_ids = set()
        for edge in selected.values():
            node_ids.update((edge.source_id, edge.target_id))
            evidence_ids.update(edge.evidence_ids)
        context = ContextPackage(
            schema_version="v1",
            repository_id=repository_id,
            snapshot_id=snap.id,
            root_id=root.id,
            nodes=tuple(
                sorted(
                    (entities[i] for i in node_ids if i != repository_id),
                    key=lambda n: (n.type.value, n.qualified_name, n.id),
                )
            ),
            edges=tuple(
                sorted(
                    selected.values(),
                    key=lambda e: (e.type.value, e.source_id, e.target_id, e.id),
                )
            ),
            evidence=tuple(load_evidence_by_ids(storage, snap.id, evidence_ids)),
            diagnostic_summary=diagnostic_summary(storage, snap.id),
            budget=ContextBudget(None, None, None, None),
        )

        observe_context(context)
        return context
