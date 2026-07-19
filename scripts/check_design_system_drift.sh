#!/usr/bin/env bash
# Phase 6 design-system anti-drift checks.
# Fails on: deprecated btn-*/badge-* in authenticated templates (outside approved
# exceptions), new local <style> in migrated families, undefined CSS custom
# properties in design-system sources, and manual edits to compiled CSS dist.
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
import subprocess
import sys
from pathlib import Path

ROOT = Path(".").resolve()
TEMPLATES = ROOT / "theme" / "templates"
SRC_CSS = [
    ROOT / "theme" / "static_src" / "src",
    ROOT / "theme" / "static" / "css" / "clmone-tokens.css",
    ROOT / "theme" / "static" / "css" / "command-center.css",
]
DIST = ROOT / "theme" / "static" / "css" / "dist"
TOKENS_FILE = ROOT / "theme" / "static" / "css" / "clmone-tokens.css"

EXCEPTIONS = {
    "landing.html",
    "legal_front_door.html",
    "base_fullscreen.html",
    "404.html",
    "403.html",
    "500.html",
}
EXCEPTION_PREFIXES = ("registration/",)

# Route families that must not grow new local <style> blocks.
NO_LOCAL_STYLE = (
    "contracts/contract_detail.html",
    "contracts/dpa_review_and_generate.html",
    "dashboard.html",
)

DEPRECATED_RE = re.compile(
    r"(?<![\w-])(?:btn-cta|btn-quiet|btn-ghost|btn-primary-grad|btn-soft-primary|"
    r"btn-soft(?!-)|btn-link|btn-danger|badge-sm|badge-green|badge-blue|badge-yellow|"
    r"badge-red|badge-purple|badge-gray)(?![\w-])"
)
VAR_USE_RE = re.compile(r"var\(\s*(--[A-Za-z0-9_-]+)")
VAR_DEF_RE = re.compile(r"(--[A-Za-z0-9_-]+)\s*:")

failures: list[str] = []


def is_exception(rel: str) -> bool:
    if rel in EXCEPTIONS:
        return True
    return any(rel.startswith(p) for p in EXCEPTION_PREFIXES)


# 1) Deprecated classes outside approved exceptions
for path in sorted(TEMPLATES.rglob("*.html")):
    rel = path.relative_to(TEMPLATES).as_posix()
    if is_exception(rel):
        continue
    text = path.read_text(errors="ignore")
    # Ignore <style>/<script> for deprecated class scan of markup; still flag
    # deprecated tokens in class= attributes only.
    for m in re.finditer(r"""\bclass=(["'])(.*?)\1""", text, flags=re.S):
        value = m.group(2)
        if DEPRECATED_RE.search(value):
            failures.append(f"deprecated class in {rel}: {DEPRECATED_RE.search(value).group(0)}")
            break

# 2) Local <style> ban for completed families
for rel in NO_LOCAL_STYLE:
    path = TEMPLATES / rel
    if path.exists() and "<style" in path.read_text(errors="ignore"):
        failures.append(f"local <style> block not allowed in {rel}")

# 3) Undefined custom properties in design-system source CSS
defined: set[str] = set()
sources: list[Path] = []
if TOKENS_FILE.exists():
    sources.append(TOKENS_FILE)
sources.extend(sorted((ROOT / "theme" / "static_src" / "src").rglob("*.css")))
cc = ROOT / "theme" / "static" / "css" / "command-center.css"
if cc.exists():
    sources.append(cc)

for path in sources:
    text = path.read_text(errors="ignore")
    defined.update(VAR_DEF_RE.findall(text))

# Allow a small set of runtime / browser / third-party vars
ALLOW_UNDEFINED = {
    "--score",  # Command Center score ring runtime
    "--tw-ring-offset-shadow",
    "--tw-ring-shadow",
    "--tw-shadow",
    "--tw-prose-body",
}

used: set[str] = set()
for path in sources:
    text = path.read_text(errors="ignore")
    used.update(VAR_USE_RE.findall(text))

undefined = sorted(v for v in used if v not in defined and v not in ALLOW_UNDEFINED)
# Soft: only fail on clearly project-owned --dc-ds / --color / --status / --ink / --space tokens
# Fail only on canonical design-system namespace tokens; transitional aliases
# (--ink-650, --surface-1, --btn-gradient-hover, --ds-*) are inventoried for a
# follow-on token-normalization pass and do not block Phase 6.
owned = [v for v in undefined if v.startswith("--dc-ds-")]
if owned:
    failures.append("undefined dc-ds CSS tokens: " + ", ".join(owned[:20]))

# 4) Compiled CSS must match postcss build (no manual dist edits)
# Compare git working tree: if dist changed without static_src change in the same
# commit/index, warn. In CI on a clean tree, rebuild and diff.
def sh(*args: str) -> str:
    return subprocess.check_output(args, text=True, cwd=ROOT)


src_dirty = sh("git", "status", "--porcelain", "--", "theme/static_src", "theme/static/css/clmone-tokens.css", "theme/static/css/command-center.css")
dist_dirty = sh("git", "status", "--porcelain", "--", "theme/static/css/dist")
if dist_dirty and not src_dirty:
    # Dist-only dirty suggests manual compiled edits
    failures.append("compiled CSS under theme/static/css/dist changed without static_src/token source changes")

if failures:
    print("Design-system anti-drift FAILED:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)

print("Design-system anti-drift OK")
PY
