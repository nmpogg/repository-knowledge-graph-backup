---
uid: null
key: TASK-RKG-023
type: task
group: normative
scope: lifecycle
system: SYS-RKG
epic: EPIC-005-TEAM-RKG
status: done
review_record: REV-RKG-2026-004
review_record_note: REV-RKG-2026-004 lists this task in its documentation reconciliation. No REV-TASK file exists.
revision: 8
ownership:
  accountable_team: TEAM-RKG
  accountable_role: tech-lead
relations:
  part_of:
  - EPIC-005-TEAM-RKG
  depends_on:
  - TASK-RKG-022
  implements:
  - PRD-RKG
classification: internal
ai_assisted: true
implementation_record:
  context: CTX-TASK-RKG-023.yaml
  plan: PLAN-TASK-RKG-023.md
  diary: DIARY-TASK-RKG-023.md
---
# TASK-RKG-023 — Final runbook and handoff

Complete setup/local-path/index/serve/LLM/history/retention/troubleshooting docs,
run final regression and report scope, evidence, limitations and remaining risks.

The operator runbook is `README.md`. The index note is `.aide/README.md`.
Closure records are `DIARY-TASK-RKG-023` and `TEST-RKG-FINAL-REGRESSION-001`.

Task execution is closed against code commit `404f057` after current-tree
verification of the existing suite. This `done` status records the runbook
and the regression report. KPI-RKG-001 is recorded in
`TEST-RKG-FIXTURE-CENSUS-SUMMARY-001`; that census has no oracle review
receipt. KPI-RKG-002 adjudication and the numeric NFR-RKG-PERF-001 re-run are recorded
in `TEST-RKG-PILOT-REVIEW-SUMMARY-002` and `TEST-RKG-PERF-SUMMARY-002`;
full-size performance acceptance remains open. This task does not approve
`EPIC-005-TEAM-RKG`.

On this host the sibling pilot repository was unavailable, so
`tests/integration/test_pilot_corpus.py` skipped. Pilot digest evidence
remains the published Task 22 reports. Symlink creation is not permitted
here, so one local-source test also skipped. Live OpenRouter checks skipped
because no credential was present.


## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-023.yaml) — commit, scope và hash đối chiếu.
- [Plan](../../evidence/plans/PLAN-TASK-RKG-023.md) — ngày theo Git, file và cách kiểm.
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-023.md) — kết quả, evidence và các correction.
