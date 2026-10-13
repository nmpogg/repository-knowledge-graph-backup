"""Static NestJS controller extraction over parsed TypeScript units.

@Controller prefixes plus @Get/@Post (and the other verb decorators) become HTTP
Endpoints. @MessagePattern and @EventPattern become MessageChannel facts with
consumes edges when the handler method resolves uniquely. RouterModule and
setGlobalPrefix apply only for a unique literal. Analyzed modules are never
imported or executed.
"""

from __future__ import annotations

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
    TechnologyDetection,
)
from rkg.adapters.typescript_parse import (
    TsDefinition,
    TsModule,
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
    endpoint_id,
    evidence_id,
    message_channel_id,
)
from rkg.ingestion import SourceManifest

DETECT_RULE = "RKG.nest.detect.v1"
ROUTE_RULE = "RKG.nest.route.v1"
HANDLER_RULE = "RKG.nest.handler.v1"
CHANNEL_RULE = "RKG.nest.channel.v1"
CONSUME_RULE = "RKG.nest.consume.v1"
_MESSAGES = {
    "nest_route_dynamic": "Route path is not a unique static literal.",
    "nest_prefix_dynamic": "Controller or router prefix is not a unique literal.",
    "nest_prefix_ambiguous": "More than one static prefix applies.",
    "nest_handler_unresolved": "Nest handler does not resolve uniquely.",
    "nest_pattern_dynamic": "Message pattern is not a unique static literal.",
    "nest_controller_missing": "HTTP mapping is not on a static @Controller.",
    "nest_module_unresolved": "Router module controllers could not be resolved.",
}
_HTTP = {
    "Get": "GET",
    "Post": "POST",
    "Put": "PUT",
    "Patch": "PATCH",
    "Delete": "DELETE",
    "Head": "HEAD",
    "Options": "OPTIONS",
    "All": "ALL",
}
_PATTERNS = {
    "MessagePattern": "pattern",
    "EventPattern": "event",
}
_NEST_DECORATORS = frozenset({*_HTTP, *_PATTERNS, "Controller", "Module"})
_SECRET = "RKG_TEST_SECRET_DO_NOT_PERSIST"
_AMBIGUOUS = object()


def _modules(parsed: ParseResult) -> dict[str, TsModule]:
    return {
        unit.relative_path: unit.representation
        for unit in parsed.units
        if isinstance(unit.representation, TsModule)
    }


def _call_function(node: Node) -> Node | None:
    found = child_named(node, "function")
    if found is not None:
        return found
    return next(
        (child for child in named_children(node) if child.type != "arguments"),
        None,
    )


def _call_args(node: Node) -> tuple[Node, ...]:
    args = child_named(node, "arguments")
    if args is None:
        args = next(
            (child for child in named_children(node) if child.type == "arguments"),
            None,
        )
    if args is None:
        return ()
    return named_children(args)


def _safe(text: str | None) -> str | None:
    if text is None or _SECRET in text:
        return None
    return text


def _join(*parts: str) -> str:
    bits = [part.strip("/") for part in parts if part and part.strip("/")]
    if not bits:
        return "/"
    return "/" + "/".join(bits)


def _object_props(source: bytes, node: Node) -> dict[str, Node]:
    props: dict[str, Node] = {}
    if node.type != "object":
        return props
    for child in named_children(node):
        if child.type != "pair":
            continue
        key_node = child_named(child, "key")
        value = child_named(child, "value")
        if key_node is None or value is None:
            continue
        key = identifier_name(source, key_node) or string_literal(source, key_node)
        if key:
            props[key] = value
    return props


def _leading_decorators(node: Node) -> tuple[Node, ...]:
    found: list[Node] = []
    sibling = node.prev_named_sibling
    while sibling is not None and sibling.type == "decorator":
        found.append(sibling)
        sibling = sibling.prev_named_sibling
    found.reverse()
    return tuple(found)


def _decorator_call(
    source: bytes, decorator: Node
) -> tuple[str | None, tuple[Node, ...]]:
    inner = next(iter(named_children(decorator)), None)
    if inner is None:
        return None, ()
    if inner.type == "identifier":
        return text_of(source, inner), ()
    if inner.type != "call_expression":
        return None, ()
    func = _call_function(inner)
    name = identifier_name(source, func)
    return name, _call_args(inner)


