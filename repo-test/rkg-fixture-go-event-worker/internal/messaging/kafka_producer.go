package messaging

import (
	"context"
	"fmt"

	"github.com/segmentio/kafka-go"
)

type KafkaWriter interface {
	WriteMessages(context.Context, ...kafka.Message) error
	Close() error
}

type KafkaProducer struct {
	writer KafkaWriter
}

func NewKafkaWriter(brokers []string) *kafka.Writer {
	return &kafka.Writer{
		Addr:     kafka.TCP(brokers...),
		Balancer: &kafka.Hash{},
	}
}

func NewKafkaProducer(writer KafkaWriter) *KafkaProducer {
	return &KafkaProducer{writer: writer}
}

func (p *KafkaProducer) Publish(ctx context.Context, topic string, key, payload []byte) error {
	message := kafka.Message{Topic: topic, Key: key, Value: payload}
	if err := p.writer.WriteMessages(ctx, message); err != nil {
		return fmt.Errorf("publish Kafka message: %w", err)
	}
	return nil
}

func (p *KafkaProducer) Close() error {
	return p.writer.Close()
}
