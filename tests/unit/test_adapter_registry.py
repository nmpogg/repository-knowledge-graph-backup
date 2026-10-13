"""Contract/registry unit tests, without the later conformance fixture adapter."""

from dataclasses import replace

import pytest

from rkg.adapters import (
    CONTRACT_VERSION,
    AdapterDescriptor,
    AdapterKind,
    AdapterRegistry,
    ConformanceReport,
    DetectionEvidence,
    TechnologyConstraint,
    TechnologyDetection,
)
from rkg.adapters.conformance import ConformanceCase


def descriptor(
    adapter_id: str,
    *,
    kind: AdapterKind = AdapterKind.LANGUAGE,
    framework: str | None = None,
    constraints: tuple[TechnologyConstraint, ...] = (),
) -> AdapterDescriptor:
    return AdapterDescriptor(
        adapter_id=adapter_id,
        adapter_version="1.0.0",
        contract_version=CONTRACT_VERSION,
        kind=kind,
        language="synthetic",
        grammar_or_target="synthetic grammar v1",
        file_patterns=("*.synthetic",),
        ignore_patterns=(),
        capabilities=("structure",),
        framework=framework,
        technology_constraints=constraints,
    )


class LanguageStub:
    def __init__(self, value: AdapterDescriptor) -> None:
        self.descriptor = value

    def detect(self, manifest):
        raise NotImplementedError

    def parse(self, manifest, config):
        raise NotImplementedError

    def extract(self, context, parsed):
        raise NotImplementedError

    def resolve(self, context, parsed, candidate):
        raise NotImplementedError


class DeepStub:
    def __init__(self, value: AdapterDescriptor) -> None:
        self.descriptor = value

    def detect(self, manifest, parsed):
        raise NotImplementedError

    def extract(self, context, parsed, base):
        raise NotImplementedError

    def resolve(self, context, parsed, candidate):
        raise NotImplementedError


def detection(technology: str, version: str | None = None) -> TechnologyDetection:
    return TechnologyDetection(
        technology,
        version,
        (DetectionEvidence("main.synthetic", "RKG.fixture.detect.v1"),),
    )


def test_descriptor_rejects_incomplete_and_invalid_contract_fields() -> None:
    valid = descriptor("rkg.synthetic")
    with pytest.raises(ValueError, match="adapter ID"):
        replace(valid, adapter_id="bad id")
    with pytest.raises(ValueError, match="adapter version"):
        replace(valid, adapter_version="latest")
    with pytest.raises(ValueError, match="file pattern"):
        replace(valid, file_patterns=())
    with pytest.raises(ValueError, match="capabilities"):
        replace(valid, capabilities=("structure", "structure"))
    with pytest.raises(ValueError, match="deep adapter"):
        replace(valid, kind=AdapterKind.FRAMEWORK)
    with pytest.raises(ValueError, match="numeric version"):
        TechnologyConstraint("framework", ">=1.0rc1")


def test_registry_rejects_incompatible_duplicate_and_missing_interface() -> None:
    registry = AdapterRegistry()
    old = LanguageStub(
        replace(descriptor("rkg.synthetic"), contract_version="rkg.adapter/v1")
    )
    result = registry.register(old)
    assert not result.accepted
    assert result.issue.code == "adapter_contract_incompatible"
    current = LanguageStub(descriptor("rkg.synthetic"))
    assert registry.register(current).accepted
    assert registry.register(current).issue.code == "adapter_duplicate"
    missing_methods = type(
        "MissingMethods", (), {"descriptor": descriptor("rkg.bad")}
    )()
    assert registry.register(missing_methods).issue.code == "adapter_interface_invalid"
    assert list(registry.inventory()) == [("rkg.synthetic", "1.0.0")]


def test_registry_selection_uses_evidence_and_stable_order() -> None:
    registry = AdapterRegistry()
    for adapter_id in ("rkg.zeta", "rkg.alpha"):
        assert registry.register(LanguageStub(descriptor(adapter_id))).accepted
    assert registry.select_language("synthetic", ()) == ()
    selected = registry.select_language("synthetic", (detection("synthetic"),))
    assert [item.descriptor.adapter_id for item in selected] == [
        "rkg.alpha",
        "rkg.zeta",
    ]
    assert (
        registry.select_language(
            "synthetic", (detection("synthetic"),), capabilities=frozenset({"routes"})
        )
        == ()
    )


def test_deep_adapter_requires_language_technology_and_matching_version() -> None:
    registry = AdapterRegistry()
    deep = DeepStub(
        descriptor(
            "rkg.web",
            kind=AdapterKind.FRAMEWORK,
            framework="web",
            constraints=(TechnologyConstraint("web", ">=1.2,<2.0"),),
        )
    )
    assert registry.register(deep).accepted
    assert registry.select_deep("other", (detection("web", "1.5"),)) == ()
    assert registry.select_deep("synthetic", ()) == ()
    assert registry.select_deep("synthetic", (detection("web", None),)) == ()
    assert registry.select_deep("synthetic", (detection("web", "2.0"),)) == ()
    assert registry.select_deep("synthetic", (detection("web", "1.5"),)) == (deep,)


def test_conformance_pass_rate_is_machine_readable() -> None:
    report = ConformanceReport(
        "rkg.synthetic",
        CONTRACT_VERSION,
        (ConformanceCase("one", True), ConformanceCase("two", False, "AssertionError")),
    )
    assert report.pass_rate == 0.5
