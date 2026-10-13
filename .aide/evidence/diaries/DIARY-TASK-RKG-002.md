---
key: DIARY-TASK-RKG-002
type: implementation-diary
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-002
revision: 5
implementation_window:
  from: '2026-09-24'
  through: '2026-09-24'
provenance: reconstructed-from-committed-diff-and-prior-evidence
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  implementation_commits:
  - 968a9f62775d4f26d23fb713fb14128fce5b97c1
prior_evidence:
- evidence/context/CTX-TASK-RKG-002.yaml
- evidence/diaries/DIARY-TASK-RKG-002.md
- evidence/plans/PLAN-TASK-RKG-002.md
revision_history:
- revision: 1
  metadata:
    key: DIARY-TASK-RKG-002
    type: implementation-diary
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-002
    revision: 1
    captured_at: 2026-09-24
    captured_against:
      artifacts:
      - key: TASK-RKG-002
        revision: 3
      - key: TBL-RKG-GRAPH
        revision: 8
      - key: FR-RKG-002
        revision: 8
      - key: FR-RKG-004
        revision: 6
      - key: API-RKG-CORE-v1
        revision: 9
      base_commit: 7e2e93c24fa1033cc3afb417703f17b5197e3026
      code_tree: working-tree-file-hashes-below
  record: "# DIARY-TASK-RKG-002 — Domain schema and golden fixtures\n\n## Thực hiện\n\n- Tạo canonical\
    \ DTO bất biến cho Entity, Edge, Evidence, Diagnostic, FactBatch,\n  effective source scan config,\
    \ context budget và context package.\n- Tạo ID SHA-256 với identity fields được đóng khung bằng JSON:\
    \ source entity,\n  Endpoint registration chain, DataResource, MessageChannel, Configuration, edge,\n\
    \  evidence và diagnostic; thêm digest cấu hình scan hiệu lực. Edge identity theo\n  snapshot/type/source/target;\
    \ nhiều\n  call site dùng một edge và nhiều evidence IDs.\n- Validator trước publication kiểm tra\
    \ repository/snapshot ownership, endpoint\n  tồn tại, evidence location/rule version, semantic edge\
    \ types, relative paths và\n  cấm value/secret/raw-source-like attributes.\n- Golden JSON mô tả SourceUnit\
    \ → Namespace → Type → Callable → nested Callable;\n  unit tests xác nhận schema-level shape cho AC-RKG-002,\
    \ invalid evidence/cross-\n  snapshot cho AC-RKG-007, deterministic context shape/budget DTO cho AC-RKG-010.\n\
    - `src/rkg/domain/README.md` ghi rõ interface bàn giao cho T-003/T-013/T-014.\n\n## Kiểm chứng trên\
    \ cây mã hiện tại\n\nMôi trường kiểm chứng: Windows, `.venv` tạo bằng `uv sync --locked --group dev\n\
    --python 3.12.5`; `kuzu==0.11.3`, `pytest==9.1.1`, `ruff==0.16.8` từ `uv.lock`.\nPin dự án `.python-version`\
    \ vẫn là 3.12.14; patch Python 3.12.5 chỉ dùng cho lần\nkiểm chứng này vì uv 0.12.3 trên máy không\
    \ tìm được 3.12.14. Không đổi lock/pin.\n\n| Lệnh | Kết quả |\n| --- | --- |\n| `.venv/Scripts/python.exe\
    \ -m pytest -q` | pass — 11 tests |\n| `.venv/Scripts/ruff.exe check src tests` | pass — All checks\
    \ passed |\n\nSHA-256 của file đã kiểm chứng:\n\n| File | SHA-256 |\n| --- | --- |\n| `src/rkg/domain/__init__.py`\
    \ | `024dedf5cf4267ec8ee2b76a05eeccc1f64c5129e3bdb40c5b5bcdd132852bd1` |\n| `src/rkg/domain/ids.py`\
    \ | `75d9b332fc0cb25e1e9131edb53452aaaa77a5daf3edc397fcf7b952620d619b` |\n| `src/rkg/domain/models.py`\
    \ | `8bb37e290b0b3249b84dbfc5410f2bb6eb5407e663fc31169c2d214365ad2e51` |\n| `src/rkg/domain/validation.py`\
    \ | `6c95dc497aa7c6f42715b1f0e88e4914617f4b59b5e7fad5149f126b51c8aa39` |\n| `src/rkg/domain/context.py`\
    \ | `be33488832fe6c658a1ff08fcfa8fe98528bf1b34222ffba82405b050c982aa9` |\n| `src/rkg/domain/README.md`\
    \ | `3c91c15a35d584fb04b23dd2dfa3b36454c4cdd5328a8734791a2e4406f996c7` |\n| `tests/fixtures/domain/source_structure.json`\
    \ | `2816f63466c3d891f44b7a60c178692f4d6405e856631170d96fa1d9ca7cb85d` |\n| `tests/unit/test_domain_schema.py`\
    \ | `e1c1c39f54f91f1ebee9449527fd7fa8c56240bc83830f17fccd3f5471aedb34` |\n\n## Giới hạn phạm vi\n\n\
    Tests này kiểm chứng **schema và DTO** của AC-RKG-002/007/010, chưa phải\nend-to-end scan, Kùzu publication\
    \ hoặc `POST /api/v1/context` với traversal và\ntruncation. Các AC đầy đủ tiếp tục được kiểm chứng\
    \ tại task analyzer/graph/API.\nKhông thêm implementation cho T-003, T-013 hoặc T-014 trong task này."
