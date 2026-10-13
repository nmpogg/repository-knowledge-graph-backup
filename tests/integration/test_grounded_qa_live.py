"""Optional real-provider check for Task 20 grounded edge selection."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from rkg.conversations import create_conversation, submit_grounded_turn
from rkg.llm import OpenRouterProvider
from rkg.storage import Storage
from tests.integration.graph_helpers import seed_cycle_graph, seed_relation_graph


@pytest.mark.skipif(
    not os.environ.get("OPENROUTER_API_KEY"), reason="OpenRouter credential unavailable"
)
def test_openrouter_live_grounded_edge_and_citation(tmp_path: Path) -> None:
    with Storage(tmp_path / "live-grounded.kuzu") as store:
        repo_id, snapshot_id, batch = seed_cycle_graph(store)
        conversation = create_conversation(
            store, repository_id=repo_id, snapshot_id=snapshot_id
        )
        b = next(
            item for item in batch.entities if item.qualified_name == "app.cycle.b"
        )
        result = submit_grounded_turn(
            store,
            conversation.id,
            question="What does app.cycle.a call?",
            client_request_id="live-grounded",
            expected_revision=1,
            provider=OpenRouterProvider(),
        )
        turn = result.submission.turn
        assert turn.status == "answered"
        assert "app.cycle.a calls app.cycle.b" in turn.answer
        assert turn.citations
        assert all(
            item["snapshot_id"] == snapshot_id and item["entity_id"] == b.id
            for item in turn.citations
        )
        assert turn.usage["model_calls"] == 1

        follow = submit_grounded_turn(
            store,
            conversation.id,
            question="What does it call?",
            client_request_id="live-followup",
            expected_revision=result.submission.conversation.revision,
            provider=OpenRouterProvider(),
        )
        assert follow.submission.turn.status == "answered"
        assert "app.cycle.a calls app.cycle.b" in follow.submission.turn.answer
        assert follow.submission.turn.context_turn_ids == (turn.id,)
        assert follow.submission.turn.usage["model_calls"] == 1


@pytest.mark.skipif(
    not os.environ.get("OPENROUTER_API_KEY"), reason="OpenRouter credential unavailable"
)
def test_openrouter_live_db_event_dependency_technology(tmp_path: Path) -> None:
    with Storage(tmp_path / "live-relations.kuzu") as store:
        repo, sid, batch, by_name = seed_relation_graph(store)
        conversation = create_conversation(
            store, repository_id=repo, snapshot_id=sid
        )
        cases = (
            ("Which database table does create_order write?", "create_order", 1),
            ("Which event does create_order publish?", "create_order", 2),
            ("Which dependency is used?", "fastapi", 3),
            ("Công nghệ fastapi phụ thuộc vào đâu?", "fastapi", 3),
        )
        revision = 1
        for index, (question, root_name, edge_index) in enumerate(cases):
            result = submit_grounded_turn(
                store,
                conversation.id,
                question=question,
                client_request_id=f"live-relation-{index}",
                expected_revision=revision,
                root_id=by_name[root_name].id,
                provider=OpenRouterProvider(),
            )
            turn = result.submission.turn
            assert turn.status == "answered"
            assert turn.claims
            assert turn.claims[0]["edge_id"] == batch.edges[edge_index].id
            assert turn.citations[0]["snapshot_id"] == sid
            assert (
                turn.citations[0]["evidence_id"]
                == batch.evidence[edge_index].id
            )
            revision = result.submission.conversation.revision
