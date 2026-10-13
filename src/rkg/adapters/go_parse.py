"""Tree-sitter Go parse helpers for the language adapter.

The structured tree-sitter CST is the intermediate representation. Analyzed
modules are never imported or executed.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import PurePosixPath

import tree_sitter_go as ts_go
from tree_sitter import Language, Node, Parser, Tree

from rkg.adapters.contracts import AdapterDiagnostic, SymbolRef

GO_LANGUAGE = Language(ts_go.language())
_PARSER = Parser(GO_LANGUAGE)

REPRESENTATION_KIND = "tree-sitter-go/0.25"
_IGNORE_PARTS = frozenset({".git", "vendor", "testdata"})


@dataclass(frozen=True, slots=True)
class GoImport:
    path: str
    alias: str | None
    line: int


@dataclass(frozen=True, slots=True)
class GoField:
    name: str
    type_name: str
    line: int
    embedded: bool = False


@dataclass(frozen=True, slots=True)
class GoCallable:
    name: str
    qualified_name: str
    kind: str
    receiver_type: str | None
    parameters: tuple[tuple[str, str], ...]
    start_line: int
    end_line: int
    node: Node


@dataclass(frozen=True, slots=True)
class GoType:
    name: str
    qualified_name: str
    kind: str
    package_name: str
    fields: tuple[GoField, ...]
    methods: tuple[str, ...]
    start_line: int
    end_line: int
    node: Node


@dataclass(slots=True)
class GoModule:
    path: str
    package_name: str
    source: bytes
    tree: Tree
    imports: tuple[GoImport, ...] = ()
    types: tuple[GoType, ...] = ()
    callables: tuple[GoCallable, ...] = ()
    constants: dict[str, str] = field(default_factory=dict)
    diagnostics: tuple[AdapterDiagnostic, ...] = ()


def is_go_file(path: str) -> bool:
    posix = PurePosixPath(path)
    if any(part in _IGNORE_PARTS for part in posix.parts):
        return False
    if path.endswith("_test.go"):
        return False
    return path.endswith(".go")


def text_of(source: bytes, node: Node | None) -> str:
    if node is None:
        return ""
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def child_named(node: Node, field: str) -> Node | None:
    return node.child_by_field_name(field)


def named_children(node: Node) -> tuple[Node, ...]:
    return tuple(child for child in node.children if child.is_named)


def walk_named(node: Node) -> Iterator[Node]:
    yield node
    for child in node.children:
        if child.is_named:
            yield from walk_named(child)


def first_error_line(root: Node) -> int | None:
    for node in walk_named(root):
        if node.type == "ERROR" or node.is_missing:
            return node.start_point[0] + 1
    return root.start_point[0] + 1 if root.has_error else None


def string_literal(source: bytes, node: Node | None) -> str | None:
    if node is None:
        return None
    if node.type == "interpreted_string_literal":
        raw = text_of(source, node)
        if len(raw) >= 2 and raw[0] == '"' and raw[-1] == '"':
            return raw[1:-1]
        return None
    if node.type == "raw_string_literal":
        raw = text_of(source, node)
        if len(raw) >= 2 and raw[0] == "`" and raw[-1] == "`":
            return raw[1:-1]
        return None
    return None


def type_name_of(source: bytes, node: Node | None) -> str:
    if node is None:
        return ""
    if node.type == "pointer_type":
        return type_name_of(source, next(iter(named_children(node)), None))
    if node.type in {"type_identifier", "identifier", "field_identifier"}:
        return text_of(source, node)
    if node.type == "qualified_type":
        pkg = child_named(node, "package") or next(
            (c for c in named_children(node) if c.type == "package_identifier"), None
        )
        name = child_named(node, "name") or next(
            (c for c in named_children(node) if c.type == "type_identifier"), None
        )
        left = text_of(source, pkg)
        right = text_of(source, name)
        return f"{left}.{right}" if left and right else right or left
    if node.type in {"slice_type", "array_type", "map_type", "channel_type"}:
        return text_of(source, node)
    return text_of(source, node)


def package_qualified(package_name: str, *parts: str) -> str:
    symbol = ".".join(part for part in parts if part)
    if package_name == "main":
        return symbol
    return f"{package_name}.{symbol}" if package_name else symbol


def symbol_refs(module: GoModule) -> list[SymbolRef]:
    refs: list[SymbolRef] = []
    for item in module.types:
        refs.append(SymbolRef(item.qualified_name, module.path, module.package_name))
    for item in module.callables:
        owner = None
        if item.receiver_type:
            owner = package_qualified(module.package_name, item.receiver_type)
        refs.append(SymbolRef(item.qualified_name, module.path, owner))
    return refs


def _parse_imports(source: bytes, root: Node) -> tuple[GoImport, ...]:
    found: list[GoImport] = []
    for node in named_children(root):
        if node.type != "import_declaration":
            continue
        for spec in walk_named(node):
            if spec.type != "import_spec":
                continue
            path_node = child_named(spec, "path") or next(
                (
                    c
                    for c in named_children(spec)
                    if c.type in {"interpreted_string_literal", "raw_string_literal"}
                ),
                None,
            )
            path = string_literal(source, path_node)
            if not path:
                continue
            alias_node = child_named(spec, "name")
            alias = text_of(source, alias_node) if alias_node is not None else None
            if alias in {"", "."}:
                alias = None
            found.append(GoImport(path, alias, spec.start_point[0] + 1))
    return tuple(found)


def _parse_constants(source: bytes, root: Node) -> dict[str, str]:
    constants: dict[str, str] = {}
    for node in named_children(root):
        if node.type != "const_declaration":
            continue
        for spec in walk_named(node):
            if spec.type != "const_spec":
                continue
            name_node = next(
                (c for c in named_children(spec) if c.type == "identifier"), None
            )
            if name_node is None:
                continue
            values = child_named(spec, "value") or next(
                (c for c in named_children(spec) if c.type == "expression_list"), None
            )
            if values is None:
                continue
            first = next(iter(named_children(values)), values)
            literal = string_literal(source, first)
            if literal is None:
                continue
            constants[text_of(source, name_node)] = literal
    return constants


def _parse_fields(source: bytes, struct_node: Node) -> tuple[GoField, ...]:
    fields: list[GoField] = []
    body = next(
        (c for c in named_children(struct_node) if c.type == "field_declaration_list"),
        None,
    )
    if body is None:
        return ()
    for decl in named_children(body):
        if decl.type != "field_declaration":
            continue
        names = [c for c in named_children(decl) if c.type == "field_identifier"]
        type_node = child_named(decl, "type") or next(
            (
                c
                for c in named_children(decl)
                if c.type
                not in {
                    "field_identifier",
                    "raw_string_literal",
                    "interpreted_string_literal",
                }
            ),
            None,
        )
        type_label = type_name_of(source, type_node)
        line = decl.start_point[0] + 1
        if not names:
            if type_label:
                fields.append(
                    GoField(type_label.split(".")[-1], type_label, line, True)
                )
            continue
        for name_node in names:
            fields.append(GoField(text_of(source, name_node), type_label, line, False))
    return tuple(fields)


def _interface_methods(source: bytes, iface_node: Node) -> tuple[str, ...]:
    methods: list[str] = []
    for child in walk_named(iface_node):
        if child.type != "method_elem":
            continue
        name_node = child_named(child, "name") or next(
            (c for c in named_children(child) if c.type == "field_identifier"), None
        )
        if name_node is not None:
            methods.append(text_of(source, name_node))
    return tuple(methods)


def _parameter_pairs(source: bytes, params: Node | None) -> tuple[tuple[str, str], ...]:
    if params is None:
        return ()
    pairs: list[tuple[str, str]] = []
    for child in named_children(params):
        if child.type not in {
            "parameter_declaration",
            "variadic_parameter_declaration",
        }:
            continue
        names = [c for c in named_children(child) if c.type == "identifier"]
        type_node = child_named(child, "type") or next(
            (c for c in named_children(child) if c.type != "identifier"),
            None,
        )
        type_label = type_name_of(source, type_node)
        if not names:
            pairs.append(("", type_label))
            continue
        for name_node in names:
            pairs.append((text_of(source, name_node), type_label))
    return tuple(pairs)


def _receiver_type(source: bytes, receiver: Node | None) -> str | None:
    if receiver is None:
        return None
    decl = next(
        (c for c in named_children(receiver) if c.type == "parameter_declaration"),
        None,
    )
    if decl is None:
        return None
    type_node = child_named(decl, "type") or next(
        (c for c in named_children(decl) if c.type != "identifier"), None
    )
    label = type_name_of(source, type_node)
    return label or None


def parse_unit(
    path: str, content: bytes
) -> tuple[GoModule | None, tuple[AdapterDiagnostic, ...]]:
    # tree-sitter-go treats a missing final newline as an ERROR on otherwise
    # valid files; normalize so editor/test fixtures without EOF newline parse.
    source = content if content.endswith(b"\n") else content + b"\n"
    tree = _PARSER.parse(source)
    root = tree.root_node
    if root.has_error:
        line = first_error_line(root) or 1
        return None, (AdapterDiagnostic("go_syntax_error", path, line),)
    package_node = next(
        (c for c in named_children(root) if c.type == "package_clause"), None
    )
    package_name = ""
    if package_node is not None:
        ident = next(
            (c for c in named_children(package_node) if c.type == "package_identifier"),
            None,
        )
        package_name = text_of(content, ident)
    imports = _parse_imports(content, root)
    constants = _parse_constants(content, root)
    types: list[GoType] = []
    callables: list[GoCallable] = []
    for node in named_children(root):
        if node.type == "type_declaration":
            for spec in walk_named(node):
                if spec.type != "type_spec":
                    continue
                name_node = child_named(spec, "name") or next(
                    (c for c in named_children(spec) if c.type == "type_identifier"),
                    None,
                )
                if name_node is None:
                    continue
                name = text_of(content, name_node)
                type_node = child_named(spec, "type") or next(
                    (c for c in named_children(spec) if c.type != "type_identifier"),
                    None,
                )
                kind = "alias"
                fields: tuple[GoField, ...] = ()
                methods: tuple[str, ...] = ()
                if type_node is not None:
                    if type_node.type == "struct_type":
                        kind = "struct"
                        fields = _parse_fields(content, type_node)
                    elif type_node.type == "interface_type":
                        kind = "interface"
                        methods = _interface_methods(content, type_node)
                    elif type_node.type == "type_identifier":
                        kind = "named"
                qn = package_qualified(package_name, name)
                types.append(
                    GoType(
                        name,
                        qn,
                        kind,
                        package_name,
                        fields,
                        methods,
                        spec.start_point[0] + 1,
                        spec.end_point[0] + 1,
                        spec,
                    )
                )
                if kind == "interface":
                    for method_name in methods:
                        callables.append(
                            GoCallable(
                                method_name,
                                package_qualified(package_name, name, method_name),
                                "interface_method",
                                name,
                                (),
                                spec.start_point[0] + 1,
                                spec.end_point[0] + 1,
                                spec,
                            )
                        )
        elif node.type == "function_declaration":
            name_node = child_named(node, "name") or next(
                (c for c in named_children(node) if c.type == "identifier"), None
            )
            if name_node is None:
                continue
            name = text_of(content, name_node)
            type_params = child_named(node, "type_parameters")
            if type_params is not None and "[" in name:
                name = name.split("[", 1)[0]
            # Generic helpers appear as identifier CloneSlice; type params are sibling.
            params = child_named(node, "parameters")
            qn = package_qualified(package_name, name)
            callables.append(
                GoCallable(
                    name,
                    qn,
                    "function",
                    None,
                    _parameter_pairs(content, params),
                    node.start_point[0] + 1,
                    node.end_point[0] + 1,
                    node,
                )
            )
        elif node.type == "method_declaration":
            name_node = child_named(node, "name") or next(
                (c for c in named_children(node) if c.type == "field_identifier"),
                None,
            )
            receiver = child_named(node, "receiver")
            if receiver is None:
                param_lists = [
                    c for c in named_children(node) if c.type == "parameter_list"
                ]
                receiver = param_lists[0] if param_lists else None
            if name_node is None:
                continue
            name = text_of(content, name_node)
            recv = _receiver_type(content, receiver)
            param_lists = [
                c for c in named_children(node) if c.type == "parameter_list"
            ]
            params = None
            if receiver is not None and len(param_lists) >= 2:
                params = param_lists[1]
            elif receiver is None and param_lists:
                params = param_lists[0]
            elif len(param_lists) >= 1:
                # receiver field may equal first parameter_list
                params = param_lists[-1] if len(param_lists) > 1 else None
            qn = package_qualified(package_name, recv or "", name)
            callables.append(
                GoCallable(
                    name,
                    qn,
                    "method",
                    recv,
                    _parameter_pairs(content, params),
                    node.start_point[0] + 1,
                    node.end_point[0] + 1,
                    node,
                )
            )
    module = GoModule(
        path,
        package_name,
        content,
        tree,
        imports,
        tuple(types),
        tuple(callables),
        constants,
    )
    return module, ()
