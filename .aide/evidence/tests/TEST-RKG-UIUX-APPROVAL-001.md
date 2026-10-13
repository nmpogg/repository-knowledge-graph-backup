---
{
  "key": "TEST-RKG-UIUX-APPROVAL-001",
  "type": "test-evidence",
  "group": "evidence",
  "system": "SYS-RKG",
  "revision": 1,
  "captured_at": "2026-10-06T14:40:42+07:00",
  "change_set": "CHG-RKG-2026-002",
  "verification_mode": "deterministic_approval_integrity_not_independent_review",
  "captured_against": {
    "base_code_commit": "86ecab6546384227d1901e24c8b8fbfc6c0e8527",
    "files": [
      {
        "key": "approval-010",
        "path": ".aide/evidence/approvals/approval-010.yaml",
        "sha256": "fca497514cb214e5a18550c7ca7132bc5a1dc3651ce278ac6790159eb459c43a"
      },
      {
        "key": "BL-CHG-RKG-2026-002-r6",
        "path": ".aide/lifecycle/change-sets/CHG-RKG-2026-002/baseline/BL-CHG-RKG-2026-002-r6.yaml",
        "sha256": "5c7f22bf448f7c0883bdac7d7189700ad1da3c71ba108592005e360e2b44b4b6"
      },
      {
        "key": "CTX-CHG-RKG-2026-002-r9",
        "path": ".aide/evidence/context/CTX-CHG-RKG-2026-002-r9.yaml",
        "sha256": "af9e1bd3c05469d4324dd4d28b2269a8afdf1ca806cf5040853a07c92fcfce4b"
      },
      {
        "key": "CHG-RKG-2026-002",
        "path": ".aide/lifecycle/change-sets/CHG-RKG-2026-002/change-set.yaml",
        "sha256": "36b6d93674f12967d59b28d79a3d94f04c917606e168567f39cc6ef19067901d"
      },
      {
        "key": "GATE-RKG-UIUX",
        "path": ".aide/policies/gates/GATE-RKG-UIUX.md",
        "sha256": "1a2f9c73ad48d1d450e6d537e3af6596971ff356303c50a96d470679a2215787"
      },
      {
        "key": "PLAN-CHG-RKG-2026-002-r4",
        "path": ".aide/evidence/plans/PLAN-CHG-RKG-2026-002-r4.md",
        "sha256": "2e22db035aca5f12dd8cbacd421f3aad726744f0660113ab7cc7033b920a90f8"
      }
    ]
  },
  "checks": {
    "named_ProductOwner_DesignOwner_QALead_authority": "passed",
    "human_walkthrough_attestation_attributed_not_agent_observation": "passed",
    "three_UI_revisions_hashes_match_reviewed_preview": "passed",
    "preview_bundle_unchanged": "passed",
    "27_current_baseline_source_pins": "passed",
    "policy_delta_only_signed_design_unchanged": "passed",
    "prior_evidence_and_baselines_append_only": "passed",
    "source_status_draft_with_explicit_scoped_baseline_approval": "passed",
    "derived_views_reproducible": "passed",
    "scope_architecture_UIUX_approved_contract_pending": "passed",
    "product_source_unchanged_no_implementation_task_marked_done": "passed",
    "production_runtime_live_provider_UAT_release": "not_run"
  },
  "closes_gates": false,
  "classification": "internal",
  "ai_assisted": true
}
---

# TEST-RKG-UIUX-APPROVAL-001 — Scoped named UI/UX approval integrity

Approval-010 attributes the decision to PhongNM as Product Owner, Design Owner
and QA Lead. Exact UXF r5, SCR r9 and UID r8 source bytes and reviewed preview
bundle remain unchanged. Baseline r6 records the approved chatbot sections;
shared source draft metadata and unrelated full-MVP pending gates are preserved.

Current policy r9 and all 27 baseline source pins match. New views reproduce
byte-for-byte. All historical evidence/baseline bytes pinned before this decision
are unchanged, including earlier not_run checks. Browser evidence and the human
attestation supplement those records. No device identifier or human observation
was invented; the signer reported the bundled walkthrough complete.

Scope, Architecture and UI/UX are approved for this change set. Contract/L3,
production runtime/provider acceptance, UAT and release remain pending/not_run.
No product code changed and no implementation task was marked done. The next
handoff is PLAN r4 for L3/UIS contract design, not authorization to bypass Contract
Gate or physical-schema verification.
