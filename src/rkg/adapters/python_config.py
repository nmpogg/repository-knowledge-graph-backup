"""Literal configuration keys and outbound HTTP origins.

Values, defaults, query strings, payloads, credentials and URL paths are never
copied into facts or diagnostics. Only a static key or a scheme/host origin is kept.
"""

from __future__ import annotations

import ast
from collections import defaultdict
from collections.abc import Iterator, Sequence
from urllib.parse import urlsplit

from rkg.adapters.contracts import (
    AdapterContext,
    AdapterDiagnostic,
    ParseResult,
)
from rkg.adapters.python_language import (
    _canonical_diagnostics,
    _module_name,
    _unique_definitions,
)
from rkg.adapters.python_resolution import (
    _bindings,
    _frames,
    _Module,
    _parameter_names,
    _qualified,
    _scope_statements,
    _Stores,
)
from rkg.domain import (
    Edge,
    EdgeType,
    Entity,
    EntityType,
    Evidence,
    FactBatch,
    configuration_id,
    edge_id,
    evidence_id,
    source_entity_id,
)

CONFIG_RULE = "RKG.python_config.key.v1"
HTTP_RULE = "RKG.python_http.origin.v1"
SETTINGS_BASES = frozenset(
    {"pydantic_settings.BaseSettings", "pydantic.BaseSettings"}
)
ENV_READS = frozenset({"os.environ", "os.getenv", "os.environ.get"})
HTTP_METHODS = frozenset(
    {
        "get",
        "post",
        "put",
        "patch",
        "delete",
        "head",
        "options",
        "request",
        "stream",
    }
)
HTTP_FUNCTIONS = frozenset(
    f"{library}.{method}"
    for library in ("requests", "httpx")
    for method in HTTP_METHODS
    if not (library == "requests" and method == "stream")
)
CLIENTS = {
    "requests.Session": "requests",
    "httpx.Client": "httpx",
    "httpx.AsyncClient": "httpx",
}
_SKIP_FIELDS = frozenset({"model_config", "model_fields"})
_MISSING = object()


def _visible(name: str | None, roots: set[str]) -> str | None:
    if name is None or name.split(".", 1)[0] in roots:
        return None
    return name


def _literal(node: ast.expr | None) -> str | None:
    if (
        isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value
        and "\n" not in node.value
        and "\r" not in node.value
        and "\x00" not in node.value
    ):
        return node.value
    return None


def _argument(node: ast.Call, name: str, index: int) -> ast.expr | None:
    for keyword in node.keywords:
        if keyword.arg == name:
            return keyword.value
    if len(node.args) > index:
        return node.args[index]
    return None


def _origin(url: str) -> str | None:
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError:
        return None
    scheme = parts.scheme.lower()
    if scheme not in {"http", "https"} or not parts.hostname or not parts.netloc:
        return None
    host = f"[{parts.hostname}]" if ":" in parts.hostname else parts.hostname
    if port and not (
        (scheme == "https" and port == 443) or (scheme == "http" and port == 80)
    ):
        return f"{scheme}://{host}:{port}"
    return f"{scheme}://{host}"


def _classvar(annotation: ast.expr) -> bool:
    node = annotation.value if isinstance(annotation, ast.Subscript) else annotation
    if isinstance(node, ast.Name):
        return node.id == "ClassVar"
    return isinstance(node, ast.Attribute) and node.attr == "ClassVar"


def _fields(node: ast.ClassDef) -> tuple[tuple[str, int], ...]:
    found: list[tuple[str, int]] = []
    seen: set[str] = set()
    for statement in node.body:
        names: list[tuple[str, int]] = []
        if isinstance(statement, ast.AnnAssign) and isinstance(
            statement.target, ast.Name
        ):
            if statement.annotation is None or not _classvar(statement.annotation):
                names.append((statement.target.id, statement.lineno))
        elif isinstance(statement, ast.Assign):
            for target in statement.targets:
                if isinstance(target, ast.Name):
                    names.append((target.id, statement.lineno))
        for name, line in names:
            if name in _SKIP_FIELDS or name in seen:
                continue
            seen.add(name)
            found.append((name, line))
    return tuple(found)


def _ctor(
    expression: ast.expr,
    frames: Sequence[dict[str, str | None]],
    roots: set[str],
    settings_classes: set[str],
) -> tuple[str, str] | None:
    node = expression.value if isinstance(expression, ast.Await) else expression
    if not isinstance(node, ast.Call):
        return None
    qualified = _qualified(node.func, frames)
    external = _visible(qualified, roots)
    if external in CLIENTS:
        return ("client", CLIENTS[external])
    # A local settings class is not an external root, so shadowing does not apply.
    if qualified in settings_classes:
        return ("settings", qualified)
    return None


