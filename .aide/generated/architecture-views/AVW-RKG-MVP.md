---
key: AVW-RKG-MVP
type: architecture-view
group: derived
status: current
revision: 3
non_normative: true
hand_written: true
derived_from:
  - CAP-RKG-001
  - CAP-RKG-002
  - CAP-RKG-003
  - CMP-RKG-ANALYZER
  - CMP-RKG-GRAPH
  - CMP-RKG-TRANSPORT
  - CMP-RKG-WEB
  - CMP-RKG-CONVERSATION
  - ADR-2026-001
  - ADR-2026-002
  - ADR-2026-003
  - ADR-2026-004
  - ADR-2026-005
  - ADR-2026-006
  - TM-RKG
  - DGM-RKG-L1
  - DGM-RKG-L2
---

> Bản gộp đem ra Architecture Gate. Khi AVW và CAP/CMP/ADR/TM bất đồng,
> **artifact normative thắng**.

# Architecture view — RKG MVP

## L1 capabilities

| CAP | Covers (FR) | Realized by |
|---|---|---|
| `CAP-RKG-001` Repository analysis | `FR-RKG-001`, `FR-RKG-002` | `CMP-RKG-ANALYZER`, transport job kickoff |
| `CAP-RKG-002` Graph exploration | `FR-RKG-001`, `FR-RKG-003`, `FR-RKG-004` | `CMP-RKG-GRAPH`, `CMP-RKG-TRANSPORT`, `CMP-RKG-WEB` |
| `CAP-RKG-003` Grounded conversation | `FR-RKG-005` | `CMP-RKG-CONVERSATION` + graph read + transport + web |

Diagram: `generated/diagrams/DGM-RKG-L1.md`.

## L2 components — handoff summary

```text
Source → CMP-RKG-ANALYZER (FactBatch, no DB write)
       → CMP-RKG-GRAPH (validate/publish/activate/query/context)
       ← CMP-RKG-TRANSPORT (API/CLI, single process/writer)
       ← CMP-RKG-WEB (React/Vite management + Explorer)
       ← CMP-RKG-CONVERSATION (turn/state/provider; persist via GRAPH façade)
```

| CMP | Transaction / concurrency highlights |
|---|---|
| ANALYZER | No DB write; jobs serialized; invalid candidates never published |
| GRAPH | Short tx for publish/activate/delete; pinned readers; single writer |
| TRANSPORT | One process owns Kùzu writer + job coordinator; bounded polling |
| WEB | Mock/live same contract shapes; no authoritative graph copy |
| CONVERSATION | Pending commit before provider call; `(conversation_id, client_request_id)` idempotency |

Diagram: `generated/diagrams/DGM-RKG-L2.md`.

## ADRs selected

| ADR | Decision |
|---|---|
| `ADR-2026-001` | Static AST + evidence-first; LLM only for grounded Q&A |
| `ADR-2026-002` | Kùzu embedded; one writer process; pin snapshot readers |
| `ADR-2026-003` | React + Vite SPA; typed RkgClient mock/live boundary |
| `ADR-2026-004` | Repository 1—N Snapshot; no RepositoryVersion entity |
| `ADR-2026-005` | Versioned language/framework adapter boundary; core does not branch by adapter ID |
| `ADR-2026-006` | Directory from SourceUnit paths; new snapshots do not emit Namespace |

Rejected alternatives and criteria are recorded in each ADR file (not restated here).

## Threat model coverage

`TM-RKG` covers source execution, local path/symlink boundary, secret disclosure,
prompt injection, XSS, snapshot mix-up, cross-repo IDOR, locator disclosure, local
mutation, dependency confusion, and Kùzu workspace corruption — each with a named
verification test id.

## Gate packaging note

Phase is `implementation_verified`. `BL-r2` is the candidate baseline and is not
an approval. Scope, Architecture, UI/UX and Contract gates remain pending.

UI/UX Gate signs `UXF`, `SCR` and `UID`. `UIS-RKG-001` is level-4 UI
specification and is an input of Contract Gate together with `API-RKG-CORE-v1`,
`TBL-RKG-GRAPH` and `DDL-RKG-GRAPH`. Revision 2 of this view said contract
drafts were waiting on a new candidate baseline and did not list `ADR-2026-006`.
