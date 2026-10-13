"""Edit-location suggestions from a real static index, without executing source."""

from pathlib import Path

import pytest

from rkg.conversations import create_conversation, submit_grounded_turn
from rkg.conversations.citations import exact_citation
from rkg.ingestion import LocalSourcePolicy
from rkg.jobs import IndexCoordinator
from rkg.llm import MockProvider
from rkg.storage import Storage


@pytest.fixture(scope="module")
def indexed(tmp_path_factory):
    source = Path(__file__).resolve().parents[2] / "repo-test/soopi"
    with Storage(tmp_path_factory.mktemp("change-guidance") / "graph") as store:
        repo = store.create_repository(
            display_name="fixture",
            source_type="local",
            source_locator=str(source),
            app_module="app.main",
            app_symbol="app",
        )
        job = IndexCoordinator(store, LocalSourcePolicy((source,))).run(repo.id)
        assert job.status in {"succeeded", "succeeded_with_warnings"}
        yield store, repo.id, store.get_repository(repo.id).active_snapshot_id


def ask(
    indexed, question, provider=None, conversation=None, revision=1, request="change"
):
    store, repo, sid = indexed
    conversation = conversation or create_conversation(
        store, repository_id=repo, snapshot_id=sid
    )
    provider = provider or MockProvider([])
    result = submit_grounded_turn(
        store,
        conversation.id,
        question=question,
        client_request_id=request,
        expected_revision=revision,
        provider=provider,
    )
    return result.submission, provider


@pytest.mark.parametrize(
    "question",
    [
        "Muốn sửa OrderService.checkout thì sửa code ở file nào, dòng nào?",
        "toi muon sua OrderService.checkout thi sua o file nao dong nao",
        "Where should I modify OrderService.checkout code?",
    ],
)
def test_checkout_suggests_real_definition_and_related_calls(indexed, question):
    submission, provider = ask(indexed, question)
    turn = submission.turn
    assert turn.status == "answered" and not provider.requests
    assert "app/services/order_service.py" in turn.answer
    assert "OrderService.checkout" in turn.answer
    assert "CartService.owned" in turn.answer
    assert "app/services/cart_service.py" in turn.answer
    assert "→" not in turn.answer
    assert turn.claims and turn.citations
    assert "dòng" in turn.answer or "lines" in turn.answer
    if "dòng" in question or "dong" in question:
        assert "dòng logic cụ thể" in turn.answer
    else:
        assert "Graph" not in turn.answer
    for index in range(len(turn.citations)):
        exact_citation(indexed[0], submission.conversation.id, turn.id, index)


def test_modify_endpoint_names_handler_and_service(indexed):
    submission, _ = ask(indexed, "Muốn sửa POST /api/v1/auth/login thì sửa ở đâu?")
    assert submission.turn.status == "answered"
    answer = submission.turn.answer
    assert "app/api/v1/endpoints/auth.py" in answer
    assert "AuthService.login" in answer
    assert "app/services/auth_service.py" in answer


def test_new_route_uses_existing_feature_without_inventing_endpoint(indexed):
    submission, provider = ask(
        indexed, "Thêm API POST /api/v1/orders/{order_id}/return ở file nào?"
    )
    assert submission.turn.status == "answered" and not provider.requests
    answer = submission.turn.answer
    assert "app/api/v1/endpoints/orders.py" in answer
    assert "vị trí tham khảo" in answer and "dòng chèn mới" in answer
    assert "/return` hiện có" not in answer


def test_unknown_new_feature_does_not_guess_file(indexed):
    submission, provider = ask(
        indexed, "Thêm API POST /api/v1/unknown-feature ở file nào?"
    )
    assert submission.turn.status == "insufficient_evidence" and not provider.requests
    assert "API hiện có" in submission.turn.answer
    assert "endpoints/orders.py" not in submission.turn.answer


def test_cancellation_feature_matches_existing_endpoint_without_model(indexed):
    provider = MockProvider(
        [
            {
                "mode": "search",
                "query": "cancel_order",
                "entity_type": "Endpoint",
                "relation_types": [],
                "direction": "outgoing",
                "candidate_index": 0,
            }
        ]
    )
    submission, _ = ask(
        indexed, "Muốn thêm API hủy đơn thì thêm code vào file nào?", provider
    )
    assert submission.turn.status == "answered"
    assert "app/api/v1/endpoints/orders.py" in submission.turn.answer
    assert "OrderService.cancel" in submission.turn.answer
    assert not provider.requests
    assert "/api/v1/orders/{order_id}/cancel" in submission.turn.answer


