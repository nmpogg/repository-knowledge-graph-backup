"""TASK-RKG-042 RED: TypeScript language adapter focused oracles.

Oracle intent follows repo-test/rkg-fixture-react-ts README (Expected inventory +
Intentional negative cases). No adapter under src/ — tests import the future
production module path; RED = missing adapter (ImportError/ModuleNotFoundError)
or NotImplemented until GREEN. No parser/extractor in this change.

AC map: AC-RKG-003 (imports), AC-RKG-006 (no-guess), AC-RKG-007 (evidence),
AC-RKG-035 (syntax isolation), AC-RKG-048 (calls).
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from rkg.adapters import AdapterContext
from rkg.domain import EdgeType, EntityType, SourceScanConfig, validate_fact_batch
from rkg.ingestion import LocalSourcePolicy, build_manifest, resolve_local_source

_TS_PATTERNS = ("*.ts", "*.tsx", "**/*.ts", "**/*.tsx")
_SECRET = "RKG_TEST_SECRET_DO_NOT_PERSIST"


def _typescript_adapter():
    # Future production path (GREEN). Absent today → valid RED (thiếu adapter).
    from rkg.adapters.typescript_language import TypeScriptLanguageAdapter

    return TypeScriptLanguageAdapter()


def _write(root: Path, relative: str, source: str) -> None:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")


def _run(root: Path):
    config = SourceScanConfig(40, 32768, _TS_PATTERNS)
    manifest = build_manifest(
        resolve_local_source("repo-ts", root, LocalSourcePolicy((root,))), config
    )
    context = AdapterContext("repo-ts", "snap-ts", "job-ts", config)
    adapter = _typescript_adapter()
    assert adapter.detect(manifest).technologies
    parsed = adapter.parse(manifest, config)
    extracted = adapter.extract(context, parsed)
    resolved = adapter.resolve(context, parsed, extracted.facts)
    validate_fact_batch(resolved.facts)
    return adapter, manifest, config, context, parsed, resolved


def _entities_by_type(resolved, entity_type: EntityType):
    return [item for item in resolved.facts.entities if item.type == entity_type]


def _qualified_names(resolved) -> set[str]:
    return {item.qualified_name for item in resolved.facts.entities}


def _edge_pairs(resolved, edge_type: EdgeType) -> set[tuple[str, str]]:
    by_id = {item.id: item for item in resolved.facts.entities}
    return {
        (by_id[edge.source_id].qualified_name, by_id[edge.target_id].qualified_name)
        for edge in resolved.facts.edges
        if edge.type == edge_type and edge.source_id in by_id
    }


def _rendered(resolved) -> str:
    payload = {
        "entities": [asdict(item) for item in resolved.facts.entities],
        "edges": [asdict(item) for item in resolved.facts.edges],
        "evidence": [asdict(item) for item in resolved.facts.evidence],
        "diagnostics": [asdict(item) for item in resolved.facts.diagnostics],
        "adapter_diagnostics": [asdict(item) for item in resolved.diagnostics],
    }
    return json.dumps(payload)


def test_named_default_namespace_alias_and_path_alias_imports(tmp_path: Path) -> None:
    """AC-RKG-003 — README: named/default/namespace/alias, relative ../, @/ alias."""
    _write(
        tmp_path,
        "tsconfig.json",
        '{"compilerOptions":{"paths":{"@/*":["src/*"]}}}',
    )
    _write(tmp_path, "src/domain/order.ts", "export type Order = { id: string };\n")
    _write(
        tmp_path,
        "src/services/orderApi.ts",
        "export class OrderApi {}\nexport default class DefaultApi {}\n",
    )
    _write(
        tmp_path,
        "src/config/environment.ts",
        "export function parseEnvironment(): void {}\n",
    )
    _write(
        tmp_path,
        "src/components/OrderStatusBadge.tsx",
        "export function OrderStatusBadge(): null { return null; }\n",
    )
    _write(
        tmp_path,
        "src/analysis-cases/positive/aliasedCalls.ts",
        "import orderApi, { OrderApi as ApiClient } from '../../services/orderApi';\n"
        "import * as orderTypes from '../../domain/order';\n"
        "import { parseEnvironment as parseEnv } from '../../config/environment';\n"
        "import { OrderStatusBadge } from '@/components/OrderStatusBadge';\n"
        "export async function loadViaAlias(id: string): Promise<orderTypes.Order> {\n"
        "  void ApiClient; void parseEnv; void OrderStatusBadge;\n"
        "  return orderApi as never;\n"
        "}\n",
    )
    _, _, _, _, _, resolved = _run(tmp_path)
    imports = _edge_pairs(resolved, EdgeType.IMPORTS)
    # Semantic targets (path → module spelling per REG draft); no entity hash IDs.
    assert any(
        src.endswith("aliasedCalls") and "orderApi" in tgt for src, tgt in imports
    )
    assert any(
        src.endswith("aliasedCalls") and "domain.order" in tgt for src, tgt in imports
    )
    assert any(
        src.endswith("aliasedCalls") and "environment" in tgt for src, tgt in imports
    )
    assert any(
        src.endswith("aliasedCalls") and "OrderStatusBadge" in tgt
        for src, tgt in imports
    )
    assert all(edge.evidence_ids for edge in resolved.facts.edges)


def test_orders_page_call_chain_to_http_client(tmp_path: Path) -> None:
    """AC-RKG-048 / AC-RKG-007 — README chain OrdersPage→useOrders→listOrders→get."""
    _write(
        tmp_path,
        "src/services/httpClient.ts",
        "export class FetchHttpClient {\n"
        "  async get(path: string): Promise<unknown> { return path; }\n"
        "}\n"
        "export const httpClient = new FetchHttpClient();\n",
    )
    _write(
        tmp_path,
        "src/services/orderApi.ts",
        "import { httpClient } from './httpClient';\n"
        "export const orderApi = {\n"
        "  listOrders: () => httpClient.get('/api/orders'),\n"
        "};\n",
    )
    _write(
        tmp_path,
        "src/hooks/useOrders.ts",
        "import { orderApi } from '../services/orderApi';\n"
        "export function useOrders() {\n"
        "  return orderApi.listOrders();\n"
        "}\n",
    )
    _write(
        tmp_path,
        "src/app/routes/OrdersPage.tsx",
        "import { useOrders } from '../../hooks/useOrders';\n"
        "export function OrdersPage() {\n"
        "  useOrders();\n"
        "  return null;\n"
        "}\n",
    )
    _, _, _, _, _, resolved = _run(tmp_path)
    calls = _edge_pairs(resolved, EdgeType.CALLS)
    assert any("OrdersPage" in src and "useOrders" in tgt for src, tgt in calls), calls
    assert any("useOrders" in src and "listOrders" in tgt for src, tgt in calls), calls
    assert any("listOrders" in src and "get" in tgt for src, tgt in calls), calls
    call_edges = [e for e in resolved.facts.edges if e.type == EdgeType.CALLS]
    assert call_edges and all(edge.evidence_ids for edge in call_edges)
    list_orders = next(
        item
        for item in resolved.facts.entities
        if item.type == EntityType.CALLABLE and item.name == "listOrders"
    )
    assert dict(list_orders.attributes).get("http_requests") == "GET /api/orders"


def test_http_client_skips_dynamic_path_but_keeps_method(tmp_path: Path) -> None:
    """AC-RKG-006 — template path is not guessed; method from callee remains."""
    _write(
        tmp_path,
        "src/services/httpClient.ts",
        "export class FetchHttpClient {\n"
        "  async get<T>(path: string): Promise<T> { return path as T; }\n"
        "  async put<T>(path: string, body: unknown): Promise<T> { "
        "return body as T; }\n"
        "}\n"
        "export const httpClient = new FetchHttpClient();\n",
    )
    _write(
        tmp_path,
        "src/domain/order.ts",
        "export type Order = { id: string };\n",
    )
    _write(
        tmp_path,
        "src/services/orderApi.ts",
        "import type { Order } from '../domain/order';\n"
        "import { httpClient } from './httpClient';\n"
        "export class OrderApi {\n"
        "  getOrder(orderId: string): Promise<Order> {\n"
        "    return httpClient.get<Order>(`/api/orders/${orderId}`);\n"
        "  }\n"
        "  listOrders(): Promise<Order[]> {\n"
        "    return httpClient.get<Order[]>('/api/orders');\n"
        "  }\n"
        "}\n",
    )
    _, _, _, _, _, resolved = _run(tmp_path)
    by_name = {
        item.name: item
        for item in resolved.facts.entities
        if item.type == EntityType.CALLABLE
    }
    assert dict(by_name["getOrder"].attributes).get("http_requests") == "GET"
    assert dict(by_name["getOrder"].attributes).get("http_response_types") == "Order"
    assert (
        dict(by_name["listOrders"].attributes).get("http_requests") == "GET /api/orders"
    )
    assert (
        dict(by_name["listOrders"].attributes).get("http_response_types") == "Order[]"
    )
    # Relative path must not become an ExternalDependency origin.
    deps = {
        item.qualified_name
        for item in resolved.facts.entities
        if item.type == EntityType.EXTERNAL_DEPENDENCY
    }
    assert "/api/orders" not in deps


def test_vite_configuration_keys_and_inventory_origin(tmp_path: Path) -> None:
    """AC-RKG-003-ish config/HTTP — README keys + https://inventory.example.test."""
    _write(
        tmp_path,
        "src/config/environment.ts",
        "export function parseEnvironment(source: Record<string, string>) {\n"
        "  return {\n"
        "    apiBaseUrl: source.VITE_API_BASE_URL,\n"
        "    enableAdmin: source.VITE_ENABLE_ADMIN === 'true',\n"
        "  };\n"
        "}\n"
        "export function getEnvironment() {\n"
        "  return parseEnvironment(import.meta.env as Record<string, string>);\n"
        "}\n",
    )
    _write(
        tmp_path,
        "src/services/orderApi.ts",
        "export async function checkInventory(): Promise<void> {\n"
        "  await fetch('https://inventory.example.test/stock');\n"
        "}\n",
    )
    _, _, _, _, _, resolved = _run(tmp_path)
    config_names = {
        item.qualified_name
        for item in _entities_by_type(resolved, EntityType.CONFIGURATION)
    }
    assert any("VITE_API_BASE_URL" in name for name in config_names), config_names
    assert any("VITE_ENABLE_ADMIN" in name for name in config_names), config_names
    origins = {
        item.qualified_name
        for item in _entities_by_type(resolved, EntityType.EXTERNAL_DEPENDENCY)
    }
    assert "https://inventory.example.test" in origins
    # Values / secrets must not appear as graph attributes.
    for item in _entities_by_type(resolved, EntityType.CONFIGURATION):
        assert "value" not in dict(item.attributes)


