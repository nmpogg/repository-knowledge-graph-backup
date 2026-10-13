"""Schema bootstrap and previous-version migration (ADR-2026-002)."""

from __future__ import annotations

from pathlib import Path

import kuzu
import pytest

from rkg.storage import CURRENT_SCHEMA_VERSION, PREVIOUS_DDL_V0, Storage
from rkg.storage._util import parse_ddl_statements, table_names, ts_param
from rkg.storage.migrate import execute_statements, read_schema_version


@pytest.fixture
def db_dir(tmp_path: Path) -> Path:
    return tmp_path / "kuzu"


def test_fresh_storage_bootstraps_schema_meta(db_dir: Path) -> None:
    with Storage(db_dir / "fresh") as store:
        assert read_schema_version(store.conn) == CURRENT_SCHEMA_VERSION
        names = table_names(store.conn)
        assert "SchemaMeta" in names
        assert "Repository" in names
        assert "DEPENDS_ON" in names


def test_migrate_previous_schema_retains_depends_on_edges(db_dir: Path) -> None:
    path = db_dir / "v0"
    path.parent.mkdir(parents=True, exist_ok=True)
    db = kuzu.Database(str(path))
    conn = kuzu.Connection(db)
    execute_statements(conn, parse_ddl_statements(PREVIOUS_DDL_V0))
    assert "SchemaMeta" not in table_names(conn)
    assert read_schema_version(conn) == 0

    # Seed repository + entity-entity DEPENDS_ON under v0 REL shape.
    conn.execute(
        "CREATE (r:Repository {id: 'repo_old', revision: 1, display_name: 'Old', "
        "source_type: 'local', source_locator: 'seed', source_identity_hash: 'h', "
        "source_locator_redacted: 'local:…/seed', source_root: null, "
        "app_module: null, app_symbol: null, scan_defaults_json: null, "
        "active_snapshot_id: null, created_at: timestamp($ts), "
        "updated_at: timestamp($ts)})",
        {"ts": ts_param()},
    )
    conn.execute(
        "CREATE (e1:Entity {id: 'e1', repository_id: 'repo_old', snapshot_id: 's1', "
        "type: 'SourceUnit', name: 'a', qualified_name: 'a', file_path: 'a.py', "
        "start_line: 1, end_line: 1, language_kind: null, framework_kind: null, "
        "attributes_json: '{}'})"
    )
    conn.execute(
        "CREATE (e2:Entity {id: 'e2', repository_id: 'repo_old', snapshot_id: 's1', "
        "type: 'ExternalDependency', name: 'x', qualified_name: 'x', file_path: null, "
        "start_line: null, end_line: null, language_kind: null, framework_kind: null, "
        "attributes_json: '{}'})"
    )
    conn.execute(
        "MATCH (a:Entity {id: 'e1'}), (b:Entity {id: 'e2'}) "
        "CREATE (a)-[:DEPENDS_ON {edge_id: 'edge1', snapshot_id: 's1', "
        "rule: 'RKG.python.depends_on.v1', evidence_ids: ['ev1']}]->(b)"
    )
    del conn
    del db

    with Storage(path) as store:
        assert read_schema_version(store.conn) == CURRENT_SCHEMA_VERSION
        rows = store.conn.execute(
            "MATCH (a:Entity)-[r:DEPENDS_ON]->(b:Entity) "
            "RETURN a.id, b.id, r.edge_id"
        )
        preserved = []
        while rows.has_next():
            preserved.append(rows.get_next())
        assert preserved == [["e1", "e2", "edge1"]]

        # Multi-FROM now accepts Repository → Entity depends_on.
        store.conn.execute(
            "MATCH (r:Repository {id: 'repo_old'}), (e:Entity {id: 'e2'}) "
            "CREATE (r)-[:DEPENDS_ON {edge_id: 'edge_repo', snapshot_id: 's1', "
            "rule: 'RKG.python.depends_on.v1', evidence_ids: ['ev2']}]->(e)"
        )
        check = store.conn.execute(
            "MATCH (r:Repository)-[rel:DEPENDS_ON]->(e:Entity) "
            "WHERE rel.edge_id = 'edge_repo' RETURN r.id, e.id"
        )
        assert check.has_next()
        assert check.get_next() == ["repo_old", "e2"]
