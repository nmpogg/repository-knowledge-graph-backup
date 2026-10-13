"""Static React Router navigation-route extraction over TypeScript parse units.

UI navigation routes reuse Endpoint with framework_kind=react-router and
attributes kind=navigation (no HTTP method, no repository EXPOSES). When a
static route element resolves to a page Callable, emit handled_by so view=flow
can expand route → page → calls. Analyzed modules are never imported or executed.
"""

from __future__ import annotations

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
from rkg.adapters.route_flow import route_flow_attrs
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

ROUTE_RULE = "RKG.react_router.route.v1"
HANDLER_RULE = "RKG.react_router.handler.v1"
NAVIGATE_RULE = "RKG.react_router.navigate.v1"
DETECT_RULE = "RKG.react_router.detect.v1"
_MESSAGES = {
    "react_router_route_dynamic": "Route path is not a unique static literal.",
    "react_router_unresolved": "React Router registration could not be resolved.",
    "react_router_navigate_dynamic": (
        "Navigation target is not a unique static literal."
    ),
    "react_router_navigate_ambiguous": (
        "Navigation target matches more than one route."
    ),
    "react_router_navigate_shadowed": (
        "Navigation API is shadowed and was not resolved."
    ),
    "react_router_navigate_unresolved": (
        "Navigation target does not match exactly one route."
    ),
}
_ROUTER_FACTORIES = frozenset(
    {"createBrowserRouter", "createHashRouter", "createMemoryRouter"}
)
_ROUTER_SPECIFIERS = frozenset({"react-router-dom", "react-router"})
_NAV_COMPONENTS = frozenset({"Link", "NavLink", "Navigate"})
_HISTORY_FACTORIES = frozenset(
    {"useHistory", "createBrowserHistory", "createHashHistory", "createMemoryHistory"}
)


@dataclass(frozen=True, slots=True)
class _Location:
    path: str
    line: int


def _join(parent: str | None, child: str | None, *, index: bool) -> str | None:
    if index:
        if parent is None or parent == "":
            return "/"
        return parent
    if child is None:
        return None
    if child == "*":
        return "*"
    if child.startswith("/"):
        return child
    if parent is None or parent in {"", "/"}:
        return f"/{child}" if not child.startswith("/") else child
    return f"{parent.rstrip('/')}/{child}"


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


def _const_string(
    module: TsModule, name: str, modules: dict[str, TsModule]
) -> str | None:
    """Resolve a uniquely assigned module-level string constant, including imports."""
    # Local binding
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
            if bound == name and value is not None:
                literal = string_literal(module.source, value)
                return literal
    # Imported binding
    files = set(modules)
    aliases = next(iter(modules.values())).aliases if modules else {}
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


def _path_value(
    module: TsModule, value: Node, modules: dict[str, TsModule]
) -> str | None:
    literal = string_literal(module.source, value)
    if literal is not None:
        return literal
    if value.type == "identifier":
        return _const_string(module, text_of(module.source, value), modules)
    return None


def _jsx_component_name(source: bytes, node: Node | None) -> str | None:
    """Return the component identifier from a JSX element/value, if unique."""
    if node is None:
        return None
    target = node
    if node.type == "jsx_element":
        opening = child_named(node, "open_tag") or next(
            (
                child
                for child in named_children(node)
                if child.type == "jsx_opening_element"
            ),
            None,
        )
        target = opening if opening is not None else node
    if target.type in {"jsx_self_closing_element", "jsx_opening_element"}:
        name_node = child_named(target, "name") or next(
            (
                child
                for child in named_children(target)
                if child.type in {"identifier", "member_expression"}
            ),
            None,
        )
        if name_node is None:
            return None
        if name_node.type == "identifier":
            return text_of(source, name_node)
        # member_expression (Foo.Bar) — not a unique page binding
        return None
    if target.type == "identifier":
        return text_of(source, target)
    return None


