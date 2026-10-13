---
{
  "key": "TEST-RKG-L3-PACKAGE-001",
  "type": "test-evidence",
  "group": "evidence",
  "system": "SYS-RKG",
  "revision": 1,
  "captured_at": "2026-10-06T15:38:16+07:00",
  "change_set": "CHG-RKG-2026-002",
  "verification_mode": "author_package_integrity_not_independent_review",
  "captured_against": {
    "base_code_commit": "86ecab6546384227d1901e24c8b8fbfc6c0e8527",
    "files": [
      {
        "key": "BL-CHG-RKG-2026-002-r7",
        "path": ".aide/lifecycle/change-sets/CHG-RKG-2026-002/baseline/BL-CHG-RKG-2026-002-r7.yaml",
        "sha256": "f9eeca88e612a3446c4cca9c531bb7b9906b3433e378f209889c08ff50914526"
      },
      {
        "key": "CTX-CHG-RKG-2026-002-r10",
        "path": ".aide/evidence/context/CTX-CHG-RKG-2026-002-r10.yaml",
        "sha256": "de6985e92c64ba4fa7bdefaba1959111b3c8be2a9456568249e121982698a9c2"
      },
      {
        "key": "CHG-RKG-2026-002",
        "path": ".aide/lifecycle/change-sets/CHG-RKG-2026-002/change-set.yaml",
        "sha256": "541a079ea591df16d1f3120ced9bda9c9064687038ea77cbb10215d825553341"
      },
      {
        "key": "LCV-RKG-CHATBOT-001",
        "path": ".aide/generated/contract-views/LCV-RKG-CHATBOT-001.md",
        "sha256": "d18d5ae71743ea5797dcde35b0cc004288cdc6aaad427c58f6086fd57ff255dc"
      },
      {
        "key": "PROMPT-RKG-CHATBOT-L3-001",
        "path": ".aide/reviewer/prompts/PROMPT-RKG-CHATBOT-L3-001.md",
        "sha256": "5858d2e2bf2b4e06a69751dbe317193041eac058d913bda3e50a53f44b6cf269"
      }
    ]
  },
  "checks": {
    "all_36_normative_source_pins": "passed",
    "L3_candidate_identity_revision_and_heading": "passed",
    "signed_Scope_L2_UI_bytes_unchanged": "passed",
    "derived_contract_view_reproducible": "passed",
    "four_consumers_from_normative_relations": "passed_acknowledgement_pending",
    "all_historical_evidence_and_baselines_unchanged": "passed",
    "product_source_and_task_status_unchanged": "passed",
    "Scope_Architecture_UIUX_approved_Contract_pending": "passed",
    "independent_L3_review_and_runtime_integration": "not_run"
  },
  "implementation_ready": false,
  "closes_gates": false,
  "classification": "internal",
  "ai_assisted": true
}
---

# TEST-RKG-L3-PACKAGE-001 — Frozen L3 review package integrity

All 36 current-tree normative hashes/revisions match baseline r7. New L3 keys,
filenames and primary headings agree. Unrelated historical reference naming was
not changed or certified by this scoped check. Signed Scope/L2/UX level-1–3
bytes remain frozen; their scoped approvals stay valid.

The L3 view reproduces exactly; four consumer dependency edges derive from
current constrained_by/owned_by relations, with acknowledgement still pending.
All prior evidence/baseline bytes remain append-only, including historical
not_run results. Product source/tests/task statuses are unchanged.

Independent contract review/signature, consumer acknowledgement, new runtime
API/UI/storage dispatcher and live quality are not_run/pending. The candidate
is ready for review, not implementation/release. Physical candidate execution
used only disposable synthetic databases.
