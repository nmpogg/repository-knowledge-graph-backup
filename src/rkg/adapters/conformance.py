"""Shared observable checks for versioned analyzer adapters."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import PurePosixPath

from rkg.adapters.contracts import (
    CONTRACT_VERSION,
    AdapterContext,
    AdapterDescriptor,
    AdapterResult,
    DetectionReport,
    FrameworkAdapter,
    LanguageAdapter,
    ParseResult,
)
from rkg.domain import FactBatch, SourceScanConfig
from rkg.domain.validation import validate_adapter_fact_batch
from rkg.ingestion import SourceManifest

RULE_ID = re.compile(
    r"^RKG\.[A-Za-z][A-Za-z0-9_]*\.[A-Za-z][A-Za-z0-9_]*\.v[1-9][0-9]*$"
)


@dataclass(frozen=True, slots=True)
class ConformanceCase:
    name: str
    passed: bool
    detail: str = ""


@dataclass(frozen=True, slots=True)
class ConformanceReport:
    adapter_id: str
    contract_version: str
    cases: tuple[ConformanceCase, ...]

    @property
    def pass_rate(self) -> float:
        return (
            sum(item.passed for item in self.cases) / len(self.cases)
            if self.cases
            else 0.0
        )


def _attempt[T](name: str, fn: Callable[[], T]) -> tuple[T | None, ConformanceCase]:
    try:
        return fn(), ConformanceCase(name, True)
    except Exception as exc:
        # A conformance report must never copy a repository path or source text.
        return None, ConformanceCase(name, False, type(exc).__name__)


def _check(name: str, fn: Callable[[], None], *, ready: bool = True) -> ConformanceCase:
    if not ready:
        return ConformanceCase(name, False, "prerequisite_failed")
    _, result = _attempt(name, fn)
    return result


def _assert(value: bool) -> None:
    if not value:
        raise ValueError("conformance_check_failed")


def _relative(path: str) -> bool:
    value = PurePosixPath(path)
    return (
        bool(path)
        and not value.is_absolute()
        and not re.match(r"^[A-Za-z]:", path)
        and "\\" not in path
        and all(part not in ("", ".", "..") for part in path.split("/"))
    )


def _valid_detection(report: DetectionReport, manifest: SourceManifest) -> None:
    paths = {item.relative_path for item in manifest.files}
    _assert(
        tuple(sorted(report.technologies, key=lambda item: item.technology))
        == report.technologies
    )
    _assert(
        tuple(sorted(report.application_entrypoints)) == report.application_entrypoints
    )
    for item in report.technologies:
        _assert(bool(item.evidence))
        _assert(
            all(
                ref.relative_path in paths and RULE_ID.fullmatch(ref.rule_id)
                for ref in item.evidence
            )
        )


def _valid_parse(parsed: ParseResult, manifest: SourceManifest) -> None:
    hashes = {item.relative_path: item.content_hash for item in manifest.files}
    _assert(
        tuple(sorted(parsed.units, key=lambda unit: unit.relative_path)) == parsed.units
    )
    for unit in parsed.units:
        _assert(unit.relative_path in hashes)
        _assert(unit.content_hash == hashes[unit.relative_path])
        _assert(bool(unit.representation_kind))
        _assert(not isinstance(unit.representation, (str, bytes, bytearray)))
    _assert(
        tuple(
            sorted(
                parsed.symbol_index,
                key=lambda ref: (ref.qualified_name, ref.relative_path),
            )
        )
        == parsed.symbol_index
    )
    _assert(
        all(
            item.relative_path is None or item.relative_path in hashes
            for item in parsed.diagnostics
        )
    )


def _parse_signature(parsed: ParseResult) -> tuple[object, ...]:
    """Compare adapter-neutral metadata; AST/CST equality is adapter-specific."""
    return (
        tuple(
            (
                unit.relative_path,
                unit.language,
                unit.representation_kind,
                unit.content_hash,
            )
            for unit in parsed.units
        ),
        parsed.symbol_index,
        parsed.diagnostics,
    )


def _valid_result(
    result: AdapterResult, context: AdapterContext, descriptor: AdapterDescriptor
) -> None:
    facts = result.facts
    _assert(facts.repository_id == context.repository_id)
    _assert(facts.snapshot_id == context.snapshot_id)
    validate_adapter_fact_batch(facts)
    _assert(tuple(sorted(facts.entities, key=lambda item: item.id)) == facts.entities)
    _assert(tuple(sorted(facts.edges, key=lambda item: item.id)) == facts.edges)
    _assert(
        tuple(sorted(result.capabilities, key=lambda item: item.name))
        == result.capabilities
    )
    _assert({item.name for item in result.capabilities} == set(descriptor.capabilities))
    _assert(
        all(
            item.relative_path is None or _relative(item.relative_path)
            for item in result.diagnostics
        )
    )


def run_language_conformance(
    adapter: LanguageAdapter,
    manifest: SourceManifest,
    config: SourceScanConfig,
    context: AdapterContext,
    *,
    no_execution_marker: Callable[[], bool],
) -> ConformanceReport:
    """Check detection, parsing, facts and isolation through the public contract."""
    descriptor = adapter.descriptor
    detection, detected = _attempt(
        "detect_entrypoint", lambda: adapter.detect(manifest)
    )
    parsed, parsed_case = _attempt(
        "parse_entrypoint", lambda: adapter.parse(manifest, config)
    )
    extracted, extracted_case = (
        _attempt(
            "extract_entrypoint",
            lambda: adapter.extract(context, parsed),
        )
        if parsed is not None
        else (None, ConformanceCase("extract_entrypoint", False, "prerequisite_failed"))
    )
    resolved, resolved_case = (
        _attempt(
            "resolve_entrypoint",
            lambda: adapter.resolve(context, parsed, extracted.facts),
        )
        if parsed is not None and extracted is not None
        else (None, ConformanceCase("resolve_entrypoint", False, "prerequisite_failed"))
    )
    cases = (
        _check(
            "contract_version",
            lambda: _assert(descriptor.contract_version == CONTRACT_VERSION),
        ),
        detected,
        _check(
            "detection_evidence_order",
            lambda: _valid_detection(detection, manifest),
            ready=detection is not None,
        ),
        _check(
            "detection_deterministic",
            lambda: _assert(detection == adapter.detect(manifest)),
            ready=detection is not None,
        ),
        parsed_case,
        _check(
            "parsed_units_boundary_order",
            lambda: _valid_parse(parsed, manifest),
            ready=parsed is not None,
        ),
        _check(
            "parse_deterministic",
            lambda: _assert(
                _parse_signature(parsed)
                == _parse_signature(adapter.parse(manifest, config))
            ),
            ready=parsed is not None,
        ),
        extracted_case,
        _check(
            "extract_fact_batch",
            lambda: _valid_result(extracted, context, descriptor),
            ready=extracted is not None,
        ),
        _check(
            "extract_deterministic",
            lambda: _assert(extracted == adapter.extract(context, parsed)),
            ready=extracted is not None and parsed is not None,
        ),
        resolved_case,
        _check(
            "resolve_fact_batch",
            lambda: _valid_result(resolved, context, descriptor),
            ready=resolved is not None,
        ),
        _check(
            "resolve_deterministic",
            lambda: _assert(
                resolved == adapter.resolve(context, parsed, extracted.facts)
            ),
            ready=resolved is not None and parsed is not None and extracted is not None,
        ),
        _check("no_source_execution", lambda: _assert(not no_execution_marker())),
    )
    return ConformanceReport(descriptor.adapter_id, descriptor.contract_version, cases)


def run_framework_conformance(
    adapter: FrameworkAdapter,
    manifest: SourceManifest,
    parsed: ParseResult,
    context: AdapterContext,
    base: FactBatch,
    *,
    no_execution_marker: Callable[[], bool],
) -> ConformanceReport:
    """Apply the same fact/evidence/determinism checks to a deep adapter."""
    descriptor = adapter.descriptor
    detection, detected = _attempt(
        "detect_entrypoint", lambda: adapter.detect(manifest, parsed)
    )
    extracted, extracted_case = _attempt(
        "extract_entrypoint", lambda: adapter.extract(context, parsed, base)
    )
    resolved, resolved_case = (
        _attempt(
            "resolve_entrypoint",
            lambda: adapter.resolve(context, parsed, extracted.facts),
        )
        if extracted is not None
        else (None, ConformanceCase("resolve_entrypoint", False, "prerequisite_failed"))
    )
    cases = (
        _check(
            "contract_version",
            lambda: _assert(descriptor.contract_version == CONTRACT_VERSION),
        ),
        detected,
        _check(
            "detection_evidence_order",
            lambda: _valid_detection(detection, manifest),
            ready=detection is not None,
        ),
        _check(
            "detection_deterministic",
            lambda: _assert(detection == adapter.detect(manifest, parsed)),
            ready=detection is not None,
        ),
        extracted_case,
        _check(
            "extract_fact_batch",
            lambda: _valid_result(extracted, context, descriptor),
            ready=extracted is not None,
        ),
        _check(
            "extract_deterministic",
            lambda: _assert(extracted == adapter.extract(context, parsed, base)),
            ready=extracted is not None,
        ),
        resolved_case,
        _check(
            "resolve_fact_batch",
            lambda: _valid_result(resolved, context, descriptor),
            ready=resolved is not None,
        ),
        _check(
            "resolve_deterministic",
            lambda: _assert(
                resolved == adapter.resolve(context, parsed, extracted.facts)
            ),
            ready=resolved is not None and extracted is not None,
        ),
        _check("no_source_execution", lambda: _assert(not no_execution_marker())),
    )
    return ConformanceReport(descriptor.adapter_id, descriptor.contract_version, cases)
