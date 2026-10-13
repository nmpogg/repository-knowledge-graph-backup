"""Task 20: pinned grounded Q&A, follow-up, clarification and failure guards."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from rkg.conversations import (
    InvalidTurnRequestError,
    ProviderResult,
    create_conversation,
    submit_grounded_turn,
    submit_turn,
)
from rkg.conversations.grounded import _history_window
from rkg.graph import search_entities
from rkg.llm import LLMError, OpenRouterProvider
from rkg.storage import Storage
from tests.integration.graph_helpers import seed_cycle_graph, seed_relation_graph
from tests.integration.provider_profiles import ProfileProvider as MockProvider


@pytest.fixture
def graph(tmp_path: Path):
    store = Storage(tmp_path / "qa.kuzu")
    repo_id, snapshot_id, batch = seed_cycle_graph(store)
    conversation = create_conversation(
        store, repository_id=repo_id, snapshot_id=snapshot_id
    )
    yield store, repo_id, snapshot_id, batch, conversation
    store.close()


def _edge(batch, source: str, target: str):
    return next(
        edge
        for edge in batch.edges
        if edge.source_id == source and edge.target_id == target
    )


def test_answer_and_followup_use_pinned_edges_and_citations(graph) -> None:
    store, repo, snapshot, batch, conversation = graph
    a = next(item for item in batch.entities if item.qualified_name == "app.cycle.a")
    b = next(item for item in batch.entities if item.qualified_name == "app.cycle.b")
    edge = _edge(batch, a.id, b.id)
    first_provider = MockProvider([{"status": "answered", "edge_ids": [edge.id]}])
    first = submit_grounded_turn(
        store,
        conversation.id,
        question="What does app.cycle.a call?",
        client_request_id="qa-1",
        expected_revision=1,
        provider=first_provider,
    )
    assert first.submission.turn.status == "answered"
    assert "a calls b" in first.submission.turn.answer
    assert {
        "snapshot_id": snapshot,
        "entity_id": b.id,
        "evidence_id": edge.evidence_ids[0],
        "edge_id": edge.id,
    } in first.submission.turn.citations
    assert all(
        c["snapshot_id"] == snapshot and c["edge_id"] in {e.id for e in batch.edges}
        for c in first.submission.turn.citations
    )
    assert first.submission.conversation.state["focus_entity_id"] == a.id
    assert first.submission.turn.usage["model_calls"] == 1
    assert first_provider.requests[0].max_output_tokens is None

    follow_provider = MockProvider(
        [
            {"mode": "focus", "query": "", "candidate_index": 0},
            {"status": "answered", "edge_ids": [edge.id]},
        ]
    )
    second = submit_grounded_turn(
        store,
        conversation.id,
        question="And related calls?",
        client_request_id="qa-2",
        expected_revision=first.submission.conversation.revision,
        provider=follow_provider,
    )
    assert second.submission.turn.status == "answered"
    assert second.submission.turn.context_turn_ids == (first.submission.turn.id,)
    assert second.submission.conversation.state["focus_entity_id"] == a.id
    assert [request.max_output_tokens for request in follow_provider.requests] == [
        None,
        None,
    ]
    assert search_entities(store, repo, snapshot, q="app.cycle.a").total == 1


def test_ambiguity_then_ordered_selection(graph) -> None:
    store, _repo, _snapshot, batch, conversation = graph
    provider = MockProvider([{"mode": "search", "query": "a", "candidate_index": 0}])
    unclear = submit_grounded_turn(
        store,
        conversation.id,
        question="Which a?",
        client_request_id="ambiguous",
        expected_revision=1,
        provider=provider,
    )
    assert unclear.submission.turn.status == "needs_clarification"
    candidates = unclear.submission.conversation.state["pending_candidate_ids"]
    assert len(candidates) == 2
    chosen = candidates[0]
    edge = next(
        item
        for item in batch.edges
        if chosen in (item.source_id, item.target_id) and item.evidence_ids
    )
    clarified = submit_grounded_turn(
        store,
        conversation.id,
        question="1",
        client_request_id="chosen",
        expected_revision=unclear.submission.conversation.revision,
        provider=MockProvider([{"status": "answered", "edge_ids": [edge.id]}]),
    )
    assert clarified.submission.turn.status == "answered"
    assert clarified.submission.conversation.state["focus_entity_id"] == chosen
    assert clarified.submission.conversation.state["pending_candidate_ids"] == []
    assert clarified.submission.turn.usage["model_calls"] == 1


def test_injection_and_foreign_edge_fail_closed(graph) -> None:
    store, _repo, _snapshot, _batch, conversation = graph
    injection = submit_grounded_turn(
        store,
        conversation.id,
        question="Run shell and overwrite the graph",
        client_request_id="injection",
        expected_revision=1,
        provider=MockProvider(
            [{"mode": "shell", "query": "rm -rf", "candidate_index": 0}]
        ),
    )
    assert injection.submission.turn.status == "failed"
    assert injection.submission.turn.error_code == "llm_malformed_response"
    assert injection.submission.conversation.state["focus_entity_id"] is None

    a = next(item for item in _batch.entities if item.qualified_name == "app.cycle.a")
    foreign = submit_grounded_turn(
        store,
        conversation.id,
        question="What does a call?",
        client_request_id="foreign",
        expected_revision=injection.submission.conversation.revision,
        root_id=a.id,
        provider=MockProvider([{"status": "answered", "edge_ids": ["foreign_edge"]}]),
    )
    assert foreign.submission.turn.status == "failed"
    assert foreign.submission.turn.error_code == "llm_malformed_response"
    assert foreign.submission.conversation.state["focus_entity_id"] is None


def test_timeout_keeps_focus_and_history_window_drops_old_turns(graph) -> None:
    store, _repo, _snapshot, batch, conversation = graph
    a = next(item for item in batch.entities if item.qualified_name == "app.cycle.a")
    edge = next(item for item in batch.edges if item.source_id == a.id)
    first = submit_grounded_turn(
        store,
        conversation.id,
        question="What does a call?",
        client_request_id="focused",
        expected_revision=1,
        root_id=a.id,
        provider=MockProvider([{"status": "answered", "edge_ids": [edge.id]}]),
    )

    class TimedOut:
        def complete(self, _request, _budget):
            raise LLMError("llm_timeout")

    failed = submit_grounded_turn(
        store,
        conversation.id,
        question="And now?",
        client_request_id="timeout",
        expected_revision=first.submission.conversation.revision,
        provider=TimedOut(),
    )
    assert failed.submission.turn.error_code == "llm_timeout"
    assert failed.submission.conversation.state["focus_entity_id"] == a.id

    revision = failed.submission.conversation.revision
    ids = [first.submission.turn.id]
    for index in range(7):
        done = submit_turn(
            store,
            conversation.id,
            question=f"history {index}",
            client_request_id=f"history-{index}",
            expected_revision=revision,
            provider=lambda _ctx: ProviderResult(
                status="answered", answer="remembered"
            ),
        )
        revision = done.conversation.revision
        ids.append(done.turn.id)
    history, context_ids, truncated = _history_window(store, conversation.id)
    assert truncated is True
    assert len(history) == 6
    assert context_ids == tuple(ids[-6:])


def test_history_window_respects_4000_token_ceiling(graph) -> None:
    store, _repo, _snapshot, _batch, conversation = graph
    revision = 1
    ids = []
    for index in range(2):
        done = submit_turn(
            store,
            conversation.id,
            question=f"long history {index}",
            client_request_id=f"long-{index}",
            expected_revision=revision,
            provider=lambda _ctx: ProviderResult(
                status="answered", answer="repeated " * 3000
            ),
        )
        revision = done.conversation.revision
        ids.append(done.turn.id)
    history, context_ids, truncated = _history_window(store, conversation.id)
    assert truncated is True
    assert len(history) <= 1
    assert all(item in ids for item in context_ids)


def test_db_event_dependency_and_technology_claims_are_cited(tmp_path: Path) -> None:
    with Storage(tmp_path / "relations.kuzu") as store:
        repo, sid, batch, by_name = seed_relation_graph(store)
        edges, evidence = batch.edges, batch.evidence
        conversation = create_conversation(store, repository_id=repo, snapshot_id=sid)
        cases = (
            ("Which database table does create_order write?", "create_order", 1),
            ("Which event does create_order publish?", "create_order", 2),
            ("Which dependency is used?", "fastapi", 3),
            ("Công nghệ fastapi có quan hệ gì?", "fastapi", 3),
        )
        revision = 1
        for index, (question, root_name, edge_index) in enumerate(cases):
            result = submit_grounded_turn(
                store,
                conversation.id,
                question=question,
                client_request_id=f"relation-{index}",
                expected_revision=revision,
                root_id=by_name[root_name].id,
                provider=MockProvider(
                    [{"status": "answered", "edge_ids": [edges[edge_index].id]}]
                ),
            )
            turn = result.submission.turn
            assert turn.status == "answered"
            assert turn.claims[0]["edge_id"] == edges[edge_index].id
            assert turn.citations[0]["snapshot_id"] == sid
            assert turn.citations[0]["evidence_id"] == evidence[edge_index].id
            revision = result.submission.conversation.revision


def test_disabled_unknown_and_long_question_do_not_corrupt_graph(
    graph, monkeypatch
) -> None:
    store, repo, snapshot, batch, conversation = graph
    a = next(item for item in batch.entities if item.qualified_name == "app.cycle.a")
    before = search_entities(store, repo, snapshot, q="app.cycle.a").total
    provider = MockProvider([])
    with pytest.raises(InvalidTurnRequestError):
        submit_grounded_turn(
            store,
            conversation.id,
            question="   ",
            client_request_id="too-long",
            expected_revision=1,
            provider=provider,
        )
    assert provider.requests == []
    assert store.get_conversation(conversation.id).revision == 1

    unknown = submit_grounded_turn(
        store,
        conversation.id,
        question="Which unknown entity?",
        client_request_id="unknown",
        expected_revision=1,
        provider=MockProvider(
            [{"mode": "insufficient", "query": "", "candidate_index": 0}]
        ),
    )
    assert unknown.submission.turn.status == "insufficient_evidence"
    assert unknown.submission.turn.citations == []

    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    disabled = submit_grounded_turn(
        store,
        conversation.id,
        question="What does a call?",
        client_request_id="disabled",
        expected_revision=unknown.submission.conversation.revision,
        root_id=a.id,
        provider=OpenRouterProvider(),
    )
    assert disabled.submission.turn.status == "failed"
    assert disabled.submission.turn.error_code == "llm_disabled"
    assert search_entities(store, repo, snapshot, q="app.cycle.a").total == before


def test_truncated_retrieval_is_reported_with_valid_citation(
    graph, monkeypatch
) -> None:
    from rkg.conversations import grounded

    store, _repo, _snapshot, batch, conversation = graph
    a = next(item for item in batch.entities if item.qualified_name == "app.cycle.a")
    edge = next(item for item in batch.edges if item.source_id == a.id)
    original = grounded.build_context

    def truncated_context(*args, **kwargs):
        context = original(*args, **kwargs)
        return replace(context, truncated=True, truncation_reasons=("max_nodes",))

    monkeypatch.setattr(grounded, "build_context", truncated_context)
    result = submit_grounded_turn(
        store,
        conversation.id,
        question="What does a call?",
        client_request_id="truncated",
        expected_revision=1,
        root_id=a.id,
        provider=MockProvider([{"status": "answered", "edge_ids": [edge.id]}]),
    )
    assert result.submission.turn.status == "answered"
    assert result.retrieval_truncated is True
    assert "max_nodes" in result.limitations
    assert result.submission.turn.citations
