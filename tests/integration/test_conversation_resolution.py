import pytest

from rkg.conversations import create_conversation, submit_grounded_turn
from rkg.conversations.service import ProviderResult, submit_turn
from rkg.graph.search import lookup_entities
from rkg.llm import OpenRouterProvider
from rkg.storage import Storage
from tests.integration.graph_helpers import seed_cycle_graph
from tests.integration.provider_profiles import ProfileProvider as MockProvider


@pytest.fixture
def graph(tmp_path):
    with Storage(tmp_path / "resolution.kuzu") as store:
        repo, sid, batch = seed_cycle_graph(store)
        conversation = create_conversation(store, repository_id=repo, snapshot_id=sid)
        yield store, repo, sid, batch, conversation


def test_greeting_has_no_model_or_graph_calls_and_keeps_state(graph, monkeypatch):
    store, _, _, _, conv = graph

    def forbidden(*args, **kwargs):
        raise AssertionError("graph lookup on greeting")

    monkeypatch.setattr("rkg.conversations.grounded.build_context", forbidden)
    monkeypatch.setattr("rkg.conversations.grounded.lookup_entities", forbidden)
    provider = MockProvider([])
    result = submit_grounded_turn(
        store,
        conv.id,
        question="alo",
        client_request_id="hi",
        expected_revision=1,
        provider=provider,
    )
    assert result.submission.turn.status == "answered"
    assert result.submission.turn.response_metadata["kind"] == "greeting"
    assert result.submission.conversation.state == conv.state
    assert provider.requests == []
    assert not result.submission.turn.claims


def test_disabled_greeting_keeps_real_provider_error(graph, monkeypatch):
    store, _, _, _, conv = graph
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    result = submit_grounded_turn(
        store,
        conv.id,
        question="hello",
        client_request_id="disabled",
        expected_revision=1,
        provider=OpenRouterProvider(),
    )
    assert result.submission.turn.error_code == "llm_disabled"


def test_endpoint_lookup_exact_attributes_and_type(graph):
    store, repo, sid, _, _ = graph
    assert (
        lookup_entities(
            store, repo, sid, method="get", path="/orders/{id}", entity_type="Endpoint"
        ).total
        == 1
    )
    assert (
        lookup_entities(
            store, repo, sid, method="GET", path="/orders/{id}/", entity_type="Endpoint"
        ).total
        == 0
    )
    assert (
        lookup_entities(
            store, repo, sid, method="GET", path="/Orders/{id}", entity_type="Endpoint"
        ).total
        == 0
    )
    assert (
        lookup_entities(store, repo, sid, query="a", entity_type="Callable").total == 1
    )
    assert lookup_entities(store, repo, sid, query="a").total == 2


def test_selection_resumes_original_question_and_locale(graph):
    store, _, _, batch, conv = graph
    first = submit_grounded_turn(
        store,
        conv.id,
        question="What does `a` call?",
        client_request_id="ask",
        expected_revision=1,
        provider=MockProvider([]),
        ui_locale="en",
    )
    assert first.submission.turn.status == "needs_clarification"
    state = first.submission.conversation.state
    assert state["pending_intent"]["question"] == "What does `a` call?"
    assert state["pending_intent"]["language"] == "en"
    chosen = state["pending_candidate_ids"][0]
    edge = next(e for e in batch.edges if e.source_id == chosen)
    selected = submit_grounded_turn(
        store,
        conv.id,
        question="1",
        client_request_id="select",
        expected_revision=first.submission.conversation.revision,
        provider=MockProvider([{"status": "answered", "edge_ids": [edge.id]}]),
    )
    assert selected.submission.turn.resolved_question == "What does `a` call?"
    assert selected.submission.turn.response_metadata["language"] == "en"
    assert selected.submission.conversation.state["pending_intent"] is None


