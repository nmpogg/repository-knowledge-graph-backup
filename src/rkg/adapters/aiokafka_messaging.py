"""Static aiokafka topic publish, consume and subscribe extraction.

The adapter reads parsed Python only. It never imports analyzed modules. A topic
that is not a string literal or a module constant becomes a diagnostic and never
a guessed MessageChannel relationship. Message payloads are not read.
"""

from __future__ import annotations

import ast
from collections import defaultdict
from collections.abc import Iterator, Sequence
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
    diagnostic_id,
    edge_id,
    evidence_id,
    message_channel_id,
    source_entity_id,
)
from rkg.ingestion import SourceManifest

DETECT_RULE = "RKG.aiokafka.detect_import.v1"
PUBLISH_RULE = "RKG.aiokafka.publish.v1"
CONSUME_RULE = "RKG.aiokafka.consume.v1"
SUBSCRIBE_RULE = "RKG.aiokafka.subscribe.v1"
PRODUCERS = frozenset(
    {
        "aiokafka.AIOKafkaProducer",
        "aiokafka.producer.AIOKafkaProducer",
        "aiokafka.producer.producer.AIOKafkaProducer",
    }
)
CONSUMERS = frozenset(
    {
        "aiokafka.AIOKafkaConsumer",
        "aiokafka.consumer.AIOKafkaConsumer",
        "aiokafka.consumer.consumer.AIOKafkaConsumer",
    }
)
PUBLISH_METHODS = frozenset({"send", "send_and_wait", "send_batch"})
_MESSAGES = {
    "aiokafka_topic_unresolved": "Topic is dynamic or not a module constant.",
    "aiokafka_topic_unscoped": "Messaging operation is outside a callable.",
}
_WAIT = object()


@dataclass(frozen=True, slots=True)
class _Prepared:
    module: _Module
    frame: dict[str, str | None]
    definitions: dict[
        str, tuple[str, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef]
    ]
    clients: dict[str, str]


@dataclass(frozen=True, slots=True)
class _Scope:
    frames: Sequence[dict[str, str | None]]
    flow: _Flow
    clients: dict[str, str]
    attributes: dict[tuple[str, str], str]
    constants: dict[str, str | tuple[str, ...]]
    module_name: str


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


def _client_kind(name: str | None) -> str | None:
    if name in PRODUCERS:
        return "producer"
    if name in CONSUMERS:
        return "consumer"
    return None


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
        topic: str,
        path: str,
        line: int,
        rule: str,
    ) -> None:
        target = message_channel_id(
            self.context.repository_id, "topic", "", topic
        )
        current = self.entities.get(target)
        place = (path, line)
        current_place = (
            (current.file_path or "", current.start_line or 0) if current else None
        )
        if current is None or current_place > place:
            self.entities[target] = Entity(
                target,
                self.context.repository_id,
                self.context.snapshot_id,
                EntityType.MESSAGE_CHANNEL,
                topic,
                f"aiokafka::{topic}",
                path,
                line,
                line,
                framework_kind="aiokafka",
                attributes=(
                    ("channel_kind", "topic"),
                    ("name", topic),
                    ("namespace", ""),
                ),
            )
        ref = evidence_id(self.context.snapshot_id, path, line, line, rule)
        self.evidence[ref] = Evidence(
            ref, self.context.snapshot_id, path, line, line, rule
        )
        key = edge_id(self.context.snapshot_id, kind, source, target)
        existing = self.edges.get(key)
        references = set(existing.evidence_ids) if existing else set()
        references.add(ref)
        chosen = min(rule, existing.rule) if existing else rule
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


def _prepare(parsed: ParseResult) -> list[_Prepared]:
    prepared = []
    for unit in parsed.units:
        tree = unit.representation
        if not isinstance(tree, ast.Module):
            continue
        module = _Module(unit.relative_path, _module_name(unit.relative_path), tree)
        frame = dict(_bindings(module, tree.body, module.name))
        definitions, _ = _unique_definitions(tree, module.name, module.path)
        item = _Prepared(
            module,
            frame,
            {name: (owner, node) for owner, name, node in definitions},
            _module_clients(module, frame),
        )
        prepared.append(item)
    return prepared


