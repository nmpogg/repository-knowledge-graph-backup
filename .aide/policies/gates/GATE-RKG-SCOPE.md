---
uid:
key: GATE-RKG-SCOPE
type: gate-policy
group: normative
scope: system
system: SYS-RKG
status: draft
revision: 9
ownership: {accountable_team: TEAM-RKG, accountable_role: product-owner}
relations:
  verifies: [PRD-RKG, FR-RKG-001, FR-RKG-002, FR-RKG-003, FR-RKG-004, FR-RKG-005, NFR-RKG-PERF-001, NFR-RKG-SEC-001, NFR-RKG-REL-001, NFR-RKG-UX-001, NFR-RKG-EXT-001]
classification: internal
ai_assisted: true
---
# GATE-RKG-SCOPE — Scope Gate checklist

- [ ] Problem, persona, in/out scope, assumptions and constraints are explicit.
- [ ] Every GOAL maps to FRs; every FR has binary AC and an implementation target.
- [ ] Extensibility goal có quality gate đo được tại NFR-RKG-EXT-001 và tách rõ MVP adapter profile khỏi core product architecture; không biểu diễn lại thành product KPI/FR riêng.
- [ ] NFR `constrains` and FR `constrained_by` links are symmetric.
- [ ] KPI target, sample rule and OBS measurement agree with `PRD-RKG`, `OBS-RKG-001`/`002`/`005` and `EVAL-RKG-QA-001`.
- [ ] Open questions state owner, concrete trigger/deadline and blocking effect.
- [ ] Repository CRUD and immutable snapshot lifecycle are explicit; no duplicate RepositoryVersion entity or cross-repository graph is implied.
- [ ] Live analyzer/backend implementation does not precede `TASK-RKG-001`; contract-shaped frontend mock is allowed and is not treated as live backend.
- [ ] PM/Product Owner, Tech Lead and QA Lead review exact artifact revisions and sign an append-only approval record.
- [ ] Approver `name` is a real accountable identity or an organization-approved
      signer identifier, not a role label repeated as the name.
      *(waived for `approval-004` — identity intentionally omitted; see OQ-RKG-006)*

## Decision rule

Any unchecked item blocks approval. The checklist never changes artifact status by
itself. On approval, record exact revisions and commit in `evidence/approvals/`, then
update PRD/change-set status and baseline in a separate reviewed change.

## CHG-RKG-2026-002 scoped approval

`approval-007` records the explicit human Scope decision by PhongNM, confirmed to
represent Product Owner, Tech Lead and QA Lead. It approves FR-RKG-005 revision 9,
with the same AC content reviewed in revision 8. Exact artifact hashes are recorded
in the approval and BL-CHG-RKG-2026-002-r2. No historical identity waiver is reused.

- [x] Scope delta AC-RKG-074…081 is selected and approved by the named human signer.
- [x] Existing AC identities/content and FR005/NFR constraint symmetry are verified.
- [x] Required Scope roles are explicitly confirmed for PhongNM.
- [x] Scope record identifies reviewed and approved revisions and hashes separately.

The full-MVP checklist above remains pending for CHG-RKG-2026-001. Scoped chatbot
approval does not approve the unrelated PRD/FR changes or resolve its OQ-RKG-006.
Author checks are deterministic evidence; the human decision is not attributed to
tooling. Architecture, UI/UX and Contract approvals for CHG-RKG-2026-002 remain pending.
