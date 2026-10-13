"""Focused conformance for VueRouterFrameworkAdapter.

Static createRouter / new Router routes, lazy .vue imports, and navigation
calls. A dynamic push is a diagnostic and does not emit an edge.
"""

from __future__ import annotations

from pathlib import Path

from rkg.adapters import AdapterContext, ParseResult, SupportState
from rkg.domain import (
    EdgeType,
    EntityType,
    FactBatch,
    SourceScanConfig,
    validate_fact_batch,
)
from rkg.ingestion import LocalSourcePolicy, build_manifest, resolve_local_source
from tests.conformance.published_edge_evidence import assert_ac_rkg_007

_VUE_PATTERNS = ("*.vue", "**/*.vue")
_TS_PATTERNS = ("*.ts", "**/*.ts", "package.json")
_IGNORE = ("**/node_modules/**", "**/dist/**", "**/coverage/**")


def _vue_adapter():
    from rkg.adapters.vue_language import VueLanguageAdapter

    return VueLanguageAdapter()


def _typescript_adapter():
    from rkg.adapters.typescript_language import TypeScriptLanguageAdapter

    return TypeScriptLanguageAdapter()


def _router_adapter():
    from rkg.adapters.vue_router_framework import VueRouterFrameworkAdapter

    return VueRouterFrameworkAdapter()


def _write(root: Path, relative: str, source: str) -> None:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")


def _page(name: str) -> str:
    return (
        "<script setup lang=\"ts\">\n"
        "export function setup() {\n"
        "  return {};\n"
        "}\n"
        "</script>\n"
        f"<template><section>{name}</section></template>\n"
    )


def _mini(root: Path) -> None:
    _write(root, "src/views/Home.vue", _page("home"))
    _write(root, "src/views/Orders.vue", _page("orders"))
    _write(root, "src/views/Users.vue", _page("users"))
    _write(root, "src/views/Legacy.vue", _page("legacy"))
    _write(
        root,
        "src/router/paths.ts",
        "export const ORDERS_PATH = '/orders';\n",
    )
    _write(
        root,
        "src/router/index.ts",
        "import { createRouter, createWebHistory } from 'vue-router';\n"
        "import { ORDERS_PATH } from './paths';\n"
        "const routes = [\n"
        "  { path: '/', name: 'home', component: () => import('../views/Home.vue') },\n"
        "  {\n"
        "    path: ORDERS_PATH,\n"
        "    name: 'orders',\n"
        "    component: () => import('../views/Orders.vue'),\n"
        "    children: [\n"
        "      { path: 'users', name: 'users',"
        " component: () => import('../views/Users.vue') },\n"
        "    ],\n"
        "  },\n"
        "];\n"
        "export const router = createRouter({ history: createWebHistory(), routes });\n",
    )
    _write(
        root,
        "src/router/legacy.ts",
        "import Router from 'vue-router';\n"
        "const legacyRoutes = [\n"
        "  { path: '/legacy', name: 'legacy',"
        " component: () => import('../views/Legacy.vue') },\n"
        "];\n"
        "export const legacyRouter = new Router({ routes: legacyRoutes });\n"
        "export function openLegacy() {\n"
        "  legacyRouter.replace('/legacy');\n"
        "}\n",
    )
    _write(
        root,
        "src/navigation/openOrders.ts",
        "import { useRouter } from 'vue-router';\n"
        "import { ORDERS_PATH } from '../router/paths';\n"
        "export function openOrders() {\n"
        "  const router = useRouter();\n"
        "  router.push(ORDERS_PATH);\n"
        "}\n"
        "export function openDynamic(target: string) {\n"
        "  const router = useRouter();\n"
        "  router.push(target);\n"
        "}\n",
    )


def _run(root: Path):
    vue = _vue_adapter()
    typescript = _typescript_adapter()
    router = _router_adapter()
    vue_config = SourceScanConfig(80, 65536, _VUE_PATTERNS, _IGNORE)
    ts_config = SourceScanConfig(80, 65536, _TS_PATTERNS, _IGNORE)
    vue_manifest = build_manifest(
        resolve_local_source("repo-vr", root, LocalSourcePolicy((root,))), vue_config
    )
    ts_manifest = build_manifest(
        resolve_local_source("repo-vr", root, LocalSourcePolicy((root,))), ts_config
    )
    context = AdapterContext("repo-vr", "snap-vr", "job-vr", vue_config)
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
        )
    )
    detected = router.detect(ts_manifest, parsed)
    extracted = router.extract(context, parsed, batch)
    resolved = router.resolve(context, parsed, extracted.facts)
    validate_fact_batch(resolved.facts)
    if resolved.facts.edges:
        assert_ac_rkg_007(resolved.facts)
    return router, detected, resolved


