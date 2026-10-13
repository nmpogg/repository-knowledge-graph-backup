"""TanStack Router framework adapter: static routes and navigation calls."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from rkg.adapters import AdapterContext
from rkg.adapters.builtins import builtin_adapters
from rkg.adapters.conformance import run_framework_conformance
from rkg.adapters.contracts import SupportState
from rkg.adapters.tanstack_router_framework import (
    NAVIGATE_RULE,
    TanStackRouterFrameworkAdapter,
)
from rkg.domain import EdgeType, EntityType, SourceScanConfig, validate_fact_batch
from tests.conformance.published_edge_evidence import assert_ac_rkg_007
from rkg.ingestion import LocalSourcePolicy, build_manifest, resolve_local_source

_SECRET = "RKG_TEST_SECRET_DO_NOT_PERSIST"
_TS_PATTERNS = ("*.ts", "*.tsx", "**/*.ts", "**/*.tsx")


def _write(root: Path, relative: str, source: str) -> None:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")


def _run(root: Path):
    config = SourceScanConfig(40, 32768, _TS_PATTERNS)
    manifest = build_manifest(
        resolve_local_source("repo-tanstack", root, LocalSourcePolicy((root,))),
        config,
    )
    context = AdapterContext("repo-tanstack", "snap-tanstack", "job-tanstack", config)
    from rkg.adapters.typescript_language import TypeScriptLanguageAdapter

    language = TypeScriptLanguageAdapter()
    parsed = language.parse(manifest, config)
    base = language.extract(context, parsed)
    base = language.resolve(context, parsed, base.facts)
    adapter = TanStackRouterFrameworkAdapter()
    result = adapter.extract(context, parsed, base.facts)
    validate_fact_batch(result.facts)
    if result.facts.edges:
        assert_ac_rkg_007(result.facts)
    report = run_framework_conformance(
        adapter,
        manifest,
        parsed,
        context,
        base.facts,
        no_execution_marker=lambda: False,
    )
    assert report.pass_rate == 1.0, report.cases
    assert {item.support_state for item in result.capabilities} == {
        SupportState.DETECTED_ONLY
    }
    assert adapter.reviewed_deep_support is False
    return result


def _names(result, edge_type: EdgeType, *, rule: str | None = None):
    entities = {item.id: item for item in result.facts.entities}
    return {
        (
            entities[edge.source_id].qualified_name,
            entities[edge.target_id].qualified_name,
        )
        for edge in result.facts.edges
        if edge.type == edge_type
        and edge.source_id in entities
        and (rule is None or edge.rule == rule)
    }


def _nav_paths(result) -> set[str]:
    return {
        str(dict(item.attributes).get("path"))
        for item in result.facts.entities
        if item.type == EntityType.ENDPOINT
        and dict(item.attributes).get("kind") == "navigation"
    }


def test_descriptor_and_builtin_registration() -> None:
    adapter = TanStackRouterFrameworkAdapter()
    assert adapter.descriptor.adapter_id == "rkg.tanstack-router"
    assert adapter.descriptor.kind.value == "framework"
    assert adapter.descriptor.language == "typescript"
    assert adapter.descriptor.framework == "tanstack-router"
    assert adapter.reviewed_deep_support is False
    matches = [
        item
        for item in builtin_adapters()
        if item.descriptor.adapter_id == "rkg.tanstack-router"
    ]
    assert len(matches) == 1


def test_parent_file_route_and_navigate_calls(tmp_path: Path) -> None:
    _write(tmp_path, "src/paths.ts", "export const ORDERS_SEGMENT = 'orders';\n")
    _write(
        tmp_path,
        "src/app.tsx",
        "import { createFileRoute, createRoute, Link, useNavigate } "
        "from '@tanstack/react-router';\n"
        "import { ORDERS_SEGMENT } from './paths';\n"
        "const Root = () => null;\n"
        "const Orders = () => null;\n"
        "const Detail = () => null;\n"
        "export const rootRoute = createRoute({\n"
        "  path: '/',\n"
        "  component: Root,\n"
        "});\n"
        "export const ordersRoute = createRoute({\n"
        "  getParentRoute: () => rootRoute,\n"
        "  path: ORDERS_SEGMENT,\n"
        "  component: Orders,\n"
        "});\n"
        "export const Route = createFileRoute('/orders/$orderId')({\n"
        "  component: Detail,\n"
        "});\n"
        "export function openOrders() {\n"
        "  const navigate = useNavigate();\n"
        "  navigate({ to: '/orders' });\n"
        "  return <Link to='/orders/$orderId' />;\n"
        "}\n",
    )
    result = _run(tmp_path)
    assert _nav_paths(result) == {"/", "/orders", "/orders/$orderId"}
    assert (
        "src.app.openOrders",
        "src.app.Orders",
    ) in _names(result, EdgeType.CALLS, rule=NAVIGATE_RULE)
    assert (
        "src.app.openOrders",
        "src.app.Detail",
    ) in _names(result, EdgeType.CALLS, rule=NAVIGATE_RULE)
    assert (
        "navigation:/orders",
        "src.app.Orders",
    ) in _names(result, EdgeType.HANDLED_BY)
    assert all(edge.evidence_ids for edge in result.facts.edges)
    http = [
        item
        for item in result.facts.entities
        if item.type == EntityType.ENDPOINT
        and dict(item.attributes).get("method") in {"GET", "POST", "PUT", "DELETE"}
    ]
    assert http == []
    assert not any(edge.type == EdgeType.DEPENDS_ON for edge in result.facts.edges)


def test_dynamic_destination_is_diagnostic_without_edge(tmp_path: Path) -> None:
    """Negative case: a non-literal destination does not invent a calls edge."""
    _write(
        tmp_path,
        "src/app.tsx",
        "import { createRoute, useNavigate } from '@tanstack/react-router';\n"
        "const Page = () => null;\n"
        "export const only = createRoute({ path: '/only', component: Page });\n"
        "const hidden = 'RKG_TEST_SECRET_DO_NOT_PERSIST';\n"
        "export function go(id: string) {\n"
        "  const navigate = useNavigate();\n"
        "  navigate({ to: `/only/${id}` });\n"
        "  navigate({ to: hidden });\n"
        "}\n",
    )
    result = _run(tmp_path)
    codes = {item.code for item in result.facts.diagnostics}
    assert "tanstack_navigate_unresolved" in codes
    assert _names(result, EdgeType.CALLS, rule=NAVIGATE_RULE) == set()
    blob = json.dumps(asdict(result.facts), default=str)
    assert _SECRET not in blob
    assert not any(_SECRET in item.message for item in result.facts.diagnostics)
    assert _nav_paths(result) == {"/only"}


def test_shadow_ambiguous_and_unresolved_parent_emit_no_edge(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "src/app.tsx",
        "import { createRoute, useNavigate } from '@tanstack/react-router';\n"
        "const Page = () => null;\n"
        "export const rootRoute = createRoute({ path: '/', component: Page });\n"
        "export const first = createRoute({\n"
        "  getParentRoute: () => rootRoute,\n"
        "  path: 'same',\n"
        "  component: Page,\n"
        "});\n"
        "export const second = createRoute({ path: '/same', component: Page });\n"
        "export function pick() { return null; }\n"
        "export const dangling = createRoute({\n"
        "  getParentRoute: () => pick(),\n"
        "  path: 'dangling',\n"
        "  component: Page,\n"
        "});\n"
        "function navigate(target: { to: string }) { return target; }\n"
        "export function shadowed() {\n"
        "  navigate({ to: '/same' });\n"
        "}\n"
        "export function ambiguous() {\n"
        "  const navigate = useNavigate();\n"
        "  navigate({ to: '/same' });\n"
        "}\n",
    )
    result = _run(tmp_path)
    codes = {item.code for item in result.facts.diagnostics}
    assert "tanstack_navigate_shadow" in codes
    assert "tanstack_navigate_ambiguous" in codes
    assert "tanstack_parent_unresolved" in codes
    assert _names(result, EdgeType.CALLS, rule=NAVIGATE_RULE) == set()
    assert "dangling" not in _nav_paths(result)
    assert "/dangling" not in _nav_paths(result)
    assert _nav_paths(result) == {"/", "/same"}
