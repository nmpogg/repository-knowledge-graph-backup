# Graph service (CMP-RKG-GRAPH)

## Publish (T-013 → T-015)

`publish_fact_batch(storage, batch, meta)` validates then atomically writes and
auto-activates. See module docstring in `__init__.py`.

## Reads (T-014, HTTP in T-016)

| API | Role |
| --- | --- |
| `search_entities` / `get_entity` | Deterministic search; order type → qualified_name → id |
| `traverse_subgraph` | BFS; direction / edge_types / depth / node+edge budgets; cycles via visited set |
| `build_context` | Bounded `ContextPackage` + `max_chars` truncation |

Search `q`: case-insensitive substring on `name`, `qualified_name`, and endpoint
`METHOD path`. Truncation reasons: `depth_limit`, `max_nodes`, `max_edges`,
`max_chars`.

Typed guards, mapped by `src/rkg/api` (T-016): `NoActiveSnapshotError` (409),
`SnapshotUnavailableError` (410), `NotFoundError` (404), `InvalidBudgetError` (422).

Pin readers with `storage.pin_reader` inside each read entrypoint.
