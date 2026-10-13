"""Read a change-set document from YAML or legacy JSON text."""

from __future__ import annotations

from pathlib import Path

from tools.aide_yaml import parse_document


def load_change_set(path: Path) -> dict:
    document = parse_document(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError(f"{path} is not a change-set mapping")
    return document
