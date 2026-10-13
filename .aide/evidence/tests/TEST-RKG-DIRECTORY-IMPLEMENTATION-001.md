---
uid:
key: TEST-RKG-DIRECTORY-IMPLEMENTATION-001
type: test-evidence
group: evidence
scope: system
system: SYS-RKG
status: recorded
revision: 1
normative: false
relations:
  verifies: [TASK-RKG-027, FR-RKG-001, FR-RKG-002, FR-RKG-003, ADR-2026-006]
classification: internal
ai_assisted: true
---
# TEST-RKG-DIRECTORY-IMPLEMENTATION-001 - Directory implementation verification

Verification date: 2026-10-01 (Asia/Bangkok). Branch: feat/directory-entities.
User authorized implementation after the documentation review.

## Executed verification

| Command (repository-relative working directory) | Result |
|---|---|
| `.venv/Scripts/python.exe -m pytest -q --tb=short` (root) | 162 passed, 6 skipped; 1 dependency deprecation warning |
| `.venv/Scripts/python.exe -m ruff check src tests` (root) | Passed |
| `npm.cmd test -- --reporter=dot --maxWorkers=1` (frontend) | 51 passed across 10 files |
| `npm.cmd run build` (frontend) | TypeScript and production build passed |
| `npm.cmd run lint` (frontend) | Exit 0; React lint warnings remain |
| `git diff --check` (root) | Passed |

Skipped backend checks depend on optional external/pilot/symlink conditions; they
are not counted as verified. Frontend graph fixture emitted NaN SVG warnings and
Vite reported a bundle size warning; neither failed the checks. No interactive
browser inspection is claimed.

## Verified behavior and coverage

- Core derives unique Directory ancestors from manifest-backed SourceUnits without
  reading analyzed source a second time. Root files, empty files, duplicate folder
  basenames, source_root, ignored/unparsed inputs and missing-manifest paths are tested.
- Stable Directory identities and immediate Repository/Directory containment are
  validated. Structural evidence uses a deterministic descendant path witness and
  filesystem provenance; API/context/UI do not present its marker as syntax lines.
- Adapter contract v2 rejects v1 registrations and adapter-emitted Directory/Namespace
  facts. Python keeps module metadata and symbol/import resolution while new snapshots
  emit no Namespace. Existing deep-adapter regression and conformance checks pass.
- Two language adapters sharing a folder produce one core Directory. The second is
  a synthetic test adapter; no Java adapter was implemented.
- Current DDL declares TBL-RKG-GRAPH revision 11 and executes on pinned Kuzu 0.11.3.
  SchemaMeta is 2. Integration tests run fresh schema bootstrap and v1-to-v2 migration,
  retaining legacy snapshot schema, entity/edge IDs, evidence and conversation pins.
  Migration is idempotent; injected failure rolls back before a successful retry.
- Loopback API integration verifies Directory search/detail/graph and legacy Namespace
  reads. Existing CLI/API/context/publication/storage regressions pass.
- Frontend maps Directory and legacy Namespace, retains module/package metadata,
  selects canonical folder/file IDs, displays __init__.py as a SourceUnit in new
  snapshots and preserves pathless resource identities on folder-name collisions.

## Scope and lifecycle limits

Tests used isolated temporary databases. User runtime databases, active snapshots
and repositories were not re-indexed or modified. The running application was not
restarted. Repository source was parsed, not executed.

All four change-set gates remain pending. This evidence records implementation
checks, not gate approval. Historical approvals, baselines and prior evidence remain
unchanged. TASK-RKG-027 may be completed on this runtime verification; its final
status metadata is excluded from the digest set to avoid a circular evidence link.

## Current-tree revision and SHA-256

Git base revision: `64739d4e674050f4944baf4aaa609cbcc86acf3b` plus the following working-tree file digests.
These identify the checked implementation, fixtures and normative artifact revisions;
no generated build output, runtime data or absolute host paths are included.

