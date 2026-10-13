---
key: DIARY-TASK-RKG-013
type: implementation-diary
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-013
revision: 5
implementation_window:
  from: '2026-09-24'
  through: '2026-09-24'
provenance: reconstructed-from-committed-diff-and-prior-evidence
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  implementation_commits:
  - 348ee6154975b4971d61c4c698e37cfd9c36ff29
prior_evidence:
- evidence/context/CTX-TASK-RKG-013.yaml
- evidence/diaries/DIARY-TASK-RKG-013.md
- evidence/plans/PLAN-TASK-RKG-013.md
- evidence/tests/TEST-RKG-STORAGE-SNAPSHOTS-001.md
revision_history:
- revision: 1
  metadata:
    key: DIARY-TASK-RKG-013
    type: implementation-diary
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-013
    revision: 1
    captured_at: 2026-09-24
    captured_against:
      artifacts:
      - key: TASK-RKG-013
        revision: 3
      - key: TBL-RKG-GRAPH
        revision: 9
      - key: DDL-RKG-GRAPH
        path: .aide/tech-specs/RKG-GRAPH/schema/DDL-RKG-GRAPH.cypher
      - key: CMP-RKG-GRAPH
        revision: 4
      - key: ADR-2026-002
        revision: 2
      - key: FR-RKG-001
        revision: 11
      - key: FR-RKG-002
        revision: 8
      - key: API-RKG-CORE-v1
        revision: 9
      base_commit: 5a3f36f86a0eea37e6c490ba567bf58f75e71737
      code_tree: working-tree-file-hashes-below
      pins:
        cpython: 3.12.14
        kuzu: 0.11.3
  record: "# DIARY-TASK-RKG-013 — Kùzu storage and atomic snapshots\n\n## Thực hiện\n\n- Quyết định 1A:\
    \ thêm `SchemaMeta` vào DDL; `migrate()` versioned trong DB; upgrade\n  từ fixture v0 (không SchemaMeta,\
    \ `DEPENDS_ON` Entity→Entity) giữ quan hệ, không\n  drop user DB.\n- Quyết định 2A: `DEPENDS_ON` multi-FROM\
    \ `Repository|Entity → Entity` (Kùzu 0.11.3\n  chấp nhận; cùng pattern EXPOSES).\n- Quyết định 3A:\
    \ Job + Conversation helpers đủ guard/test; active reader =\n  `ReaderRegistry` in-process (single\
    \ worker).\n- `src/rkg/storage/`: connection façade, migrate/bootstrap, repository optimistic\n  revision,\
    \ snapshot/job/conversation helpers, reader pins, error codes khớp\n  API-RKG-CORE-v1.\n- `src/rkg/graph/`:\
    \ `publish_fact_batch` gọi `validate_fact_batch` rồi atomic write +\n  auto-activate; activate/delete\
    \ snapshot với ownership/reference guards.\n- Physical Entity/ExternalDependency PK = `{snapshot_id}:{domain_id}`\
    \ để giữ nhiều\n  snapshot với domain ID ổn định (ghi chú trong TBL revision 9); API vẫn dùng\n  domain\
    \ ID (encode/decode ở storage boundary).\n- Handoff T-015: `src/rkg/storage/README.md`, `src/rkg/graph/README.md`.\n\
    \n## Kiểm chứng trên cây mã hiện tại\n\n| Lệnh | Kết quả |\n| --- | --- |\n| `uv run pytest tests/\
    \ -q` | pass — 21 tests |\n| `uv run ruff check src tests` | pass — All checks passed |\n\nSHA-256\
    \ của file đã kiểm chứng:\n\n| File | SHA-256 |\n| --- | --- |\n| `src/rkg/storage/__init__.py` |\
    \ `081afa224d2a1252f2760c5496a5cae727a58880cb1cacec9c6e9ac32360e438` |\n| `src/rkg/storage/README.md`\
    \ | `e90113b2c4932706fb3e60fb751540ab82458af0b0503ebc8236f7122b6d85d9` |\n| `src/rkg/storage/_util.py`\
    \ | `9ab04e4909dffe5ee8f2c4e6eb0916ab800b2419d76f09b0c50bf245095a0e7e` |\n| `src/rkg/storage/connection.py`\
    \ | `b731e44044e4b6d280c4719664143184ef48adc9eae861aecda653e88925b56c` |\n| `src/rkg/storage/conversations.py`\
    \ | `04ae7a9bd1facbb6468aec53572536d59cda754e40f7153097edde63d1d6a1ad` |\n| `src/rkg/storage/errors.py`\
    \ | `9f171cd78712e8a6f51ef324db8d26a93563075ef73670a8df407d6747a27ce1` |\n| `src/rkg/storage/jobs.py`\
    \ | `5c6a1e75cf6fcb2eaf61e26752acb08d158e911ce6f9d5292d95b0c587f03d04` |\n| `src/rkg/storage/migrate.py`\
    \ | `bbad3e1f4b6195537b79efa7f8557fdcdf430ac54b04b18927762685984b1832` |\n| `src/rkg/storage/readers.py`\
    \ | `0843b87b636c4eba3d7941da132cf5b7059b300f6db23de2b634895c5d465521` |\n| `src/rkg/storage/records.py`\
    \ | `b7b46451b93ca10e4b4d989b32f2bbbebcf949e657b38661ee198efa0c6aafcd` |\n| `src/rkg/storage/repositories.py`\
    \ | `a0c1b859ed3a212f5c275d93cce3c0823c62d394eb13b013a24e9920eab12025` |\n| `src/rkg/storage/snapshots.py`\
    \ | `0c9ba62cd49f7522cf2858380f3d15ab4ad0e75fc4dd66471c3ac636e3277617` |\n| `src/rkg/storage/fixtures/ddl_v0.cypher`\
    \ | `d1e591115ed14bade9de5ba3debad5cda751a2423e4e70f20960abc03ddaa4f0` |\n| `src/rkg/graph/__init__.py`\
    \ | `3116f4e312114e86d26f8bda8ace60b440dc1ae0a1630dfe3c8f1aa315b48f58` |\n| `src/rkg/graph/README.md`\
    \ | `fa8fb617ec3d7697efacaf046e176dd34741b2a15fdb307469e837ca5acf290c` |\n| `src/rkg/graph/ids.py`\
    \ | `386d51157127f6255aee6943b56fad304f0c1ae75d224a4c42a8215dab9b3276` |\n| `src/rkg/graph/publish.py`\
    \ | `00f38b3967be0d573f03834fb6c4ba50709e168a6bed557cef90c66558a189b8` |\n| `tests/integration/test_schema_migrate.py`\
    \ | `fba110b7175e30388a57175f47c813d574ad267a3f5a44af88e82ff0ccd3d436` |\n| `tests/integration/test_storage_lifecycle.py`\
    \ | `f16a16dcdfb52cd8290bcb7cca218e25902c5d7bedfcef2510f4c48bfb316c3e` |\n| `tests/integration/storage_helpers.py`\
    \ | `ba572843efda96b70ef52de44e03cf57f12768d767f544684e60efe24d234abd` |\n| `.aide/tech-specs/RKG-GRAPH/schema/DDL-RKG-GRAPH.cypher`\
    \ | `789127c880117c9d94cc405cf20f1a68a3e9622a8cbbed1aefb1eadea321dc88` |\n| `.aide/tech-specs/RKG-GRAPH/schema/TBL-RKG-GRAPH.md`\
    \ | `aea91e156e936e1f8445d21a9e30d5bbd3713b343a5163254c8dcf759130edec` |\n\n## Giới hạn phạm vi\n\n\
    Storage-layer verification của AC-RKG-007/008/066…071 (plus ownership → not_found).\nKhông gồm FastAPI/HTTP\
    \ (T-016), search/traversal đầy đủ (T-014), hay analyzer\n(T-003+). Conversation/Turn persistence\
    \ đầy đủ thuộc T-018."
