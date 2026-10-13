# Projection worker
Go 1.27.1 worker. Explicit `cmd/order-worker/main.go` wiring creates the Kafka/pgx clients. Constructors and package imports do not connect or spawn loops. KafkaConsumer.Run delegates `orders.events` to Processor; Processor.Process decodes the shared Spring envelope, calls OrderRepository.Upsert for `commerce.order_projection`, then publishes `orders.projection.updated`. Cleanup calls DeleteOlderThan.

After `go mod download`, run `gofmt -l .` (must be empty), `go mod verify`, `go vet ./...`, `go test ./...`, `go test -race ./...`, `go build ./...`. `go.mod` and `go.sum` pin dependencies. Tests inject fake Kafka/database boundaries; they require no external network, broker or PostgreSQL. Race testing needs a C toolchain.

Runtime requires external infrastructure only when the command is explicitly started, which verification never does. Logs contain fixed event names and safe counters, not source, config or payload. Negative examples cover dynamic topics, package initializers, package-name shadowing and ambiguous interface implementations. Root malformed Go source is outside this module's native test/build roots.
