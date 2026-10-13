---
uid:
key: UID-RKG-001
type: ui-design
group: normative
scope: system
system: SYS-RKG
status: draft
revision: 8
change_set: CHG-RKG-2026-002
ownership: {accountable_team: TEAM-RKG, accountable_role: design-owner}
relations: {refines: [SCR-RKG-001], constrained_by: [NFR-RKG-UX-001]}
classification: internal
ai_assisted: true
---
# UID-RKG-001 — UI design direction

Professional developer-tool dashboard: dense but calm, evidence-first and optimized
for scanning. Avoid decorative portfolio/masonry patterns that compete with graph
data even though the initial design-system search suggested them.

## Design principles

1. **Evidence before decoration:** graph meaning, provenance and limitation are more
   prominent than visual effects.
2. **Identity stays visible:** repository, snapshot and focus are never implicit on
   Explorer/Ask screens.
3. **Progressive density:** show the next useful decision first; advanced budgets,
   metadata and provenance remain discoverable without crowding the primary path.
4. **Failure preserves trust:** errors state what remained unchanged and offer a safe
   next action; blank canvas is never an error treatment.
5. **Keyboard parity:** every canvas interaction has an equivalent list/detail path.

## Layout

- App shell: 240 px navigation, flexible canvas, 360 px contextual drawer on desktop.
- 12-column content grid; spacing scale 4/8/12/16/24/32/48.
- Repository create/select and job status precede Explorer; one primary action per screen/region.
- Repository/snapshot destructive actions use explicit confirm copy; active/in-use
  guards remain visible and never rely on color alone.
- Responsive breakpoints: 375, 768, 1024, 1440 px.
- Content max width: 1280 px for management screens; Explorer may use the full
  viewport after navigation. Form readable width is 640 px.
- Minimum interactive target is 44×44 px on touch layouts and 32 px on dense desktop
  layouts, with at least 8 px separation where targets are destructive or adjacent.

## Surfaces and hierarchy

- Level 0 background hosts the shell; level 1 surface hosts panels/tables; level 2
  elevated surface hosts menus, dialogs and selected detail.
- Depth comes from border + subtle shadow, not blur-heavy glassmorphism. Light-mode
  borders must remain visible.
- Page title and primary action form the first scan line. Secondary actions use menu
  or quiet buttons; destructive actions never share primary styling.
- Dense tables use sticky headers only when they do not obscure focused rows; mobile
  converts rows to labeled cards instead of squeezing columns.

## Visual tokens

`design/ui/tokens/tokens.json` là handoff machine-readable của các token dưới đây.
File JSON không được tự tạo semantic name mới hoặc ghi đè yêu cầu contrast/a11y ở đây.

- Dark mode: background `#0F172A`, surface `#1E293B`, elevated `#334155`, body
  text `#F8FAFC`, muted text `#CBD5E1`.
- Light mode: background `#F8FAFC`, surface `#FFFFFF`, elevated `#E2E8F0`, body
  text `#0F172A`, muted text `#475569`.
- Semantic tokens use `color.background`, `color.surface`, `color.elevated`,
  `color.text`, and `color.textMuted`; components must not bind directly to a
  mode-specific palette value.
- Primary/action uses dark green `#15803D` in light mode and green `#22C55E` in
  dark mode. Warning, error and info each pair color with icon/text, never color
  alone.
- Text and interactive controls must meet WCAG AA contrast in both modes; token
  contrast measurement is recorded in `evidence/tests/TEST-RKG-WCAG-CONTRAST.md`;
  component-state contrast still requires implementation evidence before UI/UX approval.
- Typography: IBM Plex Sans for UI; JetBrains Mono for identifiers/paths/code. Bundle fonts
  locally for offline/local-first operation; system fallbacks are required.
- Interaction transitions 150–250 ms; respect `prefers-reduced-motion`.

## Typography and iconography

- UI/body: IBM Plex Sans; identifier/path/code: JetBrains Mono. Font assets are
  bundled locally; no runtime request to a font CDN.
- Default body is 14/20 px on dense desktop and 16/24 px on touch-first layouts.
  Page title is 24/32 px; section title 18/28 px; metadata 12/16 px.
- Identifiers may wrap at semantic separators; relative locators use middle
  truncation with full safe value available to copy, never absolute host path.
- Use one locally bundled SVG icon family. Decorative icons are `aria-hidden`; icon-
  only controls require an accessible name and tooltip. No emoji icons.

## Component language

| Component | Rule |
|---|---|
| Button | Primary once per region; stable size on hover/loading; spinner retains label context |
| Input | Persistent label, helper/error slot, visible focus; placeholder is not a label |
| Status badge | Icon + text + semantic color; contract enum available to tests |
| Data table/list | Keyboard-reachable actions; row is not wholly clickable when it contains buttons |
| Tabs | Arrow-key navigation; selected state uses text/indicator, not color alone |
| Dialog/sheet | Named heading, focus trap/restore, explicit cancel; destructive scope in body |
| Toast/status | Supplemental only; durable failure remains near affected content |
| Tooltip | Describes unfamiliar icon; never contains required workflow information |
| Graph node | Shape + type label; selection uses outline and detail heading |
| Graph edge | Arrow + relationship label; evidence action reachable from list fallback |

