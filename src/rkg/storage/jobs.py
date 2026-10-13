"""Minimal Job persistence for index lifecycle guards and T-015 handoff."""

from __future__ import annotations

import uuid
from typing import Any

import kuzu

from rkg.storage._util import (
    TERMINAL_JOB_STAGES,
    dumps_json,
    fetch_one,
    loads_json,
    ts_param,
)
from rkg.storage.errors import NotFoundError
from rkg.storage.records import JobRecord
from rkg.storage.repositories import get_repository

_JOB_RETURN = (
    "j.id, j.repository_id, j.status, j.stage, j.source_type, "
    "j.manifest_hash, j.report_json, j.error_code, j.created_at, j.updated_at"
)


def _row_to_job(row: list[Any]) -> JobRecord:
    (
        job_id,
        repository_id,
        status,
        stage,
        source_type,
        manifest_hash,
        report_json,
        error_code,
        created_at,
        updated_at,
    ) = row
    return JobRecord(
        id=job_id,
        repository_id=repository_id,
        status=status,
        stage=stage,
        source_type=source_type,
        manifest_hash=manifest_hash,
        report=loads_json(report_json, default=None),
        error_code=error_code,
        created_at=created_at,
        updated_at=updated_at,
    )


def create_job(
    conn: kuzu.Connection,
    repository_id: str,
    *,
    stage: str = "queued",
    status: str | None = None,
    source_type: str | None = None,
    job_id: str | None = None,
) -> JobRecord:
    get_repository(conn, repository_id)
    jid = job_id or f"job_{uuid.uuid4().hex}"
    now = ts_param()
    conn.execute(
        "CREATE (j:Job {"
        "id: $id, repository_id: $rid, status: $status, stage: $stage, "
        "source_type: $stype, manifest_hash: null, report_json: null, "
        "error_code: null, created_at: timestamp($ts), updated_at: timestamp($ts)})",
        {
            "id": jid,
            "rid": repository_id,
            "status": status or stage,
            "stage": stage,
            "stype": source_type,
            "ts": now,
        },
    )
    return get_job(conn, jid)


def get_job(conn: kuzu.Connection, job_id: str) -> JobRecord:
    row = fetch_one(
        conn,
        f"MATCH (j:Job {{id: $id}}) RETURN {_JOB_RETURN}",
        {"id": job_id},
    )
    if row is None:
        raise NotFoundError("job not found")
    return _row_to_job(row)


def update_job(
    conn: kuzu.Connection,
    job_id: str,
    *,
    stage: str | None = None,
    status: str | None = None,
    manifest_hash: str | None = None,
    report: dict[str, Any] | None = None,
    error_code: str | None = None,
) -> JobRecord:
    current = get_job(conn, job_id)
    new_stage = stage if stage is not None else current.stage
    new_status = status if status is not None else (stage or current.status)
    new_manifest = (
        manifest_hash if manifest_hash is not None else current.manifest_hash
    )
    new_report = (
        dumps_json(report)
        if report is not None
        else (dumps_json(current.report) if current.report is not None else None)
    )
    new_error = error_code if error_code is not None else current.error_code
    row = fetch_one(
        conn,
        f"MATCH (j:Job {{id: $id}}) SET j.stage = $stage, j.status = $status, "
        f"j.manifest_hash = $mhash, j.report_json = $report, "
        f"j.error_code = $err, j.updated_at = timestamp($ts) "
        f"RETURN {_JOB_RETURN}",
        {
            "id": job_id,
            "stage": new_stage,
            "status": new_status,
            "mhash": new_manifest,
            "report": new_report,
            "err": new_error,
            "ts": ts_param(),
        },
    )
    assert row is not None
    return _row_to_job(row)


def has_non_terminal_jobs(conn: kuzu.Connection, repository_id: str) -> bool:
    row = fetch_one(
        conn,
        "MATCH (j:Job) WHERE j.repository_id = $rid AND NOT j.stage IN $terms "
        "RETURN count(j)",
        {"rid": repository_id, "terms": list(TERMINAL_JOB_STAGES)},
    )
    return bool(row and int(row[0]) > 0)
