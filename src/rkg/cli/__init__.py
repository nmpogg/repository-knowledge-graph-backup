"""Local-first command line interface for repository and snapshot lifecycle."""

from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import uvicorn

from rkg.api import create_app
from rkg.ingestion import LocalSourcePolicy, SourceError, resolve_local_source
from rkg.jobs import (
    IndexCoordinator,
    IndexJobBusyError,
    recover_interrupted_jobs,
    scan_config,
)
from rkg.llm import LLMError
from rkg.storage.connection import Storage
from rkg.storage.errors import StorageError
from rkg.storage.records import RepositoryRecord
from rkg.terminal_logging import configure_terminal_logging

_LOCAL_ENV_KEYS = frozenset(
    {
        "RKG_SESSION_TOKEN",
        "RKG_DB_PATH",
        "RKG_LLM_PROVIDER",
        "OPENROUTER_API_KEY",
        "OPENROUTER_MODEL",
        "OPENAI_API_KEY",
        "OPENAI_MODEL",
    }
)


def _load_local_env() -> None:
    """Load supported server settings from the current directory's .env file."""
    env_file = Path.cwd() / ".env"
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding="utf-8-sig").splitlines():
        entry = line.strip()
        if not entry or entry.startswith("#") or "=" not in entry:
            continue
        key, value = entry.split("=", 1)
        key = key.strip()
        if key not in _LOCAL_ENV_KEYS:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(key, value)


def _repository(item: RepositoryRecord) -> dict[str, Any]:
    return {
        "repository_id": item.id,
        "revision": item.revision,
        "display_name": item.display_name,
        "source_type": item.source_type,
        "source_locator_redacted": item.source_locator_redacted,
        "source_root": item.source_root,
        "app_module": item.app_module,
        "app_symbol": item.app_symbol,
        "scan_defaults": item.scan_defaults,
        "active_snapshot_id": item.active_snapshot_id,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    }


def _snapshot(item: Any) -> dict[str, Any]:
    data = asdict(item)
    data["created_at"] = item.created_at.isoformat()
    return data


