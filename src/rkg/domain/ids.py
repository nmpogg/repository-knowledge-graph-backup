"""Stable, opaque IDs for canonical graph facts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rkg.domain.models import SourceScanConfig


def _id(prefix: str, *parts: str) -> str:
    # JSON framing avoids collisions between variable-length identity fields.
    payload = json.dumps(parts, ensure_ascii=False, separators=(",", ":"))
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"{prefix}_{digest}"


def source_entity_id(
    repository_id: str, file_path: str, entity_type: str, qualified_name: str
) -> str:
    """Line movement does not change an ordinary source entity's identity."""
    return _id("ent", repository_id, file_path, entity_type, qualified_name)


def endpoint_id(
    repository_id: str,
    file_path: str,
    qualified_name: str,
    method: str,
    route_path: str,
    registration_chain: tuple[str, ...],
) -> str:
    """Keep distinct registrations, including duplicate method/path routes."""
    if not registration_chain:
        raise ValueError("endpoint registration_chain cannot be empty")
    return _id(
        "ent",
        repository_id,
        file_path,
        "Endpoint",
        qualified_name,
        method.upper(),
        route_path,
        *registration_chain,
    )


def data_resource_id(
    repository_id: str,
    resource_kind: str,
    namespace: str,
    adapter_identity: tuple[str, ...],
) -> str:
    if not adapter_identity:
        raise ValueError("data resource adapter_identity cannot be empty")
    return _id(
        "ent",
        repository_id,
        "DataResource",
        resource_kind,
        namespace,
        *adapter_identity,
    )


def message_channel_id(
    repository_id: str, channel_kind: str, namespace: str, name: str
) -> str:
    return _id("ent", repository_id, "MessageChannel", channel_kind, namespace, name)


def configuration_id(repository_id: str, kind: str, owner: str, key: str) -> str:
    return _id("ent", repository_id, "Configuration", kind, owner, key)


def edge_id(snapshot_id: str, edge_type: str, source_id: str, target_id: str) -> str:
    """Call sites for the same directed pair aggregate under one edge ID."""
    return _id("edge", snapshot_id, edge_type, source_id, target_id)


def evidence_id(
    snapshot_id: str, file_path: str, start_line: int, end_line: int, rule: str
) -> str:
    return _id("ev", snapshot_id, file_path, str(start_line), str(end_line), rule)


def diagnostic_id(
    job_id: str, code: str, file_path: str | None, line: int | None, ordinal: int
) -> str:
    return _id("diag", job_id, code, file_path or "", str(line or ""), str(ordinal))


def scan_config_digest(config: SourceScanConfig) -> str:
    """Digest effective non-secret scan options for snapshot provenance."""
    payload = json.dumps(
        asdict(config), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
