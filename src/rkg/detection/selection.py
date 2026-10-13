"""Adapter-neutral detection aggregation and deterministic registry selection."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from rkg.adapters import (
    AdapterDescriptor,
    AdapterKind,
    AdapterRegistry,
    DetectionEvidence,
    DetectionReport,
    FrameworkAdapter,
    LanguageAdapter,
    ParseResult,
    TechnologyDetection,
)
from rkg.adapters.registry import _matches_version
from rkg.detection.contracts import ApplicationCandidate, FrameworkObservation
from rkg.ingestion import SourceManifest


class DetectionState(StrEnum):
    SUPPORTED_PATTERNS = "supported_patterns"
    DETECTED_ONLY = "detected_only"
    VERSION_UNVERIFIED = "version_unverified"
    UNSUPPORTED_VERSION = "unsupported_version"


@dataclass(frozen=True, slots=True)
class TechnologySupport:
    technology: str
    version: str | None
    state: DetectionState
    evidence: tuple[DetectionEvidence, ...]
    adapter_ids: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SelectionResult:
    status: str
    technologies: tuple[TechnologySupport, ...]
    language_adapters: tuple[LanguageAdapter, ...]
    deep_adapters: tuple[FrameworkAdapter, ...]
    application_candidates: tuple[ApplicationCandidate, ...]
    selected_application: ApplicationCandidate | None = None
    error_code: str | None = None


class FrameworkDetector(Protocol):
    def detect(
        self, manifest: SourceManifest, parsed: ParseResult
    ) -> FrameworkObservation: ...


def _aggregate(reports: tuple[DetectionReport, ...]) -> tuple[TechnologyDetection, ...]:
    entries: dict[str, list[TechnologyDetection]] = {}
    for report in reports:
        for item in report.technologies:
            if item.evidence:
                entries.setdefault(item.technology, []).append(item)
    merged = []
    for name, values in sorted(entries.items()):
        versions = {item.version for item in values if item.version is not None}
        version = next(iter(versions)) if len(versions) == 1 else None
        evidence = tuple(
            sorted(
                {ref for item in values for ref in item.evidence},
                key=lambda ref: (ref.relative_path, ref.rule_id),
            )
        )
        merged.append(TechnologyDetection(name, version, evidence))
    return tuple(merged)


def _unmatched_state(
    candidates: tuple[AdapterDescriptor, ...],
    detections: tuple[TechnologyDetection, ...],
) -> DetectionState:
    versions = {item.technology: item.version for item in detections}
    maybe_compatible = False
    for candidate in candidates:
        unknown = False
        mismatched = False
        for constraint in candidate.technology_constraints:
            version = versions.get(constraint.technology)
            if version is None:
                unknown = True
            elif not _matches_version(version, constraint.version_spec):
                mismatched = True
        if unknown and not mismatched:
            maybe_compatible = True
    return (
        DetectionState.VERSION_UNVERIFIED
        if maybe_compatible
        else DetectionState.UNSUPPORTED_VERSION
    )


def select_adapters(
    manifest: SourceManifest,
    parsed: ParseResult,
    language_adapter: LanguageAdapter,
    registry: AdapterRegistry,
    detectors: tuple[FrameworkDetector, ...] = (),
    *,
    application_override: str | None = None,
    prior_application: str | None = None,
    adapter_overrides: tuple[str, ...] | None = None,
) -> SelectionResult:
    """Select every compatible adapter; application choice is a separate concern.

    Detector implementations own language/framework syntax. This coordinator only
    combines evidence and compares generic descriptor constraints and capabilities.
    """
    observations = tuple(detector.detect(manifest, parsed) for detector in detectors)
    language_report = language_adapter.detect(manifest)
    detections = _aggregate(
        (language_report,) + tuple(item.report for item in observations)
    )
    observed = {
        item.technology
        for observation in observations
        for item in observation.report.technologies
        if item.evidence
    }
    language_adapters = registry.select_language(
        language_adapter.descriptor.language, detections
    )
    descriptors = tuple(registry.inventory().values())
    selected: dict[tuple[str, str], FrameworkAdapter] = {}
    supports = []
    for detected in detections:
        language_matches = tuple(
            item
            for item in language_adapters
            if item.descriptor.language == detected.technology
        )
        candidates = tuple(
            item
            for item in descriptors
            if item.kind != AdapterKind.LANGUAGE
            and item.language == language_adapter.descriptor.language
            and item.framework == detected.technology
        )
        compatible = tuple(
            item
            for item in registry.select_deep(
                language_adapter.descriptor.language, detections
            )
            if item.descriptor.framework == detected.technology
        )
        if language_matches:
            state = DetectionState.SUPPORTED_PATTERNS
        elif detected.technology not in observed:
            state = DetectionState.DETECTED_ONLY
        elif compatible:
            for adapter in compatible:
                key = (
                    adapter.descriptor.adapter_id,
                    adapter.descriptor.adapter_version,
                )
                selected[key] = adapter
            # An adapter without a reviewed registry entry still extracts.
            # It must not publish the deep-supported claim.
            state = (
                DetectionState.VERSION_UNVERIFIED
                if any(
                    constraint.version_spec
                    and next(
                        (
                            item.version
                            for item in detections
                            if item.technology == constraint.technology
                        ),
                        None,
                    )
                    is None
                    for adapter in compatible
                    for constraint in adapter.descriptor.technology_constraints
                )
                else DetectionState.SUPPORTED_PATTERNS
                if any(
                    getattr(adapter, "reviewed_deep_support", True)
                    for adapter in compatible
                )
                else DetectionState.DETECTED_ONLY
            )
        elif candidates and any(item.technology_constraints for item in candidates):
            state = _unmatched_state(candidates, detections)
        else:
            state = DetectionState.DETECTED_ONLY
        supports.append(
            TechnologySupport(
                detected.technology,
                detected.version,
                state,
                detected.evidence,
                tuple(
                    item.descriptor.adapter_id for item in language_matches + compatible
                )
                if state
                in (
                    DetectionState.SUPPORTED_PATTERNS,
                    DetectionState.VERSION_UNVERIFIED,
                )
                else (),
                tuple(
                    sorted(
                        {
                            capability
                            for item in language_matches + compatible
                            for capability in item.descriptor.capabilities
                        }
                    )
                )
                if state
                in (
                    DetectionState.SUPPORTED_PATTERNS,
                    DetectionState.VERSION_UNVERIFIED,
                )
                else (),
            )
        )
    available = tuple(selected[key] for key in sorted(selected))
    candidates = tuple(
        sorted(
            {candidate for item in observations for candidate in item.applications},
            key=lambda item: (item.reference, item.relative_path, item.line),
        )
    )

    def result(
        status: str,
        deep: tuple[FrameworkAdapter, ...],
        application: ApplicationCandidate | None = None,
        error: str | None = None,
    ) -> SelectionResult:
        return SelectionResult(
            status,
            tuple(supports),
            language_adapters,
            deep,
            candidates,
            application,
            error,
        )

    if adapter_overrides is not None:
        chosen = set(adapter_overrides)
        if len(chosen) != len(adapter_overrides) or not chosen.issubset(
            {item.descriptor.adapter_id for item in available}
        ):
            return result("invalid_override", (), error="adapter_override_invalid")
        available = tuple(
            item for item in available if item.descriptor.adapter_id in chosen
        )

    requested = application_override or prior_application
    matches = [item for item in candidates if item.reference == requested]
    if requested and len(matches) != 1:
        return result("invalid_override", available, error="app_override_invalid")
    selected_application = matches[0] if matches else None
    requires_entrypoint = any(
        getattr(adapter, "entrypoint_required", False) for adapter in available
    )
    if requires_entrypoint and selected_application is None:
        if len(candidates) > 1:
            return result(
                "app_selection_required", available, error="app_selection_required"
            )
        if not candidates:
            return result("app_unresolved", available, error="app_unresolved")
    if selected_application is None and len(candidates) == 1:
        selected_application = candidates[0]
    return result("ready", available, selected_application)