def _module_clients(module: _Module, frame: dict[str, str | None]) -> dict[str, str]:
    assigns: dict[str, list[ast.expr]] = defaultdict(list)
    notes: dict[str, list[ast.expr]] = defaultdict(list)
    for statement in module.tree.body:
        if isinstance(statement, ast.AnnAssign) and isinstance(
            statement.target, ast.Name
        ):
            if statement.annotation is not None:
                notes[statement.target.id].append(statement.annotation)
            if statement.value is not None:
                assigns[statement.target.id].append(statement.value)
            continue
        assigned = _single_assign(statement)
        if assigned is not None:
            assigns[assigned[0]].append(assigned[1])
    clients = {}
    for name in set(assigns) | set(notes):
        values = assigns.get(name, [])
        annotations = notes.get(name, [])
        if len(values) > 1 or len(annotations) > 1:
            continue
        constructed = None
        if len(values) == 1 and isinstance(values[0], ast.Call):
            constructed = _client_kind(_qualified(values[0].func, [frame]))
        if len(values) == 1 and constructed is None:
            continue
        noted = (
            _client_kind(_qualified(annotations[0], [frame]))
            if len(annotations) == 1
            else None
        )
        if len(annotations) == 1 and noted is None:
            continue
        if constructed and noted and constructed != noted:
            continue
        kind = constructed or (noted if not values else None)
        if kind:
            clients[name] = kind
    return clients


def _constant_key(
    expression: ast.expr,
    frames: Sequence[dict[str, str | None]],
    module_name: str,
) -> str | None:
    if isinstance(expression, ast.Name):
        for frame in frames:
            if expression.id not in frame:
                continue
            target = frame[expression.id]
            if target:
                return target
            if frame is frames[-1]:
                return f"{module_name}.{expression.id}"
            return None
        return None
    if isinstance(expression, ast.Attribute):
        parent = _qualified(expression.value, frames)
        if parent:
            return f"{parent}.{expression.attr}"
    return None


def _resolve_constant(
    expression: ast.expr,
    frames: Sequence[dict[str, str | None]],
    module_name: str,
    known: dict[str, str | tuple[str, ...]],
    pending: set[str],
) -> str | tuple[str, ...] | None | object:
    if isinstance(expression, ast.Constant) and isinstance(expression.value, str):
        return expression.value or None
    if isinstance(expression, (ast.List, ast.Tuple)):
        if any(isinstance(item, ast.Starred) for item in expression.elts):
            return None
        values: list[str] = []
        waiting = False
        for item in expression.elts:
            resolved = _resolve_constant(item, frames, module_name, known, pending)
            if resolved is _WAIT:
                waiting = True
                continue
            if not isinstance(resolved, str):
                return None
            values.append(resolved)
        if waiting:
            return _WAIT
        return tuple(values) if values else None
    key = _constant_key(expression, frames, module_name)
    if key is None:
        return None
    if key in known:
        return known[key]
    if key in pending:
        return _WAIT
    return None


def _constants(
    prepared: Sequence[_Prepared],
) -> dict[str, str | tuple[str, ...]]:
    raw: dict[str, tuple[ast.expr, dict[str, str | None], str]] = {}
    for item in prepared:
        counts: dict[str, int] = defaultdict(int)
        expressions: dict[str, ast.expr] = {}
        for statement in item.module.tree.body:
            assigned = _single_assign(statement)
            if assigned is None:
                continue
            counts[assigned[0]] += 1
            expressions[assigned[0]] = assigned[1]
        for name, count in counts.items():
            if count == 1:
                raw[f"{item.module.name}.{name}"] = (
                    expressions[name],
                    item.frame,
                    item.module.name,
                )
    known: dict[str, str | tuple[str, ...]] = {}
    pending = set(raw)
    changed = True
    while changed and pending:
        changed = False
        for key in tuple(pending):
            expression, frame, module_name = raw[key]
            resolved = _resolve_constant(
                expression, [frame], module_name, known, pending
            )
            if resolved is _WAIT:
                continue
            pending.remove(key)
            changed = True
            if isinstance(resolved, str) or (
                isinstance(resolved, tuple) and resolved
            ):
                known[key] = resolved
    return known


