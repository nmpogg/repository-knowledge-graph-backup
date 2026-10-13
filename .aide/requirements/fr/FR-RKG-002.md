---
uid:
key: FR-RKG-002
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
  satisfies: [GOAL-RKG-001, GOAL-RKG-002, GOAL-RKG-004]
  constrained_by: [NFR-RKG-SEC-001, NFR-RKG-REL-001, NFR-RKG-EXT-001]
classification: internal
ai_assisted: true
---

# FR-RKG-002 — Phân tích repository thành evidence graph

## Mô tả

Hệ thống dùng pipeline adapter để phát hiện technology, parse source thành representation có cấu trúc, trích xuất entity/relationship vào canonical graph và gắn evidence. Canonical entity do adapter emit gồm SourceUnit, Type, Callable, Endpoint, DataResource, MessageChannel, Configuration và ExternalDependency; thuộc tính `language_kind`/`framework_kind` giữ chi tiết nguồn. Repository là catalog/graph root do vòng đời FR-RKG-001 quản lý, không do adapter emit. Core không phụ thuộc một ngôn ngữ hay framework cụ thể, không thực thi source và không dùng LLM để tạo graph fact. Core builds Directory ancestors from manifest-backed SourceUnits. Adapters do not emit Repository/Directory or Namespace in new snapshots; module/package scope remains adapter metadata and resolution input.

Các pattern theo ngôn ngữ/framework không được đóng cứng trong FR này. Chúng được
khai báo và kiểm thử qua `REG-ADAPTER-001`; adapter chỉ được công bố capability mà
nó thực sự hỗ trợ và phải trả diagnostic thay vì suy đoán khi không đủ bằng chứng.

## Acceptance Criteria

### Cấu trúc source

#### AC-RKG-002
- **given** a golden repository with nested directories, root/nested SourceUnits, module/package scopes, types, callables and member callables
- **when** scan
- **then** unique Directory nodes and Repository -> Directory -> SourceUnit -> Type/Callable containment match the golden JSON, including nested lexical scopes; root files attach directly to Repository; no new Namespace nodes; module/package metadata and qualified names preserve semantics; no empty/unrepresented directories; structural evidence follows TBL-RKG-GRAPH
- `implementation_target:` [CMP-RKG-ANALYZER]
- `validated_by:` [TEST-RKG-SOURCE-STRUCTURE]
- `story:` [STORY-RKG-017]

#### AC-RKG-035
- **given** fixture chứa file hợp lệ theo grammar của language adapter mục tiêu và file có cú pháp không parse được
- **when** scan
- **then** file hợp lệ vẫn được extract; file lỗi tạo diagnostic có relative path và vị trí, không làm analyzer thực thi source hoặc gán fact suy đoán
- `implementation_target:` [CMP-RKG-ANALYZER]
- `validated_by:` [TEST-RKG-SYNTAX-DIAGNOSTIC]

### Endpoint và dependency wiring

#### AC-RKG-004
- **given** fixture gồm direct app route, nested router, multi-method route, router chưa gắn entrypoint và cùng router gắn ở nhiều prefix
- **when** scan app đã chọn
- **then** chỉ endpoint được expose có method, full path (giữ trailing slash/path param), handler và registration chain đúng; trùng method/path giữ riêng theo chain
- `implementation_target:` [CMP-RKG-ANALYZER]
- `validated_by:` [TEST-RKG-ENDPOINT-EXTRACTION]

#### AC-RKG-005
- **given** dependency wiring ở parameter default, annotation, decorator/app/router/include và sub-dependency function
- **when** scan
- **then** tạo `depends_on` đúng chiều (Callable→Callable hoặc Endpoint→Callable); không chuyển declared dependency thành `calls`; pattern không hỗ trợ ghi warning
- `implementation_target:` [CMP-RKG-ANALYZER]
- `validated_by:` [TEST-RKG-DECLARED-DEPENDENCY]

### Relationship và evidence

#### AC-RKG-003
- **given** import trực tiếp, alias, relative import và binding bị che khuất
- **when** resolve
- **then** imports from SourceUnit resolve to internal SourceUnits/symbols or ExternalDependency without relying on Namespace nodes or using Directory as an import target; ambiguous/star/dynamic targets produce diagnostics, not guessed edges
- `implementation_target:` [CMP-RKG-ANALYZER]
- `validated_by:` [TEST-RKG-IMPORT-RESOLVE]
- `story:` [STORY-RKG-017]

