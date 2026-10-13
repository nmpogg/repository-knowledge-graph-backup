---
key: PLAN-CHG-RKG-2026-002
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
revision: 1
captured_at: 2026-10-06
change_set: CHG-RKG-2026-002
stage: change-planning-before-definition-of-ready
non_normative: true
implementation_ready: false
captured_against:
  code_commit: 86ecab6546384227d1901e24c8b8fbfc6c0e8527
  code_tree: 6868e73b8d0b5abdecdd9a64265596d8fe809548
  context: CTX-CHG-RKG-2026-002
  request: CR-RKG-002
process_reference: docs/reference/agentic-sdlc/agentic-sdlc-workflow-reference.md
classification: internal
ai_assisted: true
---
# PLAN-CHG-RKG-2026-002 — Chatbot dễ hỏi và trả lời tự nhiên

## Mục tiêu và vị trí trong quy trình

Đề xuất cải thiện chatbot để người dùng hỏi bằng ngôn ngữ quen thuộc, hiểu kết quả
ngay và biết làm gì tiếp khi câu hỏi chưa rõ hoặc dữ liệu chưa đủ. Câu trả lời vẫn
thuộc đúng snapshot, phân biệt gọi trực tiếp/gián tiếp và có bằng chứng kiểm tra được.

Đây là plan chuẩn bị cho flow Change, không phải implementation plan đã đủ điều
kiện code ở B.14. Hiện mới thực hiện intake/context khảo sát và tạo change-set shell
(B.3–B.4). Yêu cầu, L2, UI/UX và baseline cho thay đổi này chưa được duyệt.
Không tạo Epic/Story/Task trước bước decomposition B.12; sau khi design/contract
đủ điều kiện, tạo bộ CTX-TASK / PLAN-TASK / DIARY-TASK cho từng lát cắt.

`.aide/` vẫn là nguồn chuẩn tắc. Tài liệu workflow được dùng làm quy trình theo
yêu cầu của user; plan này không thay FR/AC, không tự ký gate hoặc sửa approval cũ.
Không sửa runtime code trong lượt viết plan này.

## Chẩn đoán từ current tree

| Hiện trạng đã đọc trong code | Ảnh hưởng người dùng | Nơi liên quan |
|---|---|---|
| Model chỉ chọn edge IDs; backend nối các câu quan hệ đơn lẻ | Câu trả lời giống danh sách cạnh graph, thiếu dẫn giải | `src/rkg/conversations/grounded.py` |
| Backend đoán tiếng Việt bằng ký tự có dấu | Câu hỏi Việt không dấu có thể nhận phản hồi tiếng Anh | `src/rkg/conversations/grounded.py` |
| Regex ưu tiên tên có dấu chấm/gạch dưới; planner còn lại tìm bằng chuỗi | Người dùng phải biết tên kỹ thuật; method/path chưa có bước resolve riêng | `grounded.py`, `src/rkg/graph/search.py` |
| Loại cạnh theo từ khóa được dùng làm bộ lọc traversal | Có nguy cơ bỏ cạnh nối endpoint tới handler trước khi tìm calls; phải tái hiện bằng fixture | `grounded.py`, `src/rkg/graph/context.py` |
| Context đi hai chiều, depth cố định | Kết quả có thể lẫn lời gọi trực tiếp, gián tiếp, caller và vượt budget | `grounded.py`, `src/rkg/graph/traversal.py` |
| UI hiển thị answer và toàn bộ claims bên dưới | Thông tin lặp và tên dài làm đoạn chat khó đọc | `frontend/src/pages/conversations/ConversationPage.tsx` |
| UI thêm thông báo insufficient rồi tiếp tục hiện answer | Một trạng thái xuất hiện hai lần | `ConversationPage.tsx` |
| UI hiển thị truncation reason kỹ thuật | Người dùng không biết dữ liệu còn thiếu và cách thu hẹp câu hỏi | `ConversationPage.tsx`, `frontend/src/i18n/{vi,en}.ts` |
| Citation mở evidence của entity đích, chưa đối chiếu evidence_id của citation trong UI | Cần xác minh bằng chứng hiện ra có đúng phát biểu đã chọn | `ConversationPage.tsx` |

