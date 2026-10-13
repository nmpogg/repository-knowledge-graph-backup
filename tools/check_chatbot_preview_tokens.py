#!/usr/bin/env python3
"""Check current token bindings and foreground pairs; not browser state contrast."""

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
token_path = ROOT / ".aide/design/ui/tokens/tokens.json"
css_path = ROOT / "frontend/src/index.css"
tokens = json.loads(token_path.read_text())
css = css_path.read_text()


def luminance(color):
    rgb = [int(color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return sum(c * weight for c, weight in zip(linear, (0.2126, 0.7152, 0.0722)))


results = []
for mode in ("light", "dark"):
    selector = (
        r":root\s*\{([^}]+)\}"
        if mode == "light"
        else (r"(?:\[data-theme=['\"]dark['\"]\])\s*\{([^}]+)\}")
    )
    block = re.search(selector, css).group(1)
    colors = tokens["color"][mode]
    for name, token in colors.items():
        suffix = re.sub(r"[A-Z]", lambda match: "-" + match[0].lower(), name)
        bound = re.search(r"--color-" + suffix + r":\s*([^;]+)", block).group(1)
        assert bound.lower() == token["$value"].lower(), (mode, name)
    for foreground in ("text", "textMuted", "action", "error"):
        for background in ("background", "surface"):
            fg, bg = colors[foreground]["$value"], colors[background]["$value"]
            high, low = sorted((luminance(fg), luminance(bg)), reverse=True)
            ratio = (high + 0.05) / (low + 0.05)
            assert ratio >= 4.5, (mode, foreground, background, ratio)
            results.append(
                {
                    "mode": mode,
                    "foreground": foreground,
                    "background": background,
                    "ratio": round(ratio, 2),
                }
            )
print(
    json.dumps(
        {
            "token_sha256": hashlib.sha256(token_path.read_bytes()).hexdigest(),
            "frontend_css_sha256": hashlib.sha256(css_path.read_bytes()).hexdigest(),
            "bindings": "passed",
            "normal_text_pairs": results,
            "browser_component_state_contrast": "not_run",
        },
        indent=2,
    )
)
