"""Tests for the multi-rule shared-standards sync."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def load_module(root: Path):
    """Import sync_shared_rules with ROOT pointed at a scratch repo."""
    spec = importlib.util.spec_from_file_location(
        f"sync_shared_rules_{root.name}", REPO / "scripts" / "sync_shared_rules.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    module.ROOT = root
    module.STANDARDS_DIR = root / "standards"
    return module


class SyncSharedRulesTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "standards").mkdir()
        (self.root / "skills" / "alpha").mkdir(parents=True)
        (self.root / "skills" / "beta").mkdir(parents=True)
        (self.root / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
        for name in ("alpha", "beta"):
            (self.root / "skills" / name / "SKILL.md").write_text(
                f"---\nname: {name}\ndescription: test\n---\n\n# {name}\n",
                encoding="utf-8",
            )
        self.addCleanup(self._tmp.cleanup)

    def write_standard(self, slug: str, body: str):
        (self.root / "standards" / f"{slug}.md").write_text(body, encoding="utf-8")

    def test_every_standard_reaches_every_skill(self):
        """N standards land in AGENTS.md and all SKILL.md files."""
        mod = load_module(self.root)
        self.write_standard("rule-one", "## One\n\n- first")
        self.write_standard("rule-two", "## Two\n\n- second")

        changed, orphans = mod.sync()

        self.assertEqual(orphans, [])
        self.assertEqual(len(changed), 3)  # AGENTS.md + 2 skills
        for path in mod.targets():
            text = path.read_text(encoding="utf-8")
            for slug in ("rule-one", "rule-two"):
                self.assertIn(f"<!-- shared-rule:{slug}:start -->", text)
                self.assertIn(f"<!-- shared-rule:{slug}:end -->", text)

    def test_sync_is_idempotent(self):
        """A second run changes nothing and --check passes."""
        mod = load_module(self.root)
        self.write_standard("rule-one", "## One\n\n- first")

        mod.sync()
        changed, _ = mod.sync()
        self.assertEqual(changed, [])

        stale, _ = mod.sync(check=True)
        self.assertEqual(stale, [])

    def test_edited_standard_is_detected_as_stale(self):
        """Changing a standard makes --check fail until re-synced."""
        mod = load_module(self.root)
        self.write_standard("rule-one", "## One\n\n- first")
        mod.sync()

        self.write_standard("rule-one", "## One\n\n- first\n- amended")
        stale, _ = mod.sync(check=True)
        self.assertTrue(stale, "an amended standard must report as stale")

        mod.sync()
        stale, _ = mod.sync(check=True)
        self.assertEqual(stale, [])

    def test_adding_a_standard_does_not_clobber_an_existing_one(self):
        """The regression that matters: rule two must not eat rule one."""
        mod = load_module(self.root)
        self.write_standard("rule-one", "## One\n\n- first")
        mod.sync()

        self.write_standard("rule-two", "## Two\n\n- second")
        mod.sync()

        for path in mod.targets():
            text = path.read_text(encoding="utf-8")
            self.assertIn("- first", text)
            self.assertIn("- second", text)
            self.assertEqual(text.count("<!-- shared-rule:rule-one:start -->"), 1)

    def test_orphan_block_is_reported(self):
        """A block whose standards/ source was deleted fails rather than lingering."""
        mod = load_module(self.root)
        self.write_standard("rule-one", "## One\n\n- first")
        mod.sync()
        (self.root / "standards" / "rule-one.md").unlink()

        _, orphans = mod.sync(check=True)
        self.assertTrue(orphans)
        self.assertEqual(orphans[0][1], "rule-one")

    def test_bad_filename_is_rejected(self):
        mod = load_module(self.root)
        self.write_standard("Rule_One", "## One\n\n- first")
        with self.assertRaises(ValueError):
            mod.standards()

    def test_empty_standard_is_rejected(self):
        mod = load_module(self.root)
        self.write_standard("rule-one", "   \n")
        with self.assertRaises(ValueError):
            mod.standards()


if __name__ == "__main__":
    unittest.main()


class ScopedEmbeddingTests(unittest.TestCase):
    """Rules reach every agent that needs them, and no further.

    Embedding every rule in every skill made the rules larger than the skills
    carrying them. Scoping is only safe if nothing becomes invisible — so a rule
    a skill does not carry must still be named in its index.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "standards").mkdir()
        (self.root / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
        self.addCleanup(self._tmp.cleanup)

    def skill(self, name: str, scopes: str | None = None):
        directory = self.root / "skills" / name
        directory.mkdir(parents=True)
        scope_line = f"rule-scopes: {scopes}\n" if scopes else ""
        (directory / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: test\n{scope_line}---\n\n# {name}\n",
            encoding="utf-8",
        )
        return directory / "SKILL.md"

    def standard(self, slug: str, applies_to: list[str], body: str):
        import json as _json

        header = {
            "title": slug.replace("-", " ").capitalize(),
            "severity": "error",
            "captured": "2026-08-16",
            "captured_from": "test",
            "applies_to": applies_to,
        }
        (self.root / "standards" / f"{slug}.md").write_text(
            "---\n" + _json.dumps(header) + f"\n---\n\n## {slug}\n\n- {body}\n",
            encoding="utf-8",
        )

    def test_agent_rules_reach_every_skill_and_web_rules_only_web_skills(self):
        mod = load_module(self.root)
        plain = self.skill("subscription-audit")
        web = self.skill("website-agent", scopes="published-html, design-review")
        self.standard("always-verify", ["agent-behaviour"], "check the artifact")
        self.standard("no-black-buttons", ["published-html"], "never black")

        mod.sync()

        plain_text = plain.read_text(encoding="utf-8")
        web_text = web.read_text(encoding="utf-8")

        self.assertIn("<!-- shared-rule:always-verify:start -->", plain_text)
        self.assertIn("<!-- shared-rule:always-verify:start -->", web_text)

        self.assertNotIn("<!-- shared-rule:no-black-buttons:start -->", plain_text)
        self.assertIn("<!-- shared-rule:no-black-buttons:start -->", web_text)

    def test_a_rule_a_skill_does_not_carry_is_still_named_in_its_index(self):
        mod = load_module(self.root)
        plain = self.skill("subscription-audit")
        self.standard("no-black-buttons", ["published-html"], "never black")

        mod.sync()
        text = plain.read_text(encoding="utf-8")

        self.assertIn(mod.INDEX_START, text)
        self.assertIn("`no-black-buttons`", text)
        self.assertIn("AGENTS.md", text)

    def test_agents_md_always_carries_every_rule(self):
        mod = load_module(self.root)
        self.skill("subscription-audit")
        self.standard("always-verify", ["agent-behaviour"], "check the artifact")
        self.standard("no-black-buttons", ["published-html"], "never black")

        mod.sync()
        text = (self.root / "AGENTS.md").read_text(encoding="utf-8")

        self.assertIn("<!-- shared-rule:always-verify:start -->", text)
        self.assertIn("<!-- shared-rule:no-black-buttons:start -->", text)
        self.assertNotIn(mod.INDEX_START, text)

    def test_dropping_a_scope_removes_the_block_without_an_orphan_error(self):
        mod = load_module(self.root)
        skill = self.skill("website-agent", scopes="published-html")
        self.standard("no-black-buttons", ["published-html"], "never black")
        mod.sync()
        self.assertIn("<!-- shared-rule:no-black-buttons:start -->",
                      skill.read_text(encoding="utf-8"))

        skill.write_text(
            skill.read_text(encoding="utf-8").replace(
                "rule-scopes: published-html\n", ""
            ),
            encoding="utf-8",
        )
        _, orphans = mod.sync()

        self.assertEqual(orphans, [])
        text = skill.read_text(encoding="utf-8")
        self.assertNotIn("<!-- shared-rule:no-black-buttons:start -->", text)
        self.assertIn("`no-black-buttons`", text)

    def test_an_unknown_scope_is_rejected(self):
        mod = load_module(self.root)
        self.skill("website-agent", scopes="published-html, nonsense")
        self.standard("always-verify", ["agent-behaviour"], "check")
        with self.assertRaises(ValueError):
            mod.sync()


class SinglePassConvergenceTests(ScopedEmbeddingTests):
    """One sync pass must be enough, forever.

    The regression this exists for: a file carrying a trailing rule index gained
    a *new* standard. The new block was appended after the index, and the join
    that then lifted the index out glued the new block to the previous one —
    one missing blank line. `sync` reported it had updated every file and
    `--check` still called them stale, so the fix looked like it had not worked.
    Running sync twice converged, which made a real bug look like a mystery and
    cost six red CI runs on 2026-08-22 to track down.

    An idempotence test over agent-behaviour rules alone never sees this: those
    files have no index block for a new rule to land behind.
    """

    def test_adding_a_standard_to_a_file_with_an_index_converges_in_one_pass(self):
        mod = load_module(self.root)
        self.skill("subscription-audit")  # unscoped, so web rules become an index
        self.standard("always-verify", ["agent-behaviour"], "check the artifact")
        self.standard("no-black-buttons", ["published-html"], "never pure black")
        mod.sync()
        self.assertEqual(mod.sync(check=True)[0], [], "setup should start clean")

        # The move that broke it: a brand-new rule arriving in a file with an index.
        self.standard("commits-name-the-agent", ["agent-behaviour"], "sign it")
        changed, _ = mod.sync()
        self.assertTrue(changed, "the new rule should have been written somewhere")

        stale, _ = mod.sync(check=True)
        self.assertEqual(
            stale,
            [],
            "one pass must converge — a second pass that changes files is the bug",
        )

    def test_one_pass_output_equals_repeated_passes(self):
        mod = load_module(self.root)
        self.skill("subscription-audit")
        self.skill("website-agent", scopes="published-html")
        self.standard("always-verify", ["agent-behaviour"], "check the artifact")
        self.standard("no-black-buttons", ["published-html"], "never pure black")
        mod.sync()
        self.standard("commits-name-the-agent", ["agent-behaviour"], "sign it")

        mod.sync()
        after_one = {p: p.read_text(encoding="utf-8") for p in mod.targets()}
        for _ in range(3):
            mod.sync()
        after_many = {p: p.read_text(encoding="utf-8") for p in mod.targets()}

        self.assertEqual(after_one, after_many)

    def test_every_generated_block_is_separated_by_a_blank_line(self):
        """The exact byte that went missing."""
        mod = load_module(self.root)
        skill = self.skill("subscription-audit")
        self.standard("always-verify", ["agent-behaviour"], "check the artifact")
        self.standard("no-black-buttons", ["published-html"], "never pure black")
        mod.sync()
        self.standard("commits-name-the-agent", ["agent-behaviour"], "sign it")
        mod.sync()

        for path in (skill, self.root / "AGENTS.md"):
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertNotRegex(
                    text,
                    r":end -->\n<!-- shared-rule:",
                    "two generated blocks are touching with no blank line between",
                )


class BlockRemovalSpacingTests(ScopedEmbeddingTests):
    def test_removing_a_middle_block_leaves_its_neighbours_separated(self):
        mod = load_module(self.root)
        skill = self.skill("subscription-audit")
        for slug in ("a-rule", "b-rule", "c-rule"):
            self.standard(slug, ["agent-behaviour"], "do it")
        mod.sync()

        (self.root / "standards" / "b-rule.md").unlink()
        mod.sync(prune=True)

        text = skill.read_text(encoding="utf-8")
        self.assertNotIn("shared-rule:b-rule", text)
        self.assertNotRegex(text, r":end -->\n<!-- shared-rule:")
        self.assertEqual(mod.sync(check=True)[0], [])
