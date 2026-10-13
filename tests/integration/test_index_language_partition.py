"""Index jobs parse only the files assigned to each language adapter."""

from __future__ import annotations

from rkg.adapters import (
    CONTRACT_VERSION,
    AdapterContext,
    AdapterDescriptor,
    AdapterKind,
    AdapterResult,
    AIOKafkaMessagingAdapter,
    DetectionReport,
    FastAPIFrameworkAdapter,
    ParsedUnit,
    ParseResult,
    PythonLanguageAdapter,
    SQLAlchemyDataAccessAdapter,
)
from rkg.domain import Entity, EntityType, FactBatch, source_entity_id
from rkg.graph import count_entities, entity_qualified_names
from rkg.ingestion import LocalSourcePolicy
from rkg.jobs import IndexCoordinator
from rkg.jobs.coordinator import builtin_adapters
from rkg.storage.connection import Storage


class CountingPython(PythonLanguageAdapter):
    def __init__(self) -> None:
        self.seen_parse: list[tuple[str, ...]] = []
        self.seen_detect: list[tuple[str, ...]] = []

    def detect(self, manifest):
        self.seen_detect.append(tuple(item.relative_path for item in manifest.files))
        return super().detect(manifest)

    def parse(self, manifest, config):
        self.seen_parse.append(tuple(item.relative_path for item in manifest.files))
        return super().parse(manifest, config)


class LineLanguageAdapter:
    """Parse every file it is given, without searching the repository."""

    def __init__(self, extension: str, language: str, adapter_id: str) -> None:
        self.seen_parse: list[tuple[str, ...]] = []
        self.seen_detect: list[tuple[str, ...]] = []
        self.descriptor = AdapterDescriptor(
            adapter_id,
            "1.0.0",
            CONTRACT_VERSION,
            AdapterKind.LANGUAGE,
            language,
            "line-list/v1",
            (f"*.{extension}",),
            (),
            ("structure",),
        )

    def detect(self, manifest):
        paths = tuple(item.relative_path for item in manifest.files)
        self.seen_detect.append(paths)
        return DetectionReport()

    def parse(self, manifest, config):
        del config
        paths = tuple(item.relative_path for item in manifest.files)
        self.seen_parse.append(paths)
        return ParseResult(
            tuple(
                ParsedUnit(path, self.descriptor.language, "line-list/v1", "hash", path)
                for path in paths
            )
        )

    def extract(self, context: AdapterContext, parsed: ParseResult) -> AdapterResult:
        entities = []
        for unit in parsed.units:
            path = unit.relative_path
            entities.append(
                Entity(
                    source_entity_id(
                        context.repository_id, path, EntityType.SOURCE_UNIT, path
                    ),
                    context.repository_id,
                    context.snapshot_id,
                    EntityType.SOURCE_UNIT,
                    path,
                    path,
                    path,
                    language_kind=f"{self.descriptor.language}_source_unit",
                )
            )
        return AdapterResult(
            FactBatch(
                context.repository_id,
                context.snapshot_id,
                tuple(sorted(entities, key=lambda item: item.id)),
            ),
            (),
        )

    def resolve(self, context, parsed, candidate):
        del context, parsed
        return AdapterResult(candidate, ())


def _file_paths(storage: Storage, snapshot_id: str) -> set[str]:
    result = storage.conn.execute(
        "MATCH (e:Entity {snapshot_id: $sid}) "
        "WHERE e.file_path IS NOT NULL RETURN e.file_path",
        {"sid": snapshot_id},
    )
    paths = set()
    while result.has_next():
        value = result.get_next()[0]
        if value:
            paths.add(str(value))
    return paths


def _index(tmp_path, source, adapters):
    with Storage(tmp_path / "graph") as storage:
        repo = storage.create_repository(
            display_name="fixture", source_type="local", source_locator=str(source)
        )
        job = IndexCoordinator(
            storage, LocalSourcePolicy((tmp_path,)), adapter_factory=lambda: adapters
        ).run(repo.id)
        snapshot_id = storage.get_repository(repo.id).active_snapshot_id
        return {
            "status": job.status,
            "error_code": job.error_code,
            "report": job.report,
            "parsed": job.report.get("files", {}).get("parsed"),
            "snapshot_id": snapshot_id,
            "snapshots": storage.list_snapshots(repo.id).total if snapshot_id else 0,
            "paths": _file_paths(storage, snapshot_id) if snapshot_id else set(),
            "names": (
                entity_qualified_names(storage, snapshot_id) if snapshot_id else []
            ),
            "entities": count_entities(storage, snapshot_id) if snapshot_id else 0,
            "versions": (
                storage.get_snapshot(repo.id, snapshot_id).adapter_versions
                if snapshot_id
                else {}
            ),
        }


def test_python_only_repository_still_builds_the_same_graph(tmp_path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "app.py").write_text("def kept():\n    return 1\n", encoding="utf-8")
    python = CountingPython()
    result = _index(tmp_path, source, (python, *builtin_adapters()[1:]))
    assert result["status"] == "succeeded"
    assert result["parsed"] == 1
    assert result["snapshots"] == 1
    assert "app.kept" in result["names"]
    assert result["paths"] == {"app.py"}
    assert result["versions"]["rkg.python"] == "2.1"
    assert python.seen_parse == [("app.py",)]
    assert python.seen_detect == [("app.py",)]


