"""Focused conformance for NuxtFrameworkAdapter.

Oracle intent: repo-test/rkg-fixture-nuxt4 README — pages → navigation Endpoints
(OQ-RKG-007), Nitro server/api → HTTP Endpoints, unique auto-imports, runtimeConfig
keys without values.
"""

from __future__ import annotations

from pathlib import Path

from rkg.adapters import AdapterContext, ParseResult
from rkg.domain import (
    EdgeType,
    EntityType,
    FactBatch,
    SourceScanConfig,
    validate_fact_batch,
)
from rkg.ingestion import LocalSourcePolicy, build_manifest, resolve_local_source

_VUE_PATTERNS = ("*.vue", "**/*.vue")
_TS_PATTERNS = ("*.ts", "**/*.ts", "package.json")
_IGNORE = (
    "**/node_modules/**",
    "**/.nuxt/**",
    "**/.output/**",
    "**/dist/**",
    "**/coverage/**",
)

_EXPECTED_NAV = {"/", "/orders", "/orders/:orderId", "/account/profile"}
_EXPECTED_HTTP = {
    ("GET", "/api/orders"),
    ("GET", "/api/orders/:orderId"),
    ("POST", "/api/orders/:orderId/cancel"),
}


def _vue_adapter():
    from rkg.adapters.vue_language import VueLanguageAdapter

    return VueLanguageAdapter()


def _typescript_adapter():
    from rkg.adapters.typescript_language import TypeScriptLanguageAdapter

    return TypeScriptLanguageAdapter()


def _nuxt_adapter():
    from rkg.adapters.nuxt_framework import NuxtFrameworkAdapter

    return NuxtFrameworkAdapter()


def _write(root: Path, relative: str, source: str) -> None:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")


def _run_fixture(root: Path):
    vue = _vue_adapter()
    typescript = _typescript_adapter()
    nuxt = _nuxt_adapter()
    vue_config = SourceScanConfig(80, 65536, _VUE_PATTERNS, _IGNORE)
    ts_config = SourceScanConfig(80, 65536, _TS_PATTERNS, _IGNORE)
    vue_manifest = build_manifest(
        resolve_local_source("repo-nuxt", root, LocalSourcePolicy((root,))), vue_config
    )
    ts_manifest = build_manifest(
        resolve_local_source("repo-nuxt", root, LocalSourcePolicy((root,))), ts_config
    )
    context = AdapterContext("repo-nuxt", "snap-nuxt", "job-nuxt", vue_config)
    vue_parsed = vue.parse(vue_manifest, vue_config)
    vue_batch = vue.resolve(
        context, vue_parsed, vue.extract(context, vue_parsed).facts
    ).facts
    ts_parsed = typescript.parse(ts_manifest, ts_config)
    ts_batch = typescript.resolve(
        context, ts_parsed, typescript.extract(context, ts_parsed).facts
    ).facts
    batch = FactBatch(
        context.repository_id,
        context.snapshot_id,
        tuple(sorted((*vue_batch.entities, *ts_batch.entities), key=lambda i: i.id)),
        tuple(sorted((*vue_batch.edges, *ts_batch.edges), key=lambda i: i.id)),
        tuple(sorted((*vue_batch.evidence, *ts_batch.evidence), key=lambda i: i.id)),
        (*vue_batch.diagnostics, *ts_batch.diagnostics),
    )
    parsed = ParseResult(
        tuple(
            sorted(
                (*vue_parsed.units, *ts_parsed.units),
                key=lambda unit: (unit.relative_path, unit.representation_kind),
            )
        ),
        (),
        (),
    )
    # Prefer full-ish manifest for detection evidence (package.json + pages).
    detect_manifest = build_manifest(
        resolve_local_source("repo-nuxt", root, LocalSourcePolicy((root,))),
        SourceScanConfig(
            80,
            65536,
            (*_VUE_PATTERNS, *_TS_PATTERNS, "nuxt.config.ts"),
            _IGNORE,
        ),
    )
    assert nuxt.detect(detect_manifest, parsed).technologies
    result = nuxt.extract(context, parsed, batch)
    validate_fact_batch(result.facts)
    return nuxt, result


