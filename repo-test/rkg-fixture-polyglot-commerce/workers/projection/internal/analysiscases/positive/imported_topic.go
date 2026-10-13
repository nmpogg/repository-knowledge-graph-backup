package positive

import (
	"context"

	msg "example.com/rkg-fixture-polyglot-commerce/projection/internal/messaging"
)

type Marker struct{}

func PublishProjection(ctx context.Context, publisher msg.EventPublisher, payload []byte) error {
	return publisher.Publish(ctx, msg.ProjectionUpdatedTopic, nil, payload)
}