def _resolve_component_binding(
    module: TsModule, local_name: str, modules: dict[str, TsModule]
) -> str | None:
    """Resolve a JSX component identifier to a Callable/Type qualified_name."""
    # Local module-level definition (const Page = () => … / function Page).
    for item in module.definitions:
        if item.owner == module.name and item.name == local_name:
            return item.qualified_name
    files = set(modules)
    aliases = next(iter(modules.values())).aliases if modules else {}
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
            if child.type == "identifier":
                if text_of(module.source, child) != local_name:
                    continue
                return _default_export_target(target)
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
                if local != local_name:
                    continue
                return f"{target.name}.{imported}"
    return None


def _lookup_callable(
    entities: dict[str, Entity], qualified_name: str
) -> Entity | None:
    matches = [
        item
        for item in entities.values()
        if item.type == EntityType.CALLABLE and item.qualified_name == qualified_name
    ]
    return matches[0] if len(matches) == 1 else None


def _collect_routes(
    module: TsModule,
    array: Node,
    parent: str | None,
    modules: dict[str, TsModule],
    diagnostics: list[AdapterDiagnostic],
) -> list[tuple[str, _Location, str | None]]:
    routes: list[tuple[str, _Location, str | None]] = []
    for element in named_children(array):
        line = element.start_point[0] + 1
        if element.type == "spread_element":
            diagnostics.append(
                AdapterDiagnostic("react_router_route_dynamic", module.path, line)
            )
            continue
        if element.type == "ternary_expression" or element.type == "binary_expression":
            diagnostics.append(
                AdapterDiagnostic("react_router_route_dynamic", module.path, line)
            )
            continue
        if element.type != "object":
            continue
        props = _object_props(module.source, element)
        index = "index" in props and text_of(module.source, props["index"]) == "true"
        path_node = props.get("path")
        path_value = (
            _path_value(module, path_node, modules) if path_node is not None else None
        )
        if path_node is not None and path_value is None:
            diagnostics.append(
                AdapterDiagnostic("react_router_route_dynamic", module.path, line)
            )
        element_name = _jsx_component_name(module.source, props.get("element"))
        joined = _join(parent, path_value, index=index)
        if joined is not None:
            routes.append((joined, _Location(module.path, line), element_name))
        # Pathless layout continues with same parent.
        next_parent = (
            joined
            if joined is not None and not index
            else (parent if path_node is None else joined)
        )
        if index:
            next_parent = parent if parent is not None else joined
        if path_node is None and not index:
            next_parent = parent
        elif joined is not None and not index:
            next_parent = joined
        children = props.get("children")
        if children is not None and children.type == "array":
            routes.extend(
                _collect_routes(module, children, next_parent, modules, diagnostics)
            )
    return routes


def _find_route_arrays(
    module: TsModule, modules: dict[str, TsModule]
) -> list[tuple[Node, _Location]]:
    found: list[tuple[Node, _Location]] = []
    # createBrowserRouter(appRoutes) or createBrowserRouter([...])
    for node in walk_named(module.tree.root_node):
        if node.type != "call_expression":
            continue
        callee = child_named(node, "function")
        name = identifier_name(module.source, callee)
        if name not in _ROUTER_FACTORIES:
            continue
        args = child_named(node, "arguments")
        if args is None or not named_children(args):
            continue
        arg = named_children(args)[0]
        line = node.start_point[0] + 1
        if arg.type == "array":
            found.append((arg, _Location(module.path, line)))
        elif arg.type == "identifier":
            array = _bound_array(module, text_of(module.source, arg))
            if array is not None:
                found.append((array, _Location(module.path, line)))
    return found


def _diagnose_dynamic_route_objects(
    module: TsModule,
    modules: dict[str, TsModule],
    diagnostics: list[AdapterDiagnostic],
) -> None:
    """Emit diagnostics for RouteObject-like `{ path: <non-static> }` shapes."""
    if b"react-router" not in module.source:
        return
    for node in walk_named(module.tree.root_node):
        if node.type != "object":
            continue
        props = _object_props(module.source, node)
        path_node = props.get("path")
        if path_node is None:
            continue
        if _path_value(module, path_node, modules) is not None:
            continue
        # Runtime / non-literal path — diagnostic only (no guessed route).
        diagnostics.append(
            AdapterDiagnostic(
                "react_router_route_dynamic",
                module.path,
                path_node.start_point[0] + 1,
            )
        )


