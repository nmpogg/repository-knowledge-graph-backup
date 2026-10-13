"""Deterministic entity search within a snapshot (AC-RKG-036 / AC-RKG-060)."""

from __future__ import annotations

from rkg.domain.models import Entity, EntityType
from rkg.graph.access import load_entities, load_entity, require_readable_snapshot
from rkg.storage.connection import Storage
from rkg.storage.records import Page


def _endpoint_search_labels(entity: Entity) -> tuple[str, ...]:
    """Labels clients may type when searching endpoints (HTTP or navigation)."""
    if entity.type != EntityType.ENDPOINT:
        return ()
    attrs = dict(entity.attributes)
    labels: list[str] = []
    method = attrs.get("method")
    path = attrs.get("path") or attrs.get("route_path")
    if isinstance(method, str) and isinstance(path, str) and method and path:
        labels.append(f"{method} {path}")
    kind = attrs.get("kind")
    if kind == "navigation" and isinstance(path, str) and path:
        labels.append(path)
        labels.append(f"navigation:{path}")
    elif (
        entity.framework_kind == "react-router"
        and isinstance(path, str)
        and path
        and not method
    ):
        labels.append(path)
        labels.append(f"navigation:{path}")
    return tuple(labels)


def entity_matches_query(entity: Entity, q: str) -> bool:
    """Case-insensitive substring on name, qualified_name, and endpoint labels."""
    needle = q.casefold()
    if needle in entity.name.casefold():
        return True
    if needle in entity.qualified_name.casefold():
        return True
    return any(needle in label.casefold() for label in _endpoint_search_labels(entity))

def search_entities(
    storage: Storage,
    repository_id: str,
    snapshot_id: str | None,
    *,
    q: str | None = None,
    entity_type: str | EntityType | None = None,
    offset: int = 0,
    limit: int = 20,
) -> Page:
    """Search entities in one snapshot; order type → qualified_name → id."""
    if offset < 0 or limit < 1:
        raise ValueError("offset/limit out of range")
    limit = min(limit, 100)

    snap = require_readable_snapshot(storage, repository_id, snapshot_id)
    with storage.pin_reader(repository_id, snap.id):
        entities = load_entities(storage, repository_id, snap.id)
        type_filter: str | None = None
        if entity_type is not None:
            type_filter = (
                entity_type.value
                if isinstance(entity_type, EntityType)
                else str(entity_type)
            )
        matched = [
            e
            for e in entities
            if (type_filter is None or e.type.value == type_filter)
            and (q is None or q == "" or entity_matches_query(e, q))
        ]
        # load_entities already orders; preserve after filter.
        total = len(matched)
        page_items = matched[offset : offset + limit]
        return Page(
            items=tuple(page_items),
            offset=offset,
            limit=limit,
            total=total,
        )


def get_entity(
    storage: Storage,
    repository_id: str,
    snapshot_id: str | None,
    entity_id: str,
) -> Entity:
    snap = require_readable_snapshot(storage, repository_id, snapshot_id)
    with storage.pin_reader(repository_id, snap.id):
        return load_entity(storage, repository_id, snap.id, entity_id)


def lookup_entities(
    storage: Storage,
    repository_id: str,
    snapshot_id: str,
    *,
    query: str = "",
    entity_type: str = "any",
    method: str | None = None,
    path: str | None = None,
) -> Page:
    """Exact predicates precede paging; name collisions and overflow stay visible."""
    snap = require_readable_snapshot(storage, repository_id, snapshot_id)
    with storage.pin_reader(repository_id, snap.id):
        entities = load_entities(storage, repository_id, snap.id)
        typed = [
            e for e in entities if entity_type == "any" or e.type.value == entity_type
        ]
        if path is not None:
            matched = [
                e
                for e in typed
                if e.type.value == "Endpoint"
                and dict(e.attributes).get("path") == path.strip()
                and (
                    method is None
                    or str(dict(e.attributes).get("method", "")).upper()
                    == method.upper()
                )
            ]
        else:
            exact = [
                e
                for e in typed
                if query.casefold()
                in (
                    {e.id.casefold(), e.qualified_name.casefold()}
                    | entity_short_names(e)
                )
            ]
            matched = exact or [e for e in typed if entity_matches_query(e, query)]
        return Page(items=tuple(matched[:20]), offset=0, limit=20, total=len(matched))


def get_entities(
    storage: Storage, repository_id: str, snapshot_id: str, ids: tuple[str, ...]
) -> tuple[Entity, ...]:
    """One batch read preserves every committed candidate ordinal or fails closed."""
    snap = require_readable_snapshot(storage, repository_id, snapshot_id)
    with storage.pin_reader(repository_id, snap.id):
        by_id = {e.id: e for e in load_entities(storage, repository_id, snap.id)}
        from rkg.storage.errors import NotFoundError

        if any(i not in by_id for i in ids):
            raise NotFoundError("candidate unavailable in snapshot")
        return tuple(by_id[i] for i in ids)


def entity_short_names(entity: Entity) -> set[str]:
    names = {entity.name.casefold()}
    if entity.type.value in {"Callable", "Endpoint", "Type"}:
        qualified = (
            entity.qualified_name.split(":", 1)[0]
            if entity.type.value == "Endpoint"
            else entity.qualified_name
        )
        suffix = qualified.rsplit(".", 1)[-1]
        if suffix.isidentifier():
            names.add(suffix.casefold())
    return names


def lookup_named_entities(
    storage: Storage,
    repository_id: str,
    snapshot_id: str,
    words: frozenset[str],
    *,
    entity_type: str = "any",
) -> Page:
    """Match exact known names in prose; paging retains collision/overflow total."""
    snap = require_readable_snapshot(storage, repository_id, snapshot_id)
    with storage.pin_reader(repository_id, snap.id):
        matched = [
            entity
            for entity in load_entities(storage, repository_id, snap.id)
            if entity_short_names(entity) & words
            and (entity_type == "any" or entity.type.value == entity_type)
        ]
        return Page(items=tuple(matched[:20]), offset=0, limit=20, total=len(matched))
