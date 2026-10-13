"""Conservative intra-repository import, call and class resolution."""

from __future__ import annotations

import ast
from collections import defaultdict
from collections.abc import Iterator, Sequence
from dataclasses import dataclass

from rkg.adapters.contracts import (
    AdapterContext,
    AdapterDiagnostic,
    ParseResult,
)
from rkg.adapters.python_language import (
    _canonical_diagnostics,
    _module_name,
    _nested_bodies,
    _unique_definitions,
)
from rkg.domain import (
    Edge,
    EdgeType,
    Entity,
    EntityType,
    Evidence,
    FactBatch,
    edge_id,
    evidence_id,
)

IMPORT_RULE = "RKG.python.import.v1"
CALL_RULE = "RKG.python.call.v1"
INHERIT_RULE = "RKG.python.inherit.v1"
IMPLEMENT_RULE = "RKG.python.implement.v1"
ABSTRACT_MARKERS = frozenset(
    {"abc.ABC", "abc.ABCMeta", "typing.Protocol", "typing_extensions.Protocol"}
)
ABSTRACT_DECORATORS = frozenset({"abc.abstractmethod"})


@dataclass(frozen=True, slots=True)
class _Module:
    path: str
    name: str
    tree: ast.Module


def _scope_statements(
    body: Sequence[ast.stmt], conditional: bool = False
) -> Iterator[tuple[ast.stmt, bool]]:
    for statement in body:
        yield statement, conditional
        if not isinstance(
            statement, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            for nested in _nested_bodies(statement):
                yield from _scope_statements(nested, True)


class _Stores(ast.NodeVisitor):
    def __init__(self) -> None:
        self.names: set[str] = set()

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            self.names.add(node.id)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        del node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        del node

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        del node

    def visit_Lambda(self, node: ast.Lambda) -> None:
        del node


def _package(module: _Module) -> list[str]:
    parts = module.name.split(".")
    return parts if module.path.endswith("/__init__.py") else parts[:-1]


def _from_base(module: _Module, node: ast.ImportFrom) -> str | None:
    if node.level == 0:
        return node.module
    parts = _package(module)
    if node.level > len(parts) + 1:
        return None
    prefix = parts[: len(parts) - node.level + 1]
    if node.module:
        prefix.extend(node.module.split("."))
    return ".".join(prefix) or None


def _import_entries(
    module: _Module, statement: ast.Import | ast.ImportFrom
) -> Iterator[tuple[str, str | None, bool]]:
    if isinstance(statement, ast.Import):
        for alias in statement.names:
            bound = alias.asname or alias.name.split(".")[0]
            target = alias.name if alias.asname else alias.name.split(".")[0]
            yield bound, target, False
    else:
        base = _from_base(module, statement)
        for alias in statement.names:
            if alias.name == "*":
                yield "*", None, True
            else:
                yield (
                    alias.asname or alias.name,
                    f"{base}.{alias.name}" if base else None,
                    False,
                )


def _parameter_names(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    args = node.args
    names = {arg.arg for arg in (*args.posonlyargs, *args.args, *args.kwonlyargs)}
    if args.vararg:
        names.add(args.vararg.arg)
    if args.kwarg:
        names.add(args.kwarg.arg)
    return names


def _bindings(
    module: _Module,
    body: Sequence[ast.stmt],
    owner: str,
    parameters: set[str] | None = None,
) -> dict[str, str | None]:
    options: dict[str, set[str]] = defaultdict(set)
    unknown = set(parameters or ())
    counts: dict[str, int] = defaultdict(int)
    for statement, conditional in _scope_statements(body):
        if isinstance(statement, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            counts[statement.name] += 1
            if conditional:
                unknown.add(statement.name)
            else:
                options[statement.name].add(f"{owner}.{statement.name}")
        elif isinstance(statement, (ast.Import, ast.ImportFrom)):
            for name, target, star in _import_entries(module, statement):
                if star:
                    continue
                if conditional or target is None:
                    unknown.add(name)
                else:
                    options[name].add(target)
        else:
            stores = _Stores()
            stores.visit(statement)
            unknown.update(stores.names)
            if isinstance(statement, (ast.Global, ast.Nonlocal)):
                unknown.update(statement.names)
    unknown.update(name for name, count in counts.items() if count > 1)
    return {
        name: next(iter(targets)) if name not in unknown and len(targets) == 1 else None
        for name, targets in options.items()
    } | {name: None for name in unknown}


def _qualified(
    expression: ast.expr, frames: Sequence[dict[str, str | None]]
) -> str | None:
    if isinstance(expression, ast.Name):
        for frame in frames:
            if expression.id in frame:
                return frame[expression.id]
        return None
    if isinstance(expression, ast.Attribute):
        parent = _qualified(expression.value, frames)
        return f"{parent}.{expression.attr}" if parent else None
    return None


class _Index:
    def __init__(self, parsed: ParseResult, candidate: FactBatch) -> None:
        self.modules: list[_Module] = [
            _Module(
                unit.relative_path,
                _module_name(unit.relative_path),
                unit.representation,
            )
            for unit in parsed.units
            if unit.language == "python" and isinstance(unit.representation, ast.Module)
        ]
        self.by_name: dict[str, list[Entity]] = defaultdict(list)
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

    def shadows_external_marker(self, name: str) -> bool:
        root = name.split(".", 1)[0]
        return any(item.type == EntityType.SOURCE_UNIT for item in self.by_name[root])


class _Edges:
    def __init__(self, context: AdapterContext, candidate: FactBatch) -> None:
        self.context = context
        self.edges: dict[str, Edge] = {item.id: item for item in candidate.edges}
        self.evidence: dict[str, Evidence] = {
            item.id: item for item in candidate.evidence
        }

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


class _Calls(ast.NodeVisitor):
    def __init__(
        self,
        source: Entity,
        module: _Module,
        frames: Sequence[dict[str, str | None]],
        index: _Index,
        edges: _Edges,
        diagnostics: list[AdapterDiagnostic],
        types,
    ) -> None:
        self.source = source
        self.module = module
        self.frames = frames
        self.index = index
        self.edges = edges
        self.diagnostics = diagnostics
        self.types = types

    def _bound_method(self, node: ast.Call) -> Entity | None:
        if not isinstance(node.func, ast.Attribute):
            return None
        target = self.types.call_target(self.source.qualified_name, node)
        if target is None or target.language_kind not in {
            "python_method",
            "python_async_method",
        }:
            return None
        return target

    def visit_Call(self, node: ast.Call) -> None:
        bound = self._bound_method(node)
        if bound is not None:
            self.edges.add(
                EdgeType.CALLS,
                self.source.id,
                bound.id,
                self.module.path,
                node.lineno,
                CALL_RULE,
            )
            self.generic_visit(node)
            return
        target_name = _qualified(node.func, self.frames)
        target = self.index.unique(target_name, frozenset({EntityType.CALLABLE}))
        constructor = self.index.unique(target_name, frozenset({EntityType.TYPE}))
        if target and target.language_kind in (
            "python_function",
            "python_async_function",
        ):
            self.edges.add(
                EdgeType.CALLS,
                self.source.id,
                target.id,
                self.module.path,
                node.lineno,
                CALL_RULE,
            )
        elif constructor is None:
            is_self_dispatch = (
                isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id in {"self", "cls"}
            )
            is_method = target is not None and target.language_kind in (
                "python_method",
                "python_async_method",
            )
            is_shadowed = isinstance(node.func, ast.Name) and any(
                node.func.id in frame and frame[node.func.id] is None
                for frame in self.frames
            )
            if (
                not isinstance(node.func, (ast.Name, ast.Attribute))
                or is_self_dispatch
                or is_method
            ):
                code = "python_call_dynamic"
            elif is_shadowed:
                code = "python_binding_ambiguous"
            else:
                code = "python_call_unresolved"
            self.diagnostics.append(
                AdapterDiagnostic(code, self.module.path, node.lineno)
            )
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        del node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        del node

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        del node

    def visit_Lambda(self, node: ast.Lambda) -> None:
        del node


def _frames(
    owner: str,
    module: _Module,
    definitions: dict[
        str, tuple[str, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef]
    ],
    module_frame: dict[str, str | None],
) -> list[dict[str, str | None]]:
    frames = []
    current = owner
    while current in definitions:
        parent, node = definitions[current]
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            frames.append(_bindings(module, node.body, current, _parameter_names(node)))
        current = parent
    frames.append(module_frame)
    return frames


def resolve_python(
    context: AdapterContext, parsed: ParseResult, candidate: FactBatch
) -> tuple[FactBatch, tuple[AdapterDiagnostic, ...]]:
    """Resolve only unique local targets; every emitted edge has source evidence."""
    from rkg.adapters.python_types import StaticTypes

    index = _Index(parsed, candidate)
    types = StaticTypes(index)
    edges = _Edges(context, candidate)
    diagnostics = list(parsed.diagnostics)
    abstract: set[str] = set()
    class_bases: list[tuple[Entity, list[Entity], str, int]] = []
    for module in index.modules:
        source = index.unique(module.name, frozenset({EntityType.SOURCE_UNIT}))
        if source is None or source.file_path != module.path:
            continue
        module_frame = _bindings(module, module.tree.body, module.name)
        definitions_list, _ = _unique_definitions(module.tree, module.name, module.path)
        definitions = {name: (owner, node) for owner, name, node in definitions_list}

        for statement in ast.walk(module.tree):
            if not isinstance(statement, (ast.Import, ast.ImportFrom)):
                continue
            if isinstance(statement, ast.Import):
                import_targets = ((alias.name, False) for alias in statement.names)
            else:
                import_targets = (
                    (target_name, star)
                    for _, target_name, star in _import_entries(module, statement)
                )
            for target_name, star in import_targets:
                if star:
                    diagnostics.append(
                        AdapterDiagnostic(
                            "python_import_star", module.path, statement.lineno
                        )
                    )
                    continue
                target = index.import_target(target_name)
                if target and target.id != source.id:
                    edges.add(
                        EdgeType.IMPORTS,
                        source.id,
                        target.id,
                        module.path,
                        statement.lineno,
                        IMPORT_RULE,
                    )
                elif target is None:
                    diagnostics.append(
                        AdapterDiagnostic(
                            "python_import_unresolved", module.path, statement.lineno
                        )
                    )

        for owner, name, node in definitions_list:
            if not isinstance(node, ast.ClassDef):
                continue
            source_type = index.unique(name, frozenset({EntityType.TYPE}))
            if source_type is None or source_type.file_path != module.path:
                continue
            frames = _frames(owner, module, definitions, module_frame)
            resolved_bases = []
            for base in node.bases:
                base_target = base.value if isinstance(base, ast.Subscript) else base
                target_name = _qualified(base_target, frames)
                target = index.unique(target_name, frozenset({EntityType.TYPE}))
                if target is not None:
                    resolved_bases.append(target)
                elif (
                    target_name in ABSTRACT_MARKERS
                    and not index.shadows_external_marker(target_name)
                ):
                    abstract.add(name)
                else:
                    diagnostics.append(
                        AdapterDiagnostic(
                            "python_base_unresolved", module.path, base.lineno
                        )
                    )
            for keyword in node.keywords:
                if (
                    keyword.arg == "metaclass"
                    and _qualified(keyword.value, frames) == "abc.ABCMeta"
                    and index.unique("abc.ABCMeta", frozenset({EntityType.TYPE}))
                    is None
                    and not index.shadows_external_marker("abc.ABCMeta")
                ):
                    abstract.add(name)
            for member in node.body:
                if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)) and any(
                    _qualified(decorator, frames) in ABSTRACT_DECORATORS
                    and index.unique(
                        _qualified(decorator, frames),
                        frozenset({EntityType.CALLABLE}),
                    )
                    is None
                    and not index.shadows_external_marker(_qualified(decorator, frames))
                    for decorator in member.decorator_list
                ):
                    abstract.add(name)
            class_bases.append((source_type, resolved_bases, module.path, node.lineno))

        for owner, name, node in definitions_list:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            caller = index.unique(name, frozenset({EntityType.CALLABLE}))
            if caller is None or caller.file_path != module.path:
                continue
            frames = _frames(name, module, definitions, module_frame)
            visitor = _Calls(caller, module, frames, index, edges, diagnostics, types)
            for statement in node.body:
                visitor.visit(statement)

    for child, bases, path, line in class_bases:
        for base in bases:
            edges.add(
                EdgeType.INHERITS_FROM,
                child.id,
                base.id,
                path,
                line,
                INHERIT_RULE,
            )
            if base.qualified_name in abstract:
                edges.add(
                    EdgeType.IMPLEMENTS,
                    child.id,
                    base.id,
                    path,
                    line,
                    IMPLEMENT_RULE,
                )

    ordered_diagnostics = tuple(
        sorted(
            diagnostics,
            key=lambda item: (item.relative_path or "", item.line or 0, item.code),
        )
    )
    facts = FactBatch(
        candidate.repository_id,
        candidate.snapshot_id,
        candidate.entities,
        tuple(edges.edges[key] for key in sorted(edges.edges)),
        tuple(edges.evidence[key] for key in sorted(edges.evidence)),
        _canonical_diagnostics(context, ordered_diagnostics),
    )
    return facts, ordered_diagnostics
