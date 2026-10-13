---
key: TEST-RKG-AC-NFR-RERUN-001-r4
type: test-evidence
group: evidence
system: SYS-RKG
status: recorded
revision: 4
captured_at: 2026-10-08
captured_against:
  code_commit: 3d94500
  product_commit: 6f880eb41f607189c5f02b1bca304a75ada91664
  prior: TEST-RKG-AC-NFR-RERUN-001-r3
---

# TEST-RKG-AC-NFR-RERUN-001-r4 — non-OpenRouter slice

Append-only. Does not edit earlier test evidence. Does not mark a story, task,
epic, or gate done. Does not sign an approval. OpenRouter live tests were not
started. Every item keeps exactly one status. Items not listed below keep the
status in `TEST-RKG-AC-NFR-RERUN-001-r3`.

## Command

`uv run pytest` on `tests/unit/test_local_source.py`,
`tests/unit/test_directory_structure.py`,
`tests/conformance/test_vue_language.py::test_syntax_error_is_isolated_with_relative_path`,
`tests/conformance/test_typescript_language.py::test_syntax_error_is_isolated_with_relative_path`,
`tests/conformance/test_python_resolution.py`,
`tests/integration/test_core_api.py::test_repository_crud_redacts_paths_and_guards_lifecycle`,
`tests/conformance/test_flask_framework.py`, and
`tests/conformance/test_adapter_conformance.py`.

Result: 40 passed, 1 skipped, 0 failed. The skip is
`test_symlink_escape_is_rejected_without_reading_target`: this host cannot
create a symlink. `test_link_escape_branch_is_checked_without_host_symlink_privilege`
passed and raises `source_link_escape`. Analyzed-repository source was not
executed. The pilot benchmark was not started.

## Status changes

| id | validated_by | evidence | rerun |
| --- | --- | --- | --- |
| AC-RKG-001 | TEST-RKG-SCAN-SAFE | tests/unit/test_local_source.py | passed |
| AC-RKG-051 | TEST-RKG-SOURCE-BOUNDARY | tests/unit/test_local_source.py; tests/integration/test_core_api.py | passed |
| NFR-RKG-SEC-001#3 | normative item 3 local source boundary | tests/unit/test_local_source.py; tests/integration/test_core_api.py | passed |

AC-RKG-001 passed because `test_safe_source_with_shell_metacharacters_is_data_only`
builds the manifest from a module that would write a marker if imported, and
the marker is absent. `src/rkg` has no import or process execution of analyzed
source.

AC-RKG-051 and NFR-RKG-SEC-001#3 passed because registration rejects a path
outside the allowlist with `source_outside_allowed_roots`, the error text does
not contain the host path, and the link-escape branch returns
`source_link_escape`.

## Still not_run after this command

These tests passed and still do not close the AC:

- Directory structure tests do not compare a golden JSON of nested lexical scopes, so AC-RKG-002 stays `not_run`.
- Vue and TypeScript syntax isolation passed. Java and Go still have no matching syntax-diagnostic assert, so AC-RKG-035 stays `not_run`.
- Python import resolution passed. Java still does not assert import edges, so AC-RKG-003 stays `not_run`.
- Flask `run_framework_conformance` reported `pass_rate` 1.0 on its shared cases and every capability stayed `DETECTED_ONLY`. That figure is not a TASK-RKG-042..047 conformance `pass_rate` of 100%. NFR-RKG-EXT-001 acceptance item 3 stays `not_run`.

OpenRouter items stay `not_run`: AC-RKG-024, AC-RKG-028, AC-RKG-063, and
NFR-RKG-REL-001#11. The pilot corpus is still absent, so the six
NFR-RKG-PERF-001 rows and AC-RKG-039, AC-RKG-037, and AC-RKG-062 stay
`not_run`.

## Matrix counts

119 items. `passed` 65. `failed` 0. `not_run` 54.
