---
key: PLAN-TASK-RKG-004
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-004
revision: 3
plan_date: '2026-09-24'
date_basis:
  commit: b10116e027f792991f03f7959a114834a33cf72d
  field: author_at converted to Asia/Bangkok
provenance: git-derived implementation plan
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  context: CTX-TASK-RKG-004.yaml
verification_targets:
- path: tests/conformance/test_adapter_conformance.py
  tests:
  - test_fixture_adapter_contract_and_registry
  - test_core_has_no_fixture_specific_dispatch
- path: tests/unit/test_adapter_registry.py
  tests:
  - test_descriptor_rejects_incomplete_and_invalid_contract_fields
  - test_registry_rejects_incompatible_duplicate_and_missing_interface
  - test_registry_selection_uses_evidence_and_stable_order
  - test_deep_adapter_requires_language_technology_and_matching_version
  - test_conformance_pass_rate_is_machine_readable
frontend_test_paths: []
revision_history:
- revision: 1
  metadata:
    key: PLAN-TASK-RKG-004
    type: implementation-plan
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-004
    captured_at: 2026-09-24
    captured_against:
      artifacts:
      - key: CTX-TASK-RKG-004
      - key: TASK-RKG-004
        revision: 1
  record: '# PLAN-TASK-RKG-004


    Khóa contract LanguageAdapter và FrameworkAdapter version hóa, cộng conformance suite, để core không
    branch theo adapter ID.


    ## Thứ tự


    1. `src/rkg/adapters/contracts.py` — descriptor và FactBatch boundary. Kiểm: registry từ chối registration
    lệch version.

    2. `src/rkg/adapters/conformance.py` — suite dùng chung. Kiểm: fixture adapter chỉ sống trong test,
    so với allowlist.

    3. `tests` — NFR-RKG-EXT-001. Kiểm: TEST-RKG-ADAPTER-CONFORMANCE.


    ## Không làm


    - Không sửa coordinator, schema graph hay API.

    - Không thêm adapter sản phẩm trong lát cắt conformance.'
---

# PLAN-TASK-RKG-004

Khóa contract LanguageAdapter và FrameworkAdapter version hóa, cộng conformance suite, để core không branch theo adapter ID.

## Thứ tự

1. `src/rkg/adapters/contracts.py` — descriptor và FactBatch boundary. Kiểm: registry từ chối registration lệch version.
2. `src/rkg/adapters/conformance.py` — suite dùng chung. Kiểm: fixture adapter chỉ sống trong test, so với allowlist.
3. `tests` — NFR-RKG-EXT-001. Kiểm: TEST-RKG-ADAPTER-CONFORMANCE.

## Không làm

- Không sửa coordinator, schema graph hay API.
- Không thêm adapter sản phẩm trong lát cắt conformance.

## Phạm vi code và kiểm chứng

- `src/rkg/adapters/__init__.py`
- `src/rkg/adapters/conformance.py`
- `src/rkg/adapters/contracts.py`
- `src/rkg/adapters/registry.py`
- `tests/unit/test_adapter_registry.py`
- `tests/conformance/fixture_adapter.py`
- `tests/conformance/test_adapter_conformance.py`
- `tests/fixtures/adapter/sample.synthetic`

- `python -m pytest tests/conformance/test_adapter_conformance.py tests/unit/test_adapter_registry.py -q`

Các lệnh này mô tả cách kiểm, không khẳng định đã chạy trong lần bổ sung hồ sơ. Kết quả thực thi theo evidence đã ghi của task.

Context: [CTX-TASK-RKG-004](../context/CTX-TASK-RKG-004.yaml). Kết quả triển khai: [DIARY-TASK-RKG-004](../diaries/DIARY-TASK-RKG-004.md).
