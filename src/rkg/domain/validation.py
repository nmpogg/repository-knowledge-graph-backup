"""Pre-publication checks for generic FactBatch objects."""

from __future__ import annotations

import re
from math import isfinite
from pathlib import PurePosixPath

from rkg.domain.ids import edge_id, evidence_id, source_entity_id
from rkg.domain.models import EdgeType, EntityType, FactBatch

RULE_ID = re.compile(
    r"^RKG\.[A-Za-z][A-Za-z0-9_]*\.[A-Za-z][A-Za-z0-9_]*\.v[1-9][0-9]*$"
)
VALUE_LIKE_KEYS = {
    "value",
    "raw_value",
    "secret",
    "credential",
    "password",
    "token",
    "payload",
    "raw_source",
}
SENSITIVE_KEYS = VALUE_LIKE_KEYS - {"value", "raw_value"}


class InvalidFactBatch(ValueError):
    """Candidate graph cannot be published as a snapshot."""


def _json_scalar(value: object) -> bool:
    return isinstance(value, (str, int, float, bool, type(None))) and (
        not isinstance(value, float) or isfinite(value)
    )


def _relative_path(path: str) -> bool:
    pure = PurePosixPath(path)
    return (
        bool(path)
        and not pure.is_absolute()
        and not re.match(r"^[A-Za-z]:", path)
        and "\\" not in path
        and all(part not in (".", "..") for part in path.split("/"))
    )


