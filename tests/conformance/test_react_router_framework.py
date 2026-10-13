"""TASK-RKG-042: React Router framework adapter focused oracles.

Oracle: repo-test/rkg-fixture-react-ts README route registration chain.
UI navigation routes reuse Endpoint with kind=navigation (no HTTP method).
"""

from __future__ import annotations

from pathlib import Path

from rkg.adapters import AdapterContext, ParseResult
from rkg.domain import EntityType, FactBatch, SourceScanConfig, validate_fact_batch
from rkg.ingestion import LocalSourcePolicy, build_manifest, resolve_local_source

_TS_PATTERNS = ("*.ts", "*.tsx", "**/*.ts", "**/*.tsx")

# README Expected route registration chain (semantic paths only).
_EXPECTED_NAV_PATHS = {
    "/",
    "/orders",
    "/orders/:orderId",
    "/orders/:orderId/edit",
    "/admin/users",
    "*",
}


def _typescript_adapter():
    from rkg.adapters.typescript_language import TypeScriptLanguageAdapter

    return TypeScriptLanguageAdapter()


def _react_router_adapter():
    from rkg.adapters.react_router_framework import ReactRouterFrameworkAdapter

    return ReactRouterFrameworkAdapter()


def _write(root: Path, relative: str, source: str) -> None:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")


def _navigation_paths(result) -> set[str]:
    """Provisional path harvest for navigation Endpoints (OQ-RKG-007 resolved).

    Accepts entities marked framework_kind=react-router or attributes
    kind=navigation / route_path / path — never requires HTTP method.
    """
    paths: set[str] = set()
    for item in result.facts.entities:
        attrs = dict(item.attributes)
        is_nav = (
            item.framework_kind == "react-router"
            or attrs.get("kind") == "navigation"
        )
        if not is_nav and item.type == EntityType.ENDPOINT:
            # Reject FastAPI-style HTTP endpoints mistaken for UI routes.
            continue
        candidate = attrs.get("route_path") or attrs.get("path")
        if is_nav and isinstance(candidate, str):
            paths.add(candidate)
    return paths


def _run(root: Path):
    config = SourceScanConfig(40, 32768, _TS_PATTERNS)
    manifest = build_manifest(
        resolve_local_source("repo-rr", root, LocalSourcePolicy((root,))), config
    )
    context = AdapterContext("repo-rr", "snap-rr", "job-rr", config)
    language = _typescript_adapter()
    try:
        parsed = language.parse(manifest, config)
        extracted = language.extract(context, parsed)
        base = language.resolve(context, parsed, extracted.facts).facts
    except NotImplementedError:
        parsed = ParseResult(())
        base = FactBatch(context.repository_id, context.snapshot_id)
    adapter = _react_router_adapter()
    result = adapter.extract(context, parsed, base)
    validate_fact_batch(result.facts)
    return adapter, result, parsed


def _mini_router_fixture(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "src/analysis-cases/positive/importedConstants.ts",
        "export const ADMIN_USERS_PATH = 'admin/users';\n",
    )
    _write(
        tmp_path,
        "src/app/router.tsx",
        "import { createBrowserRouter, type RouteObject } "
        "from 'react-router-dom';\n"
        "import { ADMIN_USERS_PATH } "
        "from '../analysis-cases/positive/importedConstants';\n"
        "const Root = () => null;\n"
        "const Dashboard = () => null;\n"
        "const Orders = () => null;\n"
        "const Detail = () => null;\n"
        "const Edit = () => null;\n"
        "const Admin = () => null;\n"
        "const Users = () => null;\n"
        "const Missing = () => null;\n"
        "export const appRoutes: RouteObject[] = [\n"
        "  {\n"
        "    path: '/',\n"
        "    element: <Root />,\n"
        "    children: [\n"
        "      { index: true, element: <Dashboard /> },\n"
        "      { path: 'orders', element: <Orders /> },\n"
        "      { path: 'orders/:orderId', element: <Detail /> },\n"
        "      { path: 'orders/:orderId/edit', element: <Edit /> },\n"
        "      { element: <Admin />, children: ["
        "{ path: ADMIN_USERS_PATH, element: <Users /> }] },\n"
        "      { path: '*', element: <Missing /> },\n"
        "    ],\n"
        "  },\n"
        "];\n"
        "export const router = createBrowserRouter(appRoutes);\n",
    )


def test_static_route_registration_paths(tmp_path: Path) -> None:
    """AC-RKG-007 (+ inventory) — static nested/layout/index/dynamic/catch-all paths.

    Navigation routes reuse Endpoint with kind=navigation (no HTTP method).
    Assert path inventory via navigation attributes only.
    """
    _mini_router_fixture(tmp_path)
    _, result, _ = _run(tmp_path)
    paths = _navigation_paths(result)
    assert _EXPECTED_NAV_PATHS <= paths, paths
    # Must not publish UI paths as FastAPI-style HTTP method Endpoints.
    http_style = {
        (dict(item.attributes).get("method"), dict(item.attributes).get("path"))
        for item in result.facts.entities
        if item.type == EntityType.ENDPOINT
        and dict(item.attributes).get("method") in {"GET", "POST", "PUT", "DELETE"}
    }
    assert not any(path in _EXPECTED_NAV_PATHS for _, path in http_style), http_style
    assert all(edge.evidence_ids for edge in result.facts.edges)


