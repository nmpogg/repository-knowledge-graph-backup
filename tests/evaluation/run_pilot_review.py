"""Select reproducible Task 22 edge samples and cross-check source AST sites."""

from __future__ import annotations

import argparse
import ast
import json
import random
from collections import Counter
from pathlib import Path

from tests.integration.test_pilot_corpus import (
    DEFAULT_PILOT,
    EXPECTED_PILOT_SHA256,
    pilot_digest,
)

from rkg.adapters import (
    AdapterContext,
    AIOKafkaMessagingAdapter,
    FastAPIFrameworkAdapter,
    PythonLanguageAdapter,
    SQLAlchemyDataAccessAdapter,
)
from rkg.domain import EdgeType, EntityType, SourceScanConfig, validate_fact_batch
from rkg.ingestion import LocalSourcePolicy, build_manifest, resolve_local_source

SEED = 220026
THRESHOLDS = {
    "imports": 30,
    "calls": 30,
    "di": 30,
    "db_maps_to": 10,
    "db_reads": 10,
    "db_writes": 10,
    "event_publishes": 10,
    "event_consumes": 10,
    "config": 10,
    "implements": 10,
}
EDGE_TYPES = {
    "imports": EdgeType.IMPORTS,
    "calls": EdgeType.CALLS,
    "di": EdgeType.DEPENDS_ON,
    "db_maps_to": EdgeType.MAPS_TO,
    "db_reads": EdgeType.READS,
    "db_writes": EdgeType.WRITES,
    "event_publishes": EdgeType.PUBLISHES,
    "event_consumes": EdgeType.CONSUMES,
    "config": EdgeType.DEPENDS_ON,
    "implements": EdgeType.IMPLEMENTS,
}


def _facts(pilot: Path):
    scan = SourceScanConfig(
        100,
        65536,
        ("*.py", "**/*.py", "pyproject.toml", "uv.lock"),
        (".venv/**", "**/__pycache__/**", ".pytest_cache/**", ".git/**"),
    )
    manifest = build_manifest(
        resolve_local_source("pilot-fastapi", pilot, LocalSourcePolicy((pilot,))),
        scan,
    )
    context = AdapterContext("pilot-fastapi", "pilot-review", "pilot-review", scan)
    language = PythonLanguageAdapter()
    parsed = language.parse(manifest, scan)
    result = language.resolve(context, parsed, language.extract(context, parsed).facts)
    for adapter in (
        FastAPIFrameworkAdapter("pilot.app:app"),
        SQLAlchemyDataAccessAdapter(),
        AIOKafkaMessagingAdapter(),
    ):
        result = adapter.extract(context, parsed, result.facts)
        validate_fact_batch(result.facts)
    return result.facts


def _call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _matches_source(group: str, tree: ast.Module, line: int, target: str) -> bool:
    nodes = [node for node in ast.walk(tree) if getattr(node, "lineno", 0) == line]
    calls = [node for node in nodes if isinstance(node, ast.Call)]
    literals = {
        node.value
        for parent in nodes
        for node in ast.walk(parent)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    if group == "imports":
        return any(
            isinstance(node, ast.ImportFrom)
            and any(alias.name == target.rsplit(".", 1)[-1] for alias in node.names)
            for node in nodes
        )
    if group == "calls":
        return any(_call_name(call) == target.rsplit(".", 1)[-1] for call in calls)
    if group == "di":
        return any(
            _call_name(call) == "Depends"
            and any(
                isinstance(arg, ast.Name) and arg.id == target.rsplit(".", 1)[-1]
                for arg in call.args
            )
            for call in calls
        )
    if group == "db_maps_to":
        return any(
            isinstance(node, ast.Assign)
            and any(
                isinstance(item, ast.Name) and item.id == "__tablename__"
                for item in node.targets
            )
            for node in nodes
        ) and (target.split("::", 1)[-1] in literals)
    if group == "db_reads":
        return any(_call_name(call) == "select" for call in calls)
    if group == "db_writes":
        return any(_call_name(call) == "add" for call in calls)
    if group == "event_publishes":
        return any(
            _call_name(call) in {"send", "send_and_wait", "send_batch"}
            for call in calls
        ) and (target.split("::", 1)[-1] in literals)
    if group == "event_consumes":
        return target.split("::", 1)[-1] in literals
    if group == "config":
        return target.split(":", 1)[-1] in literals
    if group == "implements":
        return any(
            isinstance(node, ast.ClassDef)
            and any(
                isinstance(base, ast.Name) and base.id == target.rsplit(".", 1)[-1]
                for base in node.bases
            )
            for node in nodes
        )
    return False


def run(pilot: Path) -> dict:
    assert pilot_digest(pilot) == EXPECTED_PILOT_SHA256
    facts = _facts(pilot)
    entities = {item.id: item for item in facts.entities}
    evidence = {item.id: item for item in facts.evidence}
    trees: dict[str, ast.Module] = {}
    output = {}
    for group, threshold in THRESHOLDS.items():
        candidates = [
            edge
            for edge in facts.edges
            if edge.type == EDGE_TYPES[group]
            and any(
                evidence[item_id].file_path.startswith("pilot/domains/")
                for item_id in edge.evidence_ids
            )
            and (
                group not in {"di", "config"}
                or entities[edge.target_id].type
                == (EntityType.CALLABLE if group == "di" else EntityType.CONFIGURATION)
            )
        ]
        ordered = sorted(candidates, key=lambda item: item.id)
        sampled = random.Random(SEED).sample(ordered, min(threshold, len(ordered)))
        records = []
        for edge in sampled:
            sites = [
                evidence[item_id]
                for item_id in edge.evidence_ids
                if evidence[item_id].file_path.startswith("pilot/domains/")
            ]
            target = entities[edge.target_id].qualified_name
            verified = False
            for site in sites:
                if site.file_path not in trees:
                    trees[site.file_path] = ast.parse(
                        (pilot / site.file_path).read_text(encoding="utf-8")
                    )
                verified |= _matches_source(
                    group, trees[site.file_path], site.start_line, target
                )
            records.append(
                {
                    "edge_id": edge.id,
                    "source_entity": entities[edge.source_id].qualified_name,
                    "target_entity": target,
                    "rule": edge.rule,
                    "evidence": [
                        {"relative_path": site.file_path, "line": site.start_line}
                        for site in sites
                    ],
                    "source_ast_label": "TP" if verified else "unresolved",
                    "owner_adjudication": "pending",
                }
            )
        labels = Counter(item["source_ast_label"] for item in records)
        output[group] = {
            "population": len(ordered),
            "minimum": threshold,
            "sample_size": len(records),
            "source_ast_tp": labels["TP"],
            "source_ast_unresolved": labels["unresolved"],
            "owner_adjudication": "pending",
            "samples": records,
        }
    return {
        "key": "TEST-RKG-PILOT-REVIEW-001",
        "type": "test-evidence",
        "task_key": "TASK-RKG-022",
        "pilot_tree_sha256": EXPECTED_PILOT_SHA256,
        "seed": SEED,
        "sampling": "stable edge ID sort then seeded sample; census below threshold",
        "method": "independent source AST site cross-check; owner review pending",
        "groups": output,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot", type=Path, default=DEFAULT_PILOT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert args.output.stem == "TEST-RKG-PILOT-REVIEW-001"
    report = run(args.pilot.resolve())
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                name: [data["sample_size"], data["source_ast_tp"]]
                for name, data in report["groups"].items()
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
