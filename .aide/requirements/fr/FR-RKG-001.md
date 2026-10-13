---
uid:
key: FR-RKG-001
type: functional-requirement
group: normative
scope: system
system: SYS-RKG
status: approved
revision: 7
ownership:
  accountable_team: TEAM-RKG
  accountable_role: product-owner
relations:
  satisfies: [GOAL-RKG-001, GOAL-RKG-002]
  constrained_by: [NFR-RKG-SEC-001, NFR-RKG-REL-001, NFR-RKG-PERF-001, NFR-RKG-UX-001]
classification: internal
ai_assisted: true
---

# FR-RKG-001 — Quản lý repository, index job và snapshot

## Mô tả

Hệ thống quản lý catalog repository từ thư mục local, khởi chạy và theo dõi index job, tạo scan report, rồi publish candidate graph hợp lệ thành snapshot bất biến. Mỗi job và snapshot thuộc đúng một repository; lỗi không thay active snapshot. UI, API và CLI cùng tuân theo lifecycle, concurrency, isolation và deletion guard.

## Acceptance Criteria

### Tiếp nhận source local và thực thi job

#### AC-RKG-001
- **given** fixture repository có side effect ở cấp module khi import
- **when** chạy index
- **then** scan thành công mà không import hoặc thực thi source; không tạo side effect từ fixture
- `constrained_by:` [NFR-RKG-SEC-001]
- `implementation_target:` [CMP-RKG-ANALYZER]
- `validated_by:` [TEST-RKG-SCAN-SAFE]

#### AC-RKG-026
- **given** path hoặc nội dung source chứa shell metacharacters, path ngoài allowlist, hoặc chỉ dẫn độc hại
- **when** submit index cho repository
- **then** allowlist path chặn shell/network/code ngoài contract; không lộ đường dẫn tuyệt đối host trong error
- `constrained_by:` [NFR-RKG-SEC-001]
- `implementation_target:` [CMP-RKG-ANALYZER, CMP-RKG-TRANSPORT]
- `validated_by:` [TEST-RKG-INDEX-INJECTION]

#### AC-RKG-034
- **given** một index job đang ở trạng thái chưa kết thúc
- **when** client thứ hai submit index job cho cùng hoặc repository khác
- **then** request thứ hai nhận `409 index_job_busy`; job đang chạy không bị hủy hoặc thay cấu hình và không có candidate snapshot thứ hai được publish
- `constrained_by:` [NFR-RKG-REL-001]
- `implementation_target:` [CMP-RKG-ANALYZER, CMP-RKG-TRANSPORT]
- `validated_by:` [TEST-RKG-INDEX-SINGLE-WRITER]

#### AC-RKG-051
- **given** repository local có path nằm ngoài `allowed_local_roots`, hoặc symlink/junction trong source trỏ ra ngoài canonical repository root
- **when** đăng ký repository, submit index hoặc dựng manifest
- **then** hệ thống trả `source_outside_allowed_roots` hoặc `source_link_escape`, không đọc nội dung đích, không tạo candidate snapshot và không sửa filesystem người dùng
- `constrained_by:` [NFR-RKG-SEC-001]
- `implementation_target:` [CMP-RKG-ANALYZER, CMP-RKG-TRANSPORT]
- `validated_by:` [TEST-RKG-SOURCE-BOUNDARY]

#### AC-RKG-055
- **given** repository local hợp lệ và một tập input CLI không hợp lệ hoặc job thất bại
- **when** chạy `rkg index --repository <id>` hoặc `rkg serve`
- **then** CLI dùng cùng validation/error contract với API; `index` trả exit `0` khi job thành công và `1` khi validation/job lỗi; `serve` mặc định bind `127.0.0.1` với đúng một worker
- `constrained_by:` [NFR-RKG-SEC-001, NFR-RKG-REL-001]
- `implementation_target:` [CMP-RKG-TRANSPORT, CMP-RKG-ANALYZER]
- `validated_by:` [TEST-RKG-CLI]

