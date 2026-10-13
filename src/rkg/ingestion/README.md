# Local source loader handoff (T-003)

`resolve_local_source(repository_id, path, policy, source_root=...)` validates a
local directory against server-owned `allowed_local_roots`. It returns an internal
`LocalRepositorySource`; its absolute paths are deliberately omitted from `repr`.
`build_manifest(source, SourceScanConfig(...))` discovers selected regular files,
checks links and read handles, and returns a frozen `SourceManifest`.
Windows UNC/device paths are rejected before filesystem resolution so the loader
does not access a network share through a local-source request.

`ManifestFile.content` holds immutable bytes in memory for later adapters. It is
excluded from `repr` and must never be put into graph facts, logs, API responses or
evidence artifacts. Adapters should consume these bytes; rereading by path would
break the manifest's consistency guarantee. No source is imported or executed.

Paths in the manifest, skipped-file records and diagnostics are repository-relative
POSIX paths. Include/ignore patterns match those paths; `**/` can also match a
top-level file, and a pattern ending `/**` excludes the directory itself. The
loader skips in-root symlinks/junctions to avoid cycles/duplicates, and rejects
links that escape the canonical repository root before reading content. Windows
uses the opened handle's final path; Linux uses `/proc/self/fd`. Other platforms
fail closed until a handle-path implementation is supplied.

The selected file count includes oversized files. Exceeding `max_files` raises
`file_limit_exceeded`; a file above `max_file_bytes` is omitted and recorded as a
`file_too_large` skip. The manifest hash covers selected content hashes and skip
metadata; `source_revision` is `manifest:<sha256>`. Effective scan options have a
separate `scan_config_digest` from T-002.

`SourceError.code` is safe to map to a transport/CLI error. Messages contain only
the code, never an absolute host path. The loader does not decide job status,
publish snapshots, parse syntax, or assemble the full scan report; T-005/T-015/T-016
own those steps. Parse errors should become per-file diagnostics while valid files
remain available in this manifest.
