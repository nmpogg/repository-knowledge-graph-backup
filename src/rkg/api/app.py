"""FastAPI transport for API-RKG-CORE-v1."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from contextlib import asynccontextmanager
from time import perf_counter
from typing import Any

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ConfigDict
from starlette.middleware.cors import CORSMiddleware

from rkg.api.catalog import (
    entity_evidence,
    list_dependencies,
    list_diagnostics,
    repository_for_snapshot,
    snapshot_capabilities,
)
from rkg.api.conversations import mount_conversations
from rkg.api.errors import error_response
from rkg.api.guard import mutation_allowed
from rkg.api.jobs import mirrored, submit_index
from rkg.api.serialize import (
    entity_json,
    job_headers,
    job_json,
    page_json,
    repository_json,
    snapshot_json,
)
from rkg.conversations import delete_conversation
from rkg.domain.context import context_dict
from rkg.domain.models import EntityType
from rkg.graph import build_context, get_entity, search_entities, traverse_subgraph
from rkg.graph.access import require_readable_snapshot
from rkg.ingestion import LocalSourcePolicy, SourceError, resolve_local_source
from rkg.jobs import IndexJobBusyError, call_when_idle, scan_config, writer_busy
from rkg.llm import StructuredProvider
from rkg.storage.connection import Storage
from rkg.storage.errors import RepositorySourceImmutableError, StorageError
from rkg.terminal_logging import log_context, log_event

_IMMUTABLE = frozenset({"path", "source_type", "source_locator", "source_identity"})


class RepositoryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    display_name: str
    source_type: str = "local"
    path: str
    source_root: str | None = None
    app_module: str | None = None
    app_symbol: str | None = None
    scan_defaults: dict[str, Any] | None = None


class IndexBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    app_module: str | None = None
    app_symbol: str | None = None
    app_candidate_id: str | None = None
    scan_defaults: dict[str, Any] | None = None


class ContextBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    snapshot_id: str
    root_id: str
    repository_id: str | None = None
    direction: str = "outgoing"
    edge_types: list[str] | None = None
    depth: int = 4
    max_nodes: int = 50
    max_edges: int = 100
    max_chars: int = 20000
    view: str = "neighborhood"
    include_structure: bool = False
    include_dependencies: bool = False


def create_app(
    storage: Storage,
    policy: LocalSourcePolicy,
    *,
    session_token: str,
    provider: StructuredProvider | None = None,
) -> FastAPI:
    """Build the loopback API around an already-open storage handle."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        for thread in app.state.workers:
            thread.join(timeout=5)

    app = FastAPI(title="RKG", version="v1", lifespan=lifespan)
    app.state.storage = storage
    app.state.policy = policy
    app.state.session_token = session_token
    app.state.workers = []

    @app.middleware("http")
    async def session_gate(request: Request, call_next: Callable):
        mutating = request.method in {"POST", "PATCH", "DELETE"}
        if mutating and request.url.path.startswith("/api/"):
            if not mutation_allowed(request.headers, request.app.state.session_token):
                return error_response("unauthorized")
        return await call_next(request)

    @app.exception_handler(StorageError)
    async def on_storage(_: Request, exc: StorageError) -> JSONResponse:
        return error_response(exc.code, exc)

    @app.exception_handler(SourceError)
    async def on_source(_: Request, exc: SourceError) -> JSONResponse:
        return error_response(exc.code, exc)

    @app.exception_handler(IndexJobBusyError)
    async def on_busy(_: Request, exc: IndexJobBusyError) -> JSONResponse:
        return error_response(exc.code, exc)

    @app.exception_handler(ValueError)
    async def on_value(_: Request, exc: ValueError) -> JSONResponse:
        code = str(exc) if str(exc) == "invalid_request" else "invalid_request"
        return error_response(code)

    @app.exception_handler(RequestValidationError)
    async def on_validation(_: Request, __: RequestValidationError) -> JSONResponse:
        return error_response("invalid_request")

    def idle[T](operation: Callable[[], T]) -> T:
        return call_when_idle(operation)

    def bounds(offset: int, limit: int) -> tuple[int, int]:
        if offset < 0 or not 1 <= limit <= 100:
            raise ValueError("invalid_request")
        return offset, limit

    @app.post("/api/v1/repositories", status_code=201)
    def create_repository(body: RepositoryCreate) -> dict[str, Any]:
        if body.source_type != "local":
            raise SourceError("source_type_unsupported")
        if body.scan_defaults is not None:
            scan_config(body.scan_defaults)

        def write() -> dict[str, Any]:
            source = resolve_local_source(
                "registration",
                body.path,
                policy,
                source_root=body.source_root,
            )
            item = storage.create_repository(
                display_name=body.display_name,
                source_type="local",
                source_locator=str(source.canonical_root),
                source_root=body.source_root,
                app_module=body.app_module,
                app_symbol=body.app_symbol,
                scan_defaults=body.scan_defaults,
            )
            return repository_json(item)

        return idle(write)

    @app.get("/api/v1/repositories")
    def list_repositories(
        q: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> dict[str, Any]:
        offset, limit = bounds(offset, limit)

        def read() -> dict[str, Any]:
            page = storage.list_repositories(offset=offset, limit=limit, q=q)
            return page_json(
                [repository_json(item) for item in page.items],
                offset=page.offset,
                limit=page.limit,
                total=page.total,
            )

        return idle(read)

    @app.get("/api/v1/repositories/{repository_id}")
    def get_repository(repository_id: str) -> dict[str, Any]:
        return idle(lambda: repository_json(storage.get_repository(repository_id)))

    @app.patch("/api/v1/repositories/{repository_id}")
    async def update_repository(repository_id: str, request: Request) -> dict[str, Any]:
        payload = await request.json()
        if not isinstance(payload, dict):
            raise ValueError("invalid_request")
        if _IMMUTABLE & payload.keys():
            raise RepositorySourceImmutableError("source identity is immutable")
        revision = payload.get("expected_revision")
        if type(revision) is not int:
            raise ValueError("invalid_request")
        if revision < 1:
            raise ValueError("invalid_request")

        def write() -> dict[str, Any]:
            current = storage.get_repository(repository_id)
            fields: dict[str, Any] = {}
            if "display_name" in payload:
                name = payload["display_name"]
                if not isinstance(name, str) or not name:
                    raise ValueError("invalid_request")
                fields["display_name"] = name
            if "source_root" in payload:
                resolve_local_source(
                    current.id,
                    current.source_locator,
                    policy,
                    source_root=payload["source_root"],
                )
                fields["source_root"] = payload["source_root"]
            for name in ("app_module", "app_symbol"):
                if name in payload:
                    fields[name] = payload[name]
            if "scan_defaults" in payload:
                if payload["scan_defaults"] is not None:
                    scan_config(payload["scan_defaults"])
                fields["scan_defaults"] = payload["scan_defaults"]
            updated = storage.update_repository(
                repository_id,
                expected_revision=revision,
                **fields,
            )
            return repository_json(updated)

        return idle(write)

    @app.delete("/api/v1/repositories/{repository_id}", status_code=204)
    def delete_repository(repository_id: str) -> Response:
        idle(lambda: storage.delete_repository(repository_id))
        return Response(status_code=204)

    @app.post("/api/v1/repositories/{repository_id}/index-jobs", status_code=202)
    def create_index_job(
        repository_id: str, body: IndexBody | None = None
    ) -> JSONResponse:
        module = body.app_module if body else None
        symbol = body.app_symbol if body else None
        if body and body.app_candidate_id:
            if ":" not in body.app_candidate_id:
                raise ValueError("invalid_request")
            module, symbol = body.app_candidate_id.rsplit(":", 1)
        defaults = body.scan_defaults if body else None
        job = submit_index(
            storage,
            policy,
            repository_id,
            app_module=module,
            app_symbol=symbol,
            scan_defaults=defaults,
            workers=app.state.workers,
        )
        return JSONResponse(
            status_code=202, content=job_json(job), headers=job_headers(job)
        )

    @app.get("/api/v1/index-jobs/{job_id}")
    def get_index_job(job_id: str) -> JSONResponse:
        if writer_busy():
            current = mirrored(job_id)
            if current is not None:
                return JSONResponse(
                    content=job_json(current), headers=job_headers(current)
                )
        item = idle(lambda: storage.get_job(job_id))
        return JSONResponse(content=job_json(item), headers=job_headers(item))

    @app.get("/api/v1/repositories/{repository_id}/snapshots")
    def list_snapshots(
        repository_id: str, offset: int = 0, limit: int = 20
    ) -> dict[str, Any]:
        offset, limit = bounds(offset, limit)

        def read() -> dict[str, Any]:
            page = storage.list_snapshots(repository_id, offset=offset, limit=limit)
            return page_json(
                [snapshot_json(storage, item) for item in page.items],
                offset=page.offset,
                limit=page.limit,
                total=page.total,
            )

        return idle(read)

    @app.get("/api/v1/repositories/{repository_id}/snapshots/{snapshot_id}")
    def get_snapshot(repository_id: str, snapshot_id: str) -> dict[str, Any]:
        return idle(
            lambda: snapshot_json(
                storage, storage.get_snapshot(repository_id, snapshot_id)
            )
        )

    @app.post("/api/v1/repositories/{repository_id}/snapshots/{snapshot_id}/activate")
    def activate_snapshot(repository_id: str, snapshot_id: str) -> dict[str, Any]:
        return idle(
            lambda: repository_json(
                storage.activate_snapshot(repository_id, snapshot_id)
            )
        )

    @app.delete(
        "/api/v1/repositories/{repository_id}/snapshots/{snapshot_id}",
        status_code=204,
    )
    def delete_snapshot(repository_id: str, snapshot_id: str) -> Response:
        idle(lambda: storage.delete_snapshot(repository_id, snapshot_id))
        return Response(status_code=204)

    def scope(
        snapshot_id: str | None, repository_id: str | None
    ) -> tuple[str, str | None]:
        if snapshot_id and repository_id:
            storage.get_snapshot(repository_id, snapshot_id)
            return repository_id, snapshot_id
        if snapshot_id:
            return repository_for_snapshot(storage, snapshot_id), snapshot_id
        if repository_id:
            return repository_id, None
        raise ValueError("invalid_request")

    @app.get("/api/v1/entities")
    def search(
        snapshot_id: str | None = None,
        repository_id: str | None = None,
        q: str | None = None,
        type: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> dict[str, Any]:
        offset, limit = bounds(offset, limit)
        entity_type = _entity_type(type)

        def read() -> dict[str, Any]:
            repo_id, snap_id = scope(snapshot_id, repository_id)
            page = search_entities(
                storage,
                repo_id,
                snap_id,
                q=q,
                entity_type=entity_type,
                offset=offset,
                limit=limit,
            )
            return page_json(
                [entity_json(item) for item in page.items],
                offset=page.offset,
                limit=page.limit,
                total=page.total,
            )

        return idle(read)

    @app.get("/api/v1/entities/{entity_id}")
    def entity_detail(
        entity_id: str,
        snapshot_id: str | None = None,
        repository_id: str | None = None,
    ) -> dict[str, Any]:
        def read() -> dict[str, Any]:
            repo_id, snap_id = scope(snapshot_id, repository_id)
            item = get_entity(storage, repo_id, snap_id, entity_id)
            evidence = entity_evidence(
                storage,
                item.snapshot_id,
                item.file_path,
                directory_id=item.id if item.type == EntityType.DIRECTORY else None,
            )
            return entity_json(item, evidence)

        return idle(read)

    @app.get("/api/v1/subgraph")
    def subgraph(
        root_id: str,
        snapshot_id: str | None = None,
        repository_id: str | None = None,
        direction: str = "both",
        edge_types: list[str] | None = Query(default=None),
        depth: int = 4,
        max_nodes: int = 50,
        max_edges: int = 100,
        view: str = "neighborhood",
        include_structure: bool = False,
        include_dependencies: bool = False,
    ) -> dict[str, Any]:
        def read() -> dict[str, Any]:
            repo_id, snap_id = scope(snapshot_id, repository_id)
            graph = traverse_subgraph(
                storage,
                repo_id,
                snap_id,
                root_id,
                direction=direction,  # type: ignore[arg-type]
                edge_types=edge_types,
                depth=depth,
                max_nodes=max_nodes,
                max_edges=max_edges,
                view=view,  # type: ignore[arg-type]
                include_structure=include_structure,
                include_dependencies=include_dependencies,
            )
            return {
                "repository_id": graph.repository_id,
                "snapshot_id": graph.snapshot_id,
                "root_id": graph.root_id,
                "view": view,
                "nodes": [entity_json(item) for item in graph.nodes],
                "edges": [
                    {
                        "id": edge.id,
                        "type": edge.type.value,
                        "source_id": edge.source_id,
                        "target_id": edge.target_id,
                        "rule": edge.rule,
                        "evidence_ids": list(edge.evidence_ids),
                    }
                    for edge in graph.edges
                ],
                "truncated": graph.truncated,
                "truncation_reasons": list(graph.truncation_reasons),
                "limits": {
                    "depth": graph.depth,
                    "max_nodes": graph.max_nodes,
                    "max_edges": graph.max_edges,
                },
            }

        return idle(read)

    @app.get("/api/v1/technologies")
    def technologies(
        snapshot_id: str,
        repository_id: str | None = None,
    ) -> list[dict[str, Any]]:
        def read() -> list[dict[str, Any]]:
            repo_id, snap_id = scope(snapshot_id, repository_id)
            require_readable_snapshot(storage, repo_id, snap_id)
            return snapshot_capabilities(storage, repo_id, snap_id or snapshot_id)

        return idle(read)

    @app.get("/api/v1/dependencies")
    def dependencies(
        snapshot_id: str,
        repository_id: str | None = None,
        subtype: str | None = None,
        q: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> dict[str, Any]:
        offset, limit = bounds(offset, limit)

        def read() -> dict[str, Any]:
            repo_id, snap_id = scope(snapshot_id, repository_id)
            require_readable_snapshot(storage, repo_id, snap_id)
            items, total = list_dependencies(
                storage,
                snap_id or snapshot_id,
                subtype=subtype,
                q=q,
                offset=offset,
                limit=limit,
            )
            return page_json(items, offset=offset, limit=limit, total=total)

        return idle(read)

    @app.get("/api/v1/diagnostics")
    def diagnostics(
        snapshot_id: str,
        repository_id: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> dict[str, Any]:
        offset, limit = bounds(offset, limit)

        def read() -> dict[str, Any]:
            repo_id, snap_id = scope(snapshot_id, repository_id)
            require_readable_snapshot(storage, repo_id, snap_id)
            items, total = list_diagnostics(
                storage, snap_id or snapshot_id, offset=offset, limit=limit
            )
            return page_json(items, offset=offset, limit=limit, total=total)

        return idle(read)

    @app.post("/api/v1/context")
    def context(body: ContextBody) -> dict[str, Any]:
        def read() -> dict[str, Any]:
            repo_id, snap_id = scope(body.snapshot_id, body.repository_id)
            package = build_context(
                storage,
                repo_id,
                snap_id,
                body.root_id,
                direction=body.direction,  # type: ignore[arg-type]
                edge_types=body.edge_types,
                depth=body.depth,
                max_nodes=body.max_nodes,
                max_edges=body.max_edges,
                max_chars=body.max_chars,
                view=body.view,
                include_structure=body.include_structure,
                include_dependencies=body.include_dependencies,
            )
            return context_dict(package)

        return idle(read)

    @app.delete("/api/v1/conversations/{conversation_id}", status_code=204)
    def remove_conversation(conversation_id: str) -> Response:
        idle(lambda: delete_conversation(storage, conversation_id))
        return Response(status_code=204)

    mount_conversations(app, storage, idle, bounds, provider)

    # Browser UI (Vite) is a different loopback port. Reflect only loopback origins.
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$",
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Accept", "Content-Type", "X-RKG-Session"],
        allow_credentials=False,
    )

    @app.middleware("http")
    async def request_log(request: Request, call_next: Callable):
        with log_context(request_id=uuid.uuid4().hex):
            started = perf_counter()
            status = 500
            try:
                response = await call_next(request)
                status = response.status_code
                return response
            finally:
                log_event(
                    "http_request",
                    method=request.method,
                    route=getattr(request.scope.get("route"), "path", "unmatched"),
                    status=status,
                    elapsed_ms=round((perf_counter() - started) * 1000, 2),
                )

    return app


def _entity_type(value: str | None) -> EntityType | None:
    if value is None or value == "":
        return None
    try:
        return EntityType(value)
    except ValueError:
        raise ValueError("invalid_request") from None
