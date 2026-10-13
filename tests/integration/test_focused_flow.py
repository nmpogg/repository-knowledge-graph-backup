"""An endpoint flow cannot leak through ownership or shared data resources."""

import pytest
from fastapi.testclient import TestClient

from rkg.api import create_app
from rkg.domain import EntityType
from rkg.domain.models import EdgeType
from rkg.graph import search_entities, traverse_subgraph
from rkg.ingestion import LocalSourcePolicy
from rkg.jobs import IndexCoordinator
from rkg.storage import Storage
from tests.integration.graph_helpers import seed_ui_route_flow_graph


@pytest.fixture
def flow_graph(tmp_path):
    source = tmp_path / "source"
    files = {
        "pkg/__init__.py": "",
        "pkg/models.py": "from sqlalchemy.orm import DeclarativeBase\n"
        "class Base(DeclarativeBase): pass\n"
        "class Item(Base):\n    __tablename__ = 'items'\n"
        "class Other(Base):\n    __tablename__ = 'other'\n",
        "pkg/repos.py": "from sqlalchemy import select\nfrom .models import Item\n"
        "class Repo:\n"
        "    def __init__(self, session):\n        self.session = session\n"
        "    async def read(self):\n"
        "        query = select(Item)\n"
        "        if lock:\n            query = query.with_for_update()\n"
        "        return await self.session.scalar(query.execution_options(flag=True))\n"
        "    def save(self):\n        self.session.add(Item())\n",
        "pkg/services.py": "from .repos import Repo\n"
        "class Service:\n"
        "    def __init__(self, db):\n        self.repo = Repo(db)\n"
        "    async def run(self):\n        return await self.repo.read()\n"
        "    def save(self):\n        self.repo.save()\n"
        "async def invoke(service):\n    return await service.run()\n",
        "pkg/handlers.py": "from fastapi import FastAPI, Depends\n"
        "from .services import Service, invoke\n"
        "from .models import Other\nfrom sqlalchemy import select\n"
        "raise RuntimeError('source must not execute')\n"
        "app = FastAPI()\n"
        "def auth():\n    pass\n"
        "@app.get('/items')\n"
        "async def handler(db=Depends(auth)):\n"
        "    return await invoke(Service(db))\n"
        "@app.post('/items')\n"
        "def writer(db):\n    service = Service(db)\n    service.save()\n"
        "@app.get('/unrelated')\n"
        "async def unrelated(db):\n    return await db.scalar(select(Other))\n",
    }
    for name, text in files.items():
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    with Storage(tmp_path / "graph") as storage:
        repo = storage.create_repository(
            display_name="flow", source_type="local", source_locator=str(source)
        )
        job = IndexCoordinator(storage, LocalSourcePolicy((source,))).run(repo.id)
        assert job.status == "succeeded_with_warnings", job.error_code
        sid = job.report["snapshot_id"]
        endpoints = search_entities(
            storage, repo.id, sid, entity_type=EntityType.ENDPOINT
        )
        root = next(
            e
            for e in endpoints.items
            if dict(e.attributes)["path"] == "/items"
            and dict(e.attributes)["method"] == "GET"
        )
        yield storage, repo.id, sid, root, source


def test_flow_reaches_database_and_ownership_never_expands_siblings(flow_graph):
    storage, repo, sid, root, _ = flow_graph
    graph = traverse_subgraph(storage, repo, sid, root.id, view="flow", depth=6)
    names = {n.qualified_name for n in graph.nodes}
    assert {
        "pkg.handlers.handler",
        "pkg.services.invoke",
        "pkg.services.Service.run",
        "pkg.repos.Repo.read",
        "sqlalchemy::items",
    } <= names
    assert not any(
        n.type in (EntityType.SOURCE_UNIT, EntityType.DIRECTORY) for n in graph.nodes
    )
    assert "pkg.handlers.auth" not in names
    assert "pkg.handlers.unrelated" not in names
    assert "sqlalchemy::other" not in names
    assert "pkg.handlers.writer" not in names
    assert not any(
        e.type.value in {"contains", "imports", "depends_on"} for e in graph.edges
    )

    overlay = traverse_subgraph(
        storage, repo, sid, root.id, view="flow", depth=6, include_structure=True
    )
    assert names <= {n.qualified_name for n in overlay.nodes}
    assert any(n.type == EntityType.DIRECTORY for n in overlay.nodes)
    assert "pkg.handlers.unrelated" not in {n.qualified_name for n in overlay.nodes}
    assert "sqlalchemy::other" not in {n.qualified_name for n in overlay.nodes}
    assert not any(e.type.value == "imports" for e in overlay.edges)


