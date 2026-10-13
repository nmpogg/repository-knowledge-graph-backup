"""Static Gin, chi, and gorilla/mux route extraction over parsed Go units.

Routes are recorded only when the router, path, and HTTP method are static.
handled_by is emitted only when the handler resolves to exactly one Callable
already present in the base facts. Dynamic paths, shadowed names, and
ambiguous targets become diagnostics. Analyzed source is never executed.
"""

from __future__ import annotations

from dataclasses import dataclass, field

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
from rkg.adapters.go_parse import (
    GoModule,
    _parameter_pairs,
    named_children,
    package_qualified,
    string_literal,
    text_of,
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

DETECT_RULE = "RKG.go_http.detect.v1"
ROUTE_RULE = "RKG.go_http.route.v1"
HANDLER_RULE = "RKG.go_http.handler.v1"
_SECRET = "RKG_TEST_SECRET_DO_NOT_PERSIST"
_MESSAGES = {
    "go_http_route_dynamic": "Route path or method is not static.",
    "go_http_handler_unresolved": "Route handler does not resolve to one callable.",
    "go_http_router_unresolved": "HTTP router receiver is ambiguous or shadowed.",
}
_GIN_METHODS = {
    "GET": "GET",
    "POST": "POST",
    "PUT": "PUT",
    "PATCH": "PATCH",
    "DELETE": "DELETE",
    "HEAD": "HEAD",
    "OPTIONS": "OPTIONS",
}
_CHI_METHODS = {
    "Get": "GET",
    "Post": "POST",
    "Put": "PUT",
    "Patch": "PATCH",
    "Delete": "DELETE",
    "Head": "HEAD",
    "Options": "OPTIONS",
    "Connect": "CONNECT",
    "Trace": "TRACE",
}
_HTTP_METHODS = frozenset(
    {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "CONNECT", "TRACE"}
)
_GIN_TYPES = frozenset({"Engine", "RouterGroup", "IRoutes", "IRouter"})
_CHI_TYPES = frozenset({"Router", "Mux"})
_MUX_TYPES = frozenset({"Router"})


def _modules(parsed: ParseResult) -> dict[str, GoModule]:
    return {
        unit.relative_path: unit.representation
        for unit in parsed.units
        if isinstance(unit.representation, GoModule)
    }


def _library(import_path: str) -> str | None:
    path = import_path.strip("/")
    if path == "github.com/gin-gonic/gin" or path.startswith(
        "github.com/gin-gonic/gin/"
    ):
        return "gin"
    if path == "github.com/go-chi/chi" or path.startswith("github.com/go-chi/chi/"):
        return "chi"
    if path == "github.com/gorilla/mux" or path.startswith("github.com/gorilla/mux/"):
        return "mux"
    return None


def _http_aliases(module: GoModule) -> dict[str, str]:
    """Map the local import name to gin, chi, or mux."""
    aliases: dict[str, str] = {}
    for item in module.imports:
        library = _library(item.path)
        if library is None:
            continue
        local = item.alias or library
        if local in {".", "_", ""}:
            continue
        aliases[local] = library
    return aliases


def _contains_secret(value: str | None) -> bool:
    return value is not None and _SECRET in value


@dataclass
class _Scope:
    bindings: dict[str, _Sym]
    assigned: set[str]


@dataclass(frozen=True, slots=True)
class _Sym:
    kind: str
    library: str = ""
    prefix: str | None = None
    value: str | None = None
    handler: str | None = None
    handler_file: str | None = None


@dataclass(frozen=True, slots=True)
class _FuncRef:
    qualified_name: str
    file_path: str


@dataclass
class _Ctx:
    adapter_context: AdapterContext
    module: GoModule
    aliases: dict[str, str]
    functions: dict[tuple[str, str], tuple[_FuncRef, ...]]
    constants: dict[tuple[str, str], str]
    ambiguous_constants: set[tuple[str, str]]
    entities: dict[str, Entity]
    edges: dict[str, Edge]
    evidence: dict[str, Evidence]
    callable_entities: tuple[Entity, ...]
    issues: list[AdapterDiagnostic] = field(default_factory=list)
    consumed_funcs: set[int] = field(default_factory=set)

    @property
    def source(self) -> bytes:
        return self.module.source

    @property
    def libs(self) -> frozenset[str]:
        return frozenset(self.aliases.values())

    def issue(self, code: str, line: int) -> None:
        self.issues.append(AdapterDiagnostic(code, self.module.path, line))


def _functions(
    modules: dict[str, GoModule],
) -> dict[tuple[str, str], tuple[_FuncRef, ...]]:
    found: dict[tuple[str, str], list[_FuncRef]] = {}
    for module in modules.values():
        for item in module.callables:
            if item.kind != "function":
                continue
            found.setdefault((module.package_name, item.name), []).append(
                _FuncRef(item.qualified_name, module.path)
            )
    return {key: tuple(refs) for key, refs in found.items()}


def _lookup_function(ctx: _Ctx, package: str, name: str) -> _Sym | None:
    """One function is unique only when qualified name and file both match once."""
    refs = ctx.functions.get((package, name))
    if not refs:
        return None
    unique = {(ref.qualified_name, ref.file_path) for ref in refs}
    if len(unique) != 1:
        return _Sym("shadow")
    qualified_name, file_path = next(iter(unique))
    if _contains_secret(qualified_name):
        return _Sym("shadow")
    return _Sym("handler", handler=qualified_name, handler_file=file_path)


def _package_constants(
    modules: dict[str, GoModule],
) -> tuple[dict[tuple[str, str], str], set[tuple[str, str]]]:
    grouped: dict[tuple[str, str], set[str]] = {}
    for module in modules.values():
        for name, value in module.constants.items():
            grouped.setdefault((module.package_name, name), set()).add(value)
    resolved: dict[tuple[str, str], str] = {}
    ambiguous: set[tuple[str, str]] = set()
    for key, values in grouped.items():
        if len(values) == 1:
            resolved[key] = next(iter(values))
        else:
            ambiguous.add(key)
    return resolved, ambiguous


def _arg_nodes(source: bytes, call) -> tuple:
    del source
    args = call.child_by_field_name("arguments")
    if args is None:
        args = next(
            (c for c in named_children(call) if c.type == "argument_list"), None
        )
    if args is None:
        return ()
    return named_children(args)


def _selector(source: bytes, call) -> tuple | None:
    func = call.child_by_field_name("function")
    if func is None:
        func = next(iter(named_children(call)), None)
    if func is None or func.type != "selector_expression":
        return None
    operand = func.child_by_field_name("operand")
    field = func.child_by_field_name("field")
    if operand is None or field is None:
        children = named_children(func)
        if len(children) < 2:
            return None
        operand, field = children[0], children[-1]
    return operand, text_of(source, field)


def _import_library(operand, scope: _Scope, ctx: _Ctx) -> str | None:
    if operand is None or operand.type != "identifier":
        return None
    name = text_of(ctx.source, operand)
    if name in scope.bindings:
        return None
    return ctx.aliases.get(name)


def _param_router(type_label: str, ctx: _Ctx) -> _Sym | None:
    if "." not in type_label:
        return None
    left, right = type_label.split(".", 1)
    library = ctx.aliases.get(left)
    # A root engine created in view has an empty prefix. A group or an
    # incoming chi/mux router does not: the mount prefix is unknown.
    if library == "gin" and right == "Engine":
        return _Sym("router", library="gin", prefix="")
    if library == "gin" and right in _GIN_TYPES:
        return _Sym("router", library="gin", prefix=None)
    if library == "chi" and right in _CHI_TYPES:
        return _Sym("router", library="chi", prefix=None)
    if library == "mux" and right in _MUX_TYPES:
        return _Sym("router", library="mux", prefix=None)
    return None


def _bind_params(pairs: tuple[tuple[str, str], ...], scope: _Scope, ctx: _Ctx) -> None:
    for name, type_label in pairs:
        if not name or name == "_":
            continue
        router = _param_router(type_label, ctx)
        scope.bindings[name] = router if router is not None else _Sym("shadow")


def _assign(scope: _Scope, name: str, sym: _Sym | None) -> None:
    if not name or name == "_":
        return
    if name in scope.assigned:
        scope.bindings[name] = _Sym("shadow")
        return
    scope.assigned.add(name)
    scope.bindings[name] = sym if sym is not None else _Sym("shadow")


def _join(prefix: str | None, route: str | None) -> str | None:
    secret = _contains_secret(prefix) or _contains_secret(route)
    if prefix is None or route is None or secret:
        return None
    if not route:
        return None
    if not prefix:
        return route if route.startswith("/") else f"/{route}"
    if route == "/":
        return prefix
    if route.startswith("/"):
        return prefix.rstrip("/") + route
    return prefix.rstrip("/") + "/" + route


def _eval_ident(name: str, scope: _Scope, ctx: _Ctx) -> _Sym | None:
    if name in scope.bindings:
        return scope.bindings[name]
    key = (ctx.module.package_name, name)
    if key in ctx.ambiguous_constants:
        return _Sym("shadow")
    if key in ctx.constants:
        value = ctx.constants[key]
        if _contains_secret(value):
            return _Sym("shadow")
        return _Sym("path", value=value)
    package, _name = key
    return _lookup_function(ctx, package, name)


def _eval(node, scope: _Scope, ctx: _Ctx) -> _Sym | None:
    if node is None:
        return None
    if node.type == "literal_element":
        children = named_children(node)
        return _eval(children[0], scope, ctx) if children else None
    if node.type == "expression_list":
        children = named_children(node)
        if len(children) != 1:
            return _Sym("shadow")
        return _eval(children[0], scope, ctx)
    if node.type == "parenthesized_expression":
        children = named_children(node)
        return _eval(children[0], scope, ctx) if len(children) == 1 else _Sym("shadow")
    literal = string_literal(ctx.source, node)
    if literal is not None:
        if _contains_secret(literal):
            return _Sym("shadow")
        return _Sym("path", value=literal)
    if node.type == "identifier":
        return _eval_ident(text_of(ctx.source, node), scope, ctx)
    if node.type == "binary_expression":
        return _Sym("shadow")
    if node.type == "call_expression":
        return _eval_call(node, scope, ctx)
    if node.type == "selector_expression":
        return _eval_selector(node, scope, ctx)
    return None


def _eval_selector(node, scope: _Scope, ctx: _Ctx) -> _Sym | None:
    children = named_children(node)
    operand = node.child_by_field_name("operand") or (children[0] if children else None)
    field = node.child_by_field_name("field") or (
        named_children(node)[-1] if named_children(node) else None
    )
    if operand is None or field is None or operand.type != "identifier":
        return None
    if text_of(ctx.source, operand) in scope.bindings:
        return _Sym("shadow")
    package = text_of(ctx.source, operand)
    found = _lookup_function(ctx, package, text_of(ctx.source, field))
    return found if found is not None else _Sym("shadow")


def _eval_call(node, scope: _Scope, ctx: _Ctx) -> _Sym | None:
    selected = _selector(ctx.source, node)
    if selected is None:
        return None
    operand, field = selected
    library = _import_library(operand, scope, ctx)
    if library == "gin" and field in {"New", "Default"}:
        return _Sym("router", library="gin", prefix="")
    if library == "chi" and field in {"NewRouter", "NewMux"}:
        return _Sym("router", library="chi", prefix="")
    if library == "mux" and field == "NewRouter":
        return _Sym("router", library="mux", prefix="")
    if field != "Group":
        return None
    router = _as_router(_eval(operand, scope, ctx))
    if router is None or router.library != "gin":
        return None
    args = _arg_nodes(ctx.source, node)
    path = _path_value(_eval(args[0], scope, ctx) if args else None)
    if router.prefix is None or path is None:
        return _Sym("router", library="gin", prefix=None)
    joined = _join(router.prefix, path)
    if joined is None:
        return _Sym("router", library="gin", prefix=None)
    return _Sym("router", library="gin", prefix=joined)


def _as_router(sym: _Sym | None) -> _Sym | None:
    if sym is not None and sym.kind == "router":
        return sym
    return None


def _path_value(sym: _Sym | None) -> str | None:
    if sym is None or sym.kind != "path" or not sym.value:
        return None
    if _contains_secret(sym.value):
        return None
    return sym.value


def _handler_entity(ctx: _Ctx, sym: _Sym | None) -> Entity | None:
    if sym is None or sym.kind != "handler" or not sym.handler or not sym.handler_file:
        return None
    matches = [
        item
        for item in ctx.callable_entities
        if item.type == EntityType.CALLABLE
        and item.qualified_name == sym.handler
        and item.file_path == sym.handler_file
    ]
    if len(matches) != 1:
        return None
    return matches[0]


def _method_token(sym: _Sym | None) -> str | None:
    value = _path_value(sym)
    if value is None:
        return None
    token = value.upper()
    if token in _HTTP_METHODS and value.upper() == token:
        return token if value == token or value.upper() == token else None
    if value in _HTTP_METHODS:
        return value
    return None


def _statements(block) -> tuple:
    for child in named_children(block):
        if child.type == "statement_list":
            return named_children(child)
    return named_children(block)


def _decl_pairs(source: bytes, node) -> list[tuple[str, object]]:
    lists = [c for c in named_children(node) if c.type == "expression_list"]
    if len(lists) != 2:
        return []
    names = named_children(lists[0])
    values = named_children(lists[1])
    if len(names) != len(values):
        return [
            (text_of(source, name) if name.type == "identifier" else "", None)
            for name in names
        ]
    pairs = []
    for name, value in zip(names, values, strict=True):
        if name.type != "identifier":
            pairs.append(("", None))
        else:
            pairs.append((text_of(source, name), value))
    return pairs


def _apply_assign(node, scope: _Scope, ctx: _Ctx) -> None:
    for name, value in _decl_pairs(ctx.source, node):
        _assign(scope, name, _eval(value, scope, ctx) if value is not None else None)


def _apply_const(node, scope: _Scope, ctx: _Ctx) -> None:
    for spec in named_children(node):
        if spec.type != "const_spec":
            continue
        name_node = next(
            (c for c in named_children(spec) if c.type == "identifier"), None
        )
        if name_node is None:
            continue
        value_node = next(
            (
                c
                for c in named_children(spec)
                if c.type not in {"identifier", "type_identifier", "qualified_type"}
            ),
            None,
        )
        _assign(
            scope,
            text_of(ctx.source, name_node),
            _eval(value_node, scope, ctx) if value_node is not None else None,
        )


def _walk_func(node, scope: _Scope, ctx: _Ctx, extras: dict[str, _Sym]) -> None:
    if id(node) in ctx.consumed_funcs:
        return
    ctx.consumed_funcs.add(id(node))
    local = _Scope(dict(scope.bindings), set(scope.assigned))
    params = node.child_by_field_name("parameters")
    if params is not None:
        _bind_params(_parameter_pairs(ctx.source, params), local, ctx)
    for name, sym in extras.items():
        local.bindings[name] = sym
        local.assigned.discard(name)
    body = next((c for c in named_children(node) if c.type == "block"), None)
    if body is not None:
        _walk(body, local, ctx)


def _fork(scope: _Scope) -> _Scope:
    """Nested := bindings die with the block. Outer names stay visible."""
    return _Scope(dict(scope.bindings), set())


def _walk_if(node, scope: _Scope, ctx: _Ctx) -> None:
    local = _fork(scope)
    for child in named_children(node):
        if child.type == "short_var_declaration":
            _apply_assign(child, local, ctx)
        else:
            _walk(child, local, ctx)


def _range_names(source: bytes, clause) -> list[str]:
    lists = [c for c in named_children(clause) if c.type == "expression_list"]
    if not lists:
        return []
    return [
        text_of(source, item)
        for item in named_children(lists[0])
        if item.type == "identifier" and text_of(source, item) not in {"", "_"}
    ]


def _bind_range(clause, local: _Scope, outer: _Scope, ctx: _Ctx) -> None:
    names = _range_names(ctx.source, clause)
    exprs = [c for c in named_children(clause) if c.type != "expression_list"]
    target = _eval(exprs[0], local, ctx) if exprs else None
    if target is not None and target.kind == "handler" and target.handler_file:
        value = target
    else:
        value = _Sym("shadow")
    defining = any(child.type == ":=" for child in clause.children)
    if not names:
        return
    bindings = {name: _Sym("shadow") for name in names}
    bindings[names[-1]] = value
    dest = local if defining else outer
    for name, sym in bindings.items():
        if defining:
            dest.bindings[name] = sym
        else:
            _assign(dest, name, sym)
            local.bindings[name] = dest.bindings[name]


def _walk_for(node, scope: _Scope, ctx: _Ctx) -> None:
    local = _fork(scope)
    for child in named_children(node):
        if child.type == "range_clause":
            _bind_range(child, local, scope, ctx)
        elif child.type == "for_clause":
            for part in named_children(child):
                if part.type == "short_var_declaration":
                    _apply_assign(part, local, ctx)
        elif child.type == "block":
            _walk(child, local, ctx)


def _walk(node, scope: _Scope, ctx: _Ctx) -> None:
    if node.type in {"short_var_declaration", "assignment_statement"}:
        _apply_assign(node, scope, ctx)
        return
    if node.type == "const_declaration":
        _apply_const(node, scope, ctx)
        return
    if node.type == "call_expression":
        _on_call(node, scope, ctx)
        return
    if node.type == "func_literal":
        _walk_func(node, scope, ctx, {})
        return
    if node.type == "block":
        local = _fork(scope)
        for stmt in _statements(node):
            _walk(stmt, local, ctx)
        return
    if node.type == "if_statement":
        _walk_if(node, scope, ctx)
        return
    if node.type == "for_statement":
        _walk_for(node, scope, ctx)
        return
    for child in named_children(node):
        _walk(child, scope, ctx)


def _on_call(call, scope: _Scope, ctx: _Ctx) -> None:
    consumed: set[int] = set()
    _try_route(call, scope, ctx, consumed)
    for arg in _arg_nodes(ctx.source, call):
        if arg.type == "func_literal" and id(arg) not in consumed:
            _walk_func(arg, scope, ctx, {})


def _family(field: str, libs: frozenset[str]) -> str | None:
    if field in _GIN_METHODS or field == "Any":
        return "gin" if "gin" in libs else None
    if field in _CHI_METHODS or field == "Method":
        return "chi" if "chi" in libs else None
    if field in {"HandleFunc", "Methods"}:
        return "mux" if "mux" in libs else None
    if field == "Handle" and ("gin" in libs or "mux" in libs):
        return "handle"
    if field == "Route":
        return "chi" if "chi" in libs else None
    return None


def _under_methods(call, source: bytes) -> bool:
    parent = call.parent
    if parent is None or parent.type != "selector_expression":
        return False
    field = parent.child_by_field_name("field")
    if field is None or text_of(source, field) != "Methods":
        return False
    return parent.parent is not None and parent.parent.type == "call_expression"


def _try_route(call, scope: _Scope, ctx: _Ctx, consumed: set[int]) -> None:
    selected = _selector(ctx.source, call)
    if selected is None:
        return
    operand, field = selected
    family = _family(field, ctx.libs)
    if family is None:
        return
    line = call.start_point[0] + 1
    if field == "Methods":
        if operand.type != "call_expression":
            return
        inner = _selector(ctx.source, operand)
        if inner is None or inner[1] != "HandleFunc":
            return
        _emit_mux(operand, call, scope, ctx)
        return
    if field == "Route":
        _emit_route_group(call, operand, scope, ctx, consumed, line)
        return
    if field == "HandleFunc":
        if _under_methods(call, ctx.source):
            return
        router = _as_router(_eval(operand, scope, ctx))
        if router is None or router.library != "mux":
            ctx.issue("go_http_router_unresolved", line)
            return
        ctx.issue("go_http_route_dynamic", line)
        return
    if field == "Handle":
        _emit_handle(call, operand, scope, ctx, line)
        return
    if field == "Any":
        router = _as_router(_eval(operand, scope, ctx))
        ctx.issue(
            "go_http_router_unresolved" if router is None else "go_http_route_dynamic",
            line,
        )
        return
    method = _GIN_METHODS.get(field) or _CHI_METHODS.get(field)
    if method is None:
        return
    library = "gin" if field in _GIN_METHODS else "chi"
    _emit_shortcut(call, operand, scope, ctx, line, method, library)


def _emit_route_group(
    call, operand, scope: _Scope, ctx: _Ctx, consumed: set[int], line: int
) -> None:
    router = _as_router(_eval(operand, scope, ctx))
    if router is None or router.library != "chi":
        ctx.issue("go_http_router_unresolved", line)
        return
    args = _arg_nodes(ctx.source, call)
    path = _path_value(_eval(args[0], scope, ctx) if args else None)
    prefix = _join(router.prefix, path) if router.prefix is not None else None
    literal = next((arg for arg in args if arg.type == "func_literal"), None)
    if literal is None:
        return
    params = literal.child_by_field_name("parameters")
    pairs = _parameter_pairs(ctx.source, params) if params is not None else ()
    target = next((name for name, _ in pairs if name and name != "_"), "")
    extras = {}
    if target:
        extras[target] = _Sym("router", library="chi", prefix=prefix)
    consumed.add(id(literal))
    _walk_func(literal, scope, ctx, extras)


def _emit_shortcut(
    call, operand, scope, ctx: _Ctx, line: int, method: str, library: str
) -> None:
    router = _as_router(_eval(operand, scope, ctx))
    if router is None or router.library != library:
        ctx.issue("go_http_router_unresolved", line)
        return
    args = _arg_nodes(ctx.source, call)
    if router.prefix is None or not args:
        ctx.issue("go_http_route_dynamic", line)
        return
    path = _join(router.prefix, _path_value(_eval(args[0], scope, ctx)))
    if path is None:
        ctx.issue("go_http_route_dynamic", line)
        return
    handler_node = args[-1] if len(args) > 1 else None
    handler = _eval(handler_node, scope, ctx) if handler_node else None
    _emit_endpoint(ctx, line, method, path, handler)


def _emit_handle(call, operand, scope, ctx: _Ctx, line: int) -> None:
    router = _as_router(_eval(operand, scope, ctx))
    if router is None or router.library not in {"gin", "mux"}:
        ctx.issue("go_http_router_unresolved", line)
        return
    if router.library == "mux" or router.prefix is None:
        ctx.issue("go_http_route_dynamic", line)
        return
    args = _arg_nodes(ctx.source, call)
    method = _method_token(_eval(args[0], scope, ctx) if args else None)
    path_sym = _eval(args[1], scope, ctx) if len(args) > 1 else None
    path = _join(router.prefix, _path_value(path_sym))
    if method is None or path is None:
        ctx.issue("go_http_route_dynamic", line)
        return
    handler_node = args[-1] if len(args) > 2 else None
    handler = _eval(handler_node, scope, ctx) if handler_node else None
    _emit_endpoint(ctx, line, method, path, handler)


def _emit_mux(handle_call, methods_call, scope: _Scope, ctx: _Ctx) -> None:
    selected = _selector(ctx.source, handle_call)
    line = methods_call.start_point[0] + 1
    if selected is None:
        ctx.issue("go_http_router_unresolved", line)
        return
    operand, _field = selected
    router = _as_router(_eval(operand, scope, ctx))
    if router is None or router.library != "mux":
        ctx.issue("go_http_router_unresolved", line)
        return
    handle_args = _arg_nodes(ctx.source, handle_call)
    if router.prefix is None or not handle_args:
        ctx.issue("go_http_route_dynamic", line)
        return
    path = _join(router.prefix, _path_value(_eval(handle_args[0], scope, ctx)))
    if path is None:
        ctx.issue("go_http_route_dynamic", line)
        return
    methods = []
    for arg in _arg_nodes(ctx.source, methods_call):
        token = _method_token(_eval(arg, scope, ctx))
        if token is None:
            ctx.issue("go_http_route_dynamic", line)
            return
        methods.append(token)
    if not methods:
        ctx.issue("go_http_route_dynamic", line)
        return
    handler_node = handle_args[-1] if len(handle_args) > 1 else None
    handler = _eval(handler_node, scope, ctx) if handler_node is not None else None
    for method in methods:
        _emit_endpoint(ctx, line, method, path, handler)


def _emit_endpoint(
    ctx: _Ctx, line: int, method: str, path: str, handler_sym: _Sym | None
) -> None:
    if _contains_secret(path) or _contains_secret(method):
        ctx.issue("go_http_route_dynamic", line)
        return
    handler = _handler_entity(ctx, handler_sym)
    if handler is None:
        ctx.issue("go_http_handler_unresolved", line)
        qualified = package_qualified(ctx.module.package_name, f"{method}:{path}")
        name = method
        handler_line = line
        handler_path = ctx.module.path
    else:
        qualified = handler.qualified_name
        name = handler.name
        handler_line = handler.start_line or line
        handler_path = handler.file_path or ctx.module.path
    entity_key = endpoint_id(
        ctx.adapter_context.repository_id,
        ctx.module.path,
        qualified,
        method,
        path,
        (f"{ctx.module.path}:{line}:{method}:{path}",),
    )
    endpoint = Entity(
        entity_key,
        ctx.adapter_context.repository_id,
        ctx.adapter_context.snapshot_id,
        EntityType.ENDPOINT,
        name,
        qualified,
        ctx.module.path,
        line,
        line,
        "http",
        framework_kind="go-http",
        attributes=(("method", method), ("path", path)),
    )
    ctx.entities[endpoint.id] = endpoint
    route_ref = evidence_id(
        ctx.adapter_context.snapshot_id, ctx.module.path, line, line, ROUTE_RULE
    )
    ctx.evidence[route_ref] = Evidence(
        route_ref,
        ctx.adapter_context.snapshot_id,
        ctx.module.path,
        line,
        line,
        ROUTE_RULE,
    )
    if handler is None:
        return
    handler_ref = evidence_id(
        ctx.adapter_context.snapshot_id,
        handler_path,
        handler_line,
        handler_line,
        HANDLER_RULE,
    )
    ctx.evidence[handler_ref] = Evidence(
        handler_ref,
        ctx.adapter_context.snapshot_id,
        handler_path,
        handler_line,
        handler_line,
        HANDLER_RULE,
    )
    edge_key = edge_id(
        ctx.adapter_context.snapshot_id, EdgeType.HANDLED_BY, endpoint.id, handler.id
    )
    current = ctx.edges.get(edge_key)
    refs = set(current.evidence_ids) if current else set()
    refs.add(handler_ref)
    ctx.edges[edge_key] = Edge(
        edge_key,
        ctx.adapter_context.snapshot_id,
        EdgeType.HANDLED_BY,
        endpoint.id,
        handler.id,
        HANDLER_RULE,
        tuple(sorted(refs)),
    )


def _finish(
    ctx_issues: list[AdapterDiagnostic],
    base: FactBatch,
    context: AdapterContext,
    entities,
    edges,
    evidence,
):
    unique = sorted(
        set(ctx_issues),
        key=lambda item: (item.relative_path or "", item.line or 0, item.code),
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
        for ordinal, item in enumerate(unique)
    )
    facts = FactBatch(
        context.repository_id,
        context.snapshot_id,
        tuple(sorted(entities.values(), key=lambda item: item.id)),
        tuple(sorted(edges.values(), key=lambda item: item.id)),
        tuple(evidence[key] for key in sorted(evidence)),
        tuple(base.diagnostics) + canonical,
    )
    return facts, tuple(unique)


class GoHTTPFrameworkAdapter:
    """Emit Gin, chi, and gorilla/mux endpoints. Not a reviewed deep profile."""

    allow_unverified_versions = True
    reviewed_deep_support = False

    descriptor = AdapterDescriptor(
        adapter_id="rkg.go-http",
        adapter_version="0.1.0",
        contract_version=CONTRACT_VERSION,
        kind=AdapterKind.FRAMEWORK,
        language="go",
        framework="go-http",
        grammar_or_target="gin chi gorilla/mux static routes",
        file_patterns=("*.go", "**/*.go"),
        ignore_patterns=("**/vendor/**", "**/testdata/**", "**/*_test.go"),
        capabilities=("routes",),
    )

    def technology_detectors(self) -> tuple[object, ...]:
        return (GoHTTPDetector(),)

    def detect(self, manifest: SourceManifest, parsed: ParseResult) -> DetectionReport:
        del manifest
        evidence = tuple(
            sorted(
                (
                    DetectionEvidence(module.path, DETECT_RULE)
                    for module in _modules(parsed).values()
                    if _http_aliases(module)
                ),
                key=lambda item: item.relative_path,
            )
        )
        if not evidence:
            return DetectionReport()
        return DetectionReport((TechnologyDetection("go-http", None, evidence),))

    def extract(
        self, context: AdapterContext, parsed: ParseResult, base: FactBatch
    ) -> AdapterResult:
        if (
            base.repository_id != context.repository_id
            or base.snapshot_id != context.snapshot_id
        ):
            raise ValueError("candidate ownership does not match adapter context")
        modules = _modules(parsed)
        if not any(_http_aliases(module) for module in modules.values()):
            return AdapterResult(base, self._capabilities(), ())
        entities = {item.id: item for item in base.entities}
        edges = {item.id: item for item in base.edges}
        evidence = {item.id: item for item in base.evidence}
        callable_entities = tuple(
            item for item in entities.values() if item.type == EntityType.CALLABLE
        )
        functions = _functions(modules)
        constants, ambiguous_constants = _package_constants(modules)
        issues: list[AdapterDiagnostic] = []
        for module in sorted(modules.values(), key=lambda item: item.path):
            aliases = _http_aliases(module)
            if not aliases:
                continue
            ctx = _Ctx(
                context,
                module,
                aliases,
                functions,
                constants,
                ambiguous_constants,
                entities,
                edges,
                evidence,
                callable_entities,
                issues,
            )
            scope = _Scope({}, set())
            for item in module.callables:
                if item.kind == "interface_method":
                    continue
                local = _Scope(dict(scope.bindings), set())
                _bind_params(item.parameters, local, ctx)
                body = next(
                    (
                        child
                        for child in named_children(item.node)
                        if child.type == "block"
                    ),
                    None,
                )
                if body is not None:
                    _walk(body, local, ctx)
        facts, diagnostics = _finish(issues, base, context, entities, edges, evidence)
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
            for name in sorted(GoHTTPFrameworkAdapter.descriptor.capabilities)
        )


class GoHTTPDetector:
    """Surface go-http evidence so deep selection can run."""

    def detect(self, manifest: SourceManifest, parsed: ParseResult):
        from rkg.detection.contracts import FrameworkObservation

        report = GoHTTPFrameworkAdapter().detect(manifest, parsed)
        return FrameworkObservation(report)
