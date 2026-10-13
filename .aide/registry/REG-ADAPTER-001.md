---
uid:
key: REG-ADAPTER-001
type: adapter-registry
group: normative
scope: system
system: SYS-RKG
status: draft
revision: 17
ownership:
  accountable_team: TEAM-RKG
  accountable_role: architect
relations:
  satisfies: [GOAL-RKG-004, FR-RKG-002]
  constrained_by: [NFR-RKG-EXT-001]
classification: internal
ai_assisted: true
---

# REG-ADAPTER-001 - Analyzer Adapter Registry

Implemented contract: `rkg.adapter/v2` (TASK-RKG-027). Namespace remains readable
in historical snapshots; v1 adapters are rejected for new indexing. Removing
Namespace from new adapter output is an incompatible semantic change.

Registry này là hồ sơ kỹ thuật của adapter, không phải phạm vi chức năng sản phẩm.
FR-RKG-002 chỉ yêu cầu canonical output và conformance contract; việc Python/FastAPI
được chọn cho MVP không tạo dependency từ core sang các công nghệ đó.

## Pipeline contract

Mỗi adapter tham gia một hoặc nhiều stage chuẩn:

1. `discover`: nhận diện file/technology/entrypoint bằng evidence tĩnh.
2. `parse`: tạo AST/CST hoặc structured representation riêng của adapter; core không
   regex trực tiếp trên raw source.
3. `extract`: phát ra candidate entity/relationship theo canonical DTO.
4. `resolve`: nối symbol, registration chain và resource identity trong phạm vi contract.
5. `validate`: kiểm tra endpoint, evidence, snapshot ownership và capability claims.

Regex chỉ được dùng cục bộ cho token hoặc metadata format đơn giản khi adapter công bố
rule/evidence; regex không phải intermediate representation chung và không được dùng
để đoán semantic relationship. LLM không nằm trong pipeline tạo graph fact.

Canonical DTO emitted by adapters uses `SourceUnit`, `Type`, `Callable`, `Endpoint`,
`DataResource`, `MessageChannel`, `Configuration`, `ExternalDependency`; adapter giữ
chi tiết gốc trong `language_kind`, `framework_kind` và attributes có namespace.

## Required descriptor fields

`adapter_id`, `adapter_version`, `contract_version`, `kind`, `language`, optional
`framework`, `grammar_or_target`, `file_patterns`, `ignore_patterns`, `capabilities`,
`technology_constraints` và parser/extractor entrypoint nội bộ.

`kind` là `language`, `framework`, `data_access`, `messaging`, `configuration` hoặc
`external_dependency`. Registration order không quyết định kết quả; selection và output
phải deterministic theo adapter ID/version và evidence.

## MVP entries

Đây là **MVP adapter profile đầu tiên**, không phải danh sách loại entity của core.