| Relative file | SHA-256 |
|---|---|
| `.aide/architecture/adr/ADR-2026-006.md` | `c2854f5a2883f3dc090d5c0dcabe6912afc70216236a617dfc747cbf1c190c35` |
| `.aide/architecture/l2/CMP-RKG-GRAPH.md` | `81b6f30e95575a2712ac82719f5ae67c2a982bdf50c854daa1d97948af1ceba7` |
| `.aide/design/ui/UIS-RKG-001.md` | `198ee398557a40092feb2e1d87257b8ff3a77325a52a94ada0a454c5c4eb50cf` |
| `.aide/lifecycle/change-sets/CHG-RKG-2026-001/change-set.yaml` | `1a77721fe5d61d566466bb85c507823b3de687afc7764bc56f8a28a920a68a29` |
| `.aide/policies/gates/GATE-RKG-CONTRACT.md` | `c066627d348f1f196349b238ad1b85c03ce886076645892dd93e7725766f14e4` |
| `.aide/product/prd/PRD-RKG.md` | `7b43056b0229ae28d898e53a3e4d869f6ff97a1c846130a6921269371a117a94` |
| `.aide/registry/REG-ADAPTER-001.md` | `8675ac4daff2c2c60dbe681bd377dda4fe670a978ee223a597b8f99b05a1bc5f` |
| `.aide/requirements/fr/FR-RKG-002.md` | `d8b36a135a8632543e39815696e4b7b46acf94aea39d2d52e03f34edc266c1bc` |
| `.aide/requirements/fr/FR-RKG-003.md` | `8d4bd9ffde99804a65fc7e4ce9e08c3cbd18c4fafaee9befd8d50c2683e7637c` |
| `.aide/tech-specs/RKG-GRAPH/schema/DDL-RKG-GRAPH.cypher` | `19bd84f39a1e10993cdaa74cc56e993f958b6ae25a429ac444157f053d988008` |
| `.aide/tech-specs/RKG-GRAPH/schema/TBL-RKG-GRAPH.md` | `f0ce5b167d43692c5cb2ce4eddf3c935a6740898358eac9fa1db9b64c18b8a50` |
| `.aide/tech-specs/RKG-TRANSPORT/api/API-RKG-CORE-v1.md` | `e1f8a0c67354eb355ac203fcc5bc193f951f0f94743fc4515167699f83f05db8` |
| `frontend/src/client/live/liveRoundtrip.test.ts` | `9415496f1aca05b7d4bb0ce4bb39fd192867ce915b2621c2768afdc8592104c4` |
| `frontend/src/client/live/mapWire.test.ts` | `cf4d901719a12c670c41823f57d6f979d7e43a4edfa77885ba2988e38a2bf7b7` |
| `frontend/src/client/live/mapWire.ts` | `198b825e895b0d7ef8fe6ab204de45a9529e82744befdf1a4328bb82390f0094` |
| `frontend/src/i18n/en.ts` | `0388972f9867bc585894fe828b19f4cd9cbeb975fe8f20777697cb30372b3ba8` |
| `frontend/src/i18n/vi.ts` | `e5756590012fb31141a5d81b4d27bd059e852b36b0bc3993266ccf938414d22c` |
| `frontend/src/index.css` | `86ca327557962967bca31347a42079b49c40d4986c7a59915e35715e36569db6` |
| `frontend/src/pages/conversations/ConversationPage.tsx` | `75d9b7324fd7ca76d6a5a6fe55b24024fd11c8d0591d490f684cb24e74d1c206` |
| `frontend/src/pages/explorer/ExplorerPage.tsx` | `1ccdae6afd27b6dcebe3c959e91da79b4d9d2182193b380534dbd214623a5184` |
| `frontend/src/pages/explorer/SnapshotStructure.test.tsx` | `cac3650cb9135bd9d38e6347f51d31fdfd6fb43717469cc17f8a8e1298e69c1b` |
| `frontend/src/pages/explorer/SnapshotStructure.tsx` | `8f5247df0d95b606d9b05292add32e640580af3038dd4700e5d3a603cf4ab784` |
| `frontend/src/pages/explorer/structureTree.test.ts` | `be29fe379d0e01816e63a075a1709a9a9139938233e581dce9d8d6afe11c125a` |
| `frontend/src/pages/explorer/structureTree.ts` | `9c140a38c1a93e5ee25f127dd81575e2115e2b9002be2939dbea1492dd44e8fd` |
| `frontend/src/types/api.ts` | `745f7abd4ec6f87abd2ff84ccb39dd1189404f0e23657537fdadcba88a9e2b3d` |
| `src/rkg/adapters/aiokafka_messaging.py` | `aa4323dad07489e087ac2649a9ca90276115e9c9532103d4be314b26c61b1b6a` |
| `src/rkg/adapters/conformance.py` | `e52273f6ece40f34a737502afe50641deeaee5c8b9653078028f7259a7dc67b7` |
| `src/rkg/adapters/contracts.py` | `56a4b57ad4f1e0a66a77e166591f43e4f962fdc91274a352e34bfae9f3bb8cac` |
| `src/rkg/adapters/fastapi_framework.py` | `62ceb27cf465650ac3c45b9dffc6888e25eafbbe1e497061351521682fe859b2` |
| `src/rkg/adapters/flask_framework.py` | `210f4e7bff0b7f90dc907aabdb4851f15549a8066b0e45b0580bb39cac097500` |
| `src/rkg/adapters/python_language.py` | `02af6a52c920781cf7b8763ef6d7f619b14c1b4cef5a8e414e6d904c8add4039` |
| `src/rkg/adapters/sqlalchemy_data.py` | `c3cfedc1d672aa4b2854f8ad5672d2998592ba77c36dd0f5aaa13a46ee0647bb` |
| `src/rkg/api/app.py` | `ba9c3a59b79778feea8e21a779075b066039f147ed6acdfa7b72d4347d9fec3f` |
| `src/rkg/api/catalog.py` | `3dfd3669681392631021bd4eed8e5ac426bec65482384f83a534d4bd3323d766` |
| `src/rkg/api/serialize.py` | `5e57997eceb6d67a3e113687488fbb8c4a6bde3e16315130afa428293da9e52f` |
| `src/rkg/domain/context.py` | `93fb2e41ddab7220df8ff7022c5336ba346439747ed321d98f4380a27e52d890` |
| `src/rkg/domain/models.py` | `5ecf9132d533906aecd881818b91b1735f6b3d39fa5fcc50889be0ce11943a36` |
| `src/rkg/domain/validation.py` | `efa1d30dbd02ce49a4bf3c97046a7a52fb8d688920c3f74176fd6ee417645e71` |
| `src/rkg/graph/publish.py` | `ab0ae10bf452fcb652a50622d7136d6bd44371bb2d20280bffd277577c12c728` |
| `src/rkg/jobs/coordinator.py` | `efe078f2c102a81b58dc170ef051d39ec4056a98ca757e5d2765843aa3f9785c` |
| `src/rkg/jobs/structure.py` | `0972d05ee48e353768817686aeef081eb62bb1d2561431b64e98638799e09dfe` |
| `src/rkg/storage/_util.py` | `bbc90985b1fce6ec6cf08e21143ff7ba8c406138e8094570711a3eacdea8581d` |
| `src/rkg/storage/migrate.py` | `89b7d91bc6dec1c6c8b91b08aa4878222c99ae952f1ce5ef6beda9cc4aa28adc` |
| `tests/fixtures/domain/source_structure.json` | `5430346837326cb1297a33c865c3332b3841f65e26ebde29379fd17e01719b7c` |
| `tests/fixtures/storage/ddl_v1.cypher` | `789127c880117c9d94cc405cf20f1a68a3e9622a8cbbed1aefb1eadea321dc88` |
| `tests/integration/test_directory_entities.py` | `e6059c40ce7b5a35414b822268ceb7bd7fe4808d396dc0a17715a5dbd54e0ddb` |
| `tests/integration/test_index_coordinator.py` | `189a55d3b3622d98a61007f02b16879c135b43c2db7d9293386f6e9179521903` |
| `tests/integration/test_index_language_partition.py` | `2c5ff8b92dd5d872b558fec062d5922faf72118d02c6b55572181f4702b86caa` |
| `tests/unit/test_adapter_registry.py` | `10f3dd43f3306d8dd22b3f6cad08a08221b59d72864bdf502e4ebeb43de1f8a0` |
| `tests/unit/test_directory_structure.py` | `7c31fd37ed647c5b081d30f5c54691f94993e969220014810d86f2ba87b13080` |
