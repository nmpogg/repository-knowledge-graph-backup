# RKG docs-first artifact index

Thư mục này chứa artifact chuẩn tắc của dự án theo `AGENTS.md`. Workflow Agentic
SDLC tổng quát và PRD template tại `docs/reference/agentic-sdlc/` chỉ là tài liệu
tham khảo (không normative).

Phần lớn artifact chuẩn tắc đang `draft`. `TASK-RKG-000` đến `TASK-RKG-041` đã
`done`. `TASK-RKG-042` đến `TASK-RKG-055` vẫn `in_progress` trên
`CHG-RKG-2026-009`…`022`: deep-support vẫn withheld, chưa có baseline.
`EPIC-001`, `EPIC-003`, `EPIC-004` và `EPIC-005` khớp task đã `done`.
`EPIC-002` và `EPIC-006` là `in_progress`. `OQ-RKG-001`…`005` và `OQ-RKG-007`
đã resolve. `OQ-RKG-006` và `OQ-RKG-008` vẫn mở. Gate Scope, Architecture, UI/UX
và Contract của `CHG-RKG-2026-001` vẫn pending. Component Merge có checklist
`GATE-MERGE`; các approval `012`/`013` chỉ khóa lát cắt đã ghi trên
`CHG-RKG-2026-002`. UAT có checklist `GATE-UAT` và chưa có approval. Change Set
view là artifact dẫn xuất. Runbook vận hành nằm ở `README.md` (setup, đường dẫn
local, index, serve, LLM, lịch sử, retention, xử lý sự cố).

Bộ `docs/` sản phẩm (SPEC/ARCHITECTURE/TASK/…) đã gỡ khỏi repo — không còn nguồn
đối chiếu chuyển tiếp. Mọi quyết định lấy từ `.aide/`.

## Cây artifact đang áp dụng

```text
.aide/
├── product/           prd  (vision/proposals: tuỳ chọn — chưa tạo)
├── requirements/      fr · nfr
├── domain/
├── architecture/      l1 · l2 · adr · threat-model
├── tech-specs/        <CMP-slug>/{api,events,schema}
├── design/            ux · ui/tokens
├── observability/
├── lifecycle/         change-sets · epics · stories · tasks · bugs · releases
├── evidence/          requests · context · plans · diaries · reviews · findings · decisions · approvals · tests · deployments · production
├── policies/          rules (chưa có VAL-*) · gates · eval
├── reviewer/          packages · prompts (không normative)
├── registry/
└── generated/         traceability · change-set-views · architecture-views · diagrams · ui-mocks
```

Root vận hành: `AGENTS.md` · `.aide/` · `docs/reference/agentic-sdlc/` (tham khảo).
Tree code hiện có: `src/rkg/` (domain, storage/graph, index job/CLI, HTTP
transport `src/rkg/api`), `tests/`,
`frontend/` (UI repository/snapshot, Explorer và hội thoại; live khi `VITE_RKG_CLIENT=live`),
`pyproject.toml`, `.python-version`, `uv.lock`. Handoff thiết kế ở `design/`.
Trạng thái task chính thức nằm trong frontmatter tại `lifecycle/tasks/`.

## Điểm vào — Scope Gate (bước 1 + 4)

| Nhóm | Path | Ghi chú |
|---|---|---|
| **PRD** | `product/prd/PRD-RKG.md` | GOAL · KPI · Scope · Persona · flows (template I–IX) |
| **FR + AC** | `requirements/fr/FR-RKG-001..005.md` | Năm capability-level FR; AC dạng given/when/then nằm trong FR |
| **NFR** | `requirements/nfr/NFR-RKG-*.md` | PERF · SEC · REL · UX · EXT — ràng buộc và ngưỡng sống ở đây |