| Adapter ID | Kind | Language/framework | Target | Capabilities | Support |
|---|---|---|---|---|---|
| `rkg.python` | language | Python | CPython 3.12 grammar | structure, imports, calls, classes, metadata | deep-supported |
| `rkg.fastapi` | framework | Python / FastAPI | registry version constraints | app, routes, DI | deep-supported |
| `rkg.sqlalchemy` | data_access | Python / SQLAlchemy | 2.x supported subset | tables, maps-to, reads, writes | deep-supported |
| `rkg.aiokafka` | messaging | Python / aiokafka | supported subset | topics, publishes, consumes | deep-supported |
| `rkg.flask` | framework | Python / Flask | CPython 3.12 AST | app, routes | registered in `builtin_adapters()`; `reviewed_deep_support = False`; emitted capabilities are `DETECTED_ONLY`; not a reviewed deep-supported MVP profile |
| `rkg.conformance.fixture` | language/framework fixture | synthetic | test-only | structure, route, diagnostic | conformance-only |
| `rkg.typescript` | language | TypeScript / TSX | tree-sitter TypeScript/TSX | structure, imports, calls, classes, metadata | implemented (TASK-RKG-042 GREEN); registered in `builtin_adapters()`; not deep-supported until conformance review |
| `rkg.react-router` | framework | TypeScript / React Router | `react-router-dom >=6,<8` | app, routes | implemented (TASK-RKG-042 GREEN); depends on `rkg.typescript`; navigation routes use `framework_kind=react-router` (OQ-RKG-007); not deep-supported until conformance review |
| `rkg.bullmq` | messaging | TypeScript / BullMQ | BullMQ 6.x Queue/Worker | topics, publishes, consumes | implemented; depends on `rkg.typescript`; registered in `builtin_adapters()`; not deep-supported until conformance review |
| `rkg.vue` | language | Vue SFC | Vue SFC blocks + tree-sitter TypeScript script | structure, imports, calls, classes, metadata | implemented; registered in `builtin_adapters()`; not deep-supported until conformance review |
| `rkg.nuxt` | framework | Vue / Nuxt | Nuxt 3/4 pages + Nitro `server/api` | app, routes | implemented; depends on `rkg.vue` (+ `rkg.typescript` for server/composable TS); navigation `framework_kind=nuxt` (OQ-RKG-007); not deep-supported until conformance review |
| `rkg.java` | language | Java | tree-sitter Java | structure, imports, calls, classes, metadata | implemented (spring census GREEN); registered in `builtin_adapters()`; not deep-supported until conformance review |
| `rkg.spring` | framework | Java / Spring Web MVC | Spring Boot 3.x annotations | app, routes | implemented; depends on `rkg.java`; not deep-supported until conformance review |
| `rkg.jpa` | data_access | Java / JPA | Jakarta Persistence / Hibernate 6.x | tables, maps-to, reads, writes | implemented; depends on `rkg.java`; DataResource identity `relational:{schema}.{table}`; not deep-supported until conformance review |
| `rkg.spring-kafka` | messaging | Java / Spring Kafka | Spring Kafka 3.x | topics, publishes, consumes | implemented; depends on `rkg.java`; not deep-supported until conformance review |
| `rkg.go` | language | Go | tree-sitter Go | structure, calls, classes, metadata | implemented; registered in `builtin_adapters()`; not deep-supported until conformance review |
| `rkg.kafka-go` | messaging | Go / kafka-go | `NewKafkaReader` / `EventPublisher.Publish` | topics, publishes, consumes | implemented; depends on `rkg.go`; registered in `builtin_adapters()`; not deep-supported until conformance review |
| `rkg.pgx` | data_access | Go / pgx | static SQL `schema.table` | tables, reads, writes | implemented; depends on `rkg.go`; registered in `builtin_adapters()`; DataResource identity `relational:{schema}.{table}`; not deep-supported until conformance review |

Stack được detect nhưng không có compatible deep adapter vẫn được công bố là
`detected_only`. `rkg.flask` nằm trong default registration và vẫn ở cột support
trên: được chạy khi selection chọn nó, không được gọi là deep-supported. Adapter
ngoài bảng phải thêm entry/revision được review, công bố supported patterns và
pass `TEST-RKG-ADAPTER-CONFORMANCE` trước khi gọi là deep-supported.

`rkg.typescript` và `rkg.react-router` đã có module dưới `src/rkg/adapters/`
(`typescript_language.py`, `react_router_framework.py`) và đăng ký trong
`builtin_adapters()`. Không được gọi là deep-supported cho đến khi conformance
100% + review. Oracle hành vi: `repo-test/rkg-fixture-react-ts` README.

## `rkg.python` language extract

Không có adapter `kind=configuration` riêng. Configuration và HTTP origin là
output thêm của language adapter `rkg.python`, nên capability list công bố giữ
nguyên `structure`, `imports`, `calls`, `classes`, `metadata`.

| Pattern | Evidence đủ | Fact | Không lưu |
|---|---|---|---|
| `os.environ`, `os.getenv` literal | key tĩnh | `Configuration` `environment` và `depends_on` từ callable hoặc source unit | value, default, credential |
| class kế thừa explicit `pydantic_settings.BaseSettings` hoặc `pydantic.BaseSettings` | field đã khai báo | `Configuration` `settings` cùng owner/key | value, default |
| `requests` / `httpx` absolute `http`/`https`, gồm client đã resolve | literal origin | một `ExternalDependency` `http_service` cho mỗi scheme/host/port; port 80 và 443 được gộp | userinfo, path, query, payload |

