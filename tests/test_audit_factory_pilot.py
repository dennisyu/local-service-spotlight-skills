"""Audit Factory 20: what the Nov 10 pilot found (AUDIT-FACTORY-20261104).

The pilot rebuilt two finished audits at the standard and lean tiers, every model call answered
by a fresh model on the stage's tier. These defects kept runs from finishing, or made them pay
for retries and bigger models they did not need. 22 of the 23 tests below fail on the kit as it
was before this change (checked against 0e64f96, the head of #118); the 23rd guards that the
demo audit still clears G10 and G11.

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

    def test_a_namesake_only_in_a_table_trips_G11_and_says_where(self):
        a = copy.deepcopy(AUDIT)
        for n in (4, 19):                                   # take it off the pages that may cite it
            for b in page(a, n)["blocks"]:
                if b.get("type") == "table":
                    for r in b["rows"]:
                        for i in M.evidence_columns(b["columns"]):
                            r[i] = ", ".join(x for x in M.cell_ids(r[i]) if x != "V-A01")
                if isinstance(b.get("evidence"), list) and "V-A01" in b["evidence"]:
                    b["evidence"].remove("V-A01")
        self.assertNotIn("V-A01", M.refs_in(page(a, 4)) + M.refs_in(page(a, 19)))
        t = next(b for b in page(a, 3)["blocks"] if b["type"] == "table")
        t["rows"][0][-1] = "V-A01"
        c = checks(a)["G11"]
        self.assertEqual(c["status"], "FAIL")
        self.assertIn("page 3", c["msg"])

    def test_a_namesake_the_identity_page_introduces_may_explain_a_low_score(self):
        # an exam row may cite the namesake that makes the entity score low; G11 leaves that use to
        # the reviewer, as it always has (a stricter reading held a real rebuild on Nov 10)
        a = copy.deepcopy(AUDIT)
        a["exams"]["brand_authority"]["rows"][-1].setdefault("evidence", []).append("V-A01")
        self.assertEqual(checks(a)["G11"]["status"], "PASS")

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

    def test_the_words_to_cut_come_from_the_writers_blocks_only(self):
        mine = sum(M.words(M.text_of(b)) for b in PLAN["blocks"][1:])
        d = render._overflow_detail(PLAN, {"over": 110, "h": 900, "own": [351, 206, 219]})
        self.assertEqual(d["cut_words"], int(mine * 110 / (900 + 110 - 351) * 1.15) + 10)

    def test_the_advice_names_a_move_that_clears_it_for_certain(self):
        d = render._overflow_detail(PLAN, {"over": 16, "h": 900, "own": [351, 206, 219]})
        self.assertEqual(d["options"][0], "dropping block 1 timeline (206px) alone would clear it")
        self.assertEqual(d["options"][1], "so would cutting 1 row from block 2 table (about 32px a row)")
        d = render._overflow_detail(PLAN, {"over": 110, "h": 900, "own": [351, 206, 219]})
        self.assertIn("so would cutting 4 rows from block 2 table (about 32px a row)", d["options"])
        d = render._overflow_detail(PLAN, {"over": 400, "h": 900, "own": [351, 206, 219]})
        self.assertEqual(d["options"], [])                       # nothing alone clears 400px; say so by silence

    def test_R02_tells_the_writer_what_it_cannot_change(self):
        d = render._overflow_detail(PLAN, {"over": 110, "h": 900, "own": [351, 206, 219]})
        rep = gates.gate_render({"pdf_pages": 20, "overflow_pages": [18], "overflow_detail": {"18": d}, "fill": {},
                                 "links": 500, "qr_decoded": render.INSTALL_URL}, render.INSTALL_URL)
        msg = next(c for c in rep.checks if c["id"] == "R02")["msg"]
        self.assertIn("page 18 runs 12% (110px)", msg)
        self.assertIn("dropping block 1 timeline (206px) alone would clear it", msg)
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

    def test_a_revised_register_must_keep_every_action_a_page_cites(self):
        outs = copy.deepcopy(split_fixture(AUDIT))   # split_fixture shares the module-level AUDIT's objects
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            run_dir(d, outs)
            cited = set(M.action_refs_in(outs["pages"]["pages"] + outs["synthesis"]["pages"]))
            fewer = {"actions": [x for x in outs["actions"]["actions"] if x["id"] != "A1"]}
            self.assertIn("A1", cited)
            self.assertEqual(pipeline._kept_action_ids(fewer, d), ["keep action A1: a page cites it"])
            self.assertEqual(pipeline._kept_action_ids(outs["actions"], d), [])


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

    def test_the_rung_up_round_happens_once(self):
        res, fix_models, cheap, up = self._run(answer_up=False)
        self.assertEqual(fix_models, [cheap, up])
        self.assertEqual((res["fix_rounds"], res["verdict"]), (2, "HOLD"), res)


if __name__ == "__main__":
    unittest.main()
