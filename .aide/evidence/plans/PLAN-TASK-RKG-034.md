---
key: PLAN-TASK-RKG-034
group: evidence
revision: 1
type: implementation-plan
task: TASK-RKG-034
---
# PLAN-TASK-RKG-034 — Existing Ask delivery

1. RED: frontend metadata/client/UI tests cover unknown legacy/future metadata, durable limits on reload, collapsed claims, one insufficient message, coherent capability negotiation, exact source ownership/path/pin and keyboard focus.
2. GREEN: types/api.ts and client live/mapWire.ts/liveClient.ts add metadata/status interrupted, capabilities, unavailable history, exact citation response with safe source mapping, candidate method/path attributes. Mock client implements the same public shape; no preview-only adapter.
3. GREEN: existing ConversationPage.tsx negotiates features before enabling actions, only404 confirms legacy, sends locale to supported backend, preserves draft/error during history reload, reads flags from persisted metadata, shows one answer with native collapsed claims and labelled ordered candidates.
4. GREEN: exact source dialog calls per-turn citation route, checks citation ID/pin/ownership, never uses getEntity/quote/excerpt. Include loading/unavailable messages, safe locator, Escape/Tab/focus restoration. i18n en/vi translates observed limitation codes; index.css preserves multiline/long names.
5. Verify Vitest client/UI regressions, frontend lint/build, then freeze independent adversarial review. TASK035 adds browser walkthrough/AC matrix and whole-system validation. Signed UIS/API contracts unchanged.

Work on current fix/chatbot is explicit. TASK033 upstream candidate is frozen for independent review; final completion waits for its resolution.
