---
key: PLAN-TASK-RKG-035
group: evidence
revision: 1
type: implementation-plan
task: TASK-RKG-035
---
# PLAN-TASK-RKG-035 — Whole-flow AC verification

1. Refresh context/pins after TASK034 review; test-only work may prepare against its frozen candidate. Keep signed normative sources unchanged.
2. Add meaningful synthetic whole-flow regressions: endpoint lookup/handler/indirect exact citations, clarification resume after restart, concurrent pending/replay/state failure guards, malicious schemas/foreign/cyclic/directional outputs and input/model/graph budgets. Reuse existing storage fault injection and protocol tests rather than mirror implementation.
3. Run full backend unit/integration/conformance excluding live-provider/operator corpus; full frontend Vitest including loopback API roundtrip with API key unset, lint/build.
4. Run browser on production Ask code, served locally with live client and actual synthetic API/custom bounded mock provider. Check vi/en, light/dark, mobile/desktop, greeting, entity choice, claims closed, exact source disclosure/Escape/Tab/focus, limits after reload, unavailable history and readable long names. Export only assertions/counts/pins, never DOM/raw transcript/source/config or screenshots.
5. Record per-AC passed/failed/not_run with source/code revision and test provenance. Live-provider quality, human walkthrough/UAT and operator DB migration are not_run unless actually authorized and executed; no invented acceptance.
6. Freeze test/evidence/code references for independent adversarial review (max two rounds), repair actual findings. Mark done only with current-tree verification and independent review; preserve human gate signature as separate pending decision.
