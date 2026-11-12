"""Audit Factory 20: what the Nov 10 pilot found (AUDIT-FACTORY-20261104).

The pilot rebuilt two finished audits at the standard and lean tiers, every model call answered
by a fresh model on the stage's tier. These defects kept runs from finishing, or made them pay
for retries and bigger models they did not need. 63 of the 67 tests below fail on the kit as it
was before this change (checked against 0e64f96, the head of #118); the other four guard the
demo's G10 and G11, the page footer, the bound on words to cut, and the rule in 15 that a term
used throughout routes nothing. 47 fail on the first version of this change (4f31005, which the
first independent review read), 33 on the second (f91aa74, which the second review read), 24 on
823ff8b, which came before the replays showed 10 and 11, 18 on 523018f, the version the graded
replays ran on (12-14), 16 on 3c585f4, 15 on 690d255, 13 on e5d07c3, 12 on 54e59a9 and 11 on
229cfc9, the version the Nov 12 rerun ran on (15).

1. A card built on REPORTED evidence failed G21: REPORTED is a ledger state, not a card badge.
2. Ids in a table's Evidence column became chips in the PDF but no check counted them, so a
   page citing a dozen ids in its tables failed "cite at least 3 evidence ids", a made-up or
   namesake id in a table cell passed G10 and G11, and an exam row could not cite the namesake
   the identity page lists in its table.
3. Overflow advice named blocks the renderer draws itself (the plan swimlane, the exam heatmap)
   as "block 1" to cut, measured blocks side by side at their grid row's height, and asked for
   words when a table's one-line rows free no height; it now names a move that clears it.
4. Nothing could revise the action register, so a gate item there (G64, or the word G72 bans
   inside an action) stayed open through every fix round.
5. When a cheap fix model could not clear a hard failure, the loop stopped with the audit on
   HOLD and rounds unspent, instead of giving the next rung one try.
6. Page 20 is built by code, so no writer can make room on it; its five-facts table now packs
   like the crosswalk beside it.
7. A fix answer of no pages (nothing on pages 3-19 can clear a ledger-level warning) was
   rejected and retried up the ladder, and a warning the last round already had got a round to
   itself. An empty answer is now an answer, and such warnings get no round of their own.
8. The manual provider (the muse tier answers pages, actions and fixes through files) kept one
   answer file per stage, so a retry, page batches 2-4, a second fix round and the register
   revision in 4 all read back the first answer. Each distinct call now has its own file.
9. The second review found four smaller holes: an empty fix answer to a FAIL on a page the
   writer owns was accepted; an overflow on code-built page 20 went to the page writer and
   bought a rung-up round; a photo or QR without a span was placed in a row of its own; and a
   ledger id without the id shape (E012) left every table citation of it unread. Such a ledger
   now holds the run before any call (G05).
10. Every replay put an invented screenshot on the cover. The cover card asks for a real
   captured image, but no prompt listed the files that exist and no gate looked, so each PDF
   printed an IMAGE NEEDED box on page 1 and passed. The page writers now get the list (under
   # ASSETS) and R06 holds an empty image box.
11. With the sure move in a parenthesis after "cut about N words", cheap fix models cut words
   from one-line table rows round after round (page 18: 76, then 54, then 44px over); the move
   now comes first. In three of the four replays page 18 ran over with a 206px timeline the
   writer added beside the renderer's swimlane, so the page card now says that pages 5, 17 and
   18 get their visual from the renderer.
12. The graded replays (523018f) found three more. The person ledger's capture date read
   "2026-10-07 (spot re-checks to 2026-10-23)": the run accepted it, every stage was paid for,
   and then factory20 bundle refused the finished run for want of one date. The run now holds at
   the ledger, by the bundle's own rule. A bars block without max is scaled to its largest
   value, so rubric rows scored 4 of 10 printed as full bars; the page card now says what max is.
   And the card's note that the renderer draws the visual on pages 5, 17 and 18 came out as
   copy ("The renderer adds the ten-row heatmap above these notes"); G31 now fails it.
13. A fix for the first review's findings ran page 19 40px over, and the kit paid for the second
   review on a draft that could only end HOLD, then reported the render verdict from before the
   review. Such a draft now gets the fix rounds the run has left first, and no review if it
   still holds; the result reports the final files.
14. The blind graders found two more. Page 20's chart title counted only the evidence rows
   ("119 rows") above a chart of all 134. And one fix round revised the cover before the pages
   it summarizes, so the cover kept a $21 ad test that the same round's page fix had made a $14
   test on page 11. The chart now shows only the rows its title counts, and a caption names the
   rest (the same lines as #121); the page writer goes first, and the cover's writer sees its
   pages.
15. The Nov 12 rerun on 229cfc9 passed the blind grading but held on two S1s that its first
   review had found, because each finding reached the wrong writer. An exam row's reason lives in
   score.json, which no fix writer could revise, so the page writer, told about page 5, printed a
   note about its own page ("this note governs"), which G31 now fails. And a finding about four
   pages, filed under page 1 with three of the others in its where field ("p5 ...; p10 ...; p18
   ..."), reached only the cover's writer: where was read only for the register. A review finding
   now goes to every page its where field or text names; to every writer that owns the words it
   quotes (a page, the register, or an exam row's reason, which the score model revises with its
   score locked), though a short term the audit uses throughout routes nothing; to the page writer
   when it covers pages it does not number; and to the register when it names an action. The
   reviewer's score adjustments now land before any writer reads the score.

Render tests skip when Playwright/Chromium is unavailable; the rest are stdlib.
"""
import copy
import importlib.util
import json
import pathlib
import re
import shutil
import sys
import tempfile
import types
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1] / "audit-factory"
sys.path.insert(0, str(ROOT))

from factory20 import components, cost, gates, model as M, pipeline, render, router  # noqa: E402
from factory20.ledger import Ledger  # noqa: E402
from factory20.testing import fake_from_fixture, split_fixture  # noqa: E402

DEMO = ROOT / "fixtures" / "demo"
AUDIT = json.loads((DEMO / "audit.json").read_text())
LEDGER = Ledger.load(DEMO / "ledger.json")


def checks(a, tier="standard"):
    return {c["id"]: c for c in gates.gate_audit(render.expand(a, LEDGER), LEDGER, tier).checks}


def page(a, n):
    return next(p for p in a["pages"] if p["n"] == n)


def have_browser():
    if importlib.util.find_spec("playwright") is None:
        return False
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            (render.launch_chromium(p) if hasattr(render, "launch_chromium") else p.chromium.launch()).close()
        return True
    except Exception:
        return False


def run_dir(d: pathlib.Path, outs: dict) -> None:
    shutil.copy(DEMO / "ledger.json", d / "ledger.json")
    shutil.copytree(DEMO / "assets", d / "assets")
    m = AUDIT["meta"]
    (d / "brief.json").write_text(json.dumps({k: m[k] for k in (
        "subject", "subject_type", "title", "date", "plan_start", "prepared_for", "prepared_by",
        "confidentiality", "palette", "install_url")}))
    for name in ("identity", "score", "synthesis", "pages", "actions"):
        (d / f"{name}.json").write_text(json.dumps(outs[name]))


# --------------------------------------------------------------------------- 1. badges
class BadgeTests(unittest.TestCase):
    def test_a_card_on_reported_evidence_passes_G21(self):
        a = copy.deepcopy(AUDIT)
        page(a, 2)["blocks"][0]["items"][0]["badge"] = "REPORTED"
        self.assertEqual(checks(a)["G21"]["status"], "PASS")

    def test_a_wrong_badge_is_told_which_badges_exist(self):
        a = copy.deepcopy(AUDIT)
        page(a, 2)["blocks"][0]["items"][0]["badge"] = "CONFIRMED"
        c = checks(a)["G21"]
        self.assertEqual(c["status"], "FAIL")
        self.assertIn("'CONFIRMED'", c["msg"])
        for b in ("INFERRED", "OBSERVED", "REPORTED", "UNKNOWN"):
            self.assertIn(b, c["msg"])


# --------------------------------------------------------------------------- 2. table evidence
EV_TABLE = {"type": "table", "span": 12, "title": "Where each claim comes from",
            "columns": ["Claim", "Notes", "Evidence"],
            "rows": [["Reviews", "see E-NOT-AN-ID", "V-E011, V-E012"], ["Site", "", "V-E032 V-E033"],
                     ["Video", "", ["V-E025"]]]}


