---
key: TEST-RKG-GRAPH-READS-001
type: test-evidence
group: evidence
system: SYS-RKG
revision: 1
captured_at: 2026-09-24
captured_against:
  artifacts:
    - { key: TASK-RKG-014, revision: 5 }
    - { key: FR-RKG-003, revision: 7 }
    - { key: FR-RKG-004, revision: 6 }
  pins:
    cpython: "3.12.14"
    kuzu: "0.11.3"
command: uv run pytest tests/integration/test_graph_reads.py -q
---

# TEST-RKG-GRAPH-READS-001

Service-layer verification for AC-RKG-009 (cycle BFS), AC-RKG-036 (search order/
paging/endpoint match), AC-RKG-010 (deterministic context + char budget), and
AC-RKG-060 guards (`no_active_snapshot`, `snapshot_unavailable`, identity 404).

| Suite | Result |
| --- | --- |
| `tests/integration/test_graph_reads.py` | 5 passed |
| Full `tests/` | 26 passed |

AC-RKG-037 / AC-RKG-062 (p95 benchmark reports) not executed in this task.
