---
key: TEST-RKG-FOCUSED-FLOW-003
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
# TEST-RKG-FOCUSED-FLOW-003 - Active soopi snapshot refresh

Verified 2026-10-01 (Asia/Bangkok) through the user's loopback API. Existing
snapshot snap_1421d1b744c64a1484b7bc955a0413f3 was extracted with Python 2.0 and FastAPI 2.1.0,
without SQLAlchemy extraction. Its GET cart flow had three nodes at both depths
two and six, with no data resources. Increasing depth cannot add missing facts.

Authorized re-index job job_03c27374699f47c18c912db1ee9131cb completed succeeded_with_warnings.
New active snapshot: snap_6701dcd7ff9a406685029299fafd83cd. Adapters: Python 2.1, FastAPI 2.1.0,
SQLAlchemy 2.1.0. Confirmed 34 endpoints; GET /api/v1/cart at depth six has 17
nodes and tables carts/categories/product_variants/products/users, not truncated.
The previous snapshot remains readable; no snapshots or conversation pins were
removed. The existing backend was used via its API, with no process replacement.
Explorer's explicit snapshot URL remains pinned until the new snapshot is opened.

Implementation verification remains TEST-RKG-FOCUSED-FLOW-002; this is supplemental
runtime evidence. Base revision:
7b24db7773298fd2c548b76f3cd3ac46ca24cc62.
Current implementation file SHA-256 fingerprints:

| File | SHA-256 |
| --- | --- |
| src/rkg/adapters/python_language.py | 87b5d1bfb523c68a45d1347aed752d0125cbda2470e0411c46060366cf0a70c0 |
| src/rkg/adapters/python_types.py | f80c2b672dc2e2d103c8f2189466a79e4f3c2051beafc7edbb3b8cadac95c2e1 |
| src/rkg/adapters/sqlalchemy_data.py | fb0383a59530c5e7f6b8464937d0a280df153f345ea8f96c752d8bcc37be1e51 |
| src/rkg/graph/traversal.py | 728c4b2cc0cfe2b03853ddfa7e0b640393171ab29ed24f72872ccc846f35adec |
| src/rkg/api/app.py | 22c59065f1af98e8d5c7570f18e6494fe0aaab743e50f474ecd4d912d1fdfd1a |
