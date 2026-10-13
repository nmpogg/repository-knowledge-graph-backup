---
key: TEST-RKG-PILOT-REVIEW-SUMMARY-002
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-022
captured_at: 2026-10-08
captured_against:
  base_commit: da43d34785477bf26651fd0c322e45c18edce579
  pilot_tree_sha256: a094fc7b39def8636e2b73766d80510c4f4b917ea1da5a6e93e22619ef237417
  edge_id_lock_sha256: 57244f67dc1a50901a19141c3dd758302f5cea41adaba4360662b93b987e8b26
  seed: 220026
---

# TEST-RKG-PILOT-REVIEW-SUMMARY-002 — Pilot edge review

This summary records the owner-confirmed review of the current sibling pilot.
`TEST-RKG-PILOT-REVIEW-001.json` stays bound to digest `7acca861c59558ded14fc9aade5cebe35e9cb627c3d803331990d404371dda2c` and is not the sample measured here. The measured tree, sheet, lock and reconciliation share digest `a094fc7b39def8636e2b73766d80510c4f4b917ea1da5a6e93e22619ef237417` and lock `57244f67dc1a50901a19141c3dd758302f5cea41adaba4360662b93b987e8b26`.

The sheet is `TEST-RKG-KPI002-SHEET-003.json`. Sampling is seed 220026, stable edge-id order, then sample. Ten groups stay separate: 30 samples for imports, calls and DI, and 10 samples for each DB, event, config and implements group. That is 160 samples. An independent source review of every locked line agreed with `TEST-RKG-KPI002-X1-003.json`: 160 TP, 0 FP, and no disagreements.

| Group | Population | Sample | TP | FP | Precision | Status |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| imports | 36 | 30 | 30 | 0 | 1.00 | measured |
| calls | 48 | 30 | 30 | 0 | 1.00 | measured |
| di | 48 | 30 | 30 | 0 | 1.00 | measured |
| db_maps_to | 12 | 10 | 10 | 0 | 1.00 | measured |
| db_reads | 12 | 10 | 10 | 0 | 1.00 | measured |
| db_writes | 12 | 10 | 10 | 0 | 1.00 | measured |
| event_publishes | 12 | 10 | 10 | 0 | 1.00 | measured |
| event_consumes | 12 | 10 | 10 | 0 | 1.00 | measured |
| config | 12 | 10 | 10 | 0 | 1.00 | measured |
| implements | 12 | 10 | 10 | 0 | 1.00 | measured |

Precision is `TP / (TP + FP)`. Every measured group is at 1.00, above the 95% publication threshold. No group is N/A or `insufficient_sample`. Scan diagnostics that were not in the sample stay omissions: 109 unresolved imports, 96 unresolved calls, 12 unresolved bases and 12 dynamic routes on the paired benchmark scan. They are not counted as reviewed TP.

The paired scan reported 17 files considered, 16 parsed, 308 entities and 524 edges, status `succeeded_with_warnings`. The pilot corpus itself is 15 Python files and 629 SLOC.