class TableEvidenceTests(unittest.TestCase):
    def test_refs_in_reads_the_evidence_column_and_only_it(self):
        self.assertEqual(M.refs_in({"blocks": [EV_TABLE]}), ["V-E011", "V-E012", "V-E032", "V-E033", "V-E025"])

    def test_only_id_shaped_tokens_are_citations(self):
        cases = {"V-E001 (A5)": (["V-E001"], "(A5)"), "see V-E001": (["V-E001"], "see"), "n/a": ([], "n/a"),
                 "V-E001; V-E002": (["V-E001", "V-E002"], ""), "V-E001.": (["V-E001"], ""), "3": ([], "3"),
                 "C-SPELL": (["C-SPELL"], "")}
        for cell, want in cases.items():
            self.assertEqual(M.split_cell(cell), want, cell)
        self.assertEqual(M.split_cell(["V-E001", None]), (["V-E001"], ""))
        self.assertEqual(M.split_cell(None), ([], ""))
        a = copy.deepcopy(AUDIT)                             # none of these is a dangling ref any more
        t = next(b for b in page(a, 3)["blocks"] if b["type"] == "table")
        for r, cell in zip(t["rows"], ("V-E001 (A5)", "see V-E001", "n/a", "V-E001.")):
            r[-1] = cell
        self.assertEqual(checks(a)["G10"]["status"], "PASS")

    def test_the_footer_lists_the_pages_evidence_fields_not_its_table_cells(self):
        doc, ctx = render.build_html(copy.deepcopy(AUDIT), LEDGER, DEMO)
        sec = doc[doc.index('data-n="4"'):]
        sec = sec[:sec.index("</section>")]
        foot = sec[sec.index('class="foot"'):]
        self.assertIn("V-A01", sec[:sec.index('class="foot"')])         # a chip in the namesake table
        self.assertNotIn("V-A01", foot)

    def test_a_dash_in_an_evidence_column_is_an_empty_cell_not_a_citation(self):
        t = {"type": "table", "columns": ["Claim", "Evidence"],
             "rows": [["Reviews", "-"], ["Site", "—"], ["Video", None], ["Talk", "V-E025, -"]]}
        self.assertEqual(M.refs_in({"blocks": [t]}), ["V-E025"])
        html = components.table(t, types.SimpleNamespace(ledger=LEDGER))
        self.assertEqual(re.findall(r'class="ev"[^>]*>([^<]+)<', html), ["V-E025"])
        self.assertIn("—", html)                             # the dash is still printed, as text

    def test_the_renderer_draws_exactly_the_ids_the_checks_count(self):
        html = components.table(EV_TABLE, types.SimpleNamespace(ledger=LEDGER))
        drawn = re.findall(r'class="ev"[^>]*>([^<]+)<', html)
        self.assertEqual(drawn, M.table_refs(EV_TABLE))

    def test_a_page_citing_only_in_its_tables_passes_the_pages_check(self):
        p = {"n": 3, "type": "goal", "kicker": "Goal", "headline": "Five checked claims carry the whole goal page",
             "dek": "Read the table.", "blocks": [
                 {"type": "bars", "span": 12, "title": "Reviews", "items": [{"label": "Google", "value": 386}]},
                 EV_TABLE]}
        probs = pipeline.check_pages({"pages": [p]}, LEDGER, 3, 3)
        self.assertFalse([x for x in probs if "evidence ids" in x], probs)

    def test_a_made_up_id_in_a_table_cell_trips_G10_and_says_where(self):
        a = copy.deepcopy(AUDIT)
        t = next(b for b in page(a, 16)["blocks"] if b["type"] == "table")
        t["rows"][0][-1] = "V-E999"
        c = checks(a)["G10"]
        self.assertEqual(c["status"], "FAIL")
        self.assertIn("V-E999", c["msg"])
        self.assertIn("page 16", c["msg"])

    def test_a_namesake_in_a_table_cell_trips_G11_and_says_where(self):
        a = copy.deepcopy(AUDIT)
        t = next(b for b in page(a, 3)["blocks"] if b["type"] == "table")
        t["rows"][0][-1] = "V-A01"
        c = checks(a)["G11"]
        self.assertEqual(c["status"], "FAIL")
        self.assertIn("page 3", c["msg"])

    def test_the_identity_page_listing_a_namesake_does_not_license_it_elsewhere(self):
        # the demo's identity page lists V-A01 in its namesake table; a page-2 card or an action
        # citing it is still a namesake used as proof
        for cite in (lambda a: page(a, 2)["blocks"][0]["items"][0]["evidence"].append("V-A01"),
                     lambda a: a["actions"][0]["evidence"].append("V-A01")):
            a = copy.deepcopy(AUDIT)
            self.assertIn("V-A01", M.refs_in(page(a, 4)))
            cite(a)
            self.assertEqual(checks(a)["G11"]["status"], "FAIL")

    def test_an_exam_row_may_cite_a_namesake_to_explain_its_score_but_page_6_may_not(self):
        a = copy.deepcopy(AUDIT)
        a["exams"]["brand_authority"]["rows"][-1].setdefault("evidence", []).append("V-A01")
        self.assertEqual(checks(a)["G11"]["status"], "PASS")
        b = copy.deepcopy(AUDIT)
        next(x for x in page(b, 6)["blocks"] if isinstance(x.get("evidence"), list))["evidence"].append("V-A01")
        self.assertEqual(checks(b)["G11"]["status"], "FAIL")

    def test_ids_joined_by_a_slash_or_listed_in_one_item_are_each_read(self):
        self.assertEqual(M.split_cell("V-E001/V-E002"), (["V-E001", "V-E002"], ""))
        self.assertEqual(M.split_cell(["V-E001 V-E002", None]), (["V-E001", "V-E002"], ""))
        self.assertEqual(M.split_cell(["V-E001; see V-E003"]), (["V-E001", "V-E003"], "see"))
        self.assertEqual(M.split_cell("n/a"), ([], "n/a"))              # a slash between words stays a word

    def test_a_ledger_id_no_table_can_cite_holds_the_run_before_any_call(self):
        calls = []

        def fake(stage, model, system, user):
            calls.append(stage)
            return "{}"
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            run_dir(d, copy.deepcopy(split_fixture(AUDIT)))
            for name in ("identity", "score", "synthesis", "pages", "actions"):
                (d / f"{name}.json").unlink()                        # a fresh run: every stage still to write
            data = json.loads((DEMO / "ledger.json").read_text())
            data["items"][0]["id"] = "VE001"                         # E012-style: tables would print it as a word
            (d / "ledger.json").write_text(json.dumps(data))
            res = pipeline.run(d, "standard", fake=fake, render_pdf=False)
        self.assertEqual(res["verdict"], "HOLD at ledger", res)
        self.assertIn("VE001", res["hold_reason"])
        self.assertEqual(calls, [])                                   # nothing was paid for
        self.assertEqual(M.off_shape(["V-E001", "E-12", "E012", "e-12", "V_E012", ""]), ["E012", "V_E012", "e-12"])

    def test_a_capture_date_the_bundle_cannot_read_holds_the_run_before_any_call(self):
        # The pilot's person ledger said "2026-10-07 (spot re-checks to 2026-10-23)". Every stage ran
        # and was paid for; then factory20 bundle refused the finished run for want of one date.
        calls = []

        def fake(stage, model, system, user):
            calls.append(stage)
            return "{}"
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            run_dir(d, copy.deepcopy(split_fixture(AUDIT)))
            for name in ("identity", "score", "synthesis", "pages", "actions"):
                (d / f"{name}.json").unlink()
            data = json.loads((DEMO / "ledger.json").read_text())
            data["capture_date"] = "2026-10-07 (spot re-checks to 2026-10-23)"
            (d / "ledger.json").write_text(json.dumps(data))
            res = pipeline.run(d, "standard", fake=fake, render_pdf=False)
        self.assertEqual(res["verdict"], "HOLD at ledger", res)
        self.assertIn("spot re-checks", res["hold_reason"])
        self.assertEqual(calls, [])                                   # nothing was paid for
        from factory20 import bundle                                  # one rule, two callers
        for v, ok in (("2026-10-07", True), ("2026-02-30", False), ("2026-10-07 (spot re-checks to 2026-10-23)", False),
                      ("10/07/2026", False), ("", False), (None, False)):
            self.assertEqual(bool(M.iso_day(v)), ok, v)
            self.assertEqual(bundle._iso_date(v), M.iso_day(v), v)

    def test_the_demo_still_clears_G10_and_G11(self):
        c = checks(copy.deepcopy(AUDIT))
        self.assertEqual((c["G10"]["status"], c["G11"]["status"]), ("PASS", "PASS"))


