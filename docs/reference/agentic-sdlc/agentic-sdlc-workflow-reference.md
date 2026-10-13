# Agentic SDLC — Execution Guide

**Tài liệu này nói *làm gì*. Không nói *vì sao*.** Mọi lý do, lập luận và đánh đổi nằm ở `process-working.md` (PROC-SDLC-001); ở đây chỉ trích mục để tra khi cần.

Quan hệ hai tài liệu:

| | `process-working.md` | `execution-guide-working.md` *(tài liệu này)* |
|---|---|---|
| Trả lời | Mô hình là gì, vì sao chọn thế | Tôi phải làm gì, ở đâu, ra cái gì |
| Ai đọc | Người phải đồng ý với mô hình | Người đang làm việc |
| Đọc khi | Một lần, lúc onboard hoặc lúc muốn đổi mô hình | Mỗi lần làm một bước |

Tra nhanh: **§A** thư mục · **§B** 23 bước · **§C** context và prompt cho agent · **§D** gate và governance · **§E** UI/UX · **§F** ví dụ đầy đủ · **§G** theo vai · **§H** rollout.

---

# A. Cấu trúc thư mục

## A.1 Cây chuẩn

> **Giả định: một repo = một System.** Cây dưới không có trục system vì không cần — mọi artifact trong repo này thuộc về cùng một System, và `<SYS>` trong `key` chỉ để ID unique toàn tổ chức.
>
> Nhiều System thì **nhiều repo**, mỗi repo một cây như dưới. Tham chiếu chéo (ví dụ `depends_on: API-IAM-v2` ở repo khác) đi qua **metadata graph tập trung** (PROC §4.4.2) chứ không qua đường dẫn file — nên nó chỉ chạy được từ mức C1 trở lên. Ở pilot C0+ với một System thì không gặp ca này.
>
> Nếu sau này thật sự cần monorepo nhiều System, thêm một tầng `systems/<SYS>/` bọc từ `product/` tới `observability/`; `lifecycle/`, `evidence/`, `policies/`, `registry/`, `generated/` vẫn ở gốc vì chúng cắt ngang mọi System.

```text
repo/
│
├── .aide/
│   │
│   ├── product/                          ← SCOPE TIER, sống lâu                              [Normative]
│   │   ├── vision/                      VISION-<SCOPE>.md     org hoặc system
│   │   ├── proposals/                   PROP-YYYYQN-NNN.md    org/domain — KHÔNG chết
│   │   └── prd/                         PRD-<SYS>.md          ← MỘT PRD cho mỗi System
│   │
│   ├── requirements/                                                                          [Normative]
│   │   ├── fr/                          FR-<SYS>-NNN.md       ← AC nằm trong file FR
│   │   └── nfr/                         NFR-<SCOPE>-<CAT>-NNN.md
│   │
│   ├── domain/                                                                                [Normative]
│   │   ├── glossary-core.md
│   │   └── <domain>/glossary.md
│   │
│   ├── architecture/                                                                          [Normative]
│   │   ├── l1/                          CAP-<SYS>-NNN.md · SVC-<SYS>-NNN.md
│   │   ├── l2/                          CMP-<SYS>-NNN.md
│   │   ├── adr/                         ADR-YYYY-NNN.md
│   │   └── threat-model/                TM-<SYS>.md
│   │
│   ├── tech-specs/                      ← L3, BẮT BUỘC ở Git — chia theo COMPONENT             [Normative]
│   │   └── <CMP-slug>/                  chỉ component sở hữu ≥1 API/TBL/EVT mới có thư mục
│   │       ├── api/                     API-<SYS>-<CMP>-vN.md
│   │       ├── events/                  EVT-<SYS>-<CMP>-<topic>.md
│   │       └── schema/                  TBL-<SYS>-<CMP>.md
│   │
│   ├── design/                                                                                [Normative]
│   │   ├── ux/                          UXF-<SYS>-NNN.md · SCR-<SYS>-NNN.md
│   │   └── ui/                          UID-<SYS>-NNN.md · UIS-<SYS>-NNN.md · tokens/
│   │
│   ├── observability/                   OBS-<SYS>-NNN.md                                     [Normative]
│   │
│   ├── lifecycle/                       ← normative-lifecycle: điều phối + work item; Git là nguồn, Jira là bản ghi   [Normative]
│   │   ├── change-sets/
│   │   │   └── CHG-<SYS>-YYYY-NNN/
│   │   │       ├── change-set.yaml                                                            [Normative]
│   │   │       ├── impact.yaml                                                                [Derived — sinh từ graph, cấm sửa tay]
│   │   │       ├── baseline/BL-r<n>.yaml                                                      [Normative — tập revision đã duyệt]
│   │   │       └── open-questions/      OQ-<SYS>-NNN.md                                       [Normative]
│   │   ├── epics/                       EPIC-NNN-<TEAM>.md                                    [Normative]
│   │   ├── stories/                     STORY-<SYS>-NNN.md                                    [Normative]
│   │   ├── tasks/                       TASK-<SYS>-NNN.md                                     [Normative]
│   │   ├── bugs/                        BUG-<SYS>-NNN.md                                      [Normative]
│   │   └── releases/                    REL-PLAN-NNN.yaml                                     [Normative]
│   │
│   ├── evidence/                        ← TOÀN BỘ nhóm Evidence · append-only · shard theo clone   [Evidence]
│   │   ├── requests/                    CR-<SYS>-NNN.yaml     yêu cầu gốc, nguyên văn
│   │   ├── context/                     CTX-<task-key>.yaml   snapshot agent đã thấy
│   │   ├── plans/                       PLAN-<task-key>.md    agent định làm gì
│   │   ├── diaries/                     DIARY-<task-key>.md   agent đã làm gì
│   │   ├── reviews/                     REVIEW-NNN.yaml · RCPT-NNN.yaml
│   │   ├── findings/                    FIND-<SYS>-NNN.yaml
│   │   ├── approvals/                   approval-NNN.yaml
│   │   ├── tests/
│   │   ├── deployments/
│   │   └── production/
│   │
│   ├── policies/                                                                              [Normative]
│   │   ├── rules/                       VAL-<GRP>-NNN.yaml + fixtures/
│   │   ├── gates/                       GATE-<NAME>.yaml
│   │   └── eval/                        EVAL-<AGENT>-NNN.yaml
│   │
│   ├── registry/                                                                              [Normative]
│   │   ├── REG-TYPE-001.md              Type Registry
│   │   ├── REG-OWNER-001.md             Ownership Registry
│   │   └── REG-REPO-001.md              Reference repo registry
│   │
│   └── generated/                       ← KHÔNG BAO GIỜ SỬA TAY                               [Derived]
│       ├── traceability/                TRC-<stage>-<key>.json
│       ├── change-set-views/            CSV-<CHG-key>.md
│       ├── architecture-views/          AVW-<key>.md — bản gộp CMP/API/TBL/EVT gửi review
│       └── diagrams/
│
├── AGENTS.md                            root                                              [Operational]
├── src/          (mỗi module có AGENTS.md riêng nếu khác root)
└── tests/
```

> **`TBL`/`API`/`EVT` đều là `.md`, không phải `.sql`/`.yaml`.** Spec chuẩn tắc phải mang frontmatter (§A.4) và bị `hash-artifact`/`check-sdlc` quét — chỉ file `.md` làm được cả hai; DDL (cho `TBL`) hoặc OpenAPI/schema sự kiện (cho `API`/`EVT`) nằm trong một khối mã bên trong file spec đó, không phải file rời. Migration **chạy được**, sinh ra từ khối DDL đó bằng script trích xuất, **không phải artifact chuẩn tắc** — nó là sản phẩm của task implement, sống ở `**/migrations/` (đã liệt `irreversible` — PROC §2.5.1), không mang frontmatter và không bị check-sdlc quét. Một `.yaml` changelog riêng (ví dụ breaking-change diff ở §B.10) không phải spec chuẩn tắc, không cần frontmatter, nên giữ `.yaml` được.

> **`tech-specs/` chia theo component, không theo loại contract.** Một component thường sinh ra cả API + schema + event cùng lúc — gộp theo component để agent load context một task bằng một `glob`. "Liệt mọi API của hệ thống" là việc của graph/`traceability.json` (NT-11 — *"identity thì graph là canonical"*), không phải đi bộ thư mục. Component không sở hữu API/TBL/EVT nào (ví dụ frontend thuần tiêu thụ qua gateway) **không có** thư mục con — đừng tạo `api/` rỗng cho đủ.

## A.2 Bảy luật thư mục

**1. Thiết kế và yêu cầu KHÔNG bao giờ nằm dưới `lifecycle/`.**
Change Set chứa: `change-set.yaml`, `impact.yaml`, `baseline/`, `open-questions/`. Hết. Thiết kế nằm ở `architecture/`, `tech-specs/`, `requirements/` — bump revision, không tạo file mới trong thư mục epic. *(PROC §1.2.2)*

CI reject file trong `lifecycle/` mang `type` thuộc nhóm design hoặc requirement.

**2. `product/` là scope tier, `lifecycle/` là lifecycle object.** Đây là §1.2.2 hiện lên trong filesystem. Proposal và PRD sống lâu; Change Set và work item chết khi xong việc.

Nhưng **cây chia theo nhóm artifact, không chia theo tuổi thọ** — `lifecycle/` chứa toàn bộ nhóm **normative-lifecycle**: đơn vị điều phối (Change Set), work item (Epic/Story/Task/Bug), và **Release Plan** — cả năm đều `group: normative` + `scope: lifecycle` trong registry (§1.3.1), nên `releases/` là sibling **trong** `lifecycle/`, không phải top-level riêng (PROC §1.2.2 dòng "Ranh giới: cái gì thuộc đâu" đã xếp Release Plan chung rổ với baseline/impact report/OQ — cùng bên Change Set). Loại khác mang tầng Lifecycle nhưng **khác nhóm** thì nằm chỗ khác: `CSV` → `generated/` (derived), `MR` → chính repo (derived), `PLAN` → `evidence/plans/` (evidence). Vòng đời ngắn không phải tiêu chí xếp thư mục — **nhóm** mới là tiêu chí.

