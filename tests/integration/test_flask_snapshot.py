"""A new index publishes a new snapshot and leaves the previous one intact."""

from __future__ import annotations

from rkg.graph import entity_qualified_names
from rkg.ingestion import LocalSourcePolicy
from rkg.jobs import IndexCoordinator
from rkg.storage.connection import Storage

_APP = (
    "from flask import Flask\n"
    "app = Flask(__name__)\n"
    "@app.route('/health', methods=['GET'])\n"
    "def health():\n"
    "    pass\n"
)


def test_reindex_keeps_the_published_snapshot(tmp_path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    module = source / "web.py"
    module.write_text(_APP, encoding="utf-8")
    with Storage(tmp_path / "graph") as storage:
        repo = storage.create_repository(
            display_name="fixture", source_type="local", source_locator=str(source)
        )
        coordinator = IndexCoordinator(storage, LocalSourcePolicy((tmp_path,)))
        first = coordinator.run(repo.id)
        assert first.status in {"succeeded", "succeeded_with_warnings"}
        assert first.report["entities_by_type"]["Endpoint"] == 1
        flask = next(
            item
            for item in first.report["technologies"]
            if item["technology"] == "flask"
        )
        assert flask["support_state"] == "detected_only"
        first_id = first.report["snapshot_id"]
        before = entity_qualified_names(storage, first_id)
        module.write_text(_APP + "def extra():\n    pass\n", encoding="utf-8")
        second = coordinator.run(repo.id)
        assert second.status in {"succeeded", "succeeded_with_warnings"}
        second_id = second.report["snapshot_id"]
        assert second_id != first_id
        assert entity_qualified_names(storage, first_id) == before
        assert storage.get_snapshot(repo.id, first_id).id == first_id
        assert any(
            "extra" in name for name in entity_qualified_names(storage, second_id)
        )
        assert any("health" in name for name in before)


def test_two_flask_entrypoints_do_not_publish_until_one_is_chosen(tmp_path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "one.py").write_text(
        "from flask import Flask\n"
        "app = Flask(__name__)\n"
        "@app.route('/one', methods=['GET'])\n"
        "def one():\n"
        "    pass\n",
        encoding="utf-8",
    )
    (source / "two.py").write_text(
        "from flask import Flask\n"
        "app = Flask(__name__)\n"
        "@app.route('/two', methods=['POST'])\n"
        "def two():\n"
        "    pass\n",
        encoding="utf-8",
    )
    with Storage(tmp_path / "graph") as storage:
        repo = storage.create_repository(
            display_name="fixture", source_type="local", source_locator=str(source)
        )
        coordinator = IndexCoordinator(storage, LocalSourcePolicy((tmp_path,)))
        pending = coordinator.run(repo.id)
        assert pending.error_code == "app_selection_required"
        assert pending.report["application_candidates"] == ["one:app", "two:app"]
        assert storage.get_repository(repo.id).active_snapshot_id is None
        storage.update_repository(
            repo.id, expected_revision=1, app_module="two", app_symbol="app"
        )
        selected = coordinator.run(repo.id)
        assert selected.status in {"succeeded", "succeeded_with_warnings"}
        assert selected.report["selected_application"] == "two:app"
        assert selected.report["entities_by_type"]["Endpoint"] == 1


def test_blueprint_prefix_is_published_and_dynamic_prefix_is_not(tmp_path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "routes.py").write_text(
        "from flask import Blueprint\n"
        "bp = Blueprint('bp', __name__, url_prefix='/v1')\n"
        "@bp.route('/items', methods=['POST'])\n"
        "def create_item():\n"
        "    pass\n",
        encoding="utf-8",
    )
    (source / "web.py").write_text(
        "from flask import Flask\n"
        "from routes import bp\n"
        "app = Flask(__name__)\n"
        "app.register_blueprint(bp)\n",
        encoding="utf-8",
    )
    with Storage(tmp_path / "graph") as storage:
        repo = storage.create_repository(
            display_name="fixture", source_type="local", source_locator=str(source)
        )
        coordinator = IndexCoordinator(storage, LocalSourcePolicy((tmp_path,)))
        indexed = coordinator.run(repo.id)
        assert indexed.status in {"succeeded", "succeeded_with_warnings"}
        flask = next(
            item
            for item in indexed.report["technologies"]
            if item["technology"] == "flask"
        )
        assert flask["support_state"] == "detected_only"
        assert indexed.report["entities_by_type"]["Endpoint"] == 1
        names = entity_qualified_names(storage, indexed.report["snapshot_id"])
        assert any("POST" in name and "/v1/items" in name for name in names)

    bare = tmp_path / "bare"
    bare.mkdir()
    (bare / "web.py").write_text(
        "from flask import Flask, Blueprint\n"
        "app = Flask(__name__)\n"
        "bp = Blueprint('bp', __name__, url_prefix='/v' + '1')\n"
        "app.register_blueprint(bp)\n"
        "@bp.route('/items', methods=['GET'])\n"
        "def create_item():\n"
        "    pass\n",
        encoding="utf-8",
    )
    with Storage(tmp_path / "graph-bare") as storage:
        repo = storage.create_repository(
            display_name="fixture", source_type="local", source_locator=str(bare)
        )
        coordinator = IndexCoordinator(storage, LocalSourcePolicy((tmp_path,)))
        indexed = coordinator.run(repo.id)
        assert indexed.status in {"succeeded", "succeeded_with_warnings"}
        assert indexed.report["entities_by_type"].get("Endpoint", 0) == 0
        assert "flask_blueprint_unresolved" in indexed.report["diagnostics_by_code"]
        flask = next(
            item
            for item in indexed.report["technologies"]
            if item["technology"] == "flask"
        )
        assert flask["support_state"] == "detected_only"
