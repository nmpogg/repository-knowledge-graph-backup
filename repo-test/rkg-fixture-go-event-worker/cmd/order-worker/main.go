package main

import (
	"context"
	"log/slog"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"example.com/rkg-fixture-go-event-worker/internal/app"
	"example.com/rkg-fixture-go-event-worker/internal/config"
	"example.com/rkg-fixture-go-event-worker/internal/messaging"
	"example.com/rkg-fixture-go-event-worker/internal/storage"
	"github.com/jackc/pgx/v5/pgxpool"
)

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))
	if err := run(logger); err != nil {
		logger.Error("worker stopped")
		os.Exit(1)
	}
}

func run(logger *slog.Logger) error {
	cfg, err := config.Load(os.LookupEnv)
	if err != nil {
		return err
	}
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	pool, err := pgxpool.New(ctx, cfg.DatabaseURL)
	if err != nil {
		return err
	}
	defer pool.Close()

	repository := storage.NewPostgresRepository(pool)
	producer := messaging.NewKafkaProducer(messaging.NewKafkaWriter(cfg.KafkaBrokers))
	defer producer.Close()
	processor := app.NewProcessor(repository, producer, logger)
	consumer := messaging.NewKafkaConsumer(messaging.NewKafkaReader(cfg.KafkaBrokers, cfg.KafkaGroupID))
	defer consumer.Close()
	cleanup := app.NewCleanup(repository, cfg.CleanupInterval, 30*24*time.Hour, logger)

	return supervise(ctx, consumer, processor, cleanup)
}

type runner interface {
	Run(context.Context) error
}

func supervise(ctx context.Context, consumer messaging.EventConsumer, handler messaging.MessageHandler, cleanup runner) error {
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()
	errors := make(chan error, 2)
	var workers sync.WaitGroup
	workers.Add(2)
	go func() {
		defer workers.Done()
		errors <- consumer.Run(ctx, handler)
	}()
	go func() {
		defer workers.Done()
		errors <- cleanup.Run(ctx)
	}()

	select {
	case <-ctx.Done():
		cancel()
		workers.Wait()
		return nil
	case err := <-errors:
		cancel()
		workers.Wait()
		return err
	}
}
