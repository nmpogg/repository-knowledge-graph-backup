"""Opt-in, in-memory observation of the context actually used by a turn."""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field

from rkg.domain.models import ContextPackage, Entity


@dataclass
class RetrievalTrace:
    entities: dict[str, Entity] = field(default_factory=dict)
    contexts: list[ContextPackage] = field(default_factory=list)


_TRACE: ContextVar[RetrievalTrace | None] = ContextVar(
    "rkg_retrieval_trace", default=None
)


@contextmanager
def collect_retrieval() -> Iterator[RetrievalTrace]:
    trace = RetrievalTrace()
    token = _TRACE.set(trace)
    try:
        yield trace
    finally:
        _TRACE.reset(token)


def observe_entity(entity: Entity) -> None:
    trace = _TRACE.get()
    if trace is not None:
        trace.entities[entity.id] = entity


def observe_context(context: ContextPackage) -> None:
    trace = _TRACE.get()
    if trace is not None:
        trace.contexts.append(context)
        trace.entities.update((entity.id, entity) for entity in context.nodes)


def observation_enabled() -> bool:
    return _TRACE.get() is not None
