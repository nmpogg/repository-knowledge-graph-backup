package storage

import (
	"context"
	"errors"
	"reflect"
	"testing"
	"time"

	"example.com/rkg-fixture-go-event-worker/internal/domain"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgconn"
)

func TestPostgresRepositorySQLContract(t *testing.T) {
	now := time.Date(2026, 10, 5, 10, 0, 0, 0, time.UTC)
	db := &dbStub{row: &rowStub{values: []any{domain.OrderID("order-9"), domain.OrderStatus("pending"), now}}, tag: pgconn.NewCommandTag("DELETE 3")}
	repository := NewPostgresRepository(db)

	projection, err := repository.FindByID(context.Background(), "order-9")
	if err != nil || projection.ID != "order-9" {
		t.Fatalf("FindByID() = %#v, %v", projection, err)
	}
	if db.query != FindByIDSQL || !reflect.DeepEqual(db.args, []any{domain.OrderID("order-9")}) {
		t.Fatalf("query contract = %q %#v", db.query, db.args)
	}

	want := domain.OrderProjection{ID: "order-9", Status: "completed", AuditFields: domain.AuditFields{UpdatedAt: now}}
	if err := repository.Upsert(context.Background(), want); err != nil {
		t.Fatalf("Upsert() error = %v", err)
	}
	if db.exec != UpsertSQL || len(db.args) != 3 {
		t.Fatalf("upsert contract = %q %#v", db.exec, db.args)
	}

	deleted, err := repository.DeleteOlderThan(context.Background(), now)
	if err != nil || deleted != 3 || db.exec != DeleteOlderThanSQL {
		t.Fatalf("DeleteOlderThan() = %d, %v; query %q", deleted, err, db.exec)
	}
}

type dbStub struct {
	query string
	exec  string
	args  []any
	row   pgx.Row
	tag   pgconn.CommandTag
	err   error
}

func (d *dbStub) QueryRow(_ context.Context, query string, args ...any) pgx.Row {
	d.query, d.args = query, args
	return d.row
}

func (d *dbStub) Exec(_ context.Context, query string, args ...any) (pgconn.CommandTag, error) {
	d.exec, d.args = query, args
	return d.tag, d.err
}

type rowStub struct {
	values []any
	err    error
}

func (r *rowStub) Scan(dest ...any) error {
	if r.err != nil {
		return r.err
	}
	if len(dest) != len(r.values) {
		return errors.New("unexpected destination count")
	}
	for i := range dest {
		switch target := dest[i].(type) {
		case *domain.OrderID:
			*target = r.values[i].(domain.OrderID)
		case *domain.OrderStatus:
			*target = r.values[i].(domain.OrderStatus)
		case *time.Time:
			*target = r.values[i].(time.Time)
		}
	}
	return nil
}
