---
uid:
key: NFR-RKG-REL-001
type: non-functional-requirement
group: normative
scope: system
system: SYS-RKG
status: draft
revision: 9
ownership:
  accountable_team: TEAM-RKG
  accountable_role: architect
relations:
  constrains: [FR-RKG-001, FR-RKG-002, FR-RKG-003, FR-RKG-004, FR-RKG-005]
classification: internal
ai_assisted: true
---

# NFR-RKG-REL-001 — Reliability and consistency

## Mô tả
Đảm bảo nhất quán snapshot, không mất dữ liệu hợp lệ khi lỗi, và an toàn concurrency
cho index job cũng như conversation turn.

## Yêu cầu (normative)

1. **Single writer index:** một index job tại một thời điểm trên toàn ứng dụng; request thứ hai nhận xung đột rõ (`409`).
2. **Repository ownership:** job/snapshot/conversation thuộc đúng một `repository_id`; mọi mutation và read phải kiểm tra ownership, không trộn hoặc cascade dữ liệu giữa repository.
3. **Atomic publish/activate:** candidate graph phải validate; publish snapshot mới hoặc activate snapshot cũ đổi active pointer của đúng repository trong transaction; failure rollback và giữ pointer cũ.
4. **Pinned reads:** mọi query/graph/Q&A gắn `snapshot_id`; không trộn snapshot trong một request.
5. **Immutable snapshots:** re-index luôn tạo snapshot mới; graph/source revision/manifest identity của snapshot đã publish không bị update tại chỗ.
6. **Delete/retention guards:** cleanup hoặc delete không xóa snapshot còn active, còn reader hoặc còn conversation reference; repository delete còn bị chặn bởi job chưa terminal và cascade chỉ dữ liệu con không được tham chiếu.
7. **Optimistic repository update:** PATCH repository yêu cầu `expected_revision`; conflict không áp dụng một phần mutation.
8. **Conversation concurrency:** một turn/conversation tại một thời điểm; `expected_revision` và `client_request_id` bắt buộc cho conflict/idempotency.
9. **Recovery:** pending turn sau restart chuyển `failed`/`interrupted`; không khóa conversation vĩnh viễn và không âm thầm mất history đã commit.
10. **History window:** context gửi provider tối đa 6 completed turns và 4.000 tokens; cắt turn cũ trước, giữ structured focus/pending state và công bố `context_turn_ids`/`history_truncated`.
11. **LLM turn defaults:** ứng dụng không áp trần số model calls, input tokens, output tokens, số graph query operations, tổng provider deadline hoặc số ký tự câu hỏi. Usage/call counters vẫn được ghi nhận; giới hạn của model/provider và lỗi transport vẫn được xử lý. Giữ history window ở mục10 và giới hạn context graph/semantic selection theo contract. Question vẫn phải là chuỗi không rỗng và được redaction trước khi lưu. Không giới hạn question qua byte bound của pending intent; state envelope ngoài question vẫn được bounded.
