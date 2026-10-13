"""Graph fixtures for search / traversal / context integration tests."""

from __future__ import annotations

from rkg.domain import (
    Diagnostic,
    Edge,
    EdgeType,
    Entity,
    EntityType,
    Evidence,
    FactBatch,
    Severity,
    edge_id,
    evidence_id,
    source_entity_id,
)
from rkg.graph import SnapshotPublishMeta, publish_fact_batch
from rkg.storage import Storage

RULE_CALLS = "RKG.python.calls.v1"
RULE_CONTAINS = "RKG.python.contains.v1"
RULE_EXPOSES = "RKG.fastapi.exposes.v1"


def publish_meta() -> SnapshotPublishMeta:
    return SnapshotPublishMeta(
        source_revision=f"manifest:{'a' * 64}",
        manifest_hash="b" * 64,
        scan_config_digest="c" * 64,
        analyzer_version="0.1.0",
        schema_version="TBL-RKG-GRAPH@9",
        adapter_versions={"python": "1.0.0"},
    )


def _callable(
    repository_id: str,
    snapshot_id: str,
    file_path: str,
    name: str,
    qualified_name: str,
    *,
    start: int = 1,
) -> Entity:
    return Entity(
        id=source_entity_id(repository_id, file_path, "Callable", qualified_name),
        repository_id=repository_id,
        snapshot_id=snapshot_id,
        type=EntityType.CALLABLE,
        name=name,
        qualified_name=qualified_name,
        file_path=file_path,
        start_line=start,
        end_line=start + 3,
    )


def cycle_batch(repository_id: str, snapshot_id: str) -> FactBatch:
    """A → B → C → A call cycle plus an endpoint with method/path."""
    file_path = "app/cycle.py"
    a = _callable(repository_id, snapshot_id, file_path, "a", "app.cycle.a", start=1)
    b = _callable(repository_id, snapshot_id, file_path, "b", "app.cycle.b", start=10)
    c = _callable(repository_id, snapshot_id, file_path, "c", "app.cycle.c", start=20)
    # Same display name, different qualified name / type (AC-036).
    twin = Entity(
        id=source_entity_id(repository_id, file_path, "Type", "app.cycle.Helper"),
        repository_id=repository_id,
        snapshot_id=snapshot_id,
        type=EntityType.TYPE,
        name="a",
        qualified_name="app.cycle.Helper",
        file_path=file_path,
        start_line=30,
        end_line=40,
    )
    endpoint = Entity(
        id=source_entity_id(
            repository_id, file_path, "Endpoint", "app.cycle.get_orders"
        ),
        repository_id=repository_id,
        snapshot_id=snapshot_id,
        type=EntityType.ENDPOINT,
        name="get_orders",
        qualified_name="app.cycle.get_orders",
        file_path=file_path,
        start_line=50,
        end_line=55,
        attributes=(("method", "GET"), ("path", "/orders/{id}")),
    )
    other_endpoint = Entity(
        id=source_entity_id(
            repository_id, file_path, "Endpoint", "app.cycle.post_orders"
        ),
        repository_id=repository_id,
        snapshot_id=snapshot_id,
        type=EntityType.ENDPOINT,
        name="post_orders",
        qualified_name="app.cycle.post_orders",
        file_path=file_path,
        start_line=60,
        end_line=65,
        attributes=(("method", "POST"), ("path", "/orders")),
    )
    navigation = Entity(
        id=source_entity_id(
            repository_id, file_path, "Endpoint", "navigation:/orders"
        ),
        repository_id=repository_id,
        snapshot_id=snapshot_id,
        type=EntityType.ENDPOINT,
        name="/orders",
        qualified_name="navigation:/orders",
        file_path="src/app/router.tsx",
        start_line=18,
        end_line=18,
        framework_kind="react-router",
        attributes=(
            ("kind", "navigation"),
            ("path", "/orders"),
            ("route_path", "/orders"),
        ),
    )

    entities = (a, b, c, twin, endpoint, other_endpoint, navigation)
    evidence_items = [
        Evidence(
            evidence_id(snapshot_id, file_path, line, line, RULE_CALLS),
            snapshot_id,
            file_path,
            line,
            line,
            RULE_CALLS,
        )
        for line in (1, 10, 20, 50)
    ]
    evidence_items.append(
        Evidence(
            evidence_id(snapshot_id, file_path, 50, 50, RULE_EXPOSES),
            snapshot_id,
            file_path,
            50,
            50,
            RULE_EXPOSES,
        )
    )

    def call(src: Entity, tgt: Entity, ev: Evidence) -> Edge:
        return Edge(
            id=edge_id(snapshot_id, EdgeType.CALLS, src.id, tgt.id),
            snapshot_id=snapshot_id,
            type=EdgeType.CALLS,
            source_id=src.id,
            target_id=tgt.id,
            rule=RULE_CALLS,
            evidence_ids=(ev.id,),
        )

    edges = [
        call(a, b, evidence_items[0]),
        call(b, c, evidence_items[1]),
        call(c, a, evidence_items[2]),
        Edge(
            id=edge_id(snapshot_id, EdgeType.HANDLED_BY, endpoint.id, a.id),
            snapshot_id=snapshot_id,
            type=EdgeType.HANDLED_BY,
            source_id=endpoint.id,
            target_id=a.id,
            rule=RULE_CALLS,
            evidence_ids=(evidence_items[3].id,),
        ),
        Edge(
            id=edge_id(snapshot_id, EdgeType.EXPOSES, repository_id, endpoint.id),
            snapshot_id=snapshot_id,
            type=EdgeType.EXPOSES,
            source_id=repository_id,
            target_id=endpoint.id,
            rule=RULE_EXPOSES,
            evidence_ids=(evidence_items[4].id,),
        ),
    ]
    diagnostics = (
        Diagnostic(
            id=f"diag_warn_{snapshot_id}",
            job_id=f"job_{snapshot_id}",
            severity=Severity.WARNING,
            code="W001",
            message="sample warning",
            snapshot_id=snapshot_id,
            file_path=file_path,
            line=1,
        ),
    )
    return FactBatch(
        repository_id=repository_id,
        snapshot_id=snapshot_id,
        entities=entities,
        edges=tuple(edges),
        evidence=tuple(evidence_items),
        diagnostics=diagnostics,
    )


