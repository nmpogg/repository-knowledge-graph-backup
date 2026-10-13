---
key: DIARY-TASK-RKG-019
type: implementation-diary
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-019
revision: 5
implementation_window:
  from: '2026-09-28'
  through: '2026-09-28'
provenance: reconstructed-from-committed-diff-and-prior-evidence
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  implementation_commits:
  - ca850045d9b20b7209a5c61ae9044598c41564d4
prior_evidence:
- evidence/context/CTX-TASK-RKG-019.yaml
- evidence/diaries/DIARY-TASK-RKG-019.md
- evidence/diaries/DIARY-TASK-RKG-019.md
- evidence/diaries/DIARY-TASK-RKG-019.md
- evidence/diaries/DIARY-TASK-RKG-019.md
- evidence/plans/PLAN-TASK-RKG-019.md
- evidence/tests/TEST-RKG-LLM-LIMITS.md
- evidence/tests/TEST-RKG-OPENROUTER-LIVE-001.md
- evidence/tests/TEST-RKG-OPENROUTER-LIVE-002.md
- evidence/tests/TEST-RKG-OPENROUTER-MODEL-001.md
revision_history:
- revision: 1
  metadata:
    key: DIARY-TASK-RKG-019
    type: implementation-diary
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-019
    revision: 1
    captured_at: 2026-09-28
    captured_against:
      artifacts:
      - key: TASK-RKG-019
        revision: 5
      - key: OQ-RKG-001
        revision: 3
      - key: FR-RKG-005
        revision: 7
      - key: NFR-RKG-REL-001
        revision: 8
      - key: CMP-RKG-CONVERSATION
        revision: 3
      base_commit: 4ed6103a861a0b29d61e3b9584351482c873c00f
      code_tree: working-tree-file-hashes-below
      branch: feat/task-rkg-019-llm-provider
  record: "# DIARY-TASK-RKG-019 — LLM provider interface and adapter\n\n## Entry conditions\n\n`TASK-RKG-002`\
    \ and `TASK-RKG-014` are `done`, OQ-RKG-001 is `resolved`, and\nthe source tree was clean before branching.\
    \ The branch follows the existing\n`feat/task-rkg-NNN-*` convention.\n\n## Implementation\n\n- `StructuredProvider`,\
    \ `StructuredRequest`, `StructuredResponse`, and\n  `TurnBudget` provide a typed boundary with a shared\
    \ 2-call, 3-query,\n  1,500-output-token-per-call, 30-second ceiling. Input preflight counts\n  `o200k_base`\
    \ tokens; the output is counted and checked again after response.\n- `MockProvider` exercises the\
    \ same preflight and JSON Schema validation as\n  the live adapter.\n- `OpenRouterProvider` uses the\
    \ model from OQ-RKG-001, server environment\n  credential, strict JSON Schema response format, provider\
    \ parameter routing,\n  bounded blocking transport, and optional usage/cost metadata. Safe errors\n\
    \  omit response bodies and raw transport messages.\n- The tokenizer data is bundled, hash checked,\
    \ and included in the wheel so\n  local tests and startup do not download it.\n- Retrieval, history,\
    \ citation checks, and HTTP mapping are owned by T-020/021.\n\n## Current-tree verification\n\n| Check\
    \ | Result |\n| --- | --- |\n| `.venv/Scripts/ruff.exe check src tests` | pass |\n| `.venv/Scripts/python.exe\
    \ -m pytest tests/ -q` | 116 passed, 2 skipped |\n| `uv build --offline --python .venv/Scripts/python.exe\
    \ --wheel` | pass; tokenizer present in wheel |\n| `tests/integration/test_openrouter_live.py` | skipped;\
    \ `OPENROUTER_API_KEY` absent |\n\nThe second skipped test belongs to the existing suite. Live provider\
    \ acceptance\nhas not been claimed; the task remains `in_progress`.\n\n## SHA-256 of verified files\n\
    \n| File | SHA-256 |\n| --- | --- |\n| `src/rkg/llm/provider.py` | `8406df1f68a067032abdf46508c0d4795122425ebee88cb6d0d43b59dd285fde`\
    \ |\n| `src/rkg/llm/openrouter.py` | `bac1c1b026b645e635e93a582dbf46ca7006553d0d4deca65b1abb08bc72270e`\
    \ |\n| `src/rkg/llm/mock.py` | `bdf28c019d5ef7847e45ef447e836a6d1b02242aa38c01df4acf2dc03f76661a`\
    \ |\n| `src/rkg/llm/__init__.py` | `2212265d091a0957b18509e72d6c56627a13a54bb657d46463ef6dbb13b9cbd4`\
    \ |\n| `src/rkg/llm/README.md` | `b8bfe6227c9c762a4e36b3f95918819bc31373993d176ce83e6715d28fe82e3f`\
    \ |\n| `src/rkg/llm/data/o200k_base.tiktoken` | `446a9538cb6c348e3516120d7c08b09f57c36495e2acfffe59a5bf8b0cfb1a2d`\
    \ |\n| `tests/unit/test_llm_provider.py` | `2e458ad027904cef837cc965e5338f58223b5ca90e4ea27bb79ba2b455be722a`\
    \ |\n| `tests/integration/test_openrouter_live.py` | `44bc31ab870e98c046597320f0bf45ba4240da2ff04860d7480618641ffe443c`\
    \ |\n| `pyproject.toml` | `8de81cfd0069726e9602f121c550766ca19ff3f9dcbf1989d0e15f653ef6152c` |\n|\
    \ `uv.lock` | `407bdd6d0a4fd3dd3e84afbd73b9429ab22425383117e25b8586933d0ab7c292` |\n| `.aide/lifecycle/tasks/TASK-RKG-019.md`\
    \ | `98137ea0e922926f539adb67d0a221b9282fe66ebd27a87cb4ebbe323e76801d` |"