## Interaction feedback

Loading, empty, succeeded-with-warnings, truncated và error đều có message + next action; không dùng
blank canvas. Status/error động được announce, dialog giữ/trả focus đúng và tab order
bám layout trực quan. Hover/focus không đổi kích thước layout.

- Loading under 300 ms may keep the prior stable content; longer work shows skeleton
  or progress without replacing page identity.
- Empty state distinguishes “no data yet” from “no search match”. The former offers a
  create/index action; the latter preserves query and offers clear filters.
- Warning never masquerades as success. `succeeded_with_warnings` shows result plus a
  direct link to diagnostics before Explorer.
- Conflict preserves the user's draft and presents Reload/Review before Retry.
- Truncation is shown beside the affected result and its budget controls, not only in
  a global toast.

## Graph semantics

Node shape + label encode entity type; edge arrow + text encode direction/type.
Selection uses outline and detail heading, not color alone. Zoom/pan controls,
fit-to-selection and keyboard focus are always available.

- Do not imply spatial position has semantic meaning unless the layout mode says so.
- Direction is encoded by arrowhead and readable relationship text; `reads` and
  `writes`, `publishes` and `consumes` remain visually distinguishable by label/shape.
- A minimap is optional; accessible list/detail fallback is mandatory.
- Large graph rendering may virtualize/offload visuals, but selected/focused entity
  and relationship must remain available to assistive technology.

## Content style

- Use concise verbs: Create repository, Index, Re-index, Activate, Open Explorer,
  Export context. Avoid “Submit” when the resulting action is known.
- Error copy follows: outcome → unchanged state → recovery. Example: “Index could
  not start. The active snapshot is unchanged. Review scan limits and try again.”
- Destructive confirmation names the object and scope; never ask only “Are you sure?”.
- Terms repository, snapshot, entity, evidence and conversation follow
  `DOM-RKG-CORE`; do not alternate with project/version/node when semantics differ.

## Anti-patterns

No emoji icons, layout-shifting hover, invisible light-mode borders, unsanitized
Markdown, auto-selected ambiguous entities or success-only styling that hides warnings.

Also avoid glass-heavy surfaces, masonry/portfolio layout, decorative gradients behind
graph data, fake terminal styling, infinite animation, token streaming simulation and
color-only graph legends.

## Repository and snapshot management

- Primary nav item **Repositories** (`/repositories`) luôn khả dụng; repository detail
  là điểm vào index, snapshot history, Explorer và Ask.
- Repository/snapshot lists dùng dense table/list; active state có text+icon; locator
  luôn là redacted text.
- Desktop dùng table có header/row semantics; ở 375 px chuyển thành card/detail stack
  thay vì làm vỡ viewport. Chỉ vùng dữ liệu thực sự không thể thu gọn mới được scroll ngang.
- Source identity controls chuyển read-only sau create; mutable defaults nằm trong
  edit region riêng để tránh ngộ nhận đổi source của snapshot cũ.
- Activate thành công hiển thị repository/snapshot identity chip rồi mở Explorer.
- Delete confirm nêu rõ phạm vi cascade; blocked delete giữ context và chỉ bước xử lý.
- Create/update/activate/delete thành công có feedback ngắn được announce; error dùng
  role/live region phù hợp, không chỉ đổi border hoặc màu.

## Ask natural-answer presentation — CHG-RKG-2026-002

Revision 8 selects the existing design system for the conversation refinement;
no new color/font/spacing tokens are added. Interface text uses ui font, technical
identifier/path text uses code font and wraps within the readable content region.

- Hierarchy: answer in body text, direct/indirect groups if needed, sources as
  secondary buttons, limitation note, collapsed technical details. Avoid printing
  the same answer in a second Claims block.
- Use complete sentences in vi/en; qualify short names only enough to distinguish.
  Directness/direction must be expressed in text, not just indentation/color.
- Clarification prompt names the ambiguity; each ordered control shows subject type
  and endpoint method/path or callable qualified identity when needed. No auto-select.
- Insufficient message appears once and explains an observed gap; error is visually
  and verbally distinct. No backend reason code is the primary product copy.
- Source control has a visible nonempty name and an accessible name describing the
  source. Dialog identifies exact evidence with relative path/line, retains current
  snapshot context and provides unavailable/loading states. Filesystem evidence
  has no fake syntax line marker. Never show source excerpts.
- Partial/history note remains close to answer and survives reload. Legacy turns
  without limitation metadata show unknown coverage, not a success badge.
- Existing focus, live-announcement, contrast, reduced-motion and responsive rules
  apply to all states in light/dark. Hidden details use native accessible disclosure.

UI/UX Gate needs a token-based mock and real keyboard/device walkthrough. This
revision specifies the layout/content choice; it does not assert those checks ran.
