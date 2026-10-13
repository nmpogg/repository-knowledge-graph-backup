"""Conservative vi/en resolution; source identifiers never count as prose."""

from __future__ import annotations

import re

_GREETINGS = frozenset(
    {"alo", "xin chào", "xin chao", "chào", "chao", "hello", "hi", "hey"}
)
_IDENTIFIERS = re.compile(
    r"`[^`]*`|\b(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\b|/[^\s`]+|"
    r"\b\w+(?:[._]\w+)+\b",
    re.I,
)
_VI = re.compile(
    r"\b(?:gọi|đọc|ghi|hàm|nào|những|đang|tôi|chào|quan hệ|phụ thuộc|"
    r"goi|ham|nhung|dang|toi|chao|nao|giải thích|giai thich|"
    r"liệt kê|liet ke|mô tả|mo ta|ở đâu|o dau|nằm đâu|nam dau|"
    r"vị trí|vi tri|file nào|file nao|them|sua|doi|tao|bo sung)\b",
    re.I,
)
_EN = re.compile(
    r"\b(?:where\s+(?:is|are|does|do|can)|defined\s+(?:in|at)|"
    r"located\s+(?:in|at)|location of|list|functions?|invoked|describe|"
    r"explain|what|which|who|how|calls?|reads?|writes?|does|show|"
    r"hello|hi|hey|its|it|add|adding|modify|edit|change|update|fix|refactor)\b",
    re.I,
)


def normalize_locale(locale: object) -> str:
    if locale not in (None, "vi", "en") or not isinstance(locale, (str, type(None))):
        raise ValueError("invalid locale")
    return locale or "vi"


def is_greeting(text: str) -> bool:
    return text.strip().casefold().rstrip("!?., ").strip() in _GREETINGS


def effective_language(question: str, ui_locale: object = None) -> str:
    fallback = normalize_locale(ui_locale)
    prose = _IDENTIFIERS.sub(" ", question)
    if (
        _VI.search(prose)
        or re.search(r"[ăâđêôơưĂÂĐÊÔƠƯ\u1ea0-\u1ef9]", prose)
        or prose.strip().casefold() == "alo"
    ):
        return "vi"
    if _EN.search(prose):
        return "en"
    return fallback
