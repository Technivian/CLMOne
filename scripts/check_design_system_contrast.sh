#!/usr/bin/env bash
# Automated colour-contrast spot-check for canonical badge/button token pairs.
# Uses relative luminance (WCAG 2.1) against token pairs in clmone-tokens.css /
# design-system components.css. Does not require a browser.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON_BIN="./.venv/bin/python"
if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="python3"
fi

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(".").resolve()
tokens = (ROOT / "theme" / "static" / "css" / "clmone-tokens.css").read_text()
components = (
    ROOT / "theme" / "static_src" / "src" / "design-system" / "components.css"
).read_text()

HEX_RE = re.compile(r"#([0-9A-Fa-f]{3,8})\b")


def parse_hex(value: str) -> tuple[float, float, float] | None:
    value = value.strip()
    m = HEX_RE.search(value)
    if not m:
        return None
    h = m.group(1)
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) == 8:
        h = h[:6]
    if len(h) != 6:
        return None
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return r / 255.0, g / 255.0, b / 255.0


def channel(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(rgb: tuple[float, float, float]) -> float:
    r, g, b = rgb
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def contrast(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    l1, l2 = luminance(a), luminance(b)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def resolve_token(name: str, depth: int = 0) -> tuple[float, float, float] | None:
    if depth > 6:
        return None
    # Prefer tokens file, then components
    for source in (tokens, components):
        m = re.search(rf"{re.escape(name)}\s*:\s*([^;]+);", source)
        if not m:
            continue
        raw = m.group(1).strip()
        rgb = parse_hex(raw)
        if rgb:
            return rgb
        ref = re.search(r"var\(\s*(--[A-Za-z0-9_-]+)", raw)
        if ref:
            return resolve_token(ref.group(1), depth + 1)
    return None


# Badge / status chips are UI components (WCAG 1.4.11 → 3:1). Primary CTA text
# on seal fill is also treated as a UI control. Body-copy pairs would use 4.5.
PAIRS = [
    ("--status-positive-fg", "--status-positive-bg", 3.0),
    ("--status-progress-fg", "--status-progress-bg", 3.0),
    ("--status-pending-fg", "--status-pending-bg", 3.0),
    ("--status-danger-fg", "--status-danger-bg", 3.0),
    ("--status-special-fg", "--status-special-bg", 3.0),
    ("--status-neutral-fg", "--status-neutral-bg", 3.0),
    ("--clmone-white", "--seal", 3.0),
]

failures = []
for fg_name, bg_name, minimum in PAIRS:
    fg = resolve_token(fg_name)
    bg = resolve_token(bg_name)
    if not fg or not bg:
        failures.append(f"unresolved pair {fg_name}/{bg_name}")
        continue
    ratio = contrast(fg, bg)
    if ratio < minimum:
        failures.append(f"{fg_name} on {bg_name}: {ratio:.2f} < {minimum}")
    else:
        print(f"OK {fg_name} on {bg_name}: {ratio:.2f}")

if failures:
    print("Colour contrast FAILED:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
print("Colour contrast OK")
PY
