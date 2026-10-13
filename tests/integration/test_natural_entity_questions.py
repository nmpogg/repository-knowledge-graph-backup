"""Questions start from ordinary prose, not a preselected entity ID."""

from dataclasses import replace

import pytest

from rkg.conversations import create_conversation, submit_grounded_turn
from rkg.graph import publish_fact_batch
from rkg.llm import MockProvider
from rkg.storage import Storage
from rkg.storage.conversations import write_state
from tests.integration.graph_helpers import cycle_batch, publish_meta


@pytest.fixture
def graph(tmp_path, request):
    with Storage(tmp_path / "natural.kuzu") as store:
        repo = store.create_repository(
            display_name="natural",
            source_type="local",
            source_locator="/allowed/natural",
        )
        batch = cycle_batch(repo.id, "natural-snapshot")
        renamed = []
        for node in batch.entities:
            if node.qualified_name == "app.cycle.a":
                node = replace(node, name="logout", qualified_name="app.auth.logout")
            elif node.qualified_name == "app.cycle.b":
                node = replace(node, name="revoke", qualified_name="app.auth.revoke")
            elif node.qualified_name == "app.cycle.c":
                node = replace(node, name="login", qualified_name="app.auth.login")
            if (
                getattr(request, "param", False)
                and node.type.value == "Endpoint"
                and node.name == "get_orders"
            ):
                node = replace(node, name="logout", qualified_name="app.api.logout")
            renamed.append(node)
        batch = replace(batch, entities=tuple(renamed))
        publish_fact_batch(store, batch, publish_meta())
        conv = create_conversation(
            store, repository_id=repo.id, snapshot_id=batch.snapshot_id
        )
        by_name = {n.qualified_name: n for n in batch.entities}
        logout = by_name["app.auth.logout"]
        login = by_name["app.auth.login"]
        edge = next(
            e
            for e in batch.edges
            if e.source_id == logout.id and e.type.value == "calls"
        )
        yield store, conv, logout, login, edge


def answer(root, edge):
    return {
        "status": "answered",
        "root_id": root.id,
        "sections": [
            {
                "relation": "calls",
                "direction": "outgoing",
                "paths": [{"anchor_id": root.id, "edge_ids": [edge.id]}],
            }
        ],
    }


@pytest.mark.parametrize(
    "question",
    [
        "logout dang goi nhung gi, no nam o dau",
        "logout đang gọi những gì, nó nằm ở đâu?",
        "What does logout call and where is it defined?",
    ],
)
def test_bare_name_composite_resolves_and_answers_both_parts(graph, question):
    store, conv, logout, _, edge = graph
    provider = MockProvider([answer(logout, edge)])
    result = submit_grounded_turn(
        store,
        conv.id,
        question=question,
        client_request_id="natural",
        expected_revision=1,
        provider=provider,
    )
    turn = result.submission.turn
    assert turn.status == "answered"
    assert turn.response_metadata["subject"]["entity_id"] == logout.id
    assert "app/cycle.py" in turn.answer and "1" in turn.answer
    assert turn.claims and turn.citations
    assert [r.schema_name for r in provider.requests] == ["rkg_narrative_v1"]


def test_new_name_with_pronoun_overrides_old_focus(graph):
    store, conv, logout, login, edge = graph
    write_state(
        store.conn,
        conv.id,
        expected_revision=1,
        state={
            "state_version": 2,
            "focus_entity_id": login.id,
            "pending_candidate_ids": [],
            "pending_intent": None,
        },
    )
    provider = MockProvider([answer(logout, edge)])
    result = submit_grounded_turn(
        store,
        conv.id,
        question="logout đang gọi gì, nó nằm ở đâu?",
        client_request_id="new-topic",
        expected_revision=1,
        provider=provider,
    )
    assert result.submission.turn.status == "answered"
    assert result.submission.conversation.state["focus_entity_id"] == logout.id


@pytest.mark.parametrize(
    "question", ["logout nam o dau", "logout nằm ở đâu?", "Where is logout defined?"]
)
def test_location_identity_needs_no_model_relationship_selection(graph, question):
    store, conv, logout, _, _ = graph
    provider = MockProvider([])
    result = submit_grounded_turn(
        store,
        conv.id,
        question=question,
        client_request_id="where",
        expected_revision=1,
        provider=provider,
    )
    turn = result.submission.turn
    assert turn.status == "answered"
    assert "app/cycle.py" in turn.answer
    assert turn.response_metadata["subject"]["entity_id"] == logout.id
    assert not turn.claims and not turn.citations
    assert not provider.requests
    assert turn.response_metadata["language"] == (
        "en" if question.startswith("Where") else "vi"
    )


