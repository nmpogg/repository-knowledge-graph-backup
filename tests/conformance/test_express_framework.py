"""Express framework adapter: static verb routes, middleware evidence only."""

from __future__ import annotations

from pathlib import Path

from rkg.adapters.contracts import AdapterContext, SupportState
from rkg.domain import EdgeType, EntityType, SourceScanConfig, validate_fact_batch
from rkg.ingestion import LocalSourcePolicy, build_manifest, resolve_local_source

_TS_PATTERNS = ("*.ts", "*.tsx", "**/*.ts", "**/*.tsx")
_SECRET = "RKG_TEST_SECRET_DO_NOT_PERSIST"


def _typescript_adapter():
    from rkg.adapters.typescript_language import TypeScriptLanguageAdapter

    return TypeScriptLanguageAdapter()


def _express_adapter():
    from rkg.adapters.express_framework import ExpressFrameworkAdapter

    return ExpressFrameworkAdapter()


def _write(root: Path, relative: str, source: str) -> None:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")


def _run(root: Path):
    config = SourceScanConfig(40, 32768, _TS_PATTERNS)
    manifest = build_manifest(
        resolve_local_source("repo-express", root, LocalSourcePolicy((root,))),
        config,
    )
    context = AdapterContext("repo-express", "snap-express", "job-express", config)
    language = _typescript_adapter()
    parsed = language.parse(manifest, config)
    base = language.resolve(
        context, parsed, language.extract(context, parsed).facts
    ).facts
    adapter = _express_adapter()
    result = adapter.extract(context, parsed, base)
    validate_fact_batch(result.facts)
    return adapter, result


def _endpoints(result) -> dict[tuple[str, str], str]:
    return {
        (
            dict(item.attributes)["method"],
            dict(item.attributes)["path"],
        ): item.qualified_name
        for item in result.facts.entities
        if item.type == EntityType.ENDPOINT
    }


def _handled(result) -> dict[str, str]:
    by_id = {item.id: item for item in result.facts.entities}
    return {
        by_id[edge.source_id].qualified_name: by_id[edge.target_id].qualified_name
        for edge in result.facts.edges
        if edge.type == EdgeType.HANDLED_BY
    }


def test_static_verb_routes_and_imported_handler(tmp_path: Path) -> None:
    _write(tmp_path, "src/constants.ts", 'export const ORDERS_PATH = "/orders";\n')
    _write(
        tmp_path,
        "src/handlers.ts",
        "export function listOrders(): void {}\n",
    )
    _write(
        tmp_path,
        "src/app.ts",
        "import express, { Router } from 'express';\n"
        "import { ORDERS_PATH } from './constants';\n"
        "import { listOrders } from './handlers';\n"
        "const app = express();\n"
        "const router = Router();\n"
        "function healthCheck(): void {}\n"
        "function requestLogger(): void {}\n"
        "app.get('/health', healthCheck);\n"
        "app.get(ORDERS_PATH, listOrders);\n"
        "router.delete('/orders/:id', listOrders);\n"
        "app.put('/orders/:id', (_req: unknown, _res: unknown) => {});\n"
        "app.use(requestLogger);\n",
    )
    adapter, result = _run(tmp_path)
    assert adapter.reviewed_deep_support is False
    assert {item.support_state for item in result.capabilities} == {
        SupportState.DETECTED_ONLY
    }
    assert _endpoints(result) == {
        ("GET", "/health"): "src.app.GET /health",
        ("GET", "/orders"): "src.app.GET /orders",
        ("DELETE", "/orders/:id"): "src.app.DELETE /orders/:id",
        ("PUT", "/orders/:id"): "src.app.PUT /orders/:id",
    }
    handled = _handled(result)
    assert handled["src.app.GET /health"] == "src.app.healthCheck"
    assert handled["src.app.GET /orders"] == "src.handlers.listOrders"
    assert "src.app.PUT /orders/:id" not in handled
    rules = {item.rule for item in result.facts.evidence}
    assert "RKG.express.middleware.v1" in rules
    express_entities = [
        item for item in result.facts.entities if item.framework_kind == "express"
    ]
    assert express_entities
    assert all(item.type == EntityType.ENDPOINT for item in express_entities)
    assert _SECRET not in repr(result.facts)


def test_dynamic_path_and_shadow_emit_no_edge(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "src/app.ts",
        "import express from 'express';\n"
        "const hidden = '/hidden';\n"
        "const app = express();\n"
        "function list(): void {}\n"
        "const dynamicPath = '/items/' + 'x';\n"
        "app.get(dynamicPath, list);\n"
        "function register(hidden: string): void {\n"
        "  app.get(hidden, list);\n"
        "}\n"
        "function wrap(): void {\n"
        "  const app = { get(_path: string, _handler: unknown): void {} };\n"
        "  app.get('/nope', list);\n"
        "}\n",
    )
    _, result = _run(tmp_path)
    assert _endpoints(result) == {}
    assert not [
        edge for edge in result.facts.edges if edge.type == EdgeType.HANDLED_BY
    ]
    codes = {item.code for item in result.facts.diagnostics}
    assert "express_route_dynamic" in codes
    assert "express_receiver_shadowed" in codes
    assert _SECRET not in repr(result.facts)


def test_reassigned_handler_emits_no_edge(tmp_path: Path) -> None:
    """A later assignment of the same name is not a unique handler."""
    _write(
        tmp_path,
        "src/app.ts",
        "import express from 'express';\n"
        "const app = express();\n"
        "function list(): void {}\n"
        "list = function (): void {};\n"
        "app.get('/reassigned', list);\n",
    )
    _, result = _run(tmp_path)
    assert not [
        edge for edge in result.facts.edges if edge.type == EdgeType.HANDLED_BY
    ]
    codes = {item.code for item in result.facts.diagnostics}
    assert "express_handler_unresolved" in codes
    assert _SECRET not in repr(result.facts)
