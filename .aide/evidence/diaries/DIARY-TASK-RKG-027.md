---
key: DIARY-TASK-RKG-027
type: implementation-diary
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-027
revision: 5
implementation_window:
  from: '2026-10-01'
  through: '2026-10-01'
provenance: reconstructed-from-committed-diff-and-prior-evidence
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  implementation_commits:
  - 64739d4e674050f4944baf4aaa609cbcc86acf3b
  - 08fd2d0f7b27f598cf65a9512bf60aa70c9412e2
prior_evidence:
- evidence/context/CTX-TASK-RKG-027.yaml
- evidence/diaries/DIARY-TASK-RKG-027.md
- evidence/plans/PLAN-TASK-RKG-027.md
revision_history:
- revision: 1
  metadata:
    key: DIARY-TASK-RKG-027
    type: implementation-diary
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-027
    revision: 1
    captured_at: 2026-10-01
    captured_against:
      artifacts:
      - key: TASK-RKG-027
      - key: CTX-TASK-RKG-027
      - key: PLAN-TASK-RKG-027
  record: '# DIARY-TASK-RKG-027


    ## Diễn giải


    - 2026-10-01 — Directory do core dựng từ SourceUnit đã có trong manifest. Adapter không emit Repository
    hay Directory.

    - 2026-10-01 — Snapshot cũ giữ Namespace, ID và pin. Snapshot mới không tạo Namespace.


    ## Đi chệch


    - Không re-index repository đang dùng. Áp dụng khi người dùng chạy index lại.


    ## Đánh đổi


    - 2026-10-01 — Migration CONTAINS là non-destructive. Rollback phải đọc lại snapshot cũ, nên kiểm
    migration trước khi nhận task xong.


    ## Câu hỏi mở


    - Contract Gate vẫn pending sau khi DDL chạy. Chạy DDL không phải chữ ký gate.'
---

# DIARY-TASK-RKG-027

## Diễn giải

- 2026-10-01 — Directory do core dựng từ SourceUnit đã có trong manifest. Adapter không emit Repository hay Directory.
- 2026-10-01 — Snapshot cũ giữ Namespace, ID và pin. Snapshot mới không tạo Namespace.

## Đi chệch

- Không re-index repository đang dùng. Áp dụng khi người dùng chạy index lại.

## Đánh đổi

- 2026-10-01 — Migration CONTAINS là non-destructive. Rollback phải đọc lại snapshot cũ, nên kiểm migration trước khi nhận task xong.

## Câu hỏi mở

- Contract Gate vẫn pending sau khi DDL chạy. Chạy DDL không phải chữ ký gate.

## Đối chiếu commit và phạm vi hiện hành

## Kết quả đối chiếu triển khai

Chuyển adapter v2, core Directory từ manifest, giữ legacy Namespace reads/pins, migration CONTAINS không phá dữ liệu và đồng bộ API/UI identity.

Các file thay đổi được xác định bằng Git diff của các commit được pin trong frontmatter. Current-tree hash nằm trong context revision 3; khác hash lịch sử là revision về sau, không phải cùng lần chạy.

## Diễn giải và correction

DDL/migration execution và legacy snapshot preservation được ghi trong TEST-RKG-DIRECTORY-IMPLEMENTATION-001; không suy ra Contract approval.

## Kết quả lần bổ sung hồ sơ

Đã đọc commit/file, parse test declarations và liên kết evidence; không chạy lại runtime test hoặc đo KPI. Không nhận đây là review code độc lập hay approval.