def test_secret_sentinel_is_not_persisted(tmp_path: Path) -> None:
    """Safety — README sentinel must never appear in facts/diagnostics text."""
    _write(
        tmp_path,
        "src/config/environment.ts",
        f"export const fixtureNote = '{_SECRET}';\n"
        "export function parseEnvironment(source: Record<string, string>) {\n"
        "  return { apiBaseUrl: source.VITE_API_BASE_URL };\n"
        "}\n",
    )
    _, _, _, _, _, resolved = _run(tmp_path)
    assert _SECRET not in _rendered(resolved)
    assert _SECRET not in repr(resolved)


def test_dynamic_import_is_not_guessed(tmp_path: Path) -> None:
    """AC-RKG-006 — README dynamicImport.ts: no guessed internal import edge."""
    _write(
        tmp_path,
        "src/analysis-cases/negative/dynamicImport.ts",
        "// Expected: diagnostic; do not infer internal import for runtime target.\n"
        "export async function loadOptionalModule(moduleName: string) {\n"
        "  return import(/* @vite-ignore */ moduleName);\n"
        "}\n",
    )
    _write(tmp_path, "src/services/orderApi.ts", "export const orderApi = {};\n")
    _, _, _, _, parsed, resolved = _run(tmp_path)
    imports = _edge_pairs(resolved, EdgeType.IMPORTS)
    assert not any("dynamicImport" in src and "orderApi" in tgt for src, tgt in imports)
    codes = (
        {item.code for item in parsed.diagnostics}
        | {item.code for item in resolved.diagnostics}
        | {item.code for item in resolved.facts.diagnostics}
    )
    assert any("unresolved" in code or "dynamic" in code for code in codes), codes


