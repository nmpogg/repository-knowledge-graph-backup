# rkg-fixture-polyglot-commerce
A standalone, deliberately small commerce monorepo for mixed-language RKG analysis. It contains four independently built applications, explicit composition roots, contracts and human-authored graph expectations. It contains no RKG implementation.

## Application inventory
| App key | Root | Language | Framework | Entrypoint intent |
|---|---|---|---|---|
| `web` | `apps/web` | TypeScript | React | `src/main.tsx` |
| `orders` | `services/orders` | Java | Spring Boot | `OrdersApplication.main` |
| `email-worker` | `workers/email` | TypeScript | BullMQ | `src/main.ts`, explicit `bootstrap` |
| `projection-worker` | `workers/projection` | Go | Kafka/pgx worker | `cmd/order-worker/main.go` |

There is no root package manager or npm workspace. Each Node project owns its own `package.json` and lockfile. Java owns its POM and POM checksum; Go owns `go.mod` and `go.sum`. Python is used only for offline verification tooling.

A single RKG `app_module:app_symbol` cannot express these four roots. The fixture intentionally keeps that limitation visible: future core support must select root, language and framework explicitly rather than invent one umbrella app. Shared `shared/orders` contains Java and TypeScript contract-name declarations and must produce one Directory identity per normalized path.

## Technology matrix
Verified setup: Node `24.21.0`, npm `11.19.0`, TypeScript `6.0.3`, React `19.3.0`, Vite `8.3.2`, Vitest `5.0.3`, BullMQ `6.3.11`; Eclipse Temurin Java `21.0.12.1`, Maven Wrapper `3.9.11`, Spring Boot `3.5.16`; Go `1.27.1`, kafka-go `0.4.51`, pgx `5.11.0`. Contract validation uses Python 3.10+ and pinned `jsonschema` `4.26.0`.

## Communication flow
1. React `OrderApi` calls GET/POST `/api/orders`. Detail retrieval uses GET `/api/orders/{orderId}`; status editing uses PATCH `/api/orders/{orderId}/status`.
2. Spring controller delegates to the order service, persists `commerce.orders` / `commerce.order_items` and publishes `orders.events`.
3. The Go worker consumes `orders.events`, upserts `commerce.order_projection`, and publishes `orders.projection.updated`.
4. The email application's explicit `dispatchOrderEvent` validates a delivered `orders.events` envelope and enqueues an `order-email` job. The BullMQ processor calls `EmailService.sendOrderEmail`.

The shared wire envelope uses `type`, `order_id`, `status`, `occurred_at`; statuses match Java's uppercase enum. Java serialization, Go decoding and TypeScript queue dispatch are tested against the same synthetic example. Email event delivery is an injected application boundary, not a Kafka subscriber invented by the analyzer. A real Kafka-to-email relay and SMTP sending are deliberately outside this first fixture; the email service is an in-memory stub. Unit tests need no Docker, Redis, Kafka, PostgreSQL, SMTP or external network. Spring persistence tests use in-memory H2 and mock Kafka.

## Install dependencies once
Use a Java 21 JDK (`JAVA_HOME`), Go `1.27.1` (`PATH`) and Node from `.nvmrc`.

```sh
(cd apps/web && npm ci)
(cd workers/email && npm ci)
(cd services/orders && ./mvnw -DskipTests verify)
(cd workers/projection && go mod download)
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-contracts.txt
```

Dependency setup may use network. The verification commands after setup use cached dependencies and never install global packages or start service processes. For a fully isolated environment, populate the package/Maven/Go caches beforehand.

## Verify from the repository root
```sh
PYTHON=.venv/bin/python ./scripts/verify-all
```
The POSIX shell script fails immediately when a component fails, preserving its exit code. It runs each Node app's `npm run lint`, `npm test`, `npm run typecheck`, `npm run build`; Maven `./mvnw -o -q verify`; Go formatting check, module verification, `vet`, `test`, `test -race`, `build`; then offline schema/contract/inventory and orchestration/benchmark tests. Use WSL or another POSIX shell on Windows; there is no PowerShell variant.

Native component commands may also be run independently from their component roots. Build/dependency outputs are ignored and not part of the fixture.

## RKG scan inputs
Use `rkg-scan-defaults.json` as the repository scan defaults after building locally. It excludes nested dependency/build directories explicitly; a root-only `node_modules/**` ignore is insufficient for this monorepo. No app_module/app_symbol override is supplied. These are operator inputs, not RKG implementation changes.

## Expected graph
See [expected/README.md](expected/README.md) and `applications.yaml`, `technologies.yaml`, `entities.yaml`, `edges.yaml`, `diagnostics.yaml`, `prohibited-values.txt`. JSON syntax is used inside YAML files for straightforward offline parsing. These are source-backed semantic intentions, not dumped RKG hash IDs or an assertion that all future analyzer features exist today.

Adapter-local facts include React HTTP call sites, Spring routes/handlers and Kafka publishing, Go Kafka consume/publish and SQL resource access, BullMQ queue creation/consumption, internal call chains and schema-specific tables. Current language adapters must not inspect another language's AST.

Post-merge linker targets are listed separately: normalized HTTP method/path matching; evidence-backed Kafka channel identity across Java and Go; optional spec-to-implementation linking. Identical names alone are insufficient. Contracts are supplementary evidence and never silently override conflicting source.

## Intentional negative cases
- Dynamic client URL, dynamic Kafka topic and dynamic BullMQ queue are not statically merged or linked.
- GET and POST `/api/orders` are separate endpoints; `commerce.orders` and `audit.orders` are separate resources, and the audit entity has no application access edge.
- Java `Order` and TypeScript `Order` are separate scoped symbols.
- Real malformed `.ts`, `.java`, `.go` files live under root `analysis-cases/syntax`, outside every native build/lint/test root. Static analysis may report syntax errors but must not invent callables from them.
- `analysis-cases/unsupported/schema.proto` and Markdown/YAML have no fabricated SourceUnit without an appropriate adapter.
- Synthetic sensitive input lives in text/test fixtures; it must never reach graph/report/log. There are no real credentials. Imports do not connect to external services; bootstrap is explicit.

## Scanner performance corpus
```sh
python3 scripts/benchmark-corpus.py --count 100 --seed 2026
python3 scripts/benchmark-corpus.py --cleanup
python3 scripts/benchmark-corpus.py --count 1000
python3 scripts/benchmark-corpus.py --cleanup
python3 scripts/benchmark-corpus.py --count 9000
python3 scripts/benchmark-corpus.py --cleanup
```
Generated input is deterministic, lives only in ignored `.benchmark/corpus`, and is never imported or executed. Generation refuses an existing output directory; cleanup only deletes that fixed directory and refuses symlinks. This corpus is for scanner benchmarks, not production source.

## Contract validation limits
OpenAPI 3.0 and AsyncAPI 2.6 schemas are vendored from their official projects with SHA-256 provenance. Verification performs JSON Schema validation, rejects external contract refs, checks local refs, unique operation IDs, required route parameters, exact implemented routes, literal channels, status spellings and example payloads. This small AsyncAPI fixture has no servers/security/tags/channel parameters requiring additional parser validation. The script is scoped to this fixture, not a general replacement for the AsyncAPI parser.
