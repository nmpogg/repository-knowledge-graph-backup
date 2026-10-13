"""End-to-end index job and CLI lifecycle checks."""

from __future__ import annotations

import json
import threading

from rkg.cli import main
from rkg.graph import entity_qualified_names
from rkg.ingestion import LocalSourcePolicy
from rkg.jobs import IndexCoordinator, IndexJobBusyError, recover_interrupted_jobs
from rkg.storage.connection import Storage


def test_reindex_failure_and_recovery(tmp_path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    module = source / "app.py"
    module.write_text("def old():\n    pass\n", encoding="utf-8")
    with Storage(tmp_path / "graph") as storage:
        repo = storage.create_repository(
            display_name="fixture", source_type="local", source_locator=str(source)
        )
        coordinator = IndexCoordinator(storage, LocalSourcePolicy((tmp_path,)))
        first = coordinator.run(repo.id)
        assert first.status == "succeeded"
        assert first.report["files"]["parsed"] == 1
        first_snapshot = storage.get_repository(repo.id).active_snapshot_id
        module.write_text("def new():\n    pass\n", encoding="utf-8")
        second = coordinator.run(repo.id)
        assert second.status == "succeeded"
        second_snapshot = storage.get_repository(repo.id).active_snapshot_id
        assert second_snapshot != first_snapshot
        assert storage.get_snapshot(repo.id, first_snapshot).id == first_snapshot
        assert any(
            "old" in name for name in entity_qualified_names(storage, first_snapshot)
        )
        assert not any(
            "old" in name for name in entity_qualified_names(storage, second_snapshot)
        )
        storage.update_repository(
            repo.id, expected_revision=1, scan_defaults={"max_files": 1}
        )
        (source / "extra.py").write_text("pass\n", encoding="utf-8")
        failed = coordinator.run(repo.id)
        assert failed.status == "failed"
        assert failed.error_code == "file_limit_exceeded"
        assert storage.get_repository(repo.id).active_snapshot_id == second_snapshot
        interrupted = storage.create_job(repo.id)
        assert recover_interrupted_jobs(storage) == (interrupted.id,)
        assert storage.get_job(interrupted.id).error_code == "index_interrupted"


def test_warnings_and_global_busy(tmp_path, monkeypatch) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "valid.py").write_text("def valid():\n    pass\n", encoding="utf-8")
    (source / "bad.py").write_text("def broken(:\n", encoding="utf-8")
    (source / "large.bin").write_bytes(b"x" * 100)
    with Storage(tmp_path / "graph") as storage:
        repo = storage.create_repository(
            display_name="fixture",
            source_type="local",
            source_locator=str(source),
            scan_defaults={"max_file_bytes": 50},
        )
        coordinator = IndexCoordinator(storage, LocalSourcePolicy((tmp_path,)))
        job = coordinator.run(repo.id)
        assert job.status == "succeeded_with_warnings"
        assert job.report["files"] == {
            "considered": 3,
            "parsed": 1,
            "skipped": 1,
            "errors": 1,
        }
        assert job.report["entity_total"] == sum(
            job.report["entities_by_type"].values()
        )
        assert job.report["edge_total"] == sum(job.report["edges_by_type"].values())
        assert any(
            item["code"] == "python_syntax_error" and item["relative_path"] == "bad.py"
            for item in job.report["diagnostics"]
        )
        assert job.report["skipped_files"] == [
            {"relative_path": "large.bin", "code": "file_too_large"}
        ]
        entered = threading.Event()
        release = threading.Event()
        import rkg.jobs.coordinator as module

        original = module.build_manifest

        def delayed(*args, **kwargs):
            entered.set()
            assert release.wait(5)
            return original(*args, **kwargs)

        monkeypatch.setattr(module, "build_manifest", delayed)
        worker = threading.Thread(target=lambda: coordinator.run(repo.id))
        worker.start()
        assert entered.wait(5)
        try:
            try:
                coordinator.run(repo.id)
            except IndexJobBusyError as exc:
                assert exc.code == "index_job_busy"
            else:
                raise AssertionError("second job should be rejected")
        finally:
            release.set()
            worker.join(timeout=10)
        assert not worker.is_alive()


def test_cli_repository_and_index(tmp_path, capsys) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "sample.py").write_text("def sample():\n    pass\n", encoding="utf-8")
    common = ["--db", str(tmp_path / "graph"), "--allow-root", str(tmp_path)]
    assert (
        main(
            common
            + ["repository", "create", "--name", "fixture", "--path", str(source)]
        )
        == 0
    )
    created = json.loads(capsys.readouterr().out)
    assert str(source) not in json.dumps(created)
    repo_id = created["repository_id"]
    assert main(common + ["index", "--repository", repo_id]) == 0
    indexed = json.loads(capsys.readouterr().out)
    assert indexed["status"] == "succeeded"
    assert (
        main(
            common
            + [
                "snapshot",
                "show",
                "--repository",
                repo_id,
                indexed["report"]["snapshot_id"],
            ]
        )
        == 0
    )
    shown = json.loads(capsys.readouterr().out)
    assert shown["is_active"] is True
    assert main(common + ["serve", "--host", "0.0.0.0"]) == 1
    assert json.loads(capsys.readouterr().out)["error_code"] == "serve_config_invalid"