def _imported_map(
    module: TsModule, specifier: str, allowed: frozenset[str]
) -> dict[str, str]:
    mapping: dict[str, str] = {}
    blocked: set[str] = set()
    for node in named_children(module.tree.root_node):
        if node.type != "import_statement":
            continue
        source_node = next(
            (child for child in named_children(node) if child.type == "string"),
            None,
        )
        if string_literal(module.source, source_node) != specifier:
            continue
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
                if not names or names[0] not in allowed:
                    continue
                local = names[-1]
                if local in mapping or local in blocked:
                    mapping.pop(local, None)
                    blocked.add(local)
                    continue
                mapping[local] = names[0]
    return mapping


def _follow_import(
    module: TsModule, name: str, modules: dict[str, TsModule]
) -> tuple[TsModule, str] | None:
    files = set(modules)
    aliases = module.aliases
    found: tuple[TsModule, str] | None = None
    hits = 0
    for node in named_children(module.tree.root_node):
        if node.type != "import_statement":
            continue
        source_node = next(
            (child for child in named_children(node) if child.type == "string"),
            None,
        )
        specifier = string_literal(module.source, source_node)
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
                    hits += 1
                    found = (target, imported)
    if hits == 1 and found is not None:
        return found
    return None


def _module_statements(module: TsModule) -> tuple[Node, ...]:
    statements: list[Node] = []
    for node in named_children(module.tree.root_node):
        target = node
        if node.type == "export_statement":
            declaration = child_named(node, "declaration")
            if declaration is None:
                continue
            target = declaration
        statements.append(target)
    return tuple(statements)


def _const_string(
    module: TsModule,
    name: str,
    modules: dict[str, TsModule],
    seen: set[tuple[str, str]] | None = None,
) -> str | None:
    trail = set() if seen is None else seen
    key = (module.path, name)
    if key in trail:
        return None
    trail.add(key)
    found: list[str | None] = []
    for statement in _module_statements(module):
        if statement.type not in {"lexical_declaration", "variable_declaration"}:
            continue
        for declarator in named_children(statement):
            if declarator.type != "variable_declarator":
                continue
            bound = identifier_name(module.source, child_named(declarator, "name"))
            if bound != name:
                continue
            value = child_named(declarator, "value")
            found.append(_safe(string_literal(module.source, value)))
    if len(found) != 1:
        return None if found else _imported_const(module, name, modules, trail)
    return found[0]


def _imported_const(
    module: TsModule,
    name: str,
    modules: dict[str, TsModule],
    seen: set[tuple[str, str]],
) -> str | None:
    imported = _follow_import(module, name, modules)
    if imported is None:
        return None
    target, imported_name = imported
    return _const_string(target, imported_name, modules, seen)


def _resolve_text(
    module: TsModule, node: Node | None, modules: dict[str, TsModule]
) -> str | None:
    if node is None:
        return None
    literal = _safe(string_literal(module.source, node))
    if literal is not None:
        return literal
    if node.type == "identifier":
        return _const_string(module, text_of(module.source, node), modules)
    if node.type == "object":
        path = _object_props(module.source, node).get("path")
        if path is None:
            return None
        return _resolve_text(module, path, modules)
    return None


def _definition_for(module: TsModule, node: Node) -> TsDefinition | None:
    for item in module.definitions:
        if item.node == node:
            return item
    return None


def _resolve_class(
    module: TsModule,
    name: str,
    modules: dict[str, TsModule],
    seen: set[tuple[str, str]] | None = None,
) -> str | None:
    trail = set() if seen is None else seen
    key = (module.path, name)
    if key in trail:
        return None
    trail.add(key)
    matches = [
        item.qualified_name
        for item in module.definitions
        if item.name == name
        and item.owner == module.name
        and item.kind == "typescript_class"
    ]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        return None
    imported = _follow_import(module, name, modules)
    if imported is None:
        return None
    target, imported_name = imported
    return _resolve_class(target, imported_name, modules, trail)


def _canonical(
    decorators: dict[str, str], source: bytes, decorator: Node
) -> tuple[str | None, tuple[Node, ...]]:
    local, args = _decorator_call(source, decorator)
    if local is None:
        return None, ()
    return decorators.get(local), args


