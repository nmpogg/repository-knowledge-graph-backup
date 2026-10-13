"""Tree-sitter Java parse helpers for the language adapter.

The structured tree-sitter CST is the intermediate representation. Analyzed
modules are never imported or executed.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import PurePosixPath

import tree_sitter_java as ts_java
from tree_sitter import Language, Node, Parser, Tree

from rkg.adapters.contracts import AdapterDiagnostic, SymbolRef

JAVA_LANGUAGE = Language(ts_java.language())
_PARSER = Parser(JAVA_LANGUAGE)

REPRESENTATION_KIND = "tree-sitter-java/0.23"
_IGNORE_PARTS = frozenset({"target", ".mvn", ".git"})
_ORDERS_ROOT = "com.example.rkgfixture.orders"
_FIXTURE_ROOT = "com.example.rkgfixture"


@dataclass(frozen=True, slots=True)
class JavaImport:
    qualified_name: str
    simple_name: str
    is_static: bool
    is_wildcard: bool
    line: int


@dataclass(frozen=True, slots=True)
class JavaAnnotation:
    name: str
    arguments: tuple[tuple[str | None, str], ...]
    line: int
    raw: str


@dataclass(frozen=True, slots=True)
class JavaCallable:
    name: str
    qualified_name: str
    kind: str
    parameters: tuple[tuple[str, str], ...]
    annotations: tuple[JavaAnnotation, ...]
    start_line: int
    end_line: int
    node: Node


@dataclass(frozen=True, slots=True)
class JavaType:
    name: str
    qualified_name: str
    kind: str
    package_name: str
    annotations: tuple[JavaAnnotation, ...]
    extends: tuple[str, ...]
    implements: tuple[str, ...]
    fields: tuple[tuple[str, str, str | None, int], ...]
    callables: tuple[JavaCallable, ...]
    nested: tuple[JavaType, ...]
    start_line: int
    end_line: int
    node: Node


@dataclass(slots=True)
class JavaModule:
    path: str
    package_name: str
    short_package: str
    source: bytes
    tree: Tree
    imports: tuple[JavaImport, ...] = ()
    types: tuple[JavaType, ...] = ()
    diagnostics: tuple[AdapterDiagnostic, ...] = ()
    constants: dict[str, str] = field(default_factory=dict)


def is_java_file(path: str) -> bool:
    posix = PurePosixPath(path)
    if any(part in _IGNORE_PARTS for part in posix.parts):
        return False
    return path.endswith(".java")


def is_yaml_file(path: str) -> bool:
    posix = PurePosixPath(path)
    if any(part in _IGNORE_PARTS for part in posix.parts):
        return False
    return path.endswith((".yml", ".yaml"))


def short_package_name(package_name: str) -> str:
    if not package_name:
        return ""
    if package_name == _ORDERS_ROOT:
        return ""
    prefix = _ORDERS_ROOT + "."
    if package_name.startswith(prefix):
        return package_name[len(prefix) :]
    fixture = _FIXTURE_ROOT + "."
    if package_name.startswith(fixture):
        return package_name[len(fixture) :]
    return package_name


def type_qualified_name(package_name: str, *parts: str) -> str:
    short = short_package_name(package_name)
    symbols = ".".join(parts)
    return f"{short}.{symbols}" if short else symbols


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


def _identifier_chain(source: bytes, node: Node | None) -> str:
    if node is None:
        return ""
    if node.type == "identifier":
        return text_of(source, node)
    if node.type in {"scoped_identifier", "field_access"}:
        parts = []
        for child in named_children(node):
            part = _identifier_chain(source, child)
            if part:
                parts.append(part)
        return ".".join(parts)
    if node.type == "type_identifier":
        return text_of(source, node)
    if node.type == "generic_type":
        base = child_named(node, "type") or next(
            (c for c in named_children(node) if c.type == "type_identifier"), None
        )
        return _identifier_chain(source, base)
    if node.type == "array_type":
        element = child_named(node, "element") or next(iter(named_children(node)), None)
        return f"{_identifier_chain(source, element)}[]"
    if node.type in {
        "integral_type",
        "floating_point_type",
        "boolean_type",
        "void_type",
    }:
        return text_of(source, node)
    if node.type == "scoped_type_identifier":
        return ".".join(
            _identifier_chain(source, child) for child in named_children(node)
        )
    return text_of(source, node)


def _type_label(source: bytes, node: Node | None) -> str:
    if node is None:
        return ""
    if node.type == "generic_type":
        base = _identifier_chain(source, child_named(node, "type") or node)
        args_node = None
        for child in named_children(node):
            if child.type == "type_arguments":
                args_node = child
                break
        if args_node is None:
            return base
        args = []
        for child in named_children(args_node):
            label = _type_label(source, child)
            if label:
                args.append(label)
        return f"{base}<{', '.join(args)}>" if args else base
    if node.type == "array_type":
        element = child_named(node, "element") or next(iter(named_children(node)), None)
        return f"{_type_label(source, element)}[]"
    return _identifier_chain(source, node)


def _string_literal(source: bytes, node: Node | None) -> str | None:
    if node is None:
        return None
    if node.type == "string_literal":
        for child in named_children(node):
            if child.type == "string_fragment":
                return text_of(source, child)
        raw = text_of(source, node)
        if len(raw) >= 2 and raw[0] == '"' and raw[-1] == '"':
            return raw[1:-1]
    return None


def _annotations(source: bytes, node: Node | None) -> tuple[JavaAnnotation, ...]:
    if node is None or node.type != "modifiers":
        return ()
    items: list[JavaAnnotation] = []
    for child in named_children(node):
        if child.type == "marker_annotation":
            name = _identifier_chain(source, child_named(child, "name") or child)
            items.append(
                JavaAnnotation(
                    name.split(".")[-1],
                    (),
                    child.start_point[0] + 1,
                    text_of(source, child),
                )
            )
        elif child.type == "annotation":
            name = _identifier_chain(source, child_named(child, "name") or child)
            args: list[tuple[str | None, str]] = []
            arguments = None
            for part in named_children(child):
                if part.type == "annotation_argument_list":
                    arguments = part
            if arguments is not None:
                for arg in named_children(arguments):
                    if arg.type == "element_value_pair":
                        key = None
                        value = ""
                        for piece in named_children(arg):
                            if piece.type == "identifier" and key is None:
                                key = text_of(source, piece)
                            else:
                                value = text_of(source, piece)
                        args.append((key, value))
                    else:
                        args.append((None, text_of(source, arg)))
            items.append(
                JavaAnnotation(
                    name.split(".")[-1],
                    tuple(args),
                    child.start_point[0] + 1,
                    text_of(source, child),
                )
            )
    return tuple(items)


def _has_modifier(source: bytes, modifiers: Node | None, name: str) -> bool:
    if modifiers is None:
        return False
    return any(
        child.type == "modifier" and text_of(source, child) == name
        for child in named_children(modifiers)
    )


def _formal_parameters(source: bytes, node: Node | None) -> tuple[tuple[str, str], ...]:
    if node is None:
        return ()
    params: list[tuple[str, str]] = []
    for child in named_children(node):
        if child.type not in {"formal_parameter", "spread_parameter"}:
            continue
        type_node = None
        name_node = None
        for part in named_children(child):
            if part.type in {
                "type_identifier",
                "generic_type",
                "array_type",
                "scoped_type_identifier",
                "integral_type",
                "floating_point_type",
                "boolean_type",
            }:
                type_node = part
            elif part.type == "identifier":
                name_node = part
            elif part.type == "modifiers":
                continue
        params.append(
            (
                _type_label(source, type_node),
                text_of(source, name_node) if name_node else "",
            )
        )
    return tuple(params)


def _callable_qn(
    owner: str, name: str, params: tuple[tuple[str, str], ...], overload_count: int
) -> str:
    labels = [item[0] for item in params]
    if overload_count > 1 or name == "main":
        return f"{owner}.{name}({', '.join(labels)})"
    return f"{owner}.{name}"


def _extract_fields(
    source: bytes, body: Node | None
) -> tuple[tuple[str, str, str | None, int], ...]:
    if body is None:
        return ()
    fields: list[tuple[str, str, str | None, int]] = []
    for child in named_children(body):
        if child.type != "field_declaration":
            continue
        modifiers = None
        type_node = None
        for part in named_children(child):
            if part.type == "modifiers":
                modifiers = part
            elif part.type in {
                "type_identifier",
                "generic_type",
                "array_type",
                "scoped_type_identifier",
                "integral_type",
                "floating_point_type",
                "boolean_type",
            }:
                type_node = part
        type_label = _type_label(source, type_node)
        for part in named_children(child):
            if part.type != "variable_declarator":
                continue
            name_node = child_named(part, "name")
            value_node = child_named(part, "value")
            name = text_of(source, name_node)
            value = _string_literal(source, value_node)
            if value is None and value_node is not None:
                # uniquely assigned field access / identifier constants resolved later
                raw = text_of(source, value_node)
                if raw and "\n" not in raw and len(raw) < 200:
                    value = f"@{raw}"
            fields.append((name, type_label, value, child.start_point[0] + 1))
            del modifiers  # silence unused when not needed
    return tuple(fields)


def _extract_type(
    source: bytes,
    node: Node,
    package_name: str,
    owner_parts: tuple[str, ...],
) -> JavaType:
    kind_map = {
        "class_declaration": "class",
        "interface_declaration": "interface",
        "enum_declaration": "enum",
        "record_declaration": "record",
        "annotation_type_declaration": "annotation",
    }
    kind = kind_map.get(node.type, "class")
    name_node = child_named(node, "name")
    name = text_of(source, name_node)
    parts = (*owner_parts, name)
    qualified = type_qualified_name(package_name, *parts)
    modifiers = None
    for child in named_children(node):
        if child.type == "modifiers":
            modifiers = child
            break
    annotations = _annotations(source, modifiers)
    extends: list[str] = []
    implements: list[str] = []
    for child in named_children(node):
        if child.type == "superclass":
            for part in named_children(child):
                label = _type_label(source, part)
                if label:
                    extends.append(label)
        elif child.type in {"super_interfaces", "extends_interfaces"}:
            for part in walk_named(child):
                if part.type in {
                    "type_identifier",
                    "scoped_type_identifier",
                    "generic_type",
                }:
                    label = _type_label(source, part)
                    if label and label not in implements and label not in extends:
                        if child.type == "extends_interfaces":
                            extends.append(label)
                        else:
                            implements.append(label)
        elif child.type == "interfaces":
            for part in walk_named(child):
                if part.type in {
                    "type_identifier",
                    "scoped_type_identifier",
                    "generic_type",
                }:
                    label = _type_label(source, part)
                    if label and label not in implements:
                        implements.append(label)
    body = None
    for child in named_children(node):
        if child.type in {
            "class_body",
            "interface_body",
            "enum_body",
            "annotation_type_body",
        }:
            body = child
            break
    fields = _extract_fields(source, body)
    nested: list[JavaType] = []
    callables_raw: list[tuple[str, JavaCallable]] = []
    if body is not None:
        for child in named_children(body):
            if child.type in {
                "class_declaration",
                "interface_declaration",
                "enum_declaration",
                "record_declaration",
            }:
                nested.append(_extract_type(source, child, package_name, parts))
            elif child.type == "method_declaration":
                method_mods = None
                for part in named_children(child):
                    if part.type == "modifiers":
                        method_mods = part
                method_name = text_of(source, child_named(child, "name"))
                params = _formal_parameters(source, child_named(child, "parameters"))
                callables_raw.append(
                    (
                        method_name,
                        JavaCallable(
                            method_name,
                            "",
                            "method",
                            params,
                            _annotations(source, method_mods),
                            child.start_point[0] + 1,
                            child.end_point[0] + 1,
                            child,
                        ),
                    )
                )
            elif child.type == "constructor_declaration":
                ctor_mods = None
                for part in named_children(child):
                    if part.type == "modifiers":
                        ctor_mods = part
                params = _formal_parameters(source, child_named(child, "parameters"))
                callables_raw.append(
                    (
                        name,
                        JavaCallable(
                            name,
                            "",
                            "constructor",
                            params,
                            _annotations(source, ctor_mods),
                            child.start_point[0] + 1,
                            child.end_point[0] + 1,
                            child,
                        ),
                    )
                )
            elif child.type == "compact_constructor_declaration":
                callables_raw.append(
                    (
                        name,
                        JavaCallable(
                            name,
                            "",
                            "constructor",
                            (),
                            (),
                            child.start_point[0] + 1,
                            child.end_point[0] + 1,
                            child,
                        ),
                    )
                )
    overload_counts: dict[str, int] = defaultdict(int)
    for method_name, _ in callables_raw:
        overload_counts[method_name] += 1
    callables: list[JavaCallable] = []
    for method_name, item in callables_raw:
        qn = _callable_qn(
            qualified, method_name, item.parameters, overload_counts[method_name]
        )
        callables.append(
            JavaCallable(
                item.name,
                qn,
                item.kind,
                item.parameters,
                item.annotations,
                item.start_line,
                item.end_line,
                item.node,
            )
        )
    return JavaType(
        name,
        qualified,
        kind,
        package_name,
        annotations,
        tuple(extends),
        tuple(implements),
        fields,
        tuple(callables),
        tuple(nested),
        node.start_point[0] + 1,
        node.end_point[0] + 1,
        node,
    )


def _imports(source: bytes, root: Node) -> tuple[JavaImport, ...]:
    items: list[JavaImport] = []
    for child in named_children(root):
        if child.type != "import_declaration":
            continue
        text = text_of(source, child)
        is_static = " static " in f" {text} "
        is_wildcard = text.rstrip(";").endswith(".*")
        name_node = None
        for part in named_children(child):
            if part.type in {"scoped_identifier", "identifier", "asterisk"}:
                name_node = part
        qualified = _identifier_chain(source, name_node).rstrip(".*")
        if is_wildcard and text.rstrip(";").endswith(".*"):
            qualified = (
                text.split("import", 1)[1]
                .strip()
                .rstrip(";")
                .removeprefix("static ")
                .strip()
            )
            if qualified.endswith(".*"):
                qualified = qualified[:-2]
        simple = qualified.split(".")[-1] if qualified else ""
        items.append(
            JavaImport(
                qualified,
                simple,
                is_static,
                is_wildcard,
                child.start_point[0] + 1,
            )
        )
    return tuple(items)


def parse_unit(
    path: str, content: bytes
) -> tuple[JavaModule | None, list[AdapterDiagnostic]]:
    diagnostics: list[AdapterDiagnostic] = []
    try:
        source = content if isinstance(content, bytes) else content.encode("utf-8")
        source.decode("utf-8")
    except (UnicodeError, AttributeError):
        diagnostics.append(AdapterDiagnostic("java_syntax_error", path, 1))
        return None, diagnostics
    tree = _PARSER.parse(source)
    if tree.root_node.has_error:
        line = first_error_line(tree.root_node) or 1
        diagnostics.append(AdapterDiagnostic("java_syntax_error", path, line))
        return None, diagnostics
    package_name = ""
    for child in named_children(tree.root_node):
        if child.type == "package_declaration":
            for part in named_children(child):
                if part.type in {"scoped_identifier", "identifier"}:
                    package_name = _identifier_chain(source, part)
            break
    imports = _imports(source, tree.root_node)
    types: list[JavaType] = []
    for child in named_children(tree.root_node):
        if child.type in {
            "class_declaration",
            "interface_declaration",
            "enum_declaration",
            "record_declaration",
        }:
            types.append(_extract_type(source, child, package_name, ()))
    constants: dict[str, str] = {}
    for item in types:
        for field_name, _type, value, _line in item.fields:
            if value and not value.startswith("@"):
                constants[f"{item.qualified_name}.{field_name}"] = value
                constants[f"{item.name}.{field_name}"] = value
                constants[field_name] = value
    module = JavaModule(
        path,
        package_name,
        short_package_name(package_name),
        source,
        tree,
        imports,
        tuple(types),
        tuple(diagnostics),
        constants,
    )
    return module, diagnostics


def symbol_refs(module: JavaModule) -> list[SymbolRef]:
    refs: list[SymbolRef] = []

    def visit(item: JavaType, owner: str | None) -> None:
        refs.append(SymbolRef(item.qualified_name, module.path, owner))
        for nested in item.nested:
            visit(nested, item.qualified_name)
        for callable_item in item.callables:
            refs.append(
                SymbolRef(
                    callable_item.qualified_name, module.path, item.qualified_name
                )
            )

    for item in module.types:
        visit(item, None)
    return refs


def iter_types(module: JavaModule) -> Iterator[JavaType]:
    stack = list(module.types)
    while stack:
        item = stack.pop()
        yield item
        stack.extend(reversed(item.nested))


def annotation_has(item: JavaType | JavaCallable, *names: str) -> bool:
    wanted = {name.split(".")[-1] for name in names}
    return any(ann.name in wanted for ann in item.annotations)


def annotation_named(
    item: JavaType | JavaCallable, *names: str
) -> JavaAnnotation | None:
    wanted = {name.split(".")[-1] for name in names}
    for ann in item.annotations:
        if ann.name in wanted:
            return ann
    return None


def resolve_constant(
    modules: dict[str, JavaModule], owner: JavaType, expression: str
) -> str | None:
    del owner
    expression = expression.strip()
    if expression.startswith('"') and expression.endswith('"'):
        return expression[1:-1]
    if expression.startswith("@"):
        expression = expression[1:]
    for module in modules.values():
        if expression in module.constants:
            value = module.constants[expression]
            if not value.startswith("@"):
                return value
        simple = expression.split(".")[-1]
        matches = [
            value
            for key, value in module.constants.items()
            if key.endswith(f".{simple}") and not value.startswith("@")
        ]
        if expression == simple and len(set(matches)) == 1:
            return matches[0]
        if "." in expression:
            type_name, field = expression.rsplit(".", 1)
            for java_type in iter_types(module):
                if (
                    java_type.name != type_name
                    and java_type.qualified_name != type_name
                ):
                    continue
                found = [
                    value
                    for fname, _t, value, _line in java_type.fields
                    if fname == field and value and not value.startswith("@")
                ]
                if len(found) == 1:
                    return found[0]
    return None
