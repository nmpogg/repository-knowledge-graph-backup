---
key: DIARY-TASK-RKG-003
type: implementation-diary
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-003
revision: 5
implementation_window:
  from: '2026-09-24'
  through: '2026-09-24'
provenance: reconstructed-from-committed-diff-and-prior-evidence
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  implementation_commits:
  - 4ee8a54a47ecafe383baa0450040a7cc65e37914
prior_evidence:
- evidence/context/CTX-TASK-RKG-003.yaml
- evidence/diaries/DIARY-TASK-RKG-003.md
- evidence/plans/PLAN-TASK-RKG-003.md
revision_history:
- revision: 1
  metadata:
    key: DIARY-TASK-RKG-003
    type: implementation-diary
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-003
    revision: 1
    captured_at: 2026-09-24
    captured_against:
      artifacts:
      - key: TASK-RKG-003
        revision: 5
      - key: FR-RKG-001
        revision: 7
      - key: FR-RKG-002
        revision: 8
      - key: CMP-RKG-ANALYZER
        revision: 5
      - key: NFR-RKG-SEC-001
        revision: 7
      - key: NFR-RKG-REL-001
        revision: 8
      base_commit: b86e0533f3b2caeda4dbed042fa5003940447637
      code_tree: working-tree-file-hashes-below
  record: "# DIARY-TASK-RKG-003 — Local source loader\n\n## Thực hiện\n\n- `resolve_local_source` canonicalize\
    \ repository path và optional `source_root`,\n  kiểm tra server-owned `allowed_local_roots`, trả mã\
    \ lỗi cố định không chứa host\n  path. Missing path, outside allowlist, invalid subroot và link escape\
    \ phân biệt.\n- `build_manifest` duyệt file deterministic theo path relative, áp dụng include/\n \
    \ ignore patterns, đếm `max_files`, không đọc file vượt `max_file_bytes`, ghi\n  `SkippedFile` với\
    \ warning code và tạo `manifest:<sha256>` cùng config digest.\n- Nội dung file được đọc một lần vào\
    \ bytes bất biến để adapter dùng về sau; bytes\n  không xuất hiện trong `repr`, graph/log/API/evidence.\
    \ Loader không import, execute,\n  parse, gọi shell hay network tới source.\n- Link/junction bên trong\
    \ root được skip; link thoát root bị reject. Kiểm tra\n  canonical path của handle và identity trước\
    \ khi đọc, rồi kiểm tra lại identity\n  sau đọc để giảm rủi ro thay đổi source trong lúc scan. Windows\
    \ dùng final path\n  từ handle; Linux dùng `/proc/self/fd`; nền tảng không hỗ trợ fail closed.\n-\
    \ Windows UNC/device path bị từ chối trước khi resolve để local-source request\n  không truy cập network\
    \ share.\n- `src/rkg/ingestion/README.md` ghi interface bàn giao cho adapter/job/API.\n\n## Kiểm chứng\
    \ trên cây mã hiện tại\n\nMôi trường: `.venv` do `uv sync --locked --group dev --python 3.12.5` tạo;\n\
    `kuzu==0.11.3`, `pytest==9.1.1`, `ruff==0.16.8` từ `uv.lock`. Pin dự án vẫn\nlà Python 3.12.14; phiên\
    \ này kiểm chứng bằng 3.12.5 do máy chưa có 3.12.14.\n\n| Lệnh | Kết quả |\n| --- | --- |\n| `.venv/Scripts/python.exe\
    \ -m pytest -q -ra` | pass — 21 tests, 1 skip |\n| `.venv/Scripts/ruff.exe check src tests` | pass\
    \ — All checks passed |\n\nTest symlink thật bị skip vì host không cấp quyền tạo symlink. Test độc\
    \ lập cho\nnhánh link escape (mock), kiểm tra handle thoát root trước khi đọc và file quá\nlớn không\
    \ được đọc đều pass. Junction thật trên Windows chưa có fixture trong\nlần kiểm chứng này; AC-RKG-051\
    \ end-to-end cần kiểm lại ở integration suite.\n\nSHA-256 của file đã kiểm chứng:\n\n| File | SHA-256\
    \ |\n| --- | --- |\n| `src/rkg/ingestion/__init__.py` | `5a928d7a424d95d3f80744ca12fb90a701dc4ac3d3fc7a292355956eae35c693`\
    \ |\n| `src/rkg/ingestion/local.py` | `3e9d72c0346ffa23873f244fa7baf1b05aacf730f1dbaf8b2976d00b8a28f2dc`\
    \ |\n| `src/rkg/ingestion/README.md` | `34a96970512d2cf006f5b9d8e44530d6281f5004f33bc69ad9ec6344698b1b2f`\
    \ |\n| `tests/unit/test_local_source.py` | `d7bc11de12e6315e31d410ad3a73595ee05e179b9a786510f17aa54b9aa8ab4c`\
    \ |\n\n## Giới hạn phạm vi\n\nCác test này kiểm chứng phần loader của AC-RKG-001/012/026/035/038/049/050/051/054.\n\
    Chúng không xác nhận toàn bộ index job, parse error diagnostic, candidate publish,\nscan report API\
    \ hoặc onboarding UI. Những kiểm chứng đó thuộc T-005/T-015/T-016/T-024."
