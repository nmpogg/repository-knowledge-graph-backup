"""TASK-RKG-006: conservative Python import, call and class edges."""

from __future__ import annotations

from pathlib import Path

from rkg.adapters import AdapterContext, PythonLanguageAdapter, run_language_conformance
from rkg.domain import EdgeType, EntityType, SourceScanConfig, validate_fact_batch
from rkg.ingestion import LocalSourcePolicy, build_manifest, resolve_local_source


def _write(root: Path, relative: str, source: str) -> None:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")


def _run(root: Path):
    config = SourceScanConfig(30, 16384, ("*.py", "**/*.py"))
    manifest = build_manifest(
        resolve_local_source("repo-six", root, LocalSourcePolicy((root,))), config
    )
    context = AdapterContext("repo-six", "snap-six", "job-six", config)
    adapter = PythonLanguageAdapter()
    parsed = adapter.parse(manifest, config)
    extracted = adapter.extract(context, parsed)
    resolved = adapter.resolve(context, parsed, extracted.facts)
    validate_fact_batch(resolved.facts)
    by_id = {item.id: item for item in resolved.facts.entities}
    relations = [
        (
            edge.type,
            by_id[edge.source_id].qualified_name,
            by_id[edge.target_id].qualified_name,
            edge,
        )
        for edge in resolved.facts.edges
        if edge.type != EdgeType.CONTAINS
    ]
    return adapter, manifest, config, context, parsed, resolved, relations


def test_direct_alias_relative_imports_and_await_calls(tmp_path: Path) -> None:
    _write(tmp_path, "pkg/__init__.py", "")
    _write(
        tmp_path,
        "pkg/service.py",
        "def execute():\n    pass\ndef other():\n    pass\n",
    )
    _write(
        tmp_path,
        "pkg/handler.py",
        "from .service import execute as run\n"
        "from . import service\n"
        "import pkg.service as svc\n"
        "async def handler():\n"
        "    run()\n"
        "    await run()\n"
        "    service.execute()\n"
        "    svc.other()\n",
    )
    adapter, manifest, config, context, _, resolved, relations = _run(tmp_path)
    imports = [
        (source, target)
        for kind, source, target, _ in relations
        if kind == EdgeType.IMPORTS
    ]
    assert imports.count(("pkg.handler", "pkg.service")) == 1
    assert ("pkg.handler", "pkg.service.execute") in imports
    calls = [
        (source, target)
        for kind, source, target, _ in relations
        if kind == EdgeType.CALLS
    ]
    assert sorted(calls) == [
        ("pkg.handler.handler", "pkg.service.execute"),
        ("pkg.handler.handler", "pkg.service.other"),
    ]
    execute_edge = next(
        edge
        for kind, _, target, edge in relations
        if kind == EdgeType.CALLS and target == "pkg.service.execute"
    )
    assert len(execute_edge.evidence_ids) == 3
    assert all(
        item.type != EntityType.EXTERNAL_DEPENDENCY for item in resolved.facts.entities
    )
    report = run_language_conformance(
        adapter, manifest, config, context, no_execution_marker=lambda: False
    )
    assert report.pass_rate == 1.0


def test_shadowing_star_import_dynamic_dispatch_and_constructor_are_not_calls(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path,
        "local.py",
        "from unknown import *\n"
        "def target():\n    pass\n"
        "def caller(target):\n    target()\n"
        "def duplicate():\n    pass\n"
        "def duplicate():\n    pass\n"
        "def use():\n    duplicate()\n    Service()\n"
        "class Service:\n"
        "    def method(self):\n        self.dynamic()\n"
        "target()\n",
    )
    _, _, _, _, _, resolved, relations = _run(tmp_path)
    assert not any(kind == EdgeType.CALLS for kind, _, _, _ in relations)
    codes = {item.code for item in resolved.diagnostics}
    assert {
        "python_import_star",
        "python_duplicate_definition",
        "python_binding_ambiguous",
        "python_call_dynamic",
    }.issubset(codes)
    assert all(
        item.file_path == "local.py" and item.line is not None
        for item in resolved.facts.diagnostics
    )


def test_unique_instance_method_call_and_reassignment_is_not_guessed(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path,
        "service.py",
        "def helper():\n"
        "    pass\n"
        "class RoomBook:\n"
        "    def create(self):\n"
        "        helper()\n"
        "book = RoomBook()\n"
        "again = RoomBook()\n"
        "again = RoomBook()\n"
        "def run():\n"
        "    book.create()\n"
        "    again.create()\n",
    )
    _, _, _, _, _, resolved, relations = _run(tmp_path)
    calls = [
        (source, target, edge)
        for kind, source, target, edge in relations
        if kind == EdgeType.CALLS
    ]
    assert sorted((source, target) for source, target, _ in calls) == [
        ("service.RoomBook.create", "service.helper"),
        ("service.run", "service.RoomBook.create"),
    ]
    run_edge = next(edge for source, _, edge in calls if source == "service.run")
    assert len(run_edge.evidence_ids) == 1
    assert "python_call_unresolved" in {item.code for item in resolved.diagnostics}
    assert all(
        item.file_path == "service.py" and item.line
        for item in resolved.facts.diagnostics
        if item.code == "python_call_unresolved"
    )