# --------------------------------------------------------------------------- 3. overflow advice
PLAN = {"n": 18, "type": "plan", "blocks": [
    {"type": "swimlane", "auto": True, "span": 12, "title": "Who does what, when"},
    {"type": "timeline", "span": 12, "events": [{"date": "2026-11-03", "label": "Day 7: answers in"}]},
    {"type": "table", "span": 12, "title": "Days 1-30", "columns": ["Days", "Action"],
     "rows": [["1-3", "Answer on brands, title and fact sheet; grant read access"]] * 6}]}


class OverflowAdviceTests(unittest.TestCase):
    def test_renderer_blocks_are_named_as_fixed_and_never_offered_as_cuts(self):
        d = render._overflow_detail(PLAN, {"over": 110, "h": 900, "kids": [351, 206, 219], "own": [351, 206, 219]})
        self.assertEqual(d["fixed"], ["swimlane (351px)"])
        self.assertTrue(d["tallest"][0].startswith("block 2 table (219px"), d)   # numbered as the writer sees it
        self.assertTrue(d["tallest"][1].startswith("block 1 timeline (206px"), d)
        self.assertNotIn("swimlane", " ".join(d["tallest"]))
        self.assertEqual(d["over_px"], 110)

    def test_blocks_side_by_side_are_measured_at_their_own_height(self):
        pg = {"n": 5, "type": "exams", "blocks": [
            {"type": "bars", "span": 6, "items": [{"label": "Row", "value": 3}]},
            {"type": "callout", "span": 6, "title": "What it does not mean", "body": "Short."}]}
        d = render._overflow_detail(pg, {"over": 40, "h": 900, "kids": [353, 353], "own": [353, 180]})
        self.assertTrue(d["tallest"][0].startswith("block 1 bars (353px"), d)
        self.assertTrue(d["tallest"][1].startswith("block 2 callout (180px"), d)

    def test_the_words_to_cut_never_exceed_the_writers_own(self):
        mine = sum(M.words(M.text_of(b)) for b in PLAN["blocks"][1:])
        small = render._overflow_detail(PLAN, {"over": 20, "h": 900, "own": [351, 206, 219]})["cut_words"]
        big = render._overflow_detail(PLAN, {"over": 200, "h": 900, "own": [351, 206, 219]})["cut_words"]
        self.assertTrue(0 < small < big <= mine, (small, big, mine))
        # renderer blocks side by side are one row of fixed space, not the sum of their heights
        p20 = {"n": 20, "type": "receipt", "blocks": [
            {"type": "bars", "auto": True, "span": 6}, {"type": "table", "auto": True, "span": 6},
            {"type": "prose", "span": 12, "text": " ".join(["word"] * 120)}]}
        d = render._overflow_detail(p20, {"over": 20, "h": 900, "own": [400, 420, 160]})
        self.assertLessEqual(d["cut_words"], 120)

    def test_no_writer_is_told_to_cut_a_page_the_renderer_builds_alone(self):
        p20 = {"n": 20, "type": "receipt", "blocks": [{"type": "bars", "auto": True, "span": 6},
                                                     {"type": "table", "auto": True, "span": 6}]}
        d = render._overflow_detail(p20, {"over": 15, "h": 900, "own": [400, 420]})
        self.assertEqual((d["cut_words"], d["tallest"], d["options"]), (0, [], []))
        rep = gates.gate_render({"pdf_pages": 20, "overflow_pages": [20], "overflow_detail": {"20": d}, "fill": {},
                                 "links": 500, "qr_decoded": render.INSTALL_URL}, render.INSTALL_URL)
        msg = next(c for c in rep.checks if c["id"] == "R02")["msg"]
        self.assertIn("no page writer can make room on it", msg)
        self.assertNotIn("your tallest", msg)

    def test_the_advice_never_offers_to_drop_the_findings_or_the_only_visual(self):
        p2 = page(render.expand(AUDIT, LEDGER), 2)
        d = render._overflow_detail(p2, {"over": 30, "h": 900, "own": [900] * len(p2["blocks"])})
        self.assertFalse([o for o in d["options"] if o.startswith("drop ")], d["options"])
        pg = {"n": 13, "type": "content_factory", "blocks": [
            {"type": "timeline", "span": 12, "events": []},
            {"type": "table", "span": 12, "columns": ["a"], "rows": [["x"]] * 20}]}
        d = render._overflow_detail(pg, {"over": 30, "h": 900, "own": [200, 700]})
        self.assertFalse([o for o in d["options"] if "timeline" in o], d["options"])

    def test_the_advice_names_a_move_that_clears_it_for_certain(self):
        d = render._overflow_detail(PLAN, {"over": 16, "h": 900, "own": [351, 206, 219]})
        self.assertEqual(d["options"][0], "drop block 1 timeline (206px) or move it to a later page")
        self.assertEqual(d["options"][1], "cut 1 row from block 2 table (about 32px a row)")
        d = render._overflow_detail(PLAN, {"over": 110, "h": 900, "own": [351, 206, 219]})
        self.assertIn("cut 4 rows from block 2 table (about 32px a row)", d["options"])
        d = render._overflow_detail(PLAN, {"over": 400, "h": 900, "own": [351, 206, 219]})
        self.assertEqual(d["options"], [])                       # nothing alone clears 400px; say so by silence

    def test_a_block_beside_a_taller_one_is_never_offered_as_the_cut(self):
        # dropping a callout that shares a row with a taller chart frees nothing; the first
        # version of the advice offered exactly that, and a writer dropped the callout for nothing
        pg = {"n": 5, "type": "exams", "blocks": [
            {"type": "heatmap", "auto": True, "span": 12}, {"type": "scorebar", "auto": True, "span": 12},
            {"type": "bars", "span": 6, "items": [{"label": "Row", "value": 3}]},
            {"type": "callout", "span": 6, "title": "What moves the number", "body": "Two rows."}]}
        d = render._overflow_detail(pg, {"over": 92, "h": 900, "own": [295, 161, 353, 180]})
        self.assertEqual(d["options"], ["drop block 1 bars (353px) or move it to a later page"])
        d = render._overflow_detail(pg, {"over": 200, "h": 900, "own": [295, 161, 353, 180]})
        self.assertEqual(d["options"], [])                     # 353 - 180 = 173 is not enough

    def test_R02_tells_the_writer_what_it_cannot_change(self):
        d = render._overflow_detail(PLAN, {"over": 110, "h": 900, "own": [351, 206, 219]})
        rep = gates.gate_render({"pdf_pages": 20, "overflow_pages": [18], "overflow_detail": {"18": d}, "fill": {},
                                 "links": 500, "qr_decoded": render.INSTALL_URL}, render.INSTALL_URL)
        msg = next(c for c in rep.checks if c["id"] == "R02")["msg"]
        self.assertIn("page 18 runs 12% (110px)", msg)
        # the sure move leads; cutting words, which a one-line table row cannot use, comes after
        self.assertIn("past the page. Either of these clears it for certain: drop block 1 timeline (206px) or "
                      "move it to a later page; or cut 4 rows from block 2 table (about 32px a row). Otherwise cut "
                      "about", msg)
        self.assertLess(msg.index("drop block 1"), msg.index("words from your own blocks"))
        self.assertIn("your tallest: block 2 table", msg)
        self.assertIn("cannot change it: swimlane (351px)", msg)

    def test_every_block_the_renderer_adds_is_marked(self):
        full = render.expand(AUDIT, LEDGER)
        added = []
        for p in full["pages"]:
            written = {json.dumps(b, sort_keys=True) for b in page(AUDIT, p["n"])["blocks"]}
            added += [b for b in p["blocks"] if json.dumps(b, sort_keys=True) not in written]
        self.assertTrue({"heatmap", "swimlane", "qr"} <= {b["type"] for b in added}, [b["type"] for b in added])
        self.assertTrue(all(b.get("auto") for b in added), [b["type"] for b in added if not b.get("auto")])

    def test_the_code_built_receipt_page_keeps_its_slack(self):
        # page 20 has no writer to make room on it; its five-facts table now packs like the crosswalk
        p20 = page(render.expand(AUDIT, LEDGER), 20)
        facts = next(b for b in p20["blocks"] if b.get("title", "").startswith("The five facts"))
        self.assertTrue(facts.get("compact"))

    def test_a_photo_without_a_span_shares_its_row_as_in_the_browser(self):
        blocks = [{"type": "photo", "src": "x.png"}, {"type": "prose", "span": 8, "body": "w " * 120},
                  {"type": "bars", "span": 12, "items": []}]
        self.assertEqual(render._grid_rows(blocks), [[0, 1], [2]])
        self.assertEqual([components.span_of(b) for b in blocks], [4, 8, 12])
        self.assertIn("grid-column: span 4", components.photo(blocks[0], types.SimpleNamespace(
            asset_ok=lambda s: False, missing_assets=[], asset_url=lambda s: s)))
        det = render._overflow_detail({"n": 9, "blocks": blocks}, {"over": 30, "h": 800, "own": [150, 400, 300]})
        self.assertFalse(any("photo" in o for o in det["options"]), det)   # it sits beside the 400px prose

    @unittest.skipUnless(have_browser(), "needs Playwright + Chromium")
    def test_the_browser_measures_each_blocks_own_height_then_puts_its_style_back(self):
        from playwright.sync_api import sync_playwright
        html = ('<section class="page" data-n="9"><div class="body" style="display:grid;'
                'grid-template-columns:repeat(12,1fr);height:300px;overflow:hidden">'
                '<div style="grid-column:span 6;height:200px">tall</div>'
                '<div style="grid-column:span 6"><p style="margin:0;height:40px">short</p></div>'
                '<div style="grid-column:span 12;height:180px">next row</div></div></section>')
        with sync_playwright() as p:
            b = render.launch_chromium(p) if hasattr(render, "launch_chromium") else p.chromium.launch()
            try:
                pg = b.new_page()
                pg.set_content(html)
                m = pg.evaluate(render.MEASURE_JS)[0]
                left = pg.evaluate("() => [...document.querySelectorAll('.body > *')].map(c => c.style.alignSelf)")
            finally:
                b.close()
        self.assertEqual(m["kids"][:2], [200, 200])            # the row stretches the short block
        self.assertEqual(m["own"][:2], [200, 40])              # its own height is what dropping it frees
        self.assertTrue(m["overflow"] and m["over"] > 0, m)
        self.assertEqual(left, ["", "", ""])                   # nothing measured is left on the page

    @unittest.skipUnless(have_browser(), "needs Playwright + Chromium")
    def test_a_real_render_reports_the_plan_swimlane_as_fixed(self):
        a = copy.deepcopy(AUDIT)
        p18 = page(a, 18)
        p18["blocks"].append({"type": "table", "span": 12, "title": "More rows than the page holds",
                              "columns": ["Days", "Owner", "Action", "Done when"],
                              "rows": [[f"{i}-{i + 2}", "Agents", "Draft and stage one more page of the rebuild "
                                        "with its proof and its owner", "Staging link sent"] for i in range(1, 40, 3)]})
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            shutil.copytree(DEMO / "assets", d / "assets")
            (d / "audit.json").write_text(json.dumps(a))
            rr = render.render(d / "audit.json", DEMO / "ledger.json", d / "audit.pdf")
        self.assertIn(18, rr["overflow_pages"])
        det = rr["overflow_detail"]["18"]
        self.assertTrue(det["fixed"] and det["fixed"][0].startswith("swimlane ("), det)
        self.assertNotIn("swimlane", " ".join(det["tallest"]))


