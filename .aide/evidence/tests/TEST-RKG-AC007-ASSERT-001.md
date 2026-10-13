---
key: TEST-RKG-AC007-ASSERT-001
type: test-evidence
group: evidence
scope: system
system: SYS-RKG
revision: 1
captured_at: "2026-10-13"
result: passed
captured_against:
  code_commit: cbdfa3e25acc5b9c246ece0c4f68b7b3a5004f48
  note: Pytest ran on the uncommitted working tree. That commit does not contain the new asserts.
suites:
  - tests/conformance/test_django_framework.py
  - tests/conformance/test_next_framework.py
  - tests/conformance/test_express_framework.py
  - tests/conformance/test_nest_framework.py
  - tests/conformance/test_go_http_framework.py
  - tests/conformance/test_tanstack_router_framework.py
  - tests/conformance/test_vue_router_framework.py
  - tests/conformance/test_flask_framework.py
  - tests/conformance/test_go_stack.py
  - tests/unit/test_http_depends.py
---

# TEST-RKG-AC007-ASSERT-001

39 passed. The new check is `assert_ac_rkg_007`: each edge in the batch shares the snapshot, has a rule id, and at least one evidence location. Nest also asserts two `handled_by` targets ending in `findOne` and `create`.

This record does not cover `AC-RKG-003`, `AC-RKG-015`, `AC-RKG-016`, `AC-RKG-035`, or `AC-RKG-048` where those suites still lack the published given. Sentinel absence is not recorded as `AC-RKG-016`. `AC-RKG-005` stays off `TASK-RKG-055` while `OQ-RKG-008` is open.

Task status stays `in_progress`.
