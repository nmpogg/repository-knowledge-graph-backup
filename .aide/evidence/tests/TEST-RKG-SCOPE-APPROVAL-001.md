---
key: TEST-RKG-SCOPE-APPROVAL-001
type: test-evidence
group: evidence
system: SYS-RKG
revision: 1
captured_at: '2026-10-06T11:22:37+07:00'
change_set: CHG-RKG-2026-002
verification_mode: deterministic-approval-record-integrity
captured_against:
  base_code_commit: 86ecab6546384227d1901e24c8b8fbfc6c0e8527
  approval: approval-007
  files:
  - path: .aide/evidence/approvals/approval-007.yaml
    sha256: a2166557c8b719f619628157beb3fcae9b1d48a197a3e66159a50326241e3f97
  - path: .aide/lifecycle/change-sets/CHG-RKG-2026-002/baseline/BL-CHG-RKG-2026-002-r2.yaml
    sha256: 3cf69ea1258789a8f3ed3fba07759ac860b0cff81078f74ec3643ba9e3f03bdf
  - path: .aide/lifecycle/change-sets/CHG-RKG-2026-002/change-set.yaml
    sha256: f1229e71a00800877b8a488ae52a7195f457c34b4d7d18128af34a3795067e98
  - path: .aide/requirements/fr/FR-RKG-005.md
    sha256: 6f240da74dd108933c85da36bf973106c30b7a6825f2e3b57e67318fa22a78f5
  - path: .aide/evidence/context/CTX-CHG-RKG-2026-002-r3.yaml
    sha256: 31612820fc24dfe894fe159a2f29358945a816c350fbbcf655994a828770a1c9
  - path: .aide/generated/change-set-views/CSV-CHG-RKG-2026-002-r2.md
    sha256: 6053abb1237b03ac576daf5b543cdc73c7f282dc986ea4e28408310e6682eeff
  - path: .aide/generated/architecture-views/AVW-RKG-CHATBOT-002-r2.md
    sha256: a3f9f3b1a7cef49d22cbf096dfe344a0f01bdc35f3bb276b5e1f40ca4a906f69
checks:
  signer_identity_and_confirmed_scope_roles: passed
  exact_signed_scope_hash: passed
  reviewed_and_approved_AC_content_equivalence: passed
  source_view_reproducibility: passed
  scope_only_gate_effect: passed
  previous_baseline_approval_and_runtime_preservation: passed
  generator_ruff: passed
  diff_whitespace: passed
  independent_design_review: not_run
  runtime_tests_live_eval_UAT: not_run
closes_gates: false
approval_authority: human approval-007; this test is not an approval
---

# TEST-RKG-SCOPE-APPROVAL-001 — Scope approval record integrity

Verified current scope signature pins, named roles and unchanged reviewed AC content.
Only the chatbot change-set Scope Gate is approved by PhongNM; other gates and
full-MVP approval remain pending. No runtime or independent design review was run.
