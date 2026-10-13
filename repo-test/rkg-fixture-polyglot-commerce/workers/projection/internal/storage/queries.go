package storage

// RKG_EXPECT: projection-table-sql
const FindByIDSQL = `SELECT order_id, status, updated_at
FROM commerce.order_projection
WHERE order_id = $1`

const UpsertSQL = `INSERT INTO commerce.order_projection (order_id, status, updated_at)
VALUES ($1, $2, $3)
ON CONFLICT (order_id) DO UPDATE
SET status = EXCLUDED.status, updated_at = EXCLUDED.updated_at`

const DeleteOlderThanSQL = `DELETE FROM commerce.order_projection
WHERE updated_at < $1`
