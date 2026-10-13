---
key: PLAN-TASK-RKG-030-r2
group: evidence
system: SYS-RKG
revision: 1
captured_at: '2026-10-06T16:27:40+07:00'
classification: internal
ai_assisted: true
type: implementation-plan
task_key: TASK-RKG-030
previous_plan: PLAN-TASK-RKG-030
stage: isolation_recovery_and_review_handoff
pre_code_plan: PLAN-TASK-RKG-030
---
# PLAN-TASK-RKG-030-r2 — Isolation recovery và review handoff

Kế hoạch bổ sung sau implementation; không thay thế hay giả lập thời điểm plan r1 đã viết trước code. Workflow B.15 yêu cầu worktree riêng.

1. Chuyển đúng mười file code/test thuộc TASK030 sang branch feat/chatbot-storage-v3, đối chiếu từng SHA-256. Kế thừa frozen normative sources từ baseline r8, không đổi revision/hash.
2. Khôi phục chỉ các file task đã sửa tại checkout chính bằng bytes Git HEAD đối chiếu pre-code context; chuyển các file mới đã hash-verify. Không đổi tài liệu người dùng hoặc evidence lịch sử.
3. Chạy lại suite backend synthetic trong worktree: unit/integration/conformance, bỏ hai live-provider modules và pilot corpus. Ruff/diff checks dùng cùng code tree.
4. Freeze manifest code/contract hashes cho reviewer. Author test results là validation, không phải independent review.
5. Review adversarial độc lập rồi Component Merge Gate; giữ task in_progress tới gate pass, không commit/merge/deploy hoặc mở DB người dùng trong handoff.
