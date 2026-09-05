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
    skill_scopes,
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

    def write(
        self,
        name: str,
        header: dict | None,
        body: str = "## Example rule\n\n- do it",
    ):
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

    def test_a_file_with_no_header_cannot_silently_disable_enforcement(self):
        with self.assertRaises(StandardError):
            parse_standard(self.write("legacy-rule.md", None))

    def test_only_the_body_is_embedded_never_the_header(self):
        """Machine configuration must not leak into every skill as guidance."""
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

    def test_duplicate_json_members_are_rejected_at_every_depth(self):
        for raw_header in (
            '{"title":"One","title":"Two"}',
            '{"title":"One","checks":[{"id":"x","id":"y"}]}',
        ):
            with self.subTest(raw_header=raw_header):
                path = self.dir / "example-rule.md"
                path.write_text(
                    f"---\n{raw_header}\n---\n\n## One\n\n- do it\n",
                    encoding="utf-8",
                )
                with self.assertRaises(StandardError) as caught:
                    parse_standard(path)
                self.assertIn("duplicate JSON member", str(caught.exception))

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
        with self.assertRaises(StandardError):
            parse_standard(self.write("c-rule.md", {**HEADER, "captured": "2026-02-30"}))
        with self.assertRaises(StandardError):
            parse_standard(self.write("d-rule.md", {**HEADER, "captured": "2099-01-01"}))

    def test_public_metadata_rejects_private_values_and_nonpublic_sources(self):
        for captured_from in (
            "alice@example.com",
            "/Users/alice/private.json",
            "$PWD/private.json",
            "Private prompt: secret",
            "ghp_abcdefghijklmnopqrstuvwxyz",
        ):
            with self.subTest(captured_from=captured_from), self.assertRaises(StandardError):
                parse_standard(
                    self.write(
                        "example-rule.md",
                        {**HEADER, "captured_from": captured_from},
                    )
                )
        for source in (
            "https://localhost/rule",
            "https://127.0.0.1/rule",
            "https://10.0.0.1/rule",
            "https://internal.corp/rule",
            "https://example.test/rule?token=secret",
            "https://example.test/rule#private",
            "https://hooks.slack.com/services/T/B/secret",
        ):
            with self.subTest(source=source), self.assertRaises(StandardError):
                parse_standard(
                    self.write("example-rule.md", {**HEADER, "source": source})
                )

    def test_header_field_types_title_and_source_fail_closed(self):
        for field, value in (
            ("title", True),
            ("title", ["Example rule"]),
            ("captured", True),
            ("captured", []),
            ("captured_from", None),
            ("captured_from", 1),
            ("source", True),
            ("source", "http://example.test/rule"),
            ("source", "https://example.test:443/rule"),
            ("applies_to", ["agent-behaviour", "agent-behaviour"]),
        ):
            with self.subTest(field=field, value=value), self.assertRaises(StandardError):
                parse_standard(self.write("example-rule.md", {**HEADER, field: value}))

        with self.assertRaises(StandardError):
            parse_standard(
                self.write("example-rule.md", HEADER, "## A different title\n\n- do it")
            )

    def test_json_constants_bom_crlf_and_invalid_utf8_are_rejected(self):
        for constant in ("NaN", "Infinity", "-Infinity"):
            path = self.dir / "constant.md"
            path.write_text(
                '---\n{"title":"Example rule","severity":"error",'
                '"captured":"2026-08-16","captured_from":' + constant + '}'
                '\n---\n\n## Example rule\n',
                encoding="utf-8",
            )
            with self.subTest(constant=constant), self.assertRaises(StandardError):
                parse_standard(path)
        for raw in (
            b"\xef\xbb\xbf---\n{}\n---\n\n## Example\n",
            b"---\r\n{}\r\n---\r\n\r\n## Example\r\n",
            b"---\n\xff\n---\n\n## Example\n",
        ):
            path = self.dir / "encoding.md"
            path.write_bytes(raw)
            with self.subTest(raw=raw[:8]), self.assertRaises(StandardError):
                parse_standard(path)

    def test_http_status_and_limit_fields_reject_boolean_lookalikes(self):
        for overrides in (
            {"allow_status": [True, 200]},
            {"allow_status": [200, 200]},
            {"allow_status": [99]},
            {"limit": True},
        ):
            check = {
                "id": "links",
                "kind": "resolve_urls",
                "extract": 'href="(https?://[^\"]+)"',
                "message": "link",
                "examples": {"extracts": [{"html": "", "urls": []}]},
                **overrides,
            }
            header = {**HEADER, "applies_to": ["published-html"], "checks": [check]}
            with self.subTest(overrides=overrides), self.assertRaises(StandardError):
                parse_standard(self.write("example-rule.md", header))

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

    def test_structural_contract_requires_both_example_classes(self):
        check = {
            "id": "provenance",
            "kind": "provenance_contract",
            "message": "bad provenance",
            "examples": {"violating": ["<p>none</p>"]},
        }
        header = {**HEADER, "applies_to": ["published-html"], "checks": [check]}
        with self.assertRaises(StandardError) as caught:
            parse_standard(self.write("example-rule.md", header))
        self.assertIn("examples.clean", str(caught.exception))

    def test_structural_contract_rejects_misleading_regex_options(self):
        check = {
            "id": "provenance",
            "kind": "provenance_contract",
            "pattern": "anything",
            "message": "bad provenance",
            "examples": {"violating": ["<p>none</p>"], "clean": ["<aside></aside>"]},
        }
        header = {**HEADER, "applies_to": ["published-html"], "checks": [check]}
        with self.assertRaises(StandardError) as caught:
            parse_standard(self.write("example-rule.md", header))
        self.assertIn("has no regex", str(caught.exception))

    def test_filename_must_be_kebab_case(self):
        with self.assertRaises(StandardError):
            parse_standard(self.write("Example_Rule.md", HEADER))

    def test_skill_scope_declaration_is_unique_nonblank_and_column_zero(self):
        for frontmatter in (
            "rule-scopes:\nrule-scopes: published-html, design-review",
            "rule-scopes: published-html\nrule-scopes: design-review",
            "rule-scopes:   ",
            "  rule-scopes: published-html",
            "rule-scopes : published-html",
            "Rule-Scopes: published-html",
            "RULE-SCOPES: published-html",
            "rule_scopes: published-html",
            "rules-scopes: published-html",
            "rule-scope: published-html",
            "rule-Scopes: published-html",
            "ｒｕｌｅ-scopes: published-html",
            "rule-ｓｃｏｐｅｓ: published-html",
        ):
            with self.subTest(frontmatter=frontmatter):
                skill = self.dir / "SKILL.md"
                skill.write_text(
                    f"---\nname: fixture\n{frontmatter}\n---\n\n# Fixture\n",
                    encoding="utf-8",
                )
                with self.assertRaises(StandardError):
                    skill_scopes(skill)

        skill = self.dir / "SKILL.md"
        skill.write_text(
            "---\nname: fixture\nrule-scopes: published-html, design-review\n"
            "---\n\n# Fixture\n",
            encoding="utf-8",
        )
        self.assertEqual(
            skill_scopes(skill), {"published-html", "design-review"}
        )

        skill.write_text(
            "---\nname: fixture\n---\n\n# Fixture\n", encoding="utf-8"
        )
        with self.assertRaises(StandardError):
            skill_scopes(skill)

    def test_skill_scope_frontmatter_cannot_disappear_through_encoding_or_delimiters(self):
        malformed = (
            "\ufeff---\nname: fixture\nrule-scopes: published-html\n---\n",
            "---\r\nname: fixture\r\nrule-scopes: published-html\r\n---\r\n",
            "name: fixture\nrule-scopes: published-html\n",
            "---\nname: fixture\nrule-scopes: published-html\n",
        )
        for text in malformed:
            with self.subTest(text=repr(text[:20])):
                skill = self.dir / "SKILL.md"
                skill.write_bytes(text.encode("utf-8"))
                with self.assertRaises(StandardError):
                    skill_scopes(skill)


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

    def test_published_scaffold_teaches_every_supported_check_shape(self):
        from scripts.new_standard import scaffold

        text = scaffold(
            title="Published rule",
            slug="published-rule",
            captured_from="Test fixture",
            severity="error",
            applies_to=["published-html"],
            source=None,
            captured="2026-08-16",
        )
        for expected in (
            "forbid_regex",
            "require_regex",
            "resolve_urls",
            "require_paths",
            "provenance_contract",
            "examples.extracts",
            "examples.builds",
        ):
            self.assertIn(expected, text)


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
