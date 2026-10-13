"""Snapshot metadata helpers and guarded graph deletion."""

from __future__ import annotations

from typing import Any

import kuzu

from rkg.storage._util import dumps_json, fetch_all, fetch_one, loads_json
from rkg.storage.errors import (
    NotFoundError,
    SnapshotActiveError,
    SnapshotInUseError,
)
from rkg.storage.readers import ReaderRegistry
from rkg.storage.records import Page, SnapshotRecord
from rkg.storage.repositories import get_repository, set_active_snapshot

_SNAP_RETURN = (
    "s.id, s.repository_id, s.source_revision, s.manifest_hash, "
    "s.scan_config_digest, s.analyzer_version, s.schema_version, "
    "s.adapter_versions_json, s.status, s.created_at"
)


def _row_to_snapshot(row: list[Any], *, active_id: str | None) -> SnapshotRecord:
    (
        snap_id,
        repository_id,
        source_revision,
        manifest_hash,
        scan_config_digest,
        analyzer_version,
        schema_version,
        adapter_versions_json,
        status,
        created_at,
    ) = row
    return SnapshotRecord(
        id=snap_id,
        repository_id=repository_id,
        source_revision=source_revision,
        manifest_hash=manifest_hash,
        scan_config_digest=scan_config_digest,
        analyzer_version=analyzer_version,
        schema_version=schema_version,
        adapter_versions=loads_json(adapter_versions_json, default={}) or {},
        status=status,
        created_at=created_at,
        is_active=active_id is not None and snap_id == active_id,
    )


def get_snapshot(
    conn: kuzu.Connection, repository_id: str, snapshot_id: str
) -> SnapshotRecord:
    """Ownership-aware get: mismatch and missing both raise NotFoundError."""
    repo = get_repository(conn, repository_id)
    row = fetch_one(
        conn,
        f"MATCH (s:Snapshot {{id: $sid}}) RETURN {_SNAP_RETURN}",
        {"sid": snapshot_id},
    )
    if row is None or row[1] != repository_id:
        raise NotFoundError("snapshot not found")
    return _row_to_snapshot(row, active_id=repo.active_snapshot_id)


def list_snapshots(
    conn: kuzu.Connection,
    repository_id: str,
    *,
    offset: int = 0,
    limit: int = 20,
) -> Page:
    get_repository(conn, repository_id)
    if offset < 0 or limit < 1:
        raise ValueError("offset/limit out of range")
    limit = min(limit, 100)
    repo = get_repository(conn, repository_id)
    total_row = fetch_one(
        conn,
        "MATCH (s:Snapshot {repository_id: $rid}) RETURN count(s)",
        {"rid": repository_id},
    )
    items = fetch_all(
        conn,
        f"MATCH (s:Snapshot {{repository_id: $rid}}) RETURN {_SNAP_RETURN} "
        f"ORDER BY s.created_at DESC, s.id ASC SKIP $o LIMIT $l",
        {"rid": repository_id, "o": offset, "l": limit},
    )
    return Page(
        items=tuple(
            _row_to_snapshot(row, active_id=repo.active_snapshot_id) for row in items
        ),
        offset=offset,
        limit=limit,
        total=int(total_row[0]) if total_row else 0,
    )


def insert_snapshot_row(
    conn: kuzu.Connection,
    *,
    snapshot_id: str,
    repository_id: str,
    source_revision: str,
    manifest_hash: str,
    scan_config_digest: str,
    analyzer_version: str,
    schema_version: str,
    adapter_versions: dict[str, str],
    status: str = "ready",
    created_at_iso: str,
) -> None:
    conn.execute(
        "CREATE (s:Snapshot {"
        "id: $id, repository_id: $rid, source_revision: $rev, "
        "manifest_hash: $mhash, scan_config_digest: $digest, "
        "analyzer_version: $aver, schema_version: $sver, "
        "adapter_versions_json: $adapters, status: $status, "
        "created_at: timestamp($ts)})",
        {
            "id": snapshot_id,
            "rid": repository_id,
            "rev": source_revision,
            "mhash": manifest_hash,
            "digest": scan_config_digest,
            "aver": analyzer_version,
            "sver": schema_version,
            "adapters": dumps_json(adapter_versions),
            "status": status,
            "ts": created_at_iso,
        },
    )


def _has_conversations_for_snapshot(
    conn: kuzu.Connection, snapshot_id: str
) -> bool:
    row = fetch_one(
        conn,
        "MATCH (c:Conversation {snapshot_id: $sid}) RETURN count(c)",
        {"sid": snapshot_id},
    )
    return bool(row and int(row[0]) > 0)


def delete_snapshot_graph(conn: kuzu.Connection, snapshot_id: str) -> None:
    conn.execute(
        "MATCH (e:Entity {snapshot_id: $sid}) DETACH DELETE e", {"sid": snapshot_id}
    )
    conn.execute(
        "MATCH (e:Evidence {snapshot_id: $sid}) DELETE e", {"sid": snapshot_id}
    )
    conn.execute(
        "MATCH (d:Diagnostic) WHERE d.snapshot_id = $sid DELETE d",
        {"sid": snapshot_id},
    )
    conn.execute(
        "MATCH (x:ExternalDependency {snapshot_id: $sid}) DELETE x",
        {"sid": snapshot_id},
    )
    conn.execute(
        "MATCH (t:TechnologyDetection {snapshot_id: $sid}) DELETE t",
        {"sid": snapshot_id},
    )


def delete_snapshot(
    conn: kuzu.Connection,
    repository_id: str,
    snapshot_id: str,
    *,
    readers: ReaderRegistry,
) -> None:
    snap = get_snapshot(conn, repository_id, snapshot_id)
    if snap.is_active:
        raise SnapshotActiveError("cannot delete the active snapshot")
    if readers.has_snapshot_readers(snapshot_id) or _has_conversations_for_snapshot(
        conn, snapshot_id
    ):
        raise SnapshotInUseError("snapshot has active readers or conversations")

    conn.execute("BEGIN TRANSACTION")
    try:
        delete_snapshot_graph(conn, snapshot_id)
        conn.execute("MATCH (s:Snapshot {id: $id}) DELETE s", {"id": snapshot_id})
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise


def cleanup_unreferenced_snapshots(
    conn: kuzu.Connection,
    repository_id: str,
    *,
    readers: ReaderRegistry,
) -> tuple[str, ...]:
    """Delete snapshots that fail no retention guard.

    Active, reader-pinned and conversation-referenced snapshots stay. Guards
    skip that snapshot instead of aborting the rest of the cleanup.
    """
    get_repository(conn, repository_id)
    ids: list[str] = []
    offset = 0
    while True:
        page = list_snapshots(conn, repository_id, offset=offset, limit=100)
        ids.extend(item.id for item in page.items)
        offset += len(page.items)
        if offset >= page.total or not page.items:
            break
    deleted: list[str] = []
    for snapshot_id in ids:
        try:
            delete_snapshot(conn, repository_id, snapshot_id, readers=readers)
        except (SnapshotActiveError, SnapshotInUseError):
            continue
        deleted.append(snapshot_id)
    return tuple(deleted)


def activate_snapshot(
    conn: kuzu.Connection, repository_id: str, snapshot_id: str
) -> None:
    """Atomically point repository.active_snapshot_id at an owned snapshot."""
    get_snapshot(conn, repository_id, snapshot_id)
    set_active_snapshot(conn, repository_id, snapshot_id)
