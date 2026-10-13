"""Static React Router navigation-route extraction over TypeScript parse units.

UI navigation routes reuse Endpoint with framework_kind=react-router and
attributes kind=navigation (no HTTP method, no repository EXPOSES). When a
static route element resolves to a page Callable, emit handled_by so view=flow
can expand route → page → calls. Analyzed modules are never imported or executed.
"""

from __future__ import annotations

from dataclasses import dataclass

from tree_sitter import Node

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
from rkg.adapters.route_flow import route_flow_attrs
from rkg.adapters.typescript_parse import (
    TsModule,
    child_named,
    identifier_name,
    named_children,
    resolve_specifier,
    string_literal,
    text_of,
    walk_named,
)
from rkg.adapters.typescript_resolution import _default_export_target
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

ROUTE_RULE = "RKG.react_router.route.v1"
HANDLER_RULE = "RKG.react_router.handler.v1"
DETECT_RULE = "RKG.react_router.detect.v1"
_MESSAGES = {
    "react_router_route_dynamic": "Route path is not a unique static literal.",
    "react_router_unresolved": "React Router registration could not be resolved.",
}
_ROUTER_FACTORIES = frozenset(
    {"createBrowserRouter", "createHashRouter", "createMemoryRouter"}
)


@dataclass(frozen=True, slots=True)
class _Location:
    path: str
    line: int


def _join(parent: str | None, child: str | None, *, index: bool) -> str | None:
    if index:
        if parent is None or parent == "":
            return "/"
        return parent
    if child is None:
        return None
    if child == "*":
        return "*"
    if child.startswith("/"):
        return child
    if parent is None or parent in {"", "/"}:
        return f"/{child}" if not child.startswith("/") else child
    return f"{parent.rstrip('/')}/{child}"


def _object_props(source: bytes, node: Node) -> dict[str, Node]:
    props: dict[str, Node] = {}
    if node.type != "object":
        return props
    for child in named_children(node):
        if child.type != "pair":
            continue
        key_node = child_named(child, "key")
        value = child_named(child, "value")
        if key_node is None or value is None:
            continue
        key = identifier_name(source, key_node) or string_literal(source, key_node)
        if key:
            props[key] = value
    return props


def _const_string(
    module: TsModule, name: str, modules: dict[str, TsModule]
) -> str | None:
    """Resolve a uniquely assigned module-level string constant, including imports."""
    # Local binding
    for node in named_children(module.tree.root_node):
        stmt = node
        if node.type == "export_statement":
            decl = child_named(node, "declaration")
            if decl is None:
                continue
            stmt = decl
        if stmt.type not in {"lexical_declaration", "variable_declaration"}:
            continue
        for declarator in named_children(stmt):
            if declarator.type != "variable_declarator":
                continue
            bound = identifier_name(module.source, child_named(declarator, "name"))
            value = child_named(declarator, "value")
            if bound == name and value is not None:
                literal = string_literal(module.source, value)
                return literal
    # Imported binding
    files = set(modules)
    aliases = next(iter(modules.values())).aliases if modules else {}
    for node in named_children(module.tree.root_node):
        if node.type != "import_statement":
            continue
        source_node = next(
            (child for child in named_children(node) if child.type == "string"), None
        )
        specifier = string_literal(module.source, source_node)
        if specifier is None:
            continue
        target_path = resolve_specifier(module.path, specifier, files, aliases)
        if target_path is None or target_path not in modules:
            continue
        target = modules[target_path]
        clause = next(
            (child for child in named_children(node) if child.type == "import_clause"),
            None,
        )
        if clause is None:
            continue
        for child in named_children(clause):
            if child.type != "named_imports":
                continue
            for spec in named_children(child):
                if spec.type != "import_specifier":
                    continue
                names = [
                    text_of(module.source, part)
                    for part in named_children(spec)
                    if part.type == "identifier"
                ]
                if not names:
                    continue
                imported, local = names[0], names[-1]
                if local == name:
                    return _const_string(target, imported, modules)
    return None


def _path_value(
    module: TsModule, value: Node, modules: dict[str, TsModule]
) -> str | None:
    literal = string_literal(module.source, value)
    if literal is not None:
        return literal
    if value.type == "identifier":
        return _const_string(module, text_of(module.source, value), modules)
    return None


def _jsx_component_name(source: bytes, node: Node | None) -> str | None:
    """Return the component identifier from a JSX element/value, if unique."""
    if node is None:
        return None
    target = node
    if node.type == "jsx_element":
        opening = child_named(node, "open_tag") or next(
            (
                child
                for child in named_children(node)
                if child.type == "jsx_opening_element"
            ),
            None,
        )
        target = opening if opening is not None else node
    if target.type in {"jsx_self_closing_element", "jsx_opening_element"}:
        name_node = child_named(target, "name") or next(
            (
                child
                for child in named_children(target)
                if child.type in {"identifier", "member_expression"}
            ),
            None,
        )
        if name_node is None:
            return None
        if name_node.type == "identifier":
            return text_of(source, name_node)
        # member_expression (Foo.Bar) — not a unique page binding
        return None
    if target.type == "identifier":
        return text_of(source, target)
    return None


