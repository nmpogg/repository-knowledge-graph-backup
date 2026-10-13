"""Static TanStack Router navigation-route extraction over TypeScript parse units.

Routes come from createFileRoute and createRoute. A parent path is joined only
when getParentRoute resolves to exactly one route. navigate({ to }) and Link to
emit calls only when that destination equals exactly one navigation route whose
handler is exactly one Callable. Analyzed modules are never imported or executed.
"""

from __future__ import annotations

from dataclasses import dataclass, field

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
from rkg.adapters.route_flow import route_flow_attrs
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
from rkg.adapters.typescript_resolution import _default_export_target
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

ROUTE_RULE = "RKG.tanstack_router.route.v1"
HANDLER_RULE = "RKG.tanstack_router.handler.v1"
NAVIGATE_RULE = "RKG.tanstack_router.navigate.v1"
DETECT_RULE = "RKG.tanstack_router.detect.v1"
_PACKAGE = "@tanstack/react-router"
_NESTED = frozenset(
    {
        "function_declaration",
        "generator_function_declaration",
        "arrow_function",
        "function_expression",
        "generator_function",
        "method_definition",
    }
)
_MESSAGES = {
    "tanstack_route_dynamic": "TanStack route path is not a unique static literal.",
    "tanstack_parent_unresolved": "TanStack parent route did not resolve uniquely.",
    "tanstack_parent_cycle": "TanStack parent route cycle was skipped.",
    "tanstack_component_unresolved": "TanStack route component was not unique.",
    "tanstack_navigate_unresolved": "Navigation destination did not match one route.",
    "tanstack_navigate_ambiguous": "Navigation destination matches several routes.",
    "tanstack_navigate_shadow": "Navigation call is shadowed and was not linked.",
}


@dataclass(frozen=True, slots=True)
class _Location:
    path: str
    line: int


@dataclass(slots=True)
class _Route:
    binding: str | None
    module_path: str
    line: int
    kind: str
    segment: str | None
    parent_name: str | None
    parent_failed: bool
    component: str | None
    parent: _Route | None = None
    full: str | None = None
    fail: str | None = None
    ready: bool = False


@dataclass
class _Facts:
    context: AdapterContext
    entities: dict[str, Entity]
    edges: dict[str, Edge]
    evidence: dict[str, Evidence]
    diagnostics: list[Diagnostic]
    issues: list[AdapterDiagnostic] = field(default_factory=list)

    def issue(self, code: str, path: str, line: int) -> None:
        self.issues.append(AdapterDiagnostic(code, path, line))

    def edge(
        self, kind: EdgeType, source: str, target: str, location: _Location, rule: str
    ) -> None:
        ref = evidence_id(
            self.context.snapshot_id, location.path, location.line, location.line, rule
        )
        self.evidence[ref] = Evidence(
            ref,
            self.context.snapshot_id,
            location.path,
            location.line,
            location.line,
            rule,
        )
        key = edge_id(self.context.snapshot_id, kind, source, target)
        current = self.edges.get(key)
        references = set(current.evidence_ids) if current else set()
        references.add(ref)
        self.edges[key] = Edge(
            key,
            self.context.snapshot_id,
            kind,
            source,
            target,
            rule,
            tuple(sorted(references)),
        )


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
        if key and key not in props:
            props[key] = value
        elif key:
            props[key] = value
            props[f"__dup__{key}"] = value
    return props


def _same_node(left: Node | None, right: Node | None) -> bool:
    if left is None or right is None:
        return False
    return (
        left.type == right.type
        and left.start_byte == right.start_byte
        and left.end_byte == right.end_byte
    )


def _is_nested(node: Node) -> bool:
    current = node.parent
    while current is not None:
        if current.type in _NESTED:
            return True
        current = current.parent
    return False


def _binding_name(node: Node, source: bytes) -> str | None:
    parent = node.parent
    if parent is None or parent.type != "variable_declarator":
        return None
    if not _same_node(child_named(parent, "value"), node) or _is_nested(parent):
        return None
    return identifier_name(source, child_named(parent, "name"))


def _join(parent: str, child: str) -> str:
    if child.startswith("/"):
        return child
    if parent in {"", "/"}:
        return f"/{child}" if child else "/"
    return f"{parent.rstrip('/')}/{child}"


