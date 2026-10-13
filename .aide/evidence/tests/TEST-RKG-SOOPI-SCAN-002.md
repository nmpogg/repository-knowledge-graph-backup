---
key: TEST-RKG-SOOPI-SCAN-002
type: test-evidence
group: evidence
scope: system
system: SYS-RKG
status: recorded
revision: 1
normative: false
---
# TEST-RKG-SOOPI-SCAN-002

Verification date: 2026-10-01 (Asia/Bangkok).

## Finding and correction

The current soopi registration had no persisted scan defaults and no active snapshot.
Earlier TEST-RKG-SOOPI-SCAN-001 applies to a previous registration, not this one.
The first API retry using recursive cache patterns still failed. Applying explicit
root-cache excludes to the running backend removed the source scan failure.
The exact OS error and individual cache directory are not available in the error
contract; this evidence does not identify them.

Regression tests additionally demonstrated that the previous matcher did not prune
cache directories matched by recursive `**/folder/**` patterns. It required a child
path before matching, causing traversal of unreadable directories. The matcher now
matches the directory itself at root or nested depth. Link boundary validation still
runs before ignore handling. Core defaults exclude Python/tool caches, preserving
custom operator patterns. README documents the defaults.

## Runtime verification

Updated only current soopi scan defaults through the authenticated loopback API,
preserving other settings. No token, absolute locator or source text is recorded.
The running backend was not restarted. Explicit root cache excludes make this scan
work with its already-loaded matcher; the code fix applies after backend restart.

Job: `job_ba893831d6e64477b30750a5669190f6`.
Snapshot: `snap_46895b86a72f45b9adf2d0e0f3c192c3`.
Repository: `repo_4bf6ffedc1d247bb8d55a9b4764e0728`.

Result: succeeded_with_warnings; 65 files considered, 54 parsed, zero file errors,
364 entities including 12 Directory entities. Active snapshot verified equal to
this job snapshot. Analyzer warnings remain (1309). No analyzed source was executed.
The API path was tested; interactive browser behavior was not automated.

## Current-tree checks

- Focused source/coordinator regressions: 20 passed, 1 skipped.
- Full backend `.venv/Scripts/python.exe -m pytest -q --tb=short`: 168 passed,
  6 skipped, one existing Starlette dependency deprecation warning.
- Ruff on changed Python files: passed.
- `git diff --check`: passed.
- Six new parameterized regression cases simulate PermissionError on root/nested
  cache directories and verify they are never traversed while source files remain.

Prior evidence and approvals remain historical and unchanged. Gates remain pending.

Git base revision: `64739d4e674050f4944baf4aaa609cbcc86acf3b` plus these working-tree SHA-256 digests:

| Relative file | SHA-256 |
|---|---|
| `src/rkg/ingestion/local.py` | `e6c67e568da2e3499970e87236ec3d1b70962ab59ccb2dfdeaa166c03c275ad9` |
| `src/rkg/jobs/coordinator.py` | `34a8c053cf41d5d8a722a2ef70582416d989a895b1dde4d3a01da6f91034a63b` |
| `tests/unit/test_local_source.py` | `a8305acb47f7c9b1c3e83b4a240991c6d116c4f6c2e588a1987fc2d98855e9e6` |
| `README.md` | `82c038ce1b68a979cfc0849813fe9721080a9c92e3e9d483caae6fbe979b5644` |
