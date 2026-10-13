"""Atomic FactBatch publication into Kùzu (validate → write → auto-activate)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rkg.domain.models import EdgeType, EntityType, FactBatch
from rkg.domain.validation import validate_fact_batch
from rkg.graph.ids import physical_entity_id, resolve_endpoint_physical_id
from rkg.storage._util import EDGE_REL_TABLE, dumps_json, ts_param
from rkg.storage.connection import Storage
from rkg.storage.records import SnapshotRecord
from rkg.storage.repositories import get_repository, set_active_snapshot
from rkg.storage.snapshots import get_snapshot, insert_snapshot_row


@dataclass(frozen=True, slots=True)
class SnapshotPublishMeta:
    """Immutable provenance written with a published snapshot row."""

    source_revision: str
    manifest_hash: str
    scan_config_digest: str
    analyzer_version: str
    schema_version: str
    adapter_versions: dict[str, str]


def _attributes_json(attributes: tuple[tuple[str, Any], ...]) -> str:
    payload: dict[str, Any] = {}
    for key, value in attributes:
        payload[key] = list(value) if isinstance(value, tuple) else value
    return dumps_json(payload)


def _insert_entity(conn: Any, entity: Any) -> None:
    phys_id = physical_entity_id(entity.snapshot_id, entity.id)
    conn.execute(
        "CREATE (e:Entity {"
        "id: $id, repository_id: $rid, snapshot_id: $sid, type: $etype, "
        "name: $name, qualified_name: $qname, file_path: $fpath, "
        "start_line: $start_line, end_line: $end_line, language_kind: $lang, "
        "framework_kind: $fw, attributes_json: $attrs})",
        {
            "id": phys_id,
            "rid": entity.repository_id,
            "sid": entity.snapshot_id,
            "etype": entity.type.value,
            "name": entity.name,
            "qname": entity.qualified_name,
            "fpath": entity.file_path,
            "start_line": entity.start_line,
            "end_line": entity.end_line,
            "lang": entity.language_kind,
            "fw": entity.framework_kind,
            "attrs": _attributes_json(entity.attributes),
        },
    )
    if entity.type == EntityType.EXTERNAL_DEPENDENCY:
        attrs = dict(entity.attributes)
        conn.execute(
            "CREATE (x:ExternalDependency {"
            "id: $id, snapshot_id: $sid, kind: $kind, name: $name, "
            "version_constraint: $ver, provenance_json: $prov, origin: $origin})",
            {
                "id": phys_id,
                "sid": entity.snapshot_id,
                "kind": str(attrs.get("kind", "")),
                "name": entity.name,
                "ver": str(attrs.get("version_constraint", "")),
                "prov": dumps_json(attrs.get("provenance", {})),
                "origin": str(attrs.get("origin", "")),
            },
        )


def _insert_evidence(conn: Any, item: Any) -> None:
    conn.execute(
        "CREATE (e:Evidence {"
        "id: $id, snapshot_id: $sid, file_path: $fpath, "
        "start_line: $start_line, end_line: $end_line, rule: $rule})",
        {
            "id": item.id,
            "sid": item.snapshot_id,
            "fpath": item.file_path,
            "start_line": item.start_line,
            "end_line": item.end_line,
            "rule": item.rule,
        },
    )


def _insert_diagnostic(conn: Any, item: Any) -> None:
    conn.execute(
        "CREATE (d:Diagnostic {"
        "id: $id, job_id: $jid, snapshot_id: $sid, severity: $sev, "
        "code: $code, file_path: $fpath, line: $line, message: $msg})",
        {
            "id": item.id,
            "jid": item.job_id,
            "sid": item.snapshot_id,
            "sev": item.severity.value,
            "code": item.code,
            "fpath": item.file_path,
            "line": item.line,
            "msg": item.message,
        },
    )


def _insert_edge(conn: Any, edge: Any, repository_id: str) -> None:
    rel = EDGE_REL_TABLE[edge.type.value]
    props = "{edge_id: $eid, snapshot_id: $sid, rule: $rule, evidence_ids: $ev}"
    src = resolve_endpoint_physical_id(
        edge.source_id, snapshot_id=edge.snapshot_id, repository_id=repository_id
    )
    tgt = resolve_endpoint_physical_id(
        edge.target_id, snapshot_id=edge.snapshot_id, repository_id=repository_id
    )
    params = {
        "src": src,
        "tgt": tgt,
        "eid": edge.id,
        "sid": edge.snapshot_id,
        "rule": edge.rule,
        "ev": list(edge.evidence_ids),
    }
    if (
        edge.type in (EdgeType.EXPOSES, EdgeType.DEPENDS_ON, EdgeType.CONTAINS)
        and edge.source_id == repository_id
    ):
        conn.execute(
            f"MATCH (r:Repository {{id: $src}}), (e:Entity {{id: $tgt}}) "
            f"CREATE (r)-[:{rel} {props}]->(e)",
            params,
        )
    else:
        conn.execute(
            f"MATCH (a:Entity {{id: $src}}), (b:Entity {{id: $tgt}}) "
            f"CREATE (a)-[:{rel} {props}]->(b)",
            params,
        )


def publish_fact_batch(
    storage: Storage,
    batch: FactBatch,
    meta: SnapshotPublishMeta,
    *,
    activate: bool = True,
) -> SnapshotRecord:
    """Validate then atomically publish; success auto-activates by default.

    On any write failure the transaction rolls back and the previous
    ``active_snapshot_id`` is unchanged (AC-RKG-008 / AC-RKG-068).
    """
    validate_fact_batch(batch)
    get_repository(storage.conn, batch.repository_id)

    existing = storage.conn.execute(
        "MATCH (s:Snapshot {id: $id}) RETURN s.repository_id",
        {"id": batch.snapshot_id},
    )
    if existing.has_next():
        raise ValueError("snapshot_id already exists")

    created_at = ts_param()
    storage.conn.execute("BEGIN TRANSACTION")
    try:
        insert_snapshot_row(
            storage.conn,
            snapshot_id=batch.snapshot_id,
            repository_id=batch.repository_id,
            source_revision=meta.source_revision,
            manifest_hash=meta.manifest_hash,
            scan_config_digest=meta.scan_config_digest,
            analyzer_version=meta.analyzer_version,
            schema_version=meta.schema_version,
            adapter_versions=meta.adapter_versions,
            status="ready",
            created_at_iso=created_at,
        )
        for entity in batch.entities:
            _insert_entity(storage.conn, entity)
        for item in batch.evidence:
            _insert_evidence(storage.conn, item)
        for item in batch.diagnostics:
            _insert_diagnostic(storage.conn, item)
        for edge in batch.edges:
            _insert_edge(storage.conn, edge, batch.repository_id)
        if activate:
            set_active_snapshot(storage.conn, batch.repository_id, batch.snapshot_id)
        storage.conn.execute("COMMIT")
    except Exception:
        try:
            storage.conn.execute("ROLLBACK")
        except RuntimeError:
            # Kùzu may already abort the transaction on the failing statement.
            pass
        raise

    return get_snapshot(storage.conn, batch.repository_id, batch.snapshot_id)


def count_entities(storage: Storage, snapshot_id: str) -> int:
    result = storage.conn.execute(
        "MATCH (e:Entity {snapshot_id: $sid}) RETURN count(e)",
        {"sid": snapshot_id},
    )
    row = result.get_next() if result.has_next() else [0]
    return int(row[0])


def entity_qualified_names(storage: Storage, snapshot_id: str) -> list[str]:
    result = storage.conn.execute(
        "MATCH (e:Entity {snapshot_id: $sid}) "
        "RETURN e.qualified_name ORDER BY e.qualified_name",
        {"sid": snapshot_id},
    )
    names: list[str] = []
    while result.has_next():
        names.append(str(result.get_next()[0]))
    return names


def edge_exists(
    storage: Storage,
    *,
    snapshot_id: str,
    edge_type: str,
    source_id: str,
    target_id: str,
    repository_id: str | None = None,
) -> bool:
    rel = EDGE_REL_TABLE[edge_type]
    src = source_id
    tgt = target_id
    if repository_id is not None:
        src = resolve_endpoint_physical_id(
            source_id, snapshot_id=snapshot_id, repository_id=repository_id
        )
        tgt = resolve_endpoint_physical_id(
            target_id, snapshot_id=snapshot_id, repository_id=repository_id
        )
    result = storage.conn.execute(
        f"MATCH (a)-[r:{rel}]->(b) "
        f"WHERE r.snapshot_id = $sid AND a.id = $src AND b.id = $tgt "
        f"RETURN count(r)",
        {"sid": snapshot_id, "src": src, "tgt": tgt},
    )
    row = result.get_next() if result.has_next() else [0]
    return int(row[0]) > 0
