---
key: CSV-CHG-RKG-2026-002-r8
type: change-set-view
group: derived
non_normative: true
hand_written: true
derived_from:
  - BL-CHG-RKG-2026-002-r8
---
> Khi bản này và file FR bất đồng, **FR thắng**.

# Chatbot dễ hỏi và trả lời tự nhiên

Bản này suy từ baseline hiện tại `BL-CHG-RKG-2026-002-r8`. File `CSV-CHG-RKG-2026-002.md` vẫn là view sinh từ r1 và không bị ghi đè.

## Mục tiêu

Cải thiện cách hỏi, câu trả lời và hướng dẫn khôi phục của chatbot, giữ câu trả lời kiểm chứng được bằng graph và citation. Change set thỏa `GOAL-RKG-003`. Phase hiện tại là `implementation_complete_UAT_pending`. Baseline r8 đã approved cho lát contract; UAT chưa có approval.

## Mục tiêu nghiệp vụ đổi

`PRD-RKG` trên baseline này là `reference_only`. GOAL và KPI không đổi trong r8.

## Tính năng mới

Không có FR mới. `FR-RKG-005` revision 9 là FR được chọn cho lát chatbot.

## Thay đổi hành vi hiện có

Hành vi hỏi đáp grounded của `FR-RKG-005`. AC cần `verified_against` khi UAT: `AC-RKG-024`, `AC-RKG-025`, `AC-RKG-041`, `AC-RKG-042`, `AC-RKG-047`, `AC-RKG-063`, `AC-RKG-028`, `AC-RKG-029`, `AC-RKG-030`, `AC-RKG-031`, `AC-RKG-032`, `AC-RKG-033`, `AC-RKG-044`, `AC-RKG-045`, `AC-RKG-046`, `AC-RKG-059`, `AC-RKG-064`, `AC-RKG-074`, `AC-RKG-075`, `AC-RKG-076`, `AC-RKG-077`, `AC-RKG-078`, `AC-RKG-079`, `AC-RKG-080`, `AC-RKG-081`.

Contract candidate trên cùng baseline: `API-RKG-CORE-v1`, `TBL-RKG-GRAPH`, `UIS-RKG-001`, `DDL-RKG-GRAPH`, `MIG-RKG-CHATBOT-v3`, `CON-RKG-CONVERSATION-v1`, `SCH-RKG-CONVERSATION-v1`, `OAS-RKG-CONVERSATION-v1`, `SCH-RKG-READ-PLAN-v2`, `SCH-RKG-NARRATIVE-v1`, `CHL-RKG-CONVERSATION-v1`.

## NGOÀI phạm vi lần này

Production deploy, ký Production Gate, và mọi FR ngoài `FR-RKG-005`. `approved_by` của UAT phải là người khác `accountable_role` của `FR-RKG-005` (`product-owner`). Không tạo approval trong lát này.

## Ràng buộc mới

Không có NFR mới trên các dòng `reference_only` của r8. Ràng buộc đã chọn vẫn là các NFR mà `FR-RKG-005` trỏ tới.

## Câu hỏi mở còn lại

Change set này không có file open question riêng. `OQ-RKG-006` vẫn mở trên `CHG-RKG-2026-001` và không được điền tên role thay cho signer.
