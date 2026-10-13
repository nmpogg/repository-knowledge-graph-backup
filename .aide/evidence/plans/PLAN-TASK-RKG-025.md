---
key: PLAN-TASK-RKG-025
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-025
revision: 3
plan_date: '2026-09-24'
date_basis:
  commit: 5a3f36f86a0eea37e6c490ba567bf58f75e71737
  field: author_at converted to Asia/Bangkok
provenance: git-derived implementation plan
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  context: CTX-TASK-RKG-025.yaml
verification_targets: []
frontend_test_paths:
- frontend/src/App.test.tsx
- frontend/src/client/mockClient.test.ts
revision_history:
- revision: 1
  metadata:
    key: PLAN-TASK-RKG-025
    type: implementation-plan
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-025
    captured_at: 2026-09-24
    captured_against:
      artifacts:
      - key: CTX-TASK-RKG-025
      - key: TASK-RKG-025
        revision: 1
  record: '# PLAN-TASK-RKG-025


    Màn quản lý repository và snapshot trên mock, gồm conflict và confirm.


    ## Thứ tự


    1. `repository screens` — list, create, edit, delete, empty/error. Kiểm: phần UI AC-RKG-066, AC-RKG-067,
    AC-RKG-071, AC-RKG-072.

    2. `snapshot screens` — activate, delete, blocked states. Kiểm: AC-RKG-069, AC-RKG-070.

    3. `handoff` — create tới index result tới activate tới Explorer. Kiểm: smoke trên mock.


    ## Không làm


    - Không persist thật.

    - Không bỏ guard của thao tác phá hủy.'
---

# PLAN-TASK-RKG-025

Màn quản lý repository và snapshot trên mock, gồm conflict và confirm.

## Thứ tự

1. `repository screens` — list, create, edit, delete, empty/error. Kiểm: phần UI AC-RKG-066, AC-RKG-067, AC-RKG-071, AC-RKG-072.
2. `snapshot screens` — activate, delete, blocked states. Kiểm: AC-RKG-069, AC-RKG-070.
3. `handoff` — create tới index result tới activate tới Explorer. Kiểm: smoke trên mock.

## Không làm

- Không persist thật.
- Không bỏ guard của thao tác phá hủy.

## Phạm vi code và kiểm chứng

- `frontend/src/App.test.tsx`
- `frontend/src/App.tsx`
- `frontend/src/client/mock/fixtures.ts`
- `frontend/src/client/mock/mockClient.ts`
- `frontend/src/client/mockClient.test.ts`
- `frontend/src/components/shell/AppShell.tsx`
- `frontend/src/components/ui/ConfirmDialog.tsx`
- `frontend/src/components/ui/ThemeToggle.tsx`
- `frontend/src/i18n/en.ts`
- `frontend/src/i18n/index.ts`
- `frontend/src/i18n/locale.tsx`
- `frontend/src/i18n/vi.ts`
- `frontend/src/index.css`
- `frontend/src/lib/format.ts`
- `frontend/src/lib/presets.ts`
- `frontend/src/lib/time.ts`
- `frontend/src/pages/conversations/ConversationsPlaceholderPage.tsx`
- `frontend/src/pages/explorer/ExplorerPage.tsx`
- `frontend/src/pages/jobs/JobMonitorPage.tsx`
- `frontend/src/pages/repositories/RepositoryCreatePage.tsx`
- `frontend/src/pages/repositories/RepositoryDetailPage.tsx`
- `frontend/src/pages/repositories/RepositoryEditPage.tsx`
- `frontend/src/pages/repositories/RepositoryListPage.tsx`
- `frontend/src/test/setup.ts`
- `frontend/src/types/api.ts`

- Trong `frontend/`: `npm test`, `npm run lint`, `npm run build`.

Các lệnh này mô tả cách kiểm, không khẳng định đã chạy trong lần bổ sung hồ sơ. Kết quả thực thi theo evidence đã ghi của task.

Context: [CTX-TASK-RKG-025](../context/CTX-TASK-RKG-025.yaml). Kết quả triển khai: [DIARY-TASK-RKG-025](../diaries/DIARY-TASK-RKG-025.md).
