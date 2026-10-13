"""Canonical, transport-neutral DTOs shared by analyzer and graph services."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | tuple[JsonScalar, ...]


class EntityType(StrEnum):
    SOURCE_UNIT = "SourceUnit"
    DIRECTORY = "Directory"
    NAMESPACE = "Namespace"  # Legacy snapshots only.
    TYPE = "Type"
    CALLABLE = "Callable"
    ENDPOINT = "Endpoint"
    DATA_RESOURCE = "DataResource"
    MESSAGE_CHANNEL = "MessageChannel"
    CONFIGURATION = "Configuration"
    EXTERNAL_DEPENDENCY = "ExternalDependency"


class EdgeType(StrEnum):
    CONTAINS = "contains"
    IMPORTS = "imports"
    EXPOSES = "exposes"
    HANDLED_BY = "handled_by"
    CALLS = "calls"
    IMPLEMENTS = "implements"
    INHERITS_FROM = "inherits_from"
    MAPS_TO = "maps_to"
    READS = "reads"
    WRITES = "writes"
    PUBLISHES = "publishes"
    CONSUMES = "consumes"
    DEPENDS_ON = "depends_on"


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class Entity:
    id: str
    repository_id: str
    snapshot_id: str
    type: EntityType
    name: str
    qualified_name: str
    file_path: str | None = None
    start_line: int | None = None
    end_line: int | None = None
    language_kind: str | None = None
    framework_kind: str | None = None
    # Tuples avoid mutable facts crossing the adapter -> validator boundary.
    attributes: tuple[tuple[str, JsonValue], ...] = ()


@dataclass(frozen=True, slots=True)
class Evidence:
    id: str
    snapshot_id: str
    file_path: str
    start_line: int
    end_line: int
    rule: str


@dataclass(frozen=True, slots=True)
class Edge:
    id: str
    snapshot_id: str
    type: EdgeType
    source_id: str
    target_id: str
    rule: str
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Diagnostic:
    id: str
    job_id: str
    severity: Severity
    code: str
    message: str
    snapshot_id: str | None = None
    file_path: str | None = None
    line: int | None = None


@dataclass(frozen=True, slots=True)
class SourceScanConfig:
    """Effective scan limits/patterns; host roots stay in server-owned config."""

    max_files: int
    max_file_bytes: int
    include_patterns: tuple[str, ...] = ()
    ignore_patterns: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.max_files < 1 or self.max_file_bytes < 1:
            raise ValueError("scan limits must be positive")


@dataclass(frozen=True, slots=True)
class ContextBudget:
    depth: int | None
    max_nodes: int | None
    max_edges: int | None
    max_chars: int | None

    def __post_init__(self) -> None:
        if self.depth is not None and not (0 <= self.depth <= 6):
            raise ValueError("context depth must be between 0 and 6")
        if (self.max_nodes is not None and not 1 <= self.max_nodes <= 200) or (
            self.max_edges is not None and not 1 <= self.max_edges <= 400
        ):
            raise ValueError("context node/edge budget outside API limits")
        if self.max_chars is not None and not (2000 <= self.max_chars <= 50000):
            raise ValueError("context character budget outside API limits")


@dataclass(frozen=True, slots=True)
class FactBatch:
    repository_id: str
    snapshot_id: str
    entities: tuple[Entity, ...] = ()
    edges: tuple[Edge, ...] = ()
    evidence: tuple[Evidence, ...] = ()
    diagnostics: tuple[Diagnostic, ...] = ()


@dataclass(frozen=True, slots=True)
class ContextPackage:
    """A completed bounded context; traversal/truncation belongs to T-014."""

    schema_version: str
    repository_id: str
    snapshot_id: str
    root_id: str
    nodes: tuple[Entity, ...]
    edges: tuple[Edge, ...]
    evidence: tuple[Evidence, ...]
    diagnostic_summary: tuple[tuple[str, int], ...] = ()
    truncated: bool = False
    truncation_reasons: tuple[str, ...] = ()
    budget: ContextBudget = field(
        default_factory=lambda: ContextBudget(4, 50, 100, 20000)
    )
