package domain

import "time"

type OrderID string

type OrderStatus string

const (
	OrderPending   OrderStatus = "pending"
	OrderCompleted OrderStatus = "completed"
	OrderCancelled OrderStatus = "cancelled"
)

type AuditFields struct {
	UpdatedAt time.Time
}

type OrderProjection struct {
	AuditFields
	ID     OrderID
	Status OrderStatus
}

func (o OrderProjection) IsTerminal() bool {
	return o.Status == OrderCompleted || o.Status == OrderCancelled
}

func (o *OrderProjection) Touch(at time.Time) {
	o.UpdatedAt = at
}

func CloneSlice[T any](values []T) []T {
	return append([]T(nil), values...)
}
