"""Offline tests for the content-library-keeper scripts (no network)."""
import csv
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "content-library-keeper" / "scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


inv = load("published_inventory")
rmap = load("render_library_map")
summ = load("build_summary")


class Norm(unittest.TestCase):
    def test_strips_scheme_www_slash_and_case(self):
        self.assertEqual(inv.norm("https://www.Example.com/Hello-World/"), "example.com/hello-world")

    def test_drafts_and_admin_are_not_public(self):
        self.assertIsNone(inv.norm("https://example.com/?p=70000&preview=true"))
        self.assertIsNone(inv.norm("https://example.com/wp-admin/post.php?post=427&action=edit"))

    def test_home_page_and_garbage(self):
        self.assertEqual(inv.norm("https://example.com/"), "example.com/")
        self.assertIsNone(inv.norm("not a url"))
        self.assertIsNone(inv.norm(""))


class Slug(unittest.TestCase):
    def test_old_date_permalink_matches_new_slug(self):
        self.assertEqual(inv.slug("https://example.com/2008/08/18/when-people-take-facebook-too-seriously/"),
                         inv.slug("https://example.com/when-people-take-facebook-too-seriously/"))

    def test_root(self):
        self.assertEqual(inv.slug("https://example.com/"), "/")


class Titles(unittest.TestCase):
    def test_configured_brand_suffix_removed(self):
        self.assertEqual(inv.clean_title("How MAA Works | Example Co", ["Example Co"]), "How MAA Works")
        self.assertEqual(inv.clean_title("Hello &amp; welcome - Jane Doe", ["Jane Doe"]), "Hello & welcome")

    def test_no_suffixes_keeps_title(self):
        self.assertEqual(inv.clean_title("A | B", []), "A | B")


class Taxonomy(unittest.TestCase):
    def test_topics_hit_and_miss(self):
        self.assertIn("Paid ads & Dollar a Day", inv.tags_for("How to run Dollar a Day on Facebook", inv.TOPICS))
        self.assertIn("Local service businesses", inv.tags_for("HVAC Marketing Scorecard", inv.TOPICS))
        self.assertEqual(inv.tags_for("Untitled", inv.TOPICS), "")

    def test_ai_word_boundary(self):
        self.assertEqual(inv.tags_for("Daily email", [("AI", r"\b(ai)\b")]), "")


class NineTriangles(unittest.TestCase):
    def test_all_nine_accepted_names_present(self):
        acr = [n.split("(")[-1].rstrip(")") for n, _ in inv.TRIANGLES if "(" in n]
        for a in ["SBP", "AEC", "GCT", "MAA", "DDD", "CID", "LDT", "CCS", "MOF"]:
            self.assertIn(a, acr)

    def test_names_match_the_accepted_reference(self):
        ref = (ROOT / "skills" / "nine-triangles" / "references" / "canonical-framework.md").read_text(encoding="utf-8")
        for name, _rx in inv.TRIANGLES:
            if "(" not in name or "overview" in name:
                continue
            acronym = name.split("(")[-1].rstrip(")")
            corners = name.split(" (")[0].replace("·", " · ")
            self.assertIn(f"**{acronym}**", ref)
            self.assertIn(corners, ref)

    def test_legacy_aliases_map_to_current_names(self):
        self.assertIn("Audience·Engagement·Conversion (AEC)",
                      inv.tags_for("#ACC: Awareness, Consideration, Conversion", inv.TRIANGLES))
        self.assertIn("Specialist·Business·Partner (SBP)",
                      inv.tags_for("Analyst, Business, Partner explained", inv.TRIANGLES))

    def test_no_false_hits(self):
        self.assertEqual(inv.tags_for("Accounting tips for accountants", inv.TRIANGLES), "")
        self.assertEqual(inv.tags_for("Why I love my team", inv.TRIANGLES), "")


class Dedupe(unittest.TestCase):
    def test_video_listing_merges_into_post(self):
        out = inv.dedupe_sitemap([("post", "https://b.com/a/", "2026-01-01"), ("video", "https://b.com/a/", "2026-02-01")])
        self.assertEqual(len(out), 1)
        kind, url, lastmod, has_video, repeats = out[0]
        self.assertEqual((kind, has_video, repeats, lastmod), ("post", True, 1, "2026-02-01"))

    def test_same_kind_twice_is_a_repeat(self):
        rows = [("page", "https://d.com/people/x/", "2026-10-03"), ("page", "https://d.com/people/x/", "2026-10-03")]
        self.assertEqual(inv.dedupe_sitemap(rows)[0][4], 2)

    def test_video_only_page_kept(self):
        self.assertEqual(inv.dedupe_sitemap([("video", "https://b.com/v/", "")])[0][0], "video")

    def test_distinct_urls_kept_in_order(self):
        out = inv.dedupe_sitemap([("post", "https://b.com/1/", ""), ("page", "https://b.com/2/", "")])
        self.assertEqual([o[1] for o in out], ["https://b.com/1/", "https://b.com/2/"])


