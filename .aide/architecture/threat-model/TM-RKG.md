---
uid:
key: TM-RKG
type: threat-model
group: normative
scope: system
system: SYS-RKG
status: draft
revision: 8
change_set: CHG-RKG-2026-002
ownership: {accountable_team: TEAM-RKG, accountable_role: architect}
relations: {constrains: [CMP-RKG-ANALYZER, CMP-RKG-GRAPH, CMP-RKG-TRANSPORT, CMP-RKG-WEB, CMP-RKG-CONVERSATION]}
classification: internal
ai_assisted: true
---
# TM-RKG — Threat model

| Threat | Boundary | Control | Verification |
|---|---|---|---|
| Malicious source executes | ingestion/analyzer | Structured parser + metadata allowlist; never import/build/install | `TEST-RKG-SCAN-SAFE`, `TEST-RKG-SYNTAX-DIAGNOSTIC` |
| Path/symlink escape | local source/workspace | canonical root check; no external link traversal | `TEST-RKG-SOURCE-BOUNDARY`, `TEST-RKG-LOCAL-ONBOARDING-E2E` |
| Secret disclosure | graph/report/log/provider | never read `.env`; redact; omit values/payload/query | `TEST-RKG-CONFIG`, `TEST-RKG-CONVERSATION-REDACTION` |
| Prompt injection | repository/model text | bounded instructions; schema; read-only query allowlist | `TEST-RKG-QA-INJECTION` |
| Stored/reflected XSS | UI | render text; sanitize Markdown; no source HTML execution | `TEST-RKG-CONVERSATION-A11Y`, `TEST-RKG-UI-VISUAL-A11Y` |
| Snapshot/history mix-up | storage/conversation | snapshot IDs, pinning, referential validation | `TEST-RKG-REINDEX`, `TEST-RKG-SNAPSHOT-PIN`, `TEST-RKG-SNAPSHOT-RETENTION` |
| Cross-repository IDOR/cascade | API/storage | validate repository ownership before read/mutation; repository-scoped transaction/delete | `TEST-RKG-REPOSITORY-ISOLATION`, `TEST-RKG-REPOSITORY-DELETE-GUARD` |
| Repository locator disclosure or substitution | API/UI/storage | immutable source identity; canonical validation; redact locator/error/log | `TEST-RKG-REPOSITORY-CRUD`, `TEST-RKG-REPOSITORY-UPDATE` |
| Unauthorized local mutation | API | loopback, session token, Origin validation | `TEST-RKG-LOCAL-SESSION`, `TEST-RKG-INDEX-SESSION` |
| Dependency confusion / poisoned package metadata | ingestion/analyzer | metadata chỉ là dữ liệu; không install/import; provenance + local-shadow checks | `TEST-RKG-PKG-INVENTORY`, `TEST-RKG-DETECT-NEG` |
| Kùzu workspace disclosure or concurrent corruption | filesystem/storage | server-owned path, restrictive host permissions, one application worker, atomic publication + backup/migration tests | `TEST-RKG-INDEX-SINGLE-WRITER`, `TEST-RKG-REINDEX`, migration fixture planned by Contract Gate |

## Residual risks

Static analysis can miss dynamic relationships; compromised local account can access
the single-user service; configured external LLM receives only explicitly permitted
bounded context. UI and reports must communicate these limitations.

## Structured conversational explanation risks — CHG-RKG-2026-002

Revision 8 adds controls for ADR-2026-007; it is draft pending exact-hash review.
Existing controls and historical evidence remain applicable only to their pinned
revisions, not proof of this future behavior.

| Threat | Boundary | Required control | Planned verification |
|---|---|---|---|
| Fluent prose adds unsupported meaning despite valid citation | narrative selection/render | Reference-only model structure; backend factual renderer, no free-form answer field; check edge meaning/direction/path | TEST-RKG-CONVERSATIONAL-QA |
| Reversed or disconnected path presented as indirect call | graph→narrative | Root reachability, path continuity, evidence membership, cycle handling, direct/indirect labeling | TEST-RKG-CONVERSATIONAL-QA |
| Endpoint/handler alias silently chooses wrong subject | lookup | Exact method/path; Endpoint intent restriction; explicit clarification for collisions | TEST-RKG-CONVERSATIONAL-QA |
| Ordinal selection or greeting loses pending intent | conversation state | Persist redacted original intent/candidate order atomically; preserve focus on greeting/provider failure | TEST-RKG-CONVERSATIONAL-QA |
| Citation opens unrelated entity evidence | answer→UI | Resolve exact evidence_id in pinned snapshot; unavailable if missing, never substitute evidence | TEST-RKG-CONVERSATIONAL-UI |
| Reload conceals truncated/unknown context | storage→UI | Persist limitation state; absent legacy metadata is unknown; no false completeness claim | TEST-RKG-CONVERSATIONAL-UI |

Model output remains untrusted and cannot authorize tools/queries or create graph
facts. No new provider data class is allowed: bounded redacted question/history,
identities and supported facts only; never raw source/config/transcripts in evidence.
