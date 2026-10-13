package messaging

import "context"

type EventPublisher interface {
	Publish(context.Context, string, []byte, []byte) error
	Close() error
}
