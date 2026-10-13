"""Versioned, transport-neutral analyzer adapter boundary."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable

from rkg.domain import FactBatch, SourceScanConfig
from rkg.ingestion import SourceManifest

CONTRACT_VERSION = "rkg.adapter/v2"
_IDENTIFIER = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_VERSION = re.compile(r"^[0-9]+(?:\.[0-9]+){1,2}$")


class AdapterKind(StrEnum):
    LANGUAGE = "language"
    FRAMEWORK = "framework"
    DATA_ACCESS = "data_access"
    MESSAGING = "messaging"
    CONFIGURATION = "configuration"
    EXTERNAL_DEPENDENCY = "external_dependency"


class SupportState(StrEnum):
    SUPPORTED = "supported"
    DETECTED_ONLY = "detected_only"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True, slots=True)
class TechnologyConstraint:
    technology: str
    version_spec: str = ""

    def __post_init__(self) -> None:
        if not _IDENTIFIER.fullmatch(self.technology):
            raise ValueError("invalid technology identifier")
        if self.version_spec and not all(
            re.fullmatch(r"(>=|<=|==|>|<)[0-9]+(?:\.[0-9]+){1,2}", part)
            for part in self.version_spec.split(",")
        ):
            raise ValueError("invalid numeric version constraint")


@dataclass(frozen=True, slots=True)
class AdapterDescriptor:
    adapter_id: str
    adapter_version: str
    contract_version: str
    kind: AdapterKind
    language: str
    grammar_or_target: str
    file_patterns: tuple[str, ...]
    ignore_patterns: tuple[str, ...]
    capabilities: tuple[str, ...]
    framework: str | None = None
    technology_constraints: tuple[TechnologyConstraint, ...] = ()

    def __post_init__(self) -> None:
        if not _IDENTIFIER.fullmatch(self.adapter_id):
            raise ValueError("invalid adapter ID")
        if not _VERSION.fullmatch(self.adapter_version):
            raise ValueError("invalid adapter version")
        if not _IDENTIFIER.fullmatch(self.language):
            raise ValueError("invalid language identifier")
        if self.framework is not None and not _IDENTIFIER.fullmatch(self.framework):
            raise ValueError("invalid framework identifier")
        if not self.grammar_or_target.strip():
            raise ValueError("grammar or target is required")
        if not self.file_patterns or any(not pattern for pattern in self.file_patterns):
            raise ValueError("at least one file pattern is required")
        if (
            not self.capabilities
            or len(set(self.capabilities)) != len(self.capabilities)
            or any(not _IDENTIFIER.fullmatch(name) for name in self.capabilities)
        ):
            raise ValueError("capabilities must be unique identifiers")
        if self.kind == AdapterKind.LANGUAGE and self.framework is not None:
            raise ValueError("language adapter cannot declare a framework")
        if self.kind != AdapterKind.LANGUAGE and self.framework is None:
            raise ValueError("deep adapter must declare a framework")


@dataclass(frozen=True, slots=True)
class AdapterContext:
    repository_id: str
    snapshot_id: str
    job_id: str
    scan_config: SourceScanConfig


@dataclass(frozen=True, slots=True)
class DetectionEvidence:
    relative_path: str
    rule_id: str


@dataclass(frozen=True, slots=True)
class TechnologyDetection:
    technology: str
    version: str | None
    evidence: tuple[DetectionEvidence, ...]


@dataclass(frozen=True, slots=True)
class DetectionReport:
    technologies: tuple[TechnologyDetection, ...] = ()
    application_entrypoints: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ParsedUnit:
    relative_path: str
    language: str
    representation_kind: str
    content_hash: str
    representation: object


@dataclass(frozen=True, slots=True)
class SymbolRef:
    qualified_name: str
    relative_path: str
    owner: str | None = None


@dataclass(frozen=True, slots=True)
class ParseResult:
    units: tuple[ParsedUnit, ...]
    symbol_index: tuple[SymbolRef, ...] = ()
    diagnostics: tuple[AdapterDiagnostic, ...] = ()


@dataclass(frozen=True, slots=True)
class AdapterDiagnostic:
    code: str
    relative_path: str | None = None
    line: int | None = None


@dataclass(frozen=True, slots=True)
class Capability:
    name: str
    support_state: SupportState


@dataclass(frozen=True, slots=True)
class AdapterResult:
    facts: FactBatch
    capabilities: tuple[Capability, ...]
    diagnostics: tuple[AdapterDiagnostic, ...] = ()


@runtime_checkable
class LanguageAdapter(Protocol):
    @property
    def descriptor(self) -> AdapterDescriptor: ...

    def detect(self, manifest: SourceManifest) -> DetectionReport: ...

    def parse(
        self, manifest: SourceManifest, config: SourceScanConfig
    ) -> ParseResult: ...

    def extract(
        self, context: AdapterContext, parsed: ParseResult
    ) -> AdapterResult: ...

    def resolve(
        self, context: AdapterContext, parsed: ParseResult, candidate: FactBatch
    ) -> AdapterResult: ...


@runtime_checkable
class FrameworkAdapter(Protocol):
    @property
    def descriptor(self) -> AdapterDescriptor: ...

    def detect(
        self, manifest: SourceManifest, parsed: ParseResult
    ) -> DetectionReport: ...

    def extract(
        self, context: AdapterContext, parsed: ParseResult, base: FactBatch
    ) -> AdapterResult: ...

    def resolve(
        self, context: AdapterContext, parsed: ParseResult, candidate: FactBatch
    ) -> AdapterResult: ...