**3. Story KHÔNG chứa hành vi.** Không có `given`/`when`/`then` trong file Story — hành vi thuộc AC, Story chỉ `satisfies` tới nó. *(PROC §1.2.4)* `enforced_by: deterministic-check` — VAL-WORK-001.

**4. `generated/` không bao giờ sửa tay.** Sửa nguồn rồi sinh lại. *(PROC §1.2.1)*

**5. Một artifact một file.** AC nằm trong file FR của nó. GOAL/KPI nằm trong PRD.

**6. `evidence/` chứa TOÀN BỘ nhóm Evidence, và append-only.** Review, receipt, finding, approval, context snapshot, **implementation plan**, nhật ký, test, deployment — tất cả. Sai thì thêm bản đính chính, không sửa file cũ. Ghi theo shard `<host>-<clone>` để nhiều worktree không conflict. *(PROC §4.4.3)*

Ba thư mục con là **bộ ba của một lượt agent chạy**, cùng `<task-key>`: `context/` — agent **thấy gì** · `plans/` — agent **định làm gì** · `diaries/` — agent **đã làm gì**. Append-only là cái làm cho plan có nghĩa: kế hoạch sửa được sau khi làm xong thì không chứng minh được điều gì. Replan là revision mới, và số lần replan tự nó là tín hiệu.

Đừng nhầm với `lifecycle/releases/`: đó là **Release Plan** (normative — sửa được qua review, đem ra Production Gate), khác hẳn Implementation Plan dù tên gần giống. Approval của release thì nằm ở `evidence/approvals/`, không nằm cạnh Release Plan.

**7. `generated/` không gitignore cả cục.** Tách theo hai loại: nội dung **được ký hoặc được trích dẫn ở nơi khác** (CSV đem ra gate, `AVW` gửi review, diagram được link từ tài liệu khác) — **không bao giờ** gitignore, vì đó là bằng chứng: "gắn commit SHA của thứ được duyệt" (PROC §2.2.1) vô nghĩa nếu bản đó không tồn tại ở đúng commit. Nội dung **sinh lại mỗi lần CI chạy, không ai ký lên nó** (`traceability/`, coverage report) — được gitignore theo dự án. `hand_written: true` (§D.1b) là dấu hiệu chắc chắn nhất cho loại phải commit: nếu người phải viết tay thì gitignore nghĩa là xoá công sức viết tay ngay khi có ai `clone` sạch.

## A.3 Đặt tên và ID

```
key    = <PREFIX>-<SYSTEM>-<NNN>        FR-PAY-041, CMP-PAY-INSTALLMENT
uid    = ULID, tooling sinh, không gõ tay
file   = <key>.md  (hoặc .yaml/.json theo loại)
```

Prefix hợp lệ: xem `registry/REG-TYPE-001.md`. Thêm prefix mới = thêm một dòng vào registry qua PR. *(PROC §1.3.1)*

## A.4 Frontmatter tối thiểu

Dán vào mọi artifact chuẩn tắc:

```yaml
---
uid:      # ULID — để trống, chạy script cấp trước khi commit
key: FR-PAY-041
type: functional-requirement
group: normative
scope: system                    # normative BẮT BUỘC ∈ {org, domain, system}
system: SYS-PAYMENT
status: draft                    # draft → in-review → approved → deprecated
revision: 1

ownership:
  accountable_team: TEAM-PAYMENT
  accountable_role: product-owner

relations:
  satisfies: [GOAL-PAY-004]
  constrained_by: [NFR-PERF-001]

verified_at: 2026-09-09
verified_against:
  - { key: GOAL-PAY-004, revision: 3, hash: abc123 }

classification: internal
ai_assisted: true
---
```

Evidence thì thêm `captured_against` thay cho `verified_against`:

```yaml
captured_against:
  artifacts: [{ key: CMP-PAY-AUTH, revision: 18, hash: a1b2 }]
  code_tree: 7f3c9d1
  graph_revision: 893214
```

---

# B. 23 bước triển khai

## B.0 Bảng tổng

| # | Bước | Ai làm | Input | Output | Thư mục | Gate | CLI/Skill `aide` |
|---|---|---|---|---|---|---|---|
| 0 | Proposal *(tuỳ chọn)* | Product | Yêu cầu mở hướng đi mới | Proposal | `product/proposals/` | — | CLI — `aide generate proposal` |
| 1 | PRD gốc *(chỉ New System)* | Product | Proposal nếu có, hoặc yêu cầu trực tiếp | `PRD-<SYS>.md` gốc — GOAL/KPI/Scope | `product/prd/` | *(duyệt cùng Scope Gate ở bước 4)* | CLI — `aide generate prd` |
| 2 | Intake & Triage | Product + Tech Lead | Yêu cầu | CR *(evidence)* · Impact report, tier, flow | `evidence/requests/`, `lifecycle/change-sets/<CHG>/impact.yaml` | — | Cả hai — `aide tier suggest` (CLI) + `/aide-intake` (skill, viết impact report) |
| 3 | Change Set Shell | Tự sinh | Impact | Change Set khung | `lifecycle/change-sets/<CHG>/change-set.yaml` | — | CLI — `aide changeset init` |
| 4 | FR & AC | **Product** | Impact, PRD hiện có | FR mới + AC · PRD *bump nếu GOAL/KPI/Scope đổi* | `requirements/fr/` (+ `product/prd/` nếu bump) | **Scope Gate** | Cả hai — `aide generate fr` (CLI) + `/aide-spec-draft`, `/aide-spec-review` (skill) |
| 5 | Domain design | Domain Owner | FR, AC | Glossary bổ sung, invariant | `domain/` | — | CLI — `aide generate domain` |
| 6 | L1 — capability | Architect | FR, AC | Cạnh `covers`, CAP mới nếu có | `architecture/l1/` | *(bounded context mới → Arch Gate)* | CLI — `aide generate l1` |
| 7 | L2 + ADR | **Architect** | L1, FR, AC, NFR | CMP mới hoặc revision, ADR, threat model | `architecture/l2/`, `adr/` | **Architecture Gate** | Cả hai — `aide generate l2/adr` (CLI) + `/aide-design-propose`, `/aide-design-review` (skill — panel 3 vai là GĐ6, Phase 1 chỉ 1 reviewer) |
| 8 | UX / UI — cấp 1–3 + mock | Design + Tech Lead | FR, AC | UX flow, screen inventory, UI design, **UI mock** | `design/ux/`, `design/ui/`, `generated/ui-mocks/` | **UI/UX Gate** | Cả hai — `aide generate ux/ui` (CLI) + mock dựng bằng Artifact/code thật (không phải skill riêng của `aide`) |
| 9 | L3 — contracts | **Tech Lead** | L2, AC | API / TBL / EVT | `tech-specs/` | **Contract Gate** *nếu breaking* | Cả hai — `aide generate api/tbl/evt`, `aide verify --contract` (CLI) + `/aide-contract-draft`, `/aide-code-review` (skill) |
| 10 | UI Specification — cấp 4 | Design + Tech Lead | **L3** · AC · **cấp 1–3 đã duyệt** | UI spec máy đọc được | `design/ui/` | *(input của Contract Gate)* | CLI — `aide generate ui-spec` |
| 11 | Epic / Story / Task decomposition | Tech Lead | AC, L2, L3 | Epic, Story, Task | `lifecycle/` | — | Cả hai — `aide generate epic/story/task` (CLI) + `/aide-task-decompose` (skill) |
| 12 | Context package | Platform *(tự động)* | Task, graph, baseline | Context package | `evidence/context/` | — | CLI — `aide context compile` |
| 13 | Implementation plan | Agent → Dev | Context package | Plan có bước + cách kiểm từng bước | `evidence/plans/` | — | Cả hai — `aide generate plan` (CLI) + `/aide-plan-draft` (skill) |
| 14 | Implementation | **Developer** + agent | Context package, plan | MR, nhật ký quyết định | repo; `evidence/diaries/` | — | Skill — Implementer là Claude Code (không phải skill riêng của `aide`, chỉ giới hạn quyền); `/aide-diary-log` ghi nền + `aide diary log` (CLI, phần khung) |
| 15 | Automated validation | CI | MR | Test result, coverage, `traceability.json` | `evidence/tests/`, `generated/traceability/` | — | CLI — `aide verify` trong CI |
| 16 | Review | Agent + **Tech Lead** | MR, evidence | Review pass, receipt, finding | `evidence/reviews/`, `evidence/findings/` | **Component Merge Gate** | Cả hai — `/aide-code-review` (skill) + `aide finding reconcile`, `aide gate approve GATE-MERGE` (CLI) |
| 17 | Fix / re-review | Developer | Finding | MR mới, review pass mới | như trên | — | Cả hai — lặp lại bước 16 |
| 18 | UAT | **Business Owner** | MR đã merge (build trên staging) · AC baseline | UAT approval record | `evidence/approvals/` | **UAT Gate** *T1/T2 nếu Change Set đổi FR/AC* | CLI — `aide csv render`, `aide gate approve GATE-UAT --approver` (chặn nếu approver = accountable_role của FR) |
| 19 | Release prep | SRE | Change Set đã ready | Release plan | `lifecycle/releases/` | **Change Integration Gate** *nếu nhiều team* | — *(ngoài phạm vi `aide` hiện tại)* |
| 20 | Release approval | **SRE** | Release plan, evidence | Approval record | `evidence/approvals/` | **Production Gate** | CLI — `aide gate approve GATE-PRODUCTION` |
| 21 | Deploy & verify | SRE | Approval | Deployment record, production verification | `evidence/deployments/`, `production/` | — | — *(ngoài phạm vi `aide` hiện tại — hạ tầng CI/CD)* |
| 22 | Close / learn | Product + Governance | Nhật ký, finding, KPI | Rule/ADR/AGENTS.md cập nhật | `policies/`, `AGENTS.md` | *(knowledge promotion)* | CLI — `aide diary surface` (nghi thức verbatim §2.5.5); quyết định vẫn là người |

