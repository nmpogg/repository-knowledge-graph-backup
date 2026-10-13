"""TASK-RKG-009 static FastAPI endpoint and dependency facts."""

from __future__ import annotations

from pathlib import Path

import pytest

from rkg.adapters import (
    AdapterContext,
    AdapterRegistry,
    FastAPIFrameworkAdapter,
    PythonLanguageAdapter,
    run_framework_conformance,
)
from rkg.detection import FastAPIAppDetector, PythonImportDetector, select_adapters
from rkg.domain import (
    EdgeType,
    EntityType,
    SourceScanConfig,
    endpoint_id,
    validate_fact_batch,
)
from rkg.ingestion import LocalSourcePolicy, build_manifest, resolve_local_source


def _write(root: Path, path: str, content: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def _run(root: Path, *, application: str | None = None):
    config = SourceScanConfig(40, 32768)
    manifest = build_manifest(
        resolve_local_source("repo-nine", root, LocalSourcePolicy((root,))), config
    )
    context = AdapterContext("repo-nine", "snap-nine", "job-nine", config)
    language = PythonLanguageAdapter()
    parsed = language.parse(manifest, config)
    base = language.extract(context, parsed)
    base = language.resolve(context, parsed, base.facts)
    adapter = FastAPIFrameworkAdapter(application)
    result = adapter.extract(context, parsed, base.facts)
    validate_fact_batch(result.facts)
    report = run_framework_conformance(
        adapter,
        manifest,
        parsed,
        context,
        base.facts,
        no_execution_marker=lambda: False,
    )
    assert report.pass_rate == 1.0, report.cases
    return adapter, result


def _endpoints(result):
    return {
        item.id: item
        for item in result.facts.entities
        if item.type == EntityType.ENDPOINT
    }


@pytest.mark.parametrize("sequence", ["(first, second)", "[first, second]"])
def test_factory_literal_loop_and_empty_path(tmp_path: Path, sequence: str) -> None:
    _write(tmp_path, "pkg/__init__.py", "")
    for name in ("first", "second"):
        _write(
            tmp_path,
            f"pkg/{name}.py",
            "from fastapi import APIRouter\n"
            f"router = APIRouter(prefix='/{name}')\n"
            "@router.get('')\ndef handler():\n    pass\n",
        )
    _write(
        tmp_path,
        "pkg/routes.py",
        "from fastapi import APIRouter\nfrom . import first, second\n"
        "router = APIRouter(prefix='/v1')\n"
        f"for module in {sequence}:\n    router.include_router(module.router)\n",
    )
    _write(
        tmp_path,
        "pkg/main.py",
        "from fastapi import FastAPI as API\nfrom .routes import router\n"
        "raise RuntimeError('analyzed source must not execute')\n"
        "def create_app():\n"
        "    local_app = API()\n"
        "    settings = get_settings()\n"
        "    local_app.add_middleware(Middleware, options=settings.options)\n"
        "    local_app.include_router(router, prefix='/api')\n"
        "    return local_app\n"
        "app = create_app()\n",
    )
    _, result = _run(tmp_path, application="pkg.main:app")
    endpoints = _endpoints(result)
    assert sorted(dict(e.attributes)["path"] for e in endpoints.values()) == [
        "/api/v1/first",
        "/api/v1/second",
    ]
    entities = {e.id: e for e in result.facts.entities}
    assert sorted(
        entities[edge.target_id].qualified_name
        for edge in result.facts.edges
        if edge.type == EdgeType.HANDLED_BY
    ) == ["pkg.first.handler", "pkg.second.handler"]
    assert not result.diagnostics


@pytest.mark.parametrize(
    "factory",
    [
        "def make(flag):\n    app = FastAPI()\n    return app\napp = make(True)\n",
        "def make():\n    app = FastAPI()\n    if condition:\n"
        "        return app\n    return app\napp = make()\n",
        "def make():\n    app = FastAPI()\n    app = replacement\n"
        "    return app\napp = make()\n",
        "def make():\n    app = FastAPI()\n    router = replacement\n"
        "    app.include_router(router)\n    return app\napp = make()\n",
    ],
)
def test_ambiguous_factories_do_not_guess_routes(tmp_path: Path, factory: str) -> None:
    _write(
        tmp_path,
        "main.py",
        "from fastapi import FastAPI, APIRouter\n"
        "router = APIRouter(prefix='/items')\n"
        "@router.get('')\ndef handler():\n    pass\n" + factory,
    )
    _, result = _run(tmp_path)
    assert not _endpoints(result)
    assert "fastapi_app_unresolved" in {d.code for d in result.diagnostics}


def test_dynamic_loop_is_diagnostic_and_unattached_routes_are_not_published(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path,
        "main.py",
        "from fastapi import FastAPI, APIRouter\n"
        "app = FastAPI()\nrouter = APIRouter(prefix='/items')\n"
        "@router.get('')\ndef handler():\n    pass\n"
        "for item in get_routers():\n    app.include_router(item)\n",
    )
    _, result = _run(tmp_path)
    assert not _endpoints(result)
    assert "fastapi_router_unresolved" in {d.code for d in result.diagnostics}


def test_empty_path_without_effective_prefix_is_rejected(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "main.py",
        "from fastapi import FastAPI\napp = FastAPI()\n"
        "@app.get('')\ndef handler():\n    pass\n",
    )
    _, result = _run(tmp_path)
    assert not _endpoints(result)
    assert "fastapi_route_dynamic" in {d.code for d in result.diagnostics}


def test_direct_nested_router_multi_method_and_unattached_router(
    tmp_path: Path,
) -> None:
    _write(tmp_path, "pkg/__init__.py", "")
    _write(
        tmp_path,
        "pkg/routes.py",
        "from fastapi import APIRouter\n"
        "leaf = APIRouter(prefix='/v1')\n"
        "@leaf.api_route('/items/{item_id}/', methods=['GET', 'POST'])\n"
        "def item(item_id):\n    return item_id\n"
        "parent = APIRouter()\nparent.include_router(leaf, prefix='/nested')\n"
        "unused = APIRouter()\n@unused.get('/hidden')\n"
        "def hidden():\n    pass\n",
    )
    _write(
        tmp_path,
        "pkg/main.py",
        "from fastapi import FastAPI\n"
        "from .routes import parent\n"
        "app = FastAPI()\n"
        "@app.get('/health/')\ndef health():\n    pass\n"
        "app.include_router(parent, prefix='/api')\n"
        "app.include_router(parent, prefix='/api')\n"
        "app.include_router(parent, prefix='/alt')\n",
    )
    adapter, result = _run(tmp_path, application="pkg.main:app")
    assert adapter.detect is not None
    endpoints = _endpoints(result)
    methods_paths = [
        (dict(item.attributes)["method"], dict(item.attributes)["path"])
        for item in endpoints.values()
    ]
    assert sorted(methods_paths) == [
        ("GET", "/alt/nested/v1/items/{item_id}/"),
        ("GET", "/api/nested/v1/items/{item_id}/"),
        ("GET", "/api/nested/v1/items/{item_id}/"),
        ("GET", "/health/"),
        ("POST", "/alt/nested/v1/items/{item_id}/"),
        ("POST", "/api/nested/v1/items/{item_id}/"),
        ("POST", "/api/nested/v1/items/{item_id}/"),
    ]
    assert len(set(endpoints)) == 7
    for endpoint in endpoints.values():
        assert any(
            edge.type == EdgeType.EXPOSES and edge.target_id == endpoint.id
            for edge in result.facts.edges
        )
        assert any(
            edge.type == EdgeType.HANDLED_BY and edge.source_id == endpoint.id
            for edge in result.facts.edges
        )
    assert not any("hidden" in item.qualified_name for item in endpoints.values())


def test_declared_dependencies_across_wiring_layers(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "main.py",
        "from typing import Annotated\n"
        "from fastapi import FastAPI, APIRouter, Depends\n"
        "def base():\n    pass\n"
        "def sub(x=Depends(base)):\n    pass\n"
        "def app_dep():\n    pass\n"
        "def router_dep():\n    pass\n"
        "def include_dep():\n    pass\n"
        "def decorator_dep():\n    pass\n"
        "app = FastAPI(dependencies=[Depends(app_dep)])\n"
        "router = APIRouter(dependencies=[Depends(router_dep)])\n"
        "@router.get('/item', dependencies=[Depends(decorator_dep)])\n"
        "def handler(x=Depends(sub), y: Annotated[str, Depends(base)] = ''):\n"
        "    pass\n"
        "app.include_router(router, dependencies=[Depends(include_dep)])\n",
    )
    _, result = _run(tmp_path)
    entities = {item.id: item for item in result.facts.entities}
    depends = {
        (
            entities[edge.source_id].qualified_name,
            entities[edge.target_id].qualified_name,
        )
        for edge in result.facts.edges
        if edge.type == EdgeType.DEPENDS_ON and edge.source_id in entities
    }
    assert ("main.sub", "main.base") in depends
    assert ("main.handler", "main.sub") in depends
    assert ("main.handler", "main.base") in depends
    endpoint = next(iter(_endpoints(result).values()))
    assert {
        target for source, target in depends if source == endpoint.qualified_name
    } == {"main.app_dep", "main.router_dep", "main.include_dep", "main.decorator_dep"}
    assert not any(edge.type == EdgeType.CALLS for edge in result.facts.edges)


def test_dynamic_routes_duplicate_binding_and_local_shadow_are_conservative(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path,
        "main.py",
        "from fastapi import FastAPI, APIRouter, Depends\n"
        "app = FastAPI()\nrouter = APIRouter()\n"
        "path = '/dynamic'\n"
        "@app.get(path)\ndef dynamic():\n    pass\n"
        "@router.get('/unattached')\ndef unattached():\n    pass\n"
        "@app.get('/duplicate')\ndef duplicate():\n    pass\n"
        "@app.get('/duplicate')\ndef duplicate():\n    pass\n"
        "@app.get('/bad', dependencies=variable)\n"
        "def bad():\n    pass\n",
    )
    _, result = _run(tmp_path)
    paths = {dict(item.attributes)["path"] for item in _endpoints(result).values()}
    assert paths == {"/bad"}
    assert {item.code for item in result.diagnostics} >= {
        "fastapi_route_dynamic",
        "fastapi_dependency_unsupported",
    }
    assert all(
        item.file_path == "main.py" and item.line
        for item in result.facts.diagnostics
        if item.code.startswith("fastapi_")
    )

    _write(tmp_path, "fastapi.py", "class FastAPI:\n    pass\n")
    _, shadowed = _run(tmp_path)
    assert _endpoints(shadowed) == {}


def test_direct_registration_and_router_cycle(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "main.py",
        "from fastapi import FastAPI, APIRouter\n"
        "app = FastAPI()\n"
        "first = APIRouter()\nsecond = APIRouter()\n"
        "def handler():\n    pass\n"
        "app.add_api_route('/direct/', handler, methods=['PATCH', 'GET'])\n"
        "first.add_api_route('/from-router', handler)\n"
        "first.include_router(second)\nsecond.include_router(first)\n"
        "app.include_router(first, prefix='/api')\n",
    )
    _, result = _run(tmp_path)
    paths = sorted(
        dict(item.attributes)["path"] for item in _endpoints(result).values()
    )
    assert paths == ["/api/from-router", "/direct/", "/direct/"]
    assert "fastapi_router_cycle" in {item.code for item in result.diagnostics}


def test_registered_adapter_is_selected_with_verified_version(tmp_path: Path) -> None:
    _write(tmp_path, "pyproject.toml", '[project]\ndependencies = ["fastapi>=0.100"]\n')
    _write(tmp_path, "uv.lock", '[[package]]\nname = "fastapi"\nversion = "0.115.0"\n')
    _write(
        tmp_path,
        "main.py",
        "from fastapi import FastAPI\napp = FastAPI()\n"
        "@app.get('/ready')\ndef ready():\n    pass\n",
    )
    config = SourceScanConfig(40, 32768)
    manifest = build_manifest(
        resolve_local_source("repo-nine", tmp_path, LocalSourcePolicy((tmp_path,))),
        config,
    )
    language = PythonLanguageAdapter()
    parsed = language.parse(manifest, config)
    registry = AdapterRegistry()
    adapter = FastAPIFrameworkAdapter("main:app")
    assert registry.register(language).accepted
    assert registry.register(adapter).accepted
    selection = select_adapters(
        manifest,
        parsed,
        language,
        registry,
        (PythonImportDetector(), FastAPIAppDetector()),
    )
    assert selection.status == "ready"
    assert selection.deep_adapters == (adapter,)
    assert selection.selected_application.reference == "main:app"
    _, result = _run(tmp_path, application=selection.selected_application.reference)
    endpoints = _endpoints(result)
    assert {dict(item.attributes)["path"] for item in endpoints.values()} == {"/ready"}
    assert (
        endpoint_id(
            "repo-nine",
            "main.py",
            "main.ready",
            "GET",
            "/ready",
            ("app:main.app", "route:main.py:3:GET"),
        )
        in endpoints
    )


def test_multiple_apps_require_explicit_entrypoint(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "main.py",
        "from fastapi import FastAPI\n"
        "first = FastAPI()\nsecond = FastAPI()\n"
        "@first.get('/first')\ndef one():\n    pass\n"
        "@second.get('/second')\ndef two():\n    pass\n",
    )
    _, ambiguous = _run(tmp_path)
    assert _endpoints(ambiguous) == {}
    assert "fastapi_app_ambiguous" in {item.code for item in ambiguous.diagnostics}
    _, selected = _run(tmp_path, application="main:second")
    assert {
        dict(item.attributes)["path"] for item in _endpoints(selected).values()
    } == {"/second"}
