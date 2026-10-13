package domain

import (
	"encoding/json"
	"errors"
	"fmt"
	"time"
)

var ErrInvalidEvent = errors.New("invalid order event")

type EventEnvelope struct {
	Type       string      `json:"type"`
	OrderID    OrderID     `json:"order_id"`
	Status     OrderStatus `json:"status"`
	OccurredAt time.Time   `json:"occurred_at"`
}

func DecodeEvent(payload []byte) (EventEnvelope, error) {
	var event EventEnvelope
	if err := json.Unmarshal(payload, &event); err != nil {
		return EventEnvelope{}, fmt.Errorf("%w: malformed JSON", ErrInvalidEvent)
	}
	if event.Type == "" || event.OrderID == "" || event.Status == "" || event.OccurredAt.IsZero() {
		return EventEnvelope{}, fmt.Errorf("%w: required field missing", ErrInvalidEvent)
	}
	return event, nil
}
