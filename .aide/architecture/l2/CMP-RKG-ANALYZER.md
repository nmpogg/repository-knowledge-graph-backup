---
uid:
key: CMP-RKG-ANALYZER
type: component
group: normative
scope: system
system: SYS-RKG
status: draft
revision: 16
ownership: {accountable_team: TEAM-RKG, accountable_role: architect}
relations: {realizes: [CAP-RKG-001], constrained_by: [NFR-RKG-SEC-001]}
classification: internal
ai_assisted: true
---
# CMP-RKG-ANALYZER - Analyzer component

## Responsibilities

Repository-scoped source ingestion, immutable manifest, adapter registry/selection,
language parsing, symbol resolution, technology detection và deep extraction qua
contract version hóa. Bộ profile deep-supported đầu tiên của MVP là Python 3.12,
FastAPI, SQLAlchemy 2.x và aiokafka; chúng không phải dependency đóng cứng theo
adapter ID trong coordinator. `builtin_adapters()` còn đăng ký `FlaskFrameworkAdapter`
(`adapter_id=rkg.flask`). Adapter đó chạy trong pipeline mặc định, trích route Flask
tĩnh, và khai `reviewed_deep_support = False` với capability `DETECTED_ONLY`. Nó
không phải profile deep-supported đã review.

`builtin_adapters()` cũng đăng ký `rkg.typescript` (language) và `rkg.react-router`
(framework). Cả hai đã implemented / selectable theo `REG-ADAPTER-001`, emit fact
theo pattern đã đăng ký, và giữ `reviewed_deep_support = False` — chưa phải profile
deep-supported MVP cho đến khi conformance review đóng. Ownership extract/emit thuộc
adapter; semantic Entity navigation Endpoint (`kind=navigation`,
`framework_kind=react-router`) nằm ở `CMP-RKG-GRAPH` / OQ-RKG-007, không mở entity
type mới ở đây.

`builtin_adapters()` cũng đăng ký `rkg.vue` (language) và `rkg.nuxt` (framework).
Cả hai đã implemented / selectable theo `REG-ADAPTER-001`, emit fact theo pattern
đã đăng ký, và giữ `reviewed_deep_support = False` — chưa phải profile deep-supported
cho đến khi conformance review đóng. Framework Nuxt chạy sau khi merge partition
Vue + TypeScript. Ownership extract/emit thuộc adapter; semantic Entity navigation
Endpoint (`kind=navigation`, `framework_kind=nuxt`) nằm ở `CMP-RKG-GRAPH` /
OQ-RKG-007, không mở entity type mới ở đây. Nitro HTTP Endpoint là HTTP Endpoint
thường (method + path).

`builtin_adapters()` cũng đăng ký `rkg.bullmq` (messaging). Adapter đã implemented /
selectable theo `REG-ADAPTER-001`, emit fact theo pattern đã đăng ký, và giữ
`reviewed_deep_support = False`. Phụ thuộc language fact từ `rkg.typescript`. Emit
`MessageChannel` / `publishes` / `consumes`; scheduler/repeatable không thành HTTP
Endpoint. Không mở entity type mới.

`builtin_adapters()` cũng đăng ký `rkg.java` (language), `rkg.spring` (framework),
`rkg.jpa` (data_access) và `rkg.spring-kafka` (messaging). Cả bốn đã implemented /
selectable theo `REG-ADAPTER-001` và giữ `reviewed_deep_support = False`.
`rkg.spring`, `rkg.jpa` và `rkg.spring-kafka` phụ thuộc `rkg.java`. Spring emit
HTTP Endpoint (method + path) và `handled_by`. JPA emit `DataResource` với
identity `relational:{schema}.{table}`. Spring Kafka emit `MessageChannel` cùng
`publishes` / `consumes`. Không mở entity type mới.

`builtin_adapters()` cũng đăng ký `rkg.go` (language), `rkg.kafka-go` (messaging)
và `rkg.pgx` (data_access). Cả ba đã implemented / selectable theo
`REG-ADAPTER-001` và giữ `reviewed_deep_support = False`. `rkg.kafka-go` và
`rkg.pgx` phụ thuộc `rkg.go`. kafka-go emit `MessageChannel` cùng `publishes` /
`consumes`. pgx emit `DataResource` với identity `relational:{schema}.{table}`
và method `reads` / `writes`. Không mở entity type mới.

`builtin_adapters()` cũng đăng ký `rkg.django`, `rkg.next`, `rkg.express`,
`rkg.nest`, `rkg.go-http`, `rkg.tanstack-router` và `rkg.vue-router`. Cả bảy
đã có trong `REG-ADAPTER-001` revision 19, chạy trong pipeline mặc định, và giữ
`reviewed_deep_support = False` với capability `DETECTED_ONLY`. Chúng không phải
profile deep-supported đã review. Không mở entity type mới. Các adapter này
không emit HTTP `depends_on`.

