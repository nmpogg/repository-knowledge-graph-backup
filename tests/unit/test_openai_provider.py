"""Direct OpenAI routing and strict wire/local validation without remote calls."""

import copy
import json
import urllib.error
from pathlib import Path

import pytest

from rkg.cli import _load_local_env
from rkg.llm import (
    LLMError,
    OpenAIProvider,
    OpenRouterProvider,
    StructuredRequest,
    TurnBudget,
)
from rkg.llm.factory import configured_provider
from rkg.llm.openai import ENDPOINT, _post, wire_schema

SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {"enum": ["a", "b"]},
            "uniqueItems": True,
            "minItems": 1,
            "maxItems": 3,
        }
    },
    "required": ["items"],
    "additionalProperties": False,
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "urn:synthetic",
    "x-aide": {"key": "synthetic"},
}


def request(**kwargs):
    return StructuredRequest(
        messages=({"role": "user", "content": "Synthetic question"},),
        schema_name="synthetic",
        schema=SCHEMA,
        **kwargs,
    )


def reply(value=None):
    return {
        "choices": [
            {
                "finish_reason": "stop",
                "message": {"content": json.dumps(value or {"items": ["a"]})},
            }
        ],
        "usage": {"prompt_tokens": 17, "completion_tokens": 9},
    }


def test_openai_wire_payload_and_usage(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-openai")
    monkeypatch.setenv("OPENROUTER_API_KEY", "synthetic-other")
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    seen = {}

    def transport(payload, headers, timeout):
        seen.update(payload=payload, headers=headers, timeout=timeout)
        return reply()

    result = OpenAIProvider(transport).complete(request(), TurnBudget())
    assert result.value == {"items": ["a"]}
    assert (result.input_tokens, result.output_tokens, result.model, result.cost) == (
        17,
        9,
        "gpt-4o-mini",
        None,
    )
    payload = seen["payload"]
    assert set(payload) == {"model", "messages", "response_format", "stream", "store"}
    assert payload["store"] is False and payload["stream"] is False
    profile = payload["response_format"]["json_schema"]
    assert profile["strict"] is True and profile["name"] == "synthetic"
    assert profile["schema"]["properties"]["items"]["items"]["type"] == "string"
    assert "uniqueItems" not in profile["schema"]["properties"]["items"]
    assert not {"$schema", "$id", "x-aide"} & profile["schema"].keys()
    assert seen["headers"]["Authorization"] == "Bearer synthetic-openai"
    assert seen["timeout"] is None


def test_schema_projection_preserves_original_and_property_names():
    original = copy.deepcopy(SCHEMA)
    original["properties"]["x-aide"] = {"type": "string"}
    original["required"].append("x-aide")
    snapshot = copy.deepcopy(original)
    projected = wire_schema(original)
    assert original == snapshot
    assert projected["properties"]["x-aide"] == {"type": "string"}
    assert projected["properties"]["items"]["maxItems"] == 3
    assert projected["additionalProperties"] is False


@pytest.mark.parametrize(
    "filename", ["SCH-RKG-READ-PLAN-v2.json", "SCH-RKG-NARRATIVE-v1.json"]
)
def test_actual_model_profiles_project_without_artifact_metadata(filename):
    schema = json.loads(
        (Path(".aide/tech-specs/RKG-CONVERSATION/llm") / filename).read_text()
    )
    snapshot = copy.deepcopy(schema)
    projected = wire_schema(schema)

    def check(node):
        assert not {"$schema", "$id", "x-aide", "uniqueItems"} & node.keys()
        if "enum" in node:
            assert node["type"] == "string"
        if node.get("type") == "object":
            assert node["additionalProperties"] is False
            assert set(node["required"]) == set(node["properties"])
        for child in node.get("properties", {}).values():
            check(child)
        if "items" in node:
            check(node["items"])

    check(projected)
    assert schema == snapshot


@pytest.mark.parametrize(
    "value",
    [
        {"items": ["a", "a"]},
        {"items": ["invented"]},
        {"items": []},
        {"items": ["a"], "extra": True},
    ],
)
def test_original_schema_still_enforced(monkeypatch, value):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic")
    with pytest.raises(LLMError, match="llm_malformed_response"):
        OpenAIProvider(lambda *_: reply(value)).complete(request(), TurnBudget())


@pytest.mark.parametrize(
    "data",
    [
        None,
        [],
        {},
        {"choices": []},
        {"choices": [None]},
        {"choices": [{}]},
        {"choices": [{"finish_reason": "stop", "message": None}]},
        {
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {"content": None, "refusal": "synthetic"},
                }
            ]
        },
        {
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {"content": '{"items":["a"]}', "refusal": "synthetic"},
                }
            ]
        },
        {
            "choices": [
                {"finish_reason": "content_filter", "message": {"content": None}}
            ]
        },
    ],
)
def test_malformed_or_refused_completion_is_safe(monkeypatch, data):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic")
    with pytest.raises(LLMError, match="llm_malformed_response"):
        OpenAIProvider(lambda *_: data).complete(request(), TurnBudget())