#### AC-RKG-006
- **given** dynamic route, instance/self dispatch, star import hoặc duplicate binding
- **when** scan
- **then** không tạo cạnh suy đoán; diagnostic giải thích lý do unresolved/unsupported
- `implementation_target:` [CMP-RKG-ANALYZER]
- `validated_by:` [TEST-RKG-NO-GUESS]

#### AC-RKG-007
- **given** candidate graph sau extract
- **when** validate trước publish
- **then** mọi edge có endpoint cùng snapshot, rule_id và ít nhất một evidence location hợp lệ; không gộp nhầm Endpoint identity
- `implementation_target:` [CMP-RKG-ANALYZER, CMP-RKG-GRAPH]
- `validated_by:` [TEST-RKG-EVIDENCE]

#### AC-RKG-048
- **given** fixture có handler gọi service/repository nội bộ qua direct import, alias và `await`, đồng thời có constructor, lời gọi cấp module, binding bị che khuất và target mơ hồ
- **when** resolve call sites
- **then** tạo `calls` đúng hướng Callable caller → Callable callee cho từng target resolve duy nhất, kèm evidence tại call site; không tạo `calls` cho invocation kind ngoài profile, lời gọi cấp source unit, shadowed hoặc unresolved target
- `implementation_target:` [CMP-RKG-ANALYZER]
- `validated_by:` [TEST-RKG-CALL-RESOLVE]

### Data resource

#### AC-RKG-013
- **given** declarative models có `__tablename__` literal, schema literal hoặc thiếu schema, cùng tên table khác namespace; kèm case âm tính reflection/dynamic table
- **when** scan với adapter data-access đã chọn
- **then** DataResource và `maps_to` đúng identity theo adapter profile; không gộp theo tên; case âm tính không tạo edge sai
- `implementation_target:` [CMP-RKG-ANALYZER]
- `validated_by:` [TEST-RKG-DB-MAPS]

#### AC-RKG-014
- **given** patterns get/select/insert/update/delete/add thuộc adapter data-access đã công bố trong `REG-ADAPTER-001`
- **when** scan
- **then** `reads`/`writes` và operation metadata đúng DataResource; khai báo operation chưa đủ bằng chứng thực thi không sinh `reads`
- `implementation_target:` [CMP-RKG-ANALYZER]
- `validated_by:` [TEST-RKG-DB-RW]

### Messaging

#### AC-RKG-015
- **given** các pattern publish, consume và subscribe đã đăng ký với topic literal hoặc hằng module
- **when** scan
- **then** publisher/consumer nối đúng MessageChannel + namespace; channel động chỉ warning/unresolved; không lưu payload
- `implementation_target:` [CMP-RKG-ANALYZER]
- `validated_by:` [TEST-RKG-EVENT]

### Configuration

#### AC-RKG-016
- **given** fixture truy cập biến môi trường và configuration object chứa secret sentinel
- **when** scan, query, export context hoặc ghi report
- **then** key/field và `depends_on` users đúng; sentinel không xuất hiện trong database, report, context hoặc operational log
- `constrained_by:` [NFR-RKG-SEC-001]
- `implementation_target:` [CMP-RKG-ANALYZER, CMP-RKG-GRAPH]
- `validated_by:` [TEST-RKG-CONFIG]

### Type hierarchy

#### AC-RKG-017
- **given** abstraction/interface và base type thông thường trong fixture
- **when** scan
- **then** `implements` chỉ cho declaration abstraction/interface explicit; `inherits_from` giữ direct base; Type chỉ trùng member không tạo `implements`
- `implementation_target:` [CMP-RKG-ANALYZER]
- `validated_by:` [TEST-RKG-CLASS-REL]

### Detection và adapter selection

#### AC-RKG-020
- FastAPI may extract known static patterns with unknown version when its adapter
  explicitly opts in; support remains `version_unverified`, with an executed-adapter
  record and warning. Known incompatible versions remain excluded. See
  REG-ADAPTER-001 for the static factory, literal-loop and empty-path profile.
- **given** registry fixtures gồm declared-only, multiple clients, unknown/unsupported version và từng entry registry MVP
- **when** detect
- **then** candidate/evidence và `supported_patterns` / `detected_only` / `version_unverified` / `unsupported_version` khớp hoàn toàn; thiếu deep adapter không làm hỏng graph cấu trúc mã nguồn / HTTP route / external
- `implementation_target:` [CMP-RKG-ANALYZER]
- `validated_by:` [TEST-RKG-DETECT]

#### AC-RKG-021
- **given** local module shadowing tên thư viện, import/distribution khác tên, hai technology cùng hệ sinh thái nhưng khác capability contract
- **when** resolve/detect
- **then** không nhận nhầm distribution từ tên; technology ngoài contract không bị coi là deep-supported nếu ngoài contract
- `implementation_target:` [CMP-RKG-ANALYZER]
- `validated_by:` [TEST-RKG-DETECT-NEG]

