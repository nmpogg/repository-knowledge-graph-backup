package negative

import (
	"context"

	"example.com/rkg-fixture-go-event-worker/internal/messaging"
)

type Marker struct{}

// PublishDynamic intentionally uses a runtime topic and must not produce a static channel edge.
func PublishDynamic(ctx context.Context, publisher messaging.EventPublisher, topic string, payload []byte) error {
	return publisher.Publish(ctx, topic, nil, payload)
}
