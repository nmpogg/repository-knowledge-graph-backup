package positive

import (
	"example.com/rkg-fixture-polyglot-commerce/projection/internal/app"
	"example.com/rkg-fixture-polyglot-commerce/projection/internal/messaging"
	"example.com/rkg-fixture-polyglot-commerce/projection/internal/storage"
)

var (
	_ storage.OrderRepository  = (*storage.PostgresRepository)(nil)
	_ messaging.EventPublisher = (*messaging.KafkaProducer)(nil)
	_ messaging.EventConsumer  = (*messaging.KafkaConsumer)(nil)
	_ messaging.MessageHandler = (*app.Processor)(nil)
)
