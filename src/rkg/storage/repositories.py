"""Repository catalog persistence with optimistic revision and delete guards."""

from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

import kuzu

from rkg.storage._util import dumps_json, fetch_all, fetch_one, loads_json, ts_param
from rkg.storage.errors import (
    NotFoundError,
    RepositoryBusyError,
    RepositoryConflictError,
    RepositoryInUseError,
    RepositorySourceImmutableError,
)
from rkg.storage.readers import ReaderRegistry
from rkg.storage.records import Page, RepositoryRecord


def _row_to_repository(row: list[Any]) -> RepositoryRecord:
    (
        repo_id,
        revision,
        display_name,
        source_type,
        source_locator,
        source_identity_hash,
        source_locator_redacted,
        source_root,
        app_module,
        app_symbol,
        scan_defaults_json,
        active_snapshot_id,
        created_at,
        updated_at,
    ) = row
    return RepositoryRecord(
        id=repo_id,
        revision=int(revision),
        display_name=display_name,
        source_type=source_type,
        source_locator=source_locator,
        source_identity_hash=source_identity_hash,
        source_locator_redacted=source_locator_redacted,
        source_root=source_root,
        app_module=app_module,
        app_symbol=app_symbol,
        scan_defaults=loads_json(scan_defaults_json, default=None),
        active_snapshot_id=active_snapshot_id,
        created_at=created_at,
        updated_at=updated_at,
    )


_REPO_RETURN = (
    "r.id, r.revision, r.display_name, r.source_type, r.source_locator, "
    "r.source_identity_hash, r.source_locator_redacted, r.source_root, "
    "r.app_module, r.app_symbol, r.scan_defaults_json, r.active_snapshot_id, "
    "r.created_at, r.updated_at"
)