def _instances(
    body: Sequence[ast.stmt],
    frames: Sequence[dict[str, str | None]],
    roots: set[str],
    settings_classes: set[str],
    parameters: set[str],
) -> dict[str, tuple[str, str] | None]:
    found: dict[str, set[tuple[str, str]]] = defaultdict(set)
    unknown = set(parameters)

    def accept(name: str, kind: tuple[str, str] | None, conditional: bool) -> None:
        if conditional or kind is None:
            unknown.add(name)
        else:
            found[name].add(kind)

    for statement, conditional in _scope_statements(body):
        pairs: list[tuple[str, tuple[str, str]]] = []
        recognized = False
        if isinstance(statement, ast.Assign) and all(
            isinstance(target, ast.Name) for target in statement.targets
        ):
            kind = _ctor(statement.value, frames, roots, settings_classes)
            if kind and statement.targets:
                recognized = True
                pairs.extend((target.id, kind) for target in statement.targets)
        elif (
            isinstance(statement, ast.AnnAssign)
            and isinstance(statement.target, ast.Name)
            and statement.value is not None
        ):
            kind = _ctor(statement.value, frames, roots, settings_classes)
            if kind:
                recognized = True
                pairs.append((statement.target.id, kind))
        elif isinstance(statement, (ast.With, ast.AsyncWith)):
            with_pairs: list[tuple[str, tuple[str, str]]] = []
            valid = True
            for item in statement.items:
                if not isinstance(item.optional_vars, ast.Name):
                    if item.optional_vars is not None:
                        valid = False
                    continue
                kind = _ctor(item.context_expr, frames, roots, settings_classes)
                if kind is None:
                    valid = False
                    break
                with_pairs.append((item.optional_vars.id, kind))
            if valid and with_pairs:
                recognized = True
                pairs.extend(with_pairs)
        if recognized:
            for name, kind in pairs:
                accept(name, kind, conditional)
            continue
        stores = _Stores()
        stores.visit(statement)
        unknown.update(stores.names)
    resolved: dict[str, tuple[str, str] | None] = {name: None for name in unknown}
    for name, kinds in found.items():
        unique = len(kinds) == 1 and name not in unknown
        resolved[name] = next(iter(kinds)) if unique else None
    return resolved


def _nodes(body: Sequence[ast.stmt]) -> Iterator[ast.AST]:
    pending = list(body)
    while pending:
        node = pending.pop()
        if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)
        ):
            continue
        if isinstance(node, ast.ClassDef):
            pending.extend(node.body)
            continue
        yield node
        pending.extend(ast.iter_child_nodes(node))


def _settings_owner(
    expression: ast.expr,
    frames: Sequence[dict[str, str | None]],
    roots: set[str],
    instances: dict[str, tuple[str, str] | None],
    settings_classes: set[str],
    self_class: str | None,
) -> str | None:
    if isinstance(expression, ast.Name):
        if expression.id in {"self", "cls"} and self_class:
            return self_class
        if expression.id in instances:
            mapped = instances[expression.id]
            if mapped and mapped[0] == "settings":
                return mapped[1]
            return None
        visible = _qualified(expression, frames)
        if visible in settings_classes:
            return visible
        return None
    kind = _ctor(expression, frames, roots, settings_classes)
    if kind and kind[0] == "settings":
        return kind[1]
    return None


def _client_library(
    expression: ast.expr,
    frames: Sequence[dict[str, str | None]],
    roots: set[str],
    instances: dict[str, tuple[str, str] | None],
    settings_classes: set[str],
) -> str | None:
    if isinstance(expression, ast.Name) and expression.id in instances:
        mapped = instances[expression.id]
        if mapped and mapped[0] == "client":
            return mapped[1]
        return None
    kind = _ctor(expression, frames, roots, settings_classes)
    if kind and kind[0] == "client":
        return kind[1]
    return None


