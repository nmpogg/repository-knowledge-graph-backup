package app

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"time"

	"example.com/rkg-fixture-go-event-worker/internal/domain"
	"example.com/rkg-fixture-go-event-worker/internal/messaging"
	"example.com/rkg-fixture-go-event-worker/internal/storage"
)

type Processor struct {
	repository storage.OrderRepository
	publisher  messaging.EventPublisher
	logger     *slog.Logger
}

func NewProcessor(repository storage.OrderRepository, publisher messaging.EventPublisher, logger *slog.Logger) *Processor {
	return &Processor{repository: repository, publisher: publisher, logger: logger}
}

func (p *Processor) HandleMessage(ctx context.Context, message messaging.Message) error {
	return p.Process(ctx, message.Value)
}

func (p *Processor) Process(ctx context.Context, payload []byte) error {
	event, err := domain.DecodeEvent(payload)
	if err != nil {
		return err
	}
	projection := domain.OrderProjection{
		ID:          event.OrderID,
		Status:      event.Status,
		AuditFields: domain.AuditFields{UpdatedAt: event.OccurredAt},
	}
	if err := p.repository.Upsert(ctx, projection); err != nil {
		return fmt.Errorf("store projection: %w", err)
	}
	update, err := json.Marshal(projectionUpdated{
		OrderID:   projection.ID,
		Status:    projection.Status,
		UpdatedAt: projection.UpdatedAt,
	})
	if err != nil {
		return fmt.Errorf("encode projection update: %w", err)
	}
	if err := p.publisher.Publish(ctx, messaging.ProjectionUpdatedTopic, []byte(projection.ID), update); err != nil {
		return fmt.Errorf("publish projection update: %w", err)
	}
	p.logger.InfoContext(ctx, "order projection updated")
	return nil
}

type projectionUpdated struct {
	OrderID   domain.OrderID     `json:"order_id"`
	Status    domain.OrderStatus `json:"status"`
	UpdatedAt time.Time          `json:"updated_at"`
}
