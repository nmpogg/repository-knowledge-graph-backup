"""Published configuration facts, context and logs omit secret sentinels."""

from __future__ import annotations

import io
import logging
from pathlib import Path

import pytest

from rkg.adapters import AdapterContext, PythonLanguageAdapter
from rkg.domain import EntityType, SourceScanConfig, context_json
from rkg.graph import build_context, publish_fact_batch, search_entities
from rkg.ingestion import LocalSourcePolicy, build_manifest, resolve_local_source
from rkg.storage import Storage
from tests.integration.graph_helpers import publish_meta

SENTINEL = "sekret-publish-9f3a"


@pytest.fixture
def store(tmp_path: Path) -> Storage:
    storage = Storage(tmp_path / "rkg.kuzu")
    yield storage
    storage.close()


def test_published_graph_context_and_log_omit_configuration_values(
    store: Storage, tmp_path: Path
) -> None:
    source = tmp_path / "repo"
    source.mkdir()
    (source / "app.py").write_text(
        "import os\n"
        "from pydantic_settings import BaseSettings\n"
        "import requests\n"
        "\n"
        "class Settings(BaseSettings):\n"
        f'    api_token: str = "{SENTINEL}"\n'
        "\n"
        "def load():\n"
        "    cfg = Settings()\n"
        '    requests.get("https://user:pass@api.example.com/secret?q=1", '
        f'json={{"password": "{SENTINEL}"}})\n'
        '    return cfg.api_token, os.getenv("API_TOKEN", '
        f'"{SENTINEL}")\n',
        encoding="utf-8",
    )
    repo = store.create_repository(
        repository_id="repo-config",
        display_name="config",
        source_type="local",
        source_locator="fixture/config-http",
    )
    config = SourceScanConfig(20, 16384)
    manifest = build_manifest(
        resolve_local_source(repo.id, source, LocalSourcePolicy((source,))), config
    )
    context = AdapterContext(repo.id, "snap-config", "job-config", config)
    adapter = PythonLanguageAdapter()
    parsed = adapter.parse(manifest, config)
    result = adapter.resolve(context, parsed, adapter.extract(context, parsed).facts)
    buffer = io.StringIO()
    captured = logging.StreamHandler(buffer)
    captured.setLevel(logging.DEBUG)
    log = logging.getLogger("rkg")
    previous_level = log.level
    log.setLevel(logging.DEBUG)
    log.addHandler(captured)
    try:
        publish_fact_batch(store, result.facts, publish_meta())
        found = search_entities(store, repo.id, "snap-config", q="API_TOKEN")
        root = next(
            item
            for item in result.facts.entities
            if item.qualified_name == "app.load"
        )
        package = build_context(
            store,
            repo.id,
            "snap-config",
            root.id,
            direction="outgoing",
            edge_types=("depends_on",),
            depth=1,
        )
        rendered = context_json(package)
    finally:
        log.removeHandler(captured)
        log.setLevel(previous_level)
    assert any(item.name == "API_TOKEN" for item in found.items)
    assert any(
        item.language_kind == "http_service" and item.name == "https://api.example.com"
        for item in package.nodes
    )
    assert any(item.type == EntityType.CONFIGURATION for item in package.nodes)
    blob = rendered + "\n" + buffer.getvalue()
    rows = store.conn.execute(
        "MATCH (e:Entity) RETURN e.name, e.qualified_name, e.attributes_json, "
        "e.language_kind"
    )
    while rows.has_next():
        cells = rows.get_next()
        blob += "\n" + "|".join("" if cell is None else str(cell) for cell in cells)
    messages = store.conn.execute("MATCH (d:Diagnostic) RETURN d.message, d.code")
    while messages.has_next():
        blob += "\n" + "|".join(str(cell) for cell in messages.get_next())
    assert SENTINEL not in blob
    assert "user:pass" not in blob