class _Facts:
    def __init__(self, context: AdapterContext, candidate: FactBatch) -> None:
        self.context = context
        self.entities = {item.id: item for item in candidate.entities}
        self.edges = {item.id: item for item in candidate.edges}
        self.evidence = {item.id: item for item in candidate.evidence}
        self.diagnostics: list[AdapterDiagnostic] = []
        self.roots = {
            item.qualified_name.split(".", 1)[0]
            for item in candidate.entities
            if item.type == EntityType.SOURCE_UNIT and item.qualified_name
        }

    def user(
        self, path: str, qualified_name: str, entity_type: EntityType
    ) -> Entity | None:
        matches = [
            item
            for item in self.entities.values()
            if item.type == entity_type
            and item.qualified_name == qualified_name
            and item.file_path == path
        ]
        return matches[0] if len(matches) == 1 else None

    def unresolved(self, code: str, path: str, line: int) -> None:
        self.diagnostics.append(AdapterDiagnostic(code, path, line))

    def link(
        self,
        user_id: str,
        target: Entity,
        path: str,
        line: int,
        rule: str,
    ) -> None:
        self.entities[target.id] = target
        ref_id = evidence_id(self.context.snapshot_id, path, line, line, rule)
        self.evidence[ref_id] = Evidence(
            ref_id, self.context.snapshot_id, path, line, line, rule
        )
        key = edge_id(self.context.snapshot_id, EdgeType.DEPENDS_ON, user_id, target.id)
        current = self.edges.get(key)
        references = set(current.evidence_ids) if current else set()
        references.add(ref_id)
        self.edges[key] = Edge(
            key,
            self.context.snapshot_id,
            EdgeType.DEPENDS_ON,
            user_id,
            target.id,
            rule,
            tuple(sorted(references)),
        )

    def configuration(
        self,
        kind: str,
        owner: str,
        key: str,
        path: str,
        line: int,
    ) -> Entity:
        entity_id = configuration_id(self.context.repository_id, kind, owner, key)
        current = self.entities.get(entity_id)
        if current is not None:
            return current
        qualified = f"{kind}:{owner}:{key}" if owner else f"{kind}:{key}"
        return Entity(
            entity_id,
            self.context.repository_id,
            self.context.snapshot_id,
            EntityType.CONFIGURATION,
            key,
            qualified,
            path,
            line,
            line,
            kind,
            attributes=(("kind", kind), ("owner", owner)),
        )

    def http_service(self, origin: str) -> Entity:
        entity_id = source_entity_id(
            self.context.repository_id,
            "",
            EntityType.EXTERNAL_DEPENDENCY,
            f"http_service:{origin}",
        )
        current = self.entities.get(entity_id)
        if current is not None:
            return current
        return Entity(
            entity_id,
            self.context.repository_id,
            self.context.snapshot_id,
            EntityType.EXTERNAL_DEPENDENCY,
            origin,
            origin,
            language_kind="http_service",
            attributes=(("kind", "http_service"), ("origin", origin)),
        )


def _settings_classes(
    module: _Module,
    definitions: dict[str, tuple[str, ast.AST]],
    definitions_list: Sequence[tuple[str, str, ast.AST]],
    module_frame: dict[str, str | None],
    roots: set[str],
) -> dict[str, tuple[tuple[str, int], ...]]:
    found: dict[str, tuple[tuple[str, int], ...]] = {}
    for owner, name, node in definitions_list:
        if not isinstance(node, ast.ClassDef):
            continue
        frames = _frames(owner, module, definitions, module_frame)
        explicit = False
        for base in node.bases:
            target = base.value if isinstance(base, ast.Subscript) else base
            if _visible(_qualified(target, frames), roots) in SETTINGS_BASES:
                explicit = True
        if explicit:
            found[name] = _fields(node)
    return found


def _record_url(
    facts: _Facts,
    user_id: str,
    path: str,
    line: int,
    expression: ast.expr | None,
) -> None:
    literal = _literal(expression)
    origin = _origin(literal) if literal else None
    if origin is None:
        facts.unresolved("python_http_unresolved", path, line)
        return
    facts.link(user_id, facts.http_service(origin), path, line, HTTP_RULE)