def _bound_array(module: TsModule, name: str) -> Node | None:
    matches: list[Node] = []
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
            if bound == name and value is not None and value.type == "array":
                matches.append(value)
    return matches[0] if len(matches) == 1 else None


@dataclass(frozen=True, slots=True)
class _Binding:
    name: str
    kind: str
    start: int
    end: int
    value: Node | None = None
    symbol: str | None = None
    specifier: str | None = None


@dataclass(frozen=True, slots=True)
class _Dest:
    status: str
    value: str | None = None


def _unwrap_expr(node: Node | None) -> Node | None:
    current = node
    while current is not None and current.type in {
        "as_expression",
        "type_assertion",
        "parenthesized_expression",
        "non_null_expression",
        "satisfies_expression",
    }:
        inner = child_named(current, "expression") or next(
            (child for child in named_children(current) if child.is_named), None
        )
        if inner is None or inner == current:
            break
        current = inner
    return current


def _scope_bounds(node: Node, root: Node) -> tuple[int, int]:
    current = node.parent
    while current is not None:
        if current.type in {
            "statement_block",
            "function_declaration",
            "generator_function_declaration",
            "arrow_function",
            "function_expression",
            "method_definition",
        }:
            return current.start_byte, current.end_byte
        current = current.parent
    return root.start_byte, root.end_byte


def _router_imports(module: TsModule) -> dict[str, tuple[str, str]]:
    """Local name → (exported symbol, module specifier) for React Router."""
    found: dict[str, tuple[str, str]] = {}
    for node in named_children(module.tree.root_node):
        if node.type != "import_statement":
            continue
        source_node = next(
            (child for child in named_children(node) if child.type == "string"), None
        )
        specifier = string_literal(module.source, source_node)
        if specifier not in _ROUTER_SPECIFIERS:
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
                found[names[-1]] = (names[0], specifier)
    return found


def _collect_bindings(module: TsModule) -> list[_Binding]:
    root = module.tree.root_node
    bindings: list[_Binding] = []
    for local, (symbol, specifier) in _router_imports(module).items():
        bindings.append(
            _Binding(
                local,
                "import",
                root.start_byte,
                root.end_byte,
                symbol=symbol,
                specifier=specifier,
            )
        )
    for node in walk_named(root):
        if node.type == "variable_declarator":
            name = identifier_name(module.source, child_named(node, "name"))
            value = child_named(node, "value")
            if not name:
                continue
            start, end = _scope_bounds(node, root)
            bindings.append(_Binding(name, "value", start, end, value))
        elif node.type in {
            "function_declaration",
            "generator_function_declaration",
        }:
            name = identifier_name(module.source, child_named(node, "name"))
            if not name:
                continue
            start, end = _scope_bounds(node, root)
            bindings.append(_Binding(name, "function", start, end))
    return bindings


def _innermost(
    bindings: list[_Binding], name: str, pos: int
) -> _Binding | None | str:
    hits = [
        item
        for item in bindings
        if item.name == name and item.start <= pos < item.end
    ]
    if not hits:
        return None
    rank = {"function": 0, "value": 1, "import": 2}
    hits.sort(key=lambda item: (item.end - item.start, rank.get(item.kind, 9)))
    best = hits[0]
    span = best.end - best.start
    best_rank = rank.get(best.kind, 9)
    tied = [
        item
        for item in hits
        if item.end - item.start == span and rank.get(item.kind, 9) == best_rank
    ]
    if len(tied) > 1:
        return "ambiguous"
    return best


def _imported_symbol(binding: _Binding | None | str, symbol: str) -> bool:
    return (
        isinstance(binding, _Binding)
        and binding.kind == "import"
        and binding.symbol == symbol
    )


