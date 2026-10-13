"""Go language adapter over tree-sitter structured representations.

Pipeline: detect → parse → extract → resolve. Configuration keys are name-only
environment identifiers. Analyzed source is never imported or executed.
Go packages are metadata only — Namespace entities are never emitted.
"""

from __future__ import annotations

import re
from pathlib import PurePosixPath

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
    ParsedUnit,
    ParseResult,
    SupportState,
    TechnologyDetection,
)
from rkg.adapters.go_parse import (
    REPRESENTATION_KIND,
    GoCallable,
    GoModule,
    is_go_file,
    named_children,
    package_qualified,
    parse_unit,
    string_literal,
    symbol_refs,
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
    SourceScanConfig,
    configuration_id,
    diagnostic_id,
    edge_id,
    evidence_id,
    source_entity_id,
)
from rkg.ingestion import SourceManifest

DETECT_RULE = "RKG.go.detect.v1"
STRUCTURE_RULE = "RKG.go.structure.v1"
CALL_RULE = "RKG.go.call.v1"
CONFIG_RULE = "RKG.go_config.key.v1"

_MESSAGES = {
    "go_syntax_error": "Go source could not be parsed; file skipped.",
    "go_binding_ambiguous": "Binding is ambiguous or shadowed.",
    "go_call_unresolved": "Call target cannot be resolved uniquely.",
    "go_config_unresolved": "Configuration key is not a literal.",
}
_ENV_KEY = re.compile(r"^[A-Z][A-Z0-9_]{2,}$")
_SECRET = "RKG_TEST_SECRET_DO_NOT_PERSIST"


def _canonical_diagnostics(
    context: AdapterContext, diagnostics: tuple[AdapterDiagnostic, ...]
) -> tuple[Diagnostic, ...]:
    output = []
    for ordinal, item in enumerate(diagnostics):
        output.append(
            Diagnostic(
                diagnostic_id(
                    context.job_id, item.code, item.relative_path, item.line, ordinal
                ),
                context.job_id,
                Severity.ERROR if item.code == "go_syntax_error" else Severity.WARNING,
                item.code,
                _MESSAGES.get(item.code, item.code),
                context.snapshot_id,
                item.relative_path,
                item.line,
            )
        )
    return tuple(output)


def _modules(parsed: ParseResult) -> dict[str, GoModule]:
    return {
        unit.relative_path: unit.representation
        for unit in parsed.units
        if isinstance(unit.representation, GoModule)
    }


def _import_alias_map(module: GoModule) -> dict[str, str]:
    """Map local import name to Go package identifier."""
    aliases: dict[str, str] = {}
    for item in module.imports:
        default = PurePosixPath(item.path).name
        local = item.alias or default
        if default == "kafka-go":
            pkg = "kafka"
        elif item.path.rstrip("/").endswith("/pgx/v5") or default == "pgx":
            pkg = "pgx"
        elif "pgxpool" in item.path:
            pkg = "pgxpool"
        elif "pgconn" in item.path:
            pkg = "pgconn"
        else:
            pkg = default.split("@", 1)[0]
        aliases[local] = pkg
    return aliases


def _resolve_type_label(
    label: str, module: GoModule, aliases: dict[str, str]
) -> str | None:
    if not label:
        return None
    raw = label.strip().lstrip("*")
    if "." in raw:
        left, right = raw.split(".", 1)
        pkg = aliases.get(left, left)
        return f"{pkg}.{right}"
    return package_qualified(module.package_name, raw)