# --------------------------------------------------------------------------- 4. the register
def with_password(a: dict, aid: str = "A5") -> dict:
    act = next(x for x in a["actions"] if x["id"] == aid)
    act["action"] += " and move the shared password out of the thread"
    return a


class RegisterFixTests(unittest.TestCase):
    def test_G72_says_the_word_is_in_the_register(self):
        c = checks(with_password(copy.deepcopy(AUDIT)))["G72"]
        self.assertEqual(c["status"], "FAIL")
        self.assertIn("action register A5", c["msg"])

    def test_register_items_go_to_the_actions_writer_not_the_page_writer(self):
        only_register = {"from": "gate", "id": "G72", "status": "FAIL", "msg": "remove ['password'] (found on action register A5)"}
        window = {"from": "gate", "id": "G64", "status": "WARN", "msg": "windows present ['30', '7']"}
        both = {"from": "gate", "id": "G72", "status": "FAIL", "msg": "remove ['password'] (found on page 7; action register A5)"}
        page2 = {"from": "gate", "id": "G70", "status": "FAIL", "msg": "remove ['x@y.com'] (found on page 2)"}
        for it in (only_register, window):
            self.assertEqual((pipeline._front(it), pipeline._back(it), pipeline._acts(it)), (False, False, True), it)
        self.assertEqual((pipeline._back(both), pipeline._acts(both)), (True, True))
        self.assertEqual((pipeline._front(page2), pipeline._back(page2), pipeline._acts(page2)), (True, False, False))
        review = {"from": "review", "id": "R1-03", "status": "FAIL", "page": None, "where": "register, A9",
                  "msg": "A9 has no observable test. Fix: name the URL."}
        self.assertTrue(pipeline._acts(review))

    def test_a_do_not_print_hit_in_the_register_goes_to_the_actions_writer(self):
        a = copy.deepcopy(AUDIT)
        a["actions"][4]["action"] += " for Project Bluebird"
        rep = gates.gate_audit(render.expand(a, LEDGER), LEDGER, "standard", do_not_print=["Project Bluebird"])
        c = next(x for x in rep.checks if x["id"] == "G74")
        self.assertIn("in the action register", c["msg"])
        item = {"from": "gate", "id": "G74", "status": "FAIL", "msg": c["msg"]}
        self.assertEqual((pipeline._back(item), pipeline._acts(item)), (False, True))

    def test_review_findings_reach_the_register_by_where_not_by_a_word(self):
        def it(page, where, msg):
            return {"from": "review", "id": "R1-01", "status": "FAIL", "page": page, "where": where, "msg": msg}
        verb = it(None, "exam row 4", "She should register with the BBB. Fix: lower row 4 to 2.")
        on_page = it(7, "table 2", "Says to register the domain. Fix: say renew.")
        by_id = it(None, "A8", "A8 has no approval gate. Fix: make it AGENT_AFTER_APPROVAL.")
        named = it(None, "actions", "Two actions repeat each other. Fix: merge them.")
        # an exam row's reason lives in score.json: its writer gets the finding, not the page writer (15)
        self.assertEqual((pipeline._back(verb), pipeline._acts(verb), pipeline._score(verb)), (False, False, True))
        self.assertEqual((pipeline._back(on_page), pipeline._acts(on_page)), (True, False))
        for x in (by_id, named):
            self.assertEqual((pipeline._back(x), pipeline._acts(x)), (False, True), x["where"])

    def test_a_register_FAIL_is_cleared_by_revising_the_register(self):
        outs = copy.deepcopy(split_fixture(AUDIT))   # split_fixture shares the module-level AUDIT's objects
        good = copy.deepcopy(outs["actions"])
        outs["actions"] = with_password({"actions": copy.deepcopy(good["actions"])})
        base = fake_from_fixture(str(DEMO / "audit.json"))
        seen = []

        def fake(stage, model, system, user):
            seen.append(stage)
            if stage == "actions" and '"fix_list"' in user:
                self.assertIn("G72", user)
                self.assertIn('"current_actions"', user)            # the writer sees the register it revises
                return json.dumps(good)
            return base(stage, model, system, user)
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            run_dir(d, outs)
            res = pipeline.run(d, "standard", fake=fake, render_pdf=False)
            self.assertNotIn("password", (d / "actions.json").read_text())
        self.assertEqual(res["verdict"], "READY", res)
        self.assertEqual(res["fix_rounds"], 1, res)
        self.assertNotIn("fix", seen)                                # nothing on the pages to patch

    def test_a_revised_register_keeps_every_action_id(self):
        outs = copy.deepcopy(split_fixture(AUDIT))   # split_fixture shares the module-level AUDIT's objects
        cur = outs["actions"]
        fewer = {"actions": [x for x in cur["actions"] if x["id"] != "A13"]}   # A13 is printed only as table text
        self.assertEqual(pipeline._kept_action_ids(fewer, cur),
                         ["keep action A13: every id stays, because pages and to-dos already print it"])
        more = {"actions": cur["actions"] + [dict(cur["actions"][0], id="A99")]}
        self.assertEqual(pipeline._kept_action_ids(more, cur), [])