class Config(unittest.TestCase):
    def test_config_replaces_topics_and_people_rules(self):
        saved_topics, saved_cfg = list(inv.TOPICS), json.loads(json.dumps(inv.CONFIG))
        try:
            inv.apply_config({"sites": ["a.com"], "topics": [["Bakery", r"\bbread\b"]],
                              "people": {"owner_entity_id": "me", "real_sources": ["crm"]}})
            self.assertEqual(inv.TOPICS, [("Bakery", r"\bbread\b")])
            self.assertEqual(inv.CONFIG["people"]["owner_entity_id"], "me")
            d = tempfile.mkdtemp()
            reg = os.path.join(d, "registry.json")
            with open(reg, "w", encoding="utf-8") as fh:
                json.dump([{"entity_id": "me", "type": "person", "name": "Me Myself", "sources": "crm"},
                           {"entity_id": "ann", "type": "person", "name": "Ann Example", "sources": "crm"},
                           {"entity_id": "bob", "type": "person", "name": "Bob Example", "sources": "newsletter"},
                           {"entity_id": "bot-two", "type": "person", "name": "Helper Bot", "sources": "crm"}], fh)
            inv.apply_config({"people": {"exclude_entity_ids": ["bot-two"]}})
            people = {p["entity_id"]: p for p in inv.load_people(reg)}
            self.assertNotIn("me", people)
            self.assertNotIn("bot-two", people)
            self.assertTrue(people["ann"]["real"])
            self.assertFalse(people["bob"]["real"])
        finally:
            inv.TOPICS = saved_topics
            inv.CONFIG.clear(); inv.CONFIG.update(saved_cfg)


class Retag(unittest.TestCase):
    def _write(self, d, name, fields, row):
        with open(os.path.join(d, name), "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore"); w.writeheader(); w.writerow(row)

    def _read(self, d, name):
        with open(os.path.join(d, name), newline="", encoding="utf-8") as fh:
            return list(csv.DictReader(fh))[0]

    def test_retag_rewrites_tags_only_and_slim_agrees(self):
        d = tempfile.mkdtemp()
        row = {"site": "b.com", "type": "post", "title": "Marketing, Operations, Finance", "url": "https://b.com/x/",
               "people_in_title_v1": "Jane Doe", "notes": "keep"}
        self._write(d, "published-inventory.csv", inv.FIELDS, row)
        self._write(d, "published-inventory-sheet.csv", inv.SLIM, row)
        self.assertTrue(inv.retag(d))
        full, slim = self._read(d, "published-inventory.csv"), self._read(d, "published-inventory-sheet.csv")
        self.assertIn("MOF", full["nine_triangles_v1"])
        self.assertEqual((full["people_in_title_v1"], full["notes"]), ("Jane Doe", "keep"))
        self.assertEqual(slim["nine_triangles_v1"], full["nine_triangles_v1"])

    def test_slim_copies_tags_it_cannot_compute(self):
        d = tempfile.mkdtemp()
        row = {"site": "b.com", "type": "post", "title": "Untitled", "url": "https://b.com/y/", "categories": "Dollar a Day"}
        self._write(d, "published-inventory.csv", inv.FIELDS, row)
        self._write(d, "published-inventory-sheet.csv", inv.SLIM, row)
        inv.retag(d)
        self.assertIn("Dollar a Day", self._read(d, "published-inventory-sheet.csv")["topics_v1"])


class RenderMap(unittest.TestCase):
    HEADER = ["#", "Kind", "Collection (what it holds)", "Status", "Where it lives",
              "If two places disagree, this wins", "Rows now (live count)",
              "Owner: function → who today", "Factory stage · Triangle", "Freshness", "Next action"]
    SHEET_ID = "abc123"
    LINK = "https://docs.google.com/spreadsheets/d/abc123/edit#gid=42"

    def tab(self, *rows):
        return [["TITLE"], ["legend"], ["how it fits"], self.HEADER] + [list(r) for r in rows]

    def row(self, n="1", where=None, nxt="Do it | now"):
        return [n, "Map", "This map", "MASTER", where or self.LINK, "This tab", "32", "Library agent", "Post", "ok", nxt]

    def test_one_line_per_collection(self):
        out = rmap.render(self.tab(self.row("1"), self.row("2")), "2026-11-04", "test", self.SHEET_ID)
        self.assertIn("2 collections.", out)

    def test_pipes_escaped_and_own_sheet_links_shortened(self):
        out = rmap.render(self.tab(self.row()), "2026-11-04", "test", self.SHEET_ID)
        self.assertIn("Do it \\| now", out)
        self.assertIn("(this sheet, tab gid 42)", out)
        self.assertNotIn("edit#gid=", out)

    def test_other_links_kept(self):
        out = rmap.render(self.tab(self.row(where="https://github.com/x/y")), "2026-11-04", "test", self.SHEET_ID)
        self.assertIn("https://github.com/x/y", out)

    def test_without_sheet_id_links_are_left_alone(self):
        out = rmap.render(self.tab(self.row()), "2026-11-04", "test")
        self.assertIn(self.LINK, out)

    def test_blank_and_short_rows(self):
        out = rmap.render(self.tab(self.row("1"), [], ["", "stray"], ["2", "Kind"]), "2026-11-04", "test")
        self.assertIn("2 collections.", out)

    def test_missing_column_fails_loudly(self):
        with self.assertRaises(SystemExit):
            rmap.render([["#", "Kind"], ["1", "Map"]], "2026-11-04", "test")

    def test_template_renders(self):
        tpl = ROOT / "skills" / "content-library-keeper" / "references" / "library-map-template.json"
        out = rmap.render(rmap.load_rows(tpl), "2026-11-04", "test")
        self.assertIn("collections.", out)


