"""TASK-RKG-030: temporary DB migration and durable conversation JSON."""

import json
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import kuzu
import pytest

from rkg.conversations import (
    ProviderResult,
    begin_turn,
    create_conversation,
    list_turns,
    submit_turn,
)
from rkg.graph import publish_fact_batch
from rkg.storage import Storage
from rkg.storage._util import (
    DDL_PATH,
    EDGE_REL_TABLE,
    dumps_json,
    fetch_all,
    parse_ddl_statements,
    ts_param,
)
from rkg.storage.conversations import create_conversation as create_row
from rkg.storage.migrate import execute_statements, migrate, read_schema_version
from rkg.storage.repositories import create_repository
from tests.integration.storage_helpers import publish_meta, simple_batch


def _metadata(kind="clarification"):
    return {
        "version": 1,
        "language": "vi",
        "kind": kind,
        "subject": None,
        "coverage": "not_applicable",
        "retrieval_truncated": None,
        "history_truncated": False,
        "limitations": [],
        "insufficient_reason": None,
    }


def _intent(ids):
    return {
        "question": "endpoint login gọi những hàm nào? password=fixture-secret",
        "ui_locale": "en",
        "language": "vi",
        "relation_types": ["calls"],
        "direction": "outgoing",
        "entity_type": "Endpoint",
        "candidate_ids": ids,
    }


def _conversation(store):
    repo = store.create_repository(
        display_name="Fixture", source_type="local", source_locator="seed"
    )
    publish_fact_batch(store, simple_batch(repo.id, "old"), publish_meta())
    return create_conversation(store, repository_id=repo.id, snapshot_id="old")


def _v2(path):
    db = kuzu.Database(str(path))
    conn = kuzu.Connection(db)
    ddl = (Path(__file__).parents[1] / "fixtures/storage/ddl_v1.cypher").read_text()
    ddl = ddl.replace(
        "CREATE REL TABLE CONTAINS(FROM Entity TO Entity,",
        "CREATE REL TABLE CONTAINS(FROM Repository TO Entity, FROM Entity TO Entity,",
    )
    execute_statements(conn, parse_ddl_statements(ddl))
    conn.execute(
        "CREATE (:SchemaMeta {id:'current', version:2, applied_at:timestamp($ts)})",
        {"ts": ts_param()},
    )
    repo = create_repository(
        conn, display_name="Fixture", source_type="local", source_locator="seed"
    )
    publish_fact_batch(
        SimpleNamespace(conn=conn), simple_batch(repo.id, "old"), publish_meta()
    )
    state = {"focus_entity_id": "legacy", "pending_candidate_ids": ["b", "a"]}
    conv = create_row(conn, repository_id=repo.id, snapshot_id="old", state=state)
    conn.execute(
        "CREATE (:Turn {id:'legacy', conversation_id:$cid, sequence:1, "
        "client_request_id:'legacy-key', request_hash:'legacy-hash', "
        "question:'fixture', status:'answered', answer:'fixture', "
        "claims_json:'[]', citations_json:'[]', context_turn_ids:[], "
        "created_at:timestamp($ts), updated_at:timestamp($ts)})",
        {"cid": conv.id, "ts": ts_param()},
    )
    return db, conn, conv.id


def _old_rows(conn):
    queries = [
        "MATCH (t:Turn) RETURN t.id,t.conversation_id,t.sequence,t.client_request_id,"
        "t.request_hash,t.question,t.resolved_question,t.status,t.answer,"
        "t.claims_json,t.citations_json,t.context_turn_ids,t.usage_json,t.error_code,"
        "t.created_at,t.updated_at ORDER BY t.id",
        "MATCH (c:Conversation) RETURN c.* ORDER BY c.id",
        "MATCH (s:Snapshot) RETURN s.* ORDER BY s.id",
        "MATCH (r:Repository) RETURN r.* ORDER BY r.id",
        "MATCH (e:Evidence) RETURN e.* ORDER BY e.id",
        "MATCH (a)-[r:CONTAINS]->(b) RETURN a.id,b.id,r.edge_id,r.evidence_ids "
        "ORDER BY r.edge_id",
    ]
    return [fetch_all(conn, q) for q in queries]


def _columns(conn):
    return fetch_all(conn, "CALL table_info('Turn') RETURN name,type")


