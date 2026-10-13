"""Conservative local receiver types; never import analyzed modules."""

from __future__ import annotations

import ast
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from rkg.adapters.python_language import _unique_definitions
from rkg.adapters.python_resolution import (
    _bindings,
    _frames,
    _qualified,
    _scope_statements,
)
from rkg.domain import EntityType


class _Writes(ast.NodeVisitor):
    def __init__(self):
        self.names = Counter()

    def visit_Name(self, node):
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            self.names[node.id] += 1

    def visit_FunctionDef(self, node):
        self.names[node.name] += 1

    visit_AsyncFunctionDef = visit_FunctionDef
    visit_ClassDef = visit_FunctionDef

    def visit_Lambda(self, node):
        pass


class _CallsInScope(ast.NodeVisitor):
    def __init__(self):
        self.calls = []

    def visit_Call(self, node):
        self.calls.append(node)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        pass

    visit_AsyncFunctionDef = visit_FunctionDef
    visit_ClassDef = visit_FunctionDef
    visit_Lambda = visit_FunctionDef


@dataclass
class _Scope:
    module: object
    node: object
    owner: str
    frames: list
    writes: Counter = field(default_factory=Counter)
    values: dict = field(default_factory=dict)
    annotations: dict = field(default_factory=dict)
    calls: list = field(default_factory=list)