def test_dependencies_depth_budgets_and_reverse_resource_flow(flow_graph):
    storage, repo, sid, root, _ = flow_graph
    deps = traverse_subgraph(
        storage, repo, sid, root.id, view="flow", depth=6, include_dependencies=True
    )
    assert "pkg.handlers.auth" in {n.qualified_name for n in deps.nodes}
    one = traverse_subgraph(
        storage,
        repo,
        sid,
        root.id,
        view="flow",
        depth=1,
        include_structure=True,
        max_nodes=20,
    )
    assert "pkg.services.invoke" not in {n.qualified_name for n in one.nodes}
    assert "depth_limit" in one.truncation_reasons
    limited = traverse_subgraph(
        storage,
        repo,
        sid,
        root.id,
        view="flow",
        depth=6,
        include_structure=True,
        max_nodes=3,
        max_edges=2,
    )
    assert len(limited.nodes) <= 3 and len(limited.edges) <= 2
    assert limited.truncated
    table = search_entities(
        storage, repo, sid, entity_type=EntityType.DATA_RESOURCE, q="items"
    ).items[0]
    upstream = traverse_subgraph(
        storage, repo, sid, table.id, view="flow", depth=6, max_nodes=100, max_edges=200
    )
    names = {n.qualified_name for n in upstream.nodes}
    assert "pkg.handlers.handler" in names and "pkg.handlers.writer" in names
    assert "pkg.handlers.unrelated" not in names and "sqlalchemy::other" not in names


def test_api_flow_and_export_share_profile_and_legacy_defaults(flow_graph):
    storage, repo, sid, root, source = flow_graph
    app = create_app(storage, LocalSourcePolicy((source,)), session_token="test")
    with TestClient(app, base_url="http://127.0.0.1") as client:
        params = {"snapshot_id": sid, "root_id": root.id, "depth": 6, "view": "flow"}
        graph = client.get("/api/v1/subgraph", params=params)
        assert graph.status_code == 200
        assert graph.json()["view"] == "flow"
        assert "sqlalchemy::items" in {
            n["qualified_name"] for n in graph.json()["nodes"]
        }
        assert not any(e["type"] == "contains" for e in graph.json()["edges"])
        exported = client.post(
            "/api/v1/context", json=params, headers={"X-RKG-Session": "test"}
        )
        assert exported.status_code == 200
        assert {n["id"] for n in exported.json()["nodes"]} == {
            n["id"] for n in graph.json()["nodes"]
        }
        invalid = client.get("/api/v1/subgraph", params=params | {"view": "invalid"})
        assert invalid.status_code == 422


