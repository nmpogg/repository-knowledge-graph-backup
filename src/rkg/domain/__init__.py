"""Transport-neutral canonical facts and identity/validation helpers."""

from rkg.domain.context import context_dict, context_json
from rkg.domain.ids import (
    configuration_id,
    data_resource_id,
    diagnostic_id,
    edge_id,
    endpoint_id,
    evidence_id,
    message_channel_id,
    scan_config_digest,
    source_entity_id,
)
from rkg.domain.models import (
    ContextBudget,
    ContextPackage,
    Diagnostic,
    Edge,
    EdgeType,
    Entity,
    EntityType,
    Evidence,
    FactBatch,
    Severity,
    SourceScanConfig,
)
from rkg.domain.validation import InvalidFactBatch, validate_fact_batch

__all__ = [
    "ContextBudget",
    "ContextPackage",
    "Diagnostic",
    "Edge",
    "EdgeType",
    "Entity",
    "EntityType",
    "Evidence",
    "FactBatch",
    "InvalidFactBatch",
    "Severity",
    "SourceScanConfig",
    "configuration_id",
    "context_dict",
    "context_json",
    "data_resource_id",
    "diagnostic_id",
    "edge_id",
    "endpoint_id",
    "evidence_id",
    "message_channel_id",
    "scan_config_digest",
    "source_entity_id",
    "validate_fact_batch",
]
