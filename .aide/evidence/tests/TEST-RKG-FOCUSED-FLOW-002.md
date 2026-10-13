---
key: TEST-RKG-FOCUSED-FLOW-002
type: test-evidence
group: evidence
scope: system
system: SYS-RKG
status: recorded
revision: 1
normative: false
relations:
  verifies: [TASK-RKG-029, FR-RKG-003, UIS-RKG-001, API-RKG-CORE-v1]
classification: internal
ai_assisted: true
---
# TEST-RKG-FOCUSED-FLOW-002 - Browser-verified flow presentation correction

Verification date: 2026-10-01 (Asia/Bangkok). Branch: feat/focused-flow-graph.
This record supersedes TEST-RKG-FOCUSED-FLOW-001 as current correction evidence;
the prior record is retained unchanged. Base commit: 7b24db7773298fd2c548b76f3cd3ac46ca24cc62.

## Findings and correction

The prior implementation filtered facts but retained a generic layout: shortest-hop
layering put shared tables among callables, ownership parents became disconnected
columns, graphs over twelve edges hid access labels, selection changed the viewport,
and a long horizontal chain shrank the text. The running user's loopback backend
exposed the pre-flow OpenAPI parameters and silently ignored the requested profile.

The renderer now condenses call cycles and layers after all predecessors, using
readable top-to-bottom flow steps with terminal resources last. Skip-row edges route
between nodes; all flow edge labels remain visible. Method names identify their Type.
Ownership becomes optional relative-path breadcrumbs on the same steps, without
separate boxes or semantic expansion. Selecting a step preserves the flow viewport.
Opening an endpoint closes Results, which remains reopenable. Structural roots retain
architecture layout. Request sequencing prevents an older response replacing a newer
selection; errors clear the previous graph. Subgraph responses acknowledge `view`;
the live client rejects an unacknowledged flow response with a translated restart
message. Vietnamese copy was corrected to proper Unicode.

## Automated verification

- Full frontend single-worker suite: 59 passed in 12 files. Includes shortcut-table
  layering, upstream resource layout, cyclic-call determinism, ownership identity/
  position stability, class-qualified method labels and old-backend rejection.
- After adding mock location paths/correcting translations: mock/App focused suite,
  12 passed. Final frontend production build passed.
- Focused backend flow integration: 4 passed; core API integration: 11 passed.
  Existing Starlette/httpx deprecation warning retained. Backend changes in this
  correction only add the profile acknowledgement; extraction was not changed.
- Frontend lint passed with existing React warnings; Ruff and diff checks passed.
- Published AC IDs/order unchanged. Normative revisions: FR-RKG-003 r11,
  UIS-RKG-001 r11, API-RKG-CORE-v1 r14, CHG-RKG-2026-001 r23. Gates remain pending.
  No schema/DDL change; no analyzed source executed.

## Actual browser verification

Headless Microsoft Edge, real React Flow canvas at 1680x1000, actual loopback RKG
API and an isolated static index of local soopi (34 endpoints). Review snapshot:
snap_954367d40e7f47a1a08bfd4120d73819. Existing user database/server were preserved.

- GET /api/v1/cart: 17 flow steps, ending at users/carts/categories/products/
  product_variants. Ownership enabled: 17 location captions, zero file/folder boxes.
- Captured and inspected screenshots of the real rendered flow, with/without
  locations. Long horizontal tiny-text presentation was replaced after inspection.
- Clicking CartRepository.owned preserved the exact viewport transform.
- POST /api/v1/cart/guest reached only carts; PUT /api/v1/categories/{category_id}
  reached only categories.
- Browser simulation of the legacy response contract (absent acknowledgement)
  produced the translated warning and zero rendered graph nodes.
- Screenshot: [flow with relative locations](TEST-RKG-FOCUSED-FLOW-002.png).

The user backend on port 8000 remains the pre-flow process; restart it with the
current code and re-index to apply new extraction there. The separate loopback
preview uses the current backend and isolated review snapshot. This remains static
analysis, not an execution trace; unsupported dynamic dispatch is not fabricated.

## Checked working-tree fingerprints

SHA-256 of checked file bytes. Lifecycle closure metadata and evidence text excluded
from the hash set; screenshot included. Historical approvals/baselines unchanged.