- Domain: `domain/glossary-core.md`
- Architecture: `architecture/l1/`, `architecture/l2/`, `architecture/adr/`, `architecture/threat-model/`
- Contracts: `tech-specs/RKG-TRANSPORT/api/` · `tech-specs/RKG-GRAPH/schema/`
- Experience: `design/README.md`, `design/ux/` và `design/ui/`
- Observability KPI: `OBS-RKG-001`, `002`, `005`; performance và extensibility quality gates nằm trong NFR tương ứng
- Delivery: `lifecycle/change-sets/CHG-RKG-2026-001/` … `022/` · `lifecycle/epics/` · `lifecycle/stories/` · `lifecycle/tasks/`
- Evidence: `evidence/`
- Policies: `policies/gates/` (`GATE-RKG-SCOPE`, `ARCHITECTURE`, `UIUX`, `CONTRACT`, `GATE-MERGE`, `GATE-UAT`) · rubric ở `policies/eval/`
- Review inputs: `reviewer/packages/`, `reviewer/prompts/` — không normative; disposition chính thức được append ở `evidence/reviews/`
- Registries: `registry/`
- Generated: `generated/`

ID AC đã phát hành không được tái sử dụng sau khi scope thay đổi. Khoảng trống như
`AC-RKG-019` là ID đã retire; task và artifact hiện hành không được tham chiếu ID đã
retire nếu không có AC tương ứng.

Các thư mục placeholder chỉ được tạo artifact khi đến đúng phase: `stories/` và
`bugs/` khi breakdown/phát hiện công việc, `releases/` khi release prep, và các
nhánh evidence `tests/`, `approvals/`, `deployments/`, `production/` khi có bằng
chứng thực tế. Không tạo approval/test evidence giả để làm đầy cây.

Gate checklist hiện nằm ở `policies/gates/`; các checklist chỉ định điều kiện và
không tự phê duyệt. Evidence ký duyệt phải được append vào `evidence/approvals/`.
Rubric Q&A nằm ở `policies/eval/EVAL-RKG-QA-001.md`.

## Eval / evidence authority (hiện hành)

Trần evaluation là KPI-RKG-005. Lần quét này không đo lại và không mở KPI đã retire.

| Nhánh | Authority hiện tại | Ghi chú |
|---|---|---|
| Policy nghiệm thu Q&A | `policies/eval/EVAL-RKG-QA-001.md` | Rubric / KPI method — không đặt trong `tests/` hay evidence |
| Harness (census, pilot runners, oracle JSON) | `tests/evaluation/` | Không dùng `tests/evals/` |
| Census (OBS-RKG-001) | `TEST-RKG-FIXTURE-CENSUS-SUMMARY-001` (+ raw `TEST-RKG-FIXTURE-CENSUS-001`) | Coverage 1.00, precision 1.00, 296 TP / 0 FN / 0 FP. Bản extraction cũ (`TEST-RKG-EXTRACTION-FIXTURES-001`, `-r2`) là historical. Chưa có oracle review receipt |
| Extraction scope note | `TEST-RKG-EXTRACTION-FIXTURES-001-r3` | Bổ sung phạm vi MVP; không thay census numbers |
| Q&A (OBS-RKG-005) | `TEST-RKG-QA-EVAL-SUMMARY-001-r4` | `001` / `-r2` / `-r3` historical; raw `TEST-RKG-QA-EVAL-001` |
| Pilot precision (OBS-RKG-002) | `TEST-RKG-PILOT-REVIEW-SUMMARY-002` | Sheet `TEST-RKG-KPI002-SHEET-003`; `TEST-RKG-PILOT-REVIEW-SUMMARY-001` historical, digest cũ |
| Perf (NFR-RKG-PERF-001) | `TEST-RKG-PERF-SUMMARY-002` | Raw `TEST-RKG-PERF-002-RUN1` / `RUN2`; `TEST-RKG-PERF-SUMMARY-001` historical. Pilot dưới trần kích thước, không phải nghiệm thu full-size |
| Oracle review / receipt | `REV-RKG-EVAL-ORACLE-001` / `RCPT-RKG-EVAL-ORACLE-001` | `.aide/evidence/reviews/` |

Unit/conformance: `tests/unit/`, `tests/conformance/`. Báo cáo đã chạy: `.aide/evidence/tests/` (`TEST-*`).

## Quy tắc phân xử

