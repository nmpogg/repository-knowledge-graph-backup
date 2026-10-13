"""Configuration keys and literal HTTP origins without sensitive values."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from rkg.adapters import (
    AdapterContext,
    PythonLanguageAdapter,
    run_language_conformance,
)
from rkg.domain import EdgeType, EntityType, SourceScanConfig, validate_fact_batch
from rkg.ingestion import LocalSourcePolicy, build_manifest, resolve_local_source


def _write(root: Path, name: str, content: str) -> None:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _run(root: Path):
    config = SourceScanConfig(30, 16384)
    manifest = build_manifest(
        resolve_local_source("repo-config", root, LocalSourcePolicy((root,))), config
    )
    context = AdapterContext("repo-config", "snap-config", "job-config", config)
    adapter = PythonLanguageAdapter()
    parsed = adapter.parse(manifest, config)
    candidate = adapter.extract(context, parsed)
    result = adapter.resolve(context, parsed, candidate.facts)
    validate_fact_batch(result.facts)
    report = run_language_conformance(
        adapter, manifest, config, context, no_execution_marker=lambda: False
    )
    assert report.pass_rate == 1.0, report.cases
    return result


def _text(result) -> str:
    payload = {
        "entities": [asdict(item) for item in result.facts.entities],
        "edges": [asdict(item) for item in result.facts.edges],
        "evidence": [asdict(item) for item in result.facts.evidence],
        "diagnostics": [asdict(item) for item in result.facts.diagnostics],
        "adapter_diagnostics": [asdict(item) for item in result.diagnostics],
    }
    return json.dumps(payload)


def _pairs(result, target_type: EntityType) -> set[tuple[str, str]]:
    by_id = {item.id: item for item in result.facts.entities}
    pairs = set()
    for edge in result.facts.edges:
        if edge.type != EdgeType.DEPENDS_ON or edge.source_id == "repo-config":
            continue
        target = by_id[edge.target_id]
        if target.type != target_type:
            continue
        pairs.add((by_id[edge.source_id].qualified_name, target.qualified_name))
    return pairs


def test_environment_and_settings_keys_omit_sentinels(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "app.py",
        "from abc import ABC\n"
        "from os import getenv\n"
        "import os\n"
        "from pydantic_settings import BaseSettings\n"
        "\n"
        "class Port(ABC):\n"
        "    pass\n"
        "\n"
        "class Store(Port):\n"
        "    def read(self):\n"
        '        os.environ["API_TOKEN"] = "sekret-write-9f3a"\n'
        '        return os.environ.get("API_TOKEN", "sekret-default-9f3a")\n'
        "\n"
        "class Settings(BaseSettings):\n"
        '    api_token: str = "sekret-value-9f3a"\n'
        "    timeout: int = 5\n"
        "\n"
        "    def reveal(self):\n"
        "        return self.api_token\n"
        "\n"
        "def load():\n"
        "    cfg = Settings()\n"
        '    return cfg.api_token, getenv("CACHE_URL", "sekret-default-9f3a")\n',
    )
    result = _run(tmp_path)
    config = {
        item.qualified_name: item
        for item in result.facts.entities
        if item.type == EntityType.CONFIGURATION
    }
    assert set(config) == {
        "environment:API_TOKEN",
        "environment:CACHE_URL",
        "settings:app.Settings:api_token",
        "settings:app.Settings:timeout",
    }
    assert dict(config["settings:app.Settings:timeout"].attributes)["owner"] == (
        "app.Settings"
    )
    assert _pairs(result, EntityType.CONFIGURATION) == {
        ("app.Store.read", "environment:API_TOKEN"),
        ("app.load", "environment:CACHE_URL"),
        ("app.load", "settings:app.Settings:api_token"),
        ("app.Settings.reveal", "settings:app.Settings:api_token"),
        ("app", "settings:app.Settings:api_token"),
        ("app", "settings:app.Settings:timeout"),
    }
    by_id = {item.id: item for item in result.facts.entities}
    hierarchy = {
        (
            edge.type,
            by_id[edge.source_id].qualified_name,
            by_id[edge.target_id].qualified_name,
        )
        for edge in result.facts.edges
        if edge.type in {EdgeType.INHERITS_FROM, EdgeType.IMPLEMENTS}
    }
    assert hierarchy == {
        (EdgeType.INHERITS_FROM, "app.Store", "app.Port"),
        (EdgeType.IMPLEMENTS, "app.Store", "app.Port"),
    }
    rendered = _text(result)
    assert "sekret-" not in rendered
    assert "9f3a" not in rendered


def test_http_literal_origins_drop_sensitive_url_parts(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "client.py",
        "import requests\n"
        "import httpx\n"
        "from requests import request as invoke\n"
        "\n"
        "def fetch(url, host):\n"
        "    requests.get(\n"
        '        "https://API.Example.com:443/v1/sekret-path-9f3a?q=sekret-query-9f3a"\n'
        "    )\n"
        "    requests.post(\n"
        '        "https://sekret-user-9f3a:sekret-pass-9f3a@api.example.com/other",\n'
        '        json={"token": "sekret-payload-9f3a"},\n'
        "    )\n"
        '    invoke("GET", "https://hooks.example:8443/health")\n'
        "    session = requests.Session()\n"
        '    session.delete("https://hooks.example:8443/drop")\n'
        "    with httpx.Client() as client:\n"
        '        client.get("https://hooks.example:8443/again")\n'
        "    requests.get(url)\n"
        '    httpx.get("https://" + host)\n'
        '    httpx.get(f"https://{host}/x")\n',
    )
    result = _run(tmp_path)
    services = {
        item.qualified_name: dict(item.attributes)
        for item in result.facts.entities
        if item.language_kind == "http_service"
    }
    assert services == {
        "https://api.example.com": {
            "kind": "http_service",
            "origin": "https://api.example.com",
        },
        "https://hooks.example:8443": {
            "kind": "http_service",
            "origin": "https://hooks.example:8443",
        },
    }
    assert _pairs(result, EntityType.EXTERNAL_DEPENDENCY) == {
        ("client.fetch", "https://api.example.com"),
        ("client.fetch", "https://hooks.example:8443"),
    }
    assert [
        item.code for item in result.facts.diagnostics
    ].count("python_http_unresolved") == 3
    rendered = _text(result)
    assert "sekret-" not in rendered
    assert "9f3a" not in rendered


def test_shadowed_or_dynamic_config_is_not_guessed(tmp_path: Path) -> None:
    _write(tmp_path, "os.py", "def getenv(name, default=None):\n    return name\n")
    _write(tmp_path, "requests.py", "def get(url):\n    return url\n")
    _write(
        tmp_path,
        "app.py",
        "import os\n"
        "import requests\n"
        "\n"
        "def read(os, name):\n"
        '    return os.getenv("SHOULD_SKIP"), requests.get("https://example.com")\n'
        "\n"
        "def dynamic(name):\n"
        "    return os.getenv(name)\n",
    )
    result = _run(tmp_path)
    assert not any(
        item.type == EntityType.CONFIGURATION or item.language_kind == "http_service"
        for item in result.facts.entities
    )
    assert "sekret" not in _text(result)
    assert "SHOULD_SKIP" not in _text(result)