def test_model_and_explicit_finite_budget(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o")
    seen = {}

    def transport(payload, headers, timeout):
        seen.update(payload=payload, timeout=timeout)
        return reply()

    result = OpenAIProvider(transport).complete(
        request(max_output_tokens=100), TurnBudget(timeout_seconds=10)
    )
    assert result.model == "gpt-4o"
    assert seen["payload"]["max_completion_tokens"] == 100
    assert 0 < seen["timeout"] <= 10


@pytest.mark.parametrize(
    "setting, expected",
    [
        (None, OpenRouterProvider),
        ("openrouter", OpenRouterProvider),
        ("openai", OpenAIProvider),
    ],
)
def test_provider_selection(monkeypatch, setting, expected):
    if setting is None:
        monkeypatch.delenv("RKG_LLM_PROVIDER", raising=False)
    else:
        monkeypatch.setenv("RKG_LLM_PROVIDER", setting)
    assert isinstance(configured_provider(), expected)


def test_invalid_provider_is_not_silent_fallback(monkeypatch):
    monkeypatch.setenv("RKG_LLM_PROVIDER", "synthetic-invalid")
    with pytest.raises(LLMError, match="llm_invalid_request"):
        configured_provider()


def test_selected_missing_key_does_not_use_other_provider(monkeypatch):
    monkeypatch.setenv("RKG_LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("OPENROUTER_API_KEY", "synthetic-other")
    provider = configured_provider()
    assert provider.enabled is False
    with pytest.raises(LLMError, match="llm_disabled"):
        provider.complete(request(), TurnBudget())


def test_server_env_loads_openai_settings_with_process_precedence(
    tmp_path, monkeypatch
):
    (tmp_path / ".env").write_text(
        "RKG_LLM_PROVIDER=openai\nOPENAI_API_KEY=synthetic-file\nOPENAI_MODEL=gpt-4o-mini\nVITE_OPENAI_API_KEY=forbidden\n"
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("RKG_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("VITE_OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-process")
    _load_local_env()
    import os

    assert os.environ["RKG_LLM_PROVIDER"] == "openai"
    assert os.environ["OPENAI_API_KEY"] == "synthetic-process"
    assert os.environ["OPENAI_MODEL"] == "gpt-4o-mini"
    assert "VITE_OPENAI_API_KEY" not in os.environ


def test_fixed_openai_http_endpoint(monkeypatch):
    seen = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def read(self, size):
            assert size == 1_000_001
            return json.dumps(reply()).encode()

    def urlopen(req, timeout):
        seen.update(
            url=req.full_url,
            method=req.method,
            payload=json.loads(req.data),
            timeout=timeout,
        )
        return Response()

    monkeypatch.setattr(
        "urllib.request.OpenerDirector.open",
        lambda _opener, *args, **kwargs: urlopen(*args, **kwargs),
    )
    assert (
        _post({"synthetic": True}, {"Authorization": "Bearer synthetic"}, None)
        == reply()
    )
    assert seen["url"] == ENDPOINT == "https://api.openai.com/v1/chat/completions"
    assert seen["method"] == "POST" and seen["timeout"] is None


@pytest.mark.parametrize(
    "code, expected",
    [(401, "llm_provider_error"), (429, "llm_provider_error"), (504, "llm_timeout")],
)
def test_http_errors_never_echo_remote_body(monkeypatch, code, expected):
    def urlopen(*args, **kwargs):
        raise urllib.error.HTTPError(
            ENDPOINT, code, "synthetic-sensitive-body", {}, None
        )

    monkeypatch.setattr(
        "urllib.request.OpenerDirector.open",
        lambda _opener, *args, **kwargs: urlopen(*args, **kwargs),
    )
    with pytest.raises(LLMError) as error:
        _post({}, {}, None)
    assert str(error.value) == expected


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
def test_fixed_transport_rejects_redirect_without_forwarding_key(monkeypatch, status):
    import io
    import urllib.request
    import urllib.response
    from email.message import Message

    seen = []

    class SyntheticHTTPS(urllib.request.HTTPSHandler):
        def https_open(self, req):
            seen.append(req)
            headers = Message()
            if req.full_url == ENDPOINT:
                headers["Location"] = "https://synthetic-other.invalid/collect"
                response = urllib.response.addinfourl(
                    io.BytesIO(b""), headers, req.full_url, status
                )
            else:
                response = urllib.response.addinfourl(
                    io.BytesIO(json.dumps(reply()).encode()), headers, req.full_url, 200
                )
            response.msg = "synthetic"
            return response

    monkeypatch.setattr("urllib.request.HTTPSHandler", SyntheticHTTPS)
    monkeypatch.setattr("urllib.request._opener", None)
    with pytest.raises(LLMError, match="llm_provider_error"):
        _post({}, {"Authorization": "Bearer synthetic-only"}, None)
    assert len(seen) == 1
    assert seen[0].full_url == ENDPOINT


def test_invalid_provider_cli_exits_with_safe_json(tmp_path, monkeypatch, capsys):
    from rkg.cli import main

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("RKG_LLM_PROVIDER", "synthetic-invalid")
    monkeypatch.setenv("RKG_SESSION_TOKEN", "synthetic")
    assert main(["--db", str(tmp_path / "synthetic.kuzu"), "serve"]) == 1
    captured = capsys.readouterr()
    assert json.loads(captured.out) == {"error_code": "llm_invalid_request"}
    assert captured.err == ""


def test_openai_wire_omits_string_length_but_original_validator_rejects_it(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic")
    schema = {
        "type": "object",
        "properties": {"query": {"type": "string", "minLength": 1, "maxLength": 3}},
        "required": ["query"],
        "additionalProperties": False,
    }
    projected = wire_schema(schema)
    assert projected["properties"]["query"] == {"type": "string"}
    for value in ["", "abcd"]:
        req = StructuredRequest(
            messages=({"role": "user", "content": "Synthetic"},),
            schema_name="synthetic",
            schema=schema,
        )
        with pytest.raises(LLMError, match="llm_malformed_response"):
            OpenAIProvider(lambda *_: reply({"query": value})).complete(
                req, TurnBudget()
            )
    assert schema["properties"]["query"]["maxLength"] == 3