def _scan_scope(
    facts: _Facts,
    module: _Module,
    body: Sequence[ast.stmt],
    frames: Sequence[dict[str, str | None]],
    user_id: str,
    settings_classes: dict[str, tuple[tuple[str, int], ...]],
    self_class: str | None,
    parameters: set[str],
) -> None:
    instances = _instances(
        body, frames, facts.roots, set(settings_classes), parameters
    )
    calls: list[ast.Call] = []
    attributes: list[ast.Attribute] = []
    for node in _nodes(body):
        if isinstance(node, ast.Call):
            calls.append(node)
        elif isinstance(node, ast.Attribute):
            attributes.append(node)
        elif isinstance(node, ast.Subscript):
            if _visible(_qualified(node.value, frames), facts.roots) != "os.environ":
                continue
            key = _literal(node.slice if isinstance(node.slice, ast.expr) else None)
            if key is None:
                facts.unresolved("python_config_unresolved", module.path, node.lineno)
                continue
            facts.link(
                user_id,
                facts.configuration("environment", "", key, module.path, node.lineno),
                module.path,
                node.lineno,
                CONFIG_RULE,
            )
    called = {id(node.func) for node in calls}
    for node in attributes:
        if id(node) in called:
            continue
        owner = _settings_owner(
            node.value,
            frames,
            facts.roots,
            instances,
            set(settings_classes),
            self_class,
        )
        if owner is None or not any(
            name == node.attr for name, _ in settings_classes.get(owner, ())
        ):
            continue
        line = next(
            item_line
            for name, item_line in settings_classes[owner]
            if name == node.attr
        )
        facts.link(
            user_id,
            facts.configuration("settings", owner, node.attr, module.path, line),
            module.path,
            node.lineno,
            CONFIG_RULE,
        )
    for node in calls:
        qualified = _visible(_qualified(node.func, frames), facts.roots)
        if qualified in {"os.getenv", "os.environ.get"}:
            key = _literal(_argument(node, "key", 0))
            if key is None:
                facts.unresolved("python_config_unresolved", module.path, node.lineno)
                continue
            facts.link(
                user_id,
                facts.configuration("environment", "", key, module.path, node.lineno),
                module.path,
                node.lineno,
                CONFIG_RULE,
            )
            continue
        if qualified in HTTP_FUNCTIONS:
            method = qualified.rsplit(".", 1)[-1]
            index = 1 if method in {"request", "stream"} else 0
            _record_url(
                facts, user_id, module.path, node.lineno, _argument(node, "url", index)
            )
            continue
        if (
            not isinstance(node.func, ast.Attribute)
            or node.func.attr not in HTTP_METHODS
        ):
            continue
        if (
            _client_library(
                node.func.value, frames, facts.roots, instances, set(settings_classes)
            )
            is None
        ):
            continue
        index = 1 if node.func.attr in {"request", "stream"} else 0
        _record_url(
            facts, user_id, module.path, node.lineno, _argument(node, "url", index)
        )


def add_config_http_facts(
    context: AdapterContext, parsed: ParseResult, candidate: FactBatch
) -> tuple[FactBatch, tuple[AdapterDiagnostic, ...]]:
    """Add configuration and literal HTTP origins without copying sensitive values."""
    facts = _Facts(context, candidate)
    for unit in parsed.units:
        if not isinstance(unit.representation, ast.Module):
            continue
        module = _Module(
            unit.relative_path, _module_name(unit.relative_path), unit.representation
        )
        source = facts.user(module.path, module.name, EntityType.SOURCE_UNIT)
        if source is None:
            continue
        module_frame = _bindings(module, module.tree.body, module.name)
        definitions_list, _ = _unique_definitions(module.tree, module.name, module.path)
        definitions = {name: (owner, node) for owner, name, node in definitions_list}
        settings = _settings_classes(
            module, definitions, definitions_list, module_frame, facts.roots
        )
        for name, fields in settings.items():
            for field, line in fields:
                facts.link(
                    source.id,
                    facts.configuration("settings", name, field, module.path, line),
                    module.path,
                    line,
                    CONFIG_RULE,
                )
        _scan_scope(
            facts,
            module,
            module.tree.body,
            (module_frame,),
            source.id,
            settings,
            None,
            set(),
        )
        for owner, name, node in definitions_list:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            caller = facts.user(module.path, name, EntityType.CALLABLE)
            if caller is None:
                continue
            _scan_scope(
                facts,
                module,
                node.body,
                _frames(name, module, definitions, module_frame),
                caller.id,
                settings,
                owner if owner in settings else None,
                _parameter_names(node),
            )
    ordered = tuple(
        sorted(
            facts.diagnostics,
            key=lambda item: (item.relative_path or "", item.line or 0, item.code),
        )
    )
    batch = FactBatch(
        context.repository_id,
        context.snapshot_id,
        tuple(facts.entities[key] for key in sorted(facts.entities)),
        tuple(facts.edges[key] for key in sorted(facts.edges)),
        tuple(facts.evidence[key] for key in sorted(facts.evidence)),
        candidate.diagnostics + _canonical_diagnostics(context, ordered),
    )
    return batch, ordered
