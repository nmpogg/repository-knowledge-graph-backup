"""Static Gin, chi, and gorilla/mux routes. Not a reviewed deep-support profile."""

from __future__ import annotations

from pathlib import Path

from rkg.adapters import (
    AdapterContext,
    SupportState,
    run_framework_conformance,
)
from rkg.adapters.go_http_framework import GoHTTPFrameworkAdapter
from rkg.adapters.go_language import GoLanguageAdapter
from rkg.domain import EdgeType, EntityType, SourceScanConfig, validate_fact_batch
from rkg.ingestion import LocalSourcePolicy, build_manifest, resolve_local_source

_SECRET = "RKG_TEST_SECRET_DO_NOT_PERSIST"


def _write(root: Path, path: str, content: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def _run(root: Path):
    config = SourceScanConfig(40, 32768, ("*.go", "**/*.go"), ("**/*_test.go",))
    manifest = build_manifest(
        resolve_local_source("repo-go-http", root, LocalSourcePolicy((root,))),
        config,
    )
    context = AdapterContext("repo-go-http", "snap-go-http", "job-go-http", config)
    language = GoLanguageAdapter()
    parsed = language.parse(manifest, config)
    base = language.extract(context, parsed)
    base = language.resolve(context, parsed, base.facts)
    adapter = GoHTTPFrameworkAdapter()
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
    assert adapter.reviewed_deep_support is False
    assert {item.support_state for item in result.capabilities} == {
        SupportState.DETECTED_ONLY
    }
    return result


def _endpoints(result):
    return [item for item in result.facts.entities if item.type == EntityType.ENDPOINT]


def _handled(result) -> set[str]:
    entities = {item.id: item for item in result.facts.entities}
    return {
        entities[edge.target_id].qualified_name
        for edge in result.facts.edges
        if edge.type == EdgeType.HANDLED_BY
    }


def _handled_routes(result) -> set[tuple[str, str, str]]:
    entities = {item.id: item for item in result.facts.entities}
    found = set()
    for edge in result.facts.edges:
        if edge.type != EdgeType.HANDLED_BY:
            continue
        source = entities[edge.source_id]
        target = entities[edge.target_id]
        attrs = dict(source.attributes)
        found.add((attrs["method"], attrs["path"], target.qualified_name))
    return found


def test_static_gin_chi_mux_routes_and_dynamic_path(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "routes.go",
        "package httpapi\n"
        "\n"
        "import (\n"
        '\t"github.com/gin-gonic/gin"\n'
        '\t"github.com/go-chi/chi/v5"\n'
        '\t"github.com/gorilla/mux"\n'
        ")\n"
        "\n"
        'const OrdersPath = "/orders"\n'
        f'const suppressedPath = "{_SECRET}"\n'
        "\n"
        "func GinHealth() {}\n"
        "func ChiCatalog() {}\n"
        "func MuxShipment() {}\n"
        "\n"
        "func Register() {\n"
        "\tengine := gin.Default()\n"
        '\tengine.GET("/health", GinHealth)\n'
        "\tapi := engine.Group(\"/v1\")\n"
        "\tapi.POST(OrdersPath, GinHealth)\n"
        "\tengine.GET(suppressedPath, GinHealth)\n"
        '\tsuffix := "x"\n'
        '\tengine.PUT("/dyn/"+suffix, GinHealth)\n'
        "\tchiRouter := chi.NewRouter()\n"
        "\tchiRouter.Get(OrdersPath, ChiCatalog)\n"
        "\tmuxRouter := mux.NewRouter()\n"
        '\tmuxRouter.HandleFunc("/shipments", MuxShipment).Methods("POST")\n'
        "}\n",
    )
    result = _run(tmp_path)
    found = sorted(
        (dict(item.attributes)["method"], dict(item.attributes)["path"])
        for item in _endpoints(result)
    )
    assert found == [
        ("GET", "/health"),
        ("GET", "/orders"),
        ("POST", "/shipments"),
        ("POST", "/v1/orders"),
    ]
    assert _handled(result) == {
        "httpapi.GinHealth",
        "httpapi.ChiCatalog",
        "httpapi.MuxShipment",
    }
    assert EdgeType.DEPENDS_ON not in {edge.type for edge in result.facts.edges}
    dynamic = [
        item
        for item in result.facts.diagnostics
        if item.code == "go_http_route_dynamic"
    ]
    assert dynamic
    assert all(item.file_path == "routes.go" and item.line for item in dynamic)
    rendered = repr(result.facts)
    assert _SECRET not in rendered
    assert all(_SECRET not in item.message for item in result.facts.diagnostics)


def test_shadowed_handler_has_no_edge(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "routes.go",
        "package httpapi\n"
        "\n"
        'import "github.com/gin-gonic/gin"\n'
        "\n"
        "func GinHealth() {}\n"
        "\n"
        "func Register(GinHealth func()) {\n"
        "\tengine := gin.Default()\n"
        '\tengine.GET("/health", GinHealth)\n'
        "}\n",
    )
    result = _run(tmp_path)
    found = {
        (dict(item.attributes)["method"], dict(item.attributes)["path"])
        for item in _endpoints(result)
    }
    assert found == {("GET", "/health")}
    assert _handled(result) == set()
    codes = {item.code for item in result.facts.diagnostics}
    assert "go_http_handler_unresolved" in codes


def test_duplicate_function_name_has_no_edge(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "a.go",
        "package httpapi\n"
        "\n"
        'import "github.com/gin-gonic/gin"\n'
        "\n"
        "func GinHealth() {}\n"
        "\n"
        "func Register() {\n"
        "\tengine := gin.Default()\n"
        '\tengine.GET("/health", GinHealth)\n'
        "}\n",
    )
    _write(tmp_path, "b.go", "package httpapi\n\nfunc GinHealth() {}\n")
    result = _run(tmp_path)
    assert _handled(result) == set()
    codes = {item.code for item in result.facts.diagnostics}
    assert "go_http_handler_unresolved" in codes


def test_range_and_block_shadow_end_with_the_block(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "routes.go",
        "package httpapi\n"
        "\n"
        'import "github.com/gin-gonic/gin"\n'
        "\n"
        "func GinHealth() {}\n"
        "func Other() {}\n"
        "\n"
        "func Register(items []func()) {\n"
        "\tengine := gin.Default()\n"
        "\tfor _, GinHealth := range items {\n"
        '\t\tengine.GET("/ranged", GinHealth)\n'
        "\t}\n"
        '\tengine.GET("/after-range", GinHealth)\n'
        "\t{\n"
        "\t\tGinHealth := items\n"
        '\t\tengine.GET("/shadow-block", GinHealth)\n'
        "\t}\n"
        "\t{\n"
        "\t\tGinHealth := Other\n"
        '\t\tengine.GET("/block", GinHealth)\n'
        "\t}\n"
        '\tengine.GET("/after-block", GinHealth)\n'
        "\tif GinHealth := Other; true {\n"
        '\t\tengine.GET("/if", GinHealth)\n'
        "\t}\n"
        '\tengine.GET("/after-if", GinHealth)\n'
        "}\n",
    )
    result = _run(tmp_path)
    assert _handled_routes(result) == {
        ("GET", "/after-range", "httpapi.GinHealth"),
        ("GET", "/block", "httpapi.Other"),
        ("GET", "/after-block", "httpapi.GinHealth"),
        ("GET", "/if", "httpapi.Other"),
        ("GET", "/after-if", "httpapi.GinHealth"),
    }
    codes = {item.code for item in result.facts.diagnostics}
    assert "go_http_handler_unresolved" in codes


def test_router_group_parameter_emits_no_route(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "routes.go",
        "package httpapi\n"
        "\n"
        "import (\n"
        '\t"github.com/gin-gonic/gin"\n'
        '\t"github.com/go-chi/chi"\n'
        '\t"github.com/gorilla/mux"\n'
        ")\n"
        "\n"
        "func GinHealth() {}\n"
        "\n"
        "func Mount(api *gin.RouterGroup) {\n"
        '\tapi.POST("/orders", GinHealth)\n'
        "}\n"
        "\n"
        "func ChiMount(r chi.Router) {\n"
        '\tr.Get("/catalog", GinHealth)\n'
        "}\n"
        "\n"
        "func MuxMount(r *mux.Router) {\n"
        '\tr.HandleFunc("/ship", GinHealth).Methods("GET")\n'
        "}\n",
    )
    result = _run(tmp_path)
    assert _endpoints(result) == []
    assert _handled(result) == set()
    codes = {item.code for item in result.facts.diagnostics}
    assert "go_http_route_dynamic" in codes