#### AC-RKG-040
- **given** detection tìm thấy nhiều application entrypoint candidate (module/symbol)
- **when** chưa có lựa chọn explicit, rồi người dùng submit app candidate hợp lệ
- **then** lần đầu trả `app_selection_required` với ordered candidates và không đoán/publish; lần sau snapshot ghi app đã chọn cùng evidence và không tự đổi ở re-index kế tiếp
- `implementation_target:` [CMP-RKG-ANALYZER, CMP-RKG-TRANSPORT]
- `validated_by:` [TEST-RKG-DETECTION-OVERRIDE]

#### AC-RKG-052
- **given** detection tìm thấy đúng một application entrypoint cấp module
- **when** detect/index
- **then** tự chọn app đó, snapshot ghi module/symbol + evidence và không yêu cầu người dùng chọn
- `implementation_target:` [CMP-RKG-ANALYZER]
- `validated_by:` [TEST-RKG-APP-AUTOSELECT]

#### AC-RKG-053
- **given** detection tìm thấy đồng thời nhiều technology/deep adapter hợp lệ (ví dụ data-access và messaging)
- **when** index mà người dùng không gửi adapter override
- **then** tất cả detection/capability có evidence được công bố và adapter tương ứng cùng chạy; không trả `app_selection_required`, không buộc chọn một adapter thắng và không chặn publish
- `implementation_target:` [CMP-RKG-ANALYZER, CMP-RKG-TRANSPORT]
- `validated_by:` [TEST-RKG-MULTI-ADAPTER]

#### AC-RKG-065
- **given** selected web-framework adapter khai báo `entrypoint_required=true`, detection có evidence framework application nhưng không resolve được application entrypoint theo contract
- **when** detect kết thúc
- **then** job là `failed` với `app_unresolved`, không publish candidate snapshot và report nêu cách cung cấp module/symbol override
- `implementation_target:` [CMP-RKG-ANALYZER, CMP-RKG-TRANSPORT]
- `validated_by:` [TEST-RKG-APP-UNRESOLVED]

Repository không detect web framework hoặc adapter khai báo không cần application
entrypoint vẫn được publish structural graph; core không áp dụng yêu cầu entrypoint
toàn cục.

### External dependency

#### AC-RKG-022
- **given** các dependency-manifest fixture thuộc adapter profile gồm groups/markers, includes/cycle, lock-only, dynamic metadata; và usage qua direct import, alias import và symbol import
- **when** scan metadata và usage
- **then** version provenance đúng nguồn; `lock_only` / `declared_no_observed_import` ghi rõ; không suy version từ môi trường analyzer; Callable dùng symbol external (trực tiếp hoặc alias) tạo `depends_on` ExternalDependency đúng target; không tạo external call graph
- `constrained_by:` [NFR-RKG-SEC-001]
- `implementation_target:` [CMP-RKG-ANALYZER]
- `validated_by:` [TEST-RKG-PKG-INVENTORY]

#### AC-RKG-023
- **given** các outbound HTTP client thuộc adapter profile với URL absolute literal và URL động/config
- **when** scan
- **then** chỉ literal origin được deduplicate thành http_service; credential/query/payload/raw sensitive path không xuất hiện trong output; URL động unresolved
- `constrained_by:` [NFR-RKG-SEC-001]
- `implementation_target:` [CMP-RKG-ANALYZER]
- `validated_by:` [TEST-RKG-HTTP-INVENTORY]

## Focused-flow extraction profile

Python 2.1 resolves local constructor receivers, unique assignments, typed parameters,
self/cls, constructor-initialized attributes and uniquely inherited methods. A helper
parameter may be inferred only when all resolved call sites agree on a known type.
Reassignment, conditional bindings and conflicting types remain diagnostic; source is
never executed. SQLAlchemy 2.1 explicitly opts into extraction with unknown version
while retaining version_unverified and a warning. Known incompatible versions stay
blocked. Fluent refinements of one query preserve its model only for known methods.

Generic repository model binding requires an explicit model constructor argument or
matching generic base plus super-constructor argument. Concrete model access is recorded
at the calling Callable with call-site and implementation evidence. Shared generic methods
never gain edges to every caller's table. ORM mutation followed by flush is recognized
only with a known model parameter and unshadowed mutation primitive.

## Revision 12

`AC-RKG-002` and `AC-RKG-003` record `story: [STORY-RKG-017]`. Earlier story
lists that named `STORY-RKG-004` for those AC are historical. No other AC in
this file changed.
