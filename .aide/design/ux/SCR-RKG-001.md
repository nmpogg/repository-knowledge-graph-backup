---
uid:
key: SCR-RKG-001
type: screen-inventory
group: normative
scope: system
system: SYS-RKG
status: draft
revision: 9
change_set: CHG-RKG-2026-002
ownership: {accountable_team: TEAM-RKG, accountable_role: design-owner}
relations: {refines: [UXF-RKG-001, UXF-RKG-002, UXF-RKG-003]}
classification: internal
ai_assisted: true
---
# SCR-RKG-001 — Screen inventory and information architecture

## Information architecture

```text
Application shell
├── Repositories
│   ├── Repository list
│   ├── Create repository
│   └── Repository detail
│       ├── Edit defaults
│       ├── Job monitor / scan report
│       └── Snapshot history / detail
├── Explorer (requires a usable snapshot)
│   ├── Search and filters
│   ├── Graph canvas + accessible list fallback
│   ├── Entity / edge / evidence drawer
│   ├── Technology / dependency / diagnostic panels
│   └── Context export
└── Ask (requires a pinned usable snapshot and configured LLM)
    ├── Conversation list
    └── Conversation workspace / citation drawer
```

Repositories là điểm vào mặc định. Explorer và Ask luôn mang context chip gồm display
name repository và snapshot ID rút gọn; route không hợp lệ phải recovery về repository
detail thay vì render graph rỗng.

## Route inventory

| Route | Screen | Entry requirement | Primary action |
|---|---|---|---|
| `/repositories` | Repository list | none | Create/open repository |
| `/repositories/new` | Repository create | local session cho submit | Create repository |
| `/repositories/:repositoryId` | Repository detail | repository tồn tại | Index hoặc open active snapshot |
| `/repositories/:repositoryId/edit` | Repository edit | current revision | Save defaults |
| `/jobs/:jobId` | Job monitor/report | job thuộc repository khả dụng | Open published snapshot hoặc retry |
| `/explorer?snapshot_id=:snapshotId` | Explorer | snapshot usable | Search/select entity |
| `/conversations` | Conversation list | optional repository/snapshot filter | Create/open conversation |
| `/conversations/:conversationId` | Conversation workspace | conversation + pinned snapshot | Send follow-up |

Route có resource không tồn tại hoặc ownership mismatch dùng generic not-found; không
hiển thị repository/snapshot metadata từ request bị từ chối.

## Screen/state inventory

| Screen/region | Primary action | Required states |
|---|---|---|
| Repository list | Create/open repository | loading, empty, ready, error, delete-confirm, delete-blocked |
| Repository create/edit | Create/update repository | initial, validating, submitting, invalid, conflict, saved |
| Repository detail | Start indexing/open active snapshot | loading, ready, no-active-snapshot, job-conflict, delete-confirm, delete-blocked |
| Job monitor | Open completed snapshot | queued, detecting, indexing, app-selection, succeeded, succeeded_with_warnings, failed |
| Scan report | Inspect result/recovery | loading, ready, warnings, failed, unavailable |
| Snapshot list/detail | Open/activate/delete snapshot | loading, empty, ready, active, unavailable, activate-error, delete-confirm, delete-blocked |
| Explorer | Select/search graph entity | no-active-snapshot, loading, empty, ready, truncated, stale/unavailable, error |
| Evidence drawer | Copy relative location | closed, loading, ready, unavailable |
| Technology panel | Inspect detection/support | loading, empty, `supported_patterns`, `detected_only`, `version_unverified`, `unsupported_version`, error |
| Dependency panel | Filter/open provenance | loading, empty, ready, paged, error |
| Diagnostic panel | Inspect warning/error | loading, empty, ready, paged, error |
| Context export | Download JSON | ready, generating, validation-error, complete, error |
| Conversation list | Create/open conversation | loading, empty, ready, delete-confirm, delete-blocked, error |
| Conversation workspace | Send follow-up | disabled, idle, pending, answered, needs_clarification, insufficient_evidence, error, conflict, snapshot-unavailable |

Các label như “Completed with warnings” chỉ là presentation copy của contract enum;
không tạo enum lifecycle thứ hai.

## Screen blueprints

### Repository list

- Header: page title, short description, primary **Add repository**.
- Toolbar: search by display name, result count; paging ở cuối list.
- Row/card: display name, redacted locator, updated time, active snapshot state,
  overflow actions. Click name mở detail; delete không nằm trên toàn bộ row.
- Empty state: giải thích “repository registration does not modify source” và CTA.
- Error state: message an toàn + Retry; không thay lỗi bằng empty state.

### Repository create/edit

- Create sections: Identity (`display_name`, `path`) và Advanced defaults
  (`source_root`, app module/symbol, scan defaults).
- Path là text input trên host chạy RKG, không phải upload/file picker ngầm hứa truy
  cập filesystem client. Helper copy nhắc allowed roots nhưng không lộ root tuyệt đối.
- Edit hiển thị source type/locator read-only; chỉ mutable defaults được submit cùng
  `expected_revision`.
- Inline error đặt cạnh field; summary ở đầu form liên kết tới lỗi đầu tiên. Submit
  giữ nguyên draft khi validation/conflict thất bại.

### Repository detail and snapshots

- Header: repository identity, redacted locator, edit menu.
- Status strip: active snapshot, last scan result, warning count; nếu chưa có active
  snapshot thì CTA **Index repository**.
