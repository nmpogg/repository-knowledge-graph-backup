---
key: TEST-RKG-PERF-SUMMARY-002
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-022
captured_at: 2026-10-08
captured_against:
  base_commit: da43d34785477bf26651fd0c322e45c18edce579
  pilot_tree_sha256: a094fc7b39def8636e2b73766d80510c4f4b917ea1da5a6e93e22619ef237417
---

# TEST-RKG-PERF-SUMMARY-002 — Pilot benchmark

Raw runs are `TEST-RKG-PERF-002-RUN1.json` and `TEST-RKG-PERF-002-RUN2.json`. Both carry digest `a094fc7b39def8636e2b73766d80510c4f4b917ea1da5a6e93e22619ef237417`. `TEST-RKG-PERF-001.json` is unchanged and is not this measurement.

Each run is an in-process FastAPI TestClient: 5 warm-up requests, then 100 sequential requests. Context uses the contract maximum of depth 6, 200 nodes, 400 edges and 50,000 characters. No LLM timing is mixed into scan or query latency. p95 is the 95th value of the 100 sorted samples. Scan peak RAM is `scan.process_peak_working_set_mib`, taken before the query loop. The post-query peaks, 1560.59 MiB and 1582.83 MiB, are not the scan result.

The host is Windows AMD64, Python 3.12.14, Kuzu 0.11.3, 14 logical CPUs and 15.44 GiB physical RAM. Physical eligibility was checked separately: 14 physical cores and 16,574,767,104 bytes of RAM, which meets the reference host of at least 4 physical cores and 8 GiB.

| Run | Full scan | Search p95 | Subgraph p95 | Context p95 | Scan peak |
| --- | ---: | ---: | ---: | ---: | ---: |
| RUN1 | 1078 ms | 14.293 ms | 71.304 ms | 124.34 ms | 394.18 MiB |
| RUN2 | 1031 ms | 17.721 ms | 91.183 ms | 179.038 ms | 392.09 MiB |
| Threshold | ≤ 60 s | < 500 ms | < 500 ms | < 500 ms | ≤ 1 GB |

Both runs meet every numeric threshold, including context p95. The scan considered 17 files, parsed 16, and reported 308 entities and 524 edges with `succeeded_with_warnings`.

The pilot is 15 Python files and 629 SLOC, under the 500-file and 50,000-SLOC ceiling. These in-threshold numbers are not a full-size acceptance.
