---
key: TEST-RKG-UI-LIVE-API-001
type: test-evidence
group: evidence
system: SYS-RKG
task_key: TASK-RKG-024
captured_at: 2026-09-28
captured_against:
  artifacts:
    - { key: TASK-RKG-024, revision: 7 }
    - { key: API-RKG-CORE-v1, revision: 9 }
  code_tree: working-tree@4ed6103+task-024
  pins:
    node: "24.20.0"
    npm: "11.19.0"
    cpython: "3.12.14"
command: cd frontend && npm test && npm run lint && npm run build
result: pass
---

# TEST-RKG-UI-LIVE-API-001

Live UI client trên cây `frontend/`, nói với `rkg serve` qua `uv run`:

- `npm test` — 24 Vitest passed. Trong đó `liveRoundtrip` tạo repository,
  từ chối path ngoài allowlist và path không tồn tại, index một app FastAPI,
  search entity đã map `endpoint`, xuất context, đưa job hai app về stage
  `detecting`, rồi kiểm conflict revision, `snapshot_active` và lệch ownership.
- `npm run lint` — oxlint exit 0 (warnings only).
- `npm run build` — TypeScript project build + Vite production bundle.
- `test_cors_reflects_loopback_origin_only` — origin loopback được phản chiếu;
  origin khác không có `Access-Control-Allow-Origin`.

Không ghi đường dẫn máy, token hay transcript.