@pytest.mark.parametrize("graph", [True], indirect=True)
@pytest.mark.parametrize("selection", ["ordinal", "button"])
def test_ambiguous_natural_question_keeps_calls_and_location_through_selection(
    graph, selection
):
    store, conv, logout, _, edge = graph
    provider = MockProvider([])
    first = submit_grounded_turn(
        store,
        conv.id,
        question="logout dang goi nhung gi, no nam o dau",
        client_request_id="ambiguous",
        expected_revision=1,
        provider=provider,
    )
    assert first.submission.turn.status == "needs_clarification"
    assert not provider.requests
    state = store.get_conversation(conv.id).state
    ids = state["pending_candidate_ids"]
    assert len(ids) == 2 and state["pending_intent"]["relation_types"] == ["calls"]
    endpoint = next(i for i in ids if i != logout.id)
    value = answer(logout, edge)
    value["root_id"] = endpoint
    selected = submit_grounded_turn(
        store,
        conv.id,
        question=str(ids.index(endpoint) + 1)
        if selection == "ordinal"
        else "Chọn mục này",
        root_id=None if selection == "ordinal" else endpoint,
        client_request_id="selection",
        expected_revision=first.submission.conversation.revision,
        provider=MockProvider([value]),
    )
    assert selected.submission.turn.status == "answered"
    assert "app/cycle.py:50" in selected.submission.turn.answer
    assert selected.submission.turn.claims and selected.submission.turn.citations
    assert selected.submission.conversation.state["focus_entity_id"] == endpoint
    assert not selected.submission.conversation.state["pending_candidate_ids"]


def test_unaccented_location_followup_reuses_focus_and_replays(graph):
    store, conv, logout, _, edge = graph
    first = submit_grounded_turn(
        store,
        conv.id,
        question="logout goi gi",
        client_request_id="first",
        expected_revision=1,
        provider=MockProvider([answer(logout, edge)]),
    )
    kwargs = dict(
        question="no nam o dau",
        client_request_id="where-followup",
        expected_revision=first.submission.conversation.revision,
        provider=MockProvider([]),
    )
    next_turn = submit_grounded_turn(store, conv.id, **kwargs)
    assert next_turn.submission.turn.status == "answered"
    assert "app/cycle.py:1" in next_turn.submission.turn.answer
    assert next_turn.submission.turn.usage["model_calls"] == 0
    replay = submit_grounded_turn(store, conv.id, **kwargs)
    assert replay.submission.turn.answer == next_turn.submission.turn.answer
    assert (
        replay.submission.conversation.revision
        == next_turn.submission.conversation.revision
    )


@pytest.mark.parametrize("question", ["nó gọi revoke không?", "Does it call revoke?"])
def test_named_callee_in_followup_does_not_replace_subject(graph, question):
    store, conv, logout, _, edge = graph
    write_state(
        store.conn,
        conv.id,
        expected_revision=1,
        state={
            "state_version": 2,
            "focus_entity_id": logout.id,
            "pending_candidate_ids": [],
            "pending_intent": None,
        },
    )
    result = submit_grounded_turn(
        store,
        conv.id,
        question=question,
        client_request_id="callee-followup",
        expected_revision=1,
        provider=MockProvider([answer(logout, edge)]),
    )
    assert result.submission.turn.status == "answered"
    assert result.submission.conversation.state["focus_entity_id"] == logout.id


@pytest.mark.parametrize("locale", ["vi", "en"])
@pytest.mark.parametrize("mode", ["ordinal", "button"])
def test_legacy_missing_intent_requests_restatement_without_mutating_state(
    graph, locale, mode
):
    from rkg.conversations.service import ProviderResult, submit_turn

    store, conv, logout, login, _ = graph
    old = submit_turn(
        store,
        conv.id,
        question="synthetic old question",
        client_request_id="legacy",
        expected_revision=1,
        provider=lambda _: ProviderResult(
            status="needs_clarification", candidate_entity_ids=(logout.id, login.id)
        ),
    )
    provider = MockProvider([])
    selected = submit_grounded_turn(
        store,
        conv.id,
        question="1" if mode == "ordinal" else "Select",
        root_id=logout.id if mode == "button" else None,
        client_request_id="old-choice",
        expected_revision=old.conversation.revision,
        provider=provider,
        ui_locale=locale,
    ).submission
    assert selected.turn.status == "needs_clarification"
    assert ("nhập lại" if locale == "vi" else "restate") in selected.turn.answer
    assert selected.conversation.state == old.conversation.state
    assert (
        not provider.requests
        and not selected.turn.claims
        and not selected.turn.citations
    )
