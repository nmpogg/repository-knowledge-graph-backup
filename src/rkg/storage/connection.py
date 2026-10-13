"""Embedded Kùzu connection façade owned by CMP-RKG-GRAPH."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import kuzu

from rkg.storage import conversations as conv_mod
from rkg.storage import jobs as jobs_mod
from rkg.storage import repositories as repo_mod
from rkg.storage import snapshots as snap_mod
from rkg.storage import turns as turns_mod
from rkg.storage.migrate import migrate, open_migrated_database
from rkg.storage.readers import ReaderRegistry, pinned_reader
from rkg.storage.records import (
    ConversationRecord,
    JobRecord,
    Page,
    RepositoryRecord,
    SnapshotRecord,
)


class Storage:
    """Single-process storage façade: migrate-on-open + catalog/job/conversation."""

    def __init__(
        self,
        path: Path | str,
        *,
        readers: ReaderRegistry | None = None,
    ) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._db, self._conn = open_migrated_database(self.path)
        self.readers = readers or ReaderRegistry()
        # Restart recovery: pending turns cannot lock a conversation forever.
        turns_mod.recover_pending_turns(self._conn)

    @property
    def conn(self) -> kuzu.Connection:
        return self._conn

    def close(self) -> None:
        self.readers.clear()
        conn = self._conn
        db = self._db
        self._conn = None  # type: ignore[assignment]
        self._db = None  # type: ignore[assignment]
        # Release the file lock so a later process can reopen the same database.
        if conn is not None:
            conn.close()
        if db is not None:
            db.close()

    def __enter__(self) -> Storage:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # --- repositories ---

    def create_repository(self, **kwargs: Any) -> RepositoryRecord:
        return repo_mod.create_repository(self._conn, **kwargs)

    def get_repository(self, repository_id: str) -> RepositoryRecord:
        return repo_mod.get_repository(self._conn, repository_id)

    def list_repositories(
        self, *, offset: int = 0, limit: int = 20, q: str | None = None
    ) -> Page:
        return repo_mod.list_repositories(
            self._conn, offset=offset, limit=limit, q=q
        )

    def update_repository(
        self, repository_id: str, *, expected_revision: int, **fields: Any
    ) -> RepositoryRecord:
        return repo_mod.update_repository(
            self._conn,
            repository_id,
            expected_revision=expected_revision,
            **fields,
        )

    def delete_repository(self, repository_id: str) -> None:
        return repo_mod.delete_repository(
            self._conn, repository_id, readers=self.readers
        )

    # --- snapshots ---

    def get_snapshot(self, repository_id: str, snapshot_id: str) -> SnapshotRecord:
        return snap_mod.get_snapshot(self._conn, repository_id, snapshot_id)

    def list_snapshots(
        self, repository_id: str, *, offset: int = 0, limit: int = 20
    ) -> Page:
        return snap_mod.list_snapshots(
            self._conn, repository_id, offset=offset, limit=limit
        )

    def activate_snapshot(
        self, repository_id: str, snapshot_id: str
    ) -> RepositoryRecord:
        snap_mod.activate_snapshot(self._conn, repository_id, snapshot_id)
        return self.get_repository(repository_id)

    def delete_snapshot(self, repository_id: str, snapshot_id: str) -> None:
        snap_mod.delete_snapshot(
            self._conn, repository_id, snapshot_id, readers=self.readers
        )

    # --- jobs ---

    def create_job(self, repository_id: str, **kwargs: Any) -> JobRecord:
        return jobs_mod.create_job(self._conn, repository_id, **kwargs)

    def get_job(self, job_id: str) -> JobRecord:
        return jobs_mod.get_job(self._conn, job_id)

    def update_job(self, job_id: str, **kwargs: Any) -> JobRecord:
        return jobs_mod.update_job(self._conn, job_id, **kwargs)

    # --- conversations ---

    def create_conversation(self, **kwargs: Any) -> ConversationRecord:
        return conv_mod.create_conversation(self._conn, **kwargs)

    def get_conversation(self, conversation_id: str) -> ConversationRecord:
        return conv_mod.get_conversation(self._conn, conversation_id)

    def list_conversations(self, **kwargs: Any) -> Page:
        return conv_mod.list_conversations(self._conn, **kwargs)

    def delete_conversation(self, conversation_id: str) -> None:
        return conv_mod.delete_conversation(self._conn, conversation_id)

    def cleanup_snapshots(self, repository_id: str) -> tuple[str, ...]:
        return snap_mod.cleanup_unreferenced_snapshots(
            self._conn, repository_id, readers=self.readers
        )

    def pin_reader(self, repository_id: str, snapshot_id: str) -> pinned_reader:
        # Ownership check before pin.
        self.get_snapshot(repository_id, snapshot_id)
        return pinned_reader(self.readers, repository_id, snapshot_id)


def open_storage(path: Path | str, **kwargs: Any) -> Storage:
    return Storage(path, **kwargs)


# Re-export migrate entry for tests/tooling.
__all__ = ["Storage", "migrate", "open_storage"]