def _is_use_navigate_value(module: TsModule, binding: _Binding | None | str) -> bool:
    if not isinstance(binding, _Binding) or binding.kind != "value":
        return False
    value = _unwrap_expr(binding.value)
    if value is None or value.type != "call_expression":
        return False
    callee = identifier_name(module.source, child_named(value, "function"))
    if callee is None:
        return False
    imported = _innermost(_collect_bindings(module), callee, value.start_byte)
    return _imported_symbol(imported, "useNavigate") or (
        callee == "useNavigate" and _imported_symbol(imported, "useNavigate")
    )


def _is_history_value(
    module: TsModule, binding: _Binding | None | str, bindings: list[_Binding]
) -> bool:
    if not isinstance(binding, _Binding):
        return False
    if binding.kind == "import" and binding.symbol == "history":
        return binding.specifier in _ROUTER_SPECIFIERS or binding.specifier == "history"
    if binding.kind != "value":
        return False
    value = _unwrap_expr(binding.value)
    if value is None or value.type != "call_expression":
        return False
    callee = identifier_name(module.source, child_named(value, "function"))
    if callee is None:
        return False
    imported = _innermost(bindings, callee, value.start_byte)
    return isinstance(imported, _Binding) and imported.symbol in _HISTORY_FACTORIES


def _call_arg(node: Node) -> Node | None:
    args = child_named(node, "arguments")
    if args is None:
        return None
    named = named_children(args)
    return named[0] if named else None


def _jsx_name(source: bytes, node: Node) -> str | None:
    name_node = child_named(node, "name") or next(
        (
            child
            for child in named_children(node)
            if child.type in {"identifier", "member_expression"}
        ),
        None,
    )
    if name_node is None or name_node.type != "identifier":
        return None
    return text_of(source, name_node)


def _jsx_to_expr(source: bytes, node: Node) -> Node | None:
    for attr in named_children(node):
        if attr.type != "jsx_attribute":
            continue
        key_node = child_named(attr, "name") or next(
            (
                child
                for child in named_children(attr)
                if child.type == "property_identifier"
            ),
            None,
        )
        key = identifier_name(source, key_node)
        if key != "to":
            # property_identifier is not always a field
            names = [
                text_of(source, child)
                for child in named_children(attr)
                if child.type == "property_identifier"
            ]
            if "to" not in names:
                continue
        value = next(
            (
                child
                for child in named_children(attr)
                if child.type != "property_identifier"
            ),
            None,
        )
        if value is None:
            return None
        if value.type == "jsx_expression":
            inner = next((child for child in named_children(value)), None)
            return inner
        return value
    return None


def _static_path(
    module: TsModule,
    node: Node | None,
    modules: dict[str, TsModule],
    bindings: list[_Binding],
    seen: set[str],
) -> _Dest:
    current = _unwrap_expr(node)
    if current is None:
        return _Dest("dynamic")
    if current.type == "template_string" and any(
        child.type == "template_substitution" for child in current.children
    ):
        return _Dest("dynamic")
    literal = string_literal(module.source, current)
    if literal is not None:
        path = literal.split("?", 1)[0].split("#", 1)[0].strip()
        if not path or any(char.isspace() for char in path):
            return _Dest("dynamic")
        return _Dest("ok", path)
    if current.type == "identifier":
        name = text_of(module.source, current)
        if name in seen:
            return _Dest("ambiguous")
        found = _innermost(bindings, name, current.start_byte)
        if found == "ambiguous" or found is None:
            return _Dest("ambiguous" if found == "ambiguous" else "dynamic")
        if found.kind == "import":
            resolved = _const_string(module, name, modules)
            if resolved is None:
                return _Dest("dynamic")
            path = resolved.split("?", 1)[0].split("#", 1)[0].strip()
            return _Dest("ok", path) if path else _Dest("dynamic")
        if found.kind != "value" or found.value is None:
            return _Dest("dynamic")
        return _static_path(
            module, found.value, modules, bindings, seen | {name}
        )
    if current.type == "object":
        props = _object_props(module.source, current)
        chosen: list[Node] = []
        for key in ("pathname", "path"):
            if key in props:
                chosen.append(props[key])
        if not chosen:
            return _Dest("dynamic")
        resolved = [
            _static_path(module, item, modules, bindings, seen) for item in chosen
        ]
        if any(item.status != "ok" for item in resolved):
            return next(item for item in resolved if item.status != "ok")
        values = {item.value for item in resolved}
        if len(values) != 1:
            return _Dest("ambiguous")
        return resolved[0]
    return _Dest("dynamic")


