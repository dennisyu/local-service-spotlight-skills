"""Audit Factory 20: ledger, scoring, gates (positive + one negative per gate), render,
cost, router escalation, Basecamp export and the end-to-end pipeline (fake models).

Render tests skip when Playwright/Chromium is unavailable; everything else is stdlib +
pypdf and runs in CI.
"""
import base64
import contextlib
import copy
import importlib.util
import io
import itertools
import json
import pathlib
import re
import shutil
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1] / "audit-factory"
sys.path.insert(0, str(ROOT))

from factory20 import basecamp, cli, components as C, cost, gates, model as M, pipeline, render, router, score  # noqa: E402
from factory20 import ocr as OCR  # noqa: E402
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

    def test_blind_copy_strips_guidance_inside_rows(self):
        # the first blind test leaked both of these and the drafting model copied them verbatim
        data = json.loads((DEMO / "ledger.json").read_text())
        data["conflicts"] = [{"id": "V-C01", "metric": "roofs", "value_a": {"value": "3,500"},
                              "how_audit_must_present": "Lead with 3,500 as 'Vega says'."}]
        data["items"][0]["notes"] = "[lane #4] Counted 386 reviews. [editor] Frame this as the hero claim."
        b = blind_copy(data)
        self.assertNotIn("how_audit_must_present", b["conflicts"][0])
        self.assertEqual(b["conflicts"][0]["value_a"]["value"], "3,500")
        self.assertEqual(b["items"][0]["notes"], "[lane #4] Counted 386 reviews.")
        self.assertNotIn("[editor]", json.dumps(b))

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
        # the synthetic demo has no real preparer photo, so G81 warns; nothing else may
        self.assertEqual(rep.verdict, "FIX", rep.failures())
        self.assertEqual([c["id"] for c in rep.checks if c["status"] != "PASS"], ["G81"])

    def test_a_real_audit_without_the_preparers_face_holds(self):
        real = copy.deepcopy(AUDIT)
        real["meta"]["confidentiality"] = "Client edition"
        rep = gates.gate_audit(render.expand(real, LEDGER), LEDGER, "standard")
        self.assertEqual(rep.verdict, "HOLD")
        self.assertEqual([c["id"] for c in rep.failures()], ["G81"])
        real["meta"]["prepared_by"]["photo"] = "assets/preparer.jpg"
        rep = gates.gate_audit(render.expand(real, LEDGER), LEDGER, "standard")
        self.assertNotIn("G81", {c["id"] for c in rep.checks if c["status"] != "PASS"})

    def test_a_missing_qr_tool_warns_and_is_not_sent_to_the_writer(self):
        rr = {"pdf_pages": 20, "overflow_pages": [], "fill": {}, "links": 500,
              "qr_decoded": "UNCHECKED: pdftoppm (poppler-utils) is not installed"}
        rep = gates.gate_render(rr, "https://localservicespotlight.com/install/").summary()
        r05 = next(c for c in rep["checks"] if c["id"] == "R05")
        self.assertEqual(r05["status"], "WARN")
        self.assertIn("pdftoppm", r05["msg"])
        self.assertNotEqual(rep["verdict"], "HOLD")
        self.assertFalse([i for i in pipeline.fix_list({"checks": []}, {"gates": rep}) if i["id"] == "R05"])

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

    def test_G65_client_change_without_approval(self):
        self.mutate(lambda a: a["actions"][0].update(executor="AGENT"), "G65")   # A1 changes the client's site

    def test_G65_internal_report_needs_no_gate(self):
        self.assertEqual(status(gate(copy.deepcopy(AUDIT)), "G65"), "PASS")      # A16 posts to our own thread

    def test_G71_business_phone_allowed_when_listed(self):
        a = copy.deepcopy(AUDIT)
        self.page(a, 4)["blocks"][-1]["text"].append("The profile lists 918-555-0142 as the main line.")
        full = render.expand(a, LEDGER)
        listed = {c["id"]: c for c in gates.gate_audit(full, LEDGER, "standard", allowed_phones=["(918) 555-0142"]).checks}
        self.assertEqual(listed["G71"]["status"], "PASS")
        unlisted = {c["id"]: c for c in gates.gate_audit(full, LEDGER, "standard").checks}
        self.assertEqual(unlisted["G71"]["status"], "FAIL")

    def test_G80_missing_qr_without_expansion(self):
        self.mutate(lambda a: None, "G80", expand=False)

    def test_G80_expansion_adds_qr(self):
        self.assertEqual(status(gate(copy.deepcopy(AUDIT)), "G80"), "PASS")

    def test_G74_item_numbers_follow_the_brief(self):
        a = copy.deepcopy(AUDIT)
        self.page(a, 7)["blocks"][-1].setdefault("text", []).append("Investors valued it at $14M in March.")
        full = render.expand(a, LEDGER)
        # "ab" is too short to check, but it is still item 1, so the hit is item 2
        checks = {c["id"]: c for c in gates.gate_audit(full, LEDGER, "standard", do_not_print=["ab", "$14M"]).checks}
        self.assertIn("item 2 on page 7", checks["G74"]["msg"])


