"""Next.js framework adapter focused oracles.

Pages are Endpoint kind=navigation. Route handlers are HTTP method+path.
Dynamic segments use a colon prefix ([orderId] → :orderId). A navigation
calls edge exists only when the destination matches exactly one page handler.
"""

from __future__ import annotations

from pathlib import Path

from rkg.adapters import AdapterContext
from rkg.adapters.contracts import AdapterKind, SupportState
from rkg.domain import EdgeType, EntityType, SourceScanConfig, validate_fact_batch
from rkg.ingestion import LocalSourcePolicy, build_manifest, resolve_local_source

_TS_PATTERNS = ("*.ts", "*.tsx", "**/*.ts", "**/*.tsx")
SECRET = "RKG_TEST_SECRET_DO_NOT_PERSIST"


def _typescript_adapter():
    from rkg.adapters.typescript_language import TypeScriptLanguageAdapter

    return TypeScriptLanguageAdapter()


def _next_adapter():
    from rkg.adapters.next_framework import NextFrameworkAdapter

    return NextFrameworkAdapter()


def _write(root: Path, relative: str, source: str) -> None:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")


def _run(root: Path):
    config = SourceScanConfig(40, 32768, _TS_PATTERNS)
    manifest = build_manifest(
        resolve_local_source("repo-next", root, LocalSourcePolicy((root,))), config
    )
    context = AdapterContext("repo-next", "snap-next", "job-next", config)
    language = _typescript_adapter()
    parsed = language.parse(manifest, config)
    extracted = language.extract(context, parsed)
    base = language.resolve(context, parsed, extracted.facts).facts
    adapter = _next_adapter()
    result = adapter.extract(context, parsed, base)
    validate_fact_batch(result.facts)
    return adapter, result


def _attrs(entity) -> dict:
    return dict(entity.attributes)


def _endpoints(result):
    return [item for item in result.facts.entities if item.type == EntityType.ENDPOINT]


def _by_qn(result):
    return {item.qualified_name: item for item in result.facts.entities}


def test_descriptor_is_detected_only() -> None:
    adapter = _next_adapter()
    assert adapter.reviewed_deep_support is False
    assert adapter.descriptor.adapter_id == "rkg.next"
    assert adapter.descriptor.kind == AdapterKind.FRAMEWORK
    assert adapter.descriptor.language == "typescript"
    assert adapter.descriptor.framework == "next"
    assert adapter.descriptor.capabilities == ("app", "routes")
    assert all(
        item.support_state == SupportState.DETECTED_ONLY
        for item in adapter._capabilities()
    )


def test_file_routes_use_colon_dynamic_segments(tmp_path: Path) -> None:
    """App Router pages, route groups, Pages Router and HTTP verbs."""
    _write(
        tmp_path,
        "app/(shop)/orders/[orderId]/page.tsx",
        "export default function OrderPage() { return null; }\n",
    )
    _write(
        tmp_path,
        "app/api/orders/route.ts",
        "export function GET() { return null; }\n"
        "export const POST = async () => null;\n",
    )
    _write(
        tmp_path,
        "pages/blog/[slug].tsx",
        "export default function PostPage() { return null; }\n",
    )
    _write(
        tmp_path,
        "pages/api/health.ts",
        "export default function health(req, res) {\n"
        "  if (req.method === 'GET') { res.status(200); }\n"
        "}\n",
    )
    _, result = _run(tmp_path)
    paths = {
        (
            _attrs(item).get("kind"),
            _attrs(item).get("method"),
            _attrs(item).get("path"),
        )
        for item in _endpoints(result)
    }
    assert ("navigation", None, "/orders/:orderId") in paths
    assert ("navigation", None, "/blog/:slug") in paths
    http = {
        (_attrs(item).get("method"), _attrs(item).get("path"))
        for item in _endpoints(result)
        if _attrs(item).get("kind") != "navigation"
    }
    assert http == {
        ("GET", "/api/orders"),
        ("POST", "/api/orders"),
        ("GET", "/api/health"),
    }
    handled = {
        edge.type
        for edge in result.facts.edges
        if edge.type == EdgeType.HANDLED_BY
    }
    assert handled == {EdgeType.HANDLED_BY}
    assert not any(edge.type == EdgeType.DEPENDS_ON for edge in result.facts.edges)
    names = _by_qn(result)
    order = names["app.(shop).orders.[orderId].page.OrderPage"]
    assert any(
        edge.type == EdgeType.HANDLED_BY and edge.target_id == order.id
        for edge in result.facts.edges
    )


def test_navigation_calls_literal_and_constant(tmp_path: Path) -> None:
    _write(tmp_path, "lib/paths.ts", "export const ORDERS = '/orders';\n")
    _write(
        tmp_path,
        "app/page.tsx",
        "import Link from 'next/link';\n"
        "import { ORDERS } from '../lib/paths';\n"
        "export default function HomePage() {\n"
        "  return <Link href={ORDERS} />;\n"
        "}\n",
    )
    _write(
        tmp_path,
        "app/orders/page.tsx",
        "export default function OrdersPage() { return null; }\n",
    )
    _write(
        tmp_path,
        "app/account/page.tsx",
        "import { useRouter } from 'next/navigation';\n"
        "export default function AccountPage() {\n"
        "  const router = useRouter();\n"
        "  router.push('/orders');\n"
        "  return null;\n"
        "}\n",
    )
    _, result = _run(tmp_path)
    names = _by_qn(result)
    calls = [
        edge
        for edge in result.facts.edges
        if edge.type == EdgeType.CALLS and edge.rule == "RKG.next.navigation.v1"
    ]
    pairs = {
        (
            names_of(result, edge.source_id),
            names_of(result, edge.target_id),
        )
        for edge in calls
    }
    assert pairs == {
        ("app.page.HomePage", "app.orders.page.OrdersPage"),
        ("app.account.page.AccountPage", "app.orders.page.OrdersPage"),
    }
    assert all(edge.evidence_ids for edge in calls)
    assert names["app.orders.page.OrdersPage"]


