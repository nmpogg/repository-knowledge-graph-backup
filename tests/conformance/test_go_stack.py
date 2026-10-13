"""Focused conformance for Go language + kafka-go + pgx adapters."""

from __future__ import annotations

from pathlib import Path

from rkg.adapters import AdapterContext
from rkg.domain import EdgeType, EntityType, SourceScanConfig, validate_fact_batch
from rkg.ingestion import LocalSourcePolicy, build_manifest, resolve_local_source

_PATTERNS = ("*.go", "**/*.go")
_SECRET = "RKG_TEST_SECRET_DO_NOT_PERSIST"


def _write(root: Path, relative: str, source: str) -> None:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")


def _pipeline(root: Path):
    from rkg.adapters.go_language import GoLanguageAdapter
    from rkg.adapters.kafka_go_messaging import KafkaGoMessagingAdapter
    from rkg.adapters.pgx_data import PgxDataAccessAdapter

    config = SourceScanConfig(40, 65536, _PATTERNS)
    manifest = build_manifest(
        resolve_local_source("repo-go", root, LocalSourcePolicy((root,))), config
    )
    context = AdapterContext("repo-go", "snap-go", "job-go", config)
    language = GoLanguageAdapter()
    parsed = language.parse(manifest, config)
    batch = language.resolve(
        context, parsed, language.extract(context, parsed).facts
    ).facts
    for adapter in (KafkaGoMessagingAdapter(), PgxDataAccessAdapter()):
        batch = adapter.extract(context, parsed, batch).facts
        validate_fact_batch(batch)
    return batch


def _entities(batch, entity_type: EntityType):
    return [item for item in batch.entities if item.type == entity_type]


def _edge_pairs(batch, edge_type: EdgeType) -> set[tuple[str, str]]:
    by_id = {item.id: item for item in batch.entities}
    return {
        (by_id[edge.source_id].qualified_name, by_id[edge.target_id].qualified_name)
        for edge in batch.edges
        if edge.type == edge_type
        and edge.source_id in by_id
        and edge.target_id in by_id
    }


def _blob(batch) -> str:
    parts = [item.qualified_name for item in batch.entities]
    parts.extend(item.message for item in batch.diagnostics)
    parts.extend(item.file_path or "" for item in batch.entities)
    return "\n".join(parts)


def test_go_language_types_calls_config_and_no_namespace(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "internal/domain/order.go",
        """
package domain

type OrderID string
type OrderStatus string
type AuditFields struct{ UpdatedAt int64 }
type OrderProjection struct {
  AuditFields
  ID OrderID
  Status OrderStatus
}
func (o OrderProjection) IsTerminal() bool { return false }
func (o *OrderProjection) Touch() {}
func CloneSlice[T any](values []T) []T { return values }
func DecodeEvent(payload []byte) (OrderProjection, error) {
  return OrderProjection{}, nil
}
""".strip(),
    )
    _write(
        tmp_path,
        "internal/app/processor.go",
        """
package app

import "example.com/fixture/internal/domain"
import "example.com/fixture/internal/storage"
import "example.com/fixture/internal/messaging"

type Processor struct {
  repository storage.OrderRepository
  publisher messaging.EventPublisher
}
func NewProcessor(repository storage.OrderRepository, publisher messaging.EventPublisher) *Processor {
  return &Processor{repository: repository, publisher: publisher}
}
func (p *Processor) HandleMessage(payload []byte) error {
  return p.Process(payload)
}
func (p *Processor) Process(payload []byte) error {
  _, err := domain.DecodeEvent(payload)
  if err != nil { return err }
  if err := p.repository.Upsert(); err != nil { return err }
  return p.publisher.Publish("orders.projection.updated")
}
""".strip(),
    )
    _write(
        tmp_path,
        "internal/storage/repository.go",
        """
package storage
type OrderRepository interface {
  Upsert() error
  DeleteOlderThan() error
  FindByID() error
}
""".strip(),
    )
    _write(
        tmp_path,
        "internal/messaging/producer.go",
        """
package messaging
type EventPublisher interface {
  Publish(topic string) error
}
""".strip(),
    )
    _write(
        tmp_path,
        "internal/app/cleanup.go",
        """
package app
import "example.com/fixture/internal/storage"
type Cleanup struct{ repository storage.OrderRepository }
func NewCleanup(repository storage.OrderRepository) *Cleanup {
  return &Cleanup{repository: repository}
}
func (c *Cleanup) Run() error { return c.repository.DeleteOlderThan() }
""".strip(),
    )
    _write(
        tmp_path,
        "internal/config/config.go",
        """
package config
type Config struct{}
func Load(lookup func(string) (string, bool)) (Config, error) {
  _, _ = lookup("KAFKA_BROKERS")
  _, _ = lookup("KAFKA_GROUP_ID")
  _, _ = lookup("DATABASE_URL")
  _, _ = lookup("CLEANUP_INTERVAL")
  return Config{}, nil
}
""".strip(),
    )
    _write(
        tmp_path,
        "cmd/order-worker/main.go",
        """
package main
func main() { _ = run() }
func run() error { return nil }
""".strip(),
    )
    _write(
        tmp_path,
        "internal/analysiscases/positive/marker.go",
        "package positive\ntype Marker struct{}\n",
    )
    _write(
        tmp_path,
        "internal/analysiscases/negative/marker.go",
        "package negative\ntype Marker struct{}\n",
    )
    batch = _pipeline(tmp_path)
    types = {item.qualified_name for item in _entities(batch, EntityType.TYPE)}
    callables = {item.qualified_name for item in _entities(batch, EntityType.CALLABLE)}
    assert "domain.OrderProjection" in types
    assert "domain.AuditFields" in types
    assert "domain.OrderID" in types
    assert "app.Processor" in types
    assert "storage.OrderRepository" in types
    assert "positive.Marker" in types
    assert "negative.Marker" in types
    assert "domain.OrderProjection.IsTerminal" in callables
    assert "domain.OrderProjection.Touch" in callables
    assert "domain.CloneSlice" in callables
    assert "app.NewProcessor" in callables
    assert "main" in callables
    assert "run" in callables
    assert not any(item.type == EntityType.NAMESPACE for item in batch.entities)
    calls = _edge_pairs(batch, EdgeType.CALLS)
    assert ("main", "run") in calls
    assert ("app.Processor.HandleMessage", "app.Processor.Process") in calls
    assert ("app.Processor.Process", "domain.DecodeEvent") in calls
    assert ("app.Processor.Process", "storage.OrderRepository.Upsert") in calls
    assert ("app.Processor.Process", "messaging.EventPublisher.Publish") in calls
    assert ("app.Cleanup.Run", "storage.OrderRepository.DeleteOlderThan") in calls
    configs = {
        item.qualified_name: dict(item.attributes)
        for item in _entities(batch, EntityType.CONFIGURATION)
    }
    for key in (
        "environment:KAFKA_BROKERS",
        "environment:KAFKA_GROUP_ID",
        "environment:DATABASE_URL",
        "environment:CLEANUP_INTERVAL",
    ):
        assert key in configs
        assert configs[key].get("kind") == "environment"
    assert _SECRET not in _blob(batch)
    assert str(tmp_path) not in _blob(batch)


