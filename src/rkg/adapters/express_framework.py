"""Static Express route extraction over parsed TypeScript units.

HTTP verb calls with a unique path literal or resolved string constant become
Endpoint facts. ``app.use`` / ``router.use`` are middleware evidence only.
Analyzed modules are never imported or executed.
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
)
from rkg.ingestion import SourceManifest

DETECT_RULE = "RKG.express.detect.v1"
ROUTE_RULE = "RKG.express.route.v1"
HANDLER_RULE = "RKG.express.handler.v1"
MIDDLEWARE_RULE = "RKG.express.middleware.v1"
_MESSAGES = {
    "express_route_dynamic": "Route path is not a unique static literal.",
    "express_handler_unresolved": "Route handler does not resolve uniquely.",
    "express_receiver_shadowed": "Express application binding is shadowed.",
}
_VERBS = {
    "get": "GET",
    "post": "POST",
    "put": "PUT",
    "patch": "PATCH",
    "delete": "DELETE",
    "head": "HEAD",
    "options": "OPTIONS",
    "all": "ALL",
}
_FUNCTION_TYPES = frozenset(
    {
        "function_declaration",
        "generator_function_declaration",
        "arrow_function",
        "function_expression",
        "generator_function",
        "method_definition",
    }
)
_SECRET = "RKG_TEST_SECRET_DO_NOT_PERSIST"


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


def _member_parts(source: bytes, node: Node) -> tuple[str | None, str | None]:
    obj = child_named(node, "object")
    prop = child_named(node, "property")
    return identifier_name(source, obj), identifier_name(source, prop)


def _safe(text: str | None) -> str | None:
    if text is None or _SECRET in text:
        return None
    return text


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


def _param_names(source: bytes, node: Node) -> set[str]:
    params = child_named(node, "parameters")
    if params is None:
        return set()
    names: set[str] = set()
    for child in named_children(params):
        ident = child_named(child, "pattern") or child_named(child, "name")
        if ident is None:
            ident = next(
                (part for part in named_children(child) if part.type == "identifier"),
                None,
            )
        name = identifier_name(source, ident)
        if name:
            names.add(name)
    return names


def _block_binding(source: bytes, block: Node, name: str) -> Node | None | bool:
    """Return the unique value node, False when missing, None when not a string."""
    found: list[Node | None] = []
    for child in named_children(block):
        if child.type not in {"lexical_declaration", "variable_declaration"}:
            continue
        for declarator in named_children(child):
            if declarator.type != "variable_declarator":
                continue
            bound = identifier_name(source, child_named(declarator, "name"))
            if bound != name:
                continue
            found.append(child_named(declarator, "value"))
    if not found:
        return False
    if len(found) != 1:
        return None
    return found[0]


def _enclosing_string(source: bytes, node: Node, name: str) -> str | None | bool:
    """Unique enclosing string literal, False if unbound, None if shadowed."""
    current = node.parent
    while current is not None:
        if current.type == "statement_block":
            binding = _block_binding(source, current, name)
            if binding is not False:
                if binding is None:
                    return None
                return _safe(string_literal(source, binding))
        if current.type in _FUNCTION_TYPES and name in _param_names(source, current):
            return None
        current = current.parent
    return False


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
    if len(found) > 1:
        return None
    if len(found) == 1:
        return found[0]
    imported = _follow_import(module, name, modules)
    if imported is None:
        return None
    target, imported_name = imported
    return _const_string(target, imported_name, modules, trail)


def _resolve_text(
    module: TsModule, node: Node | None, modules: dict[str, TsModule]
) -> str | None:
    if node is None:
        return None
    literal = _safe(string_literal(module.source, node))
    if literal is not None:
        return literal
    if node.type != "identifier":
        return None
    name = text_of(module.source, node)
    enclosing = _enclosing_string(module.source, node, name)
    if enclosing is not False:
        return enclosing
    return _const_string(module, name, modules)


def _express_locals(module: TsModule) -> tuple[set[str], set[str]]:
    factories: set[str] = set()
    routers: set[str] = set()
    for node in named_children(module.tree.root_node):
        if node.type != "import_statement":
            continue
        source_node = next(
            (child for child in named_children(node) if child.type == "string"),
            None,
        )
        specifier = string_literal(module.source, source_node)
        if specifier is None or specifier.split("/", 1)[0] != "express":
            continue
        clause = next(
            (child for child in named_children(node) if child.type == "import_clause"),
            None,
        )
        if clause is None:
            continue
        for child in named_children(clause):
            if child.type == "identifier":
                factories.add(text_of(module.source, child))
            elif child.type == "named_imports":
                for spec in named_children(child):
                    if spec.type != "import_specifier":
                        continue
                    names = [
                        text_of(module.source, part)
                        for part in named_children(spec)
                        if part.type == "identifier"
                    ]
                    if names and names[0] == "Router":
                        routers.add(names[-1])
    return factories, routers


def _is_factory(
    source: bytes, node: Node, factories: set[str], routers: set[str]
) -> bool:
    func = _call_function(node)
    if func is None:
        return False
    if func.type == "identifier":
        name = text_of(source, func)
        return name in factories or name in routers
    if func.type == "member_expression":
        obj, prop = _member_parts(source, func)
        return prop == "Router" and obj in factories
    return False


def _receivers(module: TsModule, factories: set[str], routers: set[str]) -> set[str]:
    counts: dict[str, int] = {}
    kinds: dict[str, bool] = {}
    for statement in _module_statements(module):
        if statement.type not in {"lexical_declaration", "variable_declaration"}:
            continue
        for declarator in named_children(statement):
            if declarator.type != "variable_declarator":
                continue
            bound = identifier_name(module.source, child_named(declarator, "name"))
            value = child_named(declarator, "value")
            if not bound or value is None or value.type != "call_expression":
                continue
            counts[bound] = counts.get(bound, 0) + 1
            kinds[bound] = _is_factory(module.source, value, factories, routers)
    return {name for name, count in counts.items() if count == 1 and kinds.get(name)}


def _locally_bound(source: bytes, node: Node, name: str) -> bool:
    return _enclosing_string(source, node, name) is not False


def _assignment_count(module: TsModule, name: str) -> int:
    count = 0
    for statement in _module_statements(module):
        expressions = (
            named_children(statement)
            if statement.type == "expression_statement"
            else (statement,)
        )
        for node in expressions:
            if node.type != "assignment_expression":
                continue
            left = child_named(node, "left")
            if identifier_name(module.source, left) == name:
                count += 1
    return count


def _callable_nodes(module: TsModule, name: str) -> tuple[list[Node], int]:
    """Function nodes bound to ``name``, plus non-callable declarations."""
    functions: list[Node] = []
    other = 0
    for statement in _module_statements(module):
        if statement.type in {
            "function_declaration",
            "generator_function_declaration",
        }:
            bound = identifier_name(module.source, child_named(statement, "name"))
            if bound == name:
                functions.append(statement)
            continue
        if statement.type not in {"lexical_declaration", "variable_declaration"}:
            continue
        for declarator in named_children(statement):
            if declarator.type != "variable_declarator":
                continue
            bound = identifier_name(module.source, child_named(declarator, "name"))
            if bound != name:
                continue
            value = child_named(declarator, "value")
            if value is not None and value.type in {
                "arrow_function",
                "function_expression",
                "generator_function",
            }:
                functions.append(value)
            else:
                other += 1
    return functions, other


def _local_callable(module: TsModule, name: str) -> str | None | bool:
    """One module-level callable, False if unbound, None if ambiguous."""
    functions, other = _callable_nodes(module, name)
    if _assignment_count(module, name) or other or len(functions) > 1:
        return None
    if not functions:
        return False
    node = functions[0]
    found = [
        item.qualified_name
        for item in module.definitions
        if item.name == name
        and item.owner == module.name
        and "function" in item.kind
        and item.node == node
    ]
    if len(found) == 1:
        return found[0]
    return None


def _unique_callable(
    module: TsModule, node: Node, modules: dict[str, TsModule]
) -> str | None:
    if node.type != "identifier":
        return None
    name = text_of(module.source, node)
    if _locally_bound(module.source, node, name):
        return None
    local = _local_callable(module, name)
    if local is not False:
        return local
    imported = _follow_import(module, name, modules)
    if imported is None:
        return None
    target, imported_name = imported
    resolved = _local_callable(target, imported_name)
    if resolved is False:
        return None
    return resolved


class ExpressFrameworkAdapter:
    """Emit Express Endpoint facts. Not a reviewed deep-supported profile."""

    reviewed_deep_support = False
    descriptor = AdapterDescriptor(
        adapter_id="rkg.express",
        adapter_version="0.1.0",
        contract_version=CONTRACT_VERSION,
        kind=AdapterKind.FRAMEWORK,
        language="typescript",
        framework="express",
        grammar_or_target="Express application and Router verb calls",
        file_patterns=("*.ts", "*.tsx", "**/*.ts", "**/*.tsx"),
        ignore_patterns=("**/node_modules/**", "**/dist/**"),
        capabilities=("routes",),
    )

    def technology_detectors(self) -> tuple[object, ...]:
        return ()

    def detect(self, manifest: SourceManifest, parsed: ParseResult) -> DetectionReport:
        del manifest
        evidence = [
            DetectionEvidence(module.path, DETECT_RULE)
            for module in _modules(parsed).values()
            if any(_express_locals(module))
        ]
        if not evidence:
            return DetectionReport()
        ordered = tuple(sorted(evidence, key=lambda item: item.relative_path))
        return DetectionReport((TechnologyDetection("express", None, ordered),))

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
            evidence[ref] = Evidence(
                ref, context.snapshot_id, path, line, line, rule
            )
            return ref

        for module in modules.values():
            factories, routers = _express_locals(module)
            if not factories and not routers:
                continue
            receivers = _receivers(module, factories, routers)
            for node in walk_named(module.tree.root_node):
                if node.type != "call_expression":
                    continue
                func = _call_function(node)
                if func is None or func.type != "member_expression":
                    continue
                receiver, prop = _member_parts(module.source, func)
                if receiver is None or prop is None or receiver not in receivers:
                    continue
                line = node.start_point[0] + 1
                if _locally_bound(module.source, node, receiver):
                    issues.append(
                        AdapterDiagnostic(
                            "express_receiver_shadowed", module.path, line
                        )
                    )
                    continue
                if prop == "use":
                    add_evidence(module.path, line, MIDDLEWARE_RULE)
                    continue
                method = _VERBS.get(prop)
                if method is None:
                    continue
                args = _call_args(node)
                route = _resolve_text(module, args[0] if args else None, modules)
                if route is None:
                    issues.append(
                        AdapterDiagnostic("express_route_dynamic", module.path, line)
                    )
                    continue
                handler_node = args[-1] if len(args) > 1 else None
                handler_qn = (
                    _unique_callable(module, handler_node, modules)
                    if handler_node is not None
                    else None
                )
                if handler_qn is None:
                    issues.append(
                        AdapterDiagnostic(
                            "express_handler_unresolved", module.path, line
                        )
                    )
                for extra in args[1:-1]:
                    if extra.type == "identifier":
                        add_evidence(module.path, line, MIDDLEWARE_RULE)
                        break
                handler = by_qn.get(handler_qn) if handler_qn else None
                endpoint_qn = f"{module.name}.{method} {route}"
                entity_id = endpoint_id(
                    context.repository_id,
                    module.path,
                    endpoint_qn,
                    method,
                    route,
                    (module.path, str(line)),
                )
                entities[entity_id] = Entity(
                    entity_id,
                    context.repository_id,
                    context.snapshot_id,
                    EntityType.ENDPOINT,
                    route,
                    endpoint_qn,
                    module.path,
                    line,
                    line,
                    framework_kind="express",
                    attributes=(("method", method), ("path", route)),
                )
                add_evidence(module.path, line, ROUTE_RULE)
                if handler is None:
                    continue
                href = add_evidence(
                    handler.file_path or module.path,
                    handler.start_line or line,
                    HANDLER_RULE,
                )
                edge_key = edge_id(
                    context.snapshot_id,
                    EdgeType.HANDLED_BY,
                    entity_id,
                    handler.id,
                )
                edges[edge_key] = Edge(
                    edge_key,
                    context.snapshot_id,
                    EdgeType.HANDLED_BY,
                    entity_id,
                    handler.id,
                    HANDLER_RULE,
                    (href,),
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
            for name in sorted(ExpressFrameworkAdapter.descriptor.capabilities)
        )