def _file_uses_router_navigation(bindings: list[_Binding]) -> bool:
    return any(
        item.kind == "import"
        and item.symbol
        in _NAV_COMPONENTS
        | {"useNavigate", "redirect", "useHistory", "history"}
        | _HISTORY_FACTORIES
        for item in bindings
    )


def _navigation_site(
    module: TsModule, node: Node, bindings: list[_Binding]
) -> tuple[str, Node | None] | None:
    """Return ('nav', dest) or ('shadow', None) for a navigation site."""
    if node.type == "call_expression":
        callee = _unwrap_expr(child_named(node, "function"))
        if callee is None:
            return None
        if callee.type == "identifier":
            name = text_of(module.source, callee)
            found = _innermost(bindings, name, callee.start_byte)
            if found == "ambiguous":
                return ("shadow", None)
            if _is_use_navigate_value(module, found):
                return ("nav", _call_arg(node))
            if _imported_symbol(found, "redirect"):
                return ("nav", _call_arg(node))
            if (
                name in {"navigate", "redirect"}
                and isinstance(found, _Binding)
                and found.kind in {"function", "value"}
                and _file_uses_router_navigation(bindings)
            ):
                return ("shadow", None)
            return None
        if callee.type == "member_expression":
            prop = identifier_name(
                module.source, child_named(callee, "property")
            ) or next(
                (
                    text_of(module.source, child)
                    for child in named_children(callee)
                    if child.type == "property_identifier"
                ),
                None,
            )
            if prop not in {"push", "replace"}:
                return None
            obj = next(
                (
                    child
                    for child in named_children(callee)
                    if child.type == "identifier"
                ),
                None,
            )
            if obj is None:
                return None
            obj_name = text_of(module.source, obj)
            found = _innermost(bindings, obj_name, obj.start_byte)
            if _is_history_value(module, found, bindings):
                return ("nav", _call_arg(node))
            if (
                obj_name == "history"
                and isinstance(found, _Binding)
                and _file_uses_router_navigation(bindings)
            ):
                return ("shadow", None)
            return None
        return None
    if node.type not in {"jsx_self_closing_element", "jsx_opening_element"}:
        return None
    name = _jsx_name(module.source, node)
    if name is None:
        return None
    found = _innermost(bindings, name, node.start_byte)
    symbol = found.symbol if isinstance(found, _Binding) else None
    if symbol not in _NAV_COMPONENTS and name not in _NAV_COMPONENTS:
        return None
    if found == "ambiguous":
        return ("shadow", None)
    if (
        isinstance(found, _Binding)
        and found.kind == "import"
        and symbol in _NAV_COMPONENTS
    ):
        return ("nav", _jsx_to_expr(module.source, node))
    if isinstance(found, _Binding) and found.kind in {"function", "value"}:
        return ("shadow", None)
    if name in _NAV_COMPONENTS and any(
        item.symbol in _NAV_COMPONENTS for item in bindings if item.kind == "import"
    ):
        return ("shadow", None)
    return None


def _owner_callable(
    entities: dict[str, Entity], path: str, line: int
) -> Entity | None:
    owners = [
        item
        for item in entities.values()
        if item.type == EntityType.CALLABLE
        and item.file_path
        and item.file_path.replace("\\", "/") == path
        and item.start_line
        and item.end_line
        and item.start_line <= line <= item.end_line
    ]
    if not owners:
        return None
    owners.sort(
        key=lambda item: (
            (item.end_line or 0) - (item.start_line or 0),
            item.qualified_name,
        )
    )
    if len(owners) > 1:
        span0 = (owners[0].end_line or 0) - (owners[0].start_line or 0)
        span1 = (owners[1].end_line or 0) - (owners[1].start_line or 0)
        if span0 == span1:
            return None
    return owners[0]