def _print(payload: Any) -> None:
    print(json.dumps(payload, sort_keys=True, ensure_ascii=False))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rkg")
    parser.add_argument("--db", default=os.environ.get("RKG_DB_PATH", ".rkg/graph"))
    parser.add_argument(
        "--allow-root",
        action="append",
        dest="roots",
        help="Operator-owned local source root (defaults to current directory)",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    repository = commands.add_parser("repository")
    repo_commands = repository.add_subparsers(dest="action", required=True)
    create = repo_commands.add_parser("create")
    create.add_argument("--name", required=True)
    create.add_argument("--path", required=True)
    create.add_argument("--source-root")
    create.add_argument("--app-module")
    create.add_argument("--app-symbol")
    create.add_argument("--max-files", type=int)
    create.add_argument("--max-file-bytes", type=int)
    listing = repo_commands.add_parser("list")
    listing.add_argument("--offset", type=int, default=0)
    listing.add_argument("--limit", type=int, default=20)
    listing.add_argument("--q")
    for name in ("show", "delete"):
        item = repo_commands.add_parser(name)
        item.add_argument("repository_id")
    update = repo_commands.add_parser("update")
    update.add_argument("repository_id")
    update.add_argument("--expected-revision", type=int, required=True)
    update.add_argument("--name")
    update.add_argument("--source-root")
    update.add_argument("--app-module")
    update.add_argument("--app-symbol")
    update.add_argument("--max-files", type=int)
    update.add_argument("--max-file-bytes", type=int)
    snapshot = commands.add_parser("snapshot")
    snap_commands = snapshot.add_subparsers(dest="action", required=True)
    for name in ("list", "show", "activate", "delete"):
        item = snap_commands.add_parser(name)
        item.add_argument("--repository", required=True)
        if name != "list":
            item.add_argument("snapshot_id")
        else:
            item.add_argument("--offset", type=int, default=0)
            item.add_argument("--limit", type=int, default=20)
    index = commands.add_parser("index")
    index.add_argument("--repository", required=True)
    serve = commands.add_parser("serve")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument("--workers", type=int, default=1)
    serve.add_argument("--log-level", choices=("info", "debug"), default="info")
    return parser


def _policy(args: argparse.Namespace) -> LocalSourcePolicy:
    return LocalSourcePolicy(tuple(Path(root) for root in (args.roots or [Path.cwd()])))


def _limits(
    args: argparse.Namespace, existing: dict[str, Any] | None = None
) -> dict[str, Any] | None:
    values = dict(existing or {})
    if args.max_files is not None:
        values["max_files"] = args.max_files
    if args.max_file_bytes is not None:
        values["max_file_bytes"] = args.max_file_bytes
    scan_config(values)
    return values or None


def _handle(storage: Storage, args: argparse.Namespace) -> int:
    if args.command == "repository":
        if args.action == "create":
            source = resolve_local_source(
                "registration", args.path, _policy(args), source_root=args.source_root
            )
            item = storage.create_repository(
                display_name=args.name,
                source_type="local",
                source_locator=str(source.canonical_root),
                source_root=args.source_root,
                app_module=args.app_module,
                app_symbol=args.app_symbol,
                scan_defaults=_limits(args),
            )
            _print(_repository(item))
        elif args.action == "list":
            page = storage.list_repositories(
                offset=args.offset, limit=args.limit, q=args.q
            )
            _print(
                {
                    "items": [_repository(item) for item in page.items],
                    "total": page.total,
                    "offset": page.offset,
                    "limit": page.limit,
                }
            )
        elif args.action == "show":
            _print(_repository(storage.get_repository(args.repository_id)))
        elif args.action == "update":
            current = storage.get_repository(args.repository_id)
            fields: dict[str, Any] = {}
            if args.name is not None:
                fields["display_name"] = args.name
            if args.source_root is not None:
                resolve_local_source(
                    current.id,
                    current.source_locator,
                    _policy(args),
                    source_root=args.source_root,
                )
                fields["source_root"] = args.source_root
            for name in ("app_module", "app_symbol"):
                if getattr(args, name) is not None:
                    fields[name] = getattr(args, name)
            if args.max_files is not None or args.max_file_bytes is not None:
                fields["scan_defaults"] = _limits(args, current.scan_defaults)
            _print(
                _repository(
                    storage.update_repository(
                        args.repository_id,
                        expected_revision=args.expected_revision,
                        **fields,
                    )
                )
            )
        else:
            storage.delete_repository(args.repository_id)
            _print({"deleted": True})
    elif args.command == "snapshot":
        repo_id = args.repository
        if args.action == "list":
            page = storage.list_snapshots(repo_id, offset=args.offset, limit=args.limit)
            _print(
                {
                    "items": [_snapshot(item) for item in page.items],
                    "total": page.total,
                    "offset": page.offset,
                    "limit": page.limit,
                }
            )
        elif args.action == "show":
            _print(_snapshot(storage.get_snapshot(repo_id, args.snapshot_id)))
        elif args.action == "activate":
            _print(_repository(storage.activate_snapshot(repo_id, args.snapshot_id)))
        else:
            storage.delete_snapshot(repo_id, args.snapshot_id)
            _print({"deleted": True})
    else:
        job = IndexCoordinator(storage, _policy(args)).run(args.repository)
        _print(
            {
                "job_id": job.id,
                "repository_id": job.repository_id,
                "status": job.status,
                "error_code": job.error_code,
                "report": job.report,
            }
        )
        return 0 if job.status in {"succeeded", "succeeded_with_warnings"} else 1
    return 0


def main(argv: list[str] | None = None) -> int:
    _load_local_env()
    args = _parser().parse_args(argv)
    try:
        if args.command == "serve":
            if (
                args.host != "127.0.0.1"
                or args.workers != 1
                or not 1 <= args.port <= 65535
            ):
                raise ValueError("serve_config_invalid")
            token = os.environ.get("RKG_SESSION_TOKEN")
            if token is not None and token == "":
                raise ValueError("serve_config_invalid")
            if not token:
                token = secrets.token_urlsafe(32)
            with Storage(args.db) as storage:
                recover_interrupted_jobs(storage)
                api = create_app(storage, _policy(args), session_token=token)
                configure_terminal_logging(args.log_level)
                uvicorn.run(
                    api,
                    host=args.host,
                    port=args.port,
                    log_level=args.log_level,
                )
            return 0
        with Storage(args.db) as storage:
            recover_interrupted_jobs(storage)
            return _handle(storage, args)
    except (StorageError, SourceError, IndexJobBusyError, LLMError) as exc:
        _print({"error_code": exc.code})
    except (ValueError, OSError) as exc:
        code = str(exc) if str(exc) == "serve_config_invalid" else "invalid_request"
        _print({"error_code": code})
    return 1


if __name__ == "__main__":
    sys.exit(main())
