---
key: PLAN-TASK-RKG-022
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-022
revision: 3
plan_date: '2026-09-28'
date_basis:
  commit: adcf43816acefc63d615f2c9f90cda18dbea054d
  field: author_at converted to Asia/Bangkok
provenance: git-derived implementation plan
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  context: CTX-TASK-RKG-022.yaml
verification_targets:
- path: tests/integration/test_pilot_corpus.py
  tests:
  - test_pilot_has_reviewable_edges_in_every_required_stratum
  - test_grounded_retrieval_preserves_requested_pilot_relations
frontend_test_paths: []
revision_history:
- revision: 1
  metadata:
    key: PLAN-TASK-RKG-022
    type: implementation-plan
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-022
    captured_at: 2026-09-28
    captured_against:
      artifacts:
      - key: CTX-TASK-RKG-022
      - key: TASK-RKG-022
        revision: 1
  record: '# PLAN-TASK-RKG-022


    Đo extraction, Q&A và p95 trên corpus đã chọn. Ghi mẫu và finding, kể cả khi ngưỡng không đạt.


    ## Thứ tự


    1. `pilot corpus` — review sample theo từng nhóm. Kiểm: evidence corpus đã pin.

    2. `Q&A eval` — bộ câu hỏi và hội thoại nhiều lượt. Kiểm: summary có omission.

    3. `benchmark` — wall time scan và p95 search/context, tách latency LLM. Kiểm: AC-RKG-037, AC-RKG-039,
    AC-RKG-062.


    ## Không làm


    - Không sửa ngưỡng NFR để thành pass.

    - Không đóng gate từ kết quả đo.'
---

# PLAN-TASK-RKG-022

Đo extraction, Q&A và p95 trên corpus đã chọn. Ghi mẫu và finding, kể cả khi ngưỡng không đạt.

## Thứ tự

1. `pilot corpus` — review sample theo từng nhóm. Kiểm: evidence corpus đã pin.
2. `Q&A eval` — bộ câu hỏi và hội thoại nhiều lượt. Kiểm: summary có omission.
3. `benchmark` — wall time scan và p95 search/context, tách latency LLM. Kiểm: AC-RKG-037, AC-RKG-039, AC-RKG-062.

## Không làm

- Không sửa ngưỡng NFR để thành pass.
- Không đóng gate từ kết quả đo.

## Phạm vi code và kiểm chứng

- `README.md`
- `tests/integration/test_pilot_corpus.py`
- `src/rkg/conversations/grounded.py`
- `src/rkg/graph/context.py`
- `tests/evaluation/run_pilot_benchmark.py`
- `tests/evaluation/run_pilot_qa.py`
- `tests/evaluation/run_pilot_review.py`

- `python -m pytest tests/integration/test_pilot_corpus.py -q`

Các lệnh này mô tả cách kiểm, không khẳng định đã chạy trong lần bổ sung hồ sơ. Kết quả thực thi theo evidence đã ghi của task.

Context: [CTX-TASK-RKG-022](../context/CTX-TASK-RKG-022.yaml). Kết quả triển khai: [DIARY-TASK-RKG-022](../diaries/DIARY-TASK-RKG-022.md).