def _local_string(module: TsModule, name: str) -> str | None:
    """Return a module-level string when that binding is declared exactly once."""
    declared = 0
    literal: str | None = None
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
            if bound != name:
                continue
            declared += 1
            value = child_named(declarator, "value")
            found = string_literal(module.source, value) if value is not None else None
            literal = found if declared == 1 else None
    return literal if declared == 1 else None


def _const_string(
    module: TsModule,
    name: str,
    modules: dict[str, TsModule],
    seen: set[tuple[str, str]],
) -> str | None:
    key = (module.path, name)
    if key in seen:
        return None
    seen.add(key)
    if _declaration_count(module, name):
        return _local_string(module, name)
    imported = _imported_symbol(module, name, modules)
    if imported is None:
        return None
    target, exported = imported
    return _const_string(target, exported, modules, seen)


def _declaration_count(module: TsModule, name: str) -> int:
    count = 0
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
            if identifier_name(module.source, child_named(declarator, "name")) == name:
                count += 1
    return count


def _imported_symbol(
    module: TsModule, local_name: str, modules: dict[str, TsModule]
) -> tuple[TsModule, str] | None:
    files = set(modules)
    aliases = module.aliases
    hits: list[tuple[TsModule, str]] = []
    for node in named_children(module.tree.root_node):
        if node.type != "import_statement":
            continue
        source_node = next(
            (child for child in named_children(node) if child.type == "string"), None
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
            if (
                child.type == "identifier"
                and text_of(module.source, child) == local_name
            ):
                default_name = _default_export_target(target)
                if default_name is not None and "." in default_name:
                    hits.append((target, default_name.rsplit(".", 1)[-1]))
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
                if local == local_name:
                    hits.append((target, imported))
    if len(hits) != 1:
        return None
    return hits[0]


def _path_value(
    module: TsModule, value: Node, modules: dict[str, TsModule]
) -> str | None:
    literal = string_literal(module.source, value)
    if literal is not None:
        return literal
    if value.type == "identifier":
        return _const_string(module, text_of(module.source, value), modules, set())
    if value.type == "jsx_expression":
        inner = named_children(value)
        if len(inner) == 1:
            return _path_value(module, inner[0], modules)
    return None


def _tanstack_imports(module: TsModule) -> dict[str, str]:
    """Map a local binding to the @tanstack/react-router export, if unique."""
    found: dict[str, list[str]] = {}
    for node in named_children(module.tree.root_node):
        if node.type != "import_statement":
            continue
        source_node = next(
            (child for child in named_children(node) if child.type == "string"), None
        )
        specifier = string_literal(module.source, source_node)
        if specifier is None:
            continue
        if specifier != _PACKAGE and not specifier.startswith(f"{_PACKAGE}/"):
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
                if not names:
                    continue
                imported, local = names[0], names[-1]
                found.setdefault(local, []).append(imported)
    resolved: dict[str, str] = {}
    for local, imported in found.items():
        unique = set(imported)
        if len(unique) == 1 and len(imported) == 1:
            resolved[local] = imported[0]
    return resolved


def _module_defined(module: TsModule, name: str) -> bool:
    return any(
        item.owner == module.name and item.name == name for item in module.definitions
    )


def _callee_name(source: bytes, node: Node) -> str | None:
    return identifier_name(source, child_named(node, "function"))


def _first_object_arg(source: bytes, node: Node) -> Node | None:
    del source
    args = child_named(node, "arguments")
    if args is None:
        return None
    objects = [child for child in named_children(args) if child.type == "object"]
    if len(named_children(args)) != 1 or len(objects) != 1:
        return None
    return objects[0]


def _returned_identifier(source: bytes, node: Node) -> str | None:
    body = child_named(node, "body")
    if body is None:
        return None
    if body.type == "identifier":
        return text_of(source, body)
    if body.type != "statement_block":
        return None
    returns = [
        child for child in named_children(body) if child.type == "return_statement"
    ]
    if len(returns) != 1 or len(named_children(body)) != 1:
        return None
    inner = named_children(returns[0])
    if len(inner) == 1 and inner[0].type == "identifier":
        return text_of(source, inner[0])
    return None


def _resolve_component(
    module: TsModule, local_name: str, modules: dict[str, TsModule]
) -> str | None:
    locals_ = [
        item.qualified_name
        for item in module.definitions
        if item.owner == module.name and item.name == local_name
    ]
    if len(locals_) == 1:
        return locals_[0]
    if len(locals_) > 1:
        return None
    imported = _imported_symbol(module, local_name, modules)
    if imported is None:
        return None
    target, exported = imported
    if exported == local_name and not any(
        item.name == exported and item.owner == target.name
        for item in target.definitions
    ):
        default_target = _default_export_target(target)
        if default_target:
            return default_target
    qualified = f"{target.name}.{exported}"
    matches = [
        item.qualified_name
        for item in target.definitions
        if item.qualified_name == qualified
    ]
    return matches[0] if len(matches) == 1 else None


def _lookup_callable(entities: dict[str, Entity], qualified_name: str) -> Entity | None:
    matches = [
        item
        for item in entities.values()
        if item.type == EntityType.CALLABLE and item.qualified_name == qualified_name
    ]
    return matches[0] if len(matches) == 1 else None


def _enclosing_callable(module: TsModule, node: Node) -> TsDefinition | None:
    matches = [
        item
        for item in module.definitions
        if item.node.start_byte <= node.start_byte
        and item.node.end_byte >= node.end_byte
        and ("function" in item.kind or item.kind.endswith("method"))
    ]
    if not matches:
        return None
    return min(matches, key=lambda item: item.node.end_byte - item.node.start_byte)


def _is_use_navigate_call(module: TsModule, value: Node, use_nav_name: str) -> bool:
    if value.type != "call_expression":
        return False
    if _callee_name(module.source, value) != use_nav_name:
        return False
    args = child_named(value, "arguments")
    return args is not None and not named_children(args)


def _closest_declarator(module: TsModule, call: Node, name: str) -> Node | None:
    candidates: list[Node] = []
    for node in walk_named(module.tree.root_node):
        if node.type != "variable_declarator" or node.start_byte >= call.start_byte:
            continue
        if identifier_name(module.source, child_named(node, "name")) != name:
            continue
        scope = node.parent
        while (
            scope is not None and scope.type not in _NESTED and scope.type != "program"
        ):
            scope = scope.parent
        if scope is None:
            continue
        if scope.type != "program" and not (
            scope.start_byte <= call.start_byte and call.end_byte <= scope.end_byte
        ):
            continue
        candidates.append(node)
    if not candidates:
        return None
    return max(candidates, key=lambda item: item.start_byte)


def _function_in_scope(module: TsModule, call: Node, name: str) -> bool:
    if _module_defined(module, name):
        return any(
            item.name == name and item.node.start_byte < call.start_byte
            for item in module.definitions
        )
    return False


def _navigate_status(module: TsModule, call: Node, imports: dict[str, str]) -> str:
    """Return ok, shadow, or ignore for a navigate({ to }) call."""
    callee = _callee_name(module.source, call)
    if callee is None:
        return "ignore"
    use_nav = [
        local for local, exported in imports.items() if exported == "useNavigate"
    ]
    use_nav_name = use_nav[0] if len(use_nav) == 1 else None
    binding = _closest_declarator(module, call, callee)
    if binding is not None:
        value = child_named(binding, "value")
        if (
            use_nav_name is not None
            and value is not None
            and _is_use_navigate_call(module, value, use_nav_name)
            and not _module_defined(module, use_nav_name)
        ):
            return "ok"
        return "shadow" if callee == "navigate" else "ignore"
    if callee != "navigate" and imports.get(callee) != "navigate":
        return "ignore"
    if _function_in_scope(module, call, callee) or _module_defined(module, callee):
        return "shadow"
    if imports.get(callee) == "navigate":
        return "ok"
    return "shadow"


def _jsx_name(source: bytes, node: Node) -> str | None:
    target = node
    if node.type == "jsx_element":
        target = child_named(node, "open_tag") or node
    name_node = child_named(target, "name")
    if name_node is None or name_node.type != "identifier":
        return None
    return text_of(source, name_node)


def _link_to_nodes(source: bytes, node: Node) -> list[Node]:
    target = node
    if node.type == "jsx_element":
        opening = child_named(node, "open_tag")
        if opening is None:
            return []
        target = opening
    found: list[Node] = []
    for child in named_children(target):
        if child.type != "jsx_attribute":
            continue
        parts = [part for part in named_children(child)]
        if not parts or parts[0].type not in {"property_identifier", "identifier"}:
            continue
        if text_of(source, parts[0]) != "to":
            continue
        found.append(child)
    return found


def _has_spread(node: Node) -> bool:
    return any(child.type == "spread_element" for child in named_children(node))


def _attribute_value(source: bytes, attribute: Node) -> Node | None:
    del source
    parts = [
        part
        for part in named_children(attribute)
        if part.type not in {"property_identifier", "identifier"}
    ]
    if len(parts) != 1:
        return None
    return parts[0]


def _collect_routes(
    module: TsModule,
    modules: dict[str, TsModule],
    facts: _Facts,
) -> list[_Route]:
    imports = _tanstack_imports(module)
    if not imports:
        return []
    routes: list[_Route] = []
    for node in walk_named(module.tree.root_node):
        if node.type != "call_expression":
            continue
        parent = node.parent
        if (
            parent is not None
            and parent.type == "call_expression"
            and _same_node(child_named(parent, "function"), node)
        ):
            continue
        line = node.start_point[0] + 1
        file_call = _file_route_call(module, node, imports)
        if file_call is not None:
            if _is_nested(node):
                facts.issue("tanstack_route_dynamic", module.path, line)
                continue
            path_node, options = file_call
            segment = (
                _path_value(module, path_node, modules)
                if path_node is not None
                else None
            )
            if segment is None:
                facts.issue("tanstack_route_dynamic", module.path, line)
                continue
            routes.append(
                _Route(
                    binding=_binding_name(node, module.source),
                    module_path=module.path,
                    line=line,
                    kind="file",
                    segment=segment,
                    parent_name=None,
                    parent_failed=False,
                    component=_component_name(module, options),
                )
            )
            continue
        callee = _callee_name(module.source, node)
        if callee is None or imports.get(callee) != "createRoute":
            continue
        if _module_defined(module, callee) or _is_nested(node):
            facts.issue("tanstack_route_dynamic", module.path, line)
            continue
        options = _first_object_arg(module.source, node)
        if options is None:
            facts.issue("tanstack_route_dynamic", module.path, line)
            continue
        props = _object_props(module.source, options)
        if (
            _has_spread(options)
            or "__dup__path" in props
            or "__dup__component" in props
            or "__dup__getParentRoute" in props
        ):
            facts.issue("tanstack_route_dynamic", module.path, line)
            continue
        path_node = props.get("path")
        segment = (
            _path_value(module, path_node, modules) if path_node is not None else None
        )
        if path_node is None or segment is None:
            facts.issue("tanstack_route_dynamic", module.path, line)
            continue
        parent_name, parent_failed = _parent_name(module, props.get("getParentRoute"))
        routes.append(
            _Route(
                binding=_binding_name(node, module.source),
                module_path=module.path,
                line=line,
                kind="code",
                segment=segment,
                parent_name=parent_name,
                parent_failed=parent_failed,
                component=_component_name(module, options),
            )
        )
    return routes


def _file_route_call(
    module: TsModule, node: Node, imports: dict[str, str]
) -> tuple[Node | None, Node | None] | None:
    function = child_named(node, "function")
    if function is not None and function.type == "call_expression":
        callee = _callee_name(module.source, function)
        if callee is None or imports.get(callee) != "createFileRoute":
            return None
        if _module_defined(module, callee):
            return None
        args = child_named(function, "arguments")
        path_node = None
        if args is not None:
            named = named_children(args)
            if len(named) == 1:
                path_node = named[0]
        options = _first_object_arg(module.source, node)
        return path_node, options
    callee = _callee_name(module.source, node)
    if callee is None or imports.get(callee) != "createFileRoute":
        return None
    if _module_defined(module, callee):
        return None
    args = child_named(node, "arguments")
    if args is None:
        return None, None
    named = named_children(args)
    if len(named) != 1:
        return None, None
    return named[0], None


def _component_name(module: TsModule, options: Node | None) -> str | None:
    if options is None or options.type != "object":
        return None
    props = _object_props(module.source, options)
    if "__dup__component" in props:
        return None
    component = props.get("component")
    if component is None or component.type != "identifier":
        return None
    return text_of(module.source, component)


def _parent_name(module: TsModule, node: Node | None) -> tuple[str | None, bool]:
    if node is None:
        return None, False
    if node.type not in {"arrow_function", "function_expression"}:
        return None, True
    name = _returned_identifier(module.source, node)
    if name is None:
        return None, True
    return name, False


def _link_parents(routes: list[_Route], modules: dict[str, TsModule]) -> None:
    by_binding: dict[tuple[str, str], list[_Route]] = {}
    for route in routes:
        if route.binding:
            by_binding.setdefault((route.module_path, route.binding), []).append(route)
    modules_by_path = modules

    def resolve(
        module_path: str, name: str, seen: set[tuple[str, str]]
    ) -> list[_Route]:
        key = (module_path, name)
        if key in seen:
            return []
        seen.add(key)
        local = by_binding.get(key, [])
        if local:
            return local
        module = modules_by_path.get(module_path)
        if module is None or _declaration_count(module, name):
            return []
        imported = _imported_symbol(module, name, modules_by_path)
        if imported is None:
            return []
        target, exported = imported
        return resolve(target.path, exported, seen)

    for route in routes:
        if route.kind != "code" or route.parent_name is None:
            continue
        hits = resolve(route.module_path, route.parent_name, set())
        if len(hits) == 1 and hits[0] is not route:
            route.parent = hits[0]
        else:
            route.parent_failed = True


def _assign_paths(routes: list[_Route]) -> None:
    def walk(route: _Route, stack: list[int]) -> None:
        if route.ready:
            return
        identity = id(route)
        if identity in stack:
            route.fail = "tanstack_parent_cycle"
            route.full = None
            route.ready = True
            return
        stack.append(identity)
        segment = route.segment or ""
        if route.kind == "file":
            route.full = segment
        elif segment.startswith("/"):
            route.full = segment
            if route.parent_failed:
                route.fail = "tanstack_parent_unresolved"
        elif route.parent is None:
            route.fail = "tanstack_parent_unresolved"
            route.full = None
        else:
            walk(route.parent, stack)
            if route.parent.fail == "tanstack_parent_cycle":
                route.fail = "tanstack_parent_cycle"
                route.full = None
            elif route.parent.full is None:
                route.fail = "tanstack_parent_unresolved"
                route.full = None
            else:
                route.full = _join(route.parent.full, segment)
        stack.pop()
        route.ready = True

    for route in routes:
        walk(route, [])


def _emit_routes(
    routes: list[_Route],
    modules: dict[str, TsModule],
    facts: _Facts,
) -> None:
    for route in routes:
        if route.fail:
            facts.issue(route.fail, route.module_path, route.line)
        if route.full is None:
            continue
        chain = (
            "route:"
            f"{route.module_path}:{route.line}:{route.full}:{route.binding or ''}",
        )
        identifier = endpoint_id(
            facts.context.repository_id,
            route.module_path,
            "navigation",
            "",
            route.full,
            chain,
        )
        location = _Location(route.module_path, route.line)
        ref = evidence_id(
            facts.context.snapshot_id,
            location.path,
            location.line,
            location.line,
            ROUTE_RULE,
        )
        facts.evidence[ref] = Evidence(
            ref,
            facts.context.snapshot_id,
            location.path,
            location.line,
            location.line,
            ROUTE_RULE,
        )
        base_attrs: list[tuple[str, object]] = [
            ("kind", "navigation"),
            ("path", route.full),
            ("route_path", route.full),
            ("registration_chain", chain),
        ]
        handler: Entity | None = None
        if route.component is not None:
            module = modules[route.module_path]
            binding = _resolve_component(module, route.component, modules)
            handler = _lookup_callable(facts.entities, binding) if binding else None
            if handler is None:
                facts.issue(
                    "tanstack_component_unresolved", route.module_path, route.line
                )
        extra: tuple[tuple[str, str], ...] = ()
        if handler is not None:
            extra = route_flow_attrs(handler, facts.entities, facts.edges)
        facts.entities[identifier] = Entity(
            identifier,
            facts.context.repository_id,
            facts.context.snapshot_id,
            EntityType.ENDPOINT,
            route.full,
            f"navigation:{route.full}",
            route.module_path,
            route.line,
            route.line,
            framework_kind="tanstack-router",
            attributes=tuple(base_attrs) + extra,
        )
        if handler is not None:
            facts.edge(
                EdgeType.HANDLED_BY, identifier, handler.id, location, HANDLER_RULE
            )


def _record_navigation(
    module: TsModule,
    modules: dict[str, TsModule],
    facts: _Facts,
    by_path: dict[str, list[str | None]],
) -> None:
    imports = _tanstack_imports(module)
    if not imports:
        return
    link_locals = [local for local, exported in imports.items() if exported == "Link"]
    link_name = link_locals[0] if len(link_locals) == 1 else None
    link_shadow = bool(link_name and _module_defined(module, link_name))

    def visit_destination(
        node: Node, destination: Node | None, *, shadowed: bool
    ) -> None:
        line = node.start_point[0] + 1
        if shadowed:
            facts.issue("tanstack_navigate_shadow", module.path, line)
            return
        if destination is None:
            facts.issue("tanstack_navigate_unresolved", module.path, line)
            return
        target_path = _path_value(module, destination, modules)
        if target_path is None:
            facts.issue("tanstack_navigate_unresolved", module.path, line)
            return
        handlers = by_path.get(target_path, [])
        if len(handlers) == 0:
            facts.issue("tanstack_navigate_unresolved", module.path, line)
            return
        if len(handlers) != 1 or handlers[0] is None:
            facts.issue(
                "tanstack_navigate_ambiguous"
                if len(handlers) != 1
                else "tanstack_navigate_unresolved",
                module.path,
                line,
            )
            return
        caller_def = _enclosing_callable(module, node)
        caller = (
            _lookup_callable(facts.entities, caller_def.qualified_name)
            if caller_def is not None
            else None
        )
        if caller is None:
            facts.issue("tanstack_navigate_unresolved", module.path, line)
            return
        facts.edge(
            EdgeType.CALLS,
            caller.id,
            handlers[0],
            _Location(module.path, line),
            NAVIGATE_RULE,
        )

    for node in walk_named(module.tree.root_node):
        if node.type == "call_expression":
            status = _navigate_status(module, node, imports)
            if status == "ignore":
                continue
            destination = _to_property(module, node)
            if destination is False:
                continue
            visit_destination(
                node,
                destination if isinstance(destination, Node) else None,
                shadowed=status == "shadow",
            )
            continue
        if node.type not in {"jsx_self_closing_element", "jsx_element"}:
            continue
        name = _jsx_name(module.source, node)
        if link_name is None or name != link_name:
            continue
        attrs = _link_to_nodes(module.source, node)
        if len(attrs) != 1:
            visit_destination(node, None, shadowed=link_shadow)
            continue
        visit_destination(
            node, _attribute_value(module.source, attrs[0]), shadowed=link_shadow
        )


def _to_property(module: TsModule, call: Node) -> Node | None | bool:
    """Return the `to` value, None when it is not static, or False when absent."""
    args = child_named(call, "arguments")
    if args is None:
        return False
    named = named_children(args)
    if len(named) != 1 or named[0].type != "object" or _has_spread(named[0]):
        return None
    props = _object_props(module.source, named[0])
    if "__dup__to" in props:
        return None
    if "to" not in props:
        return False
    return props["to"]


def _index_handlers(
    routes: list[_Route],
    modules: dict[str, TsModule],
    facts: _Facts,
) -> dict[str, list[str | None]]:
    grouped: dict[str, list[str | None]] = {}
    for route in routes:
        if route.full is None:
            continue
        chain = (
            "route:"
            f"{route.module_path}:{route.line}:{route.full}:{route.binding or ''}",
        )
        identifier = endpoint_id(
            facts.context.repository_id,
            route.module_path,
            "navigation",
            "",
            route.full,
            chain,
        )
        entity = facts.entities.get(identifier)
        if entity is None:
            continue
        handler_id = None
        for edge in facts.edges.values():
            if edge.type == EdgeType.HANDLED_BY and edge.source_id == identifier:
                handler_id = edge.target_id
                break
        grouped.setdefault(route.full, []).append(handler_id)
    del modules
    return grouped


class TanStackRouterDetector:
    """Surface @tanstack/react-router evidence so deep selection can run."""

    def detect(self, manifest: SourceManifest, parsed: ParseResult) -> object:
        from rkg.detection.contracts import FrameworkObservation

        report = TanStackRouterFrameworkAdapter().detect(manifest, parsed)
        return FrameworkObservation(report)


class TanStackRouterFrameworkAdapter:
    """Extract static TanStack Router navigation paths. Not deep-supported."""

    entrypoint_required = False
    allow_unverified_versions = True
    reviewed_deep_support = False
    descriptor = AdapterDescriptor(
        adapter_id="rkg.tanstack-router",
        adapter_version="0.1.0",
        contract_version=CONTRACT_VERSION,
        kind=AdapterKind.FRAMEWORK,
        language="typescript",
        framework="tanstack-router",
        grammar_or_target="tree-sitter TypeScript/TSX + TanStack Router static routes",
        file_patterns=("*.ts", "*.tsx", "**/*.ts", "**/*.tsx"),
        ignore_patterns=("**/node_modules/**", "**/*.d.ts"),
        capabilities=("app", "routes"),
        technology_constraints=(TechnologyConstraint("tanstack-router", ">=1.0,<2.0"),),
    )

    def technology_detectors(self) -> tuple[object, ...]:
        return (TanStackRouterDetector(),)

    def detect(self, manifest: SourceManifest, parsed: ParseResult) -> DetectionReport:
        evidence: list[DetectionEvidence] = []
        for unit in parsed.units:
            if unit.language != "typescript" or not isinstance(
                unit.representation, TsModule
            ):
                continue
            module: TsModule = unit.representation
            if (
                _PACKAGE.encode("utf-8") not in module.source
                and b"createFileRoute" not in module.source
            ):
                continue
            if (
                _tanstack_imports(module)
                or b"createFileRoute" in module.source
                or b"createRoute" in module.source
            ):
                evidence.append(DetectionEvidence(module.path, DETECT_RULE))
        for item in manifest.files:
            if (
                item.relative_path.endswith("package.json")
                and _PACKAGE.encode("utf-8") in item.content
            ):
                evidence.append(DetectionEvidence(item.relative_path, DETECT_RULE))
        if not evidence:
            return DetectionReport()
        unique = tuple(
            DetectionEvidence(path, rule)
            for path, rule in sorted(
                {(item.relative_path, item.rule_id) for item in evidence}
            )
        )
        return DetectionReport((TechnologyDetection("tanstack-router", None, unique),))

    def extract(
        self, context: AdapterContext, parsed: ParseResult, base: FactBatch
    ) -> AdapterResult:
        if (
            base.repository_id != context.repository_id
            or base.snapshot_id != context.snapshot_id
        ):
            raise ValueError("candidate ownership does not match adapter context")
        modules = {
            unit.relative_path: unit.representation
            for unit in parsed.units
            if unit.language == "typescript"
            and isinstance(unit.representation, TsModule)
        }
        facts = _Facts(
            context,
            {item.id: item for item in base.entities},
            {item.id: item for item in base.edges},
            {item.id: item for item in base.evidence},
            list(base.diagnostics),
        )
        routes: list[_Route] = []
        for module in modules.values():
            routes.extend(_collect_routes(module, modules, facts))
        _link_parents(routes, modules)
        _assign_paths(routes)
        _emit_routes(routes, modules, facts)
        by_path = _index_handlers(routes, modules, facts)
        for module in modules.values():
            _record_navigation(module, modules, facts, by_path)
        issues = tuple(
            sorted(
                set(facts.issues),
                key=lambda item: (item.relative_path or "", item.line or 0, item.code),
            )
        )
        for ordinal, item in enumerate(issues):
            facts.diagnostics.append(
                Diagnostic(
                    diagnostic_id(
                        context.job_id,
                        item.code,
                        item.relative_path,
                        item.line,
                        ordinal,
                    ),
                    context.job_id,
                    Severity.WARNING,
                    item.code,
                    _MESSAGES[item.code],
                    context.snapshot_id,
                    item.relative_path,
                    item.line,
                )
            )
        batch = FactBatch(
            context.repository_id,
            context.snapshot_id,
            tuple(facts.entities[key] for key in sorted(facts.entities)),
            tuple(facts.edges[key] for key in sorted(facts.edges)),
            tuple(facts.evidence[key] for key in sorted(facts.evidence)),
            tuple(facts.diagnostics),
        )
        return AdapterResult(batch, self._capabilities(), issues)

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
            for name in TanStackRouterFrameworkAdapter.descriptor.capabilities
        )
