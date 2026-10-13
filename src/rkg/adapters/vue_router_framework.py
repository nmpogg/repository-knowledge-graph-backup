"""Static Vue Router navigation-route extraction over Vue and TypeScript units.

UI routes reuse Endpoint with framework_kind=vue-router and kind=navigation
(no HTTP method, no repository EXPOSES). A route component is linked with
handled_by only when a lazy import() or import binding points at exactly one
.vue file whose setup Callable already exists. Navigation is Callable calls
Callable: router.push / router.replace to the handler of exactly one route.
Analyzed modules are never imported or executed.
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
from rkg.adapters.vue_parse import VueSfc, module_name, resolve_vue_specifier
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

ROUTE_RULE = "RKG.vue_router.route.v1"
HANDLER_RULE = "RKG.vue_router.handler.v1"
NAVIGATE_RULE = "RKG.vue_router.navigate.v1"
DETECT_RULE = "RKG.vue_router.detect.v1"
_MESSAGES = {
    "vue_router_route_dynamic": "Route path is not a unique static literal.",
    "vue_router_unresolved": "Vue Router registration could not be resolved.",
    "vue_router_navigate_dynamic": "Navigation target is not a unique static literal.",
    "vue_router_navigate_ambiguous": "Navigation target matches more than one route.",
    "vue_router_navigate_shadowed": "Navigation API is shadowed and was not resolved.",
    "vue_router_navigate_unresolved": (
        "Navigation target does not match exactly one route."
    ),
}
_FUNCTION_TYPES = frozenset(
    {
        "function_declaration",
        "generator_function_declaration",
        "function_expression",
        "arrow_function",
        "generator_function",
        "method_definition",
    }
)
_UNWRAP = frozenset(
    {
        "parenthesized_expression",
        "as_expression",
        "satisfies_expression",
        "non_null_expression",
    }
)
_NAV_METHODS = frozenset({"push", "replace"})


@dataclass(frozen=True, slots=True)
class _Location:
    path: str
    line: int


@dataclass(frozen=True, slots=True)
class _Mod:
    path: str
    source: bytes
    root: Node
    aliases: dict[str, str]


@dataclass(frozen=True, slots=True)
class _Route:
    path: str
    name: str | None
    location: _Location
    handler_id: str | None
    endpoint_id: str


def _unwrap(node: Node | None) -> Node | None:
    seen = 0
    while node is not None and node.type in _UNWRAP and seen < 6:
        kids = named_children(node)
        if not kids:
            break
        node = kids[0]
        seen += 1
    return node


def _line(node: Node) -> int:
    return node.start_point[0] + 1


def _props(source: bytes, node: Node | None) -> dict[str, Node]:
    props: dict[str, Node] = {}
    node = _unwrap(node)
    if node is None or node.type != "object":
        return props
    for child in named_children(node):
        if child.type == "shorthand_property_identifier":
            props[text_of(source, child)] = child
            continue
        if child.type != "pair":
            continue
        key_node = child_named(child, "key")
        value = child_named(child, "value")
        key = identifier_name(source, key_node) or string_literal(source, key_node)
        if key and value is not None:
            props[key] = _unwrap(value) or value
    return props


def _arguments(node: Node) -> Node | None:
    args = child_named(node, "arguments")
    if args is not None:
        return args
    for child in named_children(node):
        if child.type == "arguments":
            return child
    return None


def _imports(mod: _Mod) -> dict[str, tuple[str, str]]:
    """Local name → (module specifier, imported symbol or default/*)."""
    found: dict[str, tuple[str, str]] = {}
    for node in named_children(mod.root):
        if node.type != "import_statement":
            continue
        if text_of(mod.source, node).startswith("import type"):
            continue
        source_node = next(
            (child for child in named_children(node) if child.type == "string"),
            None,
        )
        specifier = string_literal(mod.source, source_node)
        if specifier is None:
            continue
        clause = next(
            (child for child in named_children(node) if child.type == "import_clause"),
            None,
        )
        if clause is None:
            continue
        for child in named_children(clause):
            if child.type == "identifier":
                found[text_of(mod.source, child)] = (specifier, "default")
            elif child.type == "namespace_import":
                names = [
                    text_of(mod.source, part)
                    for part in named_children(child)
                    if part.type == "identifier"
                ]
                if names:
                    found[names[-1]] = (specifier, "*")
            elif child.type == "named_imports":
                for spec in named_children(child):
                    if spec.type != "import_specifier":
                        continue
                    names = [
                        text_of(mod.source, part)
                        for part in named_children(spec)
                        if part.type == "identifier"
                    ]
                    if names:
                        found[names[-1]] = (specifier, names[0])
    return found


def _module_declarators(mod: _Mod) -> list[tuple[str, Node]]:
    found: list[tuple[str, Node]] = []
    for node in named_children(mod.root):
        stmt = node
        if node.type == "export_statement":
            decl = child_named(node, "declaration")
            if decl is None:
                continue
            stmt = decl
        if stmt.type in {"function_declaration", "generator_function_declaration"}:
            name = identifier_name(mod.source, child_named(stmt, "name"))
            if name:
                found.append((name, stmt))
            continue
        if stmt.type in {"class_declaration", "abstract_class_declaration"}:
            name = identifier_name(mod.source, child_named(stmt, "name"))
            if name:
                found.append((name, stmt))
            continue
        if stmt.type not in {"lexical_declaration", "variable_declaration"}:
            continue
        for declarator in named_children(stmt):
            if declarator.type != "variable_declarator":
                continue
            name = identifier_name(mod.source, child_named(declarator, "name"))
            value = child_named(declarator, "value")
            if name and value is not None:
                found.append((name, value))
    return found


def _module_value_names(mod: _Mod) -> set[str]:
    return {name for name, _ in _module_declarators(mod)}


def _vue_router_binding(mod: _Mod, local: str) -> str | None:
    """Imported symbol from vue-router, or None when missing or shadowed."""
    if local in _module_value_names(mod):
        return None
    imported = _imports(mod).get(local)
    if imported is None:
        return None
    specifier, symbol = imported
    if specifier != "vue-router" and not specifier.startswith("vue-router/"):
        return None
    return symbol


def _classify_create(mod: _Mod, callee: Node | None) -> str | None:
    if callee is None:
        return None
    callee = _unwrap(callee)
    if callee is None:
        return None
    if callee.type == "identifier":
        name = text_of(mod.source, callee)
        imported = _imports(mod).get(name)
        from_router = imported is not None and (
            imported[0] == "vue-router" or imported[0].startswith("vue-router/")
        )
        if name in _module_value_names(mod):
            return "shadow" if from_router and imported and imported[1] == "createRouter" else None
        if from_router and imported and imported[1] == "createRouter":
            return "create"
        return None
    if callee.type == "member_expression":
        kids = named_children(callee)
        if len(kids) < 2:
            return None
        obj, prop = kids[0], kids[1]
        if text_of(mod.source, prop) != "createRouter" or obj.type != "identifier":
            return None
        name = text_of(mod.source, obj)
        symbol = _vue_router_binding(mod, name)
        if symbol == "*":
            return "create"
        imported = _imports(mod).get(name)
        if (
            imported
            and imported[0] in {"vue-router"}
            or (imported and imported[0].startswith("vue-router/"))
        ) and name in _module_value_names(mod):
            return "shadow"
        return None
    return None


def _classify_new(mod: _Mod, expr: Node) -> str | None:
    kids = named_children(expr)
    if not kids:
        return None
    ctor = _unwrap(kids[0])
    if ctor is None or ctor.type != "identifier":
        return None
    name = text_of(mod.source, ctor)
    imported = _imports(mod).get(name)
    from_router = imported is not None and (
        imported[0] == "vue-router" or imported[0].startswith("vue-router/")
    )
    if not from_router or imported is None:
        return None
    if imported[1] not in {"default", "Router", "VueRouter"}:
        return None
    if name in _module_value_names(mod):
        return "shadow"
    return "new"


def _classify_factory(mod: _Mod, expr: Node | None) -> str | None:
    expr = _unwrap(expr)
    if expr is None:
        return None
    if expr.type == "call_expression":
        return _classify_create(mod, child_named(expr, "function"))
    if expr.type == "new_expression":
        return _classify_new(mod, expr)
    return None


def _resolve_module(mod: _Mod, specifier: str, mods: dict[str, _Mod]) -> _Mod | None:
    files = set(mods)
    if specifier.startswith("."):
        target = resolve_vue_specifier(mod.path, specifier, files)
    else:
        target = resolve_specifier(mod.path, specifier, files, mod.aliases)
    if target is None or target not in mods:
        return None
    return mods[target]


def _const_string(
    mod: _Mod, name: str, mods: dict[str, _Mod], seen: set[tuple[str, str]]
) -> str | None:
    key = (mod.path, name)
    if key in seen:
        return None
    seen.add(key)
    values = [value for bound, value in _module_declarators(mod) if bound == name]
    if len(values) > 1:
        return None
    if len(values) == 1:
        return _eval_string(mod, values[0], mods, seen)
    imported = _imports(mod).get(name)
    if imported is None:
        return None
    specifier, symbol = imported
    if symbol in {"default", "*"}:
        return None
    target = _resolve_module(mod, specifier, mods)
    if target is None:
        return None
    return _const_string(target, symbol, mods, seen)


def _eval_string(
    mod: _Mod, node: Node | None, mods: dict[str, _Mod], seen: set[tuple[str, str]]
) -> str | None:
    node = _unwrap(node)
    if node is None:
        return None
    literal = string_literal(mod.source, node)
    if literal is not None:
        return literal
    if node.type == "identifier":
        return _const_string(mod, text_of(mod.source, node), mods, seen)
    return None


def _string_at(
    mod: _Mod,
    node: Node | None,
    mods: dict[str, _Mod],
    call: Node | None,
) -> str | None:
    node = _unwrap(node)
    if node is None:
        return None
    literal = string_literal(mod.source, node)
    if literal is not None:
        return literal
    if node.type != "identifier" or call is None:
        return _eval_string(mod, node, mods, set()) if node.type == "identifier" else None
    name = text_of(mod.source, node)
    if _param_names_covering(mod, call, name):
        return None
    local = _closest_declarator(mod, call, name)
    if local is not None:
        scope = _declarator_scope(local)
        if scope is not None and scope.type != "program":
            return _eval_string(mod, child_named(local, "value"), mods, set())
    return _const_string(mod, name, mods, set())


def _bound_array(
    mod: _Mod, name: str, mods: dict[str, _Mod], seen: set[tuple[str, str]]
) -> Node | None:
    key = (mod.path, name)
    if key in seen:
        return None
    seen.add(key)
    values = [value for bound, value in _module_declarators(mod) if bound == name]
    arrays = [_unwrap(value) for value in values]
    arrays = [item for item in arrays if item is not None and item.type == "array"]
    if len(values) > 1:
        return None
    if len(arrays) == 1:
        return arrays[0]
    if values:
        return None
    imported = _imports(mod).get(name)
    if imported is None:
        return None
    specifier, symbol = imported
    if symbol in {"default", "*"}:
        return None
    target = _resolve_module(mod, specifier, mods)
    if target is None:
        return None
    return _bound_array(target, symbol, mods, seen)


def _routes_array(mod: _Mod, expr: Node, mods: dict[str, _Mod]) -> Node | None:
    args = _arguments(expr)
    if args is None:
        return None
    positional = named_children(args)
    if not positional:
        return None
    obj = _unwrap(positional[0])
    if obj is None or obj.type != "object":
        return None
    routes = _props(mod.source, obj).get("routes")
    routes = _unwrap(routes)
    if routes is None:
        return None
    if routes.type == "array":
        return routes
    if routes.type in {"identifier", "shorthand_property_identifier"}:
        return _bound_array(mod, text_of(mod.source, routes), mods, set())
    return None


def _join(parent: str | None, child: str) -> str:
    if child.startswith("/"):
        return child
    if child == "":
        return parent if parent not in (None, "") else "/"
    if parent in (None, "", "/"):
        return f"/{child}"
    return f"{parent.rstrip('/')}/{child}"


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


def _loader_specs(source: bytes, node: Node) -> list[str | None]:
    specs: list[str | None] = []
    for item in walk_named(node):
        if item.type != "call_expression":
            continue
        callee = child_named(item, "function")
        if callee is None or callee.type != "import":
            continue
        args = _arguments(item)
        arg_nodes = named_children(args) if args is not None else ()
        if len(arg_nodes) != 1:
            specs.append(None)
            continue
        specs.append(string_literal(source, _unwrap(arg_nodes[0])))
    return specs


def _one_vue_file(mod: _Mod, specifier: str, files: set[str]) -> str | None:
    if specifier.startswith("."):
        hit = resolve_vue_specifier(mod.path, specifier, files)
    else:
        hit = resolve_specifier(mod.path, specifier, files, mod.aliases)
    if hit is None or not hit.endswith(".vue") or hit not in files:
        return None
    return hit


def _resolve_component(
    mod: _Mod,
    node: Node | None,
    mods: dict[str, _Mod],
    files: set[str],
    seen: set[tuple[str, str]],
) -> tuple[str | None, bool]:
    """Return (vue path, failed). failed means a component was present but not unique."""
    node = _unwrap(node)
    if node is None:
        return None, False
    specs = _loader_specs(mod.source, node)
    if specs:
        if len(specs) == 1 and isinstance(specs[0], str):
            vue = _one_vue_file(mod, specs[0], files)
            if vue is not None:
                return vue, False
        return None, True
    if node.type != "identifier":
        return None, True
    name = text_of(mod.source, node)
    key = (mod.path, name)
    if key in seen:
        return None, True
    values = [value for bound, value in _module_declarators(mod) if bound == name]
    if len(values) > 1:
        return None, True
    if len(values) == 1:
        return _resolve_component(mod, values[0], mods, files, seen | {key})
    imported = _imports(mod).get(name)
    if imported is None:
        return None, True
    specifier, _symbol = imported
    vue = _one_vue_file(mod, specifier, files)
    if vue is not None:
        return vue, False
    return None, True


def _setup_handler(entities: dict[str, Entity], vue_path: str) -> Entity | None:
    qualified = f"{module_name(vue_path)}.setup"
    matches = [
        item
        for item in entities.values()
        if item.type == EntityType.CALLABLE
        and item.qualified_name == qualified
        and (item.file_path or "").replace("\\", "/") == vue_path
    ]
    return matches[0] if len(matches) == 1 else None


def _collect_routes(
    mod: _Mod,
    array: Node,
    parent: str | None,
    mods: dict[str, _Mod],
    files: set[str],
    entities: dict[str, Entity],
    issues: list[AdapterDiagnostic],
) -> list[tuple[str, str | None, _Location, Entity | None]]:
    routes: list[tuple[str, str | None, _Location, Entity | None]] = []
    for element in named_children(array):
        line = _line(element)
        if element.type != "object":
            issues.append(AdapterDiagnostic("vue_router_route_dynamic", mod.path, line))
            continue
        props = _props(mod.source, element)
        if "path" not in props:
            child_array = props.get("children")
            if child_array is not None and child_array.type == "array":
                routes.extend(
                    _collect_routes(
                        mod, child_array, parent, mods, files, entities, issues
                    )
                )
            continue
        path_value = _eval_string(mod, props["path"], mods, set())
        if path_value is None:
            issues.append(AdapterDiagnostic("vue_router_route_dynamic", mod.path, line))
            child_array = props.get("children")
            if child_array is not None and child_array.type == "array":
                routes.extend(
                    _collect_routes(
                        mod, child_array, parent, mods, files, entities, issues
                    )
                )
            continue
        joined = _join(parent, path_value)
        route_name: str | None = None
        if "name" in props:
            route_name = _eval_string(mod, props["name"], mods, set())
            if route_name is None:
                issues.append(
                    AdapterDiagnostic("vue_router_route_dynamic", mod.path, line)
                )
        handler: Entity | None = None
        if "component" in props:
            vue_path, failed = _resolve_component(
                mod, props["component"], mods, files, set()
            )
            if failed or vue_path is None:
                issues.append(
                    AdapterDiagnostic("vue_router_unresolved", mod.path, line)
                )
            else:
                handler = _setup_handler(entities, vue_path)
                if handler is None:
                    issues.append(
                        AdapterDiagnostic("vue_router_unresolved", mod.path, line)
                    )
        routes.append((joined, route_name, _Location(mod.path, line), handler))
        children = props.get("children")
        if children is not None and children.type == "array":
            routes.extend(
                _collect_routes(
                    mod, children, joined, mods, files, entities, issues
                )
            )
    return routes


def _file_uses_vue_router(mod: _Mod) -> bool:
    for specifier, _symbol in _imports(mod).values():
        if specifier == "vue-router" or specifier.startswith("vue-router/"):
            return True
    return False


def _module_instances(mod: _Mod) -> set[str]:
    names: set[str] = set()
    poisoned: set[str] = set()
    for name, value in _module_declarators(mod):
        if _classify_factory(mod, value) not in {"create", "new"}:
            continue
        if name in names:
            poisoned.add(name)
        names.add(name)
    return names - poisoned


def _is_imported_instance(
    mod: _Mod, local: str, mods: dict[str, _Mod], seen: set[tuple[str, str]]
) -> bool:
    key = (mod.path, local)
    if key in seen:
        return False
    seen.add(key)
    if local in _module_instances(mod):
        return True
    imported = _imports(mod).get(local)
    if imported is None or local in _module_value_names(mod):
        return False
    specifier, symbol = imported
    if specifier == "vue-router" or specifier.startswith("vue-router/"):
        return False
    if symbol in {"default", "*"}:
        return False
    target = _resolve_module(mod, specifier, mods)
    if target is None:
        return False
    return symbol in _module_instances(target)


def _is_use_router_call(mod: _Mod, node: Node | None) -> bool:
    node = _unwrap(node)
    if node is None or node.type != "call_expression":
        return False
    callee = _unwrap(child_named(node, "function"))
    if callee is None or callee.type != "identifier":
        return False
    return _vue_router_binding(mod, text_of(mod.source, callee)) == "useRouter"


def _declarator_scope(node: Node) -> Node | None:
    scope = node.parent
    while scope is not None and scope.type not in _FUNCTION_TYPES and scope.type != "program":
        scope = scope.parent
    return scope


def _closest_declarator(mod: _Mod, call: Node, name: str) -> Node | None:
    candidates: list[Node] = []
    for node in walk_named(mod.root):
        if node.type != "variable_declarator" or node.start_byte >= call.start_byte:
            continue
        if identifier_name(mod.source, child_named(node, "name")) != name:
            continue
        scope = _declarator_scope(node)
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


def _smallest_function(mod: _Mod, call: Node) -> Node | None:
    matches = [
        node
        for node in walk_named(mod.root)
        if node.type in _FUNCTION_TYPES
        and node.start_byte <= call.start_byte
        and call.end_byte <= node.end_byte
    ]
    if not matches:
        return None
    return min(matches, key=lambda item: item.end_byte - item.start_byte)


def _parameter_names(source: bytes, fn: Node) -> set[str]:
    params = child_named(fn, "parameters")
    if params is None:
        return set()
    names: set[str] = set()
    for child in named_children(params):
        node = child
        if node.type in {"required_parameter", "optional_parameter"}:
            pattern = child_named(node, "pattern")
            node = pattern or node
        if node.type == "rest_pattern":
            inner = child_named(node, "name") or next(
                (part for part in named_children(node) if part.type == "identifier"),
                None,
            )
            node = inner or node
        if node.type == "identifier":
            names.add(text_of(source, node))
    return names


def _param_names_covering(mod: _Mod, call: Node, name: str) -> bool:
    fn = _smallest_function(mod, call)
    if fn is None:
        return False
    return name in _parameter_names(mod.source, fn)


def _receiver_status(mod: _Mod, call: Node, mods: dict[str, _Mod]) -> str:
    """Return ok, shadow, or ignore for router.push / router.replace."""
    callee = _unwrap(child_named(call, "function"))
    if callee is None or callee.type != "member_expression":
        return "ignore"
    kids = named_children(callee)
    if len(kids) < 2 or text_of(mod.source, kids[-1]) not in _NAV_METHODS:
        return "ignore"
    obj = kids[0]
    if obj.type == "call_expression":
        if _is_use_router_call(mod, obj):
            return "ok"
        inner = _unwrap(child_named(obj, "function"))
        if (
            inner is not None
            and inner.type == "identifier"
            and text_of(mod.source, inner) == "useRouter"
            and _file_uses_vue_router(mod)
        ):
            return "shadow"
        return "ignore"
    if obj.type != "identifier":
        return "ignore"
    name = text_of(mod.source, obj)
    if not _file_uses_vue_router(mod) and not _is_imported_instance(mod, name, mods, set()):
        return "ignore"
    if _param_names_covering(mod, call, name):
        local = _closest_declarator(mod, call, name)
        scope = _declarator_scope(local) if local is not None else None
        fn = _smallest_function(mod, call)
        inside = (
            local is not None
            and fn is not None
            and scope is not None
            and scope.type != "program"
            and fn.start_byte <= local.start_byte
        )
        if not inside:
            return "shadow"
    decl = _closest_declarator(mod, call, name)
    if decl is not None:
        value = child_named(decl, "value")
        if _is_use_router_call(mod, value) or _classify_factory(mod, value) in {
            "create",
            "new",
        }:
            return "ok"
        if (
            value is not None
            and value.type == "identifier"
            and _is_imported_instance(mod, text_of(mod.source, value), mods, set())
        ):
            return "ok"
        return "shadow" if _file_uses_vue_router(mod) else "ignore"
    if name in _module_instances(mod) or _is_imported_instance(mod, name, mods, set()):
        return "ok"
    return "ignore"


def _destination(
    mod: _Mod, call: Node, mods: dict[str, _Mod]
) -> tuple[str, str | None, str | None]:
    """Return (status, path, name). status is ok or dynamic."""
    args = _arguments(call)
    positional = named_children(args) if args is not None else ()
    if not positional:
        return "dynamic", None, None
    node = _unwrap(positional[0])
    if node is None:
        return "dynamic", None, None
    if node.type == "object":
        props = _props(mod.source, node)
        path_s = _string_at(mod, props["path"], mods, call) if "path" in props else None
        name_s = _string_at(mod, props["name"], mods, call) if "name" in props else None
        if "path" in props and path_s is None:
            return "dynamic", None, None
        if "name" in props and name_s is None:
            return "dynamic", None, None
        if path_s is None and name_s is None:
            return "dynamic", None, None
        if path_s is not None:
            path_s = path_s.split("?", 1)[0].split("#", 1)[0].strip()
            if not path_s:
                return "dynamic", None, None
        return "ok", path_s, name_s
    path_s = _string_at(mod, node, mods, call)
    if path_s is None:
        return "dynamic", None, None
    path_s = path_s.split("?", 1)[0].split("#", 1)[0].strip()
    if not path_s:
        return "dynamic", None, None
    return "ok", path_s, None


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


def _caller_routes(routes: list[_Route], caller_id: str) -> list[str]:
    found: list[str] = []
    for route in routes:
        if route.handler_id == caller_id and route.path not in found:
            found.append(route.path)
    return found


def _match_route(
    routes: list[_Route],
    path: str | None,
    name: str | None,
    caller_paths: list[str],
) -> tuple[str, str | None]:
    if path is not None and not path.startswith("/"):
        if len(caller_paths) != 1:
            return "unresolved", None
        path = _join_relative(caller_paths[0], path)
        if path is None:
            return "unresolved", None
    by_path = [item for item in routes if path is not None and item.path == path]
    by_name = [item for item in routes if name is not None and item.name == name]
    if path is not None and name is not None:
        if (
            len(by_path) == 1
            and len(by_name) == 1
            and by_path[0].endpoint_id == by_name[0].endpoint_id
            and by_path[0].handler_id
        ):
            return "ok", by_path[0].handler_id
        if len(by_path) > 1 or len(by_name) > 1:
            return "ambiguous", None
        return "unresolved", None
    chosen = by_path if path is not None else by_name
    if len(chosen) > 1:
        return "ambiguous", None
    if len(chosen) != 1 or not chosen[0].handler_id:
        return "unresolved", None
    return "ok", chosen[0].handler_id


def _mods_from_parsed(parsed: ParseResult) -> dict[str, _Mod]:
    mods: dict[str, _Mod] = {}
    for unit in parsed.units:
        if isinstance(unit.representation, TsModule):
            module: TsModule = unit.representation
            mods[module.path] = _Mod(
                module.path,
                module.source,
                module.tree.root_node,
                dict(module.aliases),
            )
        elif isinstance(unit.representation, VueSfc):
            sfc: VueSfc = unit.representation
            if sfc.script_tree is None:
                continue
            mods[sfc.path] = _Mod(
                sfc.path, sfc.script_source, sfc.script_tree.root_node, {}
            )
    return mods


def _package_version(content: bytes) -> str | None:
    import json

    try:
        data = json.loads(content.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    for section in ("dependencies", "devDependencies", "peerDependencies"):
        block = data.get(section) or {}
        if not isinstance(block, dict):
            continue
        version = block.get("vue-router")
        if not isinstance(version, str):
            continue
        raw = version.lstrip("^~>=<")
        parts = raw.split(".")
        if parts and all(part.isdigit() for part in parts[:3]) and parts[0]:
            return ".".join(parts[:3])
    return None


class VueRouterFrameworkAdapter:
    """Extract static Vue Router navigation paths from Vue and TypeScript facts."""

    entrypoint_required = False
    allow_unverified_versions = True
    reviewed_deep_support = False

    descriptor = AdapterDescriptor(
        adapter_id="rkg.vue-router",
        adapter_version="0.1.0",
        contract_version=CONTRACT_VERSION,
        kind=AdapterKind.FRAMEWORK,
        language="vue",
        framework="vue-router",
        grammar_or_target="tree-sitter TypeScript + Vue Router static routes",
        file_patterns=(
            "*.vue",
            "**/*.vue",
            "*.ts",
            "*.tsx",
            "**/*.ts",
            "**/*.tsx",
        ),
        ignore_patterns=(
            "**/node_modules/**",
            "**/.nuxt/**",
            "**/.output/**",
            "**/dist/**",
            "**/coverage/**",
        ),
        capabilities=("app", "routes"),
        technology_constraints=(TechnologyConstraint("vue-router", ">=3.0,<5.0"),),
    )

    def technology_detectors(self) -> tuple[object, ...]:
        from rkg.detection.vue_router import VueRouterDetector

        return (VueRouterDetector(),)

    def _capabilities(self) -> tuple[Capability, ...]:
        return tuple(
            Capability(name, SupportState.DETECTED_ONLY)
            for name in self.descriptor.capabilities
        )

    def detect(self, manifest: SourceManifest, parsed: ParseResult) -> DetectionReport:
        evidence: list[DetectionEvidence] = []
        version: str | None = None
        for item in manifest.files:
            path = item.relative_path.replace("\\", "/")
            if path.endswith("package.json") and b'"vue-router"' in item.content:
                evidence.append(DetectionEvidence(path, DETECT_RULE))
                version = version or _package_version(item.content)
        for mod in _mods_from_parsed(parsed).values():
            if any(
                specifier == "vue-router" or specifier.startswith("vue-router/")
                for specifier, _symbol in _imports(mod).values()
            ):
                evidence.append(DetectionEvidence(mod.path, DETECT_RULE))
                continue
            for _name, value in _module_declarators(mod):
                if _classify_factory(mod, value) in {"create", "new"}:
                    evidence.append(DetectionEvidence(mod.path, DETECT_RULE))
                    break
        if not evidence:
            return DetectionReport()
        unique = tuple(
            DetectionEvidence(path, rule)
            for path, rule in sorted({(item.relative_path, item.rule_id) for item in evidence})
        )
        return DetectionReport((TechnologyDetection("vue-router", version, unique),))

    def extract(
        self, context: AdapterContext, parsed: ParseResult, base: FactBatch
    ) -> AdapterResult:
        mods = _mods_from_parsed(parsed)
        files = {unit.relative_path.replace("\\", "/") for unit in parsed.units}
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

        collected: list[_Route] = []
        for mod in mods.values():
            for node in walk_named(mod.root):
                kind = None
                if node.type == "call_expression":
                    kind = _classify_create(mod, child_named(node, "function"))
                elif node.type == "new_expression":
                    kind = _classify_new(mod, node)
                if kind is None:
                    continue
                line = _line(node)
                if kind == "shadow":
                    issues.append(
                        AdapterDiagnostic("vue_router_unresolved", mod.path, line)
                    )
                    continue
                array = _routes_array(mod, node, mods)
                if array is None:
                    issues.append(
                        AdapterDiagnostic("vue_router_unresolved", mod.path, line)
                    )
                    continue
                for path, route_name, location, handler in _collect_routes(
                    mod, array, None, mods, files, entities, issues
                ):
                    chain = (f"route:{location.path}:{location.line}:{path}",)
                    identifier = endpoint_id(
                        context.repository_id,
                        location.path,
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
                    if route_name is not None:
                        base_attrs.append(("route_name", route_name))
                    extra: tuple[tuple[str, str], ...] = ()
                    if handler is not None:
                        extra = route_flow_attrs(handler, entities, edges)
                    entities[identifier] = Entity(
                        identifier,
                        context.repository_id,
                        context.snapshot_id,
                        EntityType.ENDPOINT,
                        path,
                        f"navigation:{path}",
                        location.path,
                        location.line,
                        location.line,
                        framework_kind="vue-router",
                        attributes=tuple(base_attrs) + extra,
                    )
                    ref = evidence_id(
                        context.snapshot_id,
                        location.path,
                        location.line,
                        location.line,
                        ROUTE_RULE,
                    )
                    evidence[ref] = Evidence(
                        ref,
                        context.snapshot_id,
                        location.path,
                        location.line,
                        location.line,
                        ROUTE_RULE,
                    )
                    if handler is not None:
                        emit_edge(
                            EdgeType.HANDLED_BY,
                            identifier,
                            handler.id,
                            location,
                            HANDLER_RULE,
                        )
                    collected.append(
                        _Route(
                            path,
                            route_name,
                            location,
                            handler.id if handler is not None else None,
                            identifier,
                        )
                    )

        for mod in mods.values():
            for node in walk_named(mod.root):
                if node.type != "call_expression":
                    continue
                status = _receiver_status(mod, node, mods)
                if status == "ignore":
                    continue
                line = _line(node)
                if status == "shadow":
                    issues.append(
                        AdapterDiagnostic(
                            "vue_router_navigate_shadowed", mod.path, line
                        )
                    )
                    continue
                dest_status, path, route_name = _destination(mod, node, mods)
                if dest_status != "ok":
                    issues.append(
                        AdapterDiagnostic("vue_router_navigate_dynamic", mod.path, line)
                    )
                    continue
                caller = _owner_callable(entities, mod.path, line)
                if caller is None:
                    issues.append(
                        AdapterDiagnostic(
                            "vue_router_navigate_unresolved", mod.path, line
                        )
                    )
                    continue
                match, handler_id = _match_route(
                    collected,
                    path,
                    route_name,
                    _caller_routes(collected, caller.id),
                )
                if match != "ok" or handler_id is None:
                    issues.append(
                        AdapterDiagnostic(
                            f"vue_router_navigate_{match}", mod.path, line
                        )
                    )
                    continue
                emit_edge(
                    EdgeType.CALLS,
                    caller.id,
                    handler_id,
                    _Location(mod.path, line),
                    NAVIGATE_RULE,
                )

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
        return AdapterResult(facts, self._capabilities(), adapter_issues)

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
