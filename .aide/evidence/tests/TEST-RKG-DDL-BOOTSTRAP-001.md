---
key: TEST-RKG-DDL-BOOTSTRAP-001
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-001
captured_at: 2026-09-24
captured_against:
  artifacts:
    - { key: DDL-RKG-GRAPH, path: .aide/tech-specs/RKG-GRAPH/schema/DDL-RKG-GRAPH.cypher }
    - { key: TASK-RKG-001, revision: 5 }
  pins:
    cpython: "3.12.14"
    kuzu: "0.11.3"
command: uv run pytest tests/integration/test_ddl_execute.py -q
result: pass
---

# TEST-RKG-DDL-BOOTSTRAP-001

Pinned Kùzu **0.11.3** on CPython **3.12.14** executed every statement in
`DDL-RKG-GRAPH.cypher` against a temporary database created by
`tests/integration/test_ddl_execute.py`. No production store or migration path
was exercised (those belong to later graph tasks).
