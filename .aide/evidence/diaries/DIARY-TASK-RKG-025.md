---
key: DIARY-TASK-RKG-025
type: implementation-diary
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-025
revision: 5
implementation_window:
  from: '2026-09-24'
  through: '2026-09-24'
provenance: reconstructed-from-committed-diff-and-prior-evidence
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  implementation_commits:
  - 5a3f36f86a0eea37e6c490ba567bf58f75e71737
prior_evidence:
- evidence/context/CTX-TASK-RKG-025.yaml
- evidence/diaries/DIARY-TASK-RKG-025.md
- evidence/plans/PLAN-TASK-RKG-025.md
- evidence/tests/TEST-RKG-UI-REPO-MGMT-MOCK-001.md
revision_history:
- revision: 2
  metadata:
    key: DIARY-TASK-RKG-025
    type: implementation-diary
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-025
    revision: 2
    captured_at: 2026-09-24
    captured_against:
      artifacts:
      - key: TASK-RKG-025
        revision: 7
      - key: UIS-RKG-001
        revision: 6
      - key: SCR-RKG-001
        revision: 7
      - key: UXF-RKG-003
        revision: 6
      - key: API-RKG-CORE-v1
        revision: 9
      - key: FR-RKG-001
        revision: 11
      code_tree: frontend-repo-mgmt-mock@acb4a7f+local-vi
    reference_machine:
      os: Windows 10.0.26200
      arch: x86_64
      node: 24.20.0
      npm: 11.19.0
  record: "# DIARY-TASK-RKG-025\n\n## Diễn giải\n\n- 2026-09-24 — Hoàn thiện UI quản lý repository/snapshot\
    \ trên mock:\n  list/create/edit/detail/delete, snapshot activate/delete, confirm + blocked\n  states,\
    \ optimistic `expected_revision` conflict trên edit, Explorer handoff\n  sau activate, danger zone\
    \ tách khỏi primary index action.\n- Mock client bổ sung `updateRepository` / `deleteRepository` /\
    \ `deleteSnapshot`\n  với mã lỗi contract: `repository_conflict`, `repository_busy`,\n  `repository_in_use`,\
    \ `snapshot_active`, `snapshot_in_use`, `generic_not_found`.\n- Fixture `seedConversationSnapshotRefs`\
    \ (snap-orders-000) để chứng minh\n  in-use guards mà không lộ absolute path.\n- Polish scoped `.repo-mgmt`\
    \ (toolbar/table/danger zone/dialog motion).\n- Cùng ngày: copy UI toàn frontend chuyển sang **tiếng\
    \ Việt** (presentation);\n  mã lỗi/enum contract giữ tiếng Anh. Không mở i18n song ngữ.\n\n## Đi chệch\n\
    \n- Snapshot “detail” dùng hàng lịch sử trên repository detail (không route riêng\n  `/snapshots/:id`);\
    \ đủ metadata + actions theo SCR/UIS.\n- Activate có confirm dialog (UXF copy) trước khi navigate\
    \ Explorer.\n- UI locale `vi` thay vì English presentation trong blueprint/mock gốc — không\n  đổi\
    \ semantics UIS/SCR.\n\n## Đánh đổi\n\n- Conversation refs chỉ là Set mock; live API thuộc TASK-RKG-024.\n\
    - Demo repo delete bị `repository_in_use` by design — smoke delete thành công\n  dùng repo tạo mới\
    \ không có pin.\n\n## Lệnh đã chạy và kết quả\n\n| Lệnh | Kết quả |\n| --- | --- |\n| `cd frontend\
    \ && npm test` | pass — 10 Vitest (App + mock lifecycle/guards) |\n| `cd frontend && npm run lint`\
    \ | pass — oxlint (warnings only) |\n| `cd frontend && npm run build` | pass — `tsc -b` + Vite production\
    \ build |\n\n## AC coverage (mock UI phần T-025)\n\n| AC | Evidence trên mock |\n| --- | --- |\n|\
    \ AC-RKG-066 | Create + list/detail paged; edit route; delete confirm/blocked UI |\n| AC-RKG-067 |\
    \ PATCH + `expected_revision`; stale → `409 repository_conflict` + keep draft |\n| AC-RKG-068 | Index\
    \ publish snapshot; job `repository_id`; list newest-first |\n| AC-RKG-069 | Activate inactive → active\
    \ pointer + navigate `/explorer?snapshot_id=` |\n| AC-RKG-070 | Active → `snapshot_active`; pinned\
    \ → `snapshot_in_use`; else delete OK |\n| AC-RKG-071 | Demo refs → `repository_in_use`; fresh repo\
    \ cascade delete OK |\n| AC-RKG-072 | Ownership mismatch → `404 generic_not_found`; loading/empty/error/confirm\
    \ |\n\n## DoD TASK-RKG-025\n\n- [x] Repository edit/delete + snapshot activate/delete trên mock\n\
    - [x] Conflict / confirm / blocked states\n- [x] Smoke create → index → activate → Explorer + destructive\
    \ guards (Vitest)\n- [x] Evidence diary + TEST-RKG-UI-REPO-MGMT-MOCK-001\n- [x] Task → `done`\n\n\
    ## Không làm / bàn giao tiếp\n\n- TASK-RKG-024: live API client.\n- TASK-RKG-021: Ask/conversation\
    \ UI (refs thật thay mock Set).\n---"
