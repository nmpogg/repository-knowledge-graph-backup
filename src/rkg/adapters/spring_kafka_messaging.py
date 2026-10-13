"""Static Spring Kafka publish/consume extraction over parsed Java units.

Topics come from uniquely assigned constants only. SpEL / dynamic topics become
diagnostics and never invent MessageChannel identities. Payloads are ignored.
"""

from __future__ import annotations

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
    evidence_id,
    message_channel_id,
)
from rkg.ingestion import SourceManifest

DETECT_RULE = "RKG.spring_kafka.detect.v1"
PUBLISH_RULE = "RKG.spring_kafka.publish.v1"
CONSUME_RULE = "RKG.spring_kafka.consume.v1"
_MESSAGES = {
    "spring_kafka_topic_unresolved": "Topic is dynamic or not a unique constant.",
}


def _modules(parsed: ParseResult) -> dict[str, JavaModule]:
    return {
        unit.relative_path: unit.representation
        for unit in parsed.units
        if isinstance(unit.representation, JavaModule)
    }


def _topic_from_expression(
    modules: dict[str, JavaModule], owner, expression: str
) -> str | None:
    text = expression.strip()
    if "${" in text or "#{" in text:
        return None
    if text.startswith('"') and text.endswith('"'):
        return text[1:-1]
    return resolve_constant(modules, owner, text)