def test_descriptor_is_detected_only() -> None:
    adapter = _router_adapter()
    assert adapter.descriptor.adapter_id == "rkg.vue-router"
    assert adapter.descriptor.kind.value == "framework"
    assert adapter.descriptor.language == "vue"
    assert adapter.descriptor.framework == "vue-router"
    assert adapter.reviewed_deep_support is False
    assert adapter.descriptor.technology_constraints[0].technology == "vue-router"
    states = {item.support_state for item in adapter._capabilities()}
    assert states == {SupportState.DETECTED_ONLY}


def test_static_routes_handlers_and_navigation(tmp_path: Path) -> None:
    _mini(tmp_path)
    adapter, detected, resolved = _run(tmp_path)
    assert detected.technologies
    assert adapter.reviewed_deep_support is False
    by_id = {item.id: item for item in resolved.facts.entities}
    paths = {
        dict(item.attributes).get("path")
        for item in resolved.facts.entities
        if item.type == EntityType.ENDPOINT
        and item.framework_kind == "vue-router"
        and dict(item.attributes).get("kind") == "navigation"
    }
    assert paths == {"/", "/orders", "/orders/users", "/legacy"}
    handled = {
        dict(by_id[edge.source_id].attributes).get("path"): by_id[
            edge.target_id
        ].qualified_name
        for edge in resolved.facts.edges
        if edge.type == EdgeType.HANDLED_BY
        and by_id[edge.source_id].type == EntityType.ENDPOINT
        and by_id[edge.source_id].framework_kind == "vue-router"
    }
    assert handled["/orders"] == "src.views.Orders.setup"
    assert handled["/orders/users"] == "src.views.Users.setup"
    assert handled["/legacy"] == "src.views.Legacy.setup"
    calls = {
        (
            by_id[edge.source_id].qualified_name,
            by_id[edge.target_id].qualified_name,
            edge.rule,
        )
        for edge in resolved.facts.edges
        if edge.type == EdgeType.CALLS
        and edge.rule == "RKG.vue_router.navigate.v1"
    }
    assert (
        "src.navigation.openOrders.openOrders",
        "src.views.Orders.setup",
        "RKG.vue_router.navigate.v1",
    ) in calls
    assert (
        "src.router.legacy.openLegacy",
        "src.views.Legacy.setup",
        "RKG.vue_router.navigate.v1",
    ) in calls
    assert all(
        any(by_id_ev.rule == edge.rule for by_id_ev in resolved.facts.evidence if by_id_ev.id in edge.evidence_ids)
        for edge in resolved.facts.edges
        if edge.rule == "RKG.vue_router.navigate.v1"
    )
    http_depends = [
        edge
        for edge in resolved.facts.edges
        if edge.type == EdgeType.DEPENDS_ON
        and edge.target_id in by_id
        and by_id[edge.target_id].type == EntityType.ENDPOINT
    ]
    assert http_depends == []


def test_dynamic_navigate_is_diagnostic_without_edge(tmp_path: Path) -> None:
    _mini(tmp_path)
    _, _, resolved = _run(tmp_path)
    by_id = {item.id: item for item in resolved.facts.entities}
    dynamic_calls = [
        edge
        for edge in resolved.facts.edges
        if edge.type == EdgeType.CALLS
        and edge.source_id in by_id
        and by_id[edge.source_id].qualified_name
        == "src.navigation.openOrders.openDynamic"
    ]
    assert dynamic_calls == []
    codes = {item.code for item in resolved.facts.diagnostics}
    assert "vue_router_navigate_dynamic" in codes
    assert all(
        "RKG_TEST_SECRET_DO_NOT_PERSIST" not in (item.message or "")
        for item in resolved.facts.diagnostics
    )
