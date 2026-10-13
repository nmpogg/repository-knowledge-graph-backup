---
{
  "key": "TEST-RKG-CHATBOT-PREVIEW-001",
  "type": "test-evidence",
  "group": "evidence",
  "scope": "system",
  "system": "SYS-RKG",
  "revision": 1,
  "status": "completed",
  "captured_at": "2026-10-06T14:24:26+07:00",
  "change_set": "CHG-RKG-2026-002",
  "non_normative": true,
  "author_checks_only": true,
  "classification": "internal",
  "ai_assisted": true,
  "captured_against": {
    "base_code_commit": "86ecab6546384227d1901e24c8b8fbfc6c0e8527",
    "working_tree_inputs": ".aide/generated/ui-mocks/chatbot-002/manifest.json",
    "baseline": {
      "key": "BL-CHG-RKG-2026-002-r5",
      "path": ".aide/lifecycle/change-sets/CHG-RKG-2026-002/baseline/BL-CHG-RKG-2026-002-r5.yaml",
      "sha256": "60c98aa306cc9f7c39bdb402c455c951d65d5024def0236b16f98d4e7083df90"
    },
    "preview": {
      "key": "UIM-RKG-002",
      "path": ".aide/generated/ui-mocks/chatbot-002/manifest.json",
      "sha256": "85f66e0983a51b7acd1416f90e9b2445e95beafa9f32d66727a5ceba50d51d4b"
    },
    "generator": {
      "path": "tools/render_chatbot_preview.py",
      "sha256": "e60dea130a14a1a338d2a3d5c91c3fa86c49771fc173e81605053fbca5f86d70"
    },
    "prototype_assets": {
      "tools/chatbot-preview/Accessibility.test.tsx": "21cb53a9d8978b147fc462f62ff944fa9d7e6f46ea3830b4eb5787f40b047977",
      "tools/chatbot-preview/Preview.test.tsx": "67fb2cb1a10261420f0c810ceeb77e55f63c40dfda11ee98ea3a777c0c9a46b8",
      "tools/chatbot-preview/PreviewHarness.tsx": "2494b69c09dc25e4d7ce3a29117e28926e3d3346cd973860d528e18af0a43f39",
      "tools/chatbot-preview/PreviewReply.tsx": "233ebbdd81f210d98b7c691b2629340f9475506c0804cd992a849fd33755a88d",
      "tools/chatbot-preview/README.md": "ee1473875585cda0555f6c48cd1f16dc42cf39ad8e4aed22deab81305f069dac",
      "tools/chatbot-preview/preview.css": "640fca2c698e4687c047c9730dd9e4068f238201357e68ada2d830182c0250d8",
      "tools/chatbot-preview/previewClient.ts": "48db4cac966c6ee99a2aa2355fdbd20b0dc0606a6bf12a8697ddbea0cc6e942c"
    },
    "token_checker": {
      "path": "tools/check_chatbot_preview_tokens.py",
      "sha256": "365ba9370982ee927c4f5ba3a14b7895d63037d77e3a362b8caeee99433fa950"
    },
    "axe": {
      "version": "4.10.3",
      "module_sha256": "beeadb8d4043458482a8432dd227af926d1baf378ffbcd63888e91ec0ca8535d"
    }
  },
  "checks": {
    "component_tests": {
      "result": "passed",
      "count": 27,
      "command": "npm run test -- src/preview/Preview.test.tsx"
    },
    "axe_dom": {
      "result": "passed",
      "count": 64,
      "matrix": "16 cases x vi/en x light/dark",
      "rules": "wcag2a,wcag2aa,wcag21aa",
      "color_contrast_rule": "disabled_in_jsdom"
    },
    "typescript_and_bundle": {
      "result": "passed",
      "command": "npm run build",
      "warning": "Single full-app JS chunk exceeds Vite 500 kB advisory threshold."
    },
    "staging_lint": {
      "result": "passed_with_warnings",
      "command": "npm run lint",
      "note": "No lint errors; existing frontend React warnings remain."
    },
    "prototype_assets_lint": {
      "result": "passed",
      "command": "frontend/node_modules/.bin/oxlint tools/chatbot-preview"
    },
    "python_tool_lint": {
      "result": "passed",
      "command": ".venv/bin/ruff check tools/render_chatbot_preview.py tools/check_chatbot_preview_tokens.py"
    },
    "token_bindings_and_contrast": {
      "result": "passed",
      "bindings": "all current palette bindings for both themes match TOK r2",
      "normal_text_pairs": 16,
      "minimum_ratio": 4.79,
      "limit": "Token pairs only; no browser/composite/focus/disabled-state certification."
    },
    "source_integrity": {
      "result": "passed",
      "baseline_pins": 27,
      "frontend_inputs_unchanged": true,
      "review_and_architecture_approval_hashes_unchanged": true,
      "bundle_hashes": "all match manifest"
    },
    "loopback_http": {
      "result": "passed",
      "index_status": 200,
      "port": 5174
    },
    "real_browser_walkthrough": {
      "result": "not_run"
    },
    "primary_device_readability_responsive": {
      "result": "not_run"
    },
    "browser_component_state_contrast": {
      "result": "not_run"
    },
    "independent_ui_review": {
      "result": "not_run"
    },
    "backend_graph_language_provider_persistence": {
      "result": "not_run"
    }
  },
  "gates": {
    "scope": "approved",
    "architecture": "approved",
    "ui_ux": "pending",
    "contract": "pending"
  },
  "implementation_ready": false
}
---
# TEST-RKG-CHATBOT-PREVIEW-001 — Current-tree Ask UX prototype checks

Author deterministic checks on the generated fixture prototype; not independent
semantic review and not verification of the production chatbot ACs.

27 interaction tests pass: one natural answer/collapsed claims; exact synthetic
source/location and snapshot identity; dialog Tab/Escape/focus restoration; one
insufficient message; partial/legacy annotations on remount; clarification retains
calls intent; pending controls and draft on disabled/timeout/conflict; unavailable
transcript guard; safe text; fixture answer/UI language separation; no runtime fetch
across all 16 scenarios. Remount checks use the private seed catalog, not persistence.

64 axe DOM checks pass across vi/en and light/dark with review controls expanded.
Color contrast is excluded in jsdom. Current CSS palette matches TOK r2, and 16
foreground/background pairs pass AA normal text (minimum 4.79:1). These are token
calculations, not rendered browser/component-state measurements.

TypeScript/build pass. The full existing app bundle retains Vite's size advisory.
Staging lint exits 0 with existing React warnings; prototype TS assets and Python
tools lint cleanly. Frontend/backend product source and all 27 baseline pins are
unchanged. Manifest pins current working-tree source bytes; base Git commit is
provenance only for those source inputs, not a claim that new documentation is committed.

The static bundle responds HTTP 200 on loopback port 5174. No screenshot, actual
browser/device walkthrough, full WCAG signoff, live LLM/resolver/grounding/API binding
or server persistence test ran. Synthetic evidence/coverage sidecars are private
presentation fixtures and do not define a public schema. Questions entered into
this prototype remain in memory; reload re-seeds fixtures. No transcript is stored
in this evidence record.

Scope/Architecture approvals remain valid for their exact frozen content.
UIUX/Contract remain pending and no implementation task was marked done. Human
review must inspect the existing Ask flow on the primary device, both theme/locale,
keyboard, long identifiers and exact source dialog, before signing UXF r5/SCR r9/UID r8.
