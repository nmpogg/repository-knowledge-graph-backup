---
key: DIARY-TASK-RKG-014
type: implementation-diary
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-014
revision: 5
implementation_window:
  from: '2026-09-24'
  through: '2026-09-24'
provenance: reconstructed-from-committed-diff-and-prior-evidence
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  implementation_commits:
  - 4399660b46a8362ec9d87652795d023318ea6dbc
prior_evidence:
- evidence/context/CTX-TASK-RKG-014.yaml
- evidence/diaries/DIARY-TASK-RKG-014.md
- evidence/plans/PLAN-TASK-RKG-014.md
revision_history:
- revision: 1
  metadata:
    key: DIARY-TASK-RKG-014
    type: implementation-diary
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-014
    revision: 1
    captured_at: 2026-09-24
    captured_against:
      artifacts:
      - key: TASK-RKG-014
        revision: 5
      - key: FR-RKG-003
        revision: 7
      - key: FR-RKG-004
        revision: 6
      - key: API-RKG-CORE-v1
        revision: 9
      - key: CMP-RKG-GRAPH
        revision: 4
      - key: approval-006
        revision: 1
      base_commit: 348ee6154975b4971d61c4c698e37cfd9c36ff29
      code_tree: working-tree-file-hashes-below
      pins:
        cpython: 3.12.14
        kuzu: 0.11.3
  record: "# DIARY-TASK-RKG-014 — Search, traversal and context services\n\n## Thực hiện\n\n- Operator\
    \ decisions before implement: defer AC-037/062 p95 reports to later\n  tasks; service-layer guards\
    \ only for AC-060 (HTTP/UI → T-016); truncation\n  reasons `depth_limit|max_nodes|max_edges|max_chars`;\
    \ search =\n  case-insensitive substring on name / qualified_name / `METHOD path`; baseline\n  API\
    \ rev 9 via partial Contract approval-006.\n- `search_entities` / `get_entity`: snapshot-scoped, order\
    \ type →\n  qualified_name → id, paging default 20 / max 100.\n- `traverse_subgraph`: BFS, direction/edge_types\
    \ filter, visited-set cycles,\n  deterministic edge expansion, no dangling non-repo ends.\n- `build_context`:\
    \ wraps traversal + evidence + diagnostic severity counts +\n  `context_json` char budget with referential\
    \ integrity.\n- Typed errors: `NoActiveSnapshotError`, `SnapshotUnavailableError`,\n  `NotFoundError`,\
    \ `InvalidBudgetError`.\n\n## Kiểm chứng trên cây mã hiện tại\n\n| Lệnh | Kết quả |\n| --- | --- |\n\
    | `uv run pytest tests/ -q` | pass — 26 tests |\n| `uv run ruff check src tests` | pass — All checks\
    \ passed |\n\nSHA-256 của file đã kiểm chứng:\n\n| File | SHA-256 |\n| --- | --- |\n| `src/rkg/graph/__init__.py`\
    \ | `8465dfcdd1ff9e31b30a77ac208c27d1061b2a78fe3444a1d5ebbc8c8c247273` |\n| `src/rkg/graph/README.md`\
    \ | `be49543e9fcf2fba62a202cc85e9e416509e68031186aee02ce5387471d9460c` |\n| `src/rkg/graph/errors.py`\
    \ | `cad1713787cdd529f4c75a880e762a3415e4646c2ee95c38cc6ab3a8749cb145` |\n| `src/rkg/graph/access.py`\
    \ | `86fb1873e597f0ba3326f50e29f9dd1a4dc79aaa0f0add5233b14115fe6c390d` |\n| `src/rkg/graph/search.py`\
    \ | `7a27f5ce7fe88a0a036e7fb9e4680222a6df2f75966f24d15037b1239446cf28` |\n| `src/rkg/graph/traversal.py`\
    \ | `7bd11e55187ff4d08f567a557df7e3016921631a2e7d1e838aac0d8f3c64ba47` |\n| `src/rkg/graph/context.py`\
    \ | `c95ece6b843dc1a9bbaf4b56d2b19ce3dd330d69f8ce243ef0f0172086787215` |\n| `tests/integration/graph_helpers.py`\
    \ | `c1af0f363817f0b954a79277ecd78eb1ee6c854b0f568bee6611b0b19cd893c2` |\n| `tests/integration/test_graph_reads.py`\
    \ | `22a40a7dc6b6385e047f24d18c2a80fbfcef118964698f299a03394b20c3a1e2` |\n| `.aide/lifecycle/tasks/TASK-RKG-014.md`\
    \ | `6856c4f687fbee85fe04f11a3bfd1594be3b166030448e4f113f32adaae02be3` |\n\n## Deferred\n\n- AC-RKG-037\
    \ / AC-RKG-062 benchmark corpus + machine report → T-016/T-022.\n- HTTP mapping of error codes → T-016."
