"""Static Flask routes that are not part of a reviewed deep-support profile."""

from __future__ import annotations

from pathlib import Path

from rkg.adapters import (
    AdapterContext,
    AdapterRegistry,
    FlaskFrameworkAdapter,
    PythonLanguageAdapter,
    SupportState,
    run_framework_conformance,
)
from rkg.detection import (
    DetectionState,
    FlaskAppDetector,
    PythonImportDetector,
    select_adapters,
)
from rkg.domain import EdgeType, EntityType, SourceScanConfig, validate_fact_batch
from rkg.ingestion import LocalSourcePolicy, build_manifest, resolve_local_source


def _write(root: Path, path: str, content: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def _run(root: Path, *, application: str | None = None):
    config = SourceScanConfig(40, 32768)
    manifest = build_manifest(
        resolve_local_source("repo-flask", root, LocalSourcePolicy((root,))), config
    )
    context = AdapterContext("repo-flask", "snap-flask", "job-flask", config)
    language = PythonLanguageAdapter()
    parsed = language.parse(manifest, config)
    base = language.extract(context, parsed)
    base = language.resolve(context, parsed, base.facts)
    adapter = FlaskFrameworkAdapter(application)
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
    return result


def _endpoints(result):
    return {
        item.id: item
        for item in result.facts.entities
        if item.type == EntityType.ENDPOINT
    }


def _names(result, edge_type: EdgeType):
    entities = {item.id: item for item in result.facts.entities}
    return {
        (
            entities[edge.source_id].qualified_name,
            entities[edge.target_id].qualified_name,
        )
        for edge in result.facts.edges
        if edge.type == edge_type and edge.source_id in entities
    }


def test_blueprint_route_add_url_rule_and_plain_callable(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "service.py",
        "def helper():\n"
        "    pass\n"
        "class RoomBook:\n"
        "    def create(self):\n"
        "        helper()\n"
        "def idle():\n"
        "    helper()\n",
    )
    _write(
        tmp_path,
        "routes_file.py",
        "from flask import Blueprint\n"
        "from service import RoomBook\n"
        "def require_token():\n"
        "    pass\n"
        "book = Blueprint('book', __name__, url_prefix='/v1')\n"
        "rooms = RoomBook()\n"
        "@book.route('/items', methods=['POST'])\n"
        "@require_token\n"
        "def create_item():\n"
        "    rooms.create()\n"
        "def not_routed():\n"
        "    rooms.create()\n",
    )
    _write(
        tmp_path,
        "web.py",
        "from flask import Flask\n"
        "from routes_file import book\n"
        "app = Flask(__name__)\n"
        "app.register_blueprint(book)\n"
        "@app.route('/health', methods=['GET'])\n"
        "def health():\n"
        "    pass\n"
        "def ping():\n"
        "    pass\n"
        "app.add_url_rule('/ping', view_func=ping)\n"
        "rule = '/moving'\n"
        "methods = ['POST']\n"
        "@app.route(rule, methods=methods)\n"
        "def moving():\n"
        "    pass\n",
    )
    result = _run(tmp_path)
    endpoints = _endpoints(result)
    found = sorted(
        (dict(item.attributes)["method"], dict(item.attributes)["path"])
        for item in endpoints.values()
    )
    assert found == [("GET", "/health"), ("GET", "/ping"), ("POST", "/v1/items")]
    entities = {item.id: item for item in result.facts.entities}
    handled = {
        entities[edge.target_id].qualified_name
        for edge in result.facts.edges
        if edge.type == EdgeType.HANDLED_BY
    }
    assert handled == {
        "routes_file.create_item",
        "web.health",
        "web.ping",
    }
    assert "routes_file.not_routed" not in handled
    assert "service.idle" not in handled
    assert any(
        item.type == EntityType.CALLABLE
        and item.qualified_name == "routes_file.not_routed"
        for item in result.facts.entities
    )
    assert any(
        item.type == EntityType.CALLABLE and item.qualified_name == "web.moving"
        for item in result.facts.entities
    )
    assert not any("moving" in item.qualified_name for item in endpoints.values())
    depends = _names(result, EdgeType.DEPENDS_ON)
    endpoint = next(
        item
        for item in endpoints.values()
        if dict(item.attributes)["path"] == "/v1/items"
    )
    assert (endpoint.qualified_name, "routes_file.require_token") in depends
    calls = _names(result, EdgeType.CALLS)
    assert ("routes_file.create_item", "service.RoomBook.create") in calls
    assert ("service.RoomBook.create", "service.helper") in calls
    assert ("routes_file.not_routed", "service.RoomBook.create") in calls
    assert ("service.idle", "service.helper") in calls
    dynamic = [
        item
        for item in result.facts.diagnostics
        if item.code == "flask_route_dynamic"
    ]
    assert dynamic
    assert all(
        item.file_path == "web.py"
        and item.line
        and "\\" not in (item.file_path or "")
        and not (item.file_path or "").startswith("/")
        for item in dynamic
    )
    assert all("moving" not in item.message for item in dynamic)


def test_one_entrypoint_is_selected_and_many_require_a_choice(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "web.py",
        "from flask import Flask\n"
        "app = Flask(__name__)\n"
        "@app.route('/only', methods=['GET'])\n"
        "def only():\n"
        "    pass\n",
    )
    config = SourceScanConfig(20, 16384)
    manifest = build_manifest(
        resolve_local_source("repo-flask", tmp_path, LocalSourcePolicy((tmp_path,))),
        config,
    )
    language = PythonLanguageAdapter()
    parsed = language.parse(manifest, config)
    registry = AdapterRegistry()
    adapter = FlaskFrameworkAdapter()
    assert registry.register(language).accepted
    assert registry.register(adapter).accepted
    selection = select_adapters(
        manifest,
        parsed,
        language,
        registry,
        (PythonImportDetector(), FlaskAppDetector()),
    )
    assert selection.status == "ready"
    assert selection.selected_application is not None
    assert selection.selected_application.reference == "web:app"
    assert selection.deep_adapters == (adapter,)
    flask = next(item for item in selection.technologies if item.technology == "flask")
    assert flask.state == DetectionState.DETECTED_ONLY
    assert flask.adapter_ids == ()
    result = _run(tmp_path, application=selection.selected_application.reference)
    assert {dict(item.attributes)["path"] for item in _endpoints(result).values()} == {
        "/only"
    }

    _write(
        tmp_path,
        "other.py",
        "from flask import Flask\n"
        "app = Flask(__name__)\n"
        "@app.route('/other', methods=['PUT'])\n"
        "def other():\n"
        "    pass\n",
    )
    manifest = build_manifest(
        resolve_local_source("repo-flask", tmp_path, LocalSourcePolicy((tmp_path,))),
        config,
    )
    parsed = language.parse(manifest, config)
    many = select_adapters(
        manifest,
        parsed,
        language,
        registry,
        (PythonImportDetector(), FlaskAppDetector()),
    )
    assert many.status == "app_selection_required"
    assert many.error_code == "app_selection_required"
    assert [item.reference for item in many.application_candidates] == [
        "other:app",
        "web:app",
    ]
    ambiguous = _run(tmp_path)
    assert _endpoints(ambiguous) == {}
    assert "flask_app_ambiguous" in {item.code for item in ambiguous.diagnostics}
    chosen = _run(tmp_path, application="web:app")
    assert {dict(item.attributes)["path"] for item in _endpoints(chosen).values()} == {
        "/only"
    }


def test_local_flask_module_does_not_become_an_endpoint(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "flask.py",
        "class Flask:\n    def __init__(self, name):\n        pass\n",
    )
    _write(
        tmp_path,
        "web.py",
        "from flask import Flask\n"
        "app = Flask(__name__)\n"
        "@app.route('/nope')\n"
        "def nope():\n"
        "    pass\n",
    )
    assert _endpoints(_run(tmp_path)) == {}
