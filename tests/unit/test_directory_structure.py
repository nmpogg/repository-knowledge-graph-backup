"""Manifest-backed filesystem structure and ownership invariants."""

from dataclasses import replace
from pathlib import Path

import pytest

from rkg.adapters import AdapterContext, PythonLanguageAdapter
from rkg.domain import (
    EntityType,
    InvalidFactBatch,
    SourceScanConfig,
    edge_id,
    validate_fact_batch,
)
from rkg.domain.validation import validate_adapter_fact_batch
from rkg.ingestion import LocalSourcePolicy, build_manifest, resolve_local_source
from rkg.jobs.structure import STRUCTURE_RULE, add_directory_structure


def _build(root: Path, source_root=None):
    config = SourceScanConfig(20, 4096, ("**/*.py",), ("ignored/**",))
    source = resolve_local_source(
        "repo", root, LocalSourcePolicy((root,)), source_root=source_root
    )
    manifest = build_manifest(source, config)
    adapter = PythonLanguageAdapter()
    parsed = adapter.parse(manifest, config)
    facts = adapter.extract(AdapterContext("repo", "snap", "job", config), parsed).facts
    return manifest, facts, add_directory_structure(facts, manifest)


def test_unique_ancestors_empty_files_and_root_files(tmp_path):
    for path in ("main.py", "a/sub/one.py", "a/sub/two.py", "b/sub/empty.py"):
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("" if "empty" in path else "def f(): pass\n")
    (tmp_path / "unused").mkdir()
    ignored = tmp_path / "ignored"
    ignored.mkdir()
    (ignored / "bad.py").write_text("def nope(:\n")
    manifest, facts, result = _build(tmp_path)
    directories = {
        e.file_path: e for e in result.entities if e.type == EntityType.DIRECTORY
    }
    assert set(directories) == {"a", "a/sub", "b", "b/sub"}
    assert directories["a/sub"].id != directories["b/sub"].id
    assert all(
        e.name == Path(e.file_path).name
        and e.qualified_name == e.file_path
        and e.start_line is None
        and e.language_kind is None
        for e in directories.values()
    )
    assert not any(e.type == EntityType.NAMESPACE for e in result.entities)
    root_file = next(
        e
        for e in result.entities
        if e.file_path == "main.py" and e.type == EntityType.SOURCE_UNIT
    )
    assert any(
        e.source_id == "repo" and e.target_id == root_file.id for e in result.edges
    )
    assert add_directory_structure(facts, manifest) == result
    assert result.entities == tuple(sorted(result.entities, key=lambda e: e.id))
    assert len(manifest.files) == 4  # Directories do not count towards file limits.


def test_source_root_ancestors_and_syntax_error_do_not_trigger_another_walk(
    tmp_path, monkeypatch
):
    folder = tmp_path / "app" / "services"
    folder.mkdir(parents=True)
    (folder / "good.py").write_text("def f(): pass\n")
    (folder / "bad.py").write_text("def f(:\n")
    manifest, facts, result = _build(tmp_path, "app/services")
    assert {e.file_path for e in result.entities if e.type == EntityType.DIRECTORY} == {
        "app",
        "app/services",
    }
    assert not any(e.file_path == "app/services/bad.py" for e in result.entities)
    monkeypatch.setattr(
        Path, "open", lambda *_a, **_k: pytest.fail("second source walk")
    )
    assert add_directory_structure(facts, manifest) == result


def test_structure_rejects_missing_manifest_member_and_adapter_owned_directory(
    tmp_path,
):
    (tmp_path / "main.py").write_text("")
    manifest, facts, result = _build(tmp_path)
    with pytest.raises(InvalidFactBatch, match="manifest"):
        add_directory_structure(facts, replace(manifest, files=()))
    folder = tmp_path / "pkg"
    folder.mkdir()
    (folder / "unit.py").write_text("")
    _, _, directories = _build(tmp_path)
    with pytest.raises(InvalidFactBatch, match="v2 adapters"):
        validate_adapter_fact_batch(directories)
    assert dict(facts.entities[0].attributes)["module_name"] == "main"
    validate_fact_batch(result, manifest_paths=frozenset({"main.py"}))


@pytest.mark.parametrize("mutation", ["parent", "evidence", "manifest", "identity"])
def test_invalid_directory_structure_is_rejected(tmp_path, mutation):
    folder = tmp_path / "a" / "b"
    folder.mkdir(parents=True)
    (folder / "file.py").write_text("")
    _, _, result = _build(tmp_path)
    edge = next(
        e for e in result.edges if e.source_id != "repo" and e.rule == STRUCTURE_RULE
    )
    if mutation == "parent":
        new = replace(
            edge,
            source_id="repo",
            id=edge_id("snap", edge.type, "repo", edge.target_id),
        )
        result = replace(
            result, edges=tuple(new if e == edge else e for e in result.edges)
        )
    elif mutation == "evidence":
        result = replace(
            result, evidence=tuple(replace(e, start_line=2) for e in result.evidence)
        )
    elif mutation == "identity":
        result = replace(
            result,
            entities=tuple(
                replace(e, name="wrong") if e.type == EntityType.DIRECTORY else e
                for e in result.entities
            ),
        )
    with pytest.raises(InvalidFactBatch):
        validate_fact_batch(
            result,
            manifest_paths=frozenset()
            if mutation == "manifest"
            else frozenset({"a/b/file.py"}),
        )
