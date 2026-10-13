# Ask UX preview

Prototype cho CHG-RKG-2026-002, tái sử dụng frontend/Ask hiện có trong staging.
Không chỉnh product source. Không có API proxy, provider/session config hoặc LLM.
Không chạy source của repository đang phân tích. Dữ liệu fixture là synthetic.

Từ repository root:

```bash
python3 tools/render_chatbot_preview.py
```

Tool in đường dẫn staging mới. Trong thư mục staging đó chạy:

```bash
npm run test -- src/preview/Preview.test.tsx
npm run lint
npm run build
npm run preview
```

Mở `http://127.0.0.1:5174/#/conversations/preview-answer`. Dùng selector phía trên
để xem từng tình huống; đổi theme/locale bằng nút của AppShell hiện có. Không nhập
dữ liệu thật: prototype chỉ giữ câu nhập ở memory, reload trở về fixture.
Dependencies dùng frontend/node_modules đã cài; staging không copy `.env`.

Sau khi kiểm tra, sinh bundle/provenance mới (tool không ghi đè bundle hiện có):

```bash
python3 tools/render_chatbot_preview.py --publish-stage <staging-directory>
```

Bundle đã sinh có thể chạy offline từ repository root:

```bash
python3 -m http.server 5174 --bind 127.0.0.1 --directory .aide/generated/ui-mocks/chatbot-002/app
```

Fixtures mô tả cách trình bày; không chứng minh grounding/language resolver hay
API binding/server persistence đã triển khai. Private source/coverage catalog
không phải public wire contract. Bản generated khai non_normative/derived_from;
UXF/SCR/UID thắng nếu bất đồng. Không ký gate từ test/build fixture.

DOM accessibility dùng axe-core riêng ở thư mục tạm, không thêm dependency app:

```bash
npm install --prefix /tmp/rkg-chatbot-a11y-checks --no-audit --no-fund axe-core@4.10.3
RKG_PREVIEW_AXE_MODULE=/tmp/rkg-chatbot-a11y-checks/node_modules/axe-core/axe.js npm run test -- src/preview/Accessibility.test.tsx
```

Chạy lệnh test trong staging. Axe kiểm tra DOM ở cả locale/theme; color-contrast
không chạy trong jsdom, cần kiểm tra riêng trong trình duyệt. Chưa chạy
real-browser/device walkthrough và full automated WCAG audit.
UI/UX Gate cần review trên thiết bị chính thật, cả theme/locale, keyboard và
source dialog, rồi ký đúng UXF r5 / SCR r9 / UID r8.
