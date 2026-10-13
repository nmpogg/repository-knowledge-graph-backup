"""Structured Vue SFC parse helpers for the language adapter.

SFC intermediate representation is typed blocks (template / script / style).
Script bodies with TypeScript evidence reuse tree-sitter TypeScript CST.
Regex is not used as the shared IR. Analyzed modules are never imported or
executed.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import PurePosixPath

import tree_sitter_typescript as ts_typescript
from tree_sitter import Language, Node, Parser, Tree

from rkg.adapters.contracts import AdapterDiagnostic, SymbolRef

TS_LANGUAGE = Language(ts_typescript.language_typescript())
_TS_PARSER = Parser(TS_LANGUAGE)

REPRESENTATION_KIND = "vue-sfc/v1+tree-sitter-typescript/0.23"
_IGNORE_PARTS = frozenset(
    {"node_modules", ".nuxt", ".output", "dist", "coverage", ".git"}
)
_BLOCK_KINDS = frozenset({"template", "script", "style"})


@dataclass(frozen=True, slots=True)
class VueBlock:
    kind: str
    attributes: tuple[tuple[str, str | None], ...]
    content: bytes
    start_line: int
    end_line: int
    content_start_line: int

    @property
    def lang(self) -> str | None:
        for key, value in self.attributes:
            if key == "lang":
                return value
        return None

    @property
    def is_setup(self) -> bool:
        return any(key == "setup" for key, _ in self.attributes)

    @property
    def is_scoped(self) -> bool:
        return any(key == "scoped" for key, _ in self.attributes)


@dataclass(frozen=True, slots=True)
class VueDefinition:
    owner: str
    qualified_name: str
    name: str
    kind: str
    node: Node
    start_line: int
    end_line: int


@dataclass(frozen=True, slots=True)
class VueImport:
    specifier: str
    default_name: str | None
    named: tuple[tuple[str, str], ...]
    namespace: str | None
    line: int
    is_type_only: bool


@dataclass(slots=True)
class VueSfc:
    path: str
    name: str
    source: bytes
    template: VueBlock | None = None
    scripts: tuple[VueBlock, ...] = ()
    styles: tuple[VueBlock, ...] = ()
    script_source: bytes = b""
    script_tree: Tree | None = None
    definitions: tuple[VueDefinition, ...] = ()
    imports: tuple[VueImport, ...] = ()
    diagnostics: tuple[AdapterDiagnostic, ...] = ()
    component_name: str | None = None


def is_vue_file(path: str) -> bool:
    posix = PurePosixPath(path)
    if any(part in _IGNORE_PARTS for part in posix.parts):
        return False
    return path.endswith(".vue")


def module_name(path: str) -> str:
    return ".".join(PurePosixPath(path).with_suffix("").parts)


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
    if node.type == "string":
        raw = text_of(source, node)
        if len(raw) >= 2 and raw[0] in {'"', "'", "`"} and raw[0] == raw[-1]:
            return raw[1:-1]
        return None
    if node.type == "template_string":
        if any(child.type == "template_substitution" for child in node.children):
            return None
        raw = text_of(source, node)
        if len(raw) >= 2 and raw[0] == "`" and raw[-1] == "`":
            return raw[1:-1]
        return None
    return None


def identifier_name(source: bytes, node: Node | None) -> str | None:
    if node is None:
        return None
    if node.type in {
        "identifier",
        "property_identifier",
        "type_identifier",
        "statement_identifier",
    }:
        return text_of(source, node)
    return None


def resolve_vue_specifier(
    from_path: str, specifier: str, files: set[str]
) -> str | None:
    """Resolve relative Vue/TS specifiers only — no Nuxt alias invention."""
    if not specifier or not specifier.startswith("."):
        return None
    base = PurePosixPath(from_path).parent / specifier
    parts: list[str] = []
    for part in base.parts:
        if part == "..":
            if parts:
                parts.pop()
        elif part not in {".", ""}:
            parts.append(part)
    stem = "/".join(parts)
    candidates = (
        stem,
        f"{stem}.vue",
        f"{stem}.ts",
        f"{stem}.tsx",
        f"{stem}/index.vue",
        f"{stem}/index.ts",
        f"{stem}/index.tsx",
    )
    matches = [item for item in candidates if item in files]
    return matches[0] if len(matches) == 1 else None


def parse_unit(
    path: str, content: bytes
) -> tuple[VueSfc | None, list[AdapterDiagnostic]]:
    diagnostics: list[AdapterDiagnostic] = []
    try:
        blocks, split_issues = split_sfc_blocks(path, content)
    except (UnicodeError, ValueError):
        diagnostics.append(AdapterDiagnostic("vue_syntax_error", path, 1))
        return None, diagnostics
    diagnostics.extend(split_issues)
    if any(item.code == "vue_syntax_error" for item in split_issues):
        return None, diagnostics

    template = next((item for item in blocks if item.kind == "template"), None)
    scripts = tuple(item for item in blocks if item.kind == "script")
    styles = tuple(item for item in blocks if item.kind == "style")
    sfc = VueSfc(
        path,
        module_name(path),
        content,
        template=template,
        scripts=scripts,
        styles=styles,
    )
    if not scripts:
        # Template-only SFC is still a valid SourceUnit (e.g. app shell).
        return sfc, diagnostics

    primary = _primary_script(scripts)
    if primary is None:
        diagnostics.append(
            AdapterDiagnostic("vue_syntax_error", path, scripts[0].start_line)
        )
        return None, diagnostics

    script_module, script_issues = _parse_script(path, primary)
    diagnostics.extend(script_issues)
    if script_module is None:
        return None, diagnostics

    sfc.script_source = script_module[0]
    sfc.script_tree = script_module[1]
    definitions, component_name, def_issues = collect_definitions(sfc, primary)
    diagnostics.extend(def_issues)
    sfc.definitions = tuple(definitions)
    sfc.component_name = component_name
    sfc.imports = tuple(collect_imports(sfc))
    return sfc, diagnostics


def split_sfc_blocks(
    path: str, content: bytes
) -> tuple[list[VueBlock], list[AdapterDiagnostic]]:
    """Scan top-level Vue SFC blocks into a structured block list."""
    diagnostics: list[AdapterDiagnostic] = []
    text = content.decode("utf-8")
    blocks: list[VueBlock] = []
    index = 0
    length = len(text)

    while index < length:
        while index < length and text[index].isspace():
            index += 1
        if index >= length:
            break
        if text[index] != "<":
            # Non-whitespace outside blocks is a syntax error for SFC.
            line = text.count("\n", 0, index) + 1
            diagnostics.append(AdapterDiagnostic("vue_syntax_error", path, line))
            return [], diagnostics
        if text.startswith("<!--", index):
            end = text.find("-->", index + 4)
            if end < 0:
                diagnostics.append(
                    AdapterDiagnostic(
                        "vue_syntax_error", path, text.count("\n", 0, index) + 1
                    )
                )
                return [], diagnostics
            index = end + 3
            continue
        close = text.find(">", index + 1)
        if close < 0:
            diagnostics.append(
                AdapterDiagnostic(
                    "vue_syntax_error", path, text.count("\n", 0, index) + 1
                )
            )
            return [], diagnostics
        header = text[index + 1 : close]
        self_closing = header.endswith("/")
        if self_closing:
            header = header[:-1].rstrip()
        parts = header.split(None, 1)
        if not parts:
            diagnostics.append(
                AdapterDiagnostic(
                    "vue_syntax_error", path, text.count("\n", 0, index) + 1
                )
            )
            return [], diagnostics
        tag = parts[0].lower()
        attr_text = parts[1] if len(parts) > 1 else ""
        attributes = _parse_attributes(attr_text)
        start_line = text.count("\n", 0, index) + 1
        if self_closing:
            end_line = text.count("\n", 0, close) + 1
            block = VueBlock(
                tag if tag in _BLOCK_KINDS else "custom",
                attributes,
                b"",
                start_line,
                end_line,
                end_line,
            )
            if tag in _BLOCK_KINDS:
                blocks.append(block)
            index = close + 1
            continue
        content_start = close + 1
        closer = f"</{tag}>"
        # Template may nest identical tags; script/style use first closer.
        if tag == "template":
            end = _find_balanced_close(text, content_start, "template")
        else:
            end = text.find(closer, content_start)
        if end < 0:
            diagnostics.append(AdapterDiagnostic("vue_syntax_error", path, start_line))
            return [], diagnostics
        raw_content = text[content_start:end]
        content_start_line = text.count("\n", 0, content_start) + 1
        end_line = text.count("\n", 0, end + len(closer) - 1) + 1
        if tag in _BLOCK_KINDS:
            blocks.append(
                VueBlock(
                    tag,
                    attributes,
                    raw_content.encode("utf-8"),
                    start_line,
                    end_line,
                    content_start_line,
                )
            )
        index = end + len(closer)

    if not blocks:
        diagnostics.append(AdapterDiagnostic("vue_syntax_error", path, 1))
    return blocks, diagnostics


def _find_balanced_close(text: str, start: int, tag: str) -> int:
    open_token = f"<{tag}"
    close_token = f"</{tag}>"
    depth = 1
    index = start
    length = len(text)
    while index < length:
        next_open = text.find(open_token, index)
        next_close = text.find(close_token, index)
        if next_close < 0:
            return -1
        if next_open >= 0 and next_open < next_close:
            # Ensure it is a real tag start (`<template` / `<template ` / `<template>`).
            after = next_open + len(open_token)
            if after < length and (
                text[after].isspace() or text[after] in {">", "/"}
            ):
                depth += 1
                index = after
                continue
            index = after
            continue
        depth -= 1
        if depth == 0:
            return next_close
        index = next_close + len(close_token)
    return -1


def _parse_attributes(raw: str) -> tuple[tuple[str, str | None], ...]:
    attrs: list[tuple[str, str | None]] = []
    index = 0
    text = raw.strip()
    length = len(text)
    while index < length:
        while index < length and text[index].isspace():
            index += 1
        if index >= length:
            break
        start = index
        while index < length and (
            text[index].isalnum() or text[index] in {"-", "_", ":"}
        ):
            index += 1
        if start == index:
            break
        name = text[start:index]
        while index < length and text[index].isspace():
            index += 1
        if index < length and text[index] == "=":
            index += 1
            while index < length and text[index].isspace():
                index += 1
            if index < length and text[index] in {'"', "'"}:
                quote = text[index]
                index += 1
                value_start = index
                while index < length and text[index] != quote:
                    index += 1
                value = text[value_start:index]
                if index < length:
                    index += 1
                attrs.append((name, value))
            else:
                value_start = index
                while index < length and not text[index].isspace():
                    index += 1
                attrs.append((name, text[value_start:index] or None))
        else:
            attrs.append((name, None))
    return tuple(attrs)


def _primary_script(scripts: tuple[VueBlock, ...]) -> VueBlock | None:
    if not scripts:
        return None
    setup = [item for item in scripts if item.is_setup]
    if len(setup) == 1:
        return setup[0]
    if len(setup) > 1:
        return None
    return scripts[0]


def _parse_script(
    path: str, block: VueBlock
) -> tuple[tuple[bytes, Tree] | None, list[AdapterDiagnostic]]:
    diagnostics: list[AdapterDiagnostic] = []
    lang = (block.lang or "ts").lower()
    if lang not in {"ts", "typescript", "js", "javascript"}:
        diagnostics.append(
            AdapterDiagnostic("vue_syntax_error", path, block.start_line)
        )
        return None, diagnostics
    # Pad so tree-sitter line numbers match the original .vue file.
    prefix = b"\n" * max(block.content_start_line - 1, 0)
    source = prefix + block.content
    try:
        tree = _TS_PARSER.parse(source)
    except (ValueError, TypeError, RuntimeError):
        diagnostics.append(
            AdapterDiagnostic("vue_syntax_error", path, block.content_start_line)
        )
        return None, diagnostics
    line = first_error_line(tree.root_node)
    if line is not None:
        diagnostics.append(AdapterDiagnostic("vue_syntax_error", path, line))
        return None, diagnostics
    return (source, tree), diagnostics


def collect_imports(sfc: VueSfc) -> list[VueImport]:
    if sfc.script_tree is None:
        return []
    imports: list[VueImport] = []
    for node in named_children(sfc.script_tree.root_node):
        if node.type != "import_statement":
            continue
        line = node.start_point[0] + 1
        is_type_only = any(
            child.type == "type" for child in node.children if not child.is_named
        ) or text_of(sfc.script_source, node).lstrip().startswith("import type ")
        source_node = next(
            (child for child in named_children(node) if child.type == "string"), None
        )
        specifier = string_literal(sfc.script_source, source_node)
        if specifier is None:
            continue
        clause = next(
            (child for child in named_children(node) if child.type == "import_clause"),
            None,
        )
        default_name: str | None = None
        namespace: str | None = None
        named: list[tuple[str, str]] = []
        if clause is not None:
            for child in named_children(clause):
                if child.type == "identifier":
                    default_name = text_of(sfc.script_source, child)
                elif child.type == "namespace_import":
                    alias = next(
                        (
                            part
                            for part in named_children(child)
                            if part.type == "identifier"
                        ),
                        None,
                    )
                    namespace = identifier_name(sfc.script_source, alias)
                elif child.type == "named_imports":
                    for spec in named_children(child):
                        if spec.type != "import_specifier":
                            continue
                        ids = [
                            text_of(sfc.script_source, part)
                            for part in named_children(spec)
                            if part.type == "identifier"
                        ]
                        if not ids:
                            continue
                        imported = ids[0]
                        local = ids[-1]
                        named.append((imported, local))
        imports.append(
            VueImport(
                specifier,
                default_name,
                tuple(named),
                namespace,
                line,
                is_type_only,
            )
        )
    return imports


def collect_definitions(
    sfc: VueSfc, primary: VueBlock
) -> tuple[list[VueDefinition], str | None, list[AdapterDiagnostic]]:
    diagnostics: list[AdapterDiagnostic] = []
    if sfc.script_tree is None:
        return [], None, diagnostics
    definitions: list[VueDefinition] = []
    seen: set[str] = set()
    component_name: str | None = None
    owner = sfc.name

    def add(
        owner_q: str, name: str, kind: str, node: Node
    ) -> str | None:
        qualified = f"{owner_q}.{name}"
        if qualified in seen:
            diagnostics.append(
                AdapterDiagnostic(
                    "vue_duplicate_definition", sfc.path, node.start_point[0] + 1
                )
            )
            return None
        seen.add(qualified)
        definitions.append(
            VueDefinition(
                owner_q,
                qualified,
                name,
                kind,
                node,
                node.start_point[0] + 1,
                node.end_point[0] + 1,
            )
        )
        return qualified

    if primary.is_setup:
        for child in named_children(sfc.script_tree.root_node):
            _visit_setup_statement(child, owner, add, sfc)
        # Script-setup identity is the SourceUnit; no fabricated Type entity.
        component_name = PurePosixPath(sfc.path).stem
        return definitions, component_name, diagnostics

    # Classic <script lang="ts"> — look for export default defineComponent(...)
    for child in named_children(sfc.script_tree.root_node):
        target = child
        if child.type == "export_statement":
            decl = child_named(child, "declaration")
            if decl is not None:
                target = decl
            else:
                for part in named_children(child):
                    if part.type == "call_expression":
                        target = part
                        break
        if target.type != "call_expression":
            # Top-level functions still extract.
            if target.type in {
                "function_declaration",
                "lexical_declaration",
                "variable_declaration",
            }:
                _visit_setup_statement(target, owner, add, sfc)
            continue
        callee = child_named(target, "function")
        if identifier_name(sfc.script_source, callee) != "defineComponent":
            continue
        args = child_named(target, "arguments")
        if args is None:
            continue
        options = next(
            (item for item in named_children(args) if item.type == "object"), None
        )
        if options is None:
            continue
        name_literal = _object_string_prop(sfc.script_source, options, "name")
        component_name = name_literal or PurePosixPath(sfc.path).stem
        type_q = add(owner, component_name, "vue_component", target)
        if type_q is None:
            continue
        setup = _object_method(sfc.script_source, options, "setup")
        if setup is not None:
            body = child_named(setup, "body")
            if body is not None:
                for stmt in named_children(body):
                    _visit_setup_statement(stmt, type_q, add, sfc)
    return definitions, component_name, diagnostics


def _object_string_prop(source: bytes, obj: Node, key: str) -> str | None:
    for child in named_children(obj):
        if child.type != "pair":
            continue
        key_node = child_named(child, "key")
        value = child_named(child, "value")
        name = identifier_name(source, key_node) or string_literal(source, key_node)
        if name != key:
            continue
        return string_literal(source, value)
    return None


def _object_method(source: bytes, obj: Node, key: str) -> Node | None:
    for child in named_children(obj):
        if child.type == "method_definition":
            name = identifier_name(source, child_named(child, "name"))
            if name == key:
                return child
        if child.type != "pair":
            continue
        key_node = child_named(child, "key")
        value = child_named(child, "value")
        name = identifier_name(source, key_node) or string_literal(source, key_node)
        if name != key or value is None:
            continue
        if value.type in {"arrow_function", "function_expression", "method_definition"}:
            return value
    return None


def _visit_setup_statement(node: Node, owner: str, add, sfc: VueSfc) -> None:
    target = node
    if node.type == "export_statement":
        decl = child_named(node, "declaration")
        if decl is None:
            return
        target = decl
    if target.type in {"function_declaration", "generator_function_declaration"}:
        name = identifier_name(sfc.script_source, child_named(target, "name"))
        if name:
            add(
                owner,
                name,
                "vue_async_function" if _is_async(target) else "vue_function",
                target,
            )
        return
    if target.type in {"lexical_declaration", "variable_declaration"}:
        for declarator in named_children(target):
            if declarator.type != "variable_declarator":
                continue
            name = identifier_name(
                sfc.script_source, child_named(declarator, "name")
            )
            value = child_named(declarator, "value")
            if not name or value is None:
                continue
            if value.type in {
                "arrow_function",
                "function_expression",
                "generator_function",
            }:
                add(
                    owner,
                    name,
                    "vue_async_function" if _is_async(value) else "vue_function",
                    value,
                )


def _is_async(node: Node) -> bool:
    return any(child.type == "async" for child in node.children)


def symbol_refs(sfc: VueSfc) -> list[SymbolRef]:
    return [
        SymbolRef(item.qualified_name, sfc.path, item.owner)
        for item in sfc.definitions
    ]


def body_of_definition(definition: VueDefinition) -> Node | None:
    node = definition.node
    if node.type in {
        "function_declaration",
        "generator_function_declaration",
        "function_expression",
        "generator_function",
        "arrow_function",
        "method_definition",
    }:
        return child_named(node, "body")
    return None