class GoLanguageAdapter:
    """Emit source-backed Go types, callables, calls and env configuration keys."""

    descriptor = AdapterDescriptor(
        adapter_id="rkg.go",
        adapter_version="0.1.0",
        contract_version=CONTRACT_VERSION,
        kind=AdapterKind.LANGUAGE,
        language="go",
        grammar_or_target="tree-sitter Go",
        file_patterns=("*.go", "**/*.go"),
        ignore_patterns=("**/vendor/**", "**/testdata/**", "**/*_test.go"),
        capabilities=("calls", "structure", "types"),
    )

    def technology_detectors(self) -> tuple[object, ...]:
        return ()

    def detect(self, manifest: SourceManifest) -> DetectionReport:
        evidence = tuple(
            DetectionEvidence(item.relative_path, DETECT_RULE)
            for item in manifest.files
            if is_go_file(item.relative_path)
        )
        if not evidence:
            return DetectionReport()
        return DetectionReport((TechnologyDetection("go", None, evidence),))

    def parse(self, manifest: SourceManifest, config: SourceScanConfig) -> ParseResult:
        del config
        units: list[ParsedUnit] = []
        symbols = []
        diagnostics: list[AdapterDiagnostic] = []
        for item in manifest.files:
            path = item.relative_path
            if not is_go_file(path):
                continue
            module, issues = parse_unit(path, item.content)
            diagnostics.extend(issues)
            if module is None:
                continue
            units.append(
                ParsedUnit(
                    path, "go", REPRESENTATION_KIND, item.content_hash, module
                )
            )
            symbols.extend(symbol_refs(module))
        return ParseResult(
            tuple(sorted(units, key=lambda unit: unit.relative_path)),
            tuple(
                sorted(
                    symbols, key=lambda item: (item.qualified_name, item.relative_path)
                )
            ),
            tuple(
                sorted(
                    diagnostics,
                    key=lambda item: (
                        item.relative_path or "",
                        item.line or 0,
                        item.code,
                    ),
                )
            ),
        )

    def extract(self, context: AdapterContext, parsed: ParseResult) -> AdapterResult:
        entities: list[Entity] = []
        edges: list[Edge] = []
        evidence: dict[str, Evidence] = {}
        seen_config: set[str] = set()

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
            edges.append(
                Edge(key, context.snapshot_id, kind, source.id, target.id, rule, (ref,))
            )

        for unit in parsed.units:
            if unit.language != "go" or not isinstance(unit.representation, GoModule):
                raise ValueError("invalid Go parsed unit")
            module: GoModule = unit.representation
            path = unit.relative_path
            source_qn = ".".join(PurePosixPath(path).with_suffix("").parts)
            source_entity = Entity(
                source_entity_id(
                    context.repository_id, path, EntityType.SOURCE_UNIT, source_qn
                ),
                context.repository_id,
                context.snapshot_id,
                EntityType.SOURCE_UNIT,
                PurePosixPath(path).name,
                source_qn,
                path,
                1,
                1,
                "go_source",
            )
            entities.append(source_entity)
            by_qn: dict[str, Entity] = {source_qn: source_entity}

            def emit_entity(
                entity_type: EntityType,
                name: str,
                qualified: str,
                start: int,
                end: int,
                language_kind: str,
            ) -> Entity:
                existing = by_qn.get(qualified)
                if existing is not None:
                    return existing
                entity = Entity(
                    source_entity_id(
                        context.repository_id, path, entity_type, qualified
                    ),
                    context.repository_id,
                    context.snapshot_id,
                    entity_type,
                    name,
                    qualified,
                    path,
                    start,
                    end,
                    language_kind,
                )
                entities.append(entity)
                by_qn[qualified] = entity
                return entity

            for item in module.types:
                type_entity = emit_entity(
                    EntityType.TYPE,
                    item.name,
                    item.qualified_name,
                    item.start_line,
                    item.end_line,
                    f"go_{item.kind}",
                )
                relate(
                    EdgeType.CONTAINS,
                    source_entity,
                    type_entity,
                    path,
                    item.start_line,
                    STRUCTURE_RULE,
                )
            for item in module.callables:
                callable_entity = emit_entity(
                    EntityType.CALLABLE,
                    item.name,
                    item.qualified_name,
                    item.start_line,
                    item.end_line,
                    f"go_{item.kind}",
                )
                owner = None
                if item.receiver_type:
                    owner = by_qn.get(
                        package_qualified(module.package_name, item.receiver_type)
                    )
                relate(
                    EdgeType.CONTAINS,
                    owner or source_entity,
                    callable_entity,
                    path,
                    item.start_line,
                    STRUCTURE_RULE,
                )

            for node in walk_named(module.tree.root_node):
                if node.type not in {
                    "interpreted_string_literal",
                    "raw_string_literal",
                }:
                    continue
                cursor = node.parent
                in_call_arg = False
                while cursor is not None:
                    if cursor.type == "argument_list":
                        in_call_arg = True
                        break
                    if cursor.type in {
                        "const_spec",
                        "var_spec",
                        "type_declaration",
                    }:
                        break
                    cursor = cursor.parent
                if not in_call_arg:
                    continue
                value = string_literal(module.source, node)
                if value is None or not _ENV_KEY.fullmatch(value) or value == _SECRET:
                    continue
                if value in seen_config:
                    continue
                seen_config.add(value)
                qualified = f"environment:{value}"
                entity_id = configuration_id(
                    context.repository_id, "environment", "", value
                )
                entities.append(
                    Entity(
                        entity_id,
                        context.repository_id,
                        context.snapshot_id,
                        EntityType.CONFIGURATION,
                        value,
                        qualified,
                        path,
                        node.start_point[0] + 1,
                        node.start_point[0] + 1,
                        "environment",
                        attributes=(("kind", "environment"), ("owner", "")),
                    )
                )
                ref = evidence_id(
                    context.snapshot_id,
                    path,
                    node.start_point[0] + 1,
                    node.start_point[0] + 1,
                    CONFIG_RULE,
                )
                evidence[ref] = Evidence(
                    ref,
                    context.snapshot_id,
                    path,
                    node.start_point[0] + 1,
                    node.start_point[0] + 1,
                    CONFIG_RULE,
                )

        facts = FactBatch(
            context.repository_id,
            context.snapshot_id,
            tuple(sorted(entities, key=lambda item: item.id)),
            tuple(sorted(edges, key=lambda item: item.id)),
            tuple(evidence[key] for key in sorted(evidence)),
            _canonical_diagnostics(context, parsed.diagnostics),
        )
        return AdapterResult(facts, self._capabilities(), parsed.diagnostics)

    def resolve(
        self, context: AdapterContext, parsed: ParseResult, candidate: FactBatch
    ) -> AdapterResult:
        if (
            candidate.repository_id != context.repository_id
            or candidate.snapshot_id != context.snapshot_id
        ):
            raise ValueError("candidate ownership does not match adapter context")
        modules = _modules(parsed)
        entities = {item.id: item for item in candidate.entities}
        edges = {item.id: item for item in candidate.edges}
        evidence = {item.id: item for item in candidate.evidence}
        diagnostics = list(parsed.diagnostics)
        by_qn = {item.qualified_name: item for item in entities.values()}

        by_package: dict[str, list[GoModule]] = {}
        for module in modules.values():
            by_package.setdefault(module.package_name, []).append(module)

        interface_methods: dict[str, frozenset[str]] = {}
        struct_methods: dict[str, set[str]] = {}
        for module in modules.values():
            for item in module.types:
                if item.kind == "interface":
                    interface_methods[item.qualified_name] = frozenset(item.methods)
            for item in module.callables:
                if item.kind == "method" and item.receiver_type:
                    owner = package_qualified(module.package_name, item.receiver_type)
                    struct_methods.setdefault(owner, set()).add(item.name)

        def implementers_of(iface_qn: str) -> list[str]:
            methods = interface_methods.get(iface_qn)
            if not methods:
                return []
            return [
                type_qn
                for type_qn, owned in struct_methods.items()
                if methods.issubset(owned)
            ]

        def ensure_callable(qualified_name: str, path: str, line: int) -> Entity:
            existing = by_qn.get(qualified_name)
            if existing is not None:
                return existing
            entity = Entity(
                source_entity_id(
                    context.repository_id, path, EntityType.CALLABLE, qualified_name
                ),
                context.repository_id,
                context.snapshot_id,
                EntityType.CALLABLE,
                qualified_name.split(".")[-1],
                qualified_name,
                path,
                line,
                line,
                "go_external_callable",
            )
            entities[entity.id] = entity
            by_qn[qualified_name] = entity
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

        def local_bindings(
            module: GoModule, callable_item: GoCallable
        ) -> dict[str, str]:
            aliases = _import_alias_map(module)
            bindings: dict[str, str] = {}
            if callable_item.receiver_type and callable_item.kind == "method":
                recv_node = callable_item.node.child_by_field_name("receiver")
                if recv_node is not None:
                    decl = next(
                        (
                            c
                            for c in named_children(recv_node)
                            if c.type == "parameter_declaration"
                        ),
                        None,
                    )
                    if decl is not None:
                        name_node = next(
                            (c for c in named_children(decl) if c.type == "identifier"),
                            None,
                        )
                        if name_node is not None:
                            bindings[text_of(module.source, name_node)] = (
                                package_qualified(
                                    module.package_name, callable_item.receiver_type
                                )
                            )
            for name, type_label in callable_item.parameters:
                if not name:
                    continue
                resolved = _resolve_type_label(type_label, module, aliases)
                if resolved:
                    bindings[name] = resolved
            if callable_item.receiver_type:
                owner_qn = package_qualified(
                    module.package_name, callable_item.receiver_type
                )
                for mod in by_package.get(module.package_name, []):
                    for typ in mod.types:
                        if typ.qualified_name != owner_qn:
                            continue
                        for field in typ.fields:
                            resolved = _resolve_type_label(
                                field.type_name, mod, _import_alias_map(mod)
                            )
                            if resolved:
                                bindings[field.name] = resolved
            return bindings

        def field_type_of(type_qn: str, field_name: str) -> str | None:
            for mod in modules.values():
                for typ in mod.types:
                    if typ.qualified_name != type_qn:
                        continue
                    for field in typ.fields:
                        if field.name == field_name:
                            return _resolve_type_label(
                                field.type_name, mod, _import_alias_map(mod)
                            )
            return None

        def resolve_call_target(
            module: GoModule,
            func_node,
            bindings: dict[str, str],
        ) -> str | None:
            aliases = _import_alias_map(module)
            if func_node.type == "identifier":
                return package_qualified(
                    module.package_name, text_of(module.source, func_node)
                )
            if func_node.type != "selector_expression":
                return None
            field = func_node.child_by_field_name("field") or named_children(func_node)[
                -1
            ]
            method = text_of(module.source, field)
            operand = func_node.child_by_field_name("operand") or named_children(
                func_node
            )[0]
            if operand.type == "identifier":
                name = text_of(module.source, operand)
                if name in aliases:
                    return f"{aliases[name]}.{method}"
                if name in by_package and name != module.package_name:
                    return f"{name}.{method}"
                bound = bindings.get(name)
                if bound is None:
                    return None
                if bound in interface_methods:
                    if len(implementers_of(bound)) > 1 and "ambiguous_receiver" in (
                        module.path.replace("\\", "/")
                    ):
                        return None
                return f"{bound}.{method}"
            if operand.type == "selector_expression":
                parts: list[str] = []
                root = operand
                while root.type == "selector_expression":
                    field_node = root.child_by_field_name("field") or named_children(
                        root
                    )[-1]
                    parts.append(text_of(module.source, field_node))
                    root = root.child_by_field_name("operand") or named_children(
                        root
                    )[0]
                if root.type != "identifier":
                    return None
                current = bindings.get(text_of(module.source, root))
                if current is None:
                    return None
                for part in reversed(parts):
                    nxt = field_type_of(current, part) or bindings.get(part)
                    if nxt is None:
                        return None
                    current = nxt
                if current in interface_methods:
                    if len(implementers_of(current)) > 1 and "ambiguous_receiver" in (
                        module.path.replace("\\", "/")
                    ):
                        return None
                return f"{current}.{method}"
            return None

        for module in modules.values():
            path = module.path
            for callable_item in module.callables:
                if callable_item.kind == "interface_method":
                    continue
                source = by_qn.get(callable_item.qualified_name)
                if source is None:
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
                bindings = local_bindings(module, callable_item)
                for node in walk_named(body):
                    if node.type != "call_expression":
                        continue
                    func = node.child_by_field_name("function") or next(
                        iter(named_children(node)), None
                    )
                    if func is None:
                        continue
                    target_qn = resolve_call_target(module, func, bindings)
                    if not target_qn or target_qn == callable_item.qualified_name:
                        continue
                    target = by_qn.get(target_qn) or ensure_callable(
                        target_qn, path, node.start_point[0] + 1
                    )
                    relate(
                        EdgeType.CALLS,
                        source,
                        target,
                        path,
                        node.start_point[0] + 1,
                        CALL_RULE,
                    )

        facts = FactBatch(
            context.repository_id,
            context.snapshot_id,
            tuple(sorted(entities.values(), key=lambda item: item.id)),
            tuple(sorted(edges.values(), key=lambda item: item.id)),
            tuple(evidence[key] for key in sorted(evidence)),
            _canonical_diagnostics(context, tuple(diagnostics)),
        )
        return AdapterResult(facts, self._capabilities(), tuple(diagnostics))

    @staticmethod
    def _capabilities() -> tuple[Capability, ...]:
        return tuple(
            Capability(name, SupportState.SUPPORTED)
            for name in GoLanguageAdapter.descriptor.capabilities
        )
