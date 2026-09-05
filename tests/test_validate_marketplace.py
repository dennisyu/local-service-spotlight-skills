import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.validate_marketplace import validate


REPOSITORY = Path(__file__).resolve().parents[1]


class MarketplaceValidatorTests(unittest.TestCase):
    def test_current_repository_passes(self):
        self.assertEqual(validate(REPOSITORY), [])

    def test_unsafe_readme_is_reported_without_following_or_reading_it(self):
        with tempfile.TemporaryDirectory() as temp_name:
            copied = Path(temp_name) / "repository"
            shutil.copytree(REPOSITORY, copied, ignore=shutil.ignore_patterns(".git"))
            readme = copied / "README.md"
            readme.unlink()
            readme.symlink_to(copied / "missing-private-host-file")
            errors = validate(copied)
            self.assertTrue(any("README.md" in error for error in errors), errors)
            self.assertTrue(any("non-symlink" in error for error in errors), errors)

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

    def test_stale_bundle_count_fails(self):
        with tempfile.TemporaryDirectory() as temp_name:
            copied = Path(temp_name) / "repository"
            shutil.copytree(REPOSITORY, copied, ignore=shutil.ignore_patterns(".git"))
            manifest_path = copied / ".claude-plugin" / "marketplace.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["plugins"][0]["description"] = (
                "Everything we use, in one install — all 27 Local Service "
                "Spotlight skills."
            )
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            errors = validate(copied)

            self.assertIn(
                "plugin 'lss-everything' advertises 27 skills but lists 31",
                errors,
            )

    def test_stale_count_is_caught_without_all_or_parentheses_wording(self):
        with tempfile.TemporaryDirectory() as temp_name:
            copied = Path(temp_name) / "repository"
            shutil.copytree(REPOSITORY, copied, ignore=shutil.ignore_patterns(".git"))
            manifest_path = copied / ".claude-plugin" / "marketplace.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["plugins"][0]["description"] = (
                "The bundle includes 30 marketplace skills for members."
            )
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            errors = validate(copied)

            self.assertIn(
                "plugin 'lss-everything' advertises 30 skills but lists 31",
                errors,
            )

    def test_every_manifest_count_claim_is_checked(self):
        with tempfile.TemporaryDirectory() as temp_name:
            copied = Path(temp_name) / "repository"
            shutil.copytree(REPOSITORY, copied, ignore=shutil.ignore_patterns(".git"))
            manifest_path = copied / ".claude-plugin" / "marketplace.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["plugins"][0]["description"] = (
                "Current: 31 skills. A stale sentence still says 30 skills."
            )
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            errors = validate(copied)

            self.assertIn(
                "plugin 'lss-everything' advertises 30 skills but lists 31",
                errors,
            )

    def test_word_and_parenthesized_counts_are_checked(self):
        for description in (
            "Everything in one place (thirty marketplace skills).",
            "The marketplace skills (30) are bundled here.",
            "A 30-skill marketplace for members.",
            "A thirty-skill marketplace for members.",
            "Includes 30+ skills for members.",
        ):
            with self.subTest(description=description), tempfile.TemporaryDirectory() as temp_name:
                copied = Path(temp_name) / "repository"
                shutil.copytree(
                    REPOSITORY, copied, ignore=shutil.ignore_patterns(".git")
                )
                manifest_path = copied / ".claude-plugin" / "marketplace.json"
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest["plugins"][0]["description"] = description
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

                errors = validate(copied)

                self.assertIn(
                    "plugin 'lss-everything' advertises 30 skills but lists 31",
                    errors,
                )

    def test_unrelated_numbers_before_practical_skills_are_not_counts(self):
        with tempfile.TemporaryDirectory() as temp_name:
            copied = Path(temp_name) / "repository"
            shutil.copytree(REPOSITORY, copied, ignore=shutil.ignore_patterns(".git"))
            manifest_path = copied / ".claude-plugin" / "marketplace.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["plugins"][0]["description"] = (
                "Built from 10 years teaching practical skills to business owners."
            )
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            errors = validate(copied)

            self.assertFalse(any("advertises 10 skills" in error for error in errors), errors)

    def test_readme_cannot_reintroduce_a_remembered_skill_count(self):
        with tempfile.TemporaryDirectory() as temp_name:
            copied = Path(temp_name) / "repository"
            shutil.copytree(REPOSITORY, copied, ignore=shutil.ignore_patterns(".git"))
            readme = copied / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8")
                + "\nThe public bundle contains 31 released skills.\n",
                encoding="utf-8",
            )

            errors = validate(copied)

            self.assertTrue(
                any("README hard-codes a derived skill count" in error for error in errors),
                errors,
            )

    def test_readme_count_guard_covers_marketplace_and_suffix_forms(self):
        for claim in (
            "31 marketplace skills",
            "skills (31)",
            "thirty-one skills",
            "31-skill marketplace",
            "thirty-one-skill marketplace",
            "31+ skills",
            "thirty-one `SKILL.md` files",
            "31+ `SKILL.md` files",
            "31 bundled `SKILL.md` files",
            "Our suite contains 27 different skills",
            "catalog has 27 unique skills",
            "27 individually installable skills",
            "Twenty-seven distinct skills",
            "skills total 27",
            "Skill count: 27",
            "The number of skills is 27",
            "27 installable skills",
            "27 separately installable skills",
            "27 downloadable skills",
            "27 separate, individually installable skills",
            "27 agent skills",
            "27 professional skills",
            "27 public skills",
            "Skills currently number 27",
            "Our skills number 27",
            "27 highly practical skills",
            "27 core skills",
            "skills — 27",
            "skills: **27**",
            "Skill count is 27",
            "27 [skills](#skills)",
            "27 [marketplace skills](https://example.test/skills)",
            "<strong>27</strong> skills",
            "27&nbsp;skills",
            "27 <em>skills</em>",
            "27 LSS skills",
            "27 best-in-class skills",
            "| Skill count | 27 |",
            "The skill catalog has 27 entries",
            "27 entries in the skill catalog",
            "Skill catalog size: 27",
            "All 27 are individually installable skills",
            "skills × 27",
            "27 × skills",
        ):
            with self.subTest(claim=claim), tempfile.TemporaryDirectory() as temp_name:
                copied = Path(temp_name) / "repository"
                shutil.copytree(
                    REPOSITORY, copied, ignore=shutil.ignore_patterns(".git")
                )
                readme = copied / "README.md"
                readme.write_text(
                    readme.read_text(encoding="utf-8") + f"\nContains {claim}.\n",
                    encoding="utf-8",
                )

                errors = validate(copied)

                self.assertTrue(
                    any("README hard-codes a derived skill count" in error for error in errors),
                    errors,
                )

    def test_readme_cannot_reintroduce_a_remembered_bundle_count(self):
        for claim in (
            "five bundles",
            "5 bundles",
            "bundles (5)",
            "five-bundle marketplace",
            "5-bundle marketplace",
            "5+ bundles",
            "Five curated bundles",
            "five separate bundles",
            "Five packs of skills",
            "Bundle count: 5",
            "The number of bundles is five",
            "five plugin bundles",
            "five skill packs",
            "five plugin packs",
            "five collections of skills",
            "5 topic bundles",
            "5 topical plugin bundles",
            "Bundles currently number five",
            "five core bundles",
            "bundles — five",
            "bundles: **5**",
            "Bundle count is five",
            "five skill collections",
            "five groups of skills",
            "five [bundles](#bundles)",
            "<strong>five</strong> bundles",
            "five&nbsp;bundles",
            "five LSS bundles",
            "27-pack marketplace",
            "five-pack marketplace",
            "5-packs of skills",
            "five-collection marketplace",
            "5-collections of skills",
        ):
            with self.subTest(claim=claim), tempfile.TemporaryDirectory() as temp_name:
                copied = Path(temp_name) / "repository"
                shutil.copytree(
                    REPOSITORY, copied, ignore=shutil.ignore_patterns(".git")
                )
                readme = copied / "README.md"
                readme.write_text(
                    readme.read_text(encoding="utf-8") + f"\nIncludes {claim}.\n",
                    encoding="utf-8",
                )

                errors = validate(copied)

                self.assertTrue(
                    any("README hard-codes a derived bundle count" in error for error in errors),
                    errors,
                )

    def test_readme_action_or_subset_counts_are_not_catalog_totals(self):
        claims = (
            "Install 2 skills",
            "Choose 3 skills for this task",
            "Use one skill at a time",
            "The example combines 2 skills",
            "Complete five skills this week",
            "A plugin may include 5 skills",
            "Install 2 bundles",
            "Choose one bundle",
            "This agent needs 3 practical skills",
            "Compare 2 different skills",
            "Review five bundles",
            "The task uses 2 skills",
            "Learn 3 skills",
            "We tested 3 skills together",
            "Three skills failed validation",
            "Two skills are prerequisites",
            "Complete quizzes for 2 skills",
            "The first 2 skills are optional",
            "Pick from 2 skills",
            "No more than 2 skills per task",
        )
        for claim in claims:
            with self.subTest(claim=claim), tempfile.TemporaryDirectory() as temp_name:
                copied = Path(temp_name) / "repository"
                shutil.copytree(
                    REPOSITORY, copied, ignore=shutil.ignore_patterns(".git")
                )
                readme = copied / "README.md"
                readme.write_text(
                    readme.read_text(encoding="utf-8") + f"\n{claim}.\n",
                    encoding="utf-8",
                )
                errors = validate(copied)
                self.assertFalse(
                    any("README hard-codes a derived" in error for error in errors),
                    errors,
                )

    def test_non_object_manifest_fails_without_crashing(self):
        with tempfile.TemporaryDirectory() as temp_name:
            copied = Path(temp_name) / "repository"
            shutil.copytree(REPOSITORY, copied, ignore=shutil.ignore_patterns(".git"))
            manifest_path = copied / ".claude-plugin" / "marketplace.json"
            manifest_path.write_text("[]\n", encoding="utf-8")

            self.assertEqual(
                validate(copied),
                ["marketplace.json must contain a JSON object"],
            )

    def test_duplicate_marketplace_json_members_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp_name:
            copied = Path(temp_name) / "repository"
            shutil.copytree(REPOSITORY, copied, ignore=shutil.ignore_patterns(".git"))
            manifest_path = copied / ".claude-plugin" / "marketplace.json"
            original = manifest_path.read_text(encoding="utf-8")
            manifest_path.write_text(
                original.replace('"plugins": [', '"plugins": [], "plugins": [', 1),
                encoding="utf-8",
            )

            errors = validate(copied)

        self.assertEqual(len(errors), 1)
        self.assertIn("duplicate JSON member 'plugins'", errors[0])

    def test_non_json_numeric_constants_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp_name:
            copied = Path(temp_name) / "repository"
            shutil.copytree(REPOSITORY, copied, ignore=shutil.ignore_patterns(".git"))
            manifest_path = copied / ".claude-plugin" / "marketplace.json"
            manifest_path.write_text('{"plugins":NaN}\n', encoding="utf-8")
            errors = validate(copied)
        self.assertEqual(len(errors), 1)
        self.assertIn("non-JSON numeric constant", errors[0])

    def test_skill_reference_cannot_traverse_or_follow_a_symlink(self):
        with tempfile.TemporaryDirectory() as temp_name:
            copied = Path(temp_name) / "repository"
            shutil.copytree(REPOSITORY, copied, ignore=shutil.ignore_patterns(".git"))
            manifest_path = copied / ".claude-plugin" / "marketplace.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["plugins"][1]["skills"][0] = "./skills/../standards"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            errors = validate(copied)
            self.assertTrue(any("invalid skill path" in error for error in errors), errors)

            target = copied / "skills" / "seo-audit"
            shutil.rmtree(target)
            target.symlink_to(copied / "skills" / "content-agent", target_is_directory=True)
            errors = validate(copied)
            self.assertTrue(any("skills/seo-audit" in error for error in errors), errors)

    def test_markdown_local_reference_cannot_escape_or_follow_a_symlink(self):
        with tempfile.TemporaryDirectory() as temp_name:
            copied = Path(temp_name) / "repository"
            shutil.copytree(REPOSITORY, copied, ignore=shutil.ignore_patterns(".git"))
            skill = copied / "skills" / "content-agent"
            text = skill / "SKILL.md"
            text.write_text(
                text.read_text(encoding="utf-8")
                + "\nUnsafe references/../../AGENTS.md\n",
                encoding="utf-8",
            )
            errors = validate(copied)
            self.assertTrue(any("references/../../AGENTS.md" in error for error in errors), errors)

            link = skill / "references" / "outside.md"
            link.parent.mkdir(exist_ok=True)
            link.symlink_to(copied / "AGENTS.md")
            text.write_text(
                text.read_text(encoding="utf-8") + "\nUnsafe references/outside.md\n",
                encoding="utf-8",
            )
            errors = validate(copied)
            self.assertTrue(any("references/outside.md" in error for error in errors), errors)

    def test_unhashable_skill_entries_are_reported_not_raised(self):
        for malformed in ({"path": "./skills/seo-audit"}, ["./skills/seo-audit"]):
            with self.subTest(malformed=malformed), tempfile.TemporaryDirectory() as temp_name:
                copied = Path(temp_name) / "repository"
                shutil.copytree(
                    REPOSITORY, copied, ignore=shutil.ignore_patterns(".git")
                )
                manifest_path = copied / ".claude-plugin" / "marketplace.json"
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest["plugins"][0]["skills"][0] = malformed
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

                errors = validate(copied)

                self.assertTrue(
                    any("skills[0] must be a string path" in error for error in errors),
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
        from an applicable distributed skill and still pass."""
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


if __name__ == "__main__":
    unittest.main()
