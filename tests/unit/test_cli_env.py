"""Local server configuration loaded by the CLI."""

import os

from rkg.cli import _load_local_env


def test_local_env_loads_server_settings_without_overriding_process(
    tmp_path, monkeypatch
):
    (tmp_path / ".env").write_text(
        "# local settings\n"
        "RKG_SESSION_TOKEN='from-file'\n"
        "OPENROUTER_MODEL=openai/test-model\n"
        "OPENROUTER_API_KEY=from-file-key\n"
        "VITE_RKG_SESSION=browser-only\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("RKG_SESSION_TOKEN", "from-process")
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("VITE_RKG_SESSION", raising=False)

    _load_local_env()

    assert os.environ["RKG_SESSION_TOKEN"] == "from-process"
    assert os.environ["OPENROUTER_MODEL"] == "openai/test-model"
    assert os.environ["OPENROUTER_API_KEY"] == "from-file-key"
    assert "VITE_RKG_SESSION" not in os.environ