def names_of(result, entity_id: str) -> str:
    for item in result.facts.entities:
        if item.id == entity_id:
            return item.qualified_name
    raise AssertionError(entity_id)


def test_dynamic_href_is_diagnostic_without_edge(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "app/page.tsx",
        "import Link from 'next/link';\n"
        "export default function HomePage(id: string) {\n"
        "  return <Link href={`/orders/${id}`} />;\n"
        "}\n",
    )
    _write(
        tmp_path,
        "app/orders/page.tsx",
        "export default function OrdersPage() { return null; }\n",
    )
    _, result = _run(tmp_path)
    assert not any(
        edge.type == EdgeType.CALLS and edge.rule == "RKG.next.navigation.v1"
        for edge in result.facts.edges
    )
    assert any(item.code == "next_navigation_unresolved" for item in result.diagnostics)


def test_shadowed_link_has_no_edge(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "app/page.tsx",
        "import Link from 'next/link';\n"
        "export default function HomePage() {\n"
        "  const Link = (props: { href: string }) => props.href;\n"
        "  return <Link href='/orders' />;\n"
        "}\n",
    )
    _write(
        tmp_path,
        "app/orders/page.tsx",
        "export default function OrdersPage() { return null; }\n",
    )
    _, result = _run(tmp_path)
    assert not any(
        edge.type == EdgeType.CALLS and edge.rule == "RKG.next.navigation.v1"
        for edge in result.facts.edges
    )
    assert any(item.code == "next_binding_shadowed" for item in result.diagnostics)


def test_ambiguous_constant_and_duplicate_route_have_no_edge(tmp_path: Path) -> None:
    _write(tmp_path, "lib/paths.ts", "export const DEST = '/orders';\n")
    _write(
        tmp_path,
        "app/page.tsx",
        "import Link from 'next/link';\n"
        "import { DEST } from '../lib/paths';\n"
        "const DEST = '/catalog';\n"
        "export default function HomePage() {\n"
        "  return <Link href={DEST} />;\n"
        "}\n",
    )
    _write(
        tmp_path,
        "app/(a)/orders/page.tsx",
        "export default function OrdersA() { return null; }\n",
    )
    _write(
        tmp_path,
        "app/(b)/orders/page.tsx",
        "export default function OrdersB() { return null; }\n",
    )
    _write(
        tmp_path,
        "app/go/page.tsx",
        "import Link from 'next/link';\n"
        "export default function GoPage() {\n"
        "  return <Link href='/orders' />;\n"
        "}\n",
    )
    _, result = _run(tmp_path)
    calls = [
        edge
        for edge in result.facts.edges
        if edge.type == EdgeType.CALLS and edge.rule == "RKG.next.navigation.v1"
    ]
    assert calls == []
    codes = {item.code for item in result.diagnostics}
    assert "next_binding_shadowed" in codes
    assert "next_navigation_ambiguous" in codes
    orders = [
        item
        for item in _endpoints(result)
        if _attrs(item).get("path") == "/orders"
    ]
    assert len(orders) == 2


def test_unresolved_route_export_omits_handled_by(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "app/api/orders/route.ts",
        "export const GET = make();\n",
    )
    _, result = _run(tmp_path)
    http = [
        item
        for item in _endpoints(result)
        if _attrs(item).get("method") == "GET"
    ]
    assert len(http) == 1
    assert _attrs(http[0]).get("path") == "/api/orders"
    assert not any(edge.type == EdgeType.HANDLED_BY for edge in result.facts.edges)
    assert any(item.code == "next_handler_unresolved" for item in result.diagnostics)


def test_dynamic_pages_api_and_optional_catchall_emit_no_edge(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "pages/api/health.ts",
        "export default function health(req, res) { res.status(200); }\n",
    )
    _write(
        tmp_path,
        "app/docs/[[...slug]]/page.tsx",
        "export default function DocsPage() { return null; }\n",
    )
    _, result = _run(tmp_path)
    assert _endpoints(result) == []
    assert not any(edge.type == EdgeType.HANDLED_BY for edge in result.facts.edges)
    codes = {item.code for item in result.diagnostics}
    assert "next_handler_unresolved" in codes or "next_route_dynamic" in codes
    assert "next_route_dynamic" in codes


def test_secret_is_not_persisted(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "app/page.tsx",
        "import Link from 'next/link';\n"
        f"const hidden = '{SECRET}';\n"
        "export default function HomePage() {\n"
        "  return <Link href={'/missing/' + hidden} />;\n"
        "}\n",
    )
    _, result = _run(tmp_path)
    blob = "\n".join(
        [
            *(item.qualified_name for item in result.facts.entities),
            *(str(item.attributes) for item in result.facts.entities),
            *(item.message for item in result.facts.diagnostics),
            *(item.code for item in result.diagnostics),
        ]
    )
    assert SECRET not in blob
    assert not any(
        edge.type == EdgeType.CALLS and edge.rule == "RKG.next.navigation.v1"
        for edge in result.facts.edges
    )