---

# DIARY-TASK-RKG-002

## Thực hiện

- Tạo canonical DTO bất biến cho Entity, Edge, Evidence, Diagnostic, FactBatch,
  effective source scan config, context budget và context package.
- Tạo ID SHA-256 với identity fields được đóng khung bằng JSON: source entity,
  Endpoint registration chain, DataResource, MessageChannel, Configuration, edge,
  evidence và diagnostic; thêm digest cấu hình scan hiệu lực. Edge identity theo
  snapshot/type/source/target; nhiều
  call site dùng một edge và nhiều evidence IDs.
- Validator trước publication kiểm tra repository/snapshot ownership, endpoint
  tồn tại, evidence location/rule version, semantic edge types, relative paths và
  cấm value/secret/raw-source-like attributes.
- Golden JSON mô tả SourceUnit → Namespace → Type → Callable → nested Callable;
  unit tests xác nhận schema-level shape cho AC-RKG-002, invalid evidence/cross-
  snapshot cho AC-RKG-007, deterministic context shape/budget DTO cho AC-RKG-010.
- `src/rkg/domain/README.md` ghi rõ interface bàn giao cho T-003/T-013/T-014.

## Kiểm chứng trên cây mã hiện tại

Môi trường kiểm chứng: Windows, `.venv` tạo bằng `uv sync --locked --group dev
--python 3.12.5`; `kuzu==0.11.3`, `pytest==9.1.1`, `ruff==0.16.8` từ `uv.lock`.
Pin dự án `.python-version` vẫn là 3.12.14; patch Python 3.12.5 chỉ dùng cho lần
kiểm chứng này vì uv 0.12.3 trên máy không tìm được 3.12.14. Không đổi lock/pin.

| Lệnh | Kết quả |
| --- | --- |
| `.venv/Scripts/python.exe -m pytest -q` | pass — 11 tests |
| `.venv/Scripts/ruff.exe check src tests` | pass — All checks passed |

SHA-256 của file đã kiểm chứng:

| File | SHA-256 |
| --- | --- |
| `src/rkg/domain/__init__.py` | `024dedf5cf4267ec8ee2b76a05eeccc1f64c5129e3bdb40c5b5bcdd132852bd1` |
| `src/rkg/domain/ids.py` | `75d9b332fc0cb25e1e9131edb53452aaaa77a5daf3edc397fcf7b952620d619b` |
| `src/rkg/domain/models.py` | `8bb37e290b0b3249b84dbfc5410f2bb6eb5407e663fc31169c2d214365ad2e51` |
| `src/rkg/domain/validation.py` | `6c95dc497aa7c6f42715b1f0e88e4914617f4b59b5e7fad5149f126b51c8aa39` |
| `src/rkg/domain/context.py` | `be33488832fe6c658a1ff08fcfa8fe98528bf1b34222ffba82405b050c982aa9` |
| `src/rkg/domain/README.md` | `3c91c15a35d584fb04b23dd2dfa3b36454c4cdd5328a8734791a2e4406f996c7` |
| `tests/fixtures/domain/source_structure.json` | `2816f63466c3d891f44b7a60c178692f4d6405e856631170d96fa1d9ca7cb85d` |
| `tests/unit/test_domain_schema.py` | `e1c1c39f54f91f1ebee9449527fd7fa8c56240bc83830f17fccd3f5471aedb34` |

## Giới hạn phạm vi

Tests này kiểm chứng **schema và DTO** của AC-RKG-002/007/010, chưa phải
end-to-end scan, Kùzu publication hoặc `POST /api/v1/context` với traversal và
truncation. Các AC đầy đủ tiếp tục được kiểm chứng tại task analyzer/graph/API.
Không thêm implementation cho T-003, T-013 hoặc T-014 trong task này.

## Đối chiếu commit và phạm vi hiện hành

## Kết quả đối chiếu triển khai

Định nghĩa DTO bất biến, ID deterministic, validation ownership/evidence và context budgets; chuẩn bị golden fixture cho các task extraction/storage.

Các file thay đổi được xác định bằng Git diff của các commit được pin trong frontmatter. Current-tree hash nằm trong context revision 3; khác hash lịch sử là revision về sau, không phải cùng lần chạy.

## Diễn giải và correction

Hành vi và các lần kiểm đã ghi trong prior evidence giữ nguyên; bản này bổ sung liên kết và nguồn commit, không thay kết quả cũ.

## Kết quả lần bổ sung hồ sơ

Đã đọc commit/file, parse test declarations và liên kết evidence; không chạy lại runtime test hoặc đo KPI. Không nhận đây là review code độc lập hay approval.
