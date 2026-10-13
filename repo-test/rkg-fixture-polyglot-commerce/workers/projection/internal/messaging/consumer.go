package messaging

import "context"

type Message struct {
	Key   []byte
	Value []byte
}

type MessageHandler interface {
	HandleMessage(context.Context, Message) error
}

type EventConsumer interface {
	Run(context.Context, MessageHandler) error
	Close() error
}
