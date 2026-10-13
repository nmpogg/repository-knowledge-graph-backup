---
key: TEST-RKG-HTTP-INVENTORY
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

# TEST-RKG-HTTP-INVENTORY

Same current-tree run as `TEST-RKG-CONFIG`.

AC-RKG-023 is covered by `test_http_literal_origins_drop_sensitive_url_parts`
and the publish case in `test_published_graph_context_and_log_omit_configuration_values`.
Absolute `requests` / `httpx` literals collapse to one `http_service` per
origin, including case-folded hosts and default port 443. Credential, path,
query and payload sentinels do not appear in the fact batch or published rows.
Variable, concatenated and f-string URLs produce `python_http_unresolved` and
no service. A local module named `requests` does not become an HTTP service.
