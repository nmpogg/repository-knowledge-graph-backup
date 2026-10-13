"""Static SQLAlchemy 2.x mapping and data-access extraction.

The adapter reads parsed Python only. It never imports analyzed modules. A table
or operation that is not a supported literal pattern becomes a diagnostic and
never a guessed graph relationship.
"""

from __future__ import annotations

import ast
import copy
from collections import defaultdict
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, replace
from pathlib import PurePosixPath

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
from rkg.adapters.python_language import _module_name, _unique_definitions
from rkg.adapters.python_resolution import _bindings, _frames, _Module, _qualified
from rkg.domain import (
    Diagnostic,
    Edge,
    EdgeType,
    Entity,
    EntityType,
    Evidence,
    FactBatch,
    Severity,
    data_resource_id,
    diagnostic_id,
    edge_id,
    evidence_id,
    source_entity_id,
)
from rkg.ingestion import SourceManifest

MAP_RULE = "RKG.sqlalchemy.maps_to.v1"
DETECT_RULE = "RKG.sqlalchemy.detect_import.v1"
OPERATION_RULES = {
    "get": "RKG.sqlalchemy.get.v1",
    "select": "RKG.sqlalchemy.select.v1",
    "insert": "RKG.sqlalchemy.insert.v1",
    "update": "RKG.sqlalchemy.update.v1",
    "delete": "RKG.sqlalchemy.delete.v1",
    "add": "RKG.sqlalchemy.add.v1",
}
READ_OPERATIONS = frozenset({"get", "select"})
SQL_OPERATIONS = frozenset({"select", "insert", "update", "delete"})
EXECUTORS = frozenset({"execute", "scalars", "scalar"})
DECLARATIVE_BASES = frozenset(
    {
        "sqlalchemy.orm.DeclarativeBase",
        "sqlalchemy.orm.decl_api.DeclarativeBase",
    }
)
DECLARATIVE_FACTORIES = frozenset(
    {
        "sqlalchemy.orm.declarative_base",
        "sqlalchemy.orm.decl_api.declarative_base",
    }
)
TABLE_CALLS = frozenset({"sqlalchemy.Table", "sqlalchemy.sql.schema.Table"})
AUTOMAP_CALLS = frozenset({"sqlalchemy.ext.automap.automap_base"})
_MESSAGES = {
    "sqlalchemy_table_dynamic": "Table identity is dynamic or reflected.",
    "sqlalchemy_model_unresolved": "Data model could not be resolved.",
    "sqlalchemy_operation_unresolved": "Data operation could not be resolved.",
    "sqlalchemy_operation_not_executed": (
        "Declared data operation has no execution evidence."
    ),
    "sqlalchemy_operation_unscoped": "Data operation is outside a callable.",
}


@dataclass(frozen=True, slots=True)
class _Model:
    qualified_name: str
    path: str
    line: int
    table: str
    namespace: str
    type_id: str


@dataclass(frozen=True, slots=True)
class _Prepared:
    module: _Module
    frame: dict[str, str | None]
    definitions: dict[
        str, tuple[str, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef]
    ]
    factories: frozenset[str]


