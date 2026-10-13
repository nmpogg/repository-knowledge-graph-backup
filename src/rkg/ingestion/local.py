"""Safe local repository discovery and immutable in-memory source manifest."""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import stat
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from rkg.domain import SourceScanConfig, scan_config_digest


class SourceError(ValueError):
    """Stable, path-free error suitable for translation into API/CLI responses."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class LocalSourcePolicy:
    """Server-owned allowed roots; never accept them from a request body."""

    allowed_local_roots: tuple[Path, ...] = field(repr=False)

    def __post_init__(self) -> None:
        if not self.allowed_local_roots:
            raise SourceError("source_config_invalid")


@dataclass(frozen=True, slots=True)
class LocalRepositorySource:
    repository_id: str
    canonical_root: Path = field(repr=False)
    scan_root: Path = field(repr=False)
    allowed_roots: tuple[Path, ...] = field(repr=False)


@dataclass(frozen=True, slots=True)
class ManifestFile:
    relative_path: str
    content_hash: str
    size_bytes: int
    content: bytes = field(repr=False)


@dataclass(frozen=True, slots=True)
class SkippedFile:
    relative_path: str
    code: str
    size_bytes: int | None = None
    modified_ns: int | None = None


@dataclass(frozen=True, slots=True)
class SourceManifest:
    repository_id: str
    files: tuple[ManifestFile, ...]
    skipped: tuple[SkippedFile, ...]
    manifest_hash: str
    scan_config_digest: str
    considered_files: int

    @property
    def source_revision(self) -> str:
        return f"manifest:{self.manifest_hash}"

    @property
    def warning_count(self) -> int:
        return len(self.skipped)


def _within(path: Path, parent: Path) -> bool:
    try:
        return os.path.commonpath(
            (os.path.normcase(path), os.path.normcase(parent))
        ) == os.path.normcase(parent)
    except ValueError:
        return False


def _is_unc(path: Path) -> bool:
    return os.name == "nt" and str(path).startswith("\\\\")


def _canonical_directory(path: Path, *, missing_code: str) -> Path:
    try:
        resolved = path.resolve(strict=True)
        if not resolved.is_dir():
            raise SourceError("source_not_directory")
        return resolved
    except (FileNotFoundError, NotADirectoryError):
        raise SourceError(missing_code) from None
    except (OSError, RuntimeError):
        raise SourceError("source_path_invalid") from None


def _relative_subroot(value: str | None) -> PurePosixPath:
    if value in (None, "", "."):
        return PurePosixPath(".")
    if (
        value.startswith("/")
        or "\\" in value
        or ":" in value
        or any(part in ("", ".", "..") for part in value.split("/"))
    ):
        raise SourceError("source_root_invalid")
    return PurePosixPath(value)


def resolve_local_source(
    repository_id: str,
    path: str | Path,
    policy: LocalSourcePolicy,
    *,
    source_root: str | None = None,
) -> LocalRepositorySource:
    """Canonicalize registration input without exposing a host path in errors."""
    if not repository_id or not str(path):
        raise SourceError("source_path_invalid")
    if _is_unc(Path(path)):
        raise SourceError("source_path_invalid")
    if any(_is_unc(Path(root)) for root in policy.allowed_local_roots):
        raise SourceError("source_config_invalid")
    roots = tuple(
        _canonical_directory(Path(root), missing_code="source_config_invalid")
        for root in policy.allowed_local_roots
    )
    root = _canonical_directory(Path(path), missing_code="source_not_found")
    if not any(_within(root, allowed) for allowed in roots):
        raise SourceError("source_outside_allowed_roots")
    subroot = _relative_subroot(source_root)
    scan_root_path = root.joinpath(*subroot.parts)
    scan_root = _canonical_directory(
        scan_root_path, missing_code="source_root_not_found"
    )
    if not _within(scan_root, root):
        raise SourceError("source_link_escape")
    return LocalRepositorySource(repository_id, root, scan_root, roots)


def _is_link(path: Path, file_stat: os.stat_result) -> bool:
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return (
        stat.S_ISLNK(file_stat.st_mode)
        or bool(getattr(file_stat, "st_file_attributes", 0) & reparse)
        or (hasattr(os.path, "isjunction") and os.path.isjunction(path))
    )


def _match(relative_path: str, pattern: str) -> bool:
    if pattern.startswith("**/") and _match(relative_path, pattern[3:]):
        return True
    if pattern.endswith("/**"):
        parent = pattern[:-3]
        if (
            fnmatch.fnmatchcase(relative_path, parent)
            or relative_path.startswith(parent + "/")
        ):
            return True
    return fnmatch.fnmatchcase(relative_path, pattern)


def _validate_patterns(config: SourceScanConfig) -> None:
    for pattern in (*config.include_patterns, *config.ignore_patterns):
        if (
            not pattern
            or pattern.startswith("/")
            or "\\" in pattern
            or ":" in pattern
            or any(part in ("", ".", "..") for part in pattern.split("/"))
        ):
            raise SourceError("source_pattern_invalid")


def _handle_path(fd: int) -> Path:
    """Resolve the opened object before reading, including Windows reparse races."""
    if os.name == "nt":
        import ctypes
        import msvcrt

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        get_path = kernel32.GetFinalPathNameByHandleW
        get_path.argtypes = [
            ctypes.c_void_p,
            ctypes.c_wchar_p,
            ctypes.c_uint32,
            ctypes.c_uint32,
        ]
        get_path.restype = ctypes.c_uint32
        handle = msvcrt.get_osfhandle(fd)
        needed = get_path(handle, None, 0, 0)
        if not needed:
            raise SourceError("source_read_error")
        buffer = ctypes.create_unicode_buffer(needed + 1)
        if not get_path(handle, buffer, len(buffer), 0):
            raise SourceError("source_read_error")
        name = buffer.value
        if name.startswith("\\\\?\\UNC\\"):
            name = "\\\\" + name[8:]
        elif name.startswith("\\\\?\\"):
            name = name[4:]
        return Path(name)
    proc_path = Path(f"/proc/self/fd/{fd}")
    if proc_path.exists():
        return Path(os.readlink(proc_path))
    # Never trust a pathname reopened after the handle was obtained.
    raise SourceError("source_read_error")


def _verify_entry_identity(path: Path, opened: os.stat_result) -> None:
    try:
        current = path.lstat()
    except OSError:
        raise SourceError("source_changed_during_scan") from None
    if _is_link(path, current) or (
        current.st_dev,
        current.st_ino,
    ) != (opened.st_dev, opened.st_ino):
        raise SourceError("source_changed_during_scan")


def _read_regular_file(
    path: Path, root: Path, max_bytes: int
) -> tuple[bytes | None, os.stat_result]:
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
    except OSError:
        raise SourceError("source_read_error") from None
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise SourceError("source_not_regular_file")
        actual = _handle_path(fd)
        if not _within(actual, root):
            raise SourceError("source_link_escape")
        _verify_entry_identity(path, before)
        if before.st_size > max_bytes:
            return None, before
        with os.fdopen(fd, "rb", closefd=False) as source_file:
            content = source_file.read(max_bytes + 1)
        after = os.fstat(fd)
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise SourceError("source_changed_during_scan")
        _verify_entry_identity(path, after)
        if len(content) > max_bytes:
            return None, after
        return content, after
    except OSError:
        raise SourceError("source_read_error") from None
    finally:
        os.close(fd)


def build_manifest(
    source: LocalRepositorySource, config: SourceScanConfig
) -> SourceManifest:
    """Collect selected files once; downstream adapters use these frozen bytes."""
    _validate_patterns(config)
    root = _canonical_directory(source.canonical_root, missing_code="source_not_found")
    if root != source.canonical_root:
        raise SourceError("source_changed_during_scan")
    if not any(_within(root, allowed) for allowed in source.allowed_roots):
        raise SourceError("source_outside_allowed_roots")
    scan_root = _canonical_directory(
        source.scan_root, missing_code="source_root_not_found"
    )
    if not _within(scan_root, root):
        raise SourceError("source_link_escape")
    if scan_root != source.scan_root:
        raise SourceError("source_changed_during_scan")

    found: list[ManifestFile] = []
    skipped: list[SkippedFile] = []
    considered = 0
    pending = [scan_root]
    while pending:
        directory = pending.pop()
        try:
            with os.scandir(directory) as iterator:
                entries = sorted(iterator, key=lambda entry: entry.name)
        except OSError:
            raise SourceError("source_scan_error") from None
        for entry in entries:
            path = Path(entry.path)
            relative = path.relative_to(root).as_posix()
            try:
                entry_stat = path.lstat()
            except OSError:
                raise SourceError("source_scan_error") from None
            if _is_link(path, entry_stat):
                try:
                    target = path.resolve(strict=True)
                except (OSError, RuntimeError):
                    skipped.append(SkippedFile(relative, "source_link_invalid"))
                    continue
                if not _within(target, root):
                    raise SourceError("source_link_escape")
                skipped.append(SkippedFile(relative, "source_link_skipped"))
                continue
            if any(_match(relative, pattern) for pattern in config.ignore_patterns):
                continue
            if stat.S_ISDIR(entry_stat.st_mode):
                pending.append(path)
                continue
            if not stat.S_ISREG(entry_stat.st_mode):
                skipped.append(SkippedFile(relative, "source_not_regular_file"))
                continue
            if config.include_patterns and not any(
                _match(relative, pattern) for pattern in config.include_patterns
            ):
                continue
            considered += 1
            if considered > config.max_files:
                raise SourceError("file_limit_exceeded")
            content, file_stat = _read_regular_file(path, root, config.max_file_bytes)
            if content is None:
                skipped.append(
                    SkippedFile(
                        relative,
                        "file_too_large",
                        file_stat.st_size,
                        file_stat.st_mtime_ns,
                    )
                )
            else:
                found.append(
                    ManifestFile(
                        relative,
                        hashlib.sha256(content).hexdigest(),
                        len(content),
                        content,
                    )
                )
    files = tuple(sorted(found, key=lambda item: item.relative_path))
    skips = tuple(sorted(skipped, key=lambda item: (item.relative_path, item.code)))
    payload = {
        "files": [
            (item.relative_path, item.content_hash, item.size_bytes) for item in files
        ],
        "skipped": [
            (item.relative_path, item.code, item.size_bytes, item.modified_ns)
            for item in skips
        ],
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return SourceManifest(
        source.repository_id,
        files,
        skips,
        hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        scan_config_digest(config),
        considered,
    )