def validate_fact_batch(
    batch: FactBatch, *, manifest_paths: frozenset[str] | None = None
) -> None:
    """Reject identity, ownership, evidence and data-minimization violations."""
    if not batch.repository_id or not batch.snapshot_id:
        raise InvalidFactBatch("repository and snapshot IDs are required")
    entities = {entity.id: entity for entity in batch.entities}
    evidence = {item.id: item for item in batch.evidence}
    descendants: dict[str, list[str]] = {}
    structural_parents: dict[str, int] = {}
    for entity in batch.entities:
        if entity.type == EntityType.SOURCE_UNIT and entity.file_path:
            for path in (
                PurePosixPath(entity.file_path),
                *PurePosixPath(entity.file_path).parents,
            ):
                descendants.setdefault(path.as_posix(), []).append(entity.file_path)
    for paths in descendants.values():
        paths.sort()
    if len(entities) != len(batch.entities) or len(evidence) != len(batch.evidence):
        raise InvalidFactBatch("duplicate entity or evidence ID")
    if len({edge.id for edge in batch.edges}) != len(batch.edges):
        raise InvalidFactBatch(
            "duplicate edge ID; aggregate evidence for repeated call sites"
        )
    for entity in batch.entities:
        if not entity.id or not entity.name or not entity.qualified_name:
            raise InvalidFactBatch("entity identity and names are required")
        if entity.id == batch.repository_id or not isinstance(entity.type, EntityType):
            raise InvalidFactBatch("entity ID/type is invalid")
        if (
            entity.repository_id != batch.repository_id
            or entity.snapshot_id != batch.snapshot_id
        ):
            raise InvalidFactBatch("entity belongs to another repository or snapshot")
        if entity.file_path is not None and not _relative_path(entity.file_path):
            raise InvalidFactBatch("entity file_path must be relative")
        if entity.type == EntityType.DIRECTORY:
            path = entity.file_path
            if (
                not path
                or path != entity.qualified_name
                or path.endswith("/")
                or "//" in path
                or entity.name != PurePosixPath(path).name
                or any(
                    value is not None
                    for value in (
                        entity.start_line,
                        entity.end_line,
                        entity.language_kind,
                        entity.framework_kind,
                    )
                )
                or entity.id
                != source_entity_id(
                    batch.repository_id, path, EntityType.DIRECTORY, path
                )
            ):
                raise InvalidFactBatch("directory identity or metadata is invalid")
        if entity.start_line is not None and entity.start_line < 1:
            raise InvalidFactBatch("entity start_line must be positive")
        if entity.end_line is not None and (
            entity.start_line is None or entity.end_line < entity.start_line
        ):
            raise InvalidFactBatch("entity line range is invalid")
        keys = [key for key, _ in entity.attributes]
        if len(set(keys)) != len(keys) or any(not key for key in keys):
            raise InvalidFactBatch("entity attributes need unique nonempty keys")
        if any(
            not (
                _json_scalar(value)
                or (
                    isinstance(value, tuple)
                    and all(_json_scalar(item) for item in value)
                )
            )
            for _, value in entity.attributes
        ):
            raise InvalidFactBatch("entity attributes must contain finite JSON values")
        if any(key.lower() in SENSITIVE_KEYS for key in keys):
            raise InvalidFactBatch(
                "source, payload and secret values cannot be graph attributes"
            )
        if entity.type == EntityType.CONFIGURATION and any(
            key.lower() in VALUE_LIKE_KEYS or key.lower().endswith("_value")
            for key in keys
        ):
            raise InvalidFactBatch("configuration values cannot be graph attributes")
    for item in batch.evidence:
        if item.snapshot_id != batch.snapshot_id:
            raise InvalidFactBatch("evidence belongs to another snapshot")
        if (
            not _relative_path(item.file_path)
            or item.start_line < 1
            or item.end_line < item.start_line
        ):
            raise InvalidFactBatch("evidence location is invalid")
        if not RULE_ID.fullmatch(item.rule):
            raise InvalidFactBatch("evidence rule must be versioned")
        expected_id = evidence_id(
            item.snapshot_id, item.file_path, item.start_line, item.end_line, item.rule
        )
        if item.id != expected_id:
            raise InvalidFactBatch("evidence ID does not match location/rule")
    for edge in batch.edges:
        if edge.snapshot_id != batch.snapshot_id:
            raise InvalidFactBatch("edge belongs to another snapshot")
        if edge.id != edge_id(
            edge.snapshot_id, edge.type, edge.source_id, edge.target_id
        ):
            raise InvalidFactBatch("edge ID does not match its endpoints")
        if not RULE_ID.fullmatch(edge.rule):
            raise InvalidFactBatch("edge rule must be versioned")
        if not edge.evidence_ids or len(set(edge.evidence_ids)) != len(
            edge.evidence_ids
        ):
            raise InvalidFactBatch("edge requires unique evidence locations")
        if any(item_id not in evidence for item_id in edge.evidence_ids):
            raise InvalidFactBatch("edge references missing evidence")
        if not any(
            evidence[item_id].rule == edge.rule for item_id in edge.evidence_ids
        ):
            raise InvalidFactBatch("edge rule has no matching evidence")
        if edge.type == EdgeType.EXPOSES and edge.source_id != batch.repository_id:
            raise InvalidFactBatch("exposes must start at this repository")
        if edge.source_id == batch.repository_id and edge.type not in (
            EdgeType.EXPOSES,
            EdgeType.DEPENDS_ON,
            EdgeType.CONTAINS,
        ):
            raise InvalidFactBatch("repository edge type is invalid")
        if edge.source_id != batch.repository_id and edge.source_id not in entities:
            raise InvalidFactBatch("edge source is missing from snapshot")
        if edge.target_id not in entities:
            raise InvalidFactBatch("edge target is missing from snapshot")
        if (
            edge.type == EdgeType.EXPOSES
            and entities[edge.target_id].type != EntityType.ENDPOINT
        ):
            raise InvalidFactBatch("exposes must target an Endpoint")
        source_type = (
            entities[edge.source_id].type if edge.source_id in entities else None
        )
        target_type = entities[edge.target_id].type
        structural = edge.rule == "RKG.structure.contains.v1"
        if (
            edge.type == EdgeType.CONTAINS
            and not structural
            and manifest_paths is not None
        ):
            legacy_pair = (
                source_type == EntityType.SOURCE_UNIT
                and target_type == EntityType.NAMESPACE
            )
            lexical_pair = source_type in (
                EntityType.SOURCE_UNIT,
                EntityType.NAMESPACE,
                EntityType.TYPE,
                EntityType.CALLABLE,
            ) and target_type in (EntityType.TYPE, EntityType.CALLABLE)
            if not legacy_pair and not lexical_pair:
                raise InvalidFactBatch("lexical containment endpoint types are invalid")
        if (
            structural
            or source_type == EntityType.DIRECTORY
            or (
                edge.source_id == batch.repository_id and edge.type == EdgeType.CONTAINS
            )
            or target_type == EntityType.DIRECTORY
        ):
            if (
                not structural
                or edge.type != EdgeType.CONTAINS
                or source_type not in (None, EntityType.DIRECTORY)
                or target_type not in (EntityType.DIRECTORY, EntityType.SOURCE_UNIT)
            ):
                raise InvalidFactBatch(
                    "filesystem structure endpoint types are invalid"
                )
            target = entities[edge.target_id]
            target_path = target.file_path or ""
            parent_path = entities[edge.source_id].file_path if source_type else "."
            if PurePosixPath(target_path).parent.as_posix() != parent_path:
                raise InvalidFactBatch(
                    "filesystem containment is not an immediate parent"
                )
            witnesses = descendants.get(target_path, [])
            if not witnesses:
                raise InvalidFactBatch("directory has no source unit descendant")
            structural_parents[edge.target_id] = (
                structural_parents.get(edge.target_id, 0) + 1
            )
            for ref_id in edge.evidence_ids:
                ref = evidence[ref_id]
                if (
                    ref.rule != edge.rule
                    or ref.file_path != witnesses[0]
                    or (ref.start_line, ref.end_line) != (1, 1)
                    or (
                        manifest_paths is not None
                        and ref.file_path not in manifest_paths
                    )
                ):
                    raise InvalidFactBatch(
                        "filesystem evidence is not manifest path provenance"
                    )
        required_pairs = {
            EdgeType.HANDLED_BY: (EntityType.ENDPOINT, EntityType.CALLABLE),
            EdgeType.CALLS: (EntityType.CALLABLE, EntityType.CALLABLE),
            EdgeType.IMPLEMENTS: (EntityType.TYPE, EntityType.TYPE),
            EdgeType.INHERITS_FROM: (EntityType.TYPE, EntityType.TYPE),
            EdgeType.MAPS_TO: (EntityType.TYPE, EntityType.DATA_RESOURCE),
            EdgeType.PUBLISHES: (EntityType.CALLABLE, EntityType.MESSAGE_CHANNEL),
            EdgeType.CONSUMES: (EntityType.CALLABLE, EntityType.MESSAGE_CHANNEL),
        }
        if edge.type in {EdgeType.READS, EdgeType.WRITES}:
            # Callable sites are preferred; Type sources allow aggregated
            # constructor/DI-owned repository access (Java/JPA profile).
            if target_type != EntityType.DATA_RESOURCE or source_type not in (
                EntityType.CALLABLE,
                EntityType.TYPE,
            ):
                raise InvalidFactBatch(
                    "edge endpoint types violate the semantic schema"
                )
        elif (
            edge.type in required_pairs
            and (source_type, target_type) != required_pairs[edge.type]
        ):
            raise InvalidFactBatch("edge endpoint types violate the semantic schema")
        if edge.type == EdgeType.IMPORTS and source_type not in (
            EntityType.SOURCE_UNIT,
            EntityType.NAMESPACE,
        ):
            raise InvalidFactBatch("imports must start at a source unit or namespace")
        if (
            edge.type == EdgeType.DEPENDS_ON
            and edge.source_id != batch.repository_id
            and source_type
            not in (
                EntityType.ENDPOINT,
                EntityType.CALLABLE,
                EntityType.SOURCE_UNIT,
                EntityType.TYPE,
            )
        ):
            raise InvalidFactBatch("depends_on source type is invalid")
    for entity in batch.entities:
        if entity.type == EntityType.DIRECTORY:
            if structural_parents.get(entity.id) != 1:
                raise InvalidFactBatch(
                    "directory must have exactly one structural parent"
                )
    for diagnostic in batch.diagnostics:
        if (
            diagnostic.snapshot_id is not None
            and diagnostic.snapshot_id != batch.snapshot_id
        ):
            raise InvalidFactBatch("diagnostic belongs to another snapshot")
        if diagnostic.file_path is not None and not _relative_path(
            diagnostic.file_path
        ):
            raise InvalidFactBatch("diagnostic file_path must be relative")
        if diagnostic.line is not None and diagnostic.line < 1:
            raise InvalidFactBatch("diagnostic line must be positive")


def validate_adapter_fact_batch(batch: FactBatch) -> None:
    """v2 adapters own semantic facts; core alone owns filesystem structure."""
    if any(
        e.type in (EntityType.DIRECTORY, EntityType.NAMESPACE) for e in batch.entities
    ):
        raise InvalidFactBatch("v2 adapters cannot emit Directory or Namespace")
    if any(e.rule == "RKG.structure.contains.v1" for e in batch.edges):
        raise InvalidFactBatch("filesystem containment is owned by core")
    validate_fact_batch(
        batch,
        manifest_paths=frozenset(
            e.file_path
            for e in batch.entities
            if e.type == EntityType.SOURCE_UNIT and e.file_path
        ),
    )
