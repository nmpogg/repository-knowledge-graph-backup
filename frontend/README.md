# Frontend — CMP-RKG-WEB (TASK-RKG-017 MVP)

React + Vite + TypeScript UI with a contract-shaped **mock** client.

## Run

```powershell
npm ci
npm run dev
```

Default entry: `/repositories`. Demo snapshot: open **Orders API (demo)** → Explorer,
or visit `/explorer` and choose the demo snapshot.

## Stack notes

- `@xyflow/react` for the Explorer graph (list fallback always available)
- Design tokens from `.aide/design/ui/tokens/tokens.json` (light/dark)
- Fonts bundled locally (IBM Plex Sans, JetBrains Mono)
- Live client (`VITE_RKG_CLIENT=live`) calls `API-RKG-CORE-v1` and maps domain
  entity types (`Endpoint`, `Callable`, …) onto the M0 labels. Default mode stays
  `mock`.

## Live API

Copy the root `.env.example` to root `.env` if needed. Keep `RKG_SESSION_TOKEN`
and `VITE_RKG_SESSION` equal. Vite reads the root `.env` automatically; the
RKG CLI loads server settings from it. The server does not print the session value.

```powershell
# repo root
uv run rkg serve

# frontend
npm run dev
```

If PowerShell blocks `npm.ps1`, use `npm.cmd ci` and `npm.cmd run dev`.

Leave `VITE_RKG_API_BASE` empty so the dev server proxies `/api` to
`127.0.0.1:8000` (`RKG_API_UPSTREAM` overrides that target). A direct browser
call also works: the API reflects only loopback origins.

Normative UX/API still live under `.aide/`; this folder implements presentation and
may simplify layout without rewriting those artifacts.