def test_fresh_database_bootstraps_physical_three(tmp_path):
    with Storage(tmp_path / "fresh") as store:
        assert read_schema_version(store.conn) == 3
        assert ["response_metadata_json", "STRING"] in _columns(store.conn)


def test_v2_upgrade_preserves_legacy_rows_and_verified_replay(tmp_path):
    db, conn, cid = _v2(tmp_path / "legacy")
    try:
        before = _old_rows(conn)
        assert migrate(conn) == 3
        assert _old_rows(conn) == before
        assert fetch_all(conn, "MATCH (t:Turn) RETURN t.response_metadata_json") == [
            [None]
        ]
        stamp = fetch_all(conn, "MATCH (m:SchemaMeta) RETURN m.applied_at")
        assert migrate(conn) == 3
        assert fetch_all(conn, "MATCH (m:SchemaMeta) RETURN m.applied_at") == stamp
        assert _old_rows(conn) == before
    finally:
        conn.close()
        db.close()
    with Storage(tmp_path / "legacy") as store:
        assert list_turns(store, cid)[0].response_metadata is None
        assert store.get_conversation(cid).state["pending_candidate_ids"] == ["b", "a"]


def test_v2_migration_fault_rolls_back_metadata_column_and_all_rows(tmp_path):
    db, conn, _ = _v2(tmp_path / "failure")
    before = _old_rows(conn)

    class Failure:
        def execute(self, query, params=None):
            if "SET m.version" in query:
                raise RuntimeError("injected migration failure")
            return conn.execute(query, params or {})

    try:
        with pytest.raises(RuntimeError, match="injected"):
            migrate(Failure())
        assert read_schema_version(conn) == 2
        assert _old_rows(conn) == before
        assert not any(c[0] == "response_metadata_json" for c in _columns(conn))
        assert migrate(conn) == 3
    finally:
        conn.close()
        db.close()


@pytest.mark.parametrize(
    "version,column", [(2, "STRING"), (3, None), (3, "INT64"), (4, None)]
)
def test_partial_or_future_shapes_refuse_without_writes(tmp_path, version, column):
    db, conn, _ = _v2(tmp_path / "shape")
    try:
        conn.execute("MATCH (m:SchemaMeta) SET m.version=$v", {"v": version})
        if column:
            conn.execute(f"ALTER TABLE Turn ADD response_metadata_json {column}")
        before, columns = _old_rows(conn), _columns(conn)
        with pytest.raises(RuntimeError):
            migrate(conn)
        assert read_schema_version(conn) == version
        assert _old_rows(conn) == before
        assert _columns(conn) == columns
    finally:
        conn.close()
        db.close()