def _topic(expression: ast.expr, scope: _Scope) -> str | None:
    if isinstance(expression, ast.Constant) and isinstance(expression.value, str):
        return expression.value or None
    key = _constant_key(expression, scope.frames, scope.module_name)
    value = scope.constants.get(key) if key else None
    if isinstance(value, str) and value:
        return value
    return None


def _topics(expression: ast.expr, scope: _Scope) -> tuple[str, ...] | None:
    if isinstance(expression, (ast.List, ast.Tuple)):
        if any(isinstance(item, ast.Starred) for item in expression.elts):
            return None
        found = tuple(_topic(item, scope) for item in expression.elts)
        if any(item is None for item in found):
            return None
        return tuple(item for item in found if item is not None)
    key = _constant_key(expression, scope.frames, scope.module_name)
    value = scope.constants.get(key) if key else None
    if isinstance(value, tuple):
        return value
    return None


def _named_argument(
    call: ast.Call, index: int, names: set[str]
) -> ast.expr | None:
    """Return one explicit argument, or None when it is missing or duplicated."""
    if any(item.arg is None for item in call.keywords):
        return None
    positional = call.args[index] if index < len(call.args) else None
    if isinstance(positional, ast.Starred):
        return None
    matched = [item.value for item in call.keywords if item.arg in names]
    if (positional is None and len(matched) == 1) or (
        positional is not None and not matched
    ):
        return positional if positional is not None else matched[0]
    return None


def _locally_bound(name: str, frames: Sequence[dict[str, str | None]]) -> bool:
    return any(name in frame for frame in frames[:-1])


def _name_client(name: str, scope: _Scope) -> str | None:
    notes = scope.flow.annotations.get(name, [])
    note = (
        _client_kind(_qualified(notes[0], scope.frames)) if len(notes) == 1 else None
    )
    if len(notes) > 1 or (len(notes) == 1 and note is None):
        return None
    values = scope.flow.values.get(name, [])
    stores = scope.flow.stores.get(name, 0)
    if stores and len(values) != 1:
        return None
    constructed = None
    if len(values) == 1 and stores == 1 and isinstance(values[0], ast.Call):
        constructed = _client_kind(_qualified(values[0].func, scope.frames))
    if len(values) == 1 and constructed is None:
        return None
    if constructed and note and constructed != note:
        return None
    if constructed:
        return constructed
    if note and stores == 0:
        return note
    if stores == 0 and not _locally_bound(name, scope.frames):
        return scope.clients.get(name)
    return None


def _receiver_kind(receiver: ast.expr, scope: _Scope) -> str | None:
    if isinstance(receiver, ast.Call):
        return _client_kind(_qualified(receiver.func, scope.frames))
    if isinstance(receiver, ast.Name):
        return _name_client(receiver.id, scope)
    if (
        isinstance(receiver, ast.Attribute)
        and isinstance(receiver.value, ast.Name)
        and scope.flow.stores.get(receiver.value.id, 0) == 0
    ):
        return scope.attributes.get((receiver.value.id, receiver.attr))
    return None


