# rkg-fixture-django

Static Django URLconf corpus for `rkg.django`. The adapter reads the Python AST
only. It does not import Django or execute this tree. Django ORM is not in scope.

## Attribute choice

`path` is always stored.

- `path()` / included `path()` routes are slash-joined and given one leading `/`.
  Converter syntax such as `<int:pk>` is kept as text.
- `re_path()` and `url()` store the regex literal unchanged. A non-empty include
  prefix is prepended with a trailing slash and the regex is not rewritten.
- `method` is set only from a static method list: `require_GET`, `require_POST`,
  `require_safe`, a literal or uniquely resolved `require_http_methods(...)`
  sequence, or a literal `http_method_names` on the class or `as_view(...)`.
- `path()` does not imply GET. When the method expression is not a literal or a
  resolved constant, the endpoint is still emitted and `method` is omitted.

## Routes that are facts

| Registration | Path attribute | Method | handled_by |
|---|---|---|---|
| `path(HEALTH_ROUTE, health)` | `/health/` | omitted | `shop.views.health` |
| `OrderDetail.as_view()` | `/orders/<int:pk>/` | `GET` from literal `http_method_names = ["get"]` | `shop.views.OrderDetail.get` |
| `BareDetail.as_view()` | `/bare/` | omitted; `http_method_names` is absent | none; `def get` is not guessed |
| `include("shop.urls")` + `path("orders/", create_order)` | `/shop/orders/` | `POST` from `@require_POST` | `shop.views.create_order` |
| included `path("varied/", varied)` | `/shop/varied/` | omitted; `require_http_methods(_method_names())` is a call | `shop.views.varied` |
| `re_path(r"^legacy/$", "shop.views.legacy_report")` | `^legacy/$` | omitted | `shop.views.legacy_report` |
| `url(r"^old/$", health)` | `^old/$` | omitted | `shop.views.health` |

`include("shop.urls")` is not its own edge. The string matches exactly one scanned
module, and that module's `urlpatterns` are published under the prefix `shop/`.
Endpoint identity uses `{handler}:{method}:{path}` (`method` empty when omitted).
`Class.as_view()` uses the label `{class}.as_view`. Because `OrderDetail` does not
define `as_view`, `handled_by` targets the unique verb callable named by the
literal `http_method_names` entry.

## Intentional negative cases

`path("ghost/", missing_view)` and `path("dyn/", include(_dynamic_urls()))` produce
diagnostics (`django_view_unresolved`, `django_include_unresolved`) and no endpoint
or `handled_by` edge. `BareDetail` defines `get` without a literal
`http_method_names`, so `/bare/` is an endpoint with no method and no
`handled_by` (`django_view_unresolved`). `unused` is not a route. The sentinel
`RKG_TEST_SECRET_DO_NOT_PERSIST` must not appear in facts, diagnostics, or census
stdout.
