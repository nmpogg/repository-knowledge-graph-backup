---
key: TEST-RKG-PILOT-CORPUS-003
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-022
captured_against:
  pilot_tree_sha256: a094fc7b39def8636e2b73766d80510c4f4b917ea1da5a6e93e22619ef237417
  prior_pilot_tree_sha256: 7acca861c59558ded14fc9aade5cebe35e9cb627c3d803331990d404371dda2c
  artifacts:
    - { key: TEST-RKG-PILOT-CORPUS-001, revision: historical }
    - { key: TEST-RKG-PILOT-CORPUS-002, revision: historical }
---

# TEST-RKG-PILOT-CORPUS-003 — Replacement pilot baseline

The pinned 0.1.0 tree is not on this machine, and git does not contain it.
`../pilot_fastapi` is a new synthetic baseline, version 0.2.0. It is not a
restoration of digest `7acca861c59558ded14fc9aade5cebe35e9cb627c3d803331990d404371dda2c`.

`tests/integration/test_pilot_corpus.py` now pins
`a094fc7b39def8636e2b73766d80510c4f4b917ea1da5a6e93e22619ef237417`.
`TEST-RKG-PILOT-REVIEW-001.json`, its summary, and
`TEST-RKG-KPI002-SAMPLE-LOCK-002.json` still describe the lost tree. They are
not the sample for this baseline.

The digest covers 18 files. Python sources are 15 files and 629 non-blank
lines, under the 500-file and 50,000-SLOC pilot ceiling. Twelve domain modules
repeat one template. `uv.lock` pins aiokafka 0.14.0 so the messaging adapter
is selected. Indexed edges include imports 36, calls 48, implements 12,
maps_to 12, reads 12, writes 12, publishes 12, and consumes 12. These counts
are candidate facts, not a precision result.

| Check | Result |
| --- | --- |
| Sibling source tree digest | `a094fc7b39def8636e2b73766d80510c4f4b917ea1da5a6e93e22619ef237417` |
| `pytest tests/integration/test_pilot_corpus.py -q` | 2 passed |
