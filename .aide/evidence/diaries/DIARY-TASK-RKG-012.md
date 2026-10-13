---
key: DIARY-TASK-RKG-012
type: implementation-diary
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-012
revision: 5
implementation_window:
  from: '2026-09-25'
  through: '2026-09-25'
provenance: reconstructed-from-committed-diff-and-prior-evidence
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  implementation_commits:
  - 50eacb32b975117c149153fc932418bf2a7522de
prior_evidence:
- evidence/context/CTX-TASK-RKG-012.yaml
- evidence/diaries/DIARY-TASK-RKG-012.md
- evidence/plans/PLAN-TASK-RKG-012.md
- evidence/tests/TEST-RKG-CONFIG.md
- evidence/tests/TEST-RKG-HTTP-INVENTORY.md
revision_history:
- revision: 1
  metadata:
    key: DIARY-TASK-RKG-012
    type: implementation-diary
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-012
    revision: 1
    captured_at: 2026-09-25
    captured_against:
      artifacts:
      - key: TASK-RKG-012
        revision: 3
      - key: FR-RKG-002
        revision: 8
      - key: REG-ADAPTER-001
        revision: 3
      base_commit: d5bb973059bd4cac078a76c29bad8929f262efd2
      code_tree: working-tree-file-hashes-below
  record: '# DIARY-TASK-RKG-012 — Configuration keys and HTTP origins


    The Python adapter now reads literal environment keys (`os.environ`, `os.getenv`)

    and fields of classes that explicitly subclass `BaseSettings`. Each key is a

    `Configuration` entity. A callable or module that reads it gets a `depends_on`

    edge. Outbound `requests` / `httpx` calls with an absolute `http` or `https`

    literal become one `http_service` external dependency per scheme/host/port.

    Default ports are folded together. Userinfo, path, query and payload stay out

    of the entity.


    Dynamic keys, dynamic URLs, local modules that shadow `os` or `requests`, and

    ambiguous client bindings do not produce a guessed fact. The first two emit a

    path/line diagnostic with a fixed message. Class `inherits_from` and

    `implements` edges are still produced only for explicit local bases and

    declared abstractions.


    The published `rkg.python` capability list is unchanged. Configuration and HTTP

    facts are extra output of that language adapter. `REG-ADAPTER-001` revision 3

    declares the patterns on `rkg.python` and does not add a separate configuration

    adapter.


    ## Checked files


    | File | SHA-256 |

    | --- | --- |

    | `src/rkg/adapters/python_config.py` | `c3876a9e8c3971fcb70596242e641b2502ef64bcc50c416c803f263c561668ae`
    |

    | `src/rkg/adapters/python_language.py` | `38d6d770173a284f7b5c54aaffea0dc04cda38ff743e1f4be2fad82aff4258f6`
    |

    | `tests/conformance/test_python_config.py` | `0d941d8ac5cf0e163709f062ca94e5ee21887829766fc3e8bfdc12027f5d53bc`
    |

    | `tests/integration/test_config_http_publish.py` | `87e5f4d4867e3f923502b379ff5070eb72ea9ad11bff6bf567f3af674380f48f`
    |


    Verification and limits are recorded in `TEST-RKG-CONFIG` and

    `TEST-RKG-HTTP-INVENTORY`.'
---

# DIARY-TASK-RKG-012

The Python adapter now reads literal environment keys (`os.environ`, `os.getenv`)
and fields of classes that explicitly subclass `BaseSettings`. Each key is a
`Configuration` entity. A callable or module that reads it gets a `depends_on`
edge. Outbound `requests` / `httpx` calls with an absolute `http` or `https`
literal become one `http_service` external dependency per scheme/host/port.
Default ports are folded together. Userinfo, path, query and payload stay out
of the entity.

Dynamic keys, dynamic URLs, local modules that shadow `os` or `requests`, and
ambiguous client bindings do not produce a guessed fact. The first two emit a
path/line diagnostic with a fixed message. Class `inherits_from` and
`implements` edges are still produced only for explicit local bases and
declared abstractions.

The published `rkg.python` capability list is unchanged. Configuration and HTTP
facts are extra output of that language adapter. `REG-ADAPTER-001` revision 3
declares the patterns on `rkg.python` and does not add a separate configuration
adapter.

## Checked files

| File | SHA-256 |
| --- | --- |
| `src/rkg/adapters/python_config.py` | `c3876a9e8c3971fcb70596242e641b2502ef64bcc50c416c803f263c561668ae` |
| `src/rkg/adapters/python_language.py` | `38d6d770173a284f7b5c54aaffea0dc04cda38ff743e1f4be2fad82aff4258f6` |
| `tests/conformance/test_python_config.py` | `0d941d8ac5cf0e163709f062ca94e5ee21887829766fc3e8bfdc12027f5d53bc` |
| `tests/integration/test_config_http_publish.py` | `87e5f4d4867e3f923502b379ff5070eb72ea9ad11bff6bf567f3af674380f48f` |

Verification and limits are recorded in `TEST-RKG-CONFIG` and
`TEST-RKG-HTTP-INVENTORY`.

## Đối chiếu commit và phạm vi hiện hành

## Kết quả đối chiếu triển khai

Trích xuất tên config và origin tĩnh cùng usage evidence; không lưu value/secret, endpoint động thành diagnostic.

Các file thay đổi được xác định bằng Git diff của các commit được pin trong frontmatter. Current-tree hash nằm trong context revision 3; khác hash lịch sử là revision về sau, không phải cùng lần chạy.

## Diễn giải và correction

Hành vi và các lần kiểm đã ghi trong prior evidence giữ nguyên; bản này bổ sung liên kết và nguồn commit, không thay kết quả cũ.

## Kết quả lần bổ sung hồ sơ

Đã đọc commit/file, parse test declarations và liên kết evidence; không chạy lại runtime test hoặc đo KPI. Không nhận đây là review code độc lập hay approval.
