---
uid:
key: FR-RKG-005
type: functional-requirement
group: normative
scope: system
system: SYS-RKG
status: approved
revision: 9
change_set: CHG-RKG-2026-002
ownership:
  accountable_team: TEAM-RKG
  accountable_role: product-owner
relations:
  satisfies: [GOAL-RKG-003]
  constrained_by: [NFR-RKG-SEC-001, NFR-RKG-REL-001, NFR-RKG-UX-001]
classification: internal
ai_assisted: true
---

# FR-RKG-005 — Grounded Q&A nhiều lượt

## Mô tả

Khi provider được bật, hệ thống trả lời Việt/Anh dựa trên bounded graph context, citation và snapshot đã pin; đồng thời quản lý conversation, history window, focus và clarification. Provider có thể tắt hoặc lỗi mà không ảnh hưởng search/graph. LLM không ghi graph fact, không chạy source và không được vượt query/tool allowlist.

Revision 8 chốt nội dung yêu cầu cho `CHG-RKG-2026-002`: câu trả lời dễ đọc,
xác định endpoint bằng thông tin người dùng biết, clarification có hướng dẫn,
citation chính xác và giới hạn dữ liệu rõ ràng. Revision 9 ghi Scope approval
`approval-007` của PhongNM, đại diện Product Owner, Tech Lead và QA Lead.
AC không đổi so với revision 8; thay đổi revision này chỉ ghi trạng thái approval.
Approval áp dụng phạm vi chatbot của CHG-RKG-2026-002, không nghiệm thu runtime,
không đóng Architecture/UIUX/Contract Gate hoặc ký lại toàn bộ RKG MVP.

Câu trả lời dùng ngôn ngữ tự nhiên nhưng chỉ giải thích điều graph có bằng chứng.
Phát hiện tĩnh không chứng minh đầy đủ hành vi runtime; tên hàm không chứng minh
nghiệp vụ, tác dụng phụ, giá trị trả về hoặc cách triển khai của hàm.

## Acceptance Criteria

### Grounded answer

#### AC-RKG-024
- **given** bộ câu hỏi Việt/Anh answerable trên fixture (DB/event/dependency/technology)
- **when** hỏi với LLM đã cấu hình
- **then** answer đúng entity/path/direction theo rubric; mọi claim quan hệ có citation thuộc snapshot/context và không có claim trái graph
- `constrained_by:` [NFR-RKG-SEC-001]
- `implementation_target:` [CMP-RKG-CONVERSATION, CMP-RKG-GRAPH]
- `validated_by:` [TEST-RKG-QA-EVAL]

#### AC-RKG-025
- **given** ambiguity, detected-only, budget truncation, unknown question, provider disabled/timeout/malformed
- **when** hỏi
- **then** clarification hoặc báo thiếu dữ liệu/lỗi (`needs_clarification` / `insufficient_evidence` / mã llm_*); không bịa fact; search vẫn hoạt động khi LLM lỗi
- `constrained_by:` [NFR-RKG-SEC-001, NFR-RKG-REL-001]
- `implementation_target:` [CMP-RKG-CONVERSATION]
- `validated_by:` [TEST-RKG-QA-NEGATIVE]

#### AC-RKG-041
- **given** mutation hoặc Q&A request thiếu/sai `X-RKG-Session`, Origin hoặc Host ngoài allowlist
- **when** gọi API
- **then** request nhận `401` trước khi thay đổi state hoặc gọi provider; LLM credential/provider secret không xuất hiện trong browser payload, graph, error hoặc log
- `constrained_by:` [NFR-RKG-SEC-001]
- `implementation_target:` [CMP-RKG-TRANSPORT, CMP-RKG-CONVERSATION]
- `validated_by:` [TEST-RKG-LOCAL-SESSION]

#### AC-RKG-042
- **given** question hoặc retrieved repository/model text chứa prompt injection yêu cầu shell, network, code execution hay query ngoài allowlist
- **when** xử lý Q&A
- **then** chỉ plan hợp lệ theo schema và read-only query allowlist được chạy; injection không tạo graph fact, side effect hoặc citation ngoài context/snapshot
- `constrained_by:` [NFR-RKG-SEC-001]
- `implementation_target:` [CMP-RKG-CONVERSATION]
- `validated_by:` [TEST-RKG-QA-INJECTION]

#### AC-RKG-047
- **given** fixture từ local path được index thành công và provider eval được cấu hình
- **when** người dùng tạo conversation, hỏi về graph vừa index và mở citation
- **then** answer/citation dùng đúng snapshot/relative evidence của local fixture; không dùng mock graph hoặc snapshot khác
- `constrained_by:` [NFR-RKG-REL-001, NFR-RKG-SEC-001]
- `implementation_target:` [CMP-RKG-CONVERSATION, CMP-RKG-GRAPH, CMP-RKG-TRANSPORT, CMP-RKG-WEB]
- `validated_by:` [TEST-RKG-LOCAL-QA-E2E]

