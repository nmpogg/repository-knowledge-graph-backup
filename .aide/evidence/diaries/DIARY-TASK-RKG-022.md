---
key: DIARY-TASK-RKG-022
type: implementation-diary
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-022
revision: 5
implementation_window:
  from: '2026-09-28'
  through: '2026-09-28'
provenance: reconstructed-from-committed-diff-and-prior-evidence
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  implementation_commits:
  - adcf43816acefc63d615f2c9f90cda18dbea054d
  - 323035184d036d3b437e62a242ce38d1c01ae08f
  - 7eec602eede39b4b8bee42131d9379ac61d07c29
  - 8153d3e8e55c8861dc4e95ceb48f276767b0f0de
prior_evidence:
- evidence/context/CTX-TASK-RKG-022.yaml
- evidence/diaries/DIARY-TASK-RKG-022.md
- evidence/diaries/DIARY-TASK-RKG-022.md
- evidence/plans/PLAN-TASK-RKG-022.md
- evidence/tests/TEST-RKG-ADAPTER-CONFORMANCE.json
- evidence/tests/TEST-RKG-ADAPTER-CONFORMANCE.json
- evidence/tests/TEST-RKG-EXTRACTION-FIXTURES-001.md
- evidence/tests/TEST-RKG-PERF-001.json
- evidence/tests/TEST-RKG-PERF-001.json
- evidence/tests/TEST-RKG-PERF-001.json
- evidence/tests/TEST-RKG-PERF-001.json
- evidence/tests/TEST-RKG-PERF-SUMMARY-001.md
- evidence/tests/TEST-RKG-PILOT-CORPUS-001.md
- evidence/tests/TEST-RKG-PILOT-CORPUS-002.md
- evidence/tests/TEST-RKG-PILOT-REVIEW-001.json
- evidence/tests/TEST-RKG-PILOT-REVIEW-SUMMARY-001.md
- evidence/tests/TEST-RKG-QA-EVAL-001.json
- evidence/tests/TEST-RKG-QA-EVAL-001.json
- evidence/tests/TEST-RKG-QA-EVAL-001.json
- evidence/tests/TEST-RKG-QA-EVAL-001.json
- evidence/tests/TEST-RKG-QA-EVAL-001.json
- evidence/tests/TEST-RKG-QA-EVAL-001.json
- evidence/tests/TEST-RKG-QA-EVAL-SUMMARY-001.md
- evidence/tests/TEST-RKG-QA-EVAL-SUMMARY-001.md
- evidence/tests/TEST-RKG-QA-EVAL-SUMMARY-001.md
- evidence/tests/TEST-RKG-QA-EVAL-SUMMARY-001.md
revision_history:
- revision: 1
  metadata:
    key: DIARY-TASK-RKG-022
    type: implementation-diary
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-022
    revision: 1
    captured_at: 2026-09-28
    captured_against:
      base_commit: adcf43816acefc63d615f2c9f90cda18dbea054d
      task_revision: 8
      pilot_tree_sha256: 7acca861c59558ded14fc9aade5cebe35e9cb627c3d803331990d404371dda2c
      code_tree: working-tree-file-hashes-below
  record: '# DIARY-TASK-RKG-022 — Pilot evaluation and benchmark


    The selected corpus is the sibling `../pilot_fastapi/` pinned by

    `TEST-RKG-PILOT-CORPUS-002`. Task work added reproducible benchmark, pilot

    review and grounded-Q&A runners in `tests/evaluation/`, and pilot integration

    coverage in `tests/integration/test_pilot_corpus.py`. The benchmark and QA

    reports pin the pilot tree and relevant code/config hashes. The Task 22

    working copy of the pilot contains the same source digest and lives in an

    ignored workspace directory to support network-constrained eval runs.


    The context API now chooses a character-budget removal prefix by binary

    search, preserving the previous output on checked pilot budgets. Grounded

    conversation retrieval filters relationship types from the question and

    resolves a vague follow-up against the prior focus and relationship. These

    changes passed the offline tests, but the final follow-up revision has not

    been measured with the live provider because the next provider request

    returned HTTP 403.


    Current-tree verification: `python -m pytest tests -q` returned 134 passed,

    4 skipped; `ruff check src tests` passed; `git diff --check` passed. The

    test run emitted one existing Starlette TestClient deprecation warning.


    | Working-tree file | SHA-256 |

    | --- | --- |

    | `src/rkg/conversations/grounded.py` | `302aef99c7098f5068f556ab50c56ae841792d595df9032f265960c4b8e65528`
    |

    | `src/rkg/graph/context.py` | `8fdd692f6f167b40ad72f4f3add5822adf301a5041c1d5c45fdb7313c50ded37`
    |

    | `tests/integration/test_pilot_corpus.py` | `1144c8f58c053ea9dacde351c4357a41519206d1c3e43133ebf55d3953dcd5fe`
    |

    | `tests/evaluation/run_pilot_benchmark.py` | `22553f8c199e4498fd2260d464e5804fce499a2291177d556ff6dd7ded2646c8`
    |

    | `tests/evaluation/run_pilot_review.py` | `13694a46fed8881364c43626e9fe086012b0a1873449e0e5dabb453ef45f27c1`
    |

    | `tests/evaluation/run_pilot_qa.py` | `536a32dfd2d201004ba8219ac99f89ade04881d6032707dbf74de73f22a0f6cf`
    |


    Evidence and findings are summarized in

    `TEST-RKG-EXTRACTION-FIXTURES-001`,

    `TEST-RKG-PILOT-REVIEW-SUMMARY-001`,

    `TEST-RKG-QA-EVAL-SUMMARY-001`,

    `TEST-RKG-PERF-SUMMARY-001` and

    `TEST-RKG-ADAPTER-CONFORMANCE.json`. Their raw JSON reports remain

    separate and historical revisions are retained. No Task 22 acceptance or

    pilot precision is claimed while the findings in the task remain open.'
