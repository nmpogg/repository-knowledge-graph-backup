# RKG fixture: Nuxt 4 order portal

Standalone Nuxt 4 full-stack fixture for repository-knowledge-graph analysis. It
contains Vue SFCs, file-based UI routing, Nuxt auto-imports, Nitro handlers,
runtime configuration, deterministic in-memory data, and intentional negative
cases. It does not contain RKG implementation code.

## Versions

- Node.js 24.15.0 LTS
- npm 11.12.1
- Nuxt 4.5.2 (Nitro 2.13.4 and Vite 8.3.2 in the resolved lockfile)
- Vue 3.5.43 and Vue Router 5.3.1
- TypeScript 5.9.3 and vue-tsc 3.3.12
- Vitest 5.0.3, Nuxt Test Utils 4.3.3, and Vue Test Utils 2.5.1
- ESLint 10.12.0 with `@nuxt/eslint` 1.17.0

Versions are exact in `package.json`; the full transitive graph is locked by
`package-lock.json`.

## Install, run, and verify

```bash
npm ci
cp .env.example .env
npm run dev
```

The application uses Nitro and needs no separate backend or database. Its
repository resets to the same two in-memory orders on every process start.

Acceptance commands:

```bash
npm ci
npm run lint
npm test -- --run
npm run typecheck
npm run build
```

## UI route inventory

| Source file | Qualified page | UI route | Notes |
| --- | --- | --- | --- |
| `app/pages/index.vue` | `pages/index` | `/` | static index page |
| `app/pages/orders/index.vue` | `pages/orders/index` | `/orders` | index page; auto-imports `useOrders` and `OrderCard` |
| `app/pages/orders/[orderId].vue` | `pages/orders/[orderId]` | `/orders/:orderId` | dynamic segment and relative `useFetch` |
| `app/pages/account/profile.vue` | `pages/account/profile` | `/account/profile` | nested route with `account` middleware |

These paths are deterministic consequences of Nuxt's `app/pages` convention.
`definePageMeta` literals are page metadata, and the account page declares both
the middleware and `requiresAccount` flag. UI routes are distinct from the HTTP
endpoints below.

## Nitro HTTP endpoint inventory

| Source file | Method and path | Handler declarations |
| --- | --- | --- |
| `server/api/orders/index.get.ts` | `GET /api/orders` | `createListOrdersHandler`, `listOrdersHandler`, default event handler |
| `server/api/orders/[orderId].get.ts` | `GET /api/orders/:orderId` | `createGetOrderHandler`, `getOrderHandler`, default event handler |
| `server/api/orders/[orderId]/cancel.post.ts` | `POST /api/orders/:orderId/cancel` | `createCancelOrderHandler`, `cancelOrderHandler`, default event handler |

Dynamic parameters are read with H3 `getRouterParam`. Importing a handler only
constructs a callable; it does not start a server, open a socket, or make an HTTP
request. Handler factories make service delegation testable without starting
Nitro.

## Source and symbol inventory

Expected Vue SFC source units:

- `app/app.vue` — application root.
- `app/layouts/default.vue` — `useRuntimeConfig` consumer and shared navigation.
- `app/components/OrderCard.vue` — standard `<script lang="ts">`,
  `defineComponent`, typed prop, emitted `cancel` event, explicit child import,
  template usage, and scoped style.
- `app/components/OrderStatusBadge.vue` — `<script setup lang="ts">`, typed prop,
  and scoped style.
- `app/components/ConnectionState.client.vue` — client-only online state.
- The four page files listed in the route table.

Each `.vue` file is one `SourceUnit` with structured template, script, and style
sections. Those sections must not become fabricated source files. CSS does not
need graph entities.

Expected TypeScript symbols include:

- shared `Order` and `OrderStatus`;
- composable `useOrders` and fetch boundary `OrdersFetcher`;
- `OrderRepository` and its `findAll`, `findById`, and `cancel` methods;
- `OrderService`, `OrderNotFoundError`, `fetchInventoryStatus`, and the singleton
  `orderService`;
- all handler factories and named inner handler callables in the endpoint table;
- account middleware helper `hasAccountAccess`.

## Expected calls and dependencies

