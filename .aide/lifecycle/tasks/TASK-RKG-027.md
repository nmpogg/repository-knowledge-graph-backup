---
uid: null
key: TASK-RKG-027
type: task
group: normative
scope: lifecycle
system: SYS-RKG
story: STORY-RKG-017
status: done
review_record: REV-RKG-2026-004
review_record_note: REV-RKG-2026-004 lists this task in its documentation reconciliation. No REV-TASK file exists.
revision: 6
ownership:
  accountable_team: TEAM-RKG
  accountable_role: tech-lead
relations:
  part_of:
  - EPIC-002-TEAM-RKG
  depends_on:
  - TASK-RKG-002
  - TASK-RKG-005
  - TASK-RKG-006
  - TASK-RKG-013
  - TASK-RKG-014
  - TASK-RKG-017
  - TASK-RKG-026
  implements:
  - FR-RKG-001
  - FR-RKG-002
  - FR-RKG-003
classification: internal
ai_assisted: true
implementation_record:
  context: CTX-TASK-RKG-027.yaml
  plan: PLAN-TASK-RKG-027.md
  diary: DIARY-TASK-RKG-027.md
---
# TASK-RKG-027 - Directory entities and Namespace transition

## Current state and authorization

User confirmed implementation on 2026-10-01 after reviewing the documentation.
Implementation is verified on feat/directory-entities. The docs-only check
TEST-RKG-DIRECTORY-DOCS-001 remains historical evidence, not runtime verification.

## Scope after user confirmation

- Update canonical DTOs and adapter contract to v2; reject incompatible registrations.
- Build Directory ancestors in core from manifest-backed SourceUnits, with stable
  relative identities, containment and structural evidence defined by TBL revision 11.
- Remove Namespace from new Python/fixture output, attach top-level symbols to
  SourceUnit, retain module metadata and import/class/call resolution.
- Verify framework/data/messaging adapters against v2 facts without losing resource
  namespace identity. Do not implement Java as part of this task.
- Extend physical CONTAINS through a non-destructive migration. Update DDL to declare
  implemented TBL revision 11 and execute it on the pinned database before approval.
- Update API/CLI/search/traversal/context and frontend Graph/List/Structure/detail
  types to support Directory and preserve reads/citations for old Namespace snapshots.
- Do not automatically re-index user repositories or change their active snapshots.

## Verification

- AC-RKG-002 / TEST-RKG-SOURCE-STRUCTURE: root/nested/empty SourceUnits, duplicate
  directory basenames, source_root paths, ignored/unparsed input, stable IDs and
  unique ownership/containment. Every emitted Directory has a SourceUnit descendant.
- AC-RKG-003 / TEST-RKG-IMPORT-RESOLVE: imports, aliases and relative imports resolve
  without Namespace entities; Directory is never a semantic import target.
- AC-RKG-007 / TEST-RKG-EVIDENCE: structural path provenance is validated against
  the manifest and not displayed as a statement; semantic evidence remains intact.
- AC-RKG-049 / existing file-limit checks: Directory nodes do not count as files.
- AC-RKG-073 / TEST-RKG-UI-STRUCTURE: one selectable identity per Directory;
  Graph/List/Structure selection, path evidence and legacy views work consistently.
- Adapter conformance and non-destructive storage migration checks must verify
  mixed-language structure, old snapshots/relationships/IDs and conversation pins.
- Run appropriate API/CLI/UI regression checks and record current-tree revision/hashes
  in .aide/evidence/ before setting status done. Docs-only evidence is not runtime proof.

## Completion evidence

Current-tree verification is recorded in
[TEST-RKG-DIRECTORY-IMPLEMENTATION-001](../../evidence/tests/TEST-RKG-DIRECTORY-IMPLEMENTATION-001.md),
including the Git base revision and SHA-256 digests of checked code, fixtures and
normative artifacts. Backend: 162 passed, 6 skipped. Frontend: 51 passed; build and
lint completed successfully. Current DDL and migration executed on Kuzu 0.11.3;
legacy snapshot/conversation preservation and migration rollback were verified.

No user repositories were re-indexed, runtime database changed or live server
restarted. Gates remain pending; implementation completion is not gate approval.

## Hồ sơ triển khai

- [Context](../../evidence/context/CTX-TASK-RKG-027.yaml) — commit, scope và hash đối chiếu.
- [Plan](../../evidence/plans/PLAN-TASK-RKG-027.md) — ngày theo Git, file và cách kiểm.
- [Diary](../../evidence/diaries/DIARY-TASK-RKG-027.md) — kết quả, evidence và các correction.
