"""Static Spring Web MVC endpoint extraction over parsed Java units.

Only registered @RestController / @Controller beans with static path composition
emit Endpoints. Dynamic `${...}` / SpEL paths become diagnostics.

Statically registered OncePerRequestFilter and HandlerInterceptor types are
evidence. An integer order is stored on the existing Type only when every
order expression is the same literal or the same unique constant.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace

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
from rkg.adapters.java_parse import (
    JavaModule,
    JavaType,
    annotation_has,
    annotation_named,
    iter_types,
    named_children,
    resolve_constant,
    text_of,
    walk_named,
)
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

DETECT_RULE = "RKG.spring.detect.v1"
ROUTE_RULE = "RKG.spring.route.v1"
HANDLER_RULE = "RKG.spring.handler.v1"
REGISTRATION_RULE = "RKG.spring.registration.v1"
_MESSAGES = {
    "spring_route_dynamic": "Route path, method or handler is not static.",
    "spring_controller_unregistered": "Mapping found on a non-controller type.",
    "spring_filter_unregistered": "Filter or interceptor is not statically registered.",
    "spring_filter_ambiguous": "Filter or interceptor registration target is not a unique literal type.",
    "spring_filter_order_ambiguous": "Filter or interceptor order is not a single literal or unique constant.",
    "spring_filter_target_ambiguous": "Filter or interceptor path does not resolve to exactly one endpoint.",
}
_BEAN_ANNOTATIONS = (
    "Component",
    "Service",
    "Repository",
    "Configuration",
    "Controller",
    "RestController",
)
_REGISTER_METHODS = frozenset({"addInterceptor", "setFilter"})
_ORDER_METHODS = frozenset({"order", "setOrder"})
_PATH_METHODS = frozenset({"addPathPatterns", "addUrlPatterns", "setUrlPatterns"})
_INT_CONST = re.compile(r"-?\d+")
_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*")
_MAPPING = {
    "GetMapping": ("GET",),
    "PostMapping": ("POST",),
    "PutMapping": ("PUT",),
    "PatchMapping": ("PATCH",),
    "DeleteMapping": ("DELETE",),
    "RequestMapping": (),
}
_REQUEST_METHODS = {
    "RequestMethod.GET": "GET",
    "RequestMethod.POST": "POST",
    "RequestMethod.PUT": "PUT",
    "RequestMethod.PATCH": "PATCH",
    "RequestMethod.DELETE": "DELETE",
    "RequestMethod.HEAD": "HEAD",
    "RequestMethod.OPTIONS": "OPTIONS",
    "GET": "GET",
    "POST": "POST",
    "PUT": "PUT",
    "PATCH": "PATCH",
    "DELETE": "DELETE",
    "HEAD": "HEAD",
    "OPTIONS": "OPTIONS",
}


def _modules(parsed: ParseResult) -> dict[str, JavaModule]:
    return {
        unit.relative_path: unit.representation
        for unit in parsed.units
        if isinstance(unit.representation, JavaModule)
    }


def _join(prefix: str, route: str) -> str:
    if not route:
        return prefix or "/"
    if not prefix:
        return route if route.startswith("/") else f"/{route}"
    if route.startswith("/"):
        return prefix.rstrip("/") + route
    return prefix.rstrip("/") + "/" + route


def _annotation_path(modules: dict[str, JavaModule], owner, annotation) -> str | None:
    if not annotation.arguments:
        return ""
    for key, value in annotation.arguments:
        if key in {None, "value", "path"}:
            text = value.strip()
            if text.startswith('"') and text.endswith('"'):
                return text[1:-1]
            if "${" in text or "#{" in text:
                return None
            resolved = resolve_constant(modules, owner, text)
            if resolved is not None:
                return resolved
            return None
    return ""


def _annotation_methods(annotation) -> tuple[str, ...] | None:
    if annotation.name != "RequestMapping":
        return _MAPPING.get(annotation.name)
    methods: list[str] = []
    for key, value in annotation.arguments:
        if key not in {None, "method"} and key is not None:
            continue
        if key == "method" or "RequestMethod" in value or value.strip("{ }"):
            raw = value.strip()
            if raw.startswith("{") and raw.endswith("}"):
                raw = raw[1:-1]
            for part in raw.split(","):
                token = part.strip()
                mapped = _REQUEST_METHODS.get(token)
                if mapped:
                    methods.append(mapped)
                elif token:
                    return None
    if annotation.name in _MAPPING and annotation.name != "RequestMapping":
        return _MAPPING[annotation.name]
    return tuple(methods) if methods else ("GET",)


def _simple_type(label: str) -> str:
    return label.split("<", 1)[0].split(".")[-1].strip()


def _type_source(modules: dict[str, JavaModule], item: JavaType) -> bytes:
    for module in modules.values():
        for candidate in iter_types(module):
            if (
                candidate.qualified_name == item.qualified_name
                and candidate.start_line == item.start_line
            ):
                return module.source
    return b""


def _is_abstract(source: bytes, item: JavaType) -> bool:
    for child in named_children(item.node):
        if child.type != "modifiers":
            continue
        for part in named_children(child):
            if part.type == "modifier" and text_of(source, part) == "abstract":
                return True
    return False


def _resolve_declared(
    modules: dict[str, JavaModule], name: str
) -> JavaType | None:
    raw = name.split("<", 1)[0].strip()
    simple = raw.split(".")[-1]
    found: dict[str, JavaType] = {}
    for module in modules.values():
        for item in iter_types(module):
            if item.name == simple or item.qualified_name == raw:
                found[item.qualified_name] = item
    if "." in raw:
        narrowed = [
            item
            for item in found.values()
            if item.qualified_name == raw
            or item.qualified_name.endswith("." + raw)
            or raw.endswith(item.qualified_name)
        ]
        if len(narrowed) == 1:
            return narrowed[0]
        return None
    if len(found) == 1:
        return next(iter(found.values()))
    return None


def _role(
    modules: dict[str, JavaModule], item: JavaType, seen: set[str] | None = None
) -> str | None:
    seen = set() if seen is None else seen
    if item.qualified_name in seen:
        return None
    seen.add(item.qualified_name)
    if "OncePerRequestFilter" in {_simple_type(part) for part in item.extends}:
        return "filter"
    if "HandlerInterceptor" in {_simple_type(part) for part in item.implements}:
        return "interceptor"
    for label in (*item.extends, *item.implements):
        parent = _resolve_declared(modules, label)
        if parent is None:
            continue
        found = _role(modules, parent, seen)
        if found:
            return found
    return None


def _static_int(
    modules: dict[str, JavaModule], expression: str, depth: int = 0
) -> int | None:
    text = expression.strip()
    if text.startswith("(") and text.endswith(")"):
        text = text[1:-1].strip()
    if _INT_CONST.fullmatch(text):
        return int(text)
    if depth > 2 or not _IDENT.fullmatch(text):
        return None
    found: list[str] = []
    for module in modules.values():
        for item in iter_types(module):
            for fname, _typ, value, _line in item.fields:
                if not value:
                    continue
                identities = {
                    fname,
                    f"{item.name}.{fname}",
                    f"{item.qualified_name}.{fname}",
                }
                if text not in identities:
                    continue
                found.append(value)
    if len(found) != 1:
        return None
    raw = found[0][1:] if found[0].startswith("@") else found[0]
    if _INT_CONST.fullmatch(raw):
        return int(raw)
    return _static_int(modules, raw, depth + 1)


def _orders_from_annotations(
    modules: dict[str, JavaModule], annotations
) -> tuple[list[int], bool]:
    values: list[int] = []
    bad = False
    for annotation in annotations:
        if annotation.name != "Order" or not annotation.arguments:
            continue
        value = _static_int(modules, annotation.arguments[0][1])
        if value is None:
            bad = True
        else:
            values.append(value)
    return values, bad


def _invocation_name(source: bytes, node) -> str:
    name = ""
    for child in named_children(node):
        if child.type == "identifier":
            name = text_of(source, child)
    return name


def _arg_nodes(node) -> tuple:
    for child in named_children(node):
        if child.type == "argument_list":
            return named_children(child)
    return ()


def _created_type_name(source: bytes, node) -> str | None:
    for child in named_children(node):
        if child.type in {
            "type_identifier",
            "scoped_type_identifier",
            "generic_type",
            "scoped_identifier",
        }:
            return text_of(source, child).split("<", 1)[0].strip()
    return None


def _class_literal_name(source: bytes, node) -> str | None:
    for child in named_children(node):
        if child.type in {"type_identifier", "scoped_type_identifier", "generic_type"}:
            return text_of(source, child).split("<", 1)[0].strip()
    raw = text_of(source, node).strip()
    if raw.endswith(".class"):
        return raw[: -len(".class")].strip()
    return None


def _unwrap(node):
    current = node
    while current is not None and current.type == "parenthesized_expression":
        kids = named_children(current)
        current = kids[0] if len(kids) == 1 else None
    return current


def _static_int_node(modules: dict[str, JavaModule], source: bytes, node) -> int | None:
    current = _unwrap(node)
    if current is None:
        return None
    if current.type == "decimal_integer_literal":
        raw = text_of(source, current)
        return int(raw) if _INT_CONST.fullmatch(raw) else None
    if current.type == "unary_expression":
        raw = text_of(source, current).replace(" ", "")
        return int(raw) if _INT_CONST.fullmatch(raw) else None
    if current.type in {"identifier", "field_access", "scoped_identifier"}:
        return _static_int(modules, text_of(source, current))
    return None


def _static_string(
    modules: dict[str, JavaModule], owner: JavaType, source: bytes, node
) -> str | None:
    current = _unwrap(node)
    if current is None:
        return None
    if current.type == "string_literal":
        for child in named_children(current):
            if child.type == "string_fragment":
                return text_of(source, child)
        raw = text_of(source, current)
        if len(raw) >= 2 and raw[0] == '"' and raw[-1] == '"':
            return raw[1:-1]
        return None
    if current.type in {"identifier", "field_access", "scoped_identifier"}:
        return resolve_constant(modules, owner, text_of(source, current))
    return None


def _method_block(callable_item):
    for child in named_children(callable_item.node):
        if child.type == "block":
            return child
    return None


@dataclass(frozen=True, slots=True)
class _RegistrationSite:
    qualified_name: str
    path: str
    line: int
    orders: tuple[int, ...]
    order_bad: bool
    patterns: tuple[str, ...]
    pattern_bad: bool


def _registration_names(source: bytes, root) -> tuple[list[str], bool, int | None]:
    """Type names passed literally to setFilter or addInterceptor."""
    names: list[str] = []
    ambiguous = False
    line: int | None = None
    for node in walk_named(root):
        if node.type != "method_invocation":
            continue
        if _invocation_name(source, node) not in _REGISTER_METHODS:
            continue
        args = _arg_nodes(node)
        site_line = node.start_point[0] + 1
        if len(args) != 1:
            ambiguous = True
            line = line or site_line
            continue
        arg = _unwrap(args[0])
        created = None
        if arg is not None and arg.type == "object_creation_expression":
            created = _created_type_name(source, arg)
        elif arg is not None and arg.type == "class_literal":
            created = _class_literal_name(source, arg)
        if created:
            names.append(created)
            line = line or site_line
        else:
            ambiguous = True
            line = line or site_line
    return names, ambiguous, line


def _returned_type_names(source: bytes, root) -> list[str]:
    names: list[str] = []
    for node in named_children(root):
        if node.type != "return_statement":
            continue
        expr = _unwrap(next(iter(named_children(node)), None))
        if expr is not None and expr.type == "object_creation_expression":
            created = _created_type_name(source, expr)
            if created:
                names.append(created)
    return names


def _orders_in(modules: dict[str, JavaModule], source: bytes, root) -> tuple[list[int], bool]:
    values: list[int] = []
    bad = False
    for node in walk_named(root):
        if node.type != "method_invocation":
            continue
        if _invocation_name(source, node) not in _ORDER_METHODS:
            continue
        args = _arg_nodes(node)
        if len(args) != 1:
            bad = True
            continue
        value = _static_int_node(modules, source, args[0])
        if value is None:
            bad = True
        else:
            values.append(value)
    return values, bad


def _patterns_in(
    modules: dict[str, JavaModule], owner: JavaType, source: bytes, root
) -> tuple[list[str], bool]:
    patterns: list[str] = []
    bad = False
    for node in walk_named(root):
        if node.type != "method_invocation":
            continue
        if _invocation_name(source, node) not in _PATH_METHODS:
            continue
        args = _arg_nodes(node)
        if not args:
            bad = True
            continue
        for arg in args:
            value = _static_string(modules, owner, source, arg)
            if value is None:
                bad = True
            else:
                patterns.append(value)
    return patterns, bad


def _bean_line(item: JavaType) -> int | None:
    for annotation in item.annotations:
        if annotation.name in _BEAN_ANNOTATIONS:
            return annotation.line
    return None


def _consider_method_site(
    modules: dict[str, JavaModule],
    module: JavaModule,
    owner: JavaType,
    callable_item,
    root,
    sites: list[_RegistrationSite],
    issues: list[AdapterDiagnostic],
) -> None:
    names, ambiguous, line = _registration_names(module.source, root)
    if ambiguous:
        issues.append(
            AdapterDiagnostic(
                "spring_filter_ambiguous",
                module.path,
                line or callable_item.start_line,
            )
        )
    resolved: list[JavaType] = []
    for name in names:
        target = _resolve_declared(modules, name)
        if (
            not isinstance(target, JavaType)
            or _role(modules, target) is None
            or _is_abstract(_type_source(modules, target), target)
        ):
            issues.append(
                AdapterDiagnostic(
                    "spring_filter_ambiguous",
                    module.path,
                    line or callable_item.start_line,
                )
            )
            continue
        resolved.append(target)
    for name in _returned_type_names(module.source, root):
        target = _resolve_declared(modules, name)
        if (
            isinstance(target, JavaType)
            and _role(modules, target) is not None
            and not _is_abstract(_type_source(modules, target), target)
        ):
            resolved.append(target)
            line = line or callable_item.start_line
    unique = {item.qualified_name: item for item in resolved}
    if len(unique) != 1:
        if len(unique) > 1:
            issues.append(
                AdapterDiagnostic(
                    "spring_filter_ambiguous",
                    module.path,
                    line or callable_item.start_line,
                )
            )
        return
    if ambiguous:
        return
    target = next(iter(unique.values()))
    ann_orders, ann_bad = _orders_from_annotations(modules, callable_item.annotations)
    call_orders, call_bad = _orders_in(modules, module.source, root)
    patterns, pattern_bad = _patterns_in(modules, owner, module.source, root)
    sites.append(
        _RegistrationSite(
            target.qualified_name,
            module.path,
            line or callable_item.start_line,
            tuple(ann_orders + call_orders),
            ann_bad or call_bad,
            tuple(patterns),
            pattern_bad,
        )
    )


def _extract_filter_registrations(
    context: AdapterContext,
    modules: dict[str, JavaModule],
    entities: dict,
    edges: dict,
    evidence: dict,
    issues: list[AdapterDiagnostic],
    by_qn: dict,
) -> None:
    sites: list[_RegistrationSite] = []
    for module in modules.values():
        for item in iter_types(module):
            if item.kind not in {"class", "record"}:
                continue
            role = _role(modules, item)
            bean_line = _bean_line(item)
            if (
                role
                and bean_line is not None
                and not _is_abstract(module.source, item)
            ):
                orders, order_bad = _orders_from_annotations(modules, item.annotations)
                sites.append(
                    _RegistrationSite(
                        item.qualified_name,
                        module.path,
                        bean_line,
                        tuple(orders),
                        order_bad,
                        (),
                        False,
                    )
                )
            if bean_line is None:
                continue
            for callable_item in item.callables:
                block = _method_block(callable_item)
                if block is None:
                    continue
                is_bean = annotation_has(callable_item, "Bean")
                is_mvc = (
                    callable_item.name == "addInterceptors"
                    and "WebMvcConfigurer" in {_simple_type(part) for part in item.implements}
                )
                if not is_bean and not is_mvc:
                    continue
                if is_mvc:
                    for statement in named_children(block):
                        if statement.type != "expression_statement":
                            continue
                        _consider_method_site(
                            modules,
                            module,
                            item,
                            callable_item,
                            statement,
                            sites,
                            issues,
                        )
                else:
                    _consider_method_site(
                        modules,
                        module,
                        item,
                        callable_item,
                        block,
                        sites,
                        issues,
                    )

    registered = {site.qualified_name for site in sites}
    for module in modules.values():
        for item in iter_types(module):
            if item.kind not in {"class", "record"} or _is_abstract(module.source, item):
                continue
            if _role(modules, item) is None or item.qualified_name in registered:
                continue
            issues.append(
                AdapterDiagnostic(
                    "spring_filter_unregistered", module.path, item.start_line
                )
            )

    by_type: dict[str, list[_RegistrationSite]] = {}
    for site in sites:
        by_type.setdefault(site.qualified_name, []).append(site)
    for qualified_name, group in by_type.items():
        java_type = _resolve_declared(modules, qualified_name)
        if not isinstance(java_type, JavaType):
            continue
        order_values: list[int] = []
        order_bad = False
        for site in group:
            order_values.extend(site.orders)
            order_bad = order_bad or site.order_bad
        if order_bad or len(set(order_values)) > 1:
            issues.append(
                AdapterDiagnostic(
                    "spring_filter_order_ambiguous",
                    group[0].path,
                    group[0].line,
                )
            )
        elif order_values:
            entity = by_qn.get(java_type.qualified_name)
            if entity is not None and entity.type == EntityType.TYPE:
                if not any(key == "order" for key, _value in entity.attributes):
                    updated = replace(
                        entity,
                        attributes=(*entity.attributes, ("order", order_values[0])),
                    )
                    entities[updated.id] = updated
                    by_qn[updated.qualified_name] = updated
        for site in group:
            ref = evidence_id(
                context.snapshot_id,
                site.path,
                site.line,
                site.line,
                REGISTRATION_RULE,
            )
            evidence[ref] = Evidence(
                ref,
                context.snapshot_id,
                site.path,
                site.line,
                site.line,
                REGISTRATION_RULE,
            )
            if site.pattern_bad or not site.patterns:
                if site.pattern_bad:
                    issues.append(
                        AdapterDiagnostic(
                            "spring_filter_target_ambiguous", site.path, site.line
                        )
                    )
                continue
            matched: list = []
            target_bad = False
            for pattern in site.patterns:
                hits = [
                    entity
                    for entity in entities.values()
                    if entity.type == EntityType.ENDPOINT
                    and dict(entity.attributes).get("path") == pattern
                ]
                if len(hits) != 1:
                    target_bad = True
                    break
                matched.append(hits[0])
            if target_bad or len({item.id for item in matched}) != 1:
                issues.append(
                    AdapterDiagnostic(
                        "spring_filter_target_ambiguous", site.path, site.line
                    )
                )
                continue
            endpoint = matched[0]
            for key, edge in list(edges.items()):
                if edge.type != EdgeType.HANDLED_BY or edge.source_id != endpoint.id:
                    continue
                if ref in edge.evidence_ids:
                    continue
                edges[key] = replace(edge, evidence_ids=(*edge.evidence_ids, ref))


class SpringFrameworkAdapter:
    """Emit Spring MVC Endpoint and handled_by facts from static mappings."""

    # Detector emits spring-web without a pinned version; allow selection like
    # FastAPI / react-router until Boot version evidence is wired.
    allow_unverified_versions = True
    reviewed_deep_support = False

    descriptor = AdapterDescriptor(
        adapter_id="rkg.spring",
        adapter_version="0.1.0",
        contract_version=CONTRACT_VERSION,
        kind=AdapterKind.FRAMEWORK,
        language="java",
        framework="spring-web",
        grammar_or_target="Spring Web MVC annotations",
        file_patterns=("*.java", "**/*.java"),
        ignore_patterns=("**/target/**", "**/.mvn/**"),
        capabilities=("app", "routes"),
        technology_constraints=(TechnologyConstraint("spring-web", ">=6.0,<7.0"),),
    )

    def technology_detectors(self) -> tuple[object, ...]:
        from rkg.detection.spring import SpringFrameworkDetector

        return (SpringFrameworkDetector(),)

    def detect(self, manifest: SourceManifest, parsed: ParseResult) -> DetectionReport:
        del manifest
        evidence: list[DetectionEvidence] = []
        for module in _modules(parsed).values():
            for item in iter_types(module):
                if annotation_has(item, "RestController", "Controller"):
                    evidence.append(DetectionEvidence(module.path, DETECT_RULE))
                    break
            else:
                continue
            break
        if not evidence:
            # import evidence
            for module in _modules(parsed).values():
                for imported in module.imports:
                    if "springframework.web.bind.annotation" in imported.qualified_name:
                        evidence.append(DetectionEvidence(module.path, DETECT_RULE))
                        break
        if not evidence:
            return DetectionReport()
        return DetectionReport(
            (TechnologyDetection("spring-web", None, tuple(evidence)),)
        )

    def extract(
        self, context: AdapterContext, parsed: ParseResult, base: FactBatch
    ) -> AdapterResult:
        modules = _modules(parsed)
        entities = {item.id: item for item in base.entities}
        edges = {item.id: item for item in base.edges}
        evidence = {item.id: item for item in base.evidence}
        issues: list[AdapterDiagnostic] = []
        by_qn = {item.qualified_name: item for item in entities.values()}

        for module in modules.values():
            for item in iter_types(module):
                is_controller = annotation_has(item, "RestController", "Controller")
                class_mapping = annotation_named(item, "RequestMapping")
                class_path = ""
                if class_mapping is not None:
                    resolved = _annotation_path(modules, item, class_mapping)
                    if resolved is None:
                        issues.append(
                            AdapterDiagnostic(
                                "spring_route_dynamic", module.path, class_mapping.line
                            )
                        )
                        continue
                    class_path = resolved
                declared = by_qn.get(item.qualified_name)
                if declared is not None and is_controller and class_mapping is not None:
                    attrs = dict(declared.attributes)
                    attrs["route_prefix"] = class_path
                    entities[declared.id] = replace(
                        declared, attributes=tuple(attrs.items())
                    )
                for callable_item in item.callables:
                    if callable_item.kind != "method":
                        continue
                    for ann in callable_item.annotations:
                        if ann.name not in _MAPPING:
                            continue
                        if not is_controller:
                            issues.append(
                                AdapterDiagnostic(
                                    "spring_controller_unregistered",
                                    module.path,
                                    ann.line,
                                )
                            )
                            break
                        route = _annotation_path(modules, item, ann)
                        if route is None:
                            issues.append(
                                AdapterDiagnostic(
                                    "spring_route_dynamic", module.path, ann.line
                                )
                            )
                            continue
                        methods = _annotation_methods(ann)
                        if methods is None:
                            issues.append(
                                AdapterDiagnostic(
                                    "spring_route_dynamic", module.path, ann.line
                                )
                            )
                            continue
                        full_path = _join(class_path, route)
                        handler = by_qn.get(callable_item.qualified_name)
                        if handler is None:
                            continue
                        for method in methods:
                            endpoint_qn = f"{item.qualified_name}.{callable_item.name}"
                            if method == "HEAD" and "GET" in methods:
                                endpoint_qn = f"{endpoint_qn}.head"
                            entity_id = endpoint_id(
                                context.repository_id,
                                module.path,
                                endpoint_qn,
                                method,
                                full_path,
                                (item.qualified_name,),
                            )
                            endpoint = Entity(
                                entity_id,
                                context.repository_id,
                                context.snapshot_id,
                                EntityType.ENDPOINT,
                                callable_item.name,
                                endpoint_qn,
                                module.path,
                                ann.line,
                                ann.line,
                                "http",
                                framework_kind="spring-web",
                                attributes=(
                                    ("method", method),
                                    ("path", full_path),
                                ),
                            )
                            entities[endpoint.id] = endpoint
                            ref = evidence_id(
                                context.snapshot_id,
                                module.path,
                                ann.line,
                                ann.line,
                                ROUTE_RULE,
                            )
                            evidence[ref] = Evidence(
                                ref,
                                context.snapshot_id,
                                module.path,
                                ann.line,
                                ann.line,
                                ROUTE_RULE,
                            )
                            edge_key = edge_id(
                                context.snapshot_id,
                                EdgeType.HANDLED_BY,
                                endpoint.id,
                                handler.id,
                            )
                            href = evidence_id(
                                context.snapshot_id,
                                module.path,
                                callable_item.start_line,
                                callable_item.start_line,
                                HANDLER_RULE,
                            )
                            evidence[href] = Evidence(
                                href,
                                context.snapshot_id,
                                module.path,
                                callable_item.start_line,
                                callable_item.start_line,
                                HANDLER_RULE,
                            )
                            edges[edge_key] = Edge(
                                edge_key,
                                context.snapshot_id,
                                EdgeType.HANDLED_BY,
                                endpoint.id,
                                handler.id,
                                HANDLER_RULE,
                                (href,),
                            )

        _extract_filter_registrations(
            context, modules, entities, edges, evidence, issues, by_qn
        )

        diagnostics = tuple(
            sorted(
                issues,
                key=lambda item: (item.relative_path or "", item.line or 0, item.code),
            )
        )
        messages = {
            code: _MESSAGES[code]
            for code in {item.code for item in diagnostics}
            if code in _MESSAGES
        }
        canonical = tuple(
            Diagnostic(
                diagnostic_id(
                    context.job_id, item.code, item.relative_path, item.line, ordinal
                ),
                context.job_id,
                Severity.WARNING,
                item.code,
                messages.get(item.code, item.code),
                context.snapshot_id,
                item.relative_path,
                item.line,
            )
            for ordinal, item in enumerate(diagnostics)
        )
        facts = FactBatch(
            context.repository_id,
            context.snapshot_id,
            tuple(sorted(entities.values(), key=lambda item: item.id)),
            tuple(sorted(edges.values(), key=lambda item: item.id)),
            tuple(evidence[key] for key in sorted(evidence)),
            tuple(base.diagnostics) + canonical,
        )
        return AdapterResult(
            facts,
            tuple(
                Capability(name, SupportState.SUPPORTED)
                for name in self.descriptor.capabilities
            ),
            diagnostics,
        )

    def resolve(
        self, context: AdapterContext, parsed: ParseResult, candidate: FactBatch
    ) -> AdapterResult:
        del parsed
        return AdapterResult(
            candidate,
            tuple(
                Capability(name, SupportState.SUPPORTED)
                for name in self.descriptor.capabilities
            ),
        )