#### AC-RKG-063
- **given** question vượt giới hạn, provider chậm hoặc planner yêu cầu quá ngân sách model/query
- **when** submit turn
- **then** question quá dài nhận `422` trước provider call; mỗi turn không vượt giới hạn query/model-call/output-token và timeout ở NFR-RKG-REL-001; timeout trả mã `llm_timeout`/`504` mà không đổi focus đã commit
- `constrained_by:` [NFR-RKG-REL-001]
- `implementation_target:` [CMP-RKG-CONVERSATION, CMP-RKG-TRANSPORT]
- `validated_by:` [TEST-RKG-LLM-LIMITS]

### Conversation continuity

#### AC-RKG-028
- **given** câu đầu đã resolve một API
- **when** hỏi tiếp tham chiếu API đó về bảng ghi và event publish
- **then** resolve đúng focus/path/citation mà không cần nhập lại context
- `constrained_by:` [NFR-RKG-REL-001]
- `implementation_target:` [CMP-RKG-CONVERSATION]
- `validated_by:` [TEST-RKG-FOLLOWUP]

#### AC-RKG-029
- **given** nhiều candidate hoặc người dùng nhắc explicit entity mới
- **when** follow-up chọn candidate theo thứ tự hoặc đổi chủ đề
- **then** chọn đúng ordered candidate của pending clarification; entity mới thay focus; ambiguity thực sự yêu cầu clarification
- `implementation_target:` [CMP-RKG-CONVERSATION]
- `validated_by:` [TEST-RKG-CLARIFY]

#### AC-RKG-030
- **given** reload/restart dịch vụ và hai conversation
- **when** mở lại, hỏi tiếp hoặc xóa một conversation
- **then** history bền vững trong Kùzu; focus cách ly; xóa một phiên không ảnh hưởng phiên khác
- `constrained_by:` [NFR-RKG-REL-001, NFR-RKG-SEC-001]
- `implementation_target:` [CMP-RKG-CONVERSATION, CMP-RKG-GRAPH]
- `validated_by:` [TEST-RKG-HISTORY-PERSIST]

#### AC-RKG-031
- **given** snapshot mới được publish trong khi conversation cũ đang mở
- **when** hỏi tiếp trong conversation cũ
- **then** vẫn query repository/snapshot pinned; citation còn dùng được; conversation mới trên repository đó dùng active snapshot mới
- `constrained_by:` [NFR-RKG-REL-001]
- `implementation_target:` [CMP-RKG-CONVERSATION, CMP-RKG-GRAPH]
- `validated_by:` [TEST-RKG-SNAPSHOT-PIN]

#### AC-RKG-032
- **given** conversation vượt history window budget được định nghĩa ở NFR-RKG-REL-001
- **when** hỏi tiếp
- **then** bỏ turn cũ trước, giữ structured state/pending; trả đúng `context_turn_ids` và `history_truncated`; chi tiết ngoài window/state cần clarification
- `implementation_target:` [CMP-RKG-CONVERSATION]
- `constrained_by:` [NFR-RKG-REL-001]
- `validated_by:` [TEST-RKG-HISTORY-WINDOW]

#### AC-RKG-033
- **given** hai tab concurrent, retry cùng `client_request_id`, hoặc restart khi turn pending
- **when** submit turn
- **then** revision/idempotency phát hiện conflict, không duplicate; pending được recovery thành failed/interrupted; provider failure không đổi focus trước đó
- `constrained_by:` [NFR-RKG-REL-001]
- `implementation_target:` [CMP-RKG-CONVERSATION]
- `validated_by:` [TEST-RKG-TURN-GUARD]

#### AC-RKG-044
- **given** snapshot đang active, có reader hoặc còn conversation reference và một snapshot pinned bị xóa/hỏng ngoài ứng dụng
- **when** chạy cleanup rồi đọc conversation tương ứng
- **then** cleanup không xóa snapshot còn guard; trường hợp snapshot đã mất trả `410 snapshot_unavailable`, không âm thầm chuyển conversation sang active snapshot khác
- `constrained_by:` [NFR-RKG-REL-001]
- `implementation_target:` [CMP-RKG-CONVERSATION, CMP-RKG-GRAPH, CMP-RKG-TRANSPORT]
- `validated_by:` [TEST-RKG-SNAPSHOT-RETENTION]

