---
key: DIARY-TASK-RKG-001
type: implementation-diary
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-001
revision: 5
implementation_window:
  from: '2026-09-17'
  through: '2026-09-24'
provenance: reconstructed-from-committed-diff-and-prior-evidence
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  implementation_commits:
  - ec0a1c04815ab62a181dfcec08035d21b17cc551
  - 9cae9d0caaed7328d4df70a3c183fb433aa952ee
prior_evidence:
- evidence/context/CTX-TASK-RKG-001.yaml
- evidence/context/CTX-TASK-RKG-001.yaml
- evidence/diaries/DIARY-TASK-RKG-001.md
- evidence/diaries/DIARY-TASK-RKG-001.md
- evidence/diaries/DIARY-TASK-RKG-001.md
- evidence/diaries/DIARY-TASK-RKG-001.md
- evidence/plans/PLAN-TASK-RKG-001.md
- evidence/plans/PLAN-TASK-RKG-001.md
- evidence/tests/TEST-RKG-DDL-BOOTSTRAP-001.md
revision_history:
- revision: 1
  metadata:
    key: DIARY-TASK-RKG-001
    type: implementation-diary
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-001
    captured_at: 2026-09-17
    captured_against:
      artifacts:
      - key: TASK-RKG-001
        revision: 1
      - key: CTX-TASK-RKG-001
        revision: 1
      - key: PLAN-TASK-RKG-001
        revision: 1
      docs:
      - docs/RULES.md
      - docs/ARCHITECTURE.md
      - docs/TASK.md
  record: '# DIARY-TASK-RKG-001


    ## Diễn giải


    - Owner đã review CTX/PLAN; triển khai bước 14 theo `PLAN-TASK-RKG-001`.

    - Pin CPython **3.12.14** (`.python-version`), `pyproject.toml` + `uv.lock`, package `src/rkg/` với
    module placeholder theo ARCHITECTURE §3 (chỉ `__init__.py` rỗng).

    - Smoke `tests/unit/test_skeleton.py`; ruff target py312 trên `src` + `tests`.

    - Frontend Vite + React + TypeScript dưới `frontend/` (npm + `package-lock.json`); heading sản phẩm
    tối thiểu; chưa mock API (T-17).

    - Cập nhật README lệnh thật; `.gitignore` bổ sung `.ruff_cache/`, `*.egg-info/`, `/dist/`.

    - Không đụng T-17 / T-02 / analyzer / API.


    ## Đi chệch


    - **Cài uv:** máy chưa có `uv`; cài qua `pip install uv` (0.12.15) thay vì script astral (blocked
    bởi sandbox/auto-review). README ghi cả hai cách.

    - **Scaffold frontend:** `npm create vite@latest frontend` bị cancel vì thư mục `frontend/` đã có
    `dist/.gitkeep` — scaffold thủ công tương đương template react-ts.

    - **Node runtime local:** plan chốt Node **22** LTS (`.nvmrc` = 22; `engines.node` = `>=22 <25`).
    Máy chạy kiểm tra dùng **Node v24.20.0**; build/lint vẫn xanh. CI/dev nên ưu tiên Node 22 theo `.nvmrc`.

    - **Vite build xóa `dist/`:** thêm bước post-build ghi lại `frontend/dist/.gitkeep` để giữ convention
    ignore.


    ## Đánh đổi


    - Dev deps Python dùng `[dependency-groups] dev` (uv) thay optional-dependencies; lệnh: `uv sync --group
    dev`.

    - Graph UI lib chưa cài (đúng plan — chốt ở T-17).


    ## Kiểm tra đã chạy


    | Lệnh | Kết quả |

    | --- | --- |

    | `uv sync --group dev` | pass — CPython 3.12.14, tạo/cập nhật `uv.lock` |

    | `uv run python -c "import sys; assert sys.version_info[:2]==(3,12)"` | pass — `3.12.14` |

    | `uv run python -c "import rkg"` | pass — `__version__ == 0.1.0` |

    | `uv run pytest` | pass — 2 passed |

    | `uv run ruff check src tests` | pass — All checks passed |

    | `cd frontend && npm ci && npm run build` | pass — Vite production build |

    | `cd frontend && npm run lint` | pass — ESLint sạch |


    ## Chưa kiểm tra


    - Clean clone trên máy khác / CI runner với Node 22 đúng `.nvmrc`.

    - `npm run dev` E2E thủ công trong browser (không thuộc DoD T-01).

    - Analyzer/API/Explorer — ngoài phạm vi.


    ## DoD (plan)


    - [x] `uv.lock` + `frontend/package-lock.json` có trong repo

    - [x] `uv run pytest` và `uv run ruff check src tests` xanh

    - [x] `npm ci && npm run build` trong `frontend/` xanh

    - [x] README lệnh khớp thực tế

    - [x] Diary + task artifact + `docs/TASK.md` đồng bộ `done`'
