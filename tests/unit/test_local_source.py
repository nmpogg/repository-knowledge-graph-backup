"""Filesystem boundary and immutable manifest tests for T-003."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from rkg.domain import SourceScanConfig
from rkg.ingestion import (
    LocalSourcePolicy,
    SourceError,
    build_manifest,
    resolve_local_source,
)
from rkg.ingestion import local as local_module
from rkg.jobs import scan_config


def _source(root: Path, repo: Path, *, source_root: str | None = None):
    return resolve_local_source(
        "repo-1", repo, LocalSourcePolicy((root,)), source_root=source_root
    )


def test_safe_source_with_shell_metacharacters_is_data_only(tmp_path: Path) -> None:
    repo = tmp_path / "repo; $(do-not-run)"
    repo.mkdir()
    marker = tmp_path / "side-effect"
    program = repo / "main.py"
    program.write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\n",
        encoding="utf-8",
    )
    source = _source(tmp_path, repo)
    manifest = build_manifest(source, SourceScanConfig(10, 4096, ("*.py",)))
    assert [item.relative_path for item in manifest.files] == ["main.py"]
    assert manifest.files[0].content == program.read_bytes()
    assert not marker.exists()
    assert str(repo) not in repr(source)
    assert str(repo) not in repr(manifest)
    assert "write_text" not in repr(manifest)


def test_manifest_is_stable_and_keeps_original_bytes_after_source_changes(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    a = repo / "a.py"
    b = repo / "b.py"
    b.write_bytes(b"b = 1\n")
    a.write_bytes(b"a = 1\n")
    source = _source(tmp_path, repo)
    config = SourceScanConfig(10, 4096, ("*.py",))
    first = build_manifest(source, config)
    second = build_manifest(source, config)
    assert first == second
    assert [item.relative_path for item in first.files] == ["a.py", "b.py"]
    assert first.source_revision == f"manifest:{first.manifest_hash}"
    a.write_bytes(b"a = 2\n")
    b.unlink()
    third = build_manifest(source, config)
    assert first.files[0].content == b"a = 1\n"
    assert [item.relative_path for item in third.files] == ["a.py"]
    assert third.manifest_hash != first.manifest_hash


def test_loader_keeps_valid_and_invalid_syntax_for_adapter_diagnostics(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "good.py").write_text("value = 1\n", encoding="utf-8")
    (repo / "broken.py").write_text("def missing(:\n", encoding="utf-8")
    manifest = build_manifest(_source(tmp_path, repo), SourceScanConfig(2, 4096))
    assert [item.relative_path for item in manifest.files] == ["broken.py", "good.py"]
    assert manifest.skipped == ()


def test_missing_outside_and_source_root_errors_hide_host_path(tmp_path: Path) -> None:
    allowed = tmp_path / "allowed"
    outside = tmp_path / "outside"
    allowed.mkdir()
    outside.mkdir()
    policy = LocalSourcePolicy((allowed,))
    for path, code in (
        (allowed / "missing", "source_not_found"),
        (outside, "source_outside_allowed_roots"),
    ):
        with pytest.raises(SourceError) as caught:
            resolve_local_source("repo-1", path, policy)
        assert caught.value.code == code
        assert str(tmp_path) not in str(caught.value)
    with pytest.raises(SourceError, match="source_root_invalid"):
        resolve_local_source("repo-1", allowed, policy, source_root="../outside")
    with pytest.raises(SourceError, match="source_root_not_found"):
        resolve_local_source("repo-1", allowed, policy, source_root="missing")
    if os.name == "nt":
        with pytest.raises(SourceError, match="source_path_invalid"):
            resolve_local_source("repo-1", r"\\server\share\repo", policy)


def test_source_root_and_ignore_allow_lists(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    source_dir = repo / "src"
    cache = source_dir / "__pycache__"
    cache.mkdir(parents=True)
    (source_dir / "main.py").write_text("x = 1", encoding="utf-8")
    (source_dir / "notes.txt").write_text("notes", encoding="utf-8")
    (cache / "bad.py").write_text("ignored", encoding="utf-8")
    source = _source(tmp_path, repo, source_root="src")
    config = SourceScanConfig(1, 4096, ("**/*.py",), ("src/__pycache__/**",))
    manifest = build_manifest(source, config)
    assert [item.relative_path for item in manifest.files] == ["src/main.py"]
    assert manifest.considered_files == 1
    assert manifest.skipped == ()


def test_file_limit_is_fail_closed_and_large_file_is_skipped(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "a.py").write_bytes(b"small")
    (repo / "b.py").write_bytes(b"too-large")
    source = _source(tmp_path, repo)
    with pytest.raises(SourceError, match="file_limit_exceeded"):
        build_manifest(source, SourceScanConfig(1, 5, ("*.py",)))
    manifest = build_manifest(source, SourceScanConfig(2, 5, ("*.py",)))
    assert [item.relative_path for item in manifest.files] == ["a.py"]
    assert [(item.relative_path, item.code) for item in manifest.skipped] == [
        ("b.py", "file_too_large")
    ]
    assert manifest.warning_count == 1
    assert manifest.considered_files == 2


def test_oversized_file_is_not_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "large.py").write_bytes(b"x" * 100)
    source = _source(tmp_path, repo)

    def forbid_read(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("oversized file content was opened for reading")

    monkeypatch.setattr(local_module.os, "fdopen", forbid_read)
    manifest = build_manifest(source, SourceScanConfig(1, 10))
    assert manifest.files == ()
    assert manifest.skipped[0].code == "file_too_large"


def test_symlink_escape_is_rejected_without_reading_target(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    target = tmp_path / "target.py"
    target.write_text("secret", encoding="utf-8")
    link = repo / "link.py"
    try:
        os.symlink(target, link)
    except (OSError, NotImplementedError):
        pytest.skip("creating symlinks is not permitted on this host")
    source = _source(tmp_path, repo)
    with pytest.raises(SourceError, match="source_link_escape"):
        build_manifest(source, SourceScanConfig(10, 4096))


def test_open_handle_boundary_is_checked_before_content_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "main.py").write_text("safe", encoding="utf-8")
    source = _source(tmp_path, repo)
    monkeypatch.setattr(
        local_module, "_handle_path", lambda _fd: tmp_path / "outside.py"
    )
    with pytest.raises(SourceError, match="source_link_escape"):
        build_manifest(source, SourceScanConfig(10, 4096))


def test_link_escape_branch_is_checked_without_host_symlink_privilege(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    link = repo / "link.py"
    link.write_text("not read", encoding="utf-8")
    source = _source(tmp_path, repo)
    original_resolve = Path.resolve
    original_is_link = local_module._is_link

    def fake_resolve(path: Path, strict: bool = False) -> Path:
        if path == link:
            return tmp_path / "outside.py"
        return original_resolve(path, strict=strict)

    monkeypatch.setattr(Path, "resolve", fake_resolve)
    monkeypatch.setattr(
        local_module,
        "_is_link",
        lambda path, info: path == link or original_is_link(path, info),
    )
    with pytest.raises(SourceError, match="source_link_escape"):
        build_manifest(source, SourceScanConfig(10, 4096))


def test_bad_pattern_is_rejected(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    source = _source(tmp_path, repo)
    with pytest.raises(SourceError, match="source_pattern_invalid"):
        build_manifest(source, SourceScanConfig(10, 4096, ("../*.py",)))


@pytest.mark.parametrize("cache", [".cache", ".pytest_cache", ".ruff_cache"])
@pytest.mark.parametrize("prefix", ["", "nested"])
def test_default_scan_never_traverses_unreadable_caches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, cache: str, prefix: str
) -> None:
    repo = tmp_path / "repo"
    blocked = repo / prefix / cache
    blocked.mkdir(parents=True)
    (repo / "main.py").write_text("value = 1\n", encoding="utf-8")
    original = local_module.os.scandir

    def guarded_scandir(path):
        if Path(path) == blocked:
            raise PermissionError("cache is unreadable")
        return original(path)

    monkeypatch.setattr(local_module.os, "scandir", guarded_scandir)
    manifest = build_manifest(_source(tmp_path, repo), scan_config(None))
    assert [item.relative_path for item in manifest.files] == ["main.py"]
    assert manifest.considered_files == 1
