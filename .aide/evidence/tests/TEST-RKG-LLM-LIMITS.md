---
key: TEST-RKG-LLM-LIMITS
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-019
revision: 1
captured_at: 2026-09-28
captured_against:
  artifacts:
    - { key: TASK-RKG-019, revision: 5 }
    - { key: FR-RKG-005, revision: 7 }
    - { key: NFR-RKG-REL-001, revision: 8 }
  base_commit: 4ed6103a861a0b29d61e3b9584351482c873c00f
  code_tree: DIARY-TASK-RKG-019-file-hashes
command: .venv/Scripts/python.exe -m pytest tests/ -q
result: partial
---

# TEST-RKG-LLM-LIMITS

Contract tests in `tests/unit/test_llm_provider.py` passed (9 tests). They cover
schema validation, input preflight, model/query limits, output usage ceiling,
safe disabled/provider errors, and per-turn timeout. The full suite result is
116 passed, 2 skipped; one skip is the live OpenRouter smoke test because no
server-side credential is configured in this environment.

AC-RKG-063 is **partially verified** at the provider boundary. Existing
conversation validation rejects questions above 2,000 characters before its
provider callback. HTTP `422`/`504`, coordinator query execution limits, focus
preservation on timeout, and a live provider response require T-020/021
integration and live acceptance. This record does not mark AC-RKG-063 complete.
