"""The rule-not-a-skill gate must catch rules and never block real skills."""

import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "check_skill_vs_rule", ROOT / "scripts" / "check_skill_vs_rule.py"
)
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)


class SkillVsRuleTests(unittest.TestCase):
    def test_self_test_passes(self):
        self.assertEqual(gate.self_test(), 0)

    def test_gate_never_blocks_a_skill_already_in_the_pack(self):
        """A gate that rejects the corpus it guards is a gate somebody disables."""
        blocked = {
            p.parent.name: gate.judge(p, p.read_text(encoding="utf-8"))
            for p in sorted((ROOT / "skills").glob("*/SKILL.md"))
            if gate.judge(p, p.read_text(encoding="utf-8"))
        }
        self.assertEqual(blocked, {}, f"gate blocks shipped skills: {blocked}")

    def test_catches_the_2026_09_04_regression(self):
        """The rule that was proposed as a skill, verbatim. If this passes, the
        gate has stopped doing the one thing it was built for."""
        why = gate.judge(pathlib.Path("x"), gate.THE_ONE_THAT_GOT_THROUGH)
        self.assertTrue(why, "the regression case is no longer caught")
        self.assertIn("calls this a rule", " ".join(why))

    def test_catches_a_prohibition_list_with_no_procedure(self):
        why = gate.judge(pathlib.Path("x"), gate.A_RULE)
        self.assertIn("prohibitions", " ".join(why))

    def test_passes_a_job(self):
        self.assertEqual(gate.judge(pathlib.Path("x"), gate.A_JOB), [])

    def test_advisories_do_not_block(self):
        """Missing a convention is reported, not fatal."""
        text = gate.A_RULE_WITH_STEPS_BUT_NO_DONE
        self.assertEqual(gate.judge(pathlib.Path("x"), text), [])
        self.assertTrue(gate.advisories(pathlib.Path("x"), text))

    def test_shared_rule_blocks_are_ignored(self):
        """Every skill carries 40 stamped house rules full of the word 'never'.
        If those counted, every skill would look like a rule."""
        stamped = gate.A_JOB + (
            "\n<!-- shared-rule:no-black-buttons:start -->\n"
            "- Never ship a black button.\n"
            "- Do not use pure black.\n"
            "- Always use the accent.\n"
            "- Never override this.\n"
            "<!-- shared-rule:no-black-buttons:end -->\n"
        )
        self.assertEqual(gate.judge(pathlib.Path("x"), stamped), [])


if __name__ == "__main__":
    unittest.main()