---

# DIARY-TASK-RKG-014

## Thực hiện

- Operator decisions before implement: defer AC-037/062 p95 reports to later
  tasks; service-layer guards only for AC-060 (HTTP/UI → T-016); truncation
  reasons `depth_limit|max_nodes|max_edges|max_chars`; search =
  case-insensitive substring on name / qualified_name / `METHOD path`; baseline
  API rev 9 via partial Contract approval-006.
- `search_entities` / `get_entity`: snapshot-scoped, order type →
  qualified_name → id, paging default 20 / max 100.
- `traverse_subgraph`: BFS, direction/edge_types filter, visited-set cycles,
  deterministic edge expansion, no dangling non-repo ends.
- `build_context`: wraps traversal + evidence + diagnostic severity counts +
  `context_json` char budget with referential integrity.
- Typed errors: `NoActiveSnapshotError`, `SnapshotUnavailableError`,
  `NotFoundError`, `InvalidBudgetError`.

## Kiểm chứng trên cây mã hiện tại

| Lệnh | Kết quả |
| --- | --- |
| `uv run pytest tests/ -q` | pass — 26 tests |
| `uv run ruff check src tests` | pass — All checks passed |

SHA-256 của file đã kiểm chứng:

| File | SHA-256 |
| --- | --- |
| `src/rkg/graph/__init__.py` | `8465dfcdd1ff9e31b30a77ac208c27d1061b2a78fe3444a1d5ebbc8c8c247273` |
| `src/rkg/graph/README.md` | `be49543e9fcf2fba62a202cc85e9e416509e68031186aee02ce5387471d9460c` |
| `src/rkg/graph/errors.py` | `cad1713787cdd529f4c75a880e762a3415e4646c2ee95c38cc6ab3a8749cb145` |
| `src/rkg/graph/access.py` | `86fb1873e597f0ba3326f50e29f9dd1a4dc79aaa0f0add5233b14115fe6c390d` |
| `src/rkg/graph/search.py` | `7a27f5ce7fe88a0a036e7fb9e4680222a6df2f75966f24d15037b1239446cf28` |
| `src/rkg/graph/traversal.py` | `7bd11e55187ff4d08f567a557df7e3016921631a2e7d1e838aac0d8f3c64ba47` |
| `src/rkg/graph/context.py` | `c95ece6b843dc1a9bbaf4b56d2b19ce3dd330d69f8ce243ef0f0172086787215` |
| `tests/integration/graph_helpers.py` | `c1af0f363817f0b954a79277ecd78eb1ee6c854b0f568bee6611b0b19cd893c2` |
| `tests/integration/test_graph_reads.py` | `22a40a7dc6b6385e047f24d18c2a80fbfcef118964698f299a03394b20c3a1e2` |
| `.aide/lifecycle/tasks/TASK-RKG-014.md` | `6856c4f687fbee85fe04f11a3bfd1594be3b166030448e4f113f32adaae02be3` |

## Deferred

- AC-RKG-037 / AC-RKG-062 benchmark corpus + machine report → T-016/T-022.
- HTTP mapping of error codes → T-016.

## Đối chiếu commit và phạm vi hiện hành

## Kết quả đối chiếu triển khai

Implement search deterministic, BFS cycle/budget/direction/filter và context serialization/truncation; chỉ đọc snapshot đã pin.

Các file thay đổi được xác định bằng Git diff của các commit được pin trong frontmatter. Current-tree hash nằm trong context revision 3; khác hash lịch sử là revision về sau, không phải cùng lần chạy.

## Diễn giải và correction

Hành vi và các lần kiểm đã ghi trong prior evidence giữ nguyên; bản này bổ sung liên kết và nguồn commit, không thay kết quả cũ.

## Kết quả lần bổ sung hồ sơ

Đã đọc commit/file, parse test declarations và liên kết evidence; không chạy lại runtime test hoặc đo KPI. Không nhận đây là review code độc lập hay approval.
