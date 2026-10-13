package config

import (
	"strings"
	"testing"
	"time"
)

func TestLoadValidConfig(t *testing.T) {
	values := map[string]string{
		"KAFKA_BROKERS":    "kafka-1:9092, kafka-2:9092",
		"KAFKA_GROUP_ID":   "projection-worker",
		"DATABASE_URL":     "postgres://example",
		"CLEANUP_INTERVAL": "15m",
	}
	cfg, err := Load(func(key string) (string, bool) { value, ok := values[key]; return value, ok })
	if err != nil {
		t.Fatalf("Load() error = %v", err)
	}
	if len(cfg.KafkaBrokers) != 2 || cfg.CleanupInterval != 15*time.Minute {
		t.Fatalf("config = %#v", cfg)
	}
}

func TestLoadRejectsInvalidValuesWithoutLeakingThem(t *testing.T) {
	values := map[string]string{
		"KAFKA_BROKERS":    "kafka:9092",
		"KAFKA_GROUP_ID":   "worker",
		"DATABASE_URL":     "RKG_TEST_SECRET_DO_NOT_PERSIST",
		"CLEANUP_INTERVAL": "not-a-duration",
	}
	_, err := Load(func(key string) (string, bool) { value, ok := values[key]; return value, ok })
	if err == nil || strings.Contains(err.Error(), values["DATABASE_URL"]) {
		t.Fatalf("Load() error = %v", err)
	}
}
