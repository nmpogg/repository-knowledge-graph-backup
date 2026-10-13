"""Kùzu storage façade — repository/snapshot/job/conversation persistence.

Handoff for T-015 (index job / CLI):
- Open with ``Storage(path)`` or ``open_storage(path)``; migrate-on-open applies
  ``DDL-RKG-GRAPH`` + ``SchemaMeta`` without dropping an existing user DB.
- Call ``rkg.domain.validate_fact_batch`` indirectly via
  ``rkg.graph.publish_fact_batch`` before atomic publication.
- Successful publish auto-activates ``Repository.active_snapshot_id``.
- Pin readers with ``storage.pin_reader(repository_id, snapshot_id)`` for the
  duration of a graph read request (in-process registry; single worker).
- Delete guards raise ``StorageError`` subclasses whose ``.code`` matches
  API-RKG-CORE-v1 (``snapshot_active``, ``snapshot_in_use``, ``repository_busy``,
  ``repository_in_use``, ``repository_conflict``, ``not_found``).
- Ownership mismatch on snapshot routes raises ``NotFoundError`` (HTTP 404) and
  must not reveal cross-repository ownership.
"""

from rkg.storage.connection import Storage, open_storage
from rkg.storage.errors import (
    ConflictError,
    ConversationBusyError,
    ConversationConflictError,
    InvalidTurnRequestError,
    NotFoundError,
    RepositoryBusyError,
    RepositoryConflictError,
    RepositoryInUseError,
    RepositorySourceImmutableError,
    SnapshotActiveError,
    SnapshotInUseError,
    StorageError,
)
from rkg.storage.migrate import (
    CURRENT_SCHEMA_VERSION,
    PREVIOUS_DDL_V0,
    migrate,
    read_schema_version,
)
from rkg.storage.readers import ReaderPin, ReaderRegistry, pinned_reader
from rkg.storage.records import (
    ConversationRecord,
    JobRecord,
    Page,
    RepositoryRecord,
    SnapshotRecord,
    TurnRecord,
)
from rkg.storage.repositories import redact_local_locator, source_identity_hash

__all__ = [
    "CURRENT_SCHEMA_VERSION",
    "ConflictError",
    "ConversationBusyError",
    "ConversationConflictError",
    "ConversationRecord",
    "InvalidTurnRequestError",
    "JobRecord",
    "NotFoundError",
    "PREVIOUS_DDL_V0",
    "Page",
    "ReaderPin",
    "ReaderRegistry",
    "RepositoryBusyError",
    "RepositoryConflictError",
    "RepositoryInUseError",
    "RepositoryRecord",
    "RepositorySourceImmutableError",
    "SnapshotActiveError",
    "SnapshotInUseError",
    "SnapshotRecord",
    "Storage",
    "StorageError",
    "TurnRecord",
    "migrate",
    "open_storage",
    "pinned_reader",
    "read_schema_version",
    "redact_local_locator",
    "source_identity_hash",
]
