"""Bounded AST views for FastAPI factories and literal router loops.

These views never evaluate Python. They retain source locations and leave the
original parse tree intact for language facts and handler identities.
"""

from __future__ import annotations

import ast
import copy
from collections import Counter
from collections.abc import Iterator, Sequence

from rkg.adapters.python_resolution import _bindings, _Module, _qualified


def module_writes(tree: ast.Module) -> Counter[str]:
    class Writes(ast.NodeVisitor):
        def visit_Name(self, node):
            if isinstance(node.ctx, (ast.Store, ast.Del)):
                counts[node.id] += 1

        def visit_FunctionDef(self, node):
            counts[node.name] += 1

        visit_AsyncFunctionDef = visit_FunctionDef
        visit_ClassDef = visit_FunctionDef

        def visit_Lambda(self, node):
            pass

    counts: Counter[str] = Counter()
    Writes().visit(tree)
    return counts


def assignment(statement: ast.stmt) -> tuple[str | None, ast.expr | None]:
    if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
        target = statement.targets[0]
        if isinstance(target, ast.Name):
            return target.id, statement.value
    if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
        return statement.target.id, statement.value
    return None, None


def factory_view(module: _Module) -> ast.Module:
    """Expand a unique local, parameterless factory returning its single app.

    Only the app assignment and registration statements are projected. Branches,
    imported factories, decorated factories and parameterized calls are unresolved.
    Nested function definitions keep their original language symbol identities.
    """
    tree = module.tree
    frame = _bindings(module, tree.body, module.name)
    factories = {
        f"{module.name}.{node.name}": node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and not node.decorator_list
        and not node.args.args
        and not node.args.posonlyargs
        and not node.args.kwonlyargs
        and not node.args.vararg
        and not node.args.kwarg
        and frame.get(node.name) == f"{module.name}.{node.name}"
    }
    writes = module_writes(tree)
    body: list[ast.stmt] = []
    for statement in tree.body:
        target, value = assignment(statement)
        factory = (
            factories.get(_qualified(value.func, [frame]))
            if isinstance(value, ast.Call) and not value.args and not value.keywords
            else None
        )
        if not target or writes[target] != 1 or factory is None:
            body.append(statement)
            continue

        # Ignore returns inside nested middleware/handlers.
        class Returns(ast.NodeVisitor):
            def visit_Return(self, node):
                returns.append(node)

            def visit_FunctionDef(self, node):
                pass

            visit_AsyncFunctionDef = visit_FunctionDef
            visit_ClassDef = visit_FunctionDef

        returns = []
        visitor = Returns()
        for node in factory.body:
            visitor.visit(node)
        if (
            len(returns) != 1
            or factory.body[-1] is not returns[0]
            or not isinstance(returns[0].value, ast.Name)
        ):
            body.append(statement)
            continue
        local = returns[0].value.id
        local_tree = ast.Module(body=factory.body, type_ignores=[])
        local_frame = frame | _bindings(
            module, factory.body, f"{module.name}.{factory.name}"
        )
        constructors = [
            node
            for node in factory.body
            if assignment(node)[0] == local
            and isinstance(assignment(node)[1], ast.Call)
            and _qualified(assignment(node)[1].func, [local_frame]) == "fastapi.FastAPI"
        ]
        # Other locals/imports must not escape into the module-level frame.
        bindings = module_writes(local_tree)
        if len(constructors) != 1 or bindings[local] != 1:
            body.append(statement)
            continue
        if any(
            isinstance(n, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal))
            for n in factory.body
        ):
            body.append(statement)
            continue

        class Rename(ast.NodeTransformer):
            def visit_Name(self, node):
                if node.id == local:
                    return ast.copy_location(ast.Name(id=target, ctx=node.ctx), node)
                return node

        projected = []
        unsafe = False
        for node in factory.body[:-1]:
            if isinstance(node, ast.Expr) and not (
                isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Attribute)
                and node.value.func.attr in {"include_router", "add_api_route"}
            ):
                continue
            if node is constructors[0] or isinstance(node, (ast.Expr, ast.For)):
                if node is not constructors[0]:
                    loop_names = {
                        n.target.id
                        for n in ast.walk(node)
                        if isinstance(n, ast.For) and isinstance(n.target, ast.Name)
                    }
                    if any(
                        isinstance(n, ast.Name)
                        and isinstance(n.ctx, ast.Load)
                        and n.id in bindings
                        and n.id != local
                        and n.id not in loop_names
                        for n in ast.walk(node)
                    ):
                        unsafe = True
                        break
                # Only module imports and this app are statically bound here.
                candidate = Rename().visit(copy.deepcopy(node))
                if node is constructors[0]:
                    ast.copy_location(candidate, statement)
                projected.append(candidate)
        body.extend([statement] if unsafe else projected)
    return ast.Module(body=body, type_ignores=tree.type_ignores)


def registration_statements(
    body: Sequence[ast.stmt], frame: dict[str, str | None], *, budget: int = 256
) -> Iterator[tuple[ast.Expr, dict[str, str | None]]]:
    """Expand only finite list/tuple loops containing registration expressions."""
    remaining = [budget]

    def visit(statements, bindings):
        for statement in statements:
            if isinstance(statement, ast.Expr):
                if remaining[0] <= 0:
                    return
                remaining[0] -= 1
                yield statement, bindings
            elif (
                isinstance(statement, ast.For)
                and isinstance(statement.target, ast.Name)
                and isinstance(statement.iter, (ast.Tuple, ast.List))
                and not statement.orelse
                and all(isinstance(n, ast.Expr) for n in statement.body)
                and len(statement.iter.elts) <= remaining[0]
            ):
                targets = [_qualified(node, [bindings]) for node in statement.iter.elts]
                if any(target is None for target in targets):
                    continue
                for target in targets:
                    yield from visit(
                        statement.body, bindings | {statement.target.id: target}
                    )

    yield from visit(body, frame)
