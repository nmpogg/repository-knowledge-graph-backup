---
key: DIARY-TASK-RKG-004
type: implementation-diary
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-004
revision: 5
implementation_window:
  from: '2026-09-24'
  through: '2026-09-24'
provenance: reconstructed-from-committed-diff-and-prior-evidence
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  implementation_commits:
  - b10116e027f792991f03f7959a114834a33cf72d
  - fd729652ec74e5e411466b4d381a0da92ce45dc5
prior_evidence:
- evidence/context/CTX-TASK-RKG-004.yaml
- evidence/diaries/DIARY-TASK-RKG-004.md
- evidence/plans/PLAN-TASK-RKG-004.md
revision_history:
- revision: 1
  metadata:
    key: DIARY-TASK-RKG-004
    type: implementation-diary
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-004
    revision: 1
    captured_at: 2026-09-24
    captured_against:
      artifacts:
      - key: TASK-RKG-004
      - key: CTX-TASK-RKG-004
      - key: PLAN-TASK-RKG-004
  record: '# DIARY-TASK-RKG-004


    ## Diễn giải


    - 2026-09-24 — Contract adapter version hóa tách khỏi coordinator: core chỉ gọi descriptor, không
    branch theo ID.

    - 2026-09-24 — Conformance fixture chỉ nằm trong test. Bản contract và bản thêm fixture là hai bước,
    để suite không bị tính là implementation sản phẩm.


    ## Đi chệch


    - Không có.


    ## Đánh đổi


    - 2026-09-24 — Chưa sửa registry khi một adapter sản phẩm cần field mới. Field mới phải đi qua contract,
    rồi suite, rồi mới tới adapter.


    ## Câu hỏi mở


    - Contract Gate của API vẫn pending. Suite này không đóng gate đó.'
---

# DIARY-TASK-RKG-004

## Diễn giải

- 2026-09-24 — Contract adapter version hóa tách khỏi coordinator: core chỉ gọi descriptor, không branch theo ID.
- 2026-09-24 — Conformance fixture chỉ nằm trong test. Bản contract và bản thêm fixture là hai bước, để suite không bị tính là implementation sản phẩm.

## Đi chệch

- Không có.

## Đánh đổi

- 2026-09-24 — Chưa sửa registry khi một adapter sản phẩm cần field mới. Field mới phải đi qua contract, rồi suite, rồi mới tới adapter.

## Câu hỏi mở

- Contract Gate của API vẫn pending. Suite này không đóng gate đó.

## Đối chiếu commit và phạm vi hiện hành

## Kết quả đối chiếu triển khai

Định nghĩa adapter descriptor, version/capabilities, registry và FactBatch; kiểm fixture adapter độc lập qua conformance runner.

Các file thay đổi được xác định bằng Git diff của các commit được pin trong frontmatter. Current-tree hash nằm trong context revision 3; khác hash lịch sử là revision về sau, không phải cùng lần chạy.

## Diễn giải và correction

Hành vi và các lần kiểm đã ghi trong prior evidence giữ nguyên; bản này bổ sung liên kết và nguồn commit, không thay kết quả cũ.

## Kết quả lần bổ sung hồ sơ

Đã đọc commit/file, parse test declarations và liên kết evidence; không chạy lại runtime test hoặc đo KPI. Không nhận đây là review code độc lập hay approval.
