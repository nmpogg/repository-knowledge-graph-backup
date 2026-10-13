---
key: DIARY-TASK-RKG-020
type: implementation-diary
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-020
revision: 5
implementation_window:
  from: '2026-09-28'
  through: '2026-09-28'
provenance: reconstructed-from-committed-diff-and-prior-evidence
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  implementation_commits:
  - 1f4b7475dd3bd6c8b1dd58cb561cdeea6d89718b
  - 249684a6d6a069008c90d4553ff6ee6ee9e9b922
prior_evidence:
- evidence/context/CTX-TASK-RKG-020.yaml
- evidence/diaries/DIARY-TASK-RKG-020.md
- evidence/diaries/DIARY-TASK-RKG-020.md
- evidence/plans/PLAN-TASK-RKG-020.md
- evidence/tests/TEST-RKG-GROUNDED-QA-001.md
- evidence/tests/TEST-RKG-GROUNDED-QA-002.md
revision_history:
- revision: 1
  metadata:
    key: DIARY-TASK-RKG-020
    type: implementation-diary
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-020
    revision: 1
    captured_at: 2026-09-28
    captured_against:
      artifacts:
      - key: TASK-RKG-020
        revision: 6
      - key: TASK-RKG-018
        revision: 5
      - key: TASK-RKG-019
        revision: 7
      - key: FR-RKG-005
        revision: 7
      - key: NFR-RKG-REL-001
        revision: 8
      - key: CMP-RKG-CONVERSATION
        revision: 3
      base_commit: 32b787516d081abfecfd2880205f9a693767f935
      code_tree: working-tree-file-hashes-below
      branch: feat/task-rkg-020-grounded-qa
  record: "# DIARY-TASK-RKG-020 — History-aware grounded Q&A\n\n## Entry conditions\n\nTasks 18 and 19\
    \ were `done` with current-tree evidence. Their implementations\nwere merged into `dev`; the working\
    \ tree was clean before branching.\n\n## Implementation\n\n- `submit_grounded_turn` runs behind the\
    \ existing pending/finalize transaction\n  boundary. It keeps at most six completed turns and 4,000\
    \ history tokens,\n  dropping oldest turns while retaining structured focus and pending candidates.\n\
    - An explicit root, ordered candidate or unambiguous pronoun follow-up resolves\n  deterministically.\
    \ Otherwise a JSON Schema plan can select only a bounded\n  search, existing focus/candidate or insufficient\
    \ evidence. Graph access is\n  restricted to pinned `get_entity`, `search_entities` and `build_context`.\n\
    - Synthesis selects edge IDs from the bounded context. The service validates\n  each selected ID and\
    \ evidence against that context and renders relation text\n  from graph facts, preserving direction.\
    \ A model-supplied free-form relation\n  claim cannot become an answer or graph fact.\n- The shared\
    \ per-turn budget from T-019 caps model calls, graph operations,\n  output tokens and elapsed time.\
    \ Stable `llm_*` failures finalize without\n  changing committed focus; question validation occurs\
    \ before provider calls.\n- `GroundedTurn` exposes history/retrieval truncation and limitations for\
    \ the\n  later HTTP layer. HTTP routes/status mapping remain T-021; pilot-scale eval\n  remains T-022.\n\
    \n## Verification\n\n| Check | Result |\n| --- | --- |\n| `.venv/Scripts/python.exe -m pytest tests/\
    \ -q` without key loaded | 126 passed, 4 skipped |\n| Full suite with key/model loaded from ignored\
    \ local `.env` | 129 passed, 1 skipped |\n| `.venv/Scripts/ruff.exe check src tests` | pass |\n| `git\
    \ diff --check` | pass |\n\nThe two new live tests include a follow-up and DB/event/dependency/technology\n\
    relations. The one remaining skip belongs to the existing suite. The live\nrun used a workspace-local\
    \ pytest temporary directory because the elevated\nprocess could not access its system Temp path.\
    \ No credential or response body\nwas recorded. See `TEST-RKG-GROUNDED-QA-001`.\n\n## SHA-256 of verified\
    \ files\n\n| File | SHA-256 |\n| --- | --- |\n| `.aide/lifecycle/tasks/TASK-RKG-020.md` | `bf6bdf2b811c15f0206d28bf79452ce429cbf3e3ff461008b90d5aff045e518a`\
    \ |\n| `src/rkg/conversations/grounded.py` | `3cb942bf2c22e91f705f257820b0355332b777f4d0da11e0649766d302b24b9c`\
    \ |\n| `src/rkg/conversations/service.py` | `3470ca303f9da1b2b3f38d73c3b7bd0a9979d695176bf6b6819d70eb03ea9bc4`\
    \ |\n| `src/rkg/conversations/__init__.py` | `7ab91f2b421be50fb1dd1c01ed9cd35f91d8ff3b65faed258a7a48b3b5c03e84`\
    \ |\n| `src/rkg/conversations/README.md` | `4c6bcc3ba5b18193b53dbde7dcbec571424ccf2472478ce462114cdc73e2816a`\
    \ |\n| `tests/integration/graph_helpers.py` | `de97841533bcc5b5d15258fc974a9422ea2b21c656c77b1c787b3e67a2ad2649`\
    \ |\n| `tests/integration/test_grounded_qa.py` | `1507f3385ca2d32ffafdeb91fd9294b3c2acb89fd77355de4553bb58dfa5446d`\
    \ |\n| `tests/integration/test_grounded_qa_live.py` | `b94d0c5043acec7a61148ccf1779c6dbd7540d0cc67a0d9766fcdf5281560514`\
    \ |"
