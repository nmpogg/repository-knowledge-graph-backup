---
key: PLAN-TASK-RKG-027
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-027
revision: 3
plan_date: '2026-10-01'
date_basis:
  commit: 64739d4e674050f4944baf4aaa609cbcc86acf3b
  field: author_at converted to Asia/Bangkok
provenance: git-derived implementation plan
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  context: CTX-TASK-RKG-027.yaml
verification_targets:
- path: tests/integration/test_directory_entities.py
  tests:
  - test_v1_migration_retains_namespace_snapshot_and_new_api_directory
  - test_v1_migration_failure_rolls_back_table_and_metadata
- path: tests/integration/test_index_coordinator.py
  tests:
  - test_reindex_failure_and_recovery
  - test_warnings_and_global_busy
  - test_cli_repository_and_index
  - test_fastapi_selection_and_binding
  - test_unknown_version_factory_publishes_routes_and_warning
- path: tests/integration/test_index_language_partition.py
  tests:
  - test_python_only_repository_still_builds_the_same_graph
  - test_other_language_runs_and_python_does_not_parse
  - test_two_languages_merge_into_one_snapshot
  - test_companion_uses_only_the_parent_language_portion
  - test_unregistered_extension_succeeds_without_language_nodes
  - test_duplicate_language_extension_fails_the_job
  - test_shared_directory_is_built_once_for_two_languages
- path: tests/unit/test_adapter_registry.py
  tests:
  - test_descriptor_rejects_incomplete_and_invalid_contract_fields
  - test_registry_rejects_incompatible_duplicate_and_missing_interface
  - test_registry_selection_uses_evidence_and_stable_order
  - test_deep_adapter_requires_language_technology_and_matching_version
  - test_conformance_pass_rate_is_machine_readable
- path: tests/unit/test_directory_structure.py
  tests:
  - test_unique_ancestors_empty_files_and_root_files
  - test_source_root_ancestors_and_syntax_error_do_not_trigger_another_walk
  - test_structure_rejects_missing_manifest_member_and_adapter_owned_directory
  - test_invalid_directory_structure_is_rejected
- path: tests/unit/test_local_source.py
  tests:
  - test_safe_source_with_shell_metacharacters_is_data_only
  - test_manifest_is_stable_and_keeps_original_bytes_after_source_changes
  - test_loader_keeps_valid_and_invalid_syntax_for_adapter_diagnostics
  - test_missing_outside_and_source_root_errors_hide_host_path
  - test_source_root_and_ignore_allow_lists
  - test_file_limit_is_fail_closed_and_large_file_is_skipped
  - test_oversized_file_is_not_read
  - test_symlink_escape_is_rejected_without_reading_target
  - test_open_handle_boundary_is_checked_before_content_read
  - test_link_escape_branch_is_checked_without_host_symlink_privilege
  - test_bad_pattern_is_rejected
  - test_default_scan_never_traverses_unreadable_caches
frontend_test_paths:
- frontend/src/client/live/liveRoundtrip.test.ts
- frontend/src/client/live/mapWire.test.ts
- frontend/src/pages/explorer/SnapshotStructure.test.tsx
- frontend/src/pages/explorer/structureTree.test.ts
revision_history:
- revision: 1
  metadata:
    key: PLAN-TASK-RKG-027
    type: implementation-plan
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-027
    captured_at: 2026-10-01
    captured_against:
      artifacts:
      - key: CTX-TASK-RKG-027
      - key: TASK-RKG-027
        revision: 1
  record: '# PLAN-TASK-RKG-027


    Directory do core dựng từ SourceUnit. Snapshot mới không emit Namespace. Snapshot cũ giữ ID.


    ## Thứ tự


    1. `domain và adapter v2` — bỏ Namespace ở output mới, giữ metadata module. Kiểm: AC-RKG-002, AC-RKG-003.

    2. `storage migration` — CONTAINS cho Directory, khai TBL revision đang implement. Kiểm: DDL chạy
    trên Kùzu đã pin; snapshot cũ còn đọc.

    3. `API và Structure` — một identity Directory cho Graph, List, Structure. Kiểm: AC-RKG-073.


    ## Không làm


    - Không re-index repository người dùng.

    - Không implement Java.

    - Không migration phá snapshot cũ.'
