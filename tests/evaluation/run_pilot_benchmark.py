"""Reproducible Task 22 local pilot benchmark; emits metrics without source text."""

from __future__ import annotations

import argparse
import ctypes
import importlib.metadata
import json
import os
import platform
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient
from tests.integration.test_pilot_corpus import EXPECTED_PILOT_SHA256, pilot_digest

from rkg.api import create_app
from rkg.graph import search_entities
from rkg.ingestion import LocalSourcePolicy
from rkg.jobs import IndexCoordinator
from rkg.storage import Storage


class MemoryStatus(ctypes.Structure):
    _fields_ = [
        ("length", ctypes.c_ulong),
        ("memory_load", ctypes.c_ulong),
        ("total_physical", ctypes.c_ulonglong),
        ("available_physical", ctypes.c_ulonglong),
        ("total_page_file", ctypes.c_ulonglong),
        ("available_page_file", ctypes.c_ulonglong),
        ("total_virtual", ctypes.c_ulonglong),
        ("available_virtual", ctypes.c_ulonglong),
        ("available_extended_virtual", ctypes.c_ulonglong),
    ]


class ProcessMemory(ctypes.Structure):
    _fields_ = [
        ("size", ctypes.c_ulong),
        ("page_faults", ctypes.c_ulong),
        ("peak_working_set", ctypes.c_size_t),
        ("working_set", ctypes.c_size_t),
        ("peak_paged_pool", ctypes.c_size_t),
        ("paged_pool", ctypes.c_size_t),
        ("peak_nonpaged_pool", ctypes.c_size_t),
        ("nonpaged_pool", ctypes.c_size_t),
        ("pagefile", ctypes.c_size_t),
        ("peak_pagefile", ctypes.c_size_t),
        ("private", ctypes.c_size_t),
    ]


def _memory() -> tuple[int | None, int | None]:
    if sys.platform != "win32":
        return None, None
    status = MemoryStatus()
    status.length = ctypes.sizeof(MemoryStatus)
    process = ProcessMemory()
    process.size = ctypes.sizeof(ProcessMemory)
    kernel = ctypes.windll.kernel32
    psapi = ctypes.windll.psapi
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    psapi.GetProcessMemoryInfo.argtypes = (
        ctypes.c_void_p,
        ctypes.POINTER(ProcessMemory),
        ctypes.c_ulong,
    )
    if not kernel.GlobalMemoryStatusEx(ctypes.byref(status)):
        return None, None
    if not psapi.GetProcessMemoryInfo(
        kernel.GetCurrentProcess(), ctypes.byref(process), process.size
    ):
        return int(status.total_physical), None
    return int(status.total_physical), int(process.peak_working_set)


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return round(ordered[94], 3)


def _measure(client: TestClient, method: str, url: str, **kwargs) -> list[float]:
    for _ in range(5):
        response = client.request(method, url, **kwargs)
        assert response.status_code == 200, response.status_code
    values = []
    for _ in range(100):
        start = time.perf_counter()
        response = client.request(method, url, **kwargs)
        values.append((time.perf_counter() - start) * 1000)
        assert response.status_code == 200, response.status_code
    return [round(item, 3) for item in values]


