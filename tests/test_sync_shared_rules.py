"""Tests for the multi-rule shared-standards sync."""

from __future__ import annotations

import importlib.util
import json
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
                f"---\nname: {name}\ndescription: test\n"
                f"rule-scopes: agent-behaviour\n---\n\n# {name}\n",
                encoding="utf-8",
            )
        self.addCleanup(self._tmp.cleanup)

    def write_standard(self, slug: str, body: str):
        heading = body.splitlines()[0].removeprefix("## ").strip()
        header = {
            "title": heading,
            "severity": "error",
            "captured": "2026-08-16",
            "captured_from": "test",
        }
        (self.root / "standards" / f"{slug}.md").write_text(
            "---\n" + json.dumps(header) + "\n---\n\n" + body,
            encoding="utf-8",
        )

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

    def test_lone_or_duplicate_shared_rule_markers_fail_closed(self):
        mod = load_module(self.root)
        self.write_standard("rule-one", "## One\n\n- first")
        for malformed in (
            "<!-- shared-rule:orphan:end -->",
            "<!-- shared-rule:rule-one:start -->\n"
            "<!-- shared-rule:rule-one:start -->\n"
            "<!-- shared-rule:rule-one:end -->",
            "<!-- shared-rule:rule-one:end -->\n"
            "<!-- shared-rule:rule-one:start -->",
        ):
            with self.subTest(malformed=malformed):
                (self.root / "AGENTS.md").write_text(malformed, encoding="utf-8")
                with self.assertRaises(ValueError):
                    mod.sync(check=True)

    def test_confusable_shared_rule_markers_cannot_leave_stale_teaching(self):
        mod = load_module(self.root)
        self.write_standard("rule-one", "## One\n\n- current")
        malformed_pairs = (
            "<!-- shared-rule:rule-one:START -->\n- stale\n"
            "<!-- shared-rule:rule-one:END -->",
            "<!-- shared-rule : rule-one : start -->\n- stale\n"
            "<!-- shared-rule : rule-one : end -->",
            "<!-- ｓｈａｒｅｄ-rule:rule-one:start -->\n- stale\n"
            "<!-- ｓｈａｒｅｄ-rule:rule-one:end -->",
            "<!-- shared-\u200brule:rule-one:start -->\n- stale\n"
            "<!-- shared-\u200brule:rule-one:end -->",
            "<!-- shared‐rule:rule-one:start -->\n- stale\n"
            "<!-- shared‐rule:rule-one:end -->",
            "<!-- shared_rule:rule-one:start -->\n- stale\n"
            "<!-- shared_rule:rule-one:end -->",
            "<!-- shared-rule:rule-one:start >\n- stale\n",
            "<!-- benign --> <!-- shared-rule:rule-one:start >",
            "<!-- benign --><!-- shared_\u200brule:rule-one:start >",
            "<!-- benign shared‐rule:rule-one:start -->\n- stale",
            "<!--prefix shared-rule:rule-one:start -->\n- stale",
            "<!-- benign <!-- shared‐rule:rule-one:start -->\n- stale",
            "<!-- shared-rule∶rule-one∶start -->\n- stale",
            "<!-- shared-rule꞉rule-one꞉start -->\n- stale",
        )
        for malformed in malformed_pairs:
            with self.subTest(malformed=malformed[:50]):
                (self.root / "AGENTS.md").write_text(malformed, encoding="utf-8")
                with self.assertRaises(ValueError):
                    mod.sync(check=True)

    def test_legacy_index_markers_must_be_one_ordered_pair(self):
        mod = load_module(self.root)
        for malformed in (
            mod.INDEX_START,
            mod.INDEX_END,
            mod.INDEX_START + mod.INDEX_START + mod.INDEX_END,
            mod.INDEX_END + mod.INDEX_START,
        ):
            with self.subTest(malformed=malformed):
                with self.assertRaises(ValueError):
                    mod.drop_index(malformed)


if __name__ == "__main__":
    unittest.main()


class ScopedEmbeddingTests(unittest.TestCase):
    """Rules reach every agent that needs them, and no further."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "standards").mkdir()
        (self.root / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
        self.addCleanup(self._tmp.cleanup)

    def skill(self, name: str, scopes: str | None = None):
        directory = self.root / "skills" / name
        directory.mkdir(parents=True)
        scope_line = f"rule-scopes: {scopes or 'agent-behaviour'}\n"
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
            "---\n" + _json.dumps(header) + f"\n---\n\n## {header['title']}\n\n- {body}\n",
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

    def test_out_of_scope_rule_does_not_leave_an_evaporating_repository_link(self):
        mod = load_module(self.root)
        plain = self.skill("subscription-audit")
        self.standard("no-black-buttons", ["published-html"], "never black")

        mod.sync()
        text = plain.read_text(encoding="utf-8")

        self.assertNotIn(mod.INDEX_START, text)
        self.assertNotIn("`no-black-buttons`", text)
        self.assertNotIn("AGENTS.md", text)

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
                "rule-scopes: published-html\n", "rule-scopes: agent-behaviour\n"
            ),
            encoding="utf-8",
        )
        _, orphans = mod.sync()

        self.assertEqual(orphans, [])
        text = skill.read_text(encoding="utf-8")
        self.assertNotIn("<!-- shared-rule:no-black-buttons:start -->", text)
        self.assertNotIn(mod.INDEX_START, text)

    def test_an_unknown_scope_is_rejected(self):
        mod = load_module(self.root)
        self.skill("website-agent", scopes="published-html, nonsense")
        self.standard("always-verify", ["agent-behaviour"], "check")
        with self.assertRaises(ValueError):
            mod.sync()