---

# DIARY-TASK-RKG-013

## Thực hiện

- Quyết định 1A: thêm `SchemaMeta` vào DDL; `migrate()` versioned trong DB; upgrade
  từ fixture v0 (không SchemaMeta, `DEPENDS_ON` Entity→Entity) giữ quan hệ, không
  drop user DB.
- Quyết định 2A: `DEPENDS_ON` multi-FROM `Repository|Entity → Entity` (Kùzu 0.11.3
  chấp nhận; cùng pattern EXPOSES).
- Quyết định 3A: Job + Conversation helpers đủ guard/test; active reader =
  `ReaderRegistry` in-process (single worker).
- `src/rkg/storage/`: connection façade, migrate/bootstrap, repository optimistic
  revision, snapshot/job/conversation helpers, reader pins, error codes khớp
  API-RKG-CORE-v1.
- `src/rkg/graph/`: `publish_fact_batch` gọi `validate_fact_batch` rồi atomic write +
  auto-activate; activate/delete snapshot với ownership/reference guards.
- Physical Entity/ExternalDependency PK = `{snapshot_id}:{domain_id}` để giữ nhiều
  snapshot với domain ID ổn định (ghi chú trong TBL revision 9); API vẫn dùng
  domain ID (encode/decode ở storage boundary).
- Handoff T-015: `src/rkg/storage/README.md`, `src/rkg/graph/README.md`.

## Kiểm chứng trên cây mã hiện tại

| Lệnh | Kết quả |
| --- | --- |
| `uv run pytest tests/ -q` | pass — 21 tests |
| `uv run ruff check src tests` | pass — All checks passed |

SHA-256 của file đã kiểm chứng:

