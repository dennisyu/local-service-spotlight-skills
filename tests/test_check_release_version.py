import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.check_release_version import (
    ReleaseVersionError,
    changed_paths,
    check_release,
    resolve_base_commit,
)


class ReleaseVersionGateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "repository"
        self.root.mkdir()
        self._git("init", "-q")
        self._git("config", "user.email", "tests@example.com")
        self._git("config", "user.name", "Release Gate Tests")
        (self.root / ".claude-plugin").mkdir()
        (self.root / ".grok-plugin").mkdir()
        (self.root / "skills" / "example").mkdir(parents=True)
        self._write_versions("1.2.1", "1.2.0")
        (self.root / "skills" / "example" / "SKILL.md").write_text(
            "example\n", encoding="utf-8"
        )
        (self.root / "README.md").write_text("base\n", encoding="utf-8")
        self.base = self._commit("base")

    def tearDown(self):
        self.temporary.cleanup()

    def _git(self, *arguments: str) -> str:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=self.root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return completed.stdout.strip()

    def _write_versions(self, claude: str, grok: str) -> None:
        (self.root / ".claude-plugin" / "marketplace.json").write_text(
            json.dumps({"metadata": {"version": claude}}),
            encoding="utf-8",
        )
        (self.root / ".grok-plugin" / "plugin.json").write_text(
            json.dumps({"name": "lss-everything", "version": grok}),
            encoding="utf-8",
        )

    def _commit(self, message: str) -> str:
        self._git("add", "--all")
        self._git("commit", "-qm", message)
        return self._git("rev-parse", "HEAD")

    def test_pr21_target_passes_for_protected_changes(self):
        (self.root / "AGENTS.md").write_text("new rule\n", encoding="utf-8")
        self._write_versions("1.2.2", "1.2.2")

        report = check_release(self.root, self.base)

        self.assertEqual(report.current_version, "1.2.2")
        self.assertEqual(report.base_versions.claude, "1.2.1")
        self.assertEqual(report.base_versions.grok, "1.2.0")
        self.assertEqual(report.protected_changes, ("AGENTS.md",))

    def test_protected_change_rejects_version_unchanged_from_either_base_manifest(self):
        (self.root / "standards").mkdir()
        (self.root / "standards" / "new-rule.md").write_text(
            "rule\n", encoding="utf-8"
        )
        self._write_versions("1.2.1", "1.2.1")

        with self.assertRaisesRegex(
            ReleaseVersionError,
            r"not changed from every base manifest.*marketplace\.json",
        ):
            check_release(self.root, self.base)

    def test_current_manifests_must_match_even_for_unprotected_change(self):
        (self.root / "README.md").write_text("docs only\n", encoding="utf-8")
        self._write_versions("1.2.2", "1.2.1")

        with self.assertRaisesRegex(
            ReleaseVersionError, "current release versions must match"
        ):
            check_release(self.root, self.base)

    def test_unprotected_change_allows_existing_shared_version(self):
        self._write_versions("1.2.1", "1.2.1")
        self.base = self._commit("align versions")
        (self.root / "README.md").write_text("docs only\n", encoding="utf-8")

        report = check_release(self.root, self.base)

        self.assertEqual(report.current_version, "1.2.1")
        self.assertEqual(report.protected_changes, ())
        self.assertIsNone(report.base_versions)

    def test_move_out_of_skills_cannot_evade_bump(self):
        (self.root / "docs").mkdir()
        self._git("mv", "skills/example/SKILL.md", "docs/example.md")
        self._write_versions("1.2.1", "1.2.1")
        base_commit = resolve_base_commit(self.root, self.base)

        paths = changed_paths(self.root, base_commit)

        self.assertIn("skills/example/SKILL.md", paths)
        with self.assertRaisesRegex(ReleaseVersionError, "protected marketplace"):
            check_release(self.root, self.base)

    def test_unknown_base_ref_fails_closed(self):
        self._write_versions("1.2.2", "1.2.2")

        with self.assertRaisesRegex(ReleaseVersionError, "rev-parse.*failed"):
            check_release(self.root, "missing-base")


if __name__ == "__main__":
    unittest.main()
