---
key: PLAN-TASK-RKG-002
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-002
revision: 3
plan_date: '2026-09-24'
date_basis:
  commit: 968a9f62775d4f26d23fb713fb14128fce5b97c1
  field: author_at converted to Asia/Bangkok
provenance: git-derived implementation plan
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  context: CTX-TASK-RKG-002.yaml
verification_targets:
- path: tests/unit/test_domain_schema.py
  tests:
  - test_ac_002_golden_source_structure_and_lexical_parent
  - test_ac_007_rejects_missing_cross_snapshot_and_invalid_evidence
  - test_endpoint_identity_keeps_registration_chains_distinct
  - test_endpoint_chain_metadata_can_be_serialized_without_merging_identity
  - test_configuration_value_is_not_a_graph_fact
  - test_ac_010_context_schema_order_and_budget_dto
  - test_source_scan_config_limits
frontend_test_paths: []
revision_history:
- revision: 1
  metadata:
    key: PLAN-TASK-RKG-002
    type: implementation-plan
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-002
    captured_at: 2026-09-24
    captured_against:
      artifacts:
      - key: CTX-TASK-RKG-002
      - key: TASK-RKG-002
        revision: 1
  record: '# PLAN-TASK-RKG-002


    Chốt DTO, ID, validator và golden JSON để các lát cắt extract và context sau dùng chung, trước khi
    có ingestion hay storage.


    ## Thứ tự


    1. `src/rkg/domain/models.py` — DTO entity, edge, evidence, diagnostic, FactBatch, context budget.
    Kiểm: unit test schema-level cho hình golden.

    2. `src/rkg/domain/ids.py` — ID ổn định theo field identity đã khóa trong TBL. Kiểm: cùng input ra
    cùng ID; edge nhiều evidence không đổi identity.

    3. `src/rkg/domain/validation.py` — từ chối edge lệch snapshot, thiếu evidence, hoặc attribute dạng
    secret/raw source. Kiểm: test âm AC-RKG-007.

    4. `tests fixtures golden JSON` — SourceUnit, scope, type, callable theo AC-RKG-002 lúc này. Kiểm:
    test shape deterministic, chưa cần Kùzu.


    ## Không làm


    - Không viết loader, adapter, Kùzu hay API.

    - Không đổi AC để khớp một fixture tiện tay.'
---

# PLAN-TASK-RKG-002

Chốt DTO, ID, validator và golden JSON để các lát cắt extract và context sau dùng chung, trước khi có ingestion hay storage.

## Thứ tự

1. `src/rkg/domain/models.py` — DTO entity, edge, evidence, diagnostic, FactBatch, context budget. Kiểm: unit test schema-level cho hình golden.
2. `src/rkg/domain/ids.py` — ID ổn định theo field identity đã khóa trong TBL. Kiểm: cùng input ra cùng ID; edge nhiều evidence không đổi identity.
3. `src/rkg/domain/validation.py` — từ chối edge lệch snapshot, thiếu evidence, hoặc attribute dạng secret/raw source. Kiểm: test âm AC-RKG-007.
4. `tests fixtures golden JSON` — SourceUnit, scope, type, callable theo AC-RKG-002 lúc này. Kiểm: test shape deterministic, chưa cần Kùzu.

## Không làm

- Không viết loader, adapter, Kùzu hay API.
- Không đổi AC để khớp một fixture tiện tay.

## Phạm vi code và kiểm chứng

- `src/rkg/domain/README.md`
- `src/rkg/domain/__init__.py`
- `src/rkg/domain/context.py`
- `src/rkg/domain/ids.py`
- `src/rkg/domain/models.py`
- `src/rkg/domain/validation.py`
- `tests/fixtures/domain/source_structure.json`
- `tests/unit/test_domain_schema.py`

- `python -m pytest tests/unit/test_domain_schema.py -q`

Các lệnh này mô tả cách kiểm, không khẳng định đã chạy trong lần bổ sung hồ sơ. Kết quả thực thi theo evidence đã ghi của task.

Context: [CTX-TASK-RKG-002](../context/CTX-TASK-RKG-002.yaml). Kết quả triển khai: [DIARY-TASK-RKG-002](../diaries/DIARY-TASK-RKG-002.md).
