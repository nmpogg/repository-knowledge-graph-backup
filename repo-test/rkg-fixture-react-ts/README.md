# rkg-fixture-react-ts

`rkg-fixture-react-ts` is a standalone, runnable Order Operations Console and a golden fixture for static repository analysis. It deliberately exposes unambiguous TypeScript import/call relationships, React Router registrations, configuration reads, and outbound HTTP candidates alongside documented negative cases. It contains no RKG parser or product code.

## Stack and commands

The checked-in manifest uses Node.js `>=22.22.2` (Node 24 LTS recommended), React `19.3.0`, React Router DOM `7.18.4`, TypeScript `6.0.3`, Vite `8.3.2`, Vitest `5.0.3`, Testing Library React `16.3.3`, and ESLint `10.12.0`. Exact transitive versions are recorded in `package-lock.json`.

```bash
npm ci
npm run lint
npm test -- --run
npm run build
npx tsc --noEmit
```

Copy `.env.example` to `.env` only for local development. The UI uses mocked HTTP in tests and needs no backend or network to test or build.

## Module map

```text
main.tsx -> App.tsx -> router.tsx -> layouts/routes
                               OrdersPage -> useOrders -> orderApi -> httpClient
                               OrderDetailPage --------> orderApi -> httpClient
config/environment.ts <------------------------------- httpClient/AdminLayout
analysis-cases/{positive,negative}                     analyzer corpus
```

Navigation routes are browser UI locations registered with React Router. They are not backend HTTP endpoints. Outbound dependencies appear only in service/fetch calls such as `/api/orders` and the inventory origin.

## Expected static-analysis inventory

### Important source symbols

| File | Expected qualified names / intent |
| --- | --- |
| `src/main.tsx` | module entry; `createRoot(...).render(...)` |
| `src/app/App.tsx` | `App`, `AppErrorBoundary.render`, `AppErrorBoundary.componentDidCatch` |
| `src/app/router.tsx` | `appRoutes`, `router`; static registration root |
| `src/app/layouts/RootLayout.tsx` | `RootLayout` and nested `Outlet` |
| `src/app/layouts/AdminLayout.tsx` | `AdminLayout` auth/config guard |
| `src/app/routes/OrdersPage.tsx` | `OrdersPage` -> `useOrders` |
| `src/hooks/useOrders.ts` | `useOrders` -> `orderApi.listOrders` |
| `src/services/orderApi.ts` | `OrderApi.listOrders/getOrder/updateOrder/checkInventory` |
| `src/services/httpClient.ts` | `FetchHttpClient.get/put/request`; `httpClient` |
| `src/config/environment.ts` | `parseEnvironment`, `getEnvironment` |
| `src/components/OrderStatusBadge.tsx` | `OrderStatusBadge` |

### Expected imports and calls

- `main.tsx` default-imports `App`; `OrdersPage.tsx` named-imports `useOrders`, default-imports `LoadingState`, and uses the `@/` alias for `OrderStatusBadge`.
- `aliasedCalls.ts` contains a default import, a named alias (`OrderApi as ApiClient`), a namespace import (`orderTypes`), and an aliased function import (`parseEnvironment as parseEnv`).
- The main unique chain is `OrdersPage -> useOrders -> orderApi.listOrders -> httpClient.get -> FetchHttpClient.request -> globalThis.fetch`.
- `OrderApi.getOrder/updateOrder` call the injected `HttpClient`; `OrderEditPage.submit` is an async function; callbacks and fixture helpers provide arrow functions; environment parsing is synchronous.

### Expected route registration chain

`main.tsx -> App -> RouterProvider(router) -> createBrowserRouter(appRoutes)` registers:

| Pattern | Meaning |
| --- | --- |
| `/` + index child | dashboard |
| `/orders` | order list |
| `/orders/:orderId` | dynamic detail |
| `/orders/:orderId/edit` | dynamic edit |
| imported constant `admin/users` under `AdminLayout` | guarded `/admin/users` |
| `*` | catch-all not found |

Expected configuration keys are exactly `VITE_API_BASE_URL` and `VITE_ENABLE_ADMIN`. The literal external HTTP origin candidate is exactly `https://inventory.example.test`. Relative `/api/orders` paths are application HTTP calls resolved against the configured base URL; query strings, request bodies, headers, and secrets must not become graph facts.

## Intentional negative cases

| File | Fact that must not be created |
| --- | --- |
| `dynamicImport.ts` | no guessed internal import edge from runtime `moduleName` |
| `dynamicUrl.ts` | no guessed external origin from runtime `host` |
| `ambiguousBinding.ts` | no unique call edge for reassigned `send` |
| `shadowedFetch.ts` | no Fetch API/HTTP technology fact for the local `fetch` |
| `syntax-error.invalid.ts.fixture` | no normal TS entity; it is inert unless copied to `syntax-error.ts` in a dedicated corpus branch |

The test-only sentinel `RKG_TEST_SECRET_DO_NOT_PERSIST` exists solely to verify redaction and must never be persisted in an analyzer graph, report, or log. No credential, authorization value, real `.env`, raw payload, or secret is required or committed.

## Safety and determinism

All tests mock the service/client boundary and perform no real network requests. Production source is never executed by an analyzer. This fixture has no backend dependency for installation-time lint, tests, type checking, or build (apart from downloading declared npm packages during `npm ci`).
