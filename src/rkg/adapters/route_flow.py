"""Shared UI-navigation route List/Graph enrichment (OQ-RKG-007).

Walks calls + depends_on from a page handler to derive route_signal,
page_handler, and outbound_requests for navigation Endpoints.
"""

from __future__ import annotations

from rkg.domain import Edge, EdgeType, Entity, EntityType

_HTTP_CLIENT_METHODS = frozenset(
    {"get", "put", "post", "patch", "delete", "request", "fetch"}
)


def _split_attr_lines(raw: object) -> list[str]:
    if not isinstance(raw, str) or not raw.strip():
        return []
    return [part.strip() for part in raw.split("|") if part.strip()]


def _callable_http_requests(entity: Entity) -> list[str]:
    attrs = dict(entity.attributes)
    return _split_attr_lines(attrs.get("http_requests"))


def _callable_http_responses(entity: Entity) -> list[str]:
    attrs = dict(entity.attributes)
    return _split_attr_lines(attrs.get("http_response_types"))


def _terminal_label(entity: Entity) -> str:
    """Short List label for config keys / HTTP origins (origin only, no secrets)."""
    attrs = dict(entity.attributes)
    if entity.type == EntityType.EXTERNAL_DEPENDENCY:
        origin = attrs.get("origin")
        if isinstance(origin, str) and origin:
            return origin
        return entity.name
    if entity.type == EntityType.CONFIGURATION:
        qualified = entity.qualified_name
        if ":" in qualified:
            return qualified.split(":", 1)[1]
        return entity.name
    return entity.name


def route_flow_attrs(
    handler: Entity,
    entities: dict[str, Entity],
    edges: dict[str, Edge],
) -> tuple[tuple[str, str], ...]:
    """List signals: page handler, shell/outbound signal, and outbound request lines."""
    outgoing: dict[str, list[tuple[EdgeType, str]]] = {}
    for edge in edges.values():
        if edge.type in (EdgeType.CALLS, EdgeType.DEPENDS_ON):
            outgoing.setdefault(edge.source_id, []).append((edge.type, edge.target_id))

    seen: set[str] = set()
    queue = [handler.id]
    # Page setup / script-setup: include same-file Callables so local
    # $fetch/useFetch annotations participate without inventing call edges.
    if handler.file_path:
        page_path = handler.file_path.replace("\\", "/")
        for item in entities.values():
            if (
                item.type == EntityType.CALLABLE
                and item.id != handler.id
                and item.file_path
                and item.file_path.replace("\\", "/") == page_path
            ):
                queue.append(item.id)
    reached_terminal = False
    reached_http_client = False
    call_count = 0
    while queue:
        current = queue.pop(0)
        if current in seen:
            continue
        seen.add(current)
        for kind, other in outgoing.get(current, []):
            if kind == EdgeType.CALLS:
                call_count += 1
            target = entities.get(other)
            if target is not None and target.type in (
                EntityType.EXTERNAL_DEPENDENCY,
                EntityType.CONFIGURATION,
            ):
                reached_terminal = True
            if (
                target is not None
                and target.type == EntityType.CALLABLE
                and target.name.lower() in _HTTP_CLIENT_METHODS
            ):
                reached_http_client = True
            if other not in seen:
                queue.append(other)

    request_lines: list[str] = []
    response_lines: list[str] = []
    seen_lines: set[str] = set()

    def _push(line: str, response: str | None = None) -> None:
        if line in seen_lines or len(request_lines) >= 12:
            return
        seen_lines.add(line)
        request_lines.append(line)
        if response:
            response_lines.append(response)
        else:
            response_lines.append("")

    def _reach_sort_key(entity_id: str) -> tuple[str, str]:
        source = entities.get(entity_id)
        if source is None:
            return ("", entity_id)
        return (source.qualified_name, entity_id)

    for entity_id in sorted(seen, key=_reach_sort_key):
        source = entities.get(entity_id)
        if source is None or source.name.lower() in _HTTP_CLIENT_METHODS:
            continue
        if source.type not in (EntityType.CALLABLE, EntityType.SOURCE_UNIT):
            continue
        requests = _callable_http_requests(source)
        if not requests:
            continue
        responses = _callable_http_responses(source)
        terminals: list[str] = []
        for kind, other in outgoing.get(entity_id, []):
            if kind != EdgeType.DEPENDS_ON:
                continue
            target = entities.get(other)
            if target is None or target.type not in (
                EntityType.EXTERNAL_DEPENDENCY,
                EntityType.CONFIGURATION,
            ):
                continue
            terminals.append(_terminal_label(target))
        for index, req in enumerate(requests):
            resp = responses[index] if index < len(responses) else ""
            if terminals:
                for terminal in terminals:
                    _push(f"{req} → {terminal}", resp or None)
            else:
                _push(req, resp or None)

    if not request_lines:
        for edge in edges.values():
            if edge.type != EdgeType.DEPENDS_ON or edge.source_id not in seen:
                continue
            target = entities.get(edge.target_id)
            if target is None or target.type not in (
                EntityType.EXTERNAL_DEPENDENCY,
                EntityType.CONFIGURATION,
            ):
                continue
            source = entities.get(edge.source_id)
            caller = source.name if source is not None else "?"
            _push(f"{caller} → {_terminal_label(target)}")

    if not request_lines:
        for edge in edges.values():
            if edge.type != EdgeType.CALLS or edge.source_id not in seen:
                continue
            target = entities.get(edge.target_id)
            source = entities.get(edge.source_id)
            if (
                target is None
                or source is None
                or target.type != EntityType.CALLABLE
                or target.name.lower() not in _HTTP_CLIENT_METHODS
            ):
                continue
            if source.name.lower() in _HTTP_CLIENT_METHODS:
                continue
            method = target.name.upper() if target.name.lower() != "request" else None
            if method and method != "FETCH":
                _push(method)
            else:
                _push(f"{source.name} → {target.name}")

    if reached_terminal or reached_http_client or request_lines:
        signal = "outbound_http"
    elif call_count == 0:
        signal = "shell"
    else:
        signal = "partial"

    attrs: list[tuple[str, str]] = [
        ("page_handler", handler.name),
        ("route_signal", signal),
    ]
    if request_lines:
        attrs.append(("outbound_requests", " | ".join(request_lines)))
        if any(response_lines):
            attrs.append(("outbound_responses", " | ".join(response_lines)))
    return tuple(attrs)
