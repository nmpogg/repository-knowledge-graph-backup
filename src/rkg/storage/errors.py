"""Storage-layer errors with API-aligned codes (no HTTP binding here)."""

from __future__ import annotations


class StorageError(Exception):
    """Base storage failure; subclasses carry stable contract codes."""

    code: str = "storage_error"

    def __init__(self, message: str = "") -> None:
        super().__init__(message or self.code)
        self.message = message or self.code


class NotFoundError(StorageError):
    """Missing resource or ownership mismatch — callers map to HTTP 404."""

    code = "not_found"


class ConflictError(StorageError):
    """Guarded mutation rejected — callers map to HTTP 409/422 by code."""


class RepositoryConflictError(ConflictError):
    code = "repository_conflict"


class RepositoryBusyError(ConflictError):
    code = "repository_busy"


class RepositoryInUseError(ConflictError):
    code = "repository_in_use"


class SnapshotActiveError(ConflictError):
    code = "snapshot_active"


class SnapshotInUseError(ConflictError):
    code = "snapshot_in_use"


class RepositorySourceImmutableError(ConflictError):
    code = "repository_source_immutable"


class ConversationConflictError(ConflictError):
    """Idempotency or revision clash — callers map to HTTP 409."""

    code = "conversation_conflict"


class ConversationBusyError(ConflictError):
    """A pending turn still owns the conversation — HTTP 409."""

    code = "conversation_busy"


class InvalidTurnRequestError(StorageError):
    """Missing or malformed turn identity/revision — HTTP 422."""

    code = "invalid_turn_request"
