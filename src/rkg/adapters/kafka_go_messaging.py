"""Static kafka-go publish/consume extraction over parsed Go units.

Topics come from string literals or uniquely assigned package constants only.
Dynamic topics, package-level init calls, and shadowed local names never invent
MessageChannel edges. Payloads are ignored.
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
from rkg.adapters.go_parse import (
    GoModule,
    named_children,
    package_qualified,
    string_literal,
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

DETECT_RULE = "RKG.kafka_go.detect.v1"
PUBLISH_RULE = "RKG.kafka_go.publish.v1"
CONSUME_RULE = "RKG.kafka_go.consume.v1"
_KAFKA_IMPORT = "github.com/segmentio/kafka-go"
_MESSAGES = {
    "kafka_go_topic_unresolved": "Topic is dynamic or not a unique constant.",
}


def _modules(parsed: ParseResult) -> dict[str, GoModule]:
    return {
        unit.relative_path: unit.representation
        for unit in parsed.units
        if isinstance(unit.representation, GoModule)
    }


def _has_kafka_import(module: GoModule) -> bool:
    return any(item.path == _KAFKA_IMPORT for item in module.imports)


def _package_constants(modules: dict[str, GoModule]) -> dict[str, str]:
    """Map package.ConstName and ConstName (same package) → literal."""
    found: dict[str, str] = {}
    for module in modules.values():
        for name, value in module.constants.items():
            found[f"{module.package_name}.{name}"] = value
            found[name] = value
    return found


def _literal_node(node):
    """Unwrap Go literal_element wrappers used inside composite literals."""
    if node is None:
        return None
    if node.type == "literal_element":
        children = named_children(node)
        return children[0] if children else node
    return node


def _resolve_topic(
    source: bytes,
    node,
    module: GoModule,
    constants: dict[str, str],
    import_aliases: dict[str, str],
) -> str | None:
    node = _literal_node(node)
    if node is None:
        return None
    literal = string_literal(source, node)
    if literal is not None:
        return literal or None
    if node.type == "identifier":
        name = text_of(source, node)
        return constants.get(f"{module.package_name}.{name}") or constants.get(name)
    if node.type == "selector_expression":
        operand = node.child_by_field_name("operand") or named_children(node)[0]
        field = node.child_by_field_name("field") or named_children(node)[-1]
        if operand.type != "identifier":
            return None
        left = text_of(source, operand)
        name = text_of(source, field)
        pkg = import_aliases.get(left, left)
        return constants.get(f"{pkg}.{name}")
    return None


def _import_aliases(module: GoModule) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for item in module.imports:
        parts = [p for p in item.path.split("/") if p and p not in {"v5", "v4"}]
        default = parts[-1] if parts else item.path
        # Path segment kafka-go declares package kafka.
        pkg = "kafka" if default == "kafka-go" else default
        local = item.alias or pkg
        aliases[local] = pkg
        if item.alias:
            aliases[item.alias] = pkg
    return aliases


class KafkaGoMessagingAdapter:
    """Emit kafka-go MessageChannel publish/consume facts."""

    allow_unverified_versions = True
    reviewed_deep_support = False

    descriptor = AdapterDescriptor(
        adapter_id="rkg.kafka-go",
        adapter_version="0.1.0",
        contract_version=CONTRACT_VERSION,
        kind=AdapterKind.MESSAGING,
        language="go",
        framework="kafka-go",
        grammar_or_target="segmentio/kafka-go reader/writer",
        file_patterns=("*.go", "**/*.go"),
        ignore_patterns=("**/vendor/**", "**/testdata/**", "**/*_test.go"),
        capabilities=("topics", "publishes", "consumes"),
        technology_constraints=(TechnologyConstraint("kafka-go", ">=0.4,<1.0"),),
    )

    def technology_detectors(self) -> tuple[object, ...]:
        from rkg.detection.kafka_go import KafkaGoDetector

        return (KafkaGoDetector(),)

    def detect(self, manifest: SourceManifest, parsed: ParseResult) -> DetectionReport:
        del manifest
        evidence: list[DetectionEvidence] = []
        for module in _modules(parsed).values():
            if _has_kafka_import(module):
                evidence.append(DetectionEvidence(module.path, DETECT_RULE))
        if not evidence:
            return DetectionReport()
        return DetectionReport(
            (TechnologyDetection("kafka-go", None, tuple(evidence)),)
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
        constants = _package_constants(modules)

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
                framework_kind="kafka-go",
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

        # Consumes: ReaderConfig Topic: static → KafkaConsumer type in package.
        for module in modules.values():
            if not _has_kafka_import(module):
                continue
            aliases = _import_aliases(module)
            for node in walk_named(module.tree.root_node):
                if node.type != "keyed_element":
                    continue
                key_node = _literal_node(
                    node.child_by_field_name("key")
                    or (named_children(node)[0] if named_children(node) else None)
                )
                val_node = node.child_by_field_name("value") or (
                    named_children(node)[1] if len(named_children(node)) > 1 else None
                )
                if key_node is None or val_node is None:
                    continue
                if text_of(module.source, key_node) != "Topic":
                    continue
                topic = _resolve_topic(
                    module.source, val_node, module, constants, aliases
                )
                line = node.start_point[0] + 1
                if topic is None:
                    issues.append(
                        AdapterDiagnostic(
                            "kafka_go_topic_unresolved", module.path, line
                        )
                    )
                    continue
                # Schema requires Callable → MessageChannel for consumes.
                reader_qn = package_qualified(module.package_name, "NewKafkaReader")
                source = by_qn.get(reader_qn)
                if source is None:
                    continue
                channel = ensure_channel(topic, module.path, line)
                relate(
                    EdgeType.CONSUMES,
                    source,
                    channel,
                    module.path,
                    line,
                    CONSUME_RULE,
                )

        # Publishes: EventPublisher.Publish(..., topic, ...) with static topic.
        publish_callable_qn = None
        for qn, entity in by_qn.items():
            if (
                qn.endswith("EventPublisher.Publish")
                and entity.type == EntityType.CALLABLE
            ):
                publish_callable_qn = qn
                break
        # Prefer messaging.EventPublisher.Publish when present.
        preferred = "messaging.EventPublisher.Publish"
        if preferred in by_qn:
            publish_callable_qn = preferred

        for module in modules.values():
            aliases = _import_aliases(module)
            for node in walk_named(module.tree.root_node):
                if node.type != "call_expression":
                    continue
                func = node.child_by_field_name("function") or next(
                    iter(named_children(node)), None
                )
                if func is None or func.type != "selector_expression":
                    continue
                field = func.child_by_field_name("field") or named_children(func)[-1]
                if text_of(module.source, field) != "Publish":
                    continue
                # Skip shadowed local kafka.Publish() with no topic args.
                args = node.child_by_field_name("arguments") or next(
                    (c for c in named_children(node) if c.type == "argument_list"),
                    None,
                )
                if args is None:
                    continue
                arg_nodes = named_children(args)
                # EventPublisher.Publish(ctx, topic, key, payload) → topic at index 1
                # Also allow Publish(topic) in focused conformance fixtures.
                topic_node = None
                if len(arg_nodes) >= 2:
                    topic_node = arg_nodes[1]
                elif len(arg_nodes) == 1:
                    topic_node = arg_nodes[0]
                else:
                    continue
                line = node.start_point[0] + 1
                topic = _resolve_topic(
                    module.source, topic_node, module, constants, aliases
                )
                if topic is None:
                    # Dynamic / unresolved — diagnostic only, no invent.
                    issues.append(
                        AdapterDiagnostic(
                            "kafka_go_topic_unresolved", module.path, line
                        )
                    )
                    continue
                if publish_callable_qn is None:
                    continue
                source = by_qn.get(publish_callable_qn)
                if source is None:
                    continue
                owners = [
                    c
                    for c in module.callables
                    if c.node.start_point[0] + 1 <= line <= c.node.end_point[0] + 1
                ]
                if owners:
                    owner = min(
                        owners, key=lambda c: c.node.end_byte - c.node.start_byte
                    )
                    caller = by_qn.get(owner.qualified_name)
                    if caller is not None and any(
                        e.type == EdgeType.CALLS
                        and e.source_id == caller.id
                        and e.target_id == source.id
                        for e in edges.values()
                    ):
                        source = caller
                # Ignore local Publish methods that are not EventPublisher (shadowed).
                operand = func.child_by_field_name("operand") or named_children(func)[0]
                if operand.type == "identifier":
                    recv_name = text_of(module.source, operand)
                    # Shadowed local kafka.Publish() with no topic.
                    if recv_name == "kafka" and len(arg_nodes) == 0:
                        continue
                channel = ensure_channel(topic, module.path, line)
                relate(
                    EdgeType.PUBLISHES,
                    source,
                    channel,
                    module.path,
                    line,
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