def _caller_routes(
    entities: dict[str, Entity], edges: dict[str, Edge], caller_id: str
) -> list[str]:
    found: list[str] = []
    for edge in edges.values():
        if edge.type != EdgeType.HANDLED_BY or edge.target_id != caller_id:
            continue
        endpoint = entities.get(edge.source_id)
        if endpoint is None or endpoint.framework_kind != "react-router":
            continue
        attrs = dict(endpoint.attributes)
        if attrs.get("kind") != "navigation":
            continue
        path = attrs.get("route_path") or attrs.get("path")
        if isinstance(path, str) and path not in found:
            found.append(path)
    return found


def _join_relative(base: str, relative: str) -> str | None:
    if relative.startswith("/") or relative == "*":
        return relative
    if base == "*" or any(char in relative for char in "?#"):
        return None
    parts = [part for part in base.split("/") if part]
    for segment in relative.split("/"):
        if segment in {"", "."}:
            continue
        if segment == "..":
            if not parts:
                return None
            parts.pop()
            continue
        parts.append(segment)
    return "/" + "/".join(parts) if parts else "/"


def _handlers_for_path(
    entities: dict[str, Entity], edges: dict[str, Edge], path: str
) -> tuple[str, list[Entity]]:
    endpoints = []
    for item in entities.values():
        attrs = dict(item.attributes)
        route = attrs.get("route_path") or attrs.get("path")
        if (
            item.type == EntityType.ENDPOINT
            and item.framework_kind == "react-router"
            and attrs.get("kind") == "navigation"
            and route == path
        ):
            endpoints.append(item)
    if len(endpoints) != 1:
        return ("ambiguous" if len(endpoints) > 1 else "unresolved"), []
    handlers: list[Entity] = []
    seen: set[str] = set()
    for edge in edges.values():
        if edge.type != EdgeType.HANDLED_BY or edge.source_id != endpoints[0].id:
            continue
        target = entities.get(edge.target_id)
        if target is None or target.type != EntityType.CALLABLE or target.id in seen:
            continue
        seen.add(target.id)
        handlers.append(target)
    if len(handlers) != 1:
        return ("ambiguous" if len(handlers) > 1 else "unresolved"), []
    return "ok", handlers


def _index_navigation_calls(
    modules: dict[str, TsModule],
    entities: dict[str, Entity],
    edges: dict[str, Edge],
    issues: list[AdapterDiagnostic],
    emit_edge,
) -> None:
    for module in modules.values():
        bindings = _collect_bindings(module)
        for node in walk_named(module.tree.root_node):
            site = _navigation_site(module, node, bindings)
            if site is None:
                continue
            status, dest_node = site
            line = node.start_point[0] + 1
            if status == "shadow":
                issues.append(
                    AdapterDiagnostic(
                        "react_router_navigate_shadowed", module.path, line
                    )
                )
                continue
            dest = _static_path(module, dest_node, modules, bindings, set())
            if dest.status != "ok" or not dest.value:
                issues.append(
                    AdapterDiagnostic(
                        "react_router_navigate_ambiguous"
                        if dest.status == "ambiguous"
                        else "react_router_navigate_dynamic",
                        module.path,
                        line,
                    )
                )
                continue
            owner = _owner_callable(entities, module.path, line)
            if owner is None:
                issues.append(
                    AdapterDiagnostic(
                        "react_router_navigate_unresolved", module.path, line
                    )
                )
                continue
            target_path = dest.value
            if not target_path.startswith("/") and target_path != "*":
                bases = _caller_routes(entities, edges, owner.id)
                if len(bases) != 1:
                    issues.append(
                        AdapterDiagnostic(
                            "react_router_navigate_unresolved", module.path, line
                        )
                    )
                    continue
                joined = _join_relative(bases[0], target_path)
                if joined is None:
                    issues.append(
                        AdapterDiagnostic(
                            "react_router_navigate_unresolved", module.path, line
                        )
                    )
                    continue
                target_path = joined
            match, handlers = _handlers_for_path(entities, edges, target_path)
            if match != "ok":
                issues.append(
                    AdapterDiagnostic(
                        f"react_router_navigate_{match}", module.path, line
                    )
                )
                continue
            emit_edge(
                EdgeType.CALLS,
                owner.id,
                handlers[0].id,
                _Location(module.path, line),
                NAVIGATE_RULE,
            )


