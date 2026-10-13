"""Language-independent filesystem structure over frozen source facts."""

from dataclasses import replace
from pathlib import PurePosixPath

from rkg.domain import (
    Edge,
    EdgeType,
    Entity,
    EntityType,
    Evidence,
    FactBatch,
    edge_id,
    evidence_id,
    source_entity_id,
)
from rkg.domain.validation import InvalidFactBatch, validate_fact_batch
from rkg.ingestion import SourceManifest

STRUCTURE_RULE = "RKG.structure.contains.v1"


def add_directory_structure(batch: FactBatch, manifest: SourceManifest) -> FactBatch:
    """Derive unique ancestors and path provenance without accessing source again."""
    if batch.repository_id != manifest.repository_id:
        raise InvalidFactBatch("manifest belongs to another repository")
    paths = frozenset(item.relative_path for item in manifest.files)
    units = sorted(
        (e for e in batch.entities if e.type == EntityType.SOURCE_UNIT),
        key=lambda e: (e.file_path or "", e.id),
    )
    directories: dict[str, Entity] = {}
    witnesses: dict[tuple[str, str], str] = {}
    for unit in units:
        if unit.file_path not in paths:
            raise InvalidFactBatch("source unit is not backed by the manifest")
        path = PurePosixPath(unit.file_path)
        parent_id = batch.repository_id
        for parent in reversed(path.parents):
            if parent == PurePosixPath("."):
                continue
            relative = parent.as_posix()
            directory = directories.setdefault(
                relative,
                Entity(
                    source_entity_id(
                        batch.repository_id, relative, EntityType.DIRECTORY, relative
                    ),
                    batch.repository_id,
                    batch.snapshot_id,
                    EntityType.DIRECTORY,
                    parent.name,
                    relative,
                    relative,
                ),
            )
            witnesses.setdefault((parent_id, directory.id), unit.file_path)
            parent_id = directory.id
        witnesses[(parent_id, unit.id)] = unit.file_path

    evidence = {e.id: e for e in batch.evidence}
    edges = {e.id: e for e in batch.edges}
    for (parent, child), path in sorted(witnesses.items()):
        ref = evidence_id(batch.snapshot_id, path, 1, 1, STRUCTURE_RULE)
        evidence[ref] = Evidence(ref, batch.snapshot_id, path, 1, 1, STRUCTURE_RULE)
        key = edge_id(batch.snapshot_id, EdgeType.CONTAINS, parent, child)
        edges[key] = Edge(
            key,
            batch.snapshot_id,
            EdgeType.CONTAINS,
            parent,
            child,
            STRUCTURE_RULE,
            (ref,),
        )
    result = replace(
        batch,
        entities=tuple(
            sorted((*batch.entities, *directories.values()), key=lambda e: e.id)
        ),
        edges=tuple(sorted(edges.values(), key=lambda e: e.id)),
        evidence=tuple(sorted(evidence.values(), key=lambda e: e.id)),
    )
    validate_fact_batch(result, manifest_paths=paths)
    return result
