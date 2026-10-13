"""TASK-RKG-011 static aiokafka topic publish and consume facts."""

from __future__ import annotations

from pathlib import Path

from rkg.adapters import (
    AdapterContext,
    AdapterRegistry,
    AIOKafkaMessagingAdapter,
    PythonLanguageAdapter,
    run_framework_conformance,
)
from rkg.detection import DetectionState, PythonImportDetector, select_adapters
from rkg.domain import (
    EdgeType,
    EntityType,
    SourceScanConfig,
    message_channel_id,
    validate_fact_batch,
)
from rkg.ingestion import LocalSourcePolicy, build_manifest, resolve_local_source

REPO = "repo-eleven"
PUBLISH = "RKG.aiokafka.publish.v1"
CONSUME = "RKG.aiokafka.consume.v1"
SUBSCRIBE = "RKG.aiokafka.subscribe.v1"


def _write(root: Path, path: str, content: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def _run(root: Path):
    config = SourceScanConfig(40, 32768)
    manifest = build_manifest(
        resolve_local_source(REPO, root, LocalSourcePolicy((root,))), config
    )
    context = AdapterContext(REPO, "snap-eleven", "job-eleven", config)
    language = PythonLanguageAdapter()
    parsed = language.parse(manifest, config)
    base = language.extract(context, parsed)
    base = language.resolve(context, parsed, base.facts)
    adapter = AIOKafkaMessagingAdapter()
    result = adapter.extract(context, parsed, base.facts)
    validate_fact_batch(result.facts)
    report = run_framework_conformance(
        adapter,
        manifest,
        parsed,
        context,
        base.facts,
        no_execution_marker=lambda: False,
    )
    assert report.pass_rate == 1.0, report.cases
    return context, result


def _channels(result):
    return {
        item.qualified_name: item
        for item in result.facts.entities
        if item.type == EntityType.MESSAGE_CHANNEL
    }


def _rules(result, caller: str, channel: str, kind: EdgeType) -> set[str]:
    entities = {item.id: item for item in result.facts.entities}
    evidence = {item.id: item for item in result.facts.evidence}
    found = set()
    for edge in result.facts.edges:
        if edge.type != kind or edge.source_id not in entities:
            continue
        if entities[edge.source_id].qualified_name != caller:
            continue
        if entities[edge.target_id].qualified_name != channel:
            continue
        found.update(evidence[item].rule for item in edge.evidence_ids)
    return found


def test_literal_constant_and_shared_channel(tmp_path: Path) -> None:
    _write(tmp_path, "topics.py", "ORDERS = 'orders'\nGROUP = (ORDERS, 'billing')\n")
    _write(
        tmp_path,
        "bus.py",
        "from aiokafka import AIOKafkaProducer, AIOKafkaConsumer\n"
        "from topics import ORDERS, GROUP\n"
        "producer = AIOKafkaProducer()\n"
        "async def publish():\n"
        "    await producer.send('orders', b'secret-sentinel')\n"
        "    await producer.send_and_wait(ORDERS, value=b'secret-sentinel')\n"
        "    await producer.send_batch(producer.create_batch(), topic='billing')\n"
        "async def listen():\n"
        "    consumer = AIOKafkaConsumer('orders', 'billing')\n"
        "    consumer.subscribe(GROUP)\n"
        "    consumer.subscribe(pattern='orders-.*')\n"
        "async def typed(client: AIOKafkaProducer):\n"
        "    await client.send(topic=ORDERS, value=b'secret-sentinel')\n",
    )
    _write(
        tmp_path,
        "worker.py",
        "from aiokafka import AIOKafkaProducer\n"
        "class Worker:\n"
        "    def __init__(self):\n"
        "        self.producer = AIOKafkaProducer()\n"
        "    async def publish(self):\n"
        "        await self.producer.send('orders', b'secret-sentinel')\n",
    )
    context, result = _run(tmp_path)
    channels = _channels(result)
    assert set(channels) == {"aiokafka::orders", "aiokafka::billing"}
    orders = message_channel_id(context.repository_id, "topic", "", "orders")
    billing = message_channel_id(context.repository_id, "topic", "", "billing")
    assert channels["aiokafka::orders"].id == orders
    assert channels["aiokafka::billing"].id == billing
    assert orders != billing
    assert channels["aiokafka::orders"].attributes == (
        ("channel_kind", "topic"),
        ("name", "orders"),
        ("namespace", ""),
    )
    assert _rules(result, "bus.publish", "aiokafka::orders", EdgeType.PUBLISHES) == {
        PUBLISH
    }
    assert _rules(result, "bus.publish", "aiokafka::billing", EdgeType.PUBLISHES) == {
        PUBLISH
    }
    assert _rules(result, "bus.listen", "aiokafka::orders", EdgeType.CONSUMES) == {
        CONSUME,
        SUBSCRIBE,
    }
    assert _rules(result, "bus.listen", "aiokafka::billing", EdgeType.CONSUMES) == {
        CONSUME,
        SUBSCRIBE,
    }
    assert _rules(result, "bus.typed", "aiokafka::orders", EdgeType.PUBLISHES) == {
        PUBLISH
    }
    assert _rules(
        result, "worker.Worker.publish", "aiokafka::orders", EdgeType.PUBLISHES
    ) == {PUBLISH}
    rendered = repr(result.facts)
    assert "secret-sentinel" not in rendered
    assert any(
        item.code == "aiokafka_topic_unresolved" for item in result.diagnostics
    )


def test_dynamic_topic_and_unscoped_call_do_not_emit_edges(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "app.py",
        "from aiokafka import AIOKafkaProducer\n"
        "LOCAL = 'orders'\n"
        "producer = AIOKafkaProducer()\n"
        "producer.send(LOCAL, b'secret-sentinel')\n"
        "async def publish(topic):\n"
        "    bound = 'orders'\n"
        "    await producer.send(topic, b'secret-sentinel')\n"
        "    await producer.send(f'orders.{topic}', b'secret-sentinel')\n"
        "    await producer.send(bound, b'secret-sentinel')\n",
    )
    _, result = _run(tmp_path)
    assert _channels(result) == {}
    assert not any(
        edge.type in {EdgeType.PUBLISHES, EdgeType.CONSUMES}
        for edge in result.facts.edges
    )
    codes = {item.code for item in result.diagnostics}
    assert "aiokafka_topic_unscoped" in codes
    assert "aiokafka_topic_unresolved" in codes
    assert "secret-sentinel" not in repr(result.facts)


def test_unresolved_receiver_and_repeated_binding_do_not_emit(
    tmp_path: Path,
) -> None:
    _write(tmp_path, "topics.py", "ORDERS = 'orders'\n")
    _write(
        tmp_path,
        "app.py",
        "from aiokafka import AIOKafkaConsumer, AIOKafkaProducer\n"
        "from topics import ORDERS\n"
        "producer = AIOKafkaProducer()\n"
        "producer = AIOKafkaProducer()\n"
        "other.send('outside', b'secret-sentinel')\n"
        "async def rebound():\n"
        "    await producer.send(ORDERS, b'secret-sentinel')\n"
        "    other = object()\n"
        "    other.send('mystery', b'secret-sentinel')\n"
        "class Worker:\n"
        "    def __init__(self):\n"
        "        self.producer = AIOKafkaProducer()\n"
        "    def reset(self):\n"
        "        self.producer = AIOKafkaProducer()\n"
        "    async def publish(self):\n"
        "        await self.producer.send('twice', b'secret-sentinel')\n"
        "class Service:\n"
        "    def start(cls):\n"
        "        cls.producer = AIOKafkaProducer()\n"
        "    async def run(cls):\n"
        "        batch = cls.producer.create_batch()\n"
        "        await cls.producer.send_batch(batch, 'kept')\n"
        "async def listen(client: AIOKafkaConsumer):\n"
        "    client.subscribe(['hidden'], pattern='orders-.*')\n"
        "    AIOKafkaConsumer(ORDERS + '.dyn')\n",
    )
    _, result = _run(tmp_path)
    channels = set(_channels(result))
    assert channels == {"aiokafka::kept"}
    assert _rules(result, "app.Service.run", "aiokafka::kept", EdgeType.PUBLISHES) == {
        PUBLISH
    }
    rendered = repr(result.facts)
    assert "secret-sentinel" not in rendered
    assert "orders-.*" not in rendered
    codes = {item.code for item in result.diagnostics}
    assert codes == {"aiokafka_topic_unresolved", "aiokafka_topic_unscoped"}


def test_local_aiokafka_module_is_not_analyzed(tmp_path: Path) -> None:
    _write(tmp_path, "aiokafka.py", "class AIOKafkaProducer:\n    pass\n")
    _write(
        tmp_path,
        "app.py",
        "from aiokafka import AIOKafkaProducer\n"
        "async def publish():\n"
        "    await AIOKafkaProducer().send('orders', b'x')\n",
    )
    _, result = _run(tmp_path)
    assert _channels(result) == {}
    assert not any(item.code.startswith("aiokafka_") for item in result.diagnostics)


def test_lock_selects_adapter_without_entrypoint(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "pyproject.toml",
        '[project]\ndependencies = ["aiokafka>=0.8"]\n',
    )
    _write(
        tmp_path,
        "uv.lock",
        '[[package]]\nname = "aiokafka"\nversion = "0.12.0"\n',
    )
    _write(tmp_path, "app.py", "import aiokafka\n")
    config = SourceScanConfig(20, 8192)
    manifest = build_manifest(
        resolve_local_source(REPO, tmp_path, LocalSourcePolicy((tmp_path,))), config
    )
    language = PythonLanguageAdapter()
    parsed = language.parse(manifest, config)
    registry = AdapterRegistry()
    adapter = AIOKafkaMessagingAdapter()
    assert registry.register(language).accepted
    assert registry.register(adapter).accepted
    selected = select_adapters(
        manifest, parsed, language, registry, (PythonImportDetector(),)
    )
    assert selected.status == "ready"
    assert selected.selected_application is None
    assert selected.deep_adapters == (adapter,)
    support = next(
        item for item in selected.technologies if item.technology == "aiokafka"
    )
    assert support.state == DetectionState.SUPPORTED_PATTERNS
    assert support.capabilities == ("consumes", "publishes", "topics")

    (tmp_path / "uv.lock").write_text(
        '[[package]]\nname = "aiokafka"\nversion = "1.0.0"\n',
        encoding="utf-8",
    )
    manifest = build_manifest(
        resolve_local_source(REPO, tmp_path, LocalSourcePolicy((tmp_path,))), config
    )
    parsed = language.parse(manifest, config)
    unsupported = select_adapters(
        manifest, parsed, language, registry, (PythonImportDetector(),)
    )
    assert unsupported.deep_adapters == ()
    rejected = next(
        item for item in unsupported.technologies if item.technology == "aiokafka"
    )
    assert rejected.state == DetectionState.UNSUPPORTED_VERSION

    (tmp_path / "uv.lock").unlink()
    manifest = build_manifest(
        resolve_local_source(REPO, tmp_path, LocalSourcePolicy((tmp_path,))), config
    )
    parsed = language.parse(manifest, config)
    unverified = select_adapters(
        manifest, parsed, language, registry, (PythonImportDetector(),)
    )
    assert unverified.deep_adapters == ()
    missing = next(
        item for item in unverified.technologies if item.technology == "aiokafka"
    )
    assert missing.state == DetectionState.VERSION_UNVERIFIED
