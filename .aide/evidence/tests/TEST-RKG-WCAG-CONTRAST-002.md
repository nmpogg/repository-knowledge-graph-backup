---
uid:
key: TEST-RKG-WCAG-CONTRAST-002
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

# TEST-RKG-WCAG-CONTRAST-002 — Semantic foreground contrast

**Measured at:** 2026-09-23  
**Input:** `.aide/design/ui/tokens/tokens.json`, `TOK-RKG-001` revision 2, sourced
from `UID-RKG-001` revision 7  
**SHA-256:** `a4a301a6d8bc4224b540458eacab6015b5a2e8092fceaa75cc969804adb606e2`  
**Method:** parse current-tree JSON, convert sRGB components with threshold `0.04045`,
calculate relative luminance, then `(Llighter + 0.05) / (Ldarker + 0.05)`.

| Pair on mode surface | Ratio | WCAG AA normal text |
|---|---:|---|
| Light text | 17.85:1 | PASS |
| Light muted text | 7.58:1 | PASS |
| Light action | 5.02:1 | PASS |
| Light focus/success | 7.13:1 | PASS |
| Light warning | 7.09:1 | PASS |
| Light error | 6.47:1 | PASS |
| Light info | 6.70:1 | PASS |
| Dark text | 13.98:1 | PASS |
| Dark muted text | 9.85:1 | PASS |
| Dark action | 6.42:1 | PASS |
| Dark focus/success | 10.42:1 | PASS |
| Dark warning | 11.75:1 | PASS |
| Dark error | 7.71:1 | PASS |
| Dark info | 8.11:1 | PASS |

## Result and limit

Các semantic foreground token mới đều đạt ngưỡng 4.5:1 trên `color.surface` của mode
tương ứng. Đây là kiểm tra token-level; border visibility, graph marks, disabled,
hover, focus ring geometry và component states vẫn cần browser/component evidence
trước khi UI/UX Gate được approve.

