"""Suggest edit locations from snapshot metadata and verified relationships."""

import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass

from rkg.conversations.narrative import (
    NarrativePath,
    _valid_edge,
    render_narrative,
    safe_location,
    usable_evidence,
)
from rkg.domain.models import Entity, EntityType
from rkg.graph.access import load_entities, require_readable_snapshot
from rkg.graph.observation import observe_entity
from rkg.graph.related import build_related_context
from rkg.storage import Storage


def change_intent(question: str) -> str | None:
    prose = re.sub(r"`[^`]*`|/\S+|\b\w+(?:[._]\w+)+\b", " ", question)
    prose = unicodedata.normalize("NFD", prose.casefold()).replace("đ", "d")
    prose = "".join(c for c in prose if not unicodedata.combining(c))
    scope = re.search(
        r"\b(?:api|endpoint|code|ham|function|method|class|file|logic|service|"
        r"repository|sua|o dau|dong nao|where|line)\b",
        prose,
    )
    if not scope:
        return None
    if re.search(r"\b(?:them|bo sung|tao|add|adding|new|create|implement)\b", prose):
        return "add"
    if re.search(
        r"\b(?:sua|doi|chinh|edit|modify|change|update|fix|refactor)\b", prose
    ) or re.match(r"^\s*ua\b", prose):
        return "modify"
    return None


def feature_reference(question: str, catalog: list[dict]) -> tuple[str, ...]:
    """Resolve common translated action/topic pairs against real catalog entries."""
    text = unicodedata.normalize("NFD", question.casefold()).replace("đ", "d")
    text = "".join(c for c in text if not unicodedata.combining(c))
    if re.search(r"\b(?:xoa|don dep|cleanup|delete)\b", text) and re.search(
        r"\b(?:cu|older|old|cleanup)\b", text
    ):
        cleanup = [
            e["qualified_name"]
            for e in catalog
            if e["type"] == "Callable"
            and e["name"].casefold() in {"run", "cleanup"}
            and re.search(r"cleanup", e["qualified_name"], re.I)
        ]
        if len(cleanup) == 1:
            return tuple(cleanup)
    if re.search(r"\b(?:api|endpoint)\b", text) and re.search(
        r"\b(?:them|add|new)\b", text
    ):
        words = {w.removesuffix("s") for w in re.findall(r"[a-z]+", text)}
        if "don" in words:
            words.add("order")
        controllers = [
            e["qualified_name"]
            for e in catalog
            if e["type"] == "Type"
            and e["name"].endswith("Controller")
            and words
            & {
                w.casefold().removesuffix("s")
                for w in re.findall(
                    r"[A-Z]?[a-z]+", e["name"].removesuffix("Controller")
                )
            }
        ]
        if len(controllers) == 1:
            return tuple(controllers)
    # Match action and role against symbols that actually exist in this snapshot.
    role = None
    if re.search(r"request|frontend|phia client", text) and re.search(
        r"cap nhat|update", text
    ):

        def role(e):
            return e["name"].startswith("update") and "Api" in e["qualified_name"]
    elif re.search(r"job|processor", text) and re.search(r"email|gui thu", text):

        def role(e):
            return re.search(r"process.*email", e["name"], re.I)

    if role:
        matches = [
            e["qualified_name"] for e in catalog if e["type"] == "Callable" and role(e)
        ]
        if len(matches) == 1:
            return tuple(matches)
    actions = {"huy": "cancel", "dang nhap": "login", "dang xuat": "logout"}
    topics = {"don": "order", "gio hang": "cart", "san pham": "product"}
    action = next(
        (
            value
            for key, value in actions.items()
            if re.search(r"\b" + key + r"\b", text)
        ),
        None,
    )
    topic = next(
        (
            value
            for key, value in topics.items()
            if re.search(r"\b" + key + r"\b", text)
        ),
        None,
    )
    if not action or not topic:
        return ()
    matches = []
    for entry in catalog:
        if re.search(r"\b(?:api|endpoint)\b", text) and entry["type"] != "Endpoint":
            continue
        tokens = set(
            re.findall(
                r"[a-z]+",
                (
                    entry["name"]
                    + " "
                    + entry["qualified_name"]
                    + " "
                    + (entry["path"] or "")
                ).casefold(),
            )
        )
        if action in tokens and ({topic, topic + "s"} & tokens):
            matches.append(entry["qualified_name"])
    return tuple(dict.fromkeys(matches))