### Báo cáo, re-index và publication

#### AC-RKG-008
- **given** source được thêm/sửa/xóa giữa hai lần index
- **when** lần hai thành công
- **then** một snapshot mới của cùng repository phản ánh đúng thay đổi và không còn entity cũ đã xóa; snapshot trước vẫn đọc được khi còn retained; nếu lần hai lỗi thì active snapshot trước vẫn active
- `constrained_by:` [NFR-RKG-REL-001]
- `implementation_target:` [CMP-RKG-GRAPH, CMP-RKG-ANALYZER]
- `validated_by:` [TEST-RKG-REINDEX]

#### AC-RKG-012
- **given** một hoặc nhiều file có parse error nhưng application entrypoint vẫn resolve và candidate graph còn validate được
- **when** job kết thúc
- **then** job là `succeeded_with_warnings`, publish phần hợp lệ, report có diagnostic theo từng file và UI/API không phát minh trạng thái `partial`
- `constrained_by:` [NFR-RKG-REL-001]
- `implementation_target:` [CMP-RKG-ANALYZER, CMP-RKG-TRANSPORT, CMP-RKG-WEB]
- `validated_by:` [TEST-RKG-PARTIAL-ERRORS]

#### AC-RKG-049
- **given** source có số file vượt `max_files`
- **when** dựng manifest
- **then** job là `failed` với `file_limit_exceeded`, không publish candidate snapshot và active snapshot của repository không đổi
- `constrained_by:` [NFR-RKG-REL-001]
- `implementation_target:` [CMP-RKG-ANALYZER, CMP-RKG-TRANSPORT]
- `validated_by:` [TEST-RKG-FILE-LIMIT]

#### AC-RKG-050
- **given** một file vượt `max_file_bytes` nhưng source còn file hợp lệ
- **when** scan
- **then** file quá lớn không được đọc/parse, report ghi skip + warning theo relative path; job có thể `succeeded_with_warnings` nếu candidate còn lại validate được
- `constrained_by:` [NFR-RKG-REL-001]
- `implementation_target:` [CMP-RKG-ANALYZER]
- `validated_by:` [TEST-RKG-LARGE-FILE-SKIP]

#### AC-RKG-038
- **given** job thành công, thành công có warning hoặc thất bại
- **when** đọc scan report qua API/UI
- **then** report có số file xét/parse/bỏ qua/lỗi, entity/edge theo loại, unresolved, warning/error, duration và capability/support state; các tổng số nhất quán với snapshot hoặc candidate tương ứng
- `implementation_target:` [CMP-RKG-ANALYZER, CMP-RKG-TRANSPORT, CMP-RKG-WEB]
- `validated_by:` [TEST-RKG-SCAN-REPORT]

#### AC-RKG-039
- **given** benchmark corpus và máy tham chiếu được mô tả bởi NFR-RKG-PERF-001
- **when** chạy full scan sau checkout sẵn
- **then** báo cáo wall time, analyzer peak RAM, cấu hình máy và kết quả đạt hoặc không đạt từng ngưỡng NFR; LLM latency không được trộn vào số đo
- `constrained_by:` [NFR-RKG-PERF-001]
- `implementation_target:` [CMP-RKG-ANALYZER]
- `validated_by:` [TEST-RKG-SCAN-BENCHMARK]

### Onboarding và theo dõi job

#### AC-RKG-027
- **given** local fixture và UI/API sẵn sàng
- **when** người dùng đăng ký local repository rồi chạy index
- **then** UI hiện stage/detection/report, mở được graph và evidence; nếu index lỗi thì lỗi có thể xử lý và snapshot trước vẫn truy cập được
- `constrained_by:` [NFR-RKG-UX-001, NFR-RKG-REL-001]
- `implementation_target:` [CMP-RKG-WEB, CMP-RKG-TRANSPORT]
- `validated_by:` [TEST-RKG-ONBOARDING-E2E]

