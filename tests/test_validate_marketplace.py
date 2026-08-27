import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.validate_marketplace import validate


REPOSITORY = Path(__file__).resolve().parents[1]


class MarketplaceValidatorTests(unittest.TestCase):
    def copy_repository(self, temp_name: str) -> Path:
        copied = Path(temp_name) / "repository"
        shutil.copytree(REPOSITORY, copied, ignore=shutil.ignore_patterns(".git"))
        return copied

    def test_current_repository_passes(self):
        self.assertEqual(validate(REPOSITORY), [])

    def test_missing_referenced_skill_fails(self):
        with tempfile.TemporaryDirectory() as temp_name:
            copied = Path(temp_name) / "repository"
            shutil.copytree(REPOSITORY, copied, ignore=shutil.ignore_patterns(".git"))
            shutil.rmtree(copied / "skills" / "seo-audit")

            errors = validate(copied)

            self.assertTrue(
                any("./skills/seo-audit" in error for error in errors),
                errors,
            )

    def _strip_rule(self, skill_file: Path, slug: str) -> None:
        text = skill_file.read_text(encoding="utf-8")
        start = f"<!-- shared-rule:{slug}:start -->"
        end = f"<!-- shared-rule:{slug}:end -->"
        before, rest = text.split(start, 1)
        _, after = rest.split(end, 1)
        skill_file.write_text(before.rstrip() + after, encoding="utf-8")

    def test_missing_shared_media_rule_fails(self):
        with tempfile.TemporaryDirectory() as temp_name:
            copied = Path(temp_name) / "repository"
            shutil.copytree(REPOSITORY, copied, ignore=shutil.ignore_patterns(".git"))
            self._strip_rule(
                copied / "skills" / "content-agent" / "SKILL.md",
                "silent-media-playback",
            )

            errors = validate(copied)

            self.assertTrue(
                any(
                    "content-agent/SKILL.md has a missing or stale shared rule: "
                    "silent-media-playback" in error
                    for error in errors
                ),
                errors,
            )

    def test_every_standard_is_validated_not_just_the_first(self):
        """The regression this repository already shipped once: the validator
        checked exactly one hardcoded rule, so a second rule could go missing
        from every distributed skill and still pass."""
        with tempfile.TemporaryDirectory() as temp_name:
            copied = Path(temp_name) / "repository"
            shutil.copytree(REPOSITORY, copied, ignore=shutil.ignore_patterns(".git"))
            self._strip_rule(
                copied / "skills" / "seo-audit" / "SKILL.md", "no-black-buttons"
            )

            errors = validate(copied)

            self.assertTrue(
                any(
                    "seo-audit/SKILL.md has a missing or stale shared rule: "
                    "no-black-buttons" in error
                    for error in errors
                ),
                errors,
            )

    def test_grok_and_claude_versions_must_match(self):
        with tempfile.TemporaryDirectory() as temp_name:
            copied = self.copy_repository(temp_name)
            grok_path = copied / ".grok-plugin" / "plugin.json"
            grok = json.loads(grok_path.read_text(encoding="utf-8"))
            grok["version"] = "9.9.9"
            grok_path.write_text(json.dumps(grok), encoding="utf-8")

            errors = validate(copied)

            self.assertIn(
                ".grok-plugin/plugin.json version must equal marketplace metadata.version",
                errors,
            )

    def test_manifest_description_count_must_match_bundle(self):
        with tempfile.TemporaryDirectory() as temp_name:
            copied = self.copy_repository(temp_name)
            manifest_path = copied / ".claude-plugin" / "marketplace.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            bundle = next(
                plugin for plugin in manifest["plugins"]
                if plugin["name"] == "authority-and-reputation"
            )
            bundle["description"] = bundle["description"].replace("8 skills", "999 skills")
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            errors = validate(copied)

            self.assertTrue(
                any("description advertises 999 skills but lists 8" in error for error in errors),
                errors,
            )

    def test_canonical_inventory_count_must_match_manifest(self):
        with tempfile.TemporaryDirectory() as temp_name:
            copied = self.copy_repository(temp_name)
            inventory_path = (
                copied / "skills" / "skill-registry" / "references" / "inventory.md"
            )
            inventory = inventory_path.read_text(encoding="utf-8").replace(
                "| `lss-everything` | 32 |", "| `lss-everything` | 999 |"
            )
            inventory_path.write_text(inventory, encoding="utf-8")

            errors = validate(copied)

            self.assertTrue(
                any(
                    "canonical inventory lists 999 skills for lss-everything" in error
                    for error in errors
                ),
                errors,
            )


if __name__ == "__main__":
    unittest.main()
