"""Author checks for L3 schemas, compatibility and isolated physical migration.

Not production chatbot implementation or independent review. Emits hashes/counts,
never conversation strings, database paths or configuration values.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import re
import subprocess
import tempfile
from pathlib import Path

import jsonschema
import kuzu

ROOT = Path(__file__).resolve().parents[1]
AIDE = ROOT / ".aide"
API = AIDE / "tech-specs/RKG-TRANSPORT/api"
GRAPH = AIDE / "tech-specs/RKG-GRAPH/schema"
LLM = AIDE / "tech-specs/RKG-CONVERSATION/llm"
OUTPUT = Path("/tmp/rkg-chatbot-l3-checks.json")
BASE_COMMIT = "86ecab6546384227d1901e24c8b8fbfc6c0e8527"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def statements(text: str) -> list[str]:
    body = "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith("//")
    )
    return [part.strip() for part in body.split(";") if part.strip()]


def rows(conn, query, params=None):
    result = conn.execute(query, params or {})
    names = result.get_column_names()
    values = []
    while result.has_next():
        values.append(dict(zip(names, result.get_next())))
    return values


def columns(conn):
    return rows(conn, "CALL table_info('Turn') RETURN *")


def version(conn):
    value = rows(conn, "MATCH (m:SchemaMeta) RETURN m.id AS id, m.version AS v")
    assert len(value) == 1 and value[0]["id"] == "current"
    return value[0]["v"]


def apply_migration(conn, migration):
    present = [p for p in columns(conn) if p["name"] == "response_metadata_json"]
    current = version(conn)
    if current == 3:
        assert len(present) == 1 and present[0]["type"] == "STRING"
        assert present[0]["default expression"] == "NULL"
        return "no_op"
    assert current == 2 and not present, "unexpected migration precondition"
    try:
        for statement in statements(migration):
            conn.execute(
                statement,
                {"applied_at": "2026-10-06T00:00:00"}
                if "$applied_at" in statement
                else {},
            )
    except Exception:
        try:
            conn.execute("ROLLBACK")
        except RuntimeError:
            pass
        raise
    assert version(conn) == 3
    return "applied"


def seed_legacy(conn, old_ddl):
    for statement in statements(old_ddl):
        conn.execute(statement)
    conn.execute(
        "CREATE (:SchemaMeta {id: 'current', version: 2, "
        "applied_at: timestamp('2026-10-01T00:00:00')})"
    )
    conn.execute(
        "CREATE (:Conversation {id: 'fixture-conv', "
        "repository_id: 'fixture-repo', snapshot_id: 'fixture-snapshot', "
        "revision: 7, state_json: $state})",
        {
            "state": json.dumps(
                {"focus_entity_id": "fixture-a", "pending_candidate_ids": ["fixture-b"]}
            )
        },
    )
    conn.execute(
        "CREATE (:Turn {id: 'fixture-turn', "
        "conversation_id: 'fixture-conv', sequence: 1, "
        "client_request_id: 'fixture-request', request_hash: 'fixture-hash', "
        "question: 'fixture-only', answer: 'fixture-only', "
        "status: 'answered', claims_json: '[]', citations_json: '[]'})"
    )
    for identity in ("fixture-a", "fixture-b"):
        conn.execute(
            "CREATE (:Entity {id: $id, snapshot_id: 'fixture-snapshot', "
            "repository_id: 'fixture-repo', type: 'Callable', "
            "name: $id, qualified_name: $id})",
            {"id": identity},
        )
    conn.execute(
        "MATCH (a:Entity {id: 'fixture-a'}), "
        "(b:Entity {id: 'fixture-b'}) CREATE (a)-[:CALLS "
        "{edge_id: 'fixture-edge', snapshot_id: 'fixture-snapshot', "
        "rule: 'RKG.fixture.calls.v1', evidence_ids: ['fixture-evidence']}]->(b)"
    )
    conn.execute(
        "CREATE (:Evidence {id: 'fixture-evidence', "
        "snapshot_id: 'fixture-snapshot', file_path: 'fixture.py', "
        "start_line: 1, end_line: 1, rule: 'RKG.fixture.calls.v1'})"
    )


def reference_rules(value, root, direction, evidence):
    """Contract fixture oracle only; not the production grounding validator."""
    edges = {
        "bridge": ("ep", "h", "handled_by", "ev0"),
        "e1": ("h", "a", "calls", "ev1"),
        "e2": ("a", "b", "calls", "ev2"),
        "e3": ("b", "table", "reads", "ev3"),
        "cycle": ("b", "h", "calls", "ev4"),
        "disconnected": ("other", "b", "calls", "ev5"),
    }
    assert value["root_id"] == root
    if value["status"] == "insufficient_evidence":
        assert not value["sections"]
        return
    assert value["sections"]
    selected = set()
    for section in value["sections"]:
        assert section["direction"] == direction
        for path in section["paths"]:
            anchor = path["anchor_id"]
            bridged = root == "ep" and anchor == "h"
            assert anchor == root or bridged
            if bridged:
                assert "ev0" in evidence
            assert len(path["edge_ids"]) + int(bridged) <= 4
            cursor, seen, kinds = anchor, {anchor}, []
            for edge_id in path["edge_ids"]:
                source, target, relation, ev = edges[edge_id]
                assert ev in evidence
                previous, following = (
                    (source, target) if direction == "outgoing" else (target, source)
                )
                assert cursor == previous and following not in seen
                seen.add(following)
                cursor = following
                kinds.append(relation)
                selected.add(edge_id)
            position = -1 if direction == "outgoing" else 0
            assert kinds[position] == section["relation"]
            remaining = kinds[:-1] if direction == "outgoing" else kinds[1:]
            assert all(kind == "calls" for kind in remaining)
    assert len(selected) <= 8


def run():
    public = json.loads((API / "SCH-RKG-CONVERSATION-v1.json").read_text())
    narrative = json.loads((LLM / "SCH-RKG-NARRATIVE-v1.json").read_text())
    planner = json.loads((LLM / "SCH-RKG-READ-PLAN-v2.json").read_text())
    oas = json.loads((API / "OAS-RKG-CONVERSATION-v1.json").read_text())
    for schema in (public, narrative, planner):
        jsonschema.Draft202012Validator.check_schema(schema)
    assert oas["openapi"] == "3.1.0"
    for path, operations in oas["paths"].items():
        for operation in operations.values():
            parameters = {
                p["name"]
                for p in operation.get("parameters", [])
                if p["in"] == "path" and p["required"]
            }
            assert parameters == set(re.findall(r"\{(.*?)\}", path))

    def validate(definition, value):
        jsonschema.validate(value, {**public, "$ref": "#/$defs/" + definition})

    request = {
        "question": "fixture-only",
        "client_request_id": "fixture-key",
        "expected_revision": 1,
    }
    validate("TurnRequest", request)
    for locale in (None, "vi", "en"):
        validate("TurnRequest", {**request, "ui_locale": locale})
    validate("TurnRequest", {**request, "client_request_id": "k" * 300})
    validate("TurnRequest", {**request, "root_id": ""})
    for enabled in (True, False):
        validate(
            "CapabilitiesResponse",
            {
                "schema_version": "rkg.conversation-capabilities/1",
                "features": [
                    "ui_locale",
                    "response_metadata_v1",
                    "exact_citation_lookup",
                    "history_unavailable",
                ],
                "provider_enabled": enabled,
            },
        )
    rejects = 0
    for change in (
        {"ui_locale": "fr"},
        {"expected_revision": True},
        {"question": "x" * 2001},
        {"arbitrary_query": "fixture"},
    ):
        try:
            validate("TurnRequest", {**request, **change})
        except jsonschema.ValidationError:
            rejects += 1
        else:
            raise AssertionError("invalid request accepted")
    # Shape-compatible legacy responses and unknown-coverage absence.
    old_turn = {
        "turn_id": "fixture-turn",
        "sequence": 1,
        "status": "answered",
        "question": "fixture-only",
        "resolved_question": None,
        "answer": "fixture-only",
        "claims": [],
        "citations": [],
        "context_turn_ids": [],
        "error_code": None,
    }
    validate("Turn", old_turn)
    metadata = {
        "version": 1,
        "language": "vi",
        "kind": "answer",
        "subject": {
            "entity_id": "fixture-a",
            "type": "Callable",
            "name": "fixture-a",
            "qualified_name": "fixture-a",
            "method": None,
            "path": None,
        },
        "coverage": "partial",
        "retrieval_truncated": True,
        "history_truncated": False,
        "limitations": ["max_nodes"],
        "insufficient_reason": None,
    }
    validate("ResponseMetadata", metadata)
    validate("Turn", {**old_turn, "response_metadata": metadata})
    try:
        validate("ResponseMetadata", {**metadata, "version": 2})
    except jsonschema.ValidationError:
        rejects += 1
    else:
        raise AssertionError("unknown metadata version accepted as v1")
    location = {
        "id": "fixture-evidence",
        "file_path": "app/fixture.py",
        "provenance": "source",
        "start_line": 1,
        "end_line": 2,
        "rule": "RKG.fixture.calls.v1",
    }
    validate("EvidenceLocation", location)
    validate(
        "EvidenceLocation",
        {**location, "provenance": "filesystem", "start_line": None, "end_line": None},
    )
    for change in (
        {"file_path": "/private/fixture"},
        {"file_path": "../fixture.py"},
        {"start_line": None},
        {"provenance": "filesystem"},
    ):
        try:
            validate("EvidenceLocation", {**location, **change})
        except jsonschema.ValidationError:
            rejects += 1
        else:
            raise AssertionError("unsafe evidence location accepted")
    valid_narrative = {
        "status": "answered",
        "root_id": "fixture-root",
        "sections": [
            {
                "relation": "calls",
                "direction": "outgoing",
                "paths": [{"anchor_id": "fixture-root", "edge_ids": ["fixture-edge"]}],
            }
        ],
    }
    jsonschema.validate(valid_narrative, narrative)
    for value in (
        {**valid_narrative, "answer": "unchecked-prose"},
        {
            **valid_narrative,
            "sections": [{"relation": "calls", "direction": "both", "paths": []}],
        },
    ):
        try:
            jsonschema.validate(value, narrative)
        except jsonschema.ValidationError:
            rejects += 1
        else:
            raise AssertionError("invalid narrative accepted")

    supported = {f"ev{i}" for i in range(6)}

    def selection(
        edge_ids, root="ep", anchor="h", relation="calls", direction="outgoing"
    ):
        return {
            "status": "answered",
            "root_id": root,
            "sections": [
                {
                    "relation": relation,
                    "direction": direction,
                    "paths": [{"anchor_id": anchor, "edge_ids": edge_ids}],
                }
            ],
        }

    semantic_passes = [
        selection(["e1"]),
        selection(["e1", "e2"]),
        selection(["e1", "e2", "e3"], relation="reads"),
        selection(["e2", "e1"], root="b", anchor="b", direction="incoming"),
        selection(
            ["e3", "e2", "e1"],
            root="table",
            anchor="table",
            relation="reads",
            direction="incoming",
        ),
    ]
    for value in semantic_passes:
        jsonschema.validate(value, narrative)
        reference_rules(
            value, value["root_id"], value["sections"][0]["direction"], supported
        )
    semantic_rejects = 0
    invalid = [
        selection(["foreign"]),
        selection(["disconnected"]),
        selection(["e1", "e2", "cycle"]),
        selection(["e1"], direction="incoming"),
        selection(["e1"], root="foreign"),
        selection(["e1"], anchor="other"),
        selection(["e1"], relation="reads"),
    ]
    for value in invalid:
        jsonschema.validate(value, narrative)
        try:
            reference_rules(value, "ep", "outgoing", supported)
        except (AssertionError, KeyError):
            semantic_rejects += 1
        else:
            raise AssertionError("semantic fixture accepted unsupported facts")
    try:
        reference_rules(selection(["e1"]), "ep", "outgoing", {"ev0"})
    except AssertionError:
        semantic_rejects += 1
    else:
        raise AssertionError("missing evidence accepted")

    tbl_text = (GRAPH / "TBL-RKG-GRAPH.md").read_text()
    ddl = (GRAPH / "DDL-RKG-GRAPH.cypher").read_text()
    fenced = re.search(r"```cypher\n(.*?)```", tbl_text, re.S).group(1)
    assert statements(ddl) == statements(fenced)
    assert "TBL-RKG-GRAPH revision 13" in ddl
    assert importlib.metadata.version("kuzu") == "0.11.3"
    migration = (GRAPH / "MIG-RKG-CHATBOT-v3.cypher").read_text()
    old_ddl = subprocess.check_output(
        [
            "git",
            "show",
            BASE_COMMIT + ":.aide/tech-specs/RKG-GRAPH/schema/DDL-RKG-GRAPH.cypher",
        ],
        cwd=ROOT,
        text=True,
    )
    for kind, count in (("NODE", 12), ("REL", 13)):
        current_names = re.findall(r"CREATE " + kind + r" TABLE (\w+)", ddl)
        old_names = re.findall(r"CREATE " + kind + r" TABLE (\w+)", old_ddl)
        assert len(current_names) == count and current_names == old_names
    with tempfile.TemporaryDirectory(prefix="rkg-l3-check-") as tmp:
        directory = Path(tmp)
        db = kuzu.Database(str(directory / "upgrade"))
        conn = kuzu.Connection(db)
        seed_legacy(conn, old_ddl)
        before_turn = rows(conn, "MATCH (t:Turn) RETURN t AS node")[0]["node"]
        before_conv = rows(conn, "MATCH (c:Conversation) RETURN c AS node")
        before_edge = rows(conn, "MATCH ()-[r:CALLS]->() RETURN r AS edge")
        before_ev = rows(conn, "MATCH (e:Evidence) RETURN e AS node")
        assert apply_migration(conn, migration) == "applied"
        after_turn = rows(conn, "MATCH (t:Turn) RETURN t AS node")[0]["node"]
        assert after_turn.pop("response_metadata_json") is None
        assert after_turn == before_turn
        assert rows(conn, "MATCH (c:Conversation) RETURN c AS node") == before_conv
        assert rows(conn, "MATCH ()-[r:CALLS]->() RETURN r AS edge") == before_edge
        assert rows(conn, "MATCH (e:Evidence) RETURN e AS node") == before_ev
        before_meta = rows(conn, "MATCH (m:SchemaMeta) RETURN m AS node")
        assert apply_migration(conn, migration) == "no_op"
        assert rows(conn, "MATCH (m:SchemaMeta) RETURN m AS node") == before_meta
        stored = json.dumps(metadata, ensure_ascii=False, sort_keys=True)
        conn.execute(
            "CREATE (:Turn {id: 'fixture-new-turn', "
            "conversation_id: 'fixture-conv', sequence: 2, status: 'answered', "
            "response_metadata_json: $value})",
            {"value": stored},
        )
        conn.close()
        db.close()
        db = kuzu.Database(str(directory / "upgrade"))
        conn = kuzu.Connection(db)
        assert (
            rows(
                conn,
                "MATCH (t:Turn {id: 'fixture-new-turn'}) "
                "RETURN t.response_metadata_json AS m",
            )[0]["m"]
            == stored
        )
        assert (
            rows(
                conn,
                "MATCH (t:Turn {id: 'fixture-turn'}) "
                "RETURN t.response_metadata_json AS m",
            )[0]["m"]
            is None
        )
        conn.close()
        db.close()

        db = kuzu.Database(str(directory / "rollback"))
        conn = kuzu.Connection(db)
        seed_legacy(conn, old_ddl)
        failing = migration.replace("SET m.version = 3", "SET m.nonexistent = 3")
        try:
            apply_migration(conn, failing)
        except RuntimeError:
            pass
        else:
            raise AssertionError("fault injection did not fail")
        assert version(conn) == 2
        assert not any(p["name"] == "response_metadata_json" for p in columns(conn))
        conn.close()
        db.close()

        db = kuzu.Database(str(directory / "fresh"))
        conn = kuzu.Connection(db)
        for statement in statements(ddl):
            conn.execute(statement)
        conn.execute("CREATE (:SchemaMeta {id: 'current', version: 3})")
        tables = rows(conn, "CALL show_tables() RETURN *")
        assert len(tables) == 25
        assert version(conn) == 3
        assert any(p["name"] == "response_metadata_json" for p in columns(conn))
        conn.close()
        db.close()

    files = [
        API / "API-RKG-CORE-v1.md",
        API / "SCH-RKG-CONVERSATION-v1.json",
        API / "OAS-RKG-CONVERSATION-v1.json",
        GRAPH / "TBL-RKG-GRAPH.md",
        GRAPH / "DDL-RKG-GRAPH.cypher",
        GRAPH / "MIG-RKG-CHATBOT-v3.cypher",
        LLM / "SCH-RKG-NARRATIVE-v1.json",
        LLM / "SCH-RKG-READ-PLAN-v2.json",
        AIDE / "design/ui/UIS-RKG-001.md",
        AIDE / "tech-specs/RKG-CONVERSATION/CON-RKG-CONVERSATION-v1.md",
        Path(__file__),
    ]
    result = {
        "mode": "author_contract_checks_not_runtime_or_independent_review",
        "source_hashes": {str(p.relative_to(ROOT)): digest(p) for p in files},
        "checks": {
            "schema_meta_validation": "passed",
            "oas_local_structure": "passed",
            "legacy_and_new_wire_fixtures": "passed",
            "negative_schema_cases": rejects,
            "reference_contract_fixture_positive": len(semantic_passes),
            "reference_contract_fixture_negative": semantic_rejects,
            "TBL_DDL_extract_equal": "passed",
            "fresh_Kuzu_DDL_25_tables": "passed",
            "atomic_v2_v3_preserves_legacy": "passed",
            "migration_replay_no_op": "passed",
            "migration_fault_rolls_back_column_and_version": "passed",
            "metadata_roundtrip_reopen": "passed",
            "production_dispatcher_and_API_UI_integration": "not_run",
            "live_provider_quality": "not_run",
        },
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["checks"]))


if __name__ == "__main__":
    run()
