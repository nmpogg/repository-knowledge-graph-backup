"""Default terminal levels, correlation and verbatim log content."""

import json
import os
import subprocess
import sys

from rkg.cli import _parser


def test_serve_exposes_debug_log_level():
    assert _parser().parse_args(["serve", "--log-level", "debug"]).log_level == "debug"
    assert _parser().parse_args(["serve"]).log_level == "info"


def test_actual_console_info_vs_debug_preserves_content():
    program = """
from rkg.terminal_logging import (
    configure_terminal_logging, log_event, log_debug, log_context
)
import sys
configure_terminal_logging(sys.argv[1])
configure_terminal_logging(sys.argv[1])
with log_context(request_id="test-request", turn_id="test-turn"):
    log_event("stage_started", stage="narrative", model_calls=0)
    log_debug("model_request", messages=[{
        "content":"synthetic-prompt body and synthetic-server-key"
    }])
    log_debug("model_response", content="synthetic-response-body")
log_event("after_turn")
"""
    env = dict(
        os.environ,
        OPENAI_API_KEY="synthetic-server-key",
        OPENROUTER_API_KEY="",
        RKG_SESSION_TOKEN="",
    )
    for level in ["info", "debug"]:
        result = subprocess.run(
            [sys.executable, "-c", program, level],
            env=env,
            text=True,
            capture_output=True,
            check=True,
        )
        lines = result.stderr.splitlines()
        assert sum("event=stage_started" in line for line in lines) == 1
        assert "request_id=test-request" in next(
            line for line in lines if "event=stage_started" in line
        )
        assert "test-turn" not in next(
            line for line in lines if "event=after_turn" in line
        )
        assert ("synthetic-server-key" in result.stderr) == (level == "debug")
        assert ("synthetic-prompt" in result.stderr) == (level == "debug")
        assert ("synthetic-response-body" in result.stderr) == (level == "debug")


def test_concurrent_contexts_reset():
    import asyncio

    from rkg.terminal_logging import current_context, log_context

    async def worker(identifier):
        with log_context(turn_id=identifier):
            await asyncio.sleep(0)
            assert current_context()["turn_id"] == identifier
        assert current_context() == {}

    async def run():
        await asyncio.gather(worker("left"), worker("right"))

    asyncio.run(run())


def test_console_preserves_paths_keys_and_nested_json():
    program = """
import json
from rkg.terminal_logging import configure_terminal_logging, log_context, log_event
configure_terminal_logging()
with log_context(request_id="synthetic-server-key"):
    log_event("verbatim", path="/synthetic/host/source.py", key="synthetic-server-key",
              nested=json.dumps({"key": "synthetic-server-key"}))
"""
    result = subprocess.run(
        [sys.executable, "-c", program],
        env=dict(os.environ, OPENAI_API_KEY="synthetic-server-key"),
        text=True,
        capture_output=True,
        check=True,
    )
    assert "request_id=synthetic-server-key" in result.stderr
    detail = json.loads(result.stderr.split("detail=", 1)[1])
    assert detail["path"] == "/synthetic/host/source.py"
    assert detail["key"] == "synthetic-server-key"
    assert json.loads(detail["nested"])["key"] == "synthetic-server-key"
    assert "[masked]" not in result.stderr


def test_debug_http_error_backslash_near_match_finishes_promptly():
    program = """
import io, json, time, urllib.error, urllib.request
from rkg.terminal_logging import configure_terminal_logging
from rkg.llm.http import post_json
from rkg.llm import LLMError
configure_terminal_logging("debug")
body = ("synthetic-prefix-" + chr(92) * 50000 + "wrong").encode()
class Opener:
    def open(self, *args, **kwargs):
        raise urllib.error.HTTPError("https://example.invalid", 429,
                                     "synthetic", {}, io.BytesIO(body))
urllib.request.build_opener = lambda *args: Opener()
start = time.perf_counter()
try:
    post_json("https://example.invalid", {}, {}, None)
except LLMError as exc:
    print(json.dumps({"code": str(exc), "elapsed": time.perf_counter() - start}))
"""
    env = dict(
        os.environ,
        OPENAI_API_KEY="",
        OPENROUTER_API_KEY="",
        RKG_SESSION_TOKEN="synthetic-prefix-\\z",
        VITE_RKG_SESSION="",
    )
    result = subprocess.run(
        [sys.executable, "-c", program],
        env=env,
        text=True,
        capture_output=True,
        check=True,
        timeout=3,
    )
    summary = json.loads(result.stdout)
    assert summary["code"] == "llm_provider_error"
    assert summary["elapsed"] < 1
    assert "event=provider_http_error" in result.stderr


def test_serve_keeps_default_access_logging(monkeypatch):
    from contextlib import nullcontext

    from rkg import cli

    runs = []
    app = object()
    monkeypatch.setattr(cli, "_load_local_env", lambda: None)
    monkeypatch.setattr(cli, "Storage", lambda path: nullcontext(object()))
    monkeypatch.setattr(cli, "recover_interrupted_jobs", lambda storage: None)
    monkeypatch.setattr(cli, "create_app", lambda *args, **kwargs: app)
    monkeypatch.setattr(cli, "configure_terminal_logging", lambda level: None)
    monkeypatch.setattr(
        cli.uvicorn, "run", lambda api, **kwargs: runs.append((api, kwargs))
    )
    monkeypatch.setenv("RKG_SESSION_TOKEN", "synthetic-session")
    assert cli.main(["serve"]) == 0
    assert runs[0][0] is app
    assert runs[0][1].get("access_log", True) is True
    assert runs[0][1]["log_level"] == "info"
    assert cli.main(["serve", "--log-level", "debug"]) == 0
    assert runs[1][1]["log_level"] == "debug"
