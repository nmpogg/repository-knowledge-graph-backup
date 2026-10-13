"""Static Spring Web MVC endpoint extraction over parsed Java units.

Only registered @RestController / @Controller beans with static path composition
emit Endpoints. Dynamic `${...}` / SpEL paths become diagnostics.
"""

from __future__ import annotations

from dataclasses import replace

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
    annotation_has,
    annotation_named,
    iter_types,
    resolve_constant,
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
_MESSAGES = {
    "spring_route_dynamic": "Route path, method or handler is not static.",
    "spring_controller_unregistered": "Mapping found on a non-controller type.",
}
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