def test_dynamic_url_is_not_guessed(tmp_path: Path) -> None:
    """AC-RKG-006 — README dynamicUrl.ts: no guessed external origin."""
    _write(
        tmp_path,
        "src/analysis-cases/negative/dynamicUrl.ts",
        "export async function loadFromHost(host: string) {\n"
        "  return fetch('https://' + host + '/items');\n"
        "}\n",
    )
    _, _, _, _, _, resolved = _run(tmp_path)
    origins = {
        item.qualified_name
        for item in _entities_by_type(resolved, EntityType.EXTERNAL_DEPENDENCY)
    }
    assert not any(name.startswith("https://") for name in origins), origins
    codes = {item.code for item in resolved.diagnostics} | {
        item.code for item in resolved.facts.diagnostics
    }
    assert any("unresolved" in code or "dynamic" in code for code in codes), codes


def test_ambiguous_binding_is_not_guessed(tmp_path: Path) -> None:
    """AC-RKG-006 — ambiguousBinding.ts: no unique calls for reassignment."""
    _write(
        tmp_path,
        "src/analysis-cases/negative/ambiguousBinding.ts",
        "function alpha() {}\n"
        "function beta() {}\n"
        "export function run(flag: boolean) {\n"
        "  let send = alpha;\n"
        "  if (flag) send = beta;\n"
        "  send();\n"
        "}\n",
    )
    _, _, _, _, _, resolved = _run(tmp_path)
    calls = _edge_pairs(resolved, EdgeType.CALLS)
    assert not any(
        "run" in src and ("alpha" in tgt or "beta" in tgt) for src, tgt in calls
    )


