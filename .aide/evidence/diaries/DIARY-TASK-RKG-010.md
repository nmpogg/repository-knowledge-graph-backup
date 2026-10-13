---
key: DIARY-TASK-RKG-010
type: implementation-diary
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-010
revision: 5
implementation_window:
  from: '2026-09-25'
  through: '2026-09-25'
provenance: reconstructed-from-committed-diff-and-prior-evidence
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  implementation_commits:
  - 66680533506fa6b3ab4812ac1ed4a59c8f89a44a
prior_evidence:
- evidence/context/CTX-TASK-RKG-010.yaml
- evidence/diaries/DIARY-TASK-RKG-010.md
- evidence/plans/PLAN-TASK-RKG-010.md
- evidence/tests/TEST-RKG-SQLALCHEMY-ADAPTER-001.md
revision_history:
- revision: 2
  metadata:
    key: DIARY-TASK-RKG-010
    type: implementation-diary
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-010
    revision: 2
    captured_at: 2026-09-25
    captured_against:
      artifacts:
      - key: TASK-RKG-010
        revision: 5
      - key: FR-RKG-002
        revision: 8
      - key: REG-ADAPTER-001
        revision: 5
      - key: NFR-RKG-EXT-001
        revision: 3
      base_commit: 66680533506fa6b3ab4812ac1ed4a59c8f89a44a
      code_tree: working-tree-file-hashes-below
  record: '# DIARY-TASK-RKG-010 — SQLAlchemy 2.x data-access adapter


    `SQLAlchemyDataAccessAdapter` reads Python units already parsed by the language

    adapter. It does not import analyzed code. A class is mapped only when it

    inherits `DeclarativeBase` or a module-level `declarative_base()` result and

    declares a literal `__tablename__`. Schema comes from a literal `__table_args__`

    schema, or is empty when that declaration is absent. DataResource identity is

    repository, resource kind `table`, that namespace, and adapter identity

    `rkg.sqlalchemy` plus the table name. Same namespace and table share one

    resource and can carry several `maps_to` edges. A different namespace does not

    merge.


    Executed `session.get`, `select` passed to `execute`/`scalars`/`scalar`, and

    executed `insert`/`update`/`delete` become `reads` or `writes` from the owning

    callable. `session.add` and `session.delete` do the same for an instance whose

    model resolves from a constructor, a single annotation, or `self`/`cls` on a

    mapped class. The operation name is the versioned evidence rule

    `RKG.sqlalchemy.<operation>.v1`. A declared `select`/`insert`/`update`/`delete`

    that is not executed does not create `reads` or `writes`. Reflection, dynamic

    names and a local module named `sqlalchemy` produce no guessed edge.


    The adapter sets `entrypoint_required = False` and a SQLAlchemy 2.x version

    constraint. T-015 should register `SQLAlchemyDataAccessAdapter` with the other

    deep adapters. A verified 2.x lock is required before selection reports

    `supported_patterns`. A lock outside `>=2.0,<3.0` stays `unsupported_version`.


    An unresolved model on executed `get`, `add` or `delete`, and an executed SQL

    statement whose model does not resolve, emit `sqlalchemy_model_unresolved` and

    no edge. String or other constants passed to those methods stay silent. Multiple

    writes from one callable to one resource keep one edge. The edge rule is the

    lexicographically smallest operation rule; each operation remains on evidence.


    ## Checked files


    | File | SHA-256 |

    | --- | --- |

    | `src/rkg/adapters/sqlalchemy_data.py` | `0219bcda3b250a5e0fa313b5bdd30e78b2dbbd0a46fe6b8fe0c2944d7b156d77`
    |

    | `src/rkg/adapters/__init__.py` | `99a87dcb812e4b4d2140fb029106966884e25c5b0246482fbaed4ed09112cf9b`
    |

    | `tests/conformance/test_sqlalchemy_data.py` | `7de87bae0d06ea86a02d5e65c77a1f0524411628e4c48f193bb6e7cedcb3da0f`
    |

    | `.aide/registry/REG-ADAPTER-001.md` | `21d922ecc4abaa96644c25a039d9d8ec3c594dd2d9d71b9d63851a32a2c0bd62`
    |

    | `src/rkg/detection/README.md` | `f8a97a20c49d2ec1292a9f82da465a8cdf0b25736acef7410378ea644ca42a19`
    |

    | `pyproject.toml` | `cc7e4c68ab699226e29fd9c6ad7f074a128af719bd63c0fd1827c261d64c3ea6` |


    Verification and AC mapping are recorded in `TEST-RKG-SQLALCHEMY-ADAPTER-001`.'