# ---------------------------------------------------------------- G75: do-not-print inside images
def fake_ocr(text, seen=None):
    """An OCR engine that 'reads' the given text from any image, and records what it read."""
    def read(path):
        if seen is not None:
            seen.append((pathlib.Path(path), pathlib.Path(path).read_bytes()))
        return text
    return read


PANEL_TEXT = ("Nik Halik\nEntrepreneur\nSpouse: Jane\nHalik · Children: Ava Halik, Leo Halik\n"
              "Born: Melbourne")


class ImageDoNotPrintTests(unittest.TestCase):
    """G74 reads text; a Google panel screenshot is pixels. On the 2026-11-11 Nik Halik audit
    a page-1 screenshot showed private family names from brief.do_not_print and every gate
    passed. G75 reads embedded images with OCR."""

    def g75(self, audit=None, dnp=("Jane Halik",), engine=None, base=DEMO):
        full = render.expand(audit or copy.deepcopy(AUDIT), LEDGER)
        checks = {c["id"]: c for c in gates.gate_audit(full, LEDGER, "standard", do_not_print=list(dnp),
                                                       asset_base=base, ocr_engine=engine).checks}
        return checks["G75"]

    def test_demo_embeds_a_screenshot_on_page_one(self):
        self.assertIn((1, "assets/mock-gbp.png"), gates.embedded_images(AUDIT))

    def test_passes_when_the_brief_has_no_list(self):
        self.assertEqual(self.g75(dnp=(), engine=fake_ocr(PANEL_TEXT))["status"], "PASS")

    def test_fails_on_a_private_name_read_in_a_screenshot(self):
        seen = []
        c = self.g75(engine=fake_ocr(PANEL_TEXT, seen))
        self.assertEqual(c["status"], "FAIL")
        self.assertTrue(c["hard"])
        self.assertIn("item 1 in the image on page 1 (assets/mock-gbp.png)", c["msg"])
        self.assertIn("redact", c["msg"])
        self.assertNotIn("jane", c["msg"].lower())                  # gate.json travels further than the brief
        self.assertEqual(seen[0][1], (DEMO / "assets" / "mock-gbp.png").read_bytes())
        # the text gate cannot see it: the name is in the image, not in audit.json
        full = render.expand(AUDIT, LEDGER)
        g74 = {c["id"]: c for c in gates.gate_audit(full, LEDGER, "standard", do_not_print=["Jane Halik"]).checks}["G74"]
        self.assertEqual(g74["status"], "PASS")

    def test_a_hit_holds_the_audit(self):
        full = render.expand(AUDIT, LEDGER)
        rep = gates.gate_audit(full, LEDGER, "standard", do_not_print=["Ava Halik"], asset_base=DEMO,
                               ocr_engine=fake_ocr(PANEL_TEXT))
        self.assertEqual(rep.verdict, "HOLD")

    def test_passes_when_the_screenshot_holds_nothing_private(self):
        self.assertEqual(self.g75(engine=fake_ocr("Vega Roofing LLC 4.9 386 Google reviews"))["status"], "PASS")

    def test_warns_without_an_ocr_engine(self):
        with mock.patch.object(OCR, "engine", return_value=None):
            c = self.g75()
        self.assertEqual(c["status"], "WARN")
        self.assertFalse(c["hard"])
        self.assertIn("no OCR engine", c["msg"])
        self.assertIn("tesseract", c["msg"].lower())
        self.assertIn("crop or redact private fields in screenshots before use", c["msg"])

    def test_an_unreadable_image_warns_and_is_never_passed(self):
        def broken(path):
            raise OCR.OcrError("psm 3: Error in pixReadStream")
        c = self.g75(engine=broken)
        self.assertEqual(c["status"], "WARN")
        self.assertIn("unchecked", c["msg"])
        self.assertIn("pixReadStream", c["msg"])

    def test_a_missing_image_file_is_unchecked(self):
        with tempfile.TemporaryDirectory() as d:
            c = self.g75(engine=fake_ocr(PANEL_TEXT), base=pathlib.Path(d))
        self.assertEqual(c["status"], "WARN")
        self.assertIn("file not found", c["msg"])

    def test_reads_inline_data_uri_images_and_the_preparers_photo(self):
        a = copy.deepcopy(AUDIT)
        png = (DEMO / "assets" / "mock-gbp.png").read_bytes()
        p19 = next(p for p in a["pages"] if p["n"] == 19)
        p19["blocks"].append({"type": "screenshot", "span": 4, "caption": "panel",
                              "src": "data:image/png;base64," + base64.b64encode(png).decode()})
        a["meta"]["prepared_by"]["photo"] = "assets/mock-gbp.png"
        self.assertIn((1, "assets/mock-gbp.png"), gates.embedded_images(a)[-1:])
        seen = []
        c = self.g75(a, engine=fake_ocr("nothing private here", seen))
        self.assertEqual(c["status"], "PASS")
        self.assertEqual(len(seen), 3)                                # page-1 block, page-19 data URI, face
        self.assertTrue(all(b == png for _, b in seen))
        self.assertFalse(any(p.exists() for p, _ in seen if p.name.startswith("inline")))   # temp file removed
        c = self.g75(a, engine=fake_ocr(PANEL_TEXT))
        self.assertIn("page 19", c["msg"])

    def test_remote_images_are_not_embedded_so_not_read(self):
        a = copy.deepcopy(AUDIT)
        for p in a["pages"]:
            for b in p.get("blocks", []):
                if b.get("type") in gates.IMAGE_BLOCKS:
                    b["src"] = "https://example.com/panel.png"
        self.assertEqual(self.g75(a, engine=fake_ocr(PANEL_TEXT))["status"], "PASS")

    def test_matching_survives_ocr_noise(self):
        self.assertTrue(OCR.contains("Spouse: JANE\nHalik", "Jane Halik"))           # case, line break, punctuation
        self.assertTrue(OCR.contains("Spouse JaneHalik born", "Jane Halik"))          # merged words
        self.assertTrue(OCR.contains("valued at $14M.", "$14M"))
        self.assertFalse(OCR.contains("valued at $140M", "$14M"))                    # whole words only
        self.assertFalse(OCR.contains("Bob Leeds", "Bo Lee"))                         # short items never squeezed
        self.assertFalse(OCR.contains("anything", "  "))

    def test_g75_is_not_sent_to_the_writer(self):
        rep = {"checks": [{"id": "G75", "status": "FAIL", "msg": "x"}, {"id": "G75", "status": "WARN", "msg": "y"}]}
        self.assertEqual(pipeline.fix_list(rep), [])

    def test_cli_gate_reads_images_beside_the_audit(self):
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            shutil.copy(DEMO / "audit.json", d / "audit.json")
            shutil.copytree(DEMO / "assets", d / "assets")
            (d / "brief.json").write_text(json.dumps({"do_not_print": ["Leo Halik"]}))
            out = io.StringIO()
            with mock.patch.object(OCR, "engine", return_value=fake_ocr(PANEL_TEXT)), contextlib.redirect_stdout(out):
                code = cli.main(["gate", str(d / "audit.json"), "--ledger", str(DEMO / "ledger.json")])
        self.assertEqual(code, 2)
        self.assertIn("[FAIL] G75", out.getvalue())
        self.assertNotIn("Leo", out.getvalue())

    @unittest.skipUnless(shutil.which("tesseract"), "tesseract not installed")
    def test_real_ocr_reads_the_demo_screenshot(self):
        # "Tulsa, Oklahoma" is printed only inside the page-1 Google profile mock
        self.assertEqual(self.g75(dnp=["Tulsa, Oklahoma"])["status"], "FAIL")
        self.assertEqual(self.g75(dnp=["never-printed-xyz"])["status"], "PASS")


