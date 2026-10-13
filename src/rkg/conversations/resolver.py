"""User intent parsing supplies only typed lookup predicates, never graph queries."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Lookup:
    query: str
    entity_type: str = "any"
    method: str | None = None
    path: str | None = None


def intent_question(question: str) -> str:
    """Keep the code question separate from appended execution/override demands."""
    prefix, separator, suffix = question.partition("?")
    if separator and re.search(
        r"bỏ (?:mọi|qua|bằng)|bỏ bằng|bí mật|chạy (?:source|worker)|"
        r"ignore (?:all|the)|disregard|execute|secrets|khẳng định|thay topic",
        suffix,
        re.I,
    ):
        return prefix + "?"
    return question


def explicit_lookup(question: str) -> Lookup | None:
    method_path = re.search(
        r"\b(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+(/[^\s`]+)", question, re.I
    )
    if method_path:
        return Lookup(
            "", "Endpoint", method_path[1].upper(), method_path[2].rstrip("?.!,;\"'”")
        )
    path = re.search(r"(?<!\w)(/[^\s`]+)", question)
    if path:
        return Lookup("", "Endpoint", path=path[1].rstrip("?.!,;\"'”"))
    kind = "Endpoint" if re.search(r"\bendpoint\b", question, re.I) else "any"
    quoted = re.search(r"`([^`]+)`", question)
    qualified = re.search(r"\b\w+(?:[._]\w+)+\b", question)
    typed = re.search(
        r"\b(endpoint|function|callable|handler|hàm|ham)\s+([\w.]+)",
        question,
        re.I,
    )
    if typed:
        kind = "Endpoint" if typed[1].casefold() == "endpoint" else "Callable"
    named = re.search(
        r"\b(?:endpoint|function|callable|handler|hàm|ham|does)\s+([\w.]+)",
        question,
        re.I,
    )
    symbols = re.findall(r"\b[A-Za-z_]\w*[a-z][A-Z]\w*\b", question)
    camel = (
        re.search(r"\b" + re.escape(symbols[0]) + r"\b", question)
        if len(symbols) == 1
        else None
    )
    if camel is not None and not mention_precedes_pronoun(
        question, {camel[0].casefold()}
    ):
        camel = None
    match = quoted or qualified or camel or typed or named
    if not match:
        return None
    value = (
        match[2]
        if match is typed
        else match[1]
        if match is quoted or match is named
        else match[0]
    )
    if (
        value.casefold() in {"it", "its", "this", "that", "nó", "no", "đó"}
        or (match is typed or match is named)
        and value.casefold() in _PROSE_WORDS - {"a"}
    ):
        return None
    return Lookup(value, kind)


def intent_direction(question: str) -> str:
    return (
        "incoming"
        if re.search(
            r"\b(?:who calls|called by|callers|ai gọi|ai goi|hàm nào gọi|"
            r"ham nao goi|which function calls|which method calls)\b",
            question,
            re.I,
        )
        else "outgoing"
    )


# These are prose/pronoun tokens, not evidence of a newly named graph entity.
_PROSE_WORDS = frozenset(
    """what which who how where is are does do it its this that
and or the a an calls call called reads read writes write contains contain
function functions endpoint handler source file located defined please show tell
me can you no nó đó ấy gi gì nao nào nhung những dang đang goi gọi ham hàm xử xu lý ly
nam nằm o ở dau đâu toi tôi cho biet biết va và cua của trong tai tại""".split()
)


def question_identifiers(question: str) -> frozenset[str]:
    return frozenset(
        word.casefold()
        for word in re.findall(r"\b\w+\b", question)
        if len(word) > 1 and word.casefold() not in _PROSE_WORDS
    )


def asks_source_location(question: str) -> bool:
    question = re.sub(r"`[^`]*`|/\S+|\b\w+(?:[._]\w+)+\b", " ", question)
    return bool(
        re.search(
            r"\b(?:ở đâu|o dau|nằm đâu|nam dau|vị trí|vi tri|file nào|file nao|"
            r"where|source location|defined in|located in)\b",
            question,
            re.I,
        )
    )


def source_location_only(question: str, entity) -> bool:
    if not asks_source_location(question):
        return False
    names = " ".join(
        (
            entity.name,
            entity.qualified_name,
            str(dict(entity.attributes).get("path", "")),
            str(dict(entity.attributes).get("method", "")),
        )
    )
    identity = {word.casefold() for word in re.findall(r"\b\w+\b", names)}
    filler = _PROSE_WORDS | {
        "in",
        "at",
        "on",
        "found",
        "codebase",
        "repository",
        "repo",
        "implemented",
        "định",
        "nghĩa",
        "dinh",
        "nghia",
        "khai",
        "báo",
        "bao",
        "vị",
        "vi",
        "trí",
        "tri",
        "location",
        "definition",
        "implementation",
        "code",
        "ở",
        "o",
        "được",
        "duoc",
        "dòng",
        "dong",
        "line",
        "lines",
    }
    remaining = {word.casefold() for word in re.findall(r"\b\w+\b", question)}
    return not (remaining - identity - filler)


def mention_precedes_pronoun(question: str, names: set[str]) -> bool:
    """A topic named before 'it' differs from a callee named after 'it calls'."""
    pronoun = re.search(
        r"\b(?:it|its|this|that|nó|đó|ấy)\b|\bno\s+(?:nam|dang|goi|doc|ghi)\b",
        question,
        re.I,
    )
    if pronoun is None:
        return True
    return any(
        match.start() < pronoun.start()
        for name in names
        for match in re.finditer(
            r"(?<!\w)" + re.escape(name) + r"(?!\w)", question, re.I
        )
    )
