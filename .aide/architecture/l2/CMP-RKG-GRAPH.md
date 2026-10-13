---
uid:
key: CMP-RKG-GRAPH
type: component
group: normative
scope: system
system: SYS-RKG
status: draft
revision: 9
ownership: {accountable_team: TEAM-RKG, accountable_role: architect}
relations: {realizes: [CAP-RKG-002, CAP-RKG-003], constrained_by: [NFR-RKG-PERF-001, NFR-RKG-REL-001]}
classification: internal
ai_assisted: true
---
# CMP-RKG-GRAPH - Graph and storage component

## Responsibilities

Repository catalog persistence, graph validation, Kùzu schema/migration (gồm bảng
operational/conversation theo `TBL-RKG-GRAPH`), atomic snapshot publication/
activation/deletion, search, traversal, context assembly và read-only retrieval cho
grounded Q&A. Là authority duy nhất của physical schema và connection/storage façade
trên embedded DB.

## Internal structure

Catalog repository/snapshot/job nằm ở storage façade. Publish validate rồi ghi graph
trong một transaction. Đọc graph là search, traversal và context trên snapshot đã
pin. Conversation row dùng cùng schema nhưng không có writer process riêng.

## Sequence

Publish nhận `FactBatch` đã extract: validate, rồi một transaction ghi snapshot,
entity, evidence, diagnostic, edge và (mặc định) active pointer. Đọc graph resolve
snapshot, pin reader cho request đó, rồi search/traversal/context. Dọn job/repository
xóa các nhãn graph của snapshot hoặc job, gồm cả `ScanFile` và `TechnologyDetection`
nếu các row đó tồn tại.

## Transaction boundary

Prepare/parse/extract chạy ngoài database transaction. Một transaction ngắn ghi graph
đã validate và đổi active pointer của đúng repository; lỗi rollback toàn bộ publication.
Repository update dùng optimistic revision. Activate/delete repository hoặc snapshot
dùng transaction ngắn với ownership/reference guards; không giữ transaction khi
parse/extract hoặc chờ reader.
`CMP-RKG-CONVERSATION` persist turn/state qua storage API/schema của component này,
không mở writer path song song ra ngoài single-writer process.

Publication transaction không bao trùm cả job. `IndexCoordinator` giữ writer lock
suốt scan, parse, extract và publish. API gọi storage qua `call_when_idle`, nên
lượt đọc graph chờ đến khi lock đó được thả, kể cả khi request chỉ pin snapshot.

## Idempotency

Publication lỗi thì rollback, không để lại snapshot dở. Kích hoạt lại đúng snapshot
đang active không đổi repository khác. Cùng snapshot và cùng request context thì
payload đọc ra có cùng thứ tự.

## Failure mode

Candidate không qua validation thì không đổi active pointer. Xóa bị guard trả xung
đột và không xóa một phần graph, evidence hay conversation reference.

## Concurrency

Trong một lần đọc, reader pin `repository_id`/`snapshot_id`. Trước khi tới pin đó,
request API chờ writer lock của process: cùng lock mà coordinator giữ suốt job.
Cleanup và explicit delete có active-pointer, active-reader, non-terminal-job và
conversation reference guards. Query deterministic với explicit budget/truncation;
cross-repository mismatch bị từ chối.

## Operational tables without a current writer

`ScanFile` và `TechnologyDetection` có trong schema. Code hiện tại chỉ xóa chúng
theo `job_id` hoặc `snapshot_id`. Không có writer tạo row `ScanFile` hoặc
`TechnologyDetection`. Technology mà API trả về đi theo
`adapter/detection → Job.report_json → GET /technologies` khi bảng không có row.
Xem `TBL-RKG-GRAPH`.

## Directory publication and compatibility

Validate Directory identity, containment and manifest-backed path provenance
separately from syntax evidence. Directory uses Entity rows; physical CONTAINS
requires Repository/Entity source support through a non-destructive migration.
Existing Namespace snapshots, relationships, IDs and active/conversation references
remain immutable. New scans publish Directory snapshots. Contract approval requires
execution of revised DDL and migration fixtures; TBL revision 12 keeps the
physical tables of revision 11 and SchemaMeta version 2, and records which
operational tables have no current writer. DDL execution and
migration/history-retention checks are recorded in TEST-RKG-DIRECTORY-IMPLEMENTATION-001;
Contract Gate remains pending until a new approval record is issued.

## Focused graph traversal

Subgraph/context requests add view=flow|neighborhood, include_structure and
include_dependencies. API defaults remain neighborhood with both overlays off.
Flow policy depends on root type: downstream calls/accesses for endpoint/callable;
incoming users then callers for resources; own methods/maps for a type. Terminal
resources never expand to unrelated users in downstream flow. Ownership is a separate
ancestor overlay after semantic BFS and consumes node/edge budgets without semantic
depth. Files/dirs added by the overlay are not traversal seeds. Both modes retain
pinned reads, deterministic output, cycle handling and truncation evidence. No DDL or
semantic entity/edge identity changes are required; SchemaMeta remains 2. TBL
revision 12 does not add tables.

`include_dependencies=false` không tắt mọi cạnh `depends_on` trong `view=flow`.
Khi root là `DataResource`, `MessageChannel`, `Configuration` hoặc
`ExternalDependency`, traversal vẫn thêm cạnh `depends_on` của chính root đó.
Root UI navigation `Endpoint` (`kind=navigation` / `framework_kind=react-router`,
OQ-RKG-007) cũng mở `depends_on` trong flow để tới Configuration /
ExternalDependency. Root HTTP `Endpoint` và Callable khác chỉ nhận `depends_on`
khi `include_dependencies=true`. `view=neighborhood` vẫn lọc theo `direction` và
`edge_types`; cờ `include_dependencies` không tự loại cạnh trong neighborhood.