def test_other_language_runs_and_python_does_not_parse(tmp_path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "lib.other").write_text(
        "from fastapi import FastAPI\napp = FastAPI()\n", encoding="utf-8"
    )
    python = CountingPython()
    other = LineLanguageAdapter("other", "other", "rkg.sample.other")
    result = _index(
        tmp_path,
        source,
        (
            python,
            FastAPIFrameworkAdapter(),
            SQLAlchemyDataAccessAdapter(),
            AIOKafkaMessagingAdapter(),
            other,
        ),
    )
    assert result["status"] == "succeeded"
    assert result["parsed"] == 1
    assert result["snapshots"] == 1
    assert python.seen_parse == []
    assert python.seen_detect == []
    assert other.seen_parse == [("lib.other",)]
    assert other.seen_detect == [("lib.other",)]
    assert result["paths"] == {"lib.other"}
    assert "rkg.python" not in result["versions"]
    assert "rkg.fastapi" not in result["versions"]
    assert "Endpoint" not in result["report"]["entities_by_type"]


def test_two_languages_merge_into_one_snapshot(tmp_path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "app.py").write_text("def kept():\n    return 1\n", encoding="utf-8")
    (source / "lib.other").write_text("other\n", encoding="utf-8")
    (source / "notes.md").write_text("not a language file\n", encoding="utf-8")
    python = CountingPython()
    other = LineLanguageAdapter("other", "other", "rkg.sample.other")
    result = _index(
        tmp_path,
        source,
        (
            python,
            FastAPIFrameworkAdapter(),
            SQLAlchemyDataAccessAdapter(),
            AIOKafkaMessagingAdapter(),
            other,
        ),
    )
    assert result["status"] == "succeeded"
    assert result["parsed"] == 2
    assert result["snapshots"] == 1
    assert python.seen_parse == [("app.py",)]
    assert python.seen_detect == [("app.py",)]
    assert other.seen_parse == [("lib.other",)]
    assert other.seen_detect == [("lib.other",)]
    assert result["paths"] == {"app.py", "lib.other"}
    assert "notes.md" not in result["paths"]
    assert "app.kept" in result["names"]
    assert result["versions"]["rkg.python"] == "2.1"
    assert result["versions"]["rkg.sample.other"] == "1.0.0"


def test_companion_uses_only_the_parent_language_portion(tmp_path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "pyproject.toml").write_text(
        '[project]\ndependencies = ["fastapi>=0.100"]\n', encoding="utf-8"
    )
    (source / "uv.lock").write_text(
        '[[package]]\nname = "fastapi"\nversion = "0.115.0"\n', encoding="utf-8"
    )
    (source / "app.py").write_text(
        "from fastapi import FastAPI\n"
        "app = FastAPI()\n"
        '@app.get("/kept")\n'
        "def kept():\n"
        "    return 1\n",
        encoding="utf-8",
    )
    (source / "lib.other").write_text(
        "from fastapi import FastAPI\n"
        "app = FastAPI()\n"
        '@app.get("/other")\n'
        "def other():\n"
        "    return 1\n",
        encoding="utf-8",
    )
    (source / "notes.md").write_text("not a language file\n", encoding="utf-8")
    python = CountingPython()
    other = LineLanguageAdapter("other", "other", "rkg.sample.other")
    result = _index(
        tmp_path,
        source,
        (
            python,
            FastAPIFrameworkAdapter(),
            SQLAlchemyDataAccessAdapter(),
            AIOKafkaMessagingAdapter(),
            other,
        ),
    )
    assert result["status"] in {"succeeded", "succeeded_with_warnings"}
    assert result["snapshots"] == 1
    assert result["versions"]["rkg.fastapi"] == "2.1.0"
    assert result["report"]["entities_by_type"]["Endpoint"] == 1
    assert result["report"]["selected_application"] == "app:app"
    assert python.seen_parse == [("app.py", "pyproject.toml", "uv.lock")]
    assert other.seen_parse == [("lib.other",)]
    assert "notes.md" not in result["paths"]
    assert "lib.other" in result["paths"]
    assert "app.py" in result["paths"]


def test_unregistered_extension_succeeds_without_language_nodes(tmp_path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "notes.md").write_text("# notes\n", encoding="utf-8")
    (source / "data.bin").write_bytes(b"abc")
    python = CountingPython()
    result = _index(tmp_path, source, (python, *builtin_adapters()[1:]))
    assert result["status"] == "succeeded"
    assert result["parsed"] == 0
    assert result["report"]["files"]["considered"] == 2
    assert result["entities"] == 0
    assert result["paths"] == set()
    assert result["snapshots"] == 1
    assert python.seen_parse == []
    assert "rkg.python" not in result["versions"]


def test_duplicate_language_extension_fails_the_job(tmp_path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "app.py").write_text("def kept():\n    return 1\n", encoding="utf-8")
    other = LineLanguageAdapter("py", "other", "rkg.sample.other")
    result = _index(tmp_path, source, (*builtin_adapters(), other))
    assert result["status"] == "failed"
    assert result["error_code"] == "language_extension_conflict"
    assert result["report"]["error_code"] == "language_extension_conflict"
    assert result["snapshot_id"] is None


def test_shared_directory_is_built_once_for_two_languages(tmp_path):
    source = tmp_path / "source"
    (source / "shared").mkdir(parents=True)
    (source / "shared/unit.py").write_text("def f(): pass\n")
    (source / "shared/unit.other").write_text("fixture\n")
    result = _index(
        tmp_path,
        source,
        (
            CountingPython(),
            LineLanguageAdapter("other", "other", "rkg.sample.other"),
        ),
    )
    assert result["status"] == "succeeded"
    assert result["parsed"] == 2
    assert result["report"]["entities_by_type"]["Directory"] == 1
    assert "Namespace" not in result["report"]["entities_by_type"]
    assert result["paths"] == {"shared", "shared/unit.py", "shared/unit.other"}