**Cột `CLI/Skill aide` mô tả một tool tham chiếu cụ thể (`aide`), không phải một phần bắt buộc của PROC/EXEC** — tổ chức dùng tool khác thì bỏ qua cột này, các cột còn lại không đổi. CLI = deterministic (`aide <verb>`, chạy shell/CI); Skill = agent LLM (`/aide-<tên>`, chạy trong Claude Code). Nhiều mục còn ở mức thiết kế, chưa implement — xem roadmap ở PRD-AIDE §VIII.

**In đậm = người chịu trách nhiệm cuối cho bước đó.** Bước không in đậm thì agent làm chính, người advisory.

**Bước 0 và 1 không chạy cho từng thay đổi** — chỉ khi mở một hướng đi mới (bước 0, §B.1) hoặc dựng System mới (bước 1, §B.2). Đa số thay đổi bắt đầu thẳng từ bước 2, `derived_from`/PRD đã có để rỗng hoặc giữ nguyên.

**Bước bỏ được theo tier:** T3 bỏ 5, 6, 7, 8, 18, 19 · T2 bỏ 5, có thể gộp 6 vào 7, bỏ 18 nếu Change Set không đổi FR/AC · T1 chạy hết. *(PROC §2.1.3)*

**Bước 8 và 10 tách nhau vì phụ thuộc khác nhau.** Cấp 1–3 chỉ cần FR/AC nên chạy sớm và **qua UI/UX Gate trước bước 9**. Cấp 4 tham chiếu field/endpoint của contract nên chỉ chốt được **sau** bước 9. Gộp hai thứ lại là lý do bản trước không có gate UI: nửa cần L3, nửa không.

**Số thứ tự không phải trình tự bắt buộc — cột Input mới là dependency thật.** Bước 5 (Domain), 6 (L1), và 8 cấp 1–3 (UX Flow, Screen Inventory, UI Design — §E.1) đều chỉ cần `FR, AC`: ba PIC khác nhau (Domain Owner · Architect · Design + Tech Lead) chạy **song song** ngay sau Scope Gate, không ai chờ ai. Bước 7 (L2) mới thật sự chờ bước 6 vì Input có `L1`; bước 9 (L3) chờ bước 7 vì Input có `L2`. Riêng **UI Specification** (bước **10** — field/endpoint máy đọc được, ví dụ §E.2 tham chiếu `API-PAY-v3#terms`) cần thêm L3 nên chỉ chốt được **sau** bước 9, trước khi Contract Gate đóng (§E.4) — ba cấp đầu không chờ L3, cấp cuối thì có.

## B.1 Bước 0 — Proposal *(tuỳ chọn)*

**Không chạy cho từng thay đổi.** Chỉ chạy khi mở một hướng đi mới: sản phẩm mới, thị trường mới, một nỗ lực nhiều quý.

| | |
|---|---|
| **Ai** | Product |
| **Trả lời** | Có nên làm không — vấn đề, thị trường, wedge, business case, ranh giới roadmap |
| **Output** | `product/proposals/PROP-2026Q4-003.md` |
| **Scope** | `org` hoặc `domain` — **không** `system`, vì lúc này có thể chưa biết chạm hệ thống nào |
| **Vòng đời** | **Không chết.** Các Change Set của nó đóng hết thì Proposal vẫn là bản ghi *vì sao đã quyết* |
| **Gate** | Duyệt danh mục theo chu kỳ (quý), không phải gate của quy trình này |

### Gom nhiều Change Set là một truy vấn, không phải một object

Một nỗ lực lớn gồm nhiều thay đổi thì mỗi thay đổi là **một Change Set riêng**, và cả cụm gom lại bằng `derived_from`:

```yaml
# lifecycle/change-sets/CHG-PAY-2026-084/change-set.yaml
derived_from: [PROP-2026Q4-003]
```

```yaml
# lifecycle/change-sets/CHG-CHK-2026-091/change-set.yaml
derived_from: [PROP-2026Q4-003]
```

Muốn xem toàn cụm: truy vấn "mọi Change Set `derived_from` PROP-2026Q4-003". **Không có object "Initiative" phải tạo và bảo trì.**

Lý do mỗi thay đổi là một Change Set riêng chứ không gộp làm một: **baseline phải là tập revision duyệt cùng nhau và release cùng nhau.** Một nỗ lực 6 tháng có 5 lần release thì không thể có một baseline.

### Khi nào bỏ qua

Đa số công việc. Một thay đổi đơn lẻ đi thẳng vào bước 2, `derived_from` để rỗng.

**GOAL và KPI không sống ở Proposal.** Chúng vào `PRD-<SYS>.md` của hệ thống bị chạm, ở bước 4, vì đó là thứ sống cùng hệ thống chứ không chết cùng nỗ lực.

## B.2 Bước 1 — PRD gốc *(chỉ flow New System)*

**Chạy đúng một lần cho mỗi System, trước bước 4.** Bước 4 (FR & AC) giả định `PRD-<SYS>.md` đã tồn tại (Input: "Impact, PRD hiện có") — đúng cho flow Change, nhưng **sai cho New System**: lúc này chưa hề có PRD nào. Bước này lấp khoảng trống đó. Không chạy lại cho các thay đổi sau — từ Change Set thứ hai trở đi, hệ thống đã có PRD, quay lại flow Change bình thường (bước 4 chỉ *bump*).

| | |
|---|---|
| **Ai** | Product |
| **Input** | Proposal nếu có (§B.1), hoặc yêu cầu trực tiếp |
| **Trả lời** | Mục tiêu nghiệp vụ và ranh giới ban đầu của System này |
| **Output** | `product/prd/PRD-<SYS>.md` — GOAL · KPI · Scope · Persona · Assumption · Constraint (PROC §1.2.3) |
| **Scope** | `system` — khác Proposal (org/domain); từ đây `<SYS>` chính thức tồn tại trong `key` |
| **Gate** | Không riêng — bản GOAL/KPI đầu tiên này được duyệt cùng lúc với FR/AC đầu tiên ở **Scope Gate** (bước 4), không tách gate thứ hai |

**Sau bước này, `KHÔNG tạo PRD mới` (§B.5) mới có hiệu lực.** Quy tắc "PRD chỉ bump" ở bước 4 giả định trước đúng một PRD gốc — bước này là cái tạo ra tiền đề đó.

---

## B.3 Bước 2 — Intake & Triage

**Chạy:** `aide impact <mô tả yêu cầu>`

**Trước khi tính impact, ghi lại nguyên văn yêu cầu** — `evidence/requests/CR-PAY-2026-084.yaml` (§PROC 2.5.1). Không diễn giải, không tóm tắt — agent chạy `aide impact` nhận mô tả yêu cầu và tự tạo CR trước, rồi mới phân tích impact dựa trên CR đó.

**Agent làm:** đối chiếu graph, tính flow · tier · blast radius, liệt kê artifact bị chạm và bị stale.

**Người quyết:** tier ở ca ranh giới. Hạ tier phải ghi lý do + người duyệt.

**Output** — `lifecycle/change-sets/<CHG>/impact.yaml`:

```yaml
change_request: CR-PAY-2026-084   # bắt buộc — CI reject nếu CR không tồn tại
touches: [FR-PAY-012]
stale_artifacts: [CMP-PAY-AUTH, API-PAY]
affected_teams: [TEAM-PAYMENT]
external_consumers: []
risk_signals: { pii: true, financial: true }
path_signals: ["services/payment/**"]
tier: T1
flow: change
skipped_with_reason:                        # BẮT BUỘC
  - { area: SVC-reporting, reason: "chỉ đọc EVT cũ, schema không đổi" }
confidence: { graph_coverage: 0.62 }
```

**Xong khi:** có `tier`, `flow`, `confidence`, và `skipped_with_reason` không rỗng.

## B.4 Bước 3 — Change Set Shell

**Chưa có Epic ở bước này** — Epic thật, mang `implements: [FR-...]`, chỉ sinh ở **bước 11** (§B.12), sau khi FR đã tồn tại (bước 4) và sau L2 (bước 7). Bước 3 chỉ tạo khung điều phối của Change Set.

**Một team:** Change Set tự sinh, vô hình. Về sau ở bước 11 bạn sẽ chỉ thấy **một Epic**, và bốn field cam kết liên team của nó để rỗng.

**Nhiều team:** Change Set hiện ra, mỗi team sẽ có một Epic ở bước 11, `blocked_by` bắc qua giữa các Epic.

**Output** — `lifecycle/change-sets/<CHG>/change-set.yaml`:

```yaml
key: CHG-PAY-2026-084
label: "Phase 2 — Trả góp"          # tên người gọi nó; để rỗng nếu là bugfix lẻ
status: draft
objective: { satisfies: [] }        # điền dần ở bước 4
affected_systems: [SYS-PAYMENT]
affected_teams: [TEAM-PAYMENT]
coordination: { mode: compatible-rollout, integration_gate_required: false }
tier: T1
flow: change
```

## B.5 Bước 4 — FR & AC  ⟶ **Scope Gate**

**KHÔNG tạo PRD mới.** Hệ thống đã có `PRD-<SYS>.md` — trừ **New System**, nơi bước này chạy ngay sau §B.2 (PRD gốc mới viết xong).

**Bạn tạo:** `requirements/fr/FR-PAY-041.md`, mỗi FR một file, AC nằm trong.

**Bạn bump `PRD-<SYS>.md`** chỉ khi GOAL / KPI / Scope đổi.

**Mẫu FR** *(dùng luôn, thay `[...]`)*:

```yaml
---
uid:
key: FR-PAY-041
type: functional-requirement
group: normative
scope: system
system: SYS-PAYMENT
status: draft
revision: 1
ownership: { accountable_team: TEAM-PAYMENT, accountable_role: product-owner }
relations:
  satisfies: [GOAL-PAY-004]
  measured_by: [OBS-PAY-011]
---

# FR-PAY-041 — [Tiêu đề]

## Mô tả
[Hành vi nghiệp vụ người dùng thấy. Không mô tả cách làm.]

## Acceptance Criteria

### AC-PAY-041-01
- **given** [tiền đề]
- **when** [hành động]
- **then** [kết quả quan sát được]
- `constrained_by:` [NFR-PERF-001]
- `implementation_target:` [CMP-…, API-…]
- `validated_by:` [TEST-…]
```

**Bốn luật khi viết AC:**
- Số liệu ngưỡng → `constrained_by` tới NFR, **không gõ lại con số**
- Telemetry → `measured_by` tới OBS, **không khai trong FR**
- Entity → tra `domain/glossary`, không định nghĩa lại
- Mơ hồ → tạo OQ ở `lifecycle/change-sets/<CHG>/open-questions/`, **không đoán**

**Scope Gate — Product duyệt.** Sau gate, **chỉ Product** đổi được AC, qua change request.

## B.6 Bước 5 — Domain design *(bỏ được ở T2/T3)*

Chạy khi FR đưa vào khái niệm nghiệp vụ mới hoặc invariant mới.

**Output:** bổ sung `domain/<domain>/glossary.md` + danh sách invariant. **Không** vẽ lại class diagram nếu code đã có.

## B.7 Bước 6 — L1 capability

**Bạn làm:** map mỗi FR mới sang ít nhất một CAP bằng cạnh `covers`.

```yaml
# architecture/l1/CAP-PAY-009.md
relations:
  covers: [FR-PAY-041, FR-PAY-042]
```

Tạo `CAP` mới **chỉ khi** là năng lực nghiệp vụ mới. FR nằm gọn trong CAP sẵn có → chỉ thêm cạnh.

**Bounded context mới** → chuyển sang flow Architecture change, Architecture Gate cần Enterprise Architecture. *(PROC §3.3)*

**Xong khi:** luật coverage #2 xanh — mọi FR có ≥1 CAP `covers`.

## B.8 Bước 7 — L2 + ADR  ⟶ **Architecture Gate**

**Agent đề xuất 2–3 phương án kèm tradeoff.** Ghi cả phương án bị loại và lý do loại.

**Thứ tự bắt buộc:**
1. Viết vấn đề và ràng buộc **trước khi** ai nêu phương án
2. Viết tiêu chí quyết định **trước khi** xem phương án
3. Rồi mới xem phương án

**Bạn tạo hoặc bump:**
- `architecture/l2/CMP-PAY-INSTALLMENT.md` — component mới
- `architecture/l2/CMP-PAY-AUTH.md` — bump `revision: 17 → 18`
- `architecture/adr/ADR-2026-019.md` — nếu có quyết định kiến trúc
- `architecture/threat-model/TM-SYS-PAYMENT.md` — bump nếu chạm bảo mật

### Bảy mục bắt buộc trong một file CMP

Thiếu ba mục cuối là agent phải tự quyết, và quyết đúng hay sai là may rủi:

| Mục | Trả lời |
|---|---|
| Trách nhiệm | Component này gánh phần nào của CAP |
| Cấu trúc bên trong | Chia thế nào, vì sao chia thế |
| Sequence | Luồng chính, dạng diagram-as-code |
| Failure mode | Hỏng ở đâu, hỏng thì sao |
| **Transaction boundary** | Đơn vị nguyên tử tới đâu — commit ở chỗ nào, cái gì nằm ngoài |
| **Idempotency** | Gọi lại hai lần thì sao — khoá idempotency là gì, giữ bao lâu |
| **Concurrency** | Hai request cùng lúc thì sao — optimistic hay pessimistic, khoá ở mức nào |

Ví dụ ba mục cuối cho `CMP-PAY-INSTALLMENT`:

```markdown
## Transaction boundary
Tạo lịch + ghi ledger trong một transaction. Gửi EVT-INSTALLMENT-CREATED
nằm NGOÀI transaction, qua outbox — không để publish fail làm rollback lịch.

## Idempotency
Khoá: `(order_id, term_months)`. Giữ 24h. Gọi lại trong window trả về lịch cũ
kèm 200, không tạo mới, không lỗi.

## Concurrency
Optimistic lock trên `order.version`. Hai request cùng order thì request thứ hai
nhận 409 và client retry — KHÔNG merge, vì hai lịch trả góp cho một đơn là sai nghiệp vụ.
```

**Review:** panel 3 reviewer blind theo vai (security / operability / completeness), class `advisory` — finding tới người, không có vòng sửa tự động. *(PROC §2.3.3)*

**Architecture Gate — Architect chọn phương án.** Authority theo phạm vi rủi ro: T2 trong một component → Tech Lead · cross-component cùng domain → Domain Architect · bounded context mới → + Enterprise Architecture.

**Hệ thống nhiều component — đem gì ra gate.** Không viết một tài liệu SAD gộp toàn hệ thống rồi coi đó là "L2" (vi phạm §1.3.8 — một CMP một component, mọi Change Set sau sẽ chạm cùng file đó). Đem ra gate là **`AVW`** (architecture-view, PROC §1.2.2) — sinh từ các CMP/ADR/threat-model liên quan, `non_normative: true`, ở `generated/architecture-views/`. Nội dung nào trong bản gộp cũ không suy ra được từ CMP/ADR nào cả (rationale gốc, chưa có nơi ở) thì đó là tín hiệu thiếu một CMP hoặc ADR, không phải lý do giữ nó trong view.

## B.9 Bước 8 — UX / UI cấp 1–3 + mock  ⟶ **UI/UX Gate**

Xem **§E**. Bỏ được khi thay đổi không chạm giao diện.

**Chạy song song với bước 5–7, không chờ L1/L2.** UX Flow, Screen Inventory, UI Design (§E.1 cấp 1–3) chỉ cần FR/AC — bắt đầu ngay sau Scope Gate (bước 4), cùng lúc Domain Owner làm bước 5 và Architect làm bước 6–7.

### Dựng mock để duyệt

Spec không trả lời được câu hỏi quan trọng nhất: **người dùng có dùng được không.** Nên trước khi sang L3, dựng một bản trực quan cho người duyệt bấm thử.

**Ba hình thức, chọn theo hoàn cảnh — không hình thức nào bị cấm:**

| Hình thức | Khi nào hợp | Đánh đổi |
|---|---|---|
| **Ảnh tĩnh · Figma** | Thăm dò sớm, luồng chưa chốt | Không dùng token thật → **duyệt cái này, ra cái khác** |
| **HTML/CSS/JS** | Chưa chốt framework, hoặc mock cần sống độc lập với repo | Phải viết lại khi implement |
| **Prototype trên chính stack** | Đã có design token và component | Tốn hơn ảnh, nhưng **không vứt đi** |

Cách chọn: **mock càng gần thứ sẽ chạy thật, giá trị của lần duyệt càng cao.** Ảnh tĩnh duyệt xong vẫn có thể ra một giao diện khác hẳn; prototype trên token thật thì cái được duyệt chính là cái sẽ ship.

Điều **bắt buộc với mọi hình thức**: mock phải dùng **design token thật**, không phải màu và khoảng cách gõ tay. Không có ràng buộc này thì gate duyệt một thứ không tồn tại.

### Mock bao nhiêu màn hình

**Không mock hết.** Mock **hệ thiết kế + các màn hình quyết định cảm nhận sản phẩm** — thường là màn hình người dùng chạm nhiều nhất, màn hình hậu quả cao nhất, và màn hình của người dùng ít khoan dung nhất.

Màn hình còn lại **kế thừa** hệ đã duyệt. Nếu một màn hình sau này cần mẫu chưa có trong hệ, đó là tín hiệu **mở rộng UI Design** — qua change request, không phải tự chế tại chỗ.

### Cái được duyệt không phải cái mock

Mock là `group: derived`, `non_normative: true`, khai `derived_from` tới UXF/SCR/UID và mang luật phân xử:

```yaml
> Khi mock và UXF/SCR/UID bất đồng, **UXF/SCR/UID thắng**.
```

**Thứ được ký ở gate là revision của UXF · SCR · UID.** Mock chỉ là phương tiện trình bày — đúng vai trò của Change Set view ở Scope Gate (§D.1b). Không có luật phân xử này thì mock thành nguồn sự thật thứ hai, và PROC §4.4.4 cấm đúng điều đó.

## B.10 Bước 9 — L3 contracts  ⟶ **Contract Gate** *(nếu breaking)*

**Sinh từ L2 + AC**, đặt ở `tech-specs/<CMP-slug>/` — đúng component đang expose contract đó (§A.1). Bắt buộc Git.

**Breaking hay không** do máy quyết (OpenAPI diff), không do người tự nhận.

**Nếu breaking:**

```yaml
# tech-specs/PAY-INSTALLMENT/api/API-PAY.changelog.yaml
from: v2
to: v3
compatibility: breaking
consumers:                     # DERIVED từ graph — không khai tay
  - { team: TEAM-MOBILE, ack: required, state: not-started }
coexistence: { v2: true, v3: true }
migration_window: { start: 2026-09-15, end: 2026-12-15 }
```

**Contract Gate:** Tech Lead + consumer teams ack. Consumer chính và partner ngoài luôn `ack: required`.

## B.11 Bước 10 — UI Specification — cấp 4

**Cấp 4** tham chiếu field/endpoint của contract nên phải chờ L3 đủ hình dạng, và phải xong **trước khi Contract Gate đóng** (§E.4).

Tách khỏi bước 8 vì phụ thuộc khác nhau: cấp 1–3 cần FR/AC, cấp 4 cần L3. Gộp hai thứ là lý do bản trước không có gate UI — nửa cần L3, nửa không, nên không đặt gate ở đâu được.

### Cấp 1–3 dùng để làm gì, nếu cấp 4 chỉ cần L3 + AC?