def _literal(node: ast.expr | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _single_assign(statement: ast.stmt) -> tuple[str, ast.expr, int] | None:
    if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
        target = statement.targets[0]
        if isinstance(target, ast.Name):
            return target.id, statement.value, statement.lineno
    if (
        isinstance(statement, ast.AnnAssign)
        and isinstance(statement.target, ast.Name)
        and statement.value is not None
    ):
        return statement.target.id, statement.value, statement.lineno
    return None


def _iter_calls(statements: Sequence[ast.stmt]) -> Iterator[ast.Call]:
    """Yield calls outside nested functions; class bodies stay in scope."""
    stack: list[ast.AST] = list(reversed(statements))
    while stack:
        node = stack.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            continue
        if isinstance(node, ast.ClassDef):
            stack.extend(reversed(node.body))
            continue
        if isinstance(node, ast.Call):
            yield node
        stack.extend(reversed(list(ast.iter_child_nodes(node))))


def _local_roots(parsed: ParseResult) -> set[str]:
    roots: set[str] = set()
    for unit in parsed.units:
        if not isinstance(unit.representation, ast.Module):
            continue
        pure = PurePosixPath(unit.relative_path)
        roots.update((pure.stem, _module_name(unit.relative_path).split(".")[0]))
        if pure.stem == "__init__" and len(pure.parts) > 1:
            roots.add(pure.parts[-2])
    return roots


def _dict_schema(node: ast.Dict) -> str | None:
    found: str | None = None
    seen = False
    for key, value in zip(node.keys, node.values, strict=True):
        if not isinstance(key, ast.Constant) or key.value != "schema":
            continue
        if seen:
            return None
        seen = True
        if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
            return None
        found = value.value
    return found or ""


def _schema(node: ast.expr) -> str | None:
    """Return ``""`` when schema is omitted, or None when it is not static."""
    if isinstance(node, ast.Dict):
        return _dict_schema(node)
    if isinstance(node, (ast.Tuple, ast.List)):
        if any(isinstance(item, ast.Starred) for item in node.elts):
            return None
        schemas = []
        for item in node.elts:
            if not isinstance(item, ast.Dict):
                continue
            value = _dict_schema(item)
            if value is None:
                return None
            if value:
                schemas.append(value)
        if len(set(schemas)) > 1:
            return None
        return schemas[0] if schemas else ""
    return None


def _sql_operation(
    expression: ast.expr, frames: Sequence[dict[str, str | None]]
) -> str | None:
    name = _qualified(expression, frames)
    if not name or not name.startswith("sqlalchemy."):
        return None
    operation = name.rsplit(".", 1)[-1]
    if operation in SQL_OPERATIONS:
        return operation
    return None


def _reflection(call: ast.Call, frames: Sequence[dict[str, str | None]]) -> bool:
    name = _qualified(call.func, frames)
    if name in AUTOMAP_CALLS:
        return True
    return name in TABLE_CALLS and any(
        item.arg in {"autoload", "autoload_with"} for item in call.keywords
    )


def _peel_sql(
    expression: ast.expr, frames: Sequence[dict[str, str | None]]
) -> ast.Call | None:
    seen: set[int] = set()
    node: ast.expr = expression
    while id(node) not in seen and isinstance(node, ast.Call):
        seen.add(id(node))
        if _sql_operation(node.func, frames):
            return node
        if isinstance(node.func, ast.Attribute):
            node = node.func.value
            continue
        return None
    return None


def _class_model(
    expression: ast.expr,
    frames: Sequence[dict[str, str | None]],
    mapped: dict[str, _Model],
) -> _Model | None:
    if not isinstance(expression, (ast.Name, ast.Attribute)):
        return None
    name = _qualified(expression, frames)
    return mapped.get(name) if name else None


def _reference_model(
    expression: ast.expr,
    frames: Sequence[dict[str, str | None]],
    mapped: dict[str, _Model],
) -> _Model | None:
    model = _class_model(expression, frames, mapped)
    if model is not None or not isinstance(expression, ast.Attribute):
        return model
    parent = _qualified(expression.value, frames)
    return mapped.get(parent) if parent else None


class _Flow(ast.NodeVisitor):
    """Unique assignments and annotations inside one callable."""

    def __init__(self) -> None:
        self.stores: dict[str, int] = defaultdict(int)
        self.values: dict[str, list[ast.expr]] = defaultdict(list)
        self.annotations: dict[str, list[ast.expr]] = defaultdict(list)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.stores[node.name] += 1

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.stores[node.name] += 1

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.stores[node.name] += 1

    def visit_Lambda(self, node: ast.Lambda) -> None:
        del node

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Store):
            self.stores[node.id] += 1

    def visit_Assign(self, node: ast.Assign) -> None:
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            self.stores[node.targets[0].id] += 1
            self.values[node.targets[0].id].append(node.value)
            self.visit(node.value)
            return
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if isinstance(node.target, ast.Name):
            if node.annotation is not None:
                self.annotations[node.target.id].append(node.annotation)
            if node.value is not None:
                self.stores[node.target.id] += 1
                self.values[node.target.id].append(node.value)
                self.visit(node.value)
            if node.annotation is not None:
                self.visit(node.annotation)
            return
        self.generic_visit(node)


