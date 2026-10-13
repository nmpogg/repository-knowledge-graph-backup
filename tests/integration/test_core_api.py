"""HTTP transport checks for API-RKG-CORE-v1."""

from __future__ import annotations

import json
import threading
import time
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from rkg.api import create_app
from rkg.api.guard import mutation_allowed
from rkg.cli import main
from rkg.conversations import begin_turn, create_conversation
from rkg.graph import publish_fact_batch
from rkg.graph.access import mark_snapshot_unavailable
from rkg.ingestion import LocalSourcePolicy
from rkg.storage._util import fetch_one
from rkg.storage.connection import Storage
from rkg.storage.turns import recover_pending_turns
from tests.integration.graph_helpers import cycle_batch, publish_meta, seed_cycle_graph

TOKEN = "local-test-session"


@pytest.fixture
def api(tmp_path):
    storage = Storage(tmp_path / "graph")
    policy = LocalSourcePolicy((tmp_path,))
    app = create_app(storage, policy, session_token=TOKEN)
    client = TestClient(app, base_url="http://127.0.0.1")
    try:
        yield client, storage, tmp_path
    finally:
        for thread in app.state.workers:
            thread.join(timeout=10)
        storage.close()


def _auth() -> dict[str, str]:
    return {"X-RKG-Session": TOKEN}


def _wait_job(client: TestClient, job_id: str) -> dict:
    last: dict = {}
    for _ in range(80):
        response = client.get(f"/api/v1/index-jobs/{job_id}")
        assert response.status_code == 200
        last = response.json()
        if last["status"] in {"succeeded", "succeeded_with_warnings", "failed"}:
            assert "Retry-After" not in response.headers
            return last
        assert response.headers.get("Retry-After") == "1"
        time.sleep(0.05)
    raise AssertionError(last)


def test_request_log_uses_route_template_without_query_or_payload(api) -> None:
    client, _, _ = api
    with patch("rkg.api.app.log_event") as info:
        response = client.get(
            "/api/v1/entities/secret-entity-id?repository_id=secret-query-value"
        )
        assert response.status_code >= 400
        response = client.post(
            "/api/v1/repositories",
            headers=_auth(),
            json={"display_name": "secret-body-value", "path": "secret-path-value"},
        )
        assert response.status_code == 422

    entries = [str((call.args, call.kwargs)) for call in info.call_args_list]
    assert any("/api/v1/entities/{entity_id}" in entry for entry in entries)
    assert any("/api/v1/repositories" in entry for entry in entries)
    assert all("secret-" not in entry for entry in entries)


def test_cors_reflects_loopback_origin_only(api) -> None:
    client, _, _ = api
    preflight = client.options(
        "/api/v1/repositories",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "x-rkg-session,content-type",
        },
    )
    assert preflight.status_code == 200
    assert preflight.headers["access-control-allow-origin"] == "http://localhost:5173"
    denied = client.get(
        "/api/v1/repositories",
        headers={"Origin": "http://evil.example"},
    )
    assert denied.status_code == 200
    assert "access-control-allow-origin" not in denied.headers


def test_session_rejects_missing_token_bad_origin_and_remote_host() -> None:
    headers = {"host": "127.0.0.1", "x-rkg-session": TOKEN}
    assert mutation_allowed(headers, TOKEN)
    assert not mutation_allowed({"host": "127.0.0.1"}, TOKEN)
    assert not mutation_allowed({"host": "127.0.0.1", "x-rkg-session": "nope"}, TOKEN)
    assert not mutation_allowed({**headers, "origin": "http://evil.example"}, TOKEN)
    assert not mutation_allowed({**headers, "host": "10.1.1.1"}, TOKEN)