#### AC-RKG-043
- **given** job validation trả nhiều application entrypoint candidate có ordered IDs, đồng thời có thể trả nhiều technology/adapter detection
- **when** người dùng chọn app candidate trên UI và submit lại
- **then** UI không auto-select app, gửi đúng app ID/revision và giữ lựa chọn khi retry/re-index; danh sách technology/adapter chỉ là capability panel/optional override, không mở blocking modal
- `constrained_by:` [NFR-RKG-UX-001, NFR-RKG-REL-001]
- `implementation_target:` [CMP-RKG-WEB, CMP-RKG-TRANSPORT]
- `validated_by:` [TEST-RKG-ONBOARDING-SELECTION]

#### AC-RKG-054
- **given** local path hợp lệ trong allowlist, path không tồn tại và path ngoài allowlist
- **when** người dùng đăng ký repository qua UI/API
- **then** path hợp lệ đi qua stage/report/graph flow; path không tồn tại hoặc ngoài allowlist trả mã lỗi riêng, không tạo job/candidate và không sửa filesystem người dùng
- `constrained_by:` [NFR-RKG-UX-001, NFR-RKG-SEC-001, NFR-RKG-REL-001]
- `implementation_target:` [CMP-RKG-WEB, CMP-RKG-TRANSPORT, CMP-RKG-ANALYZER]
- `validated_by:` [TEST-RKG-LOCAL-ONBOARDING-E2E]

#### AC-RKG-058
- **given** `POST /api/v1/repositories/{repository_id}/index-jobs` thiếu/sai `X-RKG-Session`, hoặc Origin/Host ngoài allowlist
- **when** submit repository index job
- **then** API trả `401` trước khi tạo job hoặc đọc source; response/log không lộ session token hay absolute host path
- `constrained_by:` [NFR-RKG-SEC-001]
- `implementation_target:` [CMP-RKG-TRANSPORT]
- `validated_by:` [TEST-RKG-INDEX-SESSION]

#### AC-RKG-061
- **given** job chưa terminal và client đang poll `GET /api/v1/index-jobs/{job_id}`
- **when** server trả `Retry-After`, job terminal hoặc view unmount
- **then** client chờ interval được chỉ định (backoff không vượt contract), dừng ở terminal và hủy request/timer ngay khi unmount; không còn phantom request
- `constrained_by:` [NFR-RKG-UX-001, NFR-RKG-REL-001]
- `implementation_target:` [CMP-RKG-WEB, CMP-RKG-TRANSPORT]
- `validated_by:` [TEST-RKG-JOB-POLLING]

### Vòng đời repository và snapshot

#### AC-RKG-066
- **given** local path hợp lệ và local session hợp lệ
- **when** người dùng tạo repository rồi gọi list/detail
- **then** API trả repository bền vững với ID, revision, display name, source type, source locator đã redact, defaults, active snapshot nullable và timestamps; không tự tạo job/snapshot; list phân trang, newest-updated-first với tie-break ID deterministic
- `constrained_by:` [NFR-RKG-UX-001, NFR-RKG-SEC-001]
- `implementation_target:` [CMP-RKG-GRAPH, CMP-RKG-TRANSPORT, CMP-RKG-WEB, API-RKG-CORE-v1]
- `validated_by:` [TEST-RKG-REPOSITORY-CRUD]

#### AC-RKG-067
- **given** repository đã tồn tại với source identity và `revision`
- **when** PATCH metadata/defaults với `expected_revision` đúng, sai hoặc yêu cầu đổi source identity
- **then** update hợp lệ tăng revision; revision sai trả `409 repository_conflict`; đổi source identity trả `422 repository_source_immutable`; không làm thay đổi snapshot cũ
- `constrained_by:` [NFR-RKG-REL-001, NFR-RKG-SEC-001]
- `implementation_target:` [CMP-RKG-GRAPH, CMP-RKG-TRANSPORT, API-RKG-CORE-v1]
- `validated_by:` [TEST-RKG-REPOSITORY-UPDATE]

