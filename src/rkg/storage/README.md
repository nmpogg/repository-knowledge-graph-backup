# Storage handoff (T-013 → T-015)

`Storage` owns the embedded Kùzu connection, schema migrations (`SchemaMeta`),
repository/snapshot catalog rows, and minimal Job/Conversation helpers used by
delete guards. Graph fact publication lives in `rkg.graph.publish_fact_batch`.

## Index job integration points

1. Ensure repository exists (`storage.get_repository`).
2. Create/update Job rows (`storage.create_job` / `storage.update_job`);
   non-terminal stages block `delete_repository` (`repository_busy`).
3. Build a domain `FactBatch` and call `publish_fact_batch(storage, batch, meta)`.
   Validation runs first; atomic write + auto-activate on success.
4. On analyzer failure, mark the job terminal (`failed`) without calling publish —
   previous `active_snapshot_id` stays put.
5. For graph reads, `with storage.pin_reader(repo_id, snap_id): ...` so deletes
   return `snapshot_in_use` / `repository_in_use` while the pin is held.

Physical schema: `.aide/tech-specs/RKG-GRAPH/schema/DDL-RKG-GRAPH.cypher`
(implements `TBL-RKG-GRAPH`). Migrations never drop the user database.

## Conversation handoff (T-018)

Turn policy, redaction and restart recovery live in `rkg.conversations`.
Opening `Storage` marks leftover pending turns `interrupted` without changing
focus or the pinned snapshot. `delete_conversation` raises `conversation_busy`
while a turn is still `pending`.
