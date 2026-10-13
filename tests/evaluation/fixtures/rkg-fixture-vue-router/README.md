# rkg-fixture-vue-router

Static Vue Router fixture for `rkg.vue-router`. Source is not executed.

## Routes

`createRouter` in `src/router/index.ts`:

| Path | Name | Page |
|---|---|---|
| `/` | `home` | `src/views/Home.vue` |
| `/orders` | `orders` | `src/views/Orders.vue` (`ORDERS_PATH`) |
| `/orders/:orderId` | `order-detail` | `src/views/OrderDetail.vue` (child) |
| `/admin` | `admin` | `src/views/AdminLayout.vue` |
| `/admin/users` | `users` | `src/views/Users.vue` (`USERS_SEGMENT`) |

`new Router` in `src/router/legacy.ts`:

| Path | Name | Page |
|---|---|---|
| `/legacy` | `legacy` | `src/views/Legacy.vue` |

Page components are lazy `import()` of exactly one `.vue` file. Each page exposes `setup`.

## Navigation

| Caller | Call | Handler |
|---|---|---|
| `src.navigation.openOrders.openOrders` | `router.push(ORDERS_PATH)` | `src.views.Orders.setup` |
| `src.navigation.openOrders.openUsers` | `router.push({ name: "users" })` | `src.views.Users.setup` |
| `src.router.legacy.openLegacy` | `legacyRouter.replace("/legacy")` | `src.views.Legacy.setup` |

`src/navigation/Ambiguous.vue` calls `router.push` with a parameter. That destination is not one literal route: diagnostic only, no `calls` edge.
