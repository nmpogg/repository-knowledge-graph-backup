"""TASK-RKG-010 static SQLAlchemy table mapping and read/write facts."""

from __future__ import annotations

from pathlib import Path

from rkg.adapters import (
    AdapterContext,
    AdapterRegistry,
    PythonLanguageAdapter,
    SQLAlchemyDataAccessAdapter,
    run_framework_conformance,
)
from rkg.detection import DetectionState, PythonImportDetector, select_adapters
from rkg.domain import (
    EdgeType,
    EntityType,
    SourceScanConfig,
    data_resource_id,
    validate_fact_batch,
)
from rkg.ingestion import LocalSourcePolicy, build_manifest, resolve_local_source

REPO = "repo-ten"
RULES = {
    "get": "RKG.sqlalchemy.get.v1",
    "select": "RKG.sqlalchemy.select.v1",
    "insert": "RKG.sqlalchemy.insert.v1",
    "update": "RKG.sqlalchemy.update.v1",
    "delete": "RKG.sqlalchemy.delete.v1",
    "add": "RKG.sqlalchemy.add.v1",
}


def _write(root: Path, path: str, content: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def _run(root: Path):
    config = SourceScanConfig(40, 32768)
    manifest = build_manifest(
        resolve_local_source(REPO, root, LocalSourcePolicy((root,))), config
    )
    context = AdapterContext(REPO, "snap-ten", "job-ten", config)
    language = PythonLanguageAdapter()
    parsed = language.parse(manifest, config)
    base = language.extract(context, parsed)
    base = language.resolve(context, parsed, base.facts)
    adapter = SQLAlchemyDataAccessAdapter()
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


def _resources(result):
    return {
        item.qualified_name: item
        for item in result.facts.entities
        if item.type == EntityType.DATA_RESOURCE
    }


def _operations(result, caller: str, resource: str, kind: EdgeType) -> set[str]:
    entities = {item.id: item for item in result.facts.entities}
    evidence = {item.id: item for item in result.facts.evidence}
    found = set()
    for edge in result.facts.edges:
        if edge.type != kind or edge.source_id not in entities:
            continue
        if entities[edge.source_id].qualified_name != caller:
            continue
        if entities[edge.target_id].qualified_name != resource:
            continue
        found.update(evidence[item].rule for item in edge.evidence_ids)
    return found


def test_declarative_identity_does_not_merge_names_or_guess(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "db.py",
        "from sqlalchemy.orm import DeclarativeBase, declarative_base\n"
        "class Base(DeclarativeBase):\n    pass\n"
        "Core = declarative_base()\n",
    )
    _write(
        tmp_path,
        "models.py",
        "from sqlalchemy import MetaData, Table\n"
        "from sqlalchemy.ext.automap import automap_base\n"
        "from db import Base, Core\n"
        "class User(Base):\n"
        "    __tablename__ = 'users'\n"
        "    __table_args__ = {'schema': 'public'}\n"
        "class Account(Base):\n"
        "    __tablename__ = 'users'\n"
        "    __table_args__ = {'schema': 'tenant'}\n"
        "class Profile(Base):\n"
        "    __tablename__ = 'users'\n"
        "class Widget(Core):\n"
        "    __tablename__ = 'widgets'\n"
        "    __table_args__ = ( {'schema': 'app'}, )\n"
        "class Dynamic(Base):\n"
        "    __tablename__ = prefix\n"
        "class Reflected(Base):\n"
        "    __table__ = Table('hidden', MetaData(), autoload_with=None)\n"
        "automap_base()\n",
    )
    _write(
        tmp_path,
        "billing.py",
        "from db import Base\n"
        "class Invoice(Base):\n"
        "    __tablename__ = 'users'\n"
        "    __table_args__ = {'schema': 'public'}\n",
    )
    context, result = _run(tmp_path)
    resources = _resources(result)
    assert set(resources) == {
        "sqlalchemy:public:users",
        "sqlalchemy:tenant:users",
        "sqlalchemy::users",
        "sqlalchemy:app:widgets",
    }
    public = data_resource_id(REPO, "table", "public", ("rkg.sqlalchemy", "users"))
    tenant = data_resource_id(REPO, "table", "tenant", ("rkg.sqlalchemy", "users"))
    plain = data_resource_id(REPO, "table", "", ("rkg.sqlalchemy", "users"))
    assert resources["sqlalchemy:public:users"].id == public
    assert resources["sqlalchemy:tenant:users"].id == tenant
    assert public != tenant != plain
    entities = {item.id: item for item in result.facts.entities}
    mapped = {
        entities[edge.source_id].qualified_name
        for edge in result.facts.edges
        if edge.type == EdgeType.MAPS_TO and edge.target_id == public
    }
    assert mapped == {"models.User", "billing.Invoice"}
    rejected = {"models.Dynamic", "models.Reflected"}
    assert not any(
        entities[edge.source_id].qualified_name in rejected
        for edge in result.facts.edges
        if edge.type == EdgeType.MAPS_TO and edge.source_id in entities
    )
    codes = {item.code for item in result.facts.diagnostics}
    assert "sqlalchemy_table_dynamic" in codes
    assert all(item.framework_kind == "sqlalchemy" for item in resources.values())


def test_reads_and_writes_follow_executed_patterns(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "db.py",
        "from sqlalchemy.orm import DeclarativeBase\n"
        "class Base(DeclarativeBase):\n    pass\n",
    )
    _write(
        tmp_path,
        "models.py",
        "from db import Base\n"
        "class User(Base):\n"
        "    __tablename__ = 'users'\n"
        "    __table_args__ = {'schema': 'public'}\n"
        "    def save(self, session):\n"
        "        session.add(self)\n"
        "class Order(Base):\n"
        "    __tablename__ = 'orders'\n",
    )
    _write(
        tmp_path,
        "repo.py",
        "from sqlalchemy import delete, insert, select, update\n"
        "from models import User as Account\n"
        "from models import Order, User\n"
        "async def read_user(session):\n"
        "    await session.execute(select(User).where(User.id == 1))\n"
        "def get_user(session):\n"
        "    return session.get(Account, 1)\n"
        "def declared_only(session):\n"
        "    stmt = select(Order)\n"
        "    return stmt\n"
        "def chained(session):\n"
        "    stmt = select(User.id)\n"
        "    session.scalars(stmt)\n"
        "def write_all(session, order: Order):\n"
        "    session.execute(insert(Order).values(name='secret-sentinel'))\n"
        "    session.execute(update(Order))\n"
        "    session.execute(delete(Order))\n"
        "    session.delete(order)\n"
        "def unresolved(session):\n"
        "    session.execute(select(Missing))\n"
        "    session.get(User if flag else Order, 1)\n"
        "    session.add(item)\n"
        "select(User)\n",
    )
    _, result = _run(tmp_path)
    users = "sqlalchemy:public:users"
    orders = "sqlalchemy::orders"
    assert _operations(result, "repo.read_user", users, EdgeType.READS) == {
        RULES["select"]
    }
    assert _operations(result, "repo.get_user", users, EdgeType.READS) == {RULES["get"]}
    assert _operations(result, "repo.chained", users, EdgeType.READS) == {
        RULES["select"]
    }
    assert _operations(result, "repo.declared_only", orders, EdgeType.READS) == set()
    assert _operations(result, "models.User.save", users, EdgeType.WRITES) == {
        RULES["add"]
    }
    entities = {item.id: item for item in result.facts.entities}
    write_rules = [
        edge.rule
        for edge in result.facts.edges
        if edge.type == EdgeType.WRITES
        and edge.source_id in entities
        and entities[edge.source_id].qualified_name == "repo.write_all"
    ]
    assert write_rules == [RULES["delete"]]
    assert _operations(result, "repo.write_all", orders, EdgeType.WRITES) == {
        RULES["insert"],
        RULES["update"],
        RULES["delete"],
    }
    assert _operations(result, "repo.unresolved", users, EdgeType.READS) == set()
    assert _operations(result, "repo.unresolved", orders, EdgeType.WRITES) == set()
    rendered = repr(result.facts)
    assert "secret-sentinel" not in rendered
    assert any(
        item.code == "sqlalchemy_operation_not_executed" for item in result.diagnostics
    )
    assert any(
        item.code == "sqlalchemy_operation_unscoped" for item in result.diagnostics
    )
    assert any(
        item.code == "sqlalchemy_model_unresolved" for item in result.diagnostics
    )


def test_local_sqlalchemy_module_is_not_analyzed(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "sqlalchemy.py",
        "class DeclarativeBase:\n    pass\n",
    )
    _write(
        tmp_path,
        "app.py",
        "from sqlalchemy.orm import DeclarativeBase\n"
        "class Base(DeclarativeBase):\n    pass\n"
        "class User(Base):\n"
        "    __tablename__ = 'users'\n",
    )
    _, result = _run(tmp_path)
    assert _resources(result) == {}
    assert not any(item.code.startswith("sqlalchemy_") for item in result.diagnostics)


def test_lock_selects_adapter_without_entrypoint(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "pyproject.toml",
        '[project]\ndependencies = ["SQLAlchemy>=2"]\n',
    )
    _write(
        tmp_path,
        "uv.lock",
        '[[package]]\nname = "sqlalchemy"\nversion = "2.0.36"\n',
    )
    _write(tmp_path, "app.py", "import sqlalchemy\n")
    config = SourceScanConfig(20, 8192)
    manifest = build_manifest(
        resolve_local_source(REPO, tmp_path, LocalSourcePolicy((tmp_path,))), config
    )
    language = PythonLanguageAdapter()
    parsed = language.parse(manifest, config)
    registry = AdapterRegistry()
    adapter = SQLAlchemyDataAccessAdapter()
    assert registry.register(language).accepted
    assert registry.register(adapter).accepted
    selected = select_adapters(
        manifest, parsed, language, registry, (PythonImportDetector(),)
    )
    assert selected.status == "ready"
    assert selected.selected_application is None
    assert selected.deep_adapters == (adapter,)
    support = next(
        item for item in selected.technologies if item.technology == "sqlalchemy"
    )
    assert support.state == DetectionState.SUPPORTED_PATTERNS
    assert support.capabilities == ("maps-to", "reads", "tables", "writes")

    (tmp_path / "uv.lock").write_text(
        '[[package]]\nname = "sqlalchemy"\nversion = "1.4.48"\n',
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
        item for item in unsupported.technologies if item.technology == "sqlalchemy"
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
    assert tuple(a.descriptor.adapter_id for a in unverified.deep_adapters) == (
        "rkg.sqlalchemy",
    )
    missing = next(
        item for item in unverified.technologies if item.technology == "sqlalchemy"
    )
    assert missing.state == DetectionState.VERSION_UNVERIFIED
