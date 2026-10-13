"""Synthetic legacy test descriptions projected into the current wire profiles.

This fixture builder is test-only. Runtime providers never accept old outputs.
New adversarial profile tests use rkg.llm.MockProvider directly.
"""

import json

from rkg.llm import MockProvider as WireProvider


class ProfileProvider:
    def __init__(self, descriptions):
        self._values = iter(descriptions)
        self.requests = []

    def complete(self, request, budget):
        value = dict(next(self._values))
        payload = json.loads(request.messages[-1]["content"])
        if request.schema_name == "rkg_read_plan_v2":
            value.update(entity_type="any", direction="outgoing", relation_types=[])
        if request.schema_name == "rkg_narrative_v1" and "edge_ids" in value:
            edge_ids = value.pop("edge_ids")
            root = payload["root_id"]
            facts = {e["id"]: e for e in payload["facts"]}
            connectors = [
                e
                for e in payload["facts"]
                if e["type"] == "handled_by" and e["source_id"] == root
            ]
            anchor = connectors[0]["target_id"] if connectors else root
            sections = []
            for edge_id in edge_ids:
                relation = facts.get(edge_id, {}).get("type", "calls")
                sections.append(
                    {
                        "relation": relation,
                        "direction": payload["direction"],
                        "paths": [{"anchor_id": anchor, "edge_ids": [edge_id]}],
                    }
                )
            value.update(root_id=root, sections=sections)
        self.requests.append(request)
        return WireProvider([value]).complete(request, budget)
