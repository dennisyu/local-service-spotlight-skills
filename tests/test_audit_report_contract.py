import copy
import hashlib
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_report_contract import AuditContractError, canonical_hash, comparable, validate_batch, validate_report


def fixtures():
    rubric = {"approved": True, "exam_family": "Brand Authority", "rubric_id": "brand-authority",
              "rubric_version": "1.0", "calculation": "sum", "scale_max": 100, "pass_line": 80,
              "rows": [{"id": str(i), "max": 10} for i in range(10)]}
    report = {k: rubric[k] for k in ("exam_family", "rubric_id", "rubric_version")}
    report.update(subject_id="synthetic-subject", rubric_sha256=canonical_hash(rubric), total=48, verdict="FAIL", coverage_id="fixture",
                  rows=[{"id": str(i), "score": v, "state": "CHECKED", "evidence_ids": ["E1"]}
                        for i, v in enumerate([5, 5, 5, 5, 5, 5, 5, 5, 4, 4])])
    return rubric, report


class AuditContractTest(unittest.TestCase):
    def test_checked_in_final_pdf_and_current_extraction(self):
        root=Path(__file__).parent/"fixtures"/"audit-contract"
        self.assertEqual(1,validate_batch(json.loads((root/"batch.json").read_text()),root)["artifact_count"])
    def test_rounding_cannot_create_a_pass(self):
        rubric, report = fixtures()
        rubric.update(calculation="weighted_mean", display_decimals=1,
                      rows=[{"id":"a", "max":100, "weight":100}])
        report.update(rubric_sha256=canonical_hash(rubric), total=80, verdict="FAIL",
                      rows=[{"id":"a", "score":79.999, "state":"CHECKED", "evidence_ids":["E1"]}])
        self.assertEqual(79.999, validate_report(rubric, report)["calculated_subtotal"])
        report["verdict"] = "PASS"
        with self.assertRaisesRegex(AuditContractError, "verdict"): validate_report(rubric, report)

    def test_unknown_cannot_hide_invalid_weight_or_maximum(self):
        rubric, report = fixtures()
        rubric.update(calculation="weighted_mean", rows=[{"id":"a","max":100,"weight":120}, {"id":"b","max":100,"weight":-20}])
        report.update(rubric_sha256=canonical_hash(rubric), total=None, verdict="INCOMPLETE", known_subtotal=96,
                      rows=[{"id":"a","state":"CHECKED","score":80,"evidence_ids":["E1"]},
                            {"id":"b","state":"UNKNOWN","score":None,"reason":"no access"}])
        with self.assertRaisesRegex(AuditContractError, "negative weight"): validate_report(rubric, report)
        rubric["rows"][1].update(max=0, weight=0); rubric["rows"][0]["weight"]=100
        report["rubric_sha256"]=canonical_hash(rubric)
        with self.assertRaisesRegex(AuditContractError, "maximum"): validate_report(rubric, report)

    def test_correct_sum(self):
        rubric, report = fixtures()
        self.assertEqual(48, validate_report(rubric, report)["calculated_subtotal"])

    def test_historical_58_headline_48_cells_is_rejected(self):
        rubric, report = fixtures(); report["total"] = 58
        with self.assertRaisesRegex(AuditContractError, "headline"):
            validate_report(rubric, report)

    def test_unknown_is_not_zero_or_a_full_denominator_score(self):
        rubric, report = fixtures()
        report["rows"][0].update(score=None, state="UNKNOWN", reason="source blocked")
        report.update(total=None, verdict="INCOMPLETE", known_subtotal=43)
        self.assertEqual(["0"], validate_report(rubric, report)["unknown_rows"])
        report["rows"][0]["score"] = 0
        with self.assertRaisesRegex(AuditContractError, "null"):
            validate_report(rubric, report)

    def test_checked_zero_keeps_its_evidence(self):
        rubric, report = fixtures(); report["rows"][0]["score"] = 0; report["total"] = 43
        self.assertEqual([], validate_report(rubric, report)["unknown_rows"])

    def test_weighted_unknown_not_renormalized(self):
        rubric, report = fixtures()
        rubric.update(calculation="weighted_mean", rows=[{"id":"a","max":100,"weight":60}, {"id":"b","max":100,"weight":40}])
        report.update(rubric_sha256=canonical_hash(rubric), total=None, verdict="INCOMPLETE", known_subtotal=48,
                      rows=[{"id":"a","state":"CHECKED","score":80,"evidence_ids":["E1"]},
                            {"id":"b","state":"UNKNOWN","score":None,"reason":"no access"}])
        self.assertEqual(48, validate_report(rubric, report)["calculated_subtotal"])
        report["known_subtotal"] = 80
        with self.assertRaises(AuditContractError): validate_report(rubric, report)

    def test_rubric_family_version_hash_and_approval(self):
        for key, value in [("exam_family","SEO/Growth"),("rubric_version","2.0"),("rubric_sha256","stale")]:
            rubric, report = fixtures(); report[key] = value
            with self.assertRaises(AuditContractError): validate_report(rubric, report)
        rubric, report = fixtures(); rubric["approved"] = False
        with self.assertRaisesRegex(AuditContractError,"not approved"): validate_report(rubric, report)

    def test_different_exams_and_versions_do_not_form_a_trend(self):
        _, before = fixtures(); after = copy.deepcopy(before)
        self.assertTrue(comparable(before, after))
        for key in ["exam_family","rubric_version","rubric_sha256","coverage_id"]:
            after = copy.deepcopy(before); after[key] = "different"
            self.assertFalse(comparable(before, after))

    def test_graph_object_does_not_establish_panel_or_claim(self):
        rubric, report = fixtures()
        report["entity"] = {"graph_object_status":"RESOLVED", "kgmid":"/g/fixture", "identity_evidence_ids":["E1","E2"],
                            "normal_google_panel_status":"UNKNOWN", "owner_claim_status":"UNKNOWN"}
        validate_report(rubric, report)
        report["entity"]["normal_google_panel_status"] = "VISIBLE"
        with self.assertRaisesRegex(AuditContractError,"separate"): validate_report(rubric, report)
        report["entity"]["normal_google_panel_status"] = "UNKNOWN"
        report["entity"]["owner_claim_status"] = "CLAIMED"
        with self.assertRaisesRegex(AuditContractError,"owner-side"): validate_report(rubric, report)

    def test_duplicate_identity_and_public_button_do_not_prove_owner_claim(self):
        rubric, report = fixtures()
        report["entity"] = {"graph_object_status":"RESOLVED", "kgmid":"/g/fixture", "identity_evidence_ids":["E1","E1"],
                            "normal_google_panel_status":"UNKNOWN", "owner_claim_status":"UNKNOWN"}
        with self.assertRaisesRegex(AuditContractError,"two identity"): validate_report(rubric, report)
        report["entity"]["identity_evidence_ids"] = ["E1", "E2"]
        report["entity"].update(owner_claim_status="CLAIMED", owner_claim_receipt={"source":"public claim button"})
        with self.assertRaisesRegex(AuditContractError,"owner-side"): validate_report(rubric, report)
        report["entity"]["owner_claim_receipt"] = {"evidence_class":"OWNER_SIDE", "authorized_owner_access":True,
            "subject_id":"synthetic-subject", "status":"CLAIMED", "captured_at":"2026-10-02", "locator":"restricted:receipt-1"}
        validate_report(rubric, report)

    def test_forced_graph_panel_is_not_normal_visibility(self):
        rubric, report = fixtures()
        report["entity"] = {"graph_object_status":"UNKNOWN", "normal_google_panel_status":"VISIBLE", "owner_claim_status":"UNKNOWN",
                            "normal_query_receipt": dict.fromkeys(["query","captured_at","locale","location","device","personalization","locator"],"fixture")}
        report["entity"]["normal_query_receipt"]["forced_kgmid"] = True
        with self.assertRaisesRegex(AuditContractError,"forced"): validate_report(rubric, report)

    def test_missing_duplicate_and_out_of_range_rows(self):
        for mutation in [lambda r:r["rows"].pop(), lambda r:r["rows"].append(r["rows"][0]), lambda r:r["rows"][0].update(score=11)]:
            rubric, report = fixtures(); mutation(report)
            with self.assertRaises(AuditContractError): validate_report(rubric, report)

    def test_correction_must_propagate_to_every_final_artifact(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); names = ["summary.txt","leaderboard.txt","report-final-pdf-text.txt"]
            for name in names: (root/name).write_text("Panel observations remain query-specific.")
            manifest = {"expected_artifacts":names, "shared_facts":{"C1":{"revision":"r2","dependents":names,
                        "required_text":"Panel observations remain query-specific.","retired_text":["0 of 20 have a Knowledge Panel"]}},
                        "artifacts":[{"path":n,"sha256":hashlib.sha256((root/n).read_bytes()).hexdigest(),"shared_fact_revisions":{"C1":"r2"}} for n in names]}
            self.assertEqual(3,validate_batch(manifest,root)["artifact_count"])
            (root/names[-1]).write_text("0 of 20 have a Knowledge Panel")
            manifest["artifacts"][-1]["sha256"] = hashlib.sha256((root/names[-1]).read_bytes()).hexdigest()
            with self.assertRaisesRegex(AuditContractError,"retired claim"): validate_batch(manifest,root)

    def test_missing_artifact_or_stale_fact_blocks_batch(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/"report.txt").write_text("new")
            m={"expected_artifacts":["report.txt"],"shared_facts":{"C1":{"revision":"r2","dependents":["report.txt"]}},
               "artifacts":[{"path":"report.txt","sha256":hashlib.sha256(b"new").hexdigest(),"shared_fact_revisions":{"C1":"r1"}}]}
            with self.assertRaisesRegex(AuditContractError,"stale"): validate_batch(m,root)
            m["artifacts"]=[]
            with self.assertRaisesRegex(AuditContractError,"every expected"): validate_batch(m,root)

    def test_final_pdf_is_bound_to_fresh_extraction(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/"final.pdf").write_bytes(b"synthetic PDF binary")
            (root/"final.txt").write_bytes(b"corrected")
            m={"expected_artifacts":["final.pdf"], "shared_facts":{"C1":{"revision":"r2","dependents":["final.pdf"],"retired_text":["retired"]}},
               "artifacts":[{"path":"final.pdf","kind":"pdf","sha256":hashlib.sha256(b"synthetic PDF binary").hexdigest(),
                 "text_path":"final.txt","text_sha256":hashlib.sha256(b"corrected").hexdigest(),"shared_fact_revisions":{"C1":"r2"}}]}
            with patch("audit_report_contract.extract_pdf", return_value=b"retired"):
                with self.assertRaisesRegex(AuditContractError,"stale PDF extraction"): validate_batch(m,root)
            with patch("audit_report_contract.extract_pdf", return_value=b"corrected"):
                self.assertEqual(1,validate_batch(m,root)["artifact_count"])
            (root/"final.pdf").write_bytes(b"changed final binary")
            with self.assertRaisesRegex(AuditContractError,"final hash"): validate_batch(m,root)


if __name__ == "__main__": unittest.main()