Câu hỏi này đúng, và nó lộ ra một lỗi nếu cấp 4 chỉ ghi Input là `L3, AC`: vậy thì cấp 1–3 là ba tài liệu không ai tiêu thụ — và một artifact không ai tiêu thụ là artifact nên xoá (`NT-10`).

Thực tế cấp 1–3 có **hai** người tiêu thụ, và cả hai đều bắt buộc:

| Ai tiêu thụ | Dùng làm gì |
|---|---|
| **UI/UX Gate** | Đây là thứ được **ký**. Gate không ký mock (`derived`), không ký UI Spec (chưa tồn tại) — nó ký revision của `UXF` · `SCR` · `UID` |
| **Cấp 4** | `UIS` **dẫn xuất từ** `SCR` + `UXF` và **bị chi phối bởi** `UID`. Không có chúng thì UI Spec không biết mình đang đặc tả màn hình nào, trong luồng nào, dùng component nào |

Quan hệ thứ hai là quan hệ thật, không phải lý thuyết — nó xuất hiện ngay trong metadata của `UIS`:

```yaml
relations:
  derived_from: [SCR-…-001, UXF-…-002]   # màn hình nào, trong luồng nào
  refines:      [UID-…-003]              # component nào, hành vi nào
  satisfies:    [AC-…-01, …]             # AC nào
```

`refines`, **không phải** `governed_by`. Vocabulary đóng (`PROC §1.3.3`) dành
`governed_by` cho *rule/policy*; `UID` là spec thiết kế, và cấp 4 **làm mịn** nó
ở tầng dưới — đúng định nghĩa của `refines`.

Nên Input đúng của bước 10 là **`L3` · `AC` · cấp 1–3 đã duyệt**, và bảng §B.0 đã ghi theo đó.

**Cách nhớ ranh giới:** cấp 1–3 trả lời *"người dùng thấy gì và đi đường nào"* — quyết được bằng FR/AC. Cấp 4 trả lời *"component nào bind vào field nào của endpoint nào"* — không quyết được trước khi endpoint tồn tại. Hai câu hỏi khác nhau, hai người duyệt khác nhau (`Product + Design` ở UI/UX Gate; `Tech Lead + consumer` ở Contract Gate), nên hai bước.

## B.12 Bước 11 — Epic / Story / Task decomposition

**Task sinh sau L2, không trước.** Trước khi có thiết kế thì task chỉ là phỏng đoán.

```
Change Set  ─→  Epic (một team)  ─→  Story  ─→  Task
                                       │           └─ satisfies ─→  AC
                                       └────────────────────→  Task   (không qua Story — không có AC)
```

**`Task` có hai cha loại trừ nhau: `story:` hoặc `epic:`.** Có AC để tách nhỏ (feature, đổi hành vi quan sát được) → qua `Story`, dùng `story:` — tương đương Jira **Sub-task**. Không có AC nào cả (tech debt, refactor, tích hợp hạ tầng, đổi công cụ nội bộ — không đổi hành vi người dùng thấy) → đi thẳng `epic:`, không tạo Story rỗng chỉ để có nơi treo — tương đương Jira **Task** ngang hàng Story dưới cùng Epic. Cùng `type: task`, không phải hai loại khác nhau.

**Git là nguồn; Jira là bản ghi để PM quản lý, có thể có hoặc không.** Nếu có, nối bằng frontmatter — không đồng bộ hai chiều, không sửa nội dung ở Jira.

### Epic

```yaml
---
key: EPIC-084-PAYMENT
type: epic
group: normative
scope: lifecycle
change_set: CHG-PAY-2026-084
accountable_team: TEAM-PAYMENT
status: not-started
jira_epic: PAY-1204                    # tuỳ chọn

implements: [FR-PAY-041]
affected_components: [CMP-PAY-INSTALLMENT]

# Bốn field dưới: ca MỘT team thì để rỗng, đừng bịa cho đủ
contracts: { produces: [API-PAY-v3], consumes: [] }
blocked_by: []                         # [EPIC-084-IAM] khi chờ team khác
ready_criteria: [contract_frozen, context_valid, tests_green]
---

# EPIC-084-PAYMENT — Thanh toán trả góp (phần backend)

## Phạm vi
[Team này gánh phần nào của Change Set. 2–4 dòng.]

## Story
- STORY-PAY-211 — tạo lịch trả góp
- STORY-PAY-212 — hiển thị tổng phí

## Task (không qua Story — không có AC)
- TASK-PAY-560 — trả nợ kỹ thuật: tách connection pool riêng cho installment worker
```

### Story

```yaml
---
key: STORY-PAY-211
type: story
group: normative
scope: lifecycle
epic: EPIC-084-PAYMENT
status: not-started
jira_story: PAY-1211                   # tuỳ chọn

satisfies: [AC-PAY-041-01]             # BẮT BUỘC khác rỗng
---

# STORY-PAY-211 — Tạo lịch trả góp

## Giao cái gì
[Lát cắt này giao được gì. KHÔNG viết given/when/then — hành vi ở AC-PAY-041-01.]

## Ngoài phạm vi
[Thứ dễ bị hiểu là thuộc story này nhưng không phải.]

## Task
- TASK-PAY-551 — migration TBL-installment-plan
- TASK-PAY-552 — endpoint POST /installment-plans
- TASK-PAY-553 — validation kỳ hạn
```

> **Không viết `given`/`when`/`then` trong Story.** CI reject. Hành vi thuộc AC; Story chỉ trỏ tới. Đây là chỗ NT-01 bị vi phạm thường xuyên nhất.

### Task

**Cha là `story:` hoặc `epic:` — không phải cả hai, không thể để trống cả hai.**

```yaml
---
key: TASK-PAY-551
type: task
group: normative
scope: lifecycle
story: STORY-PAY-211                   # có AC để tách nhỏ → story: (≈ Jira Sub-task)
status: not-started
jira_task: PAY-1551                    # tuỳ chọn
implements: [CMP-PAY-INSTALLMENT]
---

# TASK-PAY-551 — Migration TBL-installment-plan

## Làm gì
[Một đơn vị thực thi. Đủ nhỏ để một context package phủ hết.]

## Xong khi
[Kiểm được bằng máy.]
```

Việc không có AC (tech debt, refactor, tích hợp, đổi công cụ nội bộ) thì bỏ `story:`, khai `epic:` thay vào — không tạo một Story rỗng chỉ để có nơi treo, và không bỏ luôn field cha (mất containment, Task trôi tự do):

```yaml
---
key: TASK-PAY-560
type: task
group: normative
scope: lifecycle
epic: EPIC-084-PAYMENT                 # không có AC → epic: trực tiếp (≈ Jira Task, ngang Story)
status: not-started
jira_task: PAY-1560                    # tuỳ chọn — phía Jira tạo Task, không phải Sub-task
implements: [CMP-PAY-INSTALLMENT]
---

# TASK-PAY-560 — Trả nợ kỹ thuật: tách connection pool riêng cho installment worker

## Làm gì
[Một đơn vị thực thi. Đủ nhỏ để một context package phủ hết.]

## Xong khi
[Kiểm được bằng máy.]
```

### Bug

```yaml
---
key: BUG-PAY-078
type: bug
group: normative
scope: lifecycle
status: triage
jira_bug: PAY-1678                     # tuỳ chọn

violates: [AC-PAY-041-02]              # AC bị vi phạm — rỗng nếu AC chưa tồn tại
severity: high
---

# BUG-PAY-078 — Thẻ không hỗ trợ trả góp vẫn tạo được lịch

## Quan sát được
[Hành vi thật, có bước tái hiện.]

## Kỳ vọng
[Theo AC nào. Nếu không có AC nào nói tới → xem phân nhánh dưới.]

## Phân nhánh (PROC §2.1.4)
- [ ] Code lệch AC → bug thật, sửa code + test tái hiện
- [ ] AC sai hoặc thiếu → **change request trá hình**, chuyển sang flow Change
```

**Ai chốt gì:** agent đề xuất decomposition; **người chốt** `accountable_team`, thứ tự, và `blocked_by`. Regenerate không được xoá thoả thuận đã chốt.

## B.13 Bước 12 — Context package

Xem **§C**.

## B.14 Bước 13 — Implementation plan

Agent viết plan trước khi sửa dòng đầu tiên, ghi vào `evidence/plans/` — **append-only**. Plan phải có, cho từng bước: **file nào đổi · đổi gì · kiểm bằng cách nào**.

Giá trị của plan nằm ở chỗ nó được viết **trước**, nên nó là một **cam kết kiểm chứng được**, không phải mô tả viết lại sau khi xong. Đổi hướng giữa chừng thì ghi revision mới, không sửa file cũ.

```markdown
# PLAN-TASK-PAY-103

## Thứ tự (TDD)
1. RED: test cho AC-PAY-041-01 → fail vì thiếu module `installment-calculator`
2. GREEN: implement calculator
3. RED: test kỳ hạn không hợp lệ → fail
4. GREEN: validation
5. Migration TBL-installment-plan
6. Wire API-PAY-v3 endpoint

## Không làm
- Không đụng CMP-PAY-LEDGER
- Không refactor code xung quanh
```

## B.15 Bước 14 — Implementation

**Bốn luật cứng:** *(PROC §2.2.3)*

1. Agent **không sửa spec**. Mâu thuẫn → tạo OQ và dừng.
2. Agent **không review output của chính mình**.
3. MR **bắt buộc khai quan hệ**:
   ```yaml
   implements: [FR-PAY-041]
   satisfies:  [AC-PAY-041-01, AC-PAY-041-02]
   ```
4. **MR là lát mỏng nhất tự đứng được** — compile được, test xanh, review được một mình.

**Nhật ký quyết định** — agent ghi trong lúc làm, người không sửa tay:

