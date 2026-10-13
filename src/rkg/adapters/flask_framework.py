"""Static Flask route extraction over parsed Python AST.

The adapter never imports or executes analyzed modules. A route is recorded only
when the registration, method, path and handler are static. Anything else is a
fixed diagnostic with a relative path and line.
"""

from __future__ import annotations

import ast
from collections import defaultdict
from dataclasses import dataclass
from pathlib import PurePosixPath

from rkg.adapters.contracts import (
    CONTRACT_VERSION,
    AdapterContext,
    AdapterDescriptor,
    AdapterDiagnostic,
    AdapterKind,
    AdapterResult,
    Capability,
    DetectionReport,
    ParseResult,
    SupportState,
)
from rkg.adapters.python_language import _module_name, _unique_definitions
from rkg.adapters.python_resolution import _bindings, _Module, _qualified
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

ROUTE_RULE = "RKG.flask.route.v1"
HANDLER_RULE = "RKG.flask.handler.v1"
DEPENDENCY_RULE = "RKG.flask.dependency.v1"
_SHORTCUTS = {
    "get": ("GET",),
    "post": ("POST",),
    "put": ("PUT",),
    "patch": ("PATCH",),
    "delete": ("DELETE",),
    "head": ("HEAD",),
    "options": ("OPTIONS",),
}
_ROUTE_ATTRS = frozenset({"route", *_SHORTCUTS})
_MESSAGES = {
    "flask_app_ambiguous": "Application selection is required.",
    "flask_app_unresolved": "Application entrypoint could not be resolved.",
    "flask_route_dynamic": "Route path, method or handler is not static.",
    "flask_blueprint_unresolved": "Blueprint registration could not be resolved.",
    "flask_blueprint_cycle": "Blueprint registration cycle was skipped.",
    "flask_dependency_unresolved": "Route dependency could not be resolved.",
}


@dataclass(frozen=True, slots=True)
class _Location:
    path: str
    line: int


@dataclass(frozen=True, slots=True)
class _Node:
    name: str
    kind: str
    prefix: str
    location: _Location


@dataclass(frozen=True, slots=True)
class _Include:
    owner: str
    blueprint: str
    prefix: str
    location: _Location


@dataclass(frozen=True, slots=True)
class _Route:
    owner: str
    handler: str
    path: str
    methods: tuple[str, ...]
    dependencies: tuple[tuple[str, _Location], ...]
    location: _Location


def _literal(node: ast.expr | None) -> str | None:
    return (
        node.value
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
        else None
    )


def _keyword(node: ast.Call, name: str) -> ast.expr | None:
    return next((item.value for item in node.keywords if item.arg == name), None)


def _path(prefix: str, route: str) -> str:
    if not prefix:
        return route
    return prefix.rstrip("/") + (route if route.startswith("/") else "/" + route)


def _methods(node: ast.expr | None) -> tuple[str, ...] | None:
    if not isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return None
    values = [_literal(item) for item in node.elts]
    if not values or any(value is None or not value.isalpha() for value in values):
        return None
    return tuple(sorted({value.upper() for value in values if value}))


def _static_path(node: ast.expr | None) -> str | None:
    value = _literal(node)
    if value is None or not value.startswith("/"):
        return None
    return value


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
                set(self.issues),
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
        return FactBatch(
            self.context.repository_id,
            self.context.snapshot_id,
            tuple(self.entities[key] for key in sorted(self.entities)),
            tuple(self.edges[key] for key in sorted(self.edges)),
            tuple(self.evidence[key] for key in sorted(self.evidence)),
            tuple(self.diagnostics),
        ), issues