Sau merge, coordinator chạy `link_static_http_depends_on` trong
`src/rkg/jobs/http_depends.py`. Pass này không phải adapter id và không đổi
`builtin_adapters()`. Callable `depends_on` đúng một Endpoint không phải
navigation khi method và path tĩnh khớp một lần. Chiều Callable→Endpoint là
hành vi trên cây. Then-clause `AC-RKG-005` đã xuất bản vẫn là Callable→Callable
hoặc Endpoint→Callable. Lệch đó là `OQ-RKG-008`; component này không sửa
then-clause tại chỗ.

`IndexCoordinator.run` đọc catalog qua `get_repository`. Nếu request mang
`app_module` hoặc `app_symbol`, coordinator ghi các field đó bằng
`update_repository` trước khi scan. Adapter không đọc catalog, không ghi database
và không đổi lifecycle. Việc đọc/ghi catalog ở trên thuộc coordinator, không thuộc
từng adapter.

## Internal structure

Coordinator mở registry từ `builtin_adapters()`, partition file theo language
adapter, chạy language extract/resolve theo partition, merge ParseResult +
FactBatch, rồi chạy framework/deep adapter đã chọn **một lần** trên batch đã
merge (polyglot: Nuxt cần Vue SFC + TypeScript Nitro/composable cùng lúc;
React Router chạy sau merge partition TypeScript, cùng pattern framework khác).
Language adapter giữ parse/symbol. Framework adapter chỉ thêm fact. Detector
technology trả observation cho report job, không ghi bảng graph.

## Boundaries

`LanguageAdapter` nhận immutable manifest/config và trả parsed units, symbol index,
`FactBatch`, diagnostics và capabilities. `FrameworkAdapter` dùng parsed units qua
language-compatible contract và trả thêm facts/diagnostics. Adapter không ghi database,
không gọi network, không đổi lifecycle và không thực thi source. `FactBatch` tuân theo
entity/edge/evidence contract của `TBL-RKG-GRAPH`; GraphValidator mới có quyền chấp
nhận để publish. Core chọn adapter qua `REG-ADAPTER-001`, không branch theo adapter ID.
Language adapter sở hữu AST/CST hoặc structured representation tương đương; core không
biến raw source thành một văn bản chung để regex. Regex cục bộ chỉ hợp lệ cho token hoặc
metadata đơn giản theo rule đã đăng ký. LLM không tham gia tạo graph fact.

## Sequence

Coordinator đọc repository, có thể cập nhật `app_module`/`app_symbol`, tạo job,
rồi đi `scanning` → `parsing` → `extracting` → `publishing`. Manifest đã chốt đi
vào language adapter theo partition; sau khi merge, framework/deep adapter đã
chọn chạy trên ParseResult/FactBatch hợp nhất — kể cả Flask khi selection chọn
nó. Mỗi adapter trả fact, diagnostic và capability. Technology detection nằm
trong report job, không phải một lần ghi node `TechnologyDetection`.
GraphValidator của `CMP-RKG-GRAPH` mới nhận candidate để publish. Adapter không
tự publish.

## Failure mode

Lỗi parse hoặc extract thành diagnostic theo file. Selection không `ready` làm
job `failed` với `adapter_selection_failed` hoặc mã selection trả về, và không
publish. Candidate không hợp lệ không sang publication. Job terminal và active
snapshot thuộc coordinator/`CMP-RKG-GRAPH`, không phải adapter.

## Transaction boundary

Parse, resolve và extract chạy ngoài database transaction. Component này chỉ phát
`FactBatch`. Commit snapshot nằm ở `CMP-RKG-GRAPH`.

## Idempotency

Cùng manifest, cùng app đã chọn và cùng adapter set thì candidate fact lặp lại.
Analyzer không tự quyết định đã có snapshot tương đương hay chưa; coordinator mới
mở job mới.

## Concurrency

Một index job tại một thời điểm, do job coordinator giữ. Adapter không chia sẻ trạng
thái scan giữa hai job và không thực thi source.

## Directory structure ownership

Core derives Directory ancestors from manifest-backed SourceUnits after language
extraction and adds Repository/Directory containment. No second filesystem walk or
language-specific branch is permitted. Adapters own syntax, module/package scopes,
symbol identity, lexical containment and semantic relations. New output has no
Namespace nodes; module/package metadata and symbol resolution remain supported.
The target adapter v2 transition is defined in REG-ADAPTER-001 and ADR-2026-006.