#### AC-RKG-045
- **given** conversation có turn `pending`
- **when** người dùng yêu cầu xóa conversation
- **then** API trả `409 conversation_busy`; sau khi turn kết thúc hoặc recovery, xóa conversation được phép và không xóa snapshot/history của conversation khác
- `constrained_by:` [NFR-RKG-REL-001]
- `implementation_target:` [CMP-RKG-CONVERSATION, CMP-RKG-TRANSPORT]
- `validated_by:` [TEST-RKG-CONVERSATION-DELETE-GUARD]

#### AC-RKG-046
- **given** answer/candidate/error chứa Markdown hoặc text từ repository/model
- **when** người dùng thao tác conversation bằng keyboard
- **then** nội dung được escape/sanitize, candidate/citation/confirm dialog có accessible name và focus order, error/status được announce, đóng dialog trả focus về control kích hoạt
- `constrained_by:` [NFR-RKG-UX-001, NFR-RKG-SEC-001]
- `implementation_target:` [CMP-RKG-WEB]
- `validated_by:` [TEST-RKG-CONVERSATION-A11Y]

#### AC-RKG-059
- **given** turn request thiếu/sai `expected_revision` hoặc `client_request_id`
- **when** submit turn
- **then** API trả `422` và không tạo `Turn`, không gọi provider, không đổi conversation revision/focus
- `constrained_by:` [NFR-RKG-REL-001]
- `implementation_target:` [CMP-RKG-CONVERSATION, CMP-RKG-TRANSPORT]
- `validated_by:` [TEST-RKG-TURN-REQUIRED-FIELDS]

#### AC-RKG-064
- **given** question/answer chứa credential, secret/config value, raw source, provider chain-of-thought hoặc Markdown không tin cậy
- **when** persist conversation và ghi operational log
- **then** conversation chỉ lưu nội dung đã redact/sanitize theo glossary; dữ liệu cấm không xuất hiện trong graph/store/log và operational log không chứa question/answer transcript
- `constrained_by:` [NFR-RKG-SEC-001]
- `implementation_target:` [CMP-RKG-CONVERSATION, CMP-RKG-GRAPH, CMP-RKG-TRANSPORT]
- `validated_by:` [TEST-RKG-CONVERSATION-REDACTION]

### Conversational usability

#### AC-RKG-074
- **given** câu hỏi Việt có dấu, Việt không dấu hoặc tiếng Anh và ngôn ngữ giao diện Việt/Anh
- **when** chatbot trả lời, yêu cầu làm rõ hoặc báo thiếu dữ liệu
- **then** câu Việt có dấu hoặc có dấu hiệu Việt không dấu rõ được trả lời bằng tiếng Việt, câu Anh rõ được trả lời bằng tiếng Anh; câu không đủ dấu hiệu ngôn ngữ dùng ngôn ngữ giao diện, client cũ không gửi locale dùng tiếng Việt; identifier giữ nguyên và không bị dịch
- `constrained_by:` [NFR-RKG-UX-001, NFR-RKG-REL-001]
- `implementation_target:` [CMP-RKG-CONVERSATION, CMP-RKG-TRANSPORT, CMP-RKG-WEB]
- `validated_by:` [TEST-RKG-CONVERSATIONAL-QA]

#### AC-RKG-075
- **given** snapshot có endpoint và handler với bằng chứng, và câu hỏi nêu HTTP method/path, một path, tên endpoint hoặc tên handler
- **when** người dùng hỏi quan hệ của đối tượng đó
- **then** method/path đầy đủ xác định đúng endpoint, path hoặc tên không duy nhất yêu cầu chọn có mô tả; endpoint intent ưu tiên loại Endpoint và không tự đổi sang Callable cùng tên; người dùng không phải biết qualified name mới có thể hỏi
- `constrained_by:` [NFR-RKG-REL-001, NFR-RKG-SEC-001]
- `implementation_target:` [CMP-RKG-CONVERSATION, CMP-RKG-GRAPH]
- `validated_by:` [TEST-RKG-CONVERSATIONAL-QA]

#### AC-RKG-076
- **given** graph có Endpoint → handler và các quan hệ gọi hàm nhiều bước có bằng chứng
- **when** hỏi endpoint/handler gọi những hàm nào
- **then** câu trả lời xác định rõ endpoint và handler nếu có, nêu lời gọi trực tiếp từ handler/root trước, ghi riêng lời gọi gián tiếp theo đường đi đã kiểm tra; không gọi handler là callee của Endpoint, không trộn caller với callee, không suy diễn nghiệp vụ từ tên, và không nói danh sách đầy đủ khi context bị cắt
- `constrained_by:` [NFR-RKG-SEC-001, NFR-RKG-REL-001]
- `implementation_target:` [CMP-RKG-CONVERSATION, CMP-RKG-GRAPH]
- `validated_by:` [TEST-RKG-CONVERSATIONAL-QA, TEST-RKG-QA-EVAL]

