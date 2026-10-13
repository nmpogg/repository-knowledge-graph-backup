---
uid: null
key: TEST-RKG-DIRECTORY-DOCS-001
type: test-evidence
group: evidence
scope: system
system: SYS-RKG
status: recorded
revision: 2
normative: false
relations:
  verifies:
  - TASK-RKG-027
  - FR-RKG-002
  - FR-RKG-003
  - ADR-2026-006
classification: internal
ai_assisted: true
documentation_reconciliation:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  baseline:
    key: BL-CHG-RKG-2026-001
    revision: 3
  task_count: 29
  bootstrap_task: TASK-RKG-000
  task_records: 90
  checks:
    task_set_and_status: passed
    unique_filenames_without_revision_suffix: passed
    record_format_keys_and_current_pins: passed
    plan_dates_against_git: passed
    task_dependency_graph: passed
    current_task_parents: passed
    yaml_and_json_parsing: passed
    markdown_links: passed
    baseline_current_hashes: passed
    runtime_code_and_signed_approval_preservation: passed
    git_diff_check: passed
  runtime_tests: not_run
  runtime_code_changed: false
  new_tasks: 0
  approval_added: false
  parsed_documents: 259
  baseline_artifact_pins: 110
---

# TEST-RKG-DIRECTORY-DOCS-001 - Documentation consistency verification

Verification date: 2026-10-01 (Asia/Bangkok).

Documentation-only verification. Directory replaces Namespace in new snapshots;
core owns filesystem structure while adapters retain module/package resolution.
Implementation/runtime checks have not been performed. User confirmation is required
before TASK-RKG-027 code work; task remains todo.

## Current-tree checks

- PASS: Markdown artifact keys match filenames/primary headings; change-set key
  follows its existing directory convention.
- PASS: edited revisions increment once; new ADR/task revisions are 1.
- PASS: FR-RKG-002/003 published AC IDs/order and constrained_by lists are unchanged.
  Existing NFR relation symmetry is not modified by this change.
- PASS: new ADR/task FR/CMP/EPIC/task references resolve to artifact filenames; GOAL
  references resolve to current PRD definitions; task AC references are defined.
- PASS: all change-set gates are pending and current_change is in frontmatter.
- PASS: task stays todo; DDL declares TBL revision 9 while target semantic revision
  10 requires future migration/execution.
- PASS: git diff --check reports no whitespace errors.
- PASS: no tracked src/frontend/tests/DDL changes or edits to historical
  approval/baseline records in this docs phase.

Checks use Python assertions and Git diff, not a full YAML/schema validator,
adapter/UI test or DDL execution. Existing runtime database changes and separate
SOOPI evidence are outside this review. Generated views remain non-normative and
need refresh before gate approval. No claim of completed implementation is made.

## Artifact revisions verified

Git base revision: `c489ab4e58c216547371d81e05b467622209a6e8` plus these working-tree SHA-256 digests.

| Key | Revision | Relative artifact | SHA-256 |
|---|---|---|---|
| ADR-2026-006 | 1 | `.aide/architecture/adr/ADR-2026-006.md` | `c2854f5a2883f3dc090d5c0dcabe6912afc70216236a617dfc747cbf1c190c35` |
| CMP-RKG-ANALYZER | 6 | `.aide/architecture/l2/CMP-RKG-ANALYZER.md` | `11c0a3177052f3d848aabf5224fd33583209999dd9d59260a9ec947b4fca33a0` |
| CMP-RKG-GRAPH | 5 | `.aide/architecture/l2/CMP-RKG-GRAPH.md` | `fbe97d8203c114811304e7413d891052d66275dfa28a66cc01e7f7c5d0433823` |
| CMP-RKG-WEB | 6 | `.aide/architecture/l2/CMP-RKG-WEB.md` | `ccf1692049b50195f5f8471efb9150707277b369e6a03d7b02a14dd33e7ab839` |
| UIS-RKG-001 | 8 | `.aide/design/ui/UIS-RKG-001.md` | `fb20efe67e6a60969ef8a2afebacef75faf2aec38d23c1ecb783ec11584933c7` |
| CHG-RKG-2026-001 | 19 | `.aide/lifecycle/change-sets/CHG-RKG-2026-001/change-set.yaml` | `d5dc1f6fdb9123607207b5a169888c093105d43558fc99173d1ac731704e2bd5` |
| TASK-RKG-027 | 1 | `.aide/lifecycle/tasks/TASK-RKG-027.md` | `25e4a06e54094bbf602ad5c1d46ed8834b8e35713575a3e7df06ef00f612add4` |
| GATE-RKG-ARCHITECTURE | 5 | `.aide/policies/gates/GATE-RKG-ARCHITECTURE.md` | `890fa2a06f4181e1f0911c7e07a6fe852cf47c586cca983e6fd173b05779070a` |
| GATE-RKG-CONTRACT | 5 | `.aide/policies/gates/GATE-RKG-CONTRACT.md` | `4542c93e8491b89882c99cf8d843d5ea075324b0fcc88769470991a66b830c66` |
| GATE-RKG-UIUX | 6 | `.aide/policies/gates/GATE-RKG-UIUX.md` | `79ac4f56d53be49c8b3a19283b9704cc8c93188b80ee36b1669822d59094f0a4` |
| PRD-RKG | 17 | `.aide/product/prd/PRD-RKG.md` | `46d1dd71ed2f1b663e324e9163f026f059478f3f70cb14532993b6e0773f0bd3` |
| REG-ADAPTER-001 | 6 | `.aide/registry/REG-ADAPTER-001.md` | `ef46ff393fd8a0913f18917c8a2e3bbef3ccdc1bf518f70b62dbecf1dd6a3ed8` |
| FR-RKG-002 | 9 | `.aide/requirements/fr/FR-RKG-002.md` | `d8b36a135a8632543e39815696e4b7b46acf94aea39d2d52e03f34edc266c1bc` |
| FR-RKG-003 | 9 | `.aide/requirements/fr/FR-RKG-003.md` | `8d4bd9ffde99804a65fc7e4ce9e08c3cbd18c4fafaee9befd8d50c2683e7637c` |
| TBL-RKG-GRAPH | 10 | `.aide/tech-specs/RKG-GRAPH/schema/TBL-RKG-GRAPH.md` | `a132f9f6adf88d4f1d109c7a6297843505543e38bb176c464457920aa01a37d1` |
| API-RKG-CORE-v1 | 10 | `.aide/tech-specs/RKG-TRANSPORT/api/API-RKG-CORE-v1.md` | `4e127eaac0b5410c1137f295cc891e242b57edc0d35af46fc5d31cca3106e0f8` |

## Kiểm tra hồ sơ lifecycle hiện hành

Phạm vi giữ nguyên TASK-RKG-001–029 và bootstrap TASK-RKG-000. Mỗi task có
một context YAML thuần, một plan Markdown và một diary Markdown. Review là
YAML; các revision/test runs cũ nằm trong file chuẩn tương ứng. Không còn file
có hậu tố revision. Ngày plan đối chiếu ngày commit triển khai, không thêm ngày
bổ sung hồ sơ vào plan.

Kết quả kiểm tra cấu trúc, liên kết, dependency, ngày Git và hash hiện hành nằm
trong documentation_reconciliation. Phần kiểm chứng Directory ở trên giữ
nguyên là ghi nhận của lần kiểm trước khi triển khai Task 027, không mô tả trạng
thái task hiện tại. Lần kiểm hồ sơ này không chạy lại runtime tests hay ký gate.
