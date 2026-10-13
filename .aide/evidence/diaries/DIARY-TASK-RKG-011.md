---
key: DIARY-TASK-RKG-011
type: implementation-diary
group: evidence
scope: system
system: SYS-RKG
task_key: TASK-RKG-011
revision: 5
implementation_window:
  from: '2026-09-25'
  through: '2026-09-25'
provenance: reconstructed-from-committed-diff-and-prior-evidence
captured_against:
  code_tree: 3227188ff9c4a71befa0bdc389302f84cc4c606f
  implementation_commits:
  - 8e9882d26a825c906fe880086ab362c7e1d77250
prior_evidence:
- evidence/context/CTX-TASK-RKG-011.yaml
- evidence/diaries/DIARY-TASK-RKG-011.md
- evidence/plans/PLAN-TASK-RKG-011.md
- evidence/tests/TEST-RKG-AIOKAFKA-ADAPTER-001.md
revision_history:
- revision: 2
  metadata:
    key: DIARY-TASK-RKG-011
    type: implementation-diary
    group: evidence
    system: SYS-RKG
    task_key: TASK-RKG-011
    revision: 2
    captured_at: 2026-09-25
    captured_against:
      artifacts:
      - key: TASK-RKG-011
        revision: 5
      - key: FR-RKG-002
        revision: 8
      - key: REG-ADAPTER-001
        revision: 5
      - key: NFR-RKG-EXT-001
        revision: 3
      base_commit: 66680533506fa6b3ab4812ac1ed4a59c8f89a44a
      code_tree: working-tree-file-hashes-below
  record: '# DIARY-TASK-RKG-011 — aiokafka messaging adapter


    `AIOKafkaMessagingAdapter` reads Python units already parsed by the language

    adapter. It does not import analyzed code. A publish, consume or subscribe call

    inside a callable becomes a `publishes` or `consumes` edge only when the receiver

    resolves to `AIOKafkaProducer` or `AIOKafkaConsumer` and every topic is a string

    literal or a unique module constant. MessageChannel identity is repository,

    channel kind `topic`, an empty namespace and the topic name. The supported

    subset has no schema or cluster identity, so bootstrap servers are not stored.

    The same topic name is one channel. A different topic name is another channel.


    `send`, `send_and_wait` and `send_batch` record `RKG.aiokafka.publish.v1`.

    Positional constructor topics record `RKG.aiokafka.consume.v1`. `subscribe`

    without a pattern records `RKG.aiokafka.subscribe.v1`. Dynamic topics, function

    locals, pattern subscriptions and unresolved receivers produce

    `aiokafka_topic_unresolved` and no edge. A recognized call outside a callable

    produces `aiokafka_topic_unscoped` and no edge. A `self` or `cls` client

    attribute is a receiver only when that same attribute is assigned once. Payload

    arguments are not read. A local module named `aiokafka` produces no facts.


    The adapter sets `entrypoint_required = False` and an aiokafka `>=0.8,<1.0`

    version constraint. T-015 should register `AIOKafkaMessagingAdapter` with the

    other deep adapters. A verified lock in that range is required before selection

    reports `supported_patterns`. A lock outside `>=0.8,<1.0` stays

    `unsupported_version`. The registered patterns are in `REG-ADAPTER-001`

    revision 5.


    ## Checked files


    | File | SHA-256 |

    | --- | --- |

    | `src/rkg/adapters/aiokafka_messaging.py` | `ad5594a51506994e864d228f2e1c11f413315167020b35fd9305f0543cbc742a`
    |

    | `src/rkg/adapters/__init__.py` | `99a87dcb812e4b4d2140fb029106966884e25c5b0246482fbaed4ed09112cf9b`
    |

    | `tests/conformance/test_aiokafka_messaging.py` | `be0fce179d2014351c99b6eb295a841620142c0c46c0788d1b29179fe85ca876`
    |

    | `.aide/registry/REG-ADAPTER-001.md` | `21d922ecc4abaa96644c25a039d9d8ec3c594dd2d9d71b9d63851a32a2c0bd62`
    |

    | `src/rkg/detection/README.md` | `f8a97a20c49d2ec1292a9f82da465a8cdf0b25736acef7410378ea644ca42a19`
    |


    Verification and AC mapping are recorded in `TEST-RKG-AIOKAFKA-ADAPTER-001`.'