class FlaskFrameworkAdapter:
    """Extract static Flask routes. Not a reviewed deep-supported profile."""

    entrypoint_required = True
    reviewed_deep_support = False
    descriptor = AdapterDescriptor(
        adapter_id="rkg.flask",
        adapter_version="2.0.0",
        contract_version=CONTRACT_VERSION,
        kind=AdapterKind.FRAMEWORK,
        language="python",
        framework="flask",
        grammar_or_target="CPython 3.12 AST",
        file_patterns=("*.py", "**/*.py"),
        ignore_patterns=("**/__pycache__/**",),
        capabilities=("app", "routes"),
    )

    def __init__(self, application: str | None = None) -> None:
        self.application = application

    def for_application(self, reference: str) -> FlaskFrameworkAdapter:
        """Bind a selected entrypoint without mutating the registered adapter."""
        return FlaskFrameworkAdapter(reference)

    def technology_detectors(self) -> tuple[object, ...]:
        from rkg.detection.flask import FlaskAppDetector

        return (FlaskAppDetector(),)

    def detect(self, manifest: SourceManifest, parsed: ParseResult) -> DetectionReport:
        from rkg.detection.flask import FlaskAppDetector

        observation = FlaskAppDetector().detect(manifest, parsed)
        return DetectionReport(
            observation.report.technologies,
            tuple(item.reference for item in observation.applications),
        )

    def extract(
        self, context: AdapterContext, parsed: ParseResult, base: FactBatch
    ) -> AdapterResult:
        if (
            base.repository_id != context.repository_id
            or base.snapshot_id != context.snapshot_id
        ):
            raise ValueError("candidate ownership does not match adapter context")
        facts = _Facts(context, base)
        _extract(context, parsed, facts, self.application)
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
            for name in FlaskFrameworkAdapter.descriptor.capabilities
        )


def _route_spec(
    call: ast.Call, facts: _Facts, location: _Location
) -> tuple[str, tuple[str, ...]] | None:
    attr = call.func.attr if isinstance(call.func, ast.Attribute) else ""
    path_expr = call.args[0] if call.args else _keyword(call, "rule")
    route_path = _static_path(path_expr)
    methods_expr = _keyword(call, "methods")
    if methods_expr is not None:
        methods: tuple[str, ...] | None = _methods(methods_expr)
    elif attr in _SHORTCUTS:
        methods = _SHORTCUTS[attr]
    elif attr in {"route", "add_url_rule"}:
        methods = ("GET",)
    else:
        methods = None
    if route_path is None or methods is None:
        facts.issue("flask_route_dynamic", location.path, location.line)
        return None
    return route_path, methods


def _dependency_name(
    decorator: ast.expr, frame: dict[str, str | None]
) -> str | None:
    expression = decorator.func if isinstance(decorator, ast.Call) else decorator
    return _qualified(expression, [frame])


