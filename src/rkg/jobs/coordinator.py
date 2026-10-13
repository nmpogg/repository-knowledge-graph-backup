"""Single-writer, transport-neutral local index job coordinator."""

from __future__ import annotations

import threading
import time
import uuid
from collections import Counter
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Any

from rkg.adapters import AdapterContext, AdapterRegistry, ParseResult
from rkg.adapters.builtins import builtin_adapters
from rkg.detection import SelectionResult, select_adapters
from rkg.domain import Diagnostic, FactBatch, Severity, SourceScanConfig, diagnostic_id
from rkg.domain.validation import validate_adapter_fact_batch
from rkg.graph import SnapshotPublishMeta, publish_fact_batch
from rkg.ingestion import (
    LocalSourcePolicy,
    ManifestFile,
    SourceError,
    SourceManifest,
    build_manifest,
    resolve_local_source,
)
from rkg.jobs.partition import partition_language_files
from rkg.jobs.structure import add_directory_structure
from rkg.storage._util import CURRENT_SCHEMA_VERSION, TERMINAL_JOB_STAGES
from rkg.storage.connection import Storage
from rkg.storage.records import JobRecord, RepositoryRecord

_WRITER = threading.Lock()
_DEFAULT_IGNORES = (
    ".git/**",
    ".venv/**",
    "**/__pycache__/**",
    "node_modules/**",
    "**/.cache/**",
    "**/.pytest_cache/**",
    "**/.ruff_cache/**",
)


class IndexJobBusyError(RuntimeError):
    code = "index_job_busy"


def call_when_idle[T](operation: Callable[[], T]) -> T:
    """Run a storage read/write only when no index job owns the writer."""
    _WRITER.acquire()
    try:
        return operation()
    finally:
        _WRITER.release()


def writer_busy() -> bool:
    if _WRITER.acquire(blocking=False):
        _WRITER.release()
        return False
    return True


def scan_config(defaults: dict[str, Any] | None) -> SourceScanConfig:
    """Validate persisted operator defaults before reading any source bytes."""
    values = dict(defaults or {})
    if set(values) - {
        "max_files",
        "max_file_bytes",
        "include_patterns",
        "ignore_patterns",
    }:
        raise SourceError("source_config_invalid")
    max_files = values.get("max_files", 10000)
    max_bytes = values.get("max_file_bytes", 2 * 1024 * 1024)
    includes = values.get("include_patterns", ())
    ignores = values.get("ignore_patterns", ())
    if (
        type(max_files) is not int
        or type(max_bytes) is not int
        or not isinstance(includes, (list, tuple))
        or not isinstance(ignores, (list, tuple))
        or any(not isinstance(p, str) for p in (*includes, *ignores))
    ):
        raise SourceError("source_config_invalid")
    try:
        return SourceScanConfig(
            max_files, max_bytes, tuple(includes), _DEFAULT_IGNORES + tuple(ignores)
        )
    except ValueError:
        raise SourceError("source_config_invalid") from None


def recover_interrupted_jobs(storage: Storage) -> tuple[str, ...]:
    """Call once at process startup, before accepting new index requests."""
    if not _WRITER.acquire(blocking=False):
        raise IndexJobBusyError()
    try:
        result = storage.conn.execute(
            "MATCH (j:Job) WHERE NOT j.stage IN $terminal RETURN j.id ORDER BY j.id",
            {"terminal": sorted(TERMINAL_JOB_STAGES)},
        )
        ids = []
        while result.has_next():
            ids.append(str(result.get_next()[0]))
        for job_id in ids:
            storage.update_job(
                job_id,
                stage="failed",
                status="failed",
                error_code="index_interrupted",
                report={"error_code": "index_interrupted"},
            )
        return tuple(ids)
    finally:
        _WRITER.release()


def _detectors_for(language: str, adapters: tuple[object, ...]) -> tuple[object, ...]:
    """Detectors declared by adapters of this language, in factory order.

    An adapter with no ``technology_detectors`` contributes nothing. The
    coordinator does not name a language's detectors.
    """
    detectors: list[object] = []
    seen: set[type] = set()
    for adapter in adapters:
        if adapter.descriptor.language != language:
            continue
        provider = getattr(adapter, "technology_detectors", None)
        if provider is None:
            continue
        declared = provider() if callable(provider) else provider
        for detector in declared:
            kind = type(detector)
            if kind in seen:
                continue
            seen.add(kind)
            detectors.append(detector)
    return tuple(detectors)


