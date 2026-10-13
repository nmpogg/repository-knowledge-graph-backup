---
key: PLAN-TASK-RKG-001
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-001
revision: 3
plan_date: '2026-09-17'
date_basis:
  commit: ec0a1c04815ab62a181dfcec08035d21b17cc551
  field: author_at converted to Asia/Bangkok
provenance: git-derived implementation plan
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  context: CTX-TASK-RKG-001.yaml
verification_targets:
- path: tests/integration/test_ddl_execute.py
  tests:
  - test_pinned_kuzu_version
  - test_ddl_rkg_graph_executes
- path: tests/unit/test_skeleton.py
  tests:
  - test_package_version
  - test_import_rkg
frontend_test_paths:
- frontend/src/App.test.tsx
revision_history:
- revision: 1
  metadata:
    key: PLAN-TASK-RKG-001
    type: implementation-plan
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
      - key: ADR-2026-001
        revision: 1
      - key: CMP-RKG-WEB
        revision: 1
      docs:
      - docs/ARCHITECTURE.md
      - docs/SPEC.md
      - docs/RULES.md
      - docs/TASK.md
  record: |-
    # PLAN-TASK-RKG-001

    ## Mục tiêu

    Khởi tạo skeleton `src/` · `tests/` · `frontend/` và chốt toolchain (CPython 3.12 patch, Node, package managers, lockfiles, lệnh check). Xong khi clean environment chạy được checks tối thiểu và README ghi đúng lệnh thực tế — mở đường cho T-17 (UI mock) và T-02 (domain schema).

    Không thỏa AC nghiệp vụ; không ship analyzer/API/Explorer.

    ## Quyết định toolchain (chốt trong task này)

    | Mục | Lựa chọn | Lý do ngắn |
    | --- | --- | --- |
    | Python | CPython **3.12.x** (pin patch khi implement, ghi README) | SPEC + ADR-2026-001 |
    | Python packaging | `pyproject.toml` + **uv** → `uv.lock` | SPEC đã đọc `uv.lock`; một lockfile cho CI/local |
    | Python test | **pytest** (+ cấu hình trong pyproject) | ARCHITECTURE §2 |
    | Python lint (tối thiểu) | **ruff** check | nhẹ, đủ smoke cho skeleton |
    | Frontend | **React + Vite + TypeScript** | PRD / CMP-RKG-WEB |
    | Node | **Node 22 LTS** (pin major trong README / `.nvmrc` hoặc `engines`) | LTS ổn định tại thời điểm plan |
    | JS package manager | **npm** + `package-lock.json` | mặc định Vite; không bắt buộc pnpm trừ khi team đổi sau |
    | Graph UI lib | **chưa cài** ở T-01 | chốt phiên bản khi T-17 cần canvas |

    Nếu môi trường local không có đúng patch Python: ghi rõ patch đã lock và yêu cầu CI/dev khớp; không hạ major xuống 3.11.

    ## Thứ tự triển khai

    1. **Pin Python toolchain**
       - **File:** `pyproject.toml` (tạo mới), tùy chọn `.python-version`
       - **Đổi:** `requires-python = ">=3.12,<3.13"`; project name `rkg`; packages dưới `src/`; dev deps: `pytest`, `ruff`; script entry placeholder (không bắt buộc CLI thật).
       - **Kiểm:** `uv sync` (hoặc lệnh tương đương trong README) tạo/ cập nhật `uv.lock`; `uv run python -c "import sys; assert sys.version_info[:2]==(3,12)"`.

    2. **Skeleton package `src/rkg/`**
       - **File:** `src/rkg/__init__.py` (+ `__version__` hoặc docstring tối thiểu); thư mục con theo ARCHITECTURE §3 chỉ cần `.gitkeep` hoặc `__init__.py` rỗng cho các module sẽ làm sau (`domain/`, `api/`, …) — **không** viết logic analyzer/API.
       - **Đổi:** import được `import rkg`.
       - **Kiểm:** `uv run python -c "import rkg"`.

    3. **Tests smoke**
       - **File:** `tests/unit/test_skeleton.py` (hoặc `tests/test_skeleton.py`); `tests/fixtures/.gitkeep`, `tests/integration/.gitkeep`, `tests/evals/.gitkeep` nếu giữ layout ARCHITECTURE.
       - **Đổi:** một test assert version/package import.
       - **Kiểm:** `uv run pytest` → xanh.

    4. **Ruff config + lệnh lint**
       - **File:** section `[tool.ruff]` trong `pyproject.toml`
       - **Đổi:** target py312; include `src` + `tests`.
       - **Kiểm:** `uv run ruff check src tests` → xanh trên skeleton.

    5. **Frontend Vite + React + TS**
       - **File:** cây `frontend/` (`package.json`, `vite.config.ts`, `tsconfig*.json`, `index.html`, `src/main.tsx`, `src/App.tsx`, `src/vite-env.d.ts`, `public/`)
       - **Đổi:** app tối thiểu render một heading (ví dụ tên sản phẩm); `engines.node` hoặc `.nvmrc` = 22; chưa mock API client (T-17).
       - **Kiểm:** trong `frontend/`: `npm ci` (sau khi có lock) · `npm run build` · (tuỳ chọn) `npm run lint` nếu bật ESLint mặc định Vite.

    6. **`.gitignore` / dist placeholder**
       - **File:** `.gitignore` (đã có `node_modules/`, `frontend/dist/**`); bổ sung nếu thiếu `.venv/`, cache tool mới.
       - **Đổi:** giữ `frontend/dist/.gitkeep` nếu convention hiện tại yêu cầu.
       - **Kiểm:** `git status` không stage `node_modules` / `.venv`.

    7. **README vận hành**
       - **File:** `README.md`
       - **Đổi:** thay đoạn “chưa có lệnh” bằng bảng lệnh thật: Python sync/test/lint; frontend install/dev/build; nêu Node 22 + CPython 3.12.x đã pin; nêu rõ analyzer/API chưa có.
       - **Kiểm:** người khác (hoặc agent) làm theo README trên clean env không cần đoán thêm cờ.

    8. **Evidence + trạng thái task**
       - **File:** `.aide/evidence/diaries/DIARY-TASK-RKG-001.md`; `.aide/lifecycle/tasks/TASK-RKG-001.md` (`status`); `docs/TASK.md` bảng §4 + §8.
       - **Đổi:** diary ghi lệnh đã chạy + kết quả; không sửa PLAN này (append-only). Lệch hướng → mục “Đi chệch” trong DIARY.
       - **Kiểm:** status `done` chỉ khi bước 1–7 đã chạy thật và diary ghi evidence.

    ## Không làm

    - Không implement T-17 (mock client, fixture Explorer, panels).
    - Không implement T-02+ (schema domain, ingestion, extractors, Kùzu, FastAPI routes).
    - Không thêm LLM provider, credential mẫu, hoặc mặc định model giả.
    - Không sửa FR/AC/L2/SPEC để “khớp” scaffold; mâu thuẫn → OQ, dừng.
    - Không refactor `.aide/` artifacts ngoài cập nhật status/evidence của task này.
    - Không tuyên bố M0 / Explorer E2E xong.

    ## Rủi ro / giả định

    - **Giả định:** máy dev có (hoặc sẽ cài) `uv`, Node 22, CPython 3.12.x. Nếu thiếu, README nêu cách cài tối thiểu.
    - **Rủi ro:** chọn patch Python khác nhau giữa máy → mitigations bằng pin + `uv.lock` + ghi rõ trong README.
    - **Rủi ro:** Vite template kéo ESLint/React version mới — chấp nhận lock tại thời điểm scaffold; không upgrade lung tung trong cùng MR.
    - **Baseline `.aide/` vẫn draft:** toolchain dựa `docs/ARCHITECTURE.md` / SPEC; không chờ Scope Gate để làm T-01 theo backlog đã chốt.

    ## Definition of Done (task)

    - [ ] `uv.lock` + `frontend/package-lock.json` có trong repo
    - [ ] `uv run pytest` và `uv run ruff check src tests` xanh
    - [ ] `npm ci && npm run build` trong `frontend/` xanh
    - [ ] README lệnh khớp thực tế
    - [ ] `DIARY-TASK-RKG-001` ghi lệnh + kết quả; task artifact + `docs/TASK.md` đồng bộ `done`
