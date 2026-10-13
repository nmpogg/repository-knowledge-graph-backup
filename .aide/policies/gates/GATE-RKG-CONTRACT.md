---
uid:
key: GATE-RKG-CONTRACT
type: gate-policy
group: normative
scope: system
system: SYS-RKG
status: draft
revision: 9
ownership: {accountable_team: TEAM-RKG, accountable_role: tech-lead}
relations:
  verifies: [API-RKG-CORE-v1, TBL-RKG-GRAPH, DDL-RKG-GRAPH, UIS-RKG-001, NFR-RKG-SEC-001, NFR-RKG-REL-001]
classification: internal
ai_assisted: true
---
# GATE-RKG-CONTRACT - Contract Gate checklist

- [x] Endpoint inputs, outputs, paging/order, limits, errors and versioning are explicit.
- [x] Repository CRUD and nested snapshot list/detail/activate/delete define immutable source/snapshot fields, optimistic revision, ownership and delete guards.
- [ ] CLI exit codes, loopback/single-worker defaults and parity with API validation are explicit and integration-tested.
- [ ] Polling/Q&A response behavior and the non-streaming v1 decision are reflected in UI/transport artifacts.
- [ ] Session/Origin/Host checks and no-secret/no-absolute-path errors have integration ACs.
- [x] Semantic schema names exactly 12 node tables (including `SchemaMeta`) and 13 relationship tables with identity/evidence rules.
- [x] Revised DDL and non-destructive CONTAINS migration implement the physical shape shared by TBL revisions 11 and 12 and execute on the pinned Kuzu version; verified by TEST-RKG-DIRECTORY-IMPLEMENTATION-001. Revision 12 adds no tables.
- [x] Atomic publication/activation/deletion, cross-repository isolation, pinned reads, retention, idempotency and migration fixtures have planned tests.
- [ ] Tech Lead and QA Lead sign an append-only approval record that closes the full Contract Gate.

Checked items may be recorded in a partial approval for a documented subset.
Unchecked items block full Contract Gate closure; they do not block implementation tasks that only need the approved subset (API/TBL limits and schema).

## Current revision status

Contract Gate is pending. Approval-006 remains historical partial evidence for
the exact rev-9 API/TBL/DDL subset; it does not approve API revision 15, TBL
revision 12, or the current DDL comment. Gate keys in the change set are
`scope`, `architecture`, `ui_ux`, and `contract`. Policy files are
`GATE-RKG-SCOPE`, `GATE-RKG-ARCHITECTURE`, `GATE-RKG-UIUX`, and
`GATE-RKG-CONTRACT`. TASK-RKG-027 must verify adapter v2, legacy
snapshot reads, structural evidence, API/UI shapes and executed DDL/migration before
new approval. Current-tree DDL/migration execution is recorded in TEST-RKG-DIRECTORY-IMPLEMENTATION-001.
This is test evidence, not a new gate approval; historical approvals remain unchanged.

`UIS-RKG-001` is a required Contract Gate input when the change touches the
UI. UI/UX Gate signs UXF, SCR and UID only. Revision 7 of this gate did not
list `UIS-RKG-001` or `DDL-RKG-GRAPH` in `verifies`. DDL remains the physical
schema that must match the TBL revision it declares.

## CHG-RKG-2026-002 L3 candidate

The chatbot delta has Scope, Architecture and UI/UX approvals (007/009/010), but
its Contract Gate remains pending. API r16, TBL r13, declared DDL r13,
MIG-RKG-CHATBOT-v3 r1, CON-RKG-CONVERSATION-v1 r1, wire/OpenAPI/model schemas r1
and UIS r13 are the contract candidate. Frozen signed FR/L2/UXF/SCR/UID hashes
are unchanged; L3 candidates are not covered by earlier approvals.

- [ ] Exact current revisions/hashes reviewed independently; findings resolved or
  explicitly dispositioned by the human gate authority.
- [ ] Schema/request/query/response delta is machine-classified against current
  runtime OpenAPI and the pinned API-r15 normative projection; limitations of
  untyped old response schemas are explicit. No untested equivalence claim.
- [ ] DDL equals TBL's fenced executable shape; fresh DDL and atomic 2→3 migration,
  old row/pin/evidence preservation, no-op replay and injected-failure rollback
  are executed on pinned Kuzu 0.11.3 with current hashes in evidence.
- [ ] Wire negotiation, response metadata/replay, pending intent, exact source
  ownership/provenance and UIS binding align with AC-RKG-074…081 and NFR budgets.
- [ ] Consumer components are derived from normative constrained_by/owned_by
  relationships, and their accountable TEAM-RKG roles acknowledge the proposed
  wire/storage/deployment compatibility and protected-backup rollback plan.
- [ ] Named Tech Lead and QA Lead approve the exact scoped contract baseline.

Author fixture/schema/DDL checks are readiness evidence, not independent review,
production integration or human gate signature. A scoped contract approval may
approve this design/physical-schema subset for subsequent implementation tasks;
full-MVP integration/CLI/security items above remain pending where not verified.
New features must have runtime API/storage/UI/integration and quality evidence
before their implementation tasks are done; contract design approval does not
claim the pre-delta runtime already supports them. No operator database migration
or rollback is executed as part of contract drafting. UIS is level 4 and does
not require reopening UI/UX Gate unless it changes the signed level-1–3 experience.