class StaticTypes:
    def __init__(self, index):
        self.index = index
        self.scopes: dict[str, _Scope] = {}
        self.bases: dict[str, tuple[str, ...]] = {}
        self.attributes: dict[tuple[str, str], list[tuple[str, ast.expr]]] = (
            defaultdict(list)
        )
        self.inferred: dict[tuple[str, str], str] = {}
        for module in index.modules:
            definitions = _unique_definitions(module.tree, module.name, module.path)[0]
            defs = {name: (owner, node) for owner, name, node in definitions}
            frame = _bindings(module, module.tree.body, module.name)
            entries = [(module.name, module.name, module.tree)] + definitions
            for owner, name, node in entries:
                if isinstance(node, ast.ClassDef):
                    frames = _frames(owner, module, defs, frame)
                    self.bases[name] = tuple(
                        q
                        for base in node.bases
                        if (
                            q := _qualified(
                                base.value if isinstance(base, ast.Subscript) else base,
                                frames,
                            )
                        )
                        and index.unique(q, frozenset({EntityType.TYPE}))
                    )
                    continue
                scope = _Scope(module, node, owner, _frames(name, module, defs, frame))
                visitor = _Writes()
                for statement in node.body:
                    visitor.visit(statement)
                scope.writes = visitor.names
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for arg in (
                        *node.args.posonlyargs,
                        *node.args.args,
                        *node.args.kwonlyargs,
                    ):
                        if arg.annotation:
                            scope.annotations[arg.arg] = arg.annotation
                for statement, conditional in _scope_statements(node.body):
                    value = getattr(statement, "value", None)
                    targets = (
                        statement.targets
                        if isinstance(statement, ast.Assign)
                        else (
                            [statement.target]
                            if isinstance(statement, ast.AnnAssign)
                            else []
                        )
                    )
                    if len(targets) == 1 and isinstance(targets[0], ast.Name):
                        target = targets[0].id
                        if isinstance(statement, ast.AnnAssign):
                            scope.annotations[target] = statement.annotation
                        if not conditional and value is not None:
                            scope.values[target] = value
                    for target in targets:
                        if (
                            isinstance(target, ast.Attribute)
                            and isinstance(target.value, ast.Name)
                            and target.value.id == "self"
                        ):
                            self.attributes[(owner, target.attr)].append(
                                (name, None if conditional else value)
                            )
                collector = _CallsInScope()
                for statement in node.body:
                    collector.visit(statement)
                scope.calls = collector.calls
                self.scopes[name] = scope
        # Infer an unannotated helper parameter only if every resolved call site
        # supplies one and the same known local type. Conflicts remain unresolved.
        for _ in range(8):
            observations = defaultdict(list)
            for name, scope in self.scopes.items():
                for call in {id(c): c for c in scope.calls}.values():
                    target = self.call_target(name, call)
                    target_scope = (
                        self.scopes.get(target.qualified_name) if target else None
                    )
                    if target_scope is None or not isinstance(
                        target_scope.node, (ast.FunctionDef, ast.AsyncFunctionDef)
                    ):
                        continue
                    params = list(target_scope.node.args.posonlyargs) + list(
                        target_scope.node.args.args
                    )
                    if (
                        isinstance(call.func, ast.Attribute)
                        and params
                        and params[0].arg in {"self", "cls"}
                    ):
                        params = params[1:]
                    args = {p.arg: a for p, a in zip(params, call.args)}
                    args.update({k.arg: k.value for k in call.keywords if k.arg})
                    for param in params + list(target_scope.node.args.kwonlyargs):
                        arg = args.get(param.arg)
                        observations[(target.qualified_name, param.arg)].append(
                            self.expression(name, arg) if arg is not None else None
                        )
            inferred = {
                key: values[0]
                for key, values in observations.items()
                if values and None not in values and len(set(values)) == 1
            }
            if inferred == self.inferred:
                break
            self.inferred = inferred

    def annotation(self, scope, node):
        if isinstance(node, ast.Subscript) and _qualified(node.value, scope.frames) in {
            "typing.Annotated",
            "typing_extensions.Annotated",
        }:
            node = (
                node.slice.elts[0] if isinstance(node.slice, ast.Tuple) else node.slice
            )
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            if isinstance(node.right, ast.Constant) and node.right.value is None:
                node = node.left
        q = _qualified(node, scope.frames)
        return q if self.index.unique(q, frozenset({EntityType.TYPE})) else None

    def expression(self, name, node, seen=frozenset()):
        scope = self.scopes.get(name)
        if scope is None or node is None:
            return None
        if isinstance(node, ast.Call):
            q = _qualified(node.func, scope.frames)
            if self.index.unique(q, frozenset({EntityType.TYPE})):
                return q
            return None
        if isinstance(node, ast.Name):
            key = (name, node.id)
            if key in seen:
                return None
            if (
                node.id in {"self", "cls"}
                and scope.owner in self.bases
                and scope.writes[node.id] == 0
            ):
                if (
                    scope.node.args.args
                    and scope.node.args.args[0].arg == node.id
                    and not any(
                        _qualified(d, scope.frames) == "staticmethod"
                        or isinstance(d, ast.Name)
                        and d.id == "staticmethod"
                        for d in scope.node.decorator_list
                    )
                ):
                    return scope.owner
            writes = scope.writes[node.id]
            value = scope.values.get(node.id)
            if (
                writes == 1
                and value is not None
                and getattr(value, "lineno", 0) <= getattr(node, "lineno", 0)
            ):
                return self.expression(name, value, seen | {key})
            if writes == 0:
                note = scope.annotations.get(node.id)
                if note is not None:
                    return self.annotation(scope, note)
                inferred = self.inferred.get(key)
                if inferred:
                    return inferred
                for frame in scope.frames[:-1]:
                    if node.id in frame:
                        return None
                if name != scope.module.name:
                    return self.expression(scope.module.name, node, seen | {key})
            return None
        if isinstance(node, ast.Attribute):
            owner = self.expression(name, node.value, seen)
            return self.attribute(owner, node.attr, seen) if owner else None
        return None

    def attribute(self, owner, attr, seen):
        key = (owner, attr)
        if key in seen:
            return None
        assignments = self.attributes.get(key, [])
        if assignments:
            if len(assignments) != 1:
                return None
            scope, value = assignments[0]
            return self.expression(scope, value, seen | {key})
        values = {
            self.attribute(base, attr, seen | {key})
            for base in self.bases.get(owner, ())
        }
        return next(iter(values)) if len(values) == 1 else None

    def method(self, owner, attr, seen=frozenset()):
        if owner in seen:
            return None
        target = self.index.unique(f"{owner}.{attr}", frozenset({EntityType.CALLABLE}))
        if target:
            return target
        # A duplicate/rebound declaration must not fall through to a base.
        if self.index.by_name.get(f"{owner}.{attr}"):
            return None
        targets = [
            self.method(base, attr, seen | {owner})
            for base in self.bases.get(owner, ())
        ]
        ids = {t.id for t in targets if t}
        return (
            next((t for t in targets if t), None)
            if len(ids) == 1 and all(targets)
            else None
        )

    def call_target(self, name, call):
        scope = self.scopes[name]
        if isinstance(call.func, ast.Attribute):
            owner = self.expression(name, call.func.value)
            if owner:
                return self.method(owner, call.func.attr)
        return self.index.unique(
            _qualified(call.func, scope.frames), frozenset({EntityType.CALLABLE})
        )
