---
key: TEST-RKG-STORAGE-SNAPSHOTS-001
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-013
captured_at: 2026-09-24
captured_against:
  artifacts:
    - { key: TASK-RKG-013, revision: 3 }
    - { key: TBL-RKG-GRAPH, revision: 9 }
    - { key: DDL-RKG-GRAPH, path: .aide/tech-specs/RKG-GRAPH/schema/DDL-RKG-GRAPH.cypher }
    - { key: FR-RKG-001, revision: 11 }
    - { key: FR-RKG-002, revision: 8 }
    - { key: API-RKG-CORE-v1, revision: 9 }
  pins:
    cpython: "3.12.14"
    kuzu: "0.11.3"
command: uv run pytest tests/integration/test_schema_migrate.py tests/integration/test_storage_lifecycle.py tests/integration/test_ddl_execute.py -q
result: pass
---

# TEST-RKG-STORAGE-SNAPSHOTS-001

Pinned Kùzu **0.11.3** on CPython **3.12.14** verified storage/graph behaviour for
TASK-RKG-013:

| Coverage | Tests |
| --- | --- |
| Fresh bootstrap + SchemaMeta | `test_fresh_storage_bootstraps_schema_meta` |
| Previous-schema migrate retains DEPENDS_ON | `test_migrate_previous_schema_retains_depends_on_edges` |
| DDL executes on pin | `test_ddl_rkg_graph_executes` |
| AC-RKG-066 CRUD/list | `test_ac066_repository_crud_and_list_order` |
| AC-RKG-067 revision + source immutable | `test_ac067_optimistic_revision_and_source_immutable` |
| AC-RKG-007/008/068 publish/reindex | `test_ac007_008_068_publish_reindex_and_failed_keeps_active` |
| AC-RKG-069 activate | `test_ac069_activate_switches_pointer_only` |
| AC-RKG-070 snapshot delete guards | `test_ac070_snapshot_delete_guards` |
| AC-RKG-071 repository delete guards | `test_ac071_repository_delete_guards` |
| Ownership mismatch → not_found | `test_ownership_mismatch_is_not_found` |

Full suite after close-out: `uv run pytest tests/ -q` → **21 passed**.
No production user database was dropped; migration used an ephemeral v0 fixture.
