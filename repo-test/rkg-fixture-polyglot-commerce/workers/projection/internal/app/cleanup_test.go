package app

import (
	"context"
	"testing"
	"time"
)

func TestCleanupRunsAndStopsOnCancellation(t *testing.T) {
	repository := &repositoryStub{cutoffs: make(chan time.Time, 1)}
	cleanup := NewCleanup(repository, time.Millisecond, 24*time.Hour, discardLogger())
	ctx, cancel := context.WithCancel(context.Background())
	done := make(chan error, 1)
	go func() { done <- cleanup.Run(ctx) }()

	select {
	case <-repository.cutoffs:
		cancel()
	case <-time.After(time.Second):
		t.Fatal("cleanup did not run")
	}
	select {
	case err := <-done:
		if err != nil {
			t.Fatalf("Run() error = %v", err)
		}
	case <-time.After(time.Second):
		t.Fatal("cleanup did not stop after cancellation")
	}
}