---

# DIARY-TASK-RKG-011

`AIOKafkaMessagingAdapter` reads Python units already parsed by the language
adapter. It does not import analyzed code. A publish, consume or subscribe call
inside a callable becomes a `publishes` or `consumes` edge only when the receiver
resolves to `AIOKafkaProducer` or `AIOKafkaConsumer` and every topic is a string
literal or a unique module constant. MessageChannel identity is repository,
channel kind `topic`, an empty namespace and the topic name. The supported
subset has no schema or cluster identity, so bootstrap servers are not stored.
The same topic name is one channel. A different topic name is another channel.

`send`, `send_and_wait` and `send_batch` record `RKG.aiokafka.publish.v1`.
Positional constructor topics record `RKG.aiokafka.consume.v1`. `subscribe`
without a pattern records `RKG.aiokafka.subscribe.v1`. Dynamic topics, function
locals, pattern subscriptions and unresolved receivers produce
`aiokafka_topic_unresolved` and no edge. A recognized call outside a callable
produces `aiokafka_topic_unscoped` and no edge. A `self` or `cls` client
attribute is a receiver only when that same attribute is assigned once. Payload
arguments are not read. A local module named `aiokafka` produces no facts.

The adapter sets `entrypoint_required = False` and an aiokafka `>=0.8,<1.0`
version constraint. T-015 should register `AIOKafkaMessagingAdapter` with the
other deep adapters. A verified lock in that range is required before selection
reports `supported_patterns`. A lock outside `>=0.8,<1.0` stays
`unsupported_version`. The registered patterns are in `REG-ADAPTER-001`
revision 5.

## Checked files

| File | SHA-256 |
| --- | --- |
| `src/rkg/adapters/aiokafka_messaging.py` | `ad5594a51506994e864d228f2e1c11f413315167020b35fd9305f0543cbc742a` |
| `src/rkg/adapters/__init__.py` | `99a87dcb812e4b4d2140fb029106966884e25c5b0246482fbaed4ed09112cf9b` |
| `tests/conformance/test_aiokafka_messaging.py` | `be0fce179d2014351c99b6eb295a841620142c0c46c0788d1b29179fe85ca876` |
| `.aide/registry/REG-ADAPTER-001.md` | `21d922ecc4abaa96644c25a039d9d8ec3c594dd2d9d71b9d63851a32a2c0bd62` |
| `src/rkg/detection/README.md` | `f8a97a20c49d2ec1292a9f82da465a8cdf0b25736acef7410378ea644ca42a19` |

Verification and AC mapping are recorded in `TEST-RKG-AIOKAFKA-ADAPTER-001`.

## Đối chiếu commit và phạm vi hiện hành

## Kết quả đối chiếu triển khai

Trích xuất literal topic publish/consume cùng callable/evidence; topic động thành diagnostic, không lưu payload hoặc credential.

Các file thay đổi được xác định bằng Git diff của các commit được pin trong frontmatter. Current-tree hash nằm trong context revision 3; khác hash lịch sử là revision về sau, không phải cùng lần chạy.

## Diễn giải và correction

Hành vi và các lần kiểm đã ghi trong prior evidence giữ nguyên; bản này bổ sung liên kết và nguồn commit, không thay kết quả cũ.

## Kết quả lần bổ sung hồ sơ

Đã đọc commit/file, parse test declarations và liên kết evidence; không chạy lại runtime test hoặc đo KPI. Không nhận đây là review code độc lập hay approval.
