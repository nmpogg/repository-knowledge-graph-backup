"""Check the sibling pilot source selected for Task 22."""

import hashlib
import os
from pathlib import Path

import pytest

from rkg.adapters import (
    AdapterContext,
    AIOKafkaMessagingAdapter,
    FastAPIFrameworkAdapter,
    PythonLanguageAdapter,
    SQLAlchemyDataAccessAdapter,
)
from rkg.conversations import create_conversation, submit_grounded_turn
from rkg.domain import EdgeType, EntityType, SourceScanConfig, validate_fact_batch
from rkg.graph import build_context, search_entities
from rkg.ingestion import LocalSourcePolicy, build_manifest, resolve_local_source
from rkg.jobs import IndexCoordinator
from rkg.llm import MockProvider
from rkg.storage import Storage

DEFAULT_PILOT = Path(__file__).resolve().parents[3] / "pilot_fastapi"
EXPECTED_PILOT_SHA256 = (
    "a094fc7b39def8636e2b73766d80510c4f4b917ea1da5a6e93e22619ef237417"
)


def pilot_path() -> Path:
    configured = os.environ.get("RKG_PILOT_REPO")
    path = Path(configured).resolve() if configured else DEFAULT_PILOT
    if not path.is_dir():
        if configured:
            pytest.fail("configured pilot repository is unavailable")
        pytest.skip("sibling pilot repository is unavailable")
    return path


def pilot_digest(root: Path) -> str:
    ignored = {".git", ".venv", "__pycache__", ".pytest_cache"}
    files = sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and not any(part in ignored for part in path.relative_to(root).parts)
        and path.suffix not in {".db", ".pyc"}
    )
    digest = hashlib.sha256()
    for path in files:
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def domain_edges(facts, edge_type: EdgeType):
    evidence = {item.id: item for item in facts.evidence}
    return [
        edge
        for edge in facts.edges
        if edge.type == edge_type
        and any(
            evidence[item_id].file_path.startswith("pilot/domains/")
            for item_id in edge.evidence_ids
        )
    ]


def test_pilot_has_reviewable_edges_in_every_required_stratum() -> None:
    pilot = pilot_path()
    assert pilot_digest(pilot) == EXPECTED_PILOT_SHA256
    scan = SourceScanConfig(
        100,
        65536,
        ("*.py", "**/*.py"),
        (".venv/**", "**/__pycache__/**", ".pytest_cache/**"),
    )
    manifest = build_manifest(
        resolve_local_source("pilot-fastapi", pilot, LocalSourcePolicy((pilot,))),
        scan,
    )
    context = AdapterContext("pilot-fastapi", "pilot-snapshot", "pilot-job", scan)
    language = PythonLanguageAdapter()
    parsed = language.parse(manifest, scan)
    result = language.extract(context, parsed)
    result = language.resolve(context, parsed, result.facts)
    assert len(domain_edges(result.facts, EdgeType.IMPORTS)) >= 30
    assert len(domain_edges(result.facts, EdgeType.CALLS)) >= 30
    assert len(domain_edges(result.facts, EdgeType.IMPLEMENTS)) >= 10
    entities = {entity.id: entity for entity in result.facts.entities}
    config_edges = [
        edge
        for edge in domain_edges(result.facts, EdgeType.DEPENDS_ON)
        if entities[edge.target_id].type == EntityType.CONFIGURATION
    ]
    assert len(config_edges) >= 10

    for adapter in (
        FastAPIFrameworkAdapter("pilot.app:app"),
        SQLAlchemyDataAccessAdapter(),
        AIOKafkaMessagingAdapter(),
    ):
        result = adapter.extract(context, parsed, result.facts)
        validate_fact_batch(result.facts)

    entities = {entity.id: entity for entity in result.facts.entities}
    dependency_edges = [
        edge
        for edge in domain_edges(result.facts, EdgeType.DEPENDS_ON)
        if entities[edge.target_id].type == EntityType.CALLABLE
    ]
    assert len(dependency_edges) >= 30
    assert len(domain_edges(result.facts, EdgeType.MAPS_TO)) >= 10
    assert len(domain_edges(result.facts, EdgeType.READS)) >= 10
    assert len(domain_edges(result.facts, EdgeType.WRITES)) >= 10
    assert len(domain_edges(result.facts, EdgeType.PUBLISHES)) >= 10
    assert len(domain_edges(result.facts, EdgeType.CONSUMES)) >= 10


def test_grounded_retrieval_preserves_requested_pilot_relations(tmp_path: Path) -> None:
    pilot = pilot_path()
    assert pilot_digest(pilot) == EXPECTED_PILOT_SHA256
    with Storage(tmp_path / "pilot-qa.kuzu") as store:
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
        job = IndexCoordinator(store, LocalSourcePolicy((pilot,))).run(repository.id)
        assert job.status in {"succeeded", "succeeded_with_warnings"}
        snapshot = store.get_repository(repository.id).active_snapshot_id
        assert snapshot is not None
        for name, edge_type, question in (
            ("pilot.domains.delivery.read_delivery", "reads", "What does it read?"),
            (
                "pilot.domains.orders.publish_order",
                "publishes",
                "What does it publish?",
            ),
            (
                "pilot.domains.accounts.AccountCatalog",
                "implements",
                "What interface does it implement?",
            ),
        ):
            root = next(
                item
                for item in search_entities(
                    store, repository.id, snapshot, q=name, limit=100
                ).items
                if item.qualified_name == name
            )
            package = build_context(
                store,
                repository.id,
                snapshot,
                root.id,
                direction="outgoing",
                edge_types=(edge_type,),
                depth=1,
            )
            edge = next(item for item in package.edges if item.source_id == root.id)
            conversation = create_conversation(
                store, repository_id=repository.id, snapshot_id=snapshot
            )
            first = submit_grounded_turn(
                store,
                conversation.id,
                question=question,
                client_request_id=f"first-{edge_type}",
                expected_revision=1,
                root_id=root.id,
                provider=MockProvider(
                    [
                        {
                            "status": "answered",
                            "root_id": root.id,
                            "sections": [
                                {
                                    "relation": edge_type,
                                    "direction": "outgoing",
                                    "paths": [
                                        {
                                            "anchor_id": root.id,
                                            "edge_ids": [edge.id],
                                        }
                                    ],
                                }
                            ],
                        }
                    ]
                ),
            )
            assert first.submission.turn.status == "answered"
            assert not first.retrieval_truncated
            followup = submit_grounded_turn(
                store,
                conversation.id,
                question="What about it?",
                client_request_id=f"followup-{edge_type}",
                expected_revision=first.submission.conversation.revision,
                provider=MockProvider(
                    [
                        {
                            "status": "answered",
                            "root_id": root.id,
                            "sections": [
                                {
                                    "relation": edge_type,
                                    "direction": "outgoing",
                                    "paths": [
                                        {
                                            "anchor_id": root.id,
                                            "edge_ids": [edge.id],
                                        }
                                    ],
                                }
                            ],
                        }
                    ]
                ),
            )
            assert followup.submission.turn.status == "answered"
            assert not followup.retrieval_truncated