```markdown
# DIARY-TASK-PAY-103

## Diễn giải
- 2026-09-09T10:14Z — AC nói "kỳ hạn hợp lệ" không định nghĩa; hiểu là 3/6/9/12 tháng theo bảng phí hiện có.

## Đi chệch
## Đánh đổi
- 2026-09-09T11:02Z — Tính phí lúc tạo lịch thay vì lúc thanh toán, vì AC-041-01 đòi hiển thị tổng phí ngay.

## Câu hỏi mở
- Kỳ hạn 24 tháng có trong roadmap không? Ảnh hưởng schema.
```

**Isolation:** mỗi MR một worktree riêng, không sửa checkout chính.

## B.16 Bước 15 — Automated validation

CI chạy, theo thứ tự:

```
1. structural + referential + scope     (schema, relation, group/scope hợp lệ)
2. coverage → sinh generated/traceability/TRC-<key>.json
3. ownership + freshness
4. contract lint + breaking detection
5. test suite (kèm RED-first proof + baseline attribution)
```

**Ba trạng thái, không phải hai:** `passed` · `failed` · **`not_run`**. Gộp `not_run` vào `passed` là nói dối.

## B.17 Bước 16 — Review  ⟶ **Component Merge Gate**

**Class do loại artifact quyết, không do người chọn:**

| Đối tượng | Class | Cấu hình |
|---|---|---|
| Code, contract, schema, test | `adversarial` | 1 reviewer, trần 2 vòng, có vòng sửa |
| FR/AC, L1, L2, ADR | `advisory` | 1 pass, finding tới người, không vòng sửa |

**Reviewer KHÔNG được nhận:** nhật ký quyết định, plan, lý lẽ của tác giả. Chúng nằm trong `evidence/` để lưu vết, **không** vì thế mà vào review package — evidence là thứ được ghi lại, không phải thứ mặc định đem cho reviewer đọc.

**Review freeze:** từ lúc ghi receipt tới lúc approve, **cấm ghi vào artifact đã review**. Lỡ ghi → đúng một recovery review.

**Component Merge Gate:** deterministic pass · review pass · test xanh · context còn valid · MR khai đủ quan hệ.

## B.18 Bước 17 — Fix / re-review

- Sửa **chỉ** finding của gate đang fail. Không "tiện tay dọn".
- Fix đổi hành vi → chạy lại evidence.
- Reviewer vòng sau **giữ nguyên ID finding**, chỉ cập nhật status.
- Chạm trần 2 vòng → mở lựa chọn **"chấp nhận như hiện trạng"**, ghi evidence, đi tiếp.

## B.19 Bước 18 — UAT  ⟶ **UAT Gate**

**Chỉ chạy khi Change Set đổi FR hoặc AC, ở T1/T2.** T3 bỏ; T2 bỏ nếu Change Set không đổi hành vi quan sát được (refactor, migration nội bộ, perf fix). *(PROC §2.1.3, §2.2.1)*

**Giả định hạ tầng: staging luôn chạy build mới nhất đã merge.** Deploy lên staging **không phải một bước trong quy trình này** — coi CI/CD tới staging là hạ tầng có sẵn, giống cách bước 15 (Automated validation) không mô tả cách CI được cài. Nếu tổ chức bạn chưa có CD tự động tới staging, đó là việc cần làm trước, không phải việc UAT Gate tự làm.

**Ai làm:** Business Owner — vai trò **độc lập với Product**, người viết AC (PROC §1.4.2, §2.2.5 "Biz Process — nhãn tổ chức trong PRD"). Không cưỡng chế bằng máy được việc một người không tự ký nghiệm thu spec của chính mình (`enforced_by: unenforced`) — nhưng identity ở `human_presence` phải khác identity ở `accountable_role` của FR đang test, và review-log cho thấy sai lệch này thì đó là finding severity cao, không phải chuyện nhỏ.

**Dùng lại Change Set view (CSV, §D.1b) làm script đi test** — không viết "UAT script" riêng. Mục "Tính năng mới" và "Thay đổi hành vi hiện có" của CSV chính là danh sách AC cần đi qua trên staging; CSV đã suy ra từ baseline nên không lệch với AC thật.

**Approval record** (`evidence/approvals/`, `type: approval`) mở rộng đúng khuôn Production Gate (§B.20), thêm `verified_against`:

```yaml
baseline: BL-CHG-084-r3
environment: staging
build: 7f3c9d1                      # commit SHA đang chạy trên staging
verified_against:
  - { key: AC-PAY-041-01, result: pass }
  - { key: AC-PAY-041-02, result: pass }
  - { key: AC-PAY-042-01, result: fail, finding: FIND-PAY-902 }
human_presence: { evidence_id: HT-…, mode: interactive }
approved_by: <danh tính thật — KHÁC accountable_role của FR đang test>
```

**Fail thì route đúng vocabulary đã có ở §2.3.3, không phải một nhánh riêng:**

| Fail vì | Route | Đi đâu |
|---|---|---|
| Build sai so với AC đã duyệt | `patch` | Bug — quay lại bước 14 (Implementation), chạy lại 15–18 |
| AC đúng nhưng thiếu một ca thực tế Business Owner mới thấy | `intent_gap` | Open Question → Product — **không patch code để che gap trong spec** |

Không phân biệt hai đường này thì UAT Gate biến "requirement thiếu" thành "code có bug" — đúng lỗi §2.3.3 đã cảnh báo cho review, giờ lặp lại ở nghiệm thu.

## B.20 Bước 19–21 — Release

**19. Release prep** — `lifecycle/releases/REL-PLAN-NNN.yaml`, nhiều unit có thứ tự:

```yaml
units:
  - { key: REL-DB-114,  type: migration, order: 0, rollback: forward-only }
  - { key: REL-PAY-982, type: backend,   order: 1, rollback: reversible }
  - { key: REL-MOB-403, type: mobile,    order: 2, rollback: none }
partial_failure_policy: halt-and-hold
```

**20. Release approval ⟶ Production Gate** — SRE. Approval record phải có:

```yaml
baseline: BL-CHG-084-r3
covers: [{ key: CMP-PAY-INSTALLMENT, revision: 3, hash: a1b2 }]
human_presence: { evidence_id: HT-…, mode: interactive }
approved_by: <danh tính thật>
commit_sha: 7f3c9d1
accepted_risk:                    # TỰ ĐỘNG — mọi finding còn mở
  - { finding: FIND-PAY-813, severity: medium }
rejected_findings:                # phải khai tường minh
  - { finding: FIND-PAY-815, reason: "consumer đã deprecated từ Q1" }
```

**21. Deploy & verify** — mỗi unit một Deployment Record. Release là lúc revision thành **as-deployed**. Đo hành vi quan sát được ngoài đời có đúng FR/KPI không (không phải "code có đúng AC" — đó là bước 15) xem PROC §2.3.7 (Cấp 3 — Production).

## B.21 Bước 22 — Close / Learn

Trước khi đóng, chạy nghi thức tại gate:

1. Surface nhật ký **verbatim** — không tóm tắt, không lọc
2. Hỏi *"còn gì cho lần sau không?"*
3. Người tick cái muốn giữ, chọn heading — **heading quyết định đích đến**
4. **Câu hỏi mở không promote thành rule**
5. Nhật ký rỗng → ghi lặng lẽ, đi tiếp

Bài học đi vào: `policies/rules/` (rule mới) · `AGENTS.md` (module) · ADR · hoặc **một check deterministic mới**.

**Phạm vi mặc định hẹp nhất** (system). Lên domain/org là hành động tường minh riêng.

## B.22 Ba flow còn lại

§B.3–B.21 viết cho flow **Change** — 80% công việc. Ba flow kia khác ở đâu:

### New system

Giống Change, khác năm chỗ:

| Khác | Chi tiết |
|---|---|
| **Có thêm §B.2 trước bước 2** | Viết `PRD-<SYS>.md` lần đầu — GOAL/KPI/Scope gốc. Flow Change không có bước này vì PRD đã tồn tại |
| **Cổng người dày ở đầu, mỏng ở sau** | Bounded context và domain model là cửa đắt nhất; implement từng FR khi chưa có user thì rủi ro thấp |
| **Vertical slice mẫu do người viết** | Trước khi thả agent, trừ khi đã có golden example phù hợp. Agent học pattern từ slice này |
| **Kế thừa, không dựng lại** | ADR nền tảng, Glossary lõi, reference repo đã có — bước 5 và 6 gần như bằng 0 |
| **Có user thật → chuyển sang Change** | New system là trạng thái tạm thời |

Vẫn đi chiều dọc: một FR đi hết bước 4→16 rồi mới tới FR tiếp.

### Architecture change *(luôn T1)*

Kích hoạt khi: bounded context mới · lật ADR nền tảng · thay đổi cross-domain.

Chèn ba bước **trước** B.8 (L2), theo đúng thứ tự:

```
a. Viết vấn đề và ràng buộc      ← TRƯỚC khi ai nêu phương án
b. Viết tiêu chí quyết định       ← TRƯỚC khi xem phương án
c. Rồi mới xem 2–3 phương án
```

Khác Change:
- Tier **luôn T1**, không tính
- Architecture Gate authority: bounded context mới cần **Domain Architect + Enterprise Architecture**
- ADR mới `supersedes` ADR cũ nếu lật
- Mọi CMP `implements` / `governed_by` ADR cũ thành **stale** → xử lý theo strangler, chỉ nâng artifact bị chạm

### Hotfix

**Câu hỏi đầu tiên, trước khi sửa gì:**

| Hành vi hiện tại sai so với AC, hay AC vốn đã sai? | Làm gì |
|---|---|
| **Code lệch AC** | Bug thật. Sửa code, thêm test tái hiện, gắn `satisfies: [AC-xxx]`. **Không sửa tài liệu** |
| **AC sai hoặc thiếu** | Change request trá hình → **chuyển sang flow Change**, đừng hotfix |
| **Production đang cháy** | Sửa code trước → **backfill trong 48h** |

**Backfill gồm:** bump revision node bị chạm · AC bổ sung nếu hành vi mới là intended · evidence của lần hotfix.

CI gắn `undocumented_change` lên service **cho tới khi xong**. Đây là cơ chế cưỡng chế, không phải nhắc nhở.

