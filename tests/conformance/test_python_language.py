"""Golden and negative contract cases for TASK-RKG-005."""

from __future__ import annotations

import json
from pathlib import Path

from rkg.adapters import AdapterContext, AdapterRegistry, PythonLanguageAdapter
from rkg.adapters.conformance import run_language_conformance
from rkg.domain import EdgeType, EntityType, SourceScanConfig, validate_fact_batch
from rkg.ingestion import LocalSourcePolicy, build_manifest, resolve_local_source


def _manifest(root: Path):
    config = SourceScanConfig(20, 16384, ("*.py", "**/*.py"))
    source = resolve_local_source("repo-golden", root, LocalSourcePolicy((root,)))
    return build_manifest(source, config), config


def _run(root: Path):
    manifest, config = _manifest(root)
    adapter = PythonLanguageAdapter()
    context = AdapterContext("repo-golden", "snap-golden", "job-golden", config)
    parsed = adapter.parse(manifest, config)
    extracted = adapter.extract(context, parsed)
    resolved = adapter.resolve(context, parsed, extracted.facts)
    validate_fact_batch(resolved.facts)
    return adapter, manifest, config, context, parsed, resolved


def test_source_structure_matches_golden(tmp_path: Path) -> None:
    fixture_root = Path(__file__).parents[1] / "fixtures" / "python_structure"
    source = fixture_root / "pkg" / "orders.py"
    target = tmp_path / "pkg" / "orders.py"
    target.parent.mkdir()
    target.write_bytes(source.read_bytes())
    golden = json.loads(
        (
            Path(__file__).parents[1] / "fixtures" / "domain" / "source_structure.json"
        ).read_text(encoding="utf-8")
    )
    _, _, _, _, parsed, resolved = _run(tmp_path)
    facts = resolved.facts
    assert parsed.symbol_index == tuple(
        sorted(
            parsed.symbol_index,
            key=lambda item: (item.qualified_name, item.relative_path),
        )
    )
    assert [item.qualified_name for item in parsed.symbol_index] == [
        "pkg.orders.OrderService",
        "pkg.orders.OrderService.create",
        "pkg.orders.OrderService.create.validate",
    ]
    assert len(facts.entities) == len(golden["nodes"])
    by_key = {}
    for item in golden["nodes"]:
        matches = [
            entity
            for entity in facts.entities
            if entity.type == EntityType(item["type"])
            and entity.name == item["name"]
            and entity.qualified_name == item["qualified_name"]
            and entity.file_path == golden["file_path"]
        ]
        assert len(matches) == 1, item["key"]
        by_key[item["key"]] = matches[0].id
    actual_edges = {
        (edge.source_id, edge.target_id)
        for edge in facts.edges
        if edge.type == EdgeType.CONTAINS
    }
    expected_edges = {
        (by_key[parent], by_key[child]) for parent, child in golden["contains"]
    }
    assert actual_edges == expected_edges
    assert all(edge.evidence_ids for edge in facts.edges)
    assert not resolved.diagnostics


def test_syntax_error_is_isolated_and_path_safe(tmp_path: Path) -> None:
    (tmp_path / "good.py").write_text(
        "def healthy():\n    return 1\n", encoding="utf-8"
    )
    (tmp_path / "bad.py").write_text("def broken(:\n    pass\n", encoding="utf-8")
    _, _, _, _, parsed, resolved = _run(tmp_path)
    assert [unit.relative_path for unit in parsed.units] == ["good.py"]
    assert [
        (item.code, item.relative_path, item.line) for item in parsed.diagnostics
    ] == [("python_syntax_error", "bad.py", 1)]
    assert all(entity.file_path == "good.py" for entity in resolved.facts.entities)
    assert [
        (item.code, item.file_path, item.line) for item in resolved.facts.diagnostics
    ] == [("python_syntax_error", "bad.py", 1)]
    assert str(tmp_path) not in repr(resolved)


def test_no_guessed_relationships_and_duplicate_binding(tmp_path: Path) -> None:
    (tmp_path / "ambiguous.py").write_text(
        "from unknown import *\n"
        "class Service:\n"
        "    def run(self):\n"
        "        self.dynamic()\n"
        "def same():\n    pass\n"
        "def same():\n    pass\n",
        encoding="utf-8",
    )
    _, _, _, _, parsed, resolved = _run(tmp_path)
    assert [item.code for item in parsed.diagnostics] == ["python_duplicate_definition"]
    assert (
        len(
            [
                item
                for item in resolved.facts.entities
                if item.qualified_name == "ambiguous.same"
            ]
        )
        == 1
    )
    assert {item.type for item in resolved.facts.edges} == {EdgeType.CONTAINS}


def test_control_blocks_keep_lexical_owner_and_duplicate_subtree_is_skipped(
    tmp_path: Path,
) -> None:
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "__init__.py").write_text(
        "if True:\n"
        "    class Service:\n"
        "        def execute(self):\n"
        "            return 1\n"
        "class Service:\n"
        "    def hidden(self):\n"
        "        return 2\n",
        encoding="utf-8",
    )
    _, _, _, _, parsed, resolved = _run(tmp_path)
    names = {item.qualified_name for item in resolved.facts.entities}
    assert "pkg.Service.execute" in names
    assert "pkg.Service.hidden" not in names
    assert [item.code for item in parsed.diagnostics] == ["python_duplicate_definition"]


def test_python_adapter_passes_shared_conformance(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "safe.py").write_text(
        'open("source-executed.marker", "w").write("executed")\n'
        "class Safe:\n"
        "    async def run(self):\n"
        "        def nested():\n"
        "            return 1\n",
        encoding="utf-8",
    )
    marker = tmp_path / "source-executed.marker"
    adapter, manifest, config, context, _, _ = _run(tmp_path)
    registry = AdapterRegistry()
    assert registry.register(adapter).accepted
    assert adapter.detect(manifest).technologies[0].version is None
    assert registry.select_language(
        "python", adapter.detect(manifest).technologies
    ) == (adapter,)
    report = run_language_conformance(
        adapter, manifest, config, context, no_execution_marker=marker.exists
    )
    assert report.pass_rate == 1.0, [
        (item.name, item.detail) for item in report.cases if not item.passed
    ]
    assert not marker.exists()
