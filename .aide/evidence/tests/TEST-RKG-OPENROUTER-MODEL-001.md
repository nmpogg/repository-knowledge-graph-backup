---
key: TEST-RKG-OPENROUTER-MODEL-001
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
result: pass
---

# TEST-RKG-OPENROUTER-MODEL-001

The unit contract verifies the default model when `OPENROUTER_MODEL` is absent
and verifies that an environment override is used in both the OpenRouter
request and response metadata. A live request using the local configured model
returned a schema-conforming response within the budget. Full local regression:
117 passed, 2 skipped, with the live test skipped in that separate run.
