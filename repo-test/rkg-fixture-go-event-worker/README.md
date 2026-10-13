# RKG fixture: Go event worker

Standalone Go fixture for repository-knowledge-graph analysis. It consumes order
events from Kafka, updates a PostgreSQL projection, publishes a projection event,
and periodically deletes stale projections. It intentionally exposes realistic
positive and negative analysis patterns; it is not a production service.

## Toolchain and dependencies

- Go 1.27.1 (the stable release used to generate and verify this fixture)
- `github.com/segmentio/kafka-go` v0.4.51 for the explicit reader/writer clients
- `github.com/jackc/pgx/v5` v5.11.0 for PostgreSQL and its connection pool
- Standard `testing` package; tests use local fakes and require no Kafka or database

`go.mod` and `go.sum` are committed inputs. Run `go mod tidy` after dependency
changes and verify that a second tidy does not change them.

## Run and verify

```bash
cp .env.example .env
set -a; . ./.env; set +a
go run ./cmd/order-worker
```

The runtime requires Kafka and PostgreSQL, including this logical table:

```sql
CREATE SCHEMA IF NOT EXISTS commerce;
CREATE TABLE commerce.order_projection (
    order_id text PRIMARY KEY,
    status text NOT NULL,
    updated_at timestamptz NOT NULL
);
```

No HTTP server is started. Shutdown is driven by `SIGINT`, `SIGTERM`, or parent
context cancellation. Verification commands are:

```bash
gofmt -w .
go vet ./...
go test ./...
go test -race ./...
go build ./...
go mod tidy
git diff --exit-code -- go.mod go.sum
```

## Runtime flow

1. `cmd/order-worker` validates environment configuration and explicitly creates
   the pgx pool, Kafka reader, Kafka writer, processor, and cleanup runner.
2. `KafkaConsumer.Run` fetches and delegates `orders.events` messages, then commits
   only messages handled successfully.
3. `Processor.HandleMessage` decodes a minimal envelope and calls
   `OrderRepository.Upsert` for `commerce.order_projection`.
4. The processor calls `EventPublisher.Publish` with
   `orders.projection.updated`.
5. `Cleanup.Run` periodically calls `DeleteOlderThan`; all loops stop on context
   cancellation and clients are closed by the command.

Constructors only assemble values. Network-capable operations are reached from
the explicit `run`/`Run`/`Publish` paths. Libraries return errors rather than
panicking on malformed input.

## Analyzer inventory

### Packages and source roles

- `cmd/order-worker`: composition root, signal handling, concurrent supervision.
- `internal/app`: `Processor` and scheduled `Cleanup` orchestration.
- `internal/domain`: named IDs/statuses, embedded `AuditFields`, event decoding,
  value and pointer receivers, and generic `CloneSlice[T]`.
- `internal/messaging`: Kafka consumer/producer adapters, interfaces, messages,
  and topic constants.
- `internal/storage`: repository interface, pgx adapter, and static SQL constants.
- `internal/config`: validation for the four supported environment keys.
- `internal/analysiscases/positive`: imported-constant publish and explicit
  compile-time interface checks.
- `internal/analysiscases/negative`: deliberately misleading constructs that
  must not become unsupported graph edges.

Go packages are package metadata for this fixture; they are not expected to be
emitted as `Namespace` nodes.

### Expected declarations and relations

- Structs: `OrderProjection`, embedded `AuditFields`, `EventEnvelope`, `Message`,
  `Config`, `Processor`, `Cleanup`, `KafkaConsumer`, `KafkaProducer`, and
  `PostgresRepository`.
- Named scalar types: `OrderID` and `OrderStatus`.
- Interfaces: `OrderRepository`, `EventPublisher`, `EventConsumer`,
  `MessageHandler`, `KafkaReader`, `KafkaWriter`, `PgxDB`, and command-local
  `runner`.
- Constructors return pointers (`NewProcessor`, `NewCleanup`,
  `NewKafkaConsumer`, `NewKafkaProducer`, `NewPostgresRepository`).
- Both value receiver (`OrderProjection.IsTerminal`) and pointer receiver
  (`OrderProjection.Touch`) methods exist.
- `CloneSlice[T]` is the generic helper.
- The simple type name `Marker` appears in both positive and negative packages,
  so symbol identity must include package scope.
- Go interface implementation is implicit. The assignments in
  `positive/interface_binding.go` confirm real bindings but do not introduce an
  `implements` keyword or inheritance declaration.
- Import resolution includes the alias `msg` in `positive/imported_topic.go`.

Expected call flow includes:

```text
main -> run -> config.Load / pgxpool.New / constructors -> supervise
KafkaConsumer.Run -> MessageHandler.HandleMessage
Processor.HandleMessage -> Processor.Process -> domain.DecodeEvent
Processor.Process -> OrderRepository.Upsert -> EventPublisher.Publish
Cleanup.Run -> OrderRepository.DeleteOlderThan
PostgresRepository methods -> PgxDB.QueryRow / PgxDB.Exec
```

### Messaging inventory

| Direction | Topic | Evidence |
| --- | --- | --- |
| Consume | `orders.events` | Literal in `NewKafkaReader`; canonical constant `messaging.OrdersTopic` |
| Publish | `orders.projection.updated` | `messaging.ProjectionUpdatedTopic`, imported by the processor and positive case |

`negative/dynamic_topic.go` uses a runtime topic and must not create a static
channel. `negative/package_level_publish.go` is a package initializer calling a
local function, not a handler-owned publish. `negative/shadowed_package.go` uses
a local variable named `kafka`. `negative/ambiguous_receiver.go` has two possible
implicit implementations, so the interface call must not be guessed as one
concrete target.

### Database inventory

- Identity: kind `table`, schema `commerce`, name `order_projection`.
- `FindByID` uses a static `SELECT`.
- `Upsert` uses a static `INSERT ... ON CONFLICT ... DO UPDATE`.
- `DeleteOlderThan` uses a static `DELETE`.
- All values are bound parameters; no SQL is built from runtime strings.

### Configuration and sensitive-data inventory

Supported keys are `KAFKA_BROKERS`, `KAFKA_GROUP_ID`, `DATABASE_URL`, and
`CLEANUP_INTERVAL`. `.env.example` contains placeholders only. Structured logs
contain fixed event names and safe numeric cleanup counts; they do not contain
event bodies, configuration values, credentials, or raw source.

`RKG_TEST_SECRET_DO_NOT_PERSIST` appears deliberately in
`testdata/prohibited-secret.txt`, the ignored syntax-error fixture, and a config
test assertion. It is synthetic scanner input: it must never be copied into graph
properties, logs, evidence, or generated output. Files under `testdata/` are not
compiled or executed by Go commands.

## Test coverage

- processor success, repository failure, and publisher failure;
- consumer delegation/commit and producer topic mapping without network access;
- pgx boundary and exact static SQL contract;
- configuration validation without secret-value leakage;
- periodic cleanup and context cancellation;
- constructor side-effect checks.

