---
{
  "key": "TEST-RKG-CHATBOT-BROWSER-001",
  "type": "test-evidence",
  "group": "evidence",
  "system": "SYS-RKG",
  "revision": 1,
  "captured_at": "2026-10-06T14:39:39+07:00",
  "change_set": "CHG-RKG-2026-002",
  "verification_mode": "author_automated_rendered_browser_not_independent_review",
  "captured_against": {
    "base_code_commit": "86ecab6546384227d1901e24c8b8fbfc6c0e8527",
    "baseline": {
      "path": ".aide/lifecycle/change-sets/CHG-RKG-2026-002/baseline/BL-CHG-RKG-2026-002-r5.yaml",
      "sha256": "60c98aa306cc9f7c39bdb402c455c951d65d5024def0236b16f98d4e7083df90"
    },
    "design": [
      {
        "key": "UXF-RKG-002",
        "revision": 5,
        "status": "draft",
        "hash": "5e57d4c6d118e1463a96373740105d61371514de12f2f1aa17a303206d8e3add",
        "path": "design/ux/UXF-RKG-002.md",
        "role": "selected_candidate",
        "approved_sections": [
          "Conversation usability — selected content for CHG-RKG-2026-002"
        ],
        "effective_approval": "approved_in_baseline_for_chatbot_delta"
      },
      {
        "key": "SCR-RKG-001",
        "revision": 9,
        "status": "draft",
        "hash": "385e3bd7ddb7ff32397580270005574cb6cce2ae47e392e7b137c9a4520876c3",
        "path": "design/ux/SCR-RKG-001.md",
        "role": "selected_candidate",
        "approved_sections": [
          "Conversation workspace refinement — CHG-RKG-2026-002"
        ],
        "effective_approval": "approved_in_baseline_for_chatbot_delta"
      },
      {
        "key": "UID-RKG-001",
        "revision": 8,
        "status": "draft",
        "hash": "b5b92b6652c087cadaa0a347de226f9bf72fc2f5ad36eff617e9452b4e3dbc7e",
        "path": "design/ui/UID-RKG-001.md",
        "role": "selected_candidate",
        "approved_sections": [
          "Ask natural-answer presentation — CHG-RKG-2026-002"
        ],
        "effective_approval": "approved_in_baseline_for_chatbot_delta"
      }
    ],
    "preview_manifest": {
      "path": ".aide/generated/ui-mocks/chatbot-002/manifest.json",
      "sha256": "85f66e0983a51b7acd1416f90e9b2445e95beafa9f32d66727a5ceba50d51d4b"
    },
    "checker": {
      "path": "tools/check_chatbot_preview_browser.mjs",
      "sha256": "d26e954ee72ea826c0e3da55845b771aa35590d282cb5533b1472a8d7e965826"
    },
    "results": {
      "path": ".aide/evidence/tests/browser/TEST-RKG-CHATBOT-BROWSER-001-results.json",
      "sha256": "dac19e54ad7190c714a1ecf90a81c1583455ca18b6ee0bdaef7363eeb52a1ebe"
    }
  },
  "checks": {
    "initial_state_layout_and_axe": {
      "result": "passed",
      "count": 256,
      "matrix": "16 cases x 375/768/1024/1440 px x vi/en x light/dark",
      "height_px": 900
    },
    "error_state_axe_draft_pending": {
      "result": "passed",
      "count": 48
    },
    "source_dialog_axe": {
      "result": "passed"
    },
    "source_keyboard_activation_trap_escape_restore": {
      "result": "passed"
    },
    "rendered_color_contrast_rule": "enabled_no_violations_detected_in_tested_states",
    "unexpected_network": "none_detected; non-preview and /api requests blocked",
    "primary_device_human_walkthrough": "reported_complete_CR-RKG-007",
    "live_backend_provider_quality": "not_run"
  },
  "browser": {
    "engine": "Chromium",
    "version": "145.0.7632.6",
    "headless": true,
    "playwright": "1.58.2",
    "axe": "4.10.3"
  },
  "classification": "internal",
  "ai_assisted": true
}
---

# TEST-RKG-CHATBOT-BROWSER-001 — Rendered Ask preview checks

256 initial-state checks pass across all 16 synthetic cases, four required widths,
vi/en and light/dark. Visible answer/choice/source/context/form elements stay
within the viewport without internal horizontal overflow; composer is visible.
48 submitted disabled/timeout/conflict state audits pass and retain the draft
with submit/delete disabled during pending. These are fixture failures, not a
live provider or backend integration test.

Axe WCAG A/AA checks run in Chromium with the color-contrast rule enabled for
these states, plus the open source dialog; no violations were detected.
Real keyboard Enter opens the exact synthetic source, Tab stays in the dialog,
Escape closes it and focus returns to the source button. External/API requests
are blocked; no unexpected request was observed.

This is author automation at a 900 px viewport height, not independent UI review
or human-primary-device observation. The human checklist outcome is separately
reported by PhongNM in CR-RKG-007; no device identifier was supplied and none is
invented. No real question/answer transcript, credentials, source excerpt or
host path is retained in this evidence. Full state outputs contain selectors and
pass/fail metadata only. Runtime grounding/model quality/persistence are not_run.

All reviewed UI design source bytes and the original preview bundle are unchanged.
