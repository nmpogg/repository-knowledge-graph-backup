package config

import (
	"errors"
	"fmt"
	"strings"
	"time"
)

type LookupEnv func(string) (string, bool)

type Config struct {
	KafkaBrokers    []string
	KafkaGroupID    string
	DatabaseURL     string
	CleanupInterval time.Duration
}

func Load(lookup LookupEnv) (Config, error) {
	brokers, err := required(lookup, "KAFKA_BROKERS")
	if err != nil {
		return Config{}, err
	}
	groupID, err := required(lookup, "KAFKA_GROUP_ID")
	if err != nil {
		return Config{}, err
	}
	databaseURL, err := required(lookup, "DATABASE_URL")
	if err != nil {
		return Config{}, err
	}
	intervalText, err := required(lookup, "CLEANUP_INTERVAL")
	if err != nil {
		return Config{}, err
	}
	interval, err := time.ParseDuration(intervalText)
	if err != nil || interval <= 0 {
		return Config{}, errors.New("CLEANUP_INTERVAL must be a positive duration")
	}
	return Config{
		KafkaBrokers:    splitNonEmpty(brokers),
		KafkaGroupID:    groupID,
		DatabaseURL:     databaseURL,
		CleanupInterval: interval,
	}, nil
}

func required(lookup LookupEnv, key string) (string, error) {
	value, ok := lookup(key)
	if !ok || strings.TrimSpace(value) == "" {
		return "", fmt.Errorf("required environment variable %s is missing", key)
	}
	return strings.TrimSpace(value), nil
}

func splitNonEmpty(value string) []string {
	parts := strings.Split(value, ",")
	brokers := make([]string, 0, len(parts))
	for _, part := range parts {
		if broker := strings.TrimSpace(part); broker != "" {
			brokers = append(brokers, broker)
		}
	}
	return brokers
}