- revision: 2
  metadata:
    key: PLAN-TASK-RKG-001-r2
    type: implementation-plan
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-001
    revision: 2
    captured_at: 2026-09-23
    captured_against:
      artifacts:
      - key: TASK-RKG-001
        revision: 3
      - key: CTX-TASK-RKG-001-r2
        revision: 2
      - key: CMP-RKG-WEB
        revision: 4
      - key: ADR-2026-003
        revision: 1
      - key: NFR-RKG-SEC-001
        revision: 7
  record: |-
    # PLAN-TASK-RKG-001-r2 — Frontend base scaffold only

    ## Mục tiêu

    Tạo mới hoàn toàn `frontend/` (React + Vite + TypeScript) làm base toolchain cho
    `CMP-RKG-WEB`. Không lấy code từ commit cũ. Không dựng giao diện nghiệp vụ.

    Slice này **không** đóng đủ DoD TASK-RKG-001 (còn Python/uv/Kùzu DDL).

    ## Quyết định (chốt)

    | Mục | Lựa chọn |
    | --- | --- |
    | Stack | React + Vite + TypeScript |
    | Node | 22 (`.nvmrc`); `engines.node`: `>=22 <25` |
    | Package manager | npm + `package-lock.json` |
    | Test | Vitest + Testing Library smoke |
    | Lint | ESLint (flat config Vite/TS) |
    | UI nghiệp vụ | Không — chỉ heading sản phẩm tối thiểu |

    ## Thứ tự

    1. **Pin Node**
       - **File:** `.nvmrc`
       - **Đổi:** nội dung `22`
       - **Kiểm:** file tồn tại; `node -v` major ∈ [22, 24] trên máy chạy.

    2. **Scaffold Vite React-TS mới**
       - **File:** cả cây `frontend/` tạo bằng `npm create vite@latest` (template `react-ts`), không `git checkout` / copy từ history.
       - **Đổi:** app tối thiểu; `App` chỉ render heading "Repository Knowledge Graph"; không screen/route/mock.
       - **Kiểm:** `frontend/package.json` có scripts `dev`, `build`, `lint`.

    3. **Smoke test**
       - **File:** `frontend/src/App.test.tsx`, cấu hình Vitest trong `vite.config.ts` + deps dev.
       - **Đổi:** test assert heading sản phẩm render được.
       - **Kiểm:** `npm test` → pass.

    4. **Lock + dist placeholder**
       - **File:** `frontend/package-lock.json`, `frontend/dist/.gitkeep`; `engines` trong `package.json`.
       - **Đổi:** lock sau `npm install`; giữ convention `.gitignore` cho `dist/**` + `.gitkeep`.
       - **Kiểm:** `npm ci` sạch; `npm run build` xanh; `dist/.gitkeep` còn sau build (postbuild nếu Vite xóa dist).

    5. **README FE commands**
       - **File:** `README.md` (mục Frontend)
       - **Đổi:** ghi lệnh thật `npm ci` / `npm run dev` / `npm test` / `npm run lint` / `npm run build`; nêu Node 22 pin.
       - **Kiểm:** lệnh khớp diary.

    6. **Evidence + task note**
       - **File:** `DIARY-TASK-RKG-001.md`; bump `TASK-RKG-001` điểm tiếp tục (revision task +1).
       - **Đổi:** diary ghi lệnh + kết quả; task vẫn `in_progress` (Python chưa xong).
       - **Kiểm:** không đánh `done`.

    ## Không làm

    - Không restore FE từ git.
    - Không screens / AppShell / Explorer / RkgClient / UIS fixtures (T-017/T-025).
    - Không Python `pyproject.toml` / `uv.lock` / Kùzu trong MR slice này.
    - Không sửa FR/AC/CMP/ADR; không dùng `docs/` làm nguồn thiết kế.
    - Không cập nhật `docs/TASK.md` làm authority.

    ## Definition of Done (slice FE)

    - [ ] `frontend/` mới, không từ commit cũ
    - [ ] `.nvmrc` = 22; `package-lock.json` có trong repo
    - [ ] `npm ci && npm run lint && npm test && npm run build` xanh
    - [ ] README mục FE khớp lệnh thật
    - [ ] `DIARY-TASK-RKG-001-r2` ghi evidence; task vẫn `in_progress`
    ---
