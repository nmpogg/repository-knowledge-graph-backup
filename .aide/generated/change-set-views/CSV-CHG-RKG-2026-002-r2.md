---
{
  "key": "CSV-CHG-RKG-2026-002-r2",
  "type": "change-set-view",
  "group": "derived",
  "revision": 1,
  "non_normative": true,
  "hand_written": false,
  "derived_from": [
    "BL-CHG-RKG-2026-002-r2"
  ],
  "generator": "tools/render_chatbot_review.py",
  "generator_sha256": "de028fa02b3f1c0d7bec4c32af84e968056db54ce28a8e01ee9916b4ba6cb65d",
  "source_hashes": {
    "FR-RKG-005": "6f240da74dd108933c85da36bf973106c30b7a6825f2e3b57e67318fa22a78f5",
    "ADR-2026-007": "c699b29aa4c36c4be71c40b9f179731213f2f53e77d811a06e9307a2be68144c",
    "CMP-RKG-CONVERSATION": "2b2bc1bb8c3cc17cc2349d5c3be07b828efd89cbc24660cfba2c44635adffa65",
    "CMP-RKG-WEB": "9127465096842ccdf6addff5649a13839515f088a136d2bdcbbb3e5ccb5b91e6",
    "TM-RKG": "c22e337412e5c9d42bccbc5cf5ef76e92767ee130f3b4d8a9de86ea6d6570bb6",
    "UXF-RKG-002": "5e57d4c6d118e1463a96373740105d61371514de12f2f1aa17a303206d8e3add",
    "SCR-RKG-001": "385e3bd7ddb7ff32397580270005574cb6cce2ae47e392e7b137c9a4520876c3",
    "UID-RKG-001": "b5b92b6652c087cadaa0a347de226f9bf72fc2f5ad36eff617e9452b4e3dbc7e",
    "GATE-RKG-SCOPE": "bf7f2fb25f44a09f6ce42a3f937a5e125abe4cf184789b0eb9e9e5f304a2ed17",
    "GATE-RKG-ARCHITECTURE": "28b9cefd31d2573bee4b5be4a8a23c9e649e458ee97605f96972dd53b6d60826",
    "GATE-RKG-UIUX": "9738d79480c08191b7043a58e50001d3bc0e1e7f501631250a9ddab52be86a34",
    "PRD-RKG": "6406762c3f72ed86601b16711a105408be90b72389891e66dd4642b4ecbc25cc",
    "DOM-RKG-CORE": "24759954cd15951c3c6fc441d0ba0b88d831f62f86ee1e5b1c15db74318d2ff3",
    "CAP-RKG-003": "a83f81a79c97a82bb302f0db2a28ade53e32299b390d45a2318ae33839c57c93",
    "CMP-RKG-GRAPH": "7792b51117fd0d302a1e1d485e06f68f01266a151fe3bf94220ddddb17c6cbb2",
    "CMP-RKG-TRANSPORT": "6d89ca2098b2335b8455b3dad6c2b0a214079e55cd92e13d5cbf0de13e6df286",
    "ADR-2026-001": "ee392713079ebeb4904445a033ce7b5bdfd417a85cfc20e4bac8bde23442c10d",
    "ADR-2026-004": "43ade7152dac2960329b8dd0a196649e91a317c125133a53e7e26164d5f4e3e3",
    "NFR-RKG-SEC-001": "ea54ad8b488bc6bcc862ed0316dc8e6a46a58ad63119b9cadf3d24853d8135aa",
    "NFR-RKG-REL-001": "fd6742188c96da8e9859bbd15ff68715c792e57d6eaf6368d34e3d34dd902b0b",
    "NFR-RKG-UX-001": "c73044ee84ad7fda785daf4ad9818e128d5cf33e02005b00f8019668f09be4e3",
    "API-RKG-CORE-v1": "e0f482a8c98a88898aa7abae2d42e1c00cb82b0e393627447dd7f08fd03d8ce2",
    "TBL-RKG-GRAPH": "8f89df7b938dec9947a06f49fb307432b9182853ca5e4bfdcad1994a50d13bcf",
    "UIS-RKG-001": "2e66ba300e0b4e1e9fb55ccb0a1f7d376967603ad673e3bc1df339e563e7749b",
    "EVAL-RKG-QA-001": "19bba2089b095b0b431d85d843a61a3d5a4488889c269d47439869f11b673720",
    "OBS-RKG-005": "82acb6483ca288e1952b5f7f354158243ea07ea45cf090a62392787e3c92ef3f",
    "TOK-RKG-001": "ae71b14d8921b6e64f03641a5787c7b99622fa3f28904a75208eabfb32c8de96"
  }
}
---

