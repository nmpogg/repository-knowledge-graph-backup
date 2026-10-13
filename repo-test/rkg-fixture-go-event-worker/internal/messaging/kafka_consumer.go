package messaging

import (
	"context"
	"errors"
	"fmt"

	"github.com/segmentio/kafka-go"
)

type KafkaReader interface {
	FetchMessage(context.Context) (kafka.Message, error)
	CommitMessages(context.Context, ...kafka.Message) error
	Close() error
}

type KafkaConsumer struct {
	reader KafkaReader
}

func NewKafkaReader(brokers []string, groupID string) *kafka.Reader {
	return kafka.NewReader(kafka.ReaderConfig{
		Brokers: brokers,
		GroupID: groupID,
		Topic:   "orders.events",
	})
}

func NewKafkaConsumer(reader KafkaReader) *KafkaConsumer {
	return &KafkaConsumer{reader: reader}
}

func (c *KafkaConsumer) Run(ctx context.Context, handler MessageHandler) error {
	for {
		message, err := c.reader.FetchMessage(ctx)
		if err != nil {
			if errors.Is(err, context.Canceled) || errors.Is(err, context.DeadlineExceeded) {
				return nil
			}
			return fmt.Errorf("fetch Kafka message: %w", err)
		}
		if err := handler.HandleMessage(ctx, Message{Key: message.Key, Value: message.Value}); err != nil {
			return fmt.Errorf("handle Kafka message: %w", err)
		}
		if err := c.reader.CommitMessages(ctx, message); err != nil {
			return fmt.Errorf("commit Kafka message: %w", err)
		}
	}
}

func (c *KafkaConsumer) Close() error {
	return c.reader.Close()
}