- revision: 2
  metadata:
    key: DIARY-TASK-RKG-001-r2
    type: implementation-diary
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-001
    revision: 2
    captured_at: 2026-09-23
    captured_against:
      artifacts:
      - key: TASK-RKG-001
        revision: 4
      - key: PLAN-TASK-RKG-001-r2
        revision: 2
      - key: CTX-TASK-RKG-001-r2
        revision: 2
      - key: CMP-RKG-WEB
        revision: 4
      - key: ADR-2026-003
        revision: 1
      code_tree: frontend-base-scaffold
- revision: 3
  metadata:
    key: DIARY-TASK-RKG-001-r3
    type: implementation-diary
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-001
    revision: 3
    captured_at: 2026-09-24
    captured_against:
      artifacts:
      - key: TASK-RKG-001
        revision: 5
      - key: CTX-TASK-RKG-001
        revision: 1
      - key: PLAN-TASK-RKG-001
        revision: 1
      - key: ADR-2026-001
        revision: 3
      - key: ADR-2026-002
        revision: 2
      - key: DDL-RKG-GRAPH
        revision: draft
      code_tree: python-skeleton-plus-kuzu-ddl-smoke
    reference_machine:
      os: Windows 10.0.26200
      arch: x86_64
      cpython: 3.12.14
      kuzu: 0.11.3
      uv: 0.12.15
      node_observed: 24.20.0
- revision: 4
  metadata:
    key: DIARY-TASK-RKG-001-r4
    type: implementation-diary
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-001
    revision: 4
    captured_at: 2026-09-24
    captured_against:
      artifacts:
      - key: TASK-RKG-001
        revision: 5
      - key: REG-REPO-001
        revision: 5
      - key: TASK-RKG-017
        revision: 9
      - key: TASK-RKG-025
        revision: 6
      code_tree: task-001-closeout-hygiene
    reference_machine:
      os: Windows 10.0.26200
      arch: x86_64
      cpython: 3.12.14
      kuzu: 0.11.3
---

# DIARY-TASK-RKG-001

## Diễn giải

- Owner đã review CTX/PLAN; triển khai bước 14 theo `PLAN-TASK-RKG-001`.
- Pin CPython **3.12.14** (`.python-version`), `pyproject.toml` + `uv.lock`, package `src/rkg/` với module placeholder theo ARCHITECTURE §3 (chỉ `__init__.py` rỗng).
- Smoke `tests/unit/test_skeleton.py`; ruff target py312 trên `src` + `tests`.
- Frontend Vite + React + TypeScript dưới `frontend/` (npm + `package-lock.json`); heading sản phẩm tối thiểu; chưa mock API (T-17).
- Cập nhật README lệnh thật; `.gitignore` bổ sung `.ruff_cache/`, `*.egg-info/`, `/dist/`.
- Không đụng T-17 / T-02 / analyzer / API.

## Đi chệch

- **Cài uv:** máy chưa có `uv`; cài qua `pip install uv` (0.12.15) thay vì script astral (blocked bởi sandbox/auto-review). README ghi cả hai cách.
- **Scaffold frontend:** `npm create vite@latest frontend` bị cancel vì thư mục `frontend/` đã có `dist/.gitkeep` — scaffold thủ công tương đương template react-ts.
- **Node runtime local:** plan chốt Node **22** LTS (`.nvmrc` = 22; `engines.node` = `>=22 <25`). Máy chạy kiểm tra dùng **Node v24.20.0**; build/lint vẫn xanh. CI/dev nên ưu tiên Node 22 theo `.nvmrc`.
- **Vite build xóa `dist/`:** thêm bước post-build ghi lại `frontend/dist/.gitkeep` để giữ convention ignore.

## Đánh đổi

- Dev deps Python dùng `[dependency-groups] dev` (uv) thay optional-dependencies; lệnh: `uv sync --group dev`.
- Graph UI lib chưa cài (đúng plan — chốt ở T-17).

## Kiểm tra đã chạy