def test_invalid_ordinal_and_legacy_candidates_preserve_intent(graph):
    store, _, _, batch, conv = graph
    ids = tuple(e.id for e in batch.entities[:2])
    old = submit_turn(
        store,
        conv.id,
        question="legacy",
        client_request_id="legacy",
        expected_revision=1,
        provider=lambda _: ProviderResult(
            status="needs_clarification", candidate_entity_ids=ids
        ),
    )
    for text in ["0", "100", "-1", "1"]:
        result = submit_grounded_turn(
            store,
            conv.id,
            question=text,
            client_request_id="choice" + text,
            expected_revision=old.conversation.revision,
            provider=MockProvider([]),
        )
        assert result.submission.turn.status == "needs_clarification"
        assert result.submission.conversation.state == old.conversation.state
        old = result.submission


def test_exact_attributes_are_evaluated_before_first_page(graph, monkeypatch):
    from dataclasses import replace

    store, repo, sid, batch, _ = graph
    endpoint = next(e for e in batch.entities if e.type.value == "Endpoint")
    distractors = [
        replace(
            endpoint,
            id="d" + str(i),
            attributes=(("method", "GET"), ("path", "/other" + str(i))),
        )
        for i in range(25)
    ]
    monkeypatch.setattr(
        "rkg.graph.search.load_entities", lambda *args: distractors + [endpoint]
    )
    page = lookup_entities(
        store, repo, sid, method="GET", path="/orders/{id}", entity_type="Endpoint"
    )
    assert page.total == 1 and page.items[0].id == endpoint.id


def test_overflow_never_selects_first_page_and_greeting_preserves_pending(
    graph, monkeypatch
):
    from dataclasses import replace

    store, _, _, batch, conv = graph
    base = batch.entities[0]
    matches = [
        replace(base, id="item" + str(i), qualified_name="app." + str(i))
        for i in range(21)
    ]
    monkeypatch.setattr("rkg.graph.search.load_entities", lambda *args: matches)
    provider = MockProvider([])
    first = submit_grounded_turn(
        store,
        conv.id,
        question="What does `a` call?",
        client_request_id="overflow",
        expected_revision=1,
        provider=provider,
    )
    assert first.submission.turn.status == "needs_clarification"
    assert len(first.submission.conversation.state["pending_candidate_ids"]) == 20
    state = first.submission.conversation.state
    for i, text in enumerate(["21", "hello"]):
        following = submit_grounded_turn(
            store,
            conv.id,
            question=text,
            client_request_id="follow" + str(i),
            expected_revision=first.submission.conversation.revision,
            provider=provider,
        )
        assert following.submission.conversation.state == state
        first = following
    assert not provider.requests


def test_planner_candidate_uses_committed_intent_and_legacy_guard(graph):
    store, _, _, batch, conv = graph
    first = submit_grounded_turn(
        store,
        conv.id,
        question="What does `a` call?",
        client_request_id="original",
        expected_revision=1,
        provider=MockProvider([]),
        ui_locale="en",
    )
    state = first.submission.conversation.state
    chosen = state["pending_candidate_ids"][0]
    edge = next(e for e in batch.edges if e.source_id == chosen)
    plan = {"mode": "candidate", "query": "", "candidate_index": 0}
    result = submit_grounded_turn(
        store,
        conv.id,
        question="the first one",
        client_request_id="natural-selection",
        expected_revision=first.submission.conversation.revision,
        provider=MockProvider([plan, {"status": "answered", "edge_ids": [edge.id]}]),
    )
    assert result.submission.turn.status == "answered"
    assert result.submission.turn.resolved_question == "What does `a` call?"
    assert result.submission.turn.response_metadata["language"] == "en"
    old = submit_turn(
        store,
        conv.id,
        question="legacy",
        client_request_id="old",
        expected_revision=result.submission.conversation.revision,
        provider=lambda _: ProviderResult(
            status="needs_clarification", candidate_entity_ids=(chosen,)
        ),
    )
    legacy = submit_grounded_turn(
        store,
        conv.id,
        question="the first one",
        client_request_id="natural-legacy",
        expected_revision=old.conversation.revision,
        provider=MockProvider([plan]),
    )
    assert legacy.submission.turn.status == "needs_clarification"
    assert legacy.submission.conversation.state == old.conversation.state
