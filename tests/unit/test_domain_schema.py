"""Golden DTO and invariant tests for T-002, without running source analysis."""

import json
from dataclasses import replace
from pathlib import Path

import pytest

from rkg.domain import (
    ContextBudget,
    ContextPackage,
    Edge,
    EdgeType,
    Entity,
    EntityType,
    Evidence,
    FactBatch,
    InvalidFactBatch,
    SourceScanConfig,
    context_json,
    data_resource_id,
    edge_id,
    endpoint_id,
    evidence_id,
    scan_config_digest,
    source_entity_id,
    validate_fact_batch,
)

FIXTURE = Path(__file__).parents[1] / "fixtures" / "domain" / "source_structure.json"
RULE = "RKG.python.contains.v1"


def golden_batch() -> tuple[FactBatch, dict[str, object]]:
    expected = json.loads(FIXTURE.read_text(encoding="utf-8"))
    repo = expected["repository_id"]
    snap = expected["snapshot_id"]
    file_path = expected["file_path"]
    entities = tuple(
        Entity(
            id=source_entity_id(repo, file_path, node["type"], node["qualified_name"]),
            repository_id=repo,
            snapshot_id=snap,
            type=EntityType(node["type"]),
            name=node["name"],
            qualified_name=node["qualified_name"],
            file_path=file_path,
            start_line=index + 1,
            end_line=index + 1,
        )
        for index, node in enumerate(expected["nodes"])
    )
    by_key = dict(
        zip((node["key"] for node in expected["nodes"]), entities, strict=True)
    )
    locations = tuple(
        Evidence(
            evidence_id(snap, file_path, index + 2, index + 2, RULE),
            snap,
            file_path,
            index + 2,
            index + 2,
            RULE,
        )
        for index in range(len(expected["contains"]))
    )
    edges = tuple(
        Edge(
            id=edge_id(snap, EdgeType.CONTAINS, by_key[parent].id, by_key[child].id),
            snapshot_id=snap,
            type=EdgeType.CONTAINS,
            source_id=by_key[parent].id,
            target_id=by_key[child].id,
            rule=RULE,
            evidence_ids=(locations[index].id,),
        )
        for index, (parent, child) in enumerate(expected["contains"])
    )
    return FactBatch(repo, snap, entities, edges, locations), expected


def test_ac_002_golden_source_structure_and_lexical_parent() -> None:
    batch, expected = golden_batch()
    validate_fact_batch(batch)
    assert [
        (entity.type, entity.name, entity.qualified_name) for entity in batch.entities
    ] == [
        (node["type"], node["name"], node["qualified_name"])
        for node in expected["nodes"]
    ]
    ids_to_names = {entity.id: entity.qualified_name for entity in batch.entities}
    actual = [
        [ids_to_names[edge.source_id], ids_to_names[edge.target_id]]
        for edge in batch.edges
    ]
    names = {node["key"]: node["qualified_name"] for node in expected["nodes"]}
    assert actual == [
        [names[parent], names[child]] for parent, child in expected["contains"]
    ]
    assert actual[-1] == [
        "pkg.orders.OrderService.create",
        "pkg.orders.OrderService.create.validate",
    ]
    assert len({entity.id for entity in batch.entities}) == len(batch.entities)


def test_ac_007_rejects_missing_cross_snapshot_and_invalid_evidence() -> None:
    batch, _ = golden_batch()
    edge = batch.edges[0]
    with pytest.raises(InvalidFactBatch, match="missing evidence"):
        validate_fact_batch(
            replace(batch, edges=(replace(edge, evidence_ids=("missing",)),))
        )
    with pytest.raises(InvalidFactBatch, match="another snapshot"):
        changed = replace(batch.evidence[0], snapshot_id="other")
        validate_fact_batch(replace(batch, evidence=(changed, *batch.evidence[1:])))
    with pytest.raises(InvalidFactBatch, match="source is missing"):
        missing = replace(
            edge,
            source_id="other",
            id=edge_id(batch.snapshot_id, edge.type, "other", edge.target_id),
        )
        validate_fact_batch(replace(batch, edges=(missing,)))
    with pytest.raises(InvalidFactBatch, match="versioned"):
        validate_fact_batch(replace(batch, edges=(replace(edge, rule="ad_hoc"),)))
    with pytest.raises(InvalidFactBatch, match="endpoint types"):
        wrong_type = replace(
            edge,
            type=EdgeType.CALLS,
            id=edge_id(
                batch.snapshot_id, EdgeType.CALLS, edge.source_id, edge.target_id
            ),
        )
        validate_fact_batch(replace(batch, edges=(wrong_type,)))
    with pytest.raises(InvalidFactBatch, match="relative"):
        changed = replace(batch.entities[0], file_path="C:/private/source.py")
        validate_fact_batch(replace(batch, entities=(changed, *batch.entities[1:])))


