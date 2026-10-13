---
key: TEST-RKG-AIOKAFKA-ADAPTER-001
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-011
captured_at: 2026-09-25
code_revision: 66680533506fa6b3ab4812ac1ed4a59c8f89a44a
artifacts:
  - { key: TASK-RKG-011, revision: 5 }
  - { key: FR-RKG-002, revision: 8 }
  - { key: REG-ADAPTER-001, revision: 5 }
  - { key: NFR-RKG-EXT-001, revision: 3 }
---

# TEST-RKG-AIOKAFKA-ADAPTER-001

Current-tree verification. The checked implementation is the working tree on
top of the base revision above; file hashes are in `DIARY-TASK-RKG-011`.

| Check | Result |
| --- | --- |
| `pytest tests/conformance/test_aiokafka_messaging.py -q` | 5 passed |
| `pytest -q` | 94 passed, 1 skipped |
| `ruff check src tests` | All checks passed |
| `git diff --check HEAD` | No whitespace errors |
| Shared `run_framework_conformance` | 100% in every focused fixture |

| Contract ID | Focused evidence |
| --- | --- |
| AC-RKG-015 / `TEST-RKG-EVENT` | Literal topics, imported module constants and `send` / `send_and_wait` / `send_batch` / constructor topics / `subscribe` connect the callable to one MessageChannel per topic name. Namespace stays empty. The same name used by a publisher and a consumer is one channel. A receiver that is not uniquely resolved, including a `self` or `cls` client assigned more than once, emits `aiokafka_topic_unresolved` and no edge. Dynamic names, f-strings, function locals and `pattern` subscriptions, including a static topic list paired with `pattern`, do the same. A module-level call emits `aiokafka_topic_unscoped` and no edge |
| NFR-RKG-EXT-001 / `TEST-RKG-ADAPTER-CONFORMANCE` | Messaging contract and deterministic output pass the shared conformance runner. A compatible lock selects `rkg.aiokafka` without an application entrypoint. A 1.0 lock stays `unsupported_version` |

The skipped suite case is the pre-existing Windows symlink test. Payload values
are not copied into facts. Job publication remains part of TASK-RKG-015.