def _extract(
    context: AdapterContext,
    parsed: ParseResult,
    facts: _Facts,
    requested_application: str | None,
) -> None:
    local_roots = set()
    for unit in parsed.units:
        if isinstance(unit.representation, ast.Module):
            pure = PurePosixPath(unit.relative_path)
            local_roots.update(
                (pure.stem, _module_name(unit.relative_path).split(".")[0])
            )
            if pure.stem == "__init__" and len(pure.parts) > 1:
                local_roots.add(pure.parts[-2])
    if "flask" in local_roots:
        return
    nodes: dict[str, _Node] = {}
    includes: dict[str, list[_Include]] = defaultdict(list)
    routes: dict[str, list[_Route]] = defaultdict(list)
    for unit in parsed.units:
        tree = unit.representation
        if not isinstance(tree, ast.Module):
            continue
        path = unit.relative_path
        module = _Module(path, _module_name(path), tree)
        import_frame = _bindings(module, tree.body, module.name)
        writes: dict[str, int] = defaultdict(int)
        for item in ast.walk(tree):
            if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Store):
                writes[item.id] += 1
        for statement in tree.body:
            target = None
            value = None
            if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
                if isinstance(statement.targets[0], ast.Name):
                    target, value = statement.targets[0].id, statement.value
            elif isinstance(statement, ast.AnnAssign) and isinstance(
                statement.target, ast.Name
            ):
                target, value = statement.target.id, statement.value
            if not target or writes[target] != 1 or not isinstance(value, ast.Call):
                continue
            constructor = _qualified(value.func, [import_frame])
            if constructor == "flask.Flask":
                kind = "app"
                prefix = ""
            elif constructor == "flask.Blueprint":
                kind = "blueprint"
                prefix_expr = _keyword(value, "url_prefix")
                prefix = (
                    _static_path(prefix_expr) if prefix_expr is not None else ""
                )
                if prefix_expr is not None and prefix is None:
                    facts.issue("flask_blueprint_unresolved", path, statement.lineno)
                    continue
            else:
                continue
            nodes[f"{module.name}.{target}"] = _Node(
                f"{module.name}.{target}",
                kind,
                prefix or "",
                _Location(path, statement.lineno),
            )
        frame = dict(import_frame)
        frame.update(
            {
                item.name.rsplit(".", 1)[-1]: item.name
                for item in nodes.values()
                if item.location.path == path
            }
        )
        definitions, _ = _unique_definitions(tree, module.name, path)
        for _, name, statement in definitions:
            if not isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if frame.get(statement.name) != name:
                if any(_is_route(item) for item in statement.decorator_list):
                    facts.issue("flask_route_dynamic", path, statement.lineno)
                continue
            sites = [item for item in statement.decorator_list if _is_route(item)]
            if not sites:
                continue
            dependencies: list[tuple[str, _Location]] = []
            for decorator in statement.decorator_list:
                if _is_route(decorator):
                    continue
                found = _dependency_name(decorator, frame)
                if not found:
                    facts.issue(
                        "flask_dependency_unresolved", path, decorator.lineno
                    )
                    continue
                dependencies.append((found, _Location(path, decorator.lineno)))
            for decorator in sites:
                if not isinstance(decorator, ast.Call):
                    continue
                owner = _qualified(decorator.func.value, [frame])
                location = _Location(path, decorator.lineno)
                if not owner:
                    facts.issue("flask_route_dynamic", path, decorator.lineno)
                    continue
                spec = _route_spec(decorator, facts, location)
                if spec is None:
                    continue
                route_path, methods = spec
                routes[owner].append(
                    _Route(
                        owner,
                        name,
                        route_path,
                        methods,
                        tuple(dependencies),
                        location,
                    )
                )
        for statement in tree.body:
            if not isinstance(statement, ast.Expr) or not isinstance(
                statement.value, ast.Call
            ):
                continue
            call = statement.value
            if not isinstance(call.func, ast.Attribute):
                continue
            owner = _qualified(call.func.value, [frame])
            location = _Location(path, statement.lineno)
            if call.func.attr == "register_blueprint":
                target_expr = (
                    call.args[0] if call.args else _keyword(call, "blueprint")
                )
                blueprint = _qualified(target_expr, [frame]) if target_expr else None
                prefix_expr = _keyword(call, "url_prefix")
                prefix = _static_path(prefix_expr) if prefix_expr is not None else ""
                if not owner or not blueprint or prefix is None:
                    facts.issue("flask_blueprint_unresolved", path, statement.lineno)
                    continue
                includes[owner].append(
                    _Include(owner, blueprint, prefix, location)
                )
            elif call.func.attr == "add_url_rule":
                handler_expr = (
                    call.args[2] if len(call.args) > 2 else _keyword(call, "view_func")
                )
                handler = _qualified(handler_expr, [frame]) if handler_expr else None
                if not owner or not handler:
                    facts.issue("flask_route_dynamic", path, statement.lineno)
                    continue
                spec = _route_spec(call, facts, location)
                if spec is None:
                    continue
                route_path, methods = spec
                routes[owner].append(
                    _Route(owner, handler, route_path, methods, (), location)
                )

    for owner, owner_routes in routes.items():
        if owner not in nodes:
            for route in owner_routes:
                facts.issue(
                    "flask_route_dynamic", route.location.path, route.location.line
                )
    for owner, owner_includes in includes.items():
        if owner not in nodes:
            for include in owner_includes:
                facts.issue(
                    "flask_blueprint_unresolved",
                    include.location.path,
                    include.location.line,
                )
    callable_index: dict[str, list[Entity]] = defaultdict(list)
    for entity in facts.entities.values():
        if entity.type == EntityType.CALLABLE:
            callable_index[entity.qualified_name].append(entity)

    def dependency_edge(source: str, target_name: str, location: _Location) -> None:
        matches = callable_index.get(target_name, ())
        if len(matches) != 1:
            facts.issue("flask_dependency_unresolved", location.path, location.line)
            return
        facts.edge(
            EdgeType.DEPENDS_ON, source, matches[0].id, location, DEPENDENCY_RULE
        )

    apps = tuple(sorted(name for name, item in nodes.items() if item.kind == "app"))
    if requested_application is not None:
        if requested_application.replace(":", ".") not in apps:
            if parsed.units:
                facts.issue("flask_app_unresolved", parsed.units[0].relative_path, 1)
            return
        app = requested_application.replace(":", ".")
    elif len(apps) == 1:
        app = apps[0]
    elif len(apps) > 1:
        facts.issue(
            "flask_app_ambiguous",
            nodes[apps[0]].location.path,
            nodes[apps[0]].location.line,
        )
        return
    else:
        return

    def publish(
        owner: str,
        prefix: str,
        chain: tuple[str, ...],
        chain_locations: tuple[_Location, ...],
        stack: frozenset[str],
    ) -> None:
        if owner in stack:
            node = nodes.get(owner)
            if node:
                facts.issue(
                    "flask_blueprint_cycle", node.location.path, node.location.line
                )
            return
        node = nodes.get(owner)
        if node is None:
            return
        current_prefix = _path(prefix, node.prefix) if node.prefix else prefix
        for route in sorted(
            routes.get(owner, ()),
            key=lambda item: (item.location.path, item.location.line, item.handler),
        ):
            handlers = callable_index.get(route.handler, ())
            if len(handlers) != 1:
                facts.issue(
                    "flask_route_dynamic", route.location.path, route.location.line
                )
                continue
            full_path = _path(current_prefix, route.path)
            for method in route.methods:
                route_chain = chain + (
                    f"route:{route.location.path}:{route.location.line}:{method}",
                )
                identifier = endpoint_id(
                    context.repository_id,
                    route.location.path,
                    route.handler,
                    method,
                    full_path,
                    route_chain,
                )
                facts.entities[identifier] = Entity(
                    identifier,
                    context.repository_id,
                    context.snapshot_id,
                    EntityType.ENDPOINT,
                    f"{method} {full_path}",
                    f"{route.handler}:{method}:{full_path}",
                    route.location.path,
                    route.location.line,
                    route.location.line,
                    framework_kind="flask_route",
                    attributes=(
                        ("method", method),
                        ("path", full_path),
                        ("registration_chain", route_chain),
                    ),
                )
                facts.edge(
                    EdgeType.EXPOSES,
                    context.repository_id,
                    identifier,
                    route.location,
                    ROUTE_RULE,
                )
                for registration in chain_locations:
                    facts.edge(
                        EdgeType.EXPOSES,
                        context.repository_id,
                        identifier,
                        registration,
                        ROUTE_RULE,
                    )
                facts.edge(
                    EdgeType.HANDLED_BY,
                    identifier,
                    handlers[0].id,
                    route.location,
                    HANDLER_RULE,
                )
                for target, location in route.dependencies:
                    dependency_edge(identifier, target, location)
        for include in sorted(
            includes.get(owner, ()),
            key=lambda item: (item.location.path, item.location.line, item.blueprint),
        ):
            if (
                include.blueprint not in nodes
                or nodes[include.blueprint].kind != "blueprint"
            ):
                facts.issue(
                    "flask_blueprint_unresolved",
                    include.location.path,
                    include.location.line,
                )
                continue
            new_chain = chain + (
                f"blueprint:{include.location.path}:{include.location.line}:{include.blueprint}",
            )
            next_prefix = (
                _path(current_prefix, include.prefix)
                if include.prefix
                else current_prefix
            )
            publish(
                include.blueprint,
                next_prefix,
                new_chain,
                chain_locations + (include.location,),
                stack | {owner},
            )

    publish(app, "", (f"app:{app}",), (), frozenset())


def _is_route(node: ast.expr) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in _ROUTE_ATTRS
    )