def run(pilot: Path, key: str) -> dict:
    assert pilot.is_dir(), "pilot repository unavailable"
    assert pilot_digest(pilot) == EXPECTED_PILOT_SHA256, "pilot digest changed"
    policy = LocalSourcePolicy((pilot,))
    physical, peak_before = _memory()
    with tempfile.TemporaryDirectory(prefix="rkg-t22-benchmark-") as folder:
        with Storage(Path(folder) / "graph") as store:
            repository = store.create_repository(
                display_name="pilot",
                source_type="local",
                source_locator=str(pilot),
                app_module="pilot.app",
                app_symbol="app",
                scan_defaults={
                    "include_patterns": ["*.py", "**/*.py", "pyproject.toml", "uv.lock"]
                },
            )
            job = IndexCoordinator(store, policy).run(repository.id)
            assert job.status in {"succeeded", "succeeded_with_warnings"}
            _, peak_after_scan = _memory()
            snapshot = store.get_repository(repository.id).active_snapshot_id
            assert snapshot is not None
            page = search_entities(
                store, repository.id, snapshot, q="pilot.domains.orders"
            )
            root = next(
                item
                for item in page.items
                if item.qualified_name == "pilot.domains.orders"
            )
            app = create_app(store, policy, session_token="benchmark-local")
            with TestClient(app, base_url="http://127.0.0.1") as client:
                params = {"repository_id": repository.id, "snapshot_id": snapshot}
                search = _measure(
                    client,
                    "GET",
                    "/api/v1/entities",
                    params=params | {"q": "orders", "limit": 100},
                )
                subgraph = _measure(
                    client,
                    "GET",
                    "/api/v1/subgraph",
                    params=params
                    | {
                        "root_id": root.id,
                        "direction": "both",
                        "depth": 6,
                        "max_nodes": 200,
                        "max_edges": 400,
                    },
                )
                context = _measure(
                    client,
                    "POST",
                    "/api/v1/context",
                    headers={"X-RKG-Session": "benchmark-local"},
                    json=params
                    | {
                        "root_id": root.id,
                        "direction": "both",
                        "depth": 6,
                        "max_nodes": 200,
                        "max_edges": 400,
                        "max_chars": 50000,
                    },
                )
            _, peak_after_queries = _memory()
            report = job.report or {}
            return {
                "key": key,
                "type": "test-evidence",
                "group": "evidence",
                "task_key": "TASK-RKG-022",
                "captured_at": datetime.now(UTC).isoformat(),
                "pilot_tree_sha256": EXPECTED_PILOT_SHA256,
                "source": {
                    "repository_id": repository.id,
                    "snapshot_id": snapshot,
                    "manifest_hash": job.manifest_hash,
                    "scan_config": {
                        "include_patterns": [
                            "*.py",
                            "**/*.py",
                            "pyproject.toml",
                            "uv.lock",
                        ]
                    },
                    "analyzer_version": "0.1.0",
                    "adapter_contract_version": "rkg.adapter/v1",
                    "semantic_schema_revision": 9,
                },
                "machine": {
                    "os": platform.system(),
                    "architecture": platform.machine(),
                    "cpu_logical": os.cpu_count(),
                    "physical_memory_gib": (
                        round(physical / 2**30, 2) if physical is not None else None
                    ),
                    "python": platform.python_version(),
                    "kuzu": importlib.metadata.version("kuzu"),
                },
                "scan": {
                    "status": job.status,
                    "duration_ms": report.get("duration_ms"),
                    "files": report.get("files"),
                    "entity_total": report.get("entity_total"),
                    "edge_total": report.get("edge_total"),
                    "diagnostics_by_code": report.get("diagnostics_by_code"),
                    "process_peak_working_set_mib": (
                        round(peak_after_scan / 2**20, 2) if peak_after_scan else None
                    ),
                    "process_peak_before_scan_mib": (
                        round(peak_before / 2**20, 2) if peak_before else None
                    ),
                },
                "query": {
                    "method": (
                        "in-process FastAPI TestClient, 5 warm-up, 100 sequential"
                    ),
                    "search_ms": search,
                    "search_p95_ms": _p95(search),
                    "subgraph_ms": subgraph,
                    "subgraph_p95_ms": _p95(subgraph),
                    "context_ms": context,
                    "context_p95_ms": _p95(context),
                    "process_peak_after_queries_mib": (
                        round(peak_after_queries / 2**20, 2)
                        if peak_after_queries
                        else None
                    ),
                    "context_limits": {
                        "depth": 6,
                        "max_nodes": 200,
                        "max_edges": 400,
                        "max_chars": 50000,
                    },
                },
            }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot", type=Path, default=Path("../pilot_fastapi"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--key", default="TEST-RKG-PERF-001")
    args = parser.parse_args()
    assert args.output.stem == args.key, "evidence key must match filename"
    result = run(args.pilot.resolve(), args.key)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "scan_ms": result["scan"]["duration_ms"],
                "search_p95_ms": result["query"]["search_p95_ms"],
                "subgraph_p95_ms": result["query"]["subgraph_p95_ms"],
                "context_p95_ms": result["query"]["context_p95_ms"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
