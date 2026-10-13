---
key: CSV-CHG-RKG-2026-004
type: change-set-view
group: derived
non_normative: true
hand_written: true
derived_from:
  - BL-CHG-RKG-2026-004-r2
---
> Khi bản này và file FR bất đồng, **FR thắng**.

# Chọn provider OpenAI trực tiếp

## Mục tiêu

Thêm lựa chọn OpenAI cạnh OpenRouter, do server chọn, cùng ranh giới hội thoại grounded. Baseline hiện tại là `BL-CHG-RKG-2026-004-r2`. Gate vẫn pending.

## Mục tiêu nghiệp vụ đổi

Không đổi GOAL hay KPI. `FR-RKG-005` không đổi so với baseline trước.

## Tính năng mới

Không có FR mới. Story thỏa `AC-RKG-074` và `AC-RKG-080`.

## Thay đổi hành vi hiện có

`CMP-RKG-CONVERSATION` revision 10 và `CON-RKG-CONVERSATION-v1` revision 4, cả hai `changed_candidate_pending_gate`.

## NGOÀI phạm vi lần này

Fallback tự động và đổi contract giao diện. Approval gate trước không được chuyển sang.

## Ràng buộc mới

Không có NFR mới trong các dòng changed của baseline này.

## Câu hỏi mở còn lại

Không có open question trong thư mục change set này.
