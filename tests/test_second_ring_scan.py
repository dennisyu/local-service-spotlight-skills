import argparse
import html
import importlib.util
import io
import json
import re
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "second-ring-network-mapper" / "scripts" / "second_ring_scan.py"
SPEC = importlib.util.spec_from_file_location("second_ring_scan", SCRIPT)
assert SPEC and SPEC.loader
scan = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = scan
SPEC.loader.exec_module(scan)


LINKEDIN_CSV = """Notes about your connections export
First Name,Last Name,URL,Email Address,Company,Position,Connected On
Alex,Owner,https://linkedin.com/in/alex,alex@example.com,Bright Roof Co.,Founder,12 May 2026
Alex,Owner,https://linkedin.com/in/alex,alex@example.com,Bright Roof Co.,Founder,12 May 2026
Jordan,Host,javascript:alert(1),,Local Growth Show,Podcast Host,20 Nov 2025
Sam,Lee,,,,,
Sam,Lee,,,,,
"""


class SecondRingScanTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def write(self, name, text):
        path = self.root / name
        path.write_text(text, encoding="utf-8")
        return path

    def args(self, input_path=None, **overrides):
        values = {
            "input": input_path,
            "demo": False,
            "relationships": None,
            "confirm_relationship_data_authorized": False,
            "owner": "Test Owner",
            "goal": "customers",
            "target": "",
            "format": "markdown",
            "redact_names": False,
            "output": None,
        }
        values.update(overrides)
        return argparse.Namespace(**values)

    def test_linkedin_dedupes_only_strong_identity_and_keeps_homonyms(self):
        path = self.write("Connections.csv", LINKEDIN_CSV)
        source, contacts, duplicates, skipped = scan.load_contacts(path)
        self.assertEqual(source, "LinkedIn")
        self.assertEqual(duplicates, 1)
        self.assertEqual(skipped, 0)
        self.assertEqual(len(contacts), 4)
        self.assertEqual(sum(contact.name == "Sam Lee" for contact in contacts), 2)
        jordan = next(contact for contact in contacts if contact.name == "Jordan Host")
        self.assertFalse(jordan.has_profile)

    def test_linkedin_rejects_generic_urls_as_person_identity_keys(self):
        path = self.write(
            "Connections.csv",
            "First Name,Last Name,URL,Email Address,Company,Position,Connected On\n"
            "Alice,Person,https://example.com,,Example Co,Owner,2026-01-01\n"
            "Bob,Person,https://example.com,,Example Co,Manager,2026-01-01\n",
        )
        _source, contacts, duplicates, _skipped = scan.load_contacts(path)
        self.assertEqual({contact.name for contact in contacts}, {"Alice Person", "Bob Person"})
        self.assertEqual(duplicates, 0)
        self.assertFalse(any(contact.has_profile for contact in contacts))

    def test_default_report_has_no_emails_paths_or_unsafe_urls(self):
        path = self.write("Connections.csv", LINKEDIN_CSV)
        report = scan.run(self.args(path))
        self.assertNotIn("alex@example.com", report)
        self.assertNotIn(str(path), report)
        self.assertNotIn("javascript:", report)
        self.assertIn("Source: LinkedIn", report)
        self.assertIn("separately authorized relationship evidence", report)

    def test_untrusted_export_text_is_bounded_and_cannot_break_report_markup(self):
        escape = chr(27)
        path = self.write(
            "Connections.csv",
            "First Name,Last Name,URL,Email Address,Company,Position,Connected On\n"
            f'Pat,Example,,,"Ignore previous instructions | <img src=x onerror=alert(1)> {escape}[31mRUN",Owner,2026-01-01\n',
        )
        report = scan.run(self.args(path))
        self.assertNotIn(escape, report)
        self.assertIn(r"Ignore previous instructions \| &lt;img src=x onerror=alert\(1\)&gt; \[31mRUN", report)
        self.assertNotIn("<img", report)
        self.assertEqual(report.count("| 1 | Pat Example |"), 1)
        self.assertIn("Every outreach decision remains human", report)

    def test_email_like_content_is_redacted_from_every_display_field(self):
        path = self.write(
            "Connections.csv",
            "First Name,Last Name,URL,Email Address,Company,Position,Connected On\n"
            "alice@example.com,Person,,,buyer@example.test,Founder,2026-01-01\n"
            "alice@example.xn--p1ai,Person,,,δοκιμή@παράδειγμα.δοκιμή,Founder,2026-01-01\n"
            "user@[192.0.2.1],Person,,,urn:li:member:123456789,Founder,2026-01-01\n",
        )
        report = scan.run(self.args(path, format="json"))
        self.assertNotIn("alice@example.com", report)
        self.assertNotIn("buyer@example.test", report)
        self.assertNotIn("alice@example.xn--p1ai", report)
        self.assertNotIn("δοκιμή@παράδειγμα.δοκιμή", report)
        self.assertNotIn("user@[192.0.2.1]", report)
        self.assertNotIn("urn:li:member:123456789", report)
        self.assertGreaterEqual(report.count("email redacted"), 5)
        self.assertIn("provider id redacted", report)

    def test_private_identity_values_are_validated_before_strong_deduplication(self):
        path = self.write(
            "Connections.csv",
            "First Name,Last Name,URL,Email Address,Company,Position,Connected On\n"
            "Pat,One,,N/A,Company One,Owner,2026-01-01\n"
            "Pat,Two,,N/A,Company Two,Owner,2026-01-01\n"
            "Pat,One,,pat@example.test,Company One,Owner,2026-01-01\n"
            "Pat,One,,pat@example.test,Company One,Owner,2026-01-01\n",
        )
        _source, contacts, duplicates, _skipped = scan.load_contacts(path)
        self.assertEqual(len(contacts), 3)
        self.assertEqual(duplicates, 1)
        self.assertEqual(sum(contact.has_email for contact in contacts), 1)

    def test_google_contacts_shared_website_does_not_merge_distinct_people(self):
        path = self.write(
            "google-contacts.csv",
            "Name,E-mail 1 - Value,Website 1 - Value,Organization 1 - Name,Organization 1 - Title\n"
            "Alice Person,,https://example.com,Example Co,Owner\n"
            "Bob Person,,https://example.com,Example Co,Manager\n",
        )
        source, contacts, duplicates, _skipped = scan.load_contacts(path)
        self.assertEqual(source, "Google Contacts")
        self.assertEqual({contact.name for contact in contacts}, {"Alice Person", "Bob Person"})
        self.assertEqual(duplicates, 0)
        self.assertFalse(any(contact.has_profile for contact in contacts))

    def test_markdown_images_and_links_from_imports_are_rendered_as_plain_text(self):
        path = self.write(
            "Connections.csv",
            "First Name,Last Name,URL,Email Address,Company,Position,Connected On\n"
            'Pat,Example,,,"![pixel](https://tracker.example/p.gif) [click](https://evil.example)",Owner,2026-01-01\n',
        )
        report = scan.run(self.args(path))
        self.assertNotIn("![pixel]", report)
        self.assertNotIn("[click](", report)
        self.assertIn(r"\!\[pixel\]\(https://tracker.example/p.gif\)", report)

    def test_standalone_csv_limit_is_enforced_without_reading_the_whole_file(self):
        path = self.root / "Connections.csv"
        with path.open("wb") as stream:
            stream.write(b"First Name,Last Name\n")
            stream.seek(scan.MAX_ENTRY_BYTES + 1)
            stream.write(b"x")
        with self.assertRaisesRegex(scan.ScanError, "20 MiB"):
            scan.load_contacts(path)

    def test_supported_and_negative_relationships_stay_separate(self):
        input_path = self.write("Connections.csv", LINKEDIN_CSV)
        relation_path = self.write(
            "relationships.csv",
            "Source,Target,Relationship,Status,Evidence,Observed At,Target Company,Target Position\n"
            "Jordan Host,Taylor Guest,recorded podcast,confirmed,episode,2026-06-01,Trade Media,Host\n"
            "Jordan Host,Casey Buyer,shared event,unverified,event page,2026-04-01,Home Group,President\n",
        )
        result = scan.run(
            self.args(
                input_path,
                relationships=relation_path,
                confirm_relationship_data_authorized=True,
            )
        )
        self.assertIn("## Supported two-hop paths", result)
        self.assertIn("Taylor Guest", result)
        self.assertIn("## Context to verify — not introduction paths", result)
        self.assertIn("Casey Buyer", result)
        self.assertIn("unverified", result)

    def test_repeated_supported_rows_for_same_contextual_target_are_not_false_ambiguity(self):
        input_path = self.write("Connections.csv", LINKEDIN_CSV)
        relation_path = self.write(
            "relationships.csv",
            "Source,Target,Relationship,Status,Evidence,Observed At,Target Company,Target Position\n"
            "Jordan Host,Taylor Guest,recorded podcast,confirmed,episode one,2026-06-01,Trade Media,Host\n"
            "Alex Owner,Taylor Guest,recorded podcast,confirmed,episode two,2026-07-01,Trade Media,Host\n",
        )
        report = scan.run(
            self.args(
                input_path,
                target="Taylor Guest",
                relationships=relation_path,
                confirm_relationship_data_authorized=True,
            )
        )
        self.assertNotIn("matches multiple people", report)
        self.assertEqual(report.count("| Taylor Guest |"), 2)

    def test_relationship_file_requires_explicit_authority(self):
        input_path = self.write("Connections.csv", LINKEDIN_CSV)
        relation_path = self.write(
            "relationships.csv",
            "Source,Target,Relationship,Status\nJordan Host,Taylor Guest,podcast,confirmed\n",
        )
        with self.assertRaisesRegex(scan.ScanError, "requires --confirm"):
            scan.run(self.args(input_path, relationships=relation_path))

    def test_direct_target_prevents_unnecessary_introduction_hop(self):
        input_path = self.write("Connections.csv", LINKEDIN_CSV)
        relation_path = self.write(
            "relationships.csv",
            "Source,Target,Relationship,Status\nJordan Host,Alex Owner,knows,confirmed\n",
        )
        report = scan.run(
            self.args(
                input_path,
                target="Alex Owner",
                relationships=relation_path,
                confirm_relationship_data_authorized=True,
            )
        )
        self.assertIn("Contact Alex Owner directly", report)
        self.assertNotIn("Supported two-hop paths", report)

    def test_ambiguous_name_fails_closed(self):
        input_path = self.write("Connections.csv", LINKEDIN_CSV)
        report = scan.run(self.args(input_path, target="Sam Lee"))
        self.assertIn("matches multiple people", report)
        self.assertNotIn("Contact Sam Lee directly", report)

    def test_demo_and_redacted_json_are_safe_activation_surfaces(self):
        report = scan.run(
            self.args(
                demo=True,
                input=None,
                format="json",
                redact_names=True,
            )
        )
        payload = json.loads(report)
        self.assertEqual(payload["source"], "Synthetic demo")
        self.assertEqual(payload["owner"], "Network Owner")
        self.assertTrue(payload["direct"][0]["person"].startswith("Person "))
        for real_name in (
            "Alex Owner", "Jordan Host", "Riley Recruiter", "Morgan Partner",
            "Taylor Guest", "Casey Buyer",
        ):
            self.assertNotIn(real_name, report)

    def test_redacted_html_uses_one_identity_keyed_alias_map(self):
        contact_rows = [
            "Connector,Alpha,https://linkedin.com/in/connector,,Alpha Co,Owner,2026-01-01",
            "Person,Bravo,,,,Manager,2026-01-01",
            "Person,Charlie,,,,Manager,2026-01-01",
            "Person,Delta,,,,Manager,2026-01-01",
            "Person,Echo,,,,Manager,2026-01-01",
            "Person,Foxtrot,,,,Manager,2026-01-01",
            "Person,Golf,,,,Manager,2026-01-01",
        ]
        input_path = self.write(
            "Connections.csv",
            "First Name,Last Name,URL,Email Address,Company,Position,Connected On\n"
            + "\n".join(contact_rows)
            + "\n",
        )
        relation_path = self.write(
            "relationships.csv",
            "Source,Target,Relationship,Status\n"
            "Connector Alpha,Taylor Guest,recorded podcast,confirmed\n",
        )
        report = scan.run(
            self.args(
                input_path,
                relationships=relation_path,
                confirm_relationship_data_authorized=True,
                owner="Owner <script>alert(1)</script>",
                format="html",
                redact_names=True,
            )
        )
        graph_target = re.search(
            r'class="node second"/><text[^>]*>(Person \d{3})</text>', report
        )
        pre = re.search(r"<pre>(.*?)</pre>", report, flags=re.DOTALL)
        self.assertIsNotNone(graph_target)
        self.assertIsNotNone(pre)
        markdown = html.unescape(pre.group(1))
        table_target = re.search(
            r"## Supported two-hop paths.*?\n\| 1 \| (Person \d{3}) \|",
            markdown,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(table_target)
        self.assertEqual(graph_target.group(1), table_target.group(1))
        for real_name in ("Connector Alpha", "Taylor Guest", "Person Golf"):
            self.assertNotIn(real_name, report)
        self.assertNotIn("<script>alert(1)</script>", report)

    def test_redacted_aliases_keep_name_only_homonyms_distinct(self):
        path = self.write(
            "Connections.csv",
            "First Name,Last Name,URL,Email Address,Company,Position,Connected On\n"
            "Sam,Lee,,,,,\n"
            "Sam,Lee,,,,,\n",
        )
        payload = json.loads(
            scan.run(self.args(path, owner="Sam Lee", format="json", redact_names=True))
        )
        aliases = [item["person"] for item in payload["direct"]]
        self.assertEqual(payload["owner"], "Network Owner")
        self.assertEqual(len(aliases), 2)
        self.assertEqual(len(set(aliases)), 2)
        self.assertNotIn("Sam Lee", json.dumps(payload))

    def test_zip_expansion_ratio_is_rejected_before_parse(self):
        path = self.root / "linkedin.zip"
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("Connections.csv", "A" * 100_000)
        with self.assertRaisesRegex(scan.ScanError, "50:1"):
            scan.load_contacts(path)

    def test_zip_rejects_multidisk_and_zip64_metadata(self):
        original = self.root / "original.zip"
        with zipfile.ZipFile(original, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("Connections.csv", "First Name,Last Name\nAlex,Owner\n")
        raw = original.read_bytes()
        eocd = raw.rfind(b"PK\x05\x06")
        self.assertGreaterEqual(eocd, 0)

        cases = {
            "multi-disk": ((4, 1), (6, 1)),
            "ZIP64": ((8, 0xFFFF), (10, 0xFFFF)),
        }
        for label, mutations in cases.items():
            with self.subTest(label=label):
                changed = bytearray(raw)
                for relative_offset, value in mutations:
                    struct.pack_into("<H", changed, eocd + relative_offset, value)
                path = self.root / f"{label}.zip"
                path.write_bytes(changed)
                with self.assertRaisesRegex(scan.ScanError, "Multi-disk|ZIP64"):
                    scan.validated_zip_entries(path)

    def test_zip_ratio_uses_physical_span_not_forged_central_size(self):
        path = self.root / "forged.zip"
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("Connections.csv", "A" * 300_000)
        changed = bytearray(path.read_bytes())
        central = changed.find(b"PK\x01\x02")
        self.assertGreaterEqual(central, 0)
        original_size = struct.unpack_from("<L", changed, central + 24)[0]
        struct.pack_into("<L", changed, central + 20, original_size)
        path.write_bytes(changed)
        with self.assertRaisesRegex(scan.ScanError, "impossible compressed size|physical expansion"):
            scan.validated_zip_entries(path)

    def test_zip_parse_uses_the_exact_validated_snapshot(self):
        path = self.root / "linkedin.zip"
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(
                "Connections.csv",
                "First Name,Last Name,URL,Email Address,Company,Position,Connected On\n"
                "Alex,Owner,,,,,2026-01-01\n",
            )
        original_zipfile = zipfile.ZipFile
        opened_sources = []

        def recording_zipfile(source, *args, **kwargs):
            opened_sources.append(source)
            return original_zipfile(source, *args, **kwargs)

        with mock.patch.object(scan.zipfile, "ZipFile", side_effect=recording_zipfile):
            source, contacts, _duplicates, _skipped = scan.load_contacts(path)

        self.assertEqual(source, "LinkedIn")
        self.assertEqual([contact.name for contact in contacts], ["Alex Owner"])
        self.assertEqual(len(opened_sources), 2)
        self.assertTrue(all(isinstance(source, io.BytesIO) for source in opened_sources))

    def test_future_and_ambiguous_dates_are_not_fresh(self):
        self.assertEqual(scan.freshness_points("2099-01-01"), (0, "future date; not usable"))
        self.assertIsNone(scan.parse_date("04/05/2026"))
        self.assertEqual(scan.parse_date("13/05/2026").date().isoformat(), "2026-05-13")
        self.assertEqual(scan.parse_date("05/13/2026").date().isoformat(), "2026-05-13")

    def test_goal_keywords_match_words_not_substrings(self):
        false_contexts = ("Christopher Homes LLC", "Peoples Bank", "Serviceable Goods")
        for context in false_contexts:
            with self.subTest(context=context):
                points, reason = scan.goal_points(scan.Contact("key", "Name", context, ""), "hiring")
                self.assertEqual(points, 4)
                self.assertIn("no goal keyword", reason)
        points, reason = scan.goal_points(
            scan.Contact("key", "Name", "Service Talent", "HR Manager"), "hiring"
        )
        self.assertEqual(points, 15)
        self.assertIn("matched", reason)

    def test_score_components_sum_and_scopes_are_not_comparable(self):
        direct = scan.score_direct(
            scan.Contact("direct", "Direct Person", "Roof Co", "Owner", "2026-01-01"),
            "customers",
        )
        relationship = scan.Relationship(
            "Direct Person", "Target Person", "recorded podcast", "confirmed"
        )
        paths, exclusions = scan.build_paths([direct.contact], [relationship], "customers")
        self.assertEqual(exclusions, {})
        self.assertEqual(sum(map(int, re.findall(r"\+(\d+)", " ".join(direct.factors)))), direct.score)
        self.assertEqual(sum(map(int, re.findall(r"\+(\d+)", " ".join(paths[0].factors)))), paths[0].score)
        result = scan.ScanResult(
            "Owner", "customers", "Test", [direct.contact], [direct], paths, 0, 0
        )
        payload = json.loads(scan.json_report(result, False))
        self.assertFalse(payload["scoring"]["comparableAcrossScopes"])
        self.assertEqual(payload["direct"][0]["scoreScope"], "direct_priority")
        self.assertEqual(payload["paths"][0]["scoreScope"], "two_hop_path_priority")

    def test_relationship_accounting_and_zero_usable_rows_preserve_direct_report(self):
        input_path = self.write("Connections.csv", LINKEDIN_CSV)
        relation_path = self.write(
            "relationships.csv",
            "Source,Target,Relationship,Status\n"
            "Jordan Host,Taylor Guest,podcast,confirmed\n"
            "Alex Owner,Jordan Host,colleagues,confirmed\n"
            "Outside One,Outside Two,colleagues,confirmed\n",
        )
        payload = json.loads(
            scan.run(
                self.args(
                    input_path,
                    relationships=relation_path,
                    confirm_relationship_data_authorized=True,
                    format="json",
                )
            )
        )
        self.assertEqual(payload["counts"]["relationshipRowsSupplied"], 3)
        self.assertEqual(payload["counts"]["relationshipRowsExcluded"], 2)
        self.assertEqual(payload["counts"]["supportedTwoHopPaths"], 1)
        self.assertEqual(sum(payload["relationshipExclusionReasons"].values()), 2)
        self.assertEqual(payload["paths"][0]["relationship"], "podcast")

        empty_path = self.write(
            "empty-relationships.csv",
            "Source,Target,Relationship,Status\n"
            ",Missing Source,podcast,confirmed\n",
        )
        report = scan.run(
            self.args(
                input_path,
                relationships=empty_path,
                confirm_relationship_data_authorized=True,
            )
        )
        self.assertIn("## Ranked direct actions", report)
        self.assertIn("direct results remain available", report)

    def test_minimal_relationship_header_is_accepted(self):
        input_path = self.write("Connections.csv", LINKEDIN_CSV)
        relation_path = self.write(
            "relationships.csv",
            "Source,Target,Relationship,Status\n"
            "Jordan Host,Taylor Guest,podcast,confirmed\n",
        )
        report = scan.run(
            self.args(
                input_path,
                relationships=relation_path,
                confirm_relationship_data_authorized=True,
            )
        )
        self.assertIn("Taylor Guest", report)
        self.assertIn("podcast", report)

    def test_google_contacts_enforces_post_merge_contact_limit(self):
        path = self.write(
            "google-contacts.csv",
            "Name,E-mail 1 - Value\nAlice Person,\nBob Person,\nCasey Person,\n",
        )
        original_limit = scan.MAX_CONTACTS
        scan.MAX_CONTACTS = 2
        try:
            with self.assertRaisesRegex(scan.ScanError, "2-contact limit"):
                scan.load_contacts(path)
        finally:
            scan.MAX_CONTACTS = original_limit

    def test_script_contains_no_network_client(self):
        source = SCRIPT.read_text(encoding="utf-8")
        forbidden = ("import requests", "urllib.request", "import socket", "http.client")
        for marker in forbidden:
            self.assertNotIn(marker, source)


if __name__ == "__main__":
    unittest.main()