def _attribute_clients(item: _Prepared, owner: str) -> dict[tuple[str, str], str]:
    found: dict[tuple[str, str], set[str]] = defaultdict(set)
    counts: dict[tuple[str, str], int] = defaultdict(int)
    invalid: set[tuple[str, str]] = set()
    for name, (parent, node) in item.definitions.items():
        if parent != owner or not isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            continue
        frames = _frames(name, item.module, item.definitions, item.frame)
        for statement in node.body:
            assigned = _attribute_assign(statement)
            if assigned is None:
                continue
            key, value = assigned
            counts[key] += 1
            kind = (
                _client_kind(_qualified(value.func, frames))
                if isinstance(value, ast.Call)
                else None
            )
            if kind is None:
                invalid.add(key)
            else:
                found[key].add(kind)
    return {
        key: next(iter(kinds))
        for key, kinds in found.items()
        if key not in invalid and len(kinds) == 1 and counts[key] == 1
    }


def _attribute_assign(statement: ast.stmt) -> tuple[tuple[str, str], ast.expr] | None:
    value: ast.expr | None = None
    target: ast.expr | None = None
    if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
        target = statement.targets[0]
        value = statement.value
    elif isinstance(statement, ast.AnnAssign) and statement.value is not None:
        target = statement.target
        value = statement.value
    if (
        value is not None
        and isinstance(target, ast.Attribute)
        and isinstance(target.value, ast.Name)
        and target.value.id in {"self", "cls"}
    ):
        return (target.value.id, target.attr), value
    return None


def _constructor_topics(call: ast.Call, scope: _Scope) -> tuple[str, ...] | None:
    if any(isinstance(arg, ast.Starred) for arg in call.args):
        return None
    found = []
    for arg in call.args:
        topic = _topic(arg, scope)
        if topic is None:
            return None
        found.append(topic)
    return tuple(found)


def _publish_topic(call: ast.Call, method: str, scope: _Scope) -> str | None:
    index = 1 if method == "send_batch" else 0
    argument = _named_argument(call, index, {"topic"})
    if argument is None:
        return None
    return _topic(argument, scope)


def _subscribe_topics(call: ast.Call, scope: _Scope) -> tuple[str, ...] | None:
    if any(item.arg is None for item in call.keywords):
        return None
    patterned = [
        item.value
        for item in call.keywords
        if item.arg == "pattern"
        and not (isinstance(item.value, ast.Constant) and item.value.value is None)
    ]
    if patterned:
        return None
    if not call.args and not any(item.arg == "topics" for item in call.keywords):
        return ()
    argument = _named_argument(call, 0, {"topics"})
    if argument is None:
        return None
    return _topics(argument, scope)


def _emit(
    facts: _Facts,
    caller_id: str | None,
    kind: EdgeType,
    topics: tuple[str, ...],
    path: str,
    line: int,
    rule: str,
    failed: bool,
) -> None:
    if caller_id is None:
        facts.issue("aiokafka_topic_unscoped", path, line)
        return
    if failed:
        facts.issue("aiokafka_topic_unresolved", path, line)
        return
    for topic in topics:
        facts.relate(kind, caller_id, topic, path, line, rule)


def _consumer_name(expression: ast.expr) -> bool:
    if isinstance(expression, ast.Name):
        return expression.id == "AIOKafkaConsumer"
    if isinstance(expression, ast.Attribute):
        return expression.attr == "AIOKafkaConsumer"
    return False


def _recognized(
    call: ast.Call, scope: _Scope, facts: _Facts, path: str, caller_id: str | None
) -> None:
    if isinstance(call.func, ast.Attribute):
        kind = _receiver_kind(call.func.value, scope)
        method = call.func.attr
        if method in PUBLISH_METHODS:
            topic = _publish_topic(call, method, scope) if kind == "producer" else None
            _emit(
                facts,
                caller_id,
                EdgeType.PUBLISHES,
                () if topic is None else (topic,),
                path,
                call.lineno,
                PUBLISH_RULE,
                kind != "producer" or topic is None,
            )
        elif method == "subscribe":
            topics = _subscribe_topics(call, scope) if kind == "consumer" else None
            _emit(
                facts,
                caller_id,
                EdgeType.CONSUMES,
                () if topics is None else topics,
                path,
                call.lineno,
                SUBSCRIBE_RULE,
                kind != "consumer" or topics is None,
            )
        return
    if _client_kind(_qualified(call.func, scope.frames)) != "consumer":
        if _consumer_name(call.func):
            _emit(
                facts,
                caller_id,
                EdgeType.CONSUMES,
                (),
                path,
                call.lineno,
                CONSUME_RULE,
                True,
            )
        return
    topics = _constructor_topics(call, scope)
    if not call.args and topics == ():
        return
    _emit(
        facts,
        caller_id,
        EdgeType.CONSUMES,
        () if topics is None else topics,
        path,
        call.lineno,
        CONSUME_RULE,
        topics is None,
    )


