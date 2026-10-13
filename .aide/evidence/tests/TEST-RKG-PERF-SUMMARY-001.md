---
key: TEST-RKG-PERF-SUMMARY-001
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-022
captured_at: 2026-09-28
captured_against:
  base_commit: adcf43816acefc63d615f2c9f90cda18dbea054d
  pilot_tree_sha256: 7acca861c59558ded14fc9aade5cebe35e9cb627c3d803331990d404371dda2c
---

# TEST-RKG-PERF-SUMMARY-001 — Pilot benchmark

The raw reports `TEST-RKG-PERF-001.json` and revisions `-r2` through `-r4`
contain all 100 sequential latencies per endpoint after five warm-ups.
Queries used an in-process FastAPI TestClient. Context used the contract's
maximum depth 6, 200 nodes, 400 edges and 50,000 characters. The host was
Windows AMD64, 4 logical CPUs, 7.84 GiB physical RAM, Python 3.12.5 and
Kuzu 0.11.3. Physical core count was not verified, so reference-host
eligibility under NFR-RKG-PERF-001 is unconfirmed.

| Run | Full scan, s | Search p95, ms | Subgraph p95, ms | Context p95, ms | Scan peak working set, MiB |
| --- | ---: | ---: | ---: | ---: | ---: |
| Initial | 3.329 | 52.616 | 331.211 | 2082.014 | unavailable |
| r2 | 3.031 | 37.627 | 462.074 | 417.154 | invalid capture |
| r3 | 2.797 | 38.562 | 253.375 | 332.075 | 399.54 |
| r4 | 3.078 | 41.549 | 398.144 | 989.377 | 399.78 |

After the initial failure, context character-budget trimming was changed
from repeated serialization after each removal to a deterministic binary
search over removal prefixes. The returned JSON matched the previous
implementation on the pilot at four character budgets, and existing graph
read tests passed. The r2 RAM field was measured after queries, so it is
invalid as scan peak; r3 and r4 corrected the capture point. Query-process
peak after scan reached 1551.91 MiB in r3 and 1091.68 MiB in r4; this is
reported separately from analyzer scan peak.

Full-scan time and measured scan RAM meet their thresholds on this host.
Search and subgraph p95 were below 500 ms in all runs. Context p95 varied
widely and **failed** the <500 ms threshold in the initial and r4 runs.
NFR-RKG-PERF-001 is not demonstrated reliably. A qualifying reference host
and a stable context result are required for acceptance. The pilot is much
smaller than the 500-file/50,000-SLOC upper bound, so these measurements do
not establish performance at that size.