Key động, URL động, module local che `os`/`requests`/`httpx`, hoặc client không
resolve duy nhất không tạo fact. Hai trường hợp đầu chỉ phát diagnostic cố định
kèm path/line.

## `rkg.sqlalchemy` data-access extract

Chỉ declarative class có bằng chứng tĩnh. Identity của `DataResource` là
`table` + namespace: schema literal, hoặc chuỗi rỗng khi class không khai báo
schema. Cùng tên table khác namespace là hai resource. Cùng namespace và cùng
table là một resource với nhiều cạnh `maps_to`.

| Pattern | Evidence đủ | Fact | Không tạo |
|---|---|---|---|
| class declarative (`DeclarativeBase` hoặc `declarative_base()`) có `__tablename__` literal; schema literal hoặc không có schema | đúng class đó | `DataResource` `table` và `maps_to` từ `Type` | gộp theo tên table khi namespace khác |
| `session.get(Model, ...)` | Model resolve duy nhất | `reads`, rule `RKG.sqlalchemy.get.v1` | model mơ hồ |
| `session.execute` / `scalars` / `scalar` nhận `select(Model)` hoặc tên gán đúng một lần; chuỗi `.where` được bóc | Model hoặc column của model đó resolve duy nhất | `reads`, rule `RKG.sqlalchemy.select.v1` | `select` không nằm trong lời gọi thực thi |
| `session.execute` / `scalars` / `scalar` nhận `insert` / `update` / `delete(Model)` | Model resolve duy nhất | `writes`, rule `RKG.sqlalchemy.insert.v1`, `update.v1` hoặc `delete.v1` | lời gọi chưa thực thi |
| `session.add(instance)` hoặc `session.delete(instance)` | constructor, annotation hoặc `self`/`cls` của mapped class resolve duy nhất | `writes`, rule `RKG.sqlalchemy.add.v1` hoặc `delete.v1` | instance mơ hồ |

Operation metadata là rule có version trên evidence của cạnh `reads`/`writes`.
Edge không có attribute bag; nếu một callable dùng nhiều operation trên cùng
resource, evidence của từng operation được gộp vào một cạnh và rule của cạnh là
rule nhỏ nhất theo thứ tự chữ. Reflection (`autoload`, `autoload_with`,
`automap_base`), `__tablename__`/schema không literal, và module local tên
`sqlalchemy` không tạo edge. Adapter không lưu giá trị column hay payload.

## `rkg.aiokafka` messaging extract

Chỉ call site nằm trong một callable, và receiver phải resolve đúng một lần tới
`AIOKafkaProducer` hoặc `AIOKafkaConsumer`: gán một lần tới constructor, annotation
đúng class, constructor gọi trực tiếp, hoặc attribute `self`/`cls` được gán một
lần trong method của class đó. Identity của `MessageChannel` là channel kind
`topic`, namespace chuỗi rỗng và tên topic. Subset này không có schema hay cluster
riêng; bootstrap server không đưa vào graph. Cùng tên topic là một channel.

| Pattern | Evidence đủ | Fact | Không tạo |
|---|---|---|---|
| `send` / `send_and_wait`: topic là positional đầu hoặc keyword `topic` | literal hoặc hằng module | `publishes`, rule `RKG.aiokafka.publish.v1` | value, key, payload |
| `send_batch`: topic là positional thứ hai hoặc keyword `topic` | literal hoặc hằng module | `publishes`, rule `RKG.aiokafka.publish.v1` | nội dung batch |
| `AIOKafkaConsumer(*topics)` | mỗi positional là literal hoặc hằng module | `consumes`, rule `RKG.aiokafka.consume.v1` | keyword cấu hình |
| `subscribe(topics)` | list/tuple hoặc hằng module là dãy topic tĩnh, và không có `pattern` | `consumes`, rule `RKG.aiokafka.subscribe.v1` | pattern regex, payload |

