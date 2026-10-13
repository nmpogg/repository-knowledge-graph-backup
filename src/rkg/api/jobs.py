"""Background index submission that returns before the job finishes."""

from __future__ import annotations

import threading
from typing import Any

from rkg.ingestion import LocalSourcePolicy
from rkg.jobs import IndexCoordinator
from rkg.storage.connection import Storage
from rkg.storage.records import JobRecord

_MIRROR: dict[str, JobRecord] = {}
_MIRROR_LOCK = threading.Lock()


def remember(job: JobRecord) -> None:
    with _MIRROR_LOCK:
        _MIRROR[job.id] = job


def mirrored(job_id: str) -> JobRecord | None:
    with _MIRROR_LOCK:
        return _MIRROR.get(job_id)


def submit_index(
    storage: Storage,
    policy: LocalSourcePolicy,
    repository_id: str,
    *,
    app_module: str | None = None,
    app_symbol: str | None = None,
    scan_defaults: dict[str, Any] | None = None,
    workers: list[threading.Thread],
) -> JobRecord:
    """Start one job and return the accepted record while it is still running.

    Validation errors before a job row exists propagate to the caller. A second
    caller receives ``IndexJobBusyError`` while the writer lock is held.
    """
    outcome: dict[str, Any] = {}
    started = threading.Event()

    def accepted(job: JobRecord) -> None:
        remember(job)
        outcome["job"] = job
        started.set()

    def worker() -> None:
        try:
            final = IndexCoordinator(storage, policy).run(
                repository_id,
                on_accepted=accepted,
                app_module=app_module,
                app_symbol=app_symbol,
                scan_defaults=scan_defaults,
            )
            remember(final)
        except Exception as exc:
            outcome["error"] = exc
        finally:
            started.set()

    thread = threading.Thread(target=worker, name="rkg-index")
    workers.append(thread)
    thread.start()
    if not started.wait(60):
        raise TimeoutError("index_accept_timeout")
    if "job" not in outcome:
        raise outcome.get("error") or TimeoutError("index_accept_timeout")
    return outcome["job"]