def test_generic_repository_model_stays_at_concrete_caller(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "app.py").write_text(
        "from fastapi import FastAPI\n"
        "from sqlalchemy import select\n"
        "from sqlalchemy.orm import DeclarativeBase\n"
        "class Base(DeclarativeBase): pass\n"
        "class A(Base):\n    __tablename__ = 'a'\n"
        "class B(Base):\n    __tablename__ = 'b'\n"
        "class Repo[Model]:\n"
        "    def __init__(self, session, model: type[Model]):\n"
        "        self.session, self.model = session, model\n"
        "    async def get(self):\n"
        "        return await self.session.scalar(select(self.model))\n"
        "    async def update(self, entity: Model):\n"
        "        setattr(entity, 'field', value)\n        await self.session.flush()\n"
        "class ARepo(Repo[A]):\n"
        "    def __init__(self, db):\n        super().__init__(db, A)\n"
        "class BRepo(Repo[B]):\n"
        "    def __init__(self, db):\n        super().__init__(db, B)\n"
        "class Invalid(Repo[A]):\n"
        "    def __init__(self, db):\n        super().__init__(db, B)\n"
        "app = FastAPI()\n"
        "@app.get('/a')\nasync def first(db):\n    return await ARepo(db).get()\n"
        "@app.get('/b')\nasync def second(db):\n    return await BRepo(db).get()\n"
        "@app.get('/direct')\nasync def direct(db):\n"
        "    repository = Repo(db, A)\n    return await repository.get()\n"
        "@app.post('/a')\nasync def writer(db, entity):\n"
        "    await ARepo(db).update(entity)\n"
        "@app.get('/invalid')\nasync def invalid(db):\n"
        "    return await Invalid(db).get()\n",
        encoding="utf-8",
    )
    with Storage(tmp_path / "graph") as storage:
        repo = storage.create_repository(
            display_name="generic", source_type="local", source_locator=str(source)
        )
        job = IndexCoordinator(storage, LocalSourcePolicy((source,))).run(repo.id)
        assert job.status == "succeeded_with_warnings", job.error_code
        sid = job.report["snapshot_id"]
        endpoints = search_entities(
            storage, repo.id, sid, entity_type=EntityType.ENDPOINT
        )
        for path, method, expected in [
            ("/a", "GET", "a"),
            ("/b", "GET", "b"),
            ("/a", "POST", "a"),
            ("/direct", "GET", "a"),
            ("/invalid", "GET", None),
        ]:
            root = next(
                e
                for e in endpoints.items
                if dict(e.attributes)["path"] == path
                and dict(e.attributes)["method"] == method
            )
            graph = traverse_subgraph(
                storage, repo.id, sid, root.id, view="flow", depth=6
            )
            tables = {n.name for n in graph.nodes if n.type == EntityType.DATA_RESOURCE}
            assert tables == ({expected} if expected else set())
        base = search_entities(
            storage, repo.id, sid, entity_type=EntityType.CALLABLE, q="app.Repo.get"
        ).items[0]
        generic = traverse_subgraph(
            storage, repo.id, sid, base.id, view="flow", depth=6
        )
        assert not any(n.type == EntityType.DATA_RESOURCE for n in generic.nodes)


def test_navigation_flow_includes_depends_on_http_endpoint_does_not(tmp_path):
    """UI route flow opens config/external; HTTP Endpoint default stays without depends_on."""
    with Storage(tmp_path / "ui-flow") as storage:
        repo, sid, _batch, by_name = seed_ui_route_flow_graph(storage)
        nav = by_name["route_orders"]
        http = by_name["http_get_orders"]

        nav_flow = traverse_subgraph(
            storage, repo, sid, nav.id, view="flow", depth=6
        )
        nav_names = {n.qualified_name for n in nav_flow.nodes}
        assert {
            "navigation:/orders",
            "src.pages.OrdersPage.OrdersPage",
            "src.api.orderApi.listOrders",
            "config:VITE_API_BASE_URL",
            "https://inventory.example.test",
        } <= nav_names
        assert any(e.type == EdgeType.DEPENDS_ON for e in nav_flow.edges)

        http_flow = traverse_subgraph(
            storage, repo, sid, http.id, view="flow", depth=6
        )
        http_names = {n.qualified_name for n in http_flow.nodes}
        assert "api:GET:/api/orders" in http_names
        assert "app.api.get_orders" in http_names
        assert "https://inventory.example.test" not in http_names
        assert not any(e.type.value == "depends_on" for e in http_flow.edges)
