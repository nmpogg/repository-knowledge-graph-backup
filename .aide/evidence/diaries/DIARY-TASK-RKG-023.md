---
key: DIARY-TASK-RKG-023
type: implementation-diary
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-023
revision: 5
implementation_window:
  from: '2026-09-28'
  through: '2026-09-28'
provenance: reconstructed-from-committed-diff-and-prior-evidence
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  implementation_commits:
  - 16208d8a1b93035ac7c705d0b130f0b890d0dbb7
prior_evidence:
- evidence/context/CTX-TASK-RKG-023.yaml
- evidence/diaries/DIARY-TASK-RKG-023.md
- evidence/plans/PLAN-TASK-RKG-023.md
- evidence/tests/TEST-RKG-FINAL-REGRESSION-001.md
revision_history:
- revision: 1
  metadata:
    key: DIARY-TASK-RKG-023
    type: implementation-diary
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-023
    revision: 1
    captured_at: 2026-09-28
    captured_against:
      task_revision: 3
      code_commit: 404f0572ee2eabda61bee535e6ac88e3ddb53fed
      pins:
        cpython: 3.12.14
        host: Windows AMD64
      artifacts:
      - key: TASK-RKG-022
        revision: 12
      - key: TASK-RKG-023
        revision: 3
      - key: EPIC-005-TEAM-RKG
        revision: 3
  record: "# DIARY-TASK-RKG-023 — Final runbook and handoff\n\n## Phạm vi\n\nRunbook vận hành nằm ở `README.md`:\
    \ cài đặt, đường dẫn local và\n`--allow-root`, index, `rkg serve`, LLM, lịch sử hội thoại, retention\
    \ và\nbảng xử lý sự cố. `.aide/README.md` trỏ tới runbook và evidence này.\n`PLAN.md` cập nhật cửa\
    \ sổ điều phối; file đó không phải trạng thái task.\n\nBộ kiểm tra chạy trên mã tại commit ở trên.\
    \ Cây làm việc thêm runbook,\nindex, plan và frontmatter task. Không có thay đổi analyzer/API/UI trong\n\
    lượt này.\n\n## Kiểm chứng\n\n| Lệnh | Kết quả |\n| --- | --- |\n| `uv run ruff check src tests` |\
    \ pass |\n| `uv run pytest tests -q` | 132 passed, 6 skipped; một cảnh báo Starlette TestClient đã\
    \ có sẵn |\n| `npm test` trong `frontend` | 27 passed |\n| `npm run lint` trong `frontend` | exit\
    \ 0; các cảnh báo oxlint đã có trên file UI |\n| `npx tsc -b` trong `frontend` | pass |\n\nSHA-256\
    \ của tài liệu bàn giao:\n\n| File | SHA-256 |\n| --- | --- |\n| `README.md` | `fcbc147c5553547675f73bb726b1b248c897313666adea73a4c18fb04fedf99a`\
    \ |\n| `.aide/README.md` | `97ee584ae7db3d83a95c98f2b1ceb113f3c4e77d4b66c224295d9885e03e9971` |\n\
    | `.aide/lifecycle/tasks/TASK-RKG-023.md` | `ea757600bb3f76f8a7e78a963fad3f06ff62aa1652386275e7343e12c9c35896`\
    \ |\n| `PLAN.md` | `6a7fd3874c236231ddf7c4bd1cbee945edfb3655aff21ac871eff0dbb90fe369` |\n\nChi tiết\
    \ skip, phạm vi và rủi ro còn lại nằm ở\n`TEST-RKG-FINAL-REGRESSION-001`.\n\n## Giới hạn đã ghi, không\
    \ đóng\n\n- KPI-RKG-001 chưa có census expected-fact đã review\n  (`TEST-RKG-EXTRACTION-FIXTURES-001`).\n\
    - KPI-RKG-002 còn chờ Product Owner/Tech Lead chấm mẫu\n  (`TEST-RKG-PILOT-REVIEW-SUMMARY-001`).\n\
    - NFR-RKG-PERF-001: context p95 fail ở hai lần chạy và host này chưa được\n  xác nhận là reference\
    \ host (`TEST-RKG-PERF-SUMMARY-001`).\n- Q&A mới nhất trong `TEST-RKG-QA-EVAL-SUMMARY-001-r4` đạt\
    \ target đã ghi;\n  các lần chạy trước vẫn là evidence lịch sử.\n- `cleanup_snapshots` chưa có lệnh\
    \ CLI hoặc route HTTP. Người vận hành xóa\n  từng snapshot sau khi nhả active, reader và hội thoại\
    \ pin.\n- Máy regression này không có thư mục pilot sibling, nên không đo lại digest\n  pilot. Bằng\
    \ chứng digest vẫn là báo cáo Task 22.\n- `EPIC-005-TEAM-RKG` vẫn `draft`. Finding blocking và chữ\
    \ ký release\n  readiness thuộc người duyệt, không suy ra từ status task này."