class QuietRoundTests(unittest.TestCase):
    def test_an_empty_fix_answer_is_an_answer(self):
        self.assertEqual(pipeline.check_fix({"pages": []}, LEDGER), [])
        self.assertTrue(pipeline.check_fix({"note": "nothing"}, LEDGER))

    def test_but_not_when_a_FAIL_names_a_page_the_writer_owns(self):
        probs = pipeline.check_fix({"pages": []}, LEDGER, frozenset({12, 18}))
        self.assertEqual(len(probs), 1)
        self.assertIn("FAIL on page 12, 18", probs[0])
        good = copy.deepcopy(page(AUDIT, 12))
        self.assertEqual(pipeline.check_fix({"pages": [good]}, LEDGER, frozenset({12, 18})), [])   # partial is fine

    def test_an_empty_answer_to_a_page_FAIL_is_asked_again_inside_the_stage(self):
        outs = copy.deepcopy(split_fixture(AUDIT))   # split_fixture shares the module-level AUDIT's objects
        good12 = copy.deepcopy(next(p for p in outs["pages"]["pages"] if p["n"] == 12))
        p12 = next(p for p in outs["pages"]["pages"] if p["n"] == 12)
        p12["blocks"] = [b for b in p12["blocks"] if b["type"] not in M.VISUAL_BLOCKS]   # G40 on page 12
        base = fake_from_fixture(str(DEMO / "audit.json"))
        calls = []

        def fake(stage, model, system, user):
            if stage == "fix":
                calls.append((model, user))
                return json.dumps({"pages": [] if len(calls) == 1 else [good12]})
            return base(stage, model, system, user)
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            run_dir(d, outs)
            res = pipeline.run(d, "standard", fake=fake, render_pdf=False)
        self.assertEqual(len(calls), 2, res)
        self.assertEqual(calls[0][0], calls[1][0])            # the same model, told why, not a bigger one
        self.assertIn("FAIL on page 12", calls[1][1])
        self.assertEqual((res["fix_rounds"], res["verdict"]), (1, "READY"), res)

    def test_warnings_a_round_already_had_get_no_round_of_their_own(self):
        outs = copy.deepcopy(split_fixture(AUDIT))   # split_fixture shares the module-level AUDIT's objects
        good12 = copy.deepcopy(next(p for p in outs["pages"]["pages"] if p["n"] == 12))
        p12 = next(p for p in outs["pages"]["pages"] if p["n"] == 12)
        p12["blocks"] = [b for b in p12["blocks"] if b["type"] not in M.VISUAL_BLOCKS]   # G40, a FAIL
        base = fake_from_fixture(str(DEMO / "audit.json"))
        calls = []

        def fake(stage, model, system, user):
            if stage == "fix":
                calls.append(user)
                return json.dumps({"pages": [good12]})
            return base(stage, model, system, user)
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            run_dir(d, outs)
            data = json.loads((DEMO / "ledger.json").read_text())
            for row in data["items"][:45]:
                row["source_url"] = ""                       # G12 warns from the start: a ledger matter
            (d / "ledger.json").write_text(json.dumps(data))
            res = pipeline.run(d, "standard", fake=fake, render_pdf=False)
        self.assertEqual(len(calls), 1, res)                 # round 1 clears G40; G12 alone gets no round 2
        self.assertIn("G12", calls[0])
        self.assertEqual((res["fix_rounds"], res["gate"]), (1, "FIX"), res)


# --------------------------------------------------------------------------- 5. one rung up, once
class EscalationTests(unittest.TestCase):
    def _broken(self):
        outs = copy.deepcopy(split_fixture(AUDIT))   # split_fixture shares the module-level AUDIT's objects
        good12 = copy.deepcopy(next(p for p in outs["pages"]["pages"] if p["n"] == 12))
        p12 = next(p for p in outs["pages"]["pages"] if p["n"] == 12)
        p12["blocks"] = [b for b in p12["blocks"] if b["type"] not in M.VISUAL_BLOCKS]   # G40, a hard FAIL
        return outs, good12, copy.deepcopy(p12)

    def _run(self, answer_up: bool):
        outs, good12, bad12 = self._broken()
        cfg = cost.load_routing()
        cheap = cfg["tiers"]["standard"]["models"]["fix"]
        up = router.next_rung(cfg, cheap, "standard")
        base = fake_from_fixture(str(DEMO / "audit.json"))
        fix_models = []

        def fake(stage, model, system, user):
            if stage == "fix":
                fix_models.append(model)
                return json.dumps({"pages": [good12 if (answer_up and model == up) else bad12]})
            return base(stage, model, system, user)
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            run_dir(d, outs)
            res = pipeline.run(d, "standard", fake=fake, render_pdf=False)
        return res, fix_models, cheap, up

    def test_a_FAIL_the_cheap_writer_cannot_clear_gets_one_round_one_rung_up(self):
        res, fix_models, cheap, up = self._run(answer_up=True)
        self.assertEqual(fix_models, [cheap, up])
        self.assertEqual((res["fix_rounds"], res["fix_escalated_to"], res["verdict"]), (2, up, "READY"), res)

    def test_after_the_rung_up_round_the_loop_goes_back_to_the_tiers_model(self):
        # two hard FAILs: the cheap model clears neither, the next rung clears one, and the round
        # after that is the cheap model again (until Nov 10 review: the higher rung stayed on)
        outs = copy.deepcopy(split_fixture(AUDIT))   # split_fixture shares the module-level AUDIT's objects
        good = {n: copy.deepcopy(next(p for p in outs["pages"]["pages"] if p["n"] == n)) for n in (12, 13)}
        bad12 = dict(good[12], blocks=[b for b in good[12]["blocks"] if b["type"] not in M.VISUAL_BLOCKS])
        bad13 = dict(good[13], headline="Overview")
        outs["pages"]["pages"] = [bad12 if p["n"] == 12 else bad13 if p["n"] == 13 else p for p in outs["pages"]["pages"]]
        cfg = cost.load_routing()
        cheap = cfg["tiers"]["standard"]["models"]["fix"]
        up = router.next_rung(cfg, cheap, "standard")
        base = fake_from_fixture(str(DEMO / "audit.json"))
        models = []

        def fake(stage, model, system, user):
            if stage == "fix":
                models.append(model)
                if model == up:
                    return json.dumps({"pages": [good[12], bad13]})
                if len(models) == 1:
                    return json.dumps({"pages": [bad12, bad13]})
                return json.dumps({"pages": [good[13]]})
            return base(stage, model, system, user)
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            run_dir(d, outs)
            res = pipeline.run(d, "standard", fake=fake, render_pdf=False)
        self.assertEqual(models, [cheap, up, cheap])
        self.assertEqual((res["fix_rounds"], res["verdict"]), (3, "READY"), res)

    def test_a_stuck_front_page_FAIL_takes_the_findings_writer_up_a_rung(self):
        outs = copy.deepcopy(split_fixture(AUDIT))   # split_fixture shares the module-level AUDIT's objects
        good = copy.deepcopy(outs["synthesis"])
        # a word G72 bans, on page 2: the findings writer's revision passes its own stage check
        # (G72 is not one of them), so only the loop can decide to try a bigger model
        outs["synthesis"]["pages"][1]["blocks"][0]["items"][1]["body"] += " Move the shared password."
        bad = copy.deepcopy(outs["synthesis"])
        cfg = cost.load_routing()
        syn = cfg["tiers"]["standard"]["models"]["synthesis"]
        up = router.next_rung(cfg, syn, "standard")
        base = fake_from_fixture(str(DEMO / "audit.json"))
        seen = []

        def fake(stage, model, system, user):
            if stage == "synthesis" and '"fix_list"' in user:
                seen.append(model)
                return json.dumps(good if model == up else bad)
            if stage == "fix":
                seen.append("fix")
            return base(stage, model, system, user)
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            run_dir(d, outs)
            res = pipeline.run(d, "standard", fake=fake, render_pdf=False)
        self.assertEqual(seen, [syn, up])
        self.assertEqual((res["fix_rounds"], res["fix_escalated"], res["verdict"]), (2, {"synthesis": up}, "READY"), res)

    def test_the_rung_up_round_happens_once(self):
        res, fix_models, cheap, up = self._run(answer_up=False)
        self.assertEqual(fix_models, [cheap, up])
        self.assertEqual((res["fix_rounds"], res["verdict"]), (2, "HOLD"), res)

    def test_an_overflow_only_on_the_code_built_page_buys_no_writer_and_no_rung_up(self):
        on20 = {"from": "render", "id": "R02", "status": "FAIL",
                "msg": "page 20 runs 2% (15px) past the page — every block on it is drawn by the renderer "
                       "(table (230px)), so no page writer can make room on it"}
        self.assertEqual((pipeline._front(on20), pipeline._back(on20), pipeline._acts(on20)), (False, False, False))
        both = dict(on20, msg="page 18 runs 5% (40px) past the page — cut about 30 words; page 20 runs 2% (15px) past the page")
        self.assertTrue(pipeline._back(both))
        outs = copy.deepcopy(split_fixture(AUDIT))   # split_fixture shares the module-level AUDIT's objects
        base = fake_from_fixture(str(DEMO / "audit.json"))
        real, seen = pipeline._check_all, []

        def check_all(run_dir_, ledger, tier, render_pdf):
            audit, rep, _ = real(run_dir_, ledger, tier, False)
            return audit, rep, {"gates": {"verdict": "HOLD", "checks": [dict(on20, name="No page overflows", hard=True)]}}

        def fake(stage, model, system, user):
            if '"fix_list"' in user:
                seen.append((stage, model))
            return base(stage, model, system, user)
        with tempfile.TemporaryDirectory() as d, mock.patch.object(pipeline, "_check_all", check_all):
            d = pathlib.Path(d)
            run_dir(d, outs)
            res = pipeline.run(d, "standard", fake=fake, render_pdf=True)
        self.assertEqual(seen, [])                             # no writer was asked, and none paid for
        self.assertNotIn("fix_escalated", res)
        self.assertEqual(res["verdict"], "HOLD", res)