---

# PLAN-TASK-RKG-001

## Mục tiêu

Khởi tạo skeleton `src/` · `tests/` · `frontend/` và chốt toolchain (CPython 3.12 patch, Node, package managers, lockfiles, lệnh check). Xong khi clean environment chạy được checks tối thiểu và README ghi đúng lệnh thực tế — mở đường cho T-17 (UI mock) và T-02 (domain schema).

Không thỏa AC nghiệp vụ; không ship analyzer/API/Explorer.

## Quyết định toolchain (chốt trong task này)

| Mục | Lựa chọn | Lý do ngắn |
| --- | --- | --- |
| Python | CPython **3.12.x** (pin patch khi implement, ghi README) | SPEC + ADR-2026-001 |
| Python packaging | `pyproject.toml` + **uv** → `uv.lock` | SPEC đã đọc `uv.lock`; một lockfile cho CI/local |
| Python test | **pytest** (+ cấu hình trong pyproject) | ARCHITECTURE §2 |
| Python lint (tối thiểu) | **ruff** check | nhẹ, đủ smoke cho skeleton |
| Frontend | **React + Vite + TypeScript** | PRD / CMP-RKG-WEB |
| Node | **Node 22 LTS** (pin major trong README / `.nvmrc` hoặc `engines`) | LTS ổn định tại thời điểm plan |
| JS package manager | **npm** + `package-lock.json` | mặc định Vite; không bắt buộc pnpm trừ khi team đổi sau |
| Graph UI lib | **chưa cài** ở T-01 | chốt phiên bản khi T-17 cần canvas |