Hằng module là gán cấp module đúng một lần, không điều kiện, tới chuỗi hoặc dãy
chuỗi/hằng đã resolve, kể cả import đúng một target. Hằng khai báo trong hàm không
đủ. Topic động, `pattern`, receiver không resolve, và lời gọi ngoài callable chỉ
phát diagnostic `aiokafka_topic_unresolved` hoặc `aiokafka_topic_unscoped`. Module
local tên `aiokafka` không tạo fact. Constraint `>=0.8,<1.0` cần lock đã xác minh
trước khi selection báo `supported_patterns`.

## Structure ownership and v2 transition

Core owns Repository lifecycle and builds Directory ancestors from manifest-backed
SourceUnits. Adapters emit source/semantic facts, not Directory/Repository or new
Namespace nodes. Source names, qualified names and language/framework kinds belong
to the adapter. Core merges and validates results without rewriting symbol spelling
or merging entities solely because their names match.

The Python v2 profile emits SourceUnit -> Type/Callable directly, retains nested
lexical containment, and carries `module_name` on SourceUnit. Existing path-based
module naming and package __init__.py conventions are retained. Import, alias,
relative-import, class and call resolution use the symbol index independently of
Namespace entities. Database schema namespace and message-channel namespace remain
resource identity fields; removing Namespace nodes does not remove those fields.

A future Java profile documents `package_name`, language kinds and overload signatures.
Java support is not added by this change. Framework/deep adapters must be verified
against v2 base facts and updated where needed. New jobs require compatible v2
adapters; v1 descriptors are rejected explicitly, not silently relabeled. Historical
snapshots keep captured versions. Conformance covers adapter/core ownership, IDs,
containment, structural evidence, import resolution, mixed-language paths and
historical snapshot readability. The Directory builder does not branch by language.

## FastAPI static profile revision 2.1.0

FastAPI keeps its verified version target `>=0.100,<1.0`. With observed FastAPI
imports and an unknown version, the adapter explicitly opts into extraction of
known static patterns. Selection remains `version_unverified`, captures executed
adapter/capabilities and records `adapter_version_unverified` as a warning. This
does not assert version compatibility. Known out-of-range versions stay blocked;
declared-only dependencies do not activate extraction. Other adapter constraints
remain strict unless the adapter explicitly opts in.

Supported additions: a unique local parameterless, undecorated app factory with
one direct FastAPI assignment and one final unconditional return; finite literal
list/tuple loops of router registration expressions; and empty route paths with an
effective nonempty prefix. Empty paths preserve the prefix without adding `/`.
Factories preserve original handler symbols and parse trees. Registrations retain
original source line evidence. Dynamic iterables, conditional returns and ambiguous
or reassigned bindings produce diagnostics or unresolved application selection;
they never execute Python or create guessed links. Imported/parameterized factories
remain outside this profile. TASK-RKG-028 records current-tree verification.

## Python 2.1 and SQLAlchemy 2.1.0 flow support

Python adds conservative static receiver typing for constructors, local instances,
annotations, self/cls, fields and uniquely inherited methods. Conflicting helper argument
types and reassigned bindings remain unresolved. SQLAlchemy explicitly permits unknown
versions for supported static patterns with version_unverified and a persisted warning;
known out-of-range versions remain blocked. Supported query refinements preserve a
single initial SQL operation. Generic model bindings attach access to the concrete
caller, with call-site/implementation evidence, avoiding global method-to-all-tables
edges. ORM mutation/flush support requires an explicit model parameter. Dynamic dispatch,
unknown models and unsupported SQL shapes stay diagnostic.

## `rkg.typescript` language extract (TASK-RKG-042 GREEN)

Descriptor fields: `adapter_id=rkg.typescript`, `kind=language`,
`language=typescript`, `grammar_or_target` = tree-sitter TypeScript/TSX
(not raw-source regex as IR), `file_patterns` include `*.ts` / `*.tsx` (and recursive
forms), `ignore_patterns` include `**/node_modules/**` and `**/*.d.ts`,
capabilities `structure`, `imports`, `calls`, `classes`, `metadata`.
Configuration keys and HTTP origins are language outputs (same ownership pattern as
`rkg.python`); no separate `kind=configuration` adapter.

Qualified-name convention (draft): relative path without extension, `/` → `.`, then
`.` + symbol. Example: `src/hooks/useOrders.ts` + `useOrders` →
`src.hooks.useOrders.useOrders`. Path alias `@/` resolves only when tsconfig/Vite
paths uniquely map the prefix.