def test_pending_intent_metadata_survive_restart_replay_and_errors(tmp_path):
    path = tmp_path / "durable"
    with Storage(path) as store:
        conv = _conversation(store)
        result = ProviderResult(
            status="needs_clarification",
            answer="fixture",
            candidate_entity_ids=("b", "a"),
            response_metadata=_metadata(),
            pending_intent_update="replace",
            pending_intent=_intent(["b", "a"]),
        )
        submitted = submit_turn(
            store,
            conv.id,
            question="fixture",
            client_request_id="first",
            expected_revision=1,
            provider=lambda _: result,
        )
        committed = deepcopy(submitted.conversation.state)
        assert committed["pending_intent"]["candidate_ids"] == ["b", "a"]
        assert "fixture-secret" not in dumps_json(committed)
        assert submitted.turn.response_metadata == _metadata()
    with Storage(path) as store:
        seen = []

        def should_not_run(_):
            raise AssertionError("replay called provider")

        replay = submit_turn(
            store,
            conv.id,
            question="fixture",
            client_request_id="first",
            expected_revision=1,
            provider=should_not_run,
        )
        assert not replay.created and replay.turn.response_metadata == _metadata()
        assert replay.conversation.state == committed

        def greeting(ctx):
            seen.append(deepcopy(ctx.pending_intent))
            ctx.pending_intent["question"] = "provider attempted mutation"
            return ProviderResult(
                status="answered",
                answer="fixture",
                response_metadata=_metadata("greeting"),
                pending_intent_update="preserve",
            )

        greet = submit_turn(
            store,
            conv.id,
            question="hello",
            client_request_id="greeting",
            expected_revision=2,
            provider=greeting,
        )
        assert seen == [committed["pending_intent"]]
        assert greet.conversation.state == committed
        bad = submit_turn(
            store,
            conv.id,
            question="fixture",
            client_request_id="bad",
            expected_revision=3,
            provider=lambda _: ProviderResult(
                status="answered",
                response_metadata=_metadata(),
                pending_intent_update="clear",
            ),
        )
        assert bad.turn.status == "failed"
        assert bad.turn.error_code == "llm_malformed_response"
        assert bad.conversation.state == committed
        begin_turn(
            store,
            conv.id,
            question="fixture",
            client_request_id="pending",
            expected_revision=4,
        )
    with Storage(path) as store:
        assert list_turns(store, conv.id)[-1].status == "interrupted"
        assert store.get_conversation(conv.id).state == committed
        partial = {
            **_metadata("answer"),
            "subject": {
                "entity_id": "b",
                "type": "Callable",
                "name": "login",
                "qualified_name": "app.login",
                "method": None,
                "path": None,
            },
            "coverage": "partial",
            "retrieval_truncated": True,
            "limitations": ["max_nodes"],
        }
        done = submit_turn(
            store,
            conv.id,
            question="1",
            client_request_id="choice",
            expected_revision=5,
            provider=lambda _: ProviderResult(
                status="answered",
                answer="fixture",
                response_metadata=partial,
                focus_entity_id="b",
                pending_intent_update="clear",
            ),
        )
        assert done.conversation.state["pending_intent"] is None
        assert done.conversation.state["pending_candidate_ids"] == []
        assert done.conversation.state["focus_entity_id"] == "b"
    with Storage(path) as store:
        assert list_turns(store, conv.id)[-1].response_metadata == partial


@pytest.mark.parametrize("invalid", ["order", "unknown", "bytes"])
def test_invalid_terminal_json_fails_without_changing_committed_intent(
    tmp_path,
    invalid,
    caplog,
):
    with Storage(tmp_path / "invalid") as store:
        conv = _conversation(store)
        first = submit_turn(
            store,
            conv.id,
            question="fixture",
            client_request_id="first",
            expected_revision=1,
            provider=lambda _: ProviderResult(
                status="needs_clarification",
                candidate_entity_ids=("b", "a"),
                response_metadata=_metadata(),
                pending_intent_update="replace",
                pending_intent=_intent(["b", "a"]),
            ),
        )
        if invalid == "bytes":
            meta = {
                **_metadata("answer"),
                "coverage": "complete",
                "retrieval_truncated": False,
                "subject": {
                    "entity_id": "b",
                    "type": "Callable",
                    "name": "界" * 1900,
                    "qualified_name": "界" * 1900,
                    "method": None,
                    "path": None,
                },
            }
            result = ProviderResult(
                status="answered",
                response_metadata=meta,
                pending_intent_update="clear",
            )
        else:
            intent = _intent(["a", "b"] if invalid == "order" else ["b", "a"])
            if invalid == "unknown":
                intent["raw_source"] = "fixture"
            result = ProviderResult(
                status="needs_clarification",
                candidate_entity_ids=("b", "a"),
                response_metadata=_metadata(),
                pending_intent_update="replace",
                pending_intent=intent,
            )
        failed = submit_turn(
            store,
            conv.id,
            question="fixture",
            client_request_id="invalid",
            expected_revision=2,
            provider=lambda _: result,
        )
        assert failed.turn.status == "failed"
        assert failed.turn.error_code == (
            "llm_budget_exceeded" if invalid == "bytes" else "llm_malformed_response"
        )
        assert failed.turn.response_metadata is None and failed.turn.answer is None
        assert failed.conversation.state == first.conversation.state
        assert "fixture-secret" not in "\n".join(r.getMessage() for r in caplog.records)


def test_terminal_state_write_failure_rolls_back_turn_and_metadata(
    tmp_path, monkeypatch
):
    import rkg.conversations.service as service

    with Storage(tmp_path / "atomic") as store:
        conv = _conversation(store)
        before = deepcopy(conv.state)

        def fault(*_, **__):
            raise RuntimeError("injected terminal failure")

        monkeypatch.setattr(service, "write_state", fault)
        with pytest.raises(RuntimeError, match="injected terminal"):
            submit_turn(
                store,
                conv.id,
                question="hello",
                client_request_id="atomic",
                expected_revision=1,
                provider=lambda _: ProviderResult(
                    status="answered",
                    answer="fixture",
                    response_metadata=_metadata("greeting"),
                    pending_intent_update="preserve",
                ),
            )
        turn = list_turns(store, conv.id)[0]
        assert turn.status == "pending" and turn.answer is None
        assert turn.response_metadata is None
        assert store.get_conversation(conv.id).state == before