- revision: 2
  metadata:
    key: DIARY-TASK-RKG-022-r2
    type: implementation-diary
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-022
    revision: 2
    captured_at: 2026-09-28
    captured_against:
      task_revision: 12
      code_commit: 7eec602eede39b4b8bee42131d9379ac61d07c29
      pilot_tree_sha256: 7acca861c59558ded14fc9aade5cebe35e9cb627c3d803331990d404371dda2c
      artifacts:
      - key: OBS-RKG-001
        revision: 2
      - key: OBS-RKG-002
        revision: 4
      - key: OBS-RKG-005
        revision: 3
      - key: NFR-RKG-PERF-001
        revision: 5
---

# DIARY-TASK-RKG-022

The selected corpus is the sibling `../pilot_fastapi/` pinned by
`TEST-RKG-PILOT-CORPUS-002`. Task work added reproducible benchmark, pilot
review and grounded-Q&A runners in `tests/evaluation/`, and pilot integration
coverage in `tests/integration/test_pilot_corpus.py`. The benchmark and QA
reports pin the pilot tree and relevant code/config hashes. The Task 22
working copy of the pilot contains the same source digest and lives in an
ignored workspace directory to support network-constrained eval runs.

The context API now chooses a character-budget removal prefix by binary
search, preserving the previous output on checked pilot budgets. Grounded
conversation retrieval filters relationship types from the question and
resolves a vague follow-up against the prior focus and relationship. These
changes passed the offline tests, but the final follow-up revision has not
been measured with the live provider because the next provider request
returned HTTP 403.

Current-tree verification: `python -m pytest tests -q` returned 134 passed,
4 skipped; `ruff check src tests` passed; `git diff --check` passed. The
test run emitted one existing Starlette TestClient deprecation warning.

