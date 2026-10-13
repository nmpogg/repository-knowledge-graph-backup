---
uid:
key: CMP-RKG-WEB
type: component
group: normative
scope: system
system: SYS-RKG
status: draft
revision: 9
change_set: CHG-RKG-2026-002
ownership: {accountable_team: TEAM-RKG, accountable_role: architect}
relations: {realizes: [CAP-RKG-002, CAP-RKG-003], constrained_by: [NFR-RKG-UX-001]}
classification: internal
ai_assisted: true
---
# CMP-RKG-WEB - React web application

React + Vite UI: repository management, snapshot history/lifecycle,
onboarding/job/Explorer/evidence/dependency/technology thuộc
`CAP-RKG-002`; conversation workspace thuộc `CAP-RKG-003`. Data client tách
mock/live nhưng dùng cùng types; UI không giữ bản sao authoritative của
graph/history. Explorer có thêm nút Structure; cây đọc từ search của snapshot,
không bản sao graph và không surface mới.
Job monitor poll theo contract và dừng khi terminal/unmount; Q&A hiển thị pending,
timeout/error rõ ràng thay vì giả lập token streaming.

## Internal structure

Pages cho repository, job, Explorer và conversation dùng một `RkgClient`. Live
client map wire JSON, gồm `Namespace` ↔ UI `module`. Mock client dùng cùng type.
Structure tree là projection trên kết quả search, không phải store thứ hai.

## Sequence

Shell chọn repository rồi gọi live hoặc mock client cùng type. Repository form,
detail, job monitor, Explorer và conversation đều đọc API của snapshot hoặc
repository đang chọn. Structure ghép entity trả về thành cây hiển thị; không
giữ graph riêng.

## Failure mode

Lỗi API giữ form đang sửa khi contract nói giữ draft (`invalid`, conflict,
network). Job `409 index_job_busy` không tạo job thứ hai trên UI. Poll dừng khi
job terminal hoặc view unmount. Không có token streaming để che timeout.

## Transaction boundary

Trình duyệt không giữ bản ghi graph hay conversation. Mọi thay đổi đi qua lệnh API.
UI không mở transaction storage.

## Idempotency

Không phải mutation nào cũng gửi `expected_revision` hoặc `client_request_id`.

- `PATCH /repositories/{id}` gửi `expected_revision`. `409 repository_conflict`
  giữ form.
- `POST /conversations/{id}/turns` gửi `client_request_id` và
  `expected_revision`.
- `POST /repositories`, `DELETE /repositories/{id}`,
  `POST /repositories/{id}/index-jobs`, activate/delete snapshot, và
  create/delete conversation không gửi hai field đó.

UI không gộp hai lần ghi xung đột thành một.

## Concurrency

Poll job dừng khi job terminal hoặc view unmount. Hai tab không chia sẻ authority
trong bộ nhớ. Mỗi request gắn repository và snapshot đang chọn.

## Directory presentation

Graph/List/search/Structure use the same canonical Directory API identity. Structure
must not synthesize a second selectable node for an existing Directory path. Details
show relative path and structural evidence without source excerpts. API của
snapshot cũ vẫn trả `Namespace`. Client map `Namespace` sang type UI `module`
và map ngược `module` thành `Namespace` khi search. `structureTree` gộp
`Namespace` và `SourceUnit` cùng file thành một node file. Mapping này là
projection lúc hiển thị; không đổi ID lưu trong snapshot. Directory hiển thị
như folder với nhãn thư mục đã bản địa hóa.

## Conversational presentation — CHG-RKG-2026-002

Revision 9 selects the presentation in ADR-2026-007 / UXF-RKG-002 for
AC-RKG-074…081. It is a review candidate; live runtime is not changed by this spec.

### Structure and sequence

UI sends an explicit vi/en preference as defined by the future L3 contract. Backend
language wins for the answer; UI chrome follows UI locale. Switching UI locale
must not rewrite old answers. After submit and after reload, render the same stored
answer, source references and limitation state. Never infer missing persisted flags
as false or recompute an old answer in the browser.

Conversation bubble has one natural answer first, source controls with readable
labels, then a secondary collapsed details region for qualified names/relations.
Claims are retained for verification/inspection but are not printed a second time
by default. Insufficient evidence uses the server explanation once, with a localized
fallback only if no answer exists. Dynamic status must not announce duplicate text.
Clarification explains ambiguity and shows ordered options with type and safe
method/path or relative module metadata. Selecting one continues original intent.

### Failure and source handling

Translate technical errors/limitation codes to outcome and next action. Show partial
coverage beside answer; raw codes are secondary details. Historical missing metadata
is labeled unknown, not complete. Provider errors keep draft/history; unavailable
snapshot disables submit and marks sources unavailable without retargeting.

Citation controls use edge/evidence identity, not just target entity. Resolve the
requested evidence in the pinned snapshot and show only its safe relative location;
if entity detail cannot supply it, show unavailable rather than another evidence.
Physical line markers are omitted for filesystem provenance. All text is escaped,
no raw source/HTML/model free prose is trusted. Existing a11y/dialog focus rules apply.

### Transaction, idempotency and concurrency

The browser is not a persistence authority. Transport contract owns payload shape;
mock/live client and types must move together once Contract Gate is ready. All turn
requests keep client_request_id/expected_revision, and L3 must include language in
semantic replay equality. Pending locks duplicate submit/delete, not historical
source access. Conflict keeps draft and requires intentional reload/retry.
