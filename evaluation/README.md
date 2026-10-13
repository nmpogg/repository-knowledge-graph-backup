# Chatbot evaluation golden set

[Danh sách câu hỏi](CASES.md) giúp xem nhanh từng case.

`golden_set.json` chứa **50 testcase / 73 lượt hỏi**, đối chiếu trực tiếp với source
của 6 repo hiện có. Đây là fixture đánh giá không chuẩn tắc; policy nghiệm thu vẫn
nằm trong `.aide/policies/eval/EVAL-RKG-QA-001.md` và `.aide/observability/OBS-RKG-005.md`.

| Repo | Testcase |
|---|---:|
| `soopi` | 10 |
| `rkg-fixture-react-ts` | 8 |
| `rkg-fixture-bullmq-worker` | 8 |
| `rkg-fixture-spring-orders` | 8 |
| `rkg-fixture-go-event-worker` | 8 |
| `rkg-fixture-nuxt4` | 8 |

Có 39 câu độc lập: **29 answerable**, **4 insufficient**, **1 ambiguous**, **5 injection**.
Ngoài ra có **10 conversation dài 2–4 lượt** và **1 conversation dài 9 lượt**,
vượt history window 6 completed turns hiện tại. `question_variants` là cách hỏi
thay thế cho cùng case, không được tính thêm vào mẫu số 50.

## Một case gồm những gì?

- `turns`: câu hỏi, session, trạng thái mong đợi và các ý bắt buộc.
- `required_facts`: đáp án về nghĩa; từng ý dẫn tới `source_ids` cụ thể.
- `forbidden_claims`: các kết luận sai cần phát hiện.
- `sources`: đường dẫn **tương đối với repo fixture**, vùng dòng, SHA-256 toàn file
  và vùng dòng. Đây là nguồn đối chiếu, không phải graph evidence ID được bịa ra.
- `selection`: tiêu chí chọn candidate khi cần làm rõ, bằng type/symbol/file.
- `required_metadata`: ví dụ `history_truncated: true` ở cuối hội thoại dài.

Case vị trí code dùng metadata định nghĩa. Case quan hệ cần citation đúng call site
hoặc khai báo liên quan. Vị trí sửa là vùng định nghĩa để kiểm tra, không phải một
câu lệnh chắc chắn phải sửa. Với thêm API, chấp nhận các vị trí khác nếu reviewer
xác nhận phù hợp và được source hỗ trợ; không đòi đoạn văn giống đáp án mẫu.

## Kiểm tra bộ dữ liệu

Từ thư mục gốc RKG:

```bash
.venv/bin/python evaluation/validate.py
.venv/bin/pytest -q evaluation/test_validate.py
```

Validator kiểm tra JSON Schema, số lượng/phân bố case, liên kết fact→source,
trình tự hội thoại, hash toàn bộ **209 source file** và hash các vùng dẫn chứng.
Nó chỉ đọc source; không import/chạy code fixture và không gọi LLM.
Hash đúng chứng minh nguồn chưa đổi, không tự chứng minh nghĩa của đáp án đúng.

`authoring_status=source_checked` ghi việc đối chiếu source khi soạn bộ này.
`independent_review_status=pending` cần reviewer xác nhận các ý bắt buộc trước
khi dùng kết quả để nghiệm thu KPI. Validator không tự chuyển trạng thái review.

## Chạy eval và chấm

1. Kiểm tra source pins; review đáp án **trước** khi xem câu trả lời chatbot.
2. Index từng fixture. Tạo run manifest ghi revision/hash corpus, source manifest,
   repository ID, **snapshot ID cố định**, provider/model và revision code/prompt/schema.
   Corpus chưa điền graph ID vì chúng phụ thuộc lần index; không tự dùng active snapshot
   thay cho snapshot đã pin. Nếu history window thay đổi, cập nhật case dài bằng
   revision corpus mới trước khi chạy.
3. Preflight các fact bắt buộc trong graph. Nếu source có fact nhưng graph thiếu,
   ghi **indexing/coverage gap**; không sửa đáp án sau khi thấy output.
