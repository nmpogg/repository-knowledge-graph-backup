---
uid: null
key: TASK-RKG-024
type: task
group: normative
scope: lifecycle
system: SYS-RKG
story: STORY-RKG-011
status: done
review_record: REV-RKG-2026-004
review_record_note: REV-RKG-2026-004 lists this task in its documentation reconciliation. No REV-TASK file exists.
revision: 10
ownership:
  accountable_team: TEAM-RKG
  accountable_role: design-owner
relations:
  part_of:
  - EPIC-003-TEAM-RKG
  depends_on:
  - TASK-RKG-016
  - TASK-RKG-017
  - TASK-RKG-025
  implements:
  - FR-RKG-003
  - FR-RKG-002
  - FR-RKG-001
classification: internal
ai_assisted: true
implementation_record:
  context: CTX-TASK-RKG-024.yaml
  plan: PLAN-TASK-RKG-024.md
  diary: DIARY-TASK-RKG-024.md
---
# TASK-RKG-024 — Integrate UI with live API

Replace mock access with live `API-RKG-CORE-v1`, reconcile contract differences and
regress repository/snapshot/onboarding/job/explorer/evidence/dependency flows. Verify
AC-RKG-011/018/027/043/054/056/057/061/066…072 against real backend while
preserving UI structure from M0.

## Kết quả

- `frontend/src/client/live/`: client `API-RKG-CORE-v1` khi `VITE_RKG_CLIENT=live`.
  Mock vẫn là chế độ mặc định.
- Mapper giữ nguyên màn hình M0: trang `{items,total,offset,limit}` thành
  `page`, enum domain (`Endpoint`, `Callable`, …) thành nhãn UI, cạnh
  `source_id`/`target_id`, stage `scanning|parsing|extracting|publishing` thành
  stepper, và `failed` + `app_selection_required` thành stage `detecting`.
- Session là `VITE_RKG_SESSION`, cùng giá trị với `RKG_SESSION_TOKEN`. Dev server
  proxy `/api` tới loopback. API chỉ phản chiếu CORS cho origin loopback.
- AC đã chạy với backend thật: 011, 027, 043, 054, 061, 066, 067, 068, 070, 071, 072.
  AC-018 giữ preset M0 và kiểu cạnh đã map. AC-056 không chạy lại checklist viewport.
  AC-057 map provenance; fixture live không có đủ bốn support state. AC-069 chưa
  activate một snapshot không phải active vì snapshot vừa publish đã là active.
- Evidence: `DIARY-TASK-RKG-024`, `TEST-RKG-UI-LIVE-API-001`.


## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-024.yaml) — commit, scope và hash đối chiếu.
- [Plan](../../evidence/plans/PLAN-TASK-RKG-024.md) — ngày theo Git, file và cách kiểm.
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-024.md) — kết quả, evidence và các correction.
