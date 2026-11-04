"""Audit Factory 20: ledger, scoring, gates (positive + one negative per gate), render,
cost, router escalation, Basecamp export and the end-to-end pipeline (fake models).

Render tests skip when Playwright/Chromium is unavailable; everything else is stdlib +
pypdf and runs in CI.
"""
import copy
import importlib.util
import json
import pathlib
import shutil
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1] / "audit-factory"
sys.path.insert(0, str(ROOT))

from factory20 import basecamp, cost, gates, model as M, pipeline, render, router, score  # noqa: E402
from factory20.ledger import Ledger, blind_copy  # noqa: E402
from factory20.testing import fake_from_fixture  # noqa: E402

DEMO = ROOT / "fixtures" / "demo"
AUDIT = json.loads((DEMO / "audit.json").read_text())
LEDGER = Ledger.load(DEMO / "ledger.json")


def gate(a, tier="standard", expand=True):
    a = render.expand(a, LEDGER) if expand else a
    return {c["id"]: c for c in gates.gate_audit(a, LEDGER, tier).checks}


def status(checks, gid):
    hits = [c for k, c in checks.items() if k == gid]
    return hits[0]["status"] if hits else None


def have_browser():
    if importlib.util.find_spec("playwright") is None:
        return False
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch().close()
        return True
    except Exception:
        return False