def test_endpoint_identity_keeps_registration_chains_distinct() -> None:
    args = ("repo", "pkg/routes.py", "pkg.routes.get_item", "GET", "/items/{id}")
    assert endpoint_id(*args, ("app", "router-a")) != endpoint_id(
        *args, ("app", "router-b")
    )
    assert endpoint_id(*args, ("app", "router-a")) != endpoint_id(
        "repo",
        "pkg/routes.py",
        "pkg.routes.get_item",
        "POST",
        "/items/{id}",
        ("app", "router-a"),
    )
    assert source_entity_id(
        "repo", "pkg/a.py", "Callable", "pkg.a.f"
    ) == source_entity_id("repo", "pkg/a.py", "Callable", "pkg.a.f")
    assert data_resource_id(
        "repo", "table", "public", ("adapter-a", "orders")
    ) != data_resource_id("repo", "table", "tenant", ("adapter-a", "orders"))


def test_endpoint_chain_metadata_can_be_serialized_without_merging_identity() -> None:
    batch, _ = golden_batch()
    method = "GET"
    route = "/items/{id}"
    chain = ("app.register@12", "router.include@34")
    endpoint = Entity(
        id=endpoint_id(
            batch.repository_id, "pkg/routes.py", "pkg.routes.get", method, route, chain
        ),
        repository_id=batch.repository_id,
        snapshot_id=batch.snapshot_id,
        type=EntityType.ENDPOINT,
        name="get",
        qualified_name="pkg.routes.get",
        file_path="pkg/routes.py",
        attributes=(
            ("method", method),
            ("route_path", route),
            ("registration_chain", chain),
        ),
    )
    validate_fact_batch(replace(batch, entities=(*batch.entities, endpoint)))


def test_configuration_value_is_not_a_graph_fact() -> None:
    batch, _ = golden_batch()
    config = Entity(
        id="config-id",
        repository_id=batch.repository_id,
        snapshot_id=batch.snapshot_id,
        type=EntityType.CONFIGURATION,
        name="TOKEN",
        qualified_name="pkg.TOKEN",
        attributes=(("value", "secret-sentinel"),),
    )
    with pytest.raises(InvalidFactBatch, match="configuration values"):
        validate_fact_batch(replace(batch, entities=(*batch.entities, config)))


def test_ac_010_context_schema_order_and_budget_dto() -> None:
    batch, _ = golden_batch()
    package = ContextPackage(
        schema_version="v1",
        repository_id=batch.repository_id,
        snapshot_id=batch.snapshot_id,
        root_id=batch.entities[0].id,
        nodes=tuple(reversed(batch.entities)),
        edges=tuple(reversed(batch.edges)),
        evidence=tuple(reversed(batch.evidence)),
        diagnostic_summary=(("warning", 1),),
        budget=ContextBudget(4, 50, 100, 20000),
    )
    rendered = context_json(package)
    assert rendered == context_json(
        replace(
            package, nodes=batch.entities, edges=batch.edges, evidence=batch.evidence
        )
    )
    data = json.loads(rendered)
    assert set(data) == {
        "schema_version",
        "repository_id",
        "snapshot_id",
        "root_id",
        "nodes",
        "edges",
        "evidence",
        "diagnostic_summary",
        "budget",
        "truncated",
        "truncation_reasons",
    }
    assert data["budget"] == {
        "depth": 4,
        "max_nodes": 50,
        "max_edges": 100,
        "max_chars": 20000,
    }
    assert "secret-sentinel" not in rendered
    with pytest.raises(ValueError, match="context depth"):
        ContextBudget(7, 50, 100, 20000)
    with pytest.raises(ValueError, match="root"):
        context_json(replace(package, root_id="missing"))
    with pytest.raises(ValueError, match="ownership"):
        wrong_node = replace(batch.entities[0], snapshot_id="other")
        context_json(replace(package, nodes=(wrong_node, *batch.entities[1:])))


def test_source_scan_config_limits() -> None:
    config = SourceScanConfig(100, 1024)
    assert config.max_file_bytes == 1024
    assert scan_config_digest(config) == scan_config_digest(SourceScanConfig(100, 1024))
    assert scan_config_digest(config) != scan_config_digest(SourceScanConfig(100, 2048))
    with pytest.raises(ValueError, match="positive"):
        SourceScanConfig(0, 1024)


def test_identity_helpers_are_deterministic_and_partitioned() -> None:
    snap = "snap_demo"
    src = source_entity_id("repo", "app/a.py", "Callable", "app.a.f")
    assert src == source_entity_id("repo", "app/a.py", "Callable", "app.a.f")
    assert src != source_entity_id("repo", "app/a.py", "Type", "app.a.f")
    assert src != source_entity_id("other", "app/a.py", "Callable", "app.a.f")

    left = edge_id(snap, EdgeType.CALLS, "a", "b")
    assert left == edge_id(snap, EdgeType.CALLS, "a", "b")
    assert left != edge_id(snap, EdgeType.CALLS, "b", "a")
    assert left != edge_id(snap, EdgeType.CONTAINS, "a", "b")

    ev = evidence_id(snap, "app/a.py", 3, 4, RULE)
    assert ev == evidence_id(snap, "app/a.py", 3, 4, RULE)
    assert ev != evidence_id(snap, "app/a.py", 3, 5, RULE)
    assert ev != evidence_id("other", "app/a.py", 3, 4, RULE)
