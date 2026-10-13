"""Conversation persistence — AC-RKG-030/031/033/044/045/059/064."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from rkg.conversations import (
    ConversationBusyError,
    ConversationConflictError,
    InvalidTurnRequestError,
    ProviderResult,
    SnapshotUnavailableError,
    begin_turn,
    cleanup_snapshots,
    create_conversation,
    delete_conversation,
    deterministic_turn_id,
    list_turns,
    read_conversation,
    submit_turn,
)
from rkg.graph import count_entities, get_entity, publish_fact_batch, search_entities
from rkg.graph.access import mark_snapshot_unavailable
from rkg.storage import NotFoundError, SnapshotActiveError, Storage
from tests.integration.storage_helpers import publish_meta, simple_batch

QUESTION = "QUESTION-MARKER API này ghi vào bảng nào?"
ANSWER = "ANSWER-MARKER vào bảng orders"


@pytest.fixture
def store(tmp_path: Path) -> Storage:
    storage = Storage(tmp_path / "rkg.kuzu")
    yield storage
    storage.close()


def _repo(store: Storage, name: str = "demo", locator: str = "/allowed/demo") -> str:
    created = store.create_repository(
        display_name=name,
        source_type="local",
        source_locator=locator,
    )
    return created.id


def _publish(store: Storage, repository_id: str, snapshot_id: str) -> str:
    publish_fact_batch(
        store, simple_batch(repository_id, snapshot_id), publish_meta()
    )
    page = search_entities(store, repository_id, snapshot_id, q="get_health")
    assert page.total >= 1
    return str(page.items[0].id)


def _answer(focus: str, *, snapshot_id: str) -> ProviderResult:
    return ProviderResult(
        status="answered",
        answer=ANSWER,
        resolved_question=QUESTION,
        claims=({"text": "writes orders"},),
        citations=(
            {"entity_id": focus, "snapshot_id": snapshot_id, "quote": "orders"},
        ),
        focus_entity_id=focus,
        usage={"output_tokens": 12, "prompt": ANSWER},
    )


def _stored_text(store: Storage, conversation_id: str) -> str:
    row = store.get_conversation(conversation_id)
    parts = [row.title, str(row.state)]
    for turn in list_turns(store, conversation_id):
        parts.extend(
            [
                turn.question,
                turn.answer or "",
                turn.resolved_question or "",
                turn.error_code or "",
                str(turn.claims),
                str(turn.citations),
                str(turn.usage),
            ]
        )
    return "\n".join(parts)


def test_ac030_history_survives_restart_and_focus_is_isolated(
    tmp_path: Path,
) -> None:
    path = tmp_path / "restart.kuzu"
    store = Storage(path)
    repo = _repo(store)
    entity_id = _publish(store, repo, "snap_a")
    other_entity = _publish(store, repo, "snap_b")
    first = create_conversation(
        store, repository_id=repo, snapshot_id="snap_a", title="one"
    )
    second = create_conversation(
        store, repository_id=repo, snapshot_id="snap_b", title="two"
    )
    left = submit_turn(
        store,
        first.id,
        question="focus left",
        client_request_id="left-1",
        expected_revision=1,
        provider=lambda _ctx: _answer(entity_id, snapshot_id="snap_a"),
    )
    right = submit_turn(
        store,
        second.id,
        question="focus right",
        client_request_id="left-1",
        expected_revision=1,
        provider=lambda _ctx: _answer(other_entity, snapshot_id="snap_b"),
    )
    assert left.turn.id != right.turn.id
    assert left.turn.id == deterministic_turn_id(first.id, "left-1")
    store.close()

    reopened = Storage(path)
    try:
        kept_right = reopened.get_conversation(second.id)
        assert reopened.get_conversation(first.id).state["focus_entity_id"] == entity_id
        assert kept_right.state["focus_entity_id"] == other_entity
        assert [turn.status for turn in list_turns(reopened, first.id)] == ["answered"]
        delete_conversation(reopened, first.id)
        assert reopened.get_conversation(second.id).state == kept_right.state
        assert list_turns(reopened, second.id)[0].question == "focus right"
        with pytest.raises(NotFoundError):
            reopened.get_conversation(first.id)
    finally:
        reopened.close()


def test_ac031_old_conversation_stays_pinned_when_active_moves(store: Storage) -> None:
    repo = _repo(store)
    entity_id = _publish(store, repo, "snap_old")
    pinned = create_conversation(store, repository_id=repo, title="pinned")
    assert pinned.snapshot_id == "snap_old"
    done = submit_turn(
        store,
        pinned.id,
        question="citation check",
        client_request_id="pin-1",
        expected_revision=1,
        provider=lambda _ctx: _answer(entity_id, snapshot_id="snap_old"),
    )
    assert done.turn.citations[0]["snapshot_id"] == "snap_old"
    _publish(store, repo, "snap_new")
    assert store.get_repository(repo).active_snapshot_id == "snap_new"
    fresh = create_conversation(store, repository_id=repo, title="fresh")
    assert fresh.snapshot_id == "snap_new"
    still = read_conversation(store, pinned.id)
    assert still.conversation.snapshot_id == "snap_old"
    cited = get_entity(store, repo, still.conversation.snapshot_id, entity_id)
    assert cited.id == entity_id

    calls = {"n": 0}

    def _provider(ctx):
        calls["n"] += 1
        assert ctx.snapshot_id == "snap_old"
        return ProviderResult(
            status="answered",
            answer="still old",
            citations=({"entity_id": entity_id, "snapshot_id": "snap_new"},),
        )

    follow = submit_turn(
        store,
        pinned.id,
        question="follow up",
        client_request_id="pin-2",
        expected_revision=still.conversation.revision,
        provider=_provider,
    )
    assert calls["n"] == 1
    assert follow.conversation.snapshot_id == "snap_old"
    assert follow.turn.citations == []


def test_ac033_conflict_idempotency_recovery_and_failed_focus(
    tmp_path: Path,
) -> None:
    path = tmp_path / "guard.kuzu"
    store = Storage(path)
    repo = _repo(store)
    entity_id = _publish(store, repo, "snap_a")
    conversation = create_conversation(
        store, repository_id=repo, snapshot_id="snap_a", title="guard"
    )
    calls = {"n": 0}

    def _provider(_ctx: object) -> ProviderResult:
        calls["n"] += 1
        return _answer(entity_id, snapshot_id="snap_a")

    first = submit_turn(
        store,
        conversation.id,
        question="same body",
        client_request_id="req-1",
        expected_revision=1,
        provider=_provider,
    )
    replay = submit_turn(
        store,
        conversation.id,
        question="same body",
        client_request_id="req-1",
        expected_revision=1,
        provider=_provider,
    )
    assert calls["n"] == 1
    assert replay.turn.id == first.turn.id
    assert replay.created is False
    assert len(list_turns(store, conversation.id)) == 1
    assert first.conversation.state["focus_entity_id"] == entity_id

    with pytest.raises(ConversationConflictError) as conflict:
        submit_turn(
            store,
            conversation.id,
            question="different body",
            client_request_id="req-1",
            expected_revision=first.conversation.revision,
            provider=_provider,
        )
    assert conflict.value.code == "conversation_conflict"
    assert calls["n"] == 1

    with pytest.raises(ConversationConflictError) as stale:
        submit_turn(
            store,
            conversation.id,
            question="other tab",
            client_request_id="req-2",
            expected_revision=1,
            provider=_provider,
        )
    assert stale.value.code == "conversation_conflict"
    assert calls["n"] == 1
    assert len(list_turns(store, conversation.id)) == 1

    pending = begin_turn(
        store,
        conversation.id,
        question="in flight",
        client_request_id="req-3",
        expected_revision=first.conversation.revision,
    )
    assert pending.turn.status == "pending"
    with pytest.raises(ConversationBusyError) as busy:
        begin_turn(
            store,
            conversation.id,
            question="second tab",
            client_request_id="req-4",
            expected_revision=pending.conversation.revision,
        )
    assert busy.value.code == "conversation_busy"
    focus_before = pending.conversation.state["focus_entity_id"]
    store.close()

    reopened = Storage(path)
    try:
        statuses = [turn.status for turn in list_turns(reopened, conversation.id)]
        assert "pending" not in statuses
        assert "interrupted" in statuses
        kept = reopened.get_conversation(conversation.id)
        assert kept.state["focus_entity_id"] == focus_before
        failed_calls = {"n": 0}

        def _boom(_ctx: object) -> ProviderResult:
            failed_calls["n"] += 1
            raise RuntimeError("password=s3cr3t-value from provider")

        failed = submit_turn(
            reopened,
            conversation.id,
            question="provider down",
            client_request_id="req-5",
            expected_revision=kept.revision,
            provider=_boom,
        )
        assert failed_calls["n"] == 1
        assert failed.turn.status == "failed"
        assert failed.turn.error_code == "provider_failed"
        assert failed.conversation.state["focus_entity_id"] == focus_before
        assert "s3cr3t-value" not in _stored_text(reopened, conversation.id)
    finally:
        reopened.close()


def test_ac044_cleanup_keeps_guards_and_lost_snapshot_stays_pinned(
    store: Storage,
) -> None:
    repo = _repo(store)
    _publish(store, repo, "snap_a")
    _publish(store, repo, "snap_b")
    _publish(store, repo, "snap_c")
    pinned = create_conversation(
        store, repository_id=repo, snapshot_id="snap_a", title="keep"
    )
    with store.pin_reader(repo, "snap_b"):
        held = cleanup_snapshots(store, repo)
        assert "snap_a" not in held
        assert "snap_b" not in held
        assert "snap_c" not in held
    removed = cleanup_snapshots(store, repo)
    assert removed == ("snap_b",)
    assert store.get_conversation(pinned.id).snapshot_id == "snap_a"
    assert store.get_repository(repo).active_snapshot_id == "snap_c"

    mark_snapshot_unavailable(store, "snap_a")
    with pytest.raises(SnapshotUnavailableError) as unavailable:
        read_conversation(store, pinned.id)
    assert unavailable.value.code == "snapshot_unavailable"
    assert store.get_conversation(pinned.id).snapshot_id == "snap_a"
    assert store.get_repository(repo).active_snapshot_id == "snap_c"

    calls = {"n": 0}

    def _provider(_ctx: object) -> ProviderResult:
        calls["n"] += 1
        return ProviderResult(status="answered", answer="nope")

    with pytest.raises(SnapshotUnavailableError):
        submit_turn(
            store,
            pinned.id,
            question="should not run",
            client_request_id="lost-1",
            expected_revision=1,
            provider=_provider,
        )
    assert calls["n"] == 0
    assert list_turns(store, pinned.id) == ()


def test_ac045_pending_delete_is_busy_and_other_history_remains(
    store: Storage,
) -> None:
    repo = _repo(store)
    _publish(store, repo, "snap_a")
    _publish(store, repo, "snap_b")
    busy = create_conversation(
        store, repository_id=repo, snapshot_id="snap_a", title="busy"
    )
    other = create_conversation(
        store, repository_id=repo, snapshot_id="snap_b", title="other"
    )
    submit_turn(
        store,
        other.id,
        question="keep me",
        client_request_id="keep-1",
        expected_revision=1,
        provider=lambda _ctx: ProviderResult(status="answered", answer="kept"),
    )
    begin_turn(
        store,
        busy.id,
        question="not done",
        client_request_id="busy-1",
        expected_revision=1,
    )
    before = count_entities(store, "snap_b")
    with pytest.raises(ConversationBusyError) as err:
        delete_conversation(store, busy.id)
    assert err.value.code == "conversation_busy"
    assert store.get_conversation(busy.id).snapshot_id == "snap_a"
    assert list_turns(store, other.id)[0].question == "keep me"

    path = store.path
    store.close()
    reopened = Storage(path)
    try:
        statuses = [turn.status for turn in list_turns(reopened, busy.id)]
        assert statuses == ["interrupted"]
        delete_conversation(reopened, busy.id)
        assert reopened.get_conversation(other.id).snapshot_id == "snap_b"
        assert list_turns(reopened, other.id)[0].answer == "kept"
        assert count_entities(reopened, "snap_b") == before
        with pytest.raises(SnapshotActiveError):
            reopened.delete_snapshot(repo, "snap_b")
        assert reopened.get_snapshot(repo, "snap_b").id == "snap_b"
    finally:
        reopened.close()


def test_ac059_missing_or_malformed_fields_do_not_mutate(store: Storage) -> None:
    repo = _repo(store)
    _publish(store, repo, "snap_a")
    conversation = create_conversation(
        store, repository_id=repo, snapshot_id="snap_a", title="fields"
    )
    calls = {"n": 0}

    def _provider(_ctx: object) -> ProviderResult:
        calls["n"] += 1
        return ProviderResult(status="answered", answer="should not")

    cases = (
        {"client_request_id": None, "expected_revision": 1},
        {"client_request_id": " ", "expected_revision": 1},
        {"client_request_id": "ok", "expected_revision": None},
        {"client_request_id": "ok", "expected_revision": "1"},
        {"client_request_id": "ok", "expected_revision": 0},
        {"client_request_id": "ok", "expected_revision": True},
    )
    for case in cases:
        with pytest.raises(InvalidTurnRequestError) as err:
            submit_turn(
                store,
                conversation.id,
                question="hello",
                provider=_provider,
                **case,
            )
        assert err.value.code == "invalid_turn_request"
    assert calls["n"] == 0
    assert list_turns(store, conversation.id) == ()
    current = store.get_conversation(conversation.id)
    assert current.revision == 1
    assert current.state["focus_entity_id"] is None


def test_ac064_redacts_store_and_omits_transcript_from_logs(
    store: Storage, caplog: pytest.LogCaptureFixture
) -> None:
    repo = _repo(store)
    entity_id = _publish(store, repo, "snap_a")
    facts_before = count_entities(store, "snap_a")
    conversation = create_conversation(
        store,
        repository_id=repo,
        snapshot_id="snap_a",
        title="title password=s3cr3t-value",
    )
    question = (
        f"{QUESTION} password=s3cr3t-value Bearer sk-test-sentinel-value "
        "<think>hidden reasoning</think> ```\nSECRET_SOURCE = 1\n```"
    )

    def _provider(_ctx: object) -> ProviderResult:
        return ProviderResult(
            status="answered",
            answer=f"{ANSWER} api_key=live-secret <script>alert(1)</script>",
            resolved_question=question,
            claims=({"text": "token=abc", "chain_of_thought": "private plan"},),
            citations=(
                {
                    "entity_id": entity_id,
                    "snapshot_id": "snap_a",
                    "quote": "C:\\Users\\secret\\repo\\app.py",
                },
            ),
            focus_entity_id=entity_id,
            usage={"output_tokens": 3, "prompt": question},
        )

    with caplog.at_level(logging.INFO, logger="rkg.conversation"):
        done = submit_turn(
            store,
            conversation.id,
            question=question,
            client_request_id="redact-1",
            expected_revision=1,
            provider=_provider,
        )
    stored = _stored_text(store, conversation.id)
    for forbidden in (
        "s3cr3t-value",
        "sk-test-sentinel-value",
        "hidden reasoning",
        "SECRET_SOURCE",
        "live-secret",
        "alert(1)",
        "private plan",
        "Users",
        question,
    ):
        assert forbidden not in stored
    assert QUESTION in stored
    assert ANSWER in stored
    assert done.turn.usage == {"output_tokens": 3}
    assert count_entities(store, "snap_a") == facts_before
    logged = "\n".join(record.getMessage() for record in caplog.records)
    for forbidden in (QUESTION, ANSWER, "s3cr3t-value", "hidden reasoning", question):
        assert forbidden not in logged
    assert "turn_id=" in logged