def test_descriptor_contract() -> None:
    adapter = _nuxt_adapter()
    assert adapter.descriptor.adapter_id == "rkg.nuxt"
    assert adapter.descriptor.kind.value == "framework"
    assert adapter.descriptor.language == "vue"
    assert adapter.descriptor.framework == "nuxt"
    assert "app" in adapter.descriptor.capabilities
    assert "routes" in adapter.descriptor.capabilities
    assert adapter.reviewed_deep_support is False


def test_pages_and_nitro_routes_from_mini_fixture(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "package.json",
        '{"name":"mini-nuxt","dependencies":{"nuxt":"4.5.2","vue":"3.5.0"}}',
    )
    _write(
        tmp_path,
        "nuxt.config.ts",
        "import { defineNuxtConfig } from 'nuxt/config'\n"
        "export default defineNuxtConfig({\n"
        "  runtimeConfig: {\n"
        "    inventoryApiBase: 'https://inventory.example.test',\n"
        "    public: { portalName: 'Portal', apiBase: '/api' },\n"
        "  },\n"
        "})\n",
    )
    _write(
        tmp_path,
        "app/pages/index.vue",
        "<script setup lang=\"ts\">\ndefinePageMeta({ title: 'Home' })\n"
        "</script>\n<template><h1>Home</h1></template>\n",
    )
    _write(
        tmp_path,
        "app/pages/orders/index.vue",
        "<script setup lang=\"ts\">\nconst { load } = useOrders()\nawait load()\n"
        "</script>\n<template><OrderCard /></template>\n",
    )
    _write(
        tmp_path,
        "app/pages/orders/[orderId].vue",
        "<script setup lang=\"ts\"></script>\n<template><p>detail</p></template>\n",
    )
    _write(
        tmp_path,
        "app/pages/account/profile.vue",
        "<script setup lang=\"ts\"></script>\n<template><p>profile</p></template>\n",
    )
    _write(
        tmp_path,
        "app/composables/useOrders.ts",
        "export function useOrders() {\n"
        "  async function load() { return [] }\n"
        "  return { load }\n"
        "}\n",
    )
    _write(
        tmp_path,
        "app/components/OrderCard.vue",
        "<script setup lang=\"ts\"></script>\n<template><article /></template>\n",
    )
    _write(
        tmp_path,
        "server/api/orders/index.get.ts",
        "export function createListOrdersHandler() {\n"
        "  return async function listOrdersHandler() { return [] }\n"
        "}\n"
        "export default createListOrdersHandler()\n",
    )
    _write(
        tmp_path,
        "server/api/orders/[orderId].get.ts",
        "export function createGetOrderHandler() {\n"
        "  return async function getOrderHandler() { return null }\n"
        "}\n"
        "export default createGetOrderHandler()\n",
    )
    _write(
        tmp_path,
        "server/api/orders/[orderId]/cancel.post.ts",
        "export function createCancelOrderHandler() {\n"
        "  return async function cancelOrderHandler() { return null }\n"
        "}\n"
        "export default createCancelOrderHandler()\n",
    )

    _adapter, result = _run_fixture(tmp_path)
    nav = {
        dict(item.attributes).get("path")
        for item in result.facts.entities
        if item.type == EntityType.ENDPOINT
        and dict(item.attributes).get("kind") == "navigation"
    }
    assert nav == _EXPECTED_NAV
    http = {
        (dict(item.attributes).get("method"), dict(item.attributes).get("path"))
        for item in result.facts.entities
        if item.type == EntityType.ENDPOINT
        and dict(item.attributes).get("method")
    }
    assert http == _EXPECTED_HTTP
    configs = {
        item.qualified_name
        for item in result.facts.entities
        if item.type == EntityType.CONFIGURATION
    }
    assert "runtime:inventoryApiBase" in configs
    assert "runtime:public.portalName" in configs
    assert "runtime:public.apiBase" in configs
    # Values must not appear as configuration attributes.
    for item in result.facts.entities:
        if item.type != EntityType.CONFIGURATION:
            continue
        keys = {key.lower() for key, _ in item.attributes}
        assert "value" not in keys
        assert not any(key.endswith("_value") for key in keys)

    by_id = {item.id: item for item in result.facts.entities}
    depends = {
        (by_id[edge.source_id].qualified_name, by_id[edge.target_id].qualified_name)
        for edge in result.facts.edges
        if edge.type == EdgeType.DEPENDS_ON
        and edge.source_id in by_id
        and edge.target_id in by_id
    }
    assert (
        "app.pages.orders.index",
        "app.composables.useOrders.useOrders",
    ) in depends
    assert ("app.pages.orders.index", "app.components.OrderCard") in depends

    by_id = {item.id: item for item in result.facts.entities}
    nitro_handled = {
        (
            dict(by_id[edge.source_id].attributes).get("method"),
            by_id[edge.target_id].qualified_name,
        )
        for edge in result.facts.edges
        if edge.type == EdgeType.HANDLED_BY
        and edge.source_id in by_id
        and edge.target_id in by_id
        and dict(by_id[edge.source_id].attributes).get("method")
    }
    assert (
        "GET",
        "server.api.orders.index.get.createListOrdersHandler",
    ) in nitro_handled
    assert len(nitro_handled) == 3
    nav_handled = {
        dict(by_id[edge.source_id].attributes).get("path"): by_id[
            edge.target_id
        ].qualified_name
        for edge in result.facts.edges
        if edge.type == EdgeType.HANDLED_BY
        and edge.source_id in by_id
        and dict(by_id[edge.source_id].attributes).get("kind") == "navigation"
    }
    assert nav_handled.get("/orders") == "app.pages.orders.index.setup"
    assert nav_handled.get("/") == "app.pages.index.setup"
    assert nav_handled.get("/account/profile") == "app.pages.account.profile.setup"
    assert len(nav_handled) == 4


