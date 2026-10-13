from dataclasses import replace

import pytest

from rkg.conversations.narrative import source_identity
from rkg.conversations.resolver import asks_source_location, source_location_only
from rkg.domain.models import Entity, EntityType


def node():
    return Entity(
        "logout",
        "repo",
        "snap",
        EntityType.CALLABLE,
        "logout",
        "app.auth.logout",
        file_path="app/auth.py",
        start_line=26,
    )


@pytest.mark.parametrize(
    "path",
    [
        "/home/private/auth.py",
        "../auth.py",
        "app\\auth.py",
        "app/\nauth.py",
        "app/`auth.py",
    ],
)
def test_location_rejects_unsafe_source_paths(path):
    assert source_identity(replace(node(), file_path=path), "vi") is None


@pytest.mark.parametrize("line", [None, 0, -1, True])
def test_location_does_not_invent_source_line(line):
    text = source_identity(replace(node(), start_line=line), "en")
    assert "`app/auth.py`" in text
    assert ":" not in text


def test_composite_question_is_not_reduced_to_location_only():
    assert not source_location_only(
        "logout uses which database, where is it defined?", node()
    )
    assert source_location_only("Where is logout defined in the source file?", node())
    assert not asks_source_location("`where` goi ham nao?")
