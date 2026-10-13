---
key: TEST-RKG-FLASK-001-r2
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-047
captured_at: 2026-10-08
change_set: CHG-RKG-2026-001
captured_against:
  code_commit: 2d0af7204d89ea3944fbe507bc590744e45a5033
  artifacts:
  - { key: REG-ADAPTER-001, revision: 17 }
  - { key: CMP-RKG-ANALYZER, revision: 14 }
  - { key: STORY-RKG-025, revision: 1 }
  - { key: TASK-RKG-047, revision: 3 }
prior_evidence: TEST-RKG-FLASK-001
supersedes_clauses_in: TEST-RKG-FLASK-001
---

# TEST-RKG-FLASK-001-r2

Append-only wording correction. `TEST-RKG-FLASK-001` stays historical,
including its `captured_against` task revision 2. Pytest was not re-run; 3
passed stays the record in the original file.

## Corrected clause

AC-RKG-004: `routes_file.not_routed` and `service.idle` are absent from `handled_by`; only `routes_file.not_routed` remains a Callable (the suite also keeps `web.moving` as a Callable), and `service.idle` is asserted only as absent from `handled_by`.