def _resolve_component_binding(
    module: TsModule, local_name: str, modules: dict[str, TsModule]
) -> str | None:
    """Resolve a JSX component identifier to a Callable/Type qualified_name."""
    # Local module-level definition (const Page = () => … / function Page).
    for item in module.definitions:
        if item.owner == module.name and item.name == local_name:
            return item.qualified_name
    files = set(modules)
    aliases = next(iter(modules.values())).aliases if modules else {}
    for node in named_children(module.tree.root_node):
        if node.type != "import_statement":
            continue
        source_node = next(
            (child for child in named_children(node) if child.type == "string"), None
        )
        specifier = string_literal(module.source, source_node)
        if specifier is None:
            continue
        target_path = resolve_specifier(module.path, specifier, files, aliases)
        if target_path is None or target_path not in modules:
            continue
        target = modules[target_path]
        clause = next(
            (child for child in named_children(node) if child.type == "import_clause"),
            None,
        )
        if clause is None:
            continue
        for child in named_children(clause):
            if child.type == "identifier":
                if text_of(module.source, child) != local_name:
                    continue
                return _default_export_target(target)
            if child.type != "named_imports":
                continue
            for spec in named_children(child):
                if spec.type != "import_specifier":
                    continue
                names = [
                    text_of(module.source, part)
                    for part in named_children(spec)
                    if part.type == "identifier"
                ]
                if not names:
                    continue
                imported, local = names[0], names[-1]
                if local != local_name:
                    continue
                return f"{target.name}.{imported}"
    return None


def _lookup_callable(
    entities: dict[str, Entity], qualified_name: str
) -> Entity | None:
    matches = [
        item
        for item in entities.values()
        if item.type == EntityType.CALLABLE and item.qualified_name == qualified_name
    ]
    return matches[0] if len(matches) == 1 else None


def _collect_routes(
    module: TsModule,
    array: Node,
    parent: str | None,
    modules: dict[str, TsModule],
    diagnostics: list[AdapterDiagnostic],
) -> list[tuple[str, _Location, str | None]]:
    routes: list[tuple[str, _Location, str | None]] = []
    for element in named_children(array):
        line = element.start_point[0] + 1
        if element.type == "spread_element":
            diagnostics.append(
                AdapterDiagnostic("react_router_route_dynamic", module.path, line)
            )
            continue
        if element.type == "ternary_expression" or element.type == "binary_expression":
            diagnostics.append(
                AdapterDiagnostic("react_router_route_dynamic", module.path, line)
            )
            continue
        if element.type != "object":
            continue
        props = _object_props(module.source, element)
        index = "index" in props and text_of(module.source, props["index"]) == "true"
        path_node = props.get("path")
        path_value = (
            _path_value(module, path_node, modules) if path_node is not None else None
        )
        if path_node is not None and path_value is None:
            diagnostics.append(
                AdapterDiagnostic("react_router_route_dynamic", module.path, line)
            )
        element_name = _jsx_component_name(module.source, props.get("element"))
        joined = _join(parent, path_value, index=index)
        if joined is not None:
            routes.append((joined, _Location(module.path, line), element_name))
        # Pathless layout continues with same parent.
        next_parent = (
            joined
            if joined is not None and not index
            else (parent if path_node is None else joined)
        )
        if index:
            next_parent = parent if parent is not None else joined
        if path_node is None and not index:
            next_parent = parent
        elif joined is not None and not index:
            next_parent = joined
        children = props.get("children")
        if children is not None and children.type == "array":
            routes.extend(
                _collect_routes(module, children, next_parent, modules, diagnostics)
            )
    return routes


def _find_route_arrays(
    module: TsModule, modules: dict[str, TsModule]
) -> list[tuple[Node, _Location]]:
    found: list[tuple[Node, _Location]] = []
    # createBrowserRouter(appRoutes) or createBrowserRouter([...])
    for node in walk_named(module.tree.root_node):
        if node.type != "call_expression":
            continue
        callee = child_named(node, "function")
        name = identifier_name(module.source, callee)
        if name not in _ROUTER_FACTORIES:
            continue
        args = child_named(node, "arguments")
        if args is None or not named_children(args):
            continue
        arg = named_children(args)[0]
        line = node.start_point[0] + 1
        if arg.type == "array":
            found.append((arg, _Location(module.path, line)))
        elif arg.type == "identifier":
            array = _bound_array(module, text_of(module.source, arg))
            if array is not None:
                found.append((array, _Location(module.path, line)))
    return found