def test_orders_navigation_outbound_http_requests(tmp_path: Path) -> None:
    """UI→API List: /orders shows static GET /api/orders; shell pages stay empty."""
    _write(
        tmp_path,
        "package.json",
        '{"name":"mini-nuxt","dependencies":{"nuxt":"4.5.2","vue":"3.5.0"}}',
    )
    _write(
        tmp_path,
        "nuxt.config.ts",
        "export default defineNuxtConfig({})\n",
    )
    _write(
        tmp_path,
        "app/pages/index.vue",
        "<script setup lang=\"ts\">\ndefinePageMeta({ title: 'Home' })\n"
        "</script>\n<template><h1>Home</h1></template>\n",
    )
    _write(
        tmp_path,
        "app/pages/account/profile.vue",
        "<script setup lang=\"ts\"></script>\n<template><p>profile</p></template>\n",
    )
    _write(
        tmp_path,
        "app/pages/orders/index.vue",
        "<script setup lang=\"ts\">\n"
        "const { load } = useOrders()\n"
        "async function cancelOrder(id: string) {\n"
        "  await $fetch(`/api/orders/${id}/cancel`, { method: 'POST' })\n"
        "  await load()\n"
        "}\n"
        "await load()\n"
        "</script>\n<template><OrderCard /></template>\n",
    )
    _write(
        tmp_path,
        "app/composables/useOrders.ts",
        "export function useOrders(fetcher = $fetch) {\n"
        "  async function load() {\n"
        "    return fetcher<unknown[]>('/api/orders')\n"
        "  }\n"
        "  return { load }\n"
        "}\n",
    )
    _write(
        tmp_path,
        "app/components/OrderCard.vue",
        "<script setup lang=\"ts\"></script>\n<template><article /></template>\n",
    )
    _write(
        tmp_path,
        "app/pages/orders/[orderId].vue",
        "<script setup lang=\"ts\">\n"
        "const id = '1'\n"
        "await useFetch(() => `/api/orders/${id}`)\n"
        "</script>\n<template><p>detail</p></template>\n",
    )

    _adapter, result = _run_fixture(tmp_path)
    nav = {
        dict(item.attributes).get("path"): dict(item.attributes)
        for item in result.facts.entities
        if item.type == EntityType.ENDPOINT
        and dict(item.attributes).get("kind") == "navigation"
    }
    orders = nav["/orders"]
    assert orders.get("route_signal") == "outbound_http"
    assert "GET /api/orders" in (orders.get("outbound_requests") or "")
    # Dynamic cancel template must not invent a concrete path segment.
    assert "/api/orders/:orderId/cancel" not in (orders.get("outbound_requests") or "")
    assert "${" not in (orders.get("outbound_requests") or "")

    home = nav["/"]
    assert home.get("route_signal") == "shell"
    assert not home.get("outbound_requests")

    profile = nav["/account/profile"]
    assert profile.get("route_signal") == "shell"
    assert not profile.get("outbound_requests")

    detail = nav["/orders/:orderId"]
    # Dynamic useFetch URL — no invented path; must not claim outbound_http path.
    assert "/api/orders/" not in (detail.get("outbound_requests") or "")
    assert detail.get("route_signal") in {"shell", "partial"}

    use_orders = next(
        item
        for item in result.facts.entities
        if item.qualified_name == "app.composables.useOrders.useOrders"
    )
    assert dict(use_orders.attributes).get("http_requests") == "GET /api/orders"


