"""Validate reference-only narratives, then render facts with exact citations."""

from __future__ import annotations

import json
from collections import Counter, deque
from copy import deepcopy
from dataclasses import dataclass
from functools import cache
from pathlib import Path, PurePosixPath
from typing import Any

import jsonschema

from rkg.domain.models import ContextPackage, Edge, Entity
from rkg.llm import LLMError
from rkg.terminal_logging import log_debug

_SCHEMA_DIR = (
    Path(__file__).resolve().parents[3] / ".aide/tech-specs/RKG-CONVERSATION/llm"
)


@cache
def model_schema(name: str) -> dict[str, Any]:
    return json.loads((_SCHEMA_DIR / name).read_text())


def narrative_schema(context: ContextPackage) -> dict[str, Any]:
    schema = deepcopy(model_schema("SCH-RKG-NARRATIVE-v1.json"))
    if context.budget.depth is None:

        def remove_limits(value):
            if isinstance(value, dict):
                value.pop("maxItems", None)
                for child in value.values():
                    remove_limits(child)
            elif isinstance(value, list):
                for child in value:
                    remove_limits(child)

        remove_limits(schema)
    return schema


def safe_location(path: str) -> bool:
    return (
        bool(path)
        and not PurePosixPath(path).is_absolute()
        and not any(p in {"..", "."} for p in path.split("/"))
        and "\\" not in path
        and ":" not in path
        and not any(ord(c) < 32 for c in path)
    )


def source_identity(entity: Entity, language: str) -> str | None:
    """Source identity comes only from the pinned entity, never model text."""
    path = entity.file_path
    if not path or not safe_location(path) or "`" in path:
        return None
    line = entity.start_line
    position = (
        f":{line}"
        if isinstance(line, int) and not isinstance(line, bool) and line > 0
        else ""
    )
    end = entity.end_line
    span = str(line) if position else ""
    if position and isinstance(end, int) and not isinstance(end, bool) and end > line:
        span += f"–{end}"
    name = display_name(entity)
    detail = (
        (f", dòng {span}" if language == "vi" else f", lines {span}") if span else ""
    )
    return (
        f"{name} nằm trong `{path}{position}`{detail}."
        if language == "vi"
        else f"{name} is defined in `{path}{position}`{detail}."
    )


def display_name(entity: Entity) -> str:
    """Preserve the declaring class, including when its method name is unique."""
    parts = entity.qualified_name.split(".")
    if entity.type.value == "Callable" and len(parts) > 1 and parts[-2][:1].isupper():
        return ".".join(parts[-2:])
    return entity.name


def usable_evidence(context: ContextPackage) -> set[str]:
    return {
        e.id
        for e in context.evidence
        if e.snapshot_id == context.snapshot_id
        and safe_location(e.file_path)
        and 0 < e.start_line <= e.end_line
    }


@dataclass(frozen=True)
class NarrativePath:
    relation: str
    direction: str
    anchor_id: str
    edge_ids: tuple[str, ...]
    connector_id: str | None = None


def _valid_edge(
    edge: Edge, context: ContextPackage, nodes: dict[str, Entity], supported: set[str]
) -> bool:
    endpoints = (edge.source_id, edge.target_id)
    if any(
        i != context.repository_id
        and (
            i not in nodes
            or nodes[i].snapshot_id != context.snapshot_id
            or nodes[i].repository_id != context.repository_id
        )
        for i in endpoints
    ):
        return False
    return (
        edge.snapshot_id == context.snapshot_id
        and (edge.source_id in nodes or edge.source_id == context.repository_id)
        and (edge.target_id in nodes or edge.target_id == context.repository_id)
        and bool(set(edge.evidence_ids) & supported)
    )


def _connectors(
    root: Entity, context: ContextPackage, nodes: dict[str, Entity], supported: set[str]
) -> dict[str, Edge]:
    return {
        e.target_id: e
        for e in context.edges
        if e.source_id == root.id
        and e.type.value == "handled_by"
        and e.target_id in nodes
        and nodes[e.target_id].type.value == "Callable"
        and _valid_edge(e, context, nodes, supported)
    }