def _diagnose_dynamic_route_objects(
    module: TsModule,
    modules: dict[str, TsModule],
    diagnostics: list[AdapterDiagnostic],
) -> None:
    """Emit diagnostics for RouteObject-like `{ path: <non-static> }` shapes."""
    if b"react-router" not in module.source:
        return
    for node in walk_named(module.tree.root_node):
        if node.type != "object":
            continue
        props = _object_props(module.source, node)
        path_node = props.get("path")
        if path_node is None:
            continue
        if _path_value(module, path_node, modules) is not None:
            continue
        # Runtime / non-literal path — diagnostic only (no guessed route).
        diagnostics.append(
            AdapterDiagnostic(
                "react_router_route_dynamic",
                module.path,
                path_node.start_point[0] + 1,
            )
        )


def _bound_array(module: TsModule, name: str) -> Node | None:
    matches: list[Node] = []
    for node in named_children(module.tree.root_node):
        stmt = node
        if node.type == "export_statement":
            decl = child_named(node, "declaration")
            if decl is None:
                continue
            stmt = decl
        if stmt.type not in {"lexical_declaration", "variable_declaration"}:
            continue
        for declarator in named_children(stmt):
            if declarator.type != "variable_declarator":
                continue
            bound = identifier_name(module.source, child_named(declarator, "name"))
            value = child_named(declarator, "value")
            if bound == name and value is not None and value.type == "array":
                matches.append(value)
    return matches[0] if len(matches) == 1 else None


