"""The sweep is only worth running if it can fail.

The failure mode these tests exist for: a check that matches nothing, reports
every site clean, and is therefore indistinguishable from having no rule at all.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import fleet_check
from scripts.standards_lib import load_standards, parse_standard


REPOSITORY = Path(__file__).resolve().parents[1]

HEADER = {
    "title": "Example rule",
    "severity": "error",
    "captured": "2026-08-16",
    "captured_from": "Test fixture",
    "applies_to": ["published-html"],
}


def build(checks: list[dict], directory: Path, name: str = "example-rule.md"):
    path = directory / name
    path.write_text(
        "---\n"
        + json.dumps({**HEADER, "checks": checks}, indent=2)
        + "\n---\n\n## Example\n\n- do it\n",
        encoding="utf-8",
    )
    return parse_standard(path)


class RegexCheckTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_forbid_regex_reports_a_match(self):
        standard = build(
            [
                {
                    "id": "no-blink",
                    "kind": "forbid_regex",
                    "pattern": "<blink\\b",
                    "message": "blink tag",
                    "examples": {"violating": ["<blink>"], "clean": ["<b>"]},
                }
            ],
            self.dir,
        )
        found = fleet_check.run_check(
            standard.checks[0], "https://x.test/", "<p><blink>hi</blink></p>", "error"
        )
        self.assertEqual(len(found), 1)
        self.assertTrue(found[0].blocking)
        self.assertIn("blink", found[0].detail)

    def test_forbid_regex_caps_the_noise_but_reports_the_total(self):
        standard = build(
            [
                {
                    "id": "no-blink",
                    "kind": "forbid_regex",
                    "pattern": "<blink\\b",
                    "message": "blink tag",
                    "examples": {"violating": ["<blink>"], "clean": ["<b>"]},
                }
            ],
            self.dir,
        )
        found = fleet_check.run_check(
            standard.checks[0], "https://x.test/", "<blink>" * 9, "error"
        )
        self.assertEqual(len(found), 6)
        self.assertIn("and 4 more", found[-1].detail)

    def test_a_marked_exemption_is_honoured_but_only_nearby(self):
        standard = build(
            [
                {
                    "id": "no-black",
                    "kind": "forbid_regex",
                    "pattern": "background:#000",
                    "exempt_if_near": "bm-allow-black",
                    "message": "black fill",
                    "examples": {
                        "violating": ["background:#000"],
                        "clean": ["background:#fff"],
                    },
                }
            ],
            self.dir,
        )
        check = standard.checks[0]

        near = '<a class="bm-allow-black" style="background:#000">logo</a>'
        self.assertEqual(fleet_check.run_check(check, "u", near, "error"), [])

        far = 'bm-allow-black' + ("x" * 400) + 'style="background:#000"'
        self.assertEqual(len(fleet_check.run_check(check, "u", far, "error")), 1)

    def test_require_regex_reports_absence(self):
        standard = build(
            [
                {
                    "id": "needs-hero",
                    "kind": "require_regex",
                    "pattern": "height:\\d+svh",
                    "message": "no full-height hero",
                    "examples": {
                        "violating": ["<div></div>"],
                        "clean": ["<div style=\"height:94svh\"></div>"],
                    },
                }
            ],
            self.dir,
        )
        check = standard.checks[0]
        self.assertEqual(len(fleet_check.run_check(check, "u", "<div></div>", "warn")), 1)
        self.assertEqual(
            fleet_check.run_check(check, "u", 'style="height:94svh"', "warn"), []
        )


class UrlExtractionTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def check(self, **overrides):
        base = {
            "id": "links",
            "kind": "resolve_urls",
            "extract": "href=\"(https?://[^\"]+)\"",
            "message": "dead link",
            "examples": {"extracts": [{"html": "", "urls": []}]},
        }
        return build([{**base, **overrides}], self.dir).checks[0]

    def test_within_narrows_the_document(self):
        check = self.check(
            within='"sameAs"\\s*:\\s*\\[[^\\]]*\\]',
            extract='"(https?://[^"]+)"',
        )
        body = (
            '<a href="https://ignore.test/">x</a>'
            '{"sameAs":["https://a.test/1","https://b.test/2"],"url":"https://skip.test/"}'
        )
        self.assertEqual(
            fleet_check.extract_urls(check, body),
            ["https://a.test/1", "https://b.test/2"],
        )

    def test_escaped_json_ld_slashes_are_normalised(self):
        """Rank Math emits sameAs as https:\\/\\/… — the naive extractor misses it."""
        check = self.check(
            within='"sameAs"\\s*:\\s*\\[[^\\]]*\\]',
            extract='"(https?://[^"]+)"',
        )
        body = '{"sameAs":["https:\\/\\/www.wikidata.org\\/wiki\\/Q1"]}'
        self.assertEqual(
            fleet_check.extract_urls(check, body),
            ["https://www.wikidata.org/wiki/Q1"],
        )

    def test_duplicates_collapse(self):
        check = self.check()
        body = '<a href="https://a.test/">1</a><a href="https://a.test/">2</a>'
        self.assertEqual(fleet_check.extract_urls(check, body), ["https://a.test/"])

    def test_same_host_links_can_be_skipped_without_any_request(self):
        check = self.check(skip_same_host=True)
        body = '<a href="https://site.test/about/">About</a>'
        self.assertEqual(
            fleet_check.run_resolve_check(check, "https://site.test/", body, "error"),
            [],
        )

    def test_truncation_is_reported_rather_than_silent(self):
        """A sweep that quietly stops at N reads as 'all clear'."""
        check = self.check(limit=1)
        body = '<a href="https://a.test/">1</a><a href="https://b.test/">2</a>'
        original = fleet_check.status_of
        fleet_check.status_of = lambda url: (200, "")
        try:
            found = fleet_check.run_resolve_check(
                check, "https://site.test/", body, "error", pause=0
            )
        finally:
            fleet_check.status_of = original
        self.assertEqual(len(found), 1)
        self.assertIn("were NOT checked", found[0].detail)

    def test_a_dead_link_is_reported_with_its_status(self):
        check = self.check()
        body = '<a href="https://gone.test/">x</a>'
        original = fleet_check.status_of
        fleet_check.status_of = lambda url: (404, "")
        try:
            found = fleet_check.run_resolve_check(
                check, "https://site.test/", body, "error", pause=0
            )
        finally:
            fleet_check.status_of = original
        self.assertEqual(len(found), 1)
        self.assertIn("HTTP 404", found[0].detail)


class SelfTestTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_a_pattern_that_matches_nothing_is_caught(self):
        standard = build(
            [
                {
                    "id": "broken",
                    "kind": "forbid_regex",
                    "pattern": "this-string-is-not-in-the-sample",
                    "message": "broken check",
                    "examples": {"violating": ["<blink>"], "clean": ["<b>"]},
                }
            ],
            self.dir,
        )
        problems = fleet_check.self_test([standard])
        self.assertEqual(len(problems), 1)
        self.assertIn("did NOT flag", problems[0])

    def test_a_pattern_that_cries_wolf_is_caught(self):
        standard = build(
            [
                {
                    "id": "greedy",
                    "kind": "forbid_regex",
                    "pattern": "div",
                    "message": "too broad",
                    "examples": {"violating": ["<div>"], "clean": ["<div>fine</div>"]},
                }
            ],
            self.dir,
        )
        problems = fleet_check.self_test([standard])
        self.assertEqual(len(problems), 1)
        self.assertIn("falsely flagged", problems[0])

    def test_every_shipped_rule_proves_its_own_patterns(self):
        """The integration test that matters: run the real standards."""
        problems = fleet_check.self_test(load_standards(REPOSITORY / "standards"))
        self.assertEqual(problems, [])


class TargetFileTests(unittest.TestCase):
    def read(self, text: str):
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "fleet.txt"
            path.write_text(text, encoding="utf-8")
            return fleet_check.read_targets(path)

    def test_comments_and_blanks_are_ignored(self):
        self.assertEqual(
            self.read("# the fleet\n\nhttps://a.test/\n  https://b.test/  \n"),
            [("https://a.test/", ()), ("https://b.test/", ())],
        )

    def test_tags_are_read_from_the_line(self):
        self.assertEqual(
            self.read("https://a.test/   personal-brand,client\n"),
            [("https://a.test/", ("personal-brand", "client"))],
        )


class TargetScopingTests(unittest.TestCase):
    """A rule that fires everywhere gets ignored everywhere."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_untagged_rules_apply_to_every_page(self):
        standard = build([], self.dir)
        self.assertTrue(fleet_check.applies_to_target(standard, ()))
        self.assertTrue(fleet_check.applies_to_target(standard, ("company",)))

    def test_a_tagged_rule_only_applies_to_matching_pages(self):
        path = self.dir / "scoped-rule.md"
        path.write_text(
            "---\n"
            + json.dumps({**HEADER, "target_tags": ["personal-brand"], "checks": []})
            + "\n---\n\n## Scoped\n\n- only personal brand sites\n",
            encoding="utf-8",
        )
        standard = parse_standard(path)
        self.assertTrue(fleet_check.applies_to_target(standard, ("personal-brand",)))
        self.assertFalse(fleet_check.applies_to_target(standard, ("company",)))
        self.assertFalse(fleet_check.applies_to_target(standard, ()))


