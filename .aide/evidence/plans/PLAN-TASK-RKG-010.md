---
key: PLAN-TASK-RKG-010
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-010
revision: 3
plan_date: '2026-09-25'
date_basis:
  commit: 66680533506fa6b3ab4812ac1ed4a59c8f89a44a
  field: author_at converted to Asia/Bangkok
provenance: git-derived implementation plan
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  context: CTX-TASK-RKG-010.yaml
verification_targets:
- path: tests/conformance/test_sqlalchemy_data.py
  tests:
  - test_declarative_identity_does_not_merge_names_or_guess
  - test_reads_and_writes_follow_executed_patterns
  - test_local_sqlalchemy_module_is_not_analyzed
  - test_lock_selects_adapter_without_entrypoint
frontend_test_paths: []
revision_history:
- revision: 1
  metadata:
    key: PLAN-TASK-RKG-010
    type: implementation-plan
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-010
    captured_at: 2026-09-25
    captured_against:
      artifacts:
      - key: CTX-TASK-RKG-010
      - key: TASK-RKG-010
        revision: 1
  record: '# PLAN-TASK-RKG-010


    DataResource và reads/writes cho profile SQLAlchemy 2.x đã công bố.


    ## Thứ tự


    1. `sqlalchemy adapter` — maps_to và operation metadata. Kiểm: AC-RKG-013, AC-RKG-014, gồm case âm
    tính.


    ## Không làm


    - Không reflection lúc chạy.

    - Không gộp table theo tên.'
---

# PLAN-TASK-RKG-010

DataResource và reads/writes cho profile SQLAlchemy 2.x đã công bố.

## Thứ tự

1. `sqlalchemy adapter` — maps_to và operation metadata. Kiểm: AC-RKG-013, AC-RKG-014, gồm case âm tính.

## Không làm

- Không reflection lúc chạy.
- Không gộp table theo tên.

## Phạm vi code và kiểm chứng

- `pyproject.toml`
- `src/rkg/adapters/__init__.py`
- `src/rkg/adapters/sqlalchemy_data.py`
- `src/rkg/detection/README.md`
- `tests/conformance/test_sqlalchemy_data.py`

- `python -m pytest tests/conformance/test_sqlalchemy_data.py -q`

Các lệnh này mô tả cách kiểm, không khẳng định đã chạy trong lần bổ sung hồ sơ. Kết quả thực thi theo evidence đã ghi của task.

Context: [CTX-TASK-RKG-010](../context/CTX-TASK-RKG-010.yaml). Kết quả triển khai: [DIARY-TASK-RKG-010](../diaries/DIARY-TASK-RKG-010.md).
