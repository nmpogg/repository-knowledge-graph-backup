"""Assign manifest files to language adapters by declared file patterns.

Extension patterns (`*.py`, `**/*.java`) claim a suffix. Any other pattern
claims a basename (`pom.xml`, `requirements*.txt`). A basename match is
kept with the language that already owns at least one extension file, so a
build file alone does not open an assignment. Paths come from the manifest;
this module does not touch the filesystem.
"""

from __future__ import annotations

import fnmatch
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import PurePosixPath

from rkg.adapters.contracts import AdapterKind
from rkg.ingestion import ManifestFile


class LanguageExtensionConflict(RuntimeError):
    """Two language adapters claimed the same extension or basename pattern."""

    code = "language_extension_conflict"

    def __init__(self) -> None:
        super().__init__(self.code)


@dataclass(frozen=True, slots=True)
class LanguageAssignment:
    adapter: object
    files: tuple[ManifestFile, ...]


def _pattern_extension(pattern: str) -> str | None:
    name = PurePosixPath(pattern).name
    suffix = PurePosixPath(name).suffix
    if suffix and name == f"*{suffix}":
        return suffix
    return None


def _pattern_basename(pattern: str) -> str | None:
    if _pattern_extension(pattern) is not None:
        return None
    name = PurePosixPath(pattern).name
    if not name or name in {".", ".."}:
        return None
    return name


def _declared(adapter: object, *, basename: bool) -> tuple[str, ...]:
    values: list[str] = []
    for pattern in adapter.descriptor.file_patterns:
        value = _pattern_basename(pattern) if basename else _pattern_extension(pattern)
        if value and value not in values:
            values.append(value)
    return tuple(values)


def _claim(owners: dict[str, object], pattern: str, adapter: object) -> None:
    prior = owners.get(pattern)
    if prior is not None and prior is not adapter:
        raise LanguageExtensionConflict()
    owners[pattern] = adapter


def _basename_owner(name: str, owners: dict[str, object]) -> object | None:
    found: object | None = None
    for pattern, owner in owners.items():
        if not fnmatch.fnmatchcase(name, pattern):
            continue
        if found is not None and found is not owner:
            raise LanguageExtensionConflict()
        found = owner
    return found


def partition_language_files(
    files: Sequence[ManifestFile],
    adapters: Sequence[object],
) -> tuple[LanguageAssignment, ...]:
    """Return each language adapter with the manifest files its patterns claim.

    Ownership comes only from language-adapter descriptors. A file that matches
    no declared extension or basename is omitted. Basename matches are attached
    only when that adapter also owns an extension file. The same files and the
    same descriptors always produce the same groups. Registration order is not
    used.
    """
    seen: set[int] = set()
    language_adapters = []
    for adapter in sorted(
        (
            adapter
            for adapter in adapters
            if adapter.descriptor.kind == AdapterKind.LANGUAGE
        ),
        key=lambda adapter: (
            adapter.descriptor.adapter_id,
            adapter.descriptor.adapter_version,
        ),
    ):
        if id(adapter) in seen:
            continue
        seen.add(id(adapter))
        language_adapters.append(adapter)
    extensions: dict[str, object] = {}
    basenames: dict[str, object] = {}
    for adapter in language_adapters:
        for pattern in _declared(adapter, basename=False):
            _claim(extensions, pattern, adapter)
        for pattern in _declared(adapter, basename=True):
            _claim(basenames, pattern, adapter)

    grouped: dict[int, list[ManifestFile]] = {}
    with_source: set[int] = set()
    for item in sorted(files, key=lambda item: item.relative_path):
        path = PurePosixPath(item.relative_path)
        extension_owner = extensions.get(path.suffix)
        basename_owner = _basename_owner(path.name, basenames)
        if (
            extension_owner is not None
            and basename_owner is not None
            and extension_owner is not basename_owner
        ):
            raise LanguageExtensionConflict()
        owner = extension_owner or basename_owner
        if owner is None:
            continue
        grouped.setdefault(id(owner), []).append(item)
        if extension_owner is not None:
            with_source.add(id(owner))

    return tuple(
        LanguageAssignment(adapter, tuple(grouped.get(id(adapter), ())))
        for adapter in language_adapters
        if id(adapter) in with_source
    )
