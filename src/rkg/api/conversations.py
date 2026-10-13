"""Conversation HTTP routes for API-RKG-CORE-v1 (TASK-RKG-021).

Create, list, history and grounded turns. Delete stays on the app so a pending
turn still returns ``409 conversation_busy``. Provider failures keep the
committed focus and are mapped to 502/503/504. Request bodies are not logged.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal

from fastapi import FastAPI, Request
from fastapi import Path as PathParameter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, StrictInt

from rkg.api.errors import error_response
from rkg.api.serialize import entity_json, page_json
from rkg.conversations import (
    create_conversation,
    list_conversations,
    list_turns,
    read_conversation,
    submit_grounded_turn,
)
from rkg.conversations.citations import exact_citation
from rkg.graph.errors import SnapshotUnavailableError
from rkg.graph.search import get_entities
from rkg.llm import StructuredProvider, configured_provider
from rkg.storage.connection import Storage
from rkg.storage.errors import NotFoundError
from rkg.storage.records import ConversationRecord, TurnRecord

CONVERSATION_SCHEMA_VERSION = "rkg.conversation/1"


class ConversationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    repository_id: str
    snapshot_id: str | None = None
    title: str = ""


class TurnCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str
    client_request_id: str
    expected_revision: StrictInt
    root_id: str | None = None
    ui_locale: Literal["vi", "en"] | None = None


def conversation_json(item: ConversationRecord) -> dict[str, Any]:
    state = item.state or {}
    focus = state.get("focus_entity_id")
    return {
        "schema_version": CONVERSATION_SCHEMA_VERSION,
        "conversation_id": item.id,
        "repository_id": item.repository_id,
        "snapshot_id": item.snapshot_id,
        "title": item.title,
        "revision": item.revision,
        "focus_entity_id": focus if isinstance(focus, str) and focus else None,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    }


def turn_json(item: TurnRecord) -> dict[str, Any]:
    return {
        "schema_version": CONVERSATION_SCHEMA_VERSION,
        "turn_id": item.id,
        "conversation_id": item.conversation_id,
        "sequence": item.sequence,
        "status": item.status,
        "question": item.question,
        "resolved_question": item.resolved_question,
        "answer": item.answer,
        "claims": list(item.claims or []),
        "citations": list(item.citations or []),
        "context_turn_ids": list(item.context_turn_ids),
        "usage": item.usage,
        "error_code": item.error_code,
        "response_metadata": item.response_metadata,
    }


def candidate_entities(
    storage: Storage, conversation: ConversationRecord
) -> list[dict[str, Any]]:
    state = conversation.state or {}
    raw = state.get("pending_candidate_ids") or []
    if not isinstance(raw, list):
        return []
    if not raw:
        return []
    if len(raw) > 20 or not all(isinstance(i, str) and i for i in raw):
        raise NotFoundError("candidate unavailable")
    # One batch: preserve all ordinal positions, or fail without shifting them.
    return [
        entity_json(e)
        for e in get_entities(
            storage, conversation.repository_id, conversation.snapshot_id, tuple(raw)
        )
    ]


def mount_conversations(
    app: FastAPI,
    storage: Storage,
    idle: Callable[[Callable[[], Any]], Any],
    bounds: Callable[[int, int], tuple[int, int]],
    provider: StructuredProvider | None,
) -> None:
    """Register create, list, history and turn routes. Delete is already mounted."""
    app.state.provider = provider if provider is not None else configured_provider()

    @app.get("/api/v1/conversations/capabilities")
    def capabilities(request: Request) -> dict[str, Any]:
        return {
            "schema_version": "rkg.conversation-capabilities/1",
            "features": [
                "ui_locale",
                "response_metadata_v1",
                "exact_citation_lookup",
                "history_unavailable",
            ],
            "provider_enabled": getattr(request.app.state.provider, "enabled", True)
            is not False,
        }

    @app.get(
        "/api/v1/conversations/{conversation_id}/turns/{turn_id}/citations/{citation_index}"
    )
    def citation(
        conversation_id: str, turn_id: str, citation_index: int = PathParameter(ge=0)
    ) -> dict[str, Any]:
        return idle(
            lambda: exact_citation(storage, conversation_id, turn_id, citation_index)
        )

    @app.post("/api/v1/conversations", status_code=201)
    def create(body: ConversationCreate) -> dict[str, Any]:
        def write() -> dict[str, Any]:
            created = create_conversation(
                storage,
                repository_id=body.repository_id,
                snapshot_id=body.snapshot_id,
                title=body.title,
            )
            return conversation_json(created)

        return idle(write)

    @app.get("/api/v1/conversations")
    def listing(
        repository_id: str | None = None,
        snapshot_id: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> dict[str, Any]:
        offset, limit = bounds(offset, limit)

        def read() -> dict[str, Any]:
            page = list_conversations(
                storage,
                repository_id=repository_id or None,
                snapshot_id=snapshot_id or None,
                offset=offset,
                limit=limit,
            )
            return page_json(
                [conversation_json(item) for item in page.items],
                offset=page.offset,
                limit=page.limit,
                total=page.total,
            )

        return idle(read)

    @app.get("/api/v1/conversations/{conversation_id}/turns")
    def turns(
        conversation_id: str,
        offset: int = 0,
        limit: int = 20,
        include_unavailable: bool = False,
    ) -> dict[str, Any]:
        offset, limit = bounds(offset, limit)

        def read() -> dict[str, Any]:
            available = True
            conversation = storage.get_conversation(conversation_id)
            storage.get_repository(conversation.repository_id)
            try:
                conversation = read_conversation(storage, conversation_id).conversation
            except SnapshotUnavailableError:
                if not include_unavailable:
                    raise
                available = False
            ordered = list_turns(storage, conversation_id)
            window = ordered[offset : offset + limit]
            payload = page_json(
                [turn_json(item) for item in window],
                offset=offset,
                limit=limit,
                total=len(ordered),
            )
            payload["conversation"] = conversation_json(conversation)
            payload["candidate_entities"] = (
                candidate_entities(storage, conversation) if available else []
            )
            payload["snapshot_available"] = available
            return payload

        return idle(read)

    @app.post("/api/v1/conversations/{conversation_id}/turns")
    def submit(
        conversation_id: str, body: TurnCreate, request: Request
    ) -> JSONResponse:
        def write() -> JSONResponse:
            grounded = submit_grounded_turn(
                storage,
                conversation_id,
                question=body.question,
                client_request_id=body.client_request_id,
                expected_revision=body.expected_revision,
                root_id=body.root_id,
                ui_locale=body.ui_locale,
                provider=request.app.state.provider,
            )
            turn = grounded.submission.turn
            conversation = grounded.submission.conversation
            if turn.status == "failed":
                return error_response(turn.error_code or "llm_provider_error")
            payload = turn_json(turn)
            metadata = turn.response_metadata or {}
            payload.update(
                {
                    "revision": conversation.revision,
                    "repository_id": conversation.repository_id,
                    "snapshot_id": conversation.snapshot_id,
                    "candidate_entities": candidate_entities(storage, conversation),
                    "limitations": list(metadata.get("limitations") or []),
                    "retrieval_truncated": metadata.get("retrieval_truncated") is True,
                    "history_truncated": metadata.get("history_truncated") is True,
                }
            )
            return JSONResponse(status_code=200, content=payload)

        return idle(write)
