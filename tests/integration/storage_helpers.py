"""Helpers shared by storage/graph integration tests."""

from __future__ import annotations

from rkg.domain import (
    Edge,
    EdgeType,
    Entity,
    EntityType,
    Evidence,
    FactBatch,
    edge_id,
    evidence_id,
    source_entity_id,
)
from rkg.graph import SnapshotPublishMeta

RULE_CONTAINS = "RKG.python.contains.v1"
RULE_EXPOSES = "RKG.fastapi.exposes.v1"
RULE_DEPENDS = "RKG.python.depends_on.v1"


def publish_meta(suffix: str = "1") -> SnapshotPublishMeta:
    return SnapshotPublishMeta(
        source_revision=f"manifest:{'a' * 64}",
        manifest_hash="b" * 64,
        scan_config_digest="c" * 64,
        analyzer_version="0.1.0",
        schema_version="TBL-RKG-GRAPH@9",
        adapter_versions={"python": "1.0.0"},
    )


def simple_batch(
    repository_id: str,
    snapshot_id: str,
    *,
    include_repo_edges: bool = True,
    extra_entity_name: str | None = None,
) -> FactBatch:
    file_path = "app/main.py"
    entities = [
        Entity(
            id=source_entity_id(
                repository_id, file_path, "SourceUnit", "app.main"
            ),
            repository_id=repository_id,
            snapshot_id=snapshot_id,
            type=EntityType.SOURCE_UNIT,
            name="main",
            qualified_name="app.main",
            file_path=file_path,
            start_line=1,
            end_line=10,
        ),
        Entity(
            id=source_entity_id(
                repository_id, file_path, "Endpoint", "app.main.get_health"
            ),
            repository_id=repository_id,
            snapshot_id=snapshot_id,
            type=EntityType.ENDPOINT,
            name="get_health",
            qualified_name="app.main.get_health",
            file_path=file_path,
            start_line=5,
            end_line=8,
            attributes=(("method", "GET"), ("path", "/health")),
        ),
        Entity(
            id=source_entity_id(
                repository_id, "deps", "ExternalDependency", "pkg:requests"
            ),
            repository_id=repository_id,
            snapshot_id=snapshot_id,
            type=EntityType.EXTERNAL_DEPENDENCY,
            name="requests",
            qualified_name="pkg:requests",
            attributes=(
                ("kind", "pypi"),
                ("version_constraint", ">=2"),
                ("origin", "requirements"),
            ),
        ),
    ]
    if extra_entity_name:
        entities.append(
            Entity(
                id=source_entity_id(
                    repository_id,
                    file_path,
                    "Callable",
                    f"app.main.{extra_entity_name}",
                ),
                repository_id=repository_id,
                snapshot_id=snapshot_id,
                type=EntityType.CALLABLE,
                name=extra_entity_name,
                qualified_name=f"app.main.{extra_entity_name}",
                file_path=file_path,
                start_line=20,
                end_line=25,
            )
        )

    by_q = {e.qualified_name: e for e in entities}
    evidence_items = [
        Evidence(
            evidence_id(snapshot_id, file_path, 1, 1, RULE_CONTAINS),
            snapshot_id,
            file_path,
            1,
            1,
            RULE_CONTAINS,
        ),
        Evidence(
            evidence_id(snapshot_id, file_path, 5, 5, RULE_EXPOSES),
            snapshot_id,
            file_path,
            5,
            5,
            RULE_EXPOSES,
        ),
        Evidence(
            evidence_id(snapshot_id, file_path, 2, 2, RULE_DEPENDS),
            snapshot_id,
            file_path,
            2,
            2,
            RULE_DEPENDS,
        ),
    ]
    edges = [
        Edge(
            id=edge_id(
                snapshot_id,
                EdgeType.CONTAINS,
                by_q["app.main"].id,
                by_q["app.main.get_health"].id,
            ),
            snapshot_id=snapshot_id,
            type=EdgeType.CONTAINS,
            source_id=by_q["app.main"].id,
            target_id=by_q["app.main.get_health"].id,
            rule=RULE_CONTAINS,
            evidence_ids=(evidence_items[0].id,),
        ),
    ]
    if include_repo_edges:
        edges.extend(
            [
                Edge(
                    id=edge_id(
                        snapshot_id,
                        EdgeType.EXPOSES,
                        repository_id,
                        by_q["app.main.get_health"].id,
                    ),
                    snapshot_id=snapshot_id,
                    type=EdgeType.EXPOSES,
                    source_id=repository_id,
                    target_id=by_q["app.main.get_health"].id,
                    rule=RULE_EXPOSES,
                    evidence_ids=(evidence_items[1].id,),
                ),
                Edge(
                    id=edge_id(
                        snapshot_id,
                        EdgeType.DEPENDS_ON,
                        repository_id,
                        by_q["pkg:requests"].id,
                    ),
                    snapshot_id=snapshot_id,
                    type=EdgeType.DEPENDS_ON,
                    source_id=repository_id,
                    target_id=by_q["pkg:requests"].id,
                    rule=RULE_DEPENDS,
                    evidence_ids=(evidence_items[2].id,),
                ),
            ]
        )
    return FactBatch(
        repository_id=repository_id,
        snapshot_id=snapshot_id,
        entities=tuple(entities),
        edges=tuple(edges),
        evidence=tuple(evidence_items),
    )
