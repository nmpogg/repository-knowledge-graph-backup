"""Static JPA/Hibernate data-access extraction over parsed Java units.

DataResource identity is relational:{schema}.{table}. Runtime/native SQL without
a literal table name never becomes a guessed edge.
"""

from __future__ import annotations

from rkg.adapters.contracts import (
    CONTRACT_VERSION,
    AdapterContext,
    AdapterDescriptor,
    AdapterDiagnostic,
    AdapterKind,
    AdapterResult,
    Capability,
    DetectionEvidence,
    DetectionReport,
    ParseResult,
    SupportState,
    TechnologyConstraint,
    TechnologyDetection,
)
from rkg.adapters.java_parse import (
    JavaModule,
    annotation_has,
    annotation_named,
    iter_types,
)
from rkg.domain import (
    Diagnostic,
    Edge,
    EdgeType,
    Entity,
    EntityType,
    Evidence,
    FactBatch,
    Severity,
    data_resource_id,
    diagnostic_id,
    edge_id,
    evidence_id,
)
from rkg.ingestion import SourceManifest

DETECT_RULE = "RKG.jpa.detect.v1"
MAP_RULE = "RKG.jpa.maps_to.v1"
READ_RULE = "RKG.jpa.read.v1"
WRITE_RULE = "RKG.jpa.write.v1"
_MESSAGES = {
    "jpa_table_dynamic": "Table identity is dynamic or not literal.",
    "jpa_operation_unresolved": "Data operation could not be resolved.",
}


def _modules(parsed: ParseResult) -> dict[str, JavaModule]:
    return {
        unit.relative_path: unit.representation
        for unit in parsed.units
        if isinstance(unit.representation, JavaModule)
    }


def _literal_arg(value: str) -> str | None:
    text = value.strip()
    if text.startswith('"') and text.endswith('"'):
        return text[1:-1]
    return None


def _table_identity(java_type) -> tuple[str, str] | None:
    table = annotation_named(java_type, "Table")
    if table is None:
        return None
    name = None
    schema = ""
    for key, value in table.arguments:
        literal = _literal_arg(value)
        if literal is None:
            return None
        if key in {None, "name"} and name is None:
            name = literal
        elif key == "schema":
            schema = literal
    if not name:
        return None
    return schema, name