def test_kafka_go_channels_and_negatives(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "internal/messaging/topics.go",
        """
package messaging
const (
  OrdersTopic = "orders.events"
  ProjectionUpdatedTopic = "orders.projection.updated"
)
""".strip(),
    )
    _write(
        tmp_path,
        "internal/messaging/producer.go",
        """
package messaging
import "context"
type EventPublisher interface {
  Publish(ctx context.Context, topic string, key, payload []byte) error
}
""".strip(),
    )
    _write(
        tmp_path,
        "internal/messaging/consumer.go",
        """
package messaging
import "context"
type MessageHandler interface {
  HandleMessage(context.Context) error
}
type EventConsumer interface {
  Run(context.Context, MessageHandler) error
}
""".strip(),
    )
    _write(
        tmp_path,
        "internal/messaging/kafka_consumer.go",
        """
package messaging
import (
  "context"
  "github.com/segmentio/kafka-go"
)
type KafkaReader interface {
  FetchMessage(context.Context) (kafka.Message, error)
}
type KafkaConsumer struct{ reader KafkaReader }
func NewKafkaReader(brokers []string, groupID string) *kafka.Reader {
  return kafka.NewReader(kafka.ReaderConfig{
    Brokers: brokers,
    GroupID: groupID,
    Topic: "orders.events",
  })
}
func NewKafkaConsumer(reader KafkaReader) *KafkaConsumer {
  return &KafkaConsumer{reader: reader}
}
func (c *KafkaConsumer) Run(ctx context.Context, handler MessageHandler) error {
  return handler.HandleMessage(ctx)
}
""".strip(),
    )
    _write(
        tmp_path,
        "internal/app/processor.go",
        """
package app
import (
  "context"
  "example.com/fixture/internal/messaging"
)
type Processor struct{ publisher messaging.EventPublisher }
func (p *Processor) Process(ctx context.Context) error {
  return p.publisher.Publish(ctx, messaging.ProjectionUpdatedTopic, nil, nil)
}
""".strip(),
    )
    _write(
        tmp_path,
        "internal/analysiscases/positive/imported_topic.go",
        """
package positive
import (
  "context"
  msg "example.com/fixture/internal/messaging"
)
func PublishProjection(ctx context.Context, publisher msg.EventPublisher, payload []byte) error {
  return publisher.Publish(ctx, msg.ProjectionUpdatedTopic, nil, payload)
}
""".strip(),
    )
    _write(
        tmp_path,
        "internal/analysiscases/negative/dynamic_topic.go",
        """
package negative
import (
  "context"
  "example.com/fixture/internal/messaging"
)
func PublishDynamic(ctx context.Context, publisher messaging.EventPublisher, topic string, payload []byte) error {
  return publisher.Publish(ctx, topic, nil, payload)
}
""".strip(),
    )
    _write(
        tmp_path,
        "internal/analysiscases/negative/package_level_publish.go",
        """
package negative
var PackageLevelResult = localPublish()
func localPublish() string { return "not-a-message" }
""".strip(),
    )
    _write(
        tmp_path,
        "internal/analysiscases/negative/shadowed_package.go",
        """
package negative
type localKafka struct{}
func (localKafka) Publish() string { return "local" }
func ShadowedKafka() string {
  kafka := localKafka{}
  return kafka.Publish()
}
""".strip(),
    )
    _write(
        tmp_path,
        "internal/analysiscases/negative/ambiguous_receiver.go",
        """
package negative
type ambiguousWorker interface { Work() string }
type firstWorker struct{}
type secondWorker struct{}
func (firstWorker) Work() string  { return "first" }
func (secondWorker) Work() string { return "second" }
func InvokeAmbiguous(worker ambiguousWorker) string { return worker.Work() }
""".strip(),
    )
    batch = _pipeline(tmp_path)
    channels = {
        item.qualified_name: dict(item.attributes)
        for item in _entities(batch, EntityType.MESSAGE_CHANNEL)
    }
    assert "orders.events" in channels
    assert channels["orders.events"].get("name") == "orders.events"
    assert "orders.projection.updated" in channels
    consumes = _edge_pairs(batch, EdgeType.CONSUMES)
    publishes = _edge_pairs(batch, EdgeType.PUBLISHES)
    assert ("messaging.NewKafkaReader", "orders.events") in consumes
    assert ("app.Processor.Process", "orders.projection.updated") in publishes
    assert ("positive.PublishProjection", "orders.projection.updated") in publishes
    assert (
        "messaging.EventPublisher.Publish",
        "orders.projection.updated",
    ) not in publishes
    assert not any("dynamic_topic" in src for src, _ in publishes)
    assert not any("package_level_publish" in src for src, _ in publishes)
    assert not any("shadowed_package" in src for src, _ in publishes)
    calls = _edge_pairs(batch, EdgeType.CALLS)
    assert not any(
        tgt.endswith("firstWorker.Work") or tgt.endswith("secondWorker.Work")
        for _, tgt in calls
    )
    assert (
        "messaging.KafkaConsumer.Run",
        "messaging.MessageHandler.HandleMessage",
    ) in calls


