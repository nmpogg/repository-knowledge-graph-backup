---
uid:
key: GATE-RKG-ARCHITECTURE
type: gate-policy
group: normative
scope: system
system: SYS-RKG
status: draft
revision: 7
ownership: {accountable_team: TEAM-RKG, accountable_role: architect}
relations:
  verifies: [CAP-RKG-001, CAP-RKG-002, CAP-RKG-003, CMP-RKG-ANALYZER, CMP-RKG-GRAPH, CMP-RKG-TRANSPORT, CMP-RKG-WEB, CMP-RKG-CONVERSATION, ADR-2026-001, ADR-2026-002, ADR-2026-003, ADR-2026-004, ADR-2026-005, ADR-2026-006, ADR-2026-007, TM-RKG]
classification: internal
ai_assisted: true
---
# GATE-RKG-ARCHITECTURE - Architecture Gate checklist

- [x] L1 capabilities cover all FRs without hidden implementation ownership.
- [ ] Review current L2 boundaries, including core Directory ownership and adapter semantic output.
- [x] ADRs cover static/evidence-first analysis, versioned adapter boundary, Kùzu, React/Vite and Repository→Snapshot lifecycle choices with alternatives/trade-offs.
- [x] Core analyzer has no language/framework-specific branch; adapter registry, DTO boundary, failure semantics and conformance test are explicit.
- [x] One-process/single-writer rule and pinned-reader/retention guards are testable.
- [x] Threat model covers source execution, local filesystem/path boundary, secret, injection/XSS, dependency confusion and storage access.
- [x] Repository/snapshot ownership, optimistic update and guarded cascade transaction boundaries are testable.
- [ ] Derived L1/L2 views reflect current Directory and adapter ownership artifacts.
- [ ] Tech Lead and Architect sign an append-only approval record for exact revisions.
      *(waived for `approval-005` — identity intentionally omitted)*

Any unchecked item blocks Architecture Gate approval.

## Current revision status

Architecture Gate is pending after CMP revisions and draft ADR-2026-006. Historical
approval-005 is preserved and does not approve the new revisions. Review Directory
ownership, evidence, adapter v2 and historical snapshot compatibility before issuing
an append-only approval for the current artifact hashes.

## CHG-RKG-2026-002 scoped Architecture approval

`approval-009` completes the named Tech Lead/Architect signoff by PhongNM for the
chatbot architecture delta. `approval-008` remains the historical Tech Lead-only
record; CR-RKG-006 confirms the additional Architect authority. No identity waiver
is reused. The reviewed architecture source bytes remain frozen at ADR-2026-007 r2,
CMP-RKG-CONVERSATION r7, CMP-RKG-WEB r9 and TM-RKG r8.

- [x] Independent advisory review REV-RKG-2026-005 plus recovery review REV-RKG-2026-007 cover the exact current design pins.
- [x] COMP-CHG002-001 is resolved at design level; no unresolved design blocker.
- [x] Named Tech Lead and Architect signoff is captured in approval-009.
- [x] Reference-only narration, topology/direction/evidence validation, fallback, pending intent and limitation persistence are approved for the chatbot delta.

Approval scope is ADR-2026-007 and the chatbot-specific sections of the shared
CMP/TM artifacts; it does not promote unrelated full-MVP sections to approved.
Exact source hashes and approved sections are locked in BL-CHG-RKG-2026-002-r5.
Source draft metadata/comments remain as captured by review; effective scoped
approval is recorded in the signed baseline, not by rewriting frozen design bytes.

The full-MVP checklist above remains pending for CHG-RKG-2026-001. UI/UX and
Contract Gate for CHG-RKG-2026-002 remain pending; runtime/preview/UAT are not verified.