if __name__ == "__main__":
    unittest.main()


class RequirePathsTests(unittest.TestCase):
    """The only check that can catch a URL nothing on the site links to."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def check(self, **overrides):
        base = {
            "id": "short-paths",
            "kind": "require_paths",
            "paths": ["/install/", "/skills/"],
            "message": "spoken path is dead",
            "examples": {"builds": [{"target": "https://x.test/", "urls": []}]},
        }
        return build([{**base, **overrides}], self.dir).checks[0]

    def test_paths_join_onto_the_target_origin_not_its_path(self):
        check = self.check()
        self.assertEqual(
            fleet_check.build_paths(check, "https://site.test/deep/page/?a=1"),
            ["https://site.test/install/", "https://site.test/skills/"],
        )

    def test_a_dead_spoken_path_is_reported(self):
        check = self.check()
        original = fleet_check.status_of
        fleet_check.status_of = lambda url: (404, "") if "skills" in url else (200, "")
        try:
            found = fleet_check.run_paths_check(
                check, "https://site.test/", "error", pause=0
            )
        finally:
            fleet_check.status_of = original
        self.assertEqual(len(found), 1)
        self.assertIn("/skills/", found[0].detail)
        self.assertIn("HTTP 404", found[0].detail)

    def test_a_redirect_counts_as_resolving(self):
        check = self.check()
        original = fleet_check.status_of
        fleet_check.status_of = lambda url: (301, "")
        try:
            found = fleet_check.run_paths_check(
                check, "https://site.test/", "error", pause=0
            )
        finally:
            fleet_check.status_of = original
        self.assertEqual(found, [])

    def test_relative_paths_are_rejected_at_parse_time(self):
        from scripts.standards_lib import StandardError

        with self.assertRaises(StandardError):
            self.check(paths=["install/"])

    def test_builds_examples_are_required(self):
        from scripts.standards_lib import StandardError

        with self.assertRaises(StandardError):
            self.check(examples={})
