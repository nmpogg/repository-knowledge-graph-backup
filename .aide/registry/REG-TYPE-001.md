---
uid: null
key: REG-TYPE-001
type: type-registry
group: normative
scope: org
status: draft
revision: 7
ownership:
  accountable_team: TEAM-RKG
  accountable_role: tech-lead
relations: {}
classification: internal
ai_assisted: true
---

# REG-TYPE-001 — Type Registry

| Prefix | Type | Group | Location |
|---|---|---|---|
| PRD | product-requirements-document | normative | `product/prd/` |
| FR | functional-requirement | normative | `requirements/fr/` |
| NFR | non-functional-requirement | normative | `requirements/nfr/` |
| CAP | capability | normative | `architecture/l1/` |
| CMP | component | normative | `architecture/l2/` |
| ADR | architecture-decision | normative | `architecture/adr/` |
| TM | threat-model | normative | `architecture/threat-model/` |
| API | api-contract | normative | `tech-specs/*/api/` |
| TBL | storage-schema | normative | `tech-specs/*/schema/` |
| DDL | storage-schema-ddl | normative | `tech-specs/*/schema/` |
| CON | component-contract | normative | `tech-specs/<CMP-slug>/` |
| BL | baseline | normative | `lifecycle/change-sets/*/baseline/` |
| UXF | ux-flow | normative | `design/ux/` |
| SCR | screen-inventory | normative | `design/ux/` |
| UID | ui-design | normative | `design/ui/` |
| UIS | ui-specification | normative | `design/ui/` |
| TOK | design-token-set | normative | `design/ui/tokens/` |
| DOM | domain-glossary | normative | `domain/` |
| OBS | observability-spec | normative | `observability/` |
| CHG | change-set | normative | `lifecycle/change-sets/` |
| OQ | open-question | normative | `lifecycle/change-sets/*/open-questions/` |
| EPIC | epic | normative | `lifecycle/epics/` |
| TASK | task | normative | `lifecycle/tasks/` |
| STORY | story | normative | `lifecycle/stories/` |
| BUG | bug | normative | `lifecycle/bugs/` |
| REL | release | normative | `lifecycle/releases/` |
| GATE | gate-policy | normative | `policies/gates/` |
| EVAL | evaluation-policy | normative | `policies/eval/` |
| TEST | test-evidence | evidence | `evidence/tests/` (keys may be reserved before files exist) |
| REV | review-record | evidence | `evidence/reviews/*.yaml` |
| RCPT | review-receipt | evidence | `evidence/reviews/` |
| FIND | finding | evidence | `evidence/findings/` |
| DEC | human-review-limit-disposition | evidence | `evidence/decisions/` |
| approval | approval-record | evidence | `evidence/approvals/` |
| CR | change-request | evidence | `evidence/requests/` |
| CTX | context-snapshot | evidence | `evidence/context/` |
| PLAN | implementation-plan | evidence | `evidence/plans/` |
| DIARY | implementation-diary | evidence | `evidence/diaries/` |
| REG-TYPE | type-registry | normative | `registry/REG-TYPE-*.md` |
| REG-OWNER | ownership-registry | normative | `registry/REG-OWNER-*.md` |
| REG-REPO | repository-registry | normative | `registry/REG-REPO-*.md` |
| REG-ADAPTER | adapter-registry | normative | `registry/REG-ADAPTER-*.md` |
| CSV | change-set-view | derived | `generated/change-set-views/` |
| AVW | architecture-view | derived | `generated/architecture-views/` |
| LCV | contract-view | derived | `generated/contract-views/` |
| UIM | ui-mock | derived | `generated/ui-mocks/` |
| DGM | diagram-view | derived | `generated/diagrams/` |
| TRC | traceability-record | derived | `generated/traceability/` |
| RVP | review-package | derived | `reviewer/packages/` (không normative) |

## Evidence file conventions

Each CTX, PLAN, DIARY and review has one file named after its artifact key.
CTX and reviews use pure YAML; PLAN and DIARY use Markdown with YAML frontmatter.
Revision numbers and historical execution records are retained inside the canonical
file in revision_history or dated execution sections, without a filename suffix.
Mỗi Change Set giữ baseline của chính nó dưới `baseline/`. `BL-CHG-RKG-2026-001.yaml`
là baseline candidate của Change Set MVP. Các baseline sau (`BL-CHG-RKG-2026-002`
đến `008`) là file riêng, append-only theo revision. `CHG-RKG-2026-009` đến
`014` ghi `baseline: not_recorded` và chưa có file baseline.
Plan dates use the referenced Git implementation milestone and commit SHA.
Active Stories require ACs; retired Story 016 reserves its ID and has no current
child. Task 026 is directly under Epic 003.