def test_future_metadata_reads_unknown_without_backfill(tmp_path):
    with Storage(tmp_path / "future") as store:
        conv = _conversation(store)
        done = submit_turn(
            store,
            conv.id,
            question="hello",
            client_request_id="future",
            expected_revision=1,
            provider=lambda _: ProviderResult(status="answered"),
        )
        raw = dumps_json({"version": 9, "coverage": "complete"})
        store.conn.execute(
            "MATCH (t:Turn {id:$id}) SET t.response_metadata_json=$raw",
            {"id": done.turn.id, "raw": raw},
        )
        assert list_turns(store, conv.id)[0].response_metadata is None
        assert fetch_all(
            store.conn, "MATCH (t:Turn) RETURN t.response_metadata_json"
        ) == [[raw]]


def _database_snapshot(conn):
    """Compare schema, stamps and every fixture row without dumping payloads."""
    tables = sorted(fetch_all(conn, "CALL show_tables() RETURN name,type"))
    result = {}
    for name, kind in tables:
        properties = fetch_all(conn, f"CALL table_info('{name}') RETURN *")
        if kind == "NODE":
            connections = []
            rows = fetch_all(conn, f"MATCH (n:{name}) RETURN n ORDER BY n.id")
        else:
            connections = fetch_all(conn, f"CALL show_connection('{name}') RETURN *")
            rows = fetch_all(conn, f"MATCH (a)-[r:{name}]->(b) RETURN a.id,b.id,r")
        result[name] = (kind, properties, connections, rows)
    # These read APIs omit multiplicity, so also compare native schema metadata.
    with TemporaryDirectory(prefix="rkg-test-schema-") as folder:
        target = Path(folder) / "schema"
        conn.execute(
            f"EXPORT DATABASE {json.dumps(target.as_posix())} (schema_only=true)"
        )
        assert {p.name for p in target.iterdir()} == {"schema.cypher"}
        result["_native_schema"] = (target / "schema.cypher").read_text()
    return result


def _schema_fixture(path, version):
    if version in (2, 3):
        db, conn, _ = _v2(path)
        if version == 3:
            migrate(conn)
        return db, conn
    from rkg.storage import PREVIOUS_DDL_V0

    db = kuzu.Database(str(path))
    conn = kuzu.Connection(db)
    ddl = (
        PREVIOUS_DDL_V0
        if version == 0
        else (Path(__file__).parents[1] / "fixtures/storage/ddl_v1.cypher").read_text()
    )
    execute_statements(conn, parse_ddl_statements(ddl))
    if version == 1:
        conn.execute("CREATE (:SchemaMeta {id:'current', version:1})")
    return db, conn