# CSV-CHG-RKG-2026-002-r2 — Chatbot dễ hỏi và trả lời tự nhiên

> Khi view và artifact normative bất đồng, **artifact normative thắng**.

> Candidate cho review; không phải approval hoặc bằng chứng triển khai.

## Mục tiêu


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

## Mục tiêu nghiệp vụ đổi

GOAL/KPI không đổi; mở rộng trải nghiệm grounded conversation hiện có.

## Tính năng mới

### AC-RKG-074
- **given** câu hỏi Việt có dấu, Việt không dấu hoặc tiếng Anh và ngôn ngữ giao diện Việt/Anh
- **when** chatbot trả lời, yêu cầu làm rõ hoặc báo thiếu dữ liệu
- **then** câu Việt có dấu hoặc có dấu hiệu Việt không dấu rõ được trả lời bằng tiếng Việt, câu Anh rõ được trả lời bằng tiếng Anh; câu không đủ dấu hiệu ngôn ngữ dùng ngôn ngữ giao diện, client cũ không gửi locale dùng tiếng Việt; identifier giữ nguyên và không bị dịch
- `constrained_by:` [NFR-RKG-UX-001, NFR-RKG-REL-001]
- `implementation_target:` [CMP-RKG-CONVERSATION, CMP-RKG-TRANSPORT, CMP-RKG-WEB]
- `validated_by:` [TEST-RKG-CONVERSATIONAL-QA]


### AC-RKG-075
- **given** snapshot có endpoint và handler với bằng chứng, và câu hỏi nêu HTTP method/path, một path, tên endpoint hoặc tên handler
- **when** người dùng hỏi quan hệ của đối tượng đó
- **then** method/path đầy đủ xác định đúng endpoint, path hoặc tên không duy nhất yêu cầu chọn có mô tả; endpoint intent ưu tiên loại Endpoint và không tự đổi sang Callable cùng tên; người dùng không phải biết qualified name mới có thể hỏi
- `constrained_by:` [NFR-RKG-REL-001, NFR-RKG-SEC-001]
- `implementation_target:` [CMP-RKG-CONVERSATION, CMP-RKG-GRAPH]
- `validated_by:` [TEST-RKG-CONVERSATIONAL-QA]


### AC-RKG-076
- **given** graph có Endpoint → handler và các quan hệ gọi hàm nhiều bước có bằng chứng
- **when** hỏi endpoint/handler gọi những hàm nào
- **then** câu trả lời xác định rõ endpoint và handler nếu có, nêu lời gọi trực tiếp từ handler/root trước, ghi riêng lời gọi gián tiếp theo đường đi đã kiểm tra; không gọi handler là callee của Endpoint, không trộn caller với callee, không suy diễn nghiệp vụ từ tên, và không nói danh sách đầy đủ khi context bị cắt
- `constrained_by:` [NFR-RKG-SEC-001, NFR-RKG-REL-001]
- `implementation_target:` [CMP-RKG-CONVERSATION, CMP-RKG-GRAPH]
- `validated_by:` [TEST-RKG-CONVERSATIONAL-QA, TEST-RKG-QA-EVAL]


### AC-RKG-077
- **given** một câu hỏi chưa phân biệt được nhiều thực thể và đã tạo danh sách làm rõ có thứ tự
- **when** người dùng chọn bằng nút hoặc số thứ tự
- **then** danh sách giải thích vì sao cần chọn, có loại đối tượng và metadata phân biệt an toàn; lượt chọn tiếp tục trả lời ý định/câu hỏi gốc, không biến số thứ tự thành câu hỏi nghiệp vụ mới, và không âm thầm chọn mục mặc định
- `constrained_by:` [NFR-RKG-UX-001, NFR-RKG-REL-001]
- `implementation_target:` [CMP-RKG-CONVERSATION, CMP-RKG-WEB]
- `validated_by:` [TEST-RKG-CONVERSATIONAL-QA, TEST-RKG-CONVERSATIONAL-UI]


