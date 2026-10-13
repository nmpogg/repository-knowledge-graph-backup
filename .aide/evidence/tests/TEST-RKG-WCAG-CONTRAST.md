---
uid:
key: TEST-RKG-WCAG-CONTRAST
type: test-evidence
group: evidence
scope: system
system: SYS-RKG
status: completed
revision: 1
ownership: {accountable_team: TEAM-RKG, accountable_role: design-owner}
relations:
  verifies: [TOK-RKG-001, UID-RKG-001, NFR-RKG-UX-001]
classification: internal
ai_assisted: true
---

# WCAG contrast evidence — core semantic tokens

**Measured at:** 2026-09-18  
**Input:** `.aide/design/ui/tokens/tokens.json` (`TOK-RKG-001`, sourced from
`UID-RKG-001` revision 4)  
**Method:** parse the JSON values and compute WCAG relative luminance using the sRGB
linearization threshold `0.04045`; contrast is `(Llighter + 0.05) / (Ldarker + 0.05)`.

| Pair | Foreground | Background | Ratio | AA normal text (4.5:1) |
|---|---:|---:|---:|---|
| Light action / surface | `#15803D` | `#FFFFFF` | 5.02:1 | PASS |
| Light text / background | `#0F172A` | `#F8FAFC` | 17.06:1 | PASS |
| Light muted text / surface | `#475569` | `#FFFFFF` | 7.58:1 | PASS |
| Dark action / background | `#22C55E` | `#0F172A` | 7.83:1 | PASS |
| Dark action / surface | `#22C55E` | `#1E293B` | 6.42:1 | PASS |
| Dark text / background | `#F8FAFC` | `#0F172A` | 17.06:1 | PASS |
| Dark muted text / surface | `#CBD5E1` | `#1E293B` | 9.85:1 | PASS |

## Result and limit

All core foreground/background token pairs pass WCAG AA for normal text. This is
token-level evidence only. Disabled, focus, warning/error/info, graph selection and
other implemented component states still require browser/component evidence before
the UI/UX Gate can be approved.

