"""Conservative TypeScript import, call, configuration and HTTP resolution."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field, replace
from urllib.parse import urlsplit

from tree_sitter import Node

from rkg.adapters.contracts import (
    AdapterContext,
    AdapterDiagnostic,
    ParseResult,
)
from rkg.adapters.typescript_language import _canonical_diagnostics
from rkg.adapters.typescript_parse import (
    TsDefinition,
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
    Edge,
    EdgeType,
    Entity,
    EntityType,
    Evidence,
    FactBatch,
    configuration_id,
    edge_id,
    evidence_id,
    source_entity_id,
)

IMPORT_RULE = "RKG.typescript.import.v1"
CALL_RULE = "RKG.typescript.call.v1"
CONFIG_RULE = "RKG.typescript_config.key.v1"
HTTP_RULE = "RKG.typescript_http.origin.v1"

_HTTP_CLIENT_METHODS = frozenset(
    {"get", "put", "post", "patch", "delete", "request", "fetch"}
)
_HTTP_METHOD_FROM_CALLEE = {
    "get": "GET",
    "put": "PUT",
    "post": "POST",
    "patch": "PATCH",
    "delete": "DELETE",
    "fetch": "GET",
}


@dataclass
class _Index:
    modules: list[TsModule]
    by_name: dict[str, list[Entity]]
    by_path: dict[str, TsModule]
    files: set[str]
    aliases: dict[str, str]

    def __init__(self, parsed: ParseResult, candidate: FactBatch) -> None:
        self.modules = [
            unit.representation
            for unit in parsed.units
            if unit.language == "typescript"
            and isinstance(unit.representation, TsModule)
        ]
        self.by_path = {module.path: module for module in self.modules}
        self.files = set(self.by_path)
        self.aliases = next((dict(module.aliases) for module in self.modules), {})
        self.by_name = defaultdict(list)
        for entity in candidate.entities:
            self.by_name[entity.qualified_name].append(entity)

    def unique(self, name: str | None, types: frozenset[EntityType]) -> Entity | None:
        if name is None:
            return None
        matches = [item for item in self.by_name[name] if item.type in types]
        return matches[0] if len(matches) == 1 else None

    def import_target(self, name: str | None) -> Entity | None:
        if name is None:
            return None
        modules = [
            item for item in self.by_name[name] if item.type == EntityType.SOURCE_UNIT
        ]
        symbols = [
            item
            for item in self.by_name[name]
            if item.type in (EntityType.TYPE, EntityType.CALLABLE)
        ]
        matches = modules + symbols
        return matches[0] if len(matches) == 1 else None


@dataclass
class _Edges:
    context: AdapterContext
    edges: dict[str, Edge] = field(default_factory=dict)
    evidence: dict[str, Evidence] = field(default_factory=dict)

    def __init__(self, context: AdapterContext, candidate: FactBatch) -> None:
        self.context = context
        self.edges = {item.id: item for item in candidate.edges}
        self.evidence = {item.id: item for item in candidate.evidence}

    def add(
        self, kind: EdgeType, source: str, target: str, path: str, line: int, rule: str
    ) -> None:
        ref_id = evidence_id(self.context.snapshot_id, path, line, line, rule)
        self.evidence[ref_id] = Evidence(
            ref_id, self.context.snapshot_id, path, line, line, rule
        )
        key = edge_id(self.context.snapshot_id, kind, source, target)
        current = self.edges.get(key)
        references = set(current.evidence_ids) if current else set()
        references.add(ref_id)
        self.edges[key] = Edge(
            key,
            self.context.snapshot_id,
            kind,
            source,
            target,
            rule,
            tuple(sorted(references)),
        )


@dataclass
class _Facts:
    context: AdapterContext
    entities: dict[str, Entity]
    edges: _Edges
    diagnostics: list[AdapterDiagnostic]
    roots: set[str]

    def issue(self, code: str, path: str, line: int) -> None:
        self.diagnostics.append(AdapterDiagnostic(code, path, line))

    def ensure(self, entity: Entity) -> Entity:
        current = self.entities.get(entity.id)
        if current is not None:
            return current
        self.entities[entity.id] = entity
        return entity

    def configuration(self, key: str, path: str, line: int) -> Entity:
        entity_id = configuration_id(self.context.repository_id, "environment", "", key)
        return self.ensure(
            Entity(
                entity_id,
                self.context.repository_id,
                self.context.snapshot_id,
                EntityType.CONFIGURATION,
                key,
                f"environment:{key}",
                path,
                line,
                line,
                "environment",
                attributes=(("kind", "environment"), ("owner", "")),
            )
        )

    def http_service(self, origin: str) -> Entity:
        entity_id = source_entity_id(
            self.context.repository_id,
            "",
            EntityType.EXTERNAL_DEPENDENCY,
            f"http_service:{origin}",
        )
        return self.ensure(
            Entity(
                entity_id,
                self.context.repository_id,
                self.context.snapshot_id,
                EntityType.EXTERNAL_DEPENDENCY,
                origin,
                origin,
                language_kind="http_service",
                attributes=(("kind", "http_service"), ("origin", origin)),
            )
        )

    def link(
        self, user_id: str, target: Entity, path: str, line: int, rule: str
    ) -> None:
        self.edges.add(EdgeType.DEPENDS_ON, user_id, target.id, path, line, rule)


def _origin(url: str) -> str | None:
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError:
        return None
    scheme = parts.scheme.lower()
    if scheme not in {"http", "https"} or not parts.hostname or not parts.netloc:
        return None
    host = f"[{parts.hostname}]" if ":" in parts.hostname else parts.hostname
    if port and not (
        (scheme == "https" and port == 443) or (scheme == "http" and port == 80)
    ):
        return f"{scheme}://{host}:{port}"
    return f"{scheme}://{host}"


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


def _is_import_meta_env(source: bytes, node: Node | None) -> bool:
    """True for `import.meta.env` member expression (optionally cast)."""
    node = _unwrap_expr(node)
    if node is None or node.type != "member_expression":
        return False
    obj = child_named(node, "object")
    prop = child_named(node, "property")
    if identifier_name(source, prop) != "env":
        return False
    if obj is None:
        return False
    if obj.type == "meta_property":
        return text_of(source, obj) == "import.meta"
    if obj.type != "member_expression":
        return False
    return (
        text_of(source, child_named(obj, "object")) == "import"
        and identifier_name(source, child_named(obj, "property")) == "meta"
    )


def _is_process_env(source: bytes, node: Node | None) -> bool:
    """True for `process.env` member expression (optionally cast)."""
    node = _unwrap_expr(node)
    if node is None or node.type != "member_expression":
        return False
    obj = child_named(node, "object")
    prop = child_named(node, "property")
    return (
        obj is not None
        and obj.type == "identifier"
        and text_of(source, obj) == "process"
        and identifier_name(source, prop) == "env"
    )


def _is_env_source(source: bytes, node: Node | None) -> bool:
    return _is_import_meta_env(source, node) or _is_process_env(source, node)


def _member_parts(source: bytes, node: Node | None) -> list[str] | None:
    parts: list[str] = []
    current = node
    while current is not None:
        if current.type == "identifier":
            parts.append(text_of(source, current))
            parts.reverse()
            return parts
        if current.type == "member_expression":
            prop = child_named(current, "property")
            name = identifier_name(source, prop)
            if name is None:
                return None
            parts.append(name)
            current = child_named(current, "object")
            continue
        if current.type == "this":
            parts.append("this")
            parts.reverse()
            return parts
        return None
    return None


def _call_callee(node: Node) -> Node | None:
    return child_named(node, "function")


def _call_args(node: Node) -> list[Node]:
    args = child_named(node, "arguments")
    if args is None:
        return []
    return [child for child in named_children(args)]


def _call_type_arg_text(source: bytes, call: Node) -> str | None:
    """Simple generic type argument on a call (e.g. get<Order[]> → Order[])."""
    for child in named_children(call):
        if child.type != "type_arguments":
            continue
        raw = text_of(source, child).strip()
        if raw.startswith("<") and raw.endswith(">"):
            raw = raw[1:-1].strip()
        if not raw or len(raw) > 80:
            return None
        if any(token in raw for token in ("=>", "{", "extends", "infer", "?", ":")):
            return None
        return raw
    return None


def _fetch_method_literal(source: bytes, call: Node) -> str | None:
    """Literal RequestInit.method on fetch(url, { method: 'POST' })."""
    args = _call_args(call)
    if len(args) < 2:
        return None
    options = _unwrap_expr(args[1])
    if options is None or options.type != "object":
        return None
    for child in named_children(options):
        if child.type != "pair":
            continue
        key = child_named(child, "key")
        value = child_named(child, "value")
        key_name = identifier_name(source, key) or string_literal(source, key)
        if key_name != "method" or value is None:
            continue
        literal = string_literal(source, _unwrap_expr(value))
        if literal is None:
            return None
        method = literal.strip().upper()
        if method in {"GET", "PUT", "POST", "PATCH", "DELETE", "HEAD", "OPTIONS"}:
            return method
        return None
    return None


def _relative_http_path(literal: str) -> str | None:
    """Static relative request path; absolute origins stay on ExternalDependency."""
    if _origin(literal) is not None:
        return None
    if not literal or any(ch.isspace() for ch in literal):
        return None
    # Evidence-only: no template leftovers, no scheme-looking values.
    if "${" in literal or "://" in literal:
        return None
    return literal


def _annotate_http_request(
    facts: _Facts,
    caller: Entity,
    *,
    method: str,
    path: str | None,
    response_type: str | None,
) -> None:
    """Attach evidence-based request summary on the calling Callable (List/Graph)."""
    current = facts.entities.get(caller.id, caller)
    attrs = dict(current.attributes)
    request = f"{method} {path}" if path else method
    existing = attrs.get("http_requests")
    if isinstance(existing, str) and existing.strip():
        parts = [part.strip() for part in existing.split("|") if part.strip()]
        if request not in parts:
            parts.append(request)
        attrs["http_requests"] = " | ".join(parts)
    else:
        attrs["http_requests"] = request
    if response_type:
        existing_resp = attrs.get("http_response_types")
        if isinstance(existing_resp, str) and existing_resp.strip():
            resp_parts = [
                part.strip() for part in existing_resp.split("|") if part.strip()
            ]
            if response_type not in resp_parts:
                resp_parts.append(response_type)
            attrs["http_response_types"] = " | ".join(resp_parts)
        else:
            attrs["http_response_types"] = response_type
    facts.entities[caller.id] = Entity(
        current.id,
        current.repository_id,
        current.snapshot_id,
        current.type,
        current.name,
        current.qualified_name,
        current.file_path,
        current.start_line,
        current.end_line,
        current.language_kind,
        current.framework_kind,
        tuple(attrs.items()),
    )


def _maybe_http_client_request(
    module: TsModule,
    call: Node,
    callee: Node | None,
    caller: Entity,
    target: Entity | None,
    facts: _Facts,
) -> None:
    """Record method + static path when calling get/put/fetch (no dynamic guess)."""
    method: str | None = None
    parts = _member_parts(module.source, callee) if callee is not None else None
    is_fetch = parts == ["fetch"] or parts == ["globalThis", "fetch"]
    if target is not None and target.type == EntityType.CALLABLE:
        leaf = target.name.lower()
        if leaf in _HTTP_METHOD_FROM_CALLEE:
            method = _HTTP_METHOD_FROM_CALLEE[leaf]
        elif leaf == "request":
            # request(path, init) — method only when init.method is a literal.
            method = _fetch_method_literal(module.source, call)
    if method is None and is_fetch:
        method = _fetch_method_literal(module.source, call) or "GET"
    if method is None:
        return
    args = _call_args(call)
    path: str | None = None
    if args:
        literal = string_literal(module.source, _unwrap_expr(args[0]))
        if literal is not None:
            path = _relative_http_path(literal)
        elif args[0].type == "template_string" and any(
            child.type == "template_substitution" for child in args[0].children
        ):
            # Dynamic path — method only; AC-RKG-006 forbids inventing the URL.
            path = None
    response_type = _call_type_arg_text(module.source, call)
    _annotate_http_request(
        facts, caller, method=method, path=path, response_type=response_type
    )
    attrs = dict(facts.entities[caller.id].attributes)
    if (
        args
        and args[0].type == "template_string"
        and any(c.type == "template_substitution" for c in args[0].children)
    ):
        attrs["http_path_dynamic"] = True
        attrs["http_path_parameters"] = tuple(
            dict.fromkeys(
                text_of(module.source, n)
                for c in named_children(args[0])
                if c.type == "template_substitution"
                for n in walk_named(c)
                if n.type == "identifier"
                and text_of(module.source, n) not in {"encodeURIComponent"}
            )
        )
    ancestor = call.parent
    while ancestor is not None and ancestor != module.tree.root_node:
        if ancestor.type == "call_expression":
            wrapper = text_of(module.source, child_named(ancestor, "function"))
            if wrapper == "useEffect" and target:
                existing = tuple(attrs.get("callback_calls") or ())
                attrs["callback_calls"] = tuple(
                    dict.fromkeys((*existing, f"useEffect gọi {target.qualified_name}"))
                )
                break
        ancestor = ancestor.parent
    facts.entities[caller.id] = replace(
        facts.entities[caller.id], attributes=tuple(attrs.items())
    )


@dataclass
class _BindingScope:
    """name -> unique qualified target, or None when ambiguous/unknown."""

    names: dict[str, str | None] = field(default_factory=dict)
    instances: dict[str, str | None] = field(default_factory=dict)
    env_params: set[str] = field(default_factory=set)
    local_functions: set[str] = field(default_factory=set)


def _export_name(module: TsModule, node: Node) -> str | None:
    if node.type != "export_statement":
        return None
    decl = child_named(node, "declaration")
    if decl is not None:
        name = child_named(decl, "name")
        return identifier_name(module.source, name)
    for child in named_children(node):
        if child.type in {
            "function_declaration",
            "class_declaration",
            "abstract_class_declaration",
        }:
            return identifier_name(module.source, child_named(child, "name"))
        if child.type == "identifier":
            return text_of(module.source, child)
    return None


def _default_export_target(module: TsModule) -> str | None:
    for node in named_children(module.tree.root_node):
        if node.type != "export_statement":
            continue
        # Only `export default …` — never a named `export class/function`.
        children = list(node.children)
        saw_default = False
        for child in children:
            if child.type == "default":
                saw_default = True
                continue
            if not saw_default or not child.is_named:
                continue
            if child.type == "identifier":
                return f"{module.name}.{text_of(module.source, child)}"
            if child.type in {
                "function_declaration",
                "class_declaration",
                "abstract_class_declaration",
            }:
                name = identifier_name(module.source, child_named(child, "name"))
                return f"{module.name}.{name}" if name else None
            if child.type in {"arrow_function", "function_expression"}:
                return None
            decl = child if child.type == "lexical_declaration" else None
            if decl is None:
                continue
            for declarator in named_children(decl):
                if declarator.type != "variable_declarator":
                    continue
                name = identifier_name(module.source, child_named(declarator, "name"))
                if name:
                    return f"{module.name}.{name}"
    return None


def _module_bindings(module: TsModule, index: _Index) -> _BindingScope:
    scope = _BindingScope()
    for item in module.definitions:
        if item.owner != module.name:
            continue
        scope.names[item.name] = item.qualified_name
        if item.kind in {
            "typescript_function",
            "typescript_async_function",
        }:
            scope.local_functions.add(item.name)
    # const instances and aliases
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
            name = identifier_name(module.source, child_named(declarator, "name"))
            value = child_named(declarator, "value")
            if not name or value is None:
                continue
            if value.type == "new_expression":
                ctor = child_named(value, "constructor")
                ctor_name = identifier_name(module.source, ctor)
                if ctor_name and scope.names.get(ctor_name):
                    scope.instances[name] = scope.names[ctor_name]
                elif ctor_name:
                    target = f"{module.name}.{ctor_name}"
                    if index.unique(target, frozenset({EntityType.TYPE})):
                        scope.instances[name] = target
                        scope.names.setdefault(name, None)
                continue
            if value.type == "identifier":
                ref = text_of(module.source, value)
                if name in scope.names and scope.names[name] is not None:
                    continue
                scope.names[name] = scope.names.get(ref)
                if ref in scope.instances:
                    scope.instances[name] = scope.instances[ref]
    # imports
    for node in named_children(module.tree.root_node):
        if node.type != "import_statement":
            continue
        _apply_import_bindings(module, node, scope, index)
    # reassigned names become ambiguous
    writes = _count_writes(module)
    for name, count in writes.items():
        if count > 1:
            scope.names[name] = None
            scope.instances[name] = None
    return scope


def _apply_import_bindings(
    module: TsModule, node: Node, scope: _BindingScope, index: _Index
) -> None:
    source_node = child_named(node, "source")
    if source_node is None:
        for child in named_children(node):
            if child.type == "string":
                source_node = child
                break
    specifier = string_literal(module.source, source_node)
    if specifier is None:
        return
    target_path = resolve_specifier(module.path, specifier, index.files, index.aliases)
    target_module = index.by_path.get(target_path) if target_path else None
    clause = child_named(node, "import_clause") or next(
        (child for child in named_children(node) if child.type == "import_clause"),
        None,
    )
    if clause is None or target_module is None:
        return
    for child in named_children(clause):
        if child.type == "identifier":
            # default import
            default_target = _default_export_target(target_module)
            bound = text_of(module.source, child)
            scope.names[bound] = default_target
            if default_target:
                # instance default export (orderApi)
                inst = _instance_type_for_binding(target_module, default_target, index)
                if inst:
                    scope.instances[bound] = inst
                elif index.unique(default_target, frozenset({EntityType.CALLABLE})):
                    pass
                elif index.unique(default_target, frozenset({EntityType.TYPE})):
                    scope.instances[bound] = default_target
        elif child.type == "namespace_import":
            alias = None
            for part in named_children(child):
                if part.type == "identifier":
                    alias = text_of(module.source, part)
            if alias:
                scope.names[alias] = target_module.name
        elif child.type == "named_imports":
            for spec in named_children(child):
                if spec.type != "import_specifier":
                    continue
                if any(part.type == "type" for part in spec.children):
                    # type-only import still binds the type name
                    pass
                names = [
                    text_of(module.source, part)
                    for part in named_children(spec)
                    if part.type == "identifier"
                ]
                if not names:
                    continue
                imported = names[0]
                local = names[-1]
                scope.names[local] = f"{target_module.name}.{imported}"
                inst = _instance_type_for_binding(
                    target_module, f"{target_module.name}.{imported}", index
                )
                if inst:
                    scope.instances[local] = inst


def _instance_type_for_binding(
    module: TsModule, qualified: str, index: _Index
) -> str | None:
    short = qualified.rsplit(".", 1)[-1]
    # const orderApi = new OrderApi(...)
    for node in named_children(module.tree.root_node):
        stmt = (
            child_named(node, "declaration")
            if node.type == "export_statement"
            else node
        )
        if stmt is None:
            stmt = node
        if stmt.type not in {"lexical_declaration", "variable_declaration"}:
            continue
        for declarator in named_children(stmt):
            if declarator.type != "variable_declarator":
                continue
            name = identifier_name(module.source, child_named(declarator, "name"))
            value = child_named(declarator, "value")
            if name != short or value is None or value.type != "new_expression":
                continue
            ctor = identifier_name(module.source, child_named(value, "constructor"))
            if ctor:
                return f"{module.name}.{ctor}"
    if index.unique(qualified, frozenset({EntityType.TYPE})):
        return qualified
    return None


def _count_writes(module: TsModule) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for node in walk_named(module.tree.root_node):
        if node.type == "assignment_expression":
            left = child_named(node, "left")
            name = identifier_name(module.source, left)
            if name:
                counts[name] += 1
        if node.type == "variable_declarator":
            name = identifier_name(module.source, child_named(node, "name"))
            if name:
                counts[name] += 1
        if node.type in {
            "function_declaration",
            "class_declaration",
            "abstract_class_declaration",
        }:
            name = identifier_name(module.source, child_named(node, "name"))
            if name and node.parent is not None and node.parent.type == "program":
                counts[name] += 1
            if (
                name
                and node.parent is not None
                and node.parent.type == "export_statement"
                and node.parent.parent is not None
                and node.parent.parent.type == "program"
            ):
                counts[name] += 1
    return counts


def _parameter_names(source: bytes, node: Node | None) -> set[str]:
    if node is None:
        return set()
    params = child_named(node, "parameters") or child_named(node, "formal_parameters")
    if params is None:
        return set()
    names: set[str] = set()
    for child in named_children(params):
        if child.type in {
            "required_parameter",
            "optional_parameter",
            "rest_parameter",
        }:
            pattern = child_named(child, "pattern")
            name = identifier_name(source, pattern) or identifier_name(
                source,
                next(
                    (c for c in named_children(child) if c.type == "identifier"), None
                ),
            )
            if name:
                names.add(name)
        elif child.type == "identifier":
            names.add(text_of(source, child))
    return names


def _resolve_imported_type_name(
    module: TsModule, local_name: str, index: _Index
) -> str | None:
    """Map a local type identifier to a unique Type qualified_name via imports."""
    local_q = f"{module.name}.{local_name}"
    if index.unique(local_q, frozenset({EntityType.TYPE})):
        return local_q
    files = {item.path for item in index.modules}
    aliases = module.aliases
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
        if target_path is None:
            continue
        target_module = next(
            (item for item in index.modules if item.path == target_path), None
        )
        if target_module is None:
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
                if local != local_name:
                    continue
                qualified = f"{target_module.name}.{imported}"
                if index.unique(qualified, frozenset({EntityType.TYPE})):
                    return qualified
    return None


def _pick_or_type_name(source: bytes, annotation: Node | None) -> str | None:
    """Return Type / Pick<Type, …> head type identifier from a type annotation."""
    if annotation is None:
        return None
    node = annotation
    if node.type == "type_annotation":
        node = next(iter(named_children(node)), None)
    if node is None:
        return None
    if node.type in {"type_identifier", "identifier"}:
        return text_of(source, node)
    if node.type == "generic_type":
        name = identifier_name(source, child_named(node, "name")) or text_of(
            source, next(iter(named_children(node)), None)
        )
        args = child_named(node, "type_arguments") or next(
            (c for c in named_children(node) if c.type == "type_arguments"), None
        )
        if name == "Pick" and args is not None:
            first = next(iter(named_children(args)), None)
            return _pick_or_type_name(source, first)
        return name
    return None


def _class_field_types(
    module: TsModule, class_def: TsDefinition, index: _Index | None = None
) -> dict[str, str | None]:
    """Map constructor parameter properties to annotated type qualified names."""
    fields: dict[str, str | None] = {}
    for node in walk_named(class_def.node):
        if node.type != "method_definition":
            continue
        name_node = child_named(node, "name")
        if name_node is None or text_of(module.source, name_node) != "constructor":
            continue
        params = child_named(node, "parameters") or child_named(
            node, "formal_parameters"
        )
        if params is None:
            continue
        for param in named_children(params):
            if param.type not in {"required_parameter", "optional_parameter"}:
                continue
            name = None
            annotation = None
            for child in named_children(param):
                if child.type == "identifier" and name is None:
                    name = text_of(module.source, child)
                if child.type == "type_annotation":
                    annotation = child
            if not name:
                continue
            type_name = _pick_or_type_name(module.source, annotation)
            if type_name is None:
                fields[name] = None
                continue
            if index is not None:
                fields[name] = _resolve_imported_type_name(module, type_name, index)
            else:
                fields[name] = f"{module.name}.{type_name}"
    return fields


def _constructor_arg_types(index: _Index, class_q: str) -> dict[str, str | None]:
    """If Class is constructed once, map param index/name to argument instance types."""
    found: dict[str, set[str]] = defaultdict(set)
    class_module = None
    class_def = None
    for module in index.modules:
        for item in module.definitions:
            if item.qualified_name == class_q and item.kind == "typescript_class":
                class_module = module
                class_def = item
                break
    if class_module is None or class_def is None:
        return {}
    field_order = list(_class_field_types(class_module, class_def, index))
    for module in index.modules:
        scope = _module_bindings(module, index)
        for node in walk_named(module.tree.root_node):
            if node.type != "new_expression":
                continue
            ctor = identifier_name(module.source, child_named(node, "constructor"))
            if not ctor:
                continue
            ctor_q = scope.names.get(ctor) or f"{module.name}.{ctor}"
            if ctor_q != class_q:
                continue
            args_node = child_named(node, "arguments")
            if args_node is None:
                continue
            args = named_children(args_node)
            for idx, arg in enumerate(args):
                if idx >= len(field_order):
                    break
                field = field_order[idx]
                if arg.type == "identifier":
                    inst = scope.instances.get(text_of(module.source, arg))
                    if inst:
                        found[field].add(inst)
                elif arg.type == "new_expression":
                    nested = identifier_name(
                        module.source, child_named(arg, "constructor")
                    )
                    if not nested:
                        continue
                    nested_q = scope.names.get(nested) or f"{module.name}.{nested}"
                    if index.unique(nested_q, frozenset({EntityType.TYPE})):
                        found[field].add(nested_q)
    return {
        name: next(iter(targets)) if len(targets) == 1 else None
        for name, targets in found.items()
    }


def _param_annotated_types(
    module: TsModule, definition: TsDefinition, index: _Index
) -> dict[str, str]:
    """Map parameter names to resolved type qualified names (Pick unwrapped)."""
    params = child_named(definition.node, "parameters") or child_named(
        definition.node, "formal_parameters"
    )
    if params is None:
        return {}
    found: dict[str, str] = {}
    for param in named_children(params):
        if param.type not in {"required_parameter", "optional_parameter"}:
            continue
        name = None
        annotation = None
        for child in named_children(param):
            if child.type == "identifier" and name is None:
                name = text_of(module.source, child)
            if child.type == "type_annotation":
                annotation = child
        if not name or annotation is None:
            continue
        type_name = _pick_or_type_name(module.source, annotation)
        if type_name is None:
            continue
        resolved = _resolve_imported_type_name(module, type_name, index)
        if resolved:
            found[name] = resolved
    return found


def _interface_property_type(
    index: _Index, interface_q: str, property_name: str
) -> str | None:
    """Return Pick-unwrapped type name text for an interface property, if unique."""
    for module in index.modules:
        for item in module.definitions:
            if (
                item.qualified_name != interface_q
                or item.kind != "typescript_interface"
            ):
                continue
            for node in walk_named(item.node):
                if node.type != "property_signature":
                    continue
                name = identifier_name(module.source, child_named(node, "name"))
                if name != property_name:
                    continue
                annotation = child_named(node, "type") or next(
                    (
                        child
                        for child in named_children(node)
                        if child.type == "type_annotation"
                    ),
                    None,
                )
                type_name = _pick_or_type_name(module.source, annotation)
                if type_name is None:
                    return None
                return _resolve_imported_type_name(module, type_name, index)
    return None


def _unique_implementer_method(
    index: _Index, interface_q: str, method: str
) -> str | None:
    """If exactly one class method matches an interface method name, return it."""
    matches: list[str] = []
    for module in index.modules:
        for item in module.definitions:
            if item.kind != "typescript_class":
                continue
            # class implements Interface — check implements clause text
            implements = False
            for node in named_children(item.node):
                if node.type != "class_heritage":
                    continue
                if interface_q.rsplit(".", 1)[-1] in text_of(module.source, node):
                    implements = True
            if not implements:
                continue
            candidate = f"{item.qualified_name}.{method}"
            if index.unique(candidate, frozenset({EntityType.CALLABLE})):
                matches.append(candidate)
    return matches[0] if len(matches) == 1 else None


def _resolve_callee(
    module: TsModule,
    scope: _BindingScope,
    index: _Index,
    callee: Node,
    class_q: str | None,
    field_types: dict[str, str | None],
    injected: dict[str, str | None],
    param_types: dict[str, str] | None = None,
) -> str | None:
    param_types = param_types or {}
    parts = _member_parts(module.source, callee)
    if parts is None:
        return None
    if len(parts) == 1:
        name = parts[0]
        target = scope.names.get(name)
        if target:
            return target
        return None
    if parts[0] == "this" and class_q and len(parts) == 2:
        method = f"{class_q}.{parts[1]}"
        if index.unique(method, frozenset({EntityType.CALLABLE})):
            return method
        return (
            method if index.unique(method, frozenset({EntityType.CALLABLE})) else None
        )
    if parts[0] == "this" and class_q and len(parts) == 3:
        field, method = parts[1], parts[2]
        type_q = injected.get(field) or field_types.get(field)
        if type_q is None:
            return None
        target = f"{type_q}.{method}"
        if index.unique(target, frozenset({EntityType.CALLABLE})):
            return target
        return _unique_implementer_method(index, type_q, method)
    if parts[0] == "globalThis" and len(parts) == 2:
        return None
    # param.field.method where param is a typed dependency bag interface
    if len(parts) == 3:
        root, field, method = parts
        bag = param_types.get(root)
        if bag is None:
            return None
        field_type = _interface_property_type(index, bag, field)
        if field_type is None:
            return None
        target = f"{field_type}.{method}"
        if index.unique(target, frozenset({EntityType.CALLABLE})):
            return target
        return None
    # obj.method — instance, Pick<Type>/Type parameter, or class/type binding
    if len(parts) == 2:
        root, method = parts
        typed = param_types.get(root)
        if typed:
            target = f"{typed}.{method}"
            if index.unique(target, frozenset({EntityType.CALLABLE})):
                return target
        if (
            root in scope.names
            and scope.names[root] is None
            and root not in param_types
        ):
            return None
        inst = scope.instances.get(root)
        if inst:
            target = f"{inst}.{method}"
            if index.unique(target, frozenset({EntityType.CALLABLE})):
                return target
        bound = scope.names.get(root)
        if bound:
            target = f"{bound}.{method}"
            if index.unique(target, frozenset({EntityType.CALLABLE})):
                return target
            if index.unique(bound, frozenset({EntityType.TYPE})):
                nested = f"{bound}.{method}"
                if index.unique(nested, frozenset({EntityType.CALLABLE})):
                    return nested
    return None


def _definition_class(definition: TsDefinition) -> str | None:
    if definition.kind in {"typescript_method", "typescript_async_method"}:
        return definition.owner
    return None


def _resolve_imports(
    module: TsModule,
    source: Entity,
    index: _Index,
    edges: _Edges,
    diagnostics: list[AdapterDiagnostic],
) -> None:
    for node in named_children(module.tree.root_node):
        if node.type != "import_statement":
            continue
        line = node.start_point[0] + 1
        source_node = None
        for child in named_children(node):
            if child.type == "string":
                source_node = child
        specifier = string_literal(module.source, source_node)
        if specifier is None:
            diagnostics.append(
                AdapterDiagnostic("typescript_import_unresolved", module.path, line)
            )
            continue
        target_path = resolve_specifier(
            module.path, specifier, index.files, index.aliases
        )
        if target_path is None:
            # External package — record ExternalDependency once per package name.
            if not specifier.startswith(".") and not specifier.startswith("@/"):
                package = specifier.split("/", 2)
                name = (
                    "/".join(package[:2])
                    if specifier.startswith("@") and len(package) >= 2
                    else package[0]
                )
                entity_id = source_entity_id(
                    edges.context.repository_id,
                    "",
                    EntityType.EXTERNAL_DEPENDENCY,
                    f"npm:{name}",
                )
                entity = Entity(
                    entity_id,
                    edges.context.repository_id,
                    edges.context.snapshot_id,
                    EntityType.EXTERNAL_DEPENDENCY,
                    name,
                    name,
                    language_kind="npm_package",
                    attributes=(("kind", "npm_package"), ("package", name)),
                )
                # Attach via depends_on from source unit.
                # Store on a side channel through edges only if entity exists in batch —
                # caller merges entities. Use diagnostics-free external edge by
                # returning via index mutation:
                index.by_name[entity.qualified_name].append(entity)
                edges.add(
                    EdgeType.IMPORTS,
                    source.id,
                    entity.id,
                    module.path,
                    line,
                    IMPORT_RULE,
                )
                # Keep entity for fact merge
                if not hasattr(index, "extra_entities"):
                    index.extra_entities = {}  # type: ignore[attr-defined]
                index.extra_entities[entity.id] = entity  # type: ignore[attr-defined]
            else:
                diagnostics.append(
                    AdapterDiagnostic("typescript_import_unresolved", module.path, line)
                )
            continue
        target_module = index.by_path[target_path]
        clause = next(
            (child for child in named_children(node) if child.type == "import_clause"),
            None,
        )
        targets: list[str] = []
        if clause is None:
            targets.append(target_module.name)
        else:
            for child in named_children(clause):
                if child.type == "identifier":
                    default_target = _default_export_target(target_module)
                    targets.append(default_target or target_module.name)
                elif child.type == "namespace_import":
                    targets.append(target_module.name)
                elif child.type == "named_imports":
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
                        imported = names[0]
                        targets.append(f"{target_module.name}.{imported}")
        linked = False
        for target_name in targets:
            target = index.import_target(target_name)
            if target is None:
                target = index.unique(
                    target_module.name, frozenset({EntityType.SOURCE_UNIT})
                )
            if target is not None and target.id != source.id:
                edges.add(
                    EdgeType.IMPORTS,
                    source.id,
                    target.id,
                    module.path,
                    line,
                    IMPORT_RULE,
                )
                linked = True
        if not linked:
            diagnostics.append(
                AdapterDiagnostic("typescript_import_unresolved", module.path, line)
            )


def _scan_calls(
    module: TsModule,
    definition: TsDefinition,
    caller: Entity,
    scope: _BindingScope,
    index: _Index,
    edges: _Edges,
    diagnostics: list[AdapterDiagnostic],
    facts: _Facts,
) -> None:
    body = body_of_definition(definition)
    if body is None:
        return
    class_q = _definition_class(definition)
    field_types = (
        _class_field_types(
            module,
            next(item for item in module.definitions if item.qualified_name == class_q),
            index,
        )
        if class_q
        else {}
    )
    injected = _constructor_arg_types(index, class_q) if class_q else {}
    param_types = _param_annotated_types(module, definition, index)
    # Prefer concrete injected types for fields.
    for key, value in list(field_types.items()):
        if injected.get(key):
            field_types[key] = injected[key]
        elif value and not index.unique(value, frozenset({EntityType.TYPE})):
            # interface annotation — try unique class with same method later
            pass
        elif value and index.unique(value, frozenset({EntityType.TYPE})):
            entity = index.unique(value, frozenset({EntityType.TYPE}))
            if entity and entity.language_kind == "typescript_interface":
                # replace with unique constructor injection when available
                if injected.get(key):
                    field_types[key] = injected[key]

    local_scope = _BindingScope(
        names=dict(scope.names),
        instances=dict(scope.instances),
        env_params=set(scope.env_params),
        local_functions=set(scope.local_functions),
    )
    # parameters are unknown bindings unless env
    for param in _parameter_names(module.source, definition.node):
        local_scope.names.setdefault(param, None)

    local_scope.env_params.update(_env_default_params(module, definition))
    # Mark params as env when a call site passes import.meta.env / process.env.
    if definition.name and _function_receives_env_source(
        index, definition.qualified_name
    ):
        for param in _parameter_names(module.source, definition.node):
            local_scope.env_params.add(param)

    for node in walk_named(body):
        line = node.start_point[0] + 1
        if node.type == "call_expression":
            callee = _call_callee(node)
            if callee is not None and callee.type == "import":
                diagnostics.append(
                    AdapterDiagnostic("typescript_import_dynamic", module.path, line)
                )
                continue
            # fetch / globalThis.fetch HTTP
            _maybe_http(module, node, callee, caller, local_scope, facts, diagnostics)
            target_name = (
                _resolve_callee(
                    module,
                    local_scope,
                    index,
                    callee,
                    class_q,
                    field_types,
                    injected,
                    param_types,
                )
                if callee is not None
                else None
            )
            target = index.unique(target_name, frozenset({EntityType.CALLABLE}))
            # Evidence-based outbound request summary for UI→API List/Graph.
            _maybe_http_client_request(module, node, callee, caller, target, facts)
            if target is not None:
                ancestor = node.parent
                while ancestor is not None and ancestor != definition.node:
                    if (
                        ancestor.type == "call_expression"
                        and text_of(module.source, child_named(ancestor, "function"))
                        == "useEffect"
                    ):
                        current = facts.entities[caller.id]
                        attrs = dict(current.attributes)
                        refs = tuple(attrs.get("callback_calls") or ())
                        attrs["callback_calls"] = tuple(
                            dict.fromkeys(
                                (*refs, f"useEffect gọi {target.qualified_name}")
                            )
                        )
                        facts.entities[caller.id] = replace(
                            current, attributes=tuple(attrs.items())
                        )
                        break
                    ancestor = ancestor.parent
            if target is not None and target.id != caller.id:
                edges.add(
                    EdgeType.CALLS,
                    caller.id,
                    target.id,
                    module.path,
                    line,
                    CALL_RULE,
                )
            elif callee is not None and _should_diagnose_call(
                module, callee, local_scope, target_name
            ):
                code = (
                    "typescript_binding_ambiguous"
                    if _is_ambiguous(module, callee, local_scope)
                    else "typescript_call_unresolved"
                    if _member_parts(module.source, callee) is not None
                    else "typescript_call_dynamic"
                )
                # Avoid noisy unresolved for known externals (react hooks, fetch, etc.)
                parts = _member_parts(module.source, callee)
                if parts == ["globalThis", "fetch"] or (
                    parts == ["fetch"] and "fetch" not in local_scope.local_functions
                ):
                    pass
                elif parts and parts[0] in {
                    "console",
                    "JSON",
                    "Promise",
                    "Object",
                    "Array",
                }:
                    pass
                elif (
                    parts
                    and parts[0] in local_scope.names
                    and local_scope.names[parts[0]] is None
                    and len(parts) == 1
                ):
                    diagnostics.append(
                        AdapterDiagnostic(
                            "typescript_binding_ambiguous", module.path, line
                        )
                    )
                elif parts and len(parts) == 1 and parts[0] not in local_scope.names:
                    # unresolved external like useState — skip noise
                    pass
                elif code == "typescript_binding_ambiguous":
                    diagnostics.append(AdapterDiagnostic(code, module.path, line))
                elif (
                    parts
                    and parts[0] in local_scope.instances
                    or (
                        parts
                        and parts[0] in local_scope.names
                        and local_scope.names[parts[0]]
                    )
                ):
                    diagnostics.append(AdapterDiagnostic(code, module.path, line))

        if node.type == "member_expression":
            _maybe_config_key(module, node, caller, local_scope, facts, diagnostics)


def _should_diagnose_call(
    module: TsModule, callee: Node, scope: _BindingScope, target_name: str | None
) -> bool:
    parts = _member_parts(module.source, callee)
    if parts is None:
        return True
    if len(parts) == 1 and parts[0] in scope.names and scope.names[parts[0]] is None:
        return True
    return False


def _is_ambiguous(module: TsModule, callee: Node, scope: _BindingScope) -> bool:
    parts = _member_parts(module.source, callee)
    return bool(
        parts
        and len(parts) == 1
        and parts[0] in scope.names
        and scope.names[parts[0]] is None
    )


def _env_default_params(module: TsModule, definition: TsDefinition) -> set[str]:
    """Parameters whose default value is import.meta.env or process.env."""
    params = child_named(definition.node, "parameters") or child_named(
        definition.node, "formal_parameters"
    )
    if params is None:
        return set()
    found: set[str] = set()
    for param in named_children(params):
        if param.type not in {"required_parameter", "optional_parameter"}:
            continue
        name = None
        for child in named_children(param):
            if child.type == "identifier" and name is None:
                name = text_of(module.source, child)
            if name and _is_env_source(module.source, child):
                found.add(name)
    return found


def _enclosing_definition(module: TsModule, node: Node) -> TsDefinition | None:
    best: TsDefinition | None = None
    best_span: int | None = None
    for item in module.definitions:
        if item.kind not in {
            "typescript_function",
            "typescript_async_function",
            "typescript_method",
            "typescript_async_method",
        }:
            continue
        if item.node.start_byte <= node.start_byte < item.node.end_byte:
            span = item.node.end_byte - item.node.start_byte
            if best_span is None or span < best_span:
                best = item
                best_span = span
    return best


def _function_receives_env_source(index: _Index, qualified: str) -> bool:
    short = qualified.rsplit(".", 1)[-1]
    for module in index.modules:
        for node in walk_named(module.tree.root_node):
            if node.type != "call_expression":
                continue
            callee = _call_callee(node)
            name = identifier_name(module.source, callee)
            if name != short and not (
                callee
                and _member_parts(module.source, callee)
                and _member_parts(module.source, callee)[-1] == short
            ):
                if name != short:
                    continue
            args = _call_args(node)
            if not args:
                continue
            first = _unwrap_expr(args[0])
            if first is not None and _is_env_source(module.source, first):
                return True
            if first is not None and (
                "import.meta.env" in text_of(module.source, args[0])
                or text_of(module.source, args[0]).strip() == "process.env"
            ):
                return True
            # parseEnvironment(source) where caller's source defaults to process.env
            if first is not None and first.type == "identifier":
                arg_name = text_of(module.source, first)
                owner = _enclosing_definition(module, node)
                if owner is not None and arg_name in _env_default_params(module, owner):
                    return True
    return False


def _function_receives_import_meta_env(index: _Index, qualified: str) -> bool:
    """Backward-compatible alias used by older call sites / tests."""
    return _function_receives_env_source(index, qualified)


def _maybe_config_key(
    module: TsModule,
    node: Node,
    owner: Entity,
    scope: _BindingScope,
    facts: _Facts,
    diagnostics: list[AdapterDiagnostic],
) -> None:
    prop = child_named(node, "property")
    obj = child_named(node, "object")
    key = identifier_name(module.source, prop)
    if not key:
        return
    line = node.start_point[0] + 1
    if _is_env_source(module.source, obj):
        facts.link(
            owner.id,
            facts.configuration(key, module.path, line),
            module.path,
            line,
            CONFIG_RULE,
        )
        return
    if obj is not None and obj.type == "identifier":
        name = text_of(module.source, obj)
        if name in scope.env_params:
            facts.link(
                owner.id,
                facts.configuration(key, module.path, line),
                module.path,
                line,
                CONFIG_RULE,
            )


def _maybe_http(
    module: TsModule,
    call: Node,
    callee: Node | None,
    owner: Entity,
    scope: _BindingScope,
    facts: _Facts,
    diagnostics: list[AdapterDiagnostic],
) -> None:
    parts = _member_parts(module.source, callee) if callee is not None else None
    if parts is None:
        return
    is_fetch = parts == ["fetch"] or parts == ["globalThis", "fetch"]
    if not is_fetch:
        return
    line = call.start_point[0] + 1
    if parts == ["fetch"] and (
        "fetch" in scope.local_functions
        or (
            scope.names.get("fetch")
            and scope.names["fetch"]
            and scope.names["fetch"].endswith(".fetch")
            and "fetch" in scope.local_functions
        )
        or "fetch" in scope.local_functions
    ):
        # Local shadowed fetch — no HTTP technology / origin fact.
        return
    # Check local function named fetch in module scope
    if parts == ["fetch"] and "fetch" in scope.local_functions:
        return
    if parts == ["fetch"] and scope.names.get("fetch"):
        # Bound to a local callable named fetch
        target = scope.names["fetch"]
        if target and target.endswith(".fetch"):
            return
    args = _call_args(call)
    if not args:
        return
    literal = string_literal(module.source, args[0])
    if literal is None:
        # template with substitution or non-literal
        if args[0].type == "template_string" and any(
            child.type == "template_substitution" for child in args[0].children
        ):
            diagnostics.append(
                AdapterDiagnostic("typescript_http_unresolved", module.path, line)
            )
        elif args[0].type != "string":
            diagnostics.append(
                AdapterDiagnostic("typescript_http_unresolved", module.path, line)
            )
        return
    origin = _origin(literal)
    if origin is None:
        return
    facts.link(owner.id, facts.http_service(origin), module.path, line, HTTP_RULE)


def resolve_typescript(
    context: AdapterContext, parsed: ParseResult, candidate: FactBatch
) -> tuple[FactBatch, tuple[AdapterDiagnostic, ...]]:
    index = _Index(parsed, candidate)
    edges = _Edges(context, candidate)
    diagnostics = list(parsed.diagnostics)
    facts = _Facts(
        context,
        {item.id: item for item in candidate.entities},
        edges,
        diagnostics,
        {module.name for module in index.modules},
    )
    index.extra_entities = {}  # type: ignore[attr-defined]

    for module in index.modules:
        source = index.unique(module.name, frozenset({EntityType.SOURCE_UNIT}))
        if source is None or source.file_path != module.path:
            continue
        scope = _module_bindings(module, index)
        # Mark local function names including nested in module body for shadowing
        for item in module.definitions:
            if item.kind in {"typescript_function", "typescript_async_function"}:
                if item.owner == module.name:
                    scope.local_functions.add(item.name)
        # Also non-exported function declarations at module level already in definitions
        for node in named_children(module.tree.root_node):
            if node.type == "function_declaration":
                name = identifier_name(module.source, child_named(node, "name"))
                if name:
                    scope.local_functions.add(name)

        _resolve_imports(module, source, index, edges, diagnostics)
        from rkg.adapters.typescript_semantics import enrich_class_semantics

        enrich_class_semantics(module, index, scope, facts, edges)

        for definition in module.definitions:
            if definition.kind not in {
                "typescript_function",
                "typescript_async_function",
                "typescript_method",
                "typescript_async_method",
            }:
                continue
            caller = index.unique(
                definition.qualified_name, frozenset({EntityType.CALLABLE})
            )
            if caller is None or caller.file_path != module.path:
                continue
            _scan_calls(
                module, definition, caller, scope, index, edges, diagnostics, facts
            )

        # Module-level calls / config outside functions (rare) — skip for MVP.

    for entity in getattr(index, "extra_entities", {}).values():
        facts.entities[entity.id] = entity

    ordered = tuple(
        sorted(
            diagnostics,
            key=lambda item: (item.relative_path or "", item.line or 0, item.code),
        )
    )
    # Deduplicate adapter diagnostics while preserving order
    seen: set[tuple[str, str | None, int | None]] = set()
    unique_diags: list[AdapterDiagnostic] = []
    for item in ordered:
        key = (item.code, item.relative_path, item.line)
        if key in seen:
            continue
        seen.add(key)
        unique_diags.append(item)
    unique_tuple = tuple(unique_diags)
    batch = FactBatch(
        candidate.repository_id,
        candidate.snapshot_id,
        tuple(facts.entities[key] for key in sorted(facts.entities)),
        tuple(edges.edges[key] for key in sorted(edges.edges)),
        tuple(edges.evidence[key] for key in sorted(edges.evidence)),
        _canonical_diagnostics(context, unique_tuple),
    )
    return batch, unique_tuple
