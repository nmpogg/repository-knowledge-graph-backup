"""Static Django URL extraction over parsed Python AST.

The adapter never imports or executes analyzed modules. A route is recorded
only when the registration, path and handler each resolve from a literal or a
unique constant. ``path()`` does not imply GET. A method is stored only when a
decorator or ``http_method_names`` list says so literally. Anything else is a
fixed diagnostic with a relative path and line. Django ORM is out of scope.
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
    DetectionEvidence,
    DetectionReport,
    ParseResult,
    SupportState,
    TechnologyDetection,
)
from rkg.adapters.python_language import _module_name
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

ROUTE_RULE = "RKG.django.route.v1"
HANDLER_RULE = "RKG.django.handler.v1"
DETECT_IMPORT_RULE = "RKG.django.detect_import.v1"
DETECT_URLS_RULE = "RKG.django.detect_urls.v1"
_PATH_FUNCS = frozenset(
    {
        "django.urls.path",
        "django.conf.urls.path",
    }
)
_REGEX_FUNCS = frozenset(
    {
        "django.urls.re_path",
        "django.conf.urls.re_path",
        "django.conf.urls.url",
    }
)
_ROUTER_FUNCS = _PATH_FUNCS | _REGEX_FUNCS
_INCLUDE_FUNCS = frozenset(
    {
        "django.urls.include",
        "django.conf.urls.include",
    }
)
_METHOD_DECORATORS = {
    "django.views.decorators.http.require_GET": ("GET",),
    "django.views.decorators.http.require_POST": ("POST",),
    "django.views.decorators.http.require_safe": ("GET", "HEAD"),
}
_HTTP_METHODS = "django.views.decorators.http.require_http_methods"
_MESSAGES = {
    "django_route_dynamic": "Route path is not a literal or resolved constant.",
    "django_view_unresolved": "View handler could not be resolved uniquely.",
    "django_include_unresolved": "Included URLconf could not be resolved uniquely.",
    "django_include_cycle": "URLconf include cycle was skipped.",
    "django_urls_ambiguous": "URLconf root could not be selected uniquely.",
}


@dataclass(frozen=True, slots=True)
class _Location:
    path: str
    line: int


@dataclass(frozen=True, slots=True)
class _View:
    """Resolved handler. ``methods`` is None when the method must be omitted."""

    label: str
    methods: tuple[str, ...] | None
    targets: tuple[str, ...]
    per_method: bool


@dataclass(frozen=True, slots=True)
class _Route:
    view: _View
    path: str
    regex: bool
    location: _Location


@dataclass(frozen=True, slots=True)
class _Include:
    module: str
    prefix: str
    regex: bool
    location: _Location


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


class DjangoUrlsDetector:
    """Find Django URLconf modules without importing or executing source."""

    def urlconf_modules(self, parsed: ParseResult) -> tuple[str, ...]:
        """Static URLconf module names. ``extract`` calls this directly."""
        if _local_django(parsed):
            return ()
        names: list[str] = []
        for unit in parsed.units:
            tree = unit.representation
            if not isinstance(tree, ast.Module):
                continue
            module = _Module(
                unit.relative_path, _module_name(unit.relative_path), tree
            )
            frame = _bindings(module, tree.body, module.name)
            if _urlpatterns(tree, frame) is not None:
                names.append(module.name)
        return tuple(sorted(set(names)))

    def detect(
        self, manifest: SourceManifest, parsed: ParseResult
    ) -> FrameworkObservation:  # noqa: F821
        from rkg.detection.contracts import FrameworkObservation

        del manifest
        if _local_django(parsed):
            return FrameworkObservation(DetectionReport())
        evidence: set[DetectionEvidence] = set()
        modules = set(self.urlconf_modules(parsed))
        for unit in parsed.units:
            tree = unit.representation
            if not isinstance(tree, ast.Module):
                continue
            if _imports_django_urls(tree):
                evidence.add(DetectionEvidence(unit.relative_path, DETECT_IMPORT_RULE))
            module_name = _module_name(unit.relative_path)
            if module_name in modules:
                evidence.add(DetectionEvidence(unit.relative_path, DETECT_URLS_RULE))
        if not evidence:
            return FrameworkObservation(DetectionReport())
        references = tuple(
            sorted(evidence, key=lambda item: (item.relative_path, item.rule_id))
        )
        report = DetectionReport(
            (TechnologyDetection("django", None, references),),
            tuple(sorted(modules)),
        )
        return FrameworkObservation(report)


class DjangoFrameworkAdapter:
    """Extract static Django routes. Not a reviewed deep-supported profile."""

    entrypoint_required = False
    reviewed_deep_support = False
    descriptor = AdapterDescriptor(
        adapter_id="rkg.django",
        adapter_version="1.0.0",
        contract_version=CONTRACT_VERSION,
        kind=AdapterKind.FRAMEWORK,
        language="python",
        framework="django",
        grammar_or_target="CPython 3.12 AST",
        file_patterns=("*.py", "**/*.py"),
        ignore_patterns=("**/__pycache__/**",),
        capabilities=("routes",),
    )

    def technology_detectors(self) -> tuple[object, ...]:
        return (DjangoUrlsDetector(),)

    def detect(self, manifest: SourceManifest, parsed: ParseResult) -> DetectionReport:
        observation = DjangoUrlsDetector().detect(manifest, parsed)
        return observation.report

    def extract(
        self, context: AdapterContext, parsed: ParseResult, base: FactBatch
    ) -> AdapterResult:
        if (
            base.repository_id != context.repository_id
            or base.snapshot_id != context.snapshot_id
        ):
            raise ValueError("candidate ownership does not match adapter context")
        facts = _Facts(context, base)
        _extract(
            context,
            parsed,
            facts,
            DjangoUrlsDetector().urlconf_modules(parsed),
        )
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
            for name in DjangoFrameworkAdapter.descriptor.capabilities
        )


def _local_django(parsed: ParseResult) -> bool:
    for unit in parsed.units:
        if not isinstance(unit.representation, ast.Module):
            continue
        pure = PurePosixPath(unit.relative_path)
        roots = {pure.stem, _module_name(unit.relative_path).split(".")[0]}
        if pure.stem == "__init__" and len(pure.parts) > 1:
            roots.add(pure.parts[-2])
        if "django" in roots:
            return True
    return False


def _imports_django_urls(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "django.urls" or alias.name.startswith("django.urls."):
                    return True
                if alias.name == "django.conf.urls" or alias.name.startswith(
                    "django.conf.urls."
                ):
                    return True
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            if node.module in {"django.urls", "django.conf.urls"}:
                return True
            if node.module.startswith(("django.urls.", "django.conf.urls.")):
                return True
    return False


def _literal(node: ast.expr | None) -> str | None:
    return (
        node.value
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
        else None
    )


def _keyword(node: ast.Call, name: str) -> ast.expr | None:
    return next((item.value for item in node.keywords if item.arg == name), None)


def _arg(node: ast.Call, index: int, name: str) -> ast.expr | None:
    if len(node.args) > index:
        return node.args[index]
    return _keyword(node, name)


def _module_assignments(
    tree: ast.Module,
) -> dict[str, ast.expr]:
    counts: dict[str, int] = defaultdict(int)
    values: dict[str, ast.expr] = {}
    for statement in tree.body:
        target: str | None = None
        value: ast.expr | None = None
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
            if isinstance(statement.targets[0], ast.Name):
                target = statement.targets[0].id
                value = statement.value
        elif isinstance(statement, ast.AnnAssign) and isinstance(
            statement.target, ast.Name
        ):
            target = statement.target.id
            value = statement.value
        if target and value is not None:
            counts[target] += 1
            values[target] = value
    return {name: expr for name, expr in values.items() if counts[name] == 1}


def _string_literals(assignments: dict[str, ast.expr]) -> dict[str, str]:
    return {
        name: value
        for name, expr in assignments.items()
        if (value := _literal(expr)) is not None
    }


def _sequence_literals(assignments: dict[str, ast.expr]) -> dict[str, tuple[str, ...]]:
    found: dict[str, tuple[str, ...]] = {}
    for name, expr in assignments.items():
        methods = _method_list(expr)
        if methods is not None:
            found[name] = methods
    return found


def _method_list(node: ast.expr | None) -> tuple[str, ...] | None:
    if not isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return None
    values = [_literal(item) for item in node.elts]
    if not values or any(value is None or not value.isalpha() for value in values):
        return None
    return tuple(dict.fromkeys(value.upper() for value in values if value))


def _resolve_string(
    expr: ast.expr | None,
    module: str,
    frames: list[dict[str, str | None]],
    literals: dict[str, dict[str, str]],
    assignments: dict[str, dict[str, ast.expr]],
    seen: frozenset[tuple[str, str]],
) -> str | None:
    direct = _literal(expr)
    if direct is not None:
        return direct
    if not isinstance(expr, ast.Name):
        return None
    key = (module, expr.id)
    if key in seen:
        return None
    local = literals.get(module, {}).get(expr.id)
    if local is not None:
        return local
    qualified = _qualified(expr, frames)
    if qualified and "." in qualified:
        owner, name = qualified.rsplit(".", 1)
        imported = literals.get(owner, {}).get(name)
        if imported is not None:
            return imported
    alias = assignments.get(module, {}).get(expr.id)
    if isinstance(alias, ast.Name):
        return _resolve_string(
            alias, module, frames, literals, assignments, seen | {key}
        )
    return None


def _resolve_methods(
    expr: ast.expr | None,
    module: str,
    frames: list[dict[str, str | None]],
    sequences: dict[str, dict[str, tuple[str, ...]]],
    assignments: dict[str, dict[str, ast.expr]],
    seen: frozenset[tuple[str, str]],
) -> tuple[str, ...] | None:
    direct = _method_list(expr)
    if direct is not None:
        return direct
    if not isinstance(expr, ast.Name):
        return None
    key = (module, expr.id)
    if key in seen:
        return None
    local = sequences.get(module, {}).get(expr.id)
    if local is not None:
        return local
    qualified = _qualified(expr, frames)
    if qualified and "." in qualified:
        owner, name = qualified.rsplit(".", 1)
        imported = sequences.get(owner, {}).get(name)
        if imported is not None:
            return imported
    alias = assignments.get(module, {}).get(expr.id)
    if isinstance(alias, ast.Name):
        return _resolve_methods(
            alias, module, frames, sequences, assignments, seen | {key}
        )
    return None


def _urlpatterns(
    tree: ast.Module, frame: dict[str, str | None]
) -> list[ast.expr] | None:
    del frame
    assignments = _module_assignments(tree)
    value = assignments.get("urlpatterns")
    if not isinstance(value, (ast.List, ast.Tuple)):
        return None
    if any(isinstance(item, ast.Starred) for item in value.elts):
        return None
    return list(value.elts)


def _class_methods(node: ast.ClassDef) -> tuple[str, ...] | None | object:
    """Return uppercase methods, None when dynamic, or ``_ABSENT``."""
    found: tuple[str, ...] | None | object = _ABSENT
    for statement in node.body:
        target: str | None = None
        value: ast.expr | None = None
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
            if isinstance(statement.targets[0], ast.Name):
                target = statement.targets[0].id
                value = statement.value
        elif isinstance(statement, ast.AnnAssign) and isinstance(
            statement.target, ast.Name
        ):
            target = statement.target.id
            value = statement.value
        if target != "http_method_names" or value is None:
            continue
        if found is not _ABSENT:
            return None
        found = _method_list(value)
    return found


_ABSENT = object()


def _decorator_methods(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    frames: list[dict[str, str | None]],
    module: str,
    sequences: dict[str, dict[str, tuple[str, ...]]],
    assignments: dict[str, dict[str, ast.expr]],
) -> tuple[str, ...] | None:
    found: tuple[str, ...] | None = None
    for decorator in node.decorator_list:
        call = decorator if isinstance(decorator, ast.Call) else None
        expression = call.func if call else decorator
        name = _qualified(expression, frames)
        if name in _METHOD_DECORATORS:
            found = _METHOD_DECORATORS[name]
        elif name == _HTTP_METHODS and call is not None:
            arg = _arg(call, 0, "request_method_list")
            found = _resolve_methods(
                arg, module, frames, sequences, assignments, frozenset()
            )
    return found


def _unique(
    index: dict[str, list[Entity]], name: str | None, kind: EntityType
) -> Entity | None:
    if not name:
        return None
    matches = [item for item in index.get(name, ()) if item.type == kind]
    return matches[0] if len(matches) == 1 else None


def _view_from_callable(
    label: str,
    node: ast.AST | None,
    module: str,
    frames: list[dict[str, str | None]],
    sequences: dict[str, dict[str, tuple[str, ...]]],
    assignments: dict[str, dict[str, ast.expr]],
) -> _View | None:
    methods = None
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        methods = _decorator_methods(node, frames, module, sequences, assignments)
    return _View(label, methods, (label,), False)


def _view_from_class(
    class_name: str,
    call: ast.Call,
    definitions: dict[str, tuple[str, ast.AST]],
    index: dict[str, list[Entity]],
    module: str,
    frames: list[dict[str, str | None]],
    sequences: dict[str, dict[str, tuple[str, ...]]],
    assignments: dict[str, dict[str, ast.expr]],
) -> _View | None:
    if _unique(index, class_name, EntityType.TYPE) is None:
        return None
    record = definitions.get(class_name)
    class_node = record[1] if record else None
    if not isinstance(class_node, ast.ClassDef):
        return None
    owner = record[0] if record else module
    keyword = _keyword(call, "http_method_names")
    if keyword is not None:
        methods: tuple[str, ...] | None | object = _resolve_methods(
            keyword, module, frames, sequences, assignments, frozenset()
        )
    else:
        methods = _class_methods(class_node)
        if methods is not _ABSENT and not isinstance(methods, tuple):
            attr = next(
                (
                    statement.value
                    for statement in class_node.body
                    if isinstance(statement, ast.Assign)
                    and len(statement.targets) == 1
                    and isinstance(statement.targets[0], ast.Name)
                    and statement.targets[0].id == "http_method_names"
                    and isinstance(statement.value, ast.Name)
                ),
                None,
            )
            if attr is not None:
                methods = _resolve_methods(
                    attr, owner, frames, sequences, assignments, frozenset()
                )
    as_view = f"{class_name}.as_view"
    if _unique(index, as_view, EntityType.CALLABLE) is not None:
        known = methods if isinstance(methods, tuple) else None
        return _View(as_view, known, (as_view,), False)
    if not isinstance(methods, tuple):
        # Absent or dynamic http_method_names: keep the route, do not guess a verb.
        return _View(as_view, None, (), False)
    targets_list: list[str] = []
    for method in methods:
        target = f"{class_name}.{method.lower()}"
        if _unique(index, target, EntityType.CALLABLE) is None:
            return None
        targets_list.append(target)
    return _View(as_view, methods, tuple(targets_list), True)


def _resolve_include_module(
    expr: ast.expr | None,
    module: str,
    frames: list[dict[str, str | None]],
    literals: dict[str, dict[str, str]],
    assignments: dict[str, dict[str, ast.expr]],
    modules: dict[str, list[_Module]],
    seen: frozenset[tuple[str, str]],
) -> str | None:
    if isinstance(expr, (ast.List, ast.Tuple)) and expr.elts:
        return _resolve_include_module(
            expr.elts[0],
            module,
            frames,
            literals,
            assignments,
            modules,
            seen,
        )
    text = _resolve_string(expr, module, frames, literals, assignments, seen)
    if text and len(modules.get(text, ())) == 1:
        return text
    if isinstance(expr, ast.Name) and (module, expr.id) not in seen:
        alias = assignments.get(module, {}).get(expr.id)
        if alias is not None and not isinstance(alias, ast.Name):
            return _resolve_include_module(
                alias,
                module,
                frames,
                literals,
                assignments,
                modules,
                seen | {(module, expr.id)},
            )
    qualified = _qualified(expr, frames) if expr is not None else None
    if qualified and qualified.endswith(".urlpatterns"):
        qualified = qualified[: -len(".urlpatterns")]
    if qualified and len(modules.get(qualified, ())) == 1:
        return qualified
    return None


def _resolve_view(
    expr: ast.expr,
    module: str,
    frames: list[dict[str, str | None]],
    literals: dict[str, dict[str, str]],
    sequences: dict[str, dict[str, tuple[str, ...]]],
    assignments: dict[str, dict[str, ast.expr]],
    definitions: dict[str, tuple[str, ast.AST]],
    index: dict[str, list[Entity]],
    frame_map: dict[str, dict[str, str | None]],
    seen: frozenset[tuple[str, str]],
) -> _View | None:
    if isinstance(expr, ast.Name) and (module, expr.id) not in seen:
        alias = assignments.get(module, {}).get(expr.id)
        if alias is not None and _qualified(expr, frames) is None:
            return _resolve_view(
                alias,
                module,
                frames,
                literals,
                sequences,
                assignments,
                definitions,
                index,
                frame_map,
                seen | {(module, expr.id)},
            )
    dotted = _resolve_string(expr, module, frames, literals, assignments, seen)
    if dotted and "." in dotted and not dotted.startswith(("/", "^")):
        target = _unique(index, dotted, EntityType.CALLABLE)
        record = definitions.get(dotted)
        if target is None or record is None:
            return None
        return _view_from_callable(
            dotted,
            record[1],
            record[0],
            [frame_map[record[0]]],
            sequences,
            assignments,
        )
    if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Attribute):
        if expr.func.attr != "as_view":
            return None
        class_name = _qualified(expr.func.value, frames)
        if class_name is None and isinstance(expr.func.value, ast.Name):
            class_name = _follow_name(
                expr.func.value.id, module, frames, assignments, seen
            )
        return _view_from_class(
            class_name or "",
            expr,
            definitions,
            index,
            module,
            frames,
            sequences,
            assignments,
        )
    name = _qualified(expr, frames)
    target = _unique(index, name, EntityType.CALLABLE)
    if target is None or not name:
        return None
    record = definitions.get(name)
    node = record[1] if record else None
    owner = record[0] if record else module
    return _view_from_callable(
        name,
        node,
        owner,
        [frame_map.get(owner, frames[0] if frames else {})],
        sequences,
        assignments,
    )


def _follow_name(
    name: str,
    module: str,
    frames: list[dict[str, str | None]],
    assignments: dict[str, dict[str, ast.expr]],
    seen: frozenset[tuple[str, str]],
) -> str | None:
    qualified = _qualified(ast.Name(id=name, ctx=ast.Load()), frames)
    if qualified:
        return qualified
    key = (module, name)
    if key in seen:
        return None
    alias = assignments.get(module, {}).get(name)
    if isinstance(alias, ast.Name):
        return _follow_name(alias.id, module, frames, assignments, seen | {key})
    if isinstance(alias, ast.Attribute):
        return _qualified(alias, frames)
    return None


def _join_path(prefix: str, route: str) -> str:
    head = prefix
    if head and not head.endswith("/"):
        head += "/"
    tail = route[1:] if route.startswith("/") else route
    joined = f"{head}{tail}"
    if not joined.startswith("/"):
        joined = f"/{joined}"
    return joined


def _join_regex(prefix: str, route: str) -> str:
    if not prefix:
        return route
    head = prefix if prefix.endswith("/") else f"{prefix}/"
    return f"{head}{route}"


def _extract(
    context: AdapterContext,
    parsed: ParseResult,
    facts: _Facts,
    urlconf_modules: tuple[str, ...],
) -> None:
    del context
    if _local_django(parsed):
        return
    modules = [
        _Module(
            unit.relative_path,
            _module_name(unit.relative_path),
            unit.representation,
        )
        for unit in parsed.units
        if unit.language == "python" and isinstance(unit.representation, ast.Module)
    ]
    by_name: dict[str, list[_Module]] = defaultdict(list)
    for module in modules:
        by_name[module.name].append(module)
    literals: dict[str, dict[str, str]] = {}
    sequences: dict[str, dict[str, tuple[str, ...]]] = {}
    assignments: dict[str, dict[str, ast.expr]] = {}
    frames: dict[str, dict[str, str | None]] = {}
    definitions: dict[str, tuple[str, ast.AST]] = {}
    for module in modules:
        assigned = _module_assignments(module.tree)
        assignments[module.name] = assigned
        literals[module.name] = _string_literals(assigned)
        sequences[module.name] = _sequence_literals(assigned)
        frames[module.name] = _bindings(module, module.tree.body, module.name)
        from rkg.adapters.python_language import _unique_definitions

        for _owner, qualified, node in _unique_definitions(
            module.tree, module.name, module.path
        )[0]:
            definitions[qualified] = (module.name, node)
    index: dict[str, list[Entity]] = defaultdict(list)
    for entity in facts.entities.values():
        index[entity.qualified_name].append(entity)

    routes: dict[str, list[_Route]] = defaultdict(list)
    includes: dict[str, list[_Include]] = defaultdict(list)
    owners: set[str] = set()
    urlconfs = set(urlconf_modules)
    for module in modules:
        elements = _urlpatterns(module.tree, frames[module.name])
        if elements is None:
            assigned = assignments[module.name].get("urlpatterns")
            if assigned is not None:
                facts.issue("django_route_dynamic", module.path, _line(assigned))
            continue
        if module.name not in urlconfs:
            continue
        owners.add(module.name)
        frame = [frames[module.name]]
        for element in elements:
            if not isinstance(element, ast.Call):
                facts.issue("django_route_dynamic", module.path, _line(element))
                continue
            func = _qualified(element.func, frame)
            location = _Location(module.path, element.lineno)
            if func in _INCLUDE_FUNCS:
                facts.issue("django_include_unresolved", module.path, element.lineno)
                continue
            if func not in _ROUTER_FUNCS:
                facts.issue("django_route_dynamic", module.path, element.lineno)
                continue
            route_expr = _arg(element, 0, "regex" if func in _REGEX_FUNCS else "route")
            route = _resolve_string(
                route_expr,
                module.name,
                frame,
                literals,
                assignments,
                frozenset(),
            )
            if route is None:
                facts.issue("django_route_dynamic", module.path, element.lineno)
                continue
            view_expr = _arg(element, 1, "view")
            included_call = (
                isinstance(view_expr, ast.Call)
                and _qualified(view_expr.func, frame) in _INCLUDE_FUNCS
            )
            if included_call:
                included = _resolve_include_module(
                    _arg(view_expr, 0, "arg"),
                    module.name,
                    frame,
                    literals,
                    assignments,
                    by_name,
                    frozenset(),
                )
                if included is None:
                    facts.issue(
                        "django_include_unresolved", module.path, element.lineno
                    )
                    continue
                includes[module.name].append(
                    _Include(included, route, func in _REGEX_FUNCS, location)
                )
                continue
            if view_expr is None:
                facts.issue("django_view_unresolved", module.path, element.lineno)
                continue
            view = _resolve_view(
                view_expr,
                module.name,
                frame,
                literals,
                sequences,
                assignments,
                definitions,
                index,
                frames,
                frozenset(),
            )
            if view is None:
                facts.issue("django_view_unresolved", module.path, element.lineno)
                continue
            routes[module.name].append(
                _Route(view, route, func in _REGEX_FUNCS, location)
            )

    included = {item.module for group in includes.values() for item in group}
    roots = tuple(sorted(name for name in owners if name not in included))
    if not owners:
        return
    if len(roots) != 1:
        for name in sorted(owners):
            module = by_name[name][0]
            facts.issue("django_urls_ambiguous", module.path, 1)
        return

    def publish(
        module_name: str,
        prefix: str,
        chain: tuple[str, ...],
        locations: tuple[_Location, ...],
        stack: frozenset[str],
    ) -> None:
        if module_name in stack:
            module = by_name.get(module_name, [None])[0]
            if module is not None:
                facts.issue("django_include_cycle", module.path, 1)
            return
        if module_name not in owners:
            return
        for route in sorted(
            routes.get(module_name, ()),
            key=lambda item: (item.location.path, item.location.line, item.path),
        ):
            full = (
                _join_regex(prefix, route.path)
                if route.regex
                else _join_path(prefix, route.path)
            )
            _emit(facts, route, full, chain, locations)
        for include in sorted(
            includes.get(module_name, ()),
            key=lambda item: (item.location.path, item.location.line, item.module),
        ):
            if include.module not in owners:
                facts.issue(
                    "django_include_unresolved",
                    include.location.path,
                    include.location.line,
                )
                continue
            if include.regex:
                next_prefix = _join_regex(prefix, include.prefix)
            else:
                head = prefix
                if head and not head.endswith("/"):
                    head += "/"
                tail = (
                    include.prefix[1:]
                    if include.prefix.startswith("/")
                    else include.prefix
                )
                next_prefix = f"{head}{tail}"
            publish(
                include.module,
                next_prefix,
                chain
                + (
                    f"include:{include.location.path}:{include.location.line}:{include.module}",
                ),
                locations + (include.location,),
                stack | {module_name},
            )

    root = roots[0]
    publish(root, "", (f"urls:{root}",), (), frozenset())


def _line(node: ast.AST) -> int:
    return getattr(node, "lineno", 1) or 1


def _pairs(view: _View) -> tuple[tuple[str, tuple[str, ...]], ...]:
    if view.methods:
        if view.per_method:
            return tuple(
                (method, (target,))
                for method, target in zip(view.methods, view.targets, strict=True)
            )
        return tuple((method, view.targets) for method in view.methods)
    return (("", view.targets),)


def _emit(
    facts: _Facts,
    route: _Route,
    full_path: str,
    chain: tuple[str, ...],
    locations: tuple[_Location, ...],
) -> None:
    callable_index: dict[str, list[Entity]] = defaultdict(list)
    for entity in facts.entities.values():
        if entity.type == EntityType.CALLABLE:
            callable_index[entity.qualified_name].append(entity)
    for method, targets in _pairs(route.view):
        resolved: list[Entity] = []
        unresolved = False
        for target in targets:
            matches = callable_index.get(target, ())
            if len(matches) != 1:
                facts.issue(
                    "django_view_unresolved",
                    route.location.path,
                    route.location.line,
                )
                unresolved = True
                break
            resolved.append(matches[0])
        if unresolved:
            continue
        if not targets:
            facts.issue(
                "django_view_unresolved",
                route.location.path,
                route.location.line,
            )
        route_chain = chain + (
            f"route:{route.location.path}:{route.location.line}:{method or '-'}",
        )
        identifier = endpoint_id(
            facts.context.repository_id,
            route.location.path,
            route.view.label,
            method,
            full_path,
            route_chain,
        )
        label = f"{method} {full_path}".strip()
        attributes: list[tuple[str, str | tuple[str, ...]]] = [("path", full_path)]
        if method:
            attributes.append(("method", method))
        attributes.append(("registration_chain", route_chain))
        facts.entities[identifier] = Entity(
            identifier,
            facts.context.repository_id,
            facts.context.snapshot_id,
            EntityType.ENDPOINT,
            label,
            f"{route.view.label}:{method}:{full_path}",
            route.location.path,
            route.location.line,
            route.location.line,
            framework_kind="django_route",
            attributes=tuple(attributes),
        )
        facts.edge(
            EdgeType.EXPOSES,
            facts.context.repository_id,
            identifier,
            route.location,
            ROUTE_RULE,
        )
        for registration in locations:
            facts.edge(
                EdgeType.EXPOSES,
                facts.context.repository_id,
                identifier,
                registration,
                ROUTE_RULE,
            )
        for handler in resolved:
            facts.edge(
                EdgeType.HANDLED_BY,
                identifier,
                handler.id,
                route.location,
                HANDLER_RULE,
            )