Các mục trên là phân tích tĩnh, chưa phải kết quả test tái hiện. Không kết luận
mọi endpoint đều lỗi, citation rỗng, hay provider hiện đã cấu hình từ lời kể.

## Phạm vi đề xuất để Product chốt

- Câu trả lời Việt/Anh rõ ràng; hỗ trợ nhận diện câu hỏi Việt không dấu và fallback
  theo locale. Cách truyền locale phải được chốt ở contract, không đoán từ UI.
- Mở đầu trả lời đúng câu hỏi, dùng tên ngắn có thể phân biệt, giữ tên đầy đủ trong
  chi tiết. Nêu rõ thực thể nào đang được giải thích.
- Với câu hỏi gọi hàm: lời gọi trực tiếp đứng trước; gọi gián tiếp chỉ có khi đường
  đi đã được kiểm tra và được ghi rõ. Không suy diễn nghiệp vụ từ tên hàm.
- Clarification giải thích vì sao cần chọn, cho biết loại thực thể/method/path;
  không bắt người dùng hiểu từ "candidate" hoặc nhập lại qualified name.
- Greeting hướng dẫn cách hỏi về repository; không có claim graph. Thiếu bằng
  chứng được giải thích theo nguyên nhân thực sự và có một hành động tiếp theo.
- Answer không bị lặp thành khối Claims mặc định; chi tiết/citation vẫn truy cập
  được. Cảnh báo dữ liệu một phần viết bằng ngôn ngữ người dùng.
- Citation dẫn đúng evidence của phát biểu, dùng relative path/line; không hiện
  raw source hoặc absolute path. Trạng thái limitation cần đúng cả sau reload.

Ngoài phạm vi: đổi schema graph/analyzer, đọc raw source cho model, viết code cho
repository đang phân tích, chạy shell/tool ngoài allowlist, thêm model call thứ ba,
streaming, đổi snapshot pin, tự tăng budget để che retrieval không phù hợp.

## Ràng buộc và tiêu chí quyết định trước phương án

1. Mọi quan hệ trong answer phải được hỗ trợ bởi context/evidence của snapshot;
   citation hợp lệ không tự chứng minh một câu diễn giải tùy ý là đúng.
2. Tuân thủ budgets `NFR-RKG-REL-001`, redaction/session/read-only của
   `NFR-RKG-SEC-001` và khả năng truy cập của `NFR-RKG-UX-001`.
3. Giữ transaction pending/finalize, revision/idempotency/concurrency hiện có.
4. Câu trả lời dễ đọc và không làm mờ direction, trực tiếp/gián tiếp hoặc thiếu dữ liệu.
5. Không tăng latency/cost bằng lời gọi paraphrase riêng; dùng tối đa số calls hiện có.
6. Có thể kiểm thử fail-closed, rollback và tương thích với history đã lưu.

## Phương án cần review ở L2

| Phương án | Ưu điểm | Đánh đổi |
|---|---|---|
| A. Backend dựng lời giải thích theo nhóm quan hệ, model chọn facts | Grounding kiểm tra được; ít thay đổi provider/schema | Cách diễn đạt có khuôn, cần mẫu Việt/Anh |
| B. Model trả cấu trúc dẫn giải có tham chiếu edge/path; backend validate rồi render | Sắp xếp linh hoạt; diễn đạt trực tiếp/gián tiếp rõ; phù hợp limits hiện có | Cần schema mới, kiểm tra path/direction và quyết định chỗ nào cho phép text tự do |
| C. Model viết answer tự do kèm citation | Linh hoạt nhất về văn phong | ID citation hợp lệ không bảo đảm nội dung đúng; cần kiểm tra semantic/entailment và eval sâu, có thể vượt budgets |