class Summary(unittest.TestCase):
    def make(self):
        d = tempfile.mkdtemp()
        stats = {"a.com": {"live_urls": 3, "by_type": {"post": 2, "page": 1}, "with_video": 1, "in_library": 1,
                           "missing_from_library": 2, "rename_hits": 1, "listed_twice_or_more": 1},
                 "library_rows_not_live": {"a.com": 2}}
        with open(os.path.join(d, "inventory-stats.json"), "w", encoding="utf-8") as fh:
            json.dump(stats, fh)
        pages = [
            {"site": "a.com", "type": "post", "title": "Old Name tips", "url": "https://a.com/old/", "published": "2024-01-01",
             "status": "200", "topics_v1": "SEO & AI search", "notes": ""},
            {"site": "a.com", "type": "post", "title": "People", "url": "https://a.com/people/x/", "published": "2025-01-01",
             "status": "200", "topics_v1": "", "notes": "listed 2x in sitemaps"},
            {"site": "a.com", "type": "page", "title": "Gone", "url": "https://a.com/gone/", "published": "",
             "status": "404", "topics_v1": "SEO & AI search; Speaking & events", "notes": ""},
        ]
        with open(os.path.join(d, "published-inventory.csv"), "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=inv.FIELDS, extrasaction="ignore"); w.writeheader(); w.writerows(pages)
        with open(os.path.join(d, "rename-worklist.csv"), "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=inv.FIELDS, extrasaction="ignore"); w.writeheader(); w.writerow(pages[0])
        with open(os.path.join(d, "people-coverage.csv"), "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["entity_id", "name", "relationship_sources", "real_relationship", "in_vault", "in_fleet_memory",
                        "pages_with_name_in_title", "sites", "example_urls"])
            w.writerow(["b", "Bea Two", "crm", "Y", "n", "y", "0", "", ""])
            w.writerow(["a", "Al One", "crm, notes", "Y", "y", "y", "0", "", ""])
            w.writerow(["c", "Cy Three", "crm", "Y", "y", "n", "2", "a.com", ""])
            w.writerow(["z", "Zed Four", "newsletter", "N", "n", "n", "0", "", ""])
        with open(os.path.join(d, "library-rows-not-live.csv"), "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh); w.writerow(["site", "title", "url", "date", "status_in_library"])
            w.writerow(["a.com", "Secret matter", "https://a.com/legal-thing/", "", "Published"])
            w.writerow(["a.com", "Sheet link", "https://docs.google.com/spreadsheets/d/x/edit", "", ""])
        return d

    def test_sections_counts_and_order(self):
        d = self.make()
        cfg = {"sites": ["a.com"], "summary": {"withhold_titles": [{"url_contains": "legal-thing", "label": "(withheld)"}]}}
        out = summ.build(d, cfg, "2026-11-04")
        g = out["values"]
        self.assertEqual(len(out["section_header_rows"]), 6)
        self.assertEqual(g[out["total_row"] - 1][1], 3)
        flat = [" | ".join(str(c) for c in r) for r in g]
        self.assertTrue(any(r.startswith("SEO & AI search | 2") for r in flat))
        self.assertTrue(any(r.startswith("(no topic matched yet) | 1") for r in flat))
        people = [r[0] for r in g if r and r[0] in ("Al One", "Bea Two", "Cy Three", "Zed Four")]
        self.assertEqual(people, ["Al One", "Bea Two"])  # real, no page, strongest evidence first
        self.assertIn("(withheld)", " ".join(flat))
        self.assertNotIn("Secret matter", " ".join(flat))
        self.assertIn(summ.SHEET_LINK_NOTE, " ".join(flat))
        self.assertTrue(any("HTTP 404" in r for r in flat))
        self.assertTrue(any("listed more than once" in r and "(2x)" in r for r in flat))

    def test_tidy_titles(self):
        self.assertEqual(summ.tidy("???????? Attention, Kosovo!  Jobs ????????"), "Attention, Kosovo! Jobs")
        self.assertEqual(summ.tidy("America by 2026\u2033"), "America by 2026")
        self.assertEqual(summ.tidy("What? Really?"), "What? Really?")

    def test_hash_is_stable(self):
        d = self.make()
        a = summ.build(d, {"sites": ["a.com"]}, "2026-11-04")["sha256"]
        b = summ.build(d, {"sites": ["a.com"]}, "2026-11-04")["sha256"]
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main(verbosity=2)
