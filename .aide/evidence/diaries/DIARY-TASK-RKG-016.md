---
key: DIARY-TASK-RKG-016
type: implementation-diary
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-016
revision: 5
implementation_window:
  from: '2026-09-25'
  through: '2026-09-25'
provenance: reconstructed-from-committed-diff-and-prior-evidence
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  implementation_commits:
  - 20931a3d40889c60abf801498b9a1c698e2d19d7
prior_evidence:
- evidence/context/CTX-TASK-RKG-016.yaml
- evidence/diaries/DIARY-TASK-RKG-016.md
- evidence/plans/PLAN-TASK-RKG-016.md
revision_history:
- revision: 1
  metadata:
    key: DIARY-TASK-RKG-016
    type: implementation-diary
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-016
    revision: 1
    captured_at: 2026-09-25
    captured_against:
      artifacts:
      - key: TASK-RKG-016
        revision: 6
      - key: API-RKG-CORE-v1
        revision: 9
      - key: FR-RKG-001
        revision: 7
      - key: FR-RKG-002
        revision: 6
      - key: FR-RKG-003
        revision: 7
      - key: FR-RKG-004
        revision: 6
      - key: CMP-RKG-TRANSPORT
        revision: 4
      base_commit: 548c5eded456820a8a579572a31538c69cb5e20d
      code_tree: working-tree-file-hashes-below
      pins:
        cpython: 3.12.14
        kuzu: 0.11.3
  record: "# DIARY-TASK-RKG-016 — Core FastAPI transport\n\n## Thực hiện\n\n- `src/rkg/api` nối repository,\
    \ index job, snapshot và graph read vào `/api/v1`.\n  `rkg serve` chạy app này trên `127.0.0.1`, một\
    \ worker, không ghi access log.\n- Mutation và `POST /context` yêu cầu `X-RKG-Session` cùng Host loopback.\
    \ Origin\n  nếu có thì cũng phải loopback. Token lấy từ `RKG_SESSION_TOKEN`; nếu không có,\n  `serve`\
    \ giữ một token trong bộ nhớ và không in ra.\n- Index job trả `202` khi đã nhận việc. Lần poll khi\
    \ job chưa terminal có\n  `Retry-After: 1`. Writer lock vẫn là một job tại một thời điểm.\n- Entity\
    \ type trên wire là enum domain (`Endpoint`, `Callable`, …).\n- AC-RKG-062 chưa có corpus pilot, để\
    \ T-022. Conversation create/list/turn để T-021.\n  `DELETE /conversations/{id}` có ở transport để\
    \ `409 conversation_busy`.\n\n## Kiểm chứng trên cây mã hiện tại\n\n| Lệnh | Kết quả |\n| --- | ---\
    \ |\n| `uv run pytest tests -q` | 107 passed, 1 skipped |\n| `uv run ruff check src tests` | pass\
    \ |\n\nSHA-256 của file đã kiểm chứng:\n\n| File | SHA-256 |\n| --- | --- |\n| `src/rkg/api/__init__.py`\
    \ | `3bff42f7a6b0b39bb8b4b9352764232bacb77fc29979f2faa5c9ac02e120c9ec` |\n| `src/rkg/api/README.md`\
    \ | `c5b74dfab25f0cbae375ca4e1da26a3c8f5f15deb5b65d74c441606fd8b42e54` |\n| `src/rkg/api/app.py` |\
    \ `feaadec6100e260f8fe4833c0a497c231a7fcab3c3ffbff2545c3860d99cfbba` |\n| `src/rkg/api/catalog.py`\
    \ | `9d48d3c9eb9f1d2979132275ee754f81c676c699f226fcf062e0757901d12888` |\n| `src/rkg/api/errors.py`\
    \ | `28f2696ed6700736cac02259018056bd3c4c5d11a4df4588e43ac7b68622fb2d` |\n| `src/rkg/api/guard.py`\
    \ | `eaef98eea37bd2e208119a87ac03e8e0c5a4fd6e99635f9cc4622fb298f91876` |\n| `src/rkg/api/jobs.py`\
    \ | `eb7603482e1ba04677b3a13207d018cd9f1ec516624e079bca87cf324c187157` |\n| `src/rkg/api/serialize.py`\
    \ | `8f840276e0cead60d510c8cb879f0eba6c1e8175179a0f2caacdb31976e8f44c` |\n| `src/rkg/jobs/__init__.py`\
    \ | `2d2c49d6b6297504ca60846f2709f4fe9a615a9e8bc49da32261c762a3ef4de5` |\n| `src/rkg/jobs/coordinator.py`\
    \ | `9e9431009af34b732a4c296f437787a61fa2375464c7c46543d1f230bb37cdf9` |\n| `src/rkg/cli/__init__.py`\
    \ | `57e8f84aa9879a8c995b9f8e5e39d655d26ce5549111020043dd3e455ec6766b` |\n| `src/rkg/graph/README.md`\
    \ | `f248d187b2865fe2d4d6c0eee093fd7876163c7b601e0e401e69ae86d0f2106d` |\n| `src/rkg/conversations/README.md`\
    \ | `c6d18591381c635fce69b6fbc5e60094ff8ce69e5b31d9dd6f8d9e3aabdcf04b` |\n| `src/rkg/domain/README.md`\
    \ | `459cc0291b2cfbf42efb57a33e137373e7c4cbb45a144f4de6ff96af75fb6b23` |\n| `.aide/README.md` | `5b88c01aeb033580a99b2c4e647c7321d54be5239dc5df7478f331d7eee61e97`\
    \ |\n| `tests/integration/test_core_api.py` | `bf15dd5eff440a9affaacf951565949624aaabad9bf3f638d641f5dc1a1087cf`\
    \ |\n| `pyproject.toml` | `988c3a88075e891c79fc655208b0dbbe4405470ab313e7de48533c08a402d1fc` |\n|\
    \ `.aide/lifecycle/tasks/TASK-RKG-016.md` | `af07c50b1aef3677e35d990f541d8f1cee22ccb0e81dc2eb725aa106a775dc28`\
    \ |\n\n## Deferred\n\n- AC-RKG-037 / AC-RKG-062 benchmark corpus → T-022.\n- Conversation create,\
    \ list và turn HTTP → T-021.\n- UI live client → T-024."