def _manifest_for(
    manifest: SourceManifest, files: tuple[ManifestFile, ...]
) -> SourceManifest:
    if files == manifest.files:
        return manifest
    return replace(manifest, files=files)


def _application_for(
    application: str | None, language: object, adapters: tuple[object, ...]
) -> str | None:
    """Pass an entrypoint only to the language whose companion requires one."""
    if not application:
        return None
    parent = language.descriptor.language
    if any(
        adapter.descriptor.kind != language.descriptor.kind
        and adapter.descriptor.language == parent
        and getattr(adapter, "entrypoint_required", False)
        for adapter in adapters
    ):
        return application
    return None


def _merge_parsed(results: tuple[ParseResult, ...]) -> ParseResult:
    if len(results) == 1:
        return results[0]
    return ParseResult(
        tuple(
            sorted(
                (unit for result in results for unit in result.units),
                key=lambda unit: (unit.relative_path, unit.representation_kind),
            )
        ),
        (),
        tuple(
            sorted(
                (item for result in results for item in result.diagnostics),
                key=lambda item: (item.relative_path or "", item.line or 0, item.code),
            )
        ),
    )


def _merge_batches(
    repository_id: str, snapshot_id: str, batches: tuple[FactBatch, ...]
) -> FactBatch:
    if len(batches) == 1:
        return batches[0]
    return FactBatch(
        repository_id,
        snapshot_id,
        tuple(
            sorted(
                (item for batch in batches for item in batch.entities),
                key=lambda item: item.id,
            )
        ),
        tuple(
            sorted(
                (item for batch in batches for item in batch.edges),
                key=lambda item: item.id,
            )
        ),
        tuple(
            sorted(
                (item for batch in batches for item in batch.evidence),
                key=lambda item: item.id,
            )
        ),
        tuple(item for batch in batches for item in batch.diagnostics),
    )


def _merge_selections(selections: tuple[SelectionResult, ...]) -> SelectionResult:
    if len(selections) == 1:
        return selections[0]
    if not selections:
        return SelectionResult("ready", (), (), (), ())
    selected = next(
        (
            selection.selected_application
            for selection in selections
            if selection.selected_application is not None
        ),
        None,
    )
    return SelectionResult(
        "ready",
        tuple(item for selection in selections for item in selection.technologies),
        tuple(
            adapter
            for selection in selections
            for adapter in selection.language_adapters
        ),
        tuple(
            adapter for selection in selections for adapter in selection.deep_adapters
        ),
        tuple(
            sorted(
                {
                    item
                    for selection in selections
                    for item in selection.application_candidates
                },
                key=lambda item: (item.reference, item.relative_path, item.line),
            )
        ),
        selected,
    )


def _report(
    manifest: Any, parsed: Any, batch: Any, selection: Any, started: float
) -> dict[str, Any]:
    entities = Counter(item.type.value for item in batch.entities)
    edges = Counter(item.type.value for item in batch.edges)
    diagnostics = Counter(item.code for item in batch.diagnostics)
    severities = Counter(item.severity.value for item in batch.diagnostics)
    parsed_paths = {item.relative_path for item in parsed.units}
    return {
        "files": {
            "considered": manifest.considered_files,
            "parsed": len(parsed_paths),
            "skipped": len(manifest.skipped),
            "errors": sum(
                item.code.endswith("_syntax_error") for item in parsed.diagnostics
            ),
        },
        "skipped_files": [
            {"relative_path": item.relative_path, "code": item.code}
            for item in manifest.skipped
        ],
        "entities_by_type": dict(sorted(entities.items())),
        "edges_by_type": dict(sorted(edges.items())),
        "entity_total": len(batch.entities),
        "edge_total": len(batch.edges),
        "diagnostics_by_code": dict(sorted(diagnostics.items())),
        "diagnostic_total": len(batch.diagnostics),
        "diagnostics": [
            {
                "code": item.code,
                "severity": item.severity.value,
                "relative_path": item.file_path,
                "line": item.line,
            }
            for item in batch.diagnostics
        ],
        "unresolved_total": sum(
            count for code, count in diagnostics.items() if "unresolved" in code
        ),
        "warning_total": severities["warning"] + len(manifest.skipped),
        "error_total": severities["error"],
        "technologies": [
            {
                "technology": item.technology,
                "version": item.version,
                "support_state": item.state.value,
                "adapter_ids": list(item.adapter_ids),
                "capabilities": list(item.capabilities),
            }
            for item in selection.technologies
        ],
        "application_candidates": [
            item.reference for item in selection.application_candidates
        ],
        "selected_application": (
            selection.selected_application.reference
            if selection.selected_application
            else None
        ),
        "duration_ms": max(0, round((time.monotonic() - started) * 1000)),
    }