def _candidate_paths(
    context: ContextPackage,
    anchors: list[dict[str, Any]],
    direction: str,
    nodes: dict[str, Entity],
    supported: set[str],
) -> list[dict[str, Any]]:
    """One shortest acyclic witness per eligible final edge, not sibling lists."""
    edges = sorted(
        (e for e in context.edges if _valid_edge(e, context, nodes, supported)),
        key=lambda edge: edge.id,
    )
    adjacency: dict[str, list[tuple[Edge, str]]] = {}
    for edge in edges:
        start, end = (
            (edge.source_id, edge.target_id)
            if direction == "outgoing"
            else (edge.target_id, edge.source_id)
        )
        adjacency.setdefault(start, []).append((edge, end))

    def prefix(
        anchor: str, target: str, avoid: str, relation: str, max_edges: int
    ) -> list[str] | None:
        if anchor == avoid:
            return None
        queue = deque([(anchor, [])])
        visited = {anchor, avoid}
        while queue:
            current, path = queue.popleft()
            if current == target:
                return path
            if len(path) >= max_edges:
                continue
            expected = relation if direction == "incoming" and not path else "calls"
            for edge, end in adjacency.get(current, []):
                if edge.type.value == expected and end not in visited:
                    visited.add(end)
                    queue.append((end, [*path, edge.id]))
        return None

    result = []
    for entry in anchors:
        anchor = entry["anchor_id"]
        for relation in entry["relations"]:
            for edge in edges:
                start, end = (
                    (edge.source_id, edge.target_id)
                    if direction == "outgoing"
                    else (edge.target_id, edge.source_id)
                )
                if direction == "outgoing" and edge.type.value != relation:
                    continue
                if direction == "incoming" and edge.type.value not in {
                    relation,
                    "calls",
                }:
                    continue
                before = prefix(
                    anchor, start, end, relation, entry["max_path_edges"] - 1
                )
                if before is None:
                    continue
                if direction == "incoming" and edge.type.value != (
                    "calls" if before else relation
                ):
                    continue
                result.append(
                    {
                        "relation": relation,
                        "direction": direction,
                        "anchor_id": anchor,
                        "edge_ids": [*before, edge.id],
                    }
                )
    return sorted(
        result,
        key=lambda item: (
            item["relation"],
            len(item["edge_ids"]),
            item["anchor_id"],
            item["edge_ids"],
        ),
    )


def narrative_guidance(
    context: ContextPackage, relations: tuple[str, ...], direction: str = "outgoing"
) -> dict[str, Any]:
    """Supply permitted IDs and constraints; this never replaces output validation."""
    nodes = {node.id: node for node in context.nodes}
    root = nodes.get(context.root_id)
    allowed = list(relations) or list(
        model_schema("SCH-RKG-NARRATIVE-v1.json")["properties"]["sections"]["items"][
            "properties"
        ]["relation"]["enum"]
    )
    anchors = []
    depth = context.budget.depth
    unlimited = depth is None
    path_depth = len(context.nodes) if unlimited else min(4, depth)
    if (
        root is not None
        and root.repository_id == context.repository_id
        and root.snapshot_id == context.snapshot_id
    ):
        direct = (
            allowed
            if root.type.value != "Endpoint"
            else [r for r in allowed if r in {"handled_by", "depends_on"}]
        )
        if direct and (unlimited or depth > 0):
            anchors.append(
                {
                    "anchor_id": root.id,
                    "connector_id": None,
                    "relations": direct,
                    "max_path_edges": path_depth,
                }
            )
        if root.type.value == "Endpoint" and (unlimited or depth > 1):
            bridged = [r for r in allowed if r not in {"handled_by", "depends_on"}]
            if bridged:
                for anchor, edge in _connectors(
                    root, context, nodes, usable_evidence(context)
                ).items():
                    anchors.append(
                        {
                            "anchor_id": anchor,
                            "connector_id": edge.id,
                            "relations": bridged,
                            "max_path_edges": path_depth
                            if unlimited
                            else min(4, depth - 1),
                        }
                    )
    return {
        "allowed_anchors": anchors,
        "candidate_paths": _candidate_paths(
            context, anchors, direction, nodes, usable_evidence(context)
        ),
        "path_limits": {
            "max_sections": len(allowed) if unlimited else 4,
            "max_paths_per_section": len(context.edges) if unlimited else 8,
            "max_distinct_edges": len(context.edges) if unlimited else 8,
        },
    }


