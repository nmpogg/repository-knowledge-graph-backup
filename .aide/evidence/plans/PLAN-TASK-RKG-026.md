---
key: PLAN-TASK-RKG-026
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-026
revision: 3
plan_date: '2026-09-29'
date_basis:
  commit: d2148a52e04e5d79780c59afd4414ad065771bd7
  field: author_at converted to Asia/Bangkok
provenance: git-derived implementation plan
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  context: CTX-TASK-RKG-026.yaml
verification_targets: []
frontend_test_paths:
- frontend/src/pages/explorer/ExplorerPage.test.tsx
- frontend/src/pages/explorer/structureTree.test.ts
revision_history:
- revision: 1
  metadata:
    key: PLAN-TASK-RKG-026
    type: implementation-plan
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-026
    captured_at: 2026-09-29
    captured_against:
      artifacts:
      - key: CTX-TASK-RKG-026
      - key: TASK-RKG-026
        revision: 1
  record: '# PLAN-TASK-RKG-026


    Nút Structure trên thanh view, cây từ search của snapshot, chọn lá dùng drawer hiện có.


    ## Thứ tự


    1. `Explorer view switch` — Graph, List, Structure. Kiểm: AC-RKG-073 test UI.

    2. `tree` — group theo type rồi tách qualified name. Kiểm: lá mở đúng detail như List.


    ## Không làm


    - Không route mới.

    - Không dựng cây từ subgraph.

    - Không đổi identity entity trong lát cắt này.'
---

# PLAN-TASK-RKG-026

Nút Structure trên thanh view, cây từ search của snapshot, chọn lá dùng drawer hiện có.

## Thứ tự

1. `Explorer view switch` — Graph, List, Structure. Kiểm: AC-RKG-073 test UI.
2. `tree` — group theo type rồi tách qualified name. Kiểm: lá mở đúng detail như List.

## Không làm

- Không route mới.
- Không dựng cây từ subgraph.
- Không đổi identity entity trong lát cắt này.

## Phạm vi code và kiểm chứng

- `frontend/src/client/live/mapWire.ts`
- `frontend/src/i18n/en.ts`
- `frontend/src/i18n/vi.ts`
- `frontend/src/pages/explorer/ExplorerPage.test.tsx`
- `frontend/src/pages/explorer/ExplorerPage.tsx`
- `frontend/src/pages/explorer/SnapshotStructure.tsx`
- `frontend/src/pages/explorer/snapshotStructure.css`
- `frontend/src/pages/explorer/structureTree.test.ts`
- `frontend/src/pages/explorer/structureTree.ts`
- `frontend/src/pages/jobs/JobMonitorPage.tsx`
- `frontend/src/types/api.ts`

- Trong `frontend/`: `npm test`, `npm run lint`, `npm run build`.

Các lệnh này mô tả cách kiểm, không khẳng định đã chạy trong lần bổ sung hồ sơ. Kết quả thực thi theo evidence đã ghi của task.

Context: [CTX-TASK-RKG-026](../context/CTX-TASK-RKG-026.yaml). Kết quả triển khai: [DIARY-TASK-RKG-026](../diaries/DIARY-TASK-RKG-026.md).