---

# DIARY-TASK-RKG-010

`SQLAlchemyDataAccessAdapter` reads Python units already parsed by the language
adapter. It does not import analyzed code. A class is mapped only when it
inherits `DeclarativeBase` or a module-level `declarative_base()` result and
declares a literal `__tablename__`. Schema comes from a literal `__table_args__`
schema, or is empty when that declaration is absent. DataResource identity is
repository, resource kind `table`, that namespace, and adapter identity
`rkg.sqlalchemy` plus the table name. Same namespace and table share one
resource and can carry several `maps_to` edges. A different namespace does not
merge.

Executed `session.get`, `select` passed to `execute`/`scalars`/`scalar`, and
executed `insert`/`update`/`delete` become `reads` or `writes` from the owning
callable. `session.add` and `session.delete` do the same for an instance whose
model resolves from a constructor, a single annotation, or `self`/`cls` on a
mapped class. The operation name is the versioned evidence rule
`RKG.sqlalchemy.<operation>.v1`. A declared `select`/`insert`/`update`/`delete`
that is not executed does not create `reads` or `writes`. Reflection, dynamic
names and a local module named `sqlalchemy` produce no guessed edge.

The adapter sets `entrypoint_required = False` and a SQLAlchemy 2.x version
constraint. T-015 should register `SQLAlchemyDataAccessAdapter` with the other
deep adapters. A verified 2.x lock is required before selection reports
`supported_patterns`. A lock outside `>=2.0,<3.0` stays `unsupported_version`.

An unresolved model on executed `get`, `add` or `delete`, and an executed SQL
statement whose model does not resolve, emit `sqlalchemy_model_unresolved` and
no edge. String or other constants passed to those methods stay silent. Multiple
writes from one callable to one resource keep one edge. The edge rule is the
lexicographically smallest operation rule; each operation remains on evidence.

## Checked files

| File | SHA-256 |
| --- | --- |
| `src/rkg/adapters/sqlalchemy_data.py` | `0219bcda3b250a5e0fa313b5bdd30e78b2dbbd0a46fe6b8fe0c2944d7b156d77` |
| `src/rkg/adapters/__init__.py` | `99a87dcb812e4b4d2140fb029106966884e25c5b0246482fbaed4ed09112cf9b` |
| `tests/conformance/test_sqlalchemy_data.py` | `7de87bae0d06ea86a02d5e65c77a1f0524411628e4c48f193bb6e7cedcb3da0f` |
| `.aide/registry/REG-ADAPTER-001.md` | `21d922ecc4abaa96644c25a039d9d8ec3c594dd2d9d71b9d63851a32a2c0bd62` |
| `src/rkg/detection/README.md` | `f8a97a20c49d2ec1292a9f82da465a8cdf0b25736acef7410378ea644ca42a19` |
| `pyproject.toml` | `cc7e4c68ab699226e29fd9c6ad7f074a128af719bd63c0fd1827c261d64c3ea6` |

Verification and AC mapping are recorded in `TEST-RKG-SQLALCHEMY-ADAPTER-001`.

## Đối chiếu commit và phạm vi hiện hành

## Kết quả đối chiếu triển khai

Trích xuất table/model map, executed read/write và evidence; phân biệt cấu hình biểu thức với truy cập được thực thi và tránh fan-out suy đoán.

Các file thay đổi được xác định bằng Git diff của các commit được pin trong frontmatter. Current-tree hash nằm trong context revision 3; khác hash lịch sử là revision về sau, không phải cùng lần chạy.

## Diễn giải và correction

Hành vi và các lần kiểm đã ghi trong prior evidence giữ nguyên; bản này bổ sung liên kết và nguồn commit, không thay kết quả cũ.

## Kết quả lần bổ sung hồ sơ

Đã đọc commit/file, parse test declarations và liên kết evidence; không chạy lại runtime test hoặc đo KPI. Không nhận đây là review code độc lập hay approval.