def _instance_model(
    expression: ast.expr,
    flow: _Flow,
    frames: Sequence[dict[str, str | None]],
    mapped: dict[str, _Model],
    owner: _Model | None,
) -> _Model | None:
    if isinstance(expression, ast.Call):
        return _class_model(expression.func, frames, mapped)
    if not isinstance(expression, ast.Name):
        return None
    notes = flow.annotations.get(expression.id, [])
    note = _class_model(notes[0], frames, mapped) if len(notes) == 1 else None
    if len(notes) > 1 or (len(notes) == 1 and note is None):
        return None
    values = flow.values.get(expression.id, [])
    constructed = None
    if len(values) == 1 and flow.stores[expression.id] == 1:
        value = values[0]
        if isinstance(value, ast.Call):
            constructed = _class_model(value.func, frames, mapped)
        elif note is None:
            return None
    elif values:
        return None
    if (
        constructed is not None
        and note is not None
        and constructed.qualified_name != note.qualified_name
    ):
        return None
    if constructed is not None:
        return constructed
    if note is not None and flow.stores[expression.id] == 0:
        return note
    if (
        expression.id in {"self", "cls"}
        and flow.stores[expression.id] == 0
        and owner is not None
    ):
        return owner
    return None


class _Facts:
    def __init__(self, context: AdapterContext, base: FactBatch) -> None:
        self.context = context
        self.entities = {item.id: item for item in base.entities}
        self.edges = {item.id: item for item in base.edges}
        self.evidence = {item.id: item for item in base.evidence}
        self.diagnostics = list(base.diagnostics)
        self.issues: set[tuple[str, str, int]] = set()

    def issue(self, code: str, path: str, line: int) -> None:
        self.issues.add((code, path, line))

    def relate(
        self,
        kind: EdgeType,
        source: str,
        target: str,
        path: str,
        line: int,
        rule: str,
    ) -> None:
        ref = evidence_id(self.context.snapshot_id, path, line, line, rule)
        self.evidence[ref] = Evidence(
            ref, self.context.snapshot_id, path, line, line, rule
        )
        key = edge_id(self.context.snapshot_id, kind, source, target)
        current = self.edges.get(key)
        references = set(current.evidence_ids) if current else set()
        references.add(ref)
        chosen = min(rule, current.rule) if current else rule
        self.edges[key] = Edge(
            key,
            self.context.snapshot_id,
            kind,
            source,
            target,
            chosen,
            tuple(sorted(references)),
        )

    def finish(self) -> tuple[FactBatch, tuple[AdapterDiagnostic, ...]]:
        issues = tuple(sorted(self.issues))
        for ordinal, (code, path, line) in enumerate(issues):
            self.diagnostics.append(
                Diagnostic(
                    diagnostic_id(self.context.job_id, code, path, line, ordinal),
                    self.context.job_id,
                    Severity.WARNING,
                    code,
                    _MESSAGES[code],
                    self.context.snapshot_id,
                    path,
                    line,
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
            tuple(AdapterDiagnostic(code, path, line) for code, path, line in issues),
        )


def _resource_qualified(namespace: str, table: str) -> str:
    return f"sqlalchemy:{namespace}:{table}"


def _prepare(parsed: ParseResult) -> list[_Prepared]:
    prepared = []
    for unit in parsed.units:
        tree = unit.representation
        if not isinstance(tree, ast.Module):
            continue
        module = _Module(unit.relative_path, _module_name(unit.relative_path), tree)
        frame = dict(_bindings(module, tree.body, module.name))
        factories: set[str] = set()
        for statement in tree.body:
            assigned = _single_assign(statement)
            if assigned is None or not isinstance(assigned[1], ast.Call):
                continue
            if _qualified(assigned[1].func, [frame]) not in DECLARATIVE_FACTORIES:
                continue
            qualified = f"{module.name}.{assigned[0]}"
            frame[assigned[0]] = qualified
            factories.add(qualified)
        definitions, _ = _unique_definitions(tree, module.name, module.path)
        prepared.append(
            _Prepared(
                module,
                frame,
                {name: (owner, node) for owner, name, node in definitions},
                frozenset(factories),
            )
        )
    return prepared


def _declarative_names(prepared: Sequence[_Prepared]) -> set[str]:
    classes: list[tuple[str, tuple[str | None, ...]]] = []
    for item in prepared:
        for name, (owner, node) in item.definitions.items():
            if owner != item.module.name or not isinstance(node, ast.ClassDef):
                continue
            if item.frame.get(node.name) != name:
                continue
            classes.append(
                (
                    name,
                    tuple(_qualified(base, [item.frame]) for base in node.bases),
                )
            )
    known = set(DECLARATIVE_BASES)
    known.update(name for item in prepared for name in item.factories)
    changed = True
    while changed:
        changed = False
        for name, bases in classes:
            if name in known:
                continue
            if any(base in known for base in bases):
                known.add(name)
                changed = True
    return known


def _table_info(
    node: ast.ClassDef, frames: Sequence[dict[str, str | None]]
) -> tuple[str | None, str | None, int, bool]:
    """Return table, namespace, line and whether the declaration is unusable."""
    found: dict[str, list[tuple[ast.expr, int]]] = defaultdict(list)
    for statement in node.body:
        assigned = _single_assign(statement)
        if assigned and assigned[0] in {
            "__tablename__",
            "__table_args__",
            "__table__",
        }:
            found[assigned[0]].append((assigned[1], assigned[2]))
    reflected = any(_reflection(call, frames) for call in _iter_calls(node.body))
    names = found["__tablename__"]
    if len(names) != 1:
        return None, None, node.lineno, reflected or bool(names)
    table = _literal(names[0][0])
    line = names[0][1]
    if not table:
        return None, None, line, True
    schemas = found["__table_args__"]
    if not schemas:
        return table, "", line, reflected
    if len(schemas) != 1:
        return None, None, line, True
    namespace = _schema(schemas[0][0])
    if namespace is None:
        return None, None, line, True
    return table, namespace, line, reflected


def _models(
    context: AdapterContext,
    prepared: Sequence[_Prepared],
    declarative: set[str],
    facts: _Facts,
) -> dict[str, _Model]:
    models: dict[str, _Model] = {}
    for item in prepared:
        for name, (owner, node) in sorted(item.definitions.items()):
            if (
                owner != item.module.name
                or not isinstance(node, ast.ClassDef)
                or name not in declarative
                or item.frame.get(node.name) != name
            ):
                continue
            table, namespace, line, rejected = _table_info(node, [item.frame])
            if rejected or table is None or namespace is None:
                if rejected or table is not None or namespace is not None:
                    facts.issue("sqlalchemy_table_dynamic", item.module.path, line)
                continue
            type_id = source_entity_id(
                context.repository_id, item.module.path, EntityType.TYPE, name
            )
            if type_id not in facts.entities:
                facts.issue("sqlalchemy_model_unresolved", item.module.path, line)
                continue
            models[name] = _Model(
                name, item.module.path, line, table, namespace, type_id
            )
    return models


def _emit_maps(
    context: AdapterContext, models: dict[str, _Model], facts: _Facts
) -> None:
    grouped: dict[tuple[str, str], list[_Model]] = defaultdict(list)
    for model in models.values():
        grouped[(model.namespace, model.table)].append(model)
    for (namespace, table), grouped_models in sorted(grouped.items()):
        ordered = sorted(
            grouped_models,
            key=lambda item: (item.path, item.line, item.qualified_name),
        )
        first = ordered[0]
        identifier = data_resource_id(
            context.repository_id, "table", namespace, ("rkg.sqlalchemy", table)
        )
        facts.entities[identifier] = Entity(
            identifier,
            context.repository_id,
            context.snapshot_id,
            EntityType.DATA_RESOURCE,
            table,
            _resource_qualified(namespace, table),
            first.path,
            first.line,
            first.line,
            framework_kind="sqlalchemy",
            attributes=(
                ("namespace", namespace),
                ("resource_kind", "table"),
                ("table", table),
            ),
        )
        for model in ordered:
            facts.relate(
                EdgeType.MAPS_TO,
                model.type_id,
                identifier,
                model.path,
                model.line,
                MAP_RULE,
            )


def _operation_models(
    call: ast.Call,
    operation: str,
    frames: Sequence[dict[str, str | None]],
    mapped: dict[str, _Model],
) -> tuple[_Model, ...] | None:
    if call.keywords or not call.args:
        return None
    reader = _reference_model if operation == "select" else _class_model
    models = [reader(arg, frames, mapped) for arg in call.args]
    if any(model is None for model in models):
        return None
    return tuple(model for model in models if model is not None)


def _first_argument(call: ast.Call, names: set[str]) -> ast.expr | None:
    if any(item.arg is None for item in call.keywords):
        return None
    if call.args:
        return call.args[0]
    matches = [item.value for item in call.keywords if item.arg in names]
    return matches[0] if len(matches) == 1 else None


def _bound_sql(
    expression: ast.expr,
    flow: _Flow,
    frames: Sequence[dict[str, str | None]],
) -> ast.Call | None:
    peeled = _peel_sql(expression, frames)
    if peeled is not None:
        return peeled
    while isinstance(expression, ast.Call) and isinstance(
        expression.func, ast.Attribute
    ):
        if expression.func.attr not in {
            "where",
            "filter",
            "options",
            "with_for_update",
            "execution_options",
            "order_by",
            "offset",
            "limit",
            "join",
            "outerjoin",
        }:
            return None
        expression = expression.func.value
    if not isinstance(expression, ast.Name):
        return None
    values = flow.values.get(expression.id, [])
    if not values or flow.stores[expression.id] != len(values):
        return None
    original = _peel_sql(values[0], frames)
    if original is None:
        return None
    for value in values[1:]:
        while isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute):
            if value.func.attr not in {
                "where",
                "filter",
                "options",
                "with_for_update",
                "execution_options",
                "order_by",
                "offset",
                "limit",
                "join",
                "outerjoin",
            }:
                return None
            value = value.func.value
        if not isinstance(value, ast.Name) or value.id != expression.id:
            return None
    return original