class LedgerTests(unittest.TestCase):
    def test_loads_claude_format(self):
        st = LEDGER.stats()
        self.assertEqual(st["evidence"], 60)
        self.assertEqual(st["ambiguous"], 2)
        self.assertEqual(st["conflicts"], 3)
        self.assertEqual(st["unknowns"], 3)
        self.assertTrue(LEDGER.has("V-C02") and LEDGER.has("V-U01") and LEDGER.has("V-A01"))

    def test_pack_lists_every_row_once(self):
        pack = LEDGER.pack()
        for r in LEDGER.rows:
            self.assertEqual(pack.count(f"\n{r['id']} |"), 1, r["id"])

    def test_blind_copy_strips_prior_synthesis(self):
        data = json.loads((DEMO / "ledger.json").read_text())
        data["insights"] = ["the answer"]
        self.assertNotIn("insights", blind_copy(data))
        self.assertIn("items", blind_copy(data))

    def test_csv_ledger(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "l.csv"
            p.write_text("id,claim,value,source_url,state,evidence_class\nX-E001,claim,v,https://a.example,OBSERVED,SELF-CLAIM\n")
            L = Ledger.load(p)
            self.assertTrue(L.has("X-E001"))
            self.assertEqual(L.get("X-E001")["cls"], "SELF-CLAIM")


class ScoreTests(unittest.TestCase):
    def test_complete_total_is_the_sum(self):
        r = score.compute(AUDIT["exams"]["brand_authority"], "CONFIRMED")
        self.assertEqual(r["status"], "COMPLETE")
        self.assertEqual(r["total"], 38)
        self.assertEqual(r["verdict"], "BELOW PASS LINE")

    def test_unknown_row_is_incomplete_not_zero(self):
        ex = copy.deepcopy(AUDIT["exams"]["brand_authority"])
        ex["rows"][2]["score"] = "UNKNOWN"
        r = score.compute(ex, "CONFIRMED")
        self.assertEqual(r["status"], "INCOMPLETE")
        self.assertIsNone(r["total"])
        self.assertEqual(r["known_subtotal"], 33)

    def test_identity_hold_has_no_number(self):
        r = score.compute(AUDIT["exams"]["brand_authority"], "HOLD")
        self.assertEqual(r["status"], "HOLD")
        self.assertIsNone(r["total"])

    def test_demo_rows_are_calibrated(self):
        flags = [f for f in score.calibration_flags(AUDIT["exams"]["brand_authority"], LEDGER) if f["level"] == "FAIL"]
        self.assertEqual(flags, [])

    def _flags(self, row):
        return {f["code"] for f in score.calibration_flags({"rows": [row]}, LEDGER)}

    def test_generous_seven_needs_two_independent_rows(self):
        self.assertIn("GENEROUS_7", self._flags({"n": 5, "score": 7, "why": "x", "evidence": ["V-E052", "V-E001"]}))

    def test_self_claims_cap_at_four(self):
        self.assertIn("SELF_CLAIM_CAP", self._flags({"n": 1, "score": 5, "why": "x", "evidence": ["V-E001", "V-E004"]}))

    def test_zero_needs_named_harm(self):
        self.assertIn("ZERO_NEEDS_HARM", self._flags({"n": 5, "score": 0, "why": "x", "evidence": ["V-E032"]}))
        self.assertNotIn("ZERO_NEEDS_HARM", self._flags({"n": 5, "score": 0, "why": "x", "harm": "form emails a dead domain", "evidence": ["V-E032"]}))

    def test_negative_evidence_cannot_carry_a_high_score(self):
        # broken financing page + dead contact form are independent, but they prove failure
        self.assertIn("CONTRADICTED", self._flags({"n": 5, "score": 8, "why": "x", "evidence": ["V-E052", "V-E031", "V-E032"]}))

    def test_polarity_heuristic_and_override(self):
        self.assertEqual(LEDGER.get("V-E031")["polarity"], "negative")
        self.assertEqual(LEDGER.get("V-E011")["polarity"], "positive")
        from factory20.ledger import polarity
        self.assertEqual(polarity({"claim": "no complaints in 3 years", "polarity": "positive"}), "positive")

    def test_unknown_support_fails(self):
        self.assertIn("UNKNOWN_SUPPORT", self._flags({"n": 9, "score": 3, "why": "x", "evidence": ["V-U03"]}))


class GatePositiveTests(unittest.TestCase):
    def test_demo_passes_standard(self):
        rep = gates.gate_audit(render.expand(AUDIT, LEDGER), LEDGER, "standard")
        self.assertEqual(rep.verdict, "PASS", rep.failures())

    def test_enterprise_is_stricter(self):
        rep = gates.gate_audit(render.expand(AUDIT, LEDGER), LEDGER, "enterprise")
        self.assertEqual(rep.verdict, "HOLD")
        self.assertIn("G13", {c["id"] for c in rep.failures()})


class GateNegativeTests(unittest.TestCase):
    """Each mutation must trip exactly the gate that guards it."""

    def mutate(self, fn, gid, expect="FAIL", expand=True):
        a = copy.deepcopy(AUDIT)
        fn(a)
        self.assertEqual(status(gate(a, expand=expand), gid), expect, gid)

    def page(self, a, n):
        return next(p for p in a["pages"] if p["n"] == n)

    def test_G01_page_count(self):
        self.mutate(lambda a: a["pages"].pop(), "G01")

    def test_G03_coverage(self):
        self.mutate(lambda a: self.page(a, 11).update(type="audience"), "G03")

    def test_G10_dangling_ref(self):
        self.mutate(lambda a: self.page(a, 3)["blocks"][0]["steps"][0]["evidence"].append("V-E999"), "G10")

    def test_G11_namesake_used_as_proof(self):
        self.mutate(lambda a: self.page(a, 2)["blocks"][0]["items"][0]["evidence"].append("V-A01"), "G11")

    def test_G20_too_few_cards(self):
        self.mutate(lambda a: self.page(a, 2)["blocks"][0].update(items=self.page(a, 2)["blocks"][0]["items"][:3]), "G20")

    def test_G21_card_without_so(self):
        self.mutate(lambda a: self.page(a, 2)["blocks"][0]["items"][1].pop("so"), "G21")

    def test_G22_summary_of_unknowns(self):
        def f(a):
            for c in self.page(a, 2)["blocks"][0]["items"][:3]:
                c["badge"] = "UNKNOWN"
        self.mutate(f, "G22")

    def test_G23_action_not_in_register(self):
        self.mutate(lambda a: self.page(a, 2)["blocks"][0]["items"][0]["actions"].append("A99"), "G23")

    def test_G30_label_headline(self):
        self.mutate(lambda a: self.page(a, 6).update(headline="Overview"), "G30")

    def test_G31_buzzword(self):
        def f(a):
            next(b for b in self.page(a, 3)["blocks"] if b["type"] == "prose")["text"].append("We will leverage synergy.")
        self.mutate(f, "G31")

    def test_G40_page_without_visual(self):
        self.mutate(lambda a: self.page(a, 12).update(blocks=[b for b in self.page(a, 12)["blocks"] if b["type"] not in M.VISUAL_BLOCKS]), "G40")

    def test_G50_identity_one_attribute(self):
        self.mutate(lambda a: a["meta"]["identity"].update(attributes=a["meta"]["identity"]["attributes"][:1]), "G50")

    def test_G52_generous_score(self):
        self.mutate(lambda a: a["exams"]["brand_authority"]["rows"][4].update(score=8), "G52")

    def test_G54_hand_typed_score(self):
        self.mutate(lambda a: self.page(a, 6).update(dek="Brand Authority is 61/100 by our count."), "G54")

    def test_G61_action_without_test(self):
        self.mutate(lambda a: a["actions"][0].update(acceptance_test="done"), "G61")

    def test_G62_duplicate_action_id(self):
        self.mutate(lambda a: a["actions"][1].update(id="A1"), "G62")

    def test_G70_personal_email(self):
        self.mutate(lambda a: self.page(a, 4)["blocks"][-1]["text"].append("Write to marisol@gmail.com."), "G70")

    def test_G71_phone(self):
        self.mutate(lambda a: self.page(a, 4)["blocks"][-1]["text"].append("Call 918-555-0142 today."), "G71")

    def test_G72_agent_receipt_on_client_page(self):
        self.mutate(lambda a: self.page(a, 20)["blocks"][0]["text"].append("Agent receipt: Claude · action: drafted"), "G72")

    def test_G24_page_two_over_budget(self):
        def f(a):
            c = self.page(a, 2)["blocks"][0]["items"][0]
            c["body"] += " " + " ".join(["In 2025 the crew logged 41 storm jobs."] * 10)
        self.mutate(f, "G24", expect="WARN")

    def test_G24_names_the_long_card(self):
        a = copy.deepcopy(AUDIT)
        self.page(a, 2)["blocks"][0]["items"][2]["body"] += " " + " ".join(["Nine of 12 crews."] * 6)
        msg = gate(a)["G24"]["msg"]
        self.assertIn("card 3", msg)
        self.assertIn("cut at least", msg)

    def test_G74_do_not_print_fails_without_repeating_the_secret(self):
        a = copy.deepcopy(AUDIT)
        self.page(a, 7)["blocks"][-1].setdefault("text", []).append("Investors valued it at $14M in March.")
        full = render.expand(a, LEDGER)
        checks = {c["id"]: c for c in gates.gate_audit(full, LEDGER, "standard", do_not_print=["$14M"]).checks}
        self.assertEqual(checks["G74"]["status"], "FAIL")
        self.assertNotIn("14m", checks["G74"]["msg"].lower())
        self.assertIn("page 7", checks["G74"]["msg"])
        clean = {c["id"]: c for c in gates.gate_audit(full, LEDGER, "standard", do_not_print=["never-printed-xyz"]).checks}
        self.assertEqual(clean["G74"]["status"], "PASS")

    def test_R02_message_says_how_much_to_cut(self):
        rr = {"pdf_pages": 20, "overflow_pages": [2], "fill": {}, "links": 100, "qr_decoded": "u",
              "overflow_detail": {"2": {"over_pct": 0.08, "cut_words": 52, "tallest": ["card 4 (78 words)"]}}}
        ch = {c["id"]: c for c in gates.gate_render(rr, "u").checks}
        self.assertEqual(ch["R02"]["status"], "FAIL")
        self.assertIn("cut about 52 words", ch["R02"]["msg"])
        self.assertIn("card 4", ch["R02"]["msg"])

    def test_G80_missing_qr_without_expansion(self):
        self.mutate(lambda a: None, "G80", expand=False)

    def test_G80_expansion_adds_qr(self):
        self.assertEqual(status(gate(copy.deepcopy(AUDIT)), "G80"), "PASS")


@unittest.skipUnless(have_browser(), "Playwright/Chromium not available")
class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = pathlib.Path(tempfile.mkdtemp())
        cls.pdf = cls.tmp / "demo.pdf"
        cls.rr = render.render(DEMO / "audit.json", DEMO / "ledger.json", cls.pdf)

    def test_exactly_twenty_pages(self):
        self.assertEqual(self.rr["pdf_pages"], 20)

    def test_no_overflow_and_assets_present(self):
        self.assertEqual(self.rr["overflow_pages"], [])
        self.assertEqual(self.rr["missing_assets"], [])

    def test_qr_decodes_to_install_url(self):
        self.assertEqual(self.rr["qr_decoded"], "https://localservicespotlight.com/install/")

    def test_evidence_chips_are_links(self):
        self.assertGreater(self.rr["links"], 100)

    def test_render_gates_pass(self):
        self.assertNotEqual(gates.gate_render(self.rr, "https://localservicespotlight.com/install/").verdict, "HOLD")

    def test_overflow_detail_names_the_tallest_card(self):
        a = copy.deepcopy(AUDIT)
        card = next(p for p in a["pages"] if p["n"] == 2)["blocks"][0]["items"][3]
        card["body"] += " " + " ".join(["In 2025 the crew logged 41 storm jobs in 9 counties."] * 30)
        path = self.tmp / "long.json"
        path.write_text(json.dumps(a))
        rr = render.render(path, DEMO / "ledger.json", self.tmp / "long.pdf")
        self.assertIn(2, rr["overflow_pages"])
        d = rr["overflow_detail"]["2"]
        self.assertGreater(d["cut_words"], 10)
        self.assertTrue(d["tallest"][0].startswith("card 4"), d["tallest"])
        msg = {c["id"]: c for c in gates.gate_render(rr, "u").checks}["R02"]["msg"]
        self.assertIn("page 2 runs", msg)

    def test_pdfcheck_grades_demo(self):
        from factory20 import pdfcheck
        m = pdfcheck.measure(str(self.pdf))
        self.assertEqual(m["pages"], 20)
        self.assertEqual(m["pages_with_3plus_ids"], 20)
        self.assertIn(m["grade"], ("solid", "frontier"))


class CostTests(unittest.TestCase):
    def test_tiers_order_and_bounds(self):
        cfg = cost.load_routing()
        t = {k: cost.audit_cost(k, cfg)["total_usd"] for k in ("lean", "standard", "enterprise")}
        self.assertLess(t["lean"], t["standard"])
        self.assertLess(t["standard"], t["enterprise"])
        self.assertLess(t["standard"], 10)

    def test_reference_run_is_two_orders_more(self):
        ref = cost.reference_cost(cost.load_routing(), 0.97)["total_usd"]
        self.assertGreater(ref, 300)
        self.assertGreater(ref / cost.audit_cost("standard")["total_usd"], 40)

    def test_muse_tier_keeps_the_frontier_slice(self):
        cfg = cost.load_routing()
        self.assertEqual(cost.audit_cost("muse", cfg)["frontier_usd"], cost.audit_cost("standard", cfg)["frontier_usd"])

    def test_haiku_long_context_tier(self):
        cfg = cost.load_routing()
        self.assertEqual(cost.price(cfg, "claude-haiku-5-5", 50_000)["in"], 0.10)
        self.assertEqual(cost.price(cfg, "claude-haiku-5-5", 150_000)["in"], 0.50)


class RouterTests(unittest.TestCase):
    def test_extract_json(self):
        self.assertEqual(router.extract_json('x ```json\n{"a": 1}\n``` y'), {"a": 1})
        self.assertEqual(router.extract_json('{"b": 2}'), {"b": 2})

    def _run(self, replies, check):
        calls = []

        def fake(stage, model, system, user):
            calls.append(model)
            return replies[min(len(calls) - 1, len(replies) - 1)]
        with tempfile.TemporaryDirectory() as d:
            res = router.run_stage("pages", "user", "lean", pathlib.Path(d), check=check, fake=fake)
            log = json.loads((pathlib.Path(d) / "run.json").read_text())
        return res, calls, log

    def test_accepts_first_valid_reply(self):
        res, calls, log = self._run(['{"ok": true}'], lambda o: [])
        self.assertTrue(res["ok"])
        self.assertEqual(len(calls), 1)

    def test_retries_with_feedback_then_escalates_one_rung(self):
        res, calls, log = self._run(['{"ok": false}'], lambda o: [] if o.get("ok") else ["not ok"])
        self.assertFalse(res["ok"])
        self.assertEqual(calls[:2], ["deepseek-v4.1-flash", "deepseek-v4.1-flash"])
        self.assertEqual(calls[2], "claude-haiku-5-5")
        self.assertEqual(len(set(calls)), 2)  # exactly one escalation
        self.assertTrue(all(a["problems"] for a in log["attempts"]))

    def test_manual_provider_writes_prompt_and_waits(self):
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            with self.assertRaises(router.Pending):
                router.run_stage("pages", "user", "muse", d, check=lambda o: [])
            self.assertTrue((d / "prompts" / "pages.md").exists())
            (d / "outputs" / "pages.json").write_text('{"pages": []}')
            self.assertTrue(router.run_stage("pages", "user", "muse", d, check=lambda o: [])["ok"])


class BasecampTests(unittest.TestCase):
    def test_every_action_becomes_a_todo_with_a_brief(self):
        payload = basecamp.todos(AUDIT, LEDGER)
        self.assertEqual(len(payload["todos"]), len(AUDIT["actions"]))
        a8 = next(t for t in payload["todos"] if t["id"] == "A8")
        self.assertEqual(a8["executor"], "HUMAN")
        a1 = next(t for t in payload["todos"] if t["id"] == "A1")
        self.assertIn("Done when", a1["description"])
        self.assertIn("Agent brief", a1["description"])
        self.assertIn("A test lead arrives", a1["description"])
        self.assertGreaterEqual(payload["counts"]["AGENT"] + payload["counts"]["AGENT_AFTER_APPROVAL"], 12)

    def test_heuristic_executor(self):
        self.assertEqual(basecamp.executor({"action": "Record four short videos", "human_gate": "x"}), "HUMAN")
        self.assertEqual(basecamp.executor({"action": "Add schema markup", "human_gate": "none"}), "AGENT")


class PipelineTests(unittest.TestCase):
    def test_end_to_end_with_fake_models(self):
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            shutil.copy(DEMO / "ledger.json", d / "ledger.json")
            shutil.copytree(DEMO / "assets", d / "assets")
            m = AUDIT["meta"]
            brief = {k: m[k] for k in ("subject", "subject_type", "title", "date", "plan_start", "prepared_for",
                                       "prepared_by", "confidentiality", "palette", "install_url")}
            (d / "brief.json").write_text(json.dumps(brief))
            res = pipeline.run(d, "standard", fake=fake_from_fixture(str(DEMO / "audit.json")), render_pdf=False)
            self.assertEqual(res["verdict"], "REVIEW_READY", res)
            self.assertEqual(res["gate"], "PASS")
            log = json.loads((d / "run.json").read_text())
            models = {a["stage"]: a["model"] for a in log["attempts"]}
            self.assertEqual(models["synthesis"], "claude-opus-5-5")
            self.assertEqual(models["pages"], "claude-sonnet-5-5")


class SchemaTests(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec("jsonschema"), "jsonschema not installed")
    def test_demo_matches_schema(self):
        import jsonschema
        schema = json.loads((ROOT / "schema" / "audit.schema.json").read_text())
        jsonschema.validate(AUDIT, schema)


if __name__ == "__main__":
    unittest.main()