def validate_narrative(
    value: object, context: ContextPackage, relations: tuple[str, ...], direction: str
) -> tuple[NarrativePath, ...]:
    def invalid(rule: str = "invalid_narrative", **detail: Any):
        log_debug("narrative_validation_failed", rule=rule, **detail)
        raise LLMError("llm_malformed_response")

    try:
        jsonschema.validate(value, narrative_schema(context))
    except (jsonschema.ValidationError, jsonschema.SchemaError):
        invalid()
    if value["root_id"] != context.root_id:
        invalid("root_mismatch", expected=context.root_id, actual=value["root_id"])
    if (value["status"] == "insufficient_evidence") != (not value["sections"]):
        invalid("status_sections_mismatch", status=value["status"])
    nodes = {n.id: n for n in context.nodes}
    edges = {e.id: e for e in context.edges}
    supported = usable_evidence(context)
    if context.root_id not in nodes:
        invalid("missing_context_root")
    root = nodes[context.root_id]
    if (
        root.snapshot_id != context.snapshot_id
        or root.repository_id != context.repository_id
    ):
        invalid("context_pin_mismatch")

    def valid_edge(edge: Edge) -> bool:
        return _valid_edge(edge, context, nodes, supported)

    connectors = _connectors(root, context, nodes, supported)
    paths = []
    semantic = set()
    for section in value["sections"]:
        relation = section["relation"]
        if section["direction"] != direction or (
            relations and relation not in relations
        ):
            invalid(
                "section_policy_mismatch",
                expected_direction=direction,
                allowed_relations=relations,
                section=section,
            )
        for path in section["paths"]:
            anchor = path["anchor_id"]
            connector = None
            if root.type.value == "Endpoint" and relation not in {
                "handled_by",
                "depends_on",
            }:
                if anchor not in connectors:
                    invalid(
                        "invalid_handler_anchor",
                        actual=anchor,
                        allowed=list(connectors),
                    )
                connector = connectors[anchor].id
            elif anchor != root.id:
                invalid("invalid_root_anchor", actual=anchor, expected=root.id)
            current = anchor
            seen = {anchor}
            ids = path["edge_ids"]
            for i, edge_id in enumerate(ids):
                edge = edges.get(edge_id)
                if edge is None or not valid_edge(edge):
                    invalid(
                        "unknown_edge"
                        if edge is None
                        else "invalid_edge_evidence_or_pin",
                        edge_id=edge_id,
                    )
                endpoint_index = len(ids) - 1 if direction == "outgoing" else 0
                expected = relation if i == endpoint_index else "calls"
                if edge.type.value != expected:
                    invalid(
                        "edge_relation_mismatch",
                        edge_id=edge_id,
                        expected=expected,
                        actual=edge.type.value,
                    )
                start, end = (
                    (edge.source_id, edge.target_id)
                    if direction == "outgoing"
                    else (edge.target_id, edge.source_id)
                )
                if start != current or end in seen:
                    invalid(
                        "disconnected_path" if start != current else "cyclic_path",
                        edge_id=edge_id,
                        expected_start=current,
                        actual_start=start,
                    )
                seen.add(end)
                current = end
                semantic.add(edge.id)
            if context.budget.depth is not None and (
                len(ids) + (1 if connector else 0) > context.budget.depth
            ):
                invalid(
                    "path_depth_exceeded",
                    path_edges=len(ids),
                    connector_edges=1 if connector else 0,
                    depth=context.budget.depth,
                )
            paths.append(
                NarrativePath(relation, direction, anchor, tuple(ids), connector)
            )
    if context.budget.depth is not None and len(semantic) > 8:
        invalid("semantic_edge_limit", count=len(semantic), limit=8)
    return tuple(paths)


_VERBS = {
    "en": {
        "calls": "calls",
        "reads": "reads",
        "writes": "writes to",
        "publishes": "publishes to",
        "consumes": "consumes from",
        "handled_by": "is handled by",
        "depends_on": "depends on",
        "contains": "contains",
        "imports": "imports",
        "exposes": "exposes",
        "implements": "implements",
        "inherits_from": "inherits from",
        "maps_to": "maps to",
    },
    "vi": {
        "calls": "gọi",
        "reads": "đọc",
        "writes": "ghi vào",
        "publishes": "phát lên",
        "consumes": "nhận từ",
        "handled_by": "được xử lý bởi",
        "depends_on": "phụ thuộc vào",
        "contains": "chứa",
        "imports": "nhập",
        "exposes": "công bố",
        "implements": "triển khai",
        "inherits_from": "kế thừa",
        "maps_to": "ánh xạ tới",
    },
}