---

# DIARY-TASK-RKG-023

## Phạm vi

Runbook vận hành nằm ở `README.md`: cài đặt, đường dẫn local và
`--allow-root`, index, `rkg serve`, LLM, lịch sử hội thoại, retention và
bảng xử lý sự cố. `.aide/README.md` trỏ tới runbook và evidence này.
`PLAN.md` cập nhật cửa sổ điều phối; file đó không phải trạng thái task.

Bộ kiểm tra chạy trên mã tại commit ở trên. Cây làm việc thêm runbook,
index, plan và frontmatter task. Không có thay đổi analyzer/API/UI trong
lượt này.

## Kiểm chứng

| Lệnh | Kết quả |
| --- | --- |
| `uv run ruff check src tests` | pass |
| `uv run pytest tests -q` | 132 passed, 6 skipped; một cảnh báo Starlette TestClient đã có sẵn |
| `npm test` trong `frontend` | 27 passed |
| `npm run lint` trong `frontend` | exit 0; các cảnh báo oxlint đã có trên file UI |
| `npx tsc -b` trong `frontend` | pass |

SHA-256 của tài liệu bàn giao:

| File | SHA-256 |
| --- | --- |
| `README.md` | `fcbc147c5553547675f73bb726b1b248c897313666adea73a4c18fb04fedf99a` |
| `.aide/README.md` | `97ee584ae7db3d83a95c98f2b1ceb113f3c4e77d4b66c224295d9885e03e9971` |
| `.aide/lifecycle/tasks/TASK-RKG-023.md` | `ea757600bb3f76f8a7e78a963fad3f06ff62aa1652386275e7343e12c9c35896` |
| `PLAN.md` | `6a7fd3874c236231ddf7c4bd1cbee945edfb3655aff21ac871eff0dbb90fe369` |

Chi tiết skip, phạm vi và rủi ro còn lại nằm ở
`TEST-RKG-FINAL-REGRESSION-001`.

## Giới hạn đã ghi, không đóng

- KPI-RKG-001 chưa có census expected-fact đã review
  (`TEST-RKG-EXTRACTION-FIXTURES-001`).
- KPI-RKG-002 còn chờ Product Owner/Tech Lead chấm mẫu
  (`TEST-RKG-PILOT-REVIEW-SUMMARY-001`).
- NFR-RKG-PERF-001: context p95 fail ở hai lần chạy và host này chưa được
  xác nhận là reference host (`TEST-RKG-PERF-SUMMARY-001`).
- Q&A mới nhất trong `TEST-RKG-QA-EVAL-SUMMARY-001-r4` đạt target đã ghi;
  các lần chạy trước vẫn là evidence lịch sử.
- `cleanup_snapshots` chưa có lệnh CLI hoặc route HTTP. Người vận hành xóa
  từng snapshot sau khi nhả active, reader và hội thoại pin.
- Máy regression này không có thư mục pilot sibling, nên không đo lại digest
  pilot. Bằng chứng digest vẫn là báo cáo Task 22.
- `EPIC-005-TEAM-RKG` vẫn `draft`. Finding blocking và chữ ký release
  readiness thuộc người duyệt, không suy ra từ status task này.

## Đối chiếu commit và phạm vi hiện hành

## Kết quả đối chiếu triển khai

Ghi setup/index/serve/LLM/history/retention/troubleshooting, chạy regression và chuyển các finding nghiệm thu còn mở trong handoff.

Các file thay đổi được xác định bằng Git diff của các commit được pin trong frontmatter. Current-tree hash nằm trong context revision 3; khác hash lịch sử là revision về sau, không phải cùng lần chạy.

## Diễn giải và correction

Hành vi và các lần kiểm đã ghi trong prior evidence giữ nguyên; bản này bổ sung liên kết và nguồn commit, không thay kết quả cũ.

## Kết quả lần bổ sung hồ sơ

Đã đọc commit/file, parse test declarations và liên kết evidence; không chạy lại runtime test hoặc đo KPI. Không nhận đây là review code độc lập hay approval.
