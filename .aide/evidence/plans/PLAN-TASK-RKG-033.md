---
key: PLAN-TASK-RKG-033
group: evidence
system: SYS-RKG
revision: 1
type: implementation-plan
task: TASK-RKG-033
---
# PLAN-TASK-RKG-033 — Public conversation extension

1. RED: tests/integration/test_conversation_contract.py checks coherent nonsecret capabilities, validated vi/en/null locale before writes, unchanged default fingerprint, stored metadata replay/history, opt-in unavailable transcript and exact evidence lookup/ownership/index/path rejection.
2. GREEN: api/conversations.py validates locale and strict revision, exposes all four capability features together, includes persisted metadata and stored flags, batches ordered candidates with no per-ID queries/reordering, supports include_unavailable while preserving default410 and state.
3. GREEN: conversations/citations.py resolves exact persisted turn citation after conversation/turn ownership/index/pin checks. Return safe relative provenance/location only; filesystem lines null; no entity-detail substitution or source excerpt.
4. Verify JSON Schema public payloads plus HTTP/session/persistence regression with synthetic fixtures, Ruff/diff and current code/contract hashes; freeze independent adversarial review package (max two rounds), no self-review or human signature.

Context refresh and status in_progress happen after dependency TASK032 completes. Existing signed normative contracts remain unchanged. No live provider/operator DB access.
