---
uid: null
key: TASK-RKG-012
type: task
group: normative
scope: lifecycle
system: SYS-RKG
story: STORY-RKG-006
status: done
review_record: REV-RKG-2026-004
review_record_note: REV-RKG-2026-004 lists this task in its documentation reconciliation. No REV-TASK file exists.
revision: 6
ownership:
  accountable_team: TEAM-RKG
  accountable_role: tech-lead
relations:
  part_of:
  - EPIC-002-TEAM-RKG
  depends_on:
  - TASK-RKG-006
  - TASK-RKG-007
  implements:
  - FR-RKG-002
classification: internal
ai_assisted: true
implementation_record:
  context: CTX-TASK-RKG-012.yaml
  plan: PLAN-TASK-RKG-012.md
  diary: DIARY-TASK-RKG-012.md
---
# TASK-RKG-012 — Configuration and HTTP dependency extraction

Extract environment/settings keys and requests/httpx literal origins without values,
credentials, query or payload. Verify AC-RKG-016/017/023.

## Result

`PythonLanguageAdapter` now records literal environment keys, explicit
`BaseSettings` fields, and deduplicated `http_service` origins. Reads become
`depends_on` edges from the callable or source unit that uses them. Values,
defaults, credentials, query strings, payloads and URL paths are not copied
into facts, diagnostics, the published graph or context. Dynamic keys and URLs
stay unresolved. Explicit class `inherits_from` / `implements` relations from
TASK-RKG-006 are unchanged. `REG-ADAPTER-001` revision 3 declares these
patterns on `rkg.python`; published capability names stay structure, imports,
calls, classes and metadata.

Verification: `TEST-RKG-CONFIG`, `TEST-RKG-HTTP-INVENTORY` and
`DIARY-TASK-RKG-012`, checked on working tree `d5bb973` plus the file hashes
in that diary.

## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-012.yaml) — commit, scope và hash đối chiếu.
- [Plan](../../evidence/plans/PLAN-TASK-RKG-012.md) — ngày theo Git, file và cách kiểm.
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-012.md) — kết quả, evidence và các correction.