### AC-RKG-078
- **given** hội thoại trên snapshot khả dụng, provider được bật và lượt nhập chỉ là lời chào Việt/Anh
- **when** người dùng gửi lời chào
- **then** chatbot trả lời ngắn bằng ngôn ngữ hiệu lực và hướng dẫn hỏi về endpoint/hàm/quan hệ; không dùng thông báo thiếu bằng chứng cho lời chào, không tạo claim/citation, không đổi focus hoặc lựa chọn đang chờ; lời chào không tạo graph query hoặc model call
- `constrained_by:` [NFR-RKG-SEC-001, NFR-RKG-REL-001]
- `implementation_target:` [CMP-RKG-CONVERSATION, CMP-RKG-WEB]
- `validated_by:` [TEST-RKG-CONVERSATIONAL-QA]


### AC-RKG-079
- **given** không tìm được thực thể, không có quan hệ có bằng chứng để trả lời hoặc context bị cắt
- **when** chatbot trả kết quả thiếu dữ liệu hoặc kết quả một phần
- **then** giải thích theo điều hệ thống thực sự quan sát được, có hướng dẫn phù hợp để chọn/nhập đối tượng rõ hơn hoặc mở Explorer; không khẳng định đối tượng/quan hệ không tồn tại chỉ vì graph thiếu; provider error/disabled/timeout vẫn là lỗi riêng
- `constrained_by:` [NFR-RKG-SEC-001, NFR-RKG-UX-001]
- `implementation_target:` [CMP-RKG-CONVERSATION, CMP-RKG-WEB]
- `validated_by:` [TEST-RKG-CONVERSATIONAL-QA, TEST-RKG-CONVERSATIONAL-UI]


### AC-RKG-080
- **given** answer, claims, citation và thông tin giới hạn của một lượt đã lưu
- **when** xem kết quả ngay sau submit hoặc mở lại hội thoại
- **then** có một câu trả lời chính dễ đọc, không hiển thị lại cùng nội dung trong khối Claims mặc định, không lặp thông báo insufficient; chi tiết quan hệ vẫn mở được, cảnh báo history/retrieval một phần hiển thị bằng ngôn ngữ người dùng và không mất sau reload; lượt cũ thiếu metadata không bị giả định là đầy đủ
- `constrained_by:` [NFR-RKG-UX-001, NFR-RKG-REL-001]
- `implementation_target:` [CMP-RKG-CONVERSATION, CMP-RKG-GRAPH, CMP-RKG-TRANSPORT, CMP-RKG-WEB]
- `validated_by:` [TEST-RKG-CONVERSATIONAL-UI, TEST-RKG-CONVERSATIONAL-QA]


### AC-RKG-081
- **given** mỗi phát biểu quan hệ có citation của đúng snapshot/context
- **when** người dùng mở citation bằng chuột hoặc bàn phím
- **then** nhãn nguồn dễ nhận biết, evidence mở ra khớp evidence ID của phát biểu; chỉ hiện relative path và line khi provenance cho phép; không thay bằng evidence khác của entity đích, không hiện citation button rỗng, raw source hay absolute host path; evidence không còn dùng được có thông báo rõ
- `constrained_by:` [NFR-RKG-SEC-001, NFR-RKG-UX-001, NFR-RKG-REL-001]
- `implementation_target:` [CMP-RKG-CONVERSATION, CMP-RKG-GRAPH, CMP-RKG-TRANSPORT, CMP-RKG-WEB]
- `validated_by:` [TEST-RKG-CONVERSATIONAL-UI, TEST-RKG-CONVERSATIONAL-QA]

## Thay đổi hành vi hiện có

AC hiện có giữ ID/nội dung. Thêm cách resolve endpoint, grouping direct/indirect, clarification giữ intent, locale/greeting, một answer và exact citation.

## NGOÀI phạm vi lần này

Các FR khác không đổi. Runtime implementation, analyzer/graph schema changes, raw-source access, streaming và release không thuộc lượt chốt nội dung.

## Ràng buộc mới

Không đổi NFR limits. NFR-RKG-SEC-001/REL-001/UX-001 giữ nguyên; ADR-2026-007 giới hạn narration bằng references và factual renderer.

## Câu hỏi mở còn lại

Không có OQ nghiệp vụ mới chưa giải quyết trong selected scope. Review độc lập, signer/gates, token-based mock/walkthrough và L3 persistence compatibility là readiness work còn lại; baseline vẫn candidate.