# ---------------------------------------------------------------- renderer geometry (no browser)
SVG_RECT = re.compile(r'<rect x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)"[^>]*data-id="([^"]*)"')


def ctx_for(audit):
    return render.Ctx(render.expand(audit, LEDGER), LEDGER, DEMO)


def bars_in(svg_html):
    return [(m.group(5), float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4)))
            for m in SVG_RECT.finditer(svg_html)]


def overlaps(a, b):
    _, ax, ay, aw, ah = a
    _, bx, by, bw, bh = b
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


class SwimlaneTests(unittest.TestCase):
    """Bars once alternated two rows by register order, so a third action in the same window
    was drawn on top of the first: A1, A6, A7, A9 and A18 vanished from the Nik Halik plan."""

    def plan(self, actions):
        a = copy.deepcopy(AUDIT)
        a["actions"] = actions
        return C.swimlane({"type": "swimlane", "span": 12}, ctx_for(a))

    def action(self, aid, function, window, due):
        return {**AUDIT["actions"][0], "id": aid, "function": function, "window": window, "due": due}

    def assert_every_bar_visible(self, html_, ids):
        bars = bars_in(html_)
        self.assertEqual(sorted(b[0] for b in bars), sorted(ids))     # one rect per action, none missing
        for a, b in itertools.combinations(bars, 2):
            self.assertFalse(overlaps(a, b), f"{a[0]} overlaps {b[0]}")
        w, h = (float(v) for v in re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', html_).groups())
        for aid, x, y, bw, bh in bars:
            self.assertTrue(0 <= x and x + bw <= w and y + bh <= h, f"{aid} is outside the chart")
        return bars

    def test_three_same_window_actions_in_one_lane_are_three_separate_rects(self):
        start = AUDIT["meta"]["plan_start"]
        acts = [self.action("A1", "Web", 7, start), self.action("A6", "Web", 7, start),
                self.action("A7", "Web", 7, start), self.action("A9", "Outreach", 7, start)]
        bars = self.assert_every_bar_visible(self.plan(acts), ["A1", "A6", "A7", "A9"])
        web = sorted((b for b in bars if b[0] in ("A1", "A6", "A7")), key=lambda b: b[2])
        self.assertEqual(len({b[2] for b in web}), 3)                  # three rows
        self.assertEqual(len({b[1] for b in web}), 1)                  # one time window
        a9 = next(b for b in bars if b[0] == "A9")
        self.assertGreaterEqual(a9[2], web[-1][2] + web[-1][4])        # next lane starts below the third row

    def test_lane_height_grows_with_its_rows(self):
        start = AUDIT["meta"]["plan_start"]
        acts = [self.action(f"A{k}", "Web", 7, start) for k in range(1, 6)] + [self.action("A6", "Social", 7, start)]
        html_ = self.plan(acts)
        bands = [float(h) for h in re.findall(r'height="([\d.]+)" class="laneband"', html_)]
        self.assertEqual(bands[0], 8 + 13 * 5)                        # max(34, 8 + 13 * rows)
        self.assert_every_bar_visible(html_, [f"A{k}" for k in range(1, 7)])

    def test_alternating_colour_follows_the_row(self):
        start = AUDIT["meta"]["plan_start"]
        acts = [self.action("A1", "Web", 7, start), self.action("A2", "Social", 7, start)]
        html_ = self.plan(acts)
        self.assertNotIn('class="bar alt"', html_)                     # both sit in row 0 of their lane

    def test_pack_rows_needs_a_two_pixel_gap(self):
        self.assertEqual(C.pack_rows([(0, 30), (32, 60), (31, 50)]), [0, 0, 1])
        self.assertEqual(C.pack_rows([(0, 30), (0, 30), (0, 30)]), [0, 1, 2])
        self.assertEqual(C.pack_rows([]), [])

    def test_demo_plan_hides_no_action(self):
        html_ = C.swimlane({"type": "swimlane", "span": 12}, ctx_for(copy.deepcopy(AUDIT)))
        self.assert_every_bar_visible(html_, [a["id"] for a in AUDIT["actions"]])


class HeatmapTests(unittest.TestCase):
    """The score box printed <subtotal>/100 even when rows were UNKNOWN, so the page showed
    25/100 beside a verdict of '25 known of 90 checked'."""

    def heat(self, mutate=None):
        a = copy.deepcopy(AUDIT)
        if mutate:
            mutate(a)
        ctx = ctx_for(a)
        return C.heatmap({"type": "heatmap", "auto": True, "span": 12}, ctx), ctx.exam_result()

    def box(self, html_):
        m = re.search(r'<div class="et-v">([^<]*)<span>([^<]*)</span>', html_)
        return m.group(1), m.group(2)

    def test_complete_box_is_out_of_100(self):
        html_, res = self.heat()
        self.assertEqual(self.box(html_), ("38", "/100"))

    def test_incomplete_box_counts_only_checked_points(self):
        def f(a):
            a["exams"]["brand_authority"]["rows"][2]["score"] = "UNKNOWN"
        html_, res = self.heat(f)
        self.assertEqual(res["status"], "INCOMPLETE")
        self.assertEqual(self.box(html_), ("33", "/90 checked"))
        self.assertNotIn("/100", html_)
        self.assertIn("33 known of 90 checked", res["verdict"])        # box and verdict say the same thing

    def test_identity_hold_prints_no_number(self):
        html_, res = self.heat(lambda a: a["meta"]["identity"].update(status="HOLD"))
        num, units = self.box(html_)
        self.assertFalse(re.search(r"\d", num + units), (num, units))

    def test_unknown_row_ids_clear_the_word_and_stay_inside_the_chart(self):
        def f(a):
            for k in (2, 5):
                a["exams"]["brand_authority"]["rows"][k]["score"] = "UNKNOWN"
        html_, _ = self.heat(f)
        width = float(re.search(r'viewBox="0 0 ([\d.]+)', html_).group(1))
        words = {float(y): float(x) for x, y in re.findall(r'<text x="([\d.]+)" y="([\d.]+)" class="tvb">UNKNOWN', html_)}
        self.assertEqual(len(words), 2)
        ids = re.findall(r'<text x="([\d.]+)" y="([\d.]+)" class="tid">([^<]*)</text>', html_)
        self.assertEqual(len(ids), 10)
        for x, y, text in ids:
            x = float(x)
            word_x = words.get(float(y) + 1)                           # the word sits 1px lower than its ids
            if word_x is not None:
                self.assertGreaterEqual(x - word_x, 70, text)
            self.assertLessEqual(x + len(text) * C.MONO_EM * 7.6, width, text)   # never clipped by the viewBox

    def test_fit_ids_drops_whole_ids_not_half_ids(self):
        self.assertEqual(C.fit_ids(["V-E011", "V-E012", "V-E013"], 200), "V-E011 V-E012 V-E013")
        self.assertEqual(C.fit_ids(["V-E011", "V-E012", "V-E013"], 62), "V-E011 V-E012")
        self.assertEqual(C.fit_ids(["V-E011", "V-E012", "V-E013", "V-E014"], 500), "V-E011 V-E012 V-E013")
        self.assertEqual(C.fit_ids(["V-E011"], 10), "")


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

    def test_reference_run_is_priced_from_measured_tokens(self):
        ref = cost.reference_cost(cost.load_routing())
        self.assertAlmostEqual(ref["cache_read_share"], 0.983)
        self.assertTrue(275 < ref["audit_usd"] < 290, ref)           # audit only
        self.assertTrue(295 < ref["total_usd"] < 310, ref)           # with the website package
        self.assertGreater(ref["audit_usd"] / cost.audit_cost("standard")["total_usd"], 40)

    def test_muse_tier_keeps_the_frontier_slice(self):
        cfg = cost.load_routing()
        self.assertEqual(cost.audit_cost("muse", cfg)["frontier_usd"], cost.audit_cost("standard", cfg)["frontier_usd"])

    def test_haiku_long_context_tier(self):
        cfg = cost.load_routing()
        self.assertEqual(cost.price(cfg, "claude-haiku-5-5", 50_000)["in"], 0.10)
        self.assertEqual(cost.price(cfg, "claude-haiku-5-5", 150_000)["in"], 0.50)


class RouterTests(unittest.TestCase):
    def test_safe_model_climbs_past_flagged_models(self):
        cfg = cost.load_routing()
        self.assertEqual(router.safe_model(cfg, "or:deepseek/deepseek-v4.1-flash", False), "or:deepseek/deepseek-v4.1-flash")
        self.assertEqual(router.safe_model(cfg, "or:deepseek/deepseek-v4.1-flash", True), "claude-haiku-5-5")
        # a one-key OpenRouter tier climbs its own ladder, so the safe model is on the same key
        self.assertEqual(router.safe_model(cfg, "or:deepseek/deepseek-v4.1-flash", True, "openrouter-lean"),
                         "or:anthropic/claude-haiku-5.5")

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
        self.assertEqual(calls[:2], ["or:deepseek/deepseek-v4.1-flash", "or:deepseek/deepseek-v4.1-flash"])
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
        # "None for schema; X approves" names a gate, so it is not an ungated agent task
        self.assertEqual(basecamp.executor({"action": "Add schema markup",
                                            "human_gate": "None for schema; Marisol updates LinkedIn"}), "AGENT_AFTER_APPROVAL")

    def test_every_agent_todo_names_a_running_agent(self):
        payload = basecamp.todos(AUDIT, LEDGER)
        self.assertEqual(payload["unassigned"], [])
        a1 = next(t for t in payload["todos"] if t["id"] == "A1")
        self.assertEqual(a1["agent"], "Claude Fleet")
        self.assertIn("Runs it:", a1["description"])
        bare = basecamp.todos(AUDIT, LEDGER, agents={"functions": {}, "default_agent": "", "chaser": ""})
        self.assertIn("A1", bare["unassigned"])


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
            self.assertEqual(res["verdict"], "READY", res)
            self.assertEqual(res["gate"], "FIX")                 # only G81: the synthetic demo has no real face
            self.assertEqual(res["fix_rounds"], 0)               # a photo is not the writer's to fix
            self.assertEqual(res["review"], "READY")
            log = json.loads((d / "run.json").read_text())
            models = {a["stage"]: a["model"] for a in log["attempts"]}
            self.assertEqual(models["synthesis"], "claude-opus-5-5")
            self.assertEqual(models["pages"], "claude-sonnet-5-5")
            self.assertEqual(models["review"], "claude-opus-5-5")

    def _run_dir(self, d, brief_extra=None):
        shutil.copy(DEMO / "ledger.json", d / "ledger.json")
        shutil.copytree(DEMO / "assets", d / "assets")
        m = AUDIT["meta"]
        brief = {k: m[k] for k in ("subject", "subject_type", "title", "date", "plan_start", "prepared_for",
                                   "prepared_by", "confidentiality", "palette", "install_url")}
        brief.update(brief_extra or {})
        (d / "brief.json").write_text(json.dumps(brief))

    def test_gate_failure_gets_a_fix_round(self):
        from factory20.testing import split_fixture
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            self._run_dir(d)
            outs = split_fixture(AUDIT)
            broken = copy.deepcopy(outs["pages"])
            p12 = next(p for p in broken["pages"] if p["n"] == 12)
            p12["blocks"] = [b for b in p12["blocks"] if b["type"] not in M.VISUAL_BLOCKS]   # G40 fails
            for name in ("identity", "score", "synthesis", "actions"):
                (d / f"{name}.json").write_text(json.dumps(outs[name]))
            (d / "pages.json").write_text(json.dumps(broken))
            good12 = next(p for p in outs["pages"]["pages"] if p["n"] == 12)
            base = fake_from_fixture(str(DEMO / "audit.json"))

            def fake(stage, model, system, user):
                if stage == "fix":
                    self.assertIn("G40", user)                       # the writer is told exactly what failed
                    return json.dumps({"pages": [good12]})
                return base(stage, model, system, user)
            res = pipeline.run(d, "standard", fake=fake, render_pdf=False)
            self.assertEqual(res["fix_rounds"], 1, res)
            self.assertEqual(res["verdict"], "READY", res)

    def test_review_finding_triggers_a_fix_and_second_pass(self):
        s1 = {"verdict": "NOT_READY", "findings": [{"id": "R1-01", "severity": "S1", "page": 5, "where": "callout",
              "problem": "Score row 4 is generous.", "fix": "Lower it to 6.", "evidence": ["V-E011"]}],
              "score_adjustments": [], "strongest": ["page 2"]}
        from factory20.testing import READY_REVIEW
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            self._run_dir(d)
            res = pipeline.run(d, "standard", fake=fake_from_fixture(str(DEMO / "audit.json"), review=[s1, READY_REVIEW]),
                               render_pdf=False)
            self.assertEqual(res["review_passes"], 2, res)
            self.assertEqual(res["verdict"], "READY", res)
            stages = [a["stage"] for a in json.loads((d / "run.json").read_text())["attempts"]]
            self.assertIn("fix", stages)

    def test_serious_finding_on_the_last_pass_holds(self):
        s1 = {"verdict": "NOT_READY", "findings": [{"id": "R1-01", "severity": "S0", "page": 4, "where": "graph",
              "problem": "A namesake is used as proof.", "fix": "Remove it.", "evidence": ["V-A01"]}],
              "score_adjustments": [], "strongest": []}
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            self._run_dir(d)
            res = pipeline.run(d, "lean", fake=fake_from_fixture(str(DEMO / "audit.json"), review=s1), render_pdf=False)
            self.assertEqual(res["verdict"], "HOLD", res)

    def test_private_field_in_a_screenshot_holds_without_a_fix_round(self):
        """No drafting model can redact pixels: the run holds, names G75, and spends nothing on fixes."""
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            self._run_dir(d, {"do_not_print": ["Jane Halik"]})
            seen = []
            with mock.patch.object(OCR, "engine", return_value=fake_ocr(PANEL_TEXT, seen)):
                res = pipeline.run(d, "standard", fake=fake_from_fixture(str(DEMO / "audit.json")), render_pdf=False)
            self.assertEqual(res["verdict"], "HOLD", res)
            self.assertEqual(res["holding_gates"], ["G75"], res)
            self.assertEqual(res["fix_rounds"], 0, res)
            self.assertEqual(seen[0][1], (d / "assets" / "mock-gbp.png").read_bytes())   # read from the run folder
            stages = {a["stage"] for a in json.loads((d / "run.json").read_text())["attempts"]}
            self.assertNotIn("fix", stages)
            self.assertNotIn("review", stages)                         # a HOLD never reaches the reviewer

    def test_confidential_brief_never_reaches_a_flagged_model(self):
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            self._run_dir(d, {"do_not_print": ["$14M valuation"]})
            pipeline.run(d, "lean", fake=fake_from_fixture(str(DEMO / "audit.json")), render_pdf=False, review=False)
            models = {a["model"] for a in json.loads((d / "run.json").read_text())["attempts"]}
            self.assertFalse(any("deepseek" in m for m in models), models)


class SchemaTests(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec("jsonschema"), "jsonschema not installed")
    def test_demo_matches_schema(self):
        import jsonschema
        schema = json.loads((ROOT / "schema" / "audit.schema.json").read_text())
        jsonschema.validate(AUDIT, schema)


if __name__ == "__main__":
    unittest.main()
