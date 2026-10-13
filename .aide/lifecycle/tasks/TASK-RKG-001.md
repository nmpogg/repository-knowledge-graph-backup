---
uid: null
key: TASK-RKG-001
type: task
group: normative
scope: lifecycle
system: SYS-RKG
epic: EPIC-001-TEAM-RKG
status: done
review_record: REV-RKG-2026-004
review_record_note: REV-RKG-2026-004 lists this task in its documentation reconciliation. No REV-TASK file exists.
revision: 8
ownership:
  accountable_team: TEAM-RKG
  accountable_role: tech-lead
relations:
  part_of:
  - EPIC-001-TEAM-RKG
  depends_on: []
classification: internal
ai_assisted: true
implementation_record:
  context: CTX-TASK-RKG-001.yaml
  plan: PLAN-TASK-RKG-001.md
  diary: DIARY-TASK-RKG-001.md
---
# TASK-RKG-001 — Project skeleton and toolchain

Khởi tạo package/src/tests và frontend React/Vite; chốt CPython 3.12 patch, Node,
package manager, dependency locks và các lệnh dev/build/test/lint. Xong khi clean
environment chạy được checks tối thiểu, `DDL-RKG-GRAPH.cypher` execute được trên
Kùzu version đã pin và README ghi đúng lệnh thực tế.

## Kết quả

- Frontend base: React + Vite + TypeScript, `.nvmrc` = 22, `package-lock.json`,
  Vitest smoke, lint/build — evidence `DIARY-TASK-RKG-001-r2`.
- Python: CPython **3.12.14**, `pyproject.toml` + `uv.lock`, `src/rkg` placeholder
  layout (gồm `adapters/`), pytest/ruff; Kùzu **0.11.3**; DDL smoke —
  evidence `DIARY-TASK-RKG-001-r3`.
- Close-out hygiene (docs product retire → README/AGENTS/`.aide/README`,
  `REG-REPO-001`, handoff 017/025) — evidence `DIARY-TASK-RKG-001-r4`.
- UI nghiệp vụ thuộc TASK-RKG-017/025, không nằm trong task này.
  `uv.lock` + evidence r3/r4 cần được stage/commit khi đóng MR.

## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-001.yaml) — commit, scope và hash đối chiếu.
- [Plan](../../evidence/plans/PLAN-TASK-RKG-001.md) — ngày theo Git, file và cách kiểm.
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-001.md) — kết quả, evidence và các correction.
