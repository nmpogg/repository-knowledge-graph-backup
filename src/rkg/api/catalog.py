"""Snapshot-scoped technology, dependency and diagnostic reads."""

from __future__ import annotations

from typing import Any

from rkg.domain.models import Evidence
from rkg.graph.ids import logical_entity_id, physical_entity_id
from rkg.storage._util import fetch_all, fetch_one, loads_json
from rkg.storage.connection import Storage
from rkg.storage.errors import NotFoundError


def repository_for_snapshot(storage: Storage, snapshot_id: str) -> str:
    row = fetch_one(
        storage.conn,
        "MATCH (s:Snapshot {id: $id}) RETURN s.repository_id",
        {"id": snapshot_id},
    )
    if row is None:
        raise NotFoundError("snapshot not found")
    return str(row[0])


def warning_count(storage: Storage, snapshot_id: str) -> int:
    row = fetch_one(
        storage.conn,
        "MATCH (d:Diagnostic) WHERE d.snapshot_id = $sid AND d.severity = 'warning' "
        "RETURN count(d)",
        {"sid": snapshot_id},
    )
    return int(row[0]) if row else 0


def _report_technologies(
    storage: Storage, repository_id: str, snapshot_id: str
) -> list[dict[str, Any]]:
    rows = fetch_all(
        storage.conn,
        "MATCH (j:Job {repository_id: $rid}) RETURN j.report_json",
        {"rid": repository_id},
    )
    found: list[dict[str, Any]] = []
    for (raw,) in rows:
        report = loads_json(raw, default=None) or {}
        if not isinstance(report, dict) or report.get("snapshot_id") != snapshot_id:
            continue
        entries = report.get("technologies") or []
        if isinstance(entries, list):
            found = [item for item in entries if isinstance(item, dict)]
    return found


def snapshot_capabilities(
    storage: Storage, repository_id: str, snapshot_id: str
) -> list[dict[str, Any]]:
    rows = fetch_all(
        storage.conn,
        "MATCH (t:TechnologyDetection {snapshot_id: $sid}) "
        "RETURN t.technology, t.version_constraint, t.support_state, t.evidence_ids "
        "ORDER BY t.technology ASC",
        {"sid": snapshot_id},
    )
    if rows:
        items = []
        for technology, version, state, evidence_ids in rows:
            items.append(
                {
                    "technology": str(technology),
                    "version": version or None,
                    "support_state": str(state),
                    "evidence": _evidence_for_ids(storage, snapshot_id, evidence_ids),
                    "limitations": [],
                }
            )
        return items
    fallback = []
    for item in _report_technologies(storage, repository_id, snapshot_id):
        fallback.append(
            {
                "technology": item.get("technology"),
                "version": item.get("version"),
                "support_state": item.get("support_state"),
                "adapter_ids": item.get("adapter_ids") or [],
                "capabilities": item.get("capabilities") or [],
                "evidence": [],
                "limitations": [],
            }
        )
    fallback.sort(key=lambda item: str(item.get("technology")))
    return fallback


def _evidence_for_ids(
    storage: Storage, snapshot_id: str, evidence_ids: object
) -> list[dict[str, Any]]:
    wanted = {str(item) for item in (evidence_ids or [])}
    if not wanted:
        return []
    refs = []
    for item in _evidence_rows(storage, snapshot_id):
        if item["id"] in wanted:
            refs.append(item)
    return refs


def _evidence_rows(storage: Storage, snapshot_id: str) -> list[dict[str, Any]]:
    rows = fetch_all(
        storage.conn,
        "MATCH (e:Evidence {snapshot_id: $sid}) "
        "RETURN e.id, e.file_path, e.start_line, e.end_line, e.rule "
        "ORDER BY e.file_path ASC, e.start_line ASC, e.id ASC",
        {"sid": snapshot_id},
    )
    return [
        {
            "id": str(eid),
            "file_path": str(path),
            "start_line": int(start),
            "end_line": int(end),
            "rule": str(rule),
        }
        for eid, path, start, end, rule in rows
    ]


def entity_evidence(
    storage: Storage,
    snapshot_id: str,
    file_path: str | None,
    *,
    directory_id: str | None = None,
) -> list[Evidence]:
    if directory_id:
        rows = fetch_all(
            storage.conn,
            "MATCH ()-[r:CONTAINS]->(d:Entity {id: $id}) "
            "WHERE r.snapshot_id = $sid RETURN r.evidence_ids",
            {"id": physical_entity_id(snapshot_id, directory_id), "sid": snapshot_id},
        )
        refs = {str(ref) for (ids,) in rows for ref in (ids or [])}
        from rkg.graph.access import load_evidence_by_ids

        return load_evidence_by_ids(storage, snapshot_id, refs)
    if not file_path:
        return []
    rows = fetch_all(
        storage.conn,
        "MATCH (e:Evidence {snapshot_id: $sid, file_path: $path}) "
        "RETURN e.id, e.snapshot_id, e.file_path, e.start_line, e.end_line, e.rule "
        "ORDER BY e.start_line ASC, e.id ASC",
        {"sid": snapshot_id, "path": file_path},
    )
    return [
        Evidence(
            id=str(eid),
            snapshot_id=str(sid),
            file_path=str(path),
            start_line=int(start),
            end_line=int(end),
            rule=str(rule),
        )
        for eid, sid, path, start, end, rule in rows
    ]


def list_dependencies(
    storage: Storage,
    snapshot_id: str,
    *,
    subtype: str | None,
    q: str | None,
    offset: int,
    limit: int,
) -> tuple[list[dict[str, Any]], int]:
    rows = fetch_all(
        storage.conn,
        "MATCH (x:ExternalDependency {snapshot_id: $sid}) "
        "RETURN x.id, x.kind, x.name, x.version_constraint, "
        "x.provenance_json, x.origin "
        "ORDER BY x.name ASC, x.id ASC",
        {"sid": snapshot_id},
    )
    needle = q.casefold() if q else None
    matched = []
    for dep_id, kind, name, version, provenance_raw, origin in rows:
        provenance = loads_json(provenance_raw, default={}) or {}
        subtype_value = str(kind or origin or "")
        if subtype and subtype not in {str(kind), str(origin), subtype_value}:
            continue
        if needle and needle not in str(name).casefold():
            continue
        matched.append(
            {
                "id": logical_entity_id(str(dep_id), snapshot_id),
                "name": str(name),
                "version": version or None,
                "subtype": subtype_value,
                "provenance": (
                    provenance if isinstance(provenance, dict) else {"origin": origin}
                ),
                "origin": origin or None,
            }
        )
    total = len(matched)
    return matched[offset : offset + limit], total


def list_diagnostics(
    storage: Storage,
    snapshot_id: str,
    *,
    offset: int,
    limit: int,
) -> tuple[list[dict[str, Any]], int]:
    rows = fetch_all(
        storage.conn,
        "MATCH (d:Diagnostic) WHERE d.snapshot_id = $sid "
        "RETURN d.id, d.severity, d.code, d.message, d.file_path, d.line "
        "ORDER BY d.severity ASC, d.file_path ASC, d.line ASC, d.id ASC",
        {"sid": snapshot_id},
    )
    items = [
        {
            "id": str(diag_id),
            "severity": str(severity),
            "code": str(code),
            "message": str(message),
            "file_path": file_path,
            "line": line,
        }
        for diag_id, severity, code, message, file_path, line in rows
    ]
    return items[offset : offset + limit], len(items)