def test_repository_crud_redacts_paths_and_guards_lifecycle(api) -> None:
    client, storage, tmp_path = api
    source = tmp_path / "orders"
    source.mkdir()
    outside = tmp_path.parent / f"outside-{tmp_path.name}"
    outside.mkdir(exist_ok=True)
    created = client.post(
        "/api/v1/repositories",
        headers=_auth(),
        json={
            "display_name": "$(echo injected)",
            "source_type": "local",
            "path": str(source),
        },
    )
    assert created.status_code == 201
    body = created.json()
    assert body["active_snapshot_id"] is None
    assert body["revision"] == 1
    assert str(source) not in json.dumps(body)
    assert body["source_locator_redacted"].startswith("local:")
    rejected = client.post(
        "/api/v1/repositories",
        headers=_auth(),
        json={"display_name": "nope", "source_type": "local", "path": str(outside)},
    )
    assert rejected.status_code == 422
    assert rejected.json()["error"]["code"] == "source_outside_allowed_roots"
    assert str(outside) not in rejected.text
    duplicate = client.post(
        "/api/v1/repositories",
        headers=_auth(),
        json={"display_name": "again", "source_type": "local", "path": str(source)},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "repository_conflict"
    listed = client.get("/api/v1/repositories")
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    repo_id = body["repository_id"]
    conflict = client.patch(
        f"/api/v1/repositories/{repo_id}",
        headers=_auth(),
        json={"expected_revision": 9, "display_name": "renamed"},
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "repository_conflict"
    immutable = client.patch(
        f"/api/v1/repositories/{repo_id}",
        headers=_auth(),
        json={"expected_revision": 1, "path": str(source)},
    )
    assert immutable.status_code == 422
    assert immutable.json()["error"]["code"] == "repository_source_immutable"
    updated = client.patch(
        f"/api/v1/repositories/{repo_id}",
        headers=_auth(),
        json={"expected_revision": 1, "display_name": "Orders"},
    )
    assert updated.status_code == 200
    assert updated.json()["revision"] == 2
    assert updated.json()["source_locator_redacted"] == body["source_locator_redacted"]
    storage.create_job(repo_id, stage="queued")
    busy = client.delete(f"/api/v1/repositories/{repo_id}", headers=_auth())
    assert busy.status_code == 409
    assert busy.json()["error"]["code"] == "repository_busy"


def test_index_job_session_warnings_selection_and_single_writer(
    api, monkeypatch
) -> None:
    client, _storage, tmp_path = api
    source = tmp_path / "source"
    source.mkdir()
    (source / "valid.py").write_text("def valid():\n    pass\n", encoding="utf-8")
    (source / "bad.py").write_text("def broken(:\n", encoding="utf-8")
    created = client.post(
        "/api/v1/repositories",
        headers=_auth(),
        json={
            "display_name": "fixture",
            "source_type": "local",
            "path": str(source),
            "scan_defaults": {"max_file_bytes": 50},
        },
    )
    assert created.status_code == 201
    repo_id = created.json()["repository_id"]
    (source / "large.bin").write_bytes(b"x" * 100)
    denied = client.post(f"/api/v1/repositories/{repo_id}/index-jobs")
    assert denied.status_code == 401
    assert fetch_one(_storage.conn, "MATCH (j:Job) RETURN count(j)")[0] == 0
    hostile = client.post(
        f"/api/v1/repositories/{repo_id}/index-jobs",
        headers={**_auth(), "Origin": "https://evil.example"},
        json={},
    )
    assert hostile.status_code == 401
    accepted = client.post(
        f"/api/v1/repositories/{repo_id}/index-jobs",
        headers=_auth(),
        json={},
    )
    assert accepted.status_code == 202
    assert accepted.headers.get("Retry-After") == "1"
    job = _wait_job(client, accepted.json()["job_id"])
    assert job["status"] == "succeeded_with_warnings"
    assert "partial" not in json.dumps(job)
    assert job["report"]["files"]["errors"] == 1
    assert any(
        item["relative_path"] == "bad.py" for item in job["report"]["diagnostics"]
    )
    assert str(source) not in json.dumps(job)

    selected = tmp_path / "apps"
    selected.mkdir()
    (selected / "pyproject.toml").write_text(
        '[project]\ndependencies = ["fastapi>=0.100"]\n', encoding="utf-8"
    )
    (selected / "uv.lock").write_text(
        '[[package]]\nname = "fastapi"\nversion = "0.115.0"\n', encoding="utf-8"
    )
    (selected / "one.py").write_text(
        "from fastapi import FastAPI\napp = FastAPI()\n"
        '@app.get("/one")\ndef one():\n    pass\n',
        encoding="utf-8",
    )
    (selected / "two.py").write_text(
        "from fastapi import FastAPI\napp = FastAPI()\n"
        '@app.get("/two")\ndef two():\n    pass\n',
        encoding="utf-8",
    )
    registered = client.post(
        "/api/v1/repositories",
        headers=_auth(),
        json={"display_name": "apps", "source_type": "local", "path": str(selected)},
    )
    assert registered.status_code == 201
    app_repo = registered.json()["repository_id"]
    pending = _wait_job(
        client,
        client.post(
            f"/api/v1/repositories/{app_repo}/index-jobs",
            headers=_auth(),
            json={},
        ).json()["job_id"],
    )
    assert pending["error"]["code"] == "app_selection_required"
    assert pending["report"]["application_candidates"] == ["one:app", "two:app"]
    chosen = _wait_job(
        client,
        client.post(
            f"/api/v1/repositories/{app_repo}/index-jobs",
            headers=_auth(),
            json={"app_candidate_id": "two:app"},
        ).json()["job_id"],
    )
    assert chosen["status"] in {"succeeded", "succeeded_with_warnings"}
    assert chosen["report"]["selected_application"] == "two:app"
    again = _wait_job(
        client,
        client.post(
            f"/api/v1/repositories/{app_repo}/index-jobs",
            headers=_auth(),
            json={},
        ).json()["job_id"],
    )
    assert again["report"]["selected_application"] == "two:app"
    technologies = client.get(
        "/api/v1/technologies", params={"snapshot_id": chosen["snapshot_id"]}
    )
    assert technologies.status_code == 200
    assert any(item["technology"] == "fastapi" for item in technologies.json())

    import rkg.jobs.coordinator as module

    entered = threading.Event()
    release = threading.Event()
    original = module.build_manifest

    def delayed(*args, **kwargs):
        entered.set()
        assert release.wait(5)
        return original(*args, **kwargs)

    monkeypatch.setattr(module, "build_manifest", delayed)
    starter = threading.Thread(
        target=lambda: client.post(
            f"/api/v1/repositories/{repo_id}/index-jobs",
            headers=_auth(),
            json={},
        )
    )
    starter.start()
    try:
        assert entered.wait(5)
        starter.join(timeout=5)
        blocked = client.post(
            f"/api/v1/repositories/{repo_id}/index-jobs",
            headers=_auth(),
            json={},
        )
        assert blocked.status_code == 409
        assert blocked.json()["error"]["code"] == "index_job_busy"
    finally:
        release.set()
        starter.join(timeout=10)


def test_graph_reads_context_and_snapshot_guards(api) -> None:
    client, storage, _tmp_path = api
    repo_id, snapshot_id, batch = seed_cycle_graph(storage, locator="/allowed/cycle")
    other = storage.create_repository(
        display_name="Other", source_type="local", source_locator="/allowed/other"
    )
    second = "snap-cycle-2"
    publish_fact_batch(storage, cycle_batch(repo_id, second), publish_meta())
    hidden = client.get(f"/api/v1/repositories/{other.id}/snapshots/{snapshot_id}")
    assert hidden.status_code == 404
    assert hidden.json()["error"]["code"] == "not_found"
    assert "Cycle" not in hidden.text
    active = client.get(f"/api/v1/repositories/{repo_id}")
    assert active.json()["active_snapshot_id"] == second
    page = client.get(
        "/api/v1/entities",
        params={"snapshot_id": snapshot_id, "type": "Callable", "limit": 1},
    )
    assert page.status_code == 200
    body = page.json()
    assert body["total"] > 1
    assert len(body["items"]) == 1
    nxt = client.get(
        "/api/v1/entities",
        params={
            "snapshot_id": snapshot_id,
            "type": "Callable",
            "limit": 1,
            "offset": 1,
        },
    )
    assert {body["items"][0]["id"], nxt.json()["items"][0]["id"]}
    assert body["items"][0]["id"] != nxt.json()["items"][0]["id"]
    root = next(item.id for item in batch.entities if item.type.value == "Callable")
    graph = client.get(
        "/api/v1/subgraph",
        params={
            "snapshot_id": snapshot_id,
            "root_id": root,
            "direction": "outgoing",
            "depth": 4,
            "edge_types": "calls",
        },
    )
    assert graph.status_code == 200
    assert graph.json()["nodes"]
    assert all(edge["type"] == "calls" for edge in graph.json()["edges"])
    context_body = {
        "snapshot_id": snapshot_id,
        "root_id": root,
        "direction": "outgoing",
        "edge_types": ["calls"],
        "depth": 4,
        "max_nodes": 50,
        "max_edges": 100,
        "max_chars": 20000,
    }
    first = client.post("/api/v1/context", headers=_auth(), json=context_body)
    second_body = client.post("/api/v1/context", headers=_auth(), json=context_body)
    assert first.status_code == 200
    assert first.json() == second_body.json()
    rendered = first.text
    assert "def " not in rendered
    assert first.json()["schema_version"] == "v1"
    empty = client.get("/api/v1/entities", params={"repository_id": other.id})
    assert empty.status_code == 409
    assert empty.json()["error"]["code"] == "no_active_snapshot"
    mark_snapshot_unavailable(storage, snapshot_id)
    stale = client.get(f"/api/v1/entities/{root}", params={"snapshot_id": snapshot_id})
    assert stale.status_code == 410
    assert stale.json()["error"]["code"] == "snapshot_unavailable"
    budgets = client.post(
        "/api/v1/context",
        headers=_auth(),
        json={**context_body, "snapshot_id": second, "depth": 9},
    )
    assert budgets.status_code == 422
    assert budgets.json()["error"]["code"] == "invalid_budget"
    detail = client.get(f"/api/v1/repositories/{repo_id}/snapshots/{second}")
    assert detail.status_code == 200
    assert detail.json()["source_revision"].startswith("manifest:")
    assert detail.json()["manifest_hash"]
    assert detail.json()["scan_config_digest"]
    assert detail.json()["analyzer_version"]
    assert detail.json()["schema_version"]
    assert isinstance(detail.json()["adapter_versions"], dict)
    assert detail.json()["is_active"] is True
    assert detail.json()["metrics"]["entity_count"] >= 1
    diagnostics = client.get("/api/v1/diagnostics", params={"snapshot_id": second})
    assert diagnostics.status_code == 200
    dependencies = client.get("/api/v1/dependencies", params={"snapshot_id": second})
    assert dependencies.status_code == 200
    create_conversation(
        storage, repository_id=repo_id, snapshot_id=snapshot_id, title="pinned"
    )
    guarded = client.delete(
        f"/api/v1/repositories/{repo_id}/snapshots/{snapshot_id}",
        headers=_auth(),
    )
    assert guarded.status_code == 409
    assert guarded.json()["error"]["code"] == "snapshot_in_use"
    active_delete = client.delete(
        f"/api/v1/repositories/{repo_id}/snapshots/{second}",
        headers=_auth(),
    )
    assert active_delete.status_code == 409
    assert active_delete.json()["error"]["code"] == "snapshot_active"
    kept = client.get(f"/api/v1/repositories/{repo_id}")
    jobs_before = fetch_one(storage.conn, "MATCH (j:Job) RETURN count(j)", None)[0]
    activated = client.post(
        f"/api/v1/repositories/{repo_id}/snapshots/{snapshot_id}/activate",
        headers=_auth(),
    )
    # The unavailable snapshot can still be the pointer; activation only changes it.
    assert activated.status_code == 200
    assert activated.json()["active_snapshot_id"] == snapshot_id
    jobs_after = fetch_one(storage.conn, "MATCH (j:Job) RETURN count(j)")[0]
    assert jobs_after == jobs_before
    other_active = client.get(f"/api/v1/repositories/{other.id}")
    assert other_active.json()["active_snapshot_id"] is None
    assert kept.status_code == 200


def test_conversation_delete_is_busy_while_a_turn_is_pending(api) -> None:
    client, storage, _tmp_path = api
    repo_id, snapshot_id, _batch = seed_cycle_graph(storage)
    conversation = create_conversation(
        storage, repository_id=repo_id, snapshot_id=snapshot_id, title="busy"
    )
    begin_turn(
        storage,
        conversation.id,
        question="pending",
        client_request_id="busy-1",
        expected_revision=1,
    )
    denied = client.delete(f"/api/v1/conversations/{conversation.id}")
    assert denied.status_code == 401
    blocked = client.delete(f"/api/v1/conversations/{conversation.id}", headers=_auth())
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "conversation_busy"
    recover_pending_turns(storage.conn)
    removed = client.delete(f"/api/v1/conversations/{conversation.id}", headers=_auth())
    assert removed.status_code == 204
    missing = client.delete(f"/api/v1/conversations/{conversation.id}", headers=_auth())
    assert missing.status_code == 404


def test_queued_job_advertises_retry_after(api) -> None:
    client, storage, _tmp_path = api
    repo = storage.create_repository(
        display_name="queued", source_type="local", source_locator="/allowed/queued"
    )
    job = storage.create_job(repo.id, stage="queued")
    response = client.get(f"/api/v1/index-jobs/{job.id}")
    assert response.status_code == 200
    assert response.headers.get("Retry-After") == "1"
    assert response.json()["stage"] == "queued"
    storage.update_job(job.id, stage="succeeded", status="succeeded")
    done = client.get(f"/api/v1/index-jobs/{job.id}")
    assert done.status_code == 200
    assert "Retry-After" not in done.headers


def test_unreferenced_snapshot_and_repository_delete(api) -> None:
    client, storage, _tmp_path = api
    repo_id, snapshot_id, _batch = seed_cycle_graph(storage, locator="/allowed/cycle")
    second = "snap-delete-keep"
    publish_fact_batch(storage, cycle_batch(repo_id, second), publish_meta())
    other = storage.create_repository(
        display_name="Kept", source_type="local", source_locator="/allowed/kept"
    )
    foreign = client.get(
        "/api/v1/entities/not-in-snapshot", params={"snapshot_id": second}
    )
    assert foreign.status_code == 404
    assert foreign.json()["error"]["code"] == "not_found"
    conversation = create_conversation(
        storage, repository_id=repo_id, snapshot_id=snapshot_id, title="holds"
    )
    in_use = client.delete(f"/api/v1/repositories/{repo_id}", headers=_auth())
    assert in_use.status_code == 409
    assert in_use.json()["error"]["code"] == "repository_in_use"
    assert (
        client.delete(
            f"/api/v1/conversations/{conversation.id}", headers=_auth()
        ).status_code
        == 204
    )
    removed = client.delete(
        f"/api/v1/repositories/{repo_id}/snapshots/{snapshot_id}",
        headers=_auth(),
    )
    assert removed.status_code == 204
    listed = client.get(f"/api/v1/repositories/{repo_id}/snapshots")
    assert [item["snapshot_id"] for item in listed.json()["items"]] == [second]
    gone = client.get(f"/api/v1/repositories/{repo_id}/snapshots/{snapshot_id}")
    assert gone.status_code == 404
    kept = client.get(f"/api/v1/repositories/{other.id}/snapshots")
    assert kept.status_code == 200
    deleted = client.delete(f"/api/v1/repositories/{repo_id}", headers=_auth())
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/repositories/{repo_id}").status_code == 404
    assert client.get(f"/api/v1/repositories/{other.id}").status_code == 200
    alias = client.post("/api/v1/index-jobs", headers=_auth(), json={})
    assert alias.status_code == 404
    assert client.get("/api/v1/snapshots").status_code == 404


def test_repository_list_pages_without_overlap(api) -> None:
    client, _storage, tmp_path = api
    for name in ("older", "newer"):
        source = tmp_path / name
        source.mkdir()
        created = client.post(
            "/api/v1/repositories",
            headers=_auth(),
            json={"display_name": name, "source_type": "local", "path": str(source)},
        )
        assert created.status_code == 201
    first = client.get("/api/v1/repositories", params={"limit": 1, "offset": 0})
    second = client.get("/api/v1/repositories", params={"limit": 1, "offset": 1})
    assert first.status_code == 200
    assert first.json()["total"] == 2
    assert len(first.json()["items"]) == 1
    assert (
        first.json()["items"][0]["repository_id"]
        != second.json()["items"][0]["repository_id"]
    )
    assert "created_at" in first.json()["items"][0]
    assert "updated_at" in first.json()["items"][0]


def test_serve_binds_fastapi_on_loopback(tmp_path, monkeypatch, capsys) -> None:
    captured: dict = {}

    def fake_run(app, **kwargs):
        captured["kwargs"] = kwargs
        client = TestClient(app, base_url="http://127.0.0.1")
        captured["status"] = client.get("/api/v1/repositories").status_code

    monkeypatch.setattr("rkg.cli.uvicorn.run", fake_run)
    assert main(["--db", str(tmp_path / "graph"), "serve", "--host", "127.0.0.1"]) == 0
    assert captured["kwargs"]["host"] == "127.0.0.1"
    assert captured["kwargs"].get("access_log", True) is True
    assert captured["kwargs"]["log_level"] == "info"
    assert captured["status"] == 200
    assert main(["--db", str(tmp_path / "graph"), "serve", "--workers", "2"]) == 1
    assert json.loads(capsys.readouterr().out)["error_code"] == "serve_config_invalid"


def test_index_job_busy_blocks_other_repository(api, monkeypatch) -> None:
    """AC-034 — single writer is global across repositories."""
    client, _storage, tmp_path = api
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    (first / "a.py").write_text("def a():\n    pass\n", encoding="utf-8")
    (second / "b.py").write_text("def b():\n    pass\n", encoding="utf-8")
    repo_a = client.post(
        "/api/v1/repositories",
        headers=_auth(),
        json={"display_name": "first", "source_type": "local", "path": str(first)},
    ).json()["repository_id"]
    repo_b = client.post(
        "/api/v1/repositories",
        headers=_auth(),
        json={"display_name": "second", "source_type": "local", "path": str(second)},
    ).json()["repository_id"]

    import rkg.jobs.coordinator as module

    entered = threading.Event()
    release = threading.Event()
    original = module.build_manifest

    def delayed(*args, **kwargs):
        entered.set()
        assert release.wait(5)
        return original(*args, **kwargs)

    monkeypatch.setattr(module, "build_manifest", delayed)
    starter = threading.Thread(
        target=lambda: client.post(
            f"/api/v1/repositories/{repo_a}/index-jobs",
            headers=_auth(),
            json={},
        )
    )
    starter.start()
    try:
        assert entered.wait(5)
        starter.join(timeout=5)
        blocked = client.post(
            f"/api/v1/repositories/{repo_b}/index-jobs",
            headers=_auth(),
            json={},
        )
        assert blocked.status_code == 409
        assert blocked.json()["error"]["code"] == "index_job_busy"
        assert str(first) not in blocked.text
        assert str(second) not in blocked.text
    finally:
        release.set()
        starter.join(timeout=10)


def test_link_escape_and_file_limit_fail_without_changing_active(api) -> None:
    """AC-049 / AC-051 — boundary failures keep prior active snapshot."""
    client, storage, tmp_path = api
    source = tmp_path / "bounded"
    source.mkdir()
    (source / "ok.py").write_text("def ok():\n    pass\n", encoding="utf-8")
    created = client.post(
        "/api/v1/repositories",
        headers=_auth(),
        json={"display_name": "bounded", "source_type": "local", "path": str(source)},
    )
    assert created.status_code == 201
    repo_id = created.json()["repository_id"]
    first = _wait_job(
        client,
        client.post(
            f"/api/v1/repositories/{repo_id}/index-jobs",
            headers=_auth(),
            json={},
        ).json()["job_id"],
    )
    assert first["status"] in {"succeeded", "succeeded_with_warnings"}
    active = first["snapshot_id"] or storage.get_repository(repo_id).active_snapshot_id
    assert active

    (source / "extra.py").write_text("def extra():\n    pass\n", encoding="utf-8")
    limited = _wait_job(
        client,
        client.post(
            f"/api/v1/repositories/{repo_id}/index-jobs",
            headers=_auth(),
            json={"scan_defaults": {"max_files": 1}},
        ).json()["job_id"],
    )
    assert limited["status"] == "failed"
    assert limited["error"]["code"] == "file_limit_exceeded"
    assert storage.get_repository(repo_id).active_snapshot_id == active
    assert str(source) not in json.dumps(limited)

    target = tmp_path / "outside-secret.py"
    target.write_text("leak-sentinel = 1\n", encoding="utf-8")
    link = source / "escape.py"
    try:
        import os

        os.symlink(target, link)
    except (OSError, NotImplementedError):
        pytest.skip("creating symlinks is not permitted on this host")
    escaped = _wait_job(
        client,
        client.post(
            f"/api/v1/repositories/{repo_id}/index-jobs",
            headers=_auth(),
            json={},
        ).json()["job_id"],
    )
    assert escaped["status"] == "failed"
    assert escaped["error"]["code"] == "source_link_escape"
    assert storage.get_repository(repo_id).active_snapshot_id == active
    payload = json.dumps(escaped)
    assert str(tmp_path) not in payload
    assert "leak-sentinel" not in payload


def test_seeded_graph_search_subgraph_context_assert_contract(api) -> None:
    """FR-003/004 graph asserts via publish_fact_batch seed (no adapter extract)."""
    client, storage, _tmp_path = api
    repo_id, snapshot_id, batch = seed_cycle_graph(storage)
    foreign = storage.create_repository(
        display_name="Foreign",
        source_type="local",
        source_locator="/allowed/foreign-graph",
    )
    root = next(item for item in batch.entities if item.qualified_name == "app.cycle.a")
    callee = next(
        item for item in batch.entities if item.qualified_name == "app.cycle.b"
    )
    call_edge = next(
        edge
        for edge in batch.edges
        if edge.source_id == root.id and edge.target_id == callee.id
    )

    search = client.get(
        "/api/v1/entities",
        params={"snapshot_id": snapshot_id, "q": "app.cycle.a", "type": "Callable"},
    )
    assert search.status_code == 200
    assert search.json()["items"][0]["id"] == root.id
    assert search.json()["items"][0]["snapshot_id"] == snapshot_id
    assert search.json()["items"][0]["repository_id"] == repo_id

    mismatch = client.get(
        "/api/v1/entities",
        params={"snapshot_id": snapshot_id, "repository_id": foreign.id},
    )
    assert mismatch.status_code == 404
    assert mismatch.json()["error"]["code"] == "not_found"
    assert "Cycle" not in mismatch.text

    graph = client.get(
        "/api/v1/subgraph",
        params={
            "snapshot_id": snapshot_id,
            "root_id": root.id,
            "direction": "outgoing",
            "edge_types": "calls",
            "depth": 1,
        },
    )
    assert graph.status_code == 200
    body = graph.json()
    assert body["snapshot_id"] == snapshot_id
    assert {node["id"] for node in body["nodes"]} >= {root.id, callee.id}
    assert any(edge["id"] == call_edge.id for edge in body["edges"])
    assert all(edge["type"] == "calls" for edge in body["edges"])

    tiny = client.get(
        "/api/v1/subgraph",
        params={
            "snapshot_id": snapshot_id,
            "root_id": root.id,
            "direction": "outgoing",
            "edge_types": "calls",
            "depth": 6,
            "max_nodes": 1,
        },
    )
    assert tiny.status_code == 200
    assert tiny.json()["truncated"] is True
    assert "max_nodes" in tiny.json()["truncation_reasons"]

    context = client.post(
        "/api/v1/context",
        headers=_auth(),
        json={
            "snapshot_id": snapshot_id,
            "root_id": root.id,
            "direction": "outgoing",
            "edge_types": ["calls"],
            "depth": 4,
            "max_nodes": 50,
            "max_edges": 100,
            "max_chars": 2000,
        },
    )
    assert context.status_code == 200
    package = context.json()
    assert package["schema_version"] == "v1"
    assert package["snapshot_id"] == snapshot_id
    assert package["root_id"] == root.id
    assert package["truncated"] is True
    assert package["truncation_reasons"]
    assert "def " not in context.text
    assert "secret" not in context.text.lower()
    foreign_ctx = client.post(
        "/api/v1/context",
        headers=_auth(),
        json={
            "snapshot_id": snapshot_id,
            "repository_id": foreign.id,
            "root_id": root.id,
            "direction": "outgoing",
            "edge_types": ["calls"],
            "depth": 1,
            "max_nodes": 10,
            "max_edges": 10,
            "max_chars": 2000,
        },
    )
    assert foreign_ctx.status_code == 404
