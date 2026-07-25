import datetime as dt
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "browser_regression_gate.py"
SPEC = importlib.util.spec_from_file_location("browser_gate", SCRIPT)
gate = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(gate)


IDENTITY = "chromium::tests/e2e/example.spec.js::Example::works"


def result(status="passed", error=""):
    return {IDENTITY: {"id": IDENTITY, "status": status, "signature": gate.signature(error), "project": "chromium", "file": "tests/e2e/example.spec.js", "duration": 1, "artifacts": []}}


def entry(**overrides):
    value = {"id": IDENTITY, "group_id": "PWB-T", "current_outcome": "failed", "classification": "STALE_ASSERTION", "project": "chromium", "owner": "Quality", "risk": "Known UI drift", "safeguards": "Comparator", "commercial_relevance": "test", "canonical_nda_relevance": "no", "approval_evidence": "https://github.com/Technivian/CLMOne/pull/120", "remediation_reference": "https://github.com/Technivian/CLMOne/issues/120", "expires_on": "2099-01-01", "exit_criteria": "Correct test", "failure_signature": gate.signature("expected true")}
    value.update(overrides)
    return value


class BrowserRegressionGateTests(unittest.TestCase):
    def test_new_failure_fails(self):
        self.assertTrue(gate.compare(result(), result("failed", "expected true"), {}))

    def test_removed_test_fails(self):
        self.assertTrue(gate.compare(result(), {}, {}))

    def test_newly_skipped_test_fails(self):
        self.assertTrue(gate.compare(result(), result("skipped"), {}))

    def test_changed_failure_signature_fails(self):
        self.assertTrue(gate.compare(result("failed", "before"), result("failed", "after"), {IDENTITY: entry(failure_signature=gate.signature("before"))}))

    def test_unchanged_governed_failure_passes(self):
        self.assertEqual(gate.compare(result("failed", "expected true"), result("failed", "expected true"), {IDENTITY: entry()}), [])

    def test_increased_project_scope_fails_as_new_non_passing(self):
        head = result("failed", "expected true")
        head["firefox::tests/e2e/example.spec.js::Example::works"] = {**next(iter(head.values())), "id": "firefox::tests/e2e/example.spec.js::Example::works", "project": "firefox"}
        self.assertTrue(gate.compare(result("failed", "expected true"), head, {IDENTITY: entry()}))

    def test_expired_entry_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "baseline.json"
            path.write_text(json.dumps({"entries": [entry(expires_on="2000-01-01")]}))
            with self.assertRaises(ValueError):
                gate.validate_baseline(path, dt.date.today())

    def test_malformed_result_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            path.write_text("not-json")
            with self.assertRaises(ValueError):
                gate.load_results(path)

    def test_completely_green_head_passes(self):
        self.assertEqual(gate.compare(result(), result(), {}), [])