# --------------------------------------------------------------------------- 10. images that exist
class ImageTests(unittest.TestCase):
    """All four pilot rebuilds put an invented screenshot path on the cover: the cards ask for a
    real captured image, no prompt said which files exist, and no gate looked, so each PDF
    printed an IMAGE NEEDED box on page 1 and passed."""

    def test_the_page_writers_are_told_which_image_files_exist(self):
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            run_dir(d, copy.deepcopy(split_fixture(AUDIT)))
            shutil.copy(DEMO / "assets" / "mock-gbp.png", d / "assets" / "preparer.png")
            brief = json.loads((d / "brief.json").read_text())
            brief["prepared_by"] = dict(brief["prepared_by"], photo="assets/preparer.png")
            (d / "brief.json").write_text(json.dumps(brief))
            for stage in ("synthesis", "pages", "fix"):
                p = pipeline.prompt(stage, d, LEDGER)
                self.assertIn('# ASSETS', p)
                self.assertIn('["assets/mock-gbp.png"]', p)          # the byline photo is not evidence
            for stage in ("identity", "score", "actions"):
                self.assertNotIn("# ASSETS", pipeline.prompt(stage, d, LEDGER))

    def test_an_invented_image_holds_the_render_gate_and_goes_to_its_page_writer(self):
        a = render.expand(copy.deepcopy(AUDIT), LEDGER)
        page(a, 1)["blocks"] = [dict(b, src="assets/invented.png") if b.get("type") == "photo" else b
                                for b in page(a, 1)["blocks"]]
        page(a, 9)["blocks"].append({"type": "screenshot", "src": "assets/also-invented.png", "caption": "x"})
        ctx = render.Ctx(a, LEDGER, DEMO)
        gone = render.missing_images(a["pages"], ctx)
        self.assertEqual(gone, [{"page": 1, "src": "assets/invented.png"}, {"page": 9, "src": "assets/also-invented.png"}])
        self.assertEqual(render.assets_available(DEMO, a["meta"]), ["assets/mock-gbp.png"])
        rep = gates.gate_render({"pdf_pages": 20, "overflow_pages": [], "fill": {}, "links": 99,
                                 "missing_images": gone, "assets_available": ["assets/mock-gbp.png"]})
        c = next(x for x in rep.checks if x["id"] == "R06")
        self.assertEqual(c["status"], "FAIL")
        item = {"from": "render", "id": "R06", "status": "FAIL", "msg": c["msg"]}
        self.assertEqual((pipeline._front(item), pipeline._back(item)), (True, True))   # page 1 and page 9
        one = dict(item, msg=c["msg"].split("; ")[0])
        self.assertEqual((pipeline._front(one), pipeline._back(one)), (True, False))     # the cover alone

    @unittest.skipUnless(have_browser(), "needs Playwright + Chromium")
    def test_a_real_render_lists_the_empty_image_by_page(self):
        a = copy.deepcopy(AUDIT)
        page(a, 1)["blocks"] = [dict(b, src="assets/invented.png") if b.get("type") == "photo" else b
                                for b in page(a, 1)["blocks"]]
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            shutil.copytree(DEMO / "assets", d / "assets")
            (d / "audit.json").write_text(json.dumps(a))
            rr = render.render(d / "audit.json", DEMO / "ledger.json", d / "audit.pdf")
        self.assertEqual(rr["missing_images"], [{"page": 1, "src": "assets/invented.png"}])
        self.assertEqual(rr["assets_available"], ["assets/mock-gbp.png"])
        self.assertEqual(next(c for c in gates.gate_render(rr).checks if c["id"] == "R06")["status"], "FAIL")


# --------------------------------------------------------------------------- 12. the scale of a bar chart
class BarsScaleTests(unittest.TestCase):
    """The person lean rebuild drew its ten Brand Authority rows as bars with no max. The renderer
    scales such a chart to its largest value, so three rows scored 4 of 10 printed as full bars,
    and the review called it an S1: the reader overrates his best rows."""

    def _widths(self, b):
        html = components.bars(b, render.Ctx(copy.deepcopy(AUDIT), LEDGER, DEMO))
        return [float(w) for w in re.findall(r'<rect x="[\d.]+" y="[\d.]+" width="([\d.]+)"', html)]

    def test_without_max_the_largest_value_fills_the_row_so_the_card_says_when_to_set_it(self):
        rows = {"type": "bars", "span": 12, "title": "Brand Authority rows",
                "items": [{"label": "Row 1", "value": 4}, {"label": "Row 9", "value": 1}]}
        full, quarter = self._widths(rows)
        self.assertAlmostEqual(quarter / full, 0.25, places=2)          # scaled to the largest value
        out_of_ten = self._widths(dict(rows, max=10))
        self.assertAlmostEqual(out_of_ten[0] / full, 0.4, places=2)    # 4 of 10 is 40% of the row
        card = (router.STAGES_DIR / "60-pages.md").read_text()
        self.assertIn("`max` in bars is the top of the scale", card)
        self.assertIn("a row scored 4 of 10 prints as a full bar", card)


# --------------------------------------------------------------------------- 12. production notes as copy
class ProductionNoteTests(unittest.TestCase):
    """Once the card told writers that pages 5, 17 and 18 get their visual from the renderer, three
    of the four graded replays printed it: "The renderer adds the ten-row heatmap above these
    notes", "The swimlane the renderer adds shows the same windows". The review marked it."""

    def test_a_production_note_in_the_copy_fails_G31_and_reader_words_pass(self):
        a = copy.deepcopy(AUDIT)
        page(a, 5)["dek"] = "The renderer adds the ten-row heatmap above these notes."
        c = checks(a)["G31"]
        self.assertEqual(c["status"], "FAIL")
        self.assertIn("the renderer", c["msg"])
        page(a, 5)["dek"] = "The heatmap above shows each row; these notes say what moves it."
        self.assertEqual(checks(a)["G31"]["status"], "PASS")
        card = (router.STAGES_DIR / "60-pages.md").read_text()
        self.assertIn('never "the renderer adds the heatmap"', card)


