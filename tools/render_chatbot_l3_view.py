"""Render a source-pinned non-normative L3 review view from the active baseline."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def render():
    cs = (
        ROOT / ".aide/lifecycle/change-sets/CHG-RKG-2026-002/change-set.yaml"
    ).read_text()
    key = re.search(r"^baseline: ([\w-]+)$", cs, re.M)[1]
    baseline = json.loads(
        (
            ROOT / f".aide/lifecycle/change-sets/CHG-RKG-2026-002/baseline/{key}.yaml"
        ).read_text()
    )
    for pin in baseline["artifacts"]:
        path = ROOT / ".aide" / pin["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == pin["hash"], pin["key"]
    selected = [
        p
        for p in baseline["artifacts"]
        if p["role"] in {"contract_candidate", "contract_gate_policy"}
    ]
    metadata = {
        "key": "LCV-RKG-CHATBOT-001",
        "type": "contract-view",
        "group": "derived",
        "revision": 1,
        "non_normative": True,
        "hand_written": False,
        "derived_from": [key],
        "generator": "tools/render_chatbot_l3_view.py",
        "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "source_hashes": {p["key"]: p["hash"] for p in baseline["artifacts"]},
    }
    lines = [
        "---",
        json.dumps(metadata, ensure_ascii=False, indent=2),
        "---",
        "",
        "# LCV-RKG-CHATBOT-001 — Chatbot L3 contract candidate",
        "",
        "> Normative API/CON/schema/DDL/UIS artifacts win over this view.",
        "> Contract Gate is pending; this is not approval or implementation evidence.",
        "",
        "## Exact contract sources",
        "",
        "| Key | Revision | SHA-256 | Source |",
        "|---|---:|---|---|",
    ]
    for pin in selected:
        lines.append(
            f"| {pin['key']} | {pin['revision']} | `{pin['hash']}` "
            f"| `.aide/{pin['path']}` |"
        )
    for key, marker in [
        ("API-RKG-CORE-v1", "## Conversational usability L3 — CHG-RKG-2026-002"),
        (
            "TBL-RKG-GRAPH",
            "## Conversation metadata and pending intent — CHG-RKG-2026-002",
        ),
        ("UIS-RKG-001", "## Conversational usability binding — CHG-RKG-2026-002"),
    ]:
        pin = next(p for p in selected if p["key"] == key)
        text = (ROOT / ".aide" / pin["path"]).read_text()
        assert text.count(marker) == 1
        lines.extend(
            ["", f"## Source excerpt: {key}", "", text.split(marker, 1)[1].strip()]
        )
    output = ROOT / ".aide/generated/contract-views/LCV-RKG-CHATBOT-001.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(lines) + "\n"
    if output.exists():
        assert output.read_text() == content, "preserve old view; create a new revision"
    else:
        output.write_text(content)
    print("Rendered source-hashed L3 view; no review/approval inferred.")


if __name__ == "__main__":
    render()
