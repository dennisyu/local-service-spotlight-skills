import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.check_installed_parity import check, main


REPOSITORY = Path(__file__).resolve().parents[1]

SKILL = """---
name: {name}
description: "Use when testing parity: it has a colon, so it is quoted."
references:
  - https://example.com/one
  - ../other/SKILL.md
---

# {name}

Body text that must match.
"""


def make_repo(root: Path, names: list[str]) -> Path:
    for name in names:
        skill = root / "skills" / name
        (skill / "references").mkdir(parents=True)
        (skill / "SKILL.md").write_text(SKILL.format(name=name), encoding="utf-8")
        (skill / "references" / "notes.md").write_text(f"notes for {name}\n", encoding="utf-8")
    return root


class InstalledParityTests(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        base = Path(self._temp.name)
        self.repo = make_repo(base / "repo", ["alpha", "beta"])
        self.installed = base / "installed"
        shutil.copytree(self.repo / "skills", self.installed)

    def tearDown(self):
        self._temp.cleanup()

    def test_identical_install_passes(self):
        report = check(self.installed, self.repo)
        self.assertTrue(report["ok"])
        self.assertEqual(report["counts"], {"identical": 2})

    def test_missing_skill_fails(self):
        shutil.rmtree(self.installed / "beta")
        report = check(self.installed, self.repo)
        self.assertFalse(report["ok"])
        self.assertEqual(report["skills"]["beta"]["state"], "missing")

    def test_extra_local_skill_is_reported_not_failed(self):
        shutil.copytree(self.installed / "alpha", self.installed / "local-only")
        report = check(self.installed, self.repo)
        self.assertTrue(report["ok"])
        self.assertEqual(report["skills"]["local-only"]["state"], "extra")

    def test_requoted_and_reindented_frontmatter_is_formatting_only(self):
        skill = self.installed / "alpha" / "SKILL.md"
        text = skill.read_text(encoding="utf-8")
        text = text.replace(
            'description: "Use when testing parity: it has a colon, so it is quoted."',
            "description: 'Use when testing parity: it has a colon, so it is quoted.'",
        ).replace("  - https://example.com/one", "- https://example.com/one")
        text = text.replace("  - ../other/SKILL.md", "- ../other/SKILL.md")
        skill.write_text(text, encoding="utf-8")
        report = check(self.installed, self.repo)
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["skills"]["alpha"]["state"], "frontmatter-only")

    def test_folded_description_flattened_by_an_installer_is_formatting_only(self):
        repo_skill = self.repo / "skills" / "beta" / "SKILL.md"
        repo_skill.write_text(
            repo_skill.read_text(encoding="utf-8").replace(
                'description: "Use when testing parity: it has a colon, so it is quoted."',
                "description: >-\n  Use when testing parity: it has a colon,\n  so it is quoted.",
            ),
            encoding="utf-8",
        )
        report = check(self.installed, self.repo)
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["skills"]["beta"]["state"], "frontmatter-only")

    def test_changed_frontmatter_value_is_drift(self):
        skill = self.installed / "alpha" / "SKILL.md"
        skill.write_text(
            skill.read_text(encoding="utf-8").replace("https://example.com/one", "https://example.com/two"),
            encoding="utf-8",
        )
        report = check(self.installed, self.repo)
        self.assertFalse(report["ok"])
        self.assertEqual(report["skills"]["alpha"]["state"], "drift")
        self.assertIn("SKILL.md: frontmatter values differ", report["skills"]["alpha"]["reasons"])

    def test_changed_body_is_drift(self):
        skill = self.installed / "beta" / "SKILL.md"
        skill.write_text(
            skill.read_text(encoding="utf-8").replace("must match", "was edited"), encoding="utf-8"
        )
        report = check(self.installed, self.repo)
        self.assertFalse(report["ok"])
        self.assertIn("SKILL.md: body differs", report["skills"]["beta"]["reasons"])

    def test_missing_reference_file_is_drift(self):
        (self.installed / "beta" / "references" / "notes.md").unlink()
        report = check(self.installed, self.repo)
        self.assertFalse(report["ok"])
        self.assertIn("references/notes.md: missing from install", report["skills"]["beta"]["reasons"])

    def test_repository_frontmatter_a_strict_parser_rejects_is_listed(self):
        skill = self.repo / "skills" / "alpha" / "SKILL.md"
        skill.write_text(
            skill.read_text(encoding="utf-8").replace(
                'description: "Use when testing parity: it has a colon, so it is quoted."',
                "description: Use when testing parity: it has a colon and no quotes.",
            ),
            encoding="utf-8",
        )
        report = check(self.installed, self.repo)
        self.assertIn("alpha", report["repository_frontmatter_strict_yaml_problems"])

    def test_cli_exit_codes_and_json(self):
        out = Path(self._temp.name) / "report.json"
        self.assertEqual(main(["--installed", str(self.installed), "--repository", str(self.repo), "--json", str(out)]), 0)
        self.assertTrue(json.loads(out.read_text(encoding="utf-8"))["ok"])
        shutil.rmtree(self.installed / "alpha")
        self.assertEqual(main(["--installed", str(self.installed), "--repository", str(self.repo)]), 1)
        self.assertEqual(main(["--installed", str(Path(self._temp.name) / "nope"), "--repository", str(self.repo)]), 2)

    def test_this_repository_matches_itself(self):
        report = check(REPOSITORY / "skills", REPOSITORY)
        self.assertTrue(report["ok"])
        self.assertEqual(report["counts"].get("identical"), report["repository_skills"])
        self.assertEqual(report["repository_frontmatter_strict_yaml_problems"], {})


if __name__ == "__main__":
    unittest.main()