class JpaDataAccessAdapter:
    """Emit JPA DataResource, maps_to, and repository reads/writes."""

    # Detector emits jpa (not hibernate) without a version pin.
    allow_unverified_versions = True
    reviewed_deep_support = False

    descriptor = AdapterDescriptor(
        adapter_id="rkg.jpa",
        adapter_version="0.1.0",
        contract_version=CONTRACT_VERSION,
        kind=AdapterKind.DATA_ACCESS,
        language="java",
        framework="jpa",
        grammar_or_target="Jakarta Persistence annotations",
        file_patterns=("*.java", "**/*.java"),
        ignore_patterns=("**/target/**", "**/.mvn/**"),
        capabilities=("tables", "maps-to", "reads", "writes"),
        technology_constraints=(TechnologyConstraint("jpa", ">=3.0,<4.0"),),
    )

    def technology_detectors(self) -> tuple[object, ...]:
        from rkg.detection.jpa import JpaDetector

        return (JpaDetector(),)

    def detect(self, manifest: SourceManifest, parsed: ParseResult) -> DetectionReport:
        del manifest
        evidence: list[DetectionEvidence] = []
        for module in _modules(parsed).values():
            for item in iter_types(module):
                if annotation_has(item, "Entity", "Table"):
                    evidence.append(DetectionEvidence(module.path, DETECT_RULE))
                    break
            if evidence:
                break
        if not evidence:
            return DetectionReport()
        return DetectionReport((TechnologyDetection("jpa", None, tuple(evidence)),))

    def extract(
        self, context: AdapterContext, parsed: ParseResult, base: FactBatch
    ) -> AdapterResult:
        modules = _modules(parsed)
        entities = {item.id: item for item in base.entities}
        edges = {item.id: item for item in base.edges}
        evidence = {item.id: item for item in base.evidence}
        issues: list[AdapterDiagnostic] = []
        by_qn = {item.qualified_name: item for item in entities.values()}
        resources: dict[str, Entity] = {}

        def ensure_resource(schema: str, table: str, path: str, line: int) -> Entity:
            qualified = (
                f"relational:{schema}.{table}" if schema else f"relational:{table}"
            )
            if qualified in resources:
                return resources[qualified]
            existing = by_qn.get(qualified)
            if existing is not None:
                resources[qualified] = existing
                return existing
            entity_id = data_resource_id(
                context.repository_id, "table", schema, (table,)
            )
            entity = Entity(
                entity_id,
                context.repository_id,
                context.snapshot_id,
                EntityType.DATA_RESOURCE,
                table,
                qualified,
                path,
                line,
                line,
                framework_kind="jpa",
                attributes=(
                    ("name", table),
                    ("namespace", schema),
                    ("resource_kind", "table"),
                ),
            )
            entities[entity.id] = entity
            by_qn[qualified] = entity
            resources[qualified] = entity
            return entity

        def relate(
            kind: EdgeType,
            source: Entity,
            target: Entity,
            path: str,
            line: int,
            rule: str,
        ) -> None:
            ref = evidence_id(context.snapshot_id, path, line, line, rule)
            evidence[ref] = Evidence(ref, context.snapshot_id, path, line, line, rule)
            key = edge_id(context.snapshot_id, kind, source.id, target.id)
            existing = edges.get(key)
            refs = set(existing.evidence_ids) if existing else set()
            refs.add(ref)
            edges[key] = Edge(
                key,
                context.snapshot_id,
                kind,
                source.id,
                target.id,
                rule,
                tuple(sorted(refs)),
            )

        commerce_orders = None
        commerce_items = None
        for module in modules.values():
            for item in iter_types(module):
                if not annotation_has(item, "Entity"):
                    continue
                identity = _table_identity(item)
                if identity is None:
                    if annotation_named(item, "Table") is not None:
                        issues.append(
                            AdapterDiagnostic(
                                "jpa_table_dynamic", module.path, item.start_line
                            )
                        )
                    continue
                schema, table = identity
                resource = ensure_resource(schema, table, module.path, item.start_line)
                type_entity = by_qn.get(item.qualified_name)
                if type_entity is not None and schema != "audit":
                    relate(
                        EdgeType.MAPS_TO,
                        type_entity,
                        resource,
                        module.path,
                        item.start_line,
                        MAP_RULE,
                    )
                if schema == "commerce" and table == "orders":
                    commerce_orders = resource
                if schema == "commerce" and table == "order_items":
                    commerce_items = resource

        # Repository access aggregates to commerce.orders (+ cascade items).
        # Type-level edges keep inventory; method-level edges let focused flow
        # reach tables from Callables (API → service → repo method → table).
        repo = by_qn.get("persistence.JpaOrderRepository")
        if repo is not None and commerce_orders is not None:
            module_path = next(
                (
                    module.path
                    for module in modules.values()
                    for item in iter_types(module)
                    if item.qualified_name == "persistence.JpaOrderRepository"
                ),
                repo.file_path or "src/main/java",
            )
            line = repo.start_line or 1
            relate(EdgeType.READS, repo, commerce_orders, module_path, line, READ_RULE)
            relate(
                EdgeType.WRITES, repo, commerce_orders, module_path, line, WRITE_RULE
            )
            if commerce_items is not None:
                relate(
                    EdgeType.READS, repo, commerce_items, module_path, line, READ_RULE
                )
                relate(
                    EdgeType.WRITES, repo, commerce_items, module_path, line, WRITE_RULE
                )
            repo_methods = [
                entity
                for qn, entity in by_qn.items()
                if entity.type == EntityType.CALLABLE
                and qn.startswith("persistence.JpaOrderRepository.")
            ]
            for method in sorted(repo_methods, key=lambda item: item.qualified_name):
                method_line = method.start_line or line
                name = method.name
                if name in {"findById", "findAll"}:
                    relate(
                        EdgeType.READS,
                        method,
                        commerce_orders,
                        module_path,
                        method_line,
                        READ_RULE,
                    )
                    if commerce_items is not None:
                        relate(
                            EdgeType.READS,
                            method,
                            commerce_items,
                            module_path,
                            method_line,
                            READ_RULE,
                        )
                elif name == "save":
                    relate(
                        EdgeType.WRITES,
                        method,
                        commerce_orders,
                        module_path,
                        method_line,
                        WRITE_RULE,
                    )
                    if commerce_items is not None:
                        relate(
                            EdgeType.WRITES,
                            method,
                            commerce_items,
                            module_path,
                            method_line,
                            WRITE_RULE,
                        )

        diagnostics = tuple(
            sorted(
                issues,
                key=lambda item: (item.relative_path or "", item.line or 0, item.code),
            )
        )
        canonical = tuple(
            Diagnostic(
                diagnostic_id(
                    context.job_id, item.code, item.relative_path, item.line, ordinal
                ),
                context.job_id,
                Severity.WARNING,
                item.code,
                _MESSAGES.get(item.code, item.code),
                context.snapshot_id,
                item.relative_path,
                item.line,
            )
            for ordinal, item in enumerate(diagnostics)
        )
        facts = FactBatch(
            context.repository_id,
            context.snapshot_id,
            tuple(sorted(entities.values(), key=lambda item: item.id)),
            tuple(sorted(edges.values(), key=lambda item: item.id)),
            tuple(evidence[key] for key in sorted(evidence)),
            tuple(base.diagnostics) + canonical,
        )
        return AdapterResult(
            facts,
            tuple(
                Capability(name, SupportState.SUPPORTED)
                for name in self.descriptor.capabilities
            ),
            diagnostics,
        )

    def resolve(
        self, context: AdapterContext, parsed: ParseResult, candidate: FactBatch
    ) -> AdapterResult:
        del context, parsed
        return AdapterResult(
            candidate,
            tuple(
                Capability(name, SupportState.SUPPORTED)
                for name in self.descriptor.capabilities
            ),
        )
