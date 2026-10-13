package app

import (
	"context"
	"fmt"
	"log/slog"
	"time"

	"example.com/rkg-fixture-go-event-worker/internal/storage"
)

type Cleanup struct {
	repository storage.OrderRepository
	interval   time.Duration
	retention  time.Duration
	logger     *slog.Logger
}

func NewCleanup(repository storage.OrderRepository, interval, retention time.Duration, logger *slog.Logger) *Cleanup {
	return &Cleanup{repository: repository, interval: interval, retention: retention, logger: logger}
}

func (c *Cleanup) Run(ctx context.Context) error {
	ticker := time.NewTicker(c.interval)
	defer ticker.Stop()
	for {
		select {
		case <-ctx.Done():
			return nil
		case now := <-ticker.C:
			deleted, err := c.repository.DeleteOlderThan(ctx, now.Add(-c.retention))
			if err != nil {
				return fmt.Errorf("clean old projections: %w", err)
			}
			c.logger.InfoContext(ctx, "projection cleanup completed", "deleted", deleted)
		}
	}
}