def test_shadowed_fetch_is_not_http_technology(tmp_path: Path) -> None:
    """AC-RKG-006 — README shadowedFetch.ts: local fetch ≠ HTTP client technology."""
    _write(
        tmp_path,
        "src/analysis-cases/negative/shadowedFetch.ts",
        "function fetch(url: string) { return url; }\n"
        "export function readLocal() {\n"
        "  return fetch('/local-only');\n"
        "}\n",
    )
    _, _, _, _, _, resolved = _run(tmp_path)
    assert not any(
        item.type == EntityType.EXTERNAL_DEPENDENCY
        or item.language_kind == "http_service"
        for item in resolved.facts.entities
    )
    tech_names = {
        tech.technology
        for tech in _typescript_adapter()
        .detect(
            build_manifest(
                resolve_local_source(
                    "repo-ts", tmp_path, LocalSourcePolicy((tmp_path,))
                ),
                SourceScanConfig(40, 32768, _TS_PATTERNS),
            )
        )
        .technologies
    }
    assert "fetch" not in tech_names


def test_syntax_error_is_isolated_with_relative_path(tmp_path: Path) -> None:
    """AC-RKG-035 — bad sibling diagnostic; valid file still extracts."""
    _write(
        tmp_path,
        "src/good.ts",
        "export function healthy(): number { return 1; }\n",
    )
    # Content mirrors fixture syntax-error.invalid.ts.fixture; analyzed as .ts corpus.
    _write(tmp_path, "src/syntax-error.ts", "export function broken(: void {\n")
    _, _, _, _, parsed, resolved = _run(tmp_path)
    assert any(unit.relative_path == "src/good.ts" for unit in parsed.units)
    diag = [
        (item.code, item.relative_path, item.line)
        for item in parsed.diagnostics
        if item.relative_path
    ]
    assert any(
        path == "src/syntax-error.ts" and line is not None for _, path, line in diag
    ), diag
    names = _qualified_names(resolved)
    assert any("healthy" in name for name in names)
    assert str(tmp_path) not in repr(resolved)
    assert str(tmp_path) not in _rendered(resolved)


def test_http_wrappers_dynamic_paths_and_effect_context_are_source_backed(tmp_path):
    _write(
        tmp_path,
        "api.ts",
        """
export class Client {
  get(path: string) { return this.request(path, {method: 'GET'}); }
  request(path: string, options: unknown) { return fetch(path, options); }
}
const client = new Client();
export function load(orderId: string) {
  return client.get(`/api/orders/${encodeURIComponent(orderId)}`);
}
export function useOrders() {
  useEffect(() => { load('example'); }, []);
}
""",
    )
    *_, resolved = _run(tmp_path)
    attrs = {e.qualified_name: dict(e.attributes) for e in resolved.facts.entities}
    assert attrs["api.Client.get"]["http_requests"] == "GET"
    assert attrs["api.load"]["http_requests"] == "GET"
    assert attrs["api.load"]["http_path_dynamic"] is True
    assert attrs["api.load"]["http_path_parameters"] == ("orderId",)
    assert attrs["api.useOrders"]["callback_calls"] == ("useEffect gọi api.load",)
    assert "/api/orders/example" not in json.dumps(attrs)


def test_map_metadata_requires_readonly_unshadowed_map_and_no_other_calls(tmp_path):
    _write(
        tmp_path,
        "store.ts",
        """
export class Store {
  private readonly rows = new Map();
  private mutable = new Map();
  read(id: string) { return this.rows.get(id); }
  mixed(id: string) { notify(); return this.rows.get(id); }
  mutableRead(id: string) { return this.mutable.get(id); }
}
""",
    )
    *_, resolved = _run(tmp_path)
    attrs = {e.qualified_name: dict(e.attributes) for e in resolved.facts.entities}
    assert attrs["store.Store.read"]["storage_operations_only"] is True
    assert attrs["store.Store.mixed"]["storage_operations_only"] is False
    assert "storage_kind" not in attrs["store.Store.mutableRead"]


def test_shadowed_map_does_not_claim_in_memory_or_no_sql(tmp_path):
    _write(
        tmp_path,
        "store.ts",
        """
class Map { get(id: string) { return query(id); } }
export class Store {
  private readonly rows = new Map();
  read(id: string) { return this.rows.get(id); }
}
""",
    )
    *_, resolved = _run(tmp_path)
    method = next(
        e for e in resolved.facts.entities if e.qualified_name == "store.Store.read"
    )
    assert "storage_kind" not in dict(method.attributes)