#### AC-RKG-068
- **given** repository hợp lệ có hoặc chưa có snapshot
- **when** submit index/re-index và đọc snapshot list/detail
- **then** job thuộc đúng `repository_id`; publish thành công tạo snapshot mới chứa source revision dạng `manifest:<sha256>`, manifest hash, analyzer/schema/adapter versions và scan-config digest; list newest-first với tie-break ID deterministic; failure không đổi active snapshot của repository đó
- `constrained_by:` [NFR-RKG-REL-001]
- `implementation_target:` [CMP-RKG-ANALYZER, CMP-RKG-GRAPH, CMP-RKG-TRANSPORT, API-RKG-CORE-v1]
- `validated_by:` [TEST-RKG-REPOSITORY-SNAPSHOT-HISTORY]

#### AC-RKG-069
- **given** repository có snapshot khả dụng không phải active snapshot
- **when** người dùng activate snapshot đó
- **then** hệ thống atomically đổi `active_snapshot_id` của đúng repository và mở Explorer trên snapshot đã chọn; không tạo job, không đổi conversation pin và không ảnh hưởng active snapshot của repository khác
- `constrained_by:` [NFR-RKG-REL-001, NFR-RKG-UX-001]
- `implementation_target:` [CMP-RKG-GRAPH, CMP-RKG-TRANSPORT, CMP-RKG-WEB, API-RKG-CORE-v1]
- `validated_by:` [TEST-RKG-SNAPSHOT-ACTIVATE]

#### AC-RKG-070
- **given** snapshot là active, có reader, có conversation reference hoặc không còn reference
- **when** người dùng yêu cầu xóa snapshot
- **then** ba trường hợp có guard trả `409 snapshot_active` hoặc `snapshot_in_use`; trường hợp không còn reference xóa graph/evidence/diagnostic liên quan atomically và snapshot không còn trong list; snapshot/repository khác không bị ảnh hưởng
- `constrained_by:` [NFR-RKG-REL-001]
- `implementation_target:` [CMP-RKG-GRAPH, CMP-RKG-TRANSPORT, API-RKG-CORE-v1]
- `validated_by:` [TEST-RKG-SNAPSHOT-DELETE-GUARD]

#### AC-RKG-071
- **given** repository có job chưa terminal, reader/conversation reference hoặc chỉ còn dữ liệu không được tham chiếu
- **when** người dùng xác nhận xóa repository
- **then** trường hợp bận/tham chiếu trả `409 repository_busy` hoặc `repository_in_use`; trường hợp hợp lệ xóa repository cùng job/snapshot con trong một operation nhất quán; không xóa dữ liệu repository khác
- `constrained_by:` [NFR-RKG-REL-001, NFR-RKG-UX-001]
- `implementation_target:` [CMP-RKG-GRAPH, CMP-RKG-TRANSPORT, CMP-RKG-WEB, API-RKG-CORE-v1]
- `validated_by:` [TEST-RKG-REPOSITORY-DELETE-GUARD]

#### AC-RKG-072
- **given** có hai repository và các request dùng repository/snapshot ID không cùng ownership hoặc source locator chứa dữ liệu host nhạy cảm
- **when** gọi lifecycle, graph hoặc conversation API và render management UI
- **then** mismatch trả `404` không tiết lộ ownership; mọi query chỉ trả dữ liệu cùng repository/snapshot; locator/error/log được redact; UI có loading/empty/error/confirm/conflict states và keyboard/focus/status semantics theo NFR
- `constrained_by:` [NFR-RKG-SEC-001, NFR-RKG-REL-001, NFR-RKG-UX-001]
- `implementation_target:` [CMP-RKG-GRAPH, CMP-RKG-TRANSPORT, CMP-RKG-WEB, CMP-RKG-CONVERSATION]
- `validated_by:` [TEST-RKG-REPOSITORY-ISOLATION, TEST-RKG-REPOSITORY-MANAGEMENT-A11Y]