def nearby_endpoints(
    storage: Storage, repository_id: str, snapshot_id: str, path: str
) -> tuple[Entity, ...]:
    """An existing route in the same feature is an example, never a new fact.

    Require a shared feature segment beyond api/version prefixes; do not infer
    a destination from the mere fact that all routes start with /api/v1.
    """
    requested = path.strip("/").split("/")
    groups = defaultdict(list)
    best = 0
    snap = require_readable_snapshot(storage, repository_id, snapshot_id)
    with storage.pin_reader(repository_id, snap.id):
        for entity in load_entities(storage, repository_id, snap.id):
            if entity.type != EntityType.ENDPOINT or not entity.file_path:
                continue
            existing = dict(entity.attributes).get("path", "")
            if not isinstance(existing, str):
                continue
            common = []
            for left, right in zip(requested, existing.strip("/").split("/")):
                if left != right:
                    break
                common.append(left)
            feature = [
                p
                for p in common
                if p != "api" and not re.fullmatch(r"v\d+", p) and not p.startswith("{")
            ]
            if not feature or not safe_location(entity.file_path):
                continue
            if len(common) > best:
                groups.clear()
                best = len(common)
            if len(common) == best:
                groups[entity.file_path].append(entity)
    return tuple(
        min(items, key=lambda e: (e.qualified_name, e.id))
        for _, items in sorted(groups.items())
    )


def location(entity: Entity, language: str) -> str | None:
    if (
        not entity.file_path
        or not safe_location(entity.file_path)
        or "`" in entity.file_path
    ):
        return None
    position = f"`{entity.file_path}`"
    start, end = entity.start_line, entity.end_line
    if isinstance(start, int) and not isinstance(start, bool) and start > 0:
        if isinstance(end, int) and not isinstance(end, bool) and end >= start:
            lines = str(start) if end == start else f"{start}–{end}"
        else:
            lines = str(start)
        position += f", dòng {lines}" if language == "vi" else f", lines {lines}"
    return position


# Splits the decision from supporting call flow. The UI hides the tail until opened.
# Must survive redaction, which strips HTML-like tags.
ANSWER_DETAIL_MARK = "\n\n@@rkg-detail@@\n\n"


@dataclass(frozen=True)
class ChangeGuidance:
    answer: str
    claims: tuple[dict, ...]
    citations: tuple[dict, ...]


