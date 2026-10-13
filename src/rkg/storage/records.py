"""Immutable storage DTOs (not HTTP response models)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class RepositoryRecord:
    id: str
    revision: int
    display_name: str
    source_type: str
    source_locator: str
    source_identity_hash: str
    source_locator_redacted: str
    source_root: str | None
    app_module: str | None
    app_symbol: str | None
    scan_defaults: dict[str, Any] | None
    active_snapshot_id: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class SnapshotRecord:
    id: str
    repository_id: str
    source_revision: str
    manifest_hash: str
    scan_config_digest: str
    analyzer_version: str
    schema_version: str
    adapter_versions: dict[str, str]
    status: str
    created_at: datetime
    is_active: bool = False


@dataclass(frozen=True, slots=True)
class JobRecord:
    id: str
    repository_id: str
    status: str
    stage: str
    source_type: str | None
    manifest_hash: str | None
    report: dict[str, Any] | None
    error_code: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class ConversationRecord:
    id: str
    repository_id: str
    snapshot_id: str
    title: str
    revision: int
    state: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class TurnRecord:
    id: str
    conversation_id: str
    sequence: int
    client_request_id: str
    request_hash: str
    question: str
    resolved_question: str | None
    status: str
    answer: str | None
    claims: list[Any] | None
    citations: list[Any] | None
    context_turn_ids: tuple[str, ...]
    usage: dict[str, Any] | None
    error_code: str | None
    created_at: datetime
    updated_at: datetime
    response_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class Page:
    items: tuple[object, ...]
    offset: int
    limit: int
    total: int
