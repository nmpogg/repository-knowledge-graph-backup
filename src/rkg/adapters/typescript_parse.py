"""Tree-sitter TypeScript/TSX parse helpers for the language adapter.

The structured tree-sitter CST is the intermediate representation. Regex is not
used as IR. Analyzed modules are never imported or executed.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import PurePosixPath

import tree_sitter_typescript as ts_typescript
from tree_sitter import Language, Node, Parser, Tree

from rkg.adapters.contracts import AdapterDiagnostic, SymbolRef
from rkg.ingestion import SourceManifest

TS_LANGUAGE = Language(ts_typescript.language_typescript())
TSX_LANGUAGE = Language(ts_typescript.language_tsx())
_TS_PARSER = Parser(TS_LANGUAGE)
_TSX_PARSER = Parser(TSX_LANGUAGE)

REPRESENTATION_KIND = "tree-sitter-typescript/0.23"
_IGNORE_PARTS = frozenset({"node_modules", ".git", "dist", "build", "coverage"})
_EXTENSIONS = (".ts", ".tsx")
_JSON_COMMENT = re.compile(r"/\*.*?\*/|//.*?$", re.MULTILINE | re.DOTALL)


@dataclass(frozen=True, slots=True)
class TsDefinition:
    owner: str
    qualified_name: str
    name: str
    kind: str
    node: Node
    start_line: int
    end_line: int


@dataclass(slots=True)
class TsModule:
    path: str
    name: str
    source: bytes
    tree: Tree
    definitions: tuple[TsDefinition, ...] = ()
    diagnostics: tuple[AdapterDiagnostic, ...] = ()
    aliases: dict[str, str] = field(default_factory=dict)


def is_typescript_file(path: str) -> bool:
    posix = PurePosixPath(path)
    if any(part in _IGNORE_PARTS for part in posix.parts):
        return False
    if path.endswith(".d.ts"):
        return False
    return path.endswith(_EXTENSIONS)


def module_name(path: str) -> str:
    return ".".join(PurePosixPath(path).with_suffix("").parts)


def qualified_symbol(path: str, symbol: str) -> str:
    return f"{module_name(path)}.{symbol}"


def _parser_for(path: str) -> Parser:
    return _TSX_PARSER if path.endswith(".tsx") else _TS_PARSER


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


def _strip_json_comments(raw: str) -> str:
    return _JSON_COMMENT.sub("", raw)


def load_path_aliases(manifest: SourceManifest) -> dict[str, str]:
    """Map import prefix (for example '@/') to a repo-relative directory prefix."""
    aliases: dict[str, str] = {}
    for item in manifest.files:
        name = PurePosixPath(item.relative_path).name
        if name not in {"tsconfig.json", "tsconfig.app.json", "tsconfig.node.json"}:
            continue
        try:
            data = json.loads(_strip_json_comments(item.content.decode("utf-8")))
        except (UnicodeError, json.JSONDecodeError, ValueError):
            continue
        paths = data.get("compilerOptions", {}).get("paths") or {}
        if not isinstance(paths, dict):
            continue
        config_dir = PurePosixPath(item.relative_path).parent
        for pattern, targets in paths.items():
            if (
                not isinstance(pattern, str)
                or not isinstance(targets, list)
                or not targets
            ):
                continue
            target = targets[0]
            if not isinstance(target, str):
                continue
            if not pattern.endswith("/*") or not target.endswith("/*"):
                continue
            prefix = pattern[:-1]  # '@/ *' -> '@/'
            mapped = target[:-1]
            resolved = PurePosixPath(config_dir) / mapped
            parts = []
            for part in resolved.parts:
                if part == "..":
                    if parts:
                        parts.pop()
                elif part not in {".", ""}:
                    parts.append(part)
            aliases[prefix] = "/".join(parts)
    # Vite alias `@` -> `src` when uniquely present and unused by tsconfig.
    if "@/" not in aliases:
        for item in manifest.files:
            if item.relative_path.endswith("vite.config.ts"):
                aliases.setdefault("@/", "src/")
                break
    return aliases


def resolve_specifier(
    from_path: str, specifier: str, files: set[str], aliases: dict[str, str]
) -> str | None:
    if not specifier or specifier.startswith("\0"):
        return None
    if specifier.startswith("@/") or any(
        specifier.startswith(prefix) for prefix in aliases
    ):
        matched = None
        for prefix, target in sorted(aliases.items(), key=lambda item: -len(item[0])):
            if specifier.startswith(prefix):
                matched = target + specifier[len(prefix) :]
                break
        if matched is None and specifier.startswith("@/"):
            # Unique Vite/TS convention when tsconfig is outside the scan set.
            matched = "src/" + specifier[2:]
        if matched is None:
            return None
        return _existing_module(matched, files)
    if specifier.startswith("."):
        base = PurePosixPath(from_path).parent / specifier
        parts: list[str] = []
        for part in base.parts:
            if part == "..":
                if parts:
                    parts.pop()
            elif part not in {".", ""}:
                parts.append(part)
        return _existing_module("/".join(parts), files)
    return None


def _existing_module(stem: str, files: set[str]) -> str | None:
    """Resolve a path stem to a unique scanned module.

    TypeScript ESM often imports with a `.js` specifier that maps to a `.ts`
    source file; strip that runtime suffix before trying TypeScript extensions.
    """
    variants = [stem]
    pure = PurePosixPath(stem)
    if pure.suffix in {".js", ".jsx", ".mjs", ".cjs"}:
        variants.append(str(pure.with_suffix("")))
    candidates: list[str] = []
    for base in variants:
        candidates.extend(
            (
                base,
                f"{base}.ts",
                f"{base}.tsx",
                f"{base}/index.ts",
                f"{base}/index.tsx",
            )
        )
    matches = [item for item in dict.fromkeys(candidates) if item in files]
    return matches[0] if len(matches) == 1 else None


def parse_unit(
    path: str, content: bytes, aliases: dict[str, str]
) -> tuple[TsModule | None, list[AdapterDiagnostic]]:
    diagnostics: list[AdapterDiagnostic] = []
    try:
        tree = _parser_for(path).parse(content)
    except (ValueError, TypeError, RuntimeError):
        diagnostics.append(AdapterDiagnostic("typescript_syntax_error", path, 1))
        return None, diagnostics
    line = first_error_line(tree.root_node)
    if line is not None:
        diagnostics.append(AdapterDiagnostic("typescript_syntax_error", path, line))
        return None, diagnostics
    module = TsModule(path, module_name(path), content, tree, aliases=dict(aliases))
    definitions, dupes = collect_definitions(module)
    module.definitions = tuple(definitions)
    diagnostics.extend(dupes)
    return module, diagnostics


def collect_definitions(
    module: TsModule,
) -> tuple[list[TsDefinition], list[AdapterDiagnostic]]:
    seen: set[str] = set()
    definitions: list[TsDefinition] = []
    diagnostics: list[AdapterDiagnostic] = []

    def add(
        owner: str, name: str, kind: str, node: Node, *, nested_owner: str | None = None
    ) -> str | None:
        qualified = f"{owner}.{name}"
        if qualified in seen:
            diagnostics.append(
                AdapterDiagnostic(
                    "typescript_duplicate_definition",
                    module.path,
                    node.start_point[0] + 1,
                )
            )
            return None
        seen.add(qualified)
        definitions.append(
            TsDefinition(
                owner,
                qualified,
                name,
                kind,
                node,
                node.start_point[0] + 1,
                node.end_point[0] + 1,
            )
        )
        return nested_owner or qualified

    def visit_statement(node: Node, owner: str) -> None:
        target = node
        if node.type == "export_statement":
            declaration = child_named(node, "declaration")
            if declaration is None:
                # export default function/class or export default identifier
                for child in named_children(node):
                    if child.type in {
                        "function_declaration",
                        "class_declaration",
                        "abstract_class_declaration",
                        "lexical_declaration",
                        "variable_declaration",
                    }:
                        visit_statement(child, owner)
                        return
                    if child.type == "identifier":
                        return
                return
            target = declaration
        if target.type in {"function_declaration", "generator_function_declaration"}:
            name = identifier_name(module.source, child_named(target, "name"))
            if name:
                add(
                    owner,
                    name,
                    "typescript_async_function"
                    if _is_async(target)
                    else "typescript_function",
                    target,
                )
            return
        if target.type in {"class_declaration", "abstract_class_declaration"}:
            name = identifier_name(module.source, child_named(target, "name"))
            if not name:
                return
            class_q = add(owner, name, "typescript_class", target)
            if class_q is None:
                return
            body = child_named(target, "body")
            if body is None:
                return
            for member in named_children(body):
                _visit_class_member(member, class_q, add, module)
            return
        if target.type == "interface_declaration":
            name = identifier_name(module.source, child_named(target, "name"))
            if name:
                add(owner, name, "typescript_interface", target)
            return
        if target.type == "type_alias_declaration":
            name = identifier_name(module.source, child_named(target, "name"))
            if name:
                add(owner, name, "typescript_type_alias", target)
            return
        if target.type in {"lexical_declaration", "variable_declaration"}:
            for declarator in named_children(target):
                if declarator.type != "variable_declarator":
                    continue
                name_node = child_named(declarator, "name")
                value = child_named(declarator, "value")
                name = identifier_name(module.source, name_node)
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
                        "typescript_async_function"
                        if _is_async(value)
                        else "typescript_function",
                        value,
                    )
                elif value.type == "object":
                    object_q = add(owner, name, "typescript_object", value)
                    if object_q is not None:
                        _visit_object_methods(value, object_q, add, module)

    def _visit_object_methods(obj: Node, owner_q: str, add, module: TsModule) -> None:
        for child in named_children(obj):
            if child.type != "pair":
                continue
            key_node = child_named(child, "key")
            value = child_named(child, "value")
            key = identifier_name(module.source, key_node) or string_literal(
                module.source, key_node
            )
            if not key or value is None:
                continue
            if value.type in {
                "arrow_function",
                "function_expression",
                "generator_function",
            }:
                add(
                    owner_q,
                    key,
                    "typescript_async_function"
                    if _is_async(value)
                    else "typescript_function",
                    value,
                )

    def _visit_class_member(member: Node, class_q: str, add, module: TsModule) -> None:
        if member.type == "export_statement":
            return
        if member.type in {
            "public_field_definition",
            "field_definition",
            "readonly_property",
        }:
            return
        if member.type == "method_definition":
            name_node = child_named(member, "name")
            name = identifier_name(module.source, name_node)
            if (
                name is None
                and name_node is not None
                and text_of(module.source, name_node) == "constructor"
            ):
                name = "constructor"
            if not name:
                return
            kind = (
                "typescript_async_method" if _is_async(member) else "typescript_method"
            )
            add(class_q, name, kind, member)
            return
        if member.type in {
            "function_signature",
            "method_signature",
            "property_signature",
        }:
            return

    root = module.tree.root_node
    for child in named_children(root):
        visit_statement(child, module.name)
    return definitions, diagnostics


def _is_async(node: Node) -> bool:
    return any(child.type == "async" for child in node.children)


def symbol_refs(module: TsModule) -> list[SymbolRef]:
    return [
        SymbolRef(item.qualified_name, module.path, item.owner)
        for item in module.definitions
    ]


def body_of_definition(definition: TsDefinition) -> Node | None:
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
