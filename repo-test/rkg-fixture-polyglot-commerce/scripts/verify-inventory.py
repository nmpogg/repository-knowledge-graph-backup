"""Validate source-pinned semantic inventory, not an RKG-generated oracle."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IGNORED = {
    "node_modules",
    "dist",
    "target",
    "coverage",
    ".venv",
    ".benchmark",
    "__pycache__",
}


def walk(value):
    if isinstance(value, dict):
        if "evidence" in value:
            for item in value["evidence"]:
                path = Path(item["path"])
                assert not path.is_absolute() and ".." not in path.parts, (
                    "unsafe_evidence_path"
                )
                file = ROOT / path
                assert file.is_file(), "missing_evidence_file"
                text = file.read_text()
                if "marker" in item:
                    assert text.count("RKG_EXPECT: " + item["marker"]) == 1, (
                        "missing_or_ambiguous_marker"
                    )
                if "line" in item:
                    assert 1 <= item["line"] <= len(text.splitlines()), "invalid_line"
        for child in value.values():
            walk(child)
    elif isinstance(value, list):
        for child in value:
            walk(child)


def verify():
    documents = {}
    for name in ["applications", "technologies", "entities", "edges", "diagnostics"]:
        path = ROOT / "expected" / f"{name}.yaml"
        document = json.loads(path.read_text())
        walk(document)
        documents[name] = document
        # Expected inventory excludes source bodies, host paths and RKG IDs.
        assert (
            "entity_id" not in path.read_text()
            and "snapshot_id" not in path.read_text()
        )
    apps = documents["applications"]["exact"]
    assert len(apps) == 4 and len({a["key"] for a in apps}) == 4
    for app in apps:
        directory = ROOT / app["root"]
        assert directory.is_dir()
        assert (directory / app["manifest"]).is_file()
        assert (directory / app["lock_or_checksum"]).is_file()
        assert (directory / app["entrypoint"]).is_file()
        assert (directory / "README.md").is_file()
    source_files = [
        p
        for p in ROOT.rglob("*")
        if p.is_file()
        and p.suffix in {".ts", ".tsx", ".java", ".go"}
        and not (set(p.relative_to(ROOT).parts) & IGNORED)
    ]
    assert 80 <= len(source_files) <= 150, "source_file_budget"
    keys = [e["key"] for e in documents["entities"]["adapter_local"]["exact"]]
    assert len(keys) == len(set(keys)), "duplicate_semantic_key"
    for edge in documents["edges"]["adapter_local"]["exact"]:
        assert edge["source"] in keys and edge["target"] in keys, "unknown_edge_key"
    assert not (ROOT / "package.json").exists(), "fake_root_package_manager"
    assert (ROOT / "analysis-cases/unsupported/schema.proto").is_file()
    print(
        f"Inventory validated: 4 applications, {len(source_files)} source files, "
        "source-backed semantic expectations."
    )


if __name__ == "__main__":
    verify()
