"""Snapshot access guards and Entity row mapping for graph reads."""

from __future__ import annotations

import json
from typing import Any

from rkg.domain.models import Entity, EntityType, Evidence
from rkg.graph.errors import NoActiveSnapshotError, SnapshotUnavailableError
from rkg.graph.ids import logical_entity_id, physical_entity_id
from rkg.storage._util import fetch_all, fetch_one, loads_json
from rkg.storage.connection import Storage
from rkg.storage.errors import NotFoundError
from rkg.storage.records import SnapshotRecord

_ENTITY_RETURN = (
    "e.id, e.repository_id, e.snapshot_id, e.type, e.name, e.qualified_name, "
    "e.file_path, e.start_line, e.end_line, e.language_kind, e.framework_kind, "
    "e.attributes_json"
)


def resolve_snapshot_id(
    storage: Storage,
    repository_id: str,
    snapshot_id: str | None,
) -> str:
    """Resolve explicit snapshot or active pointer; raise typed guard errors."""
    repo = storage.get_repository(repository_id)
    if snapshot_id is None or snapshot_id == "":
        if not repo.active_snapshot_id:
            raise NoActiveSnapshotError("repository has no active snapshot")
        return repo.active_snapshot_id
    return snapshot_id


def require_readable_snapshot(
    storage: Storage,
    repository_id: str,
    snapshot_id: str | None,
) -> SnapshotRecord:
    """Ownership + availability guard used by all graph read entrypoints."""
    resolved = resolve_snapshot_id(storage, repository_id, snapshot_id)
    snap = storage.get_snapshot(repository_id, resolved)
    if snap.status != "ready":
        raise SnapshotUnavailableError("snapshot graph payload unavailable")
    return snap


def _attributes_from_json(raw: str | None) -> tuple[tuple[str, Any], ...]:
    data = loads_json(raw, default={}) or {}
    if not isinstance(data, dict):
        return ()
    items: list[tuple[str, Any]] = []
    for key in sorted(data):
        value = data[key]
        if isinstance(value, list):
            value = tuple(value)
        items.append((str(key), value))
    return tuple(items)


def row_to_entity(row: list[Any]) -> Entity:
    (
        phys_id,
        repository_id,
        snapshot_id,
        etype,
        name,
        qname,
        file_path,
        start_line,
        end_line,
        language_kind,
        framework_kind,
        attributes_json,
    ) = row
    return Entity(
        id=logical_entity_id(str(phys_id), str(snapshot_id)),
        repository_id=str(repository_id),
        snapshot_id=str(snapshot_id),
        type=EntityType(str(etype)),
        name=str(name),
        qualified_name=str(qname),
        file_path=file_path,
        start_line=start_line,
        end_line=end_line,
        language_kind=language_kind,
        framework_kind=framework_kind,
        attributes=_attributes_from_json(attributes_json),
    )


def load_entities(
    storage: Storage, repository_id: str, snapshot_id: str
) -> list[Entity]:
    rows = fetch_all(
        storage.conn,
        f"MATCH (e:Entity {{repository_id: $rid, snapshot_id: $sid}}) "
        f"RETURN {_ENTITY_RETURN} "
        f"ORDER BY e.type ASC, e.qualified_name ASC, e.id ASC",
        {"rid": repository_id, "sid": snapshot_id},
    )
    return [row_to_entity(row) for row in rows]


def load_entity(
    storage: Storage, repository_id: str, snapshot_id: str, entity_id: str
) -> Entity:
    phys = physical_entity_id(snapshot_id, entity_id)
    row = fetch_one(
        storage.conn,
        f"MATCH (e:Entity {{id: $id, repository_id: $rid, snapshot_id: $sid}}) "
        f"RETURN {_ENTITY_RETURN}",
        {"id": phys, "rid": repository_id, "sid": snapshot_id},
    )
    if row is None:
        raise NotFoundError("entity not found in snapshot")
    return row_to_entity(row)


def load_evidence_by_ids(
    storage: Storage, snapshot_id: str, evidence_ids: set[str]
) -> list[Evidence]:
    if not evidence_ids:
        return []
    rows = fetch_all(
        storage.conn,
        "MATCH (e:Evidence {snapshot_id: $sid}) "
        "RETURN e.id, e.snapshot_id, e.file_path, e.start_line, e.end_line, e.rule "
        "ORDER BY e.file_path ASC, e.start_line ASC, e.id ASC",
        {"sid": snapshot_id},
    )
    wanted = set(evidence_ids)
    items: list[Evidence] = []
    for row in rows:
        eid = str(row[0])
        if eid not in wanted:
            continue
        items.append(
            Evidence(
                id=eid,
                snapshot_id=str(row[1]),
                file_path=str(row[2]),
                start_line=int(row[3]),
                end_line=int(row[4]),
                rule=str(row[5]),
            )
        )
    return items


def diagnostic_summary(
    storage: Storage, snapshot_id: str
) -> tuple[tuple[str, int], ...]:
    rows = fetch_all(
        storage.conn,
        "MATCH (d:Diagnostic) WHERE d.snapshot_id = $sid "
        "RETURN d.severity, count(d) "
        "ORDER BY d.severity ASC",
        {"sid": snapshot_id},
    )
    return tuple((str(sev), int(count)) for sev, count in rows)


def mark_snapshot_unavailable(storage: Storage, snapshot_id: str) -> None:
    """Test/helper: flip snapshot status without deleting graph rows."""
    storage.conn.execute(
        "MATCH (s:Snapshot {id: $id}) SET s.status = $status",
        {"id": snapshot_id, "status": "unavailable"},
    )


def dumps_compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
