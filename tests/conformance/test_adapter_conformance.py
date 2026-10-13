"""TEST-RKG-ADAPTER-CONFORMANCE: fixture-only extension proof."""

from __future__ import annotations

import ast
from pathlib import Path

from tests.conformance.fixture_adapter import (
    SyntheticFrameworkAdapter,
    SyntheticLanguageAdapter,
)

from rkg.adapters import AdapterContext, AdapterRegistry
from rkg.adapters.conformance import run_framework_conformance, run_language_conformance
from rkg.domain import SourceScanConfig
from rkg.ingestion import LocalSourcePolicy, build_manifest, resolve_local_source


def test_fixture_adapter_contract_and_registry(tmp_path: Path, monkeypatch) -> None:
    source = Path(__file__).parents[1] / "fixtures" / "adapter" / "sample.synthetic"
    (tmp_path / source.name).write_bytes(source.read_bytes())
    monkeypatch.chdir(tmp_path)
    marker = tmp_path / "source-executed.marker"
    config = SourceScanConfig(10, 4096, ("*.synthetic",))
    manifest = build_manifest(
        resolve_local_source("repo-fixture", tmp_path, LocalSourcePolicy((tmp_path,))),
        config,
    )
    context = AdapterContext("repo-fixture", "snapshot-fixture", "job-fixture", config)
    language = SyntheticLanguageAdapter()
    framework = SyntheticFrameworkAdapter()
    registry = AdapterRegistry()
    assert registry.register(framework).accepted
    assert registry.register(language).accepted

    language_detection = language.detect(manifest)
    parsed = language.parse(manifest, config)
    assert [(item.code, item.line) for item in parsed.diagnostics] == [
        ("fixture_syntax_ignored", 4)
    ]
    framework_detection = framework.detect(manifest, parsed)
    detections = language_detection.technologies + framework_detection.technologies
    assert registry.select_language("synthetic", detections) == (language,)
    assert registry.select_deep("synthetic", detections) == (framework,)
    assert not registry.select_deep("unknown", detections)

    language_report = run_language_conformance(
        language,
        manifest,
        config,
        context,
        no_execution_marker=marker.exists,
    )
    base = language.resolve(
        context, parsed, language.extract(context, parsed).facts
    ).facts
    framework_report = run_framework_conformance(
        framework,
        manifest,
        parsed,
        context,
        base,
        no_execution_marker=marker.exists,
    )
    for report in (language_report, framework_report):
        assert report.pass_rate == 1.0, [
            (case.name, case.detail) for case in report.cases if not case.passed
        ]
    assert not marker.exists()


def test_core_has_no_fixture_specific_dispatch() -> None:
    root = Path(__file__).parents[2] / "src" / "rkg"
    core_files = [path for path in root.rglob("*.py") if "adapters" not in path.parts]
    forbidden = {
        "rkg.conformance.fixture.language",
        "rkg.conformance.fixture.framework",
        "synthetic",
        "synthetic-web",
    }
    matches = []
    for path in core_files:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and node.value in forbidden
            ):
                matches.append((path.relative_to(root).as_posix(), node.lineno))
    assert matches == []