| Working-tree file | SHA-256 |
| --- | --- |
| `src/rkg/conversations/grounded.py` | `302aef99c7098f5068f556ab50c56ae841792d595df9032f265960c4b8e65528` |
| `src/rkg/graph/context.py` | `8fdd692f6f167b40ad72f4f3add5822adf301a5041c1d5c45fdb7313c50ded37` |
| `tests/integration/test_pilot_corpus.py` | `1144c8f58c053ea9dacde351c4357a41519206d1c3e43133ebf55d3953dcd5fe` |
| `tests/evaluation/run_pilot_benchmark.py` | `22553f8c199e4498fd2260d464e5804fce499a2291177d556ff6dd7ded2646c8` |
| `tests/evaluation/run_pilot_review.py` | `13694a46fed8881364c43626e9fe086012b0a1873449e0e5dabb453ef45f27c1` |
| `tests/evaluation/run_pilot_qa.py` | `536a32dfd2d201004ba8219ac99f89ade04881d6032707dbf74de73f22a0f6cf` |

Evidence and findings are summarized in
`TEST-RKG-EXTRACTION-FIXTURES-001`,
`TEST-RKG-PILOT-REVIEW-SUMMARY-001`,
`TEST-RKG-QA-EVAL-SUMMARY-001`,
`TEST-RKG-PERF-SUMMARY-001` and
`TEST-RKG-ADAPTER-CONFORMANCE.json`. Their raw JSON reports remain
separate and historical revisions are retained. No Task 22 acceptance or
pilot precision is claimed while the findings in the task remain open.

## Lịch sử revision 2

# DIARY-TASK-RKG-022-r2 — Task closure with open acceptance findings

The Task 22 pilot, fixture, adapter, Q&A and benchmark executions and
their raw reports are published under `.aide/evidence/tests/`. The latest
Q&A run is `TEST-RKG-QA-EVAL-001.json`; its coordinator SHA-256 matches
the code at the commit above. The sibling pilot's 23-file source digest
still matches the selected corpus. The adapter conformance report is
`TEST-RKG-ADAPTER-CONFORMANCE.json`.

Current-tree verification before setting the task status to `done`:

| Check | Result |
| --- | --- |
| `python -m pytest tests -q` | 134 passed, 4 skipped; one existing Starlette deprecation warning |
| `ruff check src tests` | pass |
| Pilot digest and Q&A coordinator hash | match pinned report and current code |

The task status records completed execution and publication, including
negative findings. It is not a pass or waiver of the following acceptance
criteria:

- KPI-RKG-001 has no reviewed canonical expected-fact census and no
  calculated fixture coverage/precision; see
  `TEST-RKG-EXTRACTION-FIXTURES-001`.
- KPI-RKG-002 has 160 deterministic samples with provisional AST labels,
  but Product Owner/Tech Lead source adjudication is pending; see
  `TEST-RKG-PILOT-REVIEW-SUMMARY-001`.
- NFR-RKG-PERF-001 context p95 failed in two historical runs and reference
  host eligibility is unconfirmed; see `TEST-RKG-PERF-SUMMARY-001`.

The latest Q&A report meets the recorded OBS-RKG-005 targets; earlier
failures remain in historical reports. Carry the open items into the final
runbook/handoff and MVP gate. No reviewer decision or waiver is inferred
from this task status.

## Đối chiếu commit và phạm vi hiện hành

## Kết quả đối chiếu triển khai

Pin corpus, chạy extraction/conformance, sampling/Q&A và benchmark; công bố method/raw reports/omissions, không sửa threshold để biến failure thành pass.

Các file thay đổi được xác định bằng Git diff của các commit được pin trong frontmatter. Current-tree hash nằm trong context revision 3; khác hash lịch sử là revision về sau, không phải cùng lần chạy.

## Diễn giải và correction

Done ghi việc chạy/công bố báo cáo. Fixture census chưa đo đủ, owner adjudication và context p95 còn finding theo báo cáo gốc; không có waiver.

## Kết quả lần bổ sung hồ sơ

Đã đọc commit/file, parse test declarations và liên kết evidence; không chạy lại runtime test hoặc đo KPI. Không nhận đây là review code độc lập hay approval.
