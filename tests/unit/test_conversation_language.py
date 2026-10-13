import pytest

from rkg.conversations.identity import request_fingerprint
from rkg.conversations.language import effective_language, is_greeting


@pytest.mark.parametrize(
    ("text", "locale", "expected"),
    [
        ("auth.login", "en", "en"),
        ("GET /đơn_hàng", "en", "en"),
        ("What does `đăng_nhập` call?", "vi", "en"),
        ("endpoint login dang goi nhung ham nao", "en", "vi"),
        ("auth.login gọi những hàm nào?", "en", "vi"),
        ("Which functions does auth.login call?", "vi", "en"),
        ("2", "en", "en"),
        ("login", None, "vi"),
        ("alo", "en", "vi"),
    ],
)
def test_effective_language_excludes_identifiers(text, locale, expected):
    assert effective_language(text, locale) == expected


def test_locale_identity_preserves_legacy_body():
    old = request_fingerprint(" auth.login ", None)
    assert old == request_fingerprint(" auth.login ", None, ui_locale="vi")
    assert old == request_fingerprint(" auth.login ", None, ui_locale=None)
    assert old != request_fingerprint(" auth.login ", None, ui_locale="en")
    assert old != request_fingerprint("auth.login", None)


def test_greetings_are_only_whole_messages():
    assert is_greeting("Xin chào!")
    assert is_greeting("hello")
    assert not is_greeting("hello, what does auth.login call?")


@pytest.mark.parametrize(
    ("text", "locale", "language"),
    [
        ("Giải thích `auth.login`", "en", "vi"),
        ("List functions invoked by `auth.login`", "vi", "en"),
        ("giai thich `auth.login`", "en", "vi"),
    ],
)
def test_clear_prose_overrides_opposite_locale(text, locale, language):
    assert effective_language(text, locale) == language


def test_natural_typed_subject_precedes_does_keyword():
    from rkg.conversations.resolver import explicit_lookup

    assert explicit_lookup("What does endpoint login call?").query == "login"
    assert explicit_lookup("What does endpoint login call?").entity_type == "Endpoint"
    assert explicit_lookup("What does function login call?").entity_type == "Callable"