def _emit_access(
    facts: _Facts,
    caller_id: str,
    model: _Model,
    operation: str,
    path: str,
    line: int,
) -> None:
    identifier = data_resource_id(
        facts.context.repository_id,
        "table",
        model.namespace,
        ("rkg.sqlalchemy", model.table),
    )
    facts.relate(
        EdgeType.READS if operation in READ_OPERATIONS else EdgeType.WRITES,
        caller_id,
        identifier,
        path,
        line,
        OPERATION_RULES[operation],
    )


def _scan_callable(
    item: _Prepared,
    qualified_name: str,
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    mapped: dict[str, _Model],
    facts: _Facts,
) -> None:
    caller_id = source_entity_id(
        facts.context.repository_id,
        item.module.path,
        EntityType.CALLABLE,
        qualified_name,
    )
    if caller_id not in facts.entities:
        return
    frames = _frames(qualified_name, item.module, item.definitions, item.frame)
    owner_name = item.definitions[qualified_name][0]
    flow = _Flow()
    for argument in (
        *node.args.posonlyargs,
        *node.args.args,
        *node.args.kwonlyargs,
    ):
        if argument.annotation is not None:
            flow.annotations[argument.arg].append(argument.annotation)
    for statement in node.body:
        flow.visit(statement)
    executed: set[int] = set()
    calls = tuple(_iter_calls(node.body))
    for call in calls:
        if _reflection(call, frames):
            facts.issue("sqlalchemy_table_dynamic", item.module.path, call.lineno)
        if not isinstance(call.func, ast.Attribute):
            continue
        attr = call.func.attr
        if attr == "get":
            argument = _first_argument(call, {"entity"})
            model = (
                _class_model(argument, frames, mapped) if argument is not None else None
            )
            if model is not None:
                _emit_access(
                    facts, caller_id, model, "get", item.module.path, call.lineno
                )
            elif argument is not None and not isinstance(argument, ast.Constant):
                facts.issue(
                    "sqlalchemy_model_unresolved", item.module.path, call.lineno
                )
            continue
        if attr in {"add", "delete"}:
            argument = _first_argument(call, {"instance"})
            model = (
                _instance_model(argument, flow, frames, mapped, mapped.get(owner_name))
                if argument is not None
                else None
            )
            if model is not None:
                _emit_access(
                    facts, caller_id, model, attr, item.module.path, call.lineno
                )
            elif argument is not None and not isinstance(argument, ast.Constant):
                facts.issue(
                    "sqlalchemy_model_unresolved", item.module.path, call.lineno
                )
            continue
        if attr not in EXECUTORS:
            continue
        argument = _first_argument(call, {"statement"})
        if argument is None:
            continue
        sql = _bound_sql(argument, flow, frames)
        if sql is None:
            if isinstance(argument, ast.Name) and any(
                _peel_sql(value, frames) for value in flow.values.get(argument.id, [])
            ):
                facts.issue(
                    "sqlalchemy_operation_unresolved", item.module.path, call.lineno
                )
            continue
        executed.add(id(sql))
        operation = _sql_operation(sql.func, frames)
        models = (
            _operation_models(sql, operation, frames, mapped)
            if operation is not None
            else None
        )
        if not models:
            facts.issue("sqlalchemy_model_unresolved", item.module.path, call.lineno)
            continue
        for model in models:
            _emit_access(
                facts, caller_id, model, operation, item.module.path, call.lineno
            )
    for call in calls:
        operation = _sql_operation(call.func, frames)
        if operation and id(call) not in executed:
            facts.issue(
                "sqlalchemy_operation_not_executed", item.module.path, call.lineno
            )


