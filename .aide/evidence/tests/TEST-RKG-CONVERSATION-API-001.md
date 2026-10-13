---
key: TEST-RKG-CONVERSATION-API-001
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-021
revision: 1
captured_at: 2026-09-28
captured_against:
  artifacts:
    - { key: TASK-RKG-021, revision: 5 }
    - { key: FR-RKG-005, revision: 7 }
    - { key: API-RKG-CORE-v1, revision: 9 }
  base_commit: 33d1eb8dc20d61a69aa2d2bd43bebfee6e69ecd4
  code_tree: DIARY-TASK-RKG-021-file-hashes
  pins:
    cpython: "3.12.14"
---

# TEST-RKG-CONVERSATION-API-001

Verified on the working tree based on `33d1eb8`.

| Check | Result |
| --- | --- |
| `uv run pytest tests -q` | 132 passed, 4 skipped |
| `uv run ruff check src tests` | passed |
| `npm test` in `frontend` | 27 passed |
| `npx tsc -b` in `frontend` | passed |

| AC | Where |
| --- | --- |
| AC-RKG-028 | `test_create_list_followup_and_ordered_clarification` follow-up keeps pinned citation and `context_turn_ids` |
| AC-RKG-029 | same test: ordered candidate `1` replaces focus; the other conversation stays isolated |
| AC-RKG-030 | same test: delete one conversation leaves the other history; persistence remains the T-018 store |
| AC-RKG-031 | create without a snapshot id pins the active snapshot; UI offers a new conversation when active moves |
| AC-RKG-032 | `test_injection_and_history_window` reports `history_truncated` and at most six `context_turn_ids` |
| AC-RKG-033 | `test_required_fields_conflict_timeout_and_redaction`: replay, conflict, timeout leaves focus |
| AC-RKG-041 | `test_session_blocks_create_and_turn_before_provider` |
| AC-RKG-042 | `test_injection_and_history_window`: shell plan and foreign edge are `502` and do not add entities |
| AC-RKG-044 | `test_lost_snapshot_stays_pinned` plus existing cleanup guards |
| AC-RKG-045 | existing `test_conversation_delete_is_busy_while_a_turn_is_pending` in `tests/integration/test_core_api.py` |
| AC-RKG-046 | `frontend/src/pages/conversations/ConversationPage.test.tsx`: escaped markup, named candidates, citation dialog focus restore |
| AC-RKG-047 | `test_indexed_local_fixture_citation_uses_that_snapshot` |
| AC-RKG-059 | missing body and a 2001-character question return `422` with no turn |
| AC-RKG-063 | too-long question is `422` before the provider; timeout is `504` and focus stays |
| AC-RKG-064 | stored question redacts `api_key=...`; `rkg.conversation` log has no secret and no question text |
