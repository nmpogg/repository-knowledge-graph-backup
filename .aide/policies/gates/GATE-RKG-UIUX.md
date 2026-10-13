---
uid:
key: GATE-RKG-UIUX
type: gate-policy
group: normative
scope: system
system: SYS-RKG
status: draft
revision: 9
ownership: {accountable_team: TEAM-RKG, accountable_role: design-owner}
relations:
  verifies: [UXF-RKG-001, UXF-RKG-002, UXF-RKG-003, SCR-RKG-001, UID-RKG-001, TOK-RKG-001, NFR-RKG-UX-001]
classification: internal
ai_assisted: true
---
# GATE-RKG-UIUX — UI/UX Gate checklist

> Approval-003 chỉ khóa các revision UI/UX cũ. Gate hiện `pending` cho đến khi các
> revision hiện tại được review lại và approval record mới ghi danh tính người ký.

- [ ] Each primary flow has loading, empty, succeeded-with-warnings/truncated, error and recovery behavior using contract states.
- [ ] No-active-snapshot, app-selection, LLM-disabled and conflict states are specified.
- [ ] Repository create/edit/delete and snapshot activate/delete cover empty/error/confirm/blocked states without implying mutable snapshot content.
- [ ] Semantic tokens in `tokens.json` match UID; latest token evidence
  (`TEST-RKG-WCAG-CONTRAST-002`) passes core pairs and browser/component evidence
  covers interactive/status states in light/dark.
- [ ] Keyboard path, focus visible/order/restore, live announcements and graph list fallback are verified.
- [ ] Repository/model content is escaped or sanitized; color is never the only signal.
- [ ] Layout is checked at 375, 768, 1024 and 1440 px; only graph canvas may scroll horizontally.
- [ ] Mock and live clients use identical API shapes and state enums.
- [ ] Design Owner and QA Lead sign an append-only approval record for exact revisions.

Any unchecked item blocks UI/UX Gate approval.

## Directory revision review

UI/UX Gate remains pending. The artifacts this gate signs are UXF, SCR and UID.
`UIS-RKG-001` is level-4 UI specification. It binds to the API contract and is
verified by Contract Gate, not by this gate. Revision 6 listed `UIS-RKG-001`
in `verifies`. Token and UX-NFR checks stay on this checklist.

Directory presentation in the level 1-3 artifacts still needs review before a
new UI/UX approval. Flow binding to Directory fields is a Contract Gate check
against `UIS-RKG-001`.

## CHG-RKG-2026-002 candidate before approval-010

New FR-RKG-005, conversation/web design, ADR-2026-007 and UX level 1–3 revisions
select conversational answer behavior. At policy revision 8, this scoped gate
was pending for their exact hashes. Author verification is not independent review or human gate approval.
Historical approvals and their identity waivers do not cover these revisions.

- [ ] Review one answer, readable sources, clarification, partial/legacy states on token-based mock; keyboard and real-device walkthrough required.

## CHG-RKG-2026-002 UI/UX decision

Approval-010 records PhongNM as Product Owner, Design Owner and QA Lead for the
chatbot delta in UXF-RKG-002 r5, SCR-RKG-001 r9 and UID-RKG-001 r8. Exact frozen
hashes and scoped sections are approved in BL-CHG-RKG-2026-002-r6; shared source
metadata stays draft. UIM-RKG-002 is a derived review aid and is not signed.

- [x] One answer, readable sources, clarification, partial/legacy, empty/greeting,
  error/recovery and unavailable states reviewed on the existing token-based Ask.
- [x] Named human approval and walkthrough checklist reported in CR-RKG-007;
  actual device identifier unspecified, without inferred device telemetry.
- [x] Current-tree component/DOM checks in TEST-RKG-CHATBOT-PREVIEW-001 and rendered
  browser/layout/contrast/keyboard checks in TEST-RKG-CHATBOT-BROWSER-001.

The chatbot UI/UX gate is approved. The unchecked full-MVP checklist above and
CHG-RKG-2026-001 remain pending; this scoped decision does not approve unrelated
management/Directory/graph changes. Public wire binding, migration and UIS level 4
are Contract Gate work. Production runtime, live model quality, UAT and release
are not approved here. Changing any signed UXF/SCR/UID revision/hash reopens this
scoped gate. Historical approvals, preview/evidence and baseline r5 are preserved.