# --------------------------------------------------------------------------- 13. a review fix that breaks a gate
class ReviewFixTests(unittest.TestCase):
    """In the person standard replay a fix for the first review's findings ran page 19 40px over.
    The kit went straight on to the second review, paid for it on a draft that could only end
    HOLD, and its result still said render PASS (the verdict from before the review)."""

    S1 = {"verdict": "NOT_READY", "findings": [{"id": "R1-01", "severity": "S1", "page": 12, "where": "cards",
          "problem": "The page states an estimate as a count.", "fix": "Say it is an estimate.",
          "evidence": ["V-E011"]}], "score_adjustments": [], "strongest": ["page 2"]}

    def _run(self, gate_round_clears: bool, render_hold=False):
        from factory20.testing import READY_REVIEW
        outs = copy.deepcopy(split_fixture(AUDIT))
        good12 = copy.deepcopy(next(p for p in outs["pages"]["pages"] if p["n"] == 12))
        broken12 = dict(copy.deepcopy(good12), blocks=[b for b in good12["blocks"] if b["type"] not in M.VISUAL_BLOCKS])
        if render_hold:   # the review fix keeps a visual but runs the page over
            broken12 = dict(copy.deepcopy(good12), dek=good12.get("dek", "") + " (too long)")
        base = fake_from_fixture(str(DEMO / "audit.json"), review=[self.S1, READY_REVIEW])
        calls = []

        def fake(stage, model, system, user):
            calls.append(stage)
            if stage == "fix":
                from_review = '"from": "review"' in user
                return json.dumps({"pages": [good12 if (gate_round_clears and not from_review) else broken12]})
            return base(stage, model, system, user)
        real = pipeline._check_all

        def check_all(run_dir_, ledger, tier, render_pdf):
            audit, rep, _ = real(run_dir_, ledger, tier, False)
            p12 = next(p for p in audit["pages"] if p["n"] == 12)
            over = render_hold and "(too long)" in (p12.get("dek") or "")
            checks = [{"id": "R02", "name": "No page overflows", "hard": True, "status": "FAIL" if over else "PASS",
                       "msg": "page 12 runs 5% (40px) past the page. This clears it for certain: drop block 1" if over else ""}]
            return audit, rep, {"gates": {"verdict": "HOLD" if over else "PASS", "checks": checks}}
        with tempfile.TemporaryDirectory() as d, mock.patch.object(pipeline, "_check_all", check_all):
            d = pathlib.Path(d)
            run_dir(d, outs)
            res = pipeline.run(d, "standard", fake=fake, render_pdf=True)
        return res, calls

    def test_a_review_fix_that_breaks_a_gate_gets_a_gate_round_before_the_next_review(self):
        res, calls = self._run(gate_round_clears=True)
        self.assertEqual(calls.count("fix"), 2, calls)           # the review's fix, then the gate round
        self.assertEqual((res["review_passes"], res["verdict"]), (2, "READY"), res)

    def test_a_draft_that_still_holds_pays_for_no_second_review_and_says_so(self):
        res, calls = self._run(gate_round_clears=False, render_hold=True)
        self.assertEqual(calls.count("review"), 1, calls)        # no review on a draft that must HOLD
        self.assertEqual((res["render"], res["verdict"]), ("HOLD", "HOLD"), res)   # not the PASS from before


class FixOrderTests(unittest.TestCase):
    def test_the_front_pages_are_revised_after_the_pages_they_summarize(self):
        # Nov 10, person standard replay: in one fix round the cover was revised first, against the
        # old page 11 ($21 video test); the page fix then made page 11 a $14 two-post test, and the
        # cover kept $21. The blind grader and the kit's second review both called it an S1.
        outs = copy.deepcopy(split_fixture(AUDIT))
        fixed12 = copy.deepcopy(next(p for p in outs["pages"]["pages"] if p["n"] == 12))
        fixed12["dek"] = "MARKER-FIXED-PAGE-12 " + (fixed12.get("dek") or "")
        base = fake_from_fixture(str(DEMO / "audit.json"))
        order, seen = [], {}

        def fake(stage, model, system, user):
            if '"fix_list"' in user:
                order.append(stage)
                seen[stage] = user
                if stage == "fix":
                    return json.dumps({"pages": [fixed12]})
            return base(stage, model, system, user)
        items = [{"from": "review", "id": "R1-01", "status": "FAIL", "page": 1, "msg": "the cover sizes the test"},
                 {"from": "review", "id": "R1-02", "status": "FAIL", "page": 12, "msg": "page 12 sizes the test"}]
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            run_dir(d, outs)
            pipeline._apply_fixes(d, LEDGER, "standard", cost.load_routing(), fake, items)
        self.assertEqual(order[:2], ["fix", "synthesis"])
        self.assertIn("MARKER-FIXED-PAGE-12", seen["synthesis"])   # the cover's writer sees the new page


class ReceiptCountTests(unittest.TestCase):
    def test_the_receipt_accounts_for_every_ledger_row(self):
        # Both person-subject graders marked page 20's "EVIDENCE LEDGER — 119 ROWS BY CLASS" as
        # unsupported: the ledger has 134 rows, and the chart below the title showed all 134.
        # The chart now shows the rows its title counts, and its caption names the rest, as #121
        # does with the same lines.
        st = LEDGER.stats()
        bars = next(b for b in render._receipt_blocks(copy.deepcopy(AUDIT), LEDGER) if b["type"] == "bars")
        shown = sum(i["value"] for i in bars["items"])
        self.assertIn(f"{shown} rows", bars["title"])
        caption = bars.get("caption", "")
        for kept, n in (("namesake", st["ambiguous"]), ("conflict", st["conflicts"]), ("named unknown", st["unknowns"])):
            self.assertRegex(caption, rf"\b{n} {kept}")
        self.assertEqual(shown + st["ambiguous"] + st["conflicts"] + st["unknowns"], len(LEDGER.rows))


