---
uid:
key: UXF-RKG-002
type: ux-flow
group: normative
scope: system
system: SYS-RKG
status: draft
revision: 5
change_set: CHG-RKG-2026-002
ownership: {accountable_team: TEAM-RKG, accountable_role: design-owner}
relations: {satisfies: [FR-RKG-005]}
classification: internal
ai_assisted: true
---
# UXF-RKG-002 — Grounded conversation flow

## Mục tiêu và điều kiện

Cho phép hỏi đáp Việt/Anh nhiều lượt trên một repository/snapshot được pin, trong
khi citation và limitation luôn kiểm chứng được. Luồng chỉ bật khi LLM provider khả
dụng và snapshot còn đọc được; Explorer/search không phụ thuộc điều kiện này.

## Luồng chính

1. Người dùng tạo conversation trên active snapshot của repository hiện tại hoặc mở conversation cũ.
2. UI hiển thị pinned repository/snapshot/focus và gửi question với request ID/revision.
3. Pending state khóa submit trùng và cho biết provider đang xử lý.
4. Answer hiển thị claim/citation; click citation mở evidence panel.
5. `needs_clarification` hiển thị ordered candidates; người dùng chọn hoặc trả lời text.
6. Follow-up dùng focus/pending state; explicit entity mới thay focus.
7. Conflict cho reload/retry có chủ đích; provider error giữ state thành công trước đó.
8. Xóa conversation yêu cầu xác nhận, giải phóng snapshot reference và không xóa snapshot/history khác.

## Trạng thái response

| Status | Cách trình bày | Primary action |
|---|---|---|
| `answered` | Answer đã sanitize, claim/citation, limitation và dấu hiệu truncation | Mở citation hoặc hỏi tiếp |
| `needs_clarification` | Câu hỏi gốc + ordered candidate có type/qualified name | Chọn candidate hoặc trả lời text |
| `insufficient_evidence` | Nêu phần thiếu, không dùng empty answer như lỗi kỹ thuật | Mở Explorer hoặc hỏi lại hẹp hơn |
| `failed`/provider error | Giữ history đã commit và focus trước đó | Retry bằng request ID mới |
| `conflict` | Không ghi đè draft; công bố revision server | Reload conversation rồi review/retry |
| `disabled` | Giải thích provider chưa cấu hình | Dùng Search/Explorer |

## Recovery và consistency

- `409 conversation_conflict`: reload turns/revision; giữ draft ngoài transcript để
  người dùng quyết định gửi lại.
- `409 conversation_busy`: vô hiệu delete/submit trùng và tiếp tục theo dõi turn hiện tại.
- `410 snapshot_unavailable`: transcript vẫn đọc được, citation đánh dấu unavailable;
  không tự chuyển sang active snapshot mới.
- `502/503/504`: phân biệt provider error, disabled và timeout; không giả lập streaming.
- Khi `history_truncated=true` hoặc `retrieval_truncated=true`, hiển thị limitation gần
  answer, không chỉ trong metadata ẩn.
- Không ghi question/answer, session token, credential hay chain-of-thought vào log UI.

## Tiêu chí thoát

Success khi answer/clarification thuộc đúng pinned snapshot, citation mở được evidence
và follow-up dùng revision mới. Xóa conversation chỉ success sau confirm và khi không
có turn pending.

## Conversation usability — selected content for CHG-RKG-2026-002

Revision 5 describes the chosen experience for FR-RKG-005 AC-RKG-074…081.
It remains draft until UI/UX review of exact revisions. No new status enum or route
is introduced by this level-1 flow; field binding is deferred to L3/UIS.

1. Ready empty conversation shows a brief explanation and example categories:
   endpoint calls, table reads/writes and events. User may type a greeting; response
   gives guidance without graph claims. Provider-off remains visibly disabled.
2. User names method/path, endpoint or handler using familiar text. Keep repository,
   snapshot and resolved subject visible. Ambiguous names show explicit choices
   with endpoint/handler/service metadata and a reason for asking.
3. Selecting a choice resumes the original question. The transcript may record the
   selection, but the answer makes the selected subject and intent clear.
4. Answer starts with a full sentence, then direct relations; indirect paths are
   introduced separately only when supported and relevant. Names are shortened
   only if unambiguous; qualified names are available in details.
5. Show one main answer and source buttons labeled by their relative location or
   readable source ordinal. Verification claims belong in collapsed details,
   avoiding a duplicate Claims paragraph. Source opens exact evidence of that claim.
6. Insufficient data explains the observed stage: unmatched name, no supported
   relation, or incomplete context. Offer a concrete next step without claiming
   absent graph means absent runtime behavior.
7. Partial/history limits appear in plain language near answer, not just hidden
   metadata. On reload retain the stored indication; old turns without metadata
   show that coverage information was not recorded.
8. Error/conflict keeps draft and previously committed focus. Conversation deletion
   follows the existing confirmation and pending guards. No simulated streaming.

| Region/state | Primary copy/action |
|---|---|
| Greeting/empty | Explain what can be asked; focus the question composer |
| Clarification | Explain ambiguity; select one named option explicitly |
| Answered | Read explanation; open sources or ask a follow-up |
| Insufficient, no match | Suggest method/path or a more specific name |
| Insufficient, no supported relation | Explain what the current snapshot cannot establish; open Explorer |
| Partial | State result may be incomplete; suggest a narrower question |
| Provider error/disabled | Explain service problem; retry or open Explorer |
| Historical coverage unknown | State limitation metadata was not recorded; do not claim complete coverage |

Content examples for a UI mock must be synthetic and not taken from transcripts,
real source, secret/config or host paths. Every source label must be nonempty.
Language content follows AC-RKG-074; controls follow interface locale. Accessibility
uses native buttons/details, visible focus, ordered choices and dialog focus restore.