@pytest.mark.parametrize(
    "version,defect",
    [
        (0, "missing_column"),
        (1, "wrong_type"),
        (1, "extra_meta"),
        (2, "missing_column"),
        (2, "wrong_type"),
        (2, "extra_meta"),
        (2, "missing_table"),
        (2, "wrong_rel"),
        (2, "wrong_primary_key"),
        (2, "extra_table"),
        (2, "missing_current"),
        (3, "missing_column"),
        (3, "extra_meta"),
    ],
)
def test_finding001_rejects_full_invalid_shape_before_any_write(
    tmp_path,
    version,
    defect,
):
    db, conn = _schema_fixture(tmp_path / "invalid-shape", version)
    try:
        if defect in {"missing_column", "wrong_type"}:
            conn.execute("ALTER TABLE Turn DROP usage_json")
            if defect == "wrong_type":
                conn.execute("ALTER TABLE Turn ADD usage_json INT64")
        elif defect == "extra_meta":
            conn.execute("CREATE (:SchemaMeta {id:'extra',version:2})")
        elif defect == "missing_table":
            conn.execute("DROP TABLE Diagnostic")
        elif defect == "wrong_rel":
            conn.execute("DROP TABLE CALLS")
            conn.execute(
                "CREATE REL TABLE CALLS(FROM Repository TO Entity, "
                "edge_id STRING,snapshot_id STRING,rule STRING,evidence_ids STRING[])"
            )
        elif defect == "wrong_primary_key":
            old = (
                Path(__file__).parents[1] / "fixtures/storage/ddl_v1.cypher"
            ).read_text()
            turn_ddl = next(
                s
                for s in parse_ddl_statements(old)
                if s.startswith("CREATE NODE TABLE Turn(")
            )
            turn_ddl = turn_ddl.replace("id STRING PRIMARY KEY", "id STRING").replace(
                "client_request_id STRING", "client_request_id STRING PRIMARY KEY"
            )
            conn.execute("DROP TABLE Turn")
            conn.execute(turn_ddl)
        elif defect == "extra_table":
            conn.execute("CREATE NODE TABLE Unexpected(id STRING PRIMARY KEY)")
        elif defect == "missing_current":
            conn.execute("MATCH (m:SchemaMeta) DELETE m")
        before = _database_snapshot(conn)
        with pytest.raises(RuntimeError):
            migrate(conn)
        assert _database_snapshot(conn) == before
    finally:
        conn.close()
        db.close()


@pytest.mark.parametrize("version", [0, 1, 2, 3])
def test_finding001_supported_versions_upgrade_and_noop(tmp_path, version):
    db, conn = _schema_fixture(tmp_path / "supported", version)
    try:
        assert migrate(conn) == 3
        before = _database_snapshot(conn)
        assert migrate(conn) == 3
        assert _database_snapshot(conn) == before
    finally:
        conn.close()
        db.close()


def _pending_conversation(store):
    conv = _conversation(store)
    first = submit_turn(
        store,
        conv.id,
        question="fixture",
        client_request_id="focus",
        expected_revision=1,
        provider=lambda _: ProviderResult(
            status="answered",
            focus_entity_id="legacy",
        ),
    )
    return submit_turn(
        store,
        conv.id,
        question="fixture",
        client_request_id="clarify",
        expected_revision=first.conversation.revision,
        provider=lambda _: ProviderResult(
            status="needs_clarification",
            candidate_entity_ids=("b", "a"),
            response_metadata=_metadata(),
            pending_intent_update="replace",
            pending_intent=_intent(["b", "a"]),
        ),
    )


@pytest.mark.parametrize(
    "kind,coverage,fact_field",
    [
        ("answer", "unknown", "claims"),
        ("answer", "not_applicable", "claims"),
        ("clarification", "not_applicable", "claims"),
        ("clarification", "not_applicable", "citations"),
        ("insufficient", "unknown", "claims"),
        ("insufficient", "unknown", "citations"),
    ],
)
def test_finding002_bad_metadata_cannot_publish_facts_or_change_state(
    tmp_path,
    kind,
    coverage,
    fact_field,
):
    path = tmp_path / "metadata-guard"
    with Storage(path) as store:
        first = _pending_conversation(store)
        cid = first.conversation.id
        meta = {**_metadata(kind), "coverage": coverage}
        if kind == "answer":
            meta.update(
                retrieval_truncated=False,
                subject={
                    "entity_id": "b",
                    "type": "Callable",
                    "name": "login",
                    "qualified_name": "app.login",
                    "method": None,
                    "path": None,
                },
            )
        if kind == "insufficient":
            meta.update(
                retrieval_truncated=None, insufficient_reason="intent_unresolved"
            )
        status = {
            "answer": "answered",
            "clarification": "needs_clarification",
            "insufficient": "insufficient_evidence",
        }[kind]
        facts = {
            fact_field: (
                {"text": "fixture"}
                if fact_field == "claims"
                else {"snapshot_id": "old", "evidence_id": "fixture"},
            )
        }
        result = ProviderResult(
            status=status,
            answer="fixture",
            response_metadata=meta,
            focus_entity_id="other",
            **facts,
        )
        failed = submit_turn(
            store,
            cid,
            question="fixture",
            client_request_id="bad",
            expected_revision=first.conversation.revision,
            provider=lambda _: result,
        )
        assert failed.turn.status == "failed"
        assert failed.turn.error_code == "llm_malformed_response"
        assert failed.turn.answer is None and failed.turn.response_metadata is None
        assert failed.turn.claims is None and failed.turn.citations is None
        assert failed.conversation.state == first.conversation.state
    with Storage(path) as store:

        def unexpected(_):
            raise AssertionError("replay invoked provider")

        replay = submit_turn(
            store,
            cid,
            question="fixture",
            client_request_id="bad",
            expected_revision=first.conversation.revision,
            provider=unexpected,
        )
        assert not replay.created and replay.turn.status == "failed"
        assert replay.conversation.state == first.conversation.state