Khuyến nghị đưa B ra review, có A làm fallback. Chưa chọn phương án thay Architect.
Nếu B cho model viết text tự do, phải chứng minh cách phát hiện claim không có
bằng chứng; schema/regex hoặc có citation đơn thuần chưa đủ. Nếu chưa có giải pháp,
giới hạn factual prose bằng renderer có cấu trúc. C không được ngầm bật bằng cách
thêm field `answer` rồi publish nguyên văn. Không tạo ADR supersedes khi chưa có
quyết định lật ADR nền tảng; nếu có, đánh giá lại flow/tier theo workflow.

## Thứ tự công việc và cách kiểm từng bước

| Bước | File/artifact dự kiến | Việc làm | Kiểm chứng / điều kiện chuyển bước |
|---|---|---|---|
| 1. Intake, B.3–B.4 | `CR-RKG-002.yaml`, change-set shell, `CTX-CHG-RKG-2026-002.yaml` | Ghi yêu cầu, impact ứng viên, tier/flow/confidence/skipped areas | Hash đầu vào; không ghi transcript/config; không sửa `impact.yaml` derived bằng tay |
| 2. FR/AC, B.5 | `.aide/requirements/fr/FR-RKG-005.md`; NFR đối xứng nếu thêm constraint | Product draft revision cho cách trả lời/locale/greeting/clarification; giữ published AC IDs | Diff current AC; ID mới chỉ cấp khi artifact hiện hành định nghĩa; Scope Gate ký đúng revision/hash |
| 3. L1/L2, B.6–B.8 | `CAP-RKG-003`, `CMP-RKG-CONVERSATION`, `CMP-RKG-WEB`; GRAPH/TM/ADR nếu thực sự bị chạm | Chọn phương án; mô tả planner/context/answer validation, failure/fallback, transaction, idempotency, concurrency | FR coverage; 2–3 phương án; review độc lập; Architecture Gate; không mặc định approval cũ áp dụng |
| 4. UX cấp 1–3, B.9 | `UXF-RKG-002`, `SCR-RKG-001`, `UID-RKG-001`; prototype derived có provenance | Sau Scope Gate, làm cùng nhịp L2; mock answer, clarification, insufficient, partial, error và citation | Token thật, keyboard, contrast/light-dark/mobile; người duyệt đi được luồng; UI/UX Gate trước L3 |
| 5. L3 + UIS, B.10–B.11 | `API-RKG-CORE-v1`, `UIS-RKG-001`; TBL chỉ nếu cần persist metadata mới | Chốt locale/status/limitation/citation và tương thích history; không đổi field/status tùy ý | Diff schema bằng máy, consumer mapping mock/live, xét breaking; Contract Gate và UIS cấp 4 |
| 6. Decomposition + context/plan, B.12–B.14 | Epic/Story/Task mới, baseline, bộ `CTX-TASK-*`, `PLAN-TASK-*` | Tách resolve/retrieval, answer, UI thành lát cắt tự đứng được sau design; pin revision/hash | Mỗi Task có một cha, `implements`/AC aligned; Definition of Ready đầy đủ; không mượn TASK-020/021 đã done |
| 7. RED resolve/retrieval, B.15 | `tests/integration/test_grounded_qa.py`, graph fixtures | Tái hiện method/path, tên ngắn/trùng, endpoint→handler→calls, trực tiếp/gián tiếp, caller, Việt không dấu | Fail vì đúng hành vi thiếu; ghi evidence RED theo commit/hash, không log nội dung prompt/answer |
| 8. GREEN resolve/retrieval | `grounded.py`; helper mới cùng module nếu cần; graph chỉ khi L2 yêu cầu | Resolve endpoint bảo thủ; phân biệt connector edges với relations cần trả lời; tập trung neighborhood theo intent | Tests ở bước 7 xanh; mọi query vẫn pin snapshot/read-only, không vượt budget; không tự chọn khi ambiguous |
| 9. RED/GREEN answer | `grounded.py`, provider mock fixtures, `tests/integration/test_grounded_qa.py`, `tests/unit/test_llm_provider.py` | Schema/formatter theo phương án đã duyệt; direct/indirect, greeting, locale, reason-specific insufficient | Unsupported ID/path/direction/text fail-closed; không bịa business semantics; malformed/timeout/disabled fallback; max calls/tokens |
| 10. RED/GREEN API/history | `src/rkg/api/conversations.py`, client types/mappers/mock; `tests/integration/test_conversation_api.py` | Wire contract được duyệt; limitation và locale/history đúng sau reload; giữ guards | Idempotent retry, conflict, restart, pin, foreign IDs, redaction và schema compatibility; DDL chỉ nếu contract yêu cầu migration |
| 11. RED/GREEN UI | `ConversationPage.tsx`, tests, `i18n/{vi,en}.ts`, `index.css` nếu cần | Narrative dễ đọc; details thay duplicate Claims; citation có nhãn; chỉ một insufficient notice; cảnh báo partial dễ hiểu | Component tests: không lặp, keyboard/focus, content escaped, draft kept, reload flags; browser/mobile theo UX đã duyệt |
| 12. Validate + eval, B.16 | Evidence tests, `tests/evaluation/run_pilot_qa.py` nếu rubric cần mapping mới | Focused tests → checks rộng khi cần; mock contract và live quality tách biệt | Rubric `EVAL-RKG-QA-001`/`OBS-RKG-005`; capture code/prompt/schema/model fingerprint và denominators; ghi `not_run` rõ |
| 13. Review/fix/UAT, B.17–B.19 | Review/receipt/findings/approval append-only | Reviewer độc lập không nhận plan/diary/rationale; fixes chỉ theo finding; Business Owner UAT khi đổi FR/AC | Không tự review; freeze hash; Component Merge Gate; UAT trên build/commit được xác định |
| 14. Release/close, B.20–B.21 | Release plan, approvals, deploy verification, diary | Rollback boundary, release được duyệt, xác minh runtime rồi mới cập nhật status | Không mark done chỉ vì test xanh; evidence current-tree + approval/release/verification theo workflow |

