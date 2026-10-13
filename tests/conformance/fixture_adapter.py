"""Test-only adapters for proving the public extension boundary."""

from __future__ import annotations

from dataclasses import dataclass

from rkg.adapters import (
    CONTRACT_VERSION,
    AdapterContext,
    AdapterDescriptor,
    AdapterDiagnostic,
    AdapterKind,
    AdapterResult,
    Capability,
    DetectionEvidence,
    DetectionReport,
    ParsedUnit,
    ParseResult,
    SupportState,
    SymbolRef,
    TechnologyConstraint,
    TechnologyDetection,
)
from rkg.domain import (
    Edge,
    EdgeType,
    Entity,
    EntityType,
    Evidence,
    FactBatch,
    SourceScanConfig,
    edge_id,
    endpoint_id,
    evidence_id,
    source_entity_id,
)
from rkg.ingestion import SourceManifest

STRUCTURE_RULE = "RKG.fixture.structure.v1"
ROUTE_RULE = "RKG.fixture.route.v1"


@dataclass(frozen=True, slots=True)
class Statement:
    kind: str
    fields: tuple[str, ...]
    line: int


def _statements(unit: ParsedUnit) -> tuple[Statement, ...]:
    if not isinstance(unit.representation, tuple):
        raise ValueError("invalid structured fixture representation")
    return unit.representation


def _evidence(context: AdapterContext, path: str, line: int, rule: str) -> Evidence:
    return Evidence(
        evidence_id(context.snapshot_id, path, line, line, rule),
        context.snapshot_id,
        path,
        line,
        line,
        rule,
    )


def _capabilities(*names: str) -> tuple[Capability, ...]:
    return tuple(Capability(name, SupportState.SUPPORTED) for name in sorted(names))


class SyntheticLanguageAdapter:
    descriptor = AdapterDescriptor(
        "rkg.conformance.fixture.language",
        "1.0",
        CONTRACT_VERSION,
        AdapterKind.LANGUAGE,
        "synthetic",
        "synthetic-lines/v1",
        ("*.synthetic",),
        (),
        ("diagnostic", "structure"),
    )

    def detect(self, manifest: SourceManifest) -> DetectionReport:
        references = tuple(
            DetectionEvidence(item.relative_path, STRUCTURE_RULE)
            for item in manifest.files
            if item.relative_path.endswith(".synthetic")
        )
        return (
            DetectionReport((TechnologyDetection("synthetic", "1.0", references),))
            if references
            else DetectionReport()
        )

    def parse(self, manifest: SourceManifest, config: SourceScanConfig) -> ParseResult:
        del config
        units = []
        symbols = []
        diagnostics = []
        for item in manifest.files:
            if not item.relative_path.endswith(".synthetic"):
                continue
            statements = []
            for line, raw in enumerate(item.content.decode("utf-8").splitlines(), 1):
                parts = tuple(raw.split())
                if parts and (
                    (parts[0] in ("unit", "callable") and len(parts) == 2)
                    or (parts[0] == "route" and len(parts) == 4)
                ):
                    statements.append(Statement(parts[0], parts[1:], line))
                    if parts[0] == "callable":
                        symbols.append(SymbolRef(parts[1], item.relative_path))
                elif parts:
                    diagnostics.append(
                        AdapterDiagnostic(
                            "fixture_syntax_ignored", item.relative_path, line
                        )
                    )
            units.append(
                ParsedUnit(
                    item.relative_path,
                    "synthetic",
                    "statement-tuple/v1",
                    item.content_hash,
                    tuple(statements),
                )
            )
        return ParseResult(
            tuple(sorted(units, key=lambda unit: unit.relative_path)),
            tuple(
                sorted(symbols, key=lambda ref: (ref.qualified_name, ref.relative_path))
            ),
            tuple(diagnostics),
        )

    def extract(self, context: AdapterContext, parsed: ParseResult) -> AdapterResult:
        entities = []
        edges = []
        evidence = []
        for unit in parsed.units:
            path = unit.relative_path
            source_id = source_entity_id(
                context.repository_id, path, EntityType.SOURCE_UNIT, path
            )
            entities.append(
                Entity(
                    source_id,
                    context.repository_id,
                    context.snapshot_id,
                    EntityType.SOURCE_UNIT,
                    path,
                    path,
                    path,
                    1,
                    1,
                )
            )
            for statement in _statements(unit):
                if statement.kind != "callable":
                    continue
                name = statement.fields[0]
                target_id = source_entity_id(
                    context.repository_id, path, EntityType.CALLABLE, name
                )
                entities.append(
                    Entity(
                        target_id,
                        context.repository_id,
                        context.snapshot_id,
                        EntityType.CALLABLE,
                        name.rsplit(".", 1)[-1],
                        name,
                        path,
                        statement.line,
                        statement.line,
                        "synthetic_callable",
                    )
                )
                ref = _evidence(context, path, statement.line, STRUCTURE_RULE)
                evidence.append(ref)
                edges.append(
                    Edge(
                        edge_id(
                            context.snapshot_id, EdgeType.CONTAINS, source_id, target_id
                        ),
                        context.snapshot_id,
                        EdgeType.CONTAINS,
                        source_id,
                        target_id,
                        STRUCTURE_RULE,
                        (ref.id,),
                    )
                )
        facts = FactBatch(
            context.repository_id,
            context.snapshot_id,
            tuple(sorted(entities, key=lambda entity: entity.id)),
            tuple(sorted(edges, key=lambda edge: edge.id)),
            tuple(sorted(evidence, key=lambda ref: ref.id)),
        )
        return AdapterResult(facts, _capabilities("diagnostic", "structure"))

    def resolve(
        self, context: AdapterContext, parsed: ParseResult, candidate: FactBatch
    ) -> AdapterResult:
        del context, parsed
        return AdapterResult(candidate, _capabilities("diagnostic", "structure"))


