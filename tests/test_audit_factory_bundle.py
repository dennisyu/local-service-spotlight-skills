"""Audit Factory 20 bundle: a finished run becomes a bundle the house audit-quality gate grades.

The demo run here is synthetic. Its model answers are replayed by factory20.testing's stand-in
and, where no browser is installed (CI), its PDF is twenty blank pages written by a render
stand-in. Nothing in it is client data, a real review or a real calibration, so the gate must
hold it: production mode because it is synthetic, exercise mode because calibration, the
independent review and most required checks are honestly open. The "real run" test relabels
the same demo inputs as non-synthetic and runs them through the local OpenRouter stand-in, only
to show which gaps a real run would be held on.
"""
import contextlib
import hashlib
import io
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parents[1]
KIT = REPO / "audit-factory"
GATE = REPO / "docs" / "audit-quality"
for p in (KIT, GATE, pathlib.Path(__file__).resolve().parent):
    sys.path.insert(0, str(p))

from factory20 import bundle, cli, gates, model as M, pipeline, render  # noqa: E402
from factory20.testing import fake_from_fixture  # noqa: E402
import verify_bundle  # noqa: E402
from test_audit_factory import have_browser  # noqa: E402
from test_audit_factory_openrouter import COST_PER_CALL, MockOpenRouter  # noqa: E402

DEMO = KIT / "fixtures" / "demo"
AUDIT = json.loads((DEMO / "audit.json").read_text())

# Reasons the gate gives for gaps that are really open in a factory run. Anything else (a changed
# file, a schema error, a broken envelope) means the bundle itself is wrong.
OPEN_GATES = (
    "source time requires timezone", "review evidence needs independent reviewer", "product scope not agreed",
    "authority or hold", "specialist scoring lacks typed exact-version validation",
    "missing/failed/incorrectly typed required check: ", "allowance unknown or exhausted",
    "missing typed routing capability evidence", "retrieve missing source",
    "attributed/proposed/decided claim needs limitation and test", "visual render review missing or stale",
    "unaccepted moderate defect", "hard defect open or closure unverified", "unresolved critical or major defect",
    "missing independent reviewer/author or self-review", "stale/incomplete/incorrectly typed final review: audit-pdf",
    "uncalibrated numeric acceptance", "top review and required check receipt differ", "required checks",
    "independent exact-revision review", "uncalibrated", "incomplete or below threshold", "rating evidence",
    "receipt is not ready for the asserted stage",
)
INTEGRITY_KEYS = {"receipt_sha256", "manifest_sha256", "artifact_count", "evidence_count", "checker_sha256"}


def quiet(fn, *args):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*args)


def stand_in_render(run: pathlib.Path) -> None:
    """What render.render leaves behind, without a browser (CI has none): twenty blank pages and
    a report that says so — no links, QR unchecked — with the real render gates run on it."""
    from pypdf import PdfWriter

    audit = json.loads((run / "audit.json").read_text())
    writer = PdfWriter()
    for _ in audit["pages"]:
        writer.add_blank_page(width=612, height=792)
    with open(run / "audit.pdf", "wb") as f:
        writer.write(f)
    rr = {"pdf": str(run / "audit.pdf"), "html": None, "pdf_pages": len(audit["pages"]), "overflow_pages": [],
          "fit_applied": [], "overflow_detail": {}, "fill": {}, "links": 0, "missing_assets": [],
          "qr_decoded": render.QR_UNCHECKED + ": test stand-in renderer, no browser"}
    rr["gates"] = gates.gate_render(rr, audit["meta"].get("install_url", render.INSTALL_URL)).summary()
    (run / "audit.pdf.render.json").write_text(json.dumps(rr, indent=1))


def demo_run(parent: pathlib.Path, review=None, tier="standard", with_review=True) -> pathlib.Path:
    """`factory20 init --from-demo`, then the full pipeline with replayed answers."""
    run = parent / "demo-run"
    assert quiet(cli.main, ["init", str(run), "--from-demo"]) == 0
    res = pipeline.run(run, tier, fake=fake_from_fixture(str(DEMO / "audit.json"), review=review), render_pdf=False,
                       review=with_review)
    assert res["gate"] != "HOLD", res
    stand_in_render(run)
    return run