def test_cli_validation_and_failed_index_match_api_error_codes(
    tmp_path, capsys
) -> None:
    """AC-055 — CLI shares validation/error_code contract with API; exit 1 on fail."""
    allowed = tmp_path / "allowed"
    outside = tmp_path / "outside"
    allowed.mkdir()
    outside.mkdir()
    source = allowed / "repo"
    source.mkdir()
    (source / "a.py").write_text("def a():\n    pass\n", encoding="utf-8")
    (source / "b.py").write_text("def b():\n    pass\n", encoding="utf-8")
    common = ["--db", str(tmp_path / "graph"), "--allow-root", str(allowed)]

    assert (
        main(
            common
            + [
                "repository",
                "create",
                "--name",
                "blocked",
                "--path",
                str(outside),
            ]
        )
        == 1
    )
    denied = json.loads(capsys.readouterr().out)
    assert denied["error_code"] == "source_outside_allowed_roots"
    assert str(outside) not in json.dumps(denied)
    assert str(tmp_path) not in json.dumps(denied)

    assert (
        main(
            common
            + ["repository", "create", "--name", "fixture", "--path", str(source)]
        )
        == 0
    )
    repo_id = json.loads(capsys.readouterr().out)["repository_id"]
    assert main(common + ["index", "--repository", repo_id]) == 0
    first = json.loads(capsys.readouterr().out)
    assert first["status"] == "succeeded"
    active = first["report"]["snapshot_id"]

    assert (
        main(
            common
            + [
                "repository",
                "update",
                repo_id,
                "--expected-revision",
                "1",
                "--max-files",
                "1",
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert main(common + ["index", "--repository", repo_id]) == 1
    failed = json.loads(capsys.readouterr().out)
    assert failed["status"] == "failed"
    assert failed["error_code"] == "file_limit_exceeded"
    assert str(source) not in json.dumps(failed)

    assert (
        main(
            common
            + [
                "snapshot",
                "show",
                "--repository",
                repo_id,
                active,
            ]
        )
        == 0
    )
    shown = json.loads(capsys.readouterr().out)
    assert shown["is_active"] is True


def test_fastapi_selection_and_binding(tmp_path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "pyproject.toml").write_text(
        '[project]\ndependencies = ["fastapi>=0.100"]\n', encoding="utf-8"
    )
    (source / "uv.lock").write_text(
        '[[package]]\nname = "fastapi"\nversion = "0.115.0"\n', encoding="utf-8"
    )
    (source / "one.py").write_text(
        "from fastapi import FastAPI\n"
        'app = FastAPI()\n@app.get("/one")\ndef one():\n    pass\n',
        encoding="utf-8",
    )
    (source / "two.py").write_text(
        "from fastapi import FastAPI\n"
        'app = FastAPI()\n@app.get("/two")\ndef two():\n    pass\n',
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
        snapshot = storage.get_snapshot(repo.id, selected.report["snapshot_id"])
        assert snapshot.adapter_versions["rkg.fastapi"] == "2.1.0"


def test_unknown_version_factory_publishes_routes_and_warning(tmp_path) -> None:
    from rkg.api.catalog import list_diagnostics, snapshot_capabilities
    from rkg.domain import EntityType
    from rkg.graph import search_entities

    source = tmp_path / "source"
    source.mkdir()
    (source / "routes.py").write_text(
        "from fastapi import APIRouter\nrouter = APIRouter(prefix='/items')\n"
        "@router.get('')\ndef list_items():\n    pass\n",
        encoding="utf-8",
    )
    (source / "main.py").write_text(
        "from fastapi import FastAPI\nimport routes\n"
        "def create_app():\n    app = FastAPI()\n"
        "    for module in (routes,):\n        app.include_router(module.router)\n"
        "    return app\napp = create_app()\n",
        encoding="utf-8",
    )
    with Storage(tmp_path / "graph") as storage:
        repo = storage.create_repository(
            display_name="fixture", source_type="local", source_locator=str(source)
        )
        job = IndexCoordinator(storage, LocalSourcePolicy((tmp_path,))).run(repo.id)
        assert job.status == "succeeded_with_warnings"
        assert job.report["selected_application"] == "main:app"
        snapshot_id = job.report["snapshot_id"]
        assert storage.get_repository(repo.id).active_snapshot_id == snapshot_id
        endpoints = search_entities(
            storage, repo.id, snapshot_id, entity_type=EntityType.ENDPOINT
        )
        assert endpoints.total == 1
        assert dict(endpoints.items[0].attributes)["path"] == "/items"
        support = next(
            t
            for t in snapshot_capabilities(storage, repo.id, snapshot_id)
            if t["technology"] == "fastapi"
        )
        assert support["support_state"] == "version_unverified"
        assert support["adapter_ids"] == ["rkg.fastapi"]
        diagnostics, _ = list_diagnostics(storage, snapshot_id, offset=0, limit=100)
        assert any(d["code"] == "adapter_version_unverified" for d in diagnostics)