def _scope(
    item: _Prepared,
    qualified_name: str | None,
    node: ast.FunctionDef | ast.AsyncFunctionDef | None,
    constants: dict[str, str | tuple[str, ...]],
    attributes: dict[tuple[str, str], str],
) -> _Scope:
    if node is None or qualified_name is None:
        flow = _Flow()
        frames: Sequence[dict[str, str | None]] = [item.frame]
    else:
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
        frames = _frames(qualified_name, item.module, item.definitions, item.frame)
    return _Scope(frames, flow, item.clients, attributes, constants, item.module.name)


def _scan_callable(
    item: _Prepared,
    qualified_name: str,
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    constants: dict[str, str | tuple[str, ...]],
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
    owner = item.definitions[qualified_name][0]
    attributes = (
        _attribute_clients(item, owner)
        if owner != item.module.name
        else {}
    )
    scope = _scope(item, qualified_name, node, constants, attributes)
    for call in _iter_calls(node.body):
        _recognized(call, scope, facts, item.module.path, caller_id)


def _scan_module(
    item: _Prepared,
    constants: dict[str, str | tuple[str, ...]],
    facts: _Facts,
) -> None:
    scope = _scope(item, None, None, constants, {})
    for call in _iter_calls(item.module.tree.body):
        _recognized(call, scope, facts, item.module.path, None)


def _extract(
    context: AdapterContext, parsed: ParseResult, facts: _Facts
) -> None:
    del context
    if "aiokafka" in _local_roots(parsed):
        return
    prepared = _prepare(parsed)
    constants = _constants(prepared)
    for item in prepared:
        _scan_module(item, constants, facts)
        for name, (owner, node) in sorted(item.definitions.items()):
            del owner
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                _scan_callable(item, name, node, constants, facts)


class AIOKafkaMessagingAdapter:
    """Extract the supported aiokafka topic publish and consume profile."""

    entrypoint_required = False
    descriptor = AdapterDescriptor(
        adapter_id="rkg.aiokafka",
        adapter_version="2.0.0",
        contract_version=CONTRACT_VERSION,
        kind=AdapterKind.MESSAGING,
        language="python",
        framework="aiokafka",
        grammar_or_target="aiokafka supported subset",
        file_patterns=("*.py", "**/*.py"),
        ignore_patterns=("**/__pycache__/**",),
        capabilities=("consumes", "publishes", "topics"),
        technology_constraints=(TechnologyConstraint("aiokafka", ">=0.8,<1.0"),),
    )

    def detect(self, manifest: SourceManifest, parsed: ParseResult) -> DetectionReport:
        del manifest
        if "aiokafka" in _local_roots(parsed):
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
                        alias.name.split(".")[0] == "aiokafka" for alias in node.names
                    )
                elif (
                    isinstance(node, ast.ImportFrom)
                    and node.level == 0
                    and node.module
                    and node.module.split(".")[0] == "aiokafka"
                ):
                    imported = True
                if imported:
                    evidence.add(DetectionEvidence(unit.relative_path, DETECT_RULE))
        references = tuple(
            sorted(evidence, key=lambda item: (item.relative_path, item.rule_id))
        )
        if not references:
            return DetectionReport()
        return DetectionReport((TechnologyDetection("aiokafka", None, references),))

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
            for name in AIOKafkaMessagingAdapter.descriptor.capabilities
        )
