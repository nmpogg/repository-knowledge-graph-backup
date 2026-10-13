"""Static HTTP Callable → Endpoint depends_on pass."""

from rkg.domain.ids import source_entity_id
from rkg.domain.models import Entity, EntityType, FactBatch
from rkg.domain.validation import validate_fact_batch
from rkg.jobs.http_depends import RULE, link_static_http_depends_on

REPO = "repo"
SNAP = "snap"
JOB = "job"


def _callable(name: str, requests: str, *, line: int = 4) -> Entity:
    qualified = f"app.{name}"
    return Entity(
        source_entity_id(REPO, "app/client.py", "Callable", qualified),
        REPO,
        SNAP,
        EntityType.CALLABLE,
        name,
        qualified,
        "app/client.py",
        line,
        line + 2,
        "python",
        None,
        (("http_requests", requests),),
    )


def _endpoint(
    name: str,
    method: str,
    path: str,
    *,
    kind: str | None = None,
) -> Entity:
    qualified = f"api.{name}"
    attrs: list[tuple[str, str]] = [("method", method), ("path", path)]
    if kind is not None:
        attrs.append(("kind", kind))
    return Entity(
        source_entity_id(REPO, "app/routes.py", "Endpoint", qualified),
        REPO,
        SNAP,
        EntityType.ENDPOINT,
        name,
        qualified,
        "app/routes.py",
        1,
        2,
        None,
        None,
        tuple(attrs),
    )


def _external() -> Entity:
    qualified = "https://inventory.example.test"
    return Entity(
        source_entity_id(REPO, "app/client.py", "ExternalDependency", qualified),
        REPO,
        SNAP,
        EntityType.EXTERNAL_DEPENDENCY,
        "inventory",
        qualified,
        "app/client.py",
        1,
        1,
        None,
        None,
        (("origin", qualified),),
    )


def _batch(*entities: Entity) -> FactBatch:
    return FactBatch(REPO, SNAP, entities)


def _depends(batch: FactBatch) -> list[tuple[str, str, str]]:
    by_id = {item.id: item for item in batch.entities}
    return [
        (
            by_id[edge.source_id].qualified_name,
            by_id[edge.target_id].qualified_name,
            edge.rule,
        )
        for edge in batch.edges
        if edge.type.value == "depends_on"
    ]


def test_unique_static_pair_links_and_drops_query() -> None:
    batch = link_static_http_depends_on(
        _batch(
            _callable("list_orders", "get /api/orders?status=open"),
            _endpoint("list", "GET", "/api/orders"),
            _external(),
        ),
        job_id=JOB,
    )
    validate_fact_batch(batch)
    assert _depends(batch) == [("app.list_orders", "api.list", RULE)]
    assert "status=open" not in str(batch.edges)
    assert "status=open" not in str(batch.evidence)
    assert "status=open" not in str(batch.diagnostics)
    assert all(edge.target_id != _external().id for edge in batch.edges)


def test_leading_slash_and_navigation_are_normalized() -> None:
    batch = link_static_http_depends_on(
        _batch(
            _callable("list_orders", "GET api/orders"),
            _endpoint("page", "GET", "/api/orders", kind="navigation"),
            _endpoint("list", "GET", "/api/orders"),
        ),
        job_id=JOB,
    )
    validate_fact_batch(batch)
    assert _depends(batch) == [("app.list_orders", "api.list", RULE)]


def test_ambiguous_pair_is_diagnostic_without_edge() -> None:
    batch = link_static_http_depends_on(
        _batch(
            _callable("list_orders", "GET /api/orders"),
            _endpoint("a", "GET", "/api/orders"),
            _endpoint("b", "GET", "/api/orders"),
        ),
        job_id=JOB,
    )
    validate_fact_batch(batch)
    assert _depends(batch) == []
    assert [item.code for item in batch.diagnostics] == ["http_depends_on_ambiguous"]
    assert all("?" not in item.message for item in batch.diagnostics)


def test_dynamic_unmatched_and_method_only_do_not_guess() -> None:
    dynamic = link_static_http_depends_on(
        _batch(
            _callable("by_id", "GET /api/orders/:orderId"),
            _endpoint("by_id", "GET", "/api/orders/:orderId"),
        ),
        job_id=JOB,
    )
    assert _depends(dynamic) == []
    assert [item.code for item in dynamic.diagnostics] == ["http_depends_on_dynamic"]

    silent = link_static_http_depends_on(
        _batch(
            _callable("missing", "GET /api/missing"),
            _callable("method_only", "GET", line=10),
            _callable("absolute", "GET https://inventory.example.test/health", line=20),
            _endpoint("list", "GET", "/api/orders"),
        ),
        job_id=JOB,
    )
    validate_fact_batch(silent)
    assert silent.edges == ()
    assert silent.diagnostics == ()