def seed_cycle_graph(
    store: Storage,
    *,
    locator: str = "/allowed/cycle",
    snapshot_id: str | None = None,
) -> tuple[str, str, FactBatch]:
    repo = store.create_repository(
        display_name="Cycle",
        source_type="local",
        source_locator=locator,
    )
    snap = snapshot_id or f"snap-cycle-{repo.id[-12:]}"
    batch = cycle_batch(repo.id, snap)
    publish_fact_batch(store, batch, publish_meta())
    return repo.id, batch.snapshot_id, batch


def seed_relation_graph(
    store: Storage,
) -> tuple[str, str, FactBatch, dict[str, Entity]]:
    """Small Q&A fixture covering DB, event, dependency and technology edges."""
    repo = store.create_repository(
        display_name="Relations", source_type="local", source_locator="/allowed/qa"
    )
    sid = "snap-qa-relations"
    specs = (
        ("orders_api", EntityType.ENDPOINT),
        ("create_order", EntityType.CALLABLE),
        ("orders_table", EntityType.DATA_RESOURCE),
        ("order_created", EntityType.MESSAGE_CHANNEL),
        ("fastapi", EntityType.EXTERNAL_DEPENDENCY),
    )
    entities = tuple(
        Entity(
            id=source_entity_id(repo.id, "app/orders.py", kind.value, name),
            repository_id=repo.id,
            snapshot_id=sid,
            type=kind,
            name=name,
            qualified_name=name,
            file_path="app/orders.py",
            start_line=index + 1,
            end_line=index + 1,
        )
        for index, (name, kind) in enumerate(specs)
    )
    by_name = {entity.name: entity for entity in entities}
    relations = (
        ("orders_api", EdgeType.HANDLED_BY, "create_order"),
        ("create_order", EdgeType.WRITES, "orders_table"),
        ("create_order", EdgeType.PUBLISHES, "order_created"),
        (None, EdgeType.DEPENDS_ON, "fastapi"),
    )
    evidence = tuple(
        Evidence(
            id=evidence_id(
                sid, "app/orders.py", index + 1, index + 1, "RKG.python.qa.v1"
            ),
            snapshot_id=sid,
            file_path="app/orders.py",
            start_line=index + 1,
            end_line=index + 1,
            rule="RKG.python.qa.v1",
        )
        for index in range(len(relations))
    )
    edges = tuple(
        Edge(
            id=edge_id(
                sid,
                kind,
                by_name[source].id if source else repo.id,
                by_name[target].id,
            ),
            snapshot_id=sid,
            type=kind,
            source_id=by_name[source].id if source else repo.id,
            target_id=by_name[target].id,
            rule="RKG.python.qa.v1",
            evidence_ids=(evidence[index].id,),
        )
        for index, (source, kind, target) in enumerate(relations)
    )
    batch = FactBatch(repo.id, sid, entities=entities, edges=edges, evidence=evidence)
    publish_fact_batch(store, batch, publish_meta())
    return repo.id, sid, batch, by_name