class SpringKafkaMessagingAdapter:
    """Emit Spring Kafka MessageChannel publish/consume facts."""

    allow_unverified_versions = True
    reviewed_deep_support = False

    descriptor = AdapterDescriptor(
        adapter_id="rkg.spring-kafka",
        adapter_version="0.1.0",
        contract_version=CONTRACT_VERSION,
        kind=AdapterKind.MESSAGING,
        language="java",
        framework="spring-kafka",
        grammar_or_target="Spring Kafka annotations and KafkaTemplate",
        file_patterns=("*.java", "**/*.java"),
        ignore_patterns=("**/target/**", "**/.mvn/**"),
        capabilities=("topics", "publishes", "consumes"),
        technology_constraints=(TechnologyConstraint("spring-kafka", ">=3.0,<4.0"),),
    )

    def technology_detectors(self) -> tuple[object, ...]:
        from rkg.detection.spring_kafka import SpringKafkaDetector

        return (SpringKafkaDetector(),)

    def detect(self, manifest: SourceManifest, parsed: ParseResult) -> DetectionReport:
        del manifest
        evidence: list[DetectionEvidence] = []
        for module in _modules(parsed).values():
            for imported in module.imports:
                if "springframework.kafka" in imported.qualified_name:
                    evidence.append(DetectionEvidence(module.path, DETECT_RULE))
                    break
            for item in iter_types(module):
                if annotation_has(item, "KafkaListener") or any(
                    annotation_has(c, "KafkaListener") for c in item.callables
                ):
                    evidence.append(DetectionEvidence(module.path, DETECT_RULE))
                    break
        if not evidence:
            return DetectionReport()
        # dedupe
        unique = {(item.relative_path, item.rule_id): item for item in evidence}
        return DetectionReport(
            (TechnologyDetection("spring-kafka", None, tuple(unique.values())),)
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

        def ensure_channel(topic: str, path: str, line: int) -> Entity:
            existing = by_qn.get(topic)
            if existing is not None:
                return existing
            entity_id = message_channel_id(context.repository_id, "topic", "", topic)
            entity = Entity(
                entity_id,
                context.repository_id,
                context.snapshot_id,
                EntityType.MESSAGE_CHANNEL,
                topic,
                topic,
                path,
                line,
                line,
                framework_kind="spring-kafka",
                attributes=(
                    ("channel_kind", "topic"),
                    ("name", topic),
                    ("namespace", ""),
                ),
            )
            entities[entity.id] = entity
            by_qn[topic] = entity
            return entity

        def relate(
            kind: EdgeType,
            source: Entity,
            target: Entity,
            path: str,
            line: int,
            rule: str,
        ) -> None:
            ref = evidence_id(context.snapshot_id, path, line, line, rule)
            evidence[ref] = Evidence(ref, context.snapshot_id, path, line, line, rule)
            key = edge_id(context.snapshot_id, kind, source.id, target.id)
            existing = edges.get(key)
            refs = set(existing.evidence_ids) if existing else set()
            refs.add(ref)
            edges[key] = Edge(
                key,
                context.snapshot_id,
                kind,
                source.id,
                target.id,
                rule,
                tuple(sorted(refs)),
            )

        for module in modules.values():
            for item in iter_types(module):
                # Consumes via @KafkaListener
                for callable_item in item.callables:
                    listener = annotation_named(callable_item, "KafkaListener")
                    if listener is None:
                        continue
                    if not annotation_has(item, "Component", "Service", "Repository"):
                        # DynamicTopicListener is intentionally not a component
                        topic_arg = next(
                            (
                                value
                                for key, value in listener.arguments
                                if key in {None, "topics"}
                            ),
                            "",
                        )
                        if "${" in topic_arg or "#{" in topic_arg:
                            issues.append(
                                AdapterDiagnostic(
                                    "spring_kafka_topic_unresolved",
                                    module.path,
                                    listener.line,
                                )
                            )
                        continue
                    topic_expr = next(
                        (
                            value
                            for key, value in listener.arguments
                            if key in {None, "topics"}
                        ),
                        "",
                    )
                    topic = _topic_from_expression(modules, item, topic_expr)
                    if topic is None:
                        issues.append(
                            AdapterDiagnostic(
                                "spring_kafka_topic_unresolved",
                                module.path,
                                listener.line,
                            )
                        )
                        continue
                    source = by_qn.get(callable_item.qualified_name)
                    if source is None:
                        continue
                    channel = ensure_channel(topic, module.path, listener.line)
                    relate(
                        EdgeType.CONSUMES,
                        source,
                        channel,
                        module.path,
                        listener.line,
                        CONSUME_RULE,
                    )

                # Publishes via KafkaTemplate.send
                if not annotation_has(item, "Component", "Service"):
                    continue
                for callable_item in item.callables:
                    if callable_item.kind != "method":
                        continue
                    body = next(
                        (
                            child
                            for child in named_children(callable_item.node)
                            if child.type == "block"
                        ),
                        None,
                    )
                    if body is None:
                        continue
                    for node in walk_named(body):
                        if node.type != "method_invocation":
                            continue
                        text = text_of(module.source, node)
                        if ".send(" not in text and not text.startswith("send("):
                            continue
                        # Expect receiver.send(topic, ...)
                        children = named_children(node)
                        identifiers = [
                            c
                            for c in children
                            if c.type in {"identifier", "field_access"}
                        ]
                        if len(identifiers) < 2:
                            continue
                        method_name = text_of(module.source, identifiers[1])
                        if method_name != "send":
                            continue
                        args = next(
                            (c for c in children if c.type == "argument_list"), None
                        )
                        if args is None or not named_children(args):
                            continue
                        first = named_children(args)[0]
                        topic = _topic_from_expression(
                            modules, item, text_of(module.source, first)
                        )
                        if topic is None:
                            issues.append(
                                AdapterDiagnostic(
                                    "spring_kafka_topic_unresolved",
                                    module.path,
                                    node.start_point[0] + 1,
                                )
                            )
                            continue
                        source = by_qn.get(callable_item.qualified_name)
                        if source is None:
                            continue
                        channel = ensure_channel(
                            topic, module.path, node.start_point[0] + 1
                        )
                        relate(
                            EdgeType.PUBLISHES,
                            source,
                            channel,
                            module.path,
                            node.start_point[0] + 1,
                            PUBLISH_RULE,
                        )

        diagnostics = tuple(
            sorted(
                issues,
                key=lambda item: (item.relative_path or "", item.line or 0, item.code),
            )
        )
        canonical = tuple(
            Diagnostic(
                diagnostic_id(
                    context.job_id, item.code, item.relative_path, item.line, ordinal
                ),
                context.job_id,
                Severity.WARNING,
                item.code,
                _MESSAGES.get(item.code, item.code),
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
        del context, parsed
        return AdapterResult(
            candidate,
            tuple(
                Capability(name, SupportState.SUPPORTED)
                for name in self.descriptor.capabilities
            ),
        )
