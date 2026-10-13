"""Static pgx data-access extraction over parsed Go units.

DataResource identity is relational:{schema}.{table} from static SQL string
constants. Runtime-built SQL never becomes a guessed edge.
"""

from __future__ import annotations

import re
from dataclasses import replace

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
from rkg.adapters.go_parse import (
    GoModule,
    named_children,
    text_of,
    walk_named,
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

DETECT_RULE = "RKG.pgx.detect.v1"
READ_RULE = "RKG.pgx.read.v1"
WRITE_RULE = "RKG.pgx.write.v1"
_PGX_PREFIX = "github.com/jackc/pgx"
_TABLE_RE = re.compile(
    r"(?is)\b(?:from|into|update|join)\s+([a-z_][\w]*\.[a-z_][\w]*)\b"
)
_MESSAGES = {
    "pgx_table_dynamic": "Table identity is dynamic or not literal.",
    "pgx_operation_unresolved": "Data operation could not be resolved.",
}


def _modules(parsed: ParseResult) -> dict[str, GoModule]:
    return {
        unit.relative_path: unit.representation
        for unit in parsed.units
        if isinstance(unit.representation, GoModule)
    }


def _has_pgx_import(module: GoModule) -> bool:
    return any(item.path.startswith(_PGX_PREFIX) for item in module.imports)


def _sql_tables(sql: str) -> tuple[tuple[str, str], ...]:
    found: list[tuple[str, str]] = []
    for match in _TABLE_RE.finditer(sql):
        schema, table = match.group(1).split(".", 1)
        found.append((schema, table))
    # Deduplicate preserving order
    seen: set[tuple[str, str]] = set()
    ordered: list[tuple[str, str]] = []
    for item in found:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return tuple(ordered)


def _sql_kind(sql: str) -> str | None:
    head = sql.lstrip().split(None, 1)[0].upper() if sql.strip() else ""
    if head == "SELECT":
        return "read"
    if head in {"INSERT", "UPDATE", "DELETE"}:
        return "write"
    return None


class PgxDataAccessAdapter:
    """Emit pgx DataResource reads/writes from static SQL constants."""

    allow_unverified_versions = True
    reviewed_deep_support = False

    descriptor = AdapterDescriptor(
        adapter_id="rkg.pgx",
        adapter_version="0.1.0",
        contract_version=CONTRACT_VERSION,
        kind=AdapterKind.DATA_ACCESS,
        language="go",
        framework="pgx",
        grammar_or_target="jackc/pgx static SQL",
        file_patterns=("*.go", "**/*.go"),
        ignore_patterns=("**/vendor/**", "**/testdata/**", "**/*_test.go"),
        capabilities=("tables", "reads", "writes"),
        technology_constraints=(TechnologyConstraint("pgx", ">=5.0,<6.0"),),
    )

    def technology_detectors(self) -> tuple[object, ...]:
        from rkg.detection.pgx import PgxDetector

        return (PgxDetector(),)

    def detect(self, manifest: SourceManifest, parsed: ParseResult) -> DetectionReport:
        del manifest
        evidence: list[DetectionEvidence] = []
        for module in _modules(parsed).values():
            if _has_pgx_import(module):
                evidence.append(DetectionEvidence(module.path, DETECT_RULE))
        if not evidence:
            return DetectionReport()
        return DetectionReport((TechnologyDetection("pgx", None, tuple(evidence)),))

    def extract(
        self, context: AdapterContext, parsed: ParseResult, base: FactBatch
    ) -> AdapterResult:
        modules = _modules(parsed)
        entities = {item.id: item for item in base.entities}
        edges = {item.id: item for item in base.edges}
        evidence = {item.id: item for item in base.evidence}
        issues: list[AdapterDiagnostic] = []
        by_qn = {item.qualified_name: item for item in entities.values()}

        # Collect SQL constants per package: name → (sql, kind, tables, path, line)
        sql_consts: dict[
            str, tuple[str, str, tuple[tuple[str, str], ...], str, int]
        ] = {}
        for module in modules.values():
            for name, sql in module.constants.items():
                kind = _sql_kind(sql)
                tables = _sql_tables(sql)
                if kind is None or not tables:
                    continue
                key = f"{module.package_name}.{name}"
                # Approximate line: search in source
                line = 1
                needle = name.encode("utf-8")
                idx = module.source.find(needle)
                if idx >= 0:
                    line = module.source[:idx].count(b"\n") + 1
                sql_consts[key] = (sql, kind, tables, module.path, line)
                sql_consts[name] = sql_consts[key]

        def ensure_resource(schema: str, table: str, path: str, line: int) -> Entity:
            qualified = f"relational:{schema}.{table}"
            existing = by_qn.get(qualified)
            if existing is not None:
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
                framework_kind="pgx",
                attributes=(
                    ("kind", "table"),
                    ("name", table),
                    ("namespace", schema),
                    ("resource_kind", "table"),
                ),
            )
            entities[entity.id] = entity
            by_qn[qualified] = entity
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

        for module in modules.values():
            if not _has_pgx_import(module) and not any(
                key.startswith(module.package_name + ".") for key in sql_consts
            ):
                # Still allow repository methods in package that owns SQL consts
                # even when import is only in postgres_repository.go
                pass
            for callable_item in module.callables:
                if callable_item.kind != "method":
                    continue
                body = next(
                    (
                        c
                        for c in named_children(callable_item.node)
                        if c.type == "block"
                    ),
                    None,
                )
                if body is None:
                    continue
                source = by_qn.get(callable_item.qualified_name)
                if source is None:
                    continue
                for node in walk_named(body):
                    if node.type != "call_expression":
                        continue
                    func = node.child_by_field_name("function") or next(
                        iter(named_children(node)), None
                    )
                    if func is None or func.type != "selector_expression":
                        continue
                    field = (
                        func.child_by_field_name("field") or named_children(func)[-1]
                    )
                    method = text_of(module.source, field)
                    if method not in {"QueryRow", "Exec", "Query"}:
                        continue
                    args = node.child_by_field_name("arguments") or next(
                        (c for c in named_children(node) if c.type == "argument_list"),
                        None,
                    )
                    if args is None:
                        continue
                    arg_nodes = named_children(args)
                    # QueryRow/Exec(ctx, sql, ...) → sql at index 1
                    sql_node = arg_nodes[1] if len(arg_nodes) >= 2 else None
                    if sql_node is None:
                        continue
                    sql_name = text_of(module.source, sql_node)
                    info = sql_consts.get(sql_name) or sql_consts.get(
                        f"{module.package_name}.{sql_name}"
                    )
                    line = node.start_point[0] + 1
                    if info is None:
                        issues.append(
                            AdapterDiagnostic(
                                "pgx_operation_unresolved", module.path, line
                            )
                        )
                        continue
                    _sql, kind, tables, sql_path, sql_line = info
                    current = entities[source.id]
                    attrs = dict(current.attributes)
                    operations = tuple(attrs.get("query_operations") or ())
                    attrs["query_operations"] = tuple(
                        dict.fromkeys((*operations, f"{method}({sql_name})"))
                    )
                    refs = tuple(attrs.get("query_sources") or ())
                    ref = f"{sql_name}@{sql_path}:{sql_line}"
                    attrs["query_sources"] = tuple(dict.fromkeys((*refs, ref)))
                    entities[source.id] = replace(
                        current, attributes=tuple(attrs.items())
                    )
                    for schema, table in tables:
                        resource = ensure_resource(schema, table, sql_path, sql_line)
                        edge_kind = (
                            EdgeType.READS if kind == "read" else EdgeType.WRITES
                        )
                        rule = READ_RULE if kind == "read" else WRITE_RULE
                        relate(edge_kind, source, resource, module.path, line, rule)

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
