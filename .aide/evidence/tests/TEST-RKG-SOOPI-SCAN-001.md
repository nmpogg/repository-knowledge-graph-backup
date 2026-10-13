---
key: TEST-RKG-SOOPI-SCAN-001
type: test-evidence
group: evidence
scope: system
system: SYS-RKG
status: recorded
revision: 1
normative: false
---
# TEST-RKG-SOOPI-SCAN-001

Verification date: 2026-10-01 (Asia/Bangkok).

The running backend reproduced `source_scan_error` on the soopi repository with
its original defaults. A direct workspace manifest scan succeeded, so the failure
was specific to the running backend's traversal. Excluding the three cache
folders `.cache/**`, `.pytest_cache/**`, and `.ruff_cache/**` removed the error.
The individual failing cache folder and underlying OS error were not determined;
the current error contract discards those details.

Persisted those ignores through the frontend Vite API proxy, preserving existing
scan defaults. Repository configuration revision verified: 2. Then submitted an
empty index request through the same proxy used by the UI, so the scan relied
on the persisted defaults rather than request overrides.

Verified job: `job_fd154cee0bd0497aa7b3f5c0a8586b6a`.
Verified snapshot: `snap_1be8e8ea4c2440f09fcdb04728bf50f8`.
Result: `succeeded_with_warnings`; 65 files considered, 54 parsed, zero file
errors, 397 entities. The repository active snapshot matches this job's snapshot.
Analyzer warnings remain (1309); this change only resolves source traversal.
The browser interaction itself was not automated. No analyzed source was executed.
No application code or normative artifact was changed.

Current-tree SHA-256 (code read during this verification; the running process's
loaded code revision was not independently established):

- `src/rkg/ingestion/local.py`: `24ec853cb34ce6009eb22d00997b847127556d6391190f9193e31a2e1209fbae`
- `src/rkg/jobs/coordinator.py`: `11d0a06ba2d9591e8a92d7fdffe9d3bd468c523c7d3c7aa237395438ef3d4536`
- `frontend/src/client/live/liveClient.ts`: `1bab3b729c104af9f579ee4ddf0b7393c75850af5a260327ba236c82f5a0a281`
- `frontend/src/pages/repositories/RepositoryDetailPage.tsx`: `93bbb35dd8c106e26ac130b3f91b43578d403f4348aabf8404485f306e2c0216`
