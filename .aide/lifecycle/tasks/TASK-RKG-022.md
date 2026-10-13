---
uid: null
key: TASK-RKG-022
type: task
group: normative
scope: lifecycle
system: SYS-RKG
story: STORY-RKG-015
status: done
review_record: REV-RKG-2026-004
review_record_note: REV-RKG-2026-004 lists this task in its documentation reconciliation. No REV-TASK file exists.
revision: 18
ownership:
  accountable_team: TEAM-RKG
  accountable_role: tech-lead
relations:
  part_of:
  - EPIC-005-TEAM-RKG
  depends_on:
  - TASK-RKG-015
  - TASK-RKG-024
  - TASK-RKG-021
  implements:
  - FR-RKG-001
  - FR-RKG-003
  - FR-RKG-004
  verifies:
  - AC-RKG-037
  - AC-RKG-039
  - AC-RKG-062
classification: internal
ai_assisted: true
implementation_record:
  context: CTX-TASK-RKG-022.yaml
  plan: PLAN-TASK-RKG-022.md
  diary: DIARY-TASK-RKG-022.md
---
# TASK-RKG-022 — Pilot, eval and benchmark

Run supported/negative extraction fixtures; selected pilot with at least 30 reviewed
import/call/DI samples and 10 samples per DB/event/config/implements group when present;
30-question Q&A set, 10 multi-turn conversations and performance
benchmark; publish samples, methods, versions, unresolved, omissions and findings
rather than a bare pass result.
Run and publish `TEST-RKG-ADAPTER-CONFORMANCE`, including its diff allowlist and
static-check result, to verify `NFR-RKG-EXT-001` before MVP acceptance.
`verifies` lists the three benchmark ACs this story satisfies. Published
evidence may record a miss; `verifies` here means the AC was measured, not that
every NFR threshold passed.

The selected corpus is the sibling `../pilot_fastapi/` (OQ-RKG-002 resolved;
inventory and relocation evidence in `TEST-RKG-PILOT-CORPUS-001/002`).
The pinned-corpus reports are published under `.aide/evidence/tests/`:
`TEST-RKG-PILOT-REVIEW-SUMMARY-001` (historical) and
`TEST-RKG-PILOT-REVIEW-SUMMARY-002` (current pilot precision), Q&A summaries
`TEST-RKG-QA-EVAL-SUMMARY-001` (historical) plus keyed
`TEST-RKG-QA-EVAL-SUMMARY-001-r2` / `-r3` / `-r4` (current live = `-r4`),
`TEST-RKG-PERF-SUMMARY-001` (historical) and `TEST-RKG-PERF-SUMMARY-002`
(current numeric benchmark), `TEST-RKG-FIXTURE-CENSUS-SUMMARY-001` (current KPI-RKG-001 census),
`TEST-RKG-EXTRACTION-FIXTURES-001` (historical) and
`TEST-RKG-ADAPTER-CONFORMANCE-r3`. Implementation and closure records are
`DIARY-TASK-RKG-022` and `DIARY-TASK-RKG-022-r2`.
Eval path authority: see `.aide/README.md` § Eval / evidence authority.

Task execution and reporting are closed at code commit `7eec602` after
current-tree verification. This `done` status records completion of the
pilot/eval/benchmark work and publication of its findings; it does not
assert that every MVP acceptance target passes.

Open acceptance findings after the 2026-10-08 measurement: KPI-RKG-001 is
recorded in `TEST-RKG-FIXTURE-CENSUS-SUMMARY-001` at coverage 1.00 and
precision 1.00 on six fixtures; that report does not include an oracle
review receipt. KPI-RKG-002 owner review of the
current pilot is recorded in `TEST-RKG-PILOT-REVIEW-SUMMARY-002` at precision
1.00 per group. `TEST-RKG-PERF-SUMMARY-002` records two runs on an eligible
host; every numeric NFR-RKG-PERF-001 threshold passed, and the pilot remains
under the 500-file / 50,000-SLOC ceiling, so that run is not a full-size
acceptance. The latest live Q&A run met answerable, safety and conversation
targets after increasing per-call output budget within NFR-RKG-REL-001;
earlier runs remain historical evidence. No KPI-RKG-001/002 or
NFR-RKG-PERF-001 waiver is recorded here, and this revision does not close
`EPIC-005-TEAM-RKG` or a gate.

## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-022.yaml) — commit, scope và hash đối chiếu.
- [Plan](../../evidence/plans/PLAN-TASK-RKG-022.md) — ngày theo Git, file và cách kiểm.
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-022.md) — kết quả, evidence và các correction.
