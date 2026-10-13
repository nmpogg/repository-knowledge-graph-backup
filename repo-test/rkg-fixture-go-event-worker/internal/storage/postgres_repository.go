package storage

import (
	"context"
	"fmt"
	"time"

	"example.com/rkg-fixture-go-event-worker/internal/domain"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgconn"
)

type PgxDB interface {
	QueryRow(context.Context, string, ...any) pgx.Row
	Exec(context.Context, string, ...any) (pgconn.CommandTag, error)
}

type PostgresRepository struct {
	db PgxDB
}

func NewPostgresRepository(db PgxDB) *PostgresRepository {
	return &PostgresRepository{db: db}
}

func (r *PostgresRepository) FindByID(ctx context.Context, id domain.OrderID) (domain.OrderProjection, error) {
	var projection domain.OrderProjection
	if err := r.db.QueryRow(ctx, FindByIDSQL, id).Scan(&projection.ID, &projection.Status, &projection.UpdatedAt); err != nil {
		return domain.OrderProjection{}, fmt.Errorf("find order projection: %w", err)
	}
	return projection, nil
}

func (r *PostgresRepository) Upsert(ctx context.Context, projection domain.OrderProjection) error {
	if _, err := r.db.Exec(ctx, UpsertSQL, projection.ID, projection.Status, projection.UpdatedAt); err != nil {
		return fmt.Errorf("upsert order projection: %w", err)
	}
	return nil
}

func (r *PostgresRepository) DeleteOlderThan(ctx context.Context, cutoff time.Time) (int64, error) {
	tag, err := r.db.Exec(ctx, DeleteOlderThanSQL, cutoff)
	if err != nil {
		return 0, fmt.Errorf("delete old order projections: %w", err)
	}
	return tag.RowsAffected(), nil
}
