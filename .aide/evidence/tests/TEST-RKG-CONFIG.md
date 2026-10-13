---
key: TEST-RKG-CONFIG
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-012
captured_at: 2026-09-25
base_commit: d5bb973059bd4cac078a76c29bad8929f262efd2
artifacts:
  - { key: TASK-RKG-012, revision: 3 }
  - { key: FR-RKG-002, revision: 8 }
---

# TEST-RKG-CONFIG

Current-tree verification on Python 3.12.14. File hashes are in
`DIARY-TASK-RKG-012`.

| Check | Result |
| --- | --- |
| `pytest tests/conformance/test_python_config.py tests/integration/test_config_http_publish.py tests/conformance/test_python_resolution.py tests/conformance/test_python_metadata.py -q` | 15 passed |
| `pytest -q` | 74 passed, 1 skipped |
| `ruff check src tests` | All checks passed |
| `git diff --check HEAD` | No whitespace errors |

AC-RKG-016: environment keys and explicit settings fields match their users.
Secret sentinels are absent from the fact batch, diagnostic text, published
entity/diagnostic rows, search hits, exported context JSON and the `rkg`
operational log captured during publish. There is no separate report writer;
the scan report checked here is that fact batch and its diagnostics.

AC-RKG-017: `test_direct_bases_and_explicit_abstraction_only` and
`test_local_abc_name_does_not_mark_type_as_abstract` still pass, and the
configuration fixture keeps direct `inherits_from` plus `implements` only for
the explicit abstract base.