- revision: 2
  metadata:
    key: DIARY-TASK-RKG-020-r2
    type: implementation-diary
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-020
    revision: 2
    captured_at: 2026-09-28
    captured_against:
      artifacts:
      - key: TASK-RKG-020
        revision: 7
      - key: FR-RKG-005
        revision: 7
      - key: NFR-RKG-REL-001
        revision: 8
      base_commit: 32b787516d081abfecfd2880205f9a693767f935
      code_tree: working-tree-file-hashes-below
      branch: feat/task-rkg-020-grounded-qa
---

# DIARY-TASK-RKG-020

## Entry conditions

Tasks 18 and 19 were `done` with current-tree evidence. Their implementations
were merged into `dev`; the working tree was clean before branching.

## Implementation

- `submit_grounded_turn` runs behind the existing pending/finalize transaction
  boundary. It keeps at most six completed turns and 4,000 history tokens,
  dropping oldest turns while retaining structured focus and pending candidates.
- An explicit root, ordered candidate or unambiguous pronoun follow-up resolves
  deterministically. Otherwise a JSON Schema plan can select only a bounded
  search, existing focus/candidate or insufficient evidence. Graph access is
  restricted to pinned `get_entity`, `search_entities` and `build_context`.
- Synthesis selects edge IDs from the bounded context. The service validates
  each selected ID and evidence against that context and renders relation text
  from graph facts, preserving direction. A model-supplied free-form relation
  claim cannot become an answer or graph fact.
- The shared per-turn budget from T-019 caps model calls, graph operations,
  output tokens and elapsed time. Stable `llm_*` failures finalize without
  changing committed focus; question validation occurs before provider calls.
- `GroundedTurn` exposes history/retrieval truncation and limitations for the
  later HTTP layer. HTTP routes/status mapping remain T-021; pilot-scale eval
  remains T-022.

## Verification

| Check | Result |
| --- | --- |
| `.venv/Scripts/python.exe -m pytest tests/ -q` without key loaded | 126 passed, 4 skipped |
| Full suite with key/model loaded from ignored local `.env` | 129 passed, 1 skipped |
| `.venv/Scripts/ruff.exe check src tests` | pass |
| `git diff --check` | pass |

The two new live tests include a follow-up and DB/event/dependency/technology
relations. The one remaining skip belongs to the existing suite. The live
run used a workspace-local pytest temporary directory because the elevated
process could not access its system Temp path. No credential or response body
was recorded. See `TEST-RKG-GROUNDED-QA-001`.

## SHA-256 of verified files