| File | SHA-256 |
| --- | --- |
| `src/rkg/storage/__init__.py` | `081afa224d2a1252f2760c5496a5cae727a58880cb1cacec9c6e9ac32360e438` |
| `src/rkg/storage/README.md` | `e90113b2c4932706fb3e60fb751540ab82458af0b0503ebc8236f7122b6d85d9` |
| `src/rkg/storage/_util.py` | `9ab04e4909dffe5ee8f2c4e6eb0916ab800b2419d76f09b0c50bf245095a0e7e` |
| `src/rkg/storage/connection.py` | `b731e44044e4b6d280c4719664143184ef48adc9eae861aecda653e88925b56c` |
| `src/rkg/storage/conversations.py` | `04ae7a9bd1facbb6468aec53572536d59cda754e40f7153097edde63d1d6a1ad` |
| `src/rkg/storage/errors.py` | `9f171cd78712e8a6f51ef324db8d26a93563075ef73670a8df407d6747a27ce1` |
| `src/rkg/storage/jobs.py` | `5c6a1e75cf6fcb2eaf61e26752acb08d158e911ce6f9d5292d95b0c587f03d04` |
| `src/rkg/storage/migrate.py` | `bbad3e1f4b6195537b79efa7f8557fdcdf430ac54b04b18927762685984b1832` |
| `src/rkg/storage/readers.py` | `0843b87b636c4eba3d7941da132cf5b7059b300f6db23de2b634895c5d465521` |
| `src/rkg/storage/records.py` | `b7b46451b93ca10e4b4d989b32f2bbbebcf949e657b38661ee198efa0c6aafcd` |
| `src/rkg/storage/repositories.py` | `a0c1b859ed3a212f5c275d93cce3c0823c62d394eb13b013a24e9920eab12025` |
| `src/rkg/storage/snapshots.py` | `0c9ba62cd49f7522cf2858380f3d15ab4ad0e75fc4dd66471c3ac636e3277617` |
| `src/rkg/storage/fixtures/ddl_v0.cypher` | `d1e591115ed14bade9de5ba3debad5cda751a2423e4e70f20960abc03ddaa4f0` |
| `src/rkg/graph/__init__.py` | `3116f4e312114e86d26f8bda8ace60b440dc1ae0a1630dfe3c8f1aa315b48f58` |
| `src/rkg/graph/README.md` | `fa8fb617ec3d7697efacaf046e176dd34741b2a15fdb307469e837ca5acf290c` |
| `src/rkg/graph/ids.py` | `386d51157127f6255aee6943b56fad304f0c1ae75d224a4c42a8215dab9b3276` |
| `src/rkg/graph/publish.py` | `00f38b3967be0d573f03834fb6c4ba50709e168a6bed557cef90c66558a189b8` |
| `tests/integration/test_schema_migrate.py` | `fba110b7175e30388a57175f47c813d574ad267a3f5a44af88e82ff0ccd3d436` |
| `tests/integration/test_storage_lifecycle.py` | `f16a16dcdfb52cd8290bcb7cca218e25902c5d7bedfcef2510f4c48bfb316c3e` |
| `tests/integration/storage_helpers.py` | `ba572843efda96b70ef52de44e03cf57f12768d767f544684e60efe24d234abd` |
| `.aide/tech-specs/RKG-GRAPH/schema/DDL-RKG-GRAPH.cypher` | `789127c880117c9d94cc405cf20f1a68a3e9622a8cbbed1aefb1eadea321dc88` |
| `.aide/tech-specs/RKG-GRAPH/schema/TBL-RKG-GRAPH.md` | `aea91e156e936e1f8445d21a9e30d5bbd3713b343a5163254c8dcf759130edec` |

## Giới hạn phạm vi

Storage-layer verification của AC-RKG-007/008/066…071 (plus ownership → not_found).
Không gồm FastAPI/HTTP (T-016), search/traversal đầy đủ (T-014), hay analyzer
(T-003+). Conversation/Turn persistence đầy đủ thuộc T-018.

## Đối chiếu commit và phạm vi hiện hành

## Kết quả đối chiếu triển khai

Thực thi DDL, tạo storage facade và migration; publish/activate/delete atomic, single writer, immutable snapshot, reader/conversation pin và rollback guards.

Các file thay đổi được xác định bằng Git diff của các commit được pin trong frontmatter. Current-tree hash nằm trong context revision 3; khác hash lịch sử là revision về sau, không phải cùng lần chạy.

## Diễn giải và correction

Hành vi và các lần kiểm đã ghi trong prior evidence giữ nguyên; bản này bổ sung liên kết và nguồn commit, không thay kết quả cũ.

## Kết quả lần bổ sung hồ sơ

Đã đọc commit/file, parse test declarations và liên kết evidence; không chạy lại runtime test hoặc đo KPI. Không nhận đây là review code độc lập hay approval.
