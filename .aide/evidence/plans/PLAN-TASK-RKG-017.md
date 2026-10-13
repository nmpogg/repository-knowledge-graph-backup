---
key: PLAN-TASK-RKG-017
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-017
revision: 3
plan_date: '2026-09-24'
date_basis:
  commit: acb4a7fbc062f0ed3fcf05e5a52b5cf82c21ec5b
  field: author_at converted to Asia/Bangkok
provenance: git-derived implementation plan
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  context: CTX-TASK-RKG-017.yaml
verification_targets: []
frontend_test_paths: []
revision_history:
- revision: 1
  metadata:
    key: PLAN-TASK-RKG-017
    type: implementation-plan
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-017
    captured_at: 2026-09-24
    captured_against:
      artifacts:
      - key: CTX-TASK-RKG-017
      - key: TASK-RKG-017
        revision: 1
  record: '# PLAN-TASK-RKG-017


    Dựng luồng onboarding, job và Explorer trên mock client đúng contract, dùng token đã có.


    ## Thứ tự


    1. `frontend mock client` — response cùng schema API v1. Kiểm: fixture onboarding tới export context.

    2. `Explorer` — search, preset, evidence, keyboard. Kiểm: AC-RKG-011, AC-RKG-018.

    3. `a11y` — contrast, reduced motion, viewport. Kiểm: AC-RKG-056.


    ## Không làm


    - Không gọi API thật.

    - Không làm màn quản lý repository đầy đủ (TASK-RKG-025).

    - Không hard-code màu ngoài token.'
---

# PLAN-TASK-RKG-017

Dựng luồng onboarding, job và Explorer trên mock client đúng contract, dùng token đã có.

## Thứ tự

1. `frontend mock client` — response cùng schema API v1. Kiểm: fixture onboarding tới export context.
2. `Explorer` — search, preset, evidence, keyboard. Kiểm: AC-RKG-011, AC-RKG-018.
3. `a11y` — contrast, reduced motion, viewport. Kiểm: AC-RKG-056.

## Không làm

- Không gọi API thật.
- Không làm màn quản lý repository đầy đủ (TASK-RKG-025).
- Không hard-code màu ngoài token.

## Phạm vi code và kiểm chứng



- Đối chiếu schema/reference, artifact hash, runbook và evidence được pin.

Các lệnh này mô tả cách kiểm, không khẳng định đã chạy trong lần bổ sung hồ sơ. Kết quả thực thi theo evidence đã ghi của task.

Context: [CTX-TASK-RKG-017](../context/CTX-TASK-RKG-017.yaml). Kết quả triển khai: [DIARY-TASK-RKG-017](../diaries/DIARY-TASK-RKG-017.md).