4. Mỗi case bắt đầu conversation mới. Mỗi giá trị `session` là một conversation
   riêng trong cùng snapshot; duy trì revision hiện tại và tạo client request ID riêng
   cho từng lượt, kể cả các câu hỏi lặp ở case dài. Dùng provider/model thật để đo
   chất lượng. Mock chỉ kiểm tra luồng và contract.
5. Với `selection`, tìm candidate đúng type/symbol/file và gửi root ID của nó;
   không giả định candidate luôn ở vị trí số 1. Lượt chọn tiếp tục câu hỏi gốc.
6. Chấm từng ý bắt buộc, trạng thái, forbidden claims và citations. Không yêu cầu
   khớp câu chữ. Extra claims vẫn phải đúng và có nguồn. Một case answerable chỉ
   pass khi **tất cả** tiêu chí bắt buộc pass; một conversation chỉ pass khi mọi
   lượt và ràng buộc focus/session/history đều pass.
7. Báo cáo từng case với pass/fail reason, graph support, model/provider/version,
   usage, citation coverage/validity và contradiction count. Chấm độ tự nhiên riêng
   theo `readability_checks`, không gộp nó vào accuracy.

**End-to-end answerable accuracy = số case answerable đạt / 29.**
Câu trả lời “không đủ bằng chứng” cho case source-backed answerable không được tính
đúng; nếu nguyên nhân là thiếu graph, ghi lỗi coverage riêng để biết nơi cần sửa.
Có thể báo thêm generation accuracy trên các case có graph đủ fact, nhưng phải
công bố subset và mẫu số đã chốt từ preflight, không thay thế hoặc che mẫu số 29.
Bốn insufficient và một ambiguous được chấm riêng; câu hỏi âm tính yêu cầu không
đoán dữ liệu runtime, không yêu cầu chatbot đọc raw source để giải thích chi tiết
một parameter chưa có trong graph.

Đạt ngưỡng 90% với 29 answerable cần **ít nhất 27/29** pass. Citation coverage và
validity phải 100%, không claim trái graph; nhóm safety/insufficient/ambiguous và
conversation phải pass 100% theo policy. Kết quả chạy thật nằm trong `results/`.

Nếu source thay đổi, giữ bản corpus cũ cho run cũ và tạo revision mới sau khi review
lại facts/ranges/hash; không chỉ cập nhật hash để làm validator xanh.

## Chạy chatbot thật và Ragas

```bash
uv sync --group evaluation
.venv/bin/python -m evaluation.run_ragas --output evaluation/results/run-001.json
.venv/bin/pytest -q evaluation/test_validate.py evaluation/test_run_ragas.py
```

Runner dùng provider và model đã cấu hình của chatbot, index 6 repo vào database
tạm, gọi `submit_grounded_turn` và giữ snapshot riêng cho từng hội thoại. Không
chạy source của repo-test. Ragas nhận câu hỏi, câu trả lời, đáp án chuẩn và metadata
graph thực sự được lấy trong lượt đó; không dùng đáp án chuẩn làm context retrieval.
Việc gửi dữ liệu này tới provider phải được người vận hành cho phép.

Ragas 0.4.3 chấm factual correctness F1, recall các ý bắt buộc, faithfulness,
context recall, rubric từng case và độ tự nhiên. Rubric thay cho AnswerRelevancy
để không cần dịch vụ embedding riêng. Có thể đổi judge bằng `--judge-model`;
mặc định dùng cùng model nên kết quả có thể có thiên lệch. Điểm do LLM chấm là
ước lượng, cần reviewer độc lập xác nhận trước khi dùng để nghiệm thu KPI.

Pass cần status/metadata/snapshot/citation hợp lệ, rubric 5/5, required fact recall
và faithfulness 1. Độ tự nhiên chấm riêng. Lỗi judge ghi `unscored`, không tính là
pass; mẫu số answerable vẫn là 29. Context trống ghi `not_applicable`, không tự
cho điểm 1. Citation coverage chỉ đo các relationship claims trong payload có
cấu trúc, không chứng minh mọi câu văn đều có citation.

Report chỉ lưu ID, hash, kiểm tra, usage và điểm; không lưu nội dung hội thoại,
context, credentials hay đường dẫn host. Report đang chạy được cập nhật từng case;
chỉ report có `state: completed` mới là kết quả kết thúc. Database tạm được xóa.
