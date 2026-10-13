package app

import (
	"context"
	"errors"
	"io"
	"log/slog"
	"testing"
	"time"

	"example.com/rkg-fixture-polyglot-commerce/projection/internal/domain"
)

func TestProcessorSuccess(t *testing.T) {
	repository := &repositoryStub{}
	publisher := &publisherStub{}
	processor := NewProcessor(repository, publisher, discardLogger())

	err := processor.Process(context.Background(), []byte(`{"type":"order.updated","order_id":"order-7","status":"SHIPPED","occurred_at":"2026-10-05T10:00:00Z"}`))
	if err != nil {
		t.Fatalf("Process() error = %v", err)
	}
	if len(repository.upserts) != 1 || repository.upserts[0].ID != "order-7" {
		t.Fatalf("upserts = %#v", repository.upserts)
	}
	if publisher.topic != "orders.projection.updated" {
		t.Fatalf("topic = %q", publisher.topic)
	}
}

func TestProcessorRepositoryFailureStopsPublish(t *testing.T) {
	want := errors.New("database unavailable")
	repository := &repositoryStub{upsertErr: want}
	publisher := &publisherStub{}
	err := NewProcessor(repository, publisher, discardLogger()).Process(context.Background(), validEvent())
	if !errors.Is(err, want) {
		t.Fatalf("Process() error = %v, want wrapped %v", err, want)
	}
	if publisher.calls != 0 {
		t.Fatalf("publisher calls = %d, want 0", publisher.calls)
	}
}

func TestProcessorPublishFailure(t *testing.T) {
	want := errors.New("broker unavailable")
	publisher := &publisherStub{err: want}
	err := NewProcessor(&repositoryStub{}, publisher, discardLogger()).Process(context.Background(), validEvent())
	if !errors.Is(err, want) {
		t.Fatalf("Process() error = %v, want wrapped %v", err, want)
	}
}

func validEvent() []byte {
	return []byte(`{"type":"order.updated","order_id":"order-7","status":"CREATED","occurred_at":"2026-10-05T10:00:00Z"}`)
}

func discardLogger() *slog.Logger {
	return slog.New(slog.NewTextHandler(io.Discard, nil))
}

type repositoryStub struct {
	upserts   []domain.OrderProjection
	upsertErr error
	deleteErr error
	deleted   int64
	cutoffs   chan time.Time
}

func (r *repositoryStub) FindByID(context.Context, domain.OrderID) (domain.OrderProjection, error) {
	return domain.OrderProjection{}, nil
}

func (r *repositoryStub) Upsert(_ context.Context, projection domain.OrderProjection) error {
	r.upserts = append(r.upserts, projection)
	return r.upsertErr
}

func (r *repositoryStub) DeleteOlderThan(_ context.Context, cutoff time.Time) (int64, error) {
	if r.cutoffs != nil {
		r.cutoffs <- cutoff
	}
	return r.deleted, r.deleteErr
}

type publisherStub struct {
	topic string
	calls int
	err   error
}

func (p *publisherStub) Publish(_ context.Context, topic string, _, _ []byte) error {
	p.calls++
	p.topic = topic
	return p.err
}

func (p *publisherStub) Close() error { return nil }
