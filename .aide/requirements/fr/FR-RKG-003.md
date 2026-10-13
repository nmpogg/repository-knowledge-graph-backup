---
uid:
key: FR-RKG-003
type: functional-requirement
group: normative
scope: system
system: SYS-RKG
status: draft
revision: 12
ownership:
  accountable_team: TEAM-RKG
  accountable_role: product-owner
relations:
  satisfies: [GOAL-RKG-002]
  constrained_by: [NFR-RKG-PERF-001, NFR-RKG-REL-001, NFR-RKG-UX-001]
classification: internal
ai_assisted: true
---

# FR-RKG-003 — Tìm kiếm và khám phá graph

## Mô tả

Người dùng tìm entity trong một snapshot, duyệt subgraph theo hướng/loại cạnh/ngân sách và khám phá kết quả trên UI cùng metadata, limitation và evidence. Kết quả deterministic, không trộn snapshot hoặc repository, và hỗ trợ đầy đủ các trạng thái loading, empty, error và truncated.

## Acceptance Criteria

### Search và traversal

#### AC-RKG-009
- **given** graph fixture có cycle
- **when** traversal theo direction, edge_types và depth
- **then** kết quả hữu hạn (visited set), đúng hướng/filter, deterministic, không dangling edge
- `constrained_by:` [NFR-RKG-PERF-001]
- `implementation_target:` [CMP-RKG-GRAPH, API-RKG-CORE-v1]
- `validated_by:` [TEST-RKG-TRAVERSAL]

#### AC-RKG-036
- **given** một snapshot có entity trùng tên nhưng khác qualified name/type và có API khác method/path
- **when** search bằng `q`, `type` và paging theo contract
- **then** chỉ trả entity thuộc `snapshot_id` yêu cầu; match name/qualified name/method+path đúng; thứ tự type → qualified_name → ID và page boundary deterministic, không trùng hoặc bỏ kết quả
- `constrained_by:` [NFR-RKG-PERF-001]
- `implementation_target:` [CMP-RKG-GRAPH, API-RKG-CORE-v1]
- `validated_by:` [TEST-RKG-SEARCH]

#### AC-RKG-037
- **given** benchmark corpus và máy tham chiếu được mô tả bởi NFR-RKG-PERF-001
- **when** chạy workload search/subgraph chuẩn sau warm-up
- **then** báo cáo số liệu thô, cấu hình máy và kết quả đạt hoặc không đạt ngưỡng của NFR-RKG-PERF-001
- `constrained_by:` [NFR-RKG-PERF-001]
- `implementation_target:` [CMP-RKG-GRAPH, API-RKG-CORE-v1]
- `validated_by:` [TEST-RKG-QUERY-BENCHMARK]

#### AC-RKG-060
- **given** repository chưa từng publish active snapshot, `snapshot_id` yêu cầu không khả dụng, hoặc entity/root ID không thuộc snapshot yêu cầu
- **when** gọi search, entity, subgraph hoặc context read
- **then** API trả `409 no_active_snapshot`, `410 snapshot_unavailable` hoặc `404` identity mismatch theo trường hợp; không trả graph rỗng giả và UI hiển thị no-active-snapshot/stale-unavailable state có recovery action
- `constrained_by:` [NFR-RKG-REL-001]
- `implementation_target:` [CMP-RKG-GRAPH, CMP-RKG-TRANSPORT, CMP-RKG-WEB]
- `validated_by:` [TEST-RKG-NO-ACTIVE-SNAPSHOT]

### Graph explorer

#### AC-RKG-011
- **given** snapshot/fixture sẵn sàng trên UI
- **when** người dùng search → chọn entity → duyệt graph → mở evidence → export context JSON
- **then** từng bước có tên/primary action và trạng thái loading/empty/error/truncated; toàn bộ action dùng được bằng keyboard, focus visible và error/status được announce
- `constrained_by:` [NFR-RKG-UX-001]
- `implementation_target:` [CMP-RKG-WEB]
- `validated_by:` [TEST-RKG-UI-EXPLORER]