def test_navigation_route_handled_by_page_callable(tmp_path: Path) -> None:
    """Static element={<Page />} emits handled_by → page Callable (flow root)."""
    from rkg.domain import EdgeType

    _mini_router_fixture(tmp_path)
    _, result, _ = _run(tmp_path)
    by_id = {item.id: item for item in result.facts.entities}
    handled = {
        dict(by_id[edge.source_id].attributes).get("path"): by_id[
            edge.target_id
        ].qualified_name
        for edge in result.facts.edges
        if edge.type == EdgeType.HANDLED_BY
        and by_id[edge.source_id].type == EntityType.ENDPOINT
    }
    assert handled.get("/orders") == "src.app.router.Orders"
    assert handled.get("/admin/users") == "src.app.router.Users"
    assert handled.get("*") == "src.app.router.Missing"
    # List enrichment attributes (additive; HTTP Endpoints untouched).
    orders = next(
        item
        for item in result.facts.entities
        if item.type == EntityType.ENDPOINT
        and dict(item.attributes).get("path") == "/orders"
    )
    assert dict(orders.attributes).get("page_handler") == "Orders"
    assert dict(orders.attributes).get("route_signal") in {
        "shell",
        "partial",
        "outbound_http",
    }
    # outbound_requests is optional List enrichment when call/depends evidence exists.
    outbound = dict(orders.attributes).get("outbound_requests")
    if outbound is not None:
        assert isinstance(outbound, str) and outbound.strip()
    # No repository EXPOSES for navigation endpoints.
    exposes = [
        edge
        for edge in result.facts.edges
        if edge.type == EdgeType.EXPOSES
        and by_id.get(edge.target_id) is not None
        and dict(by_id[edge.target_id].attributes).get("kind") == "navigation"
    ]
    assert exposes == []


def test_navigation_outbound_requests_prefer_http_method_path(tmp_path: Path) -> None:
    """UI route List signal uses GET /path from call-site evidence, not fn → get."""
    from rkg.domain import EdgeType

    _write(
        tmp_path,
        "src/services/httpClient.ts",
        "export class FetchHttpClient {\n"
        "  async get<T>(path: string): Promise<T> { return path as T; }\n"
        "}\n"
        "export const httpClient = new FetchHttpClient();\n",
    )
    _write(
        tmp_path,
        "src/services/orderApi.ts",
        "import { httpClient } from './httpClient';\n"
        "export function listOrders(): Promise<unknown> {\n"
        "  return httpClient.get('/api/orders');\n"
        "}\n",
    )
    _write(
        tmp_path,
        "src/app/OrdersPage.tsx",
        "import { listOrders } from '../services/orderApi';\n"
        "export function OrdersPage() {\n"
        "  void listOrders();\n"
        "  return null;\n"
        "}\n",
    )
    _write(
        tmp_path,
        "src/app/router.tsx",
        "import { createBrowserRouter, type RouteObject } "
        "from 'react-router-dom';\n"
        "import { OrdersPage } from './OrdersPage';\n"
        "export const appRoutes: RouteObject[] = [\n"
        "  { path: '/orders', element: <OrdersPage /> },\n"
        "];\n"
        "export const router = createBrowserRouter(appRoutes);\n",
    )
    _, result, _ = _run(tmp_path)
    orders = next(
        item
        for item in result.facts.entities
        if item.type == EntityType.ENDPOINT
        and dict(item.attributes).get("path") == "/orders"
    )
    attrs = dict(orders.attributes)
    assert attrs.get("route_signal") == "outbound_http"
    assert attrs.get("outbound_requests") == "GET /api/orders"
    assert "listOrders → get" not in (attrs.get("outbound_requests") or "")
    # Still emits the call chain for Graph flow.
    by_id = {item.id: item for item in result.facts.entities}
    calls = {
        (by_id[edge.source_id].name, by_id[edge.target_id].name)
        for edge in result.facts.edges
        if edge.type == EdgeType.CALLS
    }
    assert ("OrdersPage", "listOrders") in calls
    assert ("listOrders", "get") in calls


def test_dynamic_conditional_route_is_diagnostic(tmp_path: Path) -> None:
    """AC-RKG-006 — negative dynamic/conditional route → diagnostic, no guessed path."""
    _write(
        tmp_path,
        "src/analysis-cases/negative/dynamicRoute.tsx",
        "// Expected: diagnostic; do not guess a route path from runtime input.\n"
        "import { type RouteObject } from 'react-router-dom';\n"
        "export function buildRoutes(\n"
        "  flag: boolean, dynamicPath: string\n"
        "): RouteObject[] {\n"
        "  const routes: RouteObject[] = [];\n"
        "  if (flag) {\n"
        "    routes.push({ path: dynamicPath, element: null });\n"
        "  }\n"
        "  return routes;\n"
        "}\n",
    )
    _, result, parsed = _run(tmp_path)
    paths = _navigation_paths(result)
    # No static inventory path may be invented from the runtime-only builder.
    assert not (paths & _EXPECTED_NAV_PATHS), paths
    codes = {item.code for item in result.diagnostics} | {
        item.code for item in parsed.diagnostics
    } | {item.code for item in result.facts.diagnostics}
    assert any(
        "route" in code and ("dynamic" in code or "unresolved" in code)
        for code in codes
    ), codes
