package negative

type localKafka struct{}

func (localKafka) Publish() string { return "local" }

// ShadowedKafka is a local variable, not the imported Kafka package.
func ShadowedKafka() string {
	kafka := localKafka{}
	return kafka.Publish()
}
