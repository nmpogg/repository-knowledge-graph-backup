---
key: DIARY-TASK-RKG-008
type: implementation-diary
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-008
revision: 5
implementation_window:
  from: '2026-09-25'
  through: '2026-09-25'
provenance: reconstructed-from-committed-diff-and-prior-evidence
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  implementation_commits:
  - 51cede902a688529ebcd6ec164af7b3a86d826a0
prior_evidence:
- evidence/context/CTX-TASK-RKG-008.yaml
- evidence/diaries/DIARY-TASK-RKG-008.md
- evidence/plans/PLAN-TASK-RKG-008.md
- evidence/tests/TEST-RKG-DETECT-001.md
revision_history:
- revision: 1
  metadata:
    key: DIARY-TASK-RKG-008
    type: implementation-diary
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-008
    revision: 1
    captured_at: 2026-09-25
    captured_against:
      artifacts:
      - key: TASK-RKG-008
        revision: 6
      - key: FR-RKG-002
        revision: 8
      - key: NFR-RKG-EXT-001
        revision: 3
      code_revision: 51cede902a688529ebcd6ec164af7b3a86d826a0
  record: '# DIARY-TASK-RKG-008 — Technology detection and adapter selection


    The branch was created from `dev` after T-007 was merged. The detection coordinator

    combines `TechnologyDetection` evidence from the Python metadata adapter and

    syntax-specific detector plugins. Its selection path reads registry descriptors,

    keeps all compatible deep adapters and publishes capability/state details without

    branching on adapter ID. `PythonImportDetector` uses T-007''s explicit import profile.

    `FastAPIAppDetector` finds direct module-level constructors and checks local module

    shadowing and reassignment. All source analysis remains static.


    The generic result carries ordered app candidates, exact override validation,

    single-candidate auto-selection and a reusable prior choice. A selected adapter

    declares `entrypoint_required` on its instance when an application is mandatory.

    T-009 should reuse the detector and implement route/DI extraction. T-015 must turn

    `app_selection_required`/`app_unresolved` into job outcomes and persist the selected

    application with snapshot evidence. The interface handoff is in

    `src/rkg/detection/README.md`.


    Verification and scope boundaries are recorded in `TEST-RKG-DETECT-001`.'
---

# DIARY-TASK-RKG-008

The branch was created from `dev` after T-007 was merged. The detection coordinator
combines `TechnologyDetection` evidence from the Python metadata adapter and
syntax-specific detector plugins. Its selection path reads registry descriptors,
keeps all compatible deep adapters and publishes capability/state details without
branching on adapter ID. `PythonImportDetector` uses T-007's explicit import profile.
`FastAPIAppDetector` finds direct module-level constructors and checks local module
shadowing and reassignment. All source analysis remains static.

The generic result carries ordered app candidates, exact override validation,
single-candidate auto-selection and a reusable prior choice. A selected adapter
declares `entrypoint_required` on its instance when an application is mandatory.
T-009 should reuse the detector and implement route/DI extraction. T-015 must turn
`app_selection_required`/`app_unresolved` into job outcomes and persist the selected
application with snapshot evidence. The interface handoff is in
`src/rkg/detection/README.md`.

Verification and scope boundaries are recorded in `TEST-RKG-DETECT-001`.

## Đối chiếu commit và phạm vi hiện hành

## Kết quả đối chiếu triển khai

Chọn language/framework adapter từ descriptor, version evidence và application candidates; unsupported hoặc ambiguity phải hiện rõ.

Các file thay đổi được xác định bằng Git diff của các commit được pin trong frontmatter. Current-tree hash nằm trong context revision 3; khác hash lịch sử là revision về sau, không phải cùng lần chạy.

## Diễn giải và correction

Hành vi và các lần kiểm đã ghi trong prior evidence giữ nguyên; bản này bổ sung liên kết và nguồn commit, không thay kết quả cũ.

## Kết quả lần bổ sung hồ sơ

Đã đọc commit/file, parse test declarations và liên kết evidence; không chạy lại runtime test hoặc đo KPI. Không nhận đây là review code độc lập hay approval.
