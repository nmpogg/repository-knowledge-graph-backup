---
key: TEST-RKG-OPENROUTER-LIVE-001
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-019
revision: 1
captured_at: 2026-09-28
captured_against:
  artifacts:
    - { key: TASK-RKG-019, revision: 6 }
    - { key: OQ-RKG-001, revision: 3 }
    - { key: FR-RKG-005, revision: 7 }
    - { key: NFR-RKG-REL-001, revision: 8 }
  base_commit: 4ed6103a861a0b29d61e3b9584351482c873c00f
  code_tree: DIARY-TASK-RKG-019-r2-file-hashes
command: .venv/Scripts/python.exe -m pytest tests/ -q --tb=short --basetemp .aide/generated/task19-pytest-live -p no:cacheprovider
result: pass
---

# TEST-RKG-OPENROUTER-LIVE-001

With the server-side credential loaded into the test process, the OpenRouter
structured JSON response smoke test passed. The test asserts the selected
model's adapter returned a schema-conforming response within one model call
and the requested output-token limit. It does not store the key or response
text in this evidence.

Full current-tree result: **117 passed, 1 skipped**. The skipped test is not
the live OpenRouter test. Ruff passed. Provider-side AC-RKG-063 limits are
verified by `TEST-RKG-LLM-LIMITS`; transport-level and grounded Q&A end-to-end
acceptance remain with T-020/021.