| Lệnh | Kết quả |
| --- | --- |
| `uv sync --group dev` | pass — CPython 3.12.14, tạo/cập nhật `uv.lock` |
| `uv run python -c "import sys; assert sys.version_info[:2]==(3,12)"` | pass — `3.12.14` |
| `uv run python -c "import rkg"` | pass — `__version__ == 0.1.0` |
| `uv run pytest` | pass — 2 passed |
| `uv run ruff check src tests` | pass — All checks passed |
| `cd frontend && npm ci && npm run build` | pass — Vite production build |
| `cd frontend && npm run lint` | pass — ESLint sạch |

## Chưa kiểm tra

- Clean clone trên máy khác / CI runner với Node 22 đúng `.nvmrc`.
- `npm run dev` E2E thủ công trong browser (không thuộc DoD T-01).
- Analyzer/API/Explorer — ngoài phạm vi.

## DoD (plan)

- [x] `uv.lock` + `frontend/package-lock.json` có trong repo
- [x] `uv run pytest` và `uv run ruff check src tests` xanh
- [x] `npm ci && npm run build` trong `frontend/` xanh
- [x] README lệnh khớp thực tế
- [x] Diary + task artifact + `docs/TASK.md` đồng bộ `done`

## Lịch sử revision 2

# DIARY-TASK-RKG-001-r2

## Diễn giải

- 2026-09-23 — Slice FE của TASK-RKG-001: scaffold mới bằng `npm create vite@latest frontend -- --template react-ts`. Không `git checkout` / restore commit cũ.
- Authority: `.aide/` (CMP-RKG-WEB, ADR-2026-003, TASK-RKG-001). Không dùng `docs/` làm nguồn thiết kế.
- App base chỉ heading "Repository Knowledge Graph"; chưa screen/route/RkgClient (T-017).
- Pin Node 22 qua `.nvmrc`; `engines.node` `>=22 <25`. Máy chạy kiểm tra: Node v24.20.0, npm 11.19.0.

## Đi chệch

- Template Vite hiện tại dùng **oxlint** thay ESLint trong PLAN-r1; PLAN-r2 chấp nhận oxlint từ scaffold chính thức.
- TypeScript pin `~5.9.3` (ổn định với Vitest 3) thay vì `~6.0` của template create-vite.
- Tách `vitest.config.ts` khỏi `vite.config.ts` vì Vite 8 + Vitest 3 xung đột type khi gộp `defineConfig`.

## Đánh đổi

- Smoke test = Vitest + Testing Library (một test heading). Đủ cho base toolchain; chưa a11y/E2E.
- Graph canvas lib vẫn chưa cài (chờ T-017).

## Lệnh đã chạy và kết quả

| Lệnh | Kết quả |
| --- | --- |
| `npm create vite@latest frontend -- --template react-ts` | pass — scaffold mới |
| `cd frontend && npm install` | pass — `package-lock.json` |
| `cd frontend && npm run lint` | pass — oxlint |
| `cd frontend && npm test` | pass — 1 test |
| `cd frontend && npm run build` | pass — Vite 8 production build + `dist/.gitkeep` |
| `cd frontend && npm ci && npm test && npm run build` | pass — clean lock verify |

## Còn lại (TASK-RKG-001 chưa done)

- Python: `pyproject.toml`, `.python-version`, `uv.lock`, package `src/rkg` có nguồn (không chỉ cache), pytest/ruff xanh.
- Kùzu: pin version + `DDL-RKG-GRAPH.cypher` execute được.
- README phần Python vẫn placeholder cho đến khi slice đó xong.

## Không làm trong slice này

- UI nghiệp vụ / mock client / UIS fixtures.
- Đánh `done` TASK-RKG-001.
- Sửa FR/AC/CMP/ADR.
---

## Lịch sử revision 3

# DIARY-TASK-RKG-001-r3

## Diễn giải

- 2026-09-24 — Hoàn tất phần còn lại của TASK-RKG-001 sau slice FE (r2): khôi phục
  Python skeleton (`pyproject.toml`, `.python-version` = 3.12.14, `src/rkg` package
  placeholder theo ARCHITECTURE layout, `tests/`), tạo `uv.lock`, pin **Kùzu 0.11.3**,
  smoke pytest/ruff, chứng minh `DDL-RKG-GRAPH.cypher` execute được, cập nhật README
  lệnh Python thật.
