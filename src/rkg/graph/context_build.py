"""Compatibility shim — prefer ``from rkg.graph.context import build_context``."""

from rkg.graph.context import (
    CONTEXT_SCHEMA_VERSION,
    TRUNC_CHARS,
    TRUNC_DEPTH,
    TRUNC_EDGES,
    TRUNC_NODES,
    build_context,
)

__all__ = [
    "CONTEXT_SCHEMA_VERSION",
    "TRUNC_CHARS",
    "TRUNC_DEPTH",
    "TRUNC_EDGES",
    "TRUNC_NODES",
    "build_context",
]