Artifact normative trong `.aide/` là nguồn quyết định. Không dùng bộ `docs/` sản
phẩm đã retire làm đối chiếu song song. `docs/reference/agentic-sdlc/` chỉ tham
khảo quy trình. Sau Scope Gate, baseline được ký mới trở thành tập revision dùng
cho implementation.

## Đối chiếu Agentic SDLC — 2026-10-08

Quét theo `docs/reference/agentic-sdlc/agentic-sdlc-workflow-reference.md` đến
thời điểm hiện tại. Không mở task mới và không sửa source. Phần evaluation dừng
ở KPI-RKG-005: không đo lại, không thêm KPI đã retire.

Đối chiếu 2026-10-05 (bước 1–14, task 000–029) giữ nguyên như hồ sơ lịch sử.
Những mục dưới đây là trạng thái cây hiện tại.

### Cây thư mục (§A.1)

Top-level `.aide/` khớp chuẩn. `product/vision/` và `product/proposals/` không
tạo (bước 0 tuỳ chọn). `policies/rules/` chưa có `VAL-*` vì bước 22 chưa chạy.
`lifecycle/bugs/` và `lifecycle/releases/` chỉ có placeholder: chưa có bug và
chưa tới release prep. `evidence/deployments/` và `evidence/production/` trống
vì chưa có deployment record. `generated/traceability/` bị gitignore (sinh lại mỗi lần CI, không ai ký).
Lệnh ghi: `python -m tools.write_traceability` từ root repo. Không có `EVT-*`
và không có `SVC-*`.

`CHG-RKG-2026-001`…`008` có `change-set.yaml`, `impact.yaml` và baseline.
`CHG-RKG-2026-009`…`022` có shell và impact, `baseline: not_recorded` — không
tạo file baseline giả. CSV dẫn xuất hiện có cho `001` và `002`. Các change set
`003`…`022` chưa có CSV; view đó chỉ sinh bằng generator, không viết tay.

### Bước đã tới

| # | Bước | Trạng thái hiện tại |
|---|---|---|
| 1–10 | PRD đến UI spec / contract | Artifact có. Gate Scope, Architecture, UI/UX, Contract của `CHG-RKG-2026-001` vẫn pending. `OQ-RKG-006` mở. `OQ-RKG-007` resolved. |
| 11 | Epic / Story / Task | Epic ×6. `EPIC-001`, `EPIC-003`, `EPIC-004`, `EPIC-005` khớp task `done`. `EPIC-002` và `EPIC-006` là `in_progress`. Story ×43 (016 deprecated). Task ×56. `000`–`041` `done`. `042`–`055` `in_progress`. |
| 12–14 | Context, plan, diary | Mỗi task `000`–`055` có CTX, PLAN và DIARY. |
| 15–16 | Validation và Component Merge | Checklist `GATE-MERGE`. `approval-012` và `approval-013` chỉ khóa lát cắt đã ghi trên `CHG-RKG-2026-002`. Change set khác vẫn `component_merge: pending`. |
| 18 | UAT | Checklist `GATE-UAT`. `CHG-RKG-2026-002` phase UAT pending. Chưa có approval UAT. |
| 19–22 | Release, deploy, close | Chưa tới. Không tạo release plan, deployment hay production record. |

### Việc còn cần người quyết

1. **OQ-RKG-006:** ai được ủy quyền ký Scope / UI/UX cho revision hiện tại.
2. Component Merge và UAT của từng change set chưa được quyết cho toàn bộ lát cắt đang pending.
3. `TASK-RKG-042`…`055` chưa `done`; deep-support vẫn withheld; baseline `009`…`022` chưa được ghi.
4. **OQ-RKG-008:** chiều `depends_on` của liên kết HTTP tĩnh so với then-clause `AC-RKG-005`. Chặn đóng `TASK-RKG-055` và `component_merge` của `CHG-RKG-2026-022`. Then-clause không sửa tại chỗ.

### Giữ nguyên

- `TASK-RKG-000` không thêm `epic`.
- `DDL-RKG-GRAPH.cypher` đứng cạnh TBL.
- Không tạo `VAL-*`, `product/vision/`, `EVT-*`.
- Không viết tay CSV cho change set `003`…`022`.
- Evaluation không đi quá KPI-RKG-005.
