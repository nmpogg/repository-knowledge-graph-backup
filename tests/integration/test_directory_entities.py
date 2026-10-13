"""Directory indexing/API and transactional legacy snapshot migration."""

from pathlib import Path
from types import SimpleNamespace

import kuzu
import pytest
from fastapi.testclient import TestClient

from rkg.api import create_app
from rkg.domain import (
    Edge,
    EdgeType,
    Entity,
    EntityType,
    Evidence,
    FactBatch,
    edge_id,
    evidence_id,
    source_entity_id,
)
from rkg.graph import publish_fact_batch
from rkg.ingestion import LocalSourcePolicy
from rkg.jobs import IndexCoordinator
from rkg.storage import Storage
from rkg.storage._util import CURRENT_SCHEMA_VERSION, fetch_all, parse_ddl_statements
from rkg.storage.conversations import create_conversation
from rkg.storage.migrate import execute_statements, migrate, read_schema_version
from rkg.storage.repositories import create_repository
from tests.integration.storage_helpers import publish_meta


def _legacy_database(path: Path, source: Path):
    db = kuzu.Database(str(path))
    conn = kuzu.Connection(db)
    ddl = Path(__file__).parents[1] / "fixtures/storage/ddl_v1.cypher"
    execute_statements(conn, parse_ddl_statements(ddl.read_text(encoding="utf-8")))
    conn.execute("CREATE (:SchemaMeta {id: 'current', version: 1})")
    repo = create_repository(
        conn, display_name="Fixture", source_type="local", source_locator=str(source)
    )
    file = "pkg/unit.py"
    unit = Entity(
        source_entity_id(repo.id, file, "SourceUnit", "pkg.unit"),
        repo.id,
        "old",
        EntityType.SOURCE_UNIT,
        "unit.py",
        "pkg.unit",
        file,
    )
    namespace = Entity(
        source_entity_id(repo.id, file, "Namespace", "pkg.unit"),
        repo.id,
        "old",
        EntityType.NAMESPACE,
        "unit",
        "pkg.unit",
        file,
    )
    rule = "RKG.python.structure.v1"
    ref = Evidence(evidence_id("old", file, 1, 1, rule), "old", file, 1, 1, rule)
    edge = Edge(
        edge_id("old", EdgeType.CONTAINS, unit.id, namespace.id),
        "old",
        EdgeType.CONTAINS,
        unit.id,
        namespace.id,
        rule,
        (ref.id,),
    )
    publish_fact_batch(
        SimpleNamespace(conn=conn),
        FactBatch(repo.id, "old", (unit, namespace), (edge,), (ref,)),
        publish_meta(),
    )
    conversation = create_conversation(
        conn, repository_id=repo.id, snapshot_id="old", title="Fixture"
    )
    return db, conn, repo.id, namespace.id, conversation.id


def _relationships(conn):
    return fetch_all(
        conn,
        "MATCH (a:Entity)-[r:CONTAINS]->(b:Entity) "
        "WHERE r.snapshot_id='old' RETURN a.id,b.id,r.edge_id,r.rule,r.evidence_ids",
    )


def test_v1_migration_retains_namespace_snapshot_and_new_api_directory(tmp_path):
    source = tmp_path / "source"
    (source / "pkg").mkdir(parents=True)
    (source / "pkg/unit.py").write_text("def call(): pass\n")
    path = tmp_path / "graph"
    db, conn, repo, namespace, conversation = _legacy_database(path, source)
    before = _relationships(conn)
    conn.close()
    db.close()
    with Storage(path) as storage:
        assert read_schema_version(storage.conn) == CURRENT_SCHEMA_VERSION
        assert _relationships(storage.conn) == before
        assert storage.get_repository(repo).active_snapshot_id == "old"
        assert storage.get_conversation(conversation).snapshot_id == "old"
        assert storage.get_snapshot(repo, "old").adapter_versions == {"python": "1.0.0"}
        assert migrate(storage.conn) == CURRENT_SCHEMA_VERSION  # Idempotent.
        policy = LocalSourcePolicy((tmp_path,))
        job = IndexCoordinator(storage, policy).run(repo)
        assert job.status == "succeeded"
        snapshot = job.report["snapshot_id"]
        assert job.report["files"]["considered"] == 1
        assert job.report["entities_by_type"]["Directory"] == 1
        assert "Namespace" not in job.report["entities_by_type"]
        assert storage.get_snapshot(repo, snapshot).schema_version == str(
            CURRENT_SCHEMA_VERSION
        )
        with TestClient(
            create_app(storage, policy, session_token="fixture"),
            base_url="http://127.0.0.1",
        ) as client:
            directories = client.get(
                "/api/v1/entities",
                params={"snapshot_id": snapshot, "type": "Directory"},
            ).json()
            directory = directories["items"][0]
            assert directory["name"] == directory["file_path"] == "pkg"
            assert directory["start_line"] is None
            detail = client.get(
                f"/api/v1/entities/{directory['id']}", params={"snapshot_id": snapshot}
            ).json()
            assert detail["evidence"][0]["provenance"] == "filesystem"
            assert detail["evidence"][0]["file_path"] == "pkg/unit.py"
            legacy = client.get(
                f"/api/v1/entities/{namespace}", params={"snapshot_id": "old"}
            ).json()
            assert legacy["type"] == "Namespace"
            graph = client.get(
                "/api/v1/subgraph",
                params={
                    "snapshot_id": snapshot,
                    "root_id": directory["id"],
                    "depth": 3,
                },
            ).json()
            assert {e["type"] for e in graph["nodes"]} == {
                "Directory",
                "SourceUnit",
                "Callable",
            }
            context = client.post(
                "/api/v1/context",
                headers={"X-RKG-Session": "fixture"},
                json={"snapshot_id": snapshot, "root_id": directory["id"]},
            )
            assert context.status_code == 200
            assert any(
                e["provenance"] == "filesystem" for e in context.json()["evidence"]
            )
        assert _relationships(storage.conn) == before
        assert storage.get_conversation(conversation).snapshot_id == "old"


def test_v1_migration_failure_rolls_back_table_and_metadata(tmp_path):
    db, conn, *_ = _legacy_database(tmp_path / "graph", tmp_path)
    before = _relationships(conn)

    class Failure:
        def execute(self, query, params=None):
            if "SET m.version" in query:
                raise RuntimeError("injected migration failure")
            return conn.execute(query, params or {})

    try:
        with pytest.raises(RuntimeError, match="injected"):
            migrate(Failure())
        assert read_schema_version(conn) == 1
        assert _relationships(conn) == before
        assert migrate(conn) == CURRENT_SCHEMA_VERSION
        assert _relationships(conn) == before
    finally:
        conn.close()
        db.close()
