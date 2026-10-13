---
{
  "key": "TEST-RKG-CHATBOT-API-DIFF-001",
  "type": "test-evidence",
  "group": "evidence",
  "system": "SYS-RKG",
  "revision": 1,
  "captured_at": "2026-10-06T15:31:41+07:00",
  "change_set": "CHG-RKG-2026-002",
  "verification_mode": "author_contract_checks_not_independent_review",
  "captured_against": {
    "base_code_commit": "86ecab6546384227d1901e24c8b8fbfc6c0e8527",
    "baseline": {
      "key": "BL-CHG-RKG-2026-002-r7",
      "path": ".aide/lifecycle/change-sets/CHG-RKG-2026-002/baseline/BL-CHG-RKG-2026-002-r7.yaml",
      "sha256": "f9eeca88e612a3446c4cca9c531bb7b9906b3433e378f209889c08ff50914526"
    },
    "source_hashes": {
      "tools/check_chatbot_api_compatibility.py": "5dbd780240b642932160622d712e11b7fd33d6d891a49b38c0a4055cf1f149b0",
      ".aide/tech-specs/RKG-TRANSPORT/api/API-RKG-CORE-v1.md": "d73b75134b57955ae827baca16408e91b467ded0b027ccea28f58c7e536b77ce",
      ".aide/tech-specs/RKG-TRANSPORT/api/SCH-RKG-CONVERSATION-v1.json": "d7991763c99ac815caa5b271045f10d6d0b6743f1b52b82765ddccdbad6cf574",
      ".aide/tech-specs/RKG-TRANSPORT/api/OAS-RKG-CONVERSATION-v1.json": "fbf37df09fa390bb5155608424bc0c7ce01b7e88940f2fc3d3a4beac32397a02"
    },
    "raw_results": {
      "path": ".aide/evidence/tests/contracts/DIF-RKG-CHATBOT-001.json",
      "sha256": "05b41f759e40bee3a62e39a115b87bc0133b2c69f43f5df3d84ac349a8d03bac"
    }
  },
  "checks": {
    "machine_classification": "wire_additive_with_capability_negotiation",
    "runtime_parity": "not_run"
  },
  "closes_gates": false,
  "implementation_ready": false,
  "classification": "internal",
  "ai_assisted": true
}
---

# TEST-RKG-CHATBOT-API-DIFF-001 — Scoped machine API compatibility analysis

Comparator checks current TurnCreate/query OpenAPI and API-r15 normative limits/
response-field projection against target definitions. It finds optional locale/
query/response additions and two new paths, retaining old required fields.
Default locale hashes retain exact raw question/root semantics; en differs.
Whitespace, null/empty root and long request keys retain their accepted shapes.

Classification: wire_additive_with_capability_negotiation. Old response OpenAPI
is untyped: this scoped result is not full oasdiff equivalence or HTTP/client
parity. Old extra-forbid server rejects a new locale field, so negotiation and
backend-first rollout are mandatory. Schema version 3 requires a coordinated
binary upgrade and protected-backup rollback, with consumer acknowledgements
pending in the normative changelog.

No provider/API request or analyzed source executes; only app-factory OpenAPI
introspection in isolated storage. No config values/credentials/transcripts exported.
