"""Versioned Kùzu schema bootstrap and migrations (never drop user DB)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from tempfile import TemporaryDirectory

import kuzu

from rkg.storage._util import (
    CURRENT_SCHEMA_VERSION,
    DDL_PATH,
    SCHEMA_META_ID,
    fetch_all,
    fetch_one,
    parse_ddl_statements,
    table_names,
    ts_param,
)

_V0_PATH = Path(__file__).resolve().parent / "fixtures" / "ddl_v0.cypher"
PREVIOUS_DDL_V0 = _V0_PATH.read_text(encoding="utf-8")
_MULTIPLICITIES = frozenset({"MANY_MANY", "MANY_ONE", "ONE_MANY", "ONE_ONE"})

__all__ = [
    "CURRENT_SCHEMA_VERSION",
    "PREVIOUS_DDL_V0",
    "bootstrap_current_schema",
    "migrate",
    "open_migrated_database",
    "read_schema_version",
]


def execute_statements(conn: kuzu.Connection, statements: list[str]) -> None:
    for stmt in statements:
        conn.execute(stmt)


def bootstrap_current_schema(conn: kuzu.Connection, ddl_path: Path = DDL_PATH) -> None:
    statements = parse_ddl_statements(ddl_path.read_text(encoding="utf-8"))
    execute_statements(conn, statements)
    _write_schema_meta(conn, CURRENT_SCHEMA_VERSION)


def read_schema_version(conn: kuzu.Connection) -> int:
    names = table_names(conn)
    if not names:
        return -1  # empty database
    if "SchemaMeta" not in names:
        return 0
    row = fetch_one(
        conn,
        "MATCH (m:SchemaMeta {id: $id}) RETURN m.version",
        {"id": SCHEMA_META_ID},
    )
    if row is None:
        return 0
    return int(row[0])


def _write_schema_meta(conn: kuzu.Connection, version: int) -> None:
    existing = fetch_one(
        conn,
        "MATCH (m:SchemaMeta {id: $id}) RETURN m.id",
        {"id": SCHEMA_META_ID},
    )
    if existing is None:
        conn.execute(
            "CREATE (m:SchemaMeta {id: $id, version: $version, "
            "applied_at: timestamp($ts)})",
            {"id": SCHEMA_META_ID, "version": version, "ts": ts_param()},
        )
    else:
        conn.execute(
            "MATCH (m:SchemaMeta {id: $id}) SET m.version = $version, "
            "m.applied_at = timestamp($ts)",
            {"id": SCHEMA_META_ID, "version": version, "ts": ts_param()},
        )


def _migrate_v0_to_v1(conn: kuzu.Connection) -> None:
    """Add SchemaMeta and widen DEPENDS_ON to Repository|Entity → Entity."""
    names = table_names(conn)
    if "SchemaMeta" not in names:
        conn.execute(
            "CREATE NODE TABLE SchemaMeta("
            "id STRING PRIMARY KEY, version INT64, applied_at TIMESTAMP)"
        )

    if "DEPENDS_ON" in names:
        edges = conn.execute(
            "MATCH (a:Entity)-[r:DEPENDS_ON]->(b:Entity) "
            "RETURN a.id, b.id, r.edge_id, r.snapshot_id, r.rule, r.evidence_ids"
        )
        preserved: list[list[object]] = []
        while edges.has_next():
            preserved.append(edges.get_next())
        conn.execute("DROP TABLE DEPENDS_ON")
        conn.execute(
            "CREATE REL TABLE DEPENDS_ON("
            "FROM Repository TO Entity, FROM Entity TO Entity, "
            "edge_id STRING, snapshot_id STRING, rule STRING, evidence_ids STRING[])"
        )
        for source_id, target_id, edge_id, snapshot_id, rule, evidence_ids in preserved:
            conn.execute(
                "MATCH (a:Entity {id: $src}), (b:Entity {id: $tgt}) "
                "CREATE (a)-[:DEPENDS_ON {edge_id: $eid, snapshot_id: $sid, "
                "rule: $rule, evidence_ids: $ev}]->(b)",
                {
                    "src": source_id,
                    "tgt": target_id,
                    "eid": edge_id,
                    "sid": snapshot_id,
                    "rule": rule,
                    "ev": list(evidence_ids or []),
                },
            )

    _write_schema_meta(conn, 1)


def _migrate_v1_to_v2(conn: kuzu.Connection) -> None:
    """Atomically widen CONTAINS without rewriting old snapshots or their keys."""
    conn.execute("BEGIN TRANSACTION")
    try:
        result = conn.execute(
            "MATCH (a:Entity)-[r:CONTAINS]->(b:Entity) "
            "RETURN a.id, b.id, r.edge_id, r.snapshot_id, r.rule, r.evidence_ids"
        )
        preserved = []
        while result.has_next():
            preserved.append(result.get_next())
        conn.execute("DROP TABLE CONTAINS")
        conn.execute(
            "CREATE REL TABLE CONTAINS("
            "FROM Repository TO Entity, FROM Entity TO Entity, "
            "edge_id STRING, snapshot_id STRING, rule STRING, evidence_ids STRING[])"
        )
        for source, target, key, snapshot, rule, refs in preserved:
            conn.execute(
                "MATCH (a:Entity {id: $src}), (b:Entity {id: $tgt}) "
                "CREATE (a)-[:CONTAINS {edge_id: $eid, snapshot_id: $sid, "
                "rule: $rule, evidence_ids: $ev}]->(b)",
                {
                    "src": source,
                    "tgt": target,
                    "eid": key,
                    "sid": snapshot,
                    "rule": rule,
                    "ev": list(refs or []),
                },
            )
        _write_schema_meta(conn, 2)
        conn.execute("COMMIT")
    except Exception:
        try:
            conn.execute("ROLLBACK")
        except RuntimeError:
            # A failing database statement may already have aborted the transaction.
            pass
        raise


def _require_metadata_column(conn: kuzu.Connection, *, present: bool) -> None:
    columns = fetch_all(conn, "CALL table_info('Turn') RETURN name,type")
    matches = [row for row in columns if row[0] == "response_metadata_json"]
    valid = (
        matches == [["response_metadata_json", "STRING"]] if present else not matches
    )
    if not valid:
        raise RuntimeError("unexpected conversation metadata schema shape")


def _declared_shape(ddl_path: Path, version: int) -> dict[str, tuple]:
    """Derive supported physical shapes from the canonical DDL, not row data.

    Only the documented migrations differ: SchemaMeta/DEPENDS_ON at v1,
    CONTAINS at v2, and the nullable Turn metadata column at v3.
    """
    shape = {}
    statements = parse_ddl_statements(ddl_path.read_text(encoding="utf-8"))
    for statement in statements:
        match = re.fullmatch(r"CREATE (NODE|REL) TABLE (\w+)\((.*)\)", statement, re.S)
        if match is None:
            raise RuntimeError("unsupported canonical physical schema declaration")
        kind, name, body = match.groups()
        if name == "SchemaMeta" and version == 0:
            continue
        columns, keys, connections = {}, set(), set()
        multiplicity = "MANY_MANY"  # Default cardinality in pinned Kuzu 0.11.3.
        for declaration in body.split(","):
            declaration = declaration.strip()
            if kind == "REL" and declaration in _MULTIPLICITIES:
                multiplicity = declaration
                continue
            pair = re.fullmatch(r"FROM (\w+) TO (\w+)", declaration)
            if pair and kind == "REL":
                connections.add((*pair.groups(), "id", "id"))
                continue
            prop = re.fullmatch(r"(\w+) ([A-Z0-9_\[\]]+)( PRIMARY KEY)?", declaration)
            if prop is None:
                raise RuntimeError("unsupported canonical physical schema declaration")
            column, dtype, primary = prop.groups()
            if name == "Turn" and column == "response_metadata_json" and version < 3:
                continue
            columns[column] = (dtype, "NULL")
            if primary:
                keys.add(column)
        if (name == "CONTAINS" and version < 2) or (
            name == "DEPENDS_ON" and version == 0
        ):
            connections = {("Entity", "Entity", "id", "id")}
        shape[name] = (kind, columns, keys, connections, multiplicity)
    return shape


def _actual_multiplicities(conn: kuzu.Connection) -> dict[str, str]:
    """Inspect schema only; never export rows or probe cardinality with writes.

    Kuzu 0.11.3 table_info/show_connection omit multiplicity. Its schema-only
    export includes explicit cardinalities for every relationship table.
    The protected temporary directory is removed on success and failure.
    """
    try:
        with TemporaryDirectory(prefix="rkg-schema-") as directory:
            folder = Path(directory) / "schema"
            quoted_path = json.dumps(folder.as_posix())
            conn.execute(f"EXPORT DATABASE {quoted_path} (schema_only=true)")
            if {p.name for p in folder.iterdir()} != {"schema.cypher"}:
                raise RuntimeError("unexpected schema export files")
            statements = parse_ddl_statements(
                (folder / "schema.cypher").read_text(encoding="utf-8")
            )
            result = {}
            for statement in statements:
                match = re.fullmatch(
                    r"CREATE REL TABLE `(\w+)`\s*\((.*)\)",
                    statement,
                    re.S,
                )
                if match is None:
                    continue
                name, body = match.groups()
                values = [
                    s.strip() for s in body.split(",") if s.strip() in _MULTIPLICITIES
                ]
                if len(values) != 1 or name in result:
                    raise RuntimeError("unrecognized relationship multiplicity")
                result[name] = values[0]
            return result
    except (OSError, RuntimeError, UnicodeError):
        # Engine/IO errors may contain the private export directory. Do not leak it.
        raise RuntimeError("unable to verify relationship multiplicity") from None


def _require_supported_shape(
    conn: kuzu.Connection,
    version: int,
    ddl_path: Path,
) -> None:
    if version not in (0, 1, 2, 3):
        raise RuntimeError("unsupported physical schema version")
    expected = _declared_shape(ddl_path, version)
    tables = dict(fetch_all(conn, "CALL show_tables() RETURN name,type"))
    if tables != {name: spec[0] for name, spec in expected.items()}:
        raise RuntimeError("unexpected physical schema tables")
    for name, (kind, columns, keys, connections, _) in expected.items():
        # Names are derived from the trusted declaration's identifier grammar.
        rows = fetch_all(
            conn,
            f"CALL table_info('{name}') RETURN name,type,`default expression`",
        )
        if {row[0]: (row[1], row[2]) for row in rows} != columns:
            raise RuntimeError("unexpected physical schema properties")
        if kind == "NODE":
            primary = fetch_all(
                conn, f"CALL table_info('{name}') RETURN name,`primary key`"
            )
            if {row[0] for row in primary if row[1]} != keys:
                raise RuntimeError("unexpected physical schema primary key")
        else:
            actual = fetch_all(conn, f"CALL show_connection('{name}') RETURN *")
            if {tuple(row) for row in actual} != connections:
                raise RuntimeError(
                    "unexpected physical schema relationship connections"
                )
    if version > 0:
        rows = fetch_all(
            conn, "MATCH (m:SchemaMeta) RETURN m.id,m.version ORDER BY m.id"
        )
        if rows != [[SCHEMA_META_ID, version]]:
            raise RuntimeError("physical schema metadata must be the current singleton")
    actual = _actual_multiplicities(conn)
    if actual != {name: spec[4] for name, spec in expected.items() if spec[0] == "REL"}:
        raise RuntimeError("unexpected physical schema relationship multiplicity")


def _migrate_v2_to_v3(conn: kuzu.Connection) -> None:
    """TBL r13/MIG v3: nullable metadata only, no history/state backfill."""
    _require_metadata_column(conn, present=False)
    conn.execute("BEGIN TRANSACTION")
    try:
        conn.execute("ALTER TABLE Turn ADD response_metadata_json STRING")
        _write_schema_meta(conn, 3)
        conn.execute("COMMIT")
    except Exception:
        try:
            conn.execute("ROLLBACK")
        except RuntimeError:
            pass  # Engine may already have aborted; preserve the original failure.
        raise


def migrate(conn: kuzu.Connection, ddl_path: Path = DDL_PATH) -> int:
    """Bring an empty or previous-schema database to CURRENT_SCHEMA_VERSION."""
    version = read_schema_version(conn)
    if version == -1:
        bootstrap_current_schema(conn, ddl_path)
        _require_supported_shape(conn, CURRENT_SCHEMA_VERSION, ddl_path)
        return CURRENT_SCHEMA_VERSION
    # Validate all tables/properties/keys/connections and the whole singleton
    # before even a legacy migration writes. A metadata-only check is insufficient.
    _require_supported_shape(conn, version, ddl_path)
    if version < 1:
        _migrate_v0_to_v1(conn)
        version = 1
    if version == 1:
        _migrate_v1_to_v2(conn)
        version = 2
    if version == 2:
        _migrate_v2_to_v3(conn)
        version = 3
    if version != CURRENT_SCHEMA_VERSION:
        raise RuntimeError(
            f"unsupported schema version {version}; expected {CURRENT_SCHEMA_VERSION}"
        )
    if version != read_schema_version(conn):
        raise RuntimeError("physical schema migration version mismatch")
    _require_supported_shape(conn, version, ddl_path)
    return version


def open_migrated_database(path: Path | str) -> tuple[kuzu.Database, kuzu.Connection]:
    db = kuzu.Database(str(path))
    conn = kuzu.Connection(db)
    try:
        migrate(conn)
    except Exception:
        conn.close()
        db.close()
        raise
    return db, conn
