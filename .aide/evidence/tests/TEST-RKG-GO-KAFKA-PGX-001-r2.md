---
key: TEST-RKG-GO-KAFKA-PGX-001-r2
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-046
captured_at: 2026-10-08
change_set: CHG-RKG-2026-001
captured_against:
  code_commit: 2d0af7204d89ea3944fbe507bc590744e45a5033
  artifacts:
  - { key: REG-ADAPTER-001, revision: 16 }
  - { key: CMP-RKG-ANALYZER, revision: 14 }
  - { key: STORY-RKG-024, revision: 1 }
  - { key: TASK-RKG-046, revision: 4 }
  prior_evidence: TEST-RKG-GO-KAFKA-PGX-001
supersedes_clauses_in: TEST-RKG-GO-KAFKA-PGX-001
---

# TEST-RKG-GO-KAFKA-PGX-001-r2

Append-only wording correction. `TEST-RKG-GO-KAFKA-PGX-001` stays historical,
including its `captured_against` task revision 3. Pytest counts are not
re-run. The original file remains the record: 3 passed and 2 passed.

## Current contract (TASK-RKG-046 revision 4)

AC-RKG-007: oracle rows carry a relative `file_path` with null `rule_id` and
`start_line`. Census compare matches type, qualified name, required
attributes, and edge endpoints only. A null oracle `rule_id` is not checked.
`validate_fact_batch` only rejects a non-relative entity path.

## Corrected clauses

The suites agree with the task under-test list. AC-RKG-007 is the revision-4
contract above, not a path-equality exception.

The AC-RKG-007 row does not claim the task treats AC-RKG-007 as verified
corpus-level evidence paths.
