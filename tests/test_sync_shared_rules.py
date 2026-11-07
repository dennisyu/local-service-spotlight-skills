"""Tests for the multi-rule shared-standards sync.

Standard v2 (D-2026-11-05-05) gives a source skill one of three states:

- legacy inlined: it already carries rule blocks (or their index), so the sync
  embeds and checks blocks exactly as before;
- not yet converted: no blocks and no pointer, so the sync reports it and
  leaves it alone;
- referenced: it carries the harness-layer pointer, so the sync validates it
  and never inlines into it.

``AGENTS.md`` always carries every block, and ``--export`` inlines every skill
whatever its state. The embedding tests seed their skills in the legacy state,
so they exercise the same path they did before v2; ``StandardV2StatesTests``
covers the other two states and the export guarantee.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]

# An empty index marks a skill as legacy-inlined: the next sync replaces it
# with the skill's real blocks and index.
LEGACY_SEED = "\n<!-- shared-rule-index:start -->\n<!-- shared-rule-index:end -->\n"


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
                f"---\nname: {name}\ndescription: test\n---\n\n# {name}\n"
                + LEGACY_SEED,
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

        changed, orphans, problems, pending = mod.sync()

        self.assertEqual(orphans, [])
        self.assertEqual(problems, [])
        self.assertEqual(pending, [])  # both skills are on the legacy path
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
        changed, *_ = mod.sync()
        self.assertEqual(changed, [])

        stale, *_ = mod.sync(check=True)
        self.assertEqual(stale, [])

    def test_edited_standard_is_detected_as_stale(self):
        """Changing a standard makes --check fail until re-synced."""
        mod = load_module(self.root)
        self.write_standard("rule-one", "## One\n\n- first")
        mod.sync()

        self.write_standard("rule-one", "## One\n\n- first\n- amended")
        stale, *_ = mod.sync(check=True)
        self.assertTrue(stale, "an amended standard must report as stale")

        mod.sync()
        stale, *_ = mod.sync(check=True)
        self.assertEqual(stale, [])

    def test_new_rule_after_existing_scoped_index_is_immediately_stable(self):
        mod = load_module(self.root)
        self.write_standard("rule-one", "## One\n\n- first")
        self.write_standard("visual-rule", '---\n{"title":"Visual rule","severity":"error","captured":"2026-09-06","captured_from":"test","applies_to":["design-review"]}\n---\n\n## Visual\n\n- inspect')
        mod.sync()
        self.write_standard("rule-two", "## Two\n\n- added after an index exists")
        mod.sync()
        stale, orphans, *_ = mod.sync(check=True)
        self.assertEqual(stale, [])
        self.assertEqual(orphans, [])

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

        _, orphans, *_ = mod.sync(check=True)
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
            f"---\nname: {name}\ndescription: test\n{scope_line}---\n\n# {name}\n"
            + LEGACY_SEED,
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
        _, orphans, *_ = mod.sync()

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


class StandardV2StatesTests(unittest.TestCase):
    """The two source states v2 added, and the export that makes them safe.

    A rule that is only linked vanishes when one skill is installed on its own,
    so leaving a skill un-inlined in the source tree is only safe if the export
    inlines it. These tests pin both halves.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "standards").mkdir()
        (self.root / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
        self.addCleanup(self._tmp.cleanup)
        self.mod = load_module(self.root)

    def skill(self, name: str, state: str, scopes: str | None = None) -> Path:
        directory = self.root / "skills" / name
        directory.mkdir(parents=True)
        scope_line = f"rule-scopes: {scopes}\n" if scopes else ""
        text = f"---\nname: {name}\ndescription: test\n{scope_line}---\n\n# {name}\n"
        if state == "legacy":
            text += LEGACY_SEED
        elif state == "referenced":
            text += (
                f"\n{self.mod.REFERENCED_HEADING}\n\n"
                "The shared rules live once, at the harness layer.\n"
            )
        else:
            self.assertEqual(state, "pending")
        (directory / "SKILL.md").write_text(text, encoding="utf-8")
        return directory / "SKILL.md"

    def standard(self, slug: str, applies_to: list[str], body: str):
        import json as _json

        header = {
            "title": slug.replace("-", " ").capitalize(),
            "severity": "error",
            "captured": "2026-11-05",
            "captured_from": "test",
            "applies_to": applies_to,
        }
        (self.root / "standards" / f"{slug}.md").write_text(
            "---\n" + _json.dumps(header) + f"\n---\n\n## {slug}\n\n- {body}\n",
            encoding="utf-8",
        )

    def run_main(self, *args: str) -> tuple[int, str]:
        out = io.StringIO()
        saved = sys.argv
        sys.argv = ["sync_shared_rules.py", *args]
        try:
            with contextlib.redirect_stdout(out):
                code = self.mod.main()
        finally:
            sys.argv = saved
        return code, out.getvalue()

    def test_an_unconverted_skill_is_reported_and_left_alone(self):
        pending_skill = self.skill("plain", "pending")
        before = pending_skill.read_text(encoding="utf-8")
        self.standard("always-verify", ["agent-behaviour"], "check the artifact")

        changed, orphans, problems, pending = self.mod.sync()

        self.assertEqual(pending, [pending_skill])
        self.assertNotIn(pending_skill, changed)
        self.assertEqual((orphans, problems), ([], []))
        self.assertEqual(pending_skill.read_text(encoding="utf-8"), before)
        # AGENTS.md is the in-repo copy the skill is covered by, so it still
        # receives the block even though no skill is inlined.
        self.assertIn(self.root / "AGENTS.md", changed)
        self.assertIn(
            "<!-- shared-rule:always-verify:start -->",
            (self.root / "AGENTS.md").read_text(encoding="utf-8"),
        )

        code, output = self.run_main("--check")
        self.assertEqual(code, 0, output)
        self.assertIn("Not yet converted", output)
        self.assertIn("skills/plain/SKILL.md", output)

    def test_a_referenced_skill_is_validated_and_never_inlined(self):
        pointer = self.skill("pointer", "referenced")
        before = pointer.read_text(encoding="utf-8")
        self.standard("always-verify", ["agent-behaviour"], "check the artifact")

        changed, orphans, problems, pending = self.mod.sync()

        self.assertNotIn(pointer, changed)
        self.assertNotIn(pointer, pending)
        self.assertEqual((orphans, problems), ([], []))
        self.assertEqual(pointer.read_text(encoding="utf-8"), before)

    def test_a_referenced_skill_that_carries_a_block_fails_the_check(self):
        pointer = self.skill("pointer", "referenced")
        self.standard("always-verify", ["agent-behaviour"], "check the artifact")
        block = dict(self.mod.standards())["always-verify"]
        pointer.write_text(
            pointer.read_text(encoding="utf-8") + "\n" + block + "\n",
            encoding="utf-8",
        )
        before = pointer.read_text(encoding="utf-8")

        _, _, problems, _ = self.mod.sync(check=True)

        self.assertEqual(len(problems), 1)
        self.assertIn("skills/pointer/SKILL.md", problems[0])
        self.assertIn("always-verify", problems[0])
        code, output = self.run_main("--check")
        self.assertEqual(code, 1, output)
        self.assertIn("Referenced-form violations", output)
        # A write-mode run reports the same problem and changes nothing in it.
        self.assertEqual(self.run_main()[0], 1)
        self.assertEqual(pointer.read_text(encoding="utf-8"), before)

    def test_export_inlines_every_skill_whatever_its_state(self):
        sources = {
            "legacy": self.skill("legacy", "legacy"),
            "plain": self.skill("plain", "pending"),
            "pointer": self.skill("pointer", "referenced"),
            "website": self.skill("website", "pending", scopes="published-html"),
        }
        self.standard("always-verify", ["agent-behaviour"], "check the artifact")
        self.standard("no-black-buttons", ["published-html"], "never black")
        snapshot = {p: p.read_text(encoding="utf-8") for p in sources.values()}
        agents_before = (self.root / "AGENTS.md").read_text(encoding="utf-8")
        target = self.root / "export"

        written = self.mod.export_tree(target)

        self.assertEqual(len(written), 1 + len(sources))  # AGENTS.md + skills
        exported = {
            name: (target / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
            for name in sources
        }
        for name, text in exported.items():
            self.assertIn("<!-- shared-rule:always-verify:start -->", text, name)
        for name in ("legacy", "plain", "pointer"):
            # a web-only rule is not copied into an agent skill, but stays named
            self.assertNotIn(
                "<!-- shared-rule:no-black-buttons:start -->", exported[name], name
            )
            self.assertIn("`no-black-buttons`", exported[name], name)
        self.assertIn("<!-- shared-rule:no-black-buttons:start -->", exported["website"])
        self.assertIn(self.mod.REFERENCED_HEADING, exported["pointer"])
        exported_agents = (target / "AGENTS.md").read_text(encoding="utf-8")
        for slug in ("always-verify", "no-black-buttons"):
            self.assertIn(f"<!-- shared-rule:{slug}:start -->", exported_agents)
        # the source tree is untouched
        for path, text in snapshot.items():
            self.assertEqual(path.read_text(encoding="utf-8"), text, path)
        self.assertEqual(
            (self.root / "AGENTS.md").read_text(encoding="utf-8"), agents_before
        )

    def test_export_refuses_a_non_empty_target(self):
        self.skill("plain", "pending")
        self.standard("always-verify", ["agent-behaviour"], "check the artifact")
        target = self.root / "export"
        target.mkdir()
        (target / "keep.txt").write_text("someone else's file\n", encoding="utf-8")

        with self.assertRaises(self.mod.StandardError):
            self.mod.export_tree(target)
        self.assertEqual(
            (target / "keep.txt").read_text(encoding="utf-8"), "someone else's file\n"
        )


if __name__ == "__main__":
    unittest.main()