def test_local_receivers_self_fields_annotations_and_inheritance(tmp_path: Path):
    _write(
        tmp_path,
        "app.py",
        "class Repo:\n    def read(self):\n        pass\n"
        "class Child(Repo):\n    pass\n"
        "class Service:\n"
        "    def __init__(self):\n        self.repo = Child()\n"
        "    def run(self):\n        self.repo.read()\n        self.next()\n"
        "    def next(self):\n        pass\n"
        "def annotated(service: Service):\n    service.run()\n"
        "def invoke(service):\n    service.run()\n"
        "def handler():\n    instance = Service()\n"
        "    annotated(instance)\n    invoke(instance)\n    Service().run()\n",
    )
    *_, relations = _run(tmp_path)
    calls = {(s, t) for k, s, t, _ in relations if k == EdgeType.CALLS}
    assert {
        ("app.Service.run", "app.Repo.read"),
        ("app.Service.run", "app.Service.next"),
        ("app.annotated", "app.Service.run"),
        ("app.invoke", "app.Service.run"),
        ("app.handler", "app.Service.run"),
    } <= calls


def test_conflicting_parameter_types_and_reassigned_fields_are_not_guessed(
    tmp_path: Path,
):
    _write(
        tmp_path,
        "app.py",
        "class A:\n    def run(self):\n        pass\n"
        "class B:\n    def run(self):\n        pass\n"
        "def invoke(service):\n    service.run()\n"
        "def caller():\n    invoke(A())\n    invoke(B())\n"
        "class Service:\n"
        "    def __init__(self):\n        self.repo = A()\n"
        "    def reset(self):\n        self.repo = B()\n"
        "    def run(self):\n        self.repo.run()\n"
        "def conditional(flag):\n    if flag:\n        service = A()\n"
        "    service.run()\n",
    )
    *_, relations = _run(tmp_path)
    assert not any(
        s in {"app.invoke", "app.Service.run", "app.conditional"}
        and k == EdgeType.CALLS
        for k, s, _, _ in relations
    )


def test_direct_bases_and_explicit_abstraction_only(tmp_path: Path) -> None:
    _write(tmp_path, "pkg/__init__.py", "")
    _write(
        tmp_path,
        "pkg/base.py",
        "from abc import ABC, abstractmethod\n"
        "class Interface(ABC):\n"
        "    @abstractmethod\n"
        "    def run(self):\n        pass\n"
        "class Ordinary:\n"
        "    def run(self):\n        pass\n",
    )
    _write(
        tmp_path,
        "pkg/impl.py",
        "from .base import Interface, Ordinary\n"
        "class Concrete(Interface, Ordinary):\n    pass\n"
        "class Copy(Ordinary):\n    pass\n",
    )
    _, _, _, _, _, _, relations = _run(tmp_path)
    hierarchy = {
        (kind, source, target)
        for kind, source, target, _ in relations
        if kind in (EdgeType.INHERITS_FROM, EdgeType.IMPLEMENTS)
    }
    assert hierarchy == {
        (EdgeType.INHERITS_FROM, "pkg.impl.Concrete", "pkg.base.Interface"),
        (EdgeType.INHERITS_FROM, "pkg.impl.Concrete", "pkg.base.Ordinary"),
        (EdgeType.INHERITS_FROM, "pkg.impl.Copy", "pkg.base.Ordinary"),
        (EdgeType.IMPLEMENTS, "pkg.impl.Concrete", "pkg.base.Interface"),
    }


def test_local_module_shadows_distribution_name_without_external_fact(
    tmp_path: Path,
) -> None:
    _write(tmp_path, "fastapi.py", "def local():\n    pass\n")
    _write(tmp_path, "consumer.py", "import fastapi\ndef run():\n    fastapi.local()\n")
    _, _, _, _, _, resolved, relations = _run(tmp_path)
    assert (EdgeType.IMPORTS, "consumer", "fastapi") in [
        (kind, source, target) for kind, source, target, _ in relations
    ]
    assert (EdgeType.CALLS, "consumer.run", "fastapi.local") in [
        (kind, source, target) for kind, source, target, _ in relations
    ]
    assert all(
        item.type != EntityType.EXTERNAL_DEPENDENCY for item in resolved.facts.entities
    )


def test_reassigned_import_binding_does_not_create_call(tmp_path: Path) -> None:
    _write(tmp_path, "helper.py", "def act():\n    pass\n")
    _write(
        tmp_path,
        "consumer.py",
        "from helper import act as bound\nbound = object()\ndef run():\n    bound()\n",
    )
    _, _, _, _, _, resolved, relations = _run(tmp_path)
    assert not any(kind == EdgeType.CALLS for kind, _, _, _ in relations)
    assert "python_binding_ambiguous" in {item.code for item in resolved.diagnostics}


def test_local_abc_name_does_not_mark_type_as_abstract(tmp_path: Path) -> None:
    _write(tmp_path, "abc.py", "class ABC:\n    pass\n")
    _write(
        tmp_path,
        "model.py",
        "from abc import ABC\n"
        "class Base(ABC):\n    pass\n"
        "class Derived(Base):\n    pass\n",
    )
    _, _, _, _, _, _, relations = _run(tmp_path)
    hierarchy = {
        (kind, source, target)
        for kind, source, target, _ in relations
        if kind in (EdgeType.INHERITS_FROM, EdgeType.IMPLEMENTS)
    }
    assert hierarchy == {
        (EdgeType.INHERITS_FROM, "model.Base", "abc.ABC"),
        (EdgeType.INHERITS_FROM, "model.Derived", "model.Base"),
    }