def seed_ui_route_flow_graph(
    store: Storage,
) -> tuple[str, str, FactBatch, dict[str, Entity]]:
    """Navigation route → page → client → config/external (FE UI→API chain)."""
    repo = store.create_repository(
        display_name="UI routes",
        source_type="local",
        source_locator="/allowed/ui-routes",
    )
    sid = "snap-ui-route-flow"
    route_file = "src/app/router.tsx"
    page_file = "src/pages/OrdersPage.tsx"
    api_file = "src/api/orderApi.ts"
    config_file = "src/config/environment.ts"

    by_name: dict[str, Entity] = {}
    specs: list[tuple[str, EntityType, str, str, tuple[tuple[str, str], ...], str | None]] = [
        (
            "route_orders",
            EntityType.ENDPOINT,
            "/orders",
            "navigation:/orders",
            (
                ("kind", "navigation"),
                ("path", "/orders"),
                ("route_path", "/orders"),
                ("page_handler", "OrdersPage"),
                ("route_signal", "outbound_http"),
            ),
            "react-router",
        ),
        (
            "OrdersPage",
            EntityType.CALLABLE,
            "OrdersPage",
            "src.pages.OrdersPage.OrdersPage",
            (),
            None,
        ),
        (
            "listOrders",
            EntityType.CALLABLE,
            "listOrders",
            "src.api.orderApi.listOrders",
            (),
            None,
        ),
        (
            "VITE_API_BASE_URL",
            EntityType.CONFIGURATION,
            "VITE_API_BASE_URL",
            "config:VITE_API_BASE_URL",
            (),
            None,
        ),
        (
            "inventory_origin",
            EntityType.EXTERNAL_DEPENDENCY,
            "https://inventory.example.test",
            "https://inventory.example.test",
            (),
            None,
        ),
        (
            "http_get_orders",
            EntityType.ENDPOINT,
            "GET /api/orders",
            "api:GET:/api/orders",
            (("method", "GET"), ("path", "/api/orders")),
            "fastapi_route",
        ),
        (
            "get_orders",
            EntityType.CALLABLE,
            "get_orders",
            "app.api.get_orders",
            (),
            None,
        ),
    ]
    path_for = {
        "route_orders": route_file,
        "OrdersPage": page_file,
        "listOrders": api_file,
        "VITE_API_BASE_URL": config_file,
        "inventory_origin": api_file,
        "http_get_orders": "app/api.py",
        "get_orders": "app/api.py",
    }
    entities_list: list[Entity] = []
    for index, (key, kind, name, qn, attrs, framework) in enumerate(specs):
        entity = Entity(
            id=source_entity_id(repo.id, path_for[key], kind.value, qn),
            repository_id=repo.id,
            snapshot_id=sid,
            type=kind,
            name=name,
            qualified_name=qn,
            file_path=path_for[key],
            start_line=index + 1,
            end_line=index + 1,
            framework_kind=framework,
            attributes=attrs,
        )
        by_name[key] = entity
        entities_list.append(entity)

    relations = (
        ("route_orders", EdgeType.HANDLED_BY, "OrdersPage"),
        ("OrdersPage", EdgeType.CALLS, "listOrders"),
        ("listOrders", EdgeType.DEPENDS_ON, "VITE_API_BASE_URL"),
        ("listOrders", EdgeType.DEPENDS_ON, "inventory_origin"),
        ("http_get_orders", EdgeType.HANDLED_BY, "get_orders"),
        ("get_orders", EdgeType.DEPENDS_ON, "inventory_origin"),
    )
    evidence = tuple(
        Evidence(
            id=evidence_id(sid, path_for[src], index + 1, index + 1, "RKG.ui.flow.v1"),
            snapshot_id=sid,
            file_path=path_for[src],
            start_line=index + 1,
            end_line=index + 1,
            rule="RKG.ui.flow.v1",
        )
        for index, (src, _, _) in enumerate(relations)
    )
    edges = tuple(
        Edge(
            id=edge_id(sid, kind, by_name[src].id, by_name[tgt].id),
            snapshot_id=sid,
            type=kind,
            source_id=by_name[src].id,
            target_id=by_name[tgt].id,
            rule="RKG.ui.flow.v1",
            evidence_ids=(evidence[index].id,),
        )
        for index, (src, kind, tgt) in enumerate(relations)
    )
    batch = FactBatch(
        repo.id, sid, entities=tuple(entities_list), edges=edges, evidence=evidence
    )
    publish_fact_batch(store, batch, publish_meta())
    return repo.id, sid, batch, by_name
