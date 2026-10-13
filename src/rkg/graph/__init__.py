"""Graph publication, snapshot lifecycle, and read services (CMP-RKG-GRAPH).

Handoff for T-015:
- ``publish_fact_batch(storage, batch, meta)`` validates with
  ``validate_fact_batch``, writes Snapshot/Entity/Evidence/Edge/
  ExternalDependency (PK = Entity id) and diagnostics in one transaction, then
  auto-activates the new snapshot.
- ``storage.activate_snapshot`` / ``storage.delete_snapshot`` apply ownership and
  reference guards; failed publish leaves the previous active pointer unchanged.

Handoff for T-016 / T-018:
- ``search_entities`` / ``get_entity`` — deterministic search + detail.
- ``traverse_subgraph`` — BFS with direction/edge filters, budgets, cycles.
- ``build_context`` — bounded ContextPackage + safe ``max_chars`` truncation.
- Guard errors: ``NoActiveSnapshotError`` (409), ``SnapshotUnavailableError``
  (410), ``NotFoundError`` (404), ``InvalidBudgetError`` (422).
"""

from rkg.graph.context import CONTEXT_SCHEMA_VERSION, build_context
from rkg.graph.errors import (
    InvalidBudgetError,
    NoActiveSnapshotError,
    SnapshotUnavailableError,
)
from rkg.graph.ids import logical_entity_id, physical_entity_id
from rkg.graph.publish import (
    SnapshotPublishMeta,
    count_entities,
    edge_exists,
    entity_qualified_names,
    publish_fact_batch,
)
from rkg.graph.search import entity_matches_query, get_entity, search_entities
from rkg.graph.traversal import SubgraphResult, traverse_subgraph
from rkg.storage.errors import NotFoundError
from rkg.storage.snapshots import activate_snapshot, delete_snapshot

__all__ = [
    "CONTEXT_SCHEMA_VERSION",
    "InvalidBudgetError",
    "NoActiveSnapshotError",
    "NotFoundError",
    "SnapshotPublishMeta",
    "SnapshotUnavailableError",
    "SubgraphResult",
    "activate_snapshot",
    "build_context",
    "count_entities",
    "delete_snapshot",
    "edge_exists",
    "entity_matches_query",
    "entity_qualified_names",
    "get_entity",
    "logical_entity_id",
    "physical_entity_id",
    "publish_fact_batch",
    "search_entities",
    "traverse_subgraph",
]
