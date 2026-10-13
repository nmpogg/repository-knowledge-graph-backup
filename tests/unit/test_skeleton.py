"""Smoke test: package skeleton is importable."""

from rkg import __version__


def test_package_version() -> None:
    assert __version__ == "0.1.0"


def test_import_rkg() -> None:
    import rkg

    assert rkg.__name__ == "rkg"
