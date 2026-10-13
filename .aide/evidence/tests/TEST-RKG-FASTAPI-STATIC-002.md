---
key: TEST-RKG-FASTAPI-STATIC-002
type: test-evidence
group: evidence
scope: system
system: SYS-RKG
status: recorded
revision: 1
normative: false
relations:
  verifies: [TASK-RKG-028, FR-RKG-002, FR-RKG-003]
classification: internal
ai_assisted: true
---
# TEST-RKG-FASTAPI-STATIC-002 - FastAPI static indexing coverage

Verification date: 2026-10-01 (Asia/Bangkok). User authorized all four diagnosed
corrections: unknown version, app factory, literal router loops and empty route paths.

## Checks executed

- Full backend `.venv/Scripts/python.exe -m pytest -q --tb=short`: 178 passed,
  6 skipped, one existing Starlette/httpx deprecation warning.
- Focused coordinator integration: 5 passed, including snapshot capability state,
  persisted endpoints and unverified-version warning visibility through catalog reads.
- Ruff check src/tests and final formatting: passed. Final formatting changed line
  endings only; Python behavior is unchanged from the full-suite checked revision.
- `git diff --check`: passed. Published AC IDs/order unchanged; gates pending.

## Coverage

FastAPI adapter 2.1.0 opts into extraction for unknown versions while retaining
version_unverified, executed adapter/capabilities and a persisted warning. Known
incompatible versions remain blocked. Other adapters keep strict constraints unless
explicitly opted in; declared-only dependencies do not activate extraction.

Detector and adapter share an AST view for unique local parameterless factories with
one direct app construction and final unconditional return. Finite literal list/tuple
router loops resolve imports without evaluation. Handler identities, original parse
trees and source line evidence are preserved. Empty paths inherit the effective prefix
without adding a slash; empty paths without a prefix are rejected. Checks cover aliases,
local app names, unrelated middleware using local settings, dynamic loops, conditional
returns, reassignment and local shadowing. Raising-source fixtures verify that analyzed
modules are never executed. Unsupported registrations produce diagnostics rather than
guessed links. Imported/parameterized factories remain outside the static profile.

## Soopi verification

A complete coordinator run in an isolated temporary database succeeded with warnings:
34 endpoints, 34 handled_by links, selected app.main:app, version_unverified and one
adapter_version_unverified warning. 65 files considered, 54 parsed, zero file errors.
GET /api/v1/products and POST /api/v1/orders were checked; none of the 34 routes
contains an invented trailing slash.

The loopback backend was stopped. Verified the exact registered source identity,
then re-indexed the current soopi registration through Storage/IndexCoordinator with
its persisted settings. New snapshot activated; previous snapshot still readable.
Backend was not restarted; no interactive browser verification is claimed.

Job: job_228417d7047e4301a136d1ce3cb287c4.
New active snapshot: snap_38dfd7f1ad8f461492f45dfcb7b4607d.
Previous snapshot retained: snap_46895b86a72f45b9adf2d0e0f3c192c3.
Runtime result: succeeded_with_warnings; 34 endpoints, 34 handled_by links,
1319 warnings. Remaining unsupported analyzer patterns are not claimed resolved.

Historical evidence, approvals and baselines remain unchanged. User changes to
.gitignore and staged runtime database tracking were preserved. All four change-set
gates remain pending. This verification is not gate approval. No commit/push performed.

## Current-tree revision

Git base: `5d043b702b0ab82567b75c8da74c5620b7c21444` plus these SHA-256 digests. Task completion metadata is
excluded to avoid a circular evidence link. No runtime binary, absolute host path,
credentials, raw source, configuration values or transcripts are recorded.

| Relative file | SHA-256 |
|---|---|
| `src/rkg/adapters/fastapi_static.py` | `bd8bec650661ef8d65e15de2cdb5cd05eacde387e85109945dfb008b4f1391ed` |
| `src/rkg/adapters/fastapi_framework.py` | `4ab8a95dfbb53526061d3f2db6e28fae498d84b40bc6312e0cbaef4a9f0978a8` |
| `src/rkg/adapters/registry.py` | `f1c93f4cb3c9582934f20aaab7c13bccfeb9b776414752dbbace8d6895c1ea9b` |
| `src/rkg/detection/fastapi.py` | `4f58fe3e0a6453538f8f22e2fa4ed6331af2840f5af3f837d66e2e53e079d5a3` |
| `src/rkg/detection/selection.py` | `c1742ffaeae6d6d8b31aa1140762524430630cc8445951b4f6d7c753af04a79b` |
| `src/rkg/detection/README.md` | `090d740ca5a20a7ca23206ba9e0be1a9ffb68d3452a6ca6dda73dc9f8f50e691` |
| `src/rkg/jobs/coordinator.py` | `4b858a57c48473ebaf9cb8173abce1f91d8c2e673eb0a7f722d61cda6d52b950` |
| `tests/conformance/test_fastapi_framework.py` | `bcb7167473e3642ab5ac3f46700cf888093c9ef71df64bb5379b8a96d820df28` |
| `tests/unit/test_technology_detection.py` | `af4e0fef3add40b31a47a1fb5f3e0ae2f124ef23551e5542bba8b56fab63ff81` |
| `tests/integration/test_index_coordinator.py` | `0c7678a6c9bfb39fe2964c0f83050619eb41012b803d0041b4180b912c483595` |
| `tests/integration/test_index_language_partition.py` | `8d2257fb025e819aeceb884bfcc9bb6b86352e8c3578d87f3ca094b1cdc3846d` |
| `.aide/registry/REG-ADAPTER-001.md` | `641ff34dea1aab60bf2c46c04d8d8600cd542c316f2e1f82c61a63a9bd92b5cf` |
| `.aide/requirements/fr/FR-RKG-002.md` | `580b296a5751675cbe3915b1452736e33056b4dec0f4dab03f1c2572d9169e59` |
| `.aide/tech-specs/RKG-TRANSPORT/api/API-RKG-CORE-v1.md` | `40c45e244a4e41a6f2d78ac9f008feec194ff9018dd5819505e27d52aa2d5957` |
| `.aide/lifecycle/change-sets/CHG-RKG-2026-001/change-set.yaml` | `7a0d9667e10a9892e587e34e0ac7d2f0d39e7b5ef5e87118e6972e232fc755e8` |