#### AC-RKG-077
- **given** một câu hỏi chưa phân biệt được nhiều thực thể và đã tạo danh sách làm rõ có thứ tự
- **when** người dùng chọn bằng nút hoặc số thứ tự
- **then** danh sách giải thích vì sao cần chọn, có loại đối tượng và metadata phân biệt an toàn; lượt chọn tiếp tục trả lời ý định/câu hỏi gốc, không biến số thứ tự thành câu hỏi nghiệp vụ mới, và không âm thầm chọn mục mặc định
- `constrained_by:` [NFR-RKG-UX-001, NFR-RKG-REL-001]
- `implementation_target:` [CMP-RKG-CONVERSATION, CMP-RKG-WEB]
- `validated_by:` [TEST-RKG-CONVERSATIONAL-QA, TEST-RKG-CONVERSATIONAL-UI]

#### AC-RKG-078
- **given** hội thoại trên snapshot khả dụng, provider được bật và lượt nhập chỉ là lời chào Việt/Anh
- **when** người dùng gửi lời chào
- **then** chatbot trả lời ngắn bằng ngôn ngữ hiệu lực và hướng dẫn hỏi về endpoint/hàm/quan hệ; không dùng thông báo thiếu bằng chứng cho lời chào, không tạo claim/citation, không đổi focus hoặc lựa chọn đang chờ; lời chào không tạo graph query hoặc model call
- `constrained_by:` [NFR-RKG-SEC-001, NFR-RKG-REL-001]
- `implementation_target:` [CMP-RKG-CONVERSATION, CMP-RKG-WEB]
- `validated_by:` [TEST-RKG-CONVERSATIONAL-QA]

#### AC-RKG-079
- **given** không tìm được thực thể, không có quan hệ có bằng chứng để trả lời hoặc context bị cắt
- **when** chatbot trả kết quả thiếu dữ liệu hoặc kết quả một phần
- **then** giải thích theo điều hệ thống thực sự quan sát được, có hướng dẫn phù hợp để chọn/nhập đối tượng rõ hơn hoặc mở Explorer; không khẳng định đối tượng/quan hệ không tồn tại chỉ vì graph thiếu; provider error/disabled/timeout vẫn là lỗi riêng
- `constrained_by:` [NFR-RKG-SEC-001, NFR-RKG-UX-001]
- `implementation_target:` [CMP-RKG-CONVERSATION, CMP-RKG-WEB]
- `validated_by:` [TEST-RKG-CONVERSATIONAL-QA, TEST-RKG-CONVERSATIONAL-UI]

#### AC-RKG-080
- **given** answer, claims, citation và thông tin giới hạn của một lượt đã lưu
- **when** xem kết quả ngay sau submit hoặc mở lại hội thoại
- **then** có một câu trả lời chính dễ đọc, không hiển thị lại cùng nội dung trong khối Claims mặc định, không lặp thông báo insufficient; chi tiết quan hệ vẫn mở được, cảnh báo history/retrieval một phần hiển thị bằng ngôn ngữ người dùng và không mất sau reload; lượt cũ thiếu metadata không bị giả định là đầy đủ
- `constrained_by:` [NFR-RKG-UX-001, NFR-RKG-REL-001]
- `implementation_target:` [CMP-RKG-CONVERSATION, CMP-RKG-GRAPH, CMP-RKG-TRANSPORT, CMP-RKG-WEB]
- `validated_by:` [TEST-RKG-CONVERSATIONAL-UI, TEST-RKG-CONVERSATIONAL-QA]

#### AC-RKG-081
- **given** mỗi phát biểu quan hệ có citation của đúng snapshot/context
- **when** người dùng mở citation bằng chuột hoặc bàn phím
- **then** nhãn nguồn dễ nhận biết, evidence mở ra khớp evidence ID của phát biểu; chỉ hiện relative path và line khi provenance cho phép; không thay bằng evidence khác của entity đích, không hiện citation button rỗng, raw source hay absolute host path; evidence không còn dùng được có thông báo rõ
- `constrained_by:` [NFR-RKG-SEC-001, NFR-RKG-UX-001, NFR-RKG-REL-001]
- `implementation_target:` [CMP-RKG-CONVERSATION, CMP-RKG-GRAPH, CMP-RKG-TRANSPORT, CMP-RKG-WEB]
- `validated_by:` [TEST-RKG-CONVERSATIONAL-UI, TEST-RKG-CONVERSATIONAL-QA]
