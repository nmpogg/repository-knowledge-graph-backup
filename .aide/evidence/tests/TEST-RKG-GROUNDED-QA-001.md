---
key: TEST-RKG-GROUNDED-QA-001
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-020
revision: 1
captured_at: 2026-09-28
captured_against:
  artifacts:
    - { key: TASK-RKG-020, revision: 6 }
    - { key: FR-RKG-005, revision: 7 }
    - { key: NFR-RKG-REL-001, revision: 8 }
  base_commit: 32b787516d081abfecfd2880205f9a693767f935
  code_tree: DIARY-TASK-RKG-020-file-hashes
command: .venv/Scripts/python.exe -m pytest tests/ -q --tb=short --basetemp .aide/generated/task20-full-live -p no:cacheprovider
result: pass
---

# TEST-RKG-GROUNDED-QA-001

Full current-tree suite with the server-side key/model loaded into the test
process: **129 passed, 1 skipped**. The live tests ran and passed. Eight
deterministic integration tests cover the service contract; two live tests
cover an answer with citation, a follow-up, and DB/event/dependency/technology
relations on the synthetic published graph fixture.

| AC | Verified behavior | Test location |
| --- | --- | --- |
| AC-RKG-024 | Directional relation claims use context edge/evidence IDs and pinned citation; live DB/event/dependency/technology cases | `test_db_event_dependency_and_technology_claims_are_cited`, `test_openrouter_live_db_event_dependency_technology` |
| AC-RKG-025 | Unknown, ambiguity, disabled provider, malformed plan/edge, truncation and timeout fail safely; search still works | `test_disabled_unknown_and_long_question_do_not_corrupt_graph`, `test_ambiguity_then_ordered_selection`, `test_injection_and_foreign_edge_fail_closed`, `test_truncated_retrieval_is_reported_with_valid_citation`, `test_timeout_keeps_focus_and_history_window_drops_old_turns` |
| AC-RKG-028 | Focus survives a turn and live pronoun follow-up uses it | `test_answer_and_followup_use_pinned_edges_and_citations`, `test_openrouter_live_grounded_edge_and_citation` |
| AC-RKG-029 | Ordered candidate selection clears pending state; explicit new roots replace focus | `test_ambiguity_then_ordered_selection`, `test_db_event_dependency_and_technology_claims_are_cited` |
| AC-RKG-032 | Oldest completed turns are dropped at six turns or 4,000 tokens; context IDs and truncation are returned | `test_timeout_keeps_focus_and_history_window_drops_old_turns`, `test_history_window_respects_4000_token_ceiling` |
| AC-RKG-042 | Planner schema rejects a shell action; foreign edge ID cannot become claim/citation; only pinned read services execute | `test_injection_and_foreign_edge_fail_closed` |
| AC-RKG-063 | Too-long question rejected before model call; shared budget caps operations and timeout preserves focus | `test_disabled_unknown_and_long_question_do_not_corrupt_graph`, `test_timeout_keeps_focus_and_history_window_drops_old_turns`, Task 19 `TEST-RKG-LLM-LIMITS` |
| AC-RKG-064 | Grounded output follows T-018 redaction/finalize path with no transcript in operational log | T-018 `TEST-RKG-CONVERSATION-STATE-001` and current service integration |

HTTP response codes and wire fields remain T-021. The 30-question pilot rubric
and larger multi-turn evaluation remain T-022. This record verifies the Task 20
service boundary and bounded live fixture, not those later acceptance gates.
