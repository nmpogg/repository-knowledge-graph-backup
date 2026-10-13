"""Graph read errors with API-aligned codes (no HTTP binding here)."""

from __future__ import annotations

from rkg.storage.errors import ConflictError, NotFoundError, StorageError

__all__ = [
    "ConflictError",
    "GraphReadError",
    "InvalidBudgetError",
    "NoActiveSnapshotError",
    "NotFoundError",
    "SnapshotUnavailableError",
    "StorageError",
]


class GraphReadError(StorageError):
    """Base failure for search/traversal/context reads."""

    code = "graph_read_error"


class NoActiveSnapshotError(ConflictError):
    """Repository has never published / has no active snapshot — HTTP 409."""

    code = "no_active_snapshot"


class SnapshotUnavailableError(StorageError):
    """Snapshot metadata known but graph payload unusable — HTTP 410."""

    code = "snapshot_unavailable"


class InvalidBudgetError(GraphReadError):
    """Out-of-range depth/nodes/edges/chars — HTTP 422."""

    code = "invalid_budget"