# C. Context và code agent

## C.1 Compile context package

```
aide context compile --task TASK-PAY-103 --baseline BL-CHG-084-r3
```

Output `context/CTX-TASK-PAY-103.yaml`:

```yaml
key: CTX-TASK-PAY-103
compiled_at: 2026-09-09T09:00:00Z
graph_revision: 893214

objective: TASK-PAY-103
requirements: [FR-PAY-041, AC-PAY-041-01]
design:       [CMP-PAY-INSTALLMENT]
decisions:    [ADR-2026-019]
contracts:    [API-PAY-v3, TBL-installment-plan]
constraints:  [NFR-PERF-001, NFR-SEC-004]
applicable_rules: [VAL-SEC-003, VAL-GO-ERR-002]     # nạp theo trigger
rule_pack: RP-2026-09-a                              # pin theo Change Set
code_scope:   ["services/payment/installment/**", "tests/payment/installment/**"]
golden_examples: [REF-GO-SERVICE-003]
previous_findings: [FIND-PAY-813]

inputs:
  FR-PAY-041:   { revision: 7, hash: a1b2 }
  ADR-2026-019: { revision: 2, hash: c3d4 }

authority:
  baseline: BL-CHG-084-r3
  minimum_status: approved_in_baseline
  reject_if_stale: true
security: { effective_principal: <người khởi tạo>, max_classification: confidential }
```

**Revalidate trước merge.** Hash đổi → chạy lại impact → rebase hoặc escalate.

## C.2 Context theo loại thay đổi

Danh sách tối thiểu. Thiếu một dòng thì chưa đủ điều kiện code.

| Loại | Bắt buộc có |
|---|---|
| **Backend / API** | AC · **L2 của component — gồm transaction boundary, idempotency, concurrency** · API contract · NFR perf + sec · code service + test hiện có · rule API |
| **Database** | AC · **L2 — nhất là transaction boundary** · TBL schema · migration hiện có · NFR retention · rule DB · **chính sách rollback** |
| **Frontend / UI** | AC · UI spec + tokens · API contract phía consume · UX flow · component hiện có · rule accessibility |
| **Security** | AC · threat model · NFR bảo mật · classification của dữ liệu chạm tới · rule sec · finding bảo mật cũ |
| **Bug fix** | AC bị vi phạm · test tái hiện · code vùng lỗi · finding liên quan · **không nạp cả L2** |

## C.3 Prompt cho coding agent

Render từ context package, **không gõ tay**:

```text
Bạn đang thực hiện TASK-PAY-103.

MỤC TIÊU
Implement AC-PAY-041-01 (tạo lịch trả góp + hiển thị tổng phí).

NGUỒN CHUẨN TẮC — chỉ tin những thứ này
- FR-PAY-041 rev 7
- AC-PAY-041-01
- CMP-PAY-INSTALLMENT rev 3
- ADR-2026-019 rev 2
- API-PAY v3 (contract), TBL-installment-plan

RÀNG BUỘC
- NFR-PERF-001: P95 < 500ms
- NFR-SEC-004: không log số thẻ
- Rule: VAL-SEC-003, VAL-GO-ERR-002

CODE LIÊN QUAN
- services/payment/installment/**
- tests/payment/installment/**

PHẠM VI
- Chỉ TASK-PAY-103. Không đụng CMP-PAY-LEDGER. Không refactor xung quanh.

FINDING CŨ CÒN MỞ
- FIND-PAY-813: thiếu validation kỳ hạn ở nhánh retry

ĐẦU RA
- Code + test (RED trước, chứng minh fail đúng lý do)
- MR khai implements/satisfies
- Nhật ký quyết định 4 heading

TRƯỚC KHI BÁO XONG
- Chạy test bắt buộc, ghi evidence
- Đối chiếu từng AC
- Báo mọi chỗ lệch khỏi CMP-PAY-INSTALLMENT

DỪNG VÀ HỎI khi
- Spec mâu thuẫn hoặc thiếu → tạo OQ, KHÔNG đoán
- Phải sửa spec mới làm được → route bad_spec, KHÔNG patch xuống code
```

## C.4 Definition of Ready — đủ điều kiện code

Agent phải trả lời được **tất cả**, nếu không thì task chưa ready:

```
Đang xây cái gì? Vì sao?
AC nào?
Invariant nghiệp vụ nào?
Ràng buộc hệ thống nào (NFR)?
L2 nào mô tả cách làm — gồm transaction boundary, idempotency, concurrency?
Contract API/DB nào?
Hành vi UI nào (nếu có)?
Code nào liên quan?
Rule nào áp dụng?
Finding cũ nào còn mở?
Kiểm đúng bằng cách nào?
```

## C.5 Definition of Done

Xong **chỉ khi tất cả** đúng:

```
AC thoả          AND  design bị chạm đã approved trong baseline
AND  MR merged   AND  test bắt buộc xanh (có RED-first proof)
AND  finding blocking đã resolve hoặc waive có lý do
AND  release approval ghi nhận  AND  deploy thành công
AND  production verification pass
AND  evidence link đầy đủ, có captured_against
```

---

# D. Gate và governance thực thi

## D.1 Ai duyệt cái gì

| Gate | Ai quyết | Bật khi | Chặn cái gì nếu fail |
|---|---|---|---|
| **Scope Gate** | Product | Có FR/AC mới | Không được sang bước 6 |
| **Architecture Gate** | Architect *(federated §3.3)* | T1/T2, hoặc Architecture change | Không được sang bước 9 |
| **UI/UX Gate** | Product + Design | Chạm giao diện ở mức luồng hoặc màn hình mới | **Không được sang bước 9** |
| **Contract Gate** | Tech Lead + consumer ack | Contract breaking | Không được release |
| **Component Merge Gate** | Tech Lead | Mọi MR | Không merge |
| **UAT Gate** | **Business Owner** | T1/T2, Change Set đổi FR/AC | **Không được sang bước 19** |
| **Change Integration Gate** | Tech Lead các team | Nhiều team, `mode != independent` | Không release |
| **Production Gate** | SRE | Mọi release | Không deploy |

## D.1b Bản đem ra gate — Change Set view

Người duyệt không đọc file FR rời rạc. Trước mỗi commitment gate, sinh **Change Set view**:

```
aide csv render --change-set CHG-EKP-2026-002 --baseline BL-r1
→ generated/change-set-views/CSV-CHG-EKP-2026-002.md
```

Bảy mục, tất cả suy ra từ baseline:

```markdown
# Phase 2 — Engineering Knowledge Platform     ← change_set.label

## Mục tiêu                    ← change_set.objective
## Mục tiêu nghiệp vụ đổi      ← diff GOAL/KPI; rỗng nếu không đổi
## Tính năng mới               ← FR mới trong baseline, kèm AC đầy đủ
## Thay đổi hành vi hiện có    ← FR bump revision, hiện diff
## NGOÀI phạm vi lần này       ← FR đã tồn tại nhưng chưa vào baseline nào
## Ràng buộc mới               ← NFR mới hoặc siết chặt
## Câu hỏi mở còn lại          ← OQ chưa đóng
```

Mục **"NGOÀI phạm vi lần này"** là thứ người duyệt luôn hỏi, và nó suy ra được — viết tay thì không ai nhớ liệt kê.

**Chưa có generator (pilot C0+)?** Viết tay, nhưng gắn nhãn cho đúng bản chất và kèm luật phân xử:

```yaml
---
key: CSV-CHG-EKP-2026-002
group: derived
non_normative: true
derived_from: [BL-CHG-002-r1]
hand_written: true          # tạm — bỏ khi có generator
---
> Khi bản này và file FR bất đồng, **FR thắng**.
```

Không có dòng phân xử đó thì bạn vừa tạo nguồn sự thật thứ hai.

**Đừng đặt tên file là `PRD-…-phase2.md`** — người sau sẽ tưởng nó là nguồn. Tên file là `CSV-<CHG-key>.md`; tiêu đề hiển thị để "Phase 2 — PRD" cho quen mắt.

## D.2 Checklist mỗi gate

**Scope Gate** — CSV đã sinh từ baseline hiện tại · FR có ≥1 AC · AC dạng given/when/then · số liệu là reference không phải literal · OQ có owner + due · không FR nào approved mà đang blocked_by OQ mở

**Architecture Gate** — có ≥2 phương án + tradeoff · phương án bị loại có ghi lý do · tiêu chí quyết định ghi trước · threat model cập nhật nếu chạm bảo mật · mọi FR có CAP `covers` · nếu đem `AVW` ra gate thì nó `derived_from` CMP/ADR thật, không phải nguồn

**UI/UX Gate** — mock dựng từ token thật, không phải màu cứng · tương phản đạt ngưỡng ở **cả hai** chế độ sáng/tối · a11y tự động xanh · mock khai `non_normative: true` kèm luật phân xử · mọi màn hình trong screen inventory có layout xác định · **đi hết luồng chính mà không cần ai hướng dẫn** · mỗi màn hình đúng **một** hành động chính · trạng thái rỗng · tải · lỗi đều có · xem trên **thiết bị chính thật**, không phải trình giả lập · chuỗi dài nhất trong mọi ngôn ngữ không làm vỡ bố cục

**Contract Gate** — breaking detection chạy bằng máy · consumer list derived từ graph · consumer chính + partner đã ack · có migration window · coexistence khai rõ

**Component Merge Gate** — deterministic pass · review pass · test xanh có RED-first · context còn valid · MR khai đủ quan hệ · MR là lát mỏng tự đứng được

**UAT Gate** — build trên staging khớp `build`/commit SHA đang test · CSV đã sinh từ baseline hiện tại làm script đi test · mọi AC trong "Tính năng mới" + "Thay đổi hành vi hiện có" của CSV có `result: pass/fail` · `approved_by` khác `accountable_role` của FR đang test · fail được route đúng `patch` (bug) hoặc `intent_gap` (thiếu AC → OQ), không lẫn vào nhau · có bằng chứng người thật (§2.2.1)