def test_modify_release_stock_reports_callers_and_replays(indexed):
    submission, _ = ask(
        indexed, "Sửa OrderService.release_stock ở đâu, ai bị ảnh hưởng?"
    )
    assert submission.turn.status == "answered"
    answer = submission.turn.answer
    assert "OrderService.cancel" in answer and "OrderService.expire" in answer
    assert "có thể bị ảnh hưởng" in answer
    replay, provider = ask(
        indexed,
        "Sửa OrderService.release_stock ở đâu, ai bị ảnh hưởng?",
        conversation=submission.conversation,
        revision=1,
    )
    assert replay.turn.id == submission.turn.id
    assert replay.turn.answer == answer and not provider.requests


def test_ambiguous_change_preserves_intent_after_selection(indexed):
    submission, _ = ask(indexed, "Sửa hàm checkout ở file nào?")
    assert submission.turn.status == "needs_clarification"
    followup, _ = ask(
        indexed,
        "1",
        conversation=submission.conversation,
        revision=submission.conversation.revision,
        request="selection",
    )
    assert followup.turn.status == "answered"
    assert "Chỗ cần xem đầu tiên" in followup.turn.answer
    assert "vùng định nghĩa" not in followup.turn.answer


def test_followup_changes_use_committed_focus(indexed):
    first, _ = ask(indexed, "Hàm OrderService.checkout nằm ở đâu?")
    next_turn, _ = ask(
        indexed,
        "Muốn sửa nó thì sửa ở dòng nào?",
        conversation=first.conversation,
        revision=first.conversation.revision,
        request="followup",
    )
    assert next_turn.turn.status == "answered"
    assert "OrderService.checkout" in next_turn.turn.answer


@pytest.mark.parametrize(
    "question",
    [
        "Muốn thêm API hủy đơn thì nên thêm vào file nào?",
        "Thêm API hủy đơn nên đặt ở đâu?",
        "them API huy don nen dat o dau?",
    ],
)
def test_reported_cancellation_questions_answer_without_mocked_plan(indexed, question):
    submission, provider = ask(indexed, question)
    assert submission.turn.status == "answered"
    assert not provider.requests
    assert submission.turn.answer.startswith("Đặt API mới trong")
    assert "app/api/v1/endpoints/orders.py" in submission.turn.answer
    assert "/api/v1/orders/{order_id}/cancel" in submission.turn.answer
    assert "OrderService.cancel" in submission.turn.answer
    assert "snapshot" not in submission.turn.answer


def test_reported_impact_question_does_not_dump_utility_functions(indexed):
    submission, _ = ask(indexed, "Sửa release_stock có thể ảnh hưởng ai?")
    assert submission.turn.status == "answered"
    answer = submission.turn.answer
    assert "OrderService.cancel" in answer and "OrderService.expire" in answer
    assert "security.now" not in answer and "ProductRepository.variants" not in answer
    assert answer.count("app/services/order_service.py") == 1
    assert "Graph" not in answer and "snapshot" not in answer
    assert "Các hàm được gọi trực tiếp" not in answer
    assert len(answer.split("\n\n")) == 2


def test_missing_first_letter_in_edit_request_is_still_advice(indexed):
    submission, _ = ask(indexed, "ửa OrderService.checkout ở file nào, dòng nào?”")
    assert submission.turn.status == "answered"
    assert "Chỗ cần xem đầu tiên" in submission.turn.answer
    assert "21–84" in submission.turn.answer


def test_other_feature_planner_receives_actual_catalog_and_constrained_queries(indexed):
    import json

    provider = MockProvider(
        [
            {
                "mode": "search",
                "query": "checkout",
                "entity_type": "Endpoint",
                "relation_types": [],
                "direction": "outgoing",
                "candidate_index": 0,
            }
        ]
    )
    submission, _ = ask(indexed, "Thêm API chốt giỏ hàng vào file nào?", provider)
    assert submission.turn.status == "answered"
    assert len(provider.requests) == 1
    request = provider.requests[0]
    payload = json.loads(request.messages[-1]["content"])
    assert payload["reference_catalog"]
    assert any(entry["name"] == "checkout" for entry in payload["reference_catalog"])
    assert "checkout" in request.schema["properties"]["query"]["enum"]
    assert "reference_catalog" in request.messages[0]["content"]
