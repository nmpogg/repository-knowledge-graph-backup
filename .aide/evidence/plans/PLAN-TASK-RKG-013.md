---
key: PLAN-TASK-RKG-013
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-013
revision: 3
plan_date: '2026-09-24'
date_basis:
  commit: 348ee6154975b4971d61c4c698e37cfd9c36ff29
  field: author_at converted to Asia/Bangkok
provenance: git-derived implementation plan
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  context: CTX-TASK-RKG-013.yaml
verification_targets:
- path: tests/integration/test_schema_migrate.py
  tests:
  - test_fresh_storage_bootstraps_schema_meta
  - test_migrate_previous_schema_retains_depends_on_edges
- path: tests/integration/test_storage_lifecycle.py
  tests:
  - test_ac066_repository_crud_and_list_order
  - test_ac067_optimistic_revision_and_source_immutable
  - test_ac007_008_068_publish_reindex_and_failed_keeps_active
  - test_ac069_activate_switches_pointer_only
  - test_ac070_snapshot_delete_guards
  - test_ac071_repository_delete_guards
  - test_ownership_mismatch_is_not_found
  - test_duplicate_source_identity_conflicts
frontend_test_paths: []
revision_history:
- revision: 1
  metadata:
    key: PLAN-TASK-RKG-013
    type: implementation-plan
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-013
    captured_at: 2026-09-24
    captured_against:
      artifacts:
      - key: CTX-TASK-RKG-013
      - key: TASK-RKG-013
        revision: 1
  record: '# PLAN-TASK-RKG-013


    Publication và active pointer nguyên tử theo repository. Rollback khi lỗi. Không giữ transaction trong
    lúc parse.


    ## Thứ tự


    1. `src/rkg/storage/snapshots.py` — publish, retain, fail không đổi active. Kiểm: AC-RKG-008 re-index
    thành công và re-index lỗi.

    2. `src/rkg/storage/connection.py` — một writer owner. Kiểm: test không mở connection ghi song song.

    3. `DDL đã pin` — bootstrap schema từ TBL. Kiểm: DDL chạy được trên Kùzu đã pin ở TASK-RKG-001.


    ## Không làm


    - Không thêm writer process thứ hai.

    - Không search trong lát cắt này.'
---

# PLAN-TASK-RKG-013

Publication và active pointer nguyên tử theo repository. Rollback khi lỗi. Không giữ transaction trong lúc parse.

## Thứ tự

1. `src/rkg/storage/snapshots.py` — publish, retain, fail không đổi active. Kiểm: AC-RKG-008 re-index thành công và re-index lỗi.
2. `src/rkg/storage/connection.py` — một writer owner. Kiểm: test không mở connection ghi song song.
3. `DDL đã pin` — bootstrap schema từ TBL. Kiểm: DDL chạy được trên Kùzu đã pin ở TASK-RKG-001.

## Không làm

- Không thêm writer process thứ hai.
- Không search trong lát cắt này.

## Phạm vi code và kiểm chứng

- `pyproject.toml`
- `src/rkg/domain/README.md`
- `src/rkg/graph/README.md`
- `src/rkg/graph/__init__.py`
- `src/rkg/graph/ids.py`
- `src/rkg/graph/publish.py`
- `src/rkg/storage/README.md`
- `src/rkg/storage/__init__.py`
- `src/rkg/storage/_util.py`
- `src/rkg/storage/connection.py`
- `src/rkg/storage/conversations.py`
- `src/rkg/storage/errors.py`
- `src/rkg/storage/fixtures/ddl_v0.cypher`
- `src/rkg/storage/jobs.py`
- `src/rkg/storage/migrate.py`
- `src/rkg/storage/readers.py`
- `src/rkg/storage/records.py`
- `src/rkg/storage/repositories.py`
- `src/rkg/storage/snapshots.py`
- `tests/__init__.py`
- `tests/integration/__init__.py`
- `tests/integration/storage_helpers.py`
- `tests/integration/test_schema_migrate.py`
- `tests/integration/test_storage_lifecycle.py`

- `python -m pytest tests/integration/test_schema_migrate.py tests/integration/test_storage_lifecycle.py -q`

Các lệnh này mô tả cách kiểm, không khẳng định đã chạy trong lần bổ sung hồ sơ. Kết quả thực thi theo evidence đã ghi của task.

Context: [CTX-TASK-RKG-013](../context/CTX-TASK-RKG-013.yaml). Kết quả triển khai: [DIARY-TASK-RKG-013](../diaries/DIARY-TASK-RKG-013.md).
