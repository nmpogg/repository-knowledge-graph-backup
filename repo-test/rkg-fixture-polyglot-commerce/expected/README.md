# Expected semantic inventory
The `.yaml` files use JSON syntax, which is valid YAML 1.2. They are human-authored semantic oracles, not analyzer output and not RKG product requirements.

- `applications.yaml`: four independent composition roots and manifest ownership.
- `technologies.yaml`: exact stack declarations, detected-only tooling, prohibited guesses.
- `entities.yaml`: adapter-local identities and a separately labelled post-merge target.
- `edges.yaml`: source-backed relationships and separately labelled linker expectations.
- `diagnostics.yaml`: malformed syntax, unsupported files and deliberately unresolved inputs.
- `prohibited-values.txt`: synthetic exclusion sentinel; never copy this value to graph/log/report.

Evidence is a repository-relative path plus a unique `RKG_EXPECT` marker or a source line and rule intent. Semantic keys are stable across reindexing and never use generated graph hashes. In particular `Order` in Java and TypeScript, GET/POST on the same URL, and tables in different schemas remain distinct.

`exact` means the fixture requires the fact when the responsible adapter supports that capability. `optional` / `detected_only` must not be promoted to mandatory runtime wiring. `prohibited` facts must never be inferred. Post-merge entries are integration targets, separate from adapter-local facts; their inclusion does not claim that current RKG supports every listed link.

Run `python scripts/verify-inventory.py` to verify evidence, identities and size. It checks the fixture inventory; it does not pretend to run or score RKG.
