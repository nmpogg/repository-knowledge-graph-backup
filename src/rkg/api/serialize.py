"""Contract JSON for repository, snapshot, job and graph facts."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from rkg.api.catalog import snapshot_capabilities, warning_count
from rkg.domain.models import Entity, Evidence
from rkg.graph import count_entities
from rkg.storage._util import EDGE_REL_TABLE, fetch_one
from rkg.storage.connection import Storage
from rkg.storage.records import JobRecord, RepositoryRecord, SnapshotRecord

_TERMINAL = frozenset({"succeeded", "succeeded_with_warnings", "failed"})


def _stamp(value: datetime) -> str:
    return value.isoformat()


def repository_json(item: RepositoryRecord) -> dict[str, Any]:
    return {
        "repository_id": item.id,
        "revision": item.revision,
        "display_name": item.display_name,
        "source_type": item.source_type,
        "source_locator_redacted": item.source_locator_redacted,
        "source_root": item.source_root,
        "app_module": item.app_module,
        "app_symbol": item.app_symbol,
        "scan_defaults": item.scan_defaults,
        "active_snapshot_id": item.active_snapshot_id,
        "created_at": _stamp(item.created_at),
        "updated_at": _stamp(item.updated_at),
    }


def page_json(
    items: list[dict[str, Any]], *, offset: int, limit: int, total: int
) -> dict[str, Any]:
    return {"items": items, "total": total, "offset": offset, "limit": limit}


def edge_count(storage: Storage, snapshot_id: str) -> int:
    total = 0
    for rel in EDGE_REL_TABLE.values():
        row = fetch_one(
            storage.conn,
            f"MATCH ()-[r:{rel}]->() WHERE r.snapshot_id = $sid RETURN count(r)",
            {"sid": snapshot_id},
        )
        total += int(row[0]) if row else 0
    return total


def snapshot_json(storage: Storage, item: SnapshotRecord) -> dict[str, Any]:
    technologies = snapshot_capabilities(storage, item.repository_id, item.id)
    return {
        "snapshot_id": item.id,
        "repository_id": item.repository_id,
        "source_revision": item.source_revision,
        "manifest_hash": item.manifest_hash,
        "scan_config_digest": item.scan_config_digest,
        "analyzer_version": item.analyzer_version,
        "schema_version": item.schema_version,
        "adapter_versions": item.adapter_versions,
        "status": item.status,
        "metrics": {
            "entity_count": count_entities(storage, item.id),
            "edge_count": edge_count(storage, item.id),
            "warning_count": warning_count(storage, item.id),
        },
        "capabilities": {
            "technologies": [entry["technology"] for entry in technologies],
            "graph_ready": item.status == "ready",
        },
        "created_at": _stamp(item.created_at),
        "is_active": item.is_active,
    }


def progress_revision(item: JobRecord) -> int:
    return int(item.updated_at.timestamp() * 1_000_000)


def job_json(item: JobRecord) -> dict[str, Any]:
    report = item.report or None
    snapshot_id = report.get("snapshot_id") if isinstance(report, dict) else None
    error = None
    if item.error_code:
        error = {"code": item.error_code, "message": item.error_code.replace("_", " ")}
    return {
        "job_id": item.id,
        "repository_id": item.repository_id,
        "stage": item.stage,
        "status": item.status,
        "progress_revision": progress_revision(item),
        "report": report,
        "snapshot_id": snapshot_id,
        "error": error,
        "updated_at": _stamp(item.updated_at),
    }


def job_headers(item: JobRecord) -> dict[str, str]:
    if item.stage in _TERMINAL or item.status in _TERMINAL:
        return {}
    return {"Retry-After": "1"}


def entity_json(item: Entity, evidence: list[Evidence] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": item.id,
        "repository_id": item.repository_id,
        "snapshot_id": item.snapshot_id,
        "type": item.type.value,
        "name": item.name,
        "qualified_name": item.qualified_name,
        "file_path": item.file_path,
        "start_line": item.start_line,
        "end_line": item.end_line,
        "language_kind": item.language_kind,
        "framework_kind": item.framework_kind,
        "attributes": {
            key: list(value) if isinstance(value, tuple) else value
            for key, value in item.attributes
        },
    }
    if evidence is not None:
        payload["evidence"] = [evidence_json(ref) for ref in evidence]
    return payload


def evidence_json(item: Evidence) -> dict[str, Any]:
    return {
        "id": item.id,
        "file_path": item.file_path,
        "start_line": item.start_line,
        "end_line": item.end_line,
        "rule": item.rule,
        "provenance": "filesystem"
        if item.rule == "RKG.structure.contains.v1"
        else "source",
    }