| File | SHA-256 |
| --- | --- |
| `.aide/lifecycle/tasks/TASK-RKG-020.md` | `bf6bdf2b811c15f0206d28bf79452ce429cbf3e3ff461008b90d5aff045e518a` |
| `src/rkg/conversations/grounded.py` | `3cb942bf2c22e91f705f257820b0355332b777f4d0da11e0649766d302b24b9c` |
| `src/rkg/conversations/service.py` | `3470ca303f9da1b2b3f38d73c3b7bd0a9979d695176bf6b6819d70eb03ea9bc4` |
| `src/rkg/conversations/__init__.py` | `7ab91f2b421be50fb1dd1c01ed9cd35f91d8ff3b65faed258a7a48b3b5c03e84` |
| `src/rkg/conversations/README.md` | `4c6bcc3ba5b18193b53dbde7dcbec571424ccf2472478ce462114cdc73e2816a` |
| `tests/integration/graph_helpers.py` | `de97841533bcc5b5d15258fc974a9422ea2b21c656c77b1c787b3e67a2ad2649` |
| `tests/integration/test_grounded_qa.py` | `1507f3385ca2d32ffafdeb91fd9294b3c2acb89fd77355de4553bb58dfa5446d` |
| `tests/integration/test_grounded_qa_live.py` | `b94d0c5043acec7a61148ccf1779c6dbd7540d0cc67a0d9766fcdf5281560514` |

## Lịch sử revision 2

# DIARY-TASK-RKG-020-r2 — Initial question without root ID

The first live check with an explicit `root_id` passed, but a normal first
question naming `app.cycle.a` returned `insufficient_evidence` when the model
planner was asked to locate the root. The coordinator now extracts a qualified
or underscored entity name from the question and searches for it through the
same pinned, bounded `search_entities` service before asking the model to plan.
The result remains subject to exact-match/ambiguity checks and the shared
graph-query budget. Follow-up pronouns continue to use committed focus.

This corrected path passed live with no `root_id`, then passed a live follow-up.
The synthetic DB/event/dependency/technology live checks also passed.

| Check | Result |
| --- | --- |
| Full `tests/` suite with key/model loaded from ignored local `.env` | 129 passed, 1 skipped |
| `.venv/Scripts/ruff.exe check src tests` | pass |
| `git diff --check` | pass |

The one skip belongs to the existing suite. No credential, prompt, response
body or transcript is included in this evidence. HTTP routes remain T-021;
pilot-scale evaluation remains T-022.

## SHA-256 of current checked files

| File | SHA-256 |
| --- | --- |
| `.aide/lifecycle/tasks/TASK-RKG-020.md` | `f557a98650baa721860963fe48a0602fd224ef3c0d34f9767112565087c1e3f9` |
| `src/rkg/conversations/grounded.py` | `c9c8e8d3452444d4964889521ad74aa429d77032eb6735bb63a089922afa5b83` |
| `src/rkg/conversations/README.md` | `a7ab40d2ef59cc906d8e24b664a388fb8713f525324e1ccc483fe41e7e40a03e` |
| `tests/integration/test_grounded_qa.py` | `522418d6c5f19eeded9b8c1823fd7d21f95ff1d4cd9aa569d543cda7dabe8f03` |
| `tests/integration/test_grounded_qa_live.py` | `939fa9497870f832c6d38a8742759f5c8d19ada3f35187acbbb2896733371c6b` |

Unchanged Task 20 file hashes for `service.py`, `__init__.py` and graph
fixtures remain listed in `DIARY-TASK-RKG-020`.

## Đối chiếu commit và phạm vi hiện hành

## Kết quả đối chiếu triển khai

Điều phối bounded history/focus/clarification, provider planning, read-only retrieval allowlist và citation validation; dùng output budget trong NFR.

Các file thay đổi được xác định bằng Git diff của các commit được pin trong frontmatter. Current-tree hash nằm trong context revision 3; khác hash lịch sử là revision về sau, không phải cùng lần chạy.

## Diễn giải và correction

Hành vi và các lần kiểm đã ghi trong prior evidence giữ nguyên; bản này bổ sung liên kết và nguồn commit, không thay kết quả cũ.

## Kết quả lần bổ sung hồ sơ

Đã đọc commit/file, parse test declarations và liên kết evidence; không chạy lại runtime test hoặc đo KPI. Không nhận đây là review code độc lập hay approval.
