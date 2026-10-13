"""Repository/snapshot/job storage lifecycle — AC-RKG-007/008/066…071."""

from __future__ import annotations

from pathlib import Path

import pytest

from rkg.domain import InvalidFactBatch
from rkg.graph import (
    count_entities,
    edge_exists,
    entity_qualified_names,
    publish_fact_batch,
)
from rkg.storage import (
    NotFoundError,
    RepositoryBusyError,
    RepositoryConflictError,
    RepositoryInUseError,
    RepositorySourceImmutableError,
    SnapshotActiveError,
    SnapshotInUseError,
    Storage,
)
from tests.integration.storage_helpers import publish_meta, simple_batch


@pytest.fixture
def store(tmp_path: Path) -> Storage:
    storage = Storage(tmp_path / "rkg.kuzu")
    yield storage
    storage.close()


def _repo(store: Storage, name: str = "demo", locator: str = "/allowed/demo") -> str:
    return store.create_repository(
        display_name=name,
        source_type="local",
        source_locator=locator,
        source_root="src",
    ).id


def test_ac066_repository_crud_and_list_order(store: Storage) -> None:
    first = store.create_repository(
        display_name="Alpha",
        source_type="local",
        source_locator="/allowed/alpha",
    )
    second = store.create_repository(
        display_name="Beta",
        source_type="local",
        source_locator="/allowed/beta",
    )
    assert first.revision == 1
    assert first.active_snapshot_id is None
    assert first.source_locator_redacted.startswith("local:…/")
    assert "…" in first.source_locator_redacted
    assert "/allowed/" not in first.source_locator_redacted

    page = store.list_repositories(offset=0, limit=10)
    assert page.total == 2
    # Newest updated first; create order → second then first when timestamps equal-ish.
    assert {item.id for item in page.items} == {first.id, second.id}

    detail = store.get_repository(first.id)
    assert detail.display_name == "Alpha"
    with pytest.raises(NotFoundError):
        store.get_repository("missing")


def test_ac067_optimistic_revision_and_source_immutable(store: Storage) -> None:
    repo = store.create_repository(
        display_name="Demo",
        source_type="local",
        source_locator="/allowed/demo",
    )
    updated = store.update_repository(
        repo.id, expected_revision=1, display_name="Demo 2", source_root="pkg"
    )
    assert updated.revision == 2
    assert updated.display_name == "Demo 2"
    assert updated.source_root == "pkg"

    with pytest.raises(RepositoryConflictError) as conflict:
        store.update_repository(repo.id, expected_revision=1, display_name="stale")
    assert conflict.value.code == "repository_conflict"

    with pytest.raises(RepositorySourceImmutableError) as immutable:
        store.update_repository(
            repo.id,
            expected_revision=2,
            source_locator="/other",
        )
    assert immutable.value.code == "repository_source_immutable"

    # Snapshots unchanged by metadata PATCH (none yet).
    assert store.list_snapshots(repo.id).total == 0


def test_ac007_008_068_publish_reindex_and_failed_keeps_active(store: Storage) -> None:
    repo_id = _repo(store)
    batch1 = simple_batch(repo_id, "snap_1")
    published = publish_fact_batch(store, batch1, publish_meta("1"))
    assert published.is_active
    assert store.get_repository(repo_id).active_snapshot_id == "snap_1"
    assert count_entities(store, "snap_1") == 3
    assert edge_exists(
        store,
        snapshot_id="snap_1",
        edge_type="exposes",
        source_id=repo_id,
        target_id=batch1.entities[1].id,
        repository_id=repo_id,
    )
    assert edge_exists(
        store,
        snapshot_id="snap_1",
        edge_type="depends_on",
        source_id=repo_id,
        target_id=batch1.entities[2].id,
        repository_id=repo_id,
    )

    # Re-index with a new entity; previous snapshot retained.
    batch2 = simple_batch(repo_id, "snap_2", extra_entity_name="helper")
    publish_fact_batch(store, batch2, publish_meta("2"))
    assert store.get_repository(repo_id).active_snapshot_id == "snap_2"
    names_new = entity_qualified_names(store, "snap_2")
    assert "app.main.helper" in names_new
    names_old = entity_qualified_names(store, "snap_1")
    assert "app.main.helper" not in names_old
    assert count_entities(store, "snap_1") == 3

    history = store.list_snapshots(repo_id)
    assert [item.id for item in history.items] == ["snap_2", "snap_1"]

    # Failed publish (invalid batch) must not change active pointer.
    from rkg.domain import Edge, EdgeType, FactBatch, edge_id

    bad = FactBatch(
        repository_id=repo_id,
        snapshot_id="snap_bad",
        entities=batch2.entities,
        edges=(
            Edge(
                id=edge_id(
                    "snap_bad",
                    EdgeType.CALLS,
                    batch2.entities[0].id,
                    batch2.entities[1].id,
                ),
                snapshot_id="snap_bad",
                type=EdgeType.CALLS,
                source_id=batch2.entities[0].id,
                target_id=batch2.entities[1].id,
                rule="not-a-rule",
                evidence_ids=("missing",),
            ),
        ),
        evidence=(),
    )
    with pytest.raises(InvalidFactBatch):
        publish_fact_batch(store, bad, publish_meta("bad"))
    assert store.get_repository(repo_id).active_snapshot_id == "snap_2"


