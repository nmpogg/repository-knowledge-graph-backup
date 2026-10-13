# HTTP transport (CMP-RKG-TRANSPORT)

Handoff for T-021 and T-024.

`create_app(storage, policy, session_token=...)` serves `/api/v1`.

- Mutations and `POST /context` require `X-RKG-Session` and a loopback `Host`.
  A present `Origin` must also be loopback.
- The token is `RKG_SESSION_TOKEN` when set. Otherwise `rkg serve` keeps one
  in-memory token and does not print it. The UI must send that same value.
- Loopback browser origins are reflected for CORS. Other origins are not.
- Graph reads take `snapshot_id`. Omit it and pass `repository_id` to use the
  active snapshot (`409 no_active_snapshot` when none exists).
- Entity `type` values are the domain enum (`Endpoint`, `Callable`, …). The
  live UI client maps them onto the M0 labels.
- Index jobs return `202` and `Retry-After: 1` until the stage is terminal.
- `POST/GET /conversations`, `GET /conversations/{id}/turns` and
  `POST /conversations/{id}/turns` call the conversation service. Delete returns
  `409 conversation_busy` while a turn is pending. A failed provider call returns
  `502`, `503 llm_disabled` or `504 llm_timeout` and does not move committed
  focus. `GET .../turns` returns `410 snapshot_unavailable` when the pin is gone
  and does not switch the conversation to another snapshot.
