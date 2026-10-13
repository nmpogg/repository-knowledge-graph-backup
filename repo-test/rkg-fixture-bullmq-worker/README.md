# rkg-fixture-bullmq-worker

This standalone repository is an order-processing background worker and golden static-analysis fixture. It has no HTTP server or web entrypoint. Importing `src/index.ts` is inert; an application must explicitly call `bootstrap()` to construct BullMQ queues, workers, and the cleanup scheduler.

## Stack and commands

The manifest pins Node.js `>=22.22.2` (Node 24 LTS recommended), BullMQ `6.3.11`, TypeScript `6.0.3`, Vitest `5.0.3`, ESLint `10.12.0`, and `typescript-eslint` `8.71.0`. Transitive versions are fixed by `package-lock.json`.

```bash
npm ci
npm run lint
npm test -- --run
npm run build
npx tsc --noEmit
```

Tests use injected/mocked queue boundaries and never connect to Redis, a database, or the network. Copy `.env.example` to `.env` only when intentionally running against a local Redis instance; this fixture does not automatically load `.env`.

## Module flow

```text
explicit bootstrap
  -> environment -> Redis connection options
  -> order queue -> OrderProducer.enqueue
  -> order worker -> processOrderJob -> OrderService -> OrderRepository
                                      -> enqueueOrderEmail -> email queue
  -> email worker -> namedProcessor -> processEmailJob -> EmailService
  -> cleanup scheduler -> order-processing channel
```

## Expected static-analysis inventory

### Message channels

Exactly two logical `MessageChannel` identities are expected:

| Identity | Construction and use |
| --- | --- |
| `order-processing` | `ORDER_QUEUE`; order producer/worker; typed worker factory; cleanup scheduler |
| `order-email` | direct literal in `createEmailQueue`; imported/aliased `EMAIL_QUEUE`; email producer/worker |

Repeated construction with the same static name must deduplicate to one channel. Redis URL, host, port, username, password, and connection object are configuration—not channel identity or graph attributes.

### Expected callables and edges

| Source callable | Expected fact |
| --- | --- |
| `createOrderQueue` | constructs `Queue(ORDER_QUEUE)` |
| `createEmailQueue` | constructs `Queue("order-email")` |
| `OrderProducer.enqueue` | publishes job `process-order` to `order-processing` |
| `enqueueOrderEmail` | publishes job `send-order-email` to `order-email` |
| `createOrderWorker` | consumes `order-processing` with an inline async handler |
| `createEmailWorker` | consumes `order-email` through named `namedProcessor` |
| `createTypedWorker` | static factory consuming imported `ORDER_QUEUE` |
| `createCleanupScheduler` | registers static `daily-order-cleanup`/`cleanup-orders` schedule on `order-processing` |

Important internal call chains are:

- `createOrderWorker inline handler -> processOrderJob -> OrderService.processOrder -> OrderRepository.save`.
- `processOrderJob -> enqueueOrderEmail -> Queue.add`.
- `createEmailWorker namedProcessor -> processEmailJob -> EmailService.sendOrderEmail`.
- `bootstrap -> queue/worker factories + createCleanupScheduler`.

The expected configuration keys are `REDIS_URL`, `ORDER_WORKER_CONCURRENCY`, and `EMAIL_FROM`. Concurrency is parsed and validated, but its raw value is not an expected graph fact.

BullMQ retry, backoff, delay, and repeat scheduling are intentionally present. The RKG schema can represent callables and message channels, but may not fully represent retry/schedule semantics. A scheduled job must not be converted into an HTTP endpoint.

## Intentional negative cases

| Case | Fact that must not be created |
| --- | --- |
| `dynamicQueueName.ts` | no guessed channel for a runtime queue name; emit a diagnostic |
| `reassignedWorker.ts` | no consume edge from the reassigned constructor receiver |
| `unscopedPublish.ts` | no BullMQ publish edge for unrelated `LocalPublisher.publish` |
| `shadowedBullmq.ts` | no BullMQ technology/channel edge for local `Queue` and `Worker` classes |

The test sentinel `RKG_TEST_SECRET_DO_NOT_PERSIST` must never be persisted in an analyzer graph, report, or log. Job payloads, retry option bodies, Redis connection values, real email addresses, credentials, and secrets are also explicitly excluded from expected facts. Runtime code never logs a job payload, Redis URL, credential, or email address.

## Safety

No Worker or Queue is constructed as a module-import side effect. Unit tests call processors directly with minimal typed fake jobs, and the bootstrap test injects all BullMQ construction boundaries. A real Redis server is neither required nor contacted by the acceptance suite.