def _scan_module(item: _Prepared, facts: _Facts) -> None:
    for call in _iter_calls(item.module.tree.body):
        if _reflection(call, [item.frame]):
            facts.issue("sqlalchemy_table_dynamic", item.module.path, call.lineno)
        elif _sql_operation(call.func, [item.frame]):
            facts.issue("sqlalchemy_operation_unscoped", item.module.path, call.lineno)


def _extract(context: AdapterContext, parsed: ParseResult, facts: _Facts) -> None:
    if "sqlalchemy" in _local_roots(parsed):
        return
    prepared = _prepare(parsed)
    declarative = _declarative_names(prepared)
    models = _models(context, prepared, declarative, facts)
    _emit_maps(context, models, facts)
    for item in prepared:
        _scan_module(item, facts)
        for name, (owner, node) in sorted(item.definitions.items()):
            del owner
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                _scan_callable(item, name, node, models, facts)
    _generic_receiver_access(context, parsed, prepared, models, facts)


def _generic_receiver_access(context, parsed, prepared, models, facts):
    """Bind a generic repository model at its caller, never on a shared method.

    Both the generic base annotation and its explicit super-constructor argument
    must identify the same model. Evidence stays at the concrete call site.
    """
    from rkg.adapters.python_resolution import _Index, _scope_statements
    from rkg.adapters.python_types import StaticTypes

    base = FactBatch(
        context.repository_id,
        context.snapshot_id,
        tuple(facts.entities.values()),
        (),
        (),
    )
    types = StaticTypes(_Index(parsed, base))
    classes = {
        name: (item, node)
        for item in prepared
        for name, (_, node) in item.definitions.items()
        if isinstance(node, ast.ClassDef)
    }

    def model_parameter(init, generic):
        if (
            sum(
                isinstance(n, ast.Attribute)
                and isinstance(n.ctx, ast.Store)
                and n.attr == "model"
                for n in ast.walk(init)
            )
            != 1
        ):
            return None
        model_param = None
        for statement, conditional in _scope_statements(init.body):
            if (
                conditional
                or not isinstance(statement, ast.Assign)
                or len(statement.targets) != 1
            ):
                continue
            target, value = statement.targets[0], statement.value
            pairs = (
                zip(target.elts, value.elts)
                if isinstance(target, ast.Tuple)
                and isinstance(value, ast.Tuple)
                and len(target.elts) == len(value.elts)
                else [(target, value)]
            )
            for target, value in pairs:
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                    and target.attr == "model"
                    and isinstance(value, ast.Name)
                ):
                    arg = next((a for a in init.args.args if a.arg == value.id), None)
                    if (
                        arg
                        and isinstance(arg.annotation, ast.Subscript)
                        and isinstance(arg.annotation.slice, ast.Name)
                        and arg.annotation.slice.id == generic
                    ):
                        model_param = value.id
        return model_param

    specialized = {}
    for name, (item, node) in classes.items():
        if len(node.bases) != 1 or not isinstance(node.bases[0], ast.Subscript):
            continue
        inherited = node.bases[0]
        parent = _qualified(inherited.value, [item.frame])
        model = _class_model(inherited.slice, [item.frame], models)
        parent_class = classes.get(parent)
        if model is None or parent_class is None:
            continue
        parent_item, parent_node = parent_class
        params = getattr(parent_node, "type_params", [])
        if len(params) != 1:
            continue
        generic = params[0].name
        init = next(
            (
                n
                for n in parent_node.body
                if isinstance(n, ast.FunctionDef) and n.name == "__init__"
            ),
            None,
        )
        child_init = next(
            (
                n
                for n in node.body
                if isinstance(n, ast.FunctionDef) and n.name == "__init__"
            ),
            None,
        )
        if init is None or child_init is None:
            continue
        model_param = model_parameter(init, generic)
        if model_param is None:
            continue
        # Reject a child overriding the model field, even conditionally.
        if any(
            isinstance(n, ast.Attribute)
            and isinstance(n.ctx, ast.Store)
            and n.attr == "model"
            for n in ast.walk(node)
        ):
            continue
        calls = [
            n.value
            for n in child_init.body
            if isinstance(n, ast.Expr)
            and isinstance(n.value, ast.Call)
            and isinstance(n.value.func, ast.Attribute)
            and n.value.func.attr == "__init__"
            and isinstance(n.value.func.value, ast.Call)
            and isinstance(n.value.func.value.func, ast.Name)
            and n.value.func.value.func.id == "super"
        ]
        if len(calls) != 1:
            continue
        args = {p.arg: a for p, a in zip(init.args.args[1:], calls[0].args)}
        args.update({k.arg: k.value for k in calls[0].keywords if k.arg})
        bound = args.get(model_param)
        if bound is None or _class_model(bound, [item.frame], models) != model:
            continue
        specialized[name] = (parent, generic, model, parent_item)

    cache = {}
    for name, scope in types.scopes.items():
        caller = types.index.unique(name, frozenset({EntityType.CALLABLE}))
        if caller is None:
            continue
        for call in scope.calls:
            if not isinstance(call.func, ast.Attribute):
                continue
            receiver = types.expression(name, call.func.value)
            spec = specialized.get(receiver)
            if spec is None and receiver in classes:
                parent_item, parent_node = classes[receiver]
                generic_params = getattr(parent_node, "type_params", [])
                init = next(
                    (
                        n
                        for n in parent_node.body
                        if isinstance(n, ast.FunctionDef) and n.name == "__init__"
                    ),
                    None,
                )
                if len(generic_params) == 1 and init is not None:
                    generic = generic_params[0].name
                    model_param = model_parameter(init, generic)
                    expression = call.func.value
                    constructor_scope = scope
                    if isinstance(expression, ast.Name):
                        expression = scope.values.get(expression.id)
                    elif isinstance(expression, ast.Attribute):
                        owner = types.expression(name, expression.value)
                        values = types.attributes.get((owner, expression.attr), [])
                        if len(values) == 1:
                            constructor_name, expression = values[0]
                            constructor_scope = types.scopes[constructor_name]
                    if model_param and isinstance(expression, ast.Call):
                        args = {
                            p.arg: a
                            for p, a in zip(init.args.args[1:], expression.args)
                        }
                        args.update(
                            {k.arg: k.value for k in expression.keywords if k.arg}
                        )
                        argument = args.get(model_param)
                        model = (
                            _class_model(argument, constructor_scope.frames, models)
                            if argument
                            else None
                        )
                        if model is not None:
                            spec = (receiver, generic, model, parent_item)
            target = types.call_target(name, call)
            if spec is None or target is None:
                continue
            parent, generic, model, item = spec
            target_def = item.definitions.get(target.qualified_name)
            if target_def is None or target_def[0] != parent:
                continue
            key = (target.id, model.qualified_name)
            if key not in cache:

                class Bind(ast.NodeTransformer):
                    def visit_Attribute(self, node):
                        if (
                            isinstance(node.value, ast.Name)
                            and node.value.id == "self"
                            and node.attr == "model"
                        ):
                            return ast.copy_location(
                                ast.Name(id="__rkg_model", ctx=node.ctx), node
                            )
                        return self.generic_visit(node)

                    def visit_Name(self, node):
                        if node.id == generic:
                            return ast.copy_location(
                                ast.Name(id="__rkg_model", ctx=node.ctx), node
                            )
                        return node

                cloned = Bind().visit(copy.deepcopy(target_def[1]))
                scratch = _Facts(context, base)
                bound_item = replace(
                    item, frame=item.frame | {"__rkg_model": model.qualified_name}
                )
                _scan_callable(
                    bound_item, target.qualified_name, cloned, models, scratch
                )
                # A typed ORM object explicitly mutated then flushed is a write.
                model_args = {
                    arg.arg
                    for arg in (*cloned.args.args, *cloned.args.kwonlyargs)
                    if arg.annotation is not None
                    and _class_model(arg.annotation, [bound_item.frame], models)
                    == model
                }
                calls = tuple(_iter_calls(cloned.body))
                flushed = any(
                    isinstance(c.func, ast.Attribute)
                    and c.func.attr == "flush"
                    and isinstance(c.func.value, ast.Attribute)
                    and c.func.value.attr == "session"
                    and isinstance(c.func.value.value, ast.Name)
                    and c.func.value.value.id == "self"
                    for c in calls
                )
                modified = any(
                    isinstance(c.func, ast.Name)
                    and c.func.id == "setattr"
                    and c.args
                    and isinstance(c.args[0], ast.Name)
                    and c.args[0].id in model_args
                    for c in calls
                )
                target_frames = _frames(
                    target.qualified_name, item.module, item.definitions, item.frame
                )
                if (
                    flushed
                    and modified
                    and not any("setattr" in f for f in target_frames)
                ):
                    resource = data_resource_id(
                        context.repository_id,
                        "table",
                        model.namespace,
                        ("rkg.sqlalchemy", model.table),
                    )
                    scratch.relate(
                        EdgeType.WRITES,
                        target.id,
                        resource,
                        item.module.path,
                        cloned.lineno,
                        "RKG.sqlalchemy.mutation.v1",
                    )
                cache[key] = tuple(
                    edge
                    for edge in scratch.edges.values()
                    if edge.type in {EdgeType.READS, EdgeType.WRITES}
                    and edge.source_id == target.id
                )
            for edge in cache[key]:
                facts.relate(
                    edge.type,
                    caller.id,
                    edge.target_id,
                    scope.module.path,
                    call.lineno,
                    "RKG.sqlalchemy.bound_receiver.v1",
                )
                facts.relate(
                    edge.type,
                    caller.id,
                    edge.target_id,
                    item.module.path,
                    target.start_line,
                    "RKG.sqlalchemy.bound_receiver.v1",
                )