class ReactRouterFrameworkAdapter:
    """Extract static React Router navigation paths from TypeScript base facts."""

    entrypoint_required = False
    allow_unverified_versions = True
    reviewed_deep_support = False

    descriptor = AdapterDescriptor(
        adapter_id="rkg.react-router",
        adapter_version="0.1.0",
        contract_version=CONTRACT_VERSION,
        kind=AdapterKind.FRAMEWORK,
        language="typescript",
        framework="react-router-dom",
        grammar_or_target="tree-sitter TypeScript/TSX + React Router static routes",
        file_patterns=("*.ts", "*.tsx", "**/*.ts", "**/*.tsx"),
        ignore_patterns=("**/node_modules/**", "**/*.d.ts"),
        capabilities=("app", "routes"),
        technology_constraints=(
            TechnologyConstraint("react-router-dom", ">=6.0,<8.0"),
        ),
    )

    def technology_detectors(self) -> tuple[object, ...]:
        from rkg.detection.react_router import ReactRouterDetector

        return (ReactRouterDetector(),)
    def detect(self, manifest: SourceManifest, parsed: ParseResult) -> DetectionReport:
        evidence: list[DetectionEvidence] = []
        for unit in parsed.units:
            if unit.language != "typescript" or not isinstance(
                unit.representation, TsModule
            ):
                continue
            module: TsModule = unit.representation
            for node in walk_named(module.tree.root_node):
                if node.type != "call_expression":
                    continue
                name = identifier_name(module.source, child_named(node, "function"))
                if name in {
                    "createBrowserRouter",
                    "createHashRouter",
                    "createMemoryRouter",
                }:
                    evidence.append(DetectionEvidence(module.path, DETECT_RULE))
                    break
            text = module.source
            if b"react-router-dom" in text and not evidence:
                # import evidence without call still detects technology
                if any(
                    node.type == "import_statement"
                    and b"react-router-dom"
                    in module.source[node.start_byte : node.end_byte]
                    for node in named_children(module.tree.root_node)
                ):
                    evidence.append(DetectionEvidence(module.path, DETECT_RULE))
        for item in manifest.files:
            if (
                item.relative_path.endswith("package.json")
                and b"react-router-dom" in item.content
            ):
                evidence.append(DetectionEvidence(item.relative_path, DETECT_RULE))
        if not evidence:
            return DetectionReport()
        unique = tuple(
            DetectionEvidence(path, rule)
            for path, rule in sorted(
                {(item.relative_path, item.rule_id) for item in evidence}
            )
        )
        return DetectionReport((TechnologyDetection("react-router-dom", None, unique),))

    def extract(
        self, context: AdapterContext, parsed: ParseResult, base: FactBatch
    ) -> AdapterResult:
        modules = {
            unit.relative_path: unit.representation
            for unit in parsed.units
            if unit.language == "typescript"
            and isinstance(unit.representation, TsModule)
        }
        entities = {item.id: item for item in base.entities}
        edges = {item.id: item for item in base.edges}
        evidence = {item.id: item for item in base.evidence}
        diagnostics = list(base.diagnostics)
        issues: list[AdapterDiagnostic] = []

        def emit_edge(
            kind: EdgeType,
            source: str,
            target: str,
            location: _Location,
            rule: str,
        ) -> None:
            ref = evidence_id(
                context.snapshot_id,
                location.path,
                location.line,
                location.line,
                rule,
            )
            evidence[ref] = Evidence(
                ref,
                context.snapshot_id,
                location.path,
                location.line,
                location.line,
                rule,
            )
            key = edge_id(context.snapshot_id, kind, source, target)
            current = edges.get(key)
            references = set(current.evidence_ids) if current else set()
            references.add(ref)
            edges[key] = Edge(
                key,
                context.snapshot_id,
                kind,
                source,
                target,
                rule,
                tuple(sorted(references)),
            )

        for module in modules.values():
            _diagnose_dynamic_route_objects(module, modules, issues)
            for array, location in _find_route_arrays(module, modules):
                del location
                routes = _collect_routes(module, array, None, modules, issues)
                for path, route_location, element_name in routes:
                    chain = (
                        f"route:{route_location.path}:{route_location.line}:{path}",
                    )
                    identifier = endpoint_id(
                        context.repository_id,
                        route_location.path,
                        "navigation",
                        "",
                        path,
                        chain,
                    )
                    base_attrs: list[tuple[str, object]] = [
                        ("kind", "navigation"),
                        ("path", path),
                        ("route_path", path),
                        ("registration_chain", chain),
                    ]
                    entities[identifier] = Entity(
                        identifier,
                        context.repository_id,
                        context.snapshot_id,
                        EntityType.ENDPOINT,
                        path,
                        f"navigation:{path}",
                        route_location.path,
                        route_location.line,
                        route_location.line,
                        framework_kind="react-router",
                        attributes=tuple(base_attrs),
                    )
                    ref = evidence_id(
                        context.snapshot_id,
                        route_location.path,
                        route_location.line,
                        route_location.line,
                        ROUTE_RULE,
                    )
                    evidence[ref] = Evidence(
                        ref,
                        context.snapshot_id,
                        route_location.path,
                        route_location.line,
                        route_location.line,
                        ROUTE_RULE,
                    )
                    # Do not emit repository EXPOSES for UI navigation (not HTTP API).
                    if element_name is None:
                        continue
                    binding = _resolve_component_binding(
                        module, element_name, modules
                    )
                    handler = (
                        _lookup_callable(entities, binding) if binding else None
                    )
                    if handler is None:
                        issues.append(
                            AdapterDiagnostic(
                                "react_router_unresolved",
                                route_location.path,
                                route_location.line,
                            )
                        )
                        continue
                    entities[identifier] = Entity(
                        identifier,
                        context.repository_id,
                        context.snapshot_id,
                        EntityType.ENDPOINT,
                        path,
                        f"navigation:{path}",
                        route_location.path,
                        route_location.line,
                        route_location.line,
                        framework_kind="react-router",
                        attributes=tuple(
                            base_attrs
                            + list(route_flow_attrs(handler, entities, edges))
                        ),
                    )
                    emit_edge(
                        EdgeType.HANDLED_BY,
                        identifier,
                        handler.id,
                        route_location,
                        HANDLER_RULE,
                    )

        for ordinal, item in enumerate(
            sorted(
                {(i.code, i.relative_path, i.line): i for i in issues}.values(),
                key=lambda item: (item.relative_path or "", item.line or 0, item.code),
            )
        ):
            diagnostics.append(
                Diagnostic(
                    diagnostic_id(
                        context.job_id,
                        item.code,
                        item.relative_path,
                        item.line,
                        ordinal,
                    ),
                    context.job_id,
                    Severity.WARNING,
                    item.code,
                    _MESSAGES[item.code],
                    context.snapshot_id,
                    item.relative_path,
                    item.line,
                )
            )

        facts = FactBatch(
            context.repository_id,
            context.snapshot_id,
            tuple(entities[key] for key in sorted(entities)),
            tuple(edges[key] for key in sorted(edges)),
            tuple(evidence[key] for key in sorted(evidence)),
            tuple(diagnostics),
        )
        adapter_issues = tuple(
            sorted(
                {(i.code, i.relative_path, i.line): i for i in issues}.values(),
                key=lambda item: (item.relative_path or "", item.line or 0, item.code),
            )
        )
        return AdapterResult(
            facts,
            tuple(
                Capability(name, SupportState.SUPPORTED)
                for name in self.descriptor.capabilities
            ),
            adapter_issues,
        )

    def resolve(
        self, context: AdapterContext, parsed: ParseResult, candidate: FactBatch
    ) -> AdapterResult:
        if (
            candidate.repository_id != context.repository_id
            or candidate.snapshot_id != context.snapshot_id
        ):
            raise ValueError("candidate ownership does not match adapter context")
        return AdapterResult(
            candidate,
            tuple(
                Capability(name, SupportState.SUPPORTED)
                for name in self.descriptor.capabilities
            ),
            (),
        )
