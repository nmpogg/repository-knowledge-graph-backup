"""Render selected chatbot requirement/design views from a pinned candidate.

This documentation tool does not review or approve artifacts. It never reads
runtime configuration, repository source under analysis, plans or diaries.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path


def render(root: Path) -> None:
    change_set = root / ".aide/lifecycle/change-sets/CHG-RKG-2026-002/change-set.yaml"
    baseline_match = re.search(r"^baseline: ([\w-]+)$", change_set.read_text(), re.M)
    if baseline_match is None:
        raise ValueError("Active candidate baseline is missing")
    baseline_name = baseline_match.group(1)
    baseline_path = (
        root / ".aide/lifecycle/change-sets/CHG-RKG-2026-002/baseline/"
        / f"{baseline_name}.yaml"
    )
    baseline = json.loads(baseline_path.read_text())
    revision_match = re.search(r"(-r\d+)$", baseline_name)
    if revision_match is None:
        raise ValueError("Baseline revision suffix is missing")
    suffix = "" if baseline_name.endswith("-r1") else revision_match.group(1)
    sources: dict[str, str] = {}
    for item in baseline["artifacts"]:
        data = (root / ".aide" / item["path"]).read_bytes()
        if hashlib.sha256(data).hexdigest() != item["hash"]:
            raise ValueError(f"Stale pinned artifact: {item['key']}")
        sources[item["key"]] = data.decode()

    generator_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

    def view(key: str, kind: str, body: str, directory: str) -> None:
        metadata = {
            "key": key,
            "type": kind,
            "group": "derived",
            "revision": 1,
            "non_normative": True,
            "hand_written": False,
            "derived_from": [baseline["key"]],
            "generator": "tools/render_chatbot_review.py",
            "generator_sha256": generator_hash,
            "source_hashes": {
                item["key"]: item["hash"] for item in baseline["artifacts"]
            },
        }
        target = root / ".aide/generated" / directory / f"{key}.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        content = "---\n" + json.dumps(metadata, ensure_ascii=False, indent=2)
        content += "\n---\n\n" + f"# {key} — Chatbot dễ hỏi và trả lời tự nhiên\n\n"
        content += (
            "> Khi view và artifact normative bất đồng, "
            "**artifact normative thắng**.\n\n"
        )
        content += (
            "> Candidate cho review; không phải approval "
            "hoặc bằng chứng triển khai.\n\n"
        )
        target.write_text(content + body)

    fr = sources["FR-RKG-005"]
    previous_fr = subprocess.check_output(
        [
            "git", "show",
            baseline["code_commit"] + ":.aide/requirements/fr/FR-RKG-005.md",
        ],
        cwd=root,
        text=True,
    )
    previous_ids = set(re.findall(r"^#### (AC-RKG-\d+)", previous_fr, re.M))
    ac_blocks = re.findall(
        r"^#### (AC-RKG-\d+)\n(.*?)(?=^#### |^### |\Z)", fr, re.M | re.S
    )
    delta = "\n".join(
        f"### {key}\n{body}" for key, body in ac_blocks if key not in previous_ids
    )
    csv = (
        "## Mục tiêu\n\n"
        + fr.split("## Mô tả\n", 1)[1].split("## Acceptance Criteria", 1)[0]
        + "## Mục tiêu nghiệp vụ đổi\n\n"
        "GOAL/KPI không đổi; mở rộng trải nghiệm grounded conversation hiện có.\n\n"
        "## Tính năng mới\n\n"
        + delta
        + "\n## Thay đổi hành vi hiện có\n\n"
        "AC hiện có giữ ID/nội dung. Thêm cách resolve endpoint, "
        "grouping direct/indirect, "
        "clarification giữ intent, locale/greeting, một answer và exact citation.\n\n"
        "## NGOÀI phạm vi lần này\n\n"
        "Các FR khác không đổi. Runtime implementation, analyzer/graph schema changes, "
        "raw-source access, streaming và release không thuộc lượt chốt nội dung.\n\n"
        "## Ràng buộc mới\n\n"
        "Không đổi NFR limits. NFR-RKG-SEC-001/REL-001/UX-001 giữ nguyên; "
        "ADR-2026-007 giới hạn narration bằng references và factual renderer.\n\n"
        "## Câu hỏi mở còn lại\n\n"
        "Không có OQ nghiệp vụ mới chưa giải quyết trong selected scope. "
        "Review độc lập, signer/gates, token-based mock/walkthrough và L3 persistence "
        "compatibility là readiness work còn lại; baseline vẫn candidate.\n"
    )
    view(
        "CSV-CHG-RKG-2026-002" + suffix,
        "change-set-view", csv, "change-set-views",
    )

    architecture = []
    for key in [
        "ADR-2026-007", "CMP-RKG-CONVERSATION", "CMP-RKG-WEB", "TM-RKG",
        "UXF-RKG-002", "SCR-RKG-001", "UID-RKG-001",
    ]:
        text = sources[key].split("---", 2)[2].strip()
        architecture.append(f"## Source: {key}\n\n" + text + "\n")
    view(
        "AVW-RKG-CHATBOT-002" + suffix, "architecture-view",
        "\n".join(architecture), "architecture-views",
    )
    print("Rendered two source-hashed candidate views; no gate approval inferred.")


if __name__ == "__main__":
    render(Path(__file__).resolve().parents[1])
