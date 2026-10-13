---
key: PROMPT-TASK-RKG-030-REVIEW
type: reviewer-prompt
group: derived
revision: 1
non_normative: true
task: TASK-RKG-030
classification: internal
ai_assisted: true
---
# PROMPT-TASK-RKG-030-REVIEW — Independent adversarial storage code review

Bạn là reviewer độc lập, không phải tác giả hoặc người ký merge gate. Tìm worktree của branch feat/chatbot-storage-v3 bằng git worktree list và review ở worktree đó. Không review code checkout chính: code candidate chưa merge.

Đọc .aide/reviewer/packages/RVP-TASK-RKG-030-r1.yaml; tự kiểm chứng baseline SHA-256, 36 normative source pins và tất cả candidate code/test hashes trước review. Mismatch thì báo stale và dừng kết luận. So sánh code với Git base_commit trong manifest. Read-only normative sources thắng. Đọc TASK030 scope và FR005 AC077/080, TBL13/DDL13/MIG1/API16/public schema, CMP Conversation/Graph, CON v1 và NFR SEC/REL; các AC này chỉ có storage contribution ở task này.

Không đọc author plans, context, diaries, test evidence hay approval records để hình thành kết luận. Không coi việc chạy lại test tác giả là review độc lập. Tự dựng fixture nếu cần, chỉ disposable Kuzu 0.11.3 DB; không operator DB/.env/provider thật/analyzed-source execution. Không đổi code/spec/task/gate và không tự ký thay người.

Kiểm tra Security/Operability/Completeness: version0/1→2→3, precondition partial-shape refusal/no-op stamp preservation, ALTER/version rollback và legacy pin/evidence/state/hash retention; schema cùng semantic coverage/status/bounds validation; redaction không salvage unknown fields; future metadata unknown/no backfill; terminal turn+metadata+state transaction, replay/recovery/conflict; preserve/replace/clear intent/order và provider mutation isolation. Phân biệt implementation gap của TASK031–035 với bad_code trong TASK030.

Finding có stable ID, severity/perspective, bad_code hoặc bad_spec, source path/hash/line, trigger/impact/minimum fix. Kết luận ready_for_component_merge_decision hoặc needs_revision, checks passed/failed/not_run. Tạo review record mới dưới .aide/evidence/reviews/, append-only, captured_against manifest hash/baseline/code pins. Không đóng gate hoặc sửa lịch sử. Record chỉ IDs/hashes/counts và kết luận, không transcript/source/absolute host paths.
