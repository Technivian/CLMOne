#!/usr/bin/env python3
"""Compare Playwright JSON results without disguising raw suite failures."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any

SEVERITY = {"passed": 1, "governed_baseline_failure": 2, "failed": 3, "timedout": 4, "crashed": 5, "incomplete": 6, "skipped": 6, "notrun": 6}
FAILURES = {"failed", "timedout", "crashed", "incomplete"}
REQUIRED = {"id", "group_id", "current_outcome", "classification", "project", "owner", "risk", "safeguards", "commercial_relevance", "canonical_nda_relevance", "approval_evidence", "remediation_reference", "expires_on", "exit_criteria", "failure_signature"}


def signature(error: Any) -> str:
    text = error if isinstance(error, str) else (error or {}).get("message", "")
    text = re.sub(r"\x1b\[[0-9;]*m", "", str(text))
    text = re.sub(r"(?:[A-Za-z]:)?/[^\s:]+", "<path>", text)
    text = re.sub(r":\d+(?::\d+)?", ":<line>", text)
    return re.sub(r"\s+", " ", text).strip()[:500] or "<no-error-message>"


def _walk(suite: dict[str, Any], parents: list[str], records: list[dict[str, Any]]) -> None:
    title = suite.get("title")
    chain = parents + ([title] if title else [])
    for spec in suite.get("specs", []):
        spec_chain = chain + [spec.get("title", "")]
        for test in spec.get("tests", []):
            project = test.get("projectName") or "default"
            results = test.get("results") or []
            if not results:
                records.append({"id": "::".join([project, suite.get("file", ""), *spec_chain]), "status": "notrun", "signature": "<not-run>", "project": project, "file": suite.get("file", ""), "duration": 0, "artifacts": []})
            for result in results:
                records.append({
                    "id": "::".join([project, suite.get("file", ""), *spec_chain]),
                    "status": str(result.get("status", "notrun")).lower(),
                    "signature": signature(result.get("error")),
                    "project": project,
                    "file": suite.get("file", ""),
                    "duration": result.get("duration", 0),
                    "artifacts": [a.get("path") for a in result.get("attachments", []) if a.get("path")],
                })
    for child in suite.get("suites", []):
        _walk(child, chain, records)


def load_results(path: Path) -> dict[str, dict[str, Any]]:
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid Playwright result artifact {path}: {exc}") from exc
    records: list[dict[str, Any]] = []
    for suite in payload.get("suites", []):
        _walk(suite, [], records)
    if not records:
        raise ValueError(f"Playwright result artifact {path} contains no test results")
    return {record["id"]: record for record in records}


def validate_baseline(path: Path, today: dt.date, expected_sha: str | None = None) -> dict[str, dict[str, Any]]:
    payload = json.loads(path.read_text())
    if expected_sha and payload.get("baseline_sha") != expected_sha:
        raise ValueError("baseline SHA does not match the captured artifact")
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise ValueError("baseline entries must be a list")
    valid: dict[str, dict[str, Any]] = {}
    for entry in entries:
        missing = REQUIRED - set(entry)
        if missing:
            raise ValueError(f"baseline entry is incomplete: missing {sorted(missing)}")
        if "*" in entry["id"] or not str(entry["approval_evidence"]).startswith("https://github.com/"):
            raise ValueError(f"baseline entry {entry['id']} is not exact and governed")
        if dt.date.fromisoformat(entry["expires_on"]) < today:
            raise ValueError(f"baseline entry {entry['id']} is expired")
        if entry["id"] in valid:
            raise ValueError(f"duplicate baseline entry {entry['id']}")
        if entry["current_outcome"] == "timed_out" and entry["failure_signature"].startswith("Error:"):
            raise ValueError(f"timed out test {entry['id']} is recorded as an assertion failure")
        valid[entry["id"]] = entry
    return valid


def compare(base: dict[str, dict[str, Any]], head: dict[str, dict[str, Any]], baseline: dict[str, dict[str, Any]]) -> list[str]:
    problems: list[str] = []
    for ident, before in base.items():
        after = head.get(ident)
        if after is None:
            problems.append(f"removed test: {ident}")
            continue
        if before["status"] == "passed" and after["status"] != "passed":
            problems.append(f"passing test regressed: {ident} ({after['status']})")
        if after["status"] in {"skipped", "notrun"} and before["status"] not in {"skipped", "notrun"}:
            problems.append(f"test unexpectedly {after['status']}: {ident}")
        if before["status"] in FAILURES and after["status"] in FAILURES:
            entry = baseline.get(ident)
            if not entry:
                problems.append(f"unapproved baseline failure: {ident}")
            elif entry["failure_signature"] != after["signature"]:
                problems.append(f"failure signature changed: {ident}")
            elif SEVERITY[after["status"]] > SEVERITY[before["status"]]:
                problems.append(f"failure severity worsened: {ident} ({before['status']} -> {after['status']})")
    for ident, after in head.items():
        if ident not in base and after["status"] != "passed":
            problems.append(f"new non-passing test: {ident} ({after['status']})")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--head", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--baseline-sha")
    args = parser.parse_args()
    try:
        base, head = load_results(args.base), load_results(args.head)
        baseline = validate_baseline(args.baseline, dt.date.today(), args.baseline_sha)
        base_failures = {ident for ident, item in base.items() if item["status"] in FAILURES}
        if base_failures != set(baseline):
            missing = sorted(base_failures - set(baseline))
            extra = sorted(set(baseline) - base_failures)
            raise ValueError(f"baseline manifest does not exactly match raw failures; missing={missing}, extra={extra}")
        problems = compare(base, head, baseline)
    except ValueError as exc:
        print(f"Browser regression gate failed: {exc}", file=sys.stderr)
        return 2
    def counts(results):
        return {status: sum(item["status"] == status for item in results.values()) for status in sorted(SEVERITY)}
    report = {"raw_base_counts": counts(base), "raw_head_counts": counts(head), "governed_unchanged_failures": sum(item["status"] in FAILURES and item["id"] in baseline for item in head.values()), "new_or_worsened_failures": len(problems), "resolved_failures": sum(item["status"] in FAILURES and head.get(ident, {}).get("status") == "passed" for ident, item in base.items()), "removed_or_skipped_tests": sum("removed test" in problem or "unexpectedly" in problem for problem in problems), "expired_baseline_records": 0, "regressions": problems}
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"Browser regression gate {'passed' if not problems else 'failed'}: zero new or worsened failures={not problems}. Raw head result: {report['raw_head_counts']['passed']} passed, {report['raw_head_counts']['failed']} failed, {report['raw_head_counts']['timedout']} timed out.")
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
