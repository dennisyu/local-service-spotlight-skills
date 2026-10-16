import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def core(skill: str) -> str:
    text = (ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
    return text.split("<!-- shared-rule:", 1)[0]


class SAEContractsTest(unittest.TestCase):
    def test_marketplace_has_one_gct_screen(self):
        manifest = json.loads(
            (ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
        )
        everything = next(
            plugin for plugin in manifest["plugins"] if plugin["name"] == "lss-everything"
        )["skills"]
        self.assertIn("./skills/gct-screen", everything)
        self.assertNotIn("./skills/gct-qualify-screen", everything)
        self.assertEqual(1, everything.count("./skills/social-amplification-engine"))

    def test_gct_preserves_unknown_and_has_no_numeric_pass_score(self):
        text = core("gct-screen")
        self.assertIn("`UNKNOWN` is not zero", text)
        self.assertIn("`DISCOVERY_REQUIRED`", text)
        self.assertIn("invented weighted score", text)
        self.assertNotIn("Unknown = 0", text)
        self.assertNotIn("total ≥", text)
        self.assertNotIn("70/100", text)

    def test_gct_keeps_gate_outcome_separate_from_evidence_state(self):
        text = core("gct-screen")
        self.assertIn("`UNKNOWN` — the available evidence cannot establish an outcome", text)
        self.assertIn("`MET` — the gate requirement is satisfied", text)
        self.assertIn("`NOT_MET` — the gate requirement is not satisfied", text)
        self.assertIn("`UNKNOWN` — not researched or unavailable", text)
        self.assertIn("`OBSERVED` — present in a source", text)
        self.assertIn("`VERIFIED` — corroborated", text)
        self.assertIn("`CONTRADICTED` — credible sources disagree", text)
        self.assertIn("`EXPIRED` — evidence is too old", text)
        self.assertIn("separate `outcome` and `evidence_state` fields", text)

    def test_gct_verdict_precedence_is_fail_closed(self):
        text = core("gct-screen")
        self.assertIn("If the independent evaluators disagree, return `DISCOVERY_REQUIRED`", text)
        self.assertIn("any gate has `outcome: UNKNOWN`", text)
        self.assertIn("`evidence_state: UNKNOWN`", text)
        self.assertIn("`OBSERVED`, `CONTRADICTED`, or `EXPIRED`", text)
        self.assertIn("`outcome: NOT_MET` with\n   `evidence_state: VERIFIED`", text)
        self.assertIn("Only eight `outcome: MET` plus `evidence_state: VERIFIED` pairs", text)

    def test_gct_receipt_contains_all_eight_two_axis_gates(self):
        text = core("gct-screen")
        self.assertIn("schema_version: 2", text)
        receipt_gate_lines = [
            line.strip()
            for line in text.splitlines()
            if "{outcome: MET, evidence_state: VERIFIED, evidence: []}" in line
        ]
        self.assertEqual(8, len(receipt_gate_lines))
        self.assertTrue(receipt_gate_lines[0].startswith("identity_and_scope:"))

    def test_qualification_does_not_grant_execution(self):
        text = core("gct-screen")
        self.assertIn("QUALIFIED_PENDING_REVIEW", text)
        self.assertIn("accepted scope/agreement receipt", text)
        self.assertIn("Ops roster decision", text)
        self.assertIn("Qualification never authorizes", text)

    def test_sae_reuses_money_tree_and_defaults_stage_only(self):
        text = core("social-amplification-engine")
        self.assertIn("roster-driven Money Tree", text)
        self.assertIn("The default is `STAGE_ONLY`", text)
        self.assertIn("Do not create a second SAE heartbeat", text)
        self.assertIn("one terminal checkpoint for every and", text)
        self.assertIn("only current Active Client row", text)

    def test_sae_carries_the_two_axis_gct_contract(self):
        text = core("social-amplification-engine")
        self.assertIn("### GCT gate outcome", text)
        self.assertIn("`UNKNOWN | MET | NOT_MET`", text)
        self.assertIn(
            "any\nevidence state other than `VERIFIED` routes to `DISCOVERY_REQUIRED`",
            text,
        )
        self.assertIn("a verified `NOT_MET` routes to `DEVELOP`", text)
        self.assertIn("only eight verified `MET` pairs", text)
        self.assertIn("Qualification remains separate from action\nauthority", text)

    def test_shared_gct_standard_carries_verdict_taxonomy(self):
        text = (ROOT / "standards" / "screen-gct-before-amplification.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("`UNKNOWN | MET | NOT_MET`", text)
        self.assertIn("`UNKNOWN | OBSERVED | VERIFIED | CONTRADICTED | EXPIRED`", text)
        self.assertIn("verified `NOT_MET` routes to\n  `DEVELOP`", text)
        self.assertIn("Only eight verified `MET` pairs", text)

    def test_child_skills_preserve_external_action_gate(self):
        content = core("content-factory")
        dad = core("dollar-a-day-strategist")
        video = core("video-repurposing-agent")
        maa = core("weekly-brand-maa")
        self.assertIn("Stage by\n   default", content)
        self.assertIn("does not pause, kill, scale, spend", dad)
        self.assertIn("Default\n  mode is `draft`", video)
        self.assertIn("never route or draft the\n   Basecamp update through Gmail", maa)
        self.assertNotIn("send the Gmail draft fallback", maa)

    def test_no_placeholder_skill_bodies(self):
        for skill in ("gct-screen", "social-amplification-engine"):
            text = core(skill).strip()
            self.assertNotEqual("LOADING", text)
            self.assertGreater(len(text.splitlines()), 80)


if __name__ == "__main__":
    unittest.main()
