"""Language-file assignment follows descriptor extension and basename patterns."""

from __future__ import annotations

import pytest

from rkg.adapters import (
    CONTRACT_VERSION,
    AdapterDescriptor,
    AdapterKind,
    TechnologyConstraint,
)
from rkg.ingestion import ManifestFile
from rkg.jobs.partition import LanguageExtensionConflict, partition_language_files


def _file(path: str) -> ManifestFile:
    return ManifestFile(path, "hash", 1, b"already-loaded")


class _Adapter:
    def __init__(self, descriptor: AdapterDescriptor) -> None:
        self.descriptor = descriptor


def _adapter(
    adapter_id: str,
    patterns: tuple[str, ...],
    *,
    kind: AdapterKind = AdapterKind.LANGUAGE,
    version: str = "1.0.0",
) -> _Adapter:
    return _Adapter(
        AdapterDescriptor(
            adapter_id,
            version,
            CONTRACT_VERSION,
            kind,
            "synthetic",
            "synthetic grammar",
            patterns,
            (),
            ("structure",),
            framework=None if kind == AdapterKind.LANGUAGE else "fixture",
            technology_constraints=(
                ()
                if kind == AdapterKind.LANGUAGE
                else (TechnologyConstraint("fixture"),)
            ),
        )
    )


def _paths(assignments) -> dict[str, tuple[str, ...]]:
    return {
        item.adapter.descriptor.adapter_id: tuple(
            file.relative_path for file in item.files
        )
        for item in assignments
    }


def test_assigns_by_descriptor_extension_and_ignores_unknown_suffixes() -> None:
    python = _adapter("rkg.sample.python", ("*.py", "**/*.py"))
    other = _adapter("rkg.sample.other", ("*.other",))
    files = (
        _file("src/app.py"),
        _file("readme.md"),
        _file("lib.other"),
        _file("Makefile"),
        _file("nested/mod.py"),
    )
    assigned = partition_language_files(files, (other, python))
    assert _paths(assigned) == {
        "rkg.sample.other": ("lib.other",),
        "rkg.sample.python": ("nested/mod.py", "src/app.py"),
    }
    by_id = {item.adapter.descriptor.adapter_id: item for item in assigned}
    assert by_id["rkg.sample.python"].files[1] is files[0]
    assert by_id["rkg.sample.other"].files[0] is files[2]


def test_same_files_and_adapters_always_partition_the_same_way() -> None:
    first = _adapter("rkg.sample.b", ("*.b",))
    second = _adapter("rkg.sample.a", ("**/*.a",))
    files = (_file("z.b"), _file("a.a"), _file("m.a"))
    forward = _paths(partition_language_files(files, (first, second)))
    backward = _paths(partition_language_files(tuple(reversed(files)), (second, first)))
    assert forward == backward
    assert forward == {
        "rkg.sample.a": ("a.a", "m.a"),
        "rkg.sample.b": ("z.b",),
    }


def test_one_extension_belongs_to_one_language_adapter() -> None:
    with pytest.raises(LanguageExtensionConflict) as raised:
        partition_language_files(
            (_file("app.py"),),
            (
                _adapter("rkg.sample.left", ("*.py",)),
                _adapter("rkg.sample.right", ("**/*.py",)),
            ),
        )
    assert raised.value.code == "language_extension_conflict"


def test_repeated_pattern_on_one_adapter_is_not_a_conflict() -> None:
    language = _adapter("rkg.sample.python", ("*.py", "**/*.py"))
    assigned = partition_language_files((_file("app.py"),), (language, language))
    assert _paths(assigned) == {"rkg.sample.python": ("app.py",)}


def test_non_language_adapter_does_not_claim_an_extension() -> None:
    language = _adapter("rkg.sample.python", ("*.py",))
    framework = _adapter(
        "rkg.sample.framework",
        ("*.py",),
        kind=AdapterKind.FRAMEWORK,
    )
    assigned = partition_language_files(
        (_file("app.py"), _file("other.txt")), (framework, language)
    )
    assert _paths(assigned) == {"rkg.sample.python": ("app.py",)}


def test_suffix_match_is_the_final_extension() -> None:
    language = _adapter("rkg.sample.python", ("*.py",))
    assigned = partition_language_files(
        (_file("app.PY"), _file("app.py.bak"), _file("app.py")),
        (language,),
    )
    assert _paths(assigned) == {"rkg.sample.python": ("app.py",)}


def test_basename_pattern_joins_the_language_that_declares_it() -> None:
    java = _adapter("rkg.sample.java", ("*.java", "pom.xml", "build.gradle"))
    python = _adapter(
        "rkg.sample.python", ("*.py", "pyproject.toml", "requirements*.txt")
    )
    assigned = partition_language_files(
        (
            _file("src/App.java"),
            _file("pom.xml"),
            _file("readme.md"),
            _file("nested/build.gradle"),
            _file("app.py"),
            _file("pyproject.toml"),
            _file("requirements.txt"),
            _file("requirements-dev.txt"),
            _file("notes.txt"),
        ),
        (java, python),
    )
    assert _paths(assigned) == {
        "rkg.sample.java": ("nested/build.gradle", "pom.xml", "src/App.java"),
        "rkg.sample.python": (
            "app.py",
            "pyproject.toml",
            "requirements-dev.txt",
            "requirements.txt",
        ),
    }


def test_basename_file_without_source_does_not_open_an_assignment() -> None:
    java = _adapter("rkg.sample.java", ("*.java", "pom.xml"))
    assert partition_language_files((_file("pom.xml"),), (java,)) == ()


def test_one_basename_belongs_to_one_language_adapter() -> None:
    with pytest.raises(LanguageExtensionConflict) as raised:
        partition_language_files(
            (_file("pom.xml"), _file("App.java"), _file("App.kt")),
            (
                _adapter("rkg.sample.left", ("*.java", "pom.xml")),
                _adapter("rkg.sample.right", ("*.kt", "pom.xml")),
            ),
        )
    assert raised.value.code == "language_extension_conflict"
