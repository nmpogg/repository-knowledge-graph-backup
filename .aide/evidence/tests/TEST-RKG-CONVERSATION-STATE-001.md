---
key: TEST-RKG-CONVERSATION-STATE-001
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-018
revision: 1
captured_at: 2026-09-25
captured_against:
  artifacts:
    - { key: TASK-RKG-018, revision: 5 }
    - { key: FR-RKG-005, revision: 7 }
    - { key: TBL-RKG-GRAPH, revision: 9 }
    - { key: NFR-RKG-REL-001, revision: 8 }
    - { key: NFR-RKG-SEC-001, revision: 7 }
  pins:
    cpython: "3.12.14"
    kuzu: "0.11.3"
command: uv run python -m pytest tests/ -q
result: pass
---

# TEST-RKG-CONVERSATION-STATE-001

Service-layer verification for conversation persistence. HTTP mapping remains
T-016/T-021. The suite result is **65 passed, 1 skipped**.

| AC | Contract test name | Pytest |
| --- | --- | --- |
| AC-RKG-030 | TEST-RKG-HISTORY-PERSIST | `test_ac030_history_survives_restart_and_focus_is_isolated` |
| AC-RKG-031 | TEST-RKG-SNAPSHOT-PIN | `test_ac031_old_conversation_stays_pinned_when_active_moves` |
| AC-RKG-033 | TEST-RKG-TURN-GUARD | `test_ac033_conflict_idempotency_recovery_and_failed_focus` |
| AC-RKG-044 | TEST-RKG-SNAPSHOT-RETENTION | `test_ac044_cleanup_keeps_guards_and_lost_snapshot_stays_pinned` |
| AC-RKG-045 | TEST-RKG-CONVERSATION-DELETE-GUARD | `test_ac045_pending_delete_is_busy_and_other_history_remains` |
| AC-RKG-059 | TEST-RKG-TURN-REQUIRED-FIELDS | `test_ac059_missing_or_malformed_fields_do_not_mutate` |
| AC-RKG-064 | TEST-RKG-CONVERSATION-REDACTION | `test_ac064_redacts_store_and_omits_transcript_from_logs` |

Redaction unit checks: `tests/unit/test_conversation_redaction.py`.
AC-RKG-032 (history window) is not part of this task.
