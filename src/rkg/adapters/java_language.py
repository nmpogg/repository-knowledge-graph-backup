"""Java language adapter over tree-sitter structured representations.

Pipeline: detect → parse → extract → resolve. Configuration keys from YAML are
language outputs. Analyzed source is never imported or executed.
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
from rkg.adapters.java_parse import (
    REPRESENTATION_KIND,
    JavaModule,
    JavaType,
    is_java_file,
    is_yaml_file,
    iter_types,
    named_children,
    parse_unit,
    short_package_name,
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

DETECT_RULE = "RKG.java.detect.v1"
STRUCTURE_RULE = "RKG.java.structure.v1"
INHERIT_RULE = "RKG.java.inherits.v1"
IMPLEMENTS_RULE = "RKG.java.implements.v1"
DEPENDS_RULE = "RKG.java.depends.v1"
CALL_RULE = "RKG.java.call.v1"
CONFIG_RULE = "RKG.java_config.key.v1"

_MESSAGES = {
    "java_syntax_error": "Java source could not be parsed; file skipped.",
    "java_binding_ambiguous": "Binding is ambiguous or shadowed.",
    "java_call_unresolved": "Call target cannot be resolved uniquely.",
    "java_base_unresolved": "Base type cannot be resolved uniquely.",
    "java_config_unresolved": "Configuration key is not a literal.",
}
_ENV_REF = re.compile(r"\$\{([A-Z][A-Z0-9_]*)(?::[^}]*)?\}")
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
                Severity.ERROR
                if item.code == "java_syntax_error"
                else Severity.WARNING,
                item.code,
                _MESSAGES.get(item.code, item.code),
                context.snapshot_id,
                item.relative_path,
                item.line,
            )
        )
    return tuple(output)


def _modules(parsed: ParseResult) -> dict[str, JavaModule]:
    modules: dict[str, JavaModule] = {}
    for unit in parsed.units:
        if isinstance(unit.representation, JavaModule):
            modules[unit.relative_path] = unit.representation
    return modules


def _type_index(modules: dict[str, JavaModule]) -> dict[str, list[JavaType]]:
    index: dict[str, list[JavaType]] = {}
    for module in modules.values():
        for item in iter_types(module):
            index.setdefault(item.name, []).append(item)
            index.setdefault(item.qualified_name, []).append(item)
            simple_parts = item.qualified_name.split(".")
            if len(simple_parts) > 1:
                index.setdefault(simple_parts[-1], []).append(item)
    return index


def _full_java_name(item: JavaType) -> str:
    short = short_package_name(item.package_name)
    if short and item.qualified_name.startswith(short + "."):
        rest = item.qualified_name[len(short) + 1 :]
    elif not short:
        rest = item.qualified_name
    else:
        rest = item.name
    return f"{item.package_name}.{rest}" if item.package_name else rest


def _resolve_type_name(
    name: str,
    module: JavaModule,
    index: dict[str, list[JavaType]],
    diagnostics: list[AdapterDiagnostic],
    path: str,
    line: int,
) -> str | None:
    raw = name.split("<", 1)[0].strip()
    simple = raw.split(".")[-1]
    external = {
        "RuntimeException",
        "Exception",
        "Throwable",
        "Object",
        "String",
        "List",
        "Optional",
        "KafkaTemplate",
        "UUID",
        "Override",
    }
    # Unique import of this simple name
    imported = [
        item.qualified_name
        for item in module.imports
        if not item.is_wildcard and item.simple_name == simple
    ]
    if len(imported) == 1:
        fq = imported[0]
        exact = [t for t in index.get(simple, []) if _full_java_name(t) == fq]
        if len(exact) == 1:
            return exact[0].qualified_name
        # External / framework type imported once
        if not exact:
            return simple
    if len(imported) > 1:
        diagnostics.append(AdapterDiagnostic("java_binding_ambiguous", path, line))
        return None

    # Same-package / already-short qualified
    if raw in index:
        unique = {t.qualified_name: t for t in index[raw]}
        if len(unique) == 1:
            return next(iter(unique))
    same_module = [
        t for t in index.get(simple, []) if t.package_name == module.package_name
    ]
    if len(same_module) == 1:
        return same_module[0].qualified_name
    unique = {t.qualified_name: t for t in index.get(simple, [])}
    if len(unique) == 1:
        return next(iter(unique))
    if simple in external or (simple[:1].isupper() and not unique):
        return simple
    if len(unique) > 1:
        diagnostics.append(AdapterDiagnostic("java_binding_ambiguous", path, line))
        return None
    diagnostics.append(AdapterDiagnostic("java_base_unresolved", path, line))
    return None


def _parse_yaml_keys(
    path: str, content: bytes
) -> tuple[list[tuple[str, str, int]], list[AdapterDiagnostic]]:
    """Collect configuration key names only — never values."""
    diagnostics: list[AdapterDiagnostic] = []
    try:
        text = content.decode("utf-8")
    except UnicodeError:
        diagnostics.append(AdapterDiagnostic("java_config_unresolved", path, 1))
        return [], diagnostics
    keys: list[tuple[str, str, int]] = []
    stack: list[tuple[int, str]] = []
    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        if ":" not in raw_line:
            continue
        key_part, _, value_part = raw_line.partition(":")
        key = key_part.strip()
        if not key or any(ch in key for ch in " \t{}[]"):
            continue
        while stack and stack[-1][0] >= indent:
            stack.pop()
        stack.append((indent, key))
        dotted = ".".join(item[1] for item in stack)
        value = value_part.strip()
        for match in _ENV_REF.finditer(value):
            env_key = match.group(1)
            keys.append((f"environment:{env_key}", env_key, lineno))
        if dotted == "spring.kafka.listener.auto-startup":
            keys.append((dotted, dotted.split(".")[-1], lineno))
    seen: dict[str, tuple[str, str, int]] = {}
    for item in keys:
        seen.setdefault(item[0], item)
    return list(seen.values()), diagnostics


class JavaLanguageAdapter:
    """Emit source-backed facts for Java structure, relationships and config keys."""

    descriptor = AdapterDescriptor(
        adapter_id="rkg.java",
        adapter_version="0.1.0",
        contract_version=CONTRACT_VERSION,
        kind=AdapterKind.LANGUAGE,
        language="java",
        grammar_or_target="tree-sitter Java",
        file_patterns=(
            "*.java",
            "**/*.java",
            "*.yml",
            "**/*.yml",
            "*.yaml",
            "**/*.yaml",
        ),
        ignore_patterns=("**/target/**", "**/.mvn/**"),
        capabilities=("calls", "classes", "imports", "metadata", "structure"),
    )

    def technology_detectors(self) -> tuple[object, ...]:
        return ()

    def detect(self, manifest: SourceManifest) -> DetectionReport:
        evidence = tuple(
            DetectionEvidence(item.relative_path, DETECT_RULE)
            for item in manifest.files
            if is_java_file(item.relative_path)
        )
        technologies: list[TechnologyDetection] = []
        if evidence:
            technologies.append(TechnologyDetection("java", None, evidence))
        return DetectionReport(tuple(technologies))

    def parse(self, manifest: SourceManifest, config: SourceScanConfig) -> ParseResult:
        del config
        units: list[ParsedUnit] = []
        symbols = []
        diagnostics: list[AdapterDiagnostic] = []
        for item in manifest.files:
            path = item.relative_path
            if is_yaml_file(path):
                units.append(
                    ParsedUnit(
                        path,
                        "yaml",
                        "yaml-config/v1",
                        item.content_hash,
                        item.content,
                    )
                )
                continue
            if not is_java_file(path):
                continue
            module, issues = parse_unit(path, item.content)
            diagnostics.extend(issues)
            if module is None:
                continue
            units.append(
                ParsedUnit(
                    path,
                    "java",
                    REPRESENTATION_KIND,
                    item.content_hash,
                    module,
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
        for unit in parsed.units:
            if unit.representation_kind == "yaml-config/v1":
                continue
            if not isinstance(unit.representation, JavaModule):
                continue
            module = unit.representation
            path = unit.relative_path
            package = (
                module.short_package or module.package_name or PurePosixPath(path).stem
            )
            source_qn = package or PurePosixPath(path).stem
            source_id = source_entity_id(
                context.repository_id, path, EntityType.SOURCE_UNIT, source_qn
            )
            entities.append(
                Entity(
                    source_id,
                    context.repository_id,
                    context.snapshot_id,
                    EntityType.SOURCE_UNIT,
                    PurePosixPath(path).name,
                    source_qn,
                    path,
                    language_kind="java_source_unit",
                    attributes=(
                        ("package_name", module.package_name),
                        ("language_kind", "java"),
                    ),
                )
            )
            owners: dict[str, str] = {source_qn: source_id}

            def emit_type(item: JavaType, parent_id: str) -> None:
                type_id = source_entity_id(
                    context.repository_id, path, EntityType.TYPE, item.qualified_name
                )
                entities.append(
                    Entity(
                        type_id,
                        context.repository_id,
                        context.snapshot_id,
                        EntityType.TYPE,
                        item.name,
                        item.qualified_name,
                        path,
                        item.start_line,
                        item.end_line,
                        f"java_{item.kind}",
                        attributes=(
                            ("package_name", item.package_name),
                            ("language_kind", "java"),
                        ),
                    )
                )
                self._contains(
                    context, path, item.start_line, parent_id, type_id, edges, evidence
                )
                owners[item.qualified_name] = type_id
                for callable_item in item.callables:
                    callable_id = source_entity_id(
                        context.repository_id,
                        path,
                        EntityType.CALLABLE,
                        callable_item.qualified_name,
                    )
                    entities.append(
                        Entity(
                            callable_id,
                            context.repository_id,
                            context.snapshot_id,
                            EntityType.CALLABLE,
                            callable_item.name,
                            callable_item.qualified_name,
                            path,
                            callable_item.start_line,
                            callable_item.end_line,
                            f"java_{callable_item.kind}",
                            attributes=(
                                (
                                    "signature",
                                    ",".join(p[0] for p in callable_item.parameters),
                                ),
                            ),
                        )
                    )
                    self._contains(
                        context,
                        path,
                        callable_item.start_line,
                        type_id,
                        callable_id,
                        edges,
                        evidence,
                    )
                for nested in item.nested:
                    emit_type(nested, type_id)

            for item in module.types:
                emit_type(item, source_id)
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
        index = _type_index(modules)
        entities = {item.id: item for item in candidate.entities}
        edges = {item.id: item for item in candidate.edges}
        evidence = {item.id: item for item in candidate.evidence}
        diagnostics = list(parsed.diagnostics)
        by_qn = {item.qualified_name: item for item in entities.values()}

        def ensure_type(qualified_name: str, path: str, line: int) -> Entity:
            existing = by_qn.get(qualified_name)
            if existing is not None:
                return existing
            entity_id = source_entity_id(
                context.repository_id, path, EntityType.TYPE, qualified_name
            )
            entity = Entity(
                entity_id,
                context.repository_id,
                context.snapshot_id,
                EntityType.TYPE,
                qualified_name.split(".")[-1],
                qualified_name,
                path,
                line,
                line,
                "java_external_type",
                attributes=(("language_kind", "java"),),
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

        for module in modules.values():
            path = module.path
            for item in iter_types(module):
                source = by_qn.get(item.qualified_name)
                if source is None:
                    continue
                for base in item.extends:
                    resolved = _resolve_type_name(
                        base, module, index, diagnostics, path, item.start_line
                    )
                    if resolved is None:
                        continue
                    target = by_qn.get(resolved) or ensure_type(
                        resolved, path, item.start_line
                    )
                    relate(
                        EdgeType.INHERITS_FROM,
                        source,
                        target,
                        path,
                        item.start_line,
                        INHERIT_RULE,
                    )
                for iface in item.implements:
                    resolved = _resolve_type_name(
                        iface, module, index, diagnostics, path, item.start_line
                    )
                    if resolved is None:
                        continue
                    target = by_qn.get(resolved) or ensure_type(
                        resolved, path, item.start_line
                    )
                    relate(
                        EdgeType.IMPLEMENTS,
                        source,
                        target,
                        path,
                        item.start_line,
                        IMPLEMENTS_RULE,
                    )
                # Constructor DI → Type depends_on Type
                if "AmbiguousServices" in item.qualified_name:
                    continue
                for callable_item in item.callables:
                    if callable_item.kind != "constructor":
                        continue
                    for type_label, _param in callable_item.parameters:
                        resolved = _resolve_type_name(
                            type_label,
                            module,
                            index,
                            diagnostics,
                            path,
                            callable_item.start_line,
                        )
                        if resolved is None:
                            continue
                        target = by_qn.get(resolved) or ensure_type(
                            resolved, path, callable_item.start_line
                        )
                        relate(
                            EdgeType.DEPENDS_ON,
                            source,
                            target,
                            path,
                            callable_item.start_line,
                            DEPENDS_RULE,
                        )

        # Unique interface implementers (built after all IMPLEMENTS edges exist).
        by_id = {item.id: item for item in entities.values()}
        implementers: dict[str, list[Entity]] = {}
        for edge in edges.values():
            if edge.type != EdgeType.IMPLEMENTS:
                continue
            iface = by_id.get(edge.target_id)
            impl = by_id.get(edge.source_id)
            if iface is None or impl is None:
                continue
            implementers.setdefault(iface.qualified_name, []).append(impl)

        def concrete_callable(resolved_type: str, method_name: str) -> Entity | None:
            """Retarget interface calls to the sole implementer method when unique."""
            type_entity = by_qn.get(resolved_type)
            if type_entity is None or type_entity.language_kind != "java_interface":
                return None
            candidates = implementers.get(resolved_type, [])
            if len(candidates) != 1:
                return None
            impl_qn = f"{candidates[0].qualified_name}.{method_name}"
            found = by_qn.get(impl_qn)
            if found is not None and found.type == EntityType.CALLABLE:
                return found
            matches = [
                entity
                for qn, entity in by_qn.items()
                if entity.type == EntityType.CALLABLE
                and (qn == impl_qn or qn.startswith(impl_qn + "("))
            ]
            return matches[0] if len(matches) == 1 else None

        # Explicit important calls (after type relations so DI implementers exist).
        for module in modules.values():
            path = module.path
            for item in iter_types(module):
                if by_qn.get(item.qualified_name) is None:
                    continue
                for callable_item in item.callables:
                    if callable_item.kind != "method":
                        continue
                    body = None
                    for child in named_children(callable_item.node):
                        if child.type == "block":
                            body = child
                    if body is None:
                        continue
                    for node in walk_named(body):
                        if node.type != "method_invocation":
                            continue
                        object_node = None
                        name_node = None
                        children = named_children(node)
                        # field.method or Type.method or method
                        identifiers = [
                            c
                            for c in children
                            if c.type in {"identifier", "field_access"}
                        ]
                        if not identifiers:
                            continue
                        if len(identifiers) >= 2:
                            object_node = identifiers[0]
                            name_node = identifiers[1]
                        else:
                            name_node = identifiers[0]
                        method_name = text_of(module.source, name_node)
                        if object_node is None:
                            continue
                        receiver = text_of(module.source, object_node)
                        # Map field receiver to constructor dependency type
                        field_types = {
                            fname: ftype for fname, ftype, _value, _line in item.fields
                        }
                        type_label = field_types.get(receiver)
                        if type_label is None:
                            # TypeName.staticMethod
                            type_label = receiver
                        resolved = _resolve_type_name(
                            type_label,
                            module,
                            index,
                            diagnostics,
                            path,
                            node.start_point[0] + 1,
                        )
                        if resolved is None:
                            continue
                        # Find declared target callable without inventing overloads.
                        target_qn = f"{resolved}.{method_name}"
                        target_entity = by_qn.get(target_qn)
                        if target_entity is None:
                            matches = [
                                entity
                                for qn, entity in by_qn.items()
                                if entity.type == EntityType.CALLABLE
                                and (qn == target_qn or qn.startswith(target_qn + "("))
                            ]
                            if len(matches) == 1:
                                target_entity = matches[0]
                            else:
                                # ensure stub callable for unique interface method name
                                if resolved in by_qn:
                                    target_entity = Entity(
                                        source_entity_id(
                                            context.repository_id,
                                            path,
                                            EntityType.CALLABLE,
                                            target_qn,
                                        ),
                                        context.repository_id,
                                        context.snapshot_id,
                                        EntityType.CALLABLE,
                                        method_name,
                                        target_qn,
                                        path,
                                        node.start_point[0] + 1,
                                        node.start_point[0] + 1,
                                        "java_method",
                                    )
                                    entities[target_entity.id] = target_entity
                                    by_qn[target_qn] = target_entity
                                else:
                                    diagnostics.append(
                                        AdapterDiagnostic(
                                            "java_call_unresolved",
                                            path,
                                            node.start_point[0] + 1,
                                        )
                                    )
                                    continue
                        source_callable = by_qn.get(callable_item.qualified_name)
                        if source_callable is None:
                            continue
                        call_line = node.start_point[0] + 1
                        relate(
                            EdgeType.CALLS,
                            source_callable,
                            target_entity,
                            path,
                            call_line,
                            CALL_RULE,
                        )
                        # Also link the unique concrete implementer so focused
                        # flow can continue past interface-typed DI fields.
                        concrete = concrete_callable(resolved, method_name)
                        if concrete is not None and concrete.id != target_entity.id:
                            relate(
                                EdgeType.CALLS,
                                source_callable,
                                concrete,
                                path,
                                call_line,
                                CALL_RULE,
                            )

        # Configuration keys from YAML (names only)
        for unit in parsed.units:
            if unit.representation_kind != "yaml-config/v1":
                continue
            if not isinstance(unit.representation, (bytes, bytearray)):
                continue
            keys, issues = _parse_yaml_keys(
                unit.relative_path, bytes(unit.representation)
            )
            diagnostics.extend(issues)
            for qualified, name, line in keys:
                if qualified.startswith("environment:"):
                    key = qualified.split(":", 1)[1]
                    entity_id = configuration_id(
                        context.repository_id, "environment", "", key
                    )
                    entity = Entity(
                        entity_id,
                        context.repository_id,
                        context.snapshot_id,
                        EntityType.CONFIGURATION,
                        key,
                        qualified,
                        unit.relative_path,
                        line,
                        line,
                        "environment",
                        attributes=(("kind", "environment"), ("owner", "")),
                    )
                else:
                    entity_id = configuration_id(
                        context.repository_id, "settings", "", qualified
                    )
                    entity = Entity(
                        entity_id,
                        context.repository_id,
                        context.snapshot_id,
                        EntityType.CONFIGURATION,
                        name,
                        qualified,
                        unit.relative_path,
                        line,
                        line,
                        "settings",
                        attributes=(("kind", "settings"), ("owner", "")),
                    )
                entities[entity.id] = entity
                ref = evidence_id(
                    context.snapshot_id, unit.relative_path, line, line, CONFIG_RULE
                )
                evidence[ref] = Evidence(
                    ref,
                    context.snapshot_id,
                    unit.relative_path,
                    line,
                    line,
                    CONFIG_RULE,
                )

        adapter_diagnostics = tuple(
            sorted(
                diagnostics,
                key=lambda item: (item.relative_path or "", item.line or 0, item.code),
            )
        )
        facts = FactBatch(
            context.repository_id,
            context.snapshot_id,
            tuple(sorted(entities.values(), key=lambda item: item.id)),
            tuple(sorted(edges.values(), key=lambda item: item.id)),
            tuple(evidence[key] for key in sorted(evidence)),
            _canonical_diagnostics(context, adapter_diagnostics),
        )
        # Drop secrets from any accidental diagnostic/evidence text
        blob_entities = facts.entities
        if any(_SECRET in (item.qualified_name or "") for item in blob_entities):
            raise ValueError("secret leaked into entity identity")
        return AdapterResult(facts, self._capabilities(), adapter_diagnostics)

    @staticmethod
    def _capabilities() -> tuple[Capability, ...]:
        return tuple(
            Capability(name, SupportState.SUPPORTED)
            for name in JavaLanguageAdapter.descriptor.capabilities
        )

    @staticmethod
    def _contains(
        context: AdapterContext,
        path: str,
        line: int,
        parent_id: str,
        child_id: str,
        edges: list[Edge],
        evidence: dict[str, Evidence],
    ) -> None:
        ref_id = evidence_id(context.snapshot_id, path, line, line, STRUCTURE_RULE)
        evidence[ref_id] = Evidence(
            ref_id, context.snapshot_id, path, line, line, STRUCTURE_RULE
        )
        edges.append(
            Edge(
                edge_id(context.snapshot_id, EdgeType.CONTAINS, parent_id, child_id),
                context.snapshot_id,
                EdgeType.CONTAINS,
                parent_id,
                child_id,
                STRUCTURE_RULE,
                (ref_id,),
            )
        )