- revision: 2
  metadata:
    key: DIARY-TASK-RKG-019-r2
    type: implementation-diary
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-019
    revision: 2
    captured_at: 2026-09-28
    captured_against:
      artifacts:
      - key: TASK-RKG-019
        revision: 6
      - key: OQ-RKG-001
        revision: 3
      - key: FR-RKG-005
        revision: 7
      - key: NFR-RKG-REL-001
        revision: 8
      base_commit: 4ed6103a861a0b29d61e3b9584351482c873c00f
      code_tree: working-tree-file-hashes-below
      branch: feat/task-rkg-019-llm-provider
- revision: 3
  metadata:
    key: DIARY-TASK-RKG-019-r3
    type: implementation-diary
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-019
    revision: 3
    captured_at: 2026-09-28
    captured_against:
      artifacts:
      - key: TASK-RKG-019
        revision: 7
      - key: OQ-RKG-001
        revision: 3
      - key: FR-RKG-005
        revision: 7
      - key: NFR-RKG-REL-001
        revision: 8
      base_commit: 4ed6103a861a0b29d61e3b9584351482c873c00f
      code_tree: working-tree-file-hashes-below
      branch: feat/task-rkg-019-llm-provider
- revision: 4
  metadata:
    key: DIARY-TASK-RKG-019-r4
    type: implementation-diary
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-019
    revision: 4
    captured_at: 2026-09-28
    captured_against:
      artifacts:
      - key: TASK-RKG-019
        revision: 7
      - key: OQ-RKG-001
        revision: 3
      code_commit: ca850045d9b20b7209a5c61ae9044598c41564d4
      branch: feat/task-rkg-019-llm-provider
---

# DIARY-TASK-RKG-019

## Entry conditions

`TASK-RKG-002` and `TASK-RKG-014` are `done`, OQ-RKG-001 is `resolved`, and
the source tree was clean before branching. The branch follows the existing
`feat/task-rkg-NNN-*` convention.

## Implementation

- `StructuredProvider`, `StructuredRequest`, `StructuredResponse`, and
  `TurnBudget` provide a typed boundary with a shared 2-call, 3-query,
  1,500-output-token-per-call, 30-second ceiling. Input preflight counts
  `o200k_base` tokens; the output is counted and checked again after response.
- `MockProvider` exercises the same preflight and JSON Schema validation as
  the live adapter.
- `OpenRouterProvider` uses the model from OQ-RKG-001, server environment
  credential, strict JSON Schema response format, provider parameter routing,
  bounded blocking transport, and optional usage/cost metadata. Safe errors
  omit response bodies and raw transport messages.
- The tokenizer data is bundled, hash checked, and included in the wheel so
  local tests and startup do not download it.
- Retrieval, history, citation checks, and HTTP mapping are owned by T-020/021.

## Current-tree verification

