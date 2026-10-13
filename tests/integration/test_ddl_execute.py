"""Smoke: DDL-RKG-GRAPH.cypher executes on the pinned Kùzu version."""

from __future__ import annotations

import importlib.metadata
import tempfile
from pathlib import Path

import kuzu

DDL_PATH = (
    Path(__file__).resolve().parents[2]
    / ".aide"
    / "tech-specs"
    / "RKG-GRAPH"
    / "schema"
    / "DDL-RKG-GRAPH.cypher"
)
PINNED_KUZU = "0.11.3"


def _statements(ddl_text: str) -> list[str]:
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


def test_pinned_kuzu_version() -> None:
    assert importlib.metadata.version("kuzu") == PINNED_KUZU


def test_ddl_rkg_graph_executes() -> None:
    assert DDL_PATH.is_file(), f"missing DDL at {DDL_PATH.name}"
    stmts = _statements(DDL_PATH.read_text(encoding="utf-8"))
    assert stmts, "DDL file must contain executable statements"

    with tempfile.TemporaryDirectory() as tmp:
        db = kuzu.Database(str(Path(tmp) / "rkg-ddl-smoke"))
        conn = kuzu.Connection(db)
        for stmt in stmts:
            conn.execute(stmt)
