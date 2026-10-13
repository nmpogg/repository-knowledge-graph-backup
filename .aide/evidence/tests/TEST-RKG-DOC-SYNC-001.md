---
key: TEST-RKG-DOC-SYNC-001
type: test-evidence
group: evidence
system: SYS-RKG
captured_at: '2026-10-09'
hash_artifact: not_run
captured_against:
  code_tree: 2033a60f0c476358fa52e7d37ce5a1d59db501d7
  artifacts:
  - { key: REG-ADAPTER-001, revision: 18 }
  - { key: CHG-RKG-2026-015, revision: 1 }
  - { key: CHG-RKG-2026-016, revision: 1 }
  - { key: CHG-RKG-2026-017, revision: 1 }
  - { key: CHG-RKG-2026-018, revision: 1 }
  - { key: CHG-RKG-2026-019, revision: 1 }
  - { key: CHG-RKG-2026-020, revision: 1 }
  - { key: CHG-RKG-2026-021, revision: 1 }
  - { key: CHG-RKG-2026-022, revision: 1 }
---

# TEST-RKG-DOC-SYNC-001

Đối chiếu `builtin_adapters()` trên cây làm việc với bảng MVP của
REG-ADAPTER-001 revision 18, rồi với CR/CHG/task vừa backfill.
`code_tree` là `git rev-parse HEAD`. Một số module adapter có trên cây làm việc
và không có trong commit đó. `hash-artifact` không có trong repo này
(`not_run`). Không chạy pytest trong lát này.

`rkg.conformance.fixture` không nằm trong `builtin_adapters()` và không còn là
dòng bảng MVP. Bảy id mới và các id cũ trong bảng dưới khớp tập
`builtin_adapters()`.

Census oracle của id mới là `tests/evaluation/fixtures/` cùng
`tests/evaluation/expected_*.json`. Không có bản sao `repo-test/` của bảy
fixture đó trên cây này. Bản sao như vậy, nếu có sau này, không phải oracle
của census.

