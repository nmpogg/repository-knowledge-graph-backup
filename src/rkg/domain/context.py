"""Deterministic wire representation for a completed context package."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from rkg.domain.models import ContextPackage


def context_dict(package: ContextPackage) -> dict[str, Any]:
    """Sort fact collections without changing graph/traversal selection."""
    node_ids = {node.id for node in package.nodes}
    if package.root_id not in node_ids:
        raise ValueError("context root must be present")
    if any(
        node.repository_id != package.repository_id
        or node.snapshot_id != package.snapshot_id
        for node in package.nodes
    ):
        raise ValueError("context node ownership mismatch")
    if any(
        edge.snapshot_id != package.snapshot_id
        or (edge.source_id not in node_ids and edge.source_id != package.repository_id)
        or edge.target_id not in node_ids
        for edge in package.edges
    ):
        raise ValueError("context edges must reference included nodes")
    if any(item.snapshot_id != package.snapshot_id for item in package.evidence):
        raise ValueError("context evidence ownership mismatch")

    nodes = []
    for node in sorted(package.nodes, key=lambda n: (n.type, n.qualified_name, n.id)):
        payload = asdict(node)
        payload["attributes"] = dict(sorted(node.attributes))
        nodes.append(payload)
    return {
        "schema_version": package.schema_version,
        "repository_id": package.repository_id,
        "snapshot_id": package.snapshot_id,
        "root_id": package.root_id,
        "nodes": nodes,
        "edges": [
            asdict(edge)
            for edge in sorted(
                package.edges, key=lambda e: (e.type, e.source_id, e.target_id, e.id)
            )
        ],
        "evidence": [
            {
                **asdict(item),
                "provenance": (
                    "filesystem"
                    if item.rule == "RKG.structure.contains.v1"
                    else "source"
                ),
            }
            for item in sorted(
                package.evidence, key=lambda e: (e.file_path, e.start_line, e.id)
            )
        ],
        "diagnostic_summary": dict(sorted(package.diagnostic_summary)),
        "budget": asdict(package.budget),
        "truncated": package.truncated,
        "truncation_reasons": sorted(set(package.truncation_reasons)),
    }


def context_json(package: ContextPackage) -> str:
    return json.dumps(
        context_dict(package),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