class IndexCoordinator:
    """Run one repository index job at a time across coordinator instances."""

    def __init__(
        self,
        storage: Storage,
        policy: LocalSourcePolicy,
        *,
        adapter_factory: Callable[[], tuple[object, ...]] | None = None,
    ) -> None:
        self.storage = storage
        self.policy = policy
        self._adapter_factory = adapter_factory or builtin_adapters

    def _open_registry(self) -> tuple[AdapterRegistry, tuple[object, ...]]:
        adapters = tuple(self._adapter_factory())
        registry = AdapterRegistry()
        for adapter in adapters:
            registration = registry.register(adapter)
            if not registration.accepted:
                raise RuntimeError("adapter_registration_failed")
        return registry, adapters

    def run(
        self,
        repository_id: str,
        *,
        on_accepted: Callable[[JobRecord], None] | None = None,
        app_module: str | None = None,
        app_symbol: str | None = None,
        scan_defaults: dict[str, Any] | None = None,
    ) -> JobRecord:
        if not _WRITER.acquire(blocking=False):
            raise IndexJobBusyError()
        started = time.monotonic()
        job: JobRecord | None = None
        try:
            repo = self.storage.get_repository(repository_id)
            if repo.source_type != "local":
                raise SourceError("source_type_unsupported")
            if scan_defaults is not None:
                merged = dict(repo.scan_defaults or {})
                merged.update(scan_defaults)
                scan_config(merged)
                repo = replace(repo, scan_defaults=merged)
            fields: dict[str, Any] = {}
            if app_module is not None:
                fields["app_module"] = app_module
            if app_symbol is not None:
                fields["app_symbol"] = app_symbol
            if fields:
                repo = self.storage.update_repository(
                    repository_id, expected_revision=repo.revision, **fields
                )
                if scan_defaults is not None:
                    repo = replace(repo, scan_defaults=merged)
            job = self.storage.create_job(repository_id, source_type=repo.source_type)
            job = self.storage.update_job(job.id, stage="scanning")
            if on_accepted is not None:
                on_accepted(job)
            return self._run(job, repo, started)
        except Exception as exc:
            if job is None:
                raise
            code = getattr(exc, "code", None)
            if not isinstance(code, str):
                code = "index_failed"
            current_report = self.storage.get_job(job.id).report or {}
            return self.storage.update_job(
                job.id,
                stage="failed",
                status="failed",
                error_code=code,
                report=current_report
                | {
                    "error_code": code,
                    "duration_ms": max(0, round((time.monotonic() - started) * 1000)),
                },
            )
        finally:
            _WRITER.release()

    def _run(self, job: JobRecord, repo: RepositoryRecord, started: float) -> JobRecord:
        config = scan_config(repo.scan_defaults)
        source = resolve_local_source(
            repo.id,
            Path(repo.source_locator),
            self.policy,
            source_root=repo.source_root,
        )
        manifest = build_manifest(source, config)
        self.storage.update_job(
            job.id, stage="parsing", manifest_hash=manifest.manifest_hash
        )
        registry, adapters = self._open_registry()
        assignments = partition_language_files(manifest.files, adapters)
        application = (
            f"{repo.app_module}:{repo.app_symbol}"
            if repo.app_module and repo.app_symbol
            else None
        )
        prepared: list[tuple[object, ParseResult, SelectionResult]] = []
        for assignment in assignments:
            portion = _manifest_for(manifest, assignment.files)
            parsed = assignment.adapter.parse(portion, config)
            selection = select_adapters(
                portion,
                parsed,
                assignment.adapter,
                registry,
                _detectors_for(assignment.adapter.descriptor.language, adapters),
                application_override=_application_for(
                    application, assignment.adapter, adapters
                ),
            )
            if selection.status != "ready":
                return self.storage.update_job(
                    job.id,
                    stage="failed",
                    status="failed",
                    error_code=selection.error_code or "adapter_selection_failed",
                    report={
                        "error_code": selection.error_code
                        or "adapter_selection_failed",
                        "application_candidates": [
                            item.reference for item in selection.application_candidates
                        ],
                        "duration_ms": max(
                            0, round((time.monotonic() - started) * 1000)
                        ),
                    },
                )
            prepared.append((assignment.adapter, parsed, selection))
        self.storage.update_job(job.id, stage="extracting")
        context = AdapterContext(repo.id, f"snap_{uuid.uuid4().hex}", job.id, config)
        batches: list[FactBatch] = []
        adapter_versions: dict[str, str] = {}
        # Language extract/resolve stays partition-local. Deep/framework adapters
        # run once after merge so polyglot stacks (e.g. Nuxt = Vue SFCs + TS
        # Nitro/composables) see the full ParseResult and FactBatch — same model
        # as evaluation run_polyglot_pipeline / REG-ADAPTER-001 rkg.nuxt.
        deep_runs: list[tuple[object, object]] = []
        seen_deep: set[str] = set()
        for language, parsed, selection in prepared:
            batch = language.extract(context, parsed).facts
            validate_adapter_fact_batch(batch)
            batch = language.resolve(context, parsed, batch).facts
            validate_adapter_fact_batch(batch)
            adapter_versions[language.descriptor.adapter_id] = (
                language.descriptor.adapter_version
            )
            batches.append(batch)
            for adapter in selection.deep_adapters:
                adapter_id = adapter.descriptor.adapter_id
                if adapter_id in seen_deep:
                    continue
                seen_deep.add(adapter_id)
                deep_runs.append((adapter, selection))
        parsed = _merge_parsed(tuple(item[1] for item in prepared))
        selection = _merge_selections(tuple(item[2] for item in prepared))
        batch = _merge_batches(repo.id, context.snapshot_id, tuple(batches))
        for adapter, adapter_selection in deep_runs:
            configure = getattr(adapter, "for_application", None)
            if configure and adapter_selection.selected_application:
                adapter = configure(adapter_selection.selected_application.reference)
            batch = adapter.extract(context, parsed, batch).facts
            validate_adapter_fact_batch(batch)
            batch = adapter.resolve(context, parsed, batch).facts
            validate_adapter_fact_batch(batch)
            adapter_versions[adapter.descriptor.adapter_id] = (
                adapter.descriptor.adapter_version
            )
        version_warnings = tuple(
            Diagnostic(
                diagnostic_id(
                    job.id,
                    "adapter_version_unverified",
                    item.evidence[0].relative_path,
                    None,
                    ordinal,
                ),
                job.id,
                Severity.WARNING,
                "adapter_version_unverified",
                "Static patterns extracted; version compatibility is unverified.",
                context.snapshot_id,
                item.evidence[0].relative_path,
            )
            for ordinal, item in enumerate(selection.technologies)
            if item.state.value == "version_unverified" and item.adapter_ids
        )
        batch = replace(batch, diagnostics=batch.diagnostics + version_warnings)
        batch = add_directory_structure(batch, manifest)
        report = _report(manifest, parsed, batch, selection, started)
        self.storage.update_job(job.id, stage="publishing", report=report)
        snapshot = publish_fact_batch(
            self.storage,
            batch,
            SnapshotPublishMeta(
                manifest.source_revision,
                manifest.manifest_hash,
                manifest.scan_config_digest,
                "rkg/0.2.0",
                str(CURRENT_SCHEMA_VERSION),
                adapter_versions,
            ),
        )
        report["snapshot_id"] = snapshot.id
        report["duration_ms"] = max(0, round((time.monotonic() - started) * 1000))
        warning = bool(manifest.skipped or parsed.diagnostics or batch.diagnostics)
        terminal = "succeeded_with_warnings" if warning else "succeeded"
        return self.storage.update_job(
            job.id,
            stage=terminal,
            status=terminal,
            report=report,
        )