---

# DIARY-TASK-RKG-003

## Thực hiện

- `resolve_local_source` canonicalize repository path và optional `source_root`,
  kiểm tra server-owned `allowed_local_roots`, trả mã lỗi cố định không chứa host
  path. Missing path, outside allowlist, invalid subroot và link escape phân biệt.
- `build_manifest` duyệt file deterministic theo path relative, áp dụng include/
  ignore patterns, đếm `max_files`, không đọc file vượt `max_file_bytes`, ghi
  `SkippedFile` với warning code và tạo `manifest:<sha256>` cùng config digest.
- Nội dung file được đọc một lần vào bytes bất biến để adapter dùng về sau; bytes
  không xuất hiện trong `repr`, graph/log/API/evidence. Loader không import, execute,
  parse, gọi shell hay network tới source.
- Link/junction bên trong root được skip; link thoát root bị reject. Kiểm tra
  canonical path của handle và identity trước khi đọc, rồi kiểm tra lại identity
  sau đọc để giảm rủi ro thay đổi source trong lúc scan. Windows dùng final path
  từ handle; Linux dùng `/proc/self/fd`; nền tảng không hỗ trợ fail closed.
- Windows UNC/device path bị từ chối trước khi resolve để local-source request
  không truy cập network share.
- `src/rkg/ingestion/README.md` ghi interface bàn giao cho adapter/job/API.

## Kiểm chứng trên cây mã hiện tại

Môi trường: `.venv` do `uv sync --locked --group dev --python 3.12.5` tạo;
`kuzu==0.11.3`, `pytest==9.1.1`, `ruff==0.16.8` từ `uv.lock`. Pin dự án vẫn
là Python 3.12.14; phiên này kiểm chứng bằng 3.12.5 do máy chưa có 3.12.14.

| Lệnh | Kết quả |
| --- | --- |
| `.venv/Scripts/python.exe -m pytest -q -ra` | pass — 21 tests, 1 skip |
| `.venv/Scripts/ruff.exe check src tests` | pass — All checks passed |

Test symlink thật bị skip vì host không cấp quyền tạo symlink. Test độc lập cho
nhánh link escape (mock), kiểm tra handle thoát root trước khi đọc và file quá
lớn không được đọc đều pass. Junction thật trên Windows chưa có fixture trong
lần kiểm chứng này; AC-RKG-051 end-to-end cần kiểm lại ở integration suite.

SHA-256 của file đã kiểm chứng:

| File | SHA-256 |
| --- | --- |
| `src/rkg/ingestion/__init__.py` | `5a928d7a424d95d3f80744ca12fb90a701dc4ac3d3fc7a292355956eae35c693` |
| `src/rkg/ingestion/local.py` | `3e9d72c0346ffa23873f244fa7baf1b05aacf730f1dbaf8b2976d00b8a28f2dc` |
| `src/rkg/ingestion/README.md` | `34a96970512d2cf006f5b9d8e44530d6281f5004f33bc69ad9ec6344698b1b2f` |
| `tests/unit/test_local_source.py` | `d7bc11de12e6315e31d410ad3a73595ee05e179b9a786510f17aa54b9aa8ab4c` |

## Giới hạn phạm vi

Các test này kiểm chứng phần loader của AC-RKG-001/012/026/035/038/049/050/051/054.
Chúng không xác nhận toàn bộ index job, parse error diagnostic, candidate publish,
scan report API hoặc onboarding UI. Những kiểm chứng đó thuộc T-005/T-015/T-016/T-024.

## Đối chiếu commit và phạm vi hiện hành

## Kết quả đối chiếu triển khai

Canonicalize root và allowlist, chặn symlink escape, tạo immutable manifest với hash và file limits; không import hoặc chạy source.

Các file thay đổi được xác định bằng Git diff của các commit được pin trong frontmatter. Current-tree hash nằm trong context revision 3; khác hash lịch sử là revision về sau, không phải cùng lần chạy.

## Diễn giải và correction

Hành vi và các lần kiểm đã ghi trong prior evidence giữ nguyên; bản này bổ sung liên kết và nguồn commit, không thay kết quả cũ.

## Kết quả lần bổ sung hồ sơ

Đã đọc commit/file, parse test declarations và liên kết evidence; không chạy lại runtime test hoặc đo KPI. Không nhận đây là review code độc lập hay approval.