class SQLAlchemyDataAccessAdapter:
    """Extract the supported SQLAlchemy 2.x table, read and write profile."""

    allow_unverified_versions = True

    entrypoint_required = False
    descriptor = AdapterDescriptor(
        adapter_id="rkg.sqlalchemy",
        adapter_version="2.1.0",
        contract_version=CONTRACT_VERSION,
        kind=AdapterKind.DATA_ACCESS,
        language="python",
        framework="sqlalchemy",
        grammar_or_target="SQLAlchemy 2.x supported subset",
        file_patterns=("*.py", "**/*.py"),
        ignore_patterns=("**/__pycache__/**",),
        capabilities=("maps-to", "reads", "tables", "writes"),
        technology_constraints=(TechnologyConstraint("sqlalchemy", ">=2.0,<3.0"),),
    )

    def detect(self, manifest: SourceManifest, parsed: ParseResult) -> DetectionReport:
        del manifest
        if "sqlalchemy" in _local_roots(parsed):
            return DetectionReport()
        evidence: set[DetectionEvidence] = set()
        for unit in parsed.units:
            tree = unit.representation
            if not isinstance(tree, ast.Module):
                continue
            for node in ast.walk(tree):
                imported = False
                if isinstance(node, ast.Import):
                    imported = any(
                        alias.name.split(".")[0] == "sqlalchemy" for alias in node.names
                    )
                elif (
                    isinstance(node, ast.ImportFrom)
                    and node.level == 0
                    and node.module
                    and node.module.split(".")[0] == "sqlalchemy"
                ):
                    imported = True
                if imported:
                    evidence.add(DetectionEvidence(unit.relative_path, DETECT_RULE))
        references = tuple(
            sorted(evidence, key=lambda item: (item.relative_path, item.rule_id))
        )
        if not references:
            return DetectionReport()
        return DetectionReport((TechnologyDetection("sqlalchemy", None, references),))

    def extract(
        self, context: AdapterContext, parsed: ParseResult, base: FactBatch
    ) -> AdapterResult:
        if (
            base.repository_id != context.repository_id
            or base.snapshot_id != context.snapshot_id
        ):
            raise ValueError("candidate ownership does not match adapter context")
        facts = _Facts(context, base)
        _extract(context, parsed, facts)
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
            Capability(name, SupportState.SUPPORTED)
            for name in SQLAlchemyDataAccessAdapter.descriptor.capabilities
        )