---

# DIARY-TASK-RKG-016

## Thực hiện

- `src/rkg/api` nối repository, index job, snapshot và graph read vào `/api/v1`.
  `rkg serve` chạy app này trên `127.0.0.1`, một worker, không ghi access log.
- Mutation và `POST /context` yêu cầu `X-RKG-Session` cùng Host loopback. Origin
  nếu có thì cũng phải loopback. Token lấy từ `RKG_SESSION_TOKEN`; nếu không có,
  `serve` giữ một token trong bộ nhớ và không in ra.
- Index job trả `202` khi đã nhận việc. Lần poll khi job chưa terminal có
  `Retry-After: 1`. Writer lock vẫn là một job tại một thời điểm.
- Entity type trên wire là enum domain (`Endpoint`, `Callable`, …).
- AC-RKG-062 chưa có corpus pilot, để T-022. Conversation create/list/turn để T-021.
  `DELETE /conversations/{id}` có ở transport để `409 conversation_busy`.

## Kiểm chứng trên cây mã hiện tại

| Lệnh | Kết quả |
| --- | --- |
| `uv run pytest tests -q` | 107 passed, 1 skipped |
| `uv run ruff check src tests` | pass |

SHA-256 của file đã kiểm chứng:

| File | SHA-256 |
| --- | --- |
| `src/rkg/api/__init__.py` | `3bff42f7a6b0b39bb8b4b9352764232bacb77fc29979f2faa5c9ac02e120c9ec` |
| `src/rkg/api/README.md` | `c5b74dfab25f0cbae375ca4e1da26a3c8f5f15deb5b65d74c441606fd8b42e54` |
| `src/rkg/api/app.py` | `feaadec6100e260f8fe4833c0a497c231a7fcab3c3ffbff2545c3860d99cfbba` |
| `src/rkg/api/catalog.py` | `9d48d3c9eb9f1d2979132275ee754f81c676c699f226fcf062e0757901d12888` |
| `src/rkg/api/errors.py` | `28f2696ed6700736cac02259018056bd3c4c5d11a4df4588e43ac7b68622fb2d` |
| `src/rkg/api/guard.py` | `eaef98eea37bd2e208119a87ac03e8e0c5a4fd6e99635f9cc4622fb298f91876` |
| `src/rkg/api/jobs.py` | `eb7603482e1ba04677b3a13207d018cd9f1ec516624e079bca87cf324c187157` |
| `src/rkg/api/serialize.py` | `8f840276e0cead60d510c8cb879f0eba6c1e8175179a0f2caacdb31976e8f44c` |
| `src/rkg/jobs/__init__.py` | `2d2c49d6b6297504ca60846f2709f4fe9a615a9e8bc49da32261c762a3ef4de5` |
| `src/rkg/jobs/coordinator.py` | `9e9431009af34b732a4c296f437787a61fa2375464c7c46543d1f230bb37cdf9` |
| `src/rkg/cli/__init__.py` | `57e8f84aa9879a8c995b9f8e5e39d655d26ce5549111020043dd3e455ec6766b` |
| `src/rkg/graph/README.md` | `f248d187b2865fe2d4d6c0eee093fd7876163c7b601e0e401e69ae86d0f2106d` |
| `src/rkg/conversations/README.md` | `c6d18591381c635fce69b6fbc5e60094ff8ce69e5b31d9dd6f8d9e3aabdcf04b` |
| `src/rkg/domain/README.md` | `459cc0291b2cfbf42efb57a33e137373e7c4cbb45a144f4de6ff96af75fb6b23` |
| `.aide/README.md` | `5b88c01aeb033580a99b2c4e647c7321d54be5239dc5df7478f331d7eee61e97` |
| `tests/integration/test_core_api.py` | `bf15dd5eff440a9affaacf951565949624aaabad9bf3f638d641f5dc1a1087cf` |
| `pyproject.toml` | `988c3a88075e891c79fc655208b0dbbe4405470ab313e7de48533c08a402d1fc` |
| `.aide/lifecycle/tasks/TASK-RKG-016.md` | `af07c50b1aef3677e35d990f541d8f1cee22ccb0e81dc2eb725aa106a775dc28` |

## Deferred

- AC-RKG-037 / AC-RKG-062 benchmark corpus → T-022.
- Conversation create, list và turn HTTP → T-021.
- UI live client → T-024.

## Đối chiếu commit và phạm vi hiện hành

## Kết quả đối chiếu triển khai

Expose repository/job/snapshot/search/subgraph/context API trên loopback; validate session/Origin/Host, serialize stable errors và gọi chung service với CLI.

Các file thay đổi được xác định bằng Git diff của các commit được pin trong frontmatter. Current-tree hash nằm trong context revision 3; khác hash lịch sử là revision về sau, không phải cùng lần chạy.

## Diễn giải và correction

Hành vi và các lần kiểm đã ghi trong prior evidence giữ nguyên; bản này bổ sung liên kết và nguồn commit, không thay kết quả cũ.

## Kết quả lần bổ sung hồ sơ

Đã đọc commit/file, parse test declarations và liên kết evidence; không chạy lại runtime test hoặc đo KPI. Không nhận đây là review code độc lập hay approval.
