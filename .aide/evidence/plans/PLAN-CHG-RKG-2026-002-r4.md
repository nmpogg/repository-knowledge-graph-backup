---
key: PLAN-CHG-RKG-2026-002-r4
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
revision: 1
captured_at: 2026-10-06
change_set: CHG-RKG-2026-002
stage: post-UIUX-L3-handoff
non_normative: true
implementation_ready: false
captured_against:
  baseline: BL-CHG-RKG-2026-002-r6
  scope_approval: approval-007
  architecture_approval: approval-009
  ui_ux_approval: approval-010
previous_plan: PLAN-CHG-RKG-2026-002-r3
classification: internal
ai_assisted: true
---
# PLAN-CHG-RKG-2026-002-r4 — Handoff L3 sau UI/UX approval

## Điều kiện và phạm vi

Scope, Architecture và UI/UX chatbot delta đã ký trong baseline r6. Contract
Gate vẫn pending. Đây là kế hoạch bước 9–10, không phải bằng chứng các contract
đã được sửa, migration đã chạy hoặc implementation đã sẵn sàng.

Giữ FR-RKG-005 r9/AC-RKG-074…081, ADR-2026-007 r2 và các section CMP/TM/UX đã
duyệt. Theo workflow reference B.10/B.11, chốt L3 và UI Spec cấp 4 trước Contract
Gate, sau đó mới decomposition và implementation. Không đổi thiết kế B thành
free-form factual output hoặc tăng model/query budgets.

## Công việc kế tiếp

1. Đọc API-RKG-CORE-v1 r15, TBL-RKG-GRAPH r12, UIS-RKG-001 r12 và implementation
   transport/conversation hiện tại; lập mapping từ AC74…81 tới contract/dữ liệu.
2. Chốt wire shape có validation cho narrative groups/paths, direct/indirect,
   language precedence, clarification intent, reason-specific insufficient và
   limitation/coverage sau reload. Private annotation trong preview không phải
   public schema để sao chép nguyên trạng.
3. Chốt citation identity/end-to-end evidence lookup đúng snapshot/evidence;
   nêu rõ unavailable/loading và legacy turns thiếu metadata. Giữ safe text,
   relative location, không source excerpts/host paths/transcripts trong evidence.
4. Đánh giá compatibility từ API/schema cũ bằng diff; khai rollout/migration và
   consumer acknowledgement phù hợp. TBL là semantic schema source; physical DDL
   phải khai TBL revision được implement và được thực thi/kiểm chứng trước khi ký
   Contract Gate. Không giả định mở rộng metadata tự động là non-breaking.
5. Cập nhật UIS cấp 4 từ UXF r5/SCR r9/UID r8 đã duyệt: response fields, source
   lookup, history limitation và recovery controls; giữ public state enum nếu
   current contracts cho phép. Không dùng fixture test làm integration evidence.
6. Freeze baseline contract mới, tạo review views/current-tree checks; thực hiện
   review và named Contract Gate decision theo policy. Thay đổi artifact đã ký
   phải đưa gate tương ứng về pending, không sửa approval/baseline lịch sử.
7. Sau prerequisite gates, tạo Epic/Story/Task và context packages có AC/FR/NFR
   traceability; không tái sử dụng task cũ đã done. Chỉ task implementation mới
   triển khai backend/frontend và runtime/evaluation checks.

## Handoff và verification

L3 artifacts/diff/migration/UIS và Contract approval chưa có cho delta này.
Browser preview checks và human walkthrough thuộc UI/UX; không chứng minh model
quality, graph grounding, resolver, server persistence, migration hoặc live API.
Không đánh dấu implementation task done hoặc release-ready từ approval UI/UX.