@pytest.mark.parametrize(
    "action,focus,payload",
    [
        ("clear", None, None),
        ("replace", None, None),
        (None, "other", None),
        ("preserve", "other", None),
        (None, None, "candidates"),
        ("preserve", None, "intent"),
    ],
)
def test_finding003_inconsistent_greeting_fails_without_state_changes(
    tmp_path,
    action,
    focus,
    payload,
):
    path = tmp_path / "greeting-guard"
    with Storage(path) as store:
        first = _pending_conversation(store)
        result = ProviderResult(
            status="answered",
            answer="fixture",
            response_metadata=_metadata("greeting"),
            pending_intent_update=action,
            focus_entity_id=focus,
            candidate_entity_ids=("b",) if payload == "candidates" else (),
            pending_intent=_intent(["b", "a"]) if payload == "intent" else None,
        )
        failed = submit_turn(
            store,
            first.conversation.id,
            question="hello",
            client_request_id="bad-greet",
            expected_revision=first.conversation.revision,
            provider=lambda _: result,
        )
        assert failed.turn.status == "failed"
        assert failed.turn.error_code == "llm_malformed_response"
        assert failed.turn.answer is None and failed.turn.response_metadata is None
        assert failed.conversation.state == first.conversation.state
    with Storage(path) as store:
        assert (
            store.get_conversation(first.conversation.id).state
            == first.conversation.state
        )


@pytest.mark.parametrize(
    "action,focus", [(None, None), ("preserve", None), ("preserve", "legacy")]
)
def test_finding003_valid_greeting_preserves_focus_pending_and_replay(
    tmp_path,
    action,
    focus,
):
    with Storage(tmp_path / "greeting-valid") as store:
        first = _pending_conversation(store)
        result = ProviderResult(
            status="answered",
            answer="fixture",
            response_metadata=_metadata("greeting"),
            pending_intent_update=action,
            focus_entity_id=focus,
        )
        greet = submit_turn(
            store,
            first.conversation.id,
            question="hello",
            client_request_id="greet",
            expected_revision=first.conversation.revision,
            provider=lambda _: result,
        )
        assert greet.turn.status == "answered"
        assert greet.conversation.state == first.conversation.state
        replay = submit_turn(
            store,
            first.conversation.id,
            question="hello",
            client_request_id="greet",
            expected_revision=first.conversation.revision,
            provider=lambda _: pytest.fail("replay invoked provider"),
        )
        assert (
            not replay.created and replay.conversation.state == first.conversation.state
        )


@pytest.mark.parametrize("version", [2, 3])
@pytest.mark.parametrize("relation", sorted(EDGE_REL_TABLE.values()))
@pytest.mark.parametrize("multiplicity", ["MANY_ONE", "ONE_MANY", "ONE_ONE"])
def test_finding001_wrong_multiplicity_refused_on_every_relationship(
    tmp_path,
    version,
    relation,
    multiplicity,
):
    db, conn = _schema_fixture(tmp_path / "multiplicity", version)
    try:
        canonical = next(
            s
            for s in parse_ddl_statements(DDL_PATH.read_text())
            if s.startswith(f"CREATE REL TABLE {relation}(")
        )
        conn.execute(f"DROP TABLE {relation}")
        conn.execute(canonical[:-1] + f", {multiplicity})")
        before = _database_snapshot(conn)
        with pytest.raises(RuntimeError):
            migrate(conn)
        assert _database_snapshot(conn) == before
        assert read_schema_version(conn) == version
    finally:
        conn.close()
        db.close()


