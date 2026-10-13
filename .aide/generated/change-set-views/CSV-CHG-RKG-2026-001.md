---
key: CSV-CHG-RKG-2026-001
type: change-set-view
group: derived
status: current
revision: 4
non_normative: true
derived_from:
- CHG-RKG-2026-001
hand_written: true
---
> Đây là bản đọc thuận tiện được viết tay trong giai đoạn chưa có generator.
> Khi bản này và artifact normative bất đồng, **artifact normative thắng**.

# Repository Knowledge Graph MVP

## Mục tiêu

Giữ bộ normative của RKG MVP ở phase `implementation_verified`. Implementation
đã có evidence. Bốn gate vẫn pending. Change Set hiện hành không phải approval
và không phải hoàn tất.

## Mục tiêu nghiệp vụ đổi

Intent được bổ sung goal độc lập về extensibility và quyết định local-path-only được
đồng bộ xuống contract/task/schema; traceability, gate và ownership được cập nhật.

## Tính năng mới

5 FR (`FR-RKG-001`…`FR-RKG-005`) bao phủ lifecycle local, evidence graph qua adapter,
relationship, graph query, context, DB/event/config/external dependency, detection đa ngôn ngữ/framework,
onboarding, grounded Q&A, conversation history và repository/snapshot lifecycle.
Acceptance Criteria nằm trong từng FR (given/when/then).

## Thay đổi hành vi hiện có

Implementation có trong `src/rkg` và `frontend/src`. Mock và live dùng cùng
contract shape. Revision 2 của view này nói Python/backend chưa có trong working
tree. Câu đó không còn đúng.

## NGOÀI phạm vi lần này

Production deploy (bước 19–21), đóng gate khi còn pending, và coi candidate
baseline là approved. `OQ-RKG-001` và `OQ-RKG-002` đã resolved.

## Ràng buộc mới

NFR tách rõ performance, security, reliability, accessibility và adapter extensibility. UI phải đạt WCAG AA
ở cả light/dark mode (`NFR-RKG-UX-001`, `TEST-RKG-WCAG-CONTRAST`). Pilot dùng ≥30 mẫu
import/call/DI và ≥10 mẫu DB/event/config/implements khi có đủ dữ liệu; nhóm không có
trong pilot ghi N/A và vẫn phải đạt fixture riêng.

## Gate và eval

Checklist Scope / Architecture / UI-UX / Contract nằm ở `policies/gates/`. Q&A rubric
nằm ở `EVAL-RKG-QA-001`. Vì goal/NFR/ADR/contract vừa đổi materially, Scope và
Architecture và UI/UX quay lại `pending` cho exact revisions hiện tại; approval của
baseline trước không tự động áp dụng. Contract vẫn pending cho bước 9+.

## Observability

`OBS-RKG-001`, `002`, `005` đo ba KPI active. KPI-RKG-003/004/006 đã retired;
latency/RAM và adapter extensibility tiếp tục được nghiệm thu qua NFR tương ứng,
không phải product KPI.

## Câu hỏi mở còn lại

- `OQ-RKG-006` (open): cung cấp signer identity hợp lệ. Chặn approval mới của
  Scope Gate và UI/UX Gate cho candidate baseline. Gate hiện tại vẫn pending.
  `approval-004` chỉ khóa revision cũ.

Resolved: `OQ-RKG-001`, `OQ-RKG-002`, `OQ-RKG-003`, `OQ-RKG-004`, `OQ-RKG-005`.

Revision 2 of this view listed `OQ-RKG-001` and `OQ-RKG-002` as open and described
the objective as pre-implementation. That text is historical.

## Documentation recovery

BL-CHG-RKG-2026-001 revision 3 pins the reconciled task records. Scope remains 001–029 plus bootstrap 000; no new task. REV-RKG-2026-004 records Git dates and recovery provenance; REV-RKG-2026-004 maps delivery/evidence. Steps 15–18 remain applicable. Current gate status and acceptance findings retain their factual state.