def test_pgx_static_sql_reads_writes(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "internal/storage/queries.go",
        """
package storage
const FindByIDSQL = `SELECT order_id FROM commerce.order_projection WHERE order_id = $1`
const UpsertSQL = `INSERT INTO commerce.order_projection (order_id) VALUES ($1)`
const DeleteOlderThanSQL = `DELETE FROM commerce.order_projection WHERE updated_at < $1`
""".strip(),
    )
    _write(
        tmp_path,
        "internal/storage/postgres_repository.go",
        """
package storage
import (
  "context"
  "github.com/jackc/pgx/v5"
  "github.com/jackc/pgx/v5/pgconn"
)
type PgxDB interface {
  QueryRow(context.Context, string, ...any) pgx.Row
  Exec(context.Context, string, ...any) (pgconn.CommandTag, error)
}
type PostgresRepository struct{ db PgxDB }
func NewPostgresRepository(db PgxDB) *PostgresRepository {
  return &PostgresRepository{db: db}
}
func (r *PostgresRepository) FindByID(ctx context.Context) error {
  return r.db.QueryRow(ctx, FindByIDSQL).Scan()
}
func (r *PostgresRepository) Upsert(ctx context.Context) error {
  _, err := r.db.Exec(ctx, UpsertSQL)
  return err
}
func (r *PostgresRepository) DeleteOlderThan(ctx context.Context) error {
  _, err := r.db.Exec(ctx, DeleteOlderThanSQL)
  return err
}
""".strip(),
    )
    batch = _pipeline(tmp_path)
    resources = {
        item.qualified_name: dict(item.attributes)
        for item in _entities(batch, EntityType.DATA_RESOURCE)
    }
    assert "relational:commerce.order_projection" in resources
    attrs = resources["relational:commerce.order_projection"]
    assert attrs.get("kind") == "table"
    assert attrs.get("namespace") == "commerce"
    assert attrs.get("name") == "order_projection"
    reads = _edge_pairs(batch, EdgeType.READS)
    writes = _edge_pairs(batch, EdgeType.WRITES)
    assert (
        "storage.PostgresRepository.FindByID",
        "relational:commerce.order_projection",
    ) in reads
    assert (
        "storage.PostgresRepository.Upsert",
        "relational:commerce.order_projection",
    ) in writes
    assert (
        "storage.PostgresRepository.DeleteOlderThan",
        "relational:commerce.order_projection",
    ) in writes
    assert (
        "storage.PostgresRepository.FindByID",
        "storage.PgxDB.QueryRow",
    ) in _edge_pairs(batch, EdgeType.CALLS)