- Main regions: index defaults/job action, snapshot history, scan report summary.
- Snapshot row: created time, source revision rút gọn, counts, capability state,
  active marker bằng icon + text, actions Open/Activate/Delete.
- Delete repository nằm trong danger zone cuối trang, không cạnh primary index action.

### Job monitor and scan report

- Stage stepper chỉ dùng `queued → detecting → indexing → terminal`; text/live region
  thông báo thay đổi, không animate liên tục khi reduced motion.
- Poll theo `Retry-After`, hiển thị last updated và nút manual retry chỉ khi request lỗi.
- Multiple app candidates là blocking selection trong content, không auto-select;
  technology/adapter detection nằm ở non-blocking capability panel.
- Terminal success dẫn tới snapshot; warning state đặt report trước CTA Explorer;
  failed state nêu code/recovery và xác nhận active snapshot cũ không đổi.

### Explorer

Desktop composition:

```text
┌─ App nav ─┬─ Repository / snapshot context ────────────────────────┐
│ Repos     │ Search + type filter                     Export context │
│ Explorer  ├───────────────┬─────────────────────────┬───────────────┤
│ Ask       │ Result list   │ Graph canvas / list     │ Detail drawer │
│           │ + presets     │ controls + limit badge │ Evidence/tabs │
└───────────┴───────────────┴─────────────────────────┴───────────────┘
```

- Search result luôn hiển thị type, name/qualified name và disambiguating metadata;
  chọn explicit result mới đổi root.
- Graph toolbar: direction, edge type, depth, node budget, zoom, fit selection và
  nhóm view Graph / List / Structure trên cùng một hàng nút. Truncated badge nằm cạnh budget controls.
- Node/edge selection mở detail drawer nhưng giữ focus context; close trả focus về
  selected item. List fallback cung cấp cùng selection/evidence actions.
- Technology, Dependency và Diagnostics là tabs/regions trong contextual surface,
  không phủ graph bằng modal dài.
- Export dialog tóm tắt root/budget và báo `truncated` sau khi hoàn tất.

### Conversation workspace

```text
┌─ Conversation list ─┬─ Pinned repository / snapshot / focus ──────┐
│ New conversation    │ Ordered transcript                          │
│ Search/filter       │ Explanation → sources → limits / [details]   │
│ Saved conversations │ Clarification candidates                    │
│                     ├──────────────────────────────────────────────┤
│                     │ Question composer                    Send    │
└─────────────────────┴──────────────────────────────────────────────┘
```

- Composer có label, remaining-character hint và submit disabled reason; Enter/line
  break behavior được công bố, không chặn IME tiếng Việt.
- Pending tạo một status region, khóa duplicate submit/delete nhưng không khóa đọc
  history/citation đã có. Không giả lập token streaming.
- Citation là button có accessible name, mở evidence drawer và chỉ hiển thị relative
  locator. Clarification candidates là ordered radio/list options, không auto-select.
- Snapshot mới chỉ tạo notice + action tạo conversation mới; conversation hiện tại
  không đổi pin.

## Responsive behavior

| Width | Navigation | Main content | Contextual detail |
|---|---|---|---|
| 1440 px | 240 px persistent rail | 12-column, graph ưu tiên | 360 px persistent drawer |
| 1024 px | compact rail | result list có thể collapse | overlay drawer không che trigger |
| 768 px | top bar + menu | two-region stack | side sheet/full-height dialog |
| 375 px | top bar | single-column route/stack | dedicated detail route hoặc bottom sheet |

Ở mobile, table đổi thành card/detail stack; chỉ graph canvas được horizontal pan.
Graph controls có touch target tối thiểu 44×44 px và list fallback luôn khả dụng.

## Shared accessibility and content rules

- Có skip link tới main content; một `h1`/screen và heading hierarchy tuần tự.
- Tab order bám visual order; focus ring không bị clip; loading không lấy focus tự động.
- Status dùng polite live region; validation/destructive failure dùng alert phù hợp.
- Skeleton/placeholder có accessible label hoặc ẩn khỏi accessibility tree; không đọc
  từng skeleton cell.
- Empty/error copy gồm điều gì xảy ra, phạm vi ảnh hưởng và một hành động phục hồi.
- Không dùng emoji làm icon; một bộ SVG icon có accessible name hoặc `aria-hidden`.

## Conversation workspace refinement — CHG-RKG-2026-002

Revision 9 replaces the old visible Answer→Claims sequence for Ask with:

```text
Pinned repository / snapshot / selected endpoint or handler
Question
Natural explanation
  Direct relations first → relevant verified indirect paths
  Sources: readable relative location / source ordinal
  Partial/history/unknown coverage note when applicable
  [Details: qualified names and validated relations] (collapsed)
Clarification: why a choice is needed + ordered labeled choices
Question composer → Send
```

Routes and existing states stay as listed above. The Ask workspace still has one
primary action, Send; in clarification, selecting the intended entity is the current
primary decision. Secondary source/details controls do not repeat the primary answer.
Empty/greeting, insufficient, partial, disabled, error/conflict and unavailable
states follow UXF-RKG-002 revision 5. Source dialog opens exact referenced evidence.
The layout stacks at narrow widths, wraps long identifiers and does not require
horizontal scrolling to read answer/choices/sources. Native controls keep keyboard
and focus semantics. API field bindings are not part of this level-2 artifact.
