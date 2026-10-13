"""TASK-RKG-008 registry selection and static application discovery."""

from __future__ import annotations

from pathlib import Path

from rkg.adapters import (
    CONTRACT_VERSION,
    AdapterContext,
    AdapterDescriptor,
    AdapterKind,
    AdapterRegistry,
    DetectionEvidence,
    DetectionReport,
    FastAPIFrameworkAdapter,
    PythonLanguageAdapter,
    TechnologyConstraint,
    TechnologyDetection,
    run_language_conformance,
)
from rkg.detection import (
    DetectionState,
    FastAPIAppDetector,
    PythonImportDetector,
    select_adapters,
)
from rkg.detection.contracts import FrameworkObservation
from rkg.domain import SourceScanConfig
from rkg.ingestion import LocalSourcePolicy, build_manifest, resolve_local_source


class DeepStub:
    entrypoint_required: bool

    def __init__(
        self,
        adapter_id: str,
        technology: str,
        *,
        kind: AdapterKind = AdapterKind.FRAMEWORK,
        constraint: str = "",
        requires_app: bool = False,
        capabilities: tuple[str, ...] = ("app",),
    ) -> None:
        self.entrypoint_required = requires_app
        self.descriptor = AdapterDescriptor(
            adapter_id,
            "1.0.0",
            CONTRACT_VERSION,
            kind,
            "python",
            "AST profile",
            ("*.py",),
            (),
            capabilities,
            framework=technology,
            technology_constraints=(TechnologyConstraint(technology, constraint),)
            if constraint
            else (),
        )

    def detect(self, manifest, parsed):
        raise NotImplementedError

    def extract(self, context, parsed, base):
        raise NotImplementedError

    def resolve(self, context, parsed, candidate):
        raise NotImplementedError


def _fixture(root: Path, files: dict[str, str]):
    for name, content in files.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    config = SourceScanConfig(30, 16384)
    manifest = build_manifest(
        resolve_local_source("repo-eight", root, LocalSourcePolicy((root,))), config
    )
    language = PythonLanguageAdapter()
    parsed = language.parse(manifest, config)
    registry = AdapterRegistry()
    assert registry.register(language).accepted
    return manifest, parsed, language, registry, config


def _select(manifest, parsed, language, registry, **kwargs):
    return select_adapters(
        manifest,
        parsed,
        language,
        registry,
        (PythonImportDetector(), FastAPIAppDetector()),
        **kwargs,
    )


def _support(result, name: str):
    return next(item for item in result.technologies if item.technology == name)


def test_declared_only_and_version_states(tmp_path: Path) -> None:
    manifest, parsed, language, registry, _ = _fixture(
        tmp_path,
        {
            "pyproject.toml": '[project]\ndependencies = ["fastapi>=0.100"]\n',
            "main.py": "pass\n",
        },
    )
    assert registry.register(
        DeepStub("rkg.fastapi", "fastapi", constraint=">=0.100,<1.0", requires_app=True)
    ).accepted
    declared = _select(manifest, parsed, language, registry)
    assert _support(declared, "python").state == DetectionState.SUPPORTED_PATTERNS
    assert _support(declared, "fastapi").state == DetectionState.DETECTED_ONLY
    assert declared.deep_adapters == ()
    assert declared.status == "ready"

    (tmp_path / "main.py").write_text(
        "from fastapi import FastAPI\napp = FastAPI()\n", encoding="utf-8"
    )
    manifest, parsed, language, _, _ = _fixture(tmp_path, {})
    unknown = _select(manifest, parsed, language, registry)
    assert _support(unknown, "fastapi").state == DetectionState.VERSION_UNVERIFIED
    assert unknown.deep_adapters == ()

    (tmp_path / "uv.lock").write_text(
        '[[package]]\nname = "fastapi"\nversion = "2.0.0"\n', encoding="utf-8"
    )
    manifest, parsed, language, _, _ = _fixture(tmp_path, {})
    unsupported = _select(manifest, parsed, language, registry)
    assert _support(unsupported, "fastapi").state == DetectionState.UNSUPPORTED_VERSION
    assert unsupported.deep_adapters == ()


def test_fastapi_unknown_version_extracts_without_supported_claim(
    tmp_path: Path,
) -> None:
    manifest, parsed, language, registry, _ = _fixture(
        tmp_path,
        {"main.py": "from fastapi import FastAPI\napp = FastAPI()\n"},
    )
    adapter = FastAPIFrameworkAdapter()
    assert registry.register(adapter).accepted
    selection = _select(manifest, parsed, language, registry)
    assert selection.status == "ready"
    assert selection.deep_adapters == (adapter,)
    support = _support(selection, "fastapi")
    assert support.state == DetectionState.VERSION_UNVERIFIED
    assert support.adapter_ids == ("rkg.fastapi",)
    assert "routes" in support.capabilities
    assert selection.selected_application.reference == "main:app"

    (tmp_path / "uv.lock").write_text(
        '[[package]]\nname = "fastapi"\nversion = "2.0.0"\n', encoding="utf-8"
    )
    manifest, parsed, language, _, _ = _fixture(tmp_path, {})
    unsupported = _select(manifest, parsed, language, registry)
    assert unsupported.deep_adapters == ()
    assert _support(unsupported, "fastapi").state == DetectionState.UNSUPPORTED_VERSION