| Adapter ID | Builtins | Dòng MVP | CR | CHG | Task | Oracle path |
|---|---|---|---|---|---|---|
| `rkg.python` | yes | yes | no dedicated CR | CHG-RKG-2026-001 qua EPIC-002 | TASK-RKG-005, TASK-RKG-006, TASK-RKG-012 | no `expected_*.json` for this id |
| `rkg.fastapi` | yes | yes | no dedicated CR | CHG-RKG-2026-001 qua EPIC-002 | TASK-RKG-009 | no `expected_*.json` for this id |
| `rkg.sqlalchemy` | yes | yes | no dedicated CR | CHG-RKG-2026-001 qua EPIC-002 | TASK-RKG-010 | no `expected_*.json` for this id |
| `rkg.aiokafka` | yes | yes | no dedicated CR | CHG-RKG-2026-001 qua EPIC-002 | TASK-RKG-011 | no `expected_*.json` for this id |
| `rkg.flask` | yes | yes | CR-RKG-029 | CHG-RKG-2026-014 | TASK-RKG-047 | no census `expected_*.json`; conformance `tests/conformance/test_flask_framework.py` |
| `rkg.typescript` | yes | yes | CR-RKG-024 | CHG-RKG-2026-009 | TASK-RKG-042 | census opens `repo-test/rkg-fixture-react-ts`; `tests/evaluation/expected_react_ts.json` |
| `rkg.react-router` | yes | yes | CR-RKG-024 | CHG-RKG-2026-009 | TASK-RKG-042 | census opens `repo-test/rkg-fixture-react-ts`; `tests/evaluation/expected_react_ts.json` |
| `rkg.bullmq` | yes | yes | CR-RKG-026 | CHG-RKG-2026-011 | TASK-RKG-044 | census opens `repo-test/rkg-fixture-bullmq-worker`; `tests/evaluation/expected_bullmq.json` |
| `rkg.vue` | yes | yes | CR-RKG-025 | CHG-RKG-2026-010 | TASK-RKG-043 | census opens `repo-test/rkg-fixture-nuxt4`; `tests/evaluation/expected_nuxt.json` |
| `rkg.nuxt` | yes | yes | CR-RKG-025 | CHG-RKG-2026-010 | TASK-RKG-043 | census opens `repo-test/rkg-fixture-nuxt4`; `tests/evaluation/expected_nuxt.json` |
| `rkg.java` | yes | yes | CR-RKG-027 | CHG-RKG-2026-012 | TASK-RKG-045 | census opens `repo-test/rkg-fixture-spring-orders`; `tests/evaluation/expected_spring.json` |
| `rkg.spring` | yes | yes | CR-RKG-027 | CHG-RKG-2026-012 | TASK-RKG-045 | census opens `repo-test/rkg-fixture-spring-orders`; `tests/evaluation/expected_spring.json` |
| `rkg.jpa` | yes | yes | CR-RKG-027 | CHG-RKG-2026-012 | TASK-RKG-045 | census opens `repo-test/rkg-fixture-spring-orders`; `tests/evaluation/expected_spring.json` |
| `rkg.spring-kafka` | yes | yes | CR-RKG-027 | CHG-RKG-2026-012 | TASK-RKG-045 | census opens `repo-test/rkg-fixture-spring-orders`; `tests/evaluation/expected_spring.json` |
| `rkg.go` | yes | yes | CR-RKG-028 | CHG-RKG-2026-013 | TASK-RKG-046 | census opens `repo-test/rkg-fixture-go-event-worker`; `tests/evaluation/expected_go.json` |
| `rkg.kafka-go` | yes | yes | CR-RKG-028 | CHG-RKG-2026-013 | TASK-RKG-046 | census opens `repo-test/rkg-fixture-go-event-worker`; `tests/evaluation/expected_go.json` |
| `rkg.pgx` | yes | yes | CR-RKG-028 | CHG-RKG-2026-013 | TASK-RKG-046 | census opens `repo-test/rkg-fixture-go-event-worker`; `tests/evaluation/expected_go.json` |
| `rkg.django` | yes | yes | CR-RKG-030 | CHG-RKG-2026-015 | TASK-RKG-048 | `tests/evaluation/fixtures/rkg-fixture-django` + `tests/evaluation/expected_django.json` |
| `rkg.next` | yes | yes | CR-RKG-031 | CHG-RKG-2026-016 | TASK-RKG-049 | `tests/evaluation/fixtures/rkg-fixture-next` + `tests/evaluation/expected_next.json` |
| `rkg.express` | yes | yes | CR-RKG-032 | CHG-RKG-2026-017 | TASK-RKG-050 | `tests/evaluation/fixtures/rkg-fixture-express` + `tests/evaluation/expected_express.json` |
| `rkg.nest` | yes | yes | CR-RKG-033 | CHG-RKG-2026-018 | TASK-RKG-051 | `tests/evaluation/fixtures/rkg-fixture-nest` + `tests/evaluation/expected_nest.json` |
| `rkg.go-http` | yes | yes | CR-RKG-034 | CHG-RKG-2026-019 | TASK-RKG-052 | `tests/evaluation/fixtures/rkg-fixture-go-http` + `tests/evaluation/expected_go_http.json` |
| `rkg.tanstack-router` | yes | yes | CR-RKG-035 | CHG-RKG-2026-020 | TASK-RKG-053 | `tests/evaluation/fixtures/rkg-fixture-tanstack-router` + `tests/evaluation/expected_tanstack_router.json` |
| `rkg.vue-router` | yes | yes | CR-RKG-036 | CHG-RKG-2026-021 | TASK-RKG-054 | `tests/evaluation/fixtures/rkg-fixture-vue-router` + `tests/evaluation/expected_vue_router.json` |
| HTTP static `depends_on` | not an adapter id | no MVP row | CR-RKG-037 | CHG-RKG-2026-022 | TASK-RKG-055 | none |

Mỗi id mới có một story (STORY-RKG-036..042) và một plan/diary cùng số task.
Liên kết HTTP dùng STORY-RKG-043, PLAN-TASK-RKG-055 và DIARY-TASK-RKG-055.
Gate của CHG-RKG-2026-015..022 là `pending`. Không gắn các change set này vào
`adapter_scope` của CHG-RKG-2026-001.
