# Domain handoff (T-002)

`models.py` defines immutable DTOs used between the analyzer and graph service.
`ids.py` generates opaque SHA-256 IDs using JSON-framed identity fields, and
`validation.py` rejects invalid candidate facts before storage. These modules do
not parse source or write Kùzu.

## Identity rules

- `Repository` is a catalog/graph root, not an adapter-emitted `Entity`.
- Ordinary source entity: repository + relative file path + entity type +
  qualified name. Line movement does not change its ID.
- Endpoint: the source identity above plus method, full route path and ordered
  registration-chain IDs. A chain entry must identify a registration site, not
  merely a router name; this keeps duplicate method/path registrations distinct.
- DataResource: repository + resource kind + namespace + adapter identity fields.
  MessageChannel: repository + channel kind + namespace + name. Configuration:
  repository + kind + owner + key; the value is never a fact.
- HTTP origin: `ExternalDependency` with an empty path and identity
  `http_service:{origin}`; only scheme, host and a non-default port are kept.
- Edge: snapshot + type + source + target. Multiple call sites for the same pair
  aggregate as one edge with multiple evidence IDs.
- Evidence: snapshot + relative file path + line range + versioned rule ID.
- Effective scan config digest: canonical JSON of limits/patterns, SHA-256. Host
  roots and credentials are not part of this DTO or digest.

All adapter paths handed to these helpers must already be normalized to a
repository-relative POSIX path. T-003 owns path canonicalization and the source
boundary. The validator still rejects absolute/traversal paths as defense in depth.

## Handoffs

- T-003/T-004/T-005–012: emit `FactBatch` with `Entity`, `Edge`, `Evidence` and
  `Diagnostic`; use ID helpers. Unresolved cases emit diagnostics, not guessed
  edges. `SourceScanConfig` holds effective limits/patterns only; allowed host
  roots remain server-owned.
- T-015: call `validate_fact_batch` before atomic publication via
  `rkg.graph.publish_fact_batch`. `Repository` is the permitted source of
  `exposes` and `depends_on` edges. Physical Entity PKs are snapshot-qualified
  (`{snapshot_id}:{domain_id}`); decode with `rkg.graph.logical_entity_id` on
  read. See `src/rkg/storage/README.md` and `src/rkg/graph/README.md`.
- T-014/T-016: `ContextPackage` and `context_json` supply deterministic shape
  and collection order. T-014 owns traversal/budget/truncation via
  `rkg.graph.search_entities` / `traverse_subgraph` / `build_context`. T-016
  maps that contract in `src/rkg/api` (`POST /api/v1/context`). DTO-only tests
  are not a full AC-RKG-010 verification.

Golden fixture: `tests/fixtures/domain/source_structure.json`. It covers nested
lexical `contains` shape without executing repository source.