def test_app_candidates_override_and_reindex_selection(tmp_path: Path) -> None:
    manifest, parsed, language, registry, config = _fixture(
        tmp_path,
        {
            "pyproject.toml": '[project]\ndependencies = ["fastapi>=0.100"]\n',
            "uv.lock": '[[package]]\nname = "fastapi"\nversion = "0.115.0"\n',
            "one.py": "from fastapi import FastAPI as API\napp = API()\n",
            "two.py": "import fastapi as web\nserver = web.FastAPI()\n",
        },
    )
    assert registry.register(
        DeepStub("rkg.fastapi", "fastapi", constraint=">=0.100,<1.0", requires_app=True)
    ).accepted
    report = run_language_conformance(
        language,
        manifest,
        config,
        AdapterContext("repo-eight", "snap-eight", "job-eight", config),
        no_execution_marker=lambda: False,
    )
    assert report.pass_rate == 1.0
    pending = _select(manifest, parsed, language, registry)
    assert pending.status == "app_selection_required"
    assert [item.reference for item in pending.application_candidates] == [
        "one:app",
        "two:server",
    ]
    chosen = _select(
        manifest, parsed, language, registry, application_override="two:server"
    )
    assert chosen.status == "ready"
    assert chosen.selected_application.reference == "two:server"
    repeat = _select(
        manifest, parsed, language, registry, prior_application="two:server"
    )
    assert repeat.selected_application == chosen.selected_application
    invalid = _select(
        manifest, parsed, language, registry, application_override="missing:app"
    )
    assert invalid.error_code == "app_override_invalid"
    assert (
        _select(
            manifest,
            parsed,
            language,
            registry,
            adapter_overrides=("rkg.unknown",),
        ).error_code
        == "adapter_override_invalid"
    )


def test_single_app_auto_select_and_unresolved(tmp_path: Path) -> None:
    manifest, parsed, language, registry, _ = _fixture(
        tmp_path,
        {
            "uv.lock": '[[package]]\nname = "fastapi"\nversion = "0.115.0"\n',
            "app.py": "from fastapi import FastAPI\napp = FastAPI()\n",
        },
    )
    assert registry.register(
        DeepStub("rkg.fastapi", "fastapi", requires_app=True)
    ).accepted
    selected = _select(manifest, parsed, language, registry)
    assert selected.status == "ready"
    assert selected.selected_application.reference == "app:app"
    (tmp_path / "app.py").write_text(
        "from fastapi import FastAPI\ndef make():\n    return FastAPI()\n",
        encoding="utf-8",
    )
    manifest, parsed, language, _, _ = _fixture(tmp_path, {})
    unresolved = _select(manifest, parsed, language, registry)
    assert unresolved.status == "app_unresolved"
    assert unresolved.application_candidates == ()

    (tmp_path / "app.py").write_text(
        "from fastapi import FastAPI\napp = FastAPI()\napp = None\n",
        encoding="utf-8",
    )
    manifest, parsed, language, _, _ = _fixture(tmp_path, {})
    reassigned = _select(manifest, parsed, language, registry)
    assert reassigned.status == "app_unresolved"
    assert reassigned.application_candidates == ()


def test_multiple_deep_adapters_and_local_shadow(tmp_path: Path) -> None:
    manifest, parsed, language, registry, _ = _fixture(
        tmp_path,
        {
            "pyproject.toml": '[project]\ndependencies = ["SQLAlchemy>=2", '
            '"aiokafka>=0.10", "PyYAML>=6"]\n',
            "app.py": "import sqlalchemy as sa\n"
            "from aiokafka import AIOKafkaProducer\nimport yaml\n",
            "yaml.py": "pass\n",
        },
    )
    for adapter in (
        DeepStub(
            "rkg.sqlalchemy",
            "sqlalchemy",
            kind=AdapterKind.DATA_ACCESS,
            capabilities=("tables", "reads"),
        ),
        DeepStub(
            "rkg.aiokafka",
            "aiokafka",
            kind=AdapterKind.MESSAGING,
            capabilities=("topics", "publishes"),
        ),
    ):
        assert registry.register(adapter).accepted
    result = _select(manifest, parsed, language, registry)
    assert result.status == "ready"
    assert {item.descriptor.adapter_id for item in result.deep_adapters} == {
        "rkg.sqlalchemy",
        "rkg.aiokafka",
    }
    assert _support(result, "pyyaml").state == DetectionState.DETECTED_ONLY
    assert _support(result, "sqlalchemy").capabilities == ("reads", "tables")
    assert _support(result, "aiokafka").capabilities == ("publishes", "topics")


def test_new_detector_and_adapter_need_no_coordinator_change(tmp_path: Path) -> None:
    manifest, parsed, language, registry, _ = _fixture(tmp_path, {"main.py": "pass\n"})
    adapter = DeepStub(
        "vendor.custom",
        "custom",
        kind=AdapterKind.DATA_ACCESS,
        capabilities=("tables",),
    )
    assert registry.register(adapter).accepted

    class CustomDetector:
        def detect(self, manifest, parsed):
            return FrameworkObservation(
                DetectionReport(
                    (
                        TechnologyDetection(
                            "custom",
                            None,
                            (DetectionEvidence("main.py", "RKG.fixture.detect.v1"),),
                        ),
                    )
                )
            )

    result = select_adapters(manifest, parsed, language, registry, (CustomDetector(),))
    assert result.deep_adapters == (adapter,)
    assert _support(result, "custom").state == DetectionState.SUPPORTED_PATTERNS