class ReactRouterFrameworkAdapter:
    """Extract static React Router navigation paths from TypeScript base facts."""

    entrypoint_required = False
    allow_unverified_versions = True
    reviewed_deep_support = False

    descriptor = AdapterDescriptor(
        adapter_id="rkg.react-router",
        adapter_version="0.1.0",
        contract_version=CONTRACT_VERSION,
        kind=AdapterKind.FRAMEWORK,
        language="typescript",
        framework="react-router-dom",
        grammar_or_target="tree-sitter TypeScript/TSX + React Router static routes",
        file_patterns=("*.ts", "*.tsx", "**/*.ts", "**/*.tsx"),
        ignore_patterns=("**/node_modules/**", "**/*.d.ts"),
        capabilities=("app", "routes"),
        technology_constraints=(
            TechnologyConstraint("react-router-dom", ">=6.0,<8.0"),
        ),
    )

    def technology_detectors(self) -> tuple[object, ...]:
        from rkg.detection.react_router import ReactRouterDetector

        return (ReactRouterDetector(),)
    def detect(self, manifest: SourceManifest, parsed: ParseResult) -> DetectionReport:
        evidence: list[DetectionEvidence] = []
        for unit in parsed.units:
            if unit.language != "typescript" or not isinstance(
                unit.representation, TsModule
            ):
                continue
            module: TsModule = unit.representation
            for node in walk_named(module.tree.root_node):
                if node.type != "call_expression":
                    continue
                name = identifier_name(module.source, child_named(node, "function"))
                if name in {
                    "createBrowserRouter",
                    "createHashRouter",
                    "createMemoryRouter",
                }:
                    evidence.append(DetectionEvidence(module.path, DETECT_RULE))
                    break
            text = module.source
            if b"react-router-dom" in text and not evidence:
                # import evidence without call still detects technology
                if any(
                    node.type == "import_statement"
                    and b"react-router-dom"
                    in module.source[node.start_byte : node.end_byte]
                    for node in named_children(module.tree.root_node)
                ):
                    evidence.append(DetectionEvidence(module.path, DETECT_RULE))
        for item in manifest.files:
            if (
                item.relative_path.endswith("package.json")
                and b"react-router-dom" in item.content
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
        return DetectionReport((TechnologyDetection("react-router-dom", None, unique),))

    def extract(
        self, context: AdapterContext, parsed: ParseResult, base: FactBatch
    ) -> AdapterResult:
        modules = {
            unit.relative_path: unit.representation
            for unit in parsed.units
            if unit.language == "typescript"
            and isinstance(unit.representation, TsModule)
        }
        entities = {item.id: item for item in base.entities}
        edges = {item.id: item for item in base.edges}
        evidence = {item.id: item for item in base.evidence}
        diagnostics = list(base.diagnostics)
        issues: list[AdapterDiagnostic] = []

        def emit_edge(
            kind: EdgeType,
            source: str,
            target: str,
            location: _Location,
            rule: str,
        ) -> None:
            ref = evidence_id(
                context.snapshot_id,
                location.path,
                location.line,
                location.line,
                rule,
            )
            evidence[ref] = Evidence(
                ref,
                context.snapshot_id,
                location.path,
                location.line,
                location.line,
                rule,
            )
            key = edge_id(context.snapshot_id, kind, source, target)
            current = edges.get(key)
            references = set(current.evidence_ids) if current else set()
            references.add(ref)
            edges[key] = Edge(
                key,
                context.snapshot_id,
                kind,
                source,
                target,
                rule,
                tuple(sorted(references)),
            )

        for module in modules.values():
            _diagnose_dynamic_route_objects(module, modules, issues)
            for array, location in _find_route_arrays(module, modules):
                del location
                routes = _collect_routes(module, array, None, modules, issues)
                for path, route_location, element_name in routes:
                    chain = (
                        f"route:{route_location.path}:{route_location.line}:{path}",
                    )
                    identifier = endpoint_id(
                        context.repository_id,
                        route_location.path,
                        "navigation",
                        "",
                        path,
                        chain,
                    )
                    base_attrs: list[tuple[str, object]] = [
                        ("kind", "navigation"),
                        ("path", path),
                        ("route_path", path),
                        ("registration_chain", chain),
                    ]
                    entities[identifier] = Entity(
                        identifier,
                        context.repository_id,
                        context.snapshot_id,
                        EntityType.ENDPOINT,
                        path,
                        f"navigation:{path}",
                        route_location.path,
                        route_location.line,
                        route_location.line,
                        framework_kind="react-router",
                        attributes=tuple(base_attrs),
                    )
                    ref = evidence_id(
                        context.snapshot_id,
                        route_location.path,
                        route_location.line,
                        route_location.line,
                        ROUTE_RULE,
                    )
                    evidence[ref] = Evidence(
                        ref,
                        context.snapshot_id,
                        route_location.path,
                        route_location.line,
                        route_location.line,
                        ROUTE_RULE,
                    )
                    # Do not emit repository EXPOSES for UI navigation (not HTTP API).
                    if element_name is None:
                        continue
                    binding = _resolve_component_binding(
                        module, element_name, modules
                    )
                    handler = (
                        _lookup_callable(entities, binding) if binding else None
                    )
                    if handler is None:
                        issues.append(
                            AdapterDiagnostic(
                                "react_router_unresolved",
                                route_location.path,
                                route_location.line,
                            )
                        )
                        continue
                    entities[identifier] = Entity(
                        identifier,
                        context.repository_id,
                        context.snapshot_id,
                        EntityType.ENDPOINT,
                        path,
                        f"navigation:{path}",
                        route_location.path,
                        route_location.line,
                        route_location.line,
                        framework_kind="react-router",
                        attributes=tuple(
                            base_attrs
                            + list(route_flow_attrs(handler, entities, edges))
                        ),
                    )
                    emit_edge(
                        EdgeType.HANDLED_BY,
                        identifier,
                        handler.id,
                        route_location,
                        HANDLER_RULE,
                    )

        _index_navigation_calls(modules, entities, edges, issues, emit_edge)

        for ordinal, item in enumerate(
            sorted(
                {(i.code, i.relative_path, i.line): i for i in issues}.values(),
                key=lambda item: (item.relative_path or "", item.line or 0, item.code),
            )
        ):
            diagnostics.append(
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

        facts = FactBatch(
            context.repository_id,
            context.snapshot_id,
            tuple(entities[key] for key in sorted(entities)),
            tuple(edges[key] for key in sorted(edges)),
            tuple(evidence[key] for key in sorted(evidence)),
            tuple(diagnostics),
        )
        adapter_issues = tuple(
            sorted(
                {(i.code, i.relative_path, i.line): i for i in issues}.values(),
                key=lambda item: (item.relative_path or "", item.line or 0, item.code),
            )
        )
        return AdapterResult(
            facts,
            tuple(
                Capability(name, SupportState.SUPPORTED)
                for name in self.descriptor.capabilities
            ),
            adapter_issues,
        )

    def resolve(
        self, context: AdapterContext, parsed: ParseResult, candidate: FactBatch
    ) -> AdapterResult:
        if (
            candidate.repository_id != context.repository_id
            or candidate.snapshot_id != context.snapshot_id
        ):
            raise ValueError("candidate ownership does not match adapter context")
        return AdapterResult(
            candidate,
            tuple(
                Capability(name, SupportState.SUPPORTED)
                for name in self.descriptor.capabilities
            ),
            (),
        )
