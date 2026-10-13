"""Deterministic selection by descriptor and static detection evidence."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from rkg.adapters.contracts import (
    CONTRACT_VERSION,
    AdapterDescriptor,
    AdapterKind,
    FrameworkAdapter,
    LanguageAdapter,
    TechnologyConstraint,
    TechnologyDetection,
)

type AnyAdapter = LanguageAdapter | FrameworkAdapter


@dataclass(frozen=True, slots=True)
class RegistryIssue:
    adapter_id: str
    code: str


@dataclass(frozen=True, slots=True)
class Registration:
    accepted: bool
    issue: RegistryIssue | None = None


def _version(value: str) -> tuple[int, int, int] | None:
    parts = value.split(".")
    if not 1 <= len(parts) <= 3 or any(not part.isdigit() for part in parts):
        return None
    padded = [int(part) for part in (parts + ["0"] * (3 - len(parts)))]
    return padded[0], padded[1], padded[2]


def _matches_version(value: str | None, spec: str) -> bool:
    if not spec:
        return True
    actual = _version(value) if value is not None else None
    if actual is None:
        return False
    for part in spec.split(","):
        operator = next(
            op for op in (">=", "<=", "==", ">", "<") if part.startswith(op)
        )
        target = _version(part[len(operator) :])
        if target is None:
            return False
        if not {
            ">=": actual >= target,
            "<=": actual <= target,
            "==": actual == target,
            ">": actual > target,
            "<": actual < target,
        }[operator]:
            return False
    return True


def _detected(
    technology: str, detections: tuple[TechnologyDetection, ...]
) -> TechnologyDetection | None:
    return next(
        (
            item
            for item in detections
            if item.technology == technology and item.evidence
        ),
        None,
    )


def _constraints_match(
    constraints: tuple[TechnologyConstraint, ...],
    detections: tuple[TechnologyDetection, ...],
    *,
    allow_unverified: bool = False,
) -> bool:
    return all(
        (match := _detected(item.technology, detections)) is not None
        and (
            (allow_unverified and match.version is None)
            or _matches_version(match.version, item.version_spec)
        )
        for item in constraints
    )


class AdapterRegistry:
    def __init__(self, *, contract_version: str = CONTRACT_VERSION) -> None:
        self.contract_version = contract_version
        self._adapters: dict[tuple[str, str], AnyAdapter] = {}

    def register(self, adapter: AnyAdapter) -> Registration:
        descriptor = getattr(adapter, "descriptor", None)
        if not isinstance(descriptor, AdapterDescriptor):
            return Registration(
                False, RegistryIssue("unknown", "adapter_descriptor_invalid")
            )
        if descriptor.contract_version != self.contract_version:
            return Registration(
                False,
                RegistryIssue(descriptor.adapter_id, "adapter_contract_incompatible"),
            )
        expected = (
            LanguageAdapter
            if descriptor.kind == AdapterKind.LANGUAGE
            else FrameworkAdapter
        )
        if not isinstance(adapter, expected):
            return Registration(
                False, RegistryIssue(descriptor.adapter_id, "adapter_interface_invalid")
            )
        key = (descriptor.adapter_id, descriptor.adapter_version)
        if key in self._adapters:
            return Registration(
                False, RegistryIssue(descriptor.adapter_id, "adapter_duplicate")
            )
        self._adapters[key] = adapter
        return Registration(True)

    def select_language(
        self,
        language: str,
        detections: tuple[TechnologyDetection, ...],
        *,
        capabilities: frozenset[str] = frozenset(),
    ) -> tuple[LanguageAdapter, ...]:
        return tuple(
            adapter
            for adapter in self._ordered()
            if adapter.descriptor.kind == AdapterKind.LANGUAGE
            and adapter.descriptor.language == language
            and _detected(language, detections) is not None
            and capabilities.issubset(adapter.descriptor.capabilities)
            and _constraints_match(
                adapter.descriptor.technology_constraints, detections
            )
        )

    def select_deep(
        self,
        language: str,
        detections: tuple[TechnologyDetection, ...],
        *,
        capabilities: frozenset[str] = frozenset(),
    ) -> tuple[FrameworkAdapter, ...]:
        return tuple(
            adapter
            for adapter in self._ordered()
            if adapter.descriptor.kind != AdapterKind.LANGUAGE
            and adapter.descriptor.language == language
            and adapter.descriptor.framework is not None
            and _detected(adapter.descriptor.framework, detections) is not None
            and capabilities.issubset(adapter.descriptor.capabilities)
            and _constraints_match(
                adapter.descriptor.technology_constraints,
                detections,
                allow_unverified=getattr(adapter, "allow_unverified_versions", False),
            )
        )

    def inventory(self) -> Mapping[tuple[str, str], AdapterDescriptor]:
        return {key: value.descriptor for key, value in sorted(self._adapters.items())}

    def _ordered(self) -> tuple[AnyAdapter, ...]:
        return tuple(self._adapters[key] for key in sorted(self._adapters))
