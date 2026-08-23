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
        self.assertIn("do not use an invented weighted score", text)
        self.assertNotIn("Unknown = 0", text)
        self.assertNotIn("total ≥", text)
        self.assertNotIn("70/100", text)

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
