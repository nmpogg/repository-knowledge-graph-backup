"""TASK-RKG-007 dependency provenance and conservative external usage."""

from __future__ import annotations

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
        resolve_local_source("repo-seven", root, LocalSourcePolicy((root,))), config
    )
    context = AdapterContext("repo-seven", "snap-seven", "job-seven", config)
    adapter = PythonLanguageAdapter()
    parsed = adapter.parse(manifest, config)
    candidate = adapter.extract(context, parsed)
    result = adapter.resolve(context, parsed, candidate.facts)
    validate_fact_batch(result.facts)
    report = run_language_conformance(
        adapter, manifest, config, context, no_execution_marker=lambda: False
    )
    assert report.pass_rate == 1.0, report.cases
    return result, adapter.detect(manifest)


def test_declared_lock_and_import_provenance(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "pyproject.toml",
        "[project]\ndependencies = [\"PyYAML>=6; python_version >= '3.12'\", "
        '"requests>=2", "FastAPI>=0.100"]\n'
        '[project.optional-dependencies]\ndev = ["httpx>=0.25"]\n',
    )
    _write(
        tmp_path,
        "uv.lock",
        '[[package]]\nname = "PyYAML"\nversion = "6.0.2"\n'
        '[[package]]\nname = "transitive-only"\nversion = "1.2.3"\n',
    )
    _write(
        tmp_path,
        "app.py",
        "import yaml as parser\nfrom requests import get as fetch\n"
        'def work():\n    parser.safe_load("x")\n    fetch("x")\n',
    )
    result, detection = _run(tmp_path)
    deps = {
        item.name: item
        for item in result.facts.entities
        if item.type == EntityType.EXTERNAL_DEPENDENCY
    }
    assert set(deps) == {"pyyaml", "requests", "fastapi", "httpx", "transitive-only"}
    assert dict(deps["pyyaml"].attributes)["version"] == "6.0.2"
    assert dict(deps["pyyaml"].attributes)["version_provenance"] == "lock"
    assert dict(deps["pyyaml"].attributes)["markers"] == ("python_version >= '3.12'",)
    assert dict(deps["transitive-only"].attributes)["status"] == "lock_only"
    assert dict(deps["fastapi"].attributes)["status"] == "declared_no_observed_import"
    assert dict(deps["httpx"].attributes)["groups"] == ("dev",)
    used = {
        edge.target_id
        for edge in result.facts.edges
        if edge.type == EdgeType.DEPENDS_ON and edge.source_id != "repo-seven"
    }
    assert used == {deps["pyyaml"].id, deps["requests"].id}
    assert not any(
        edge.type == EdgeType.CALLS and edge.target_id in used
        for edge in result.facts.edges
    )
    detected = {item.technology: item for item in detection.technologies}
    assert detected["pyyaml"].version == "6.0.2"
    assert detected["fastapi"].version is None
    assert all(item.evidence for item in detection.technologies)


def test_local_shadow_and_unknown_distribution_are_not_guessed(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "pyproject.toml",
        '[project]\ndependencies = ["PyYAML==6.0", "mystery-client==1"]\n',
    )
    _write(tmp_path, "yaml.py", "def safe_load(value):\n    return value\n")
    _write(
        tmp_path,
        "app.py",
        "import yaml\ndef work():\n    yaml.safe_load('x')\n"
        "    import mystery_client\n",
    )
    result, _ = _run(tmp_path)
    assert not any(
        edge.type == EdgeType.DEPENDS_ON and edge.source_id != "repo-seven"
        for edge in result.facts.edges
    )


def test_requirements_include_cycle_and_dynamic_metadata(tmp_path: Path) -> None:
    _write(tmp_path, "pyproject.toml", '[project]\ndynamic = ["dependencies"]\n')
    _write(tmp_path, "requirements.txt", "-r nested.txt\n")
    _write(tmp_path, "nested.txt", "-r requirements.txt\nrequests==2.31\n")
    result, _ = _run(tmp_path)
    codes = {item.code for item in result.diagnostics}
    assert {"python_metadata_dynamic", "python_metadata_include_cycle"} <= codes
    assert any(item.name == "requests" for item in result.facts.entities)


def test_poetry_groups_and_group_include_cycle(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "pyproject.toml",
        '[tool.poetry.dependencies]\npython = "^3.12"\nrequests = "^2.31"\n'
        '[tool.poetry.group.dev.dependencies]\nhttpx = "^0.27"\n'
        '[dependency-groups]\na = [{include-group = "b"}]\n'
        'b = ["PyYAML==6.0", {include-group = "a"}]\n',
    )
    result, _ = _run(tmp_path)
    deps = {
        item.name: dict(item.attributes)
        for item in result.facts.entities
        if item.type == EntityType.EXTERNAL_DEPENDENCY
    }
    assert deps["requests"]["version"] == "^2.31"
    assert deps["httpx"]["groups"] == ("dev",)
    assert deps["pyyaml"]["groups"] == ("a", "b")
    assert "python_metadata_include_cycle" in {item.code for item in result.diagnostics}


def test_nested_callable_usage_belongs_to_inner_callable(tmp_path: Path) -> None:
    _write(tmp_path, "pyproject.toml", '[project]\ndependencies = ["requests==2"]\n')
    _write(
        tmp_path,
        "app.py",
        "from requests import get\n"
        "def outer():\n"
        "    def inner():\n"
        "        return get('https://example.invalid')\n"
        "    return inner()\n",
    )
    result, _ = _run(tmp_path)
    entities = {item.id: item for item in result.facts.entities}
    owners = {
        entities[item.source_id].qualified_name
        for item in result.facts.edges
        if item.type == EdgeType.DEPENDS_ON and item.source_id != "repo-seven"
    }
    assert owners == {"app.outer.inner"}
