"""Compare the L3 candidate with current runtime inputs and API-r15 projection.

Machine classification is scoped to this additive conversation slice. Untyped
runtime OpenAPI cannot prove response or behavioral compatibility; record that
limit explicitly. No provider/API calls or repository-source execution occur.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

import jsonschema

from rkg.api import create_app
from rkg.api.conversations import TurnCreate
from rkg.conversations.identity import request_fingerprint
from rkg.ingestion import LocalSourcePolicy
from rkg.llm import MockProvider
from rkg.storage import Storage

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / ".aide/tech-specs/RKG-TRANSPORT/api"


def run():
    candidate = json.loads((API / "SCH-RKG-CONVERSATION-v1.json").read_text())
    oas = json.loads((API / "OAS-RKG-CONVERSATION-v1.json").read_text())
    request = candidate["$defs"]["TurnRequest"]
    old_body = TurnCreate.model_json_schema()
    assert set(old_body["required"]) == set(request["required"])
    assert set(request["properties"]) - set(old_body["properties"]) == {"ui_locale"}
    assert old_body["additionalProperties"] is False
    assert request["additionalProperties"] is False

    # Normative r15 limits, already enforced by the pre-delta application service.
    normalized_legacy = json.loads(json.dumps(old_body))
    normalized_legacy["properties"]["question"].update(
        {"minLength": 1, "maxLength": 2000}
    )
    normalized_legacy["properties"]["client_request_id"]["minLength"] = 1
    normalized_legacy["properties"]["expected_revision"]["minimum"] = 1
    for prop in ("question", "client_request_id", "expected_revision"):
        old = {
            k: v
            for k, v in normalized_legacy["properties"][prop].items()
            if k not in {"title", "description", "default"}
        }
        assert request["properties"][prop] == old
    assert request["properties"]["root_id"] == {"type": ["string", "null"]}
    assert normalized_legacy["properties"]["root_id"]["anyOf"] == [
        {"type": "string"},
        {"type": "null"},
    ]
    legacy_response_fields = {
        "schema_version",
        "conversation_id",
        "turn_id",
        "sequence",
        "revision",
        "repository_id",
        "snapshot_id",
        "status",
        "question",
        "resolved_question",
        "answer",
        "claims",
        "citations",
        "candidate_entities",
        "limitations",
        "retrieval_truncated",
        "history_truncated",
        "context_turn_ids",
        "usage",
        "error_code",
    }
    assert legacy_response_fields <= set(
        candidate["$defs"]["TurnSubmitResponse"]["properties"]
    )
    assert "response_metadata" not in candidate["$defs"]["Turn"]["required"]
    assert (
        "response_metadata" not in candidate["$defs"]["TurnSubmitResponse"]["required"]
    )
    assert "citation_indexes" not in candidate["$defs"]["Claim"]["required"]
    assert "edge_id" not in candidate["$defs"]["Citation"]["required"]
    assert "snapshot_available" not in candidate["$defs"]["HistoryResponse"]["required"]

    with tempfile.TemporaryDirectory(prefix="rkg-oas-check-") as tmp:
        directory = Path(tmp)
        with Storage(directory / "db") as storage:
            app = create_app(
                storage,
                LocalSourcePolicy((directory,)),
                session_token="fixture-only",
                provider=MockProvider([]),
            )
            deployed = app.openapi()
    old_path = "/api/v1/conversations/{conversation_id}/turns"
    original_get = deployed["paths"][old_path]["get"]
    target_get = oas["paths"][old_path]["get"]
    old_parameters = {p["name"]: p for p in original_get["parameters"]}
    new_parameters = {p["name"]: p for p in target_get["parameters"]}
    assert set(new_parameters) - set(old_parameters) == {"include_unavailable"}
    assert not new_parameters["include_unavailable"]["required"]
    assert new_parameters["include_unavailable"]["schema"]["default"] is False
    for name in old_parameters:
        assert new_parameters[name]["required"] == old_parameters[name]["required"]
        if name in {"offset", "limit"}:
            assert (
                new_parameters[name]["schema"]["default"]
                == old_parameters[name]["schema"]["default"]
            )
    assert set(oas["paths"]) - set(deployed["paths"]) == {
        "/api/v1/conversations/capabilities",
        "/api/v1/conversations/{conversation_id}/turns/{turn_id}/citations/{citation_index}",
    }
    # All default-vi inputs preserve the existing hash, including whitespace/root null.
    variants = [None, "", "fixture-root"]
    for root in variants:
        payload = {"question": " fixture-only ", "root_id": root}
        expected = hashlib.sha256(
            json.dumps(
                payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
            ).encode()
        ).hexdigest()
        assert request_fingerprint(payload["question"], root) == expected
        for locale in (None, "vi", "en"):
            body = {
                "question": payload["question"],
                "root_id": root,
                "client_request_id": "k" * 300,
                "expected_revision": 1,
                "ui_locale": locale,
            }
            jsonschema.validate(body, request)
            normalized = dict(payload)
            if locale == "en":
                normalized["ui_locale"] = "en"
            fingerprint = hashlib.sha256(
                json.dumps(
                    normalized,
                    sort_keys=True,
                    ensure_ascii=False,
                    separators=(",", ":"),
                ).encode()
            ).hexdigest()
            assert (fingerprint == expected) is (locale != "en")

    result = {
        "classification": "wire_additive_with_capability_negotiation",
        "breaking_wire_changes_detected": [],
        "comparison": (
            "current runtime request/query OpenAPI plus "
            "API-r15 normative response-field/limit projection"
        ),
        "retained_legacy_POST_fields": sorted(legacy_response_fields),
        "new_paths": sorted(set(oas["paths"]) - set(deployed["paths"])),
        "new_optional_request_fields": ["ui_locale"],
        "new_optional_query_fields": ["include_unavailable=false"],
        "new_optional_response_fields": [
            "response_metadata",
            "citation_indexes",
            "citation.edge_id",
            "snapshot_available",
        ],
        "default_locale_fingerprint_compatibility": "passed",
        "counterpart_acknowledgements": "pending_Contract_Gate",
        "database_compatibility": (
            "SchemaMeta v3 requires coordinated backend upgrade; "
            "old v2 binary refuses v3"
        ),
        "limits": [
            "Deployed OpenAPI response schemas are untyped; "
            "this is not a full oasdiff equivalence proof.",
            "No HTTP runtime parity, new-server/old-client integration, "
            "or live provider quality tested.",
            "Old extra-forbid server rejects new request fields; "
            "negotiation/backend-first rollout is mandatory.",
            "All unchanged routes outside the conversation slice "
            "remain on their current contract.",
        ],
        "source_hashes": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [
                Path(__file__),
                API / "API-RKG-CORE-v1.md",
                API / "SCH-RKG-CONVERSATION-v1.json",
                API / "OAS-RKG-CONVERSATION-v1.json",
            ]
        },
        "deployed_input_snapshot": {
            "TurnCreate": old_body,
            "history_parameters": original_get["parameters"],
        },
    }
    Path("/tmp/rkg-chatbot-api-diff.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(
        result["classification"]
        + "; no wire removals or new required fields; runtime parity not_run"
    )


if __name__ == "__main__":
    run()
