---
key: TEST-RKG-CHATBOT-DESIGN-001
type: test-evidence
group: evidence
scope: system
system: SYS-RKG
revision: 1
captured_at: '2026-10-06'
change_set: CHG-RKG-2026-002
verification_mode: author-deterministic-document-checks
captured_against:
  code_commit: 86ecab6546384227d1901e24c8b8fbfc6c0e8527
  code_tree: 6868e73b8d0b5abdecdd9a64265596d8fe809548
  artifacts:
  - key: FR-RKG-005
    revision: 8
    status: draft
    hash: 01ccbae78781b11004ffc46a1fb30c0ca5b7b4669516d926bfb1bfc70f437400
    path: requirements/fr/FR-RKG-005.md
    role: selected_candidate
  - key: ADR-2026-007
    revision: 1
    status: draft
    hash: c699b29aa4c36c4be71c40b9f179731213f2f53e77d811a06e9307a2be68144c
    path: architecture/adr/ADR-2026-007.md
    role: selected_candidate
  - key: CMP-RKG-CONVERSATION
    revision: 7
    status: draft
    hash: 2b2bc1bb8c3cc17cc2349d5c3be07b828efd89cbc24660cfba2c44635adffa65
    path: architecture/l2/CMP-RKG-CONVERSATION.md
    role: selected_candidate
  - key: CMP-RKG-WEB
    revision: 9
    status: draft
    hash: 9127465096842ccdf6addff5649a13839515f088a136d2bdcbbb3e5ccb5b91e6
    path: architecture/l2/CMP-RKG-WEB.md
    role: selected_candidate
  - key: TM-RKG
    revision: 8
    status: draft
    hash: c22e337412e5c9d42bccbc5cf5ef76e92767ee130f3b4d8a9de86ea6d6570bb6
    path: architecture/threat-model/TM-RKG.md
    role: selected_candidate
  - key: UXF-RKG-002
    revision: 5
    status: draft
    hash: 5e57d4c6d118e1463a96373740105d61371514de12f2f1aa17a303206d8e3add
    path: design/ux/UXF-RKG-002.md
    role: selected_candidate
  - key: SCR-RKG-001
    revision: 9
    status: draft
    hash: 385e3bd7ddb7ff32397580270005574cb6cce2ae47e392e7b137c9a4520876c3
    path: design/ux/SCR-RKG-001.md
    role: selected_candidate
  - key: UID-RKG-001
    revision: 8
    status: draft
    hash: b5b92b6652c087cadaa0a347de226f9bf72fc2f5ad36eff617e9452b4e3dbc7e
    path: design/ui/UID-RKG-001.md
    role: selected_candidate
  - key: GATE-RKG-SCOPE
    revision: 8
    status: draft
    hash: 1d444d7eb066bd267353f43b61bb8f379aeb572e4ed6ba56637923459b0458fc
    path: policies/gates/GATE-RKG-SCOPE.md
    role: selected_candidate
  - key: GATE-RKG-ARCHITECTURE
    revision: 6
    status: draft
    hash: 28b9cefd31d2573bee4b5be4a8a23c9e649e458ee97605f96972dd53b6d60826
    path: policies/gates/GATE-RKG-ARCHITECTURE.md
    role: selected_candidate
  - key: GATE-RKG-UIUX
    revision: 8
    status: draft
    hash: 9738d79480c08191b7043a58e50001d3bc0e1e7f501631250a9ddab52be86a34
    path: policies/gates/GATE-RKG-UIUX.md
    role: selected_candidate
  - key: PRD-RKG
    revision: 20
    status: draft
    hash: 6406762c3f72ed86601b16711a105408be90b72389891e66dd4642b4ecbc25cc
    path: product/prd/PRD-RKG.md
    role: reference_only
  - key: DOM-RKG-CORE
    revision: 5
    status: draft
    hash: 24759954cd15951c3c6fc441d0ba0b88d831f62f86ee1e5b1c15db74318d2ff3
    path: domain/glossary-core.md
    role: reference_only
  - key: CAP-RKG-003
    revision: 4
    status: approved
    hash: a83f81a79c97a82bb302f0db2a28ade53e32299b390d45a2318ae33839c57c93
    path: architecture/l1/CAP-RKG-003.md
    role: reference_only
  - key: CMP-RKG-GRAPH
    revision: 9
    status: draft
    hash: 7792b51117fd0d302a1e1d485e06f68f01266a151fe3bf94220ddddb17c6cbb2
    path: architecture/l2/CMP-RKG-GRAPH.md
    role: reference_only
  - key: CMP-RKG-TRANSPORT
    revision: 7
    status: draft
    hash: 6d89ca2098b2335b8455b3dad6c2b0a214079e55cd92e13d5cbf0de13e6df286
    path: architecture/l2/CMP-RKG-TRANSPORT.md
    role: reference_only
  - key: ADR-2026-001
    revision: 3
    status: approved
    hash: ee392713079ebeb4904445a033ce7b5bdfd417a85cfc20e4bac8bde23442c10d
    path: architecture/adr/ADR-2026-001.md
    role: reference_only
  - key: ADR-2026-004
    revision: 2
    status: approved
    hash: 43ade7152dac2960329b8dd0a196649e91a317c125133a53e7e26164d5f4e3e3
    path: architecture/adr/ADR-2026-004.md
    role: reference_only
  - key: NFR-RKG-SEC-001
    revision: 7
    status: approved
    hash: ea54ad8b488bc6bcc862ed0316dc8e6a46a58ad63119b9cadf3d24853d8135aa
    path: requirements/nfr/NFR-RKG-SEC-001.md
    role: reference_only
  - key: NFR-RKG-REL-001
    revision: 8
    status: approved
    hash: fd6742188c96da8e9859bbd15ff68715c792e57d6eaf6368d34e3d34dd902b0b
    path: requirements/nfr/NFR-RKG-REL-001.md
    role: reference_only
  - key: NFR-RKG-UX-001
    revision: 7
    status: approved
    hash: c73044ee84ad7fda785daf4ad9818e128d5cf33e02005b00f8019668f09be4e3
    path: requirements/nfr/NFR-RKG-UX-001.md
    role: reference_only
  - key: API-RKG-CORE-v1
    revision: 15
    status: draft
    hash: e0f482a8c98a88898aa7abae2d42e1c00cb82b0e393627447dd7f08fd03d8ce2
    path: tech-specs/RKG-TRANSPORT/api/API-RKG-CORE-v1.md
    role: reference_only
  - key: TBL-RKG-GRAPH
    revision: 12
    status: draft
    hash: 8f89df7b938dec9947a06f49fb307432b9182853ca5e4bfdcad1994a50d13bcf
    path: tech-specs/RKG-GRAPH/schema/TBL-RKG-GRAPH.md
    role: reference_only
  - key: UIS-RKG-001
    revision: 12
    status: draft
    hash: 2e66ba300e0b4e1e9fb55ccb0a1f7d376967603ad673e3bc1df339e563e7749b
    path: design/ui/UIS-RKG-001.md
    role: reference_only
  - key: EVAL-RKG-QA-001
    revision: 2
    status: draft
    hash: 19bba2089b095b0b431d85d843a61a3d5a4488889c269d47439869f11b673720
    path: policies/eval/EVAL-RKG-QA-001.md
    role: reference_only
  - key: OBS-RKG-005
    revision: 3
    status: draft
    hash: 82acb6483ca288e1952b5f7f354158243ea07ea45cf090a62392787e3c92ef3f
    path: observability/OBS-RKG-005.md
    role: reference_only
  - key: TOK-RKG-001
    revision: 2
    status: draft
    hash: ae71b14d8921b6e64f03641a5787c7b99622fa3f28904a75208eabfb32c8de96
    path: design/ui/tokens/tokens.json
    role: reference_only
  package_files:
  - path: .aide/lifecycle/change-sets/CHG-RKG-2026-002/baseline/BL-CHG-RKG-2026-002-r1.yaml
    sha256: 821d311721a549a7e27a618615185992497fa04b0e565bccabcaf9ab1f059290
  - path: .aide/lifecycle/change-sets/CHG-RKG-2026-002/change-set.yaml
    sha256: 0bfcf3246ede1cdb42bf683545b1da38771540375b0f4b6186fff0404dde8190
  - path: .aide/evidence/context/CTX-CHG-RKG-2026-002-r2.yaml
    sha256: 6c95556b4bd4cdb26245afe873ee387aee25e0ee23cbedd495799da931aa51fc
  - path: .aide/evidence/plans/PLAN-CHG-RKG-2026-002-r2.md
    sha256: 3a053d57296c2ac98c046bd598333cb7b6ae69efaf72ca4a2761889e43bdea61
  - path: .aide/evidence/requests/CR-RKG-003.yaml
    sha256: a7070de1df6d1845f8624b7c5d87605b7dac341e705a9520a4b0ed7ca500699d
  - path: .aide/generated/change-set-views/CSV-CHG-RKG-2026-002.md
    sha256: 0a9eb4124fbb97d86c544188cae1e9997ddf23e6fe18f4b2b2f7a38fb07162c6
  - path: .aide/generated/architecture-views/AVW-RKG-CHATBOT-002.md
    sha256: d39f4ec79662726abdacab3862ae113a2dd17f3d21919d06a29450c1c06cc97e
  - path: tools/render_chatbot_review.py
    sha256: b8f87bb98e4a0794a964530c7ce92f96107bbfe0ecb885216dc29377ff6494f1