Nếu môi trường local không có đúng patch Python: ghi rõ patch đã lock và yêu cầu CI/dev khớp; không hạ major xuống 3.11.

## Thứ tự triển khai

1. **Pin Python toolchain**
   - **File:** `pyproject.toml` (tạo mới), tùy chọn `.python-version`
   - **Đổi:** `requires-python = ">=3.12,<3.13"`; project name `rkg`; packages dưới `src/`; dev deps: `pytest`, `ruff`; script entry placeholder (không bắt buộc CLI thật).
   - **Kiểm:** `uv sync` (hoặc lệnh tương đương trong README) tạo/ cập nhật `uv.lock`; `uv run python -c "import sys; assert sys.version_info[:2]==(3,12)"`.

2. **Skeleton package `src/rkg/`**
   - **File:** `src/rkg/__init__.py` (+ `__version__` hoặc docstring tối thiểu); thư mục con theo ARCHITECTURE §3 chỉ cần `.gitkeep` hoặc `__init__.py` rỗng cho các module sẽ làm sau (`domain/`, `api/`, …) — **không** viết logic analyzer/API.
   - **Đổi:** import được `import rkg`.
   - **Kiểm:** `uv run python -c "import rkg"`.

3. **Tests smoke**
   - **File:** `tests/unit/test_skeleton.py` (hoặc `tests/test_skeleton.py`); `tests/fixtures/.gitkeep`, `tests/integration/.gitkeep`, `tests/evals/.gitkeep` nếu giữ layout ARCHITECTURE.
   - **Đổi:** một test assert version/package import.
   - **Kiểm:** `uv run pytest` → xanh.

4. **Ruff config + lệnh lint**
   - **File:** section `[tool.ruff]` trong `pyproject.toml`
   - **Đổi:** target py312; include `src` + `tests`.
   - **Kiểm:** `uv run ruff check src tests` → xanh trên skeleton.

5. **Frontend Vite + React + TS**
   - **File:** cây `frontend/` (`package.json`, `vite.config.ts`, `tsconfig*.json`, `index.html`, `src/main.tsx`, `src/App.tsx`, `src/vite-env.d.ts`, `public/`)
   - **Đổi:** app tối thiểu render một heading (ví dụ tên sản phẩm); `engines.node` hoặc `.nvmrc` = 22; chưa mock API client (T-17).
   - **Kiểm:** trong `frontend/`: `npm ci` (sau khi có lock) · `npm run build` · (tuỳ chọn) `npm run lint` nếu bật ESLint mặc định Vite.

6. **`.gitignore` / dist placeholder**
   - **File:** `.gitignore` (đã có `node_modules/`, `frontend/dist/**`); bổ sung nếu thiếu `.venv/`, cache tool mới.
   - **Đổi:** giữ `frontend/dist/.gitkeep` nếu convention hiện tại yêu cầu.
   - **Kiểm:** `git status` không stage `node_modules` / `.venv`.

7. **README vận hành**
   - **File:** `README.md`
   - **Đổi:** thay đoạn “chưa có lệnh” bằng bảng lệnh thật: Python sync/test/lint; frontend install/dev/build; nêu Node 22 + CPython 3.12.x đã pin; nêu rõ analyzer/API chưa có.
   - **Kiểm:** người khác (hoặc agent) làm theo README trên clean env không cần đoán thêm cờ.