| Check | Result |
| --- | --- |
| `.venv/Scripts/ruff.exe check src tests` | pass |
| `.venv/Scripts/python.exe -m pytest tests/ -q` | 116 passed, 2 skipped |
| `uv build --offline --python .venv/Scripts/python.exe --wheel` | pass; tokenizer present in wheel |
| `tests/integration/test_openrouter_live.py` | skipped; `OPENROUTER_API_KEY` absent |

The second skipped test belongs to the existing suite. Live provider acceptance
has not been claimed; the task remains `in_progress`.

## SHA-256 of verified files

| File | SHA-256 |
| --- | --- |
| `src/rkg/llm/provider.py` | `8406df1f68a067032abdf46508c0d4795122425ebee88cb6d0d43b59dd285fde` |
| `src/rkg/llm/openrouter.py` | `bac1c1b026b645e635e93a582dbf46ca7006553d0d4deca65b1abb08bc72270e` |
| `src/rkg/llm/mock.py` | `bdf28c019d5ef7847e45ef447e836a6d1b02242aa38c01df4acf2dc03f76661a` |
| `src/rkg/llm/__init__.py` | `2212265d091a0957b18509e72d6c56627a13a54bb657d46463ef6dbb13b9cbd4` |
| `src/rkg/llm/README.md` | `b8bfe6227c9c762a4e36b3f95918819bc31373993d176ce83e6715d28fe82e3f` |
| `src/rkg/llm/data/o200k_base.tiktoken` | `446a9538cb6c348e3516120d7c08b09f57c36495e2acfffe59a5bf8b0cfb1a2d` |
| `tests/unit/test_llm_provider.py` | `2e458ad027904cef837cc965e5338f58223b5ca90e4ea27bb79ba2b455be722a` |
| `tests/integration/test_openrouter_live.py` | `44bc31ab870e98c046597320f0bf45ba4240da2ff04860d7480618641ffe443c` |
| `pyproject.toml` | `8de81cfd0069726e9602f121c550766ca19ff3f9dcbf1989d0e15f653ef6152c` |
| `uv.lock` | `407bdd6d0a4fd3dd3e84afbd73b9429ab22425383117e25b8586933d0ab7c292` |
| `.aide/lifecycle/tasks/TASK-RKG-019.md` | `98137ea0e922926f539adb67d0a221b9282fe66ebd27a87cb4ebbe323e76801d` |

## Lịch sử revision 2

# DIARY-TASK-RKG-019-r2 — Live verification

The server-side key was available in a local ignored `.env`. For verification,
only `OPENROUTER_API_KEY` was loaded into the test process environment. The key
value was not printed or included in evidence.

| Check | Result |
| --- | --- |
| Live `tests/integration/test_openrouter_live.py` | 1 passed |
| Full `tests/` suite with live test enabled | 117 passed, 1 skipped |
| `.venv/Scripts/ruff.exe check src tests` | pass |
| `git diff --check` | pass |

The one remaining skip is unrelated to the OpenRouter live test. The suite
uses a workspace-local pytest `--basetemp` when network permission is enabled;
the default system Temp path was inaccessible in that execution context.

Task 19 provider boundary and live adapter are verified. Grounded Q&A
orchestration and HTTP mapping remain assigned to T-020/021, as recorded in
`TEST-RKG-LLM-LIMITS`.

## SHA-256 of current checked files

| File | SHA-256 |
| --- | --- |
| `.aide/lifecycle/tasks/TASK-RKG-019.md` | `a519af1747f78eb746aeb9493dfdd591ee61909b49096b90b02e03245e6b2e50` |
| `.env.example` | `cfccf4002cdf324ae494075b8b866f92f7d1342527d817eaf5dbb45c0535c9e7` |
| `.gitignore` | `d30786e22256c37d0152dfc727b514a29e671998eb74008388583c56deed2816` |
| `src/rkg/llm/provider.py` | `8406df1f68a067032abdf46508c0d4795122425ebee88cb6d0d43b59dd285fde` |
| `src/rkg/llm/openrouter.py` | `bac1c1b026b645e635e93a582dbf46ca7006553d0d4deca65b1abb08bc72270e` |
| `src/rkg/llm/mock.py` | `bdf28c019d5ef7847e45ef447e836a6d1b02242aa38c01df4acf2dc03f76661a` |
| `tests/integration/test_openrouter_live.py` | `44bc31ab870e98c046597320f0bf45ba4240da2ff04860d7480618641ffe443c` |
| `tests/unit/test_llm_provider.py` | `2e458ad027904cef837cc965e5338f58223b5ca90e4ea27bb79ba2b455be722a` |

