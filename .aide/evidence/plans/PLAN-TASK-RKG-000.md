---
key: PLAN-TASK-RKG-000
type: implementation-plan
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-000
revision: 3
plan_date: '2026-09-15'
date_basis:
  commit: 799cb6cfd6dac194046d1a184546f39aca9c2071
  field: author_at converted to Asia/Bangkok
provenance: git-derived implementation plan
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  context: CTX-TASK-RKG-000.yaml
verification_targets: []
frontend_test_paths: []
revision_history:
- revision: 1
  metadata:
    key: PLAN-TASK-RKG-000
    type: implementation-plan
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-000
    captured_at: 2026-09-15
    captured_against:
      artifacts:
      - CR-RKG-001
  record: '# Plan


    1. Đọc nguồn hiện tại và xác định system/scope/FR/AC/constraints.

    2. Tạo registry, PRD, glossary, FR và NFR ở trạng thái draft.

    3. Tạo L1/L2, ADR, threat model, API/schema và UI/UX artifacts.

    4. Tạo Change Set, Open Questions, backlog và evidence; không tạo approved baseline.

    5. Kiểm tra cấu trúc, key/reference, YAML và review diff.


    ## Không làm


    Không scaffold hoặc implement frontend/backend/analyzer; không thay đổi trạng thái

    T-01…T-24 trong `docs/TASK.md`; không tự phê duyệt gate.'
---

# PLAN-TASK-RKG-000

1. Đọc nguồn hiện tại và xác định system/scope/FR/AC/constraints.
2. Tạo registry, PRD, glossary, FR và NFR ở trạng thái draft.
3. Tạo L1/L2, ADR, threat model, API/schema và UI/UX artifacts.
4. Tạo Change Set, Open Questions, backlog và evidence; không tạo approved baseline.
5. Kiểm tra cấu trúc, key/reference, YAML và review diff.

## Không làm

Không scaffold hoặc implement frontend/backend/analyzer; không thay đổi trạng thái
T-01…T-24 trong `docs/TASK.md`; không tự phê duyệt gate.

## Phạm vi code và kiểm chứng