| Pattern | Evidence đủ | Fact | Không tạo / không lưu |
|---|---|---|---|
| named / default / namespace / alias import; relative `../`; path alias `@/` unique | static specifier resolves uniquely | `imports` SourceUnit → SourceUnit/symbol or ExternalDependency | star/dynamic/ambiguous → diagnostic only |
| `OrdersPage` → `useOrders` → `orderApi.listOrders` → `httpClient.get` (unique) | call site + unique callee | `calls` Callable → Callable with call-site evidence | shadowed / reassigned / ambiguous callee |
| `import.meta.env.VITE_API_BASE_URL`, `VITE_ENABLE_ADMIN` | key literal | `Configuration` environment key; `depends_on` from owner | value, default, credential |
| absolute `https://inventory.example.test` (or equivalent literal origin) | literal origin | `ExternalDependency` `http_service` scheme/host/port | path, query, payload, userinfo |
| dynamic `import(moduleName)` | — | diagnostic | guessed internal import edge |
| dynamic URL from runtime host | — | diagnostic | guessed external origin |
| reassigned / dual-target binding | — | diagnostic | unique `calls` edge |
| local function named `fetch` | — | — | Fetch/HTTP technology from shadowed name |
| syntax-invalid unit (dedicated corpus / `.invalid.ts.fixture` content) | parse failure location | diagnostic with relative path + line; valid siblings still extract | guessed facts from bad file |
| sentinel `RKG_TEST_SECRET_DO_NOT_PERSIST` | — | — | never in facts, diagnostics text, or reports |

## `rkg.react-router` framework extract (TASK-RKG-042 GREEN)

Descriptor fields: `adapter_id=rkg.react-router`, `kind=framework`,
`language=typescript`, `framework=react-router-dom`, capabilities `app`, `routes`,
technology constraint `react-router-dom >=6.0,<8.0`. Requires compatible
`rkg.typescript` base facts. Selection uses `ReactRouterDetector` so package /
import evidence enters the observed set (same pattern as FastAPI/Flask detectors).

Static registration chain (fixture oracle): `createBrowserRouter(appRoutes)` with
nested layout/index/dynamic/catch-all. Expected navigation paths (semantic, not
entity-hash IDs): `/`, `/orders`, `/orders/:orderId`, `/orders/:orderId/edit`,
`/admin/users` (from uniquely imported constant), `*`.

| Pattern | Evidence đủ | Fact | Không tạo |
|---|---|---|---|
| static `RouteObject` path / index / splat in clear module | literal or unique imported constant | `Endpoint` with `framework_kind=react-router`, attributes `kind=navigation` + `path`/`route_path` (no HTTP method); when `element={<Page />}` resolves to a Callable, emit `handled_by` | FastAPI-style HTTP method+path Endpoint / repository `exposes` as API |
| nested layout + children | static tree | registration chain evidence | — |
| dynamic/conditional route in negative analysis-case | — | diagnostic | guessed route path |

UI navigation routes reuse logical `Endpoint` with `kind=navigation` (OQ-RKG-007
resolved): not FastAPI-style HTTP (no method, no API `exposes`). Outbound HTTP
remains language `ExternalDependency` / relative app calls only. Focused
`view=flow` from a navigation root expands via `handled_by`/`calls` and also
`depends_on` (config/external) without changing HTTP Endpoint flow defaults.

## `rkg.bullmq` messaging extract (implemented)

Descriptor: `adapter_id=rkg.bullmq`, `kind=messaging`, `language=typescript`,
`framework=bullmq`, BullMQ `>=6,<7`, capabilities `topics` / `publishes` /
`consumes`. Depends on base facts from `rkg.typescript`. Not deep-supported
until conformance review. Oracle: `repo-test/rkg-fixture-bullmq-worker` and
`tests/evaluation/expected_bullmq.json`.

