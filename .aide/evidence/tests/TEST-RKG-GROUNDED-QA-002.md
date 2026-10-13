---
key: TEST-RKG-GROUNDED-QA-002
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-020
revision: 2
captured_at: 2026-09-28
captured_against:
  artifacts:
    - { key: TASK-RKG-020, revision: 7 }
    - { key: FR-RKG-005, revision: 7 }
  base_commit: 32b787516d081abfecfd2880205f9a693767f935
  code_tree: DIARY-TASK-RKG-020-r2-file-hashes
command: .venv/Scripts/python.exe -m pytest tests/ -q --tb=short --basetemp .aide/generated/task20-final-live -p no:cacheprovider
result: pass
---

# TEST-RKG-GROUNDED-QA-002

Full current-tree suite with the server-side key/model loaded into the test
process: **129 passed, 1 skipped**. Both Task 20 live tests ran and passed.
The initial question did not supply `root_id`; its grounded claim and citation
used the pinned graph. The next question used committed focus and the previous
turn ID. Four further live questions covered data resource, message channel,
dependency and technology relations with evidence from the same snapshot.

This supersedes the Task 20 verification counts in
`TEST-RKG-GROUNDED-QA-001` without rewriting that historical record. HTTP
mapping and pilot-scale rubric remain assigned to T-021/T-022.
