"""Subset parser for artifact frontmatter and change-set documents.

Accepts a JSON object (legacy change-set.yaml) or the YAML mapping subset used
in `.aide/` (block maps, block lists, flow maps/lists, and plain scalars that
continue on the next indented line).
"""

from __future__ import annotations

import json
import re

_KEY = re.compile(r"^(?P<key>[A-Za-z0-9_-]+):(?:[ \t]*(?P<rest>.*))?$")


def parse_document(text: str):
    stripped = text.lstrip("\ufeff").lstrip()
    if stripped.startswith("{"):
        return json.loads(stripped)
    return _Parser(text).parse_map(0)


class _Parser:
    def __init__(self, text: str) -> None:
        self.lines = [
            line.replace("\t", "  ")
            for line in text.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.index = 0

    def parse_map(self, min_indent: int) -> dict:
        result: dict = {}
        while self.index < len(self.lines):
            line = self.lines[self.index]
            indent = _indent(line)
            if indent < min_indent or line.lstrip().startswith("- "):
                break
            if indent > min_indent:
                break
            matched = _KEY.match(line.lstrip())
            if matched is None:
                break
            self.index += 1
            result[matched.group("key")] = self._parse_value(
                indent, matched.group("rest") or ""
            )
        return result

    def _parse_value(self, key_indent: int, rest: str):
        rest = rest.strip()
        if rest:
            value = _parse_flow(rest)
            if not isinstance(value, str) or rest[0] in "[{\"'":
                return value
            continued = [value]
            while self.index < len(self.lines):
                nxt = self.lines[self.index]
                if _indent(nxt) <= key_indent or _starts_entry(nxt):
                    break
                continued.append(nxt.strip())
                self.index += 1
            return " ".join(continued)
        if self.index >= len(self.lines):
            return None
        nxt = self.lines[self.index]
        indent = _indent(nxt)
        stripped = nxt.lstrip()
        if stripped.startswith("- ") and indent >= key_indent:
            return self._parse_list(indent)
        if indent > key_indent:
            return self.parse_map(indent)
        return None

    def _parse_list(self, min_indent: int) -> list:
        items: list = []
        while self.index < len(self.lines):
            line = self.lines[self.index]
            indent = _indent(line)
            stripped = line.lstrip()
            if indent != min_indent or not stripped.startswith("- "):
                break
            payload = stripped[2:].strip()
            self.index += 1
            if payload == "":
                items.append(self.parse_map(min_indent + 2))
                continue
            matched = _KEY.match(payload)
            if matched and not payload.startswith(("[", "{", '"', "'")):
                child = {
                    matched.group("key"): self._parse_value(
                        indent, matched.group("rest") or ""
                    )
                }
                child.update(self.parse_map(indent + 2))
                items.append(child)
                continue
            items.append(_parse_flow(payload))
        return items


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _starts_entry(line: str) -> bool:
    stripped = line.lstrip()
    return stripped.startswith("- ") or _KEY.match(stripped) is not None


def _parse_flow(text: str):
    text = text.strip()
    if text.startswith("["):
        return _parse_flow_sequence(text)
    if text.startswith("{"):
        return _parse_flow_mapping(text)
    if text in {"", "null", "~", "Null", "NULL"}:
        return None
    if text in {"true", "True", "TRUE"}:
        return True
    if text in {"false", "False", "FALSE"}:
        return False
    if text.startswith(("'", '"')):
        return _unquote(text)
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    return text


def _parse_flow_sequence(text: str) -> list:
    inner = _unwrap(text, "[", "]")
    if inner.strip() == "":
        return []
    return [_parse_flow(part) for part in _split_flow(inner)]


def _parse_flow_mapping(text: str) -> dict:
    inner = _unwrap(text, "{", "}")
    if inner.strip() == "":
        return {}
    result = {}
    for part in _split_flow(inner):
        key, _, rest = part.partition(":")
        result[_unquote(key.strip()) if key.strip()[:1] in "\"'" else key.strip()] = (
            _parse_flow(rest)
        )
    return result


def _unwrap(text: str, open_ch: str, close_ch: str) -> str:
    if not (text.startswith(open_ch) and text.endswith(close_ch)):
        raise ValueError(f"expected {open_ch}{close_ch} flow node")
    return text[1:-1]


def _split_flow(text: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    quote = ""
    start = 0
    for index, char in enumerate(text):
        if quote:
            if char == quote and text[index - 1] != "\\":
                quote = ""
            continue
        if char in "\"'":
            quote = char
            continue
        if char in "[{":
            depth += 1
        elif char in "]}":
            depth -= 1
        elif char == "," and depth == 0:
            parts.append(text[start:index])
            start = index + 1
    parts.append(text[start:])
    return parts


def _unquote(text: str):
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        if text[0] == '"':
            return json.loads(text)
        return text[1:-1].replace("''", "'")
    return text
