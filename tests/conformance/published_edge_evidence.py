"""Explicit AC-RKG-007 checks for suites that already emit edges."""

from __future__ import annotations

from rkg.domain.models import FactBatch


def assert_ac_rkg_007(facts: FactBatch) -> None:
    """Every edge shares the batch snapshot, has a rule id, and one evidence location."""
    evidence = {item.id: item for item in facts.evidence}
    assert facts.edges
    for edge in facts.edges:
        assert edge.snapshot_id == facts.snapshot_id
        assert edge.source_id
        assert edge.target_id
        assert edge.rule
        assert edge.evidence_ids
        located = [evidence[item_id] for item_id in edge.evidence_ids]
        assert any(
            item.snapshot_id == facts.snapshot_id
            and item.rule
            and item.file_path
            and "\\" not in item.file_path
            and not item.file_path.startswith("/")
            and item.start_line >= 1
            and item.end_line >= item.start_line
            for item in located
        )