8. **Evidence + trạng thái task**
   - **File:** `.aide/evidence/diaries/DIARY-TASK-RKG-001.md`; `.aide/lifecycle/tasks/TASK-RKG-001.md` (`status`); `docs/TASK.md` bảng §4 + §8.
   - **Đổi:** diary ghi lệnh đã chạy + kết quả; không sửa PLAN này (append-only). Lệch hướng → mục “Đi chệch” trong DIARY.
   - **Kiểm:** status `done` chỉ khi bước 1–7 đã chạy thật và diary ghi evidence.

## Không làm

- Không implement T-17 (mock client, fixture Explorer, panels).
- Không implement T-02+ (schema domain, ingestion, extractors, Kùzu, FastAPI routes).
- Không thêm LLM provider, credential mẫu, hoặc mặc định model giả.
- Không sửa FR/AC/L2/SPEC để “khớp” scaffold; mâu thuẫn → OQ, dừng.
- Không refactor `.aide/` artifacts ngoài cập nhật status/evidence của task này.
- Không tuyên bố M0 / Explorer E2E xong.

## Rủi ro / giả định

- **Giả định:** máy dev có (hoặc sẽ cài) `uv`, Node 22, CPython 3.12.x. Nếu thiếu, README nêu cách cài tối thiểu.
- **Rủi ro:** chọn patch Python khác nhau giữa máy → mitigations bằng pin + `uv.lock` + ghi rõ trong README.
- **Rủi ro:** Vite template kéo ESLint/React version mới — chấp nhận lock tại thời điểm scaffold; không upgrade lung tung trong cùng MR.
- **Baseline `.aide/` vẫn draft:** toolchain dựa `docs/ARCHITECTURE.md` / SPEC; không chờ Scope Gate để làm T-01 theo backlog đã chốt.

## Definition of Done (task)

- [ ] `uv.lock` + `frontend/package-lock.json` có trong repo
- [ ] `uv run pytest` và `uv run ruff check src tests` xanh
- [ ] `npm ci && npm run build` trong `frontend/` xanh
- [ ] README lệnh khớp thực tế
- [ ] `DIARY-TASK-RKG-001` ghi lệnh + kết quả; task artifact + `docs/TASK.md` đồng bộ `done`

## Phạm vi code và kiểm chứng

- `.nvmrc`
- `.python-version`
- `README.md`
- `frontend/package-lock.json`
- `frontend/package.json`
- `frontend/src/App.css`
- `frontend/src/App.tsx`
- `frontend/src/index.css`
- `frontend/src/main.tsx`
- `frontend/src/vite-env.d.ts`
- `pyproject.toml`
- `src/rkg/__init__.py`
- `src/rkg/api/__init__.py`
- `src/rkg/cli/__init__.py`
- `src/rkg/config/__init__.py`
- `src/rkg/conversations/__init__.py`
- `src/rkg/detection/__init__.py`
- `src/rkg/domain/__init__.py`
- `src/rkg/extractors/__init__.py`
- `src/rkg/graph/__init__.py`
- `src/rkg/ingestion/__init__.py`
- `src/rkg/jobs/__init__.py`
- `src/rkg/llm/__init__.py`
- `src/rkg/parsing/__init__.py`
- `src/rkg/resolution/__init__.py`
- `src/rkg/storage/__init__.py`
- `tests/evals/.gitkeep`
- `tests/fixtures/.gitkeep`
- `tests/integration/.gitkeep`
- `tests/unit/test_skeleton.py`
- `uv.lock`
- `src/rkg/adapters/__init__.py`
- `tests/integration/test_ddl_execute.py`

- `python -m pytest tests/integration/test_ddl_execute.py tests/unit/test_skeleton.py -q`
- Trong `frontend/`: `npm test`, `npm run lint`, `npm run build`.

Các lệnh này mô tả cách kiểm, không khẳng định đã chạy trong lần bổ sung hồ sơ. Kết quả thực thi theo evidence đã ghi của task.

Context: [CTX-TASK-RKG-001](../context/CTX-TASK-RKG-001.yaml). Kết quả triển khai: [DIARY-TASK-RKG-001](../diaries/DIARY-TASK-RKG-001.md).
