"""Attribution is only real if an unsigned commit actually fails the build.

The failure mode these tests exist for: a check that accepts any commit message,
reports every branch clean, and leaves the next 9pm incident exactly as
unanswerable as the one that produced the rule.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts import check_commit_attribution as attribution
from scripts.standards_lib import parse_standard


REPOSITORY = Path(__file__).resolve().parents[1]
STANDARD = REPOSITORY / "standards" / "commits-name-the-agent.md"


def commit(message: str, **over) -> attribution.Commit:
    return attribution._sample(message, **over)


class TrailerParsingTests(unittest.TestCase):
    def test_reads_agent_and_coauthor_lines_case_insensitively(self):
        found = attribution.trailers(
            "Subject\n\nBody text\n\nagent: Cursor\nCO-AUTHORED-BY: X <x@y.z>\n"
        )
        self.assertEqual(
            found, [("agent", "Cursor"), ("co-authored-by", "X <x@y.z>")]
        )

    def test_ignores_unrelated_trailers(self):
        self.assertEqual(
            attribution.trailers("S\n\nSigned-off-by: Dennis <d@x.com>\nFixes: #4"),
            [],
        )

    def test_a_colonless_agent_word_is_not_a_trailer(self):
        self.assertEqual(attribution.trailers("S\n\nAgent"), [])


class AgentRecognitionTests(unittest.TestCase):
    def test_known_agent_identities_are_recognised(self):
        for value in (
            "Claude Opus 5 <noreply@anthropic.com>",
            "Cursor <cursoragent@cursor.com>",
            "Codex <codex@openai.com>",
            "Copilot <copilot@github.com>",
            "github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com>",
        ):
            with self.subTest(value=value):
                self.assertTrue(attribution.looks_like_agent(value))

    def test_a_human_coauthor_is_not_an_agent(self):
        self.assertFalse(
            attribution.looks_like_agent("Dennis Yu <dennis@blitzmetrics.com>")
        )

    def test_a_bare_name_with_no_email_still_resolves(self):
        self.assertTrue(attribution.looks_like_agent("Claude Code"))
        self.assertFalse(attribution.looks_like_agent("Jack"))


class ClassificationTests(unittest.TestCase):
    def test_unsigned_commit_is_unattributed(self):
        verdict = attribution.classify(commit("Stamp shared rules"))
        self.assertEqual(verdict.state, "unattributed")
        self.assertFalse(verdict.ok)

    def test_agent_trailer_names_the_agent(self):
        verdict = attribution.classify(commit("Add rule\n\nAgent: Cursor"))
        self.assertEqual((verdict.state, verdict.who), ("agent", "Cursor"))

    def test_human_declaration_is_accepted_and_not_called_an_agent(self):
        for value in sorted(attribution.HUMAN_VALUES):
            with self.subTest(value=value):
                verdict = attribution.classify(commit(f"Add rule\n\nAgent: {value}"))
                self.assertEqual(verdict.state, "human")

    def test_human_coauthor_alone_does_not_satisfy_the_rule(self):
        verdict = attribution.classify(
            commit("Add rule\n\nCo-Authored-By: Dennis Yu <dennis@blitzmetrics.com>")
        )
        self.assertEqual(verdict.state, "unattributed")

    def test_agent_coauthor_beside_a_human_one_satisfies_the_rule(self):
        verdict = attribution.classify(
            commit(
                "Add rule\n\nCo-Authored-By: Dennis Yu <d@x.com>\n"
                "Co-Authored-By: Cursor <cursoragent@cursor.com>"
            )
        )
        self.assertEqual(verdict.state, "agent")

    def test_merge_and_squash_and_bot_commits_are_exempt(self):
        for kwargs in (
            {"parents": 2},
            {"committer_email": "noreply@github.com"},
            {"author_name": "github-actions[bot]"},
        ):
            with self.subTest(**kwargs):
                verdict = attribution.classify(commit("Merge", **kwargs))
                self.assertEqual(verdict.state, "exempt")


class SelfTestTests(unittest.TestCase):
    def test_shipped_self_test_passes(self):
        self.assertEqual(attribution.self_test(), 0)

    def test_every_violating_sample_is_flagged(self):
        for sample in attribution.VIOLATING:
            with self.subTest(subject=sample.subject):
                self.assertFalse(attribution.classify(sample).ok)

    def test_every_clean_sample_is_cleared(self):
        for sample in attribution.CLEAN:
            with self.subTest(message=sample.message):
                self.assertTrue(attribution.classify(sample).ok)

    def test_self_test_fails_when_the_classifier_stops_flagging(self):
        original = attribution.classify
        try:
            attribution.classify = lambda c: attribution.Verdict("agent", "x", "stub")
            self.assertEqual(attribution.self_test(), 1)
        finally:
            attribution.classify = original


class CutoffTests(unittest.TestCase):
    def test_cutoff_comes_from_the_standard_itself(self):
        self.assertEqual(attribution.cutoff(), parse_standard(STANDARD).captured)

    def test_cutoff_is_a_date(self):
        self.assertRegex(attribution.cutoff(), r"^\d{4}-\d{2}-\d{2}$")


class GitIntegrationTests(unittest.TestCase):
    """Read real commits out of a real repository, not just fixtures."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Dennis Yu")
        self.git("config", "user.email", "668sierra@gmail.com")

    def git(self, *args):
        subprocess.run(
            ["git", *args], cwd=str(self.repo), check=True, capture_output=True
        )

    def write_commit(self, message: str, name: str):
        (self.repo / name).write_text(name, encoding="utf-8")
        self.git("add", name)
        self.git("commit", "-q", "-m", message)

    def test_reads_author_date_parents_and_message_from_git(self):
        self.write_commit("Unsigned change", "a.txt")
        self.write_commit("Signed change\n\nAgent: Claude Code", "b.txt")

        commits = attribution.read_commits("HEAD", cwd=self.repo)
        self.assertEqual(len(commits), 2)
        states = {c.subject: attribution.classify(c).state for c in commits}
        self.assertEqual(states["Unsigned change"], "unattributed")
        self.assertEqual(states["Signed change"], "agent")
        self.assertRegex(commits[0].date, r"^\d{4}-\d{2}-\d{2}$")
        self.assertEqual(commits[0].parents, 1)

    def test_multiline_body_survives_the_record_separator(self):
        self.write_commit(
            "Subject line\n\nA body with\nseveral lines\nand a blank one\n\n"
            "Agent: Cursor",
            "c.txt",
        )
        commit_obj = attribution.read_commits("HEAD", cwd=self.repo)[0]
        self.assertIn("several lines", commit_obj.message)
        self.assertEqual(attribution.classify(commit_obj).who, "Cursor")


class RepositoryHistoryTests(unittest.TestCase):
    def test_the_signing_agents_in_this_history_are_recognised(self):
        """Cursor and Claude already sign; the check must never accuse them."""
        for value in (
            "Cursor <cursoragent@cursor.com>",
            "Claude Opus 5 <noreply@anthropic.com>",
        ):
            with self.subTest(value=value):
                verdict = attribution.classify(
                    commit(f"Real commit\n\nCo-authored-by: {value}")
                )
                self.assertEqual(verdict.state, "agent")

    def test_the_incident_commit_would_have_been_caught(self):
        """The exact message from the six red runs of 2026-08-22."""
        verdict = attribution.classify(
            commit("Stamp shared rules for email/examples/CF four-stages standards")
        )
        self.assertFalse(verdict.ok)
        self.assertIn("cannot tell who wrote this", verdict.reason)


if __name__ == "__main__":
    unittest.main()
