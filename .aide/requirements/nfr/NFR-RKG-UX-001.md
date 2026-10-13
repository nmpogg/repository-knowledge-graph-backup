---
uid:
key: NFR-RKG-UX-001
type: non-functional-requirement
group: normative
scope: system
system: SYS-RKG
status: approved
revision: 7
ownership:
  accountable_team: TEAM-RKG
  accountable_role: design-owner
relations:
  constrains: [FR-RKG-003, FR-RKG-001, FR-RKG-005]
classification: internal
ai_assisted: true
---

# NFR-RKG-UX-001 — Usability and accessibility

## Mô tả
Luồng local UI phải tự giải thích, phân biệt rõ trạng thái thiếu/lỗi/cắt cụt, và
không thực thi nội dung không tin cậy từ repo hoặc model.

## Yêu cầu (normative)

1. **Primary flow:** repository create/select → job → snapshot → search → graph → evidence → context export có loading/empty/error/`succeeded_with_warnings`/truncated states; UI không phát minh enum `partial` ngoài contract.
2. **Accessibility:** keyboard navigation và focus visible; form có label; màu không là chỉ dấu duy nhất.
3. **Contrast & motion:** text/body contrast đạt WCAG AA ở light và dark; tôn trọng reduced motion.
4. **Responsive:** dùng được ở 375, 768, 1024 và 1440 px; không horizontal scroll ngoài graph canvas.
5. **Safe rendering:** tên/dữ liệu source escape; Markdown answer được sanitize; không render HTML/script từ repo hoặc model.
6. **Typography:** semantic font tokens dùng IBM Plex Sans cho UI và JetBrains Mono cho identifier/path/code, bundle local có system fallback theo `UID-RKG-001` và `design/ui/tokens/tokens.json`.
7. **Announcements and focus:** error/status động dùng live region phù hợp; dialog trap focus và trả focus về control kích hoạt; tab order bám thứ tự trực quan.
8. **Lifecycle safety:** repository/snapshot list có empty/loading/error/conflict states; active snapshot được nhận diện bằng text/icon; destructive action yêu cầu confirm, giải thích guard và giữ focus/state khi bị từ chối.