| Pattern | Evidence đủ | Fact | Không tạo / không lưu |
|---|---|---|---|
| `new Queue(name)` / `new Worker(name)` với import value từ `bullmq` | name literal hoặc hằng module unique | `MessageChannel` `channel_kind=queue`; Worker trong callable → `consumes` | Redis URL/connection; payload; local `Queue`/`Worker` shadow; constructor reassigned (`WorkerReceiver`) |
| `queue.add(jobName, …)` khi receiver là Queue bullmq (local `new Queue`, `this.field` / param typed `Queue`/`Pick<Queue<T>,…>`) và T map unique tới một queue name | jobName literal + queue name resolve unique | `publishes`, rule `RKG.bullmq.publish.v1` | `LocalPublisher.publish`; dynamic queue name (diagnostic `bullmq_queue_unresolved`); retry/backoff bodies |
| `upsertJobScheduler` / repeatable cleanup | — | không đổi MessageChannel identity; không emit HTTP `Endpoint` | schedule-as-HTTP |

## `rkg.vue` language extract (implemented)

Descriptor fields: `adapter_id=rkg.vue`, `kind=language`, `language=vue`,
`grammar_or_target` = Vue SFC structured blocks + tree-sitter TypeScript for
`<script>` / `<script setup>` (not regex as shared IR), `file_patterns`
`*.vue` / `**/*.vue` only (`package.json` remains with `rkg.typescript` to
avoid language basename partition conflict), `ignore_patterns`
`node_modules`, `.nuxt`, `.output`, `dist`, `coverage`. Capabilities:
`structure`, `imports`, `calls`, `classes`, `metadata`.

Qualified-name convention (draft): relative path without extension, `/` → `.`.
Example: `app/components/OrderCard.vue` → SourceUnit `app.components.OrderCard`.
One `.vue` file is one SourceUnit; template/script/style remain structured
sections on that unit (never fabricated sibling source files). CSS does not
need graph entities.

Oracle corpus (verify only): `repo-test/rkg-fixture-nuxt4` Vue SFCs and language
facts in `tests/evaluation/expected_nuxt.json`. Nuxt routing / Nitro / auto-import /
runtimeConfig belong to `rkg.nuxt`, not this language adapter.

| Pattern | Evidence đủ | Fact | Không tạo / không lưu |
|---|---|---|---|
| `.vue` SFC with template/script/style blocks | structured SFC parse | `SourceUnit` + section attributes | fabricated `.ts`/`.css` SourceUnits; values |
| `<script lang="ts">` + `defineComponent({ name })` | static options object | `Type` `vue_component`; setup `const fn = () =>` → `Callable` | guessed component when options dynamic |
| `<script setup lang="ts">` top-level function | static function / arrow binding | `Callable` under SourceUnit | Nuxt auto-import as ES `imports` |
| relative `import X from './Child.vue'` | unique `.vue` target in scan set | `imports` SourceUnit → SourceUnit/Type | `#shared/...` / convention aliases guessed; bare npm packages (owned by `rkg.typescript`) |
| unique same-SFC call | caller + unique callee | `calls` | `$fetch` / `useFetch` / `emit` invented; ambiguous binding |
| syntax-invalid SFC / script | parse failure location | diagnostic with relative path + line; siblings still extract | guessed facts from bad file |
| generated trees | ignore before limits | — | SourceUnits under `.nuxt` / `.output` / `node_modules` / `dist` / `coverage` |
| sentinel `RKG_TEST_SECRET_DO_NOT_PERSIST` | — | — | never in facts or diagnostics text |

## `rkg.nuxt` framework extract (implemented)

Descriptor: `adapter_id=rkg.nuxt`, `kind=framework`, `language=vue`,
`framework=nuxt`, Nuxt `>=3,<5`, capabilities `app` / `routes`. Depends on
`rkg.vue` for SFC base facts; server/composable `.ts` come from `rkg.typescript`
(reuse typescript parse units — do not re-implement language adapters). Not
deep-supported until conformance review. Oracle:
`repo-test/rkg-fixture-nuxt4` and `tests/evaluation/expected_nuxt.json`.

