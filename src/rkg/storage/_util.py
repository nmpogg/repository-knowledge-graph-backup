"""Shared helpers for Kùzu Cypher execution and JSON/timestamp encoding."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import kuzu

DDL_PATH = (
    Path(__file__).resolve().parents[3]
    / ".aide"
    / "tech-specs"
    / "RKG-GRAPH"
    / "schema"
    / "DDL-RKG-GRAPH.cypher"
)

# Physical migration counter stored in SchemaMeta.version.
CURRENT_SCHEMA_VERSION = 3
SCHEMA_META_ID = "current"

TERMINAL_JOB_STAGES = frozenset({"succeeded", "succeeded_with_warnings", "failed"})

EDGE_REL_TABLE = {
    "contains": "CONTAINS",
    "imports": "IMPORTS",
    "exposes": "EXPOSES",
    "handled_by": "HANDLED_BY",
    "calls": "CALLS",
    "implements": "IMPLEMENTS",
    "inherits_from": "INHERITS_FROM",
    "maps_to": "MAPS_TO",
    "reads": "READS",
    "writes": "WRITES",
    "publishes": "PUBLISHES",
    "consumes": "CONSUMES",
    "depends_on": "DEPENDS_ON",
}


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def ts_param(value: datetime | None = None) -> str:
    """Kùzu timestamp() expects an ISO-8601 string parameter."""
    moment = value or utc_now()
    if moment.tzinfo is not None:
        moment = moment.astimezone(UTC).replace(tzinfo=None)
    return moment.isoformat(timespec="microseconds")


def dumps_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def loads_json(raw: str | None, default: Any = None) -> Any:
    if raw is None or raw == "":
        return default
    return json.loads(raw)


def parse_ddl_statements(ddl_text: str) -> list[str]:
    lines: list[str] = []
    for line in ddl_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("//"):
            continue
        comment_at = line.find("//")
        if comment_at >= 0:
            line = line[:comment_at]
        lines.append(line)
    body = "\n".join(lines)
    return [part.strip() for part in body.split(";") if part.strip()]


def fetch_all(
    conn: kuzu.Connection, query: str, params: dict[str, Any] | None = None
) -> list[list[Any]]:
    result = conn.execute(query, params or {})
    rows: list[list[Any]] = []
    while result.has_next():
        rows.append(result.get_next())
    return rows


def fetch_one(
    conn: kuzu.Connection, query: str, params: dict[str, Any] | None = None
) -> list[Any] | None:
    rows = fetch_all(conn, query, params)
    return rows[0] if rows else None


def table_names(conn: kuzu.Connection) -> set[str]:
    rows = fetch_all(conn, "CALL show_tables() RETURN name")
    return {str(row[0]) for row in rows}
