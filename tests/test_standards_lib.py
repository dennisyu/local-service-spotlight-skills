"""The standard file format has to fail loudly, never quietly.

Every test here is a way a rule could look enforced while enforcing nothing.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.standards_lib import (
    SCAFFOLD_SENTINEL,
    StandardError,
    load_standards,
    parse_standard,
)


REPOSITORY = Path(__file__).resolve().parents[1]

HEADER = {
    "title": "Example rule",
    "severity": "error",
    "captured": "2026-08-16",
    "captured_from": "Test fixture",
}

REGEX_CHECK = {
    "id": "example-check",
    "kind": "forbid_regex",
    "pattern": "<blink\\b",
    "message": "blink tag",
    "examples": {"violating": ["<blink>hi</blink>"], "clean": ["<b>hi</b>"]},
}


class StandardFileTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def write(self, name: str, header: dict | None, body: str = "## Example\n\n- do it"):
        path = self.dir / name
        if header is None:
            path.write_text(body, encoding="utf-8")
        else:
            path.write_text(
                "---\n" + json.dumps(header, indent=2) + "\n---\n\n" + body,
                encoding="utf-8",
            )
        return path

    # --- the happy paths ---------------------------------------------------

    def test_header_and_body_parse(self):
        standard = parse_standard(self.write("example-rule.md", HEADER))
        self.assertEqual(standard.slug, "example-rule")
        self.assertEqual(standard.title, "Example rule")
        self.assertEqual(standard.captured_from, "Test fixture")
        self.assertFalse(standard.machine_checkable)

    def test_a_file_with_no_header_is_still_a_valid_rule(self):
        """Rules written before the header existed must keep working."""
        standard = parse_standard(self.write("legacy-rule.md", None))
        self.assertEqual(standard.title, "Example")
        self.assertEqual(standard.severity, "error")

    def test_only_the_body_is_embedded_never_the_header(self):
        """Machine configuration must not leak into 27 skills as guidance."""
        header = {**HEADER, "applies_to": ["published-html"], "checks": [REGEX_CHECK]}
        standard = parse_standard(self.write("example-rule.md", header))
        self.assertNotIn("captured_from", standard.block())
        self.assertNotIn("forbid_regex", standard.block())
        self.assertIn("## Example", standard.block())

    # --- the ways a rule can silently do nothing ---------------------------

    def test_scaffold_that_was_never_written_is_rejected(self):
        path = self.write("half-done.md", HEADER, f"## Half done\n\n- {SCAFFOLD_SENTINEL}")
        with self.assertRaises(StandardError) as caught:
            parse_standard(path)
        self.assertIn("still a scaffold", str(caught.exception))

    def test_regex_check_without_examples_is_rejected(self):
        check = {k: v for k, v in REGEX_CHECK.items() if k != "examples"}
        header = {**HEADER, "applies_to": ["published-html"], "checks": [check]}
        with self.assertRaises(StandardError) as caught:
            parse_standard(self.write("example-rule.md", header))
        self.assertIn("examples", str(caught.exception))

    def test_checks_require_the_published_html_scope(self):
        header = {**HEADER, "checks": [REGEX_CHECK]}
        with self.assertRaises(StandardError):
            parse_standard(self.write("example-rule.md", header))

    def test_missing_provenance_is_rejected(self):
        header = {k: v for k, v in HEADER.items() if k != "captured_from"}
        with self.assertRaises(StandardError) as caught:
            parse_standard(self.write("example-rule.md", header))
        self.assertIn("captured_from", str(caught.exception))

    def test_bad_json_names_the_file(self):
        path = self.dir / "broken.md"
        path.write_text('---\n{"title": "x",}\n---\n\n## X\n', encoding="utf-8")
        with self.assertRaises(StandardError) as caught:
            parse_standard(path)
        self.assertIn("broken.md", str(caught.exception))

    def test_unknown_header_field_is_rejected(self):
        with self.assertRaises(StandardError):
            parse_standard(self.write("example-rule.md", {**HEADER, "sevirity": "error"}))

    def test_unknown_check_key_is_rejected(self):
        check = {**REGEX_CHECK, "patern": "typo"}
        header = {**HEADER, "applies_to": ["published-html"], "checks": [check]}
        with self.assertRaises(StandardError):
            parse_standard(self.write("example-rule.md", header))

    def test_bad_severity_and_date_are_rejected(self):
        with self.assertRaises(StandardError):
            parse_standard(self.write("a-rule.md", {**HEADER, "severity": "critical"}))
        with self.assertRaises(StandardError):
            parse_standard(self.write("b-rule.md", {**HEADER, "captured": "16/08/2026"}))

    def test_duplicate_check_ids_are_rejected(self):
        header = {
            **HEADER,
            "applies_to": ["published-html"],
            "checks": [REGEX_CHECK, dict(REGEX_CHECK)],
        }
        with self.assertRaises(StandardError) as caught:
            parse_standard(self.write("example-rule.md", header))
        self.assertIn("duplicate check id", str(caught.exception))

    def test_extractor_must_capture_exactly_one_url(self):
        check = {
            "id": "links",
            "kind": "resolve_urls",
            "extract": "href=\"(https?)://([^\"]+)\"",
            "message": "link",
            "examples": {"extracts": [{"html": "", "urls": []}]},
        }
        header = {**HEADER, "applies_to": ["published-html"], "checks": [check]}
        with self.assertRaises(StandardError) as caught:
            parse_standard(self.write("example-rule.md", header))
        self.assertIn("one capturing group", str(caught.exception))

    def test_bad_regex_names_the_file_and_the_pattern(self):
        check = {**REGEX_CHECK, "pattern": "(unclosed"}
        header = {**HEADER, "applies_to": ["published-html"], "checks": [check]}
        with self.assertRaises(StandardError) as caught:
            parse_standard(self.write("example-rule.md", header))
        self.assertIn("example-rule.md", str(caught.exception))

    def test_filename_must_be_kebab_case(self):
        with self.assertRaises(StandardError):
            parse_standard(self.write("Example_Rule.md", HEADER))


class ScaffolderTests(unittest.TestCase):
    """Capturing a rule must be one command, and a half-captured rule must fail."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_slug_is_derived_from_the_title(self):
        from scripts.new_standard import slugify

        self.assertEqual(slugify("No autoplay with sound!"), "no-autoplay-with-sound")
        self.assertEqual(slugify("  Hero  —  full bleed "), "hero-full-bleed")

    def test_scaffold_is_rejected_until_the_rule_is_written(self):
        from scripts.new_standard import scaffold

        text = scaffold(
            title="No autoplay with sound",
            slug="no-autoplay-with-sound",
            captured_from="Dennis Yu, session, 2026-08-16",
            severity="error",
            applies_to=["published-html"],
            source=None,
            captured="2026-08-16",
        )
        path = self.dir / "no-autoplay-with-sound.md"
        path.write_text(text, encoding="utf-8")

        with self.assertRaises(StandardError):
            parse_standard(path)

        path.write_text(
            text.replace(f"- {SCAFFOLD_SENTINEL}: state the rule in one sentence, "
                         "in the imperative.", "- Nothing autoplays with sound."),
            encoding="utf-8",
        )
        standard = parse_standard(path)
        self.assertEqual(standard.captured_from, "Dennis Yu, session, 2026-08-16")

    def test_scaffold_always_carries_provenance(self):
        from scripts.new_standard import scaffold

        text = scaffold(
            title="Some rule",
            slug="some-rule",
            captured_from="Zoom call, 2026-08-16",
            severity="warn",
            applies_to=["agent-behaviour"],
            source=None,
            captured="2026-08-16",
        )
        self.assertIn("Zoom call, 2026-08-16", text)


class RepositoryStandardsTests(unittest.TestCase):
    """The rules actually shipped in this repository."""

    def setUp(self):
        self.standards = load_standards(REPOSITORY / "standards")

    def test_repository_standards_all_parse(self):
        self.assertGreater(len(self.standards), 1)

    def test_every_rule_records_where_it_came_from(self):
        missing = [s.slug for s in self.standards if not s.captured_from.strip()]
        self.assertEqual(missing, [], "a rule with no provenance cannot be re-checked")

    def test_no_two_rules_share_a_title(self):
        titles = [s.title for s in self.standards]
        self.assertEqual(len(titles), len(set(titles)))

    def test_published_html_rules_carry_at_least_one_check(self):
        """If a rule claims to govern published HTML, the sweep must enforce it
        or the scope is a claim nothing backs."""
        unenforced = [
            s.slug
            for s in self.standards
            if "published-html" in s.applies_to and not s.checks
        ]
        self.assertEqual(unenforced, [])


if __name__ == "__main__":
    unittest.main()
