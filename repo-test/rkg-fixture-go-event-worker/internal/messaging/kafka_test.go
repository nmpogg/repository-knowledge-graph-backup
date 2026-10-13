package messaging

import (
	"context"
	"testing"

	"github.com/segmentio/kafka-go"
)

func TestKafkaConsumerDelegatesAndCommits(t *testing.T) {
	reader := &readerStub{messages: []kafka.Message{{Key: []byte("k"), Value: []byte("v")}}}
	handler := &handlerStub{}
	consumer := NewKafkaConsumer(reader)
	if err := consumer.Run(context.Background(), handler); err != nil {
		t.Fatalf("Run() error = %v", err)
	}
	if handler.calls != 1 || string(handler.last.Value) != "v" {
		t.Fatalf("handler = calls %d, message %#v", handler.calls, handler.last)
	}
	if reader.commits != 1 {
		t.Fatalf("commits = %d, want 1", reader.commits)
	}
}

func TestKafkaProducerUsesRequestedTopicWithoutNetwork(t *testing.T) {
	writer := &writerStub{}
	producer := NewKafkaProducer(writer)
	if err := producer.Publish(context.Background(), ProjectionUpdatedTopic, []byte("k"), []byte("v")); err != nil {
		t.Fatalf("Publish() error = %v", err)
	}
	if len(writer.messages) != 1 || writer.messages[0].Topic != ProjectionUpdatedTopic {
		t.Fatalf("messages = %#v", writer.messages)
	}
}

func TestConstructorsHaveNoClientSideEffects(t *testing.T) {
	reader := &readerStub{}
	writer := &writerStub{}
	_ = NewKafkaConsumer(reader)
	_ = NewKafkaProducer(writer)
	if reader.fetches != 0 || reader.commits != 0 || len(writer.messages) != 0 {
		t.Fatal("constructor performed client I/O")
	}
}

type readerStub struct {
	messages []kafka.Message
	fetches  int
	commits  int
}

func (r *readerStub) FetchMessage(context.Context) (kafka.Message, error) {
	r.fetches++
	if len(r.messages) == 0 {
		return kafka.Message{}, context.Canceled
	}
	message := r.messages[0]
	r.messages = r.messages[1:]
	return message, nil
}

func (r *readerStub) CommitMessages(_ context.Context, messages ...kafka.Message) error {
	r.commits += len(messages)
	return nil
}

func (r *readerStub) Close() error { return nil }

type writerStub struct {
	messages []kafka.Message
	err      error
}

func (w *writerStub) WriteMessages(_ context.Context, messages ...kafka.Message) error {
	w.messages = append(w.messages, messages...)
	return w.err
}

func (w *writerStub) Close() error { return nil }

type handlerStub struct {
	calls int
	last  Message
	err   error
}

func (h *handlerStub) HandleMessage(_ context.Context, message Message) error {
	h.calls++
	h.last = message
	return h.err
}
