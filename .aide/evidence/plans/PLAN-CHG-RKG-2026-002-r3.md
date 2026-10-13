---
key: PLAN-CHG-RKG-2026-002-r3
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
revision: 1
captured_at: 2026-10-06
change_set: CHG-RKG-2026-002
stage: existing-Ask-UX-preview-before-L3
non_normative: true
implementation_ready: false
captured_against:
  base_code_commit: 86ecab6546384227d1901e24c8b8fbfc6c0e8527
  baseline: BL-CHG-RKG-2026-002-r5
  scope_approval: approval-007
  architecture_approval: approval-009
previous_plan: PLAN-CHG-RKG-2026-002-r2
classification: internal
ai_assisted: true
---
# PLAN-CHG-RKG-2026-002-r3 — Preview response trên Ask hiện có

## Mục tiêu

Chuẩn bị bản preview tương tác dùng AppShell, ConversationPage, Button, dialog,
locale/theme và token của frontend hiện có. Không xây màn hình chat khác. Đây là
prototype UX cấp 1–3 trước L3 theo workflow B.9; không phải implementation chatbot.

Scope và Architecture đã approved; UXF/SCR/UID vẫn draft và cần walkthrough.
Giữ nguyên code trong `frontend/src`, backend và artifact đã ký. Source prototype
được materialize trong thư mục tạm; bundle là derived artifact dưới generated UI.

## Bước, file và kiểm chứng

1. `tools/chatbot-preview/`: fixture client, private presentation catalog và UI
   fragment/test/harness. Tái sử dụng RkgClient/public types hiện có; annotation
   sources/flags là private prototype data, không phải đề xuất wire schema mới.
   Fixture gồm answer direct/indirect, clarification, insufficient, partial,
   legacy coverage unknown, greeting Việt/Anh, provider error và unavailable.
2. `tools/render_chatbot_preview.py`: pin inputs, copy frontend source vào staging
   mới không chứa `.env`, force fixture client, bỏ API proxy và materialize phần
   trình bày. Dùng hash/anchor guards để không sửa nhầm source. Giữ Vite/React và
   token thật; không install dependency của repository đang phân tích.
3. Trong staging: render một answer chính; claims ở details thu gọn, citation có
   nhãn và chọn exact evidence từ private fixture catalog, insufficient chỉ một
   message, partial/history/unknown nói bằng ngôn ngữ người dùng. Giữ keyboard,
   dialog focus, draft/revision/pending controls và safe text rendering.
4. Chạy component tests có ý nghĩa cho các lỗi người dùng đã gặp và source/focus
   interaction; build và lint staging. Không dùng fixture result chứng minh backend
   language resolver, graph grounding hoặc server persistence đã triển khai.
5. Sinh bundle + UIM provenance/manifest/case checklist; preview chỉ loopback trên
   cổng khác app thật. Dữ liệu nguồn là synthetic, không gửi network/provider.
6. Ghi test evidence pin baseline, fixture/tool/source hashes và checks
   passed/failed/not_run. Actual browser/device/readability walkthrough chỉ pass
   khi thực sự thực hiện; không giả screenshot hoặc human approval.
7. Handoff bản preview cho human review. UI/UX Gate vẫn pending; sau approval mới
   chốt L3/API/UIS, đánh giá metadata persistence và decomposition task/context.

## Giới hạn và evidence

- Không chỉnh response flow của service thật, public API/TBL/UIS hoặc dữ liệu user.
- Không đọc/copy `.env`, session token hoặc credentials vào prototype/bundle.
- Source fixture là synthetic; không lưu question/answer thực tế vào log/evidence.
- Không dùng localStorage của app thật: preview chạy origin riêng. Typed questions
  chỉ ở memory của prototype; reload mở fixture đã seed, không giả server persistence.
- Không đánh dấu task/gate done từ build/test fixture. UI và backend/language/citation
  integration thật được verification ở task triển khai sau các prerequisite gates.
- Findings/review/approval lịch sử append-only. Replan thêm revision mới.
