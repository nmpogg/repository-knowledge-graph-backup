package domain

import (
	"bytes"
	"errors"
	"os"
	"testing"
)

func TestSharedOrderEventContract(t *testing.T) {
	payload, err := os.ReadFile("../../../../contracts/examples/order-event.json")
	if err != nil {
		t.Fatal("shared event example unavailable")
	}
	event, err := DecodeEvent(payload)
	if err != nil {
		t.Fatal("shared event example rejected")
	}
	if event.OrderID != "order-1" || event.Status != OrderPending {
		t.Fatal("event contract mismatch")
	}
}

func TestRejectEventOutsideContract(t *testing.T) {
	payload, err := os.ReadFile("../../../../contracts/examples/order-event.json")
	if err != nil {
		t.Fatal("shared event example unavailable")
	}
	for _, invalid := range [][]byte{
		bytes.ReplaceAll(payload, []byte("order.updated"), []byte("other.event")),
		bytes.ReplaceAll(payload, []byte("CREATED"), []byte("UNKNOWN")),
	} {
		if _, err := DecodeEvent(invalid); !errors.Is(err, ErrInvalidEvent) {
			t.Fatal("invalid envelope accepted")
		}
	}
}