def render_narrative(
    paths: tuple[NarrativePath, ...], context: ContextPackage, language: str
) -> tuple[str, tuple[dict[str, Any], ...], tuple[dict[str, Any], ...]]:
    nodes = {n.id: n for n in context.nodes}
    edges = {e.id: e for e in context.edges}
    selected_ids = {i for p in paths for i in p.edge_ids} | {
        p.connector_id for p in paths if p.connector_id
    }
    rendered_nodes = {context.root_id} | {
        j for i in selected_ids for j in (edges[i].source_id, edges[i].target_id)
    }
    counts = Counter(nodes[i].name for i in rendered_nodes if i in nodes)

    def base_label(entity: Entity) -> str:
        if entity.type.value == "DataResource":
            attrs = dict(entity.attributes)
            namespace = attrs.get("namespace") or attrs.get("schema")
            if namespace:
                return f"{namespace}.{entity.name}"
        if entity.type.value == "Endpoint":
            attrs = dict(entity.attributes)
            if attrs.get("method") and attrs.get("path"):
                return f"{attrs['method']} {attrs['path']}"
        return (
            display_name(entity) if counts[entity.name] == 1 else entity.qualified_name
        )

    bases = Counter(base_label(nodes[i]) for i in rendered_nodes if i in nodes)
    if context.repository_id in rendered_nodes:
        bases["kho mã" if language == "vi" else "repository"] += 1
    locations = Counter(
        (base_label(nodes[i]), nodes[i].file_path, nodes[i].start_line)
        for i in rendered_nodes
        if i in nodes
    )

    def label(entity: Entity) -> str:
        base = base_label(entity)
        if bases[base] == 1:
            return base
        location = (
            entity.file_path
            if entity.file_path and safe_location(entity.file_path)
            else ""
        )
        if location and entity.start_line is not None and entity.start_line > 0:
            location += f":{entity.start_line}"
        if not location or locations[(base, entity.file_path, entity.start_line)] > 1:
            location = f"{location}; {entity.id}" if location else entity.id
        return f"{base} [{location}]"

    def identity(entity_id: str) -> str:
        if entity_id == context.repository_id:
            return "kho mã" if language == "vi" else "repository"
        return label(nodes[entity_id])

    def text(edge: Edge) -> str:
        source = identity(edge.source_id)
        target = identity(edge.target_id)
        return f"{source} {_VERBS[language][edge.type.value]} {target}."

    supported = usable_evidence(context)
    claims = []
    citations = []
    claimed = set()

    def add(edge_id: str):
        if edge_id in claimed:
            return
        edge = edges[edge_id]
        indexes = []
        for evidence_id in edge.evidence_ids:
            if evidence_id not in supported:
                continue
            indexes.append(len(citations))
            citations.append(
                {
                    "snapshot_id": context.snapshot_id,
                    "entity_id": edge.target_id,
                    "evidence_id": evidence_id,
                    "edge_id": edge.id,
                }
            )
        claims.append(
            {"text": text(edge), "edge_id": edge.id, "citation_indexes": indexes}
        )
        claimed.add(edge_id)

    def joined(names: list[str]) -> str:
        if len(names) < 2:
            return names[0]
        conjunction = " và " if language == "vi" else " and "
        return ", ".join(names[:-1]) + conjunction + names[-1]

    def relation_sentence(
        source_id: str, relation: str, targets: list[str], indirect: bool | None = None
    ) -> str:
        source = identity(source_id)
        names = joined([identity(target) for target in targets])
        verb = _VERBS[language][relation]
        # Name a table only when the graph actually identifies it as a table.
        if relation in {"reads", "writes"}:
            tables = all(
                target in nodes
                and dict(nodes[target].attributes).get("resource_kind") == "table"
                for target in targets
            )
            if language == "vi":
                verb = "đọc" if relation == "reads" else "ghi"
                noun = ("bảng" if len(targets) == 1 else "các bảng") if tables else ""
                preposition = "từ" if relation == "reads" else "vào"
                target_text = f"dữ liệu {preposition} {noun} {names}".replace("  ", " ")
            else:
                noun = ("table" if len(targets) == 1 else "tables") if tables else ""
                target_text = f"{noun} {names}".strip()
        else:
            target_text = names
        if indirect is None:
            return f"{source} {verb} {target_text}."
        if language == "vi":
            qualifier = "gián tiếp" if indirect else "trực tiếp"
            phrasing = {
                "handled_by": f"được xử lý {qualifier} bởi",
                "depends_on": f"phụ thuộc {qualifier} vào",
                "publishes": f"phát {qualifier} lên",
                "consumes": f"nhận {qualifier} từ",
                "maps_to": f"ánh xạ {qualifier} tới",
            }.get(relation, f"{verb} {qualifier}")
            return f"{source} {phrasing} {target_text}."
        qualifier = "indirectly" if indirect else "directly"
        return f"{source} {verb} {target_text} {qualifier}."

    paragraphs = []
    for connector in sorted({p.connector_id for p in paths if p.connector_id}):
        add(connector)
        paragraphs.append(text(edges[connector]))

    call_paths = [p for p in paths if p.relation == "calls"]
    call_edges = {i: edges[i] for p in call_paths for i in p.edge_ids}
    if call_paths:
        for key in call_edges:
            add(key)
        direction = call_paths[0].direction
        grouped_calls = {}
        evidence = {e.id: e for e in context.evidence}
        for edge in sorted(
            call_edges.values(),
            key=lambda e: (
                e.source_id,
                min(
                    (
                        evidence[i].start_line or 0
                        for i in e.evidence_ids
                        if i in evidence
                    ),
                    default=0,
                ),
                e.id,
            ),
        ):
            key, target = (
                (edge.source_id, edge.target_id)
                if direction == "outgoing"
                else (edge.target_id, edge.source_id)
            )
            grouped_calls.setdefault(key, []).append(target)
        for key, targets in grouped_calls.items():
            names = joined([identity(i) for i in dict.fromkeys(targets)])
            if direction == "incoming":
                paragraphs.append(
                    f"{identity(key)} được gọi trực tiếp bởi {names}."
                    if language == "vi"
                    else f"{identity(key)} is called directly by {names}."
                )
            else:
                paragraphs.append(
                    relation_sentence(key, "calls", list(dict.fromkeys(targets)), False)
                )
        direct_targets = {
            (
                edges[p.edge_ids[0]].target_id
                if direction == "outgoing"
                else edges[p.edge_ids[0]].source_id
            )
            for p in call_paths
            if len(p.edge_ids) == 1
        }
        indirect = [
            p
            for p in call_paths
            if len(p.edge_ids) > 1
            and (
                edges[p.edge_ids[-1]].target_id
                if direction == "outgoing"
                else edges[p.edge_ids[-1]].source_id
            )
            not in direct_targets
        ]
        if indirect:
            endpoints = list(
                dict.fromkeys(
                    edges[p.edge_ids[-1]].target_id
                    if direction == "outgoing"
                    else edges[p.edge_ids[-1]].source_id
                    for p in indirect
                )
            )
            names = joined([identity(i) for i in endpoints])
            root_name = identity(context.root_id)
            if direction == "outgoing":
                paragraphs.append(
                    f"Qua các bước gọi trên, {root_name} còn gọi gián tiếp {names}."
                    if language == "vi"
                    else f"{root_name} calls {names} indirectly through these steps."
                )
            else:
                paragraphs.append(
                    f"Các hàm {names} gọi gián tiếp {root_name} qua những bước trên."
                    if language == "vi"
                    else f"{names} call {root_name} indirectly through these steps."
                )

    # Combine sibling reads/writes with the same call prefix, keeping every
    # selected edge in claims/citations. Incoming paths keep their caller order.
    groups = {}
    for path in paths:
        if path.relation == "calls":
            continue
        key = (
            path.direction,
            path.relation,
            path.anchor_id,
            path.edge_ids[:-1] if path.direction == "outgoing" else path.edge_ids,
        )
        groups.setdefault(key, []).append(path)
    for group in groups.values():
        path = group[0]
        for item in group:
            for edge_id in item.edge_ids:
                add(edge_id)
        ordered = [edges[i] for i in path.edge_ids]
        if path.direction == "incoming":
            ordered.reverse()
        first, last = ordered[0], ordered[-1]
        targets = (
            list(dict.fromkeys(edges[item.edge_ids[-1]].target_id for item in group))
            if path.direction == "outgoing"
            else [last.target_id]
        )
        indirect = len(ordered) > 1
        summary = relation_sentence(first.source_id, path.relation, targets, indirect)
        if not indirect:
            paragraphs.append(summary)
            continue
        steps = [text(edge) for edge in ordered[:-1]]
        steps.append(relation_sentence(last.source_id, last.type.value, targets))
        introduction = "Cụ thể, " if language == "vi" else "Specifically, "
        paragraphs.append(summary + " " + introduction + " ".join(steps))
    return "\n\n".join(paragraphs), tuple(claims), tuple(citations)