#### AC-RKG-018
- **given** API có đường đi tới DB/event trong fixture
- **when** chọn preset API→DB, Event participants, Config users hoặc Interface implementations
- **then** UI áp đúng direction/edge types của UIS-RKG-001, phân biệt semantics từng cạnh và hiện evidence; không tạo direct edge suy diễn hoặc tuyên bố runtime behavior
- `constrained_by:` [NFR-RKG-UX-001]
- `implementation_target:` [CMP-RKG-WEB, CMP-RKG-GRAPH]
- `validated_by:` [TEST-RKG-UI-PRESETS]

#### AC-RKG-056
- **given** UI fixture ở light/dark mode, reduced-motion on/off và viewport 375/768/1024/1440 px
- **when** chạy checklist trực quan và accessibility
- **then** text/control đạt WCAG AA theo evidence; form có label; trạng thái không chỉ dùng màu; reduced motion loại chuyển động không thiết yếu; không có horizontal scroll ngoài graph canvas; font semantic dùng token local/fallback đã định nghĩa
- `constrained_by:` [NFR-RKG-UX-001]
- `implementation_target:` [CMP-RKG-WEB]
- `validated_by:` [TEST-RKG-UI-VISUAL-A11Y]

#### AC-RKG-057
- **given** snapshot có dependency declared/imported/usage và technology ở các support state `supported_patterns`, `detected_only`, `version_unverified`, `unsupported_version`
- **when** maintainer mở Dependency và Technology panels
- **then** UI lọc/hiển thị đúng provenance, evidence và support state; không suy diễn runtime use từ declaration/import hoặc `detected_only`
- `constrained_by:` [NFR-RKG-UX-001]
- `implementation_target:` [CMP-RKG-WEB, CMP-RKG-GRAPH]
- `validated_by:` [TEST-RKG-UI-TECH-DEPENDENCY]

#### AC-RKG-073
- **given** snapshot đã index, search trả entity có type và qualified_name; Explorer đang ở Graph hoặc List
- **when** người dùng bấm nút Structure trên thanh view
- **then** Structure displays canonical Directory/SourceUnit entities and lexical symbols, without duplicate synthesized directory identities; selecting directories/files/symbols opens the same detail as List; pathless entities remain root siblings; old Namespace snapshots use a metadata-selected compatibility projection without identity changes; structure evidence shows relative path provenance without source excerpts; Graph/List switching and canvas loading/empty/error behavior remain available
- `constrained_by:` [NFR-RKG-UX-001]
- `implementation_target:` [CMP-RKG-WEB]
- `validated_by:` [TEST-RKG-UI-STRUCTURE]
- `story:` [STORY-RKG-017]

## Focused flow and optional ownership

Explorer defaults to entity flow for semantic roots. Endpoint/Callable flow follows
outgoing handled_by/calls and data/message accesses; resources show incoming users and
upstream callers. UI navigation Endpoints (`kind=navigation`, OQ-RKG-007) also follow
`depends_on` to Configuration / ExternalDependency in flow (UI→API); HTTP Endpoint
defaults are unchanged. Resource nodes terminate downstream expansion, so a shared table does
not bring in other endpoints. Type roots may include their own methods and maps_to.
Directory/SourceUnit/legacy Namespace roots use structural neighborhood exploration.

File/folder ownership and declared dependencies are optional, off by default. Ownership
is appended after semantic traversal; those parents never expand imports, siblings or
other semantic edges. Depth counts semantic hops, and all output still obeys node/edge
budgets, deterministic order, snapshot isolation and evidence requirements. Neighborhood
mode preserves direction/edge filters and the existing API defaults. Context exports
use the same chosen profile. Published AC IDs remain unchanged.

In flow presentation, ownership is shown as optional location breadcrumbs on
semantic steps, not separate branches. Callable stages precede terminal data
resources even with shortcut edges. Selection preserves the flow viewport and
reads/writes remain identifiable. The client requires an acknowledged flow response;
a running older server must not silently substitute neighborhood data. Context
exports retain selected graph facts, including requested ownership facts.

## Revision 12

`AC-RKG-073` records `story: [STORY-RKG-017]`. `STORY-RKG-016` and
`STORY-RKG-019` no longer list that AC. No other AC in this file changed.