- Không implement analyzer/API/CLI/Explorer (T-002+ / T-017 / T-025).
- Không sửa FR/AC/CMP/ADR/`docs/*` normative ngoài evidence + status task + README
  vận hành.

## Đi chệch

- Kùzu pin thêm so với diary r1 (r1 chưa có runtime graph lib): chọn **0.11.3**
  (PyPI latest tại thời điểm implement) để thỏa DoD “DDL execute trên version đã pin”.
- Smoke DDL nằm ở `tests/integration/test_ddl_execute.py` (temp DB), không viết
  storage façade production (`CMP-RKG-GRAPH` / T-013).

## Đánh đổi

- `kuzu==0.11.3` là dependency runtime của package `rkg` (pin sớm cho Contract Gate),
  dù graph store chưa có.
- Module con dưới `src/rkg/*` chỉ `__init__.py` rỗng (placeholder layout).

## Lệnh đã chạy và kết quả

| Lệnh | Kết quả |
| --- | --- |
| `uv sync --group dev` | pass — CPython 3.12.14, `kuzu==0.11.3`, `uv.lock` |
| `uv run python -c "import sys; assert sys.version_info[:2]==(3,12)"` | pass — `3.12.14` |
| `uv run python -c "import rkg"` | pass — `__version__ == 0.1.0` |
| `uv run ruff check src tests` | pass — All checks passed |
| `uv run pytest` | pass — 4 passed (2 skeleton + 2 DDL/Kùzu) |
| `cd frontend && npm ci && npm run lint && npm test && npm run build` | pass — oxlint; 1 Vitest; Vite 8 build |

## DoD TASK-RKG-001

- [x] `uv.lock` + `frontend/package-lock.json` có trong repo
- [x] `uv run pytest` và `uv run ruff check src tests` xanh
- [x] `DDL-RKG-GRAPH.cypher` execute trên Kùzu **0.11.3**
- [x] README lệnh Python/FE khớp thực tế
- [x] Evidence diary r3; task → `done`

## Không làm trong slice này

- UI nghiệp vụ / mock client / UIS fixtures.
- FastAPI routes, analyzer, graph publication runtime.
- Sửa `docs/` hay FR/AC/CMP.
---

## Lịch sử revision 4

# DIARY-TASK-RKG-001-r4

## Diễn giải

- 2026-09-24 — Close-out hygiene sau review post-r3 (không đổi DoD runtime):
  cập nhật README / `.aide/README.md` / `AGENTS.md` vì bộ `docs/` sản phẩm đã gỡ;
  bump `REG-REPO-001` khớp `src/rkg` + `frontend/src`; sửa handoff `TASK-RKG-017` /
  `TASK-RKG-025`; thêm placeholder `src/rkg/adapters/__init__.py`.
- Evidence r3 (`DIARY-…-r3`, `TEST-RKG-DDL-BOOTSTRAP-001`,
  `tests/integration/test_ddl_execute.py`) và `uv.lock` vẫn cần `git add` + commit
  riêng khi người vận hành yêu cầu — diary này không commit giúp.

## Đi chệch

- PLAN DoD từng đòi sync `docs/TASK.md` → `done`. Product `docs/` đã retire; thay
  bằng cập nhật README/AGENTS/`.aide/README` trỏ về `.aide/` (không khôi phục
  `docs/TASK.md`).

## Không làm

- Không `git add` / commit `uv.lock` trong slice này (theo chỉ đạo: chỉ trả lời
  cách đưa lock vào Git).
- Không đổi pin Kùzu/CPython/Node; không implement UI/API.
---

## Đối chiếu commit và phạm vi hiện hành

## Kết quả đối chiếu triển khai

Dựng src/tests/frontend, khóa Python/Kuzu và frontend toolchain, ghi lệnh setup/lint/test/build. Giữ scaffold tách khỏi chức năng nghiệp vụ.

Các file thay đổi được xác định bằng Git diff của các commit được pin trong frontmatter. Current-tree hash nằm trong context revision 3; khác hash lịch sử là revision về sau, không phải cùng lần chạy.

## Diễn giải và correction

Scaffold có nhiều mốc: commit ec0a1c0 ngày 17/09 và toolchain reset/khóa ở 9cae9d0 ngày 24/09; không gộp chúng thành một lần chạy.

## Kết quả lần bổ sung hồ sơ

Đã đọc commit/file, parse test declarations và liên kết evidence; không chạy lại runtime test hoặc đo KPI. Không nhận đây là review code độc lập hay approval.
