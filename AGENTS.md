# Repository Knowledge Graph — operating rules

## Authority

1. Normative artifacts in `.aide/` are authoritative for product, requirement,
   architecture, contract, design and lifecycle state.
2. Product docs under `docs/` (SPEC/ARCHITECTURE/TASK/…) were retired; do not
   treat missing product `docs/` as a second source of truth. Only
   `docs/reference/agentic-sdlc/` remains as non-normative process reference.
3. Files in `.aide/generated/` and `.aide/reviewer/` are non-normative unless their
   frontmatter explicitly says otherwise.

## Delivery workflow

- Use task frontmatter in `.aide/lifecycle/tasks/` as the official task status.
- Valid task statuses are `todo`, `in_progress`, `blocked` and `done`.
- Do not mark a task `done` without current-tree verification and evidence under
  `.aide/evidence/` that identifies the artifact/code revision checked.
- Historical approval, diary and baseline records are append-only evidence. Correct
  current state with a new revision, finding, approval or baseline; do not rewrite a
  signed historical record.
- A gate is `pending` whenever a signed normative artifact changes revision or hash.

## Traceability and contracts

- Artifact `key`, filename and primary heading must agree.
- Published FR/AC IDs are stable. Retired IDs are not reused and must not be referenced
  by current tasks unless a current artifact defines them.
- Keep FR↔NFR links symmetric and keep task `implements`/AC verification references
  aligned with current consolidated FRs.
- `TBL-RKG-GRAPH.md` is the semantic schema source; physical DDL must declare which
  TBL revision it implements and must be executed before Contract Gate approval.

## Safety and scope

- RKG is local-first, loopback-only and must not execute analyzed repository source.
- Do not expose absolute host paths, credentials, raw source, config values or
  conversation transcripts in logs or generated evidence.
- Preserve user changes and avoid destructive Git/filesystem operations unless the
  exact target and intent are explicit.
