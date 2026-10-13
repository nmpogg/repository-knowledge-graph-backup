---
{
  "key": "TEST-RKG-CHATBOT-L3-001",
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
      ".aide/tech-specs/RKG-TRANSPORT/api/API-RKG-CORE-v1.md": "d73b75134b57955ae827baca16408e91b467ded0b027ccea28f58c7e536b77ce",
      ".aide/tech-specs/RKG-TRANSPORT/api/SCH-RKG-CONVERSATION-v1.json": "d7991763c99ac815caa5b271045f10d6d0b6743f1b52b82765ddccdbad6cf574",
      ".aide/tech-specs/RKG-TRANSPORT/api/OAS-RKG-CONVERSATION-v1.json": "fbf37df09fa390bb5155608424bc0c7ce01b7e88940f2fc3d3a4beac32397a02",
      ".aide/tech-specs/RKG-GRAPH/schema/TBL-RKG-GRAPH.md": "a624df781b47be8e631dc3e85a1140a555fb5a121012ab6ba929f4c438c305ac",
      ".aide/tech-specs/RKG-GRAPH/schema/DDL-RKG-GRAPH.cypher": "b912230b0b7039906ae6fd8b9500a69bdcccff06bbc485ed2f494afadc084de4",
      ".aide/tech-specs/RKG-GRAPH/schema/MIG-RKG-CHATBOT-v3.cypher": "04030c6d33a1780ab8ba5c8247d247b539d28305f9b685aa85485f706798e571",
      ".aide/tech-specs/RKG-CONVERSATION/llm/SCH-RKG-NARRATIVE-v1.json": "8155b0bdc464a4adae07a48911d684bdf01b3afe7b0cb4a5e1624dc3d5f71394",
      ".aide/tech-specs/RKG-CONVERSATION/llm/SCH-RKG-READ-PLAN-v2.json": "0908b8a657b6b96a1f848ee4cfd511238ed195b871fb8785e6f4d5c33c5d7336",
      ".aide/design/ui/UIS-RKG-001.md": "d849542a45c36420e35c7aa48d649884832c334224b7b73cc923de9c34e4851d",
      ".aide/tech-specs/RKG-CONVERSATION/CON-RKG-CONVERSATION-v1.md": "e66334ee24d46d476acd0920ec9344b0fc34bc84a8bdd8ff054cbaafee9620c4",
      "tools/verify_chatbot_l3.py": "4d1f5987313d971531550fbb27cb6a437b7168d86095c433a63d1badb9ac5f9d"
    },
    "raw_results": {
      "path": ".aide/evidence/tests/contracts/RES-RKG-CHATBOT-L3-001.json",
      "sha256": "ecb22a8584d20ea6001571c3b0be2e45186a1638b696f91c6e217e4c2d4c3220"
    }
  },
  "checks": {
    "schema_meta_validation": "passed",
    "oas_local_structure": "passed",
    "legacy_and_new_wire_fixtures": "passed",
    "negative_schema_cases": 11,
    "reference_contract_fixture_positive": 5,
    "reference_contract_fixture_negative": 8,
    "TBL_DDL_extract_equal": "passed",
    "fresh_Kuzu_DDL_25_tables": "passed",
    "atomic_v2_v3_preserves_legacy": "passed",
    "migration_replay_no_op": "passed",
    "migration_fault_rolls_back_column_and_version": "passed",
    "metadata_roundtrip_reopen": "passed",
    "production_dispatcher_and_API_UI_integration": "not_run",
    "live_provider_quality": "not_run",
    "existing_DDL_pytest": "passed_2_of_2"
  },
  "closes_gates": false,
  "implementation_ready": false,
  "classification": "internal",
  "ai_assisted": true
}
---

# TEST-RKG-CHATBOT-L3-001 — Current-tree L3 schemas and physical execution

Author checks only: Draft-2020-12 schemas and local OpenAPI structure pass;
legacy/new wire fixtures include locale, provider-ready flag, nullable legacy
metadata and source/filesystem location. Eleven negative schema cases reject
invalid types/extra fields/free factual text/unsafe locations. A reference-rule
fixture oracle accepts five paths and rejects eight foreign/disconnected/cyclic/
direction/root/anchor/relation/evidence selections. It is not the production
grounding validator or runtime AC acceptance.

DDL equals TBL r13 fenced statements and executes on Kuzu 0.11.3, retaining
12 node/13 relationship names. Existing DDL smoke tests: 2/2 passed. Isolated
2→3 migration preserves old turn/conversation/edge/evidence properties and
null legacy metadata, verifies no-op replay, and rolls back column/version on
injected failure. New-row metadata round-trips across Kuzu reopen without
backfilling the old turn. No operator database is read/migrated. Records contain
hashes/counts, never transcripts or database paths.

Production dispatcher stays at version 2 and API/UI/provider code is pre-delta.
New runtime/integration/live quality is not_run. No task done/gate approval inferred.
