"""Post-merge link: Callable static HTTP request → one Endpoint.

Runs after language and deep adapters. Reads `http_requests` already stored
on Callables (`METHOD` or `METHOD path`, segments separated by `|`). Emits
`depends_on` only when that segment is one static method and one static path
and exactly one non-navigation Endpoint has the same pair.

Does not invent attributes, guess dynamic segments, store query strings, or
target ExternalDependency.
"""

from __future__ import annotations

from rkg.domain.ids import diagnostic_id, edge_id, evidence_id
from rkg.domain.models import (
    Diagnostic,
    Edge,
    EdgeType,
    Entity,
    EntityType,
    Evidence,
    FactBatch,
    Severity,
)

RULE = "RKG.http.depends_on.v1"
AMBIGUOUS = "http_depends_on_ambiguous"
DYNAMIC = "http_depends_on_dynamic"
_METHODS = frozenset({"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"})
_DYNAMIC_MARKS = ("${", "{", "}", "*")


def link_static_http_depends_on(batch: FactBatch, *, job_id: str) -> FactBatch:
    """Return a batch with unique static HTTP depends_on edges added."""
    endpoints = _static_endpoints(batch)
    evidence = {item.id: item for item in batch.evidence}
    edges = {item.id: item for item in batch.edges}
    new_edges: list[Edge] = []
    new_evidence: list[Evidence] = []
    pending: list[tuple[str, str | None, int | None]] = []

    for source in batch.entities:
        if source.type != EntityType.CALLABLE:
            continue
        raw = dict(source.attributes).get("http_requests")
        for part in _segments(raw):
            classified = _classify(part)
            if classified is None:
                continue
            if classified == "dynamic":
                path, line = _diag_location(source)
                pending.append((DYNAMIC, path, line))
                continue
            method, route = classified
            matches = endpoints.get((method, route), ())
            if len(matches) == 1:
                _add_edge(
                    batch, source, matches[0], evidence, edges, new_edges, new_evidence
                )
            elif len(matches) > 1:
                path, line = _diag_location(source)
                pending.append((AMBIGUOUS, path, line))

    diagnostics = list(batch.diagnostics)
    seen = {
        (item.code, item.file_path, item.line)
        for item in diagnostics
    }
    ordinal = len(diagnostics)
    for code, path, line in pending:
        key = (code, path, line)
        if key in seen:
            continue
        seen.add(key)
        diagnostics.append(
            Diagnostic(
                diagnostic_id(job_id, code, path, line, ordinal),
                job_id,
                Severity.WARNING,
                code,
                _message(code),
                batch.snapshot_id,
                path,
                line,
            )
        )
        ordinal += 1

    if not new_edges and len(diagnostics) == len(batch.diagnostics):
        return batch
    return FactBatch(
        batch.repository_id,
        batch.snapshot_id,
        batch.entities,
        batch.edges + tuple(new_edges),
        batch.evidence + tuple(new_evidence),
        tuple(diagnostics),
    )


def _static_endpoints(batch: FactBatch) -> dict[tuple[str, str], tuple[Entity, ...]]:
    grouped: dict[tuple[str, str], list[Entity]] = {}
    for entity in batch.entities:
        if entity.type != EntityType.ENDPOINT:
            continue
        attrs = dict(entity.attributes)
        if attrs.get("kind") == "navigation":
            continue
        method = attrs.get("method")
        path = attrs.get("path")
        if not isinstance(method, str) or not isinstance(path, str):
            continue
        if "route_path" in attrs and attrs.get("route_path") not in {None, path}:
            continue
        classified = _classify(f"{method} {path}")
        if not isinstance(classified, tuple):
            continue
        grouped.setdefault(classified, []).append(entity)
    return {key: tuple(items) for key, items in grouped.items()}


def _add_edge(
    batch: FactBatch,
    source: Entity,
    target: Entity,
    evidence: dict[str, Evidence],
    edges: dict[str, Edge],
    new_edges: list[Edge],
    new_evidence: list[Evidence],
) -> None:
    location = _evidence_location(source)
    if location is None:
        return
    path, start, end = location
    key = edge_id(batch.snapshot_id, EdgeType.DEPENDS_ON, source.id, target.id)
    if key in edges:
        return
    ref = evidence_id(batch.snapshot_id, path, start, end, RULE)
    if ref not in evidence:
        created = Evidence(ref, batch.snapshot_id, path, start, end, RULE)
        evidence[ref] = created
        new_evidence.append(created)
    edge = Edge(
        key,
        batch.snapshot_id,
        EdgeType.DEPENDS_ON,
        source.id,
        target.id,
        RULE,
        (ref,),
    )
    edges[key] = edge
    new_edges.append(edge)


def _segments(raw: object) -> list[str]:
    if not isinstance(raw, str) or not raw.strip():
        return []
    return [part.strip() for part in raw.split("|") if part.strip()]


def _classify(part: str) -> tuple[str, str] | str | None:
    """Return `(method, path)`, `dynamic`, or None when the segment is not linkable."""
    pieces = part.split(None, 1)
    if len(pieces) != 2:
        return None
    method = pieces[0].upper()
    if method not in _METHODS or not pieces[0].isalpha():
        return None
    route = pieces[1].strip()
    for separator in ("?", "#"):
        route = route.split(separator, 1)[0].strip()
    if not route or any(char.isspace() for char in route):
        return None
    if "://" in route or route.startswith("//"):
        return None
    if any(mark in route for mark in _DYNAMIC_MARKS):
        return "dynamic"
    if any(segment.startswith(":") for segment in route.split("/")):
        return "dynamic"
    if not route.startswith("/"):
        route = f"/{route}"
    return method, route


def _evidence_location(entity: Entity) -> tuple[str, int, int] | None:
    path = _relative(entity.file_path)
    start = entity.start_line
    end = entity.end_line if entity.end_line is not None else start
    if path is None or start is None or end is None or start < 1 or end < start:
        return None
    return path, start, end


def _diag_location(entity: Entity) -> tuple[str | None, int | None]:
    path = _relative(entity.file_path)
    line = entity.start_line
    if line is None or line < 1:
        line = None
    return path, line


def _relative(path: str | None) -> str | None:
    if not path:
        return None
    normal = path.replace("\\", "/")
    if not normal or normal.startswith("/") or "://" in normal:
        return None
    return normal


def _message(code: str) -> str:
    if code == AMBIGUOUS:
        return "More than one endpoint has this static HTTP method and path."
    return "HTTP request path is dynamic."