```text
pages/orders/index -> useOrders -> injected/default $fetch('/api/orders')
pages/orders/index -> $fetch(POST cancellation endpoint) -> useOrders.load
pages/orders/[orderId] -> useFetch(relative order endpoint)
OrderCard.requestCancellation -> emit('cancel', order.id)
Nitro handler -> OrderService method -> OrderRepository method
fetchInventoryStatus -> injected fetcher(static external URL)
default layout -> useRuntimeConfig -> public.portalName
```

The only expected external HTTP origin candidate is
`https://inventory.example.test`. The URL path, request payloads, query strings,
and runtime configuration values are not graph properties.

## Auto-import resolution

Expected convention-backed facts:

- `useOrders` is auto-imported from `app/composables/useOrders.ts` in the orders
  page.
- `OrderCard`, `OrderStatusBadge`, and `ConnectionState` are component
  auto-imports where used without an ES import.
- Nuxt/Vue helpers such as `definePageMeta`, `useRoute`, `computed`, `useFetch`,
  `useRuntimeConfig`, `defineNuxtRouteMiddleware`, and `navigateTo` are framework
  auto-imports.
- `OrderStatusBadge` in `OrderCard.vue` is an ordinary explicit ES import for
  comparison. Server service/repository dependencies are also explicit imports.

Auto-import resolution depends on Nuxt conventions. If an analyzer does not
support the relevant convention, the occurrence remains detected-only; it must
not invent a normal ES import or guess a target. The two negative `useSummary`
symbols are intentionally ambiguous by simple name.

## Configuration inventory

| Runtime key | Environment override | Boundary |
| --- | --- | --- |
| `inventoryApiBase` | `NUXT_INVENTORY_API_BASE` | server-only |
| `inventoryApiKey` | `NUXT_INVENTORY_API_KEY` | server-only placeholder |
| `public.apiBase` | `NUXT_PUBLIC_API_BASE` | public |
| `public.portalName` | `NUXT_PUBLIC_PORTAL_NAME` | public |

Expected graph facts are configuration key names and the boundary above, never
their values. `.env.example` contains placeholders only. A synthetic prohibited
sentinel exists only inside the composable test and verifies that error state does
not retain the thrown value.

## Intentional negative and prohibited cases

- `analysis-cases/negative/dynamic-ui-route.ts`: runtime-built path is not a
  deterministic UI route.
- `dynamic-outbound-url.ts`: computed origin/resource is not a static external
  HTTP dependency.
- `runtime-server-route.ts`: computed registration is outside `server/api` and is
  not a convention-backed Nitro endpoint.
- `shadowed-fetch.ts`: local `$fetch` is a normal function call, not HTTP.
- `admin/useSummary.ts` and `storefront/useSummary.ts`: duplicate simple names
  must retain directory/module identity and must not be guessed as an auto-import.
- `BrokenPanel.vue.fixture`: deliberately malformed SFC used only as a syntax
  error corpus; Nuxt and TypeScript do not compile it.
- `analysis-cases/positive/static-routes.ts`: stable literal controls for route
  and endpoint extraction.

No negative case should create a guessed route, HTTP endpoint, external origin,
auto-import edge, or secret/config-value property.

## Generated and ignored paths

The adapter must apply ignore rules before file-count/file-size limits. The
following trees are generated and excluded by `.gitignore`:

- `.nuxt/**`
- `.output/**`
- `node_modules/**`
- `dist/**`
- `coverage/**`

Generated routes, bundles, and type declarations are not fixture source and must
not be committed or analyzed as authored source.

## Test inventory

- `test/components`: component props, rendering, child usage, and emitted event.
- `test/composables`: successful and failed mocked fetch boundaries.
- `test/pages`: static page rendering and deterministic `/orders` navigation.
- `test/server/handlers.spec.ts`: each Nitro handler delegates to the correct
  service method without server/network startup.
- `test/server/orderRepository.spec.ts`: deterministic copies, lookup, and cancel.
- `test/server/orderService.spec.ts`: repository delegation, missing order, and
  injected static external request.
- `test/config`: private/public runtime configuration boundary and prohibited
  sentinel exclusion.