Không có CLI `aide` đã được xác minh trong repo. Không ghi "aide verify passed".
Nếu cần generator/checker chưa có, chọn tooling thay thế và ghi provenance/lỗ hổng
coverage; không tự tạo impact derived bằng tay hoặc coi scan đơn giản là full gate.

## Hành vi kiểm chứng đề xuất, chưa phải AC đã duyệt

Các nhãn dưới chỉ là case trong plan; không cấp published AC ID ở đây.

| Case | Kết quả mong muốn | Trace hiện có cần đối chiếu |
|---|---|---|
| Câu hỏi Việt không dấu và Việt có dấu | Phản hồi cùng ngôn ngữ nhất quán; không suy từ dấu đơn thuần | AC-RKG-024, NFR-RKG-UX-001 |
| Endpoint theo method/path hoặc tên handler | Đúng entity; ambiguity chọn rõ, không yêu cầu biết qualified name để hỏi | AC-RKG-024/025/029 |
| Hỏi gọi hàm | Phân biệt direct/indirect/caller, có đường đi và evidence; tên rút gọn không gây nhầm | AC-RKG-024/028 |
| Không có entity / không có relation / context bị cắt | Phân biệt nguyên nhân thật, gợi ý tiếp theo, không kết luận "không tồn tại" từ graph thiếu | AC-RKG-025/032 |
| Greeting | Hướng dẫn sử dụng, không tạo claim/citation/focus giả | Intent gap: cần Product bổ sung/chốt |
| Clarification chọn bằng nút hoặc số | Hiểu đang chọn gì; thứ tự và root đúng; giữ intent gốc thay vì tổng hợp cho câu "2" | AC-RKG-029, cần kiểm tra cách lưu resolved question |
| Narrative/citation/limitation sau reload | Không lặp answer/claims; citation evidence chính xác; partial warning còn đúng | AC-RKG-030/046/047, UXF-RKG-002 |
| Provider lỗi, injection, foreign IDs, secret | Không publish claim sai; focus/draft/pin giữ đúng, nội dung cấm không được lưu/log | AC-RKG-033/041/042/059/063/064 |

