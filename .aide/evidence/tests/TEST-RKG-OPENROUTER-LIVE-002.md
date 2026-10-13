---
key: TEST-RKG-OPENROUTER-LIVE-002
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-019
revision: 1
captured_at: 2026-09-28
captured_against:
  artifacts:
    - { key: TASK-RKG-019, revision: 7 }
    - { key: OQ-RKG-001, revision: 3 }
  base_commit: 4ed6103a861a0b29d61e3b9584351482c873c00f
  code_tree: DIARY-TASK-RKG-019-r3-file-hashes
command: .venv/Scripts/python.exe -m pytest tests/ -q --tb=short --basetemp .aide/generated/task19-retest-pytest -p no:cacheprovider
result: pass
---

# TEST-RKG-OPENROUTER-LIVE-002

The API key and model were loaded from the ignored local `.env` into the test
process, without printing or recording either value. The full current-tree
suite, including the OpenRouter live structured-response test, passed:
**118 passed, 1 skipped**. The remaining skip is unrelated to OpenRouter.
One Starlette deprecation warning was emitted by the existing HTTP test client.