def suggest_changes(
    storage: Storage,
    repository_id: str,
    snapshot_id: str,
    root: Entity,
    intent: str,
    language: str,
    question: str = "",
) -> ChangeGuidance | None:
    position = location(root, language)
    if position is None:
        return None
    context = build_related_context(storage, repository_id, snapshot_id, root.id)
    nodes = {n.id: n for n in context.nodes}
    supported = usable_evidence(context)
    outgoing = [e for e in context.edges if _valid_edge(e, context, nodes, supported)]
    handlers = [
        e for e in outgoing if e.source_id == root.id and e.type.value == "handled_by"
    ]
    edges = [e for e in outgoing if e.type.value == "calls"]
    paths = [
        NarrativePath("handled_by", "outgoing", root.id, (e.id,)) for e in handlers
    ]
    paths += [NarrativePath("calls", "outgoing", e.source_id, (e.id,)) for e in edges]
    _, claims, citations = render_narrative(tuple(paths), context, language)
    vi = language == "vi"

    def name(entity):
        parts = entity.qualified_name.split(".")
        return ".".join(parts[-2:]) if len(parts) > 1 else entity.name

    def references(entities):
        by_file = defaultdict(list)
        for entity in entities:
            if location(entity, language):
                by_file[entity.file_path].append(entity)
        descriptions = []
        for file, items in by_file.items():
            labels = []
            for entity in items:
                line = location(entity, language).split("`, ", 1)
                suffix = f" ({line[1]})" if len(line) == 2 else ""
                labels.append(f"`{name(entity)}`{suffix}")
            conjunction = " và " if vi else " and "
            joined = (
                conjunction.join(labels)
                if len(labels) < 3
                else (", ".join(labels[:-1]) + conjunction + labels[-1])
            )
            where = "trong cùng file" if file == root.file_path else f"trong `{file}`"
            if not vi:
                where = "in the same file" if file == root.file_path else f"in `{file}`"
            descriptions.append(f"{joined} {where}")
        return "; ".join(descriptions)

    if intent == "add":
        intro = (
            f"Bạn có thể đặt phần code mới trong {position}, cùng phần triển khai "
            f"`{name(root)}` hiện có."
            if vi
            else f"Add the new code in {position}, alongside the existing "
            f"`{name(root)}` implementation."
        )
        if root.type == EntityType.ENDPOINT:
            attrs = dict(root.attributes)
            endpoint = f"{attrs.get('method', '')} {attrs.get('path', '')}"
            intro = (
                f"Đặt API mới trong `{root.file_path}`. File này đã có API "
                f"`{endpoint}`; bạn có thể xem cách tổ chức của nó "
                "trước khi thêm route."
                if vi
                else f"Put the new API in `{root.file_path}`. This file already "
                f"contains `{endpoint}`; use its structure as a reference "
                "for the new route."
            )
    else:
        intro = (
            f"Chỗ cần xem đầu tiên là `{name(root)}` trong {position}."
            if vi
            else f"Start with `{name(root)}` in {position}."
        )
    paragraphs = [intro]
    handler_entities = [nodes[e.target_id] for e in handlers]
    if handler_entities:
        descriptions = references(handler_entities)
        if descriptions:
            paragraphs.append(
                f"API được xử lý bởi {descriptions}. "
                "Đây là chỗ để xem phần xử lý request."
                if vi
                else f"The request handler is {descriptions}. "
                "Start there for request handling changes."
            )
    # For impact questions, callers answer the question; utility callees do not.
    impact = bool(re.search(r"ảnh hưởng|anh huong|impact|affect", question, re.I))
    related = [nodes[e.target_id] for e in edges]
    related = list({e.id: e for e in related}.values())
    snap = require_readable_snapshot(storage, repository_id, snapshot_id)
    with storage.pin_reader(repository_id, snap.id):
        all_entities = load_entities(storage, repository_id, snap.id)
    candidates = [
        e
        for e in all_entities
        if e.type == EntityType.CALLABLE
        and e.name in {n.name for n in related}
        and e.file_path
        and e.language_kind != "go_interface_method"
        and "test" not in e.file_path.split("/")
        and "tests" not in e.file_path.split("/")
    ]
    alternatives = [
        entity for entity in candidates if entity.id not in {n.id for n in related}
    ]
    for entity in alternatives:
        observe_entity(entity)
    # Prefer class methods over standalone helpers when recommending adjacent
    # business code; all verified edges remain available in claims/citations.
    methods = [
        e
        for e in related
        if len(e.qualified_name.split(".")) > 1
        and e.qualified_name.split(".")[-2][:1].isupper()
    ]
    descriptions = references(methods or related)
    if descriptions and not impact:
        paragraphs.append(
            f"Từ đây, luồng gọi sang {descriptions}. "
            "Nếu thay đổi phần xử lý ở tầng này, hãy kiểm tra các hàm đó cùng nhau."
            if vi
            else f"This code calls {descriptions}. Review these functions together "
            "when changing that part of the flow."
        )
    if alternatives:
        paragraphs.append(
            (
                "Các triển khai cùng tên có thể đối chiếu: "
                if vi
                else "Implementations with the same method name to compare: "
            )
            + references(alternatives)
            + ". Đây là gợi ý vị trí kiểm tra; graph chưa chứng minh "
            "dispatch runtime tới các triển khai này."
        )
    for entity in (root, *related, *alternatives):
        attrs = dict(entity.attributes)
        if attrs.get("http_requests"):
            paragraphs.append(
                f"Request phía client của `{name(entity)}` "
                f"là `{attrs['http_requests']}`."
                if vi
                else f"The client request for `{name(entity)}` "
                f"is `{attrs['http_requests']}`."
            )
        for ref in attrs.get("query_sources") or ():
            symbol, source = ref.split("@", 1)
            paragraphs.append(
                f"SQL `{symbol}` được khai báo tại `{source}`."
                if vi
                else f"SQL `{symbol}` is declared at `{source}`."
            )
    if root.type == EntityType.TYPE and dict(root.attributes).get("route_prefix"):
        prefix = dict(root.attributes)["route_prefix"]
        paragraphs.append(
            f"Nhóm route của `{name(root)}` có base path `{prefix}`."
            if vi
            else f"The route group of `{name(root)}` has base path `{prefix}`."
        )

    details, cs, cites = implementation_details(
        storage, repository_id, snapshot_id, (root, *related), language
    )
    if details:
        paragraphs.append(details)
        offset = len(citations)
        claims += tuple(
            {**c, "citation_indexes": [i + offset for i in c["citation_indexes"]]}
            for c in cs
        )
        citations += cites

    incoming = build_related_context(
        storage,
        repository_id,
        snapshot_id,
        root.id,
        direction="incoming",
        edge_types=("calls",),
    )
    incoming_nodes = {n.id: n for n in incoming.nodes}
    incoming_supported = usable_evidence(incoming)
    callers = [
        e
        for e in incoming.edges
        if e.target_id == root.id
        and _valid_edge(e, incoming, incoming_nodes, incoming_supported)
    ]
    if callers:
        caller_paths = tuple(
            NarrativePath("calls", "incoming", root.id, (e.id,)) for e in callers
        )
        _, more_claims, more_citations = render_narrative(
            caller_paths, incoming, language
        )
        offset = len(citations)
        claims += tuple(
            {**c, "citation_indexes": [i + offset for i in c["citation_indexes"]]}
            for c in more_claims
        )
        citations += more_citations
        caller_entities = [incoming_nodes[e.source_id] for e in callers]
        tests = [
            e
            for e in caller_entities
            if e.name.startswith("test_")
            or (e.file_path and "tests" in e.file_path.split("/"))
        ]
        production = [e for e in caller_entities if e not in tests]
        descriptions = references(production)
        if descriptions:
            paragraphs.append(
                f"Khi sửa hàm này, cần kiểm tra lại {descriptions}, "
                "vì chúng gọi trực tiếp nó và có thể bị ảnh hưởng bởi thay đổi."
                if vi
                else f"Check {descriptions} after editing: they call this "
                "function directly and may be affected by the change."
            )
        test_files = sorted({e.file_path for e in tests if location(e, language)})
        descriptions = (" và " if vi else " and ").join(
            f"`{file}`" for file in test_files
        )
        if descriptions:
            paragraphs.append(
                f"Sau khi sửa, chạy lại các test {descriptions} để kiểm tra "
                "những lời gọi hiện có."
                if vi
                else f"After editing, rerun {descriptions} to check the existing calls."
            )
    if intent == "add":
        paragraphs.append(
            "Dùng phần code hiện có làm vị trí tham khảo; "
            "dòng chèn mới còn tùy cách bạn triển khai."
            if vi
            else "Use the existing code as a reference; "
            "the insertion point depends on your implementation."
        )
    elif re.search(r"dòng|dong|line|statement", question, re.I):
        paragraphs.append(
            "Đây là vùng định nghĩa của hàm, chưa phải dòng logic cụ thể cần sửa."
            if vi
            else "This is the definition range, not the exact statement to change."
        )
    lead, *supporting = paragraphs
    answer = lead
    if supporting:
        answer += ANSWER_DETAIL_MARK + "\n\n".join(supporting)
    return ChangeGuidance(answer, claims, citations)


