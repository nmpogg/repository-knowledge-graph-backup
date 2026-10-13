"""Synthetic loopback API for the production Ask browser walkthrough.

No operator database, repository execution or external model is used.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from rkg.llm.provider import parse_response, prepare_call


class NarrativeFixtureProvider:
    enabled = True

    def __init__(self):
        self.calls = 0

    def complete(self, request, budget):
        tokens, _ = prepare_call(request, budget)
        self.calls += 1
        payload = json.loads(request.messages[-1]["content"])
        if request.schema_name == "rkg_read_plan_v2":
            raise AssertionError(
                "Walkthrough must resolve its explicit fixture subject locally"
            )
        root = payload["root_id"]
        facts = payload["facts"]
        bridge = next(
            (f for f in facts if f["source_id"] == root and f["type"] == "handled_by"),
            None,
        )
        anchor = bridge["target_id"] if bridge else root
        direction = payload["direction"]
        paths = []

        def visit(node, ids, seen):
            if len(ids) == 2:
                return
            for f in facts:
                if f["type"] != "calls":
                    continue
                source, target = (
                    (f["source_id"], f["target_id"])
                    if direction == "outgoing"
                    else (f["target_id"], f["source_id"])
                )
                if source != node or target in seen:
                    continue
                path = ids + [f["id"]] if direction == "outgoing" else [f["id"]] + ids
                paths.append({"anchor_id": anchor, "edge_ids": path})
                visit(target, path, seen | {target})

        visit(anchor, [], {anchor})
        value = {
            "status": "answered" if paths else "insufficient_evidence",
            "root_id": root,
            "sections": [{"relation": "calls", "direction": direction, "paths": paths}]
            if paths
            else [],
        }
        return parse_response(
            json.dumps(value),
            request,
            budget,
            input_tokens=tokens,
            model="synthetic-bounded",
        )


def serve(root: Path, port: int, descriptor: Path):
    from dataclasses import replace

    import uvicorn
    from tests.integration.graph_helpers import cycle_batch, publish_meta

    from rkg.api import create_app
    from rkg.domain import source_entity_id
    from rkg.graph import publish_fact_batch
    from rkg.graph.access import mark_snapshot_unavailable
    from rkg.ingestion import LocalSourcePolicy
    from rkg.storage import Storage

    with Storage(root / "browser.kuzu") as store:
        repository = store.create_repository(
            display_name="Synthetic browser",
            source_type="local",
            source_locator=str(root / "synthetic"),
        )
        repo, sid = repository.id, "snap-browser-synthetic"
        batch = cycle_batch(repo, sid)
        long_name = "synthetic." + "long_qualified_component_" * 12 + "Helper"
        entities = tuple(
            replace(
                e,
                id=source_entity_id(repo, e.file_path, e.type.value, long_name),
                qualified_name=long_name,
            )
            if e.type.value == "Type"
            else e
            for e in batch.entities
        )
        publish_fact_batch(store, replace(batch, entities=entities), publish_meta())
        provider = NarrativeFixtureProvider()
        app = create_app(
            store,
            LocalSourcePolicy((root,)),
            session_token="synthetic-browser-session",
            provider=provider,
        )

        @app.post("/__fixture/unavailable")
        def unavailable():
            mark_snapshot_unavailable(store, sid)
            return {"ok": True}

        @app.get("/__fixture/counts")
        def counts():
            return {"model_calls": provider.calls}

        descriptor.write_text(json.dumps({"repository_id": repo, "snapshot_id": sid}))
        uvicorn.run(
            app, host="127.0.0.1", port=port, access_log=False, log_level="critical"
        )


if __name__ == "__main__":
    serve(Path(sys.argv[1]), int(sys.argv[2]), Path(sys.argv[3]))
