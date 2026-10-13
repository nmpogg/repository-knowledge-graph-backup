"""In-process active-reader pin registry (single-worker MVP)."""

from __future__ import annotations

import threading
import uuid
from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReaderPin:
    """Opaque pin; release via ReaderRegistry.release or context manager."""

    pin_id: str
    repository_id: str
    snapshot_id: str


class ReaderRegistry:
    """Tracks request-scoped repository/snapshot readers in one process."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._pins: dict[str, ReaderPin] = {}
        self._by_snapshot: dict[str, set[str]] = defaultdict(set)
        self._by_repository: dict[str, set[str]] = defaultdict(set)

    def pin(self, repository_id: str, snapshot_id: str) -> ReaderPin:
        if not repository_id or not snapshot_id:
            raise ValueError("repository_id and snapshot_id are required")
        pin = ReaderPin(uuid.uuid4().hex, repository_id, snapshot_id)
        with self._lock:
            self._pins[pin.pin_id] = pin
            self._by_snapshot[snapshot_id].add(pin.pin_id)
            self._by_repository[repository_id].add(pin.pin_id)
        return pin

    def release(self, pin: ReaderPin) -> None:
        with self._lock:
            current = self._pins.pop(pin.pin_id, None)
            if current is None:
                return
            self._by_snapshot[current.snapshot_id].discard(pin.pin_id)
            if not self._by_snapshot[current.snapshot_id]:
                del self._by_snapshot[current.snapshot_id]
            self._by_repository[current.repository_id].discard(pin.pin_id)
            if not self._by_repository[current.repository_id]:
                del self._by_repository[current.repository_id]

    def has_snapshot_readers(self, snapshot_id: str) -> bool:
        with self._lock:
            return bool(self._by_snapshot.get(snapshot_id))

    def has_repository_readers(self, repository_id: str) -> bool:
        with self._lock:
            return bool(self._by_repository.get(repository_id))

    def clear(self) -> None:
        with self._lock:
            self._pins.clear()
            self._by_snapshot.clear()
            self._by_repository.clear()


class pinned_reader:
    """Context manager that pins a snapshot for the duration of a request."""

    def __init__(
        self, registry: ReaderRegistry, repository_id: str, snapshot_id: str
    ) -> None:
        self._registry = registry
        self._repository_id = repository_id
        self._snapshot_id = snapshot_id
        self._pin: ReaderPin | None = None

    def __enter__(self) -> ReaderPin:
        self._pin = self._registry.pin(self._repository_id, self._snapshot_id)
        return self._pin

    def __exit__(self, *exc: object) -> None:
        if self._pin is not None:
            self._registry.release(self._pin)
            self._pin = None
