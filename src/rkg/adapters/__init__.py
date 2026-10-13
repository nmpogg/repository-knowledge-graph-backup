"""Versioned analyzer adapter interfaces, registry and conformance checks."""

from rkg.adapters.aiokafka_messaging import AIOKafkaMessagingAdapter
from rkg.adapters.conformance import (
    ConformanceReport,
    run_framework_conformance,
    run_language_conformance,
)
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
    FrameworkAdapter,
    LanguageAdapter,
    ParsedUnit,
    ParseResult,
    SupportState,
    SymbolRef,
    TechnologyConstraint,
    TechnologyDetection,
)
from rkg.adapters.fastapi_framework import FastAPIFrameworkAdapter
from rkg.adapters.flask_framework import FlaskFrameworkAdapter
from rkg.adapters.python_language import PythonLanguageAdapter
from rkg.adapters.react_router_framework import ReactRouterFrameworkAdapter
from rkg.adapters.registry import AdapterRegistry, Registration, RegistryIssue
from rkg.adapters.sqlalchemy_data import SQLAlchemyDataAccessAdapter
from rkg.adapters.typescript_language import TypeScriptLanguageAdapter

__all__ = [
    "CONTRACT_VERSION",
    "AIOKafkaMessagingAdapter",
    "AdapterContext",
    "AdapterDescriptor",
    "AdapterDiagnostic",
    "AdapterKind",
    "AdapterRegistry",
    "AdapterResult",
    "Capability",
    "ConformanceReport",
    "DetectionEvidence",
    "DetectionReport",
    "FrameworkAdapter",
    "FastAPIFrameworkAdapter",
    "FlaskFrameworkAdapter",
    "LanguageAdapter",
    "ParseResult",
    "ParsedUnit",
    "PythonLanguageAdapter",
    "ReactRouterFrameworkAdapter",
    "SQLAlchemyDataAccessAdapter",
    "TypeScriptLanguageAdapter",
    "Registration",
    "RegistryIssue",
    "SupportState",
    "SymbolRef",
    "TechnologyConstraint",
    "TechnologyDetection",
    "run_language_conformance",
    "run_framework_conformance",
]
