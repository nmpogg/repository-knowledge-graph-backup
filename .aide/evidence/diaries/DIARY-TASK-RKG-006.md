---
key: DIARY-TASK-RKG-006
type: implementation-diary
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-006
revision: 5
implementation_window:
  from: '2026-09-24'
  through: '2026-09-24'
provenance: reconstructed-from-committed-diff-and-prior-evidence
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  implementation_commits:
  - c91e4d2ff0b249848e0d39f26bbe5b161b95abb5
prior_evidence:
- evidence/context/CTX-TASK-RKG-006.yaml
- evidence/diaries/DIARY-TASK-RKG-006.md
- evidence/plans/PLAN-TASK-RKG-006.md
revision_history:
- revision: 1
  metadata:
    key: DIARY-TASK-RKG-006
    type: implementation-diary
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-006
    revision: 1
    captured_at: 2026-09-24
    captured_against:
      artifacts:
      - key: TASK-RKG-006
        revision: 5
      - key: FR-RKG-002
        revision: 8
      - key: REG-ADAPTER-001
        revision: 2
      - key: CMP-RKG-ANALYZER
        revision: 5
      code_revision: c91e4d2ff0b249848e0d39f26bbe5b161b95abb5
  record: '# DIARY-TASK-RKG-006 — Python import, call and class resolution


    ## Implementation


    `PythonLanguageAdapter.resolve` now uses a static, repository-local symbol index.

    It resolves direct, aliased and relative imports to unique internal modules or

    symbols; resolves direct and module-qualified function calls, including `await`;

    and emits direct `inherits_from` plus `implements` only for explicitly declared

    abstractions. Every new edge has a versioned rule and source location. Repeated

    call sites aggregate evidence on one edge.


    Parameters, assignments, duplicate definitions, conditional bindings, star

    imports, instance/`self` dispatch, constructors, module-level calls and unresolved

    targets do not produce guessed `calls` edges. Unsupported or ambiguous cases

    produce path/line diagnostics with fixed messages. Local modules can shadow

    external names, including `abc` and `fastapi`; the resolver does not infer package

    distributions or deep-adapter support from an import name. The adapter advertises

    `calls`, `classes`, `imports` and `structure`; `metadata` remains for later tasks.


    ## Verification on code revision above


    | Contract test ID | Test case | Result |

    | --- | --- | --- |

    | `TEST-RKG-IMPORT-RESOLVE` | `test_direct_alias_relative_imports_and_await_calls` | pass: direct/alias/relative
    local imports and evidence aggregation |

    | `TEST-RKG-CALL-RESOLVE` | `test_direct_alias_relative_imports_and_await_calls`, `test_reassigned_import_binding_does_not_create_call`
    | pass: unique direct/module calls and `await`; reassigned alias omitted |

    | `TEST-RKG-NO-GUESS` | `test_shadowing_star_import_dynamic_dispatch_and_constructor_are_not_calls`
    | pass: no speculative calls; path/line diagnostics |

    | `TEST-RKG-CLASS-REL` | `test_direct_bases_and_explicit_abstraction_only`, `test_local_abc_name_does_not_mark_type_as_abstract`
    | pass: direct bases and explicit abstract relation only |

    | `TEST-RKG-DETECT-NEG` | `test_local_module_shadows_distribution_name_without_external_fact`, `test_local_abc_name_does_not_mark_type_as_abstract`
    | pass for local-name shadowing; no inferred distribution/external fact |

    | `TEST-RKG-ADAPTER-CONFORMANCE` | `test_direct_alias_relative_imports_and_await_calls` and existing
    Python conformance test | pass: all 14 language contract checks |


    `.venv/Scripts/python.exe -m pytest tests/conformance/test_python_resolution.py -q`

    reported **6 passed**. Current-tree `.venv/Scripts/python.exe -m pytest -q`

    reported **39 passed, 1 skipped** and `.venv/Scripts/ruff.exe check src tests`

    reported **All checks passed**. The existing symlink test is skipped on this

    Windows host. Verification used Python 3.12.5; the project pin is 3.12.14.


    ## Scope limit


    This is adapter-level verification. Dynamic web routes in AC-RKG-006 require the

    framework adapter task; distribution inventory and deep-adapter capability checks

    in AC-RKG-021 require detection/metadata tasks. End-to-end graph publication is

    outside TASK-RKG-006.'