| File | SHA-256 |
| --- | --- |
| .aide/architecture/l2/CMP-RKG-GRAPH.md | af08891bf147d5e532f92e1b5a752b851f5761aedb167dc88bf7cce96e535247 |
| .aide/design/ui/UIS-RKG-001.md | 83046eba5195d96fff88265d37f6be343cf7ca95edac89ad9f375d69d4e3fda4 |
| .aide/lifecycle/change-sets/CHG-RKG-2026-001/change-set.yaml | e7c16dd041335fd4e91e2a392888d314a75b9467b182aceb4deb42df79124b41 |
| .aide/registry/REG-ADAPTER-001.md | 56d230fd4337cde79ea82eb269534f6c73ee4c99ad4e99a1a525609fba9f5f68 |
| .aide/requirements/fr/FR-RKG-002.md | a1a16e4252bcc8ddcbae34d4bf776ef0426cba2b0dc4370b1145b49e34c5e4a5 |
| .aide/requirements/fr/FR-RKG-003.md | 391d5776beaa853b8f0a673e4d383458f1b98500f93c4f672cbe9e7138887ea1 |
| .aide/tech-specs/RKG-TRANSPORT/api/API-RKG-CORE-v1.md | 1caf1701aea691eba77b99cdd26d50df92d4c78310cb8ac73d6206706c943883 |
| frontend/src/client/live/liveClient.test.ts | 77daf9d73a122f5eba23f2dd1f2e969266c38bd9cfecf24de2bfa38e8e3a08bd |
| frontend/src/client/live/liveClient.ts | 1c2603c4a228a7927bac2fd5b08e43aca5b374446663f081a75c01aa7ed1f947 |
| frontend/src/client/live/mapWire.ts | 24fdf4c8b5a02c25f5a944b2b7e9519a26c1dcafa3b63fe845830b695176f305 |
| frontend/src/client/mock/fixtures.ts | fd1ad95a6eba27b56fa4f34473f63bdcfabfdb0bafee7fa46682851a1d8fe567 |
| frontend/src/client/mock/focusedFlow.test.ts | aa6d8d1276f383a773d6c9c90ae0c7272f71d41efecc72329ffe23b7dc4d86d4 |
| frontend/src/client/mock/mockClient.ts | 8f32a4f5310034d6b8070f6241d233e6594324381abf0b480cacc5b0c75e1644 |
| frontend/src/components/graph/KnowledgeGraph.tsx | df92ee51235fe217beffc626f94721f4a8c872c757d488b454aa70878d6bfae8 |
| frontend/src/components/graph/RelationshipEdge.tsx | 9a059f9467e3b0d5bcf24d68d1593f796570ea906563aef21fa251b1fbb6e403 |
| frontend/src/components/graph/RkgEntityNode.tsx | 5aed3c36e5bb1e43d71312959c3cb8a840989530dddc27fe870f6e8081b716e8 |
| frontend/src/components/graph/flowPresentation.test.ts | 4b6def8b63c9810aa15d0ed05d0bd4e55c8f489ae49264c0064941465965ce98 |
| frontend/src/components/graph/flowPresentation.ts | afbfd87d1d1b52a91e99cde13c7699ef0612c8cbc4ede7ece905f01f7474aa42 |
| frontend/src/components/graph/graphLayout.test.ts | d377faa24bec792c76fe3780d968e9ff4ac0766855c81456fa3198d83cf06c73 |
| frontend/src/components/graph/graphLayout.ts | b462645964cae81e9deedc5c6180c2dbe80ce15ae6da8901352a4956892f629e |
| frontend/src/i18n/en.ts | f7d194c373f20533e911ed051c9e1cf44c2a67c7c601f1fcd4c43a7a0a8c696f |
| frontend/src/i18n/vi.ts | b8dde281213592abd5fcffeb0851a203cb24c0dd35e14612c88840eab4a5ddd4 |
| frontend/src/index.css | 24f59bbb978a525e882f8d7e0c2319ace2be76d4e13920e7dc78ba425745fb70 |
| frontend/src/lib/format.ts | 1b08e68cd09819a98c97e0bb54d403c664a9bc531329e5bad02f3857abfa504e |
| frontend/src/lib/presets.ts | d9e1d09e80a0498eba3b5c353f3b37995198fe6d39b8d94ca3304d612ef3e25b |
| frontend/src/pages/explorer/ExplorerPage.test.tsx | 0487b70836114fbe5b9b7954ac77a83c4a78ea4638991da60335c6a1ead0c524 |
| frontend/src/pages/explorer/ExplorerPage.tsx | 64c7f199b49579aa226a2462cba5eabd31823512884e1ea01d3c7f5219abc135 |
| frontend/src/types/api.ts | 28d2552b2db3f848446874a4cdf59bdea7f27b22aa716c41912461fbce6ce81d |
| src/rkg/adapters/python_language.py | 87b5d1bfb523c68a45d1347aed752d0125cbda2470e0411c46060366cf0a70c0 |
| src/rkg/adapters/python_resolution.py | 789971fdf4783df41e45da6574873441b9c4d4f7ac16f348d90e1efe6a13a2d7 |
| src/rkg/adapters/python_types.py | f80c2b672dc2e2d103c8f2189466a79e4f3c2051beafc7edbb3b8cadac95c2e1 |
| src/rkg/adapters/sqlalchemy_data.py | fb0383a59530c5e7f6b8464937d0a280df153f345ea8f96c752d8bcc37be1e51 |
| src/rkg/api/app.py | 22c59065f1af98e8d5c7570f18e6494fe0aaab743e50f474ecd4d912d1fdfd1a |
| src/rkg/graph/context.py | 3cdcbe4e3e38dc347e0c3aba622fda10ee0049198261168fce6980ababf4c839 |
| src/rkg/graph/traversal.py | 728c4b2cc0cfe2b03853ddfa7e0b640393171ab29ed24f72872ccc846f35adec |
| tests/conformance/test_python_resolution.py | aede309c572e5f3f9687b08a07af173be13ecab99a2d4831af832a4ca4a5c9ce |
| tests/conformance/test_sqlalchemy_data.py | 4f7b13f65ee4dce6656f47f22d992bd9a4459ea53e3145c2f6e42b1bf2d6d757 |
| tests/integration/test_focused_flow.py | 97accdc4e7063e738041931bd20f07e7a2080357186961dcb70e1e27b73ee7cf |
| tests/integration/test_index_language_partition.py | e82f478aec959e96617600de20ff8c0bdfb0fe7e9eeb70bf0be8ccc29b44dd1d |
| .aide/evidence/tests/TEST-RKG-FOCUSED-FLOW-002.png | 2187a236b3d6cb8a510ecfdeb7192921555d7f4c0d1c9e3a45a3c576df7c4833 |