@pytest.mark.parametrize("version", [0, 1])
@pytest.mark.parametrize("multiplicity", ["MANY_ONE", "ONE_MANY", "ONE_ONE"])
def test_finding001_legacy_multiplicity_refused_before_any_upgrade(
    tmp_path,
    version,
    multiplicity,
):
    db, conn = _schema_fixture(tmp_path / "legacy-multiplicity", version)
    try:
        canonical = next(
            s
            for s in parse_ddl_statements(DDL_PATH.read_text())
            if s.startswith("CREATE REL TABLE CALLS(")
        )
        conn.execute("DROP TABLE CALLS")
        conn.execute(canonical[:-1] + f", {multiplicity})")
        before = _database_snapshot(conn)
        with pytest.raises(RuntimeError):
            migrate(conn)
        assert _database_snapshot(conn) == before
        assert read_schema_version(conn) == version
    finally:
        conn.close()
        db.close()


@pytest.mark.parametrize("version", [0, 1, 2, 3])
def test_finding001_canonical_calls_support_fan_out_and_fan_in(tmp_path, version):
    db, conn = _schema_fixture(tmp_path / "fan-out", version)
    try:
        assert migrate(conn) == 3
        for identifier in ("caller", "other-caller", "callee-a", "callee-b"):
            conn.execute(
                "CREATE (:Entity {id:$id,repository_id:'fixture',snapshot_id:'fixture',"
                "type:'Callable',name:$id,qualified_name:$id,attributes_json:'{}'})",
                {"id": identifier},
            )
        pairs = [
            ("caller", "callee-a"),
            ("caller", "callee-b"),
            ("other-caller", "callee-a"),
        ]
        for index, (source, target) in enumerate(pairs):
            conn.execute(
                "MATCH (a:Entity {id:$src}),(b:Entity {id:$dst}) "
                "CREATE (a)-[:CALLS {edge_id:$edge,snapshot_id:'fixture',"
                "rule:'RKG.python.calls.v1',evidence_ids:[]}]->(b)",
                {"src": source, "dst": target, "edge": f"fixture-edge-{index}"},
            )
        before = _database_snapshot(conn)
        assert migrate(conn) == 3
        assert _database_snapshot(conn) == before
        assert sorted(
            fetch_all(
                conn,
                "MATCH (a)-[r:CALLS]->(b) WHERE r.snapshot_id='fixture' "
                "RETURN a.id,b.id",
            )
        ) == sorted([list(pair) for pair in pairs])
    finally:
        conn.close()
        db.close()


def test_multiplicity_inspection_exports_only_schema_without_fixture_rows(tmp_path):
    db, conn, _ = _v2(tmp_path / "schema-only")
    observed = []
    conn.execute("MATCH (t:Turn) SET t.question='ROW_CONTENT_SENTINEL'")

    class Capture:
        def execute(self, query, params=None):
            result = conn.execute(query, params or {})
            if query.startswith("EXPORT DATABASE "):
                assert query.endswith(" (schema_only=true)")
                raw_path = query[len("EXPORT DATABASE ") : -len(" (schema_only=true)")]
                folder = Path(json.loads(raw_path))
                assert {p.name for p in folder.iterdir()} == {"schema.cypher"}
                assert (
                    "ROW_CONTENT_SENTINEL" not in (folder / "schema.cypher").read_text()
                )
                observed.append(folder.parent)
            return result

    try:
        assert migrate(Capture()) == 3
        assert observed and all(not folder.exists() for folder in observed)
        assert fetch_all(conn, "MATCH (t:Turn) RETURN t.question") == [
            ["ROW_CONTENT_SENTINEL"]
        ]
    finally:
        conn.close()
        db.close()


def test_multiplicity_inspection_failure_refuses_safely_without_writes(tmp_path):
    db, conn, _ = _v2(tmp_path / "export-failure")
    observed = []

    class Failure:
        def execute(self, query, params=None):
            if query.startswith("EXPORT DATABASE "):
                raw_path = query[len("EXPORT DATABASE ") : -len(" (schema_only=true)")]
                observed.append(Path(json.loads(raw_path)).parent)
                raise RuntimeError("PRIVATE_EXPORT_LOCATION_SENTINEL")
            return conn.execute(query, params or {})

    try:
        before = _database_snapshot(conn)
        with pytest.raises(
            RuntimeError, match="unable to verify relationship multiplicity"
        ):
            migrate(Failure())
        assert observed and all(not folder.exists() for folder in observed)
        assert _database_snapshot(conn) == before
    finally:
        conn.close()
        db.close()