---

# DIARY-TASK-RKG-006

## Implementation

`PythonLanguageAdapter.resolve` now uses a static, repository-local symbol index.
It resolves direct, aliased and relative imports to unique internal modules or
symbols; resolves direct and module-qualified function calls, including `await`;
and emits direct `inherits_from` plus `implements` only for explicitly declared
abstractions. Every new edge has a versioned rule and source location. Repeated
call sites aggregate evidence on one edge.

Parameters, assignments, duplicate definitions, conditional bindings, star
imports, instance/`self` dispatch, constructors, module-level calls and unresolved
targets do not produce guessed `calls` edges. Unsupported or ambiguous cases
produce path/line diagnostics with fixed messages. Local modules can shadow
external names, including `abc` and `fastapi`; the resolver does not infer package
distributions or deep-adapter support from an import name. The adapter advertises
`calls`, `classes`, `imports` and `structure`; `metadata` remains for later tasks.

## Verification on code revision above

| Contract test ID | Test case | Result |
| --- | --- | --- |
| `TEST-RKG-IMPORT-RESOLVE` | `test_direct_alias_relative_imports_and_await_calls` | pass: direct/alias/relative local imports and evidence aggregation |
| `TEST-RKG-CALL-RESOLVE` | `test_direct_alias_relative_imports_and_await_calls`, `test_reassigned_import_binding_does_not_create_call` | pass: unique direct/module calls and `await`; reassigned alias omitted |
| `TEST-RKG-NO-GUESS` | `test_shadowing_star_import_dynamic_dispatch_and_constructor_are_not_calls` | pass: no speculative calls; path/line diagnostics |
| `TEST-RKG-CLASS-REL` | `test_direct_bases_and_explicit_abstraction_only`, `test_local_abc_name_does_not_mark_type_as_abstract` | pass: direct bases and explicit abstract relation only |
| `TEST-RKG-DETECT-NEG` | `test_local_module_shadows_distribution_name_without_external_fact`, `test_local_abc_name_does_not_mark_type_as_abstract` | pass for local-name shadowing; no inferred distribution/external fact |
| `TEST-RKG-ADAPTER-CONFORMANCE` | `test_direct_alias_relative_imports_and_await_calls` and existing Python conformance test | pass: all 14 language contract checks |

`.venv/Scripts/python.exe -m pytest tests/conformance/test_python_resolution.py -q`
reported **6 passed**. Current-tree `.venv/Scripts/python.exe -m pytest -q`
reported **39 passed, 1 skipped** and `.venv/Scripts/ruff.exe check src tests`
reported **All checks passed**. The existing symlink test is skipped on this
Windows host. Verification used Python 3.12.5; the project pin is 3.12.14.

## Scope limit

This is adapter-level verification. Dynamic web routes in AC-RKG-006 require the
framework adapter task; distribution inventory and deep-adapter capability checks
in AC-RKG-021 require detection/metadata tasks. End-to-end graph publication is
outside TASK-RKG-006.

## Đối chiếu commit và phạm vi hiện hành

## Kết quả đối chiếu triển khai

Resolve symbol/alias/import/call/class có bằng chứng; unresolved/dynamic phải trả diagnostic, không tạo cạnh suy đoán.

Các file thay đổi được xác định bằng Git diff của các commit được pin trong frontmatter. Current-tree hash nằm trong context revision 3; khác hash lịch sử là revision về sau, không phải cùng lần chạy.

## Diễn giải và correction

Hành vi và các lần kiểm đã ghi trong prior evidence giữ nguyên; bản này bổ sung liên kết và nguồn commit, không thay kết quả cũ.

## Kết quả lần bổ sung hồ sơ

Đã đọc commit/file, parse test declarations và liên kết evidence; không chạy lại runtime test hoặc đo KPI. Không nhận đây là review code độc lập hay approval.