| Pattern | Evidence đủ | Fact | Không tạo / không lưu |
|---|---|---|---|
| `app/pages/**/*.vue` or `pages/**/*.vue` file convention | static path segments | `Endpoint` `framework_kind=nuxt`, `kind=navigation`, `path`/`route_path` (no HTTP method); `handled_by` → page `{qn}.setup` Callable; `route_signal` / `outbound_requests` from static HTTP evidence; no repository `exposes` | dynamic/`$` invented paths; FastAPI-style HTTP method |
| literal `$fetch` / `useFetch` / param default `$fetch` | static relative URL (and optional method literal) | `http_requests` on owning Callable (e.g. `useOrders`); feeds navigation `outbound_requests` | template/dynamic URLs; shadowed local `$fetch`; invented cancel paths |
| `server/api/**/*.{get,post,…}.ts` Nitro naming | method suffix + static segments | HTTP `Endpoint` method+path; `handled_by` when unique `create*Handler` in base | `analysis-cases` runtime registration; routes outside `server/api` |
| unbound `useX` / PascalCase component with unique convention target | unique composable/component simple name | `depends_on` (not ES `imports`) | ambiguous `useSummary`; inventing ES import edges |
| `runtimeConfig` / `runtimeDefaults` keys in `nuxt.config.*` | static object keys | `Configuration` `runtime:{key}` + `boundary` public/server | values, env secrets, sentinel |
| absolute `http(s)://` origin literal in server TS | unique origin; skip if language already emitted | `ExternalDependency` `http_service` | dynamic URL; shadowed `$fetch`; path/query as identity |

## `rkg.java` / Spring stack (draft)

Oracle: `repo-test/rkg-fixture-spring-orders` README and
`tests/evaluation/expected_spring.json`. Modules:
`java_language.py`, `spring_framework.py`, `jpa_data.py`,
`spring_kafka_messaging.py`. Not deep-supported until conformance review.

| Adapter | Pattern | Fact | Không tạo / không lưu |
|---|---|---|---|
| `rkg.java` | `*.java` CST via tree-sitter; package short QN under fixture root | SourceUnit/Type/Callable; overload signatures; `inherits_from` / `implements`; constructor DI as Type→Type `depends_on`; explicit method `calls`; YAML `${ENV}` key names + `spring.kafka.listener.auto-startup` | values, secrets, guessed ambiguous simple names |
| `rkg.spring` | `@RestController`/`@Controller` + static class/method mapping | `Endpoint` method+path; `handled_by` | UnregisteredController; `${...}` / SpEL dynamic paths |
| `rkg.jpa` | `@Entity` + literal `@Table(schema,name)` | `DataResource` `relational:{schema}.{table}`; `maps_to`; Type-level `reads`/`writes` from `JpaOrderRepository` | merge audit/commerce; runtime native SQL; column values |
| `rkg.spring-kafka` | unique topic constants; `KafkaTemplate.send`; `@KafkaListener` on `@Component` | `MessageChannel`; `publishes` / `consumes` | SpEL topics; payloads; bootstrap servers |

## `rkg.go` / kafka-go / pgx stack (draft)

Oracle: `repo-test/rkg-fixture-go-event-worker` README and
`tests/evaluation/expected_go.json`. Modules: `go_language.py` /
`go_parse.py`, `kafka_go_messaging.py`, `pgx_data.py`. Not deep-supported
until conformance review.

| Adapter | Pattern | Fact | Không tạo / không lưu |
|---|---|---|---|
| `rkg.go` | `*.go` CST via tree-sitter; package-scoped QN (`domain.Type`); no Namespace | Type/Callable; value+pointer receivers; generics name-only; explicit `calls`; env key names (`KAFKA_*`, `DATABASE_URL`, `CLEANUP_INTERVAL`) | package as Namespace; secret sentinel; absolute paths; guessed ambiguous interface targets |
| `rkg.kafka-go` | `ReaderConfig.Topic` literal/const via `NewKafkaReader`; `EventPublisher.Publish` with static topic/const (incl. import alias) | `MessageChannel`; `consumes` from `NewKafkaReader`; `publishes` from `EventPublisher.Publish` | dynamic topic; package-level publish; shadowed `kafka`; payloads; Type-sourced consumes (schema requires Callable) |
| `rkg.pgx` | static SQL string constants with `schema.table` | `DataResource` `relational:{schema}.{table}` (`kind=table`); method `reads`/`writes` | runtime-built SQL; credentials; row values |