def source_identity_hash(source_type: str, source_locator: str) -> str:
    payload = json.dumps(
        [source_type, source_locator], ensure_ascii=False, separators=(",", ":")
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def redact_local_locator(path: str) -> str:
    """Return a non-absolute redacted display form; never log the raw locator."""
    normalized = path.replace("\\", "/").rstrip("/")
    name = normalized.rsplit("/", 1)[-1] or "repository"
    return f"local:…/{name}"


def create_repository(
    conn: kuzu.Connection,
    *,
    display_name: str,
    source_type: str,
    source_locator: str,
    source_locator_redacted: str | None = None,
    source_root: str | None = None,
    app_module: str | None = None,
    app_symbol: str | None = None,
    scan_defaults: dict[str, Any] | None = None,
    repository_id: str | None = None,
) -> RepositoryRecord:
    if not display_name or not source_type or not source_locator:
        raise ValueError("display_name, source_type and source_locator are required")
    identity = source_identity_hash(source_type, source_locator)
    dup = fetch_one(
        conn,
        "MATCH (r:Repository {source_identity_hash: $hash}) RETURN r.id",
        {"hash": identity},
    )
    if dup is not None:
        raise RepositoryConflictError("repository source identity already registered")
    repo_id = repository_id or f"repo_{uuid.uuid4().hex}"
    now = ts_param()
    conn.execute(
        "CREATE (r:Repository {"
        "id: $id, revision: 1, display_name: $name, source_type: $stype, "
        "source_locator: $locator, source_identity_hash: $hash, "
        "source_locator_redacted: $redacted, source_root: $root, "
        "app_module: $module, app_symbol: $symbol, "
        "scan_defaults_json: $defaults, active_snapshot_id: null, "
        "created_at: timestamp($ts), updated_at: timestamp($ts)})",
        {
            "id": repo_id,
            "name": display_name,
            "stype": source_type,
            "locator": source_locator,
            "hash": identity,
            "redacted": source_locator_redacted or redact_local_locator(source_locator),
            "root": source_root,
            "module": app_module,
            "symbol": app_symbol,
            "defaults": (
                dumps_json(scan_defaults) if scan_defaults is not None else None
            ),
            "ts": now,
        },
    )
    return get_repository(conn, repo_id)


def get_repository(conn: kuzu.Connection, repository_id: str) -> RepositoryRecord:
    row = fetch_one(
        conn,
        f"MATCH (r:Repository {{id: $id}}) RETURN {_REPO_RETURN}",
        {"id": repository_id},
    )
    if row is None:
        raise NotFoundError("repository not found")
    return _row_to_repository(row)


def list_repositories(
    conn: kuzu.Connection,
    *,
    offset: int = 0,
    limit: int = 20,
    q: str | None = None,
) -> Page:
    if offset < 0 or limit < 1:
        raise ValueError("offset/limit out of range")
    limit = min(limit, 100)
    if q:
        total_row = fetch_one(
            conn,
            "MATCH (r:Repository) WHERE contains(lower(r.display_name), lower($q)) "
            "OR contains(lower(r.source_locator_redacted), lower($q)) "
            "RETURN count(r)",
            {"q": q},
        )
        items = fetch_all(
            conn,
            f"MATCH (r:Repository) WHERE contains(lower(r.display_name), lower($q)) "
            f"OR contains(lower(r.source_locator_redacted), lower($q)) "
            f"RETURN {_REPO_RETURN} "
            f"ORDER BY r.updated_at DESC, r.id ASC SKIP $o LIMIT $l",
            {"q": q, "o": offset, "l": limit},
        )
    else:
        total_row = fetch_one(conn, "MATCH (r:Repository) RETURN count(r)")
        items = fetch_all(
            conn,
            f"MATCH (r:Repository) RETURN {_REPO_RETURN} "
            f"ORDER BY r.updated_at DESC, r.id ASC SKIP $o LIMIT $l",
            {"o": offset, "l": limit},
        )
    total = int(total_row[0]) if total_row else 0
    return Page(
        items=tuple(_row_to_repository(row) for row in items),
        offset=offset,
        limit=limit,
        total=total,
    )


_UNSET = object()


def update_repository(
    conn: kuzu.Connection,
    repository_id: str,
    *,
    expected_revision: int,
    display_name: str | None = None,
    source_root: Any = _UNSET,
    app_module: Any = _UNSET,
    app_symbol: Any = _UNSET,
    scan_defaults: Any = _UNSET,
    source_type: str | None = None,
    source_locator: str | None = None,
) -> RepositoryRecord:
    """Optimistic PATCH. Pass ``_UNSET`` (default) to leave a field unchanged."""
    if source_type is not None or source_locator is not None:
        raise RepositorySourceImmutableError("source identity is immutable")
    current = get_repository(conn, repository_id)
    if current.revision != expected_revision:
        raise RepositoryConflictError("repository revision conflict")

    new_name = display_name if display_name is not None else current.display_name
    new_root = current.source_root if source_root is _UNSET else source_root
    new_module = current.app_module if app_module is _UNSET else app_module
    new_symbol = current.app_symbol if app_symbol is _UNSET else app_symbol
    if scan_defaults is _UNSET:
        new_defaults = (
            dumps_json(current.scan_defaults)
            if current.scan_defaults is not None
            else None
        )
    else:
        new_defaults = dumps_json(scan_defaults) if scan_defaults is not None else None

    updated = fetch_one(
        conn,
        f"MATCH (r:Repository {{id: $id}}) WHERE r.revision = $expected "
        f"SET r.revision = $expected + 1, r.display_name = $name, "
        f"r.source_root = $root, r.app_module = $module, r.app_symbol = $symbol, "
        f"r.scan_defaults_json = $defaults, r.updated_at = timestamp($ts) "
        f"RETURN {_REPO_RETURN}",
        {
            "id": repository_id,
            "expected": expected_revision,
            "name": new_name,
            "root": new_root,
            "module": new_module,
            "symbol": new_symbol,
            "defaults": new_defaults,
            "ts": ts_param(),
        },
    )
    if updated is None:
        raise RepositoryConflictError("repository revision conflict")
    return _row_to_repository(updated)


def set_active_snapshot(
    conn: kuzu.Connection, repository_id: str, snapshot_id: str | None
) -> RepositoryRecord:
    get_repository(conn, repository_id)
    updated = fetch_one(
        conn,
        f"MATCH (r:Repository {{id: $id}}) "
        f"SET r.active_snapshot_id = $sid, r.updated_at = timestamp($ts) "
        f"RETURN {_REPO_RETURN}",
        {"id": repository_id, "sid": snapshot_id, "ts": ts_param()},
    )
    assert updated is not None
    return _row_to_repository(updated)


def _has_non_terminal_jobs(conn: kuzu.Connection, repository_id: str) -> bool:
    row = fetch_one(
        conn,
        "MATCH (j:Job) WHERE j.repository_id = $rid AND NOT j.stage IN $terms "
        "RETURN count(j)",
        {
            "rid": repository_id,
            "terms": list(
                {"succeeded", "succeeded_with_warnings", "failed"}
            ),
        },
    )
    return bool(row and int(row[0]) > 0)


def _has_conversations_for_repository(
    conn: kuzu.Connection, repository_id: str
) -> bool:
    row = fetch_one(
        conn,
        "MATCH (c:Conversation {repository_id: $rid}) RETURN count(c)",
        {"rid": repository_id},
    )
    return bool(row and int(row[0]) > 0)


def delete_repository(
    conn: kuzu.Connection,
    repository_id: str,
    *,
    readers: ReaderRegistry,
) -> None:
    """Cascade-delete a repository after busy/in-use guards."""
    get_repository(conn, repository_id)
    if _has_non_terminal_jobs(conn, repository_id):
        raise RepositoryBusyError("repository has a non-terminal job")
    if readers.has_repository_readers(
        repository_id
    ) or _has_conversations_for_repository(conn, repository_id):
        raise RepositoryInUseError(
            "repository has active readers or conversations"
        )

    from rkg.storage.snapshots import delete_snapshot_graph

    conn.execute("BEGIN TRANSACTION")
    try:
        snap_ids = [
            row[0]
            for row in fetch_all(
                conn,
                "MATCH (s:Snapshot {repository_id: $rid}) RETURN s.id",
                {"rid": repository_id},
            )
        ]
        for snapshot_id in snap_ids:
            delete_snapshot_graph(conn, snapshot_id)
            conn.execute(
                "MATCH (s:Snapshot {id: $id}) DELETE s", {"id": snapshot_id}
            )

        job_ids = [
            row[0]
            for row in fetch_all(
                conn,
                "MATCH (j:Job {repository_id: $rid}) RETURN j.id",
                {"rid": repository_id},
            )
        ]
        for job_id in job_ids:
            conn.execute(
                "MATCH (d:Diagnostic {job_id: $jid}) DELETE d", {"jid": job_id}
            )
            conn.execute(
                "MATCH (f:ScanFile {job_id: $jid}) DELETE f", {"jid": job_id}
            )
            conn.execute(
                "MATCH (t:TechnologyDetection {job_id: $jid}) DELETE t",
                {"jid": job_id},
            )
            conn.execute("MATCH (j:Job {id: $jid}) DELETE j", {"jid": job_id})

        conn.execute(
            "MATCH (r:Repository {id: $id}) DELETE r", {"id": repository_id}
        )
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