class SyntheticFrameworkAdapter:
    descriptor = AdapterDescriptor(
        "rkg.conformance.fixture.framework",
        "1.0",
        CONTRACT_VERSION,
        AdapterKind.FRAMEWORK,
        "synthetic",
        "synthetic-routes/v1",
        ("*.synthetic",),
        (),
        ("route",),
        "synthetic-web",
        (TechnologyConstraint("synthetic", ">=1.0"),),
    )

    def detect(self, manifest: SourceManifest, parsed: ParseResult) -> DetectionReport:
        del manifest
        paths = tuple(
            sorted(
                {
                    unit.relative_path
                    for unit in parsed.units
                    if any(statement.kind == "route" for statement in _statements(unit))
                }
            )
        )
        references = tuple(DetectionEvidence(path, ROUTE_RULE) for path in paths)
        return (
            DetectionReport(
                (TechnologyDetection("synthetic-web", "1.0", references),), paths
            )
            if paths
            else DetectionReport()
        )

    def extract(
        self, context: AdapterContext, parsed: ParseResult, base: FactBatch
    ) -> AdapterResult:
        entities = list(base.entities)
        edges = list(base.edges)
        evidence = list(base.evidence)
        known = {item.id for item in entities}
        for unit in parsed.units:
            path = unit.relative_path
            for statement in _statements(unit):
                if statement.kind != "route":
                    continue
                method, route, handler = statement.fields
                handler_id = source_entity_id(
                    context.repository_id, path, EntityType.CALLABLE, handler
                )
                if handler_id not in known:
                    continue
                target_id = endpoint_id(
                    context.repository_id,
                    path,
                    handler,
                    method,
                    route,
                    (path, str(statement.line)),
                )
                entities.append(
                    Entity(
                        target_id,
                        context.repository_id,
                        context.snapshot_id,
                        EntityType.ENDPOINT,
                        route,
                        handler,
                        path,
                        statement.line,
                        statement.line,
                        framework_kind="synthetic_route",
                        attributes=(("method", method), ("route", route)),
                    )
                )
                ref = _evidence(context, path, statement.line, ROUTE_RULE)
                evidence.append(ref)
                for kind, source, target in (
                    (EdgeType.EXPOSES, context.repository_id, target_id),
                    (EdgeType.HANDLED_BY, target_id, handler_id),
                ):
                    edges.append(
                        Edge(
                            edge_id(context.snapshot_id, kind, source, target),
                            context.snapshot_id,
                            kind,
                            source,
                            target,
                            ROUTE_RULE,
                            (ref.id,),
                        )
                    )
        facts = FactBatch(
            context.repository_id,
            context.snapshot_id,
            tuple(sorted(entities, key=lambda entity: entity.id)),
            tuple(sorted(edges, key=lambda edge: edge.id)),
            tuple(sorted(evidence, key=lambda ref: ref.id)),
        )
        return AdapterResult(facts, _capabilities("route"))

    def resolve(
        self, context: AdapterContext, parsed: ParseResult, candidate: FactBatch
    ) -> AdapterResult:
        del context, parsed
        return AdapterResult(candidate, _capabilities("route"))