---

# PLAN-TASK-RKG-027

Directory do core dựng từ SourceUnit. Snapshot mới không emit Namespace. Snapshot cũ giữ ID.

## Thứ tự

1. `domain và adapter v2` — bỏ Namespace ở output mới, giữ metadata module. Kiểm: AC-RKG-002, AC-RKG-003.
2. `storage migration` — CONTAINS cho Directory, khai TBL revision đang implement. Kiểm: DDL chạy trên Kùzu đã pin; snapshot cũ còn đọc.
3. `API và Structure` — một identity Directory cho Graph, List, Structure. Kiểm: AC-RKG-073.

## Không làm

- Không re-index repository người dùng.
- Không implement Java.
- Không migration phá snapshot cũ.

## Phạm vi code và kiểm chứng

- `README.md`
- `frontend/src/client/live/liveRoundtrip.test.ts`
- `frontend/src/client/live/mapWire.test.ts`
- `frontend/src/client/live/mapWire.ts`
- `frontend/src/i18n/en.ts`
- `frontend/src/i18n/vi.ts`
- `frontend/src/index.css`
- `frontend/src/pages/conversations/ConversationPage.tsx`
- `frontend/src/pages/explorer/ExplorerPage.tsx`
- `frontend/src/pages/explorer/SnapshotStructure.test.tsx`
- `frontend/src/pages/explorer/SnapshotStructure.tsx`
- `frontend/src/pages/explorer/structureTree.test.ts`
- `frontend/src/pages/explorer/structureTree.ts`
- `frontend/src/types/api.ts`
- `src/rkg/adapters/aiokafka_messaging.py`
- `src/rkg/adapters/conformance.py`
- `src/rkg/adapters/contracts.py`
- `src/rkg/adapters/fastapi_framework.py`
- `src/rkg/adapters/flask_framework.py`
- `src/rkg/adapters/python_language.py`
- `src/rkg/adapters/sqlalchemy_data.py`
- `src/rkg/api/app.py`
- `src/rkg/api/catalog.py`
- `src/rkg/api/serialize.py`
- `src/rkg/domain/context.py`
- `src/rkg/domain/models.py`
- `src/rkg/domain/validation.py`
- `src/rkg/graph/publish.py`
- `src/rkg/ingestion/local.py`
- `src/rkg/jobs/coordinator.py`
- `src/rkg/jobs/structure.py`
- `src/rkg/storage/_util.py`
- `src/rkg/storage/migrate.py`
- `tests/fixtures/domain/source_structure.json`
- `tests/fixtures/storage/ddl_v1.cypher`
- `tests/integration/test_directory_entities.py`
- `tests/integration/test_index_coordinator.py`
- `tests/integration/test_index_language_partition.py`
- `tests/unit/test_adapter_registry.py`
- `tests/unit/test_directory_structure.py`
- `tests/unit/test_local_source.py`

- `python -m pytest tests/integration/test_directory_entities.py tests/integration/test_index_coordinator.py tests/integration/test_index_language_partition.py tests/unit/test_adapter_registry.py tests/unit/test_directory_structure.py tests/unit/test_local_source.py -q`
- Trong `frontend/`: `npm test`, `npm run lint`, `npm run build`.

Các lệnh này mô tả cách kiểm, không khẳng định đã chạy trong lần bổ sung hồ sơ. Kết quả thực thi theo evidence đã ghi của task.

Context: [CTX-TASK-RKG-027](../context/CTX-TASK-RKG-027.yaml). Kết quả triển khai: [DIARY-TASK-RKG-027](../diaries/DIARY-TASK-RKG-027.md).
