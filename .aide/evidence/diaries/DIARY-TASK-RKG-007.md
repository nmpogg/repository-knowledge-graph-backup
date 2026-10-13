---
key: DIARY-TASK-RKG-007
type: implementation-diary
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-007
revision: 5
implementation_window:
  from: '2026-09-25'
  through: '2026-09-25'
provenance: reconstructed-from-committed-diff-and-prior-evidence
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  implementation_commits:
  - 4e902ebd2e86dbfe8a7afd8e491ecaf25a73168e
prior_evidence:
- evidence/context/CTX-TASK-RKG-007.yaml
- evidence/diaries/DIARY-TASK-RKG-007.md
- evidence/plans/PLAN-TASK-RKG-007.md
- evidence/tests/TEST-RKG-PKG-INVENTORY.md
revision_history:
- revision: 1
  metadata:
    key: DIARY-TASK-RKG-007
    type: implementation-diary
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-007
    revision: 1
    captured_at: 2026-09-25
    captured_against:
      artifacts:
      - key: TASK-RKG-007
        revision: 4
      - key: FR-RKG-002
        revision: 8
      code_revision: 4e902ebd2e86dbfe8a7afd8e491ecaf25a73168e
  record: '# DIARY-TASK-RKG-007 — Python metadata and package inventory


    The Python adapter now reads `pyproject.toml`, requirements includes, `uv.lock` and

    `poetry.lock` from manifest bytes. Parsing is static and bounded by the manifest.

    Dependency records retain declaration or lock provenance, groups and markers; graph

    facts carry stable IDs and source evidence. The detect stage returns generic

    `TechnologyDetection` records for TASK-RKG-008. A reviewed import ownership table

    maps differently named distributions; unknown names are never inferred from imports.

    Callable usage emits `depends_on` rather than an external `calls` edge.


    The adapter does not resolve dynamic dependency metadata or unsafe URL/editable

    requirement entries. Those produce path-only diagnostics. Only exact versions from

    the lockfile are published as detected versions; declared constraints remain source

    provenance. TASK-RKG-008 consumes the detection records and decides deep support.


    Verification and limits are recorded in `TEST-RKG-PKG-INVENTORY`.'
---

# DIARY-TASK-RKG-007

The Python adapter now reads `pyproject.toml`, requirements includes, `uv.lock` and
`poetry.lock` from manifest bytes. Parsing is static and bounded by the manifest.
Dependency records retain declaration or lock provenance, groups and markers; graph
facts carry stable IDs and source evidence. The detect stage returns generic
`TechnologyDetection` records for TASK-RKG-008. A reviewed import ownership table
maps differently named distributions; unknown names are never inferred from imports.
Callable usage emits `depends_on` rather than an external `calls` edge.

The adapter does not resolve dynamic dependency metadata or unsafe URL/editable
requirement entries. Those produce path-only diagnostics. Only exact versions from
the lockfile are published as detected versions; declared constraints remain source
provenance. TASK-RKG-008 consumes the detection records and decides deep support.

Verification and limits are recorded in `TEST-RKG-PKG-INVENTORY`.

## Đối chiếu commit và phạm vi hiện hành

## Kết quả đối chiếu triển khai

Đọc metadata dependency và usage tĩnh, chuẩn hóa inventory/provenance; tách metadata khỏi hành vi core và không cài dependency đầu vào.

Các file thay đổi được xác định bằng Git diff của các commit được pin trong frontmatter. Current-tree hash nằm trong context revision 3; khác hash lịch sử là revision về sau, không phải cùng lần chạy.

## Diễn giải và correction

Hành vi và các lần kiểm đã ghi trong prior evidence giữ nguyên; bản này bổ sung liên kết và nguồn commit, không thay kết quả cũ.

## Kết quả lần bổ sung hồ sơ

Đã đọc commit/file, parse test declarations và liên kết evidence; không chạy lại runtime test hoặc đo KPI. Không nhận đây là review code độc lập hay approval.
