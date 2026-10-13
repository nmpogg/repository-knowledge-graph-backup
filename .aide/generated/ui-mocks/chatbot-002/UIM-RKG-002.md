---
key: UIM-RKG-002
type: ui-mock
group: derived
revision: 1
non_normative: true
change_set: CHG-RKG-2026-002
derived_from: [UXF-RKG-002, SCR-RKG-001, UID-RKG-001, TOK-RKG-001]
classification: internal
ai_assisted: true
---
# UIM-RKG-002 — Preview trên Ask hiện có

Khi preview và UXF/SCR/UID bất đồng, UXF/SCR/UID thắng.

Sinh bằng `tools/render_chatbot_preview.py`; không chỉnh generated bằng tay.
Revision, byte hashes của nguồn, generator, token và bundle nằm trong `manifest.json`.
Tái sử dụng AppShell/ConversationPage/Button/dialog/locale/theme/font/token thật.
Fixture client và presentation là prototype trong staging; product source không đổi.

Chạy static preview trên loopback bằng lệnh ở README của tool. Mở
`http://127.0.0.1:5174/#/conversations/preview-answer`.

Walkthrough: đọc answer direct/indirect; mở/đóng nguồn bằng keyboard; chọn entity
để tiếp tục ý định ban đầu; xem insufficient/partial/legacy/greeting/empty;
thử Gửi trong disabled/timeout/conflict để kiểm tra draft/pending; xem unavailable.
Đổi sáng/tối, Việt/Anh và kiểm tra chuỗi dài trên thiết bị chính thật.

Các flag/evidence ở đây dùng private synthetic catalog, không chứng minh public API
binding, server persistence, resolver hay LLM đã được triển khai. Reload seed lại
fixture; các câu nhập thêm chỉ ở memory. Không có model/API call.
Real browser, device, live-provider và independent UI review chưa chạy.
UI/UX Gate vẫn pending; chỉ ký UXF r5, SCR r9, UID r8 sau đủ walkthrough/evidence.
