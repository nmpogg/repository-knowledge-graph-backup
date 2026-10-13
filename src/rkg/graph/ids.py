"""Snapshot-qualified physical keys for Entity nodes (Kùzu single-column PK)."""

from __future__ import annotations

_SEP = ":"


def physical_entity_id(snapshot_id: str, domain_id: str) -> str:
    """Encode domain entity ID for physical storage within one snapshot."""
    if not snapshot_id or not domain_id:
        raise ValueError("snapshot_id and domain_id are required")
    if domain_id.startswith(f"{snapshot_id}{_SEP}"):
        return domain_id
    return f"{snapshot_id}{_SEP}{domain_id}"


def logical_entity_id(physical_id: str, snapshot_id: str | None = None) -> str:
    """Decode a physical Entity PK back to the domain ID."""
    if snapshot_id and physical_id.startswith(f"{snapshot_id}{_SEP}"):
        return physical_id[len(snapshot_id) + 1 :]
    if _SEP in physical_id:
        # Best-effort: first segment is snapshot_id (IDs use prefix_hex, no colon).
        _, _, rest = physical_id.partition(_SEP)
        return rest
    return physical_id


def resolve_endpoint_physical_id(
    endpoint_id: str, *, snapshot_id: str, repository_id: str
) -> str:
    """Repository catalog IDs stay bare; entity endpoints are snapshot-qualified."""
    if endpoint_id == repository_id:
        return endpoint_id
    return physical_entity_id(snapshot_id, endpoint_id)
