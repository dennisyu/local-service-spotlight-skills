"""Synthetic regression cases for the public bootstrap boundary."""
import copy
import json
import unittest
import sys
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_public_bootstrap import public_url, validate

NOW = datetime(2026, 1, 2, tzinfo=timezone.utc)
BASE = json.loads((ROOT / "tests" / "fixtures" / "public-bootstrap-candidate.json").read_text())


class BootstrapTests(unittest.TestCase):
    def run_case(self, change):
        data = copy.deepcopy(BASE)
        change(data)
        return validate(data, NOW)

    def test_candidate_does_not_claim_activation(self):
        result = validate(BASE, NOW)
        self.assertTrue(result["valid_manifest"])
        self.assertFalse(result["ready_for_independent_review"])
        self.assertEqual(len(result["blockers"]), 6)

    def test_private_tier_rejected(self):
        self.assertFalse(self.run_case(lambda d: d["memory"]["sources"][0].update(access="team"))["valid_manifest"])

    def test_duplicate_id_rejected(self):
        self.assertFalse(self.run_case(lambda d: d["memory"]["sources"].append(copy.deepcopy(d["memory"]["sources"][0])))["valid_manifest"])

    def test_accepted_without_evidence_rejected(self):
        self.assertFalse(self.run_case(lambda d: d.update(status="ACCEPTED"))["valid_manifest"])

    def test_fake_activation_rejected(self):
        self.assertFalse(self.run_case(lambda d: d["adapters"][0].update(state="ACTIVATED"))["valid_manifest"])

    def test_permission_expansion_rejected(self):
        self.assertFalse(self.run_case(lambda d: d["permissions"].update(publish=True))["valid_manifest"])

    def test_unknown_fields_rejected_without_echoing_secret(self):
        result = self.run_case(lambda d: d.update(token="SYNTHETIC-DO-NOT-ECHO"))
        self.assertFalse(result["valid_manifest"])
        self.assertNotIn("SYNTHETIC-DO-NOT-ECHO", json.dumps(result))

    def test_future_metadata_rejected(self):
        self.assertFalse(self.run_case(lambda d: d["memory"]["sources"][0].update(checked_at="2099-01-01T00:00:00Z"))["valid_manifest"])

    def test_expired_source_blocks_rollout(self):
        result = validate(BASE, datetime(2026, 9, 13, tzinfo=timezone.utc))
        self.assertTrue(any("expired" in s for s in result["blockers"]))

    def test_url_boundary(self):
        for url in ["https://127.0.0.1/a", "https://127.1/a", "https://8.8.8.8/a", "https://localhost/a", "https://[::1]/a", "https://example.com/?token=x", "https://user:pass@example.com/a", "https://drive.google.com/file/d/private", "https://docs.google.com/document/d/example", "https://example.com/Users/example/notes", "https://example.internal/a", "file:///Users/example/x"]:
            with self.subTest(url=url):
                self.assertFalse(public_url(url))
        self.assertTrue(public_url("https://localservicespotlight.com/install/"))

    def complete_evidence(self):
        data = copy.deepcopy(BASE)
        data["status"] = "ACCEPTED"
        data["source"]["previous_accepted_commit"] = "c" * 40
        for source in data["memory"]["sources"]:
            source.update(fetch_status="READ_BACK", sha256="b" * 64)
        for adapter in data["adapters"]:
            adapter.update(state="ACTIVATED", receipt={"run_id": "synthetic-test-only", "environment_alias": "synthetic", "commit": data["source"]["commit"], "observed_state": "ACTIVATED", "recorded_at": "2026-01-01T00:00:00Z", "result": "PASS", "output_url": "https://example.com/synthetic-receipt"})
        return data

    def test_synthetic_complete_evidence_can_pass(self):
        data = self.complete_evidence()
        self.assertTrue(validate(data, NOW)["ready_for_independent_review"])

    def test_install_claim_also_needs_receipt(self):
        self.assertFalse(self.run_case(lambda d: d["adapters"][0].update(state="INSTALLED"))["valid_manifest"])

    def test_receipt_cannot_upgrade_claimed_state(self):
        data = self.complete_evidence()
        data["adapters"][0]["state"] = "OBSERVED"
        self.assertFalse(validate(data, NOW)["valid_manifest"])

    def test_receipt_must_match_current_commit(self):
        data = self.complete_evidence()
        data["adapters"][0]["receipt"]["commit"] = "d" * 40
        self.assertFalse(validate(data, NOW)["valid_manifest"])

    def test_duplicate_adapter_rejected(self):
        self.assertFalse(self.run_case(lambda d: d["adapters"].append(copy.deepcopy(d["adapters"][0])))["valid_manifest"])

    def test_failed_receipt_rejected(self):
        data = self.complete_evidence()
        data["adapters"][0]["receipt"]["result"] = "FAIL"
        self.assertFalse(validate(data, NOW)["valid_manifest"])

    def test_lowercase_rfc3339_source_and_receipt(self):
        data = self.complete_evidence()
        data["memory"]["sources"][0]["checked_at"] = "2026-01-01t00:00:00z"
        data["adapters"][0]["receipt"]["recorded_at"] = "2026-01-01t00:00:00z"
        self.assertTrue(validate(data, NOW)["ready_for_independent_review"])

    def test_unsupported_source_and_receipt_timestamps_are_errors(self):
        for timestamp in ("2025-12-31T23:59:60Z", "2026-01-01T00:00:00", "not-a-date"):
            for field in ("source", "receipt"):
                with self.subTest(timestamp=timestamp, field=field):
                    data = self.complete_evidence()
                    if field == "source":
                        data["memory"]["sources"][0]["checked_at"] = timestamp
                    else:
                        data["adapters"][0]["receipt"]["recorded_at"] = timestamp
                    self.assertFalse(validate(data, NOW)["valid_manifest"])

    def test_cli_malformed_timestamp_does_not_traceback_or_echo_value(self):
        data = copy.deepcopy(BASE)
        data["memory"]["sources"][0]["checked_at"] = "2025-12-31T23:59:60Z"
        with tempfile.TemporaryDirectory() as folder:
            manifest = Path(folder) / "synthetic.json"
            manifest.write_text(json.dumps(data))
            run = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate_public_bootstrap.py"), str(manifest)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 1)
        self.assertEqual(run.stderr, "")
        self.assertFalse(json.loads(run.stdout)["valid_manifest"])
        self.assertNotIn("2025-12-31T23:59:60Z", run.stdout)

    def test_missing_optional_date_checker_still_rejects_naive_dates(self):
        script = """
import copy, json, sys
from datetime import datetime, timezone
sys.modules['rfc3339_validator'] = None
sys.path.insert(0, 'scripts')
from validate_public_bootstrap import validate
data = json.load(open('tests/fixtures/public-bootstrap-candidate.json'))
data['memory']['sources'][0]['checked_at'] = '2026-01-01T00:00:00'
result = validate(data, datetime(2026, 1, 2, tzinfo=timezone.utc))
assert not result['valid_manifest'], result
"""
        run = subprocess.run([sys.executable, "-c", script], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)

    def test_source_id_values_are_not_echoed(self):
        data = copy.deepcopy(BASE)
        data["memory"]["sources"][0]["id"] = "synthetic-do-not-echo"
        self.assertNotIn("synthetic-do-not-echo", json.dumps(validate(data, NOW)))


if __name__ == "__main__":
    unittest.main()