- `.aide/README.md`
- `.aide/architecture/adr/ADR-2026-001.md`
- `.aide/architecture/l1/CAP-RKG-001.md`
- `.aide/architecture/l1/CAP-RKG-002.md`
- `.aide/architecture/l1/CAP-RKG-003.md`
- `.aide/architecture/l2/CMP-RKG-ANALYZER.md`
- `.aide/architecture/l2/CMP-RKG-CONVERSATION.md`
- `.aide/architecture/l2/CMP-RKG-GRAPH.md`
- `.aide/architecture/l2/CMP-RKG-TRANSPORT.md`
- `.aide/architecture/l2/CMP-RKG-WEB.md`
- `.aide/architecture/threat-model/TM-RKG.md`
- `.aide/design/ui/UID-RKG-001.md`
- `.aide/design/ui/UIS-RKG-001.md`
- `.aide/design/ux/SCR-RKG-001.md`
- `.aide/design/ux/UXF-RKG-001.md`
- `.aide/design/ux/UXF-RKG-002.md`
- `.aide/domain/glossary-core.md`
- `.aide/lifecycle/change-sets/CHG-RKG-2026-001/change-set.yaml`
- `.aide/lifecycle/change-sets/CHG-RKG-2026-001/open-questions/OQ-RKG-001.md`
- `.aide/lifecycle/change-sets/CHG-RKG-2026-001/open-questions/OQ-RKG-002.md`
- `.aide/lifecycle/epics/EPIC-001-TEAM-RKG.md`
- `.aide/lifecycle/epics/EPIC-002-TEAM-RKG.md`
- `.aide/lifecycle/epics/EPIC-003-TEAM-RKG.md`
- `.aide/lifecycle/epics/EPIC-004-TEAM-RKG.md`
- `.aide/lifecycle/epics/EPIC-005-TEAM-RKG.md`
- `.aide/lifecycle/tasks/TASK-RKG-000.md`
- `.aide/lifecycle/tasks/TASK-RKG-001.md`
- `.aide/lifecycle/tasks/TASK-RKG-002.md`
- `.aide/lifecycle/tasks/TASK-RKG-003.md`
- `.aide/lifecycle/tasks/TASK-RKG-004.md`
- `.aide/lifecycle/tasks/TASK-RKG-005.md`
- `.aide/lifecycle/tasks/TASK-RKG-006.md`
- `.aide/lifecycle/tasks/TASK-RKG-007.md`
- `.aide/lifecycle/tasks/TASK-RKG-008.md`
- `.aide/lifecycle/tasks/TASK-RKG-009.md`
- `.aide/lifecycle/tasks/TASK-RKG-010.md`
- `.aide/lifecycle/tasks/TASK-RKG-011.md`
- `.aide/lifecycle/tasks/TASK-RKG-012.md`
- `.aide/lifecycle/tasks/TASK-RKG-013.md`
- `.aide/lifecycle/tasks/TASK-RKG-014.md`
- `.aide/lifecycle/tasks/TASK-RKG-015.md`
- `.aide/lifecycle/tasks/TASK-RKG-016.md`
- `.aide/lifecycle/tasks/TASK-RKG-017.md`
- `.aide/lifecycle/tasks/TASK-RKG-018.md`
- `.aide/lifecycle/tasks/TASK-RKG-019.md`
- `.aide/lifecycle/tasks/TASK-RKG-020.md`
- `.aide/lifecycle/tasks/TASK-RKG-021.md`
- `.aide/lifecycle/tasks/TASK-RKG-022.md`
- `.aide/lifecycle/tasks/TASK-RKG-023.md`
- `.aide/lifecycle/tasks/TASK-RKG-024.md`
- `.aide/product/prd/PRD-RKG.md`
- `.aide/registry/REG-OWNER-001.md`
- `.aide/registry/REG-REPO-001.md`
- `.aide/registry/REG-TYPE-001.md`
- `.aide/requirements/fr/FR-RKG-001.md`
- `.aide/requirements/fr/FR-RKG-002.md`
- `.aide/requirements/fr/FR-RKG-003.md`
- `.aide/requirements/fr/FR-RKG-004.md`
- `.aide/requirements/fr/FR-RKG-005.md`
- `.aide/requirements/fr/FR-RKG-006.md`
- `.aide/requirements/fr/FR-RKG-007.md`
- `.aide/requirements/fr/FR-RKG-008.md`
- `.aide/requirements/fr/FR-RKG-009.md`
- `.aide/requirements/fr/FR-RKG-010.md`
- `.aide/requirements/fr/FR-RKG-011.md`
- `.aide/requirements/fr/FR-RKG-012.md`
- `.aide/requirements/fr/FR-RKG-013.md`
- `.aide/requirements/fr/FR-RKG-014.md`
- `.aide/requirements/fr/FR-RKG-015.md`
- `.aide/requirements/fr/FR-RKG-016.md`
- `.aide/requirements/fr/FR-RKG-017.md`
- `.aide/requirements/nfr/NFR-RKG-PERF-001.md`
- `.aide/requirements/nfr/NFR-RKG-REL-001.md`
- `.aide/requirements/nfr/NFR-RKG-SEC-001.md`
- `.aide/requirements/nfr/NFR-RKG-UX-001.md`
- `.aide/tech-specs/RKG-CORE/api/API-RKG-CORE-v1.md`
- `.aide/tech-specs/RKG-CORE/schema/TBL-RKG-GRAPH.md`

- Đối chiếu schema/reference, artifact hash, runbook và evidence được pin.

Các lệnh này mô tả cách kiểm, không khẳng định đã chạy trong lần bổ sung hồ sơ. Kết quả thực thi theo evidence đã ghi của task.

Context: [CTX-TASK-RKG-000](../context/CTX-TASK-RKG-000.yaml). Kết quả triển khai: [DIARY-TASK-RKG-000](../diaries/DIARY-TASK-RKG-000.md).
