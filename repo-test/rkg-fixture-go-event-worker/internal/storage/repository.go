package storage

import (
	"context"
	"time"

	"example.com/rkg-fixture-go-event-worker/internal/domain"
)

type OrderRepository interface {
	FindByID(context.Context, domain.OrderID) (domain.OrderProjection, error)
	Upsert(context.Context, domain.OrderProjection) error
	DeleteOlderThan(context.Context, time.Time) (int64, error)
}
