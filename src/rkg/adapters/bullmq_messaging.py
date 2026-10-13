"""Static BullMQ queue publish/consume extraction over TypeScript units.

Queue names come from string literals or uniquely assigned module constants only.
Dynamic names, reassigned constructors, and shadowed local Queue/Worker bindings
never invent MessageChannel edges. Redis URLs, payloads, and secrets are ignored.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from tree_sitter import Node

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
from rkg.adapters.typescript_parse import (
    TsModule,
    body_of_definition,
    child_named,
    identifier_name,
    named_children,
    resolve_specifier,
    string_literal,
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
    diagnostic_id,
    edge_id,
    evidence_id,
    message_channel_id,
)
from rkg.ingestion import SourceManifest

DETECT_RULE = "RKG.bullmq.detect.v1"
PUBLISH_RULE = "RKG.bullmq.publish.v1"
CONSUME_RULE = "RKG.bullmq.consume.v1"
_PACKAGE = "bullmq"
_MESSAGES = {
    "bullmq_queue_unresolved": "Queue name is dynamic or not a unique constant.",
}
_CALLABLE_KINDS = frozenset(
    {
        "typescript_function",
        "typescript_async_function",
        "typescript_method",
        "typescript_async_method",
    }
)


@dataclass(frozen=True, slots=True)
class _BullmqBindings:
    """Local names imported from the bullmq package."""

    values: dict[str, str]  # local → Queue|Worker
    types: dict[str, str]  # local → Queue|Worker


def _modules(parsed: ParseResult) -> dict[str, TsModule]:
    return {
        unit.relative_path: unit.representation
        for unit in parsed.units
        if isinstance(unit.representation, TsModule)
    }


def _import_specifier(source: bytes, node: Node) -> str | None:
    for child in named_children(node):
        if child.type == "string":
            return string_literal(source, child)
    return None


def _bullmq_bindings(module: TsModule) -> _BullmqBindings:
    values: dict[str, str] = {}
    types: dict[str, str] = {}
    for node in named_children(module.tree.root_node):
        if node.type != "import_statement":
            continue
        specifier = _import_specifier(module.source, node)
        if specifier != _PACKAGE:
            continue
        is_type_only = any(
            child.type == "type" or text_of(module.source, child) == "type"
            for child in node.children
        )
        clause = next(
            (child for child in named_children(node) if child.type == "import_clause"),
            None,
        )
        if clause is None:
            continue
        for child in named_children(clause):
            if child.type != "named_imports":
                continue
            for spec in named_children(child):
                if spec.type != "import_specifier":
                    continue
                type_marker = any(
                    part.type == "type" or text_of(module.source, part) == "type"
                    for part in spec.children
                )
                names = [
                    text_of(module.source, part)
                    for part in named_children(spec)
                    if part.type == "identifier"
                ]
                if not names:
                    continue
                imported, local = names[0], names[-1]
                if imported not in {"Queue", "Worker"}:
                    continue
                if is_type_only or type_marker:
                    types[local] = imported
                else:
                    values[local] = imported
                    types.setdefault(local, imported)
    return _BullmqBindings(values, types)


def _has_bullmq_import(module: TsModule) -> bool:
    bindings = _bullmq_bindings(module)
    return bool(bindings.values or bindings.types)


def _const_string(
    module: TsModule, name: str, modules: dict[str, TsModule]
) -> str | None:
    """Resolve a uniquely assigned module-level string constant, including imports."""
    found: list[str] = []
    for node in named_children(module.tree.root_node):
        stmt = node
        if node.type == "export_statement":
            decl = child_named(node, "declaration")
            if decl is None:
                continue
            stmt = decl
        if stmt.type not in {"lexical_declaration", "variable_declaration"}:
            continue
        for declarator in named_children(stmt):
            if declarator.type != "variable_declarator":
                continue
            bound = identifier_name(module.source, child_named(declarator, "name"))
            value = child_named(declarator, "value")
            if bound != name or value is None:
                continue
            literal = string_literal(module.source, value)
            if literal is not None:
                found.append(literal)
    if len(found) == 1:
        return found[0] or None
    if found:
        return None
    files = set(modules)
    aliases = next(iter(modules.values())).aliases if modules else {}
    for node in named_children(module.tree.root_node):
        if node.type != "import_statement":
            continue
        specifier = _import_specifier(module.source, node)
        if specifier is None:
            continue
        target_path = resolve_specifier(module.path, specifier, files, aliases)
        if target_path is None or target_path not in modules:
            continue
        target = modules[target_path]
        clause = next(
            (child for child in named_children(node) if child.type == "import_clause"),
            None,
        )
        if clause is None:
            continue
        for child in named_children(clause):
            if child.type != "named_imports":
                continue
            for spec in named_children(child):
                if spec.type != "import_specifier":
                    continue
                names = [
                    text_of(module.source, part)
                    for part in named_children(spec)
                    if part.type == "identifier"
                ]
                if not names:
                    continue
                imported, local = names[0], names[-1]
                if local == name:
                    return _const_string(target, imported, modules)
    return None


def _resolve_name(
    module: TsModule, node: Node | None, modules: dict[str, TsModule]
) -> str | None:
    if node is None:
        return None
    literal = string_literal(module.source, node)
    if literal is not None:
        return literal or None
    if node.type == "identifier":
        return _const_string(module, text_of(module.source, node), modules)
    return None


def _queue_type_arg(source: bytes, node: Node | None) -> str | None:
    """Return the type argument of Queue / Pick<Queue<T>, …> when unique."""
    if node is None:
        return None
    if node.type == "type_annotation":
        inner = next(iter(named_children(node)), None)
        return _queue_type_arg(source, inner)
    if node.type == "type_identifier":
        return None
    if node.type == "generic_type":
        name = identifier_name(source, child_named(node, "name")) or text_of(
            source, next(iter(named_children(node)), None)
        )
        args = child_named(node, "type_arguments") or next(
            (c for c in named_children(node) if c.type == "type_arguments"), None
        )
        if name == "Queue" and args is not None:
            allowed = {"type_identifier", "identifier"}
            type_args = [c for c in named_children(args) if c.type in allowed]
            if len(type_args) == 1:
                return text_of(source, type_args[0])
            return None
        if name == "Pick" and args is not None:
            first = next(iter(named_children(args)), None)
            return _queue_type_arg(source, first)
    return None


def _new_constructor(source: bytes, node: Node) -> Node | None:
    if node.type != "new_expression":
        return None
    return child_named(node, "constructor") or next(
        (
            child
            for child in named_children(node)
            if child.type in {"identifier", "member_expression"}
        ),
        None,
    )


def _new_arguments(node: Node) -> list[Node]:
    args = child_named(node, "arguments") or next(
        (child for child in named_children(node) if child.type == "arguments"),
        None,
    )
    if args is None:
        return []
    return list(named_children(args))


def _new_type_arg(source: bytes, node: Node) -> str | None:
    args = child_named(node, "type_arguments") or next(
        (child for child in named_children(node) if child.type == "type_arguments"),
        None,
    )
    if args is None:
        return None
    type_args = [
        child
        for child in named_children(args)
        if child.type in {"type_identifier", "identifier"}
    ]
    if len(type_args) != 1:
        return None
    return text_of(source, type_args[0])


def _enclosing_callable(module: TsModule, node: Node) -> str | None:
    best: str | None = None
    best_span: int | None = None
    for item in module.definitions:
        if item.kind not in _CALLABLE_KINDS:
            continue
        if item.node.start_byte <= node.start_byte < item.node.end_byte:
            span = item.node.end_byte - item.node.start_byte
            if best_span is None or span < best_span:
                best = item.qualified_name
                best_span = span
    return best


def _class_of_callable(module: TsModule, qualified_name: str) -> str | None:
    for item in module.definitions:
        if item.qualified_name == qualified_name and item.kind in {
            "typescript_method",
            "typescript_async_method",
        }:
            return item.owner
    return None


def _constructor_param_queue_type(
    module: TsModule, class_q: str, field: str, bindings: _BullmqBindings
) -> str | None:
    for item in module.definitions:
        if item.qualified_name != class_q or item.kind != "typescript_class":
            continue
        for node in walk_named(item.node):
            if node.type != "method_definition":
                continue
            name = text_of(module.source, child_named(node, "name"))
            if name != "constructor":
                continue
            params = child_named(node, "parameters") or child_named(
                node, "formal_parameters"
            )
            if params is None:
                continue
            for param in named_children(params):
                if param.type not in {"required_parameter", "optional_parameter"}:
                    continue
                pname = None
                annotation = None
                for child in named_children(param):
                    if child.type == "identifier" and pname is None:
                        pname = text_of(module.source, child)
                    if child.type == "type_annotation":
                        annotation = child
                if pname != field or annotation is None:
                    continue
                type_arg = _queue_type_arg(module.source, annotation)
                # Ensure Queue in the annotation resolves to bullmq.
                if type_arg is None:
                    return None
                if not _annotation_uses_bullmq_queue(
                    module.source, annotation, bindings
                ):
                    return None
                return type_arg
    return None


def _annotation_uses_bullmq_queue(
    source: bytes, annotation: Node, bindings: _BullmqBindings
) -> bool:
    for node in walk_named(annotation):
        if node.type != "type_identifier" and node.type != "identifier":
            continue
        name = text_of(source, node)
        if bindings.types.get(name) == "Queue" or bindings.values.get(name) == "Queue":
            return True
    return False


def _param_queue_type(
    module: TsModule, callable_q: str, param_name: str, bindings: _BullmqBindings
) -> str | None:
    for item in module.definitions:
        if item.qualified_name != callable_q or item.kind not in _CALLABLE_KINDS:
            continue
        params = child_named(item.node, "parameters") or child_named(
            item.node, "formal_parameters"
        )
        if params is None:
            # arrow / function expression may nest parameters differently
            for node in named_children(item.node):
                if node.type in {"formal_parameters", "parameters"}:
                    params = node
                    break
        if params is None:
            return None
        for param in named_children(params):
            if param.type not in {"required_parameter", "optional_parameter"}:
                continue
            pname = None
            annotation = None
            for child in named_children(param):
                if child.type == "identifier" and pname is None:
                    pname = text_of(module.source, child)
                if child.type == "type_annotation":
                    annotation = child
            if pname != param_name or annotation is None:
                continue
            if not _annotation_uses_bullmq_queue(module.source, annotation, bindings):
                return None
            return _queue_type_arg(module.source, annotation)
    return None


def _local_queue_bindings(
    module: TsModule,
    callable_q: str,
    bindings: _BullmqBindings,
    modules: dict[str, TsModule],
    issues: list[AdapterDiagnostic],
) -> dict[str, str]:
    """Map uniquely assigned local names → static queue name inside one callable."""
    counts: dict[str, int] = defaultdict(int)
    values: dict[str, str | None] = {}
    for item in module.definitions:
        if item.qualified_name != callable_q:
            continue
        body = body_of_definition(item) or item.node
        for node in walk_named(body):
            if node.type not in {"lexical_declaration", "variable_declaration"}:
                continue
            # Skip nested function scopes' outer walk noise by checking parent callable.
            owner = _enclosing_callable(module, node)
            if owner != callable_q:
                continue
            for declarator in named_children(node):
                if declarator.type != "variable_declarator":
                    continue
                name = identifier_name(module.source, child_named(declarator, "name"))
                value = child_named(declarator, "value")
                if name is None or value is None:
                    continue
                counts[name] += 1
                if value.type != "new_expression":
                    values[name] = None
                    continue
                ctor = _new_constructor(module.source, value)
                ctor_name = identifier_name(module.source, ctor)
                if ctor_name is None or bindings.values.get(ctor_name) != "Queue":
                    values[name] = None
                    continue
                args = _new_arguments(value)
                queue_name = _resolve_name(module, args[0] if args else None, modules)
                if queue_name is None:
                    issues.append(
                        AdapterDiagnostic(
                            "bullmq_queue_unresolved",
                            module.path,
                            value.start_point[0] + 1,
                        )
                    )
                    values[name] = None
                else:
                    values[name] = queue_name
    return {
        name: queue
        for name, queue in values.items()
        if counts[name] == 1 and isinstance(queue, str) and queue
    }


class BullMQMessagingAdapter:
    """Emit BullMQ MessageChannel publish/consume facts over TypeScript units."""

    allow_unverified_versions = True
    reviewed_deep_support = False

    descriptor = AdapterDescriptor(
        adapter_id="rkg.bullmq",
        adapter_version="0.1.0",
        contract_version=CONTRACT_VERSION,
        kind=AdapterKind.MESSAGING,
        language="typescript",
        framework="bullmq",
        grammar_or_target="BullMQ Queue/Worker supported subset",
        file_patterns=("*.ts", "*.tsx", "**/*.ts", "**/*.tsx"),
        ignore_patterns=("**/node_modules/**", "**/dist/**", "**/*.d.ts"),
        capabilities=("topics", "publishes", "consumes"),
        technology_constraints=(TechnologyConstraint("bullmq", ">=6.0,<7.0"),),
    )

    def technology_detectors(self) -> tuple[object, ...]:
        from rkg.detection.bullmq import BullMQDetector

        return (BullMQDetector(),)

    def detect(self, manifest: SourceManifest, parsed: ParseResult) -> DetectionReport:
        del manifest
        evidence: list[DetectionEvidence] = []
        for module in _modules(parsed).values():
            if _has_bullmq_import(module):
                evidence.append(DetectionEvidence(module.path, DETECT_RULE))
        if not evidence:
            return DetectionReport()
        unique = {(item.relative_path, item.rule_id): item for item in evidence}
        return DetectionReport(
            (TechnologyDetection("bullmq", None, tuple(unique.values())),)
        )

    def extract(
        self, context: AdapterContext, parsed: ParseResult, base: FactBatch
    ) -> AdapterResult:
        if (
            base.repository_id != context.repository_id
            or base.snapshot_id != context.snapshot_id
        ):
            raise ValueError("candidate ownership does not match adapter context")
        modules = _modules(parsed)
        entities = {item.id: item for item in base.entities}
        edges = {item.id: item for item in base.edges}
        evidence = {item.id: item for item in base.evidence}
        issues: list[AdapterDiagnostic] = []
        by_qn = {item.qualified_name: item for item in entities.values()}
        type_to_queues: dict[str, set[str]] = defaultdict(set)

        def ensure_channel(name: str, path: str, line: int) -> Entity:
            existing = by_qn.get(name)
            if existing is not None and existing.type == EntityType.MESSAGE_CHANNEL:
                return existing
            entity_id = message_channel_id(context.repository_id, "queue", "", name)
            entity = Entity(
                entity_id,
                context.repository_id,
                context.snapshot_id,
                EntityType.MESSAGE_CHANNEL,
                name,
                name,
                path,
                line,
                line,
                framework_kind="bullmq",
                attributes=(
                    ("channel_kind", "queue"),
                    ("name", name),
                    ("namespace", ""),
                ),
            )
            entities[entity.id] = entity
            by_qn[name] = entity
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

        # Pass 1: Queue/Worker constructions → channels (+ consumes for Worker).
        for module in modules.values():
            bindings = _bullmq_bindings(module)
            if not bindings.values and not bindings.types:
                continue
            for node in walk_named(module.tree.root_node):
                if node.type != "new_expression":
                    continue
                ctor = _new_constructor(module.source, node)
                ctor_name = identifier_name(module.source, ctor)
                if ctor_name is None:
                    continue
                kind = bindings.values.get(ctor_name)
                if kind not in {"Queue", "Worker"}:
                    continue
                args = _new_arguments(node)
                line = node.start_point[0] + 1
                queue_name = _resolve_name(module, args[0] if args else None, modules)
                if queue_name is None:
                    issues.append(
                        AdapterDiagnostic("bullmq_queue_unresolved", module.path, line)
                    )
                    continue
                channel = ensure_channel(queue_name, module.path, line)
                type_arg = _new_type_arg(module.source, node)
                if type_arg and kind == "Queue":
                    type_to_queues[type_arg].add(queue_name)
                if kind != "Worker":
                    continue
                caller_q = _enclosing_callable(module, node)
                if caller_q is None:
                    continue
                source = by_qn.get(caller_q)
                if source is None or source.type != EntityType.CALLABLE:
                    continue
                relate(
                    EdgeType.CONSUMES,
                    source,
                    channel,
                    module.path,
                    line,
                    CONSUME_RULE,
                )

        unique_type_queues = {
            type_arg: next(iter(names))
            for type_arg, names in type_to_queues.items()
            if len(names) == 1
        }

        # Pass 2: Queue.add → publishes when receiver + queue name resolve uniquely.
        for module in modules.values():
            bindings = _bullmq_bindings(module)
            if not bindings.values and not bindings.types:
                continue
            for node in walk_named(module.tree.root_node):
                if node.type != "call_expression":
                    continue
                func = child_named(node, "function") or next(
                    iter(named_children(node)), None
                )
                if func is None or func.type != "member_expression":
                    continue
                prop = child_named(func, "property") or named_children(func)[-1]
                if text_of(module.source, prop) != "add":
                    continue
                caller_q = _enclosing_callable(module, node)
                if caller_q is None:
                    continue
                source = by_qn.get(caller_q)
                if source is None or source.type != EntityType.CALLABLE:
                    continue
                args = child_named(node, "arguments") or next(
                    (c for c in named_children(node) if c.type == "arguments"),
                    None,
                )
                job_args = list(named_children(args)) if args is not None else []
                job_name = (
                    string_literal(module.source, job_args[0]) if job_args else None
                )
                if not job_name:
                    continue
                receiver = child_named(func, "object") or named_children(func)[0]
                queue_name = _resolve_publish_queue(
                    module,
                    receiver,
                    caller_q,
                    bindings,
                    modules,
                    unique_type_queues,
                    issues,
                )
                if queue_name is None:
                    continue
                channel = ensure_channel(
                    queue_name, module.path, node.start_point[0] + 1
                )
                relate(
                    EdgeType.PUBLISHES,
                    source,
                    channel,
                    module.path,
                    node.start_point[0] + 1,
                    PUBLISH_RULE,
                )

        unique_issues = {
            (item.code, item.relative_path, item.line): item for item in issues
        }
        diagnostics = tuple(
            sorted(
                unique_issues.values(),
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


def _resolve_publish_queue(
    module: TsModule,
    receiver: Node,
    caller_q: str,
    bindings: _BullmqBindings,
    modules: dict[str, TsModule],
    unique_type_queues: dict[str, str],
    issues: list[AdapterDiagnostic],
) -> str | None:
    del issues  # local unresolved constructions already recorded in pass 1
    # this.queue.add
    if receiver.type == "member_expression":
        obj = child_named(receiver, "object") or named_children(receiver)[0]
        prop = child_named(receiver, "property") or named_children(receiver)[-1]
        if text_of(module.source, obj) == "this":
            field = text_of(module.source, prop)
            class_q = _class_of_callable(module, caller_q)
            if class_q is None:
                return None
            type_arg = _constructor_param_queue_type(module, class_q, field, bindings)
            if type_arg is None:
                return None
            return unique_type_queues.get(type_arg)
        return None
    if receiver.type != "identifier":
        return None
    name = text_of(module.source, receiver)
    locals_map = _local_queue_bindings(module, caller_q, bindings, modules, [])
    if name in locals_map:
        return locals_map[name]
    type_arg = _param_queue_type(module, caller_q, name, bindings)
    if type_arg is None:
        return None
    return unique_type_queues.get(type_arg)