**Production Gate** — release plan có ordering + rollback boundary · unit không rollback được đã khai · evidence đủ · approval có bằng chứng người thật + commit SHA

## D.3 Thao tác với finding

```
Tạo:      agent review sinh, có finding_key (rule_id + location_anchor + fingerprint)
Route:    intent_gap | bad_spec | patch | defer
          → bad_spec = sửa spec tầng trên rồi regenerate, KHÔNG patch xuống code
Xử lý:    ACCEPTED | REJECTED | WAIVED | NOT_APPLICABLE | DUPLICATE | NEEDS_MORE_EVIDENCE
Bác bỏ:   phải khai lý do khác rỗng. CẤM suy từ feedback chung chung
Vòng sau: giữ nguyên ID, chỉ cập nhật status. CẤM đánh số lại
```

## D.4 Waiver và override

```
1. Lựa chọn phải được offer tường minh (không cờ trần)
2. Một thao tác của người
3. Lý do khác rỗng
4. Ghi evidence, dùng một lần
5. CẤM ở chế độ chạy tự động
```

Waiver chỉ cấp được ở **tầng sở hữu rule**. Waiver lặp lại trên cùng một rule = tín hiệu rule sai, đưa vào vòng học.

**Nhưng trước khi sửa rule, kiểm nguyên nhân.** Ba waiver cho cùng một rule vì ba lý do khác nhau là **ba vấn đề**, không phải một — một bản vá sẽ chỉ phủ được một trong ba. Đếm triệu chứng giống nhau không phải chẩn đoán; đó là tín hiệu để **điều tra**, không phải kết luận đã có. *(Ca thật: hai trong ba waiver hoá ra là vòng tròn bootstrap thật — sửa ở PROC §1.3.6, không phải ở rule bị waiver. Waiver thứ ba không có vòng tròn nào; lỗ hổng nằm ở thiếu trigger của gate khác, sửa gate đó mới đúng chỗ.)*

## D.5 Hai chỉ số phải công khai

| Chỉ số | Ý nghĩa nếu cao |
|---|---|
| Tỷ lệ rule `enforced_by: unenforced` | Quy trình phần lớn là lời khuyên |
| Tỷ lệ `accepted_risk` mỗi gate | Gate đang thành nghi thức |

---

# E. UI / UX

## E.1 Bốn cấp

```
UX Flow          →  Screen Inventory  →  UI Design      →│→  UI Specification
luồng người dùng    danh mục màn hình    bố cục, visual  │    hành vi máy đọc được
UXF-<SYS>-NNN       SCR-<SYS>-NNN        UID-<SYS>-NNN   │    UIS-<SYS>-NNN
design/ux/          design/ux/           design/ui/      │    design/ui/
                                                          │
          ├──────── cấp 1–3: chỉ cần FR/AC ─────────────┤
                              +                          │
                      UI mock (UIM, derived)             │
                              ↓                          │
                       ⟶ UI/UX GATE ⟶                    │  ⟵ cần L3, chốt sau bước 9
                                                          │
                                                    Contract Gate
```

**Ranh giới gate nằm giữa cấp 3 và cấp 4, và nó không tuỳ tiện.** Cấp 1–3 chỉ cần FR/AC nên duyệt được sớm; cấp 4 tham chiếu field và endpoint nên không tồn tại trước L3. Đó cũng là ranh giới đúng về mặt người duyệt: Product và Design review *luồng và hình thức*, không review binding máy đọc.

## E.2 UI Specification — cấp duy nhất agent đọc

Figma đẹp không giúp agent implement. UI Spec phải máy đọc được:

*(Cấp 1–3 không vô dụng — chỉ không phải cho agent. UI/UX Gate ký chính revision của chúng, và UIS `derived_from`/`refines` chúng để biết đang đặc tả màn hình nào. Xem §B.11 "Cấp 1–3 dùng để làm gì".)*

```yaml
component: RegistrationForm
states: [idle, submitting, success, error]
fields:
  - { name: term, type: select, options_from: API-PAY-v3#terms, required: true }
validation:
  - { field: term, rule: "∈ {3,6,9,12}", message_key: err.term.invalid }
behavior:
  - on: submit
    when: valid
    then: POST API-PAY-v3/installment-plans
  - on: error.409
    then: show message_key=err.duplicate, giữ nguyên form
tokens: [color.primary, spacing.md]
a11y: { focus_order: [term, submit], label_required: true }
```

## E.3 Khi nào cần Figma

| Cần Figma | Không cần |
|---|---|
| Màn hình mới, luồng mới | Thêm field vào form đã có |
| Đổi visual language, token | Sửa validation message |
| Component chưa có trong design system | Dùng lại component có sẵn |

**Có Figma vẫn phải có UI Spec ở Git.** Figma là nguồn cho *visual*; Git là nguồn cho *hành vi*.

## E.4 Gate

**Hai điểm kiểm, hai mục đích khác nhau.**

### UI/UX Gate — cấp 1–3, TRƯỚC L3

| | |
|---|---|
| **Trả lời** | Người dùng có dùng được không? |
| **Ai quyết** | Product + Design |
| **Bật khi** | Chạm giao diện ở mức **luồng hoặc màn hình mới**. Bỏ khi chỉ thêm field vào form đã có |
| **Đem ra** | UI mock (`UIM`) — `derived`, `non_normative` |
| **Được ký** | Revision của UXF · SCR · UID — **không phải mock** |
| **Chặn** | Không được sang bước 9 |

Checklist ở §D.2. Điều chỉ gate này kiểm được: **đi hết luồng chính mà không cần ai hướng dẫn.** Không spec nào chứng minh được điều đó, và đo sau khi production thì đã muộn.

### Contract Gate — cấp 4, SAU L3

UI Spec là input bắt buộc của Contract Gate khi thay đổi chạm giao diện, và là input của context package cho task frontend. Không đổi so với trước.

### Timing

```text
Scope Gate → cấp 1–3 + mock → UI/UX GATE → L3 → cấp 4 → Contract Gate
             (song song bước 5–7)          (bước 9)
```

**Mock không thay UI Spec cho agent.** Agent đọc `UIS` và design token; mock là đường cho *người* duyệt. Hai đường phục vụ hai đối tượng, và trộn chúng là cách nhanh nhất tạo nguồn sự thật thứ hai (PROC §4.4.4).

**Timing:** UX Flow, Screen Inventory, UI Design (cấp 1–3) chỉ cần FR/AC — làm sớm, song song bước 5–7 (EXEC B.9). UI Specification (cấp 4) tham chiếu field/endpoint hợp đồng nên chốt cùng nhịp với L3 (bước 9), không sớm hơn được.

---

# F. Ví dụ đầy đủ — thêm "thanh toán trả góp" vào PaymentHub

Flow **Change**, tier **T1**, một team.

## F.1 Bảng delta

| Bước | Tạo mới | Bump revision | Không đụng |
|---|---|---|---|
| 2–3 | `CHG-PAY-2026-084` | — | — |
| 4 | `FR-PAY-041..045` + AC · `GOAL-PAY-004` · `KPI-PAY-007` | `PRD-PAYMENTHUB` *chỉ khi GOAL/KPI/Scope đổi* | PRD nếu chỉ thêm FR |
| 6 | `CAP-PAY-009` *nếu năng lực mới* · cạnh `covers` | `L1` mapping | L1 nếu nằm gọn trong CAP cũ |
| 7 | `CMP-PAY-INSTALLMENT` · `ADR-2026-019` | `CMP-PAY-AUTH` r17→r18 · threat model | CMP không liên quan |
| 8 | `UXF-PAY-004` · `SCR-PAY-011` · `UIS-PAY-011` | — | design system tokens |
| 9 | `TBL-installment-plan` · `EVT-INSTALLMENT-CREATED` | `API-PAY` r14→r15, v2→**v3** | — |
| 11 | — *(1 team: không tạo WP)* | — | — |
| 12–16 | `CTX-…` · `PLAN-…` · MR · `DIARY-…` · `TRC-…` · review · finding | — | — |
| 19–21 | `REL-PLAN-084` · deployment record · production verification | — | — |

## F.2 Ba điểm dễ sai

**`CMP-PAY-INSTALLMENT` sinh trong epic nhưng là node của System.** Nằm ở `architecture/l2/`, mang `system: SYS-PAYMENT`, sống tiếp sau khi CHG-084 đóng. Cái thuộc epic chỉ là baseline.

**Không có file nào tên `L2-EPIC-084.md`.** Muốn xem epic đổi gì → sinh `generated/change-set-views/CSV-CHG-PAY-2026-084.md`.

**`API-PAY` v2→v3 breaking** → Contract Gate. Consumer list derived. Mobile `ack: required`. Coexistence + migration window 3 tháng.

## F.3 Ai đọc gì

| Vai | Đọc | Không đọc |
|---|---|---|
| Product ở Scope Gate | 5 FR + AC mới, GOAL bị chạm | Toàn bộ PRD |
| Architect ở Arch Gate | 2–3 phương án, CMP bị chạm, ADR liên quan | Toàn bộ L2 |
| **Agent implement** | **Context package** — 1–2 CMP + contract + NFR + rule + golden example | Cả L2, cả PRD, cả epic |
| Team khác | Revision **as-deployed** | Baseline đang dở |

## F.4 Nếu là bounded context mới

Flow → **Architecture change**. Tier luôn T1. Architecture Gate cần **Domain Architect + Enterprise Architecture**. L1 thêm `SVC` mới + ranh giới context. Glossary domain có thể phải tách. ADR ghi rõ vì sao tách chứ không mở rộng context cũ.

## F.5 Nếu nhiều team

Change Set hiện ra · mỗi team một Epic · `EPIC-084-MOBILE` `blocked_by: [EPIC-084-PAYMENT]` vì mobile cần API v3 trước · Change Integration Gate bật · mode `compatible-rollout` nên mobile migrate theo nhịp của họ.

---