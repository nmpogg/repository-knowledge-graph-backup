---
key: TEST-RKG-FOCUSED-FLOW-001
type: test-evidence
group: evidence
scope: system
system: SYS-RKG
status: recorded
revision: 1
normative: false
relations:
  verifies: [TASK-RKG-029, FR-RKG-002, FR-RKG-003]
classification: internal
ai_assisted: true
---
# TEST-RKG-FOCUSED-FLOW-001 - Focused entity flow verification

Verification date: 2026-10-01 (Asia/Bangkok). Branch: feat/focused-flow-graph.
User authorized branch creation and implementation. This record identifies the
checked working tree, including uncommitted code and normative artifact revisions.
Lifecycle closure metadata and this evidence file are excluded from the hash set.

## Checks executed

- Full backend `.venv/Scripts/python.exe -m pytest -q --tb=short`: 184 passed,
  6 skipped, one existing Starlette/httpx deprecation warning.
- Full frontend `npm.cmd test -- --maxWorkers=1 --no-file-parallelism`: 54 passed,
  all 11 files, including actual loopback API round trips. Single-worker execution
  avoids resource contention observed while building/indexing in parallel.
- Frontend `npm.cmd run build`: passed. Existing large-bundle warning retained.
- Frontend `npm.cmd run lint`: passed with existing React warnings, zero errors.
- Ruff src/tests and `git diff --check`: passed.
- Published AC IDs/order unchanged; changed normative key/filename/headings aligned.
  SchemaMeta remains 2/TBL revision 11; no schema or DDL change. Gates remain pending.

## Verified behavior

AC-RKG-003/007: Python adapter 2.1 resolves proved local constructor receivers,
self fields, local type annotations, inherited methods and consistent helper
parameters. Conflicting receiver/helper observations remain unresolved with
existing diagnostics. Analysis operates on ASTs; a raising source fixture verifies
that analyzed repository modules are never executed.

AC-RKG-009/073: Endpoint/Callable flows follow handler/call/data/message edges.
Downstream shared resources terminate expansion; structural parents never expand
imports or siblings. Resource roots follow incoming users and upstream callers.
Ownership and dependencies are independently optional, off initially. UI defaults
and API-to-DB preset allow six semantic hops. Architecture neighborhood exploration
remains available, including structural roots. Node/edge/depth budgets, truncation,
deterministic ordering and snapshot isolation remain enforced.

AC-RKG-010: GET subgraph and POST context share view/include_structure/
include_dependencies; exported context matches the selected graph profile.
Existing API clients retain neighborhood defaults; invalid views return 422.

AC-RKG-013/020: SQLAlchemy 2.1.0 supports proved query refinements and explicitly
bound generic repository models, including direct constructor binding. Accesses
are attributed to the concrete caller with call-site and repository-method evidence;
a shared generic method is never linked globally to every caller's table. Positive
read/write fixtures and conflicting generic/constructor negatives passed. Unknown
versions may extract while retaining version_unverified and a warning; known
incompatible versions remain blocked.

## Local soopi verification

An isolated temporary graph was indexed from the local soopi checkout with static
entrypoint detection. Result: succeeded_with_warnings, 34 endpoints. At depth six:

| Endpoint | Flow nodes | Tables reached | Truncated |
| --- | ---: | --- | --- |
| GET /api/v1/cart | 17 | carts, categories, product_variants, products, users | false |
| POST /api/v1/cart/guest | 8 | carts | false |
| PUT /api/v1/categories/{category_id} | 6 | categories | false |

Each graph had only its selected endpoint and no imports/containment. Ownership
added parents without adding callable/endpoint/table nodes outside the semantic
flow. No analyzed source was imported or executed. Temporary data was isolated from
the user's existing snapshots. The existing backend was running on loopback, so its
process/database were preserved. Restart backend and re-index to publish extraction
from this branch; existing snapshots/conversation pins are retained.

## Limits and retained warnings

This is a proved static dependency/access graph, not an execution trace. Dynamic or
ambiguous dispatch and unsupported implicit ORM mutation remain diagnostic gaps.
Automated API/UI checks passed; no interactive browser visual review was performed.
The jsdom graph test emits geometry NaN warnings; browser rendering was not inferred
from that test. React lint and bundle-size warnings remain visible and non-blocking.
Earlier signed approvals, baselines and evidence were not modified.

## Checked working-tree fingerprints

Base commit: 7b24db7773298fd2c548b76f3cd3ac46ca24cc62. SHA-256 of file bytes after verification:

| File | SHA-256 |
| --- | --- |
| .aide/architecture/l2/CMP-RKG-GRAPH.md | af08891bf147d5e532f92e1b5a752b851f5761aedb167dc88bf7cce96e535247 |
| .aide/design/ui/UIS-RKG-001.md | c49bf387e8bd7e216fadf6b2bbcadeea403c62e628968f6c01297e34dcc8c9d8 |
| .aide/lifecycle/change-sets/CHG-RKG-2026-001/change-set.yaml | 72518826c342db706a2e4f3490700a30926fd3bc2def61fd5e987783451c5282 |
| .aide/registry/REG-ADAPTER-001.md | 56d230fd4337cde79ea82eb269534f6c73ee4c99ad4e99a1a525609fba9f5f68 |
| .aide/requirements/fr/FR-RKG-002.md | a1a16e4252bcc8ddcbae34d4bf776ef0426cba2b0dc4370b1145b49e34c5e4a5 |
| .aide/requirements/fr/FR-RKG-003.md | 186839e91b3632c2d26001715d687666dd6082693bfeba41b4af078b510e787d |
| .aide/tech-specs/RKG-TRANSPORT/api/API-RKG-CORE-v1.md | 008504d244a03ee6a17281ae923ce753fc958c226b84142205a785077060dd53 |
| frontend/src/client/live/liveClient.test.ts | bf88d938b1fb7e92c17e10069ba0fa5d5b5942d81efd890d9a433ff1733c523f |
| frontend/src/client/live/liveClient.ts | 228e90cc55e9216e3176564e604c07fd84f96e1a09c38e0c38cce7f57915bfd7 |
| frontend/src/client/mock/fixtures.ts | 6d60e2bbb6f4f3189061c505431c094b80db7a34d9b657e39f7978f8ed23de51 |
| frontend/src/client/mock/focusedFlow.test.ts | aa6d8d1276f383a773d6c9c90ae0c7272f71d41efecc72329ffe23b7dc4d86d4 |
| frontend/src/client/mock/mockClient.ts | 8f32a4f5310034d6b8070f6241d233e6594324381abf0b480cacc5b0c75e1644 |
| frontend/src/i18n/en.ts | 1fbcf80fdc598c7695c73aebbff33bcb19281d72cb11c508483c30a667ff9ebf |
| frontend/src/i18n/vi.ts | 20662d663c0311844ec8f7e1409d39bd74df3d89f83878fc5bc6f614a9ffea5c |
| frontend/src/lib/presets.ts | d9e1d09e80a0498eba3b5c353f3b37995198fe6d39b8d94ca3304d612ef3e25b |
| frontend/src/pages/explorer/ExplorerPage.test.tsx | 0487b70836114fbe5b9b7954ac77a83c4a78ea4638991da60335c6a1ead0c524 |
| frontend/src/pages/explorer/ExplorerPage.tsx | e5aa3b7b76e16a070799c73a47e58fcfd33cba77ace0f2164fff2d5b5b7bdb08 |
| frontend/src/types/api.ts | fddaf875377a4613a6ae63b393782931c2736e859cebce38963cf536bff43cf7 |
| src/rkg/adapters/python_language.py | 87b5d1bfb523c68a45d1347aed752d0125cbda2470e0411c46060366cf0a70c0 |
| src/rkg/adapters/python_resolution.py | 789971fdf4783df41e45da6574873441b9c4d4f7ac16f348d90e1efe6a13a2d7 |
| src/rkg/adapters/python_types.py | f80c2b672dc2e2d103c8f2189466a79e4f3c2051beafc7edbb3b8cadac95c2e1 |
| src/rkg/adapters/sqlalchemy_data.py | fb0383a59530c5e7f6b8464937d0a280df153f345ea8f96c752d8bcc37be1e51 |
| src/rkg/api/app.py | 01800e2c41c365b43c258691550d1d6b6ca7f45561ed0528791b1381645537a2 |
| src/rkg/graph/context.py | 3cdcbe4e3e38dc347e0c3aba622fda10ee0049198261168fce6980ababf4c839 |
| src/rkg/graph/traversal.py | 728c4b2cc0cfe2b03853ddfa7e0b640393171ab29ed24f72872ccc846f35adec |
| tests/conformance/test_python_resolution.py | aede309c572e5f3f9687b08a07af173be13ecab99a2d4831af832a4ca4a5c9ce |
| tests/conformance/test_sqlalchemy_data.py | 4f7b13f65ee4dce6656f47f22d992bd9a4459ea53e3145c2f6e42b1bf2d6d757 |
| tests/integration/test_focused_flow.py | 8e7497f011ba5468159a9d8c5ed12fcbc1c69f46b2b4dda0a9ad47ab68cb65fc |
| tests/integration/test_index_language_partition.py | e82f478aec959e96617600de20ff8c0bdfb0fe7e9eeb70bf0be8ccc29b44dd1d |
