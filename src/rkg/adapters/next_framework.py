"""Static Next.js route extraction over TypeScript base facts.

App Router ``page`` files and Pages Router files are Endpoints with
``kind=navigation``. App Router ``route`` files and ``pages/api`` handlers are
HTTP Endpoints (method + path) with ``handled_by`` when the export resolves to
exactly one Callable. ``Link``, ``router.push`` and ``redirect`` literals emit
``calls`` from the enclosing Callable to that page handler only when the
destination matches exactly one navigation route. Dynamic segments use a colon
prefix (``[orderId]`` → ``:orderId``). Route groups ``(name)`` are omitted.
Analyzed modules are never imported or executed.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import PurePosixPath

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
from rkg.detection.contracts import FrameworkObservation
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

DETECT_RULE = "RKG.next.detect.v1"
NAV_RULE = "RKG.next.navigation.v1"
ROUTE_RULE = "RKG.next.route.v1"
HANDLER_RULE = "RKG.next.handler.v1"
_HTTP_METHODS = frozenset(
    {"GET", "PUT", "POST", "PATCH", "DELETE", "HEAD", "OPTIONS"}
)
_PAGE_STEMS = frozenset({"page"})
_ROUTE_STEMS = frozenset({"route"})
_LINK_SPECIFIERS = frozenset({"next/link"})
_ROUTER_SPECIFIERS = frozenset({"next/navigation", "next/router"})
_REDIRECT_SPECIFIERS = frozenset({"next/navigation"})
_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_PLAIN = re.compile(r"^[A-Za-z0-9_-]+$")
_MESSAGES = {
    "next_route_dynamic": "Next file route is not a unique static path.",
    "next_handler_unresolved": (
        "Next page or route export could not be resolved uniquely."
    ),
    "next_navigation_unresolved": "Navigation target is not a unique static route.",
    "next_navigation_ambiguous": "Navigation target matches more than one page.",
    "next_binding_shadowed": "Navigation binding is shadowed or ambiguous.",
}


@dataclass(frozen=True, slots=True)
class _Location:
    path: str
    line: int


@dataclass(frozen=True, slots=True)
class _RouteFile:
    kind: str
    route_path: str
    dynamic: bool


@dataclass(frozen=True, slots=True)
class _ImportBinding:
    role: str
    imported: str
    specifier: str


def _posix(path: str) -> PurePosixPath:
    return PurePosixPath(path.replace("\\", "/"))


def _stem(filename: str) -> str | None:
    for ext in (".tsx", ".ts", ".jsx", ".js"):
        if filename.endswith(ext):
            return filename[: -len(ext)]
    return None


def _segment_token(name: str) -> str | None:
    """Return a path token, ``''`` to omit, or None when the segment is not static."""
    if name.startswith("_"):
        return ""
    if name.startswith("@") and _PLAIN.fullmatch(name[1:] or ""):
        return ""
    if name.startswith("(") and name.endswith(")"):
        inner = name[1:-1]
        if inner.startswith("."):
            return None
        if _PLAIN.fullmatch(inner or ""):
            return ""
        return None
    if name.startswith("[[...") and name.endswith("]]"):
        return None
    if name.startswith("[...") and name.endswith("]"):
        inner = name[4:-1]
        if _IDENT.fullmatch(inner or ""):
            return "*"
        return None
    if name.startswith("[") and name.endswith("]"):
        inner = name[1:-1]
        if _IDENT.fullmatch(inner or ""):
            return f":{inner}"
        return None
    if _PLAIN.fullmatch(name or ""):
        return name
    return None


def file_route(path: str) -> _RouteFile | None:
    """Map an App Router or Pages Router file to a navigation or HTTP path.

    Dynamic segments are spelled ``:name``. Catch-all ``[...name]`` is ``*``.
    Route groups ``(name)`` and parallel slots ``@slot`` are omitted.
    ``None`` means the file is not a Next route convention.
    A dynamic ``_RouteFile`` means the convention matched but the path is not static.
    """
    parts = list(_posix(path).parts)
    if not parts:
        return None
    if parts[0] == "src" and len(parts) > 1 and parts[1] in {"app", "pages"}:
        root = parts[1]
        rest = parts[2:]
    elif parts[0] in {"app", "pages"}:
        root = parts[0]
        rest = parts[1:]
    else:
        return None
    if not rest:
        return None
    stem = _stem(rest[-1])
    if stem is None:
        return None
    dirs = list(rest[:-1])
    if any(part.startswith("_") for part in dirs) or stem.startswith("_"):
        return None
    if root == "app":
        if stem in _PAGE_STEMS:
            kind = "navigation"
        elif stem in _ROUTE_STEMS:
            kind = "http"
        else:
            return None
        raw_segments = dirs
    else:
        if dirs and dirs[0] == "api":
            kind = "http"
        else:
            kind = "navigation"
        raw_segments = dirs if stem == "index" else [*dirs, stem]
    tokens: list[str] = []
    for part in raw_segments:
        token = _segment_token(part)
        if token is None:
            return _RouteFile(kind, "", True)
        if token == "":
            if part.startswith("_"):
                return None
            continue
        tokens.append(token)
    route_path = "/" if not tokens else "/" + "/".join(tokens)
    return _RouteFile(kind, route_path, False)


def _line(node: Node) -> int:
    return node.start_point[0] + 1


def _unwrap(node: Node | None) -> Node | None:
    current = node
    while current is not None and current.type in {
        "parenthesized_expression",
        "jsx_expression",
    }:
        named = named_children(current)
        if len(named) != 1:
            return current
        current = named[0]
    return current


def _binary_operator(node: Node) -> str | None:
    for child in node.children:
        if not child.is_named and child.type in {"==", "===", "!=", "!=="}:
            return child.type
    return None


def _is_const(node: Node) -> bool:
    return any(child.type == "const" for child in node.children)


def _has_default(node: Node) -> bool:
    return any(child.type == "default" for child in node.children)


def _jsx_tag(source: bytes, node: Node) -> str | None:
    names = [
        text_of(source, child)
        for child in named_children(node)
        if child.type == "identifier"
    ]
    if len(names) == 1:
        return names[0]
    return None


def _jsx_attr(source: bytes, node: Node, name: str) -> Node | None:
    for child in named_children(node):
        if child.type != "jsx_attribute":
            continue
        key = next(
            (
                part
                for part in named_children(child)
                if part.type == "property_identifier"
            ),
            None,
        )
        if identifier_name(source, key) != name:
            continue
        return next(
            (
                part
                for part in named_children(child)
                if part.type != "property_identifier"
            ),
            None,
        )
    return None


def _call_args(node: Node) -> list[Node]:
    arguments = child_named(node, "arguments")
    if arguments is None:
        return []
    return list(named_children(arguments))


def _member(source: bytes, node: Node | None) -> tuple[Node, str] | None:
    if node is None or node.type != "member_expression":
        return None
    obj = child_named(node, "object")
    prop = identifier_name(source, child_named(node, "property"))
    if obj is None or not prop:
        return None
    return obj, prop


def _enclosing_function(module: TsModule, node: Node):
    best = None
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


def _direct_local_names(module: TsModule, definition) -> set[str]:
    names: set[str] = set()
    params = child_named(definition.node, "parameters") or child_named(
        definition.node, "formal_parameters"
    )
    if params is not None:
        for child in walk_named(params):
            if child.type == "identifier" and child.parent is not None:
                if child.parent.type in {
                    "required_parameter",
                    "optional_parameter",
                    "rest_parameter",
                }:
                    names.add(text_of(module.source, child))
    for node in walk_named(definition.node):
        if node.type == "variable_declarator":
            owner = _enclosing_function(module, node)
            if owner is not definition:
                continue
            bound = identifier_name(module.source, child_named(node, "name"))
            if bound:
                names.add(bound)
        elif node.type in {"function_declaration", "generator_function_declaration"}:
            if node == definition.node:
                continue
            owner = _enclosing_function(module, node)
            if owner is not definition:
                continue
            bound = identifier_name(module.source, child_named(node, "name"))
            if bound:
                names.add(bound)
    return names


def _import_bindings(module: TsModule) -> dict[str, list[_ImportBinding]]:
    found: dict[str, list[_ImportBinding]] = {}
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
        clause = next(
            (child for child in named_children(node) if child.type == "import_clause"),
            None,
        )
        if clause is None:
            continue
        for child in named_children(clause):
            if child.type == "identifier" and specifier in _LINK_SPECIFIERS:
                local = text_of(module.source, child)
                found.setdefault(local, []).append(
                    _ImportBinding("link", "default", specifier)
                )
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
                    imported, local = names[0], names[-1]
                    role = None
                    if specifier in _LINK_SPECIFIERS and imported == "Link":
                        role = "link"
                    elif specifier in _ROUTER_SPECIFIERS and imported == "useRouter":
                        role = "useRouter"
                    elif specifier in _REDIRECT_SPECIFIERS and imported == "redirect":
                        role = "redirect"
                    if role is None:
                        continue
                    found.setdefault(local, []).append(
                        _ImportBinding(role, imported, specifier)
                    )
    return found


def _role(bindings: dict[str, list[_ImportBinding]], name: str) -> str | None:
    items = bindings.get(name) or []
    roles = {item.role for item in items}
    if len(roles) != 1 or len(items) != 1:
        return None
    return next(iter(roles))


def _local_functions(module: TsModule) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for item in module.definitions:
        if item.owner != module.name:
            continue
        if item.kind not in {"typescript_function", "typescript_async_function"}:
            continue
        found.setdefault(item.name, []).append(item.qualified_name)
    return found


def _resolve_callable_name(
    module: TsModule,
    name: str,
    modules: dict[str, TsModule],
    stack: set[tuple[str, str]],
) -> str | None:
    key = (module.path, name)
    if key in stack:
        return None
    stack.add(key)
    local = _local_functions(module).get(name) or []
    imported = _imported_callables(module, name, modules, stack)
    unique = set(local) | set(imported)
    if len(unique) != 1:
        return None
    return next(iter(unique))


def _imported_callables(
    module: TsModule,
    local_name: str,
    modules: dict[str, TsModule],
    stack: set[tuple[str, str]],
) -> list[str]:
    found: list[str] = []
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
        target_path = resolve_specifier(
            module.path, specifier, set(modules), module.aliases
        )
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
                resolved = _default_callable(target, modules, stack)
                if resolved:
                    found.append(resolved)
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
                    imported, local = names[0], names[-1]
                    if local != local_name:
                        continue
                    resolved = _exported_callable(target, imported, modules, stack)
                    if resolved:
                        found.append(resolved)
    return found


def _default_callable(
    module: TsModule,
    modules: dict[str, TsModule],
    stack: set[tuple[str, str]] | None = None,
) -> str | None:
    stack = set() if stack is None else stack
    found: list[str] = []
    for node in named_children(module.tree.root_node):
        if node.type != "export_statement" or not _has_default(node):
            continue
        for child in named_children(node):
            if child.type in {
                "function_declaration",
                "generator_function_declaration",
            }:
                name = identifier_name(module.source, child_named(child, "name"))
                if not name:
                    return None
                resolved = _resolve_callable_name(module, name, modules, stack)
                if resolved:
                    found.append(resolved)
            elif child.type == "identifier":
                resolved = _resolve_callable_name(
                    module, text_of(module.source, child), modules, stack
                )
                if resolved:
                    found.append(resolved)
                else:
                    return None
            elif child.type in {"arrow_function", "function_expression"}:
                return None
    if len(set(found)) != 1:
        return None
    return found[0]


def _exported_callable(
    module: TsModule,
    name: str,
    modules: dict[str, TsModule],
    stack: set[tuple[str, str]] | None = None,
) -> str | None:
    stack = set() if stack is None else stack
    key = (module.path, f"export:{name}")
    if key in stack:
        return None
    stack.add(key)
    candidates: list[str] = []
    for node in named_children(module.tree.root_node):
        if node.type != "export_statement" or _has_default(node):
            continue
        declaration = None
        for child in named_children(node):
            if child.type in {
                "function_declaration",
                "generator_function_declaration",
                "lexical_declaration",
            }:
                declaration = child
        if declaration is not None and declaration.type in {
            "function_declaration",
            "generator_function_declaration",
        }:
            fn_name = identifier_name(module.source, child_named(declaration, "name"))
            if fn_name == name:
                resolved = _resolve_callable_name(module, name, modules, stack)
                if resolved:
                    candidates.append(resolved)
        elif declaration is not None and declaration.type == "lexical_declaration":
            for declarator in named_children(declaration):
                if declarator.type != "variable_declarator":
                    continue
                bound = identifier_name(module.source, child_named(declarator, "name"))
                if bound != name:
                    continue
                value = _unwrap(child_named(declarator, "value"))
                if value is None:
                    continue
                if value.type in {
                    "arrow_function",
                    "function_expression",
                    "generator_function",
                }:
                    resolved = _resolve_callable_name(module, name, modules, stack)
                    if resolved:
                        candidates.append(resolved)
                elif value.type == "identifier":
                    resolved = _resolve_callable_name(
                        module, text_of(module.source, value), modules, stack
                    )
                    if resolved:
                        candidates.append(resolved)
        clause = next(
            (child for child in named_children(node) if child.type == "export_clause"),
            None,
        )
        source_node = next(
            (child for child in named_children(node) if child.type == "string"),
            None,
        )
        if clause is None:
            continue
        specifier = string_literal(module.source, source_node)
        target = module
        if specifier is not None:
            target_path = resolve_specifier(
                module.path, specifier, set(modules), module.aliases
            )
            if target_path is None or target_path not in modules:
                continue
            target = modules[target_path]
        for spec in named_children(clause):
            if spec.type != "export_specifier":
                continue
            names = [
                text_of(module.source, part)
                for part in named_children(spec)
                if part.type == "identifier"
            ]
            if not names:
                continue
            local, exported = names[0], names[-1]
            if exported != name:
                continue
            if specifier is None:
                resolved = _resolve_callable_name(module, local, modules, stack)
            else:
                resolved = _exported_callable(target, local, modules, stack)
                if resolved is None:
                    resolved = _resolve_callable_name(target, local, modules, stack)
            if resolved:
                candidates.append(resolved)
    if len(set(candidates)) != 1:
        return None
    return candidates[0]


def _http_export_lines(module: TsModule) -> dict[str, int]:
    lines: dict[str, int] = {}
    for node in named_children(module.tree.root_node):
        if node.type != "export_statement" or _has_default(node):
            continue
        for child in named_children(node):
            if child.type in {
                "function_declaration",
                "generator_function_declaration",
            }:
                name = identifier_name(module.source, child_named(child, "name"))
                if name in _HTTP_METHODS:
                    lines[name] = _line(node)
            elif child.type == "lexical_declaration":
                for declarator in named_children(child):
                    if declarator.type != "variable_declarator":
                        continue
                    name = identifier_name(
                        module.source, child_named(declarator, "name")
                    )
                    if name in _HTTP_METHODS:
                        lines[name] = _line(node)
            elif child.type == "export_clause":
                for spec in named_children(child):
                    if spec.type != "export_specifier":
                        continue
                    names = [
                        text_of(module.source, part)
                        for part in named_children(spec)
                        if part.type == "identifier"
                    ]
                    if names and names[-1] in _HTTP_METHODS:
                        lines[names[-1]] = _line(node)
    return lines


def _literal_methods(module: TsModule, fn_node: Node) -> set[str] | None:
    found: set[str] = set()
    saw = False
    for node in walk_named(fn_node):
        member = _member(module.source, node)
        if member is None or member[1] != "method":
            continue
        saw = True
        parent = node.parent
        if parent is None or parent.type != "binary_expression":
            return None
        if _binary_operator(parent) not in {"==", "==="}:
            return None
        sides = [
            _unwrap(child)
            for child in named_children(parent)
            if child.start_byte != node.start_byte or child.end_byte != node.end_byte
        ]
        if len(sides) != 1 or sides[0] is None:
            return None
        literal = string_literal(module.source, sides[0])
        if literal is None or literal.upper() not in _HTTP_METHODS:
            return None
        found.add(literal.upper())
    if not saw or not found:
        return None
    return found


def _const_value_nodes(module: TsModule) -> dict[str, list[Node]]:
    found: dict[str, list[Node]] = {}
    for node in named_children(module.tree.root_node):
        statement = node
        if node.type == "export_statement":
            statement = next(
                (
                    child
                    for child in named_children(node)
                    if child.type == "lexical_declaration"
                ),
                None,
            )
            if statement is None:
                continue
        if statement.type != "lexical_declaration" or not _is_const(statement):
            continue
        for declarator in named_children(statement):
            if declarator.type != "variable_declarator":
                continue
            name = identifier_name(module.source, child_named(declarator, "name"))
            value = child_named(declarator, "value")
            if name and value is not None:
                found.setdefault(name, []).append(value)
    return found


def _exported_const_names(module: TsModule) -> set[str]:
    names: set[str] = set()
    for node in named_children(module.tree.root_node):
        if node.type != "export_statement" or _has_default(node):
            continue
        for child in named_children(node):
            if child.type == "lexical_declaration":
                for declarator in named_children(child):
                    if declarator.type != "variable_declarator":
                        continue
                    bound = identifier_name(
                        module.source, child_named(declarator, "name")
                    )
                    if bound:
                        names.add(bound)
            elif child.type == "export_clause":
                for spec in named_children(child):
                    if spec.type != "export_specifier":
                        continue
                    idents = [
                        text_of(module.source, part)
                        for part in named_children(spec)
                        if part.type == "identifier"
                    ]
                    if idents:
                        names.add(idents[-1])
    return names


def _eval_string(
    module: TsModule,
    node: Node | None,
    modules: dict[str, TsModule],
    stack: set[tuple[str, str]],
) -> str | None:
    current = _unwrap(node)
    if current is None:
        return None
    literal = string_literal(module.source, current)
    if literal is not None:
        return literal
    if current.type != "identifier":
        return None
    return _const_string(module, text_of(module.source, current), modules, stack)


def _const_string(
    module: TsModule,
    name: str,
    modules: dict[str, TsModule],
    stack: set[tuple[str, str]] | None = None,
) -> str | None:
    stack = set() if stack is None else stack
    key = (module.path, f"const:{name}")
    if key in stack:
        return None
    stack.add(key)
    values = [
        _eval_string(module, item, modules, stack)
        for item in _const_value_nodes(module).get(name, [])
    ]
    imported = _imported_const_strings(module, name, modules, stack)
    resolved = [item for item in values if item is not None]
    # A name that also has an unresolvable local initializer is not unique.
    if len(_const_value_nodes(module).get(name, [])) != len(resolved):
        return None
    unique = set(resolved) | set(imported)
    if len(unique) != 1:
        return None
    return next(iter(unique))


def _imported_const_strings(
    module: TsModule,
    local_name: str,
    modules: dict[str, TsModule],
    stack: set[tuple[str, str]],
) -> list[str]:
    found: list[str] = []
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
        target_path = resolve_specifier(
            module.path, specifier, set(modules), module.aliases
        )
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
                if local != local_name:
                    continue
                if imported not in _exported_const_names(target):
                    continue
                value = _const_string(target, imported, modules, stack)
                if value is not None:
                    found.append(value)
    return found


def _static_path(
    module: TsModule,
    node: Node | None,
    modules: dict[str, TsModule],
    shadowed: set[str],
) -> tuple[str | None, str | None]:
    """Return ``(path, diagnostic_code)`` when the path resolves once."""
    current = _unwrap(node)
    if current is None:
        return None, "next_navigation_unresolved"
    if current.type == "identifier" and text_of(module.source, current) in shadowed:
        return None, "next_binding_shadowed"
    literal = string_literal(module.source, current)
    if literal is None and current.type == "identifier":
        name = text_of(module.source, current)
        local_nodes = _const_value_nodes(module).get(name, [])
        imported = _imported_const_strings(module, name, modules, set())
        if len(local_nodes) + len(imported) > 1:
            return None, "next_binding_shadowed"
        literal = _const_string(module, name, modules, set())
    if (
        literal is None
        or not literal.startswith("/")
        or "?" in literal
        or "#" in literal
    ):
        return None, "next_navigation_unresolved"
    if any(ch.isspace() for ch in literal) or "${" in literal:
        return None, "next_navigation_unresolved"
    return literal, None


def _callable_by_qn(entities: dict[str, Entity], qualified: str) -> Entity | None:
    matches = [
        item
        for item in entities.values()
        if item.type == EntityType.CALLABLE and item.qualified_name == qualified
    ]
    if len(matches) != 1:
        return None
    return matches[0]


def _router_aliases(module: TsModule, definition, bindings) -> dict[str, int]:
    counts: dict[str, int] = {}
    for node in walk_named(definition.node):
        if node.type != "lexical_declaration" or not _is_const(node):
            continue
        if _enclosing_function(module, node) is not definition:
            continue
        for declarator in named_children(node):
            if declarator.type != "variable_declarator":
                continue
            name = identifier_name(module.source, child_named(declarator, "name"))
            value = _unwrap(child_named(declarator, "value"))
            if not name or value is None or value.type != "call_expression":
                continue
            callee = child_named(value, "function")
            callee_name = identifier_name(module.source, callee)
            if (
                callee_name
                and _role(bindings, callee_name) == "useRouter"
                and callee_name not in _direct_local_names(module, definition)
            ):
                counts[name] = counts.get(name, 0) + 1
    return counts


class _Facts:
    def __init__(self, context: AdapterContext, base: FactBatch) -> None:
        self.context = context
        self.entities = {item.id: item for item in base.entities}
        self.edges = {item.id: item for item in base.edges}
        self.evidence = {item.id: item for item in base.evidence}
        self.diagnostics = list(base.diagnostics)
        self.issues: list[AdapterDiagnostic] = []

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

    def finish(self) -> tuple[FactBatch, tuple[AdapterDiagnostic, ...]]:
        issues = tuple(
            sorted(
                {
                    (item.code, item.relative_path, item.line): item
                    for item in self.issues
                }.values(),
                key=lambda item: (item.relative_path or "", item.line or 0, item.code),
            )
        )
        for ordinal, item in enumerate(issues):
            self.diagnostics.append(
                Diagnostic(
                    diagnostic_id(
                        self.context.job_id,
                        item.code,
                        item.relative_path,
                        item.line,
                        ordinal,
                    ),
                    self.context.job_id,
                    Severity.WARNING,
                    item.code,
                    _MESSAGES[item.code],
                    self.context.snapshot_id,
                    item.relative_path,
                    item.line,
                )
            )
        return (
            FactBatch(
                self.context.repository_id,
                self.context.snapshot_id,
                tuple(self.entities[key] for key in sorted(self.entities)),
                tuple(self.edges[key] for key in sorted(self.edges)),
                tuple(self.evidence[key] for key in sorted(self.evidence)),
                tuple(self.diagnostics),
            ),
            issues,
        )


class NextDetector:
    """Surface Next.js file conventions so deep selection can run."""

    def detect(
        self, manifest: SourceManifest, parsed: ParseResult
    ) -> FrameworkObservation:
        report = NextFrameworkAdapter().detect(manifest, parsed)
        return FrameworkObservation(report)


class NextFrameworkAdapter:
    """Extract static Next.js pages and route handlers. Not reviewed deep support."""

    entrypoint_required = False
    allow_unverified_versions = True
    reviewed_deep_support = False
    descriptor = AdapterDescriptor(
        adapter_id="rkg.next",
        adapter_version="0.1.0",
        contract_version=CONTRACT_VERSION,
        kind=AdapterKind.FRAMEWORK,
        language="typescript",
        framework="next",
        grammar_or_target="tree-sitter TypeScript/TSX + Next.js file routes",
        file_patterns=("*.ts", "*.tsx", "**/*.ts", "**/*.tsx"),
        ignore_patterns=("**/node_modules/**", "**/*.d.ts"),
        capabilities=("app", "routes"),
        technology_constraints=(TechnologyConstraint("next", ">=13.0,<16.0"),),
    )

    def technology_detectors(self) -> tuple[object, ...]:
        return (NextDetector(),)

    def detect(self, manifest: SourceManifest, parsed: ParseResult) -> DetectionReport:
        evidence: list[DetectionEvidence] = []
        for item in manifest.files:
            pure = _posix(item.relative_path)
            if pure.name == "package.json" and _package_declares_next(item.content):
                evidence.append(DetectionEvidence(item.relative_path, DETECT_RULE))
            elif file_route(item.relative_path) is not None:
                evidence.append(DetectionEvidence(item.relative_path, DETECT_RULE))
        for unit in parsed.units:
            if not isinstance(unit.representation, TsModule):
                continue
            module: TsModule = unit.representation
            if file_route(module.path) is not None:
                evidence.append(DetectionEvidence(module.path, DETECT_RULE))
            for node in named_children(module.tree.root_node):
                if node.type != "import_statement":
                    continue
                source_node = next(
                    (
                        child
                        for child in named_children(node)
                        if child.type == "string"
                    ),
                    None,
                )
                specifier = string_literal(module.source, source_node) or ""
                if specifier == "next" or specifier.startswith("next/"):
                    evidence.append(DetectionEvidence(module.path, DETECT_RULE))
                    break
        if not evidence:
            return DetectionReport()
        unique = tuple(
            DetectionEvidence(path, rule)
            for path, rule in sorted(
                {(item.relative_path, item.rule_id) for item in evidence}
            )
        )
        return DetectionReport((TechnologyDetection("next", None, unique),))

    def extract(
        self, context: AdapterContext, parsed: ParseResult, base: FactBatch
    ) -> AdapterResult:
        if (
            base.repository_id != context.repository_id
            or base.snapshot_id != context.snapshot_id
        ):
            raise ValueError("candidate ownership does not match adapter context")
        facts = _Facts(context, base)
        modules = {
            unit.relative_path: unit.representation
            for unit in parsed.units
            if isinstance(unit.representation, TsModule)
        }
        _extract(context, modules, facts)
        result, issues = facts.finish()
        return AdapterResult(result, self._capabilities(), issues)

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
            for name in NextFrameworkAdapter.descriptor.capabilities
        )


def _package_declares_next(content: bytes) -> bool:
    try:
        data = json.loads(content.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError, ValueError):
        return False
    if not isinstance(data, dict):
        return False
    for section in ("dependencies", "devDependencies", "peerDependencies"):
        block = data.get(section) or {}
        if isinstance(block, dict) and "next" in block:
            return True
    return False


def _emit_endpoint(
    context: AdapterContext,
    facts: _Facts,
    *,
    file_path: str,
    line: int,
    kind: str,
    method: str,
    route_path: str,
    handler: Entity | None,
) -> str:
    qualified = (
        f"navigation:{route_path}" if kind == "navigation" else f"{method} {route_path}"
    )
    chain = (f"next:{file_path}:{line}:{kind}:{method}:{route_path}",)
    identifier = endpoint_id(
        context.repository_id,
        file_path,
        qualified,
        method,
        route_path,
        chain,
    )
    attributes: list[tuple[str, object]] = [
        ("path", route_path),
        ("route_path", route_path),
        ("registration_chain", chain),
    ]
    if kind == "navigation":
        attributes.insert(0, ("kind", "navigation"))
    else:
        attributes.insert(0, ("method", method))
    facts.entities[identifier] = Entity(
        identifier,
        context.repository_id,
        context.snapshot_id,
        EntityType.ENDPOINT,
        route_path,
        qualified,
        file_path,
        line,
        line,
        framework_kind="next",
        attributes=tuple(attributes),
    )
    if handler is not None:
        facts.edge(
            EdgeType.HANDLED_BY,
            identifier,
            handler.id,
            _Location(file_path, line),
            HANDLER_RULE,
        )
    else:
        facts.issue("next_handler_unresolved", file_path, line)
    return identifier


def _extract(
    context: AdapterContext, modules: dict[str, TsModule], facts: _Facts
) -> None:
    navigation: dict[str, list[str]] = {}
    for path in sorted(modules):
        module = modules[path]
        route = file_route(path)
        if route is None:
            continue
        if route.dynamic:
            facts.issue("next_route_dynamic", path, 1)
            continue
        if route.kind == "navigation":
            handler_qn = _default_callable(module, modules)
            handler = (
                _callable_by_qn(facts.entities, handler_qn) if handler_qn else None
            )
            endpoint = _emit_endpoint(
                context,
                facts,
                file_path=path,
                line=1,
                kind="navigation",
                method="",
                route_path=route.route_path,
                handler=handler,
            )
            navigation.setdefault(route.route_path, []).append(endpoint)
            continue
        methods = _http_methods(module, modules)
        if not methods:
            facts.issue(
                "next_route_dynamic" if methods is None else "next_handler_unresolved",
                path,
                1,
            )
            continue
        for method, handler_qn, line in methods:
            handler = (
                _callable_by_qn(facts.entities, handler_qn) if handler_qn else None
            )
            _emit_endpoint(
                context,
                facts,
                file_path=path,
                line=line,
                kind="http",
                method=method,
                route_path=route.route_path,
                handler=handler,
            )
    for module in modules.values():
        _navigation_calls(module, modules, facts, navigation)
    for endpoint_ids in navigation.values():
        for endpoint_id_ in endpoint_ids:
            entity = facts.entities[endpoint_id_]
            handler = _single_handler(facts, endpoint_id_)
            if handler is None:
                continue
            attrs = list(entity.attributes) + list(
                route_flow_attrs(handler, facts.entities, facts.edges)
            )
            facts.entities[endpoint_id_] = Entity(
                entity.id,
                entity.repository_id,
                entity.snapshot_id,
                entity.type,
                entity.name,
                entity.qualified_name,
                entity.file_path,
                entity.start_line,
                entity.end_line,
                entity.language_kind,
                entity.framework_kind,
                tuple(attrs),
            )


def _single_handler(facts: _Facts, endpoint: str) -> Entity | None:
    targets = []
    for edge in facts.edges.values():
        if edge.type != EdgeType.HANDLED_BY or edge.source_id != endpoint:
            continue
        target = facts.entities.get(edge.target_id)
        if target is not None and target.type == EntityType.CALLABLE:
            targets.append(target)
    if len(targets) != 1:
        return None
    return targets[0]


def _is_pages_file(path: str) -> bool:
    parts = list(_posix(path).parts)
    if parts and parts[0] == "src":
        parts = parts[1:]
    return bool(parts) and parts[0] == "pages"


def _http_methods(
    module: TsModule, modules: dict[str, TsModule]
) -> list[tuple[str, str | None, int]] | None:
    """Return ``(method, callable_qn, line)``.

    ``None`` means the Pages API verb is dynamic. An empty list means an App
    Router route file exported no HTTP verbs.
    """
    exported = _http_export_lines(module)
    if exported:
        return [
            (method, _exported_callable(module, method, modules), exported[method])
            for method in sorted(exported)
        ]
    if not _is_pages_file(module.path):
        return []
    handler_qn = _default_callable(module, modules)
    if not handler_qn:
        return None
    handler_node = None
    owner = module
    for candidate in modules.values():
        for item in candidate.definitions:
            if item.qualified_name == handler_qn:
                owner = candidate
                handler_node = item.node
    if handler_node is None:
        return None
    methods = _literal_methods(owner, handler_node)
    if methods is None:
        return None
    return [(method, handler_qn, _line(handler_node)) for method in sorted(methods)]


def _navigation_calls(
    module: TsModule,
    modules: dict[str, TsModule],
    facts: _Facts,
    navigation: dict[str, list[str]],
) -> None:
    bindings = _import_bindings(module)
    if not bindings:
        return
    for node in walk_named(module.tree.root_node):
        if node.type in {"jsx_self_closing_element", "jsx_opening_element"}:
            tag = _jsx_tag(module.source, node)
            if tag is None or _role(bindings, tag) != "link":
                if tag and tag in bindings and _role(bindings, tag) is None:
                    facts.issue("next_binding_shadowed", module.path, _line(node))
                continue
            _link_call(module, modules, facts, navigation, bindings, node, tag)
        elif node.type == "call_expression":
            _call_navigation(module, modules, facts, navigation, bindings, node)


def _link_call(
    module: TsModule,
    modules: dict[str, TsModule],
    facts: _Facts,
    navigation: dict[str, list[str]],
    bindings: dict[str, list[_ImportBinding]],
    node: Node,
    tag: str,
) -> None:
    del bindings
    definition = _enclosing_function(module, node)
    if definition is None:
        facts.issue("next_navigation_unresolved", module.path, _line(node))
        return
    shadowed = _direct_local_names(module, definition)
    if tag in shadowed:
        facts.issue("next_binding_shadowed", module.path, _line(node))
        return
    href = _jsx_attr(module.source, node, "href")
    path, code = _static_path(module, href, modules, shadowed)
    if code or path is None:
        facts.issue(code or "next_navigation_unresolved", module.path, _line(node))
        return
    _emit_navigation_call(
        module, facts, navigation, definition, path, _line(node)
    )


def _call_navigation(
    module: TsModule,
    modules: dict[str, TsModule],
    facts: _Facts,
    navigation: dict[str, list[str]],
    bindings: dict[str, list[_ImportBinding]],
    node: Node,
) -> None:
    callee = child_named(node, "function")
    definition = _enclosing_function(module, node)
    line = _line(node)
    name = identifier_name(module.source, callee)
    if name and _role(bindings, name) == "redirect":
        if definition is None:
            facts.issue("next_navigation_unresolved", module.path, line)
            return
        shadowed = _direct_local_names(module, definition)
        if name in shadowed:
            facts.issue("next_binding_shadowed", module.path, line)
            return
        args = _call_args(node)
        path, code = _static_path(
            module, args[0] if args else None, modules, shadowed
        )
        if code or path is None:
            facts.issue(code or "next_navigation_unresolved", module.path, line)
            return
        _emit_navigation_call(module, facts, navigation, definition, path, line)
        return
    member = _member(module.source, callee)
    if member is None or member[1] != "push":
        return
    obj, _prop = member
    if definition is None:
        facts.issue("next_navigation_unresolved", module.path, line)
        return
    shadowed = _direct_local_names(module, definition)
    recognized = False
    if obj.type == "call_expression":
        callee_name = identifier_name(module.source, child_named(obj, "function"))
        if callee_name and _role(bindings, callee_name) == "useRouter":
            recognized = True
            if callee_name in shadowed:
                facts.issue("next_binding_shadowed", module.path, line)
                return
    elif obj.type == "identifier":
        alias = text_of(module.source, obj)
        counts = _router_aliases(module, definition, bindings)
        if alias in counts:
            recognized = True
            if counts[alias] != 1:
                facts.issue("next_binding_shadowed", module.path, line)
                return
    if not recognized:
        return
    args = _call_args(node)
    path, code = _static_path(module, args[0] if args else None, modules, shadowed)
    if code or path is None:
        facts.issue(code or "next_navigation_unresolved", module.path, line)
        return
    _emit_navigation_call(module, facts, navigation, definition, path, line)


def _emit_navigation_call(
    module: TsModule,
    facts: _Facts,
    navigation: dict[str, list[str]],
    definition,
    route_path: str,
    line: int,
) -> None:
    caller = _callable_by_qn(facts.entities, definition.qualified_name)
    if caller is None:
        facts.issue("next_navigation_unresolved", module.path, line)
        return
    endpoints = navigation.get(route_path) or []
    if len(endpoints) != 1:
        facts.issue(
            "next_navigation_ambiguous"
            if len(endpoints) > 1
            else "next_navigation_unresolved",
            module.path,
            line,
        )
        return
    handler = _single_handler(facts, endpoints[0])
    if handler is None:
        facts.issue("next_navigation_unresolved", module.path, line)
        return
    facts.edge(
        EdgeType.CALLS,
        caller.id,
        handler.id,
        _Location(module.path, line),
        NAV_RULE,
    )