# --------------------------------------------------------------------------- 15. a review finding reaches the writer of its text
class ReviewRoutingTests(unittest.TestCase):
    """The person standard rerun on 229cfc9 (Nov 12) held on two S1s that its first review had
    already found, because each finding reached the wrong writer. Exam rows 4 and 7 gave reasons
    their evidence did not support, but a row's reason lives in score.json, which no fix writer
    could edit; the page fixer, told about "page 5", printed a note about its own page instead ("The
    heatmap above still shows the earlier wording for these two rows until the score source is
    corrected; this note governs"). And "Four pages say we ask each client to 'repeat their words'
    as a review", filed under page 1, reached only the cover's writer, so four pages and
    the action it named kept the ask. Both blind graders marked both as S2; the second review, S1."""

    QUOTE = "104 reviews naming her"          # in exam row 4's reason, on no page

    def _apply(self, items, outs=None, review=None, answers=None):
        outs = outs or copy.deepcopy(split_fixture(AUDIT))   # split_fixture shares the module-level AUDIT's objects
        base = fake_from_fixture(str(DEMO / "audit.json"))
        asked: dict[str, list[str]] = {}

        def fake(stage, model, system, user):
            if '"fix_list"' in user:
                asked.setdefault(stage, []).append(user)
                if answers and stage in answers:
                    return json.dumps(answers[stage])
            return base(stage, model, system, user)
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            run_dir(d, outs)
            pipeline._apply_fixes(d, LEDGER, "standard", cost.load_routing(), fake, items, review=review)
            files = {n: json.loads((d / f"{n}.json").read_text()) for n in ("score", "pages", "synthesis", "actions")}
        return asked, files

    @staticmethod
    def _review(page, msg, status="WARN", where=""):
        return {"from": "review", "id": "R1-01", "status": status, "page": page, "where": where, "msg": msg}

    def test_a_quote_from_an_exam_reason_goes_to_the_score_writer_not_the_page_writer(self):
        outs = copy.deepcopy(split_fixture(AUDIT))
        everywhere_else = json.dumps(outs["pages"]) + json.dumps(outs["synthesis"]) + json.dumps(outs["actions"])
        self.assertNotIn(self.QUOTE, everywhere_else)
        revised = copy.deepcopy(outs["score"])
        row4 = next(r for r in revised["brand_authority"]["rows"] if r["n"] == 4)
        row4["why"] = "386 reviews at 4.9 and BBB A+; the reviews that name her are counted once (V-E013)."
        item = self._review(5, f"Row 4 says '{self.QUOTE}', but V-E013 counts them twice. Fix: count them once.")
        asked, files = self._apply([item], outs, answers={"score": revised})
        self.assertIn("score", asked)            # the writer that owns the reason revises it
        self.assertNotIn("fix", asked)           # nothing on page 5 says it, so the page writer is not asked
        rows = {r["n"]: r for r in files["score"]["brand_authority"]["rows"]}
        self.assertEqual((rows[4]["why"], rows[4]["score"]), (row4["why"], 7))
        self.assertIn("exam row 4", asked["score"][0])   # the writer is told where the quote stands

    def test_the_score_writer_may_rewrite_a_reason_but_never_a_score(self):
        cur = copy.deepcopy(split_fixture(AUDIT))["score"]
        ok = copy.deepcopy(cur)
        ok["brand_authority"]["rows"][3]["why"] = "A plainer reason that cites V-E011."
        self.assertEqual(pipeline.check_score_revision(ok, cur, LEDGER), [])
        bumped = copy.deepcopy(ok)
        bumped["brand_authority"]["rows"][3]["score"] = 9
        self.assertTrue(any("keep the score" in p for p in pipeline.check_score_revision(bumped, cur, LEDGER)))
        made_up = copy.deepcopy(ok)
        made_up["brand_authority"]["rows"][3]["why"] = "Per V-E999."
        self.assertTrue(any("V-E999" in p for p in pipeline.check_score_revision(made_up, cur, LEDGER)))

    ASK = "repeat their words on Google and Facebook"

    def _cover_carries_the_ask(self, on_pages: str):
        outs = copy.deepcopy(split_fixture(AUDIT))
        outs["synthesis"]["pages"][0]["dek"] += f" We ask each client to {self.ASK}."
        for p in outs["pages"]["pages"]:
            if p["n"] in (8, 10):
                p["dek"] += on_pages
        return outs

    def test_a_quote_reaches_every_page_and_action_where_it_stands(self):
        outs = self._cover_carries_the_ask(f" Ask each client to {self.ASK}.")
        item = self._review(1, f"We ask each client to '{self.ASK}', and a review of a service is not a review of "
                               "the book. Fix: Ask for recommendations; align A4's action text.", "FAIL")
        asked, _ = self._apply([item], outs)
        self.assertEqual(sorted(asked), ["actions", "fix", "synthesis"])
        self.assertIn("pages [8, 10]", asked["fix"][0])  # the page writer is told where the words stand

    def test_a_finding_over_pages_it_does_not_number_reaches_the_page_writer_where_they_paraphrase(self):
        outs = self._cover_carries_the_ask(" Clients echo their words on Google and Facebook.")
        item = self._review(1, f"Four pages say we ask each client to '{self.ASK}'. Fix: One wording everywhere.",
                            "FAIL")
        asked, _ = self._apply([item], outs)
        self.assertIn("synthesis", asked)
        self.assertIn("fix every page 3-19 that carries it", asked["fix"][0])

    def test_the_pages_a_findings_where_lists_reach_the_page_writer(self):
        # review 1 filed the S1 under page 1 and listed the rest in where; until Nov 12 only the
        # register was read from where
        it = self._review(1, "The cover asks clients for reviews. Fix: ask for recommendations.", "FAIL",
                          where="'If you read only this' callout; p5 'What moves the number'; p10 Trust row; P18 A4 row")
        self.assertEqual(pipeline._pages_named(it), {1, 5, 10, 18})
        self.assertEqual((pipeline._front(it), pipeline._back(it)), (True, True))
        self.assertEqual(pipeline._page_numbers("repetition across pages 1, 2, 3, 5 and 18; Pages [7, 9]; pages 11-13"),
                         {1, 2, 3, 5, 7, 9, 11, 12, 13, 18})

    def test_words_a_page_shares_with_a_rows_reason_are_the_pages_unless_the_row_is_named(self):
        outs = copy.deepcopy(split_fixture(AUDIT))
        next(p for p in outs["pages"]["pages"] if p["n"] == 12)["dek"] += f" She has {self.QUOTE}."
        asked, _ = self._apply([self._review(12, f"The dek says '{self.QUOTE}'. Fix: count them once.")], outs)
        self.assertNotIn("score", asked)
        asked, _ = self._apply([self._review(12, f"Row 4 and page 12 say '{self.QUOTE}'. Fix: count them once.")], outs)
        self.assertEqual(sorted(asked), ["fix", "score"])

    def test_a_short_term_the_audit_uses_throughout_routes_nothing(self):
        # on Nov 12 his name and his title, quoted in three findings, sent each to every writer
        asked, _ = self._apply([self._review(12, "The headline says 'the bare name' as if readers know it. "
                                                 "Fix: say his plain name.")])
        self.assertEqual(sorted(asked), ["fix"])

    def test_quotes_come_from_the_problem_and_an_apostrophe_is_not_a_quote(self):
        msg = ("Row 4 says 'two relationships independently corroborated', but the owner's sources are the hosts' "
               "own pages. Fix: say 'one client appears on an outside organizer page'.")
        self.assertEqual(pipeline._quoted({"msg": msg}), ["two relationships independently corroborated"])
        self.assertEqual(pipeline._quoted({"msg": "Says “no ad of any kind has run” … Fix: soften."}),
                         ["no ad of any kind has run"])

    def test_a_score_adjustment_lands_before_the_page_writer_reads_the_score(self):
        review = {"verdict": "READY_WITH_FIXES", "findings": [], "strongest": [],
                  "score_adjustments": [{"row": 4, "from": 7, "to": 5, "why": "reviews counted twice"}]}
        asked, files = self._apply([self._review(12, "Page 12 calls row 4 strong. Fix: say mixed.", "FAIL")],
                                   review=review)
        decided = re.search(r"# SCORE \(already decided[^\n]*\n(.*?)(?:\n\n# |\Z)", asked["fix"][0], re.S).group(1)
        self.assertEqual(json.loads(decided)["brand_authority"]["rows"][3]["score"], 5)
        self.assertEqual(files["score"]["brand_authority"]["rows"][3]["score"], 5)

    def test_the_page_writer_is_told_a_rows_reason_is_not_on_its_page(self):
        asked, _ = self._apply([self._review(12, "Page 12 is vague. Fix: name the audience.")])
        self.assertIn("never write a note about how the page was made", asked["fix"][0])

    def test_a_note_about_how_the_page_was_made_fails_G31(self):
        a = copy.deepcopy(AUDIT)
        page(a, 5)["dek"] = ("The heatmap above still shows the earlier wording for these two rows until the score "
                             "source is corrected; this note governs.")
        c = checks(a)["G31"]
        self.assertEqual(c["status"], "FAIL")
        self.assertIn("this note governs", c["msg"])
        page(a, 5)["dek"] = "Two rows score 3: the proof is self-published, and the posts draw few reactions."
        self.assertEqual(checks(a)["G31"]["status"], "PASS")


# --------------------------------------------------------------------------- 8. the manual provider
class ManualProviderTests(unittest.TestCase):
    """The muse tier answers pages, actions and fixes through files. Until Nov 10 each stage had
    one answer file, so the action-register revision above (and a retry, page batches 2-4 and a
    second fix round) read back the first answer instead of asking."""

    def _ask(self, d, stage, user, check=lambda o: []):
        with self.assertRaises(router.Pending):
            router.run_stage(stage, user, "muse", d, check=check)

    def test_a_revision_of_the_register_is_asked_not_replayed(self):
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            self._ask(d, "actions", "draft the register")
            [first] = (d / "prompts").glob("actions-*.md")
            (d / "outputs" / f"{first.stem}.json").write_text('{"actions": []}')
            self.assertTrue(router.run_stage("actions", "draft the register", "muse", d, check=lambda o: [])["ok"])
            self._ask(d, "actions", "revise the register: fix_list G72")
            self.assertEqual(len(list((d / "prompts").glob("actions-*.md"))), 2)

    def test_a_retry_with_feedback_is_asked_afresh(self):
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)

            def check(o):
                return [] if o.get("ok") else ["the reply must say ok"]
            self._ask(d, "fix", "clear the list", check)
            [first] = (d / "prompts").glob("fix-*.md")
            (d / "outputs" / f"{first.stem}.json").write_text('{"ok": false}')
            self._ask(d, "fix", "clear the list", check)
            retry = [p for p in (d / "prompts").glob("fix-*.md") if p != first]
            self.assertEqual(len(retry), 1)
            self.assertIn("the reply must say ok", retry[0].read_text())

    def test_a_restart_reuses_its_answers_and_each_page_batch_is_its_own_question(self):
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            self._ask(d, "pages", "write pages 3-6")
            [asked] = (d / "prompts").glob("pages-*.md")
            (d / "outputs" / f"{asked.stem}.json").write_text('{"pages": []}')
            for _ in range(2):
                self.assertTrue(router.run_stage("pages", "write pages 3-6", "muse", d, check=lambda o: [])["ok"])
            self._ask(d, "pages", "write pages 7-10")
            self.assertEqual(len(list((d / "prompts").glob("pages-*.md"))), 2)


if __name__ == "__main__":
    unittest.main()