Safety checks phải kiểm direction và meaning, không chỉ đếm citations. Mở rộng
eval readability bằng đánh giá người thật trên prototype/UAT; không tuyên bố
"dễ hiểu" chỉ vì unit tests pass. Ngưỡng chất lượng lấy từ policy/NFR hiện hành;
ngưỡng readability mới nếu cần phải chốt thành artifact chuẩn tắc.

## Lệnh xác minh dự kiến khi tới implementation

Các lệnh dưới chưa chạy trong lượt plan; đây không phải test evidence.

```bash
.venv/bin/python -m pytest tests/integration/test_grounded_qa.py tests/integration/test_conversation_api.py tests/integration/test_conversation_persistence.py tests/unit/test_llm_provider.py tests/unit/test_conversation_redaction.py -q
.venv/bin/ruff check src tests
.venv/bin/python -m pytest tests -q
```

Trong `frontend/`:

```bash
npm run test -- src/pages/conversations/ConversationPage.test.tsx
npm run lint
npm run build
```

Trước full suite kiểm tra test live có gửi request tốn phí hay không; chỉ chạy khi
phạm vi live đã được cho phép. Live eval và browser/UAT dùng corpus đã pin, ghi
model fingerprint/prompt/schema version/usage; không log prompt, answer hoặc key.
Không biến kết quả mock thành bằng chứng chất lượng live. RED-first evidence phải
chỉ ra case thất bại đúng nguyên nhân, không lưu conversation transcript.

## Definition of Ready và các quyết định còn thiếu

- Product: phạm vi natural answer, greeting, locale fallback và behavior khi thiếu
  dữ liệu; draft AC và phân biệt bug fix với intent gap.
- Architect/Tech Lead: A/B/C, giới hạn free prose, đường endpoint→handler, direction,
  direct/indirect và fallback. Nếu điều này mâu thuẫn spec, tạo OQ route bad_spec,
  sửa tầng thiết kế trước code.
- Design: mức hiển thị chi tiết/citation và wording partial/clarification; duyệt
  prototype theo exact UXF/SCR/UID revisions.
- Contract: truyền locale và persist limitation không mất sau reload; tương thích
  response/history/mock/live; có cần migration hay không.
- Baseline: tất cả inputs cần thiết được duyệt/pin. Baseline hiện tại của CHG-001
  là candidate, các gate còn pending; không dùng approval cũ làm phê duyệt cho CHG-002.
- Review/UAT: xác định người độc lập; author không review output của chính mình.

Chỉ sau các bước này mới tạo implementation task và plan cụ thể. Tiến độ chính thức
ở task frontmatter khi task đã tồn tại; plan này không gán task `done`/`blocked`.

## Quy tắc evidence và bàn giao

Plan này append-only: đổi hướng ghi revision/file mới, không sửa lại cam kết ban đầu.
Context khảo sát pin toàn bộ inputs; trước code/merge kiểm tra hash và recompile
context task. Nhật ký tương lai có Diễn giải / Đi chệch / Đánh đổi / Câu hỏi mở.
Review nhận artifact/code/test và baseline, không nhận plan/diary/rationale của tác giả.
Không viết lại historical approval, baseline hoặc raw eval report. Mọi test/approval
mới nhận `captured_against` hoặc `verified_against` trỏ đúng revision/hash/build.
