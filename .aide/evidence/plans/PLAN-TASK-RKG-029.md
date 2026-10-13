---
key: PLAN-TASK-RKG-029
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-029
revision: 3
plan_date: '2026-10-01'
date_basis:
  commit: e8a47101b5b5173b765bd8fb45b1d15ec2e79db2
  field: author_at converted to Asia/Bangkok
provenance: git-derived implementation plan
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  context: CTX-TASK-RKG-029.yaml
verification_targets:
- path: tests/conformance/test_python_resolution.py
  tests:
  - test_direct_alias_relative_imports_and_await_calls
  - test_shadowing_star_import_dynamic_dispatch_and_constructor_are_not_calls
  - test_unique_instance_method_call_and_reassignment_is_not_guessed
  - test_local_receivers_self_fields_annotations_and_inheritance
  - test_conflicting_parameter_types_and_reassigned_fields_are_not_guessed
  - test_direct_bases_and_explicit_abstraction_only
  - test_local_module_shadows_distribution_name_without_external_fact
  - test_reassigned_import_binding_does_not_create_call
  - test_local_abc_name_does_not_mark_type_as_abstract
- path: tests/conformance/test_sqlalchemy_data.py
  tests:
  - test_declarative_identity_does_not_merge_names_or_guess
  - test_reads_and_writes_follow_executed_patterns
  - test_local_sqlalchemy_module_is_not_analyzed
  - test_lock_selects_adapter_without_entrypoint
- path: tests/integration/test_focused_flow.py
  tests:
  - test_flow_reaches_database_and_ownership_never_expands_siblings
  - test_dependencies_depth_budgets_and_reverse_resource_flow
  - test_api_flow_and_export_share_profile_and_legacy_defaults
  - test_generic_repository_model_stays_at_concrete_caller
- path: tests/integration/test_index_language_partition.py
  tests:
  - test_python_only_repository_still_builds_the_same_graph
  - test_other_language_runs_and_python_does_not_parse
  - test_two_languages_merge_into_one_snapshot
  - test_companion_uses_only_the_parent_language_portion
  - test_unregistered_extension_succeeds_without_language_nodes
  - test_duplicate_language_extension_fails_the_job
  - test_shared_directory_is_built_once_for_two_languages
frontend_test_paths:
- frontend/src/client/live/liveClient.test.ts
- frontend/src/client/mock/focusedFlow.test.ts
- frontend/src/components/graph/flowPresentation.test.ts
- frontend/src/components/graph/graphLayout.test.ts
- frontend/src/pages/explorer/ExplorerPage.test.tsx
revision_history:
- revision: 1
  metadata:
    key: PLAN-TASK-RKG-029
    type: implementation-plan
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-029
    captured_at: 2026-10-01
    captured_against:
      artifacts:
      - key: CTX-TASK-RKG-029
      - key: TASK-RKG-029
        revision: 1
  record: '# PLAN-TASK-RKG-029


    View flow theo loại root, overlay ownership/dependency tách khỏi BFS semantic.


    ## Thứ tự


    1. `traversal` — flow theo root, cycle và budget như neighborhood. Kiểm: AC-RKG-009.

    2. `context` — cùng policy, deterministic. Kiểm: AC-RKG-010.

    3. `receivers và data access` — chỉ binding đơn trị. Kiểm: AC-RKG-013 không fan-out.

    4. `frontend` — cùng identity Directory. Kiểm: AC-RKG-073.


    ## Không làm


    - Không thực thi source.

    - Không nối method generic tới mọi bảng.

    - Không đổi DDL.

    - Không re-index snapshot đang chạy của người dùng trong lát cắt kiểm chứng.'
---

# PLAN-TASK-RKG-029

View flow theo loại root, overlay ownership/dependency tách khỏi BFS semantic.

## Thứ tự

1. `traversal` — flow theo root, cycle và budget như neighborhood. Kiểm: AC-RKG-009.
2. `context` — cùng policy, deterministic. Kiểm: AC-RKG-010.
3. `receivers và data access` — chỉ binding đơn trị. Kiểm: AC-RKG-013 không fan-out.
4. `frontend` — cùng identity Directory. Kiểm: AC-RKG-073.

## Không làm

- Không thực thi source.
- Không nối method generic tới mọi bảng.
- Không đổi DDL.
- Không re-index snapshot đang chạy của người dùng trong lát cắt kiểm chứng.

## Phạm vi code và kiểm chứng

- `frontend/src/client/live/liveClient.test.ts`
- `frontend/src/client/live/liveClient.ts`
- `frontend/src/client/live/mapWire.ts`
- `frontend/src/client/mock/fixtures.ts`
- `frontend/src/client/mock/focusedFlow.test.ts`
- `frontend/src/client/mock/mockClient.ts`
- `frontend/src/components/graph/KnowledgeGraph.tsx`
- `frontend/src/components/graph/RelationshipEdge.tsx`
- `frontend/src/components/graph/RkgEntityNode.tsx`
- `frontend/src/components/graph/flowPresentation.test.ts`
- `frontend/src/components/graph/flowPresentation.ts`
- `frontend/src/components/graph/graphLayout.test.ts`
- `frontend/src/components/graph/graphLayout.ts`
- `frontend/src/i18n/en.ts`
- `frontend/src/i18n/vi.ts`
- `frontend/src/index.css`
- `frontend/src/lib/format.ts`
- `frontend/src/lib/presets.ts`
- `frontend/src/pages/explorer/ExplorerPage.test.tsx`
- `frontend/src/pages/explorer/ExplorerPage.tsx`
- `frontend/src/types/api.ts`
- `src/rkg/adapters/python_language.py`
- `src/rkg/adapters/python_resolution.py`
- `src/rkg/adapters/python_types.py`
- `src/rkg/adapters/sqlalchemy_data.py`
- `src/rkg/api/app.py`
- `src/rkg/graph/context.py`
- `src/rkg/graph/traversal.py`
- `tests/conformance/test_python_resolution.py`
- `tests/conformance/test_sqlalchemy_data.py`
- `tests/integration/test_focused_flow.py`
- `tests/integration/test_index_language_partition.py`

- `python -m pytest tests/conformance/test_python_resolution.py tests/conformance/test_sqlalchemy_data.py tests/integration/test_focused_flow.py tests/integration/test_index_language_partition.py -q`
- Trong `frontend/`: `npm test`, `npm run lint`, `npm run build`.

Các lệnh này mô tả cách kiểm, không khẳng định đã chạy trong lần bổ sung hồ sơ. Kết quả thực thi theo evidence đã ghi của task.

Context: [CTX-TASK-RKG-029](../context/CTX-TASK-RKG-029.yaml). Kết quả triển khai: [DIARY-TASK-RKG-029](../diaries/DIARY-TASK-RKG-029.md).