checks:
- check: candidate_source_hashes
  result: passed
  count: 27
- check: changed_artifact_identity_heading_revision_and_draft_status
  result: passed
- check: previous_FR005_AC_bodies_and_IDs_preserved
  result: passed
  count: 17
- check: new_AC074_to_081_unique_and_given_when_then
  result: passed
  count: 8
- check: FR005_NFR_constraint_symmetry
  result: passed
- check: review_view_generator_reproducibility_and_source_hashes
  result: passed
- check: ruff_document_generator
  result: passed
- check: git_diff_whitespace
  result: passed
- check: runtime_code_and_historical_signed_records_unchanged
  result: passed
- check: YAML_frontmatter_and_package_syntax
  result: passed
- check: gates_pending_and_implementation_not_ready
  result: passed
- check: independent_advisory_review
  result: not_run
- check: UI_mock_keyboard_real_device_walkthrough
  result: not_run
- check: runtime_tests_and_live_provider_quality
  result: not_run
- check: human_exact_hash_gate_signatures
  result: not_recorded
closes_gates: false
classification: internal
ai_assisted: true
---

# TEST-RKG-CHATBOT-DESIGN-001 — Selected scope/design document verification

Verified the current candidate package, not the chatbot runtime. Document checks
covered pinned input bytes, revision/status/identity, published AC preservation,
new AC uniqueness/shape, FR/NFR symmetry, deterministic derived views and unchanged
runtime/signed historical records. The documentation generator passed Ruff.

Scope/content selection is documented by CR-RKG-003 and ADR-2026-007; these checks
are author verification, not independent advisory review or a gate signature.
Candidate baseline and all commitment gates remain pending. No runtime tests,
provider requests, browser mock walkthrough, UAT or deployment were performed.

No question/answer transcript, analyzed source, local configuration or credential
was captured. New implementation tasks await prerequisite gates and L3 readiness.
