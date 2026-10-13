---
key: DIARY-TASK-RKG-005
type: implementation-diary
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-005
revision: 5
implementation_window:
  from: '2026-09-24'
  through: '2026-09-24'
provenance: reconstructed-from-committed-diff-and-prior-evidence
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  implementation_commits:
  - 49e89097ee167403c0662ec85034a81f99c8aa4d
prior_evidence:
- evidence/context/CTX-TASK-RKG-005.yaml
- evidence/diaries/DIARY-TASK-RKG-005.md
- evidence/plans/PLAN-TASK-RKG-005.md
revision_history:
- revision: 1
  metadata:
    key: DIARY-TASK-RKG-005
    type: implementation-diary
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-005
    revision: 1
    captured_at: 2026-09-24
    captured_against:
      artifacts:
      - key: TASK-RKG-005
        revision: 4
      - key: FR-RKG-001
        revision: 7
      - key: FR-RKG-002
        revision: 8
      - key: REG-ADAPTER-001
        revision: 2
      - key: NFR-RKG-EXT-001
        revision: 3
      code_revision: 49e89097ee167403c0662ec85034a81f99c8aa4d
  record: '# DIARY-TASK-RKG-005 — Python AST and lexical scope


    ## Implementation


    `PythonLanguageAdapter` implements `rkg.adapter/v1` from immutable manifest bytes.

    It parses with CPython 3.12 AST, reports syntax errors per relative file path and

    line, and continues extracting valid files. It emits `SourceUnit`, `Namespace`,

    `Type`, `Callable`, `contains` and versioned source evidence in a generic `FactBatch`.

    The symbol index preserves lexical owners across classes, functions and control

    blocks. Duplicate definitions produce a diagnostic and do not attach children to

    the earlier binding. The adapter neither imports nor executes analyzed source.


    The descriptor advertises only `structure`, the capability implemented at this

    revision. Detection reports no inferred Python source version. Import/call/class

    resolution and other MVP capabilities remain in later tasks.


    ## Verification on code revision above


    | Contract test ID | Test case | Result |

    | --- | --- | --- |

    | `TEST-RKG-SOURCE-STRUCTURE` | `test_source_structure_matches_golden` | pass: exact golden nodes,
    lexical symbol names and `contains` edges |

    | `TEST-RKG-SYNTAX-DIAGNOSTIC` | `test_syntax_error_is_isolated_and_path_safe` | pass: valid file
    extracted; invalid file has path/line diagnostic and no facts |

    | `TEST-RKG-NO-GUESS` | `test_no_guessed_relationships_and_duplicate_binding`; `test_control_blocks_keep_lexical_owner_and_duplicate_subtree_is_skipped`
    | pass for structural phase: only `contains` edges, duplicate diagnostic, no speculative relationships
    |

    | `TEST-RKG-SCAN-SAFE` | `test_python_adapter_passes_shared_conformance` | pass: source side-effect
    marker absent |

    | `TEST-RKG-ADAPTER-CONFORMANCE` | `test_python_adapter_passes_shared_conformance` | pass: all 14
    language contract checks |


    Commands: `.venv/Scripts/python.exe -m pytest tests/conformance/test_python_language.py -q`

    reported **5 passed**; `.venv/Scripts/python.exe -m pytest -q` reported **33 passed,

    1 skipped**; `.venv/Scripts/ruff.exe check src tests` reported **All checks passed**.

    The existing symlink test is skipped on this Windows host. Verification used Python

    3.12.5 because the project-pinned 3.12.14 is unavailable locally.


    ## Scope limit


    This is component verification for TASK-RKG-005. End-to-end indexing of AC-RKG-001

    and full AC-RKG-006 import/call ambiguity diagnostics require TASK-RKG-015 and

    TASK-RKG-006 respectively. No claim of full end-to-end AC completion is made here.'
---

# DIARY-TASK-RKG-005

## Implementation

`PythonLanguageAdapter` implements `rkg.adapter/v1` from immutable manifest bytes.
It parses with CPython 3.12 AST, reports syntax errors per relative file path and
line, and continues extracting valid files. It emits `SourceUnit`, `Namespace`,
`Type`, `Callable`, `contains` and versioned source evidence in a generic `FactBatch`.
The symbol index preserves lexical owners across classes, functions and control
blocks. Duplicate definitions produce a diagnostic and do not attach children to
the earlier binding. The adapter neither imports nor executes analyzed source.

The descriptor advertises only `structure`, the capability implemented at this
revision. Detection reports no inferred Python source version. Import/call/class
resolution and other MVP capabilities remain in later tasks.

## Verification on code revision above

| Contract test ID | Test case | Result |
| --- | --- | --- |
| `TEST-RKG-SOURCE-STRUCTURE` | `test_source_structure_matches_golden` | pass: exact golden nodes, lexical symbol names and `contains` edges |
| `TEST-RKG-SYNTAX-DIAGNOSTIC` | `test_syntax_error_is_isolated_and_path_safe` | pass: valid file extracted; invalid file has path/line diagnostic and no facts |
| `TEST-RKG-NO-GUESS` | `test_no_guessed_relationships_and_duplicate_binding`; `test_control_blocks_keep_lexical_owner_and_duplicate_subtree_is_skipped` | pass for structural phase: only `contains` edges, duplicate diagnostic, no speculative relationships |
| `TEST-RKG-SCAN-SAFE` | `test_python_adapter_passes_shared_conformance` | pass: source side-effect marker absent |
| `TEST-RKG-ADAPTER-CONFORMANCE` | `test_python_adapter_passes_shared_conformance` | pass: all 14 language contract checks |

Commands: `.venv/Scripts/python.exe -m pytest tests/conformance/test_python_language.py -q`
reported **5 passed**; `.venv/Scripts/python.exe -m pytest -q` reported **33 passed,
1 skipped**; `.venv/Scripts/ruff.exe check src tests` reported **All checks passed**.
The existing symlink test is skipped on this Windows host. Verification used Python
3.12.5 because the project-pinned 3.12.14 is unavailable locally.

## Scope limit

This is component verification for TASK-RKG-005. End-to-end indexing of AC-RKG-001
and full AC-RKG-006 import/call ambiguity diagnostics require TASK-RKG-015 and
TASK-RKG-006 respectively. No claim of full end-to-end AC completion is made here.

## Đối chiếu commit và phạm vi hiện hành

## Kết quả đối chiếu triển khai

Parse Python tĩnh, tạo scope/symbol/SourceUnit/type/callable và diagnostic; không thực thi module hoặc đoán quan hệ.

Các file thay đổi được xác định bằng Git diff của các commit được pin trong frontmatter. Current-tree hash nằm trong context revision 3; khác hash lịch sử là revision về sau, không phải cùng lần chạy.

## Diễn giải và correction

Hành vi và các lần kiểm đã ghi trong prior evidence giữ nguyên; bản này bổ sung liên kết và nguồn commit, không thay kết quả cũ.

## Kết quả lần bổ sung hồ sơ

Đã đọc commit/file, parse test declarations và liên kết evidence; không chạy lại runtime test hoặc đo KPI. Không nhận đây là review code độc lập hay approval.
