---
uid:
key: DOM-RKG-CORE
type: domain-glossary
group: normative
scope: system
system: SYS-RKG
status: draft
revision: 5
ownership:
  accountable_team: TEAM-RKG
  accountable_role: domain-owner
relations:
  satisfies: [GOAL-RKG-001, GOAL-RKG-002]
  constrains: [ADR-2026-002]
classification: internal
ai_assisted: true
---

# Core glossary and invariants

| Thuật ngữ | Định nghĩa |
|---|---|
| Repository | Nguồn code local được đăng ký bền vững; source identity bất biến, metadata/defaults có revision và có tối đa một active snapshot |
| Source | Local working tree bất biến được chuẩn bị từ một Repository để làm input cho một job |
| Manifest | Danh sách file được phép đọc cùng hash/metadata của lần scan |
| Index job | Một yêu cầu thuộc đúng một Repository để chuẩn bị source, detect, extract, validate và có thể publish đúng một candidate snapshot |
| Job stage | Trạng thái tiến trình contract: `queued`, `detecting`, `indexing`, rồi terminal `succeeded`, `succeeded_with_warnings` hoặc `failed` |
| Scan report | Tổng hợp deterministic của manifest, file parsed/skipped/error, fact, unresolved, warning, duration và capability cho một job |
| Entity | Node có identity ổn định trong phạm vi một snapshot |
| Relationship | Edge có hướng, semantics xác định và evidence |
| Evidence | Vị trí source/rule chứng minh một entity hoặc relationship |
| Unresolved | Tham chiếu analyzer không đủ bằng chứng để nối thành edge |
| Snapshot | Graph bất biến đã validate và publish nguyên tử của một lần index thành công; source revision là metadata của snapshot, không phải entity Version riêng |
| Active snapshot | Snapshot thuộc một Repository được query mặc định cho repository đó; có thể đổi bằng publish hoặc activate và không đổi khi job thất bại |
| Detection | Nhận diện ngôn ngữ/framework/technology từ declaration/import/usage và provenance |
| Deep adapter | Extractor hiểu pattern cụ thể của ngôn ngữ/framework/library được hỗ trợ |
| Context package | JSON hữu hạn gồm entity, edge, evidence, warning và snapshot |
| Conversation focus | Entity đã resolve dùng để hiểu câu hỏi nối tiếp |
| Pending clarification | Danh sách candidate có thứ tự đang chờ người dùng chọn; chưa trở thành conversation focus cho đến khi được resolve explicit |
| History window | Phần turn đã hoàn tất hữu hạn được gửi provider theo giới hạn ở `NFR-RKG-REL-001`; structured focus/pending state được giữ riêng |
| Redacted conversation content | Question/answer đã loại credential, secret/config value, raw source, provider chain-of-thought và dữ liệu ngoài allowlist trước khi lưu; operational log không sao chép transcript này |

## Invariants

1. Analyzer không thực thi source hoặc kết nối dịch vụ mà source tham chiếu.
2. Không có evidence thì không tạo edge; ambiguity trở thành diagnostic/unresolved.
3. Repository có nhiều Snapshot; Snapshot thuộc đúng một Repository và query không trộn repository/snapshot.
4. Snapshot graph, manifest identity và source revision bất biến; re-index tạo snapshot mới.
5. Publish/activate snapshot là nguyên tử theo repository; failure không thay active snapshot hiện hữu.
6. Conversation pin repository/snapshot; history chỉ hỗ trợ intent, không trở thành graph fact.
7. Secret/config value/raw source không được lưu vào graph hay log; conversation history đã redact chỉ sống trong conversation store, không ở operational log.
8. Một thời điểm chỉ có một index writer toàn ứng dụng; job cạnh tranh không thay đổi job hoặc active snapshot của bất kỳ repository nào; `ADR-2026-002` và `NFR-RKG-REL-001` là các ràng buộc thực thi tương ứng.
9. Xóa snapshot/repository phải atomically tôn trọng active-reader, conversation và job guards; không cascade sang repository khác.