---

# DIARY-TASK-RKG-025

## Diễn giải

- 2026-09-24 — Hoàn thiện UI quản lý repository/snapshot trên mock:
  list/create/edit/detail/delete, snapshot activate/delete, confirm + blocked
  states, optimistic `expected_revision` conflict trên edit, Explorer handoff
  sau activate, danger zone tách khỏi primary index action.
- Mock client bổ sung `updateRepository` / `deleteRepository` / `deleteSnapshot`
  với mã lỗi contract: `repository_conflict`, `repository_busy`,
  `repository_in_use`, `snapshot_active`, `snapshot_in_use`, `generic_not_found`.
- Fixture `seedConversationSnapshotRefs` (snap-orders-000) để chứng minh
  in-use guards mà không lộ absolute path.
- Polish scoped `.repo-mgmt` (toolbar/table/danger zone/dialog motion).
- Cùng ngày: copy UI toàn frontend chuyển sang **tiếng Việt** (presentation);
  mã lỗi/enum contract giữ tiếng Anh. Không mở i18n song ngữ.

## Đi chệch

- Snapshot “detail” dùng hàng lịch sử trên repository detail (không route riêng
  `/snapshots/:id`); đủ metadata + actions theo SCR/UIS.
- Activate có confirm dialog (UXF copy) trước khi navigate Explorer.
- UI locale `vi` thay vì English presentation trong blueprint/mock gốc — không
  đổi semantics UIS/SCR.

## Đánh đổi

- Conversation refs chỉ là Set mock; live API thuộc TASK-RKG-024.
- Demo repo delete bị `repository_in_use` by design — smoke delete thành công
  dùng repo tạo mới không có pin.

## Lệnh đã chạy và kết quả

| Lệnh | Kết quả |
| --- | --- |
| `cd frontend && npm test` | pass — 10 Vitest (App + mock lifecycle/guards) |
| `cd frontend && npm run lint` | pass — oxlint (warnings only) |
| `cd frontend && npm run build` | pass — `tsc -b` + Vite production build |

## AC coverage (mock UI phần T-025)

| AC | Evidence trên mock |
| --- | --- |
| AC-RKG-066 | Create + list/detail paged; edit route; delete confirm/blocked UI |
| AC-RKG-067 | PATCH + `expected_revision`; stale → `409 repository_conflict` + keep draft |
| AC-RKG-068 | Index publish snapshot; job `repository_id`; list newest-first |
| AC-RKG-069 | Activate inactive → active pointer + navigate `/explorer?snapshot_id=` |
| AC-RKG-070 | Active → `snapshot_active`; pinned → `snapshot_in_use`; else delete OK |
| AC-RKG-071 | Demo refs → `repository_in_use`; fresh repo cascade delete OK |
| AC-RKG-072 | Ownership mismatch → `404 generic_not_found`; loading/empty/error/confirm |

## DoD TASK-RKG-025

- [x] Repository edit/delete + snapshot activate/delete trên mock
- [x] Conflict / confirm / blocked states
- [x] Smoke create → index → activate → Explorer + destructive guards (Vitest)
- [x] Evidence diary + TEST-RKG-UI-REPO-MGMT-MOCK-001
- [x] Task → `done`

## Không làm / bàn giao tiếp

- TASK-RKG-024: live API client.
- TASK-RKG-021: Ask/conversation UI (refs thật thay mock Set).
---

## Đối chiếu commit và phạm vi hiện hành

## Kết quả đối chiếu triển khai

Dựng create/update/list/detail/activate/delete UI và guard trên mock contract-shaped fixtures; live integration thuộc task 024.

Các file thay đổi được xác định bằng Git diff của các commit được pin trong frontmatter. Current-tree hash nằm trong context revision 3; khác hash lịch sử là revision về sau, không phải cùng lần chạy.

## Diễn giải và correction

Hành vi và các lần kiểm đã ghi trong prior evidence giữ nguyên; bản này bổ sung liên kết và nguồn commit, không thay kết quả cũ.

## Kết quả lần bổ sung hồ sơ

Đã đọc commit/file, parse test declarations và liên kết evidence; không chạy lại runtime test hoặc đo KPI. Không nhận đây là review code độc lập hay approval.