Unchanged Task 19 source and dependency hashes are listed in
`DIARY-TASK-RKG-019`.

## Lịch sử revision 3

# DIARY-TASK-RKG-019-r3 — Configurable OpenRouter model

`OPENROUTER_MODEL` is now read from the server environment for each call.
Absent or blank values retain the OQ-RKG-001 default model. The actual selected
model is sent in the request and returned in non-sensitive response metadata.
The setting was added to `.env.example` and to the local ignored `.env` without
changing the credential. No actual credential or local `.env` content is in
this evidence.

## Verification

| Check | Result |
| --- | --- |
| `tests/unit/test_llm_provider.py` | 10 passed; includes model override |
| Full `tests/` suite without server key loaded | 117 passed, 2 skipped |
| Live OpenRouter request with key/model from local `.env` | pass |
| `.venv/Scripts/ruff.exe check src tests` | pass |
| `git diff --check` | pass |

An earlier live attempt received a provider HTTP error; a later request with
the same configuration passed. The HTTP status was not captured, so the cause
is unknown. The full regression suite was run separately to avoid network
flakiness; its live test skips when the key is not in the process environment.

## SHA-256 of changed/current checked files

| File | SHA-256 |
| --- | --- |
| `.aide/lifecycle/tasks/TASK-RKG-019.md` | `4eb1538122f88bbc55c047fa6aae6e71b988d89fbdc155c5bdbe4bfdf154d04a` |
| `.env.example` | `4c6d05d77df70b758d12c325aca46ed71620834ad6fa31fe4880d36f81907d3b` |
| `src/rkg/llm/openrouter.py` | `3dd4c8261a847e1b141882aa63a56627b3cfdb1fde171223906a2e4f8c4076d6` |
| `src/rkg/llm/README.md` | `8ec58cf2bad6a6c2ee229dac1fb61071f60784fc5e3a658c9dc629086a726e32` |
| `tests/unit/test_llm_provider.py` | `21fb7a2f802b72b08d031a360fa82979d303e28d1eb0de65384cdeba96539e55` |
| `tests/integration/test_openrouter_live.py` | `44bc31ab870e98c046597320f0bf45ba4240da2ff04860d7480618641ffe443c` |

Other Task 19 file hashes remain listed in `DIARY-TASK-RKG-019` and
`DIARY-TASK-RKG-019-r2`.

## Lịch sử revision 4

# DIARY-TASK-RKG-019-r4 — Code commit and tokenizer integrity

The Task 19 implementation, tests, dependency lock, model configuration
example, and Git tokenizer attribute are committed in
`ca850045d9b20b7209a5c61ae9044598c41564d4`.

The committed `o200k_base.tiktoken` blob is byte-identical to the verified
working-tree file and has SHA-256
`446a9538cb6c348e3516120d7c08b09f57c36495e2acfffe59a5bf8b0cfb1a2d`.
`.gitattributes` sets `-text` for that file so Windows checkout does not
change its bytes. The `.gitattributes` working-tree SHA-256 is
`81090c93a6d39f67bcf84addb6aca07b7d77423f20e22e8895eafe2de89f6665`.

Verification on the committed code tree: full suite with key and model loaded
from the ignored local `.env` passed **118 tests, 1 skipped**
(`TEST-RKG-OPENROUTER-LIVE-002`); Ruff and `git diff --check` passed.
Earlier file hashes and the live-run details are preserved in
`DIARY-TASK-RKG-019-r3` and `TEST-RKG-OPENROUTER-LIVE-002`.

## Đối chiếu commit và phạm vi hiện hành

## Kết quả đối chiếu triển khai

Implement structured provider protocol/mock và OpenRouter adapter với schema/token/timeout budgets; không trả secret cho browser và tách mock khỏi live evidence.

Các file thay đổi được xác định bằng Git diff của các commit được pin trong frontmatter. Current-tree hash nằm trong context revision 3; khác hash lịch sử là revision về sau, không phải cùng lần chạy.

## Diễn giải và correction

Hành vi và các lần kiểm đã ghi trong prior evidence giữ nguyên; bản này bổ sung liên kết và nguồn commit, không thay kết quả cũ.

## Kết quả lần bổ sung hồ sơ

Đã đọc commit/file, parse test declarations và liên kết evidence; không chạy lại runtime test hoặc đo KPI. Không nhận đây là review code độc lập hay approval.