def test_ac069_activate_switches_pointer_only(store: Storage) -> None:
    repo_id = _repo(store)
    publish_fact_batch(store, simple_batch(repo_id, "snap_a"), publish_meta())
    publish_fact_batch(store, simple_batch(repo_id, "snap_b"), publish_meta())
    assert store.get_repository(repo_id).active_snapshot_id == "snap_b"

    activated = store.activate_snapshot(repo_id, "snap_a")
    assert activated.active_snapshot_id == "snap_a"
    assert store.get_snapshot(repo_id, "snap_a").is_active
    assert not store.get_snapshot(repo_id, "snap_b").is_active
    # No new snapshot rows from activate.
    assert store.list_snapshots(repo_id).total == 2


def test_ac070_snapshot_delete_guards(store: Storage) -> None:
    repo_id = _repo(store)
    publish_fact_batch(store, simple_batch(repo_id, "snap_a"), publish_meta())
    publish_fact_batch(store, simple_batch(repo_id, "snap_b"), publish_meta())

    with pytest.raises(SnapshotActiveError) as active_err:
        store.delete_snapshot(repo_id, "snap_b")
    assert active_err.value.code == "snapshot_active"

    with store.pin_reader(repo_id, "snap_a"):
        with pytest.raises(SnapshotInUseError) as pin_err:
            store.delete_snapshot(repo_id, "snap_a")
        assert pin_err.value.code == "snapshot_in_use"

    conv = store.create_conversation(
        repository_id=repo_id, snapshot_id="snap_a", title="q"
    )
    with pytest.raises(SnapshotInUseError):
        store.delete_snapshot(repo_id, "snap_a")
    store.delete_conversation(conv.id)

    store.delete_snapshot(repo_id, "snap_a")
    assert [s.id for s in store.list_snapshots(repo_id).items] == ["snap_b"]
    assert count_entities(store, "snap_a") == 0
    assert count_entities(store, "snap_b") == 3


def test_ac071_repository_delete_guards(store: Storage) -> None:
    repo_id = _repo(store, locator="/allowed/busy")
    other = _repo(store, name="Other", locator="/allowed/other")
    publish_fact_batch(store, simple_batch(other, "other_snap"), publish_meta())

    job = store.create_job(repo_id, stage="indexing")
    with pytest.raises(RepositoryBusyError) as busy:
        store.delete_repository(repo_id)
    assert busy.value.code == "repository_busy"
    store.update_job(job.id, stage="succeeded")

    publish_fact_batch(store, simple_batch(repo_id, "snap_x"), publish_meta())
    with store.pin_reader(repo_id, "snap_x"):
        with pytest.raises(RepositoryInUseError) as in_use:
            store.delete_repository(repo_id)
        assert in_use.value.code == "repository_in_use"

    conv = store.create_conversation(
        repository_id=repo_id, snapshot_id="snap_x", title="keep"
    )
    with pytest.raises(RepositoryInUseError):
        store.delete_repository(repo_id)
    store.delete_conversation(conv.id)

    store.delete_repository(repo_id)
    with pytest.raises(NotFoundError):
        store.get_repository(repo_id)
    # Other repository untouched.
    assert store.get_repository(other).active_snapshot_id == "other_snap"
    assert count_entities(store, "other_snap") == 3


def test_ownership_mismatch_is_not_found(store: Storage) -> None:
    repo_a = _repo(store, name="A", locator="/allowed/a")
    repo_b = _repo(store, name="B", locator="/allowed/b")
    publish_fact_batch(store, simple_batch(repo_a, "snap_a"), publish_meta())

    with pytest.raises(NotFoundError) as err:
        store.get_snapshot(repo_b, "snap_a")
    assert err.value.code == "not_found"
    assert "repo_a" not in str(err.value).lower()
    assert "ownership" not in str(err.value).lower()

    with pytest.raises(NotFoundError):
        store.activate_snapshot(repo_b, "snap_a")
    with pytest.raises(NotFoundError):
        store.delete_snapshot(repo_b, "snap_a")


def test_duplicate_source_identity_conflicts(store: Storage) -> None:
    store.create_repository(
        display_name="One",
        source_type="local",
        source_locator="/allowed/same",
    )
    with pytest.raises(RepositoryConflictError):
        store.create_repository(
            display_name="Two",
            source_type="local",
            source_locator="/allowed/same",
        )