class NestFrameworkAdapter:
    """Emit Nest HTTP endpoints and message channels. Not deep-supported."""

    reviewed_deep_support = False
    descriptor = AdapterDescriptor(
        adapter_id="rkg.nest",
        adapter_version="0.1.0",
        contract_version=CONTRACT_VERSION,
        kind=AdapterKind.FRAMEWORK,
        language="typescript",
        framework="nest",
        grammar_or_target="NestJS controller and message-pattern decorators",
        file_patterns=("*.ts", "*.tsx", "**/*.ts", "**/*.tsx"),
        ignore_patterns=("**/node_modules/**", "**/dist/**"),
        capabilities=("channels", "routes"),
    )

    def technology_detectors(self) -> tuple[object, ...]:
        return ()

    def detect(self, manifest: SourceManifest, parsed: ParseResult) -> DetectionReport:
        del manifest
        evidence: list[DetectionEvidence] = []
        for module in _modules(parsed).values():
            common = _imported_map(module, "@nestjs/common", _NEST_DECORATORS)
            core = _imported_map(
                module, "@nestjs/core", frozenset({"RouterModule", "NestFactory"})
            )
            if common or core:
                evidence.append(DetectionEvidence(module.path, DETECT_RULE))
        if not evidence:
            return DetectionReport()
        ordered = tuple(sorted(evidence, key=lambda item: item.relative_path))
        return DetectionReport((TechnologyDetection("nest", None, ordered),))

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

        def add_evidence(path: str, line: int, rule: str) -> str:
            ref = evidence_id(context.snapshot_id, path, line, line, rule)
            evidence[ref] = Evidence(ref, context.snapshot_id, path, line, line, rule)
            return ref

        global_prefix, global_ok = _global_prefix(modules, issues)
        router_prefixes = _router_prefixes(modules, issues)

        for module in modules.values():
            decorators = _imported_map(module, "@nestjs/common", _NEST_DECORATORS)
            if not decorators:
                continue
            classes = [
                item
                for item in module.definitions
                if item.kind == "typescript_class" and item.owner == module.name
            ]
            for klass in classes:
                prefix, prefix_ok = _controller_prefix(
                    module, klass, decorators, modules, issues
                )
                mount = router_prefixes.get(klass.qualified_name, "")
                if mount is _AMBIGUOUS:
                    issues.append(
                        AdapterDiagnostic(
                            "nest_prefix_ambiguous",
                            module.path,
                            klass.start_line,
                        )
                    )
                for method in module.definitions:
                    if (
                        method.owner != klass.qualified_name
                        or "method" not in method.kind
                    ):
                        continue
                    for decorator in _leading_decorators(method.node):
                        canon, args = _canonical(decorators, module.source, decorator)
                        line = decorator.start_point[0] + 1
                        if canon in _PATTERNS:
                            _emit_channel(
                                context,
                                module,
                                method,
                                canon,
                                args,
                                line,
                                modules,
                                entities,
                                edges,
                                by_qn,
                                issues,
                                add_evidence,
                            )
                            continue
                        if canon not in _HTTP:
                            continue
                        if not prefix_ok or not global_ok or mount is _AMBIGUOUS:
                            if not prefix_ok and prefix is None:
                                issues.append(
                                    AdapterDiagnostic(
                                        "nest_controller_missing", module.path, line
                                    )
                                )
                            continue
                        route = (
                            ""
                            if not args
                            else _resolve_text(module, args[0], modules)
                        )
                        if route is None:
                            issues.append(
                                AdapterDiagnostic(
                                    "nest_route_dynamic", module.path, line
                                )
                            )
                            continue
                        full = _join(
                            global_prefix,
                            "" if mount is _AMBIGUOUS else str(mount),
                            prefix or "",
                            route,
                        )
                        _emit_endpoint(
                            context,
                            module,
                            method,
                            _HTTP[canon],
                            full,
                            line,
                            entities,
                            edges,
                            by_qn,
                            issues,
                            add_evidence,
                        )

        diagnostics = tuple(
            sorted(
                set(issues),
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
                _MESSAGES[item.code],
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
        return AdapterResult(facts, self._capabilities(), diagnostics)

    def resolve(
        self, context: AdapterContext, parsed: ParseResult, candidate: FactBatch
    ) -> AdapterResult:
        del parsed
        if (
            candidate.repository_id != context.repository_id
            or candidate.snapshot_id != context.snapshot_id
        ):
            raise ValueError("candidate ownership does not match adapter context")
        return AdapterResult(candidate, self._capabilities())

    @staticmethod
    def _capabilities() -> tuple[Capability, ...]:
        return tuple(
            Capability(name, SupportState.DETECTED_ONLY)
            for name in sorted(NestFrameworkAdapter.descriptor.capabilities)
        )


def _global_prefix(
    modules: dict[str, TsModule], issues: list[AdapterDiagnostic]
) -> tuple[str, bool]:
    literals: set[str] = set()
    dynamic = False
    for module in modules.values():
        core = _imported_map(
            module, "@nestjs/core", frozenset({"RouterModule", "NestFactory"})
        )
        if not core and not _imported_map(module, "@nestjs/common", _NEST_DECORATORS):
            continue
        for node in walk_named(module.tree.root_node):
            if node.type != "call_expression":
                continue
            func = _call_function(node)
            if func is None or func.type != "member_expression":
                continue
            prop = identifier_name(module.source, child_named(func, "property"))
            if prop != "setGlobalPrefix":
                continue
            line = node.start_point[0] + 1
            args = _call_args(node)
            text = _resolve_text(module, args[0] if args else None, modules)
            if text is None:
                dynamic = True
                issues.append(
                    AdapterDiagnostic("nest_prefix_dynamic", module.path, line)
                )
            else:
                literals.add(text)
    if dynamic or len(literals) > 1:
        if len(literals) > 1:
            issues.append(AdapterDiagnostic("nest_prefix_ambiguous", None, None))
        return "", False
    if len(literals) == 1:
        return next(iter(literals)), True
    return "", True


def _router_prefixes(
    modules: dict[str, TsModule], issues: list[AdapterDiagnostic]
) -> dict[str, object]:
    """Map controller qualified name to one router prefix, or _AMBIGUOUS."""
    assigned: dict[str, set[str]] = {}
    for module in modules.values():
        routers = _imported_map(
            module, "@nestjs/core", frozenset({"RouterModule", "NestFactory"})
        )
        if "RouterModule" not in set(routers.values()):
            continue
        local_routers = {
            local
            for local, canon in routers.items()
            if canon == "RouterModule"
        }
        for node in walk_named(module.tree.root_node):
            if node.type != "call_expression":
                continue
            func = _call_function(node)
            if func is None or func.type != "member_expression":
                continue
            obj = identifier_name(module.source, child_named(func, "object"))
            prop = identifier_name(module.source, child_named(func, "property"))
            if prop != "register" or obj not in local_routers:
                continue
            line = node.start_point[0] + 1
            args = _call_args(node)
            entries = _register_entries(module, args[0] if args else None, modules)
            if entries is None:
                issues.append(
                    AdapterDiagnostic("nest_prefix_dynamic", module.path, line)
                )
                continue
            for path, module_name in entries:
                if path is None:
                    issues.append(
                        AdapterDiagnostic("nest_prefix_dynamic", module.path, line)
                    )
                    continue
                if module_name is None:
                    issues.append(
                        AdapterDiagnostic("nest_module_unresolved", module.path, line)
                    )
                    continue
                class_qn = _resolve_class(module, module_name, modules)
                if class_qn is None:
                    issues.append(
                        AdapterDiagnostic("nest_module_unresolved", module.path, line)
                    )
                    continue
                controllers = _module_controller_names(modules, class_qn)
                if controllers is None:
                    issues.append(
                        AdapterDiagnostic("nest_module_unresolved", module.path, line)
                    )
                    continue
                for controller in controllers:
                    assigned.setdefault(controller, set()).add(path)
    result: dict[str, object] = {}
    for controller, paths in assigned.items():
        if len(paths) == 1:
            result[controller] = next(iter(paths))
        else:
            result[controller] = _AMBIGUOUS
    return result


def _register_entries(
    module: TsModule, node: Node | None, modules: dict[str, TsModule]
) -> list[tuple[str | None, str | None]] | None:
    if node is None or node.type != "array":
        return None
    entries: list[tuple[str | None, str | None]] = []
    for child in named_children(node):
        if child.type != "object":
            return None
        props = _object_props(module.source, child)
        path_node = props.get("path")
        module_node = props.get("module")
        path = _resolve_text(module, path_node, modules) if path_node else None
        module_name = (
            text_of(module.source, module_node)
            if module_node is not None and module_node.type == "identifier"
            else None
        )
        entries.append((path, module_name))
    return entries


def _module_controller_names(
    modules: dict[str, TsModule], module_class_qn: str
) -> list[str] | None:
    for module in modules.values():
        decorators = _imported_map(module, "@nestjs/common", _NEST_DECORATORS)
        for item in module.definitions:
            if item.qualified_name != module_class_qn:
                continue
            for decorator in _leading_decorators(item.node):
                canon, args = _canonical(decorators, module.source, decorator)
                if canon != "Module" or not args or args[0].type != "object":
                    continue
                controllers = _object_props(module.source, args[0]).get("controllers")
                if controllers is None:
                    return []
                if controllers.type != "array":
                    return None
                names: list[str] = []
                for element in named_children(controllers):
                    if element.type != "identifier":
                        return None
                    class_qn = _resolve_class(
                        module, text_of(module.source, element), modules
                    )
                    if class_qn is None:
                        return None
                    names.append(class_qn)
                return names
    return None


def _controller_prefix(
    module: TsModule,
    klass: TsDefinition,
    decorators: dict[str, str],
    modules: dict[str, TsModule],
    issues: list[AdapterDiagnostic],
) -> tuple[str | None, bool]:
    for decorator in _leading_decorators(klass.node):
        canon, args = _canonical(decorators, module.source, decorator)
        if canon != "Controller":
            continue
        if not args:
            return "", True
        text = _resolve_text(module, args[0], modules)
        if text is None:
            issues.append(
                AdapterDiagnostic(
                    "nest_prefix_dynamic",
                    module.path,
                    decorator.start_point[0] + 1,
                )
            )
            return "", False
        return text, True
    return None, False


def _emit_channel(
    context: AdapterContext,
    module: TsModule,
    method: TsDefinition,
    canon: str,
    args: tuple[Node, ...],
    line: int,
    modules: dict[str, TsModule],
    entities: dict[str, Entity],
    edges: dict[str, Edge],
    by_qn: dict[str, Entity],
    issues: list[AdapterDiagnostic],
    add_evidence,
) -> None:
    pattern = "" if not args else _resolve_text(module, args[0], modules)
    if not pattern:
        issues.append(AdapterDiagnostic("nest_pattern_dynamic", module.path, line))
        return
    kind = _PATTERNS[canon]
    entity_id = message_channel_id(context.repository_id, kind, "", pattern)
    current = entities.get(entity_id)
    if current is None or current.type != EntityType.MESSAGE_CHANNEL:
        channel = Entity(
            entity_id,
            context.repository_id,
            context.snapshot_id,
            EntityType.MESSAGE_CHANNEL,
            pattern,
            pattern,
            module.path,
            line,
            line,
            framework_kind="nest",
            attributes=(
                ("channel_kind", kind),
                ("name", pattern),
                ("namespace", ""),
            ),
        )
        entities[channel.id] = channel
        by_qn[pattern] = channel
    else:
        channel = current
    add_evidence(module.path, line, CHANNEL_RULE)
    handler = by_qn.get(method.qualified_name)
    if handler is None or handler.type != EntityType.CALLABLE:
        issues.append(AdapterDiagnostic("nest_handler_unresolved", module.path, line))
        return
    ref = add_evidence(module.path, method.start_line, CONSUME_RULE)
    edge_key = edge_id(
        context.snapshot_id, EdgeType.CONSUMES, handler.id, channel.id
    )
    edges[edge_key] = Edge(
        edge_key,
        context.snapshot_id,
        EdgeType.CONSUMES,
        handler.id,
        channel.id,
        CONSUME_RULE,
        (ref,),
    )


def _emit_endpoint(
    context: AdapterContext,
    module: TsModule,
    method: TsDefinition,
    method_name: str,
    path: str,
    line: int,
    entities: dict[str, Entity],
    edges: dict[str, Edge],
    by_qn: dict[str, Entity],
    issues: list[AdapterDiagnostic],
    add_evidence,
) -> None:
    endpoint_qn = f"{method.qualified_name} {method_name} {path}"
    entity_id = endpoint_id(
        context.repository_id,
        module.path,
        endpoint_qn,
        method_name,
        path,
        (method.qualified_name,),
    )
    entities[entity_id] = Entity(
        entity_id,
        context.repository_id,
        context.snapshot_id,
        EntityType.ENDPOINT,
        path,
        endpoint_qn,
        module.path,
        line,
        line,
        framework_kind="nest",
        attributes=(("method", method_name), ("path", path)),
    )
    add_evidence(module.path, line, ROUTE_RULE)
    handler = by_qn.get(method.qualified_name)
    if handler is None or handler.type != EntityType.CALLABLE:
        issues.append(AdapterDiagnostic("nest_handler_unresolved", module.path, line))
        return
    ref = add_evidence(module.path, method.start_line, HANDLER_RULE)
    edge_key = edge_id(
        context.snapshot_id, EdgeType.HANDLED_BY, entity_id, handler.id
    )
    edges[edge_key] = Edge(
        edge_key,
        context.snapshot_id,
        EdgeType.HANDLED_BY,
        entity_id,
        handler.id,
        HANDLER_RULE,
        (ref,),
    )
