"""Nest framework adapter: controller routes and message channels."""

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


def _nest_adapter():
    from rkg.adapters.nest_framework import NestFrameworkAdapter

    return NestFrameworkAdapter()


def _write(root: Path, relative: str, source: str) -> None:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")


def _run(root: Path):
    config = SourceScanConfig(40, 32768, _TS_PATTERNS)
    manifest = build_manifest(
        resolve_local_source("repo-nest", root, LocalSourcePolicy((root,))),
        config,
    )
    context = AdapterContext("repo-nest", "snap-nest", "job-nest", config)
    language = _typescript_adapter()
    parsed = language.parse(manifest, config)
    base = language.resolve(
        context, parsed, language.extract(context, parsed).facts
    ).facts
    adapter = _nest_adapter()
    result = adapter.extract(context, parsed, base)
    validate_fact_batch(result.facts)
    return adapter, result


def _http(result) -> set[tuple[str, str]]:
    return {
        (dict(item.attributes).get("method"), dict(item.attributes).get("path"))
        for item in result.facts.entities
        if item.type == EntityType.ENDPOINT
    }


def _channels(result) -> set[tuple[str, str]]:
    return {
        (
            str(dict(item.attributes).get("channel_kind")),
            item.qualified_name,
        )
        for item in result.facts.entities
        if item.type == EntityType.MESSAGE_CHANNEL
    }


def test_controller_prefix_and_message_channels(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "src/constants.ts",
        'export const ORDERS = "orders";\n'
        'export const API_PREFIX = "api";\n'
        'export const SHOP = "shop";\n'
        'export const CREATED = "order.created";\n',
    )
    _write(
        tmp_path,
        "src/orders.controller.ts",
        "import { Controller, Get, Post, MessagePattern, EventPattern } "
        "from '@nestjs/common';\n"
        "import { CREATED, ORDERS } from './constants';\n"
        "@Controller(ORDERS)\n"
        "export class OrdersController {\n"
        "  @Get(':id')\n"
        "  findOne(): void {}\n"
        "  @Post()\n"
        "  create(): void {}\n"
        "  @MessagePattern(CREATED)\n"
        "  onCreated(): void {}\n"
        "  @EventPattern('order.shipped')\n"
        "  onShipped(): void {}\n"
        "}\n",
    )
    _write(
        tmp_path,
        "src/orders.module.ts",
        "import { Module } from '@nestjs/common';\n"
        "import { OrdersController } from './orders.controller';\n"
        "@Module({ controllers: [OrdersController] })\n"
        "export class OrdersModule {}\n",
    )
    _write(
        tmp_path,
        "src/app.module.ts",
        "import { Module } from '@nestjs/common';\n"
        "import { RouterModule } from '@nestjs/core';\n"
        "import { SHOP } from './constants';\n"
        "import { OrdersModule } from './orders.module';\n"
        "@Module({\n"
        "  imports: [RouterModule.register([{ path: SHOP, module: OrdersModule }])],\n"
        "})\n"
        "export class AppModule {}\n",
    )
    _write(
        tmp_path,
        "src/main.ts",
        "import { NestFactory } from '@nestjs/core';\n"
        "import { API_PREFIX } from './constants';\n"
        "import { AppModule } from './app.module';\n"
        "export async function bootstrap(): Promise<void> {\n"
        "  const app = await NestFactory.create(AppModule);\n"
        "  app.setGlobalPrefix(API_PREFIX);\n"
        "}\n",
    )
    adapter, result = _run(tmp_path)
    assert adapter.reviewed_deep_support is False
    assert {item.support_state for item in result.capabilities} == {
        SupportState.DETECTED_ONLY
    }
    assert _http(result) == {
        ("GET", "/api/shop/orders/:id"),
        ("POST", "/api/shop/orders"),
    }
    assert _channels(result) == {
        ("pattern", "order.created"),
        ("event", "order.shipped"),
    }
    by_id = {item.id: item for item in result.facts.entities}
    consumes = {
        (
            by_id[edge.source_id].qualified_name,
            by_id[edge.target_id].qualified_name,
        )
        for edge in result.facts.edges
        if edge.type == EdgeType.CONSUMES
    }
    assert consumes == {
        ("src.orders.controller.OrdersController.onCreated", "order.created"),
        ("src.orders.controller.OrdersController.onShipped", "order.shipped"),
    }
    assert not any(
        item.type == EntityType.ENDPOINT
        and dict(item.attributes).get("path") in {"order.created", "order.shipped"}
        for item in result.facts.entities
    )
    assert _SECRET not in repr(result.facts)


def test_dynamic_prefix_and_pattern_emit_no_edge(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "src/negative.controller.ts",
        "import { Controller, Get, MessagePattern } from '@nestjs/common';\n"
        "const runtimePrefix = 'audit' + '/dyn';\n"
        "@Controller(runtimePrefix)\n"
        "export class DynamicController {\n"
        "  @Get('items')\n"
        "  list(): void {}\n"
        "}\n"
        "@Controller('audit')\n"
        "export class AuditController {\n"
        "  @Get(runtimePrefix)\n"
        "  search(): void {}\n"
        "  @MessagePattern(runtimePrefix)\n"
        "  onRuntime(): void {}\n"
        "}\n",
    )
    _, result = _run(tmp_path)
    assert _http(result) == set()
    assert _channels(result) == set()
    assert not [
        edge
        for edge in result.facts.edges
        if edge.type in {EdgeType.HANDLED_BY, EdgeType.CONSUMES, EdgeType.PUBLISHES}
    ]
    codes = {item.code for item in result.facts.diagnostics}
    assert "nest_prefix_dynamic" in codes
    assert "nest_route_dynamic" in codes
    assert "nest_pattern_dynamic" in codes
    assert _SECRET not in repr(result.facts)
