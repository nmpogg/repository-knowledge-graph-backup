import pytest

from rkg.conversations.change_guidance import change_intent, location
from rkg.domain.models import Entity, EntityType


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("Thêm API hủy đơn ở file nào?", "add"),
        ("them api moi vao file nao", "add"),
        ("Where should I add a new endpoint?", "add"),
        ("Muốn đổi logic checkout thì sửa ở đâu?", "modify"),
        ("Which file should I edit for checkout?", "modify"),
        ("Ai gọi hàm OrderService.release_stock?", None),
        ("Hàm checkout nằm ở file nào?", None),
        ("What does `app.add` call?", None),
    ],
)
def test_change_intent_keeps_existing_questions(question, expected):
    assert change_intent(question) == expected


@pytest.mark.parametrize("path", ["/host/source.py", "../outside.py", "bad`path.py"])
def test_unsafe_locations_are_not_suggested(path):
    entity = Entity("e", "repo", "snap", EntityType.CALLABLE, "f", "f", file_path=path)
    assert location(entity, "vi") is None


def test_missing_lines_are_not_invented():
    entity = Entity(
        "e", "repo", "snap", EntityType.CALLABLE, "f", "f", file_path="app.py"
    )
    assert location(entity, "vi") == "`app.py`"


def test_change_questions_resolve_language_without_identifier_interference():
    from rkg.conversations.language import effective_language

    assert effective_language("sua code cho checkout", "en") == "vi"
    assert effective_language("Where should I add a new endpoint?", "vi") == "en"
    assert effective_language("Modify `app.them.sua` code", "vi") == "en"


@pytest.mark.parametrize(
    "question,kind,name,qualified",
    [
        (
            "Thêm API trong nhóm orders ở đâu?",
            "Type",
            "OrderController",
            "api.OrderController",
        ),
        (
            "Sửa request cập nhật phía frontend ở đâu?",
            "Callable",
            "updateInventory",
            "client.InventoryApi.updateInventory",
        ),
        (
            "Sửa xử lý job gửi email ở đâu?",
            "Callable",
            "processEmailJob",
            "workers.processEmailJob",
        ),
        ("Sửa luồng xóa projection cũ ở đâu?", "Callable", "Run", "app.Cleanup.Run"),
    ],
)
def test_feature_hint_requires_unique_real_catalog_entry(
    question, kind, name, qualified
):
    from rkg.conversations.change_guidance import feature_reference

    entry = {"name": name, "qualified_name": qualified, "type": kind, "path": None}
    assert feature_reference(question, []) == ()
    assert feature_reference(question, [entry]) == (qualified,)
    other = entry | {"qualified_name": "another." + qualified}
    assert feature_reference(question, [entry, other]) == ()
