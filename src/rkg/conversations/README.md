# Conversation handoff (T-018 → T-020 / T-021)

`rkg.conversations` persists conversation, turn and structured focus on the same
Kùzu database as the graph. It does not call an LLM and does not expose HTTP.

## Lifecycle

1. `create_conversation` pins `snapshot_id`, or the repository active snapshot
   when `snapshot_id` is omitted. Later publishes do not move that pin.
2. `begin_turn` / `submit_turn` require `client_request_id` and
   `expected_revision`. Missing, empty, boolean or non-positive revision is
   `invalid_turn_request` (HTTP 422) and writes nothing.
3. A positive revision that is not current is `conversation_conflict` (409).
   The same `(conversation_id, client_request_id)` with a different body is also
   `conversation_conflict` and is not overwritten. The same body replays the
   stored turn and does not call the provider again.
4. `Turn.id` is `turn_` plus the full lowercase SHA-256 of
   `conversation_id + ":" + client_request_id`.
5. Accepting a new turn commits status `pending` and increments revision, then
   returns before the provider runs. `submit_turn` finalizes in a second
   transaction. Provider exceptions become status `failed` and do not change
   focus.
6. Opening `Storage` marks leftover `pending` turns `interrupted`. History and
   focus already committed stay. Delete is `conversation_busy` only while a
   turn is `pending`.
7. `cleanup_snapshots` deletes snapshots that are not active, not reader-pinned
   and not referenced by a conversation. `read_conversation` on a missing or
   non-ready pin raises `snapshot_unavailable` (410) and leaves the pin unchanged.

## Redaction

Question, answer, title, claims and citation quotes are stored only after
`redact_conversation_text`. Chain-of-thought keys are dropped. Operational
logger `rkg.conversation` records ids, status and error codes only.

History-window budgeting (AC-RKG-032) and grounded answering are implemented
by T-020 below.
`src/rkg/api` maps create, list, history, turn and delete onto this service.
Pending delete is `409 conversation_busy`. Provider failure codes map to
HTTP 502/503/504. Reading a conversation whose pin is gone is
`410 snapshot_unavailable`.

## Grounded Q&A (T-020)

`submit_grounded_turn(storage, conversation_id, question=...,
client_request_id=..., expected_revision=..., provider=...)` uses the same
pending/finalize transaction boundary. Pass an `OpenRouterProvider` for live
answers or `MockProvider` for deterministic contract tests. The result wraps
the persisted submission with `history_truncated`, `retrieval_truncated` and
`limitations` for the later HTTP layer.

Each turn keeps at most six completed history turns and 4,000 history tokens,
retaining focus and ordered pending candidate IDs separately. An explicit
`root_id`, a qualified/underscored entity name, an ordinal clarification
choice or a clear pronoun follow-up can resolve the root deterministically.
Otherwise a schema-limited model plan
chooses between a bounded entity search, existing focus/candidate, or an
insufficient-evidence result. Only `search_entities`, `get_entity` and
`build_context` access the pinned graph; the model cannot issue raw queries.

The second model call selects edge IDs from the bounded context. The service
checks those IDs and their evidence against the pinned snapshot, then renders
relation claims from graph facts. Unknown, ambiguous, truncated and malformed
results return a clarification, insufficient evidence or a stable `llm_*`
error without inventing a graph fact. Provider failures keep committed focus.
HTTP status mapping lives in `src/rkg/api/conversations.py`. Large pilot
evaluation remains T-022.
