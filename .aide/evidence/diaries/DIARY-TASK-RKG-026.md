---
key: DIARY-TASK-RKG-026
type: implementation-diary
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-026
revision: 5
implementation_window:
  from: '2026-09-29'
  through: '2026-09-29'
provenance: reconstructed-from-committed-diff-and-prior-evidence
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  implementation_commits:
  - d2148a52e04e5d79780c59afd4414ad065771bd7
prior_evidence:
- evidence/context/CTX-TASK-RKG-026.yaml
- evidence/diaries/DIARY-TASK-RKG-026.md
- evidence/plans/PLAN-TASK-RKG-026.md
- evidence/tests/TEST-RKG-UI-STRUCTURE.md
revision_history:
- revision: 1
  metadata:
    key: DIARY-TASK-RKG-026
    type: implementation-diary
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-026
    revision: 1
    captured_at: 2026-09-29
    captured_against:
      artifacts:
      - key: TASK-RKG-026
        revision: 2
      - key: FR-RKG-003
        revision: 8
      - key: UXF-RKG-001
        revision: 7
      - key: SCR-RKG-001
        revision: 8
      - key: UIS-RKG-001
        revision: 7
      - key: CMP-RKG-WEB
        revision: 5
      - key: NFR-RKG-UX-001
        revision: 7
      code_tree: 516f17e+uncommitted-structure-view
    reference_machine:
      os: Windows 10.0.26200
      arch: x86_64
      node: 24.20.0
      npm: 11.19.0
  record: "# DIARY-TASK-RKG-026\n\n## Diễn giải\n\n- 2026-09-29 — Thêm nút Structure vào nhóm view Graph\
    \ / List trên Explorer.\n  Canvas đổi sang cây của toàn snapshot. Nguồn là `searchEntities` hiện có,\n\
    \  lặp trang đến hết. Không route, nav item, tab drawer, panel hay endpoint mới.\n- Nhóm theo `EntityType`\
    \ theo thứ tự UIS, rồi tách `qualified_name` bằng dấu `.`.\n  Qualified name rỗng thì dùng `name`.\
    \ Chọn lá gọi cùng đường mở detail drawer\n  với List, không đổi subgraph hay preset.\n- NFR-RKG-UX-001\
    \ không tăng revision: cây nằm trong canvas, có keyboard, focus\n  visible, và loading/empty/error\
    \ trong vùng đó.\n\n## Đi chệch\n\n- Chưa bấm trên trình duyệt ở desktop hay viewport hẹp. Phiên này\
    \ không có\n  công cụ trình duyệt; kiểm tra hành vi bằng test UI mock.\n\n## Đánh đổi\n\n- UI/UX Gate\
    \ giữ `pending`. Không tạo approval mới, không commit, không sửa\n  `PLAN.md`, `API-RKG-CORE-v1` hay\
    \ `TBL-RKG-GRAPH`.\n\n## Phản biện\n\nCây lấy search của snapshot nên không bị cắt bởi depth/max_nodes\
    \ của subgraph.\nCùng `name` nhưng khác `qualified_name` nằm ở hai nhánh. Snapshot không có\nentity\
    \ thì empty, không dựng cây giả."
---

# DIARY-TASK-RKG-026

## Diễn giải

- 2026-09-29 — Thêm nút Structure vào nhóm view Graph / List trên Explorer.
  Canvas đổi sang cây của toàn snapshot. Nguồn là `searchEntities` hiện có,
  lặp trang đến hết. Không route, nav item, tab drawer, panel hay endpoint mới.
- Nhóm theo `EntityType` theo thứ tự UIS, rồi tách `qualified_name` bằng dấu `.`.
  Qualified name rỗng thì dùng `name`. Chọn lá gọi cùng đường mở detail drawer
  với List, không đổi subgraph hay preset.
- NFR-RKG-UX-001 không tăng revision: cây nằm trong canvas, có keyboard, focus
  visible, và loading/empty/error trong vùng đó.

## Đi chệch

- Chưa bấm trên trình duyệt ở desktop hay viewport hẹp. Phiên này không có
  công cụ trình duyệt; kiểm tra hành vi bằng test UI mock.

## Đánh đổi

- UI/UX Gate giữ `pending`. Không tạo approval mới, không commit, không sửa
  `PLAN.md`, `API-RKG-CORE-v1` hay `TBL-RKG-GRAPH`.

## Phản biện

Cây lấy search của snapshot nên không bị cắt bởi depth/max_nodes của subgraph.
Cùng `name` nhưng khác `qualified_name` nằm ở hai nhánh. Snapshot không có
entity thì empty, không dựng cây giả.

## Đối chiếu commit và phạm vi hiện hành

## Kết quả đối chiếu triển khai

Thêm Structure cạnh Graph/List, lấy toàn bộ trang entity của snapshot và dùng selection/drawer hiện có; không thêm route/panel hoặc identity thứ hai.

Các file thay đổi được xác định bằng Git diff của các commit được pin trong frontmatter. Current-tree hash nằm trong context revision 3; khác hash lịch sử là revision về sau, không phải cùng lần chạy.

## Diễn giải và correction

Hồ sơ cũ ghi chưa kiểm browser. Code hiện tại đã nhận Directory identity từ task 027; task 026 vẫn là lát cắt Structure ban đầu, không tự nhận AC Directory.

## Kết quả lần bổ sung hồ sơ

Đã đọc commit/file, parse test declarations và liên kết evidence; không chạy lại runtime test hoặc đo KPI. Không nhận đây là review code độc lập hay approval.