def sha(path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


class DemoBundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.run_dir = demo_run(pathlib.Path(cls.tmp.name))
        cls.run_json = sha(cls.run_dir / "run.json")
        cls.summary = bundle.build(cls.run_dir)
        cls.receipt = json.loads((cls.run_dir / bundle.RECEIPT).read_text())

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def copy(self) -> pathlib.Path:
        d = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d)
        return pathlib.Path(shutil.copytree(self.run_dir, d / "run"))

    def verify(self, root=None, mode="exercise"):
        return verify_bundle.verify(root or self.run_dir, "bundle-manifest.json", mode)

    # ---------------------------------------------------------------- the gate's verdicts
    def test_exercise_mode_binds_every_file_then_holds_only_on_open_gates(self):
        """EXERCISE_PASS needs a receipt the gate accepts outright: recorded calibration, an exact-hash
        independent review and all fifteen checks PASS. None of that exists, so the honest result
        is HOLD — but only after every file binding and the receipt schema have passed."""
        r = self.verify()
        self.assertEqual(r["decision"], "HOLD", r)
        self.assertEqual(r["receipt_decision"], "HOLD")
        self.assertTrue(INTEGRITY_KEYS <= set(r), r["reasons"][:5])     # only set once every file checked out
        self.assertEqual(r["artifact_count"], 2)
        self.assertEqual(r["evidence_count"], len(self.receipt["evidence"]))
        self.assertEqual(set(r["checker_sha256"]), set(verify_bundle.BOUND_FILES))
        stray = [x for x in r["reasons"] if not x.startswith(OPEN_GATES)]
        self.assertEqual(stray, [])
        for gap in ("uncalibrated numeric acceptance", "missing independent reviewer/author or self-review",
                    "stale/incomplete/incorrectly typed final review: audit-pdf", "visual render review missing or stale",
                    "missing/failed/incorrectly typed required check: privacy"):
            self.assertIn(gap, r["reasons"])
        self.assertNotIn("missing/failed/incorrectly typed required check: identity", r["reasons"])

    def test_production_mode_holds_the_demo_because_it_is_synthetic(self):
        r = self.verify(mode="production")
        self.assertEqual(r["decision"], "HOLD")
        self.assertEqual(r["reasons"], ["synthetic exercise cannot establish production acceptance",
                                        "known synthetic fixture cannot establish production acceptance",
                                        "known synthetic evidence locator"])
        cmd = [sys.executable, str(GATE / "verify_bundle.py"), "--root", str(self.run_dir)]
        self.assertEqual(subprocess.run(cmd, capture_output=True, text=True).returncode, 1)

    def test_one_changed_pdf_byte_fails_verification(self):
        run = self.copy()
        data = bytearray((run / "audit.pdf").read_bytes())
        data[len(data) // 2] ^= 0x01
        (run / "audit.pdf").write_bytes(bytes(data))
        r = self.verify(run)
        self.assertEqual(r["decision"], "HOLD")
        self.assertEqual(r["reasons"], ["changed file: audit.pdf"])
        self.assertFalse(INTEGRITY_KEYS & set(r))

    def test_one_changed_evidence_capture_fails_verification(self):
        run = self.copy()
        manifest = json.loads((run / bundle.MANIFEST).read_text())
        envelope = json.loads((run / manifest["evidence"]["V-E012"]["path"]).read_text())
        capture = run / envelope["capture"]["path"]
        capture.write_bytes(capture.read_bytes().replace(b"236 of 386", b"237 of 386"))
        self.assertEqual(self.verify(run)["reasons"], ["changed file: " + envelope["capture"]["path"]])
        run = self.copy()                                   # a run record bound in place is a capture too
        gate = run / "gate.json"
        gate.write_text(gate.read_text() + " ")
        self.assertEqual(self.verify(run)["reasons"], ["changed file: gate.json"])

    def test_a_missing_required_artifact_fails(self):
        run = self.copy()
        (run / "audit.pdf").unlink()
        r = self.verify(run)
        self.assertEqual(r["decision"], "HOLD")
        self.assertTrue(any("audit.pdf" in x for x in r["reasons"]), r["reasons"])
        with self.assertRaises(bundle.BundleError) as e:
            bundle.build(run)
        self.assertIn("audit.pdf", str(e.exception))
        out = subprocess.run([sys.executable, "-m", "factory20", "bundle", str(run)], cwd=KIT,
                             capture_output=True, text=True)
        self.assertEqual(out.returncode, 2, out.stdout + out.stderr)
        self.assertIn("not bundled", out.stdout)

    # ---------------------------------------------------------------- what the receipt says
    def test_bundle_files_sit_beside_the_run_and_run_json_is_untouched(self):
        self.assertEqual(sha(self.run_dir / "run.json"), self.run_json)
        self.assertTrue((self.run_dir / "bundle-manifest.json").is_file() and (self.run_dir / "uaqg-receipt.json").is_file())
        manifest = json.loads((self.run_dir / bundle.MANIFEST).read_text())
        self.assertEqual(manifest["receipt"]["path"], "uaqg-receipt.json")
        self.assertEqual(manifest["artifacts"]["audit-pdf"],
                         {"path": "audit.pdf", "sha256": sha(self.run_dir / "audit.pdf")})
        self.assertEqual(len(list((self.run_dir / "uaqg" / "evidence").glob("*.json"))), len(self.receipt["evidence"]))
        self.assertEqual(self.receipt["schema_version"], "UAQG-TIER-RECEIPT-1.0.0")
        self.assertEqual(self.receipt["standard"], "UAQG-1.1.0")

    def test_calibration_ratings_and_review_stay_open(self):
        q = self.receipt["quality"]
        self.assertEqual(q["calibration"], {"status": "NOT_RUN", "receipt_id": None, "anchor_ids": []})
        self.assertEqual(q["ratings"], [None] * 6)
        self.assertEqual(q["rationales_and_evidence"], [None] * 6)
        self.assertIsNone(q["total"])
        ids = {e["id"] for e in self.receipt["evidence"]}
        self.assertFalse(ids & {"CAL-FAIL", "CAL-BORDERLINE", "CAL-STRONG"})       # never the fixture's calibration
        self.assertFalse(any(e["kind"] == "CALIBRATION_RECORD" for e in self.receipt["evidence"]))
        review = self.receipt["independent_review"]
        self.assertEqual((review["status"], review["reviewer_id"], review["fresh_context"]), ("UNKNOWN", None, False))
        self.assertEqual(review["artifacts"][0]["coverage"], "NONE")
        replay = next(e for e in self.receipt["evidence"] if e["id"] == "RUN-review")
        self.assertEqual((replay["inspection"], replay["reviewer_id"]), ("NOT_CHECKED", None))
        self.assertIn("stand-in", replay["scope"])

    def test_only_identity_is_filled_by_a_factory_gate(self):
        checks = {c["name"]: c for c in self.receipt["checks"]}
        self.assertEqual(set(checks), set(bundle.CHECK_KINDS))
        self.assertEqual(checks["identity"]["status"], "PASS")
        self.assertEqual(checks["identity"]["evidence_ids"], ["RUN-identity"])
        ev = {e["id"]: e for e in self.receipt["evidence"]}
        for name, c in checks.items():
            if name != "identity":
                self.assertEqual(c["status"], "UNKNOWN", name)
                self.assertEqual(ev[c["evidence_ids"][0]]["inspection"], "NOT_CHECKED", name)

    def test_the_replayed_cost_is_not_reported_as_a_cost(self):
        logged = sum(a["usd"] for a in json.loads((self.run_dir / "run.json").read_text())["attempts"])
        self.assertGreater(logged, 0)                        # list price on stand-in tokens, not a charge
        cost = self.receipt["timing"]["actual_cost"]
        self.assertEqual((cost["value"], cost["state"]), (None, "UNKNOWN"))
        self.assertIn("stand-in", cost["method"])
        self.assertIsNone(self.receipt["allowance"]["consumed"])
        self.assertEqual(self.receipt["timing"]["agent_runtime"]["state"], "MEASURED")

    def test_insights_become_claims_and_every_todo_an_action(self):
        cards = [i for p in AUDIT["pages"] for b in p.get("blocks", []) if b.get("type") == "cards" for i in b["items"]]
        claims = {c["id"]: c for c in self.receipt["claims"]}
        self.assertEqual(sum(1 for c in claims if c.startswith("P")), len(cards))
        self.assertEqual([a["id"] for a in self.receipt["actions"]], [a["id"] for a in AUDIT["actions"]])
        self.assertEqual(claims["P02-C1"]["evidence_ids"], cards[0]["evidence"])
        self.assertEqual(claims["P02-C8"]["type"], "UNKNOWN")
        self.assertEqual(claims["P02-C6"]["evidence_state"], "INFERRED")
        self.assertIsNone(claims["P02-C6"]["limitation"])      # the card states none; the gate says so
        for aid in ("A13", "A17"):                             # no card links them: their own finding, REPORTED
            self.assertEqual(claims[f"AF-{aid}"]["evidence_state"], "REPORTED")
            self.assertEqual(next(a for a in self.receipt["actions"] if a["id"] == aid)["finding_ids"], [f"AF-{aid}"])

    def test_pdf_visual_manifest_covers_every_page_once(self):
        pdf = self.receipt["artifacts"][0]
        self.assertEqual((pdf["id"], pdf["page_count"]), ("audit-pdf", 20))
        pages = [v["page"] for v in pdf["visual_manifest"]]
        self.assertEqual(pages, list(range(1, 21)))
        p17 = pdf["visual_manifest"][16]
        self.assertIn("QR code is a link", p17["caption"])
        self.assertTrue(all(v["render_receipt_id"] == "GAP-usability" for v in pdf["visual_manifest"]))

    def test_synthetic_run_is_labelled_synthetic_everywhere(self):
        self.assertTrue(self.receipt["synthetic"])
        self.assertTrue(self.receipt["run_id"].startswith("SYNTHETIC-"))
        self.assertTrue(all(e["locator"].startswith("synthetic-fixture:") for e in self.receipt["evidence"]))
        manifest = json.loads((self.run_dir / bundle.MANIFEST).read_text())
        envelope = json.loads((self.run_dir / manifest["evidence"]["RUN-call-log"]["path"]).read_text())
        self.assertIs(envelope["synthetic"], True)
        self.assertEqual(self.receipt["links"], [])
        self.assertFalse(self.receipt["release"]["attempted"])

    def test_tables_match_the_gate_and_the_kit(self):
        profiles = json.loads((GATE / "product-profiles.json").read_text())
        self.assertEqual(bundle.CHECK_KINDS, profiles["required_checks"])
        self.assertEqual(set(bundle.VISUAL_KIND), M.VISUAL_BLOCKS)

    # ---------------------------------------------------------------- refusals and real-run inputs
    def test_a_stale_gate_report_is_refused(self):
        run = self.copy()
        audit = json.loads((run / "audit.json").read_text())
        page = next(p for p in audit["pages"] if p["n"] == 12)
        page["blocks"] = [b for b in page["blocks"] if b["type"] not in M.VISUAL_BLOCKS]   # G40 would now fail
        (run / "audit.json").write_text(json.dumps(audit))
        with self.assertRaises(bundle.BundleError) as e:
            bundle.build(run)
        self.assertIn("gate.json does not match", str(e.exception))

    def test_a_unique_source_capture_is_bound_with_its_time(self):
        run = self.copy()
        (run / "captures").mkdir()
        (run / "captures" / "maps.json").write_text('{"reviews": 386}')
        about = "https://vegaroofing.example/about"         # captured twice: the ledger cannot say which one
        lines = [{"url": "https://maps.example/vega-roofing", "kind": "reviews", "status": "ok",
                  "captured_at": "2026-11-02T14:05:00-06:00", "path": "captures/maps.json"},
                 {"url": about, "captured_at": "2026-11-02T14:00:00Z", "path": "captures/maps.json"},
                 {"url": about, "captured_at": "2026-11-02T15:00:00Z", "path": "captures/maps.json"}]
        (run / "sources.jsonl").write_text("\n".join(json.dumps(x) for x in lines) + "\n")
        bundle.build(run)
        receipt = json.loads((run / bundle.RECEIPT).read_text())
        ev = {e["id"]: e for e in receipt["evidence"]}
        manifest = json.loads((run / bundle.MANIFEST).read_text())
        envelope = json.loads((run / manifest["evidence"]["V-E012"]["path"]).read_text())
        self.assertEqual(envelope["capture"]["path"], "captures/maps.json")
        self.assertEqual(ev["V-E012"]["retrieved_at"], "2026-11-02T14:05:00-06:00")
        ambiguous = json.loads((run / manifest["evidence"]["V-E001"]["path"]).read_text())
        self.assertEqual(ambiguous["capture"]["path"], "uaqg/captures/V-E001.json")
        self.assertIn("RUN-source-log", ev)
        self.assertTrue(INTEGRITY_KEYS <= set(self.verify(run)))

    def test_review_findings_become_open_defects(self):
        s0 = {"verdict": "NOT_READY", "findings": [{"id": "R1-01", "severity": "S0", "page": 4, "where": "graph",
              "problem": "A namesake is used as proof.", "fix": "Remove it.", "evidence": ["V-A01"]}],
              "score_adjustments": [], "strongest": []}
        with tempfile.TemporaryDirectory() as d:
            run = demo_run(pathlib.Path(d), review=s0, tier="lean")
            bundle.build(run)
            receipt = json.loads((run / bundle.RECEIPT).read_text())
            self.assertIn({"id": "REVIEW-R1-01", "severity": "S0", "closed": False, "closure_review_receipt": None,
                           "disposition": dict.fromkeys(("accepted_by", "risk_reason", "owner", "deadline",
                                                         "completion_test"))}, receipt["defects"])
            self.assertIn("hard defect open or closure unverified", self.verify(run)["reasons"])

    def test_a_run_without_its_review_still_bundles_and_says_so(self):
        with tempfile.TemporaryDirectory() as d:
            run = demo_run(pathlib.Path(d), with_review=False)
            summary = bundle.build(run)
            receipt = json.loads((run / bundle.RECEIPT).read_text())
            self.assertEqual(receipt["independent_review"]["receipt_id"], "GAP-reproducibility")
            self.assertNotIn("RUN-review", {e["id"] for e in receipt["evidence"]})
            self.assertIn("independent review: open; no factory review ran", summary["open"])
            r = self.verify(run)
            self.assertTrue(INTEGRITY_KEYS <= set(r))
            self.assertEqual([x for x in r["reasons"] if not x.startswith(OPEN_GATES)], [])

    def test_cli_writes_the_bundle_and_names_the_grading_command(self):
        run = self.copy()
        out = subprocess.run([sys.executable, "-m", "factory20", "bundle", str(run)], cwd=KIT,
                             capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("verify_bundle.py --root", out.stdout)
        self.assertIn("--mode exercise", out.stdout)
        self.assertIn("reviewer calibration: NOT_RUN", out.stdout)


class RealRunTests(unittest.TestCase):
    """The demo inputs relabelled as a real run (no SYNTHETIC label, a preparer photo, a goal) and
    answered through the local OpenRouter stand-in, which reports a charge per call the way
    OpenRouter does. This is not a real audit; it shows what a real run is held on."""

    def setUp(self):
        self.mock = MockOpenRouter()
        self.env = {k: os.environ.get(k) for k in ("OPENROUTER_API_KEY", "OPENROUTER_BASE_URL")}
        os.environ["OPENROUTER_API_KEY"] = "test-key-not-a-secret"
        os.environ["OPENROUTER_BASE_URL"] = self.mock.base
        self.tmp = tempfile.TemporaryDirectory()
        self.run_dir = pathlib.Path(self.tmp.name) / "run"
        self.run_dir.mkdir()
        ledger = json.loads((DEMO / "ledger.json").read_text())
        ledger.pop("method_note")
        (self.run_dir / "ledger.json").write_text(json.dumps(ledger, indent=1))
        shutil.copytree(DEMO / "assets", self.run_dir / "assets")
        brief = {k: AUDIT["meta"][k] for k in cli.BRIEF_KEYS}
        brief.update(confidentiality="Confidential - relabelled test run", goal="30% more inspection calls",
                     prepared_by=dict(brief["prepared_by"], photo="assets/mock-gbp.png"))
        (self.run_dir / "brief.json").write_text(json.dumps(brief))

    def tearDown(self):
        for k, v in self.env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self.mock.close()
        self.tmp.cleanup()

    def test_a_real_run_is_held_only_on_its_real_gaps(self):
        res = pipeline.run(self.run_dir, "openrouter-lean", render_pdf=False)
        self.assertEqual(res["verdict"], "READY", res)
        stand_in_render(self.run_dir)
        summary = bundle.build(self.run_dir)
        self.assertFalse(summary["synthetic"], summary["synthetic_reasons"])
        r = verify_bundle.verify(self.run_dir, "bundle-manifest.json", "production")
        self.assertEqual(r["decision"], "HOLD")
        self.assertTrue(INTEGRITY_KEYS <= set(r))
        self.assertFalse([x for x in r["reasons"] if "synthetic" in x])
        self.assertEqual([x for x in r["reasons"] if not x.startswith(OPEN_GATES)], [])
        self.assertIn("uncalibrated numeric acceptance", r["reasons"])
        receipt = json.loads((self.run_dir / bundle.RECEIPT).read_text())
        calls = json.loads((self.run_dir / "run.json").read_text())["attempts"]
        cost = receipt["timing"]["actual_cost"]
        self.assertEqual((cost["state"], cost["unit"]), ("MEASURED", "USD"))
        self.assertAlmostEqual(cost["value"], COST_PER_CALL * len(calls), places=6)
        self.assertEqual(receipt["goal"], "30% more inspection calls")
        review = receipt["independent_review"]
        self.assertTrue(review["reviewer_id"].startswith("factory20 review stage: "))
        self.assertEqual(review["status"], "UNKNOWN")                 # recorded as what it is, still open
        self.assertIn("exercise requires synthetic=true",
                      verify_bundle.verify(self.run_dir, "bundle-manifest.json", "exercise")["reasons"])


@unittest.skipUnless(have_browser(), "Playwright/Chromium not available")
class DocumentedCommandsTests(unittest.TestCase):
    """The README's own commands, end to end, with the real renderer."""

    def test_demo_init_run_bundle_and_grade(self):
        with tempfile.TemporaryDirectory() as d:
            run = str(pathlib.Path(d) / "demo")

            def factory(*args):
                return subprocess.run([sys.executable, "-m", "factory20", *args], cwd=KIT, capture_output=True, text=True)
            self.assertEqual(factory("init", run, "--from-demo").returncode, 0)
            out = factory("run", run, "--tier", "standard", "--fake", "fixtures/demo/audit.json")
            self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
            self.assertEqual(factory("bundle", run).returncode, 0)
            grade = [sys.executable, str(GATE / "verify_bundle.py"), "--root", run]
            ex = subprocess.run(grade + ["--mode", "exercise"], capture_output=True, text=True)
            result = json.loads(ex.stdout)
            self.assertEqual((ex.returncode, result["decision"]), (1, "HOLD"))
            self.assertTrue(INTEGRITY_KEYS <= set(result))
            self.assertEqual([x for x in result["reasons"] if not x.startswith(OPEN_GATES)], [])
            prod = json.loads(subprocess.run(grade, capture_output=True, text=True).stdout)
            self.assertIn("synthetic exercise cannot establish production acceptance", prod["reasons"])
            receipt = json.loads((pathlib.Path(run) / "uaqg-receipt.json").read_text())
            self.assertGreater(len(receipt["artifacts"][0]["visual_manifest"]), 19)
            self.assertIn("Chromium", next(r for r in receipt["routing"] if r["stage"] == "LAYOUT")["executor"])


if __name__ == "__main__":
    unittest.main()