def implementation_details(storage, repository_id, snapshot_id, subjects, language):
    """Follow declared interface implementations without claiming runtime dispatch."""
    snapshot = require_readable_snapshot(storage, repository_id, snapshot_id)
    with storage.pin_reader(repository_id, snapshot.id):
        entities = load_entities(storage, repository_id, snapshot.id)
    by_qn = {e.qualified_name: e for e in entities if e.type == EntityType.TYPE}
    owners = {
        e.qualified_name
        if e.type == EntityType.TYPE
        else e.qualified_name.rsplit(".", 1)[0]
        for e in subjects
    }
    prose, claims, citations = [], [], []
    for owner in sorted(owners & by_qn.keys()):
        interface = by_qn[owner]
        context = build_related_context(
            storage,
            repository_id,
            snapshot_id,
            interface.id,
            direction="incoming",
            edge_types=("implements",),
        )
        paths = tuple(
            NarrativePath("implements", "incoming", interface.id, (e.id,))
            for e in context.edges
            if e.target_id == interface.id
        )
        if not paths:
            continue
        text, more_claims, more_citations = render_narrative(paths, context, language)
        offset = len(citations)
        claims.extend(
            {**c, "citation_indexes": [i + offset for i in c["citation_indexes"]]}
            for c in more_claims
        )
        citations.extend(more_citations)
        prose.append(text)
        implementations = {
            e.source_id for e in context.edges if e.target_id == interface.id
        }
        nodes = {e.id: e for e in context.nodes}
        names = {
            e.name for e in subjects if e.qualified_name.rsplit(".", 1)[0] == owner
        }
        for identifier in implementations:
            implementation = nodes[identifier]
            observe_entity(implementation)
            if location(implementation, language):
                prose.append(
                    f"`{implementation.name}` nằm trong "
                    f"{location(implementation, language)}."
                )
            methods = [
                e
                for e in entities
                if e.type == EntityType.CALLABLE
                and e.qualified_name.rsplit(".", 1)[0] == implementation.qualified_name
                and e.name in names
            ]
            for method in methods:
                observe_entity(method)
                method_context = build_related_context(
                    storage,
                    repository_id,
                    snapshot_id,
                    method.id,
                    edge_types=("calls",),
                )
                direct = tuple(
                    NarrativePath("calls", "outgoing", method.id, (e.id,))
                    for e in method_context.edges
                    if e.source_id == method.id and e.type.value == "calls"
                )
                if direct:
                    text, cs, cites = render_narrative(direct, method_context, language)
                    offset = len(citations)
                    claims.extend(
                        {
                            **c,
                            "citation_indexes": [
                                i + offset for i in c["citation_indexes"]
                            ],
                        }
                        for c in cs
                    )
                    citations.extend(cites)
                    prose.append(text)
                if dict(method.attributes).get("http_requests"):
                    prose.append(
                        f"`{method.qualified_name}` dùng request "
                        f"`{dict(method.attributes)['http_requests']}`."
                    )
    return "\n\n".join(prose), tuple(claims), tuple(citations)
