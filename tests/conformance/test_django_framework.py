"""Static Django routes that are not part of a reviewed deep-support profile."""

from __future__ import annotations

from pathlib import Path

from rkg.adapters import (
    AdapterContext,
    DjangoFrameworkAdapter,
    PythonLanguageAdapter,
    SupportState,
    run_framework_conformance,
)
from rkg.domain import EdgeType, EntityType, SourceScanConfig, validate_fact_batch
from rkg.ingestion import LocalSourcePolicy, build_manifest, resolve_local_source

_SECRET = "RKG_TEST_SECRET_DO_NOT_PERSIST"


def _write(root: Path, path: str, content: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def _run(root: Path):
    config = SourceScanConfig(40, 32768)
    manifest = build_manifest(
        resolve_local_source("repo-django", root, LocalSourcePolicy((root,))), config
    )
    context = AdapterContext("repo-django", "snap-django", "job-django", config)
    language = PythonLanguageAdapter()
    parsed = language.parse(manifest, config)
    base = language.extract(context, parsed)
    base = language.resolve(context, parsed, base.facts)
    adapter = DjangoFrameworkAdapter()
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
    assert {item.support_state for item in result.capabilities} == {
        SupportState.DETECTED_ONLY
    }
    assert adapter.reviewed_deep_support is False
    return result


def test_path_include_as_view_and_negative_include(tmp_path: Path) -> None:
    _write(tmp_path, "shop/__init__.py", "")
    _write(
        tmp_path,
        "shop/views.py",
        "from django.views import View\n"
        "from django.views.decorators.http import require_POST\n"
        f"_SECRET = '{_SECRET}'\n"
        "def health(request):\n"
        "    return None\n"
        "def legacy_report(request):\n"
        "    return None\n"
        "@require_POST\n"
        "def create_order(request):\n"
        "    return None\n"
        "class OrderDetail(View):\n"
        "    http_method_names = ['get']\n"
        "    def get(self, request, pk):\n"
        "        return None\n"
        "class BareDetail(View):\n"
        "    def get(self, request):\n"
        "        return None\n"
        "def unused(request):\n"
        "    return None\n",
    )
    _write(
        tmp_path,
        "shop/urls.py",
        "from django.urls import path\n"
        "from shop.views import create_order\n"
        "urlpatterns = [path('orders/', create_order)]\n",
    )
    _write(
        tmp_path,
        "config/urls.py",
        "from django.conf.urls import url\n"
        "from django.urls import include, path, re_path\n"
        "from shop.views import BareDetail, OrderDetail, health\n"
        "HEALTH_ROUTE = 'health/'\n"
        "def _dynamic_urls():\n"
        "    return 'shop.urls'\n"
        "urlpatterns = [\n"
        "    path(HEALTH_ROUTE, health),\n"
        "    path('orders/<int:pk>/', OrderDetail.as_view()),\n"
        "    path('bare/', BareDetail.as_view()),\n"
        "    path('shop/', include('shop.urls')),\n"
        "    re_path(r'^legacy/$', 'shop.views.legacy_report'),\n"
        "    url(r'^old/$', health),\n"
        "    path('ghost/', missing_view),\n"
        "    path('dyn/', include(_dynamic_urls())),\n"
        "]\n",
    )
    result = _run(tmp_path)
    endpoints = [
        item
        for item in result.facts.entities
        if item.type == EntityType.ENDPOINT
    ]
    found = sorted(
        (
            (
                dict(item.attributes).get("method"),
                dict(item.attributes)["path"],
                item.qualified_name,
            )
            for item in endpoints
        ),
        key=lambda item: (item[1], item[0] or "", item[2]),
    )
    assert found == [
        (None, "/bare/", "shop.views.BareDetail.as_view::/bare/"),
        (None, "/health/", "shop.views.health::/health/"),
        (
            "GET",
            "/orders/<int:pk>/",
            "shop.views.OrderDetail.as_view:GET:/orders/<int:pk>/",
        ),
        ("POST", "/shop/orders/", "shop.views.create_order:POST:/shop/orders/"),
        (None, "^legacy/$", "shop.views.legacy_report::^legacy/$"),
        (None, "^old/$", "shop.views.health::^old/$"),
    ]
    entities = {item.id: item for item in result.facts.entities}
    handled = {
        (
            entities[edge.source_id].qualified_name,
            entities[edge.target_id].qualified_name,
        )
        for edge in result.facts.edges
        if edge.type == EdgeType.HANDLED_BY
    }
    assert handled == {
        ("shop.views.health::/health/", "shop.views.health"),
        ("shop.views.health::^old/$", "shop.views.health"),
        (
            "shop.views.OrderDetail.as_view:GET:/orders/<int:pk>/",
            "shop.views.OrderDetail.get",
        ),
        ("shop.views.create_order:POST:/shop/orders/", "shop.views.create_order"),
        ("shop.views.legacy_report::^legacy/$", "shop.views.legacy_report"),
    }
    assert "shop.views.unused" not in {target for _, target in handled}
    assert "shop.views.BareDetail.get" not in {target for _, target in handled}
    bare = next(item for item in endpoints if dict(item.attributes)["path"] == "/bare/")
    assert "method" not in dict(bare.attributes)
    assert not any(
        "ghost" in item.qualified_name or "/dyn" in dict(item.attributes)["path"]
        for item in endpoints
    )
    codes = {item.code for item in result.facts.diagnostics}
    assert "django_view_unresolved" in codes
    assert "django_include_unresolved" in codes
    rendered = repr(result.facts)
    assert _SECRET not in rendered
    assert all(
        item.file_path is None
        or ("\\" not in item.file_path and not item.file_path.startswith("/"))
        for item in result.facts.diagnostics
    )
    assert all(item.framework_kind == "django_route" for item in endpoints)
