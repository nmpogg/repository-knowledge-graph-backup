// MIG-RKG-CHATBOT-v3 — revision 1; implements TBL-RKG-GRAPH revision 13.
// Candidate physical migration: SchemaMeta version 2 -> 3, Kuzu 0.11.3.
// Runner MUST verify exactly one SchemaMeta(id='current', version=2) before execution.
// If version=3 verify Turn.response_metadata_json STRING and perform no writes.
// If any other version/shape is present refuse; do not guess or partially upgrade.
// Bind $applied_at to the runner timestamp. One connection; failure rolls back.
// Adds a nullable column only; never backfills old answers/flags/request hashes/state.
// Tested on disposable fixture databases, not applied to the user's database.
BEGIN TRANSACTION;
ALTER TABLE Turn ADD response_metadata_json STRING;
MATCH (m:SchemaMeta {id: 'current'})
SET m.version = 3, m.applied_at = timestamp($applied_at);
COMMIT;
