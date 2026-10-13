---
key: TEST-RKG-UI-MVP-MOCK-001
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-017
captured_at: 2026-09-24
captured_against:
  artifacts:
    - { key: TASK-RKG-017, revision: 10 }
    - { key: UIS-RKG-001, revision: 6 }
    - { key: API-RKG-CORE-v1, revision: 9 }
  code_tree: frontend-mvp-mock-ui@09c7d74
  pins:
    node: "24.20.0"
    npm: "11.19.0"
command: cd frontend && npm run lint && npm test && npm run build
result: pass
---

# TEST-RKG-UI-MVP-MOCK-001

Smoke M0 UI trên cây `frontend/` (mock client):

- `npm run lint` — oxlint exit 0 (warnings only).
- `npm test` — 5 Vitest passed (`App` repositories landing; mock list/create
  reject outside path; subgraph + technologies; context export `schema_version`).
- `npm run build` — TypeScript project build + Vite production bundle.

Không chạy live backend. Repository/snapshot destructive guards thuộc
TASK-RKG-025 evidence riêng.
