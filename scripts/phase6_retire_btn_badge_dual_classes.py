#!/usr/bin/env python3
"""Phase 6: strip legacy btn-* / badge-* dual classes from authenticated templates.

Approved exceptions (public shell / legal document boundaries) are skipped.
Idempotent. Markup class tokens only — no business-logic changes.

Correctly handles class attributes that mix static tokens with {% if %} branches:
inter-tag fragments that are only legacy badge/btn tokens are remapped to tone
modifiers without re-wrapping in dc-ds-badge/button.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "theme" / "templates"

BTN_TO_MOD = {
    "btn-cta": "dc-ds-button--primary",
    "btn-primary-grad": "dc-ds-button--primary",
    "btn-primary": "dc-ds-button--primary",
    "btn-quiet": "dc-ds-button--quiet",
    "btn-ghost": "dc-ds-button--quiet",
    "btn-secondary": "dc-ds-button--quiet",
    "btn-soft-primary": "dc-ds-button--soft",
    "btn-soft": "dc-ds-button--soft",
    "btn-soft-accent": "dc-ds-button--soft",
    "btn-link": "dc-ds-button--link",
    "btn-danger": "dc-ds-button--danger",
    "btn-danger-soft": "dc-ds-button--danger-soft",
    "btn-sm": "dc-ds-button--sm",
    "btn-lg": "dc-ds-button--lg",
    "btn-soft-primary-primary": "dc-ds-button--soft",
}

BADGE_TO_TONE = {
    "badge-green": "success",
    "badge-blue": "progress",
    "badge-yellow": "attention",
    "badge-red": "danger",
    "badge-purple": "special",
    "badge-gray": "neutral",
    "badge-success": "success",
    "badge-warning": "attention",
    "badge-danger": "danger",
    "badge-info": "progress",
    "badge-neutral": "neutral",
}

LEGACY_BTN_RE = re.compile(r"(?<![\w-])btn(?:-[a-z0-9-]+)?(?![\w-])")
LEGACY_BADGE_RE = re.compile(r"(?<![\w-])badge(?:-[a-z0-9-]+)?(?![\w-])")
CLASS_ATTR_RE = re.compile(r"""\bclass=(["'])(.*?)\1""", re.DOTALL)
FILTER_NAMES = (
    "contract_risk_badge_class|approval_status_badge_class|task_status_badge_class|"
    "task_priority_badge_class|risk_status_badge_class|signature_status_badge_class|"
    "client_status_badge_class|lifecycle_stage_badge_class|phase_badge_class|"
    "dpa_severity_badge_class|dpa_approval_badge_class|obligation_compliance_badge_class"
)
FILTER_BADGE_RE = re.compile(rf"\{{\{{\s*([^}}|]+)\|({FILTER_NAMES})\s*\}}\}}")
TAG_SPLIT_RE = re.compile(r"(\{%.*?%\}|\{\{.*?\}\})")


def is_exception(path: Path) -> bool:
    rel = path.relative_to(TEMPLATES).as_posix()
    if rel in (
        "landing.html",
        "legal_front_door.html",
        "base_fullscreen.html",
        "404.html",
        "403.html",
        "500.html",
    ):
        return True
    if rel.startswith("registration/"):
        return True
    return False


def _dedupe(tokens: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for t in tokens:
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def migrate_class_value(value: str, *, fragment: bool = False) -> str:
    """Rewrite a static class-token string.

    When fragment=True (text between {% %} tags), only emit tone/modifier tokens
    for pure legacy badge/btn fragments — do not wrap with base dc-ds-* classes.
    """
    tokens = value.split()
    if not tokens:
        return value

    only_legacy = all(
        tok in BTN_TO_MOD
        or tok in BADGE_TO_TONE
        or tok in ("btn", "badge-sm")
        or (tok.startswith("badge-") and tok not in ("badge-sm",))
        for tok in tokens
    )

    mods: list[str] = []
    tones: list[str] = []
    out: list[str] = []
    saw_btn = False
    saw_badge = False

    for tok in tokens:
        if tok in BTN_TO_MOD:
            saw_btn = True
            mod = BTN_TO_MOD[tok]
            if mod not in mods:
                mods.append(mod)
            continue
        if tok == "btn":
            saw_btn = True
            continue
        if tok == "badge-sm":
            saw_badge = True
            continue
        if tok in BADGE_TO_TONE:
            saw_badge = True
            tone = f"dc-ds-badge--{BADGE_TO_TONE[tok]}"
            if tone not in tones:
                tones.append(tone)
            continue
        if tok.startswith("badge-"):
            saw_badge = True
            tone = "dc-ds-badge--neutral"
            if tone not in tones:
                tones.append(tone)
            continue
        out.append(tok)

    if fragment and only_legacy:
        return " ".join(_dedupe(mods + tones))

    if saw_btn:
        if "dc-ds-button" not in out:
            out.insert(0, "dc-ds-button")
        for mod in mods:
            if mod not in out:
                try:
                    i = out.index("dc-ds-button")
                    out.insert(i + 1, mod)
                except ValueError:
                    out.append(mod)

    if saw_badge:
        if "dc-ds-badge" not in out:
            out.insert(0, "dc-ds-badge")
        if "dc-ds-badge--sm" not in out:
            try:
                i = out.index("dc-ds-badge")
                out.insert(i + 1, "dc-ds-badge--sm")
            except ValueError:
                out.append("dc-ds-badge--sm")
        for tone in tones:
            if tone not in out:
                out.append(tone)

    return " ".join(_dedupe(out))


def migrate_tag_internals(tag: str) -> str:
    """Rewrite badge-* / btn-* string literals inside a single Django tag."""
    for legacy, tone in BADGE_TO_TONE.items():
        tag = re.sub(rf"(?<![\w-]){re.escape(legacy)}(?![\w-])", f"dc-ds-badge--{tone}", tag)
    for legacy, mod in BTN_TO_MOD.items():
        tag = re.sub(rf"(?<![\w-]){re.escape(legacy)}(?![\w-])", mod, tag)
    tag = re.sub(r"(?<![\w-])badge-sm(?![\w-])", "dc-ds-badge--sm", tag)
    return tag


def migrate_class_attr(value: str) -> str:
    parts = TAG_SPLIT_RE.split(value)
    rebuilt: list[str] = []
    for part in parts:
        if part.startswith("{%") or part.startswith("{{"):
            rebuilt.append(migrate_tag_internals(part))
        elif part:
            # Preserve leading/trailing whitespace around fragments
            lead = re.match(r"^\s*", part).group(0)
            trail = re.search(r"\s*$", part).group(0)
            core = part[len(lead) : len(part) - len(trail) if trail else len(part)]
            if not core:
                rebuilt.append(part)
            else:
                rebuilt.append(lead + migrate_class_value(core, fragment=True) + trail)
        else:
            rebuilt.append(part)
    # Ensure outer static prefix still gets full wrap when it contains legacy tokens
    # Re-run non-fragment migration on leading static segment only if needed.
    text = "".join(rebuilt)
    # Fix missing spaces before {% after --sm
    text = re.sub(r"(dc-ds-badge--sm)(\{% )", r"\1 \2", text)
    text = re.sub(r"(dc-ds-badge--sm)(\{\{)", r"\1 \2", text)
    return text


def migrate_filter_expressions(text: str) -> str:
    def repl(m: re.Match) -> str:
        expr = m.group(0)
        if "legacy_badge_tone" in expr:
            return expr
        var, filt = m.group(1).strip(), m.group(2)
        return f"{{{{ {var}|{filt}|legacy_badge_tone }}}}"

    lines = text.splitlines(keepends=True)
    out = []
    for line in lines:
        if FILTER_BADGE_RE.search(line) and ("badge" in line or "dc-ds-badge" in line):
            new_line = FILTER_BADGE_RE.sub(repl, line)
            # Ensure tone class prefix before filter output used as a class token
            new_line = re.sub(
                r'(class="[^"]*?)(?<!dc-ds-badge--)(\{\{\s*[^}|]+\|\w+_badge_class\|legacy_badge_tone\s*\}\})',
                r"\1dc-ds-badge--\2",
                new_line,
            )
            new_line = new_line.replace("dc-ds-badge--dc-ds-badge--", "dc-ds-badge--")
            # Space before inserted tone filter if glued to --sm
            new_line = re.sub(
                r"(dc-ds-badge--sm)(dc-ds-badge--\{\{)",
                r"\1 \2",
                new_line,
            )
            out.append(new_line)
        else:
            out.append(line)
    return "".join(out)


def migrate_file(path: Path) -> bool:
    original = path.read_text()
    # Never rewrite inside <style> / <script> blocks
    chunks = re.split(r"(<style\b[^>]*>.*?</style>|<script\b[^>]*>.*?</script>)", original, flags=re.I | re.S)
    rebuilt: list[str] = []
    for chunk in chunks:
        if re.match(r"<style\b", chunk, re.I) or re.match(r"<script\b", chunk, re.I):
            rebuilt.append(chunk)
            continue

        def class_repl(m: re.Match) -> str:
            quote, value = m.group(1), m.group(2)
            if not LEGACY_BTN_RE.search(value) and not LEGACY_BADGE_RE.search(value):
                return m.group(0)
            return f"class={quote}{migrate_class_attr(value)}{quote}"

        chunk = CLASS_ATTR_RE.sub(class_repl, chunk)
        chunk = migrate_filter_expressions(chunk)
        rebuilt.append(chunk)

    text = "".join(rebuilt)
    if text != original:
        path.write_text(text)
        return True
    return False


def main() -> int:
    changed = []
    for path in sorted(TEMPLATES.rglob("*.html")):
        if is_exception(path):
            continue
        if migrate_file(path):
            changed.append(path.relative_to(ROOT).as_posix())
    print(f"migrated {len(changed)} templates")
    for p in changed[:60]:
        print(f"  {p}")
    if len(changed) > 60:
        print(f"  ... and {len(changed) - 60} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