def test_shadowed_fetch_is_not_http_technology(tmp_path: Path) -> None:
    """Local `$fetch` binding must not become Nuxt HTTP client evidence."""
    _write(
        tmp_path,
        "package.json",
        '{"dependencies":{"nuxt":"4.5.2","vue":"3.5.0"}}',
    )
    _write(
        tmp_path,
        "app/pages/index.vue",
        "<script setup lang=\"ts\"></script>\n<template><p /></template>\n",
    )
    _write(
        tmp_path,
        "analysis-cases/negative/shadowed-fetch.ts",
        "export async function shadowedFetch() {\n"
        "  const $fetch = (value: string) => Promise.resolve(`local:${value}`)\n"
        "  return $fetch('/api/not-an-http-call')\n"
        "}\n",
    )
    _adapter, result = _run_fixture(tmp_path)
    for item in result.facts.entities:
        attrs = dict(item.attributes)
        requests = attrs.get("http_requests") or ""
        assert "/api/not-an-http-call" not in str(requests)
        assert "shadowed" not in item.qualified_name.lower() or not requests


def test_ambiguous_auto_import_is_not_guessed(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "package.json",
        '{"dependencies":{"nuxt":"4.5.2","vue":"3.5.0"}}',
    )
    _write(
        tmp_path,
        "app/pages/index.vue",
        "<script setup lang=\"ts\">\nuseSummary()\n</script>\n"
        "<template><p /></template>\n",
    )
    _write(
        tmp_path,
        "app/composables/admin/useSummary.ts",
        "export function useSummary() { return { scope: 'admin' as const } }\n",
    )
    _write(
        tmp_path,
        "app/composables/storefront/useSummary.ts",
        "export function useSummary() { return { scope: 'storefront' as const } }\n",
    )
    _adapter, result = _run_fixture(tmp_path)
    by_id = {item.id: item for item in result.facts.entities}
    for edge in result.facts.edges:
        if edge.type != EdgeType.DEPENDS_ON:
            continue
        target = by_id.get(edge.target_id)
        if target is not None:
            assert "useSummary" not in target.qualified_name
