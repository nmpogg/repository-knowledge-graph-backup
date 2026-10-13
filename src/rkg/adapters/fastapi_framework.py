"""Static FastAPI route and dependency extraction over parsed Python AST.

The adapter never imports or executes analyzed modules. Unsupported bindings produce
path-only diagnostics and never become guessed graph relationships.
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
    TechnologyConstraint,
)
from rkg.adapters.fastapi_static import (
    factory_view,
    module_writes,
    registration_statements,
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

ROUTE_RULE = "RKG.fastapi.route.v1"
HANDLER_RULE = "RKG.fastapi.handler.v1"
DEPENDENCY_RULE = "RKG.fastapi.dependency.v1"
METHODS = {
    "get": ("GET",),
    "post": ("POST",),
    "put": ("PUT",),
    "patch": ("PATCH",),
    "delete": ("DELETE",),
    "head": ("HEAD",),
    "options": ("OPTIONS",),
}
_MESSAGES = {
    "fastapi_app_ambiguous": "Application selection is required.",
    "fastapi_app_unresolved": "Application entrypoint could not be resolved.",
    "fastapi_route_dynamic": "Route path, method or handler is not static.",
    "fastapi_router_unresolved": "Router registration could not be resolved.",
    "fastapi_dependency_unresolved": "Dependency callable could not be resolved.",
    "fastapi_dependency_unsupported": "Dependency form is unsupported.",
    "fastapi_router_cycle": "Router registration cycle was skipped.",
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
    dependencies: tuple[tuple[str, _Location], ...]
    location: _Location


@dataclass(frozen=True, slots=True)
class _Include:
    owner: str
    router: str
    prefix: str
    dependencies: tuple[tuple[str, _Location], ...]
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
    if route == "":
        return prefix
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


class FastAPIFrameworkAdapter:
    """Implement the initial framework profile for static FastAPI patterns."""

    entrypoint_required = True
    allow_unverified_versions = True
    descriptor = AdapterDescriptor(
        adapter_id="rkg.fastapi",
        adapter_version="2.1.0",
        contract_version=CONTRACT_VERSION,
        kind=AdapterKind.FRAMEWORK,
        language="python",
        framework="fastapi",
        grammar_or_target="CPython 3.12 AST",
        file_patterns=("*.py", "**/*.py"),
        ignore_patterns=("**/__pycache__/**",),
        capabilities=("app", "di", "routes"),
        technology_constraints=(TechnologyConstraint("fastapi", ">=0.100,<1.0"),),
    )

    def __init__(self, application: str | None = None) -> None:
        self.application = application

    def for_application(self, reference: str) -> FastAPIFrameworkAdapter:
        """Bind a selected entrypoint without mutating the registered adapter."""
        return FastAPIFrameworkAdapter(reference)

    def technology_detectors(self) -> tuple[object, ...]:
        from rkg.detection.fastapi import FastAPIAppDetector

        return (FastAPIAppDetector(),)

    def detect(self, manifest: SourceManifest, parsed: ParseResult) -> DetectionReport:
        from rkg.detection.fastapi import FastAPIAppDetector

        observation = FastAPIAppDetector().detect(manifest, parsed)
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
            Capability(name, SupportState.SUPPORTED)
            for name in FastAPIFrameworkAdapter.descriptor.capabilities
        )


def _dependencies(
    expression: ast.expr | None,
    frame: dict[str, str | None],
    facts: _Facts,
    location: _Location,
    *,
    sequence: bool = False,
) -> tuple[tuple[str, _Location], ...]:
    if expression is None:
        return ()
    if sequence and not isinstance(expression, (ast.List, ast.Tuple)):
        facts.issue("fastapi_dependency_unsupported", location.path, location.line)
        return ()
    targets = []
    for node in ast.walk(expression):
        if not isinstance(node, ast.Call):
            continue
        if _qualified(node.func, [frame]) not in (
            "fastapi.Depends",
            "fastapi.params.Depends",
        ):
            continue
        dependency = node.args[0] if node.args else _keyword(node, "dependency")
        name = _qualified(dependency, [frame]) if dependency else None
        if name:
            targets.append((name, _Location(location.path, node.lineno)))
        else:
            facts.issue("fastapi_dependency_unresolved", location.path, node.lineno)
    return tuple(targets)


def _register_route(
    owner: str | None,
    call: ast.Call,
    handler: str | None,
    frame: dict[str, str | None],
    location: _Location,
    facts: _Facts,
    routes: dict[str, list[_Route]],
) -> None:
    if not owner or not handler:
        facts.issue("fastapi_route_dynamic", location.path, location.line)
        return
    route_path = (
        _literal(call.args[0]) if call.args else _literal(_keyword(call, "path"))
    )
    method_name = call.func.attr if isinstance(call.func, ast.Attribute) else ""
    methods = METHODS.get(method_name)
    if method_name in {"api_route", "add_api_route"}:
        methods_expr = _keyword(call, "methods")
        methods = _methods(methods_expr) if methods_expr is not None else ("GET",)
    if (
        route_path is None
        or (route_path and not route_path.startswith("/"))
        or methods is None
    ):
        facts.issue("fastapi_route_dynamic", location.path, location.line)
        return
    deps = _dependencies(
        _keyword(call, "dependencies"), frame, facts, location, sequence=True
    )
    routes[owner].append(_Route(owner, handler, route_path, methods, deps, location))


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
    if "fastapi" in local_roots:
        return
    nodes: dict[str, _Node] = {}
    includes: dict[str, list[_Include]] = defaultdict(list)
    routes: dict[str, list[_Route]] = defaultdict(list)
    functions: list[
        tuple[str, ast.FunctionDef | ast.AsyncFunctionDef, str, dict[str, str | None]]
    ] = []
    for unit in parsed.units:
        tree = unit.representation
        if not isinstance(tree, ast.Module):
            continue
        path = unit.relative_path
        module = _Module(path, _module_name(path), tree)
        original_tree = tree
        tree = factory_view(module)
        module = _Module(path, module.name, tree)
        import_frame = _bindings(module, tree.body, module.name)
        writes = module_writes(tree)
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
            if constructor not in {
                "fastapi.FastAPI",
                "fastapi.APIRouter",
                "fastapi.routing.APIRouter",
            }:
                continue
            kind = "app" if constructor == "fastapi.FastAPI" else "router"
            location = _Location(path, statement.lineno)
            prefix = _literal(_keyword(value, "prefix")) if kind == "router" else ""
            if (
                kind == "router"
                and _keyword(value, "prefix") is not None
                and (prefix is None or not prefix.startswith("/"))
            ):
                facts.issue("fastapi_router_unresolved", path, statement.lineno)
                continue
            name = f"{module.name}.{target}"
            nodes[name] = _Node(
                name,
                kind,
                prefix or "",
                _dependencies(
                    _keyword(value, "dependencies"),
                    import_frame,
                    facts,
                    location,
                    sequence=True,
                ),
                location,
            )
        frame = dict(import_frame)
        frame.update(
            {
                item.name.rsplit(".", 1)[-1]: item.name
                for item in nodes.values()
                if item.location.path == path
            }
        )
        definitions, _ = _unique_definitions(original_tree, module.name, path)
        for _, name, statement in definitions:
            if not isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            functions.append((name, statement, path, frame))
            if frame.get(statement.name) != name:
                if statement.decorator_list:
                    facts.issue("fastapi_route_dynamic", path, statement.lineno)
                continue
            for decorator in statement.decorator_list:
                if not isinstance(decorator, ast.Call) or not isinstance(
                    decorator.func, ast.Attribute
                ):
                    continue
                method = decorator.func.attr
                if method not in METHODS and method != "api_route":
                    continue
                owner = _qualified(decorator.func.value, [frame])
                if owner is None:
                    facts.issue("fastapi_route_dynamic", path, decorator.lineno)
                    continue
                _register_route(
                    owner,
                    decorator,
                    name,
                    frame,
                    _Location(path, decorator.lineno),
                    facts,
                    routes,
                )
        registered_locations: set[int] = set()
        for statement, registration_frame in registration_statements(tree.body, frame):
            if not isinstance(statement.value, ast.Call):
                continue
            call = statement.value
            if not isinstance(call.func, ast.Attribute):
                continue
            owner = _qualified(call.func.value, [registration_frame])
            location = _Location(path, statement.lineno)
            if call.func.attr == "include_router":
                registered_locations.add(call.lineno)
                router_expr = call.args[0] if call.args else _keyword(call, "router")
                router = (
                    _qualified(router_expr, [registration_frame])
                    if router_expr
                    else None
                )
                prefix_expr = _keyword(call, "prefix")
                prefix = _literal(prefix_expr) if prefix_expr is not None else ""
                if (
                    not owner
                    or not router
                    or prefix is None
                    or (prefix and not prefix.startswith("/"))
                ):
                    facts.issue("fastapi_router_unresolved", path, statement.lineno)
                    continue
                includes[owner].append(
                    _Include(
                        owner,
                        router,
                        prefix,
                        _dependencies(
                            _keyword(call, "dependencies"),
                            registration_frame,
                            facts,
                            location,
                            sequence=True,
                        ),
                        location,
                    )
                )
            elif call.func.attr == "add_api_route":
                registered_locations.add(call.lineno)
                handler_expr = (
                    call.args[1] if len(call.args) > 1 else _keyword(call, "endpoint")
                )
                handler = (
                    _qualified(handler_expr, [registration_frame])
                    if handler_expr
                    else None
                )
                _register_route(
                    owner, call, handler, registration_frame, location, facts, routes
                )

        for call in ast.walk(original_tree):
            if (
                isinstance(call, ast.Call)
                and isinstance(call.func, ast.Attribute)
                and call.func.attr in {"include_router", "add_api_route"}
                and call.lineno not in registered_locations
            ):
                facts.issue("fastapi_router_unresolved", path, call.lineno)

    callable_index: dict[str, list[Entity]] = defaultdict(list)
    for owner, owner_routes in routes.items():
        if owner not in nodes:
            for route in owner_routes:
                facts.issue(
                    "fastapi_router_unresolved",
                    route.location.path,
                    route.location.line,
                )
    for owner, owner_includes in includes.items():
        if owner not in nodes:
            for include in owner_includes:
                facts.issue(
                    "fastapi_router_unresolved",
                    include.location.path,
                    include.location.line,
                )
    for entity in facts.entities.values():
        if entity.type == EntityType.CALLABLE:
            callable_index[entity.qualified_name].append(entity)

    def dependency_edge(source: str, target_name: str, location: _Location) -> None:
        matches = callable_index.get(target_name, ())
        if len(matches) != 1:
            facts.issue("fastapi_dependency_unresolved", location.path, location.line)
            return
        facts.edge(
            EdgeType.DEPENDS_ON, source, matches[0].id, location, DEPENDENCY_RULE
        )

    for name, statement, path, frame in functions:
        owners = callable_index.get(name, ())
        if len(owners) != 1:
            continue
        defaults = list(statement.args.defaults) + [
            item for item in statement.args.kw_defaults if item is not None
        ]
        annotations = [
            item.annotation
            for item in (
                *statement.args.posonlyargs,
                *statement.args.args,
                *statement.args.kwonlyargs,
            )
            if item.annotation is not None
        ]
        for expression in defaults + annotations:
            for target, location in _dependencies(
                expression, frame, facts, _Location(path, expression.lineno)
            ):
                dependency_edge(owners[0].id, target, location)

    apps = tuple(sorted(name for name, item in nodes.items() if item.kind == "app"))
    if requested_application is not None:
        if requested_application.replace(":", ".") not in apps:
            if parsed.units:
                facts.issue("fastapi_app_unresolved", parsed.units[0].relative_path, 1)
            return
        app = requested_application.replace(":", ".")
    elif len(apps) == 1:
        app = apps[0]
    elif len(apps) > 1:
        facts.issue(
            "fastapi_app_ambiguous",
            nodes[apps[0]].location.path,
            nodes[apps[0]].location.line,
        )
        return
    else:
        if parsed.units:
            facts.issue("fastapi_app_unresolved", parsed.units[0].relative_path, 1)
        return

    def publish(
        owner: str,
        prefix: str,
        chain: tuple[str, ...],
        inherited: tuple[tuple[str, _Location], ...],
        chain_locations: tuple[_Location, ...],
        stack: frozenset[str],
    ) -> None:
        if owner in stack:
            node = nodes.get(owner)
            if node:
                facts.issue(
                    "fastapi_router_cycle", node.location.path, node.location.line
                )
            return
        node = nodes.get(owner)
        if node is None:
            return
        current_prefix = _path(prefix, node.prefix) if node.prefix else prefix
        current_deps = inherited + node.dependencies
        for route in sorted(
            routes.get(owner, ()),
            key=lambda item: (item.location.path, item.location.line, item.handler),
        ):
            handlers = callable_index.get(route.handler, ())
            if len(handlers) != 1:
                facts.issue(
                    "fastapi_route_dynamic", route.location.path, route.location.line
                )
                continue
            full_path = _path(current_prefix, route.path)
            if not full_path.startswith("/"):
                facts.issue(
                    "fastapi_route_dynamic", route.location.path, route.location.line
                )
                continue
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
                    framework_kind="fastapi_route",
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
                for target, location in current_deps + route.dependencies:
                    dependency_edge(identifier, target, location)
        for include in sorted(
            includes.get(owner, ()),
            key=lambda item: (item.location.path, item.location.line, item.router),
        ):
            if include.router not in nodes or nodes[include.router].kind != "router":
                facts.issue(
                    "fastapi_router_unresolved",
                    include.location.path,
                    include.location.line,
                )
                continue
            new_chain = chain + (
                f"include:{include.location.path}:{include.location.line}:{include.router}",
            )
            publish(
                include.router,
                _path(current_prefix, include.prefix)
                if include.prefix
                else current_prefix,
                new_chain,
                current_deps + include.dependencies,
                chain_locations + (include.location,),
                stack | {owner},
            )

    publish(app, "", (f"app:{app}",), (), (), frozenset())
