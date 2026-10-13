---
key: TEST-RKG-UI-REPO-MGMT-MOCK-001
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-025
revision: 2
captured_at: 2026-09-24
captured_against:
  artifacts:
    - { key: TASK-RKG-025, revision: 7 }
    - { key: UIS-RKG-001, revision: 6 }
    - { key: API-RKG-CORE-v1, revision: 9 }
    - { key: FR-RKG-001, revision: 11 }
  code_tree: frontend-repo-mgmt-mock@acb4a7f+local-vi
  pins:
    node: "24.20.0"
    npm: "11.19.0"
command: cd frontend && npm test && npm run lint && npm run build
result: pass
---

# TEST-RKG-UI-REPO-MGMT-MOCK-001

Smoke repository/snapshot management UI trên cây `frontend/` (mock client):

- `npm test` — 10 Vitest passed, gồm:
  - optimistic PATCH + `repository_conflict` on stale revision
  - `snapshot_active` / `snapshot_in_use` delete guards
  - `repository_in_use` on demo conversation pin
  - create → index (publish) → re-index → activate → Explorer query handoff
    → eligible snapshot delete → repository cascade delete
  - ownership mismatch → `404 generic_not_found`
  - App landing heading tiếng Việt `Kho mã`
- `npm run lint` — oxlint exit 0 (warnings only).
- `npm run build` — TypeScript project build + Vite production bundle.

Không chạy live backend. Manual UI states (confirm dialogs, danger zone, edit
conflict banner) covered by implementation against UIS/SCR; automated path is
mock client contract behavior above. Presentation locale: Vietnamese.
