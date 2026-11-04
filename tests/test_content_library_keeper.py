"""Offline tests for the content-library-keeper scripts (no network)."""
import contextlib
import csv
import importlib.util
import io
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
        self.assertIn("Freshness", out)

    def test_stage_and_dated_freshness_columns_kept(self):
        header = list(self.HEADER)
        header[9] = "Freshness (checked 2026-11-04)"
        out = rmap.render([["TITLE"], ["legend"], ["how it fits"], header, self.row()], "2026-11-04", "test")
        self.assertIn("| Factory stage · Triangle | Freshness (checked 2026-11-04) |", out)
        self.assertIn("| Post | ok |", out)

    def test_optional_columns_may_be_absent(self):
        keep = [i for i, h in enumerate(self.HEADER) if h not in ("Factory stage · Triangle", "Freshness")]
        rows = [["TITLE"], [self.HEADER[i] for i in keep], [self.row()[i] for i in keep]]
        out = rmap.render(rows, "2026-11-04", "test")
        self.assertNotIn("Freshness", out)
        self.assertIn("1 collections.", out)

    def test_main_leaves_a_date_only_change_alone(self):
        d = tempfile.mkdtemp()
        export, md = os.path.join(d, "map.json"), os.path.join(d, "LIBRARY-MAP.md")
        with open(export, "w", encoding="utf-8") as fh:
            json.dump({"values": self.tab(self.row())}, fh)
        with contextlib.redirect_stdout(io.StringIO()):
            rmap.main([export, "--out", md, "--date", "2026-11-04"])
        first = Path(md).read_text(encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()) as said:
            rmap.main([export, "--out", md, "--date", "2026-11-05"])
        self.assertEqual(Path(md).read_text(encoding="utf-8"), first)
        self.assertIn("unchanged", said.getvalue())
        with open(export, "w", encoding="utf-8") as fh:
            json.dump({"values": self.tab(self.row(nxt="Something new"))}, fh)
        with contextlib.redirect_stdout(io.StringIO()):
            rmap.main([export, "--out", md, "--date", "2026-11-05"])
        self.assertIn("Something new", Path(md).read_text(encoding="utf-8"))


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
        self.assertNotIn("legal-thing", " ".join(flat))  # the address is withheld too, not just the title
        self.assertIn(summ.LINK_WITHHELD, " ".join(flat))
        self.assertIn(summ.SHEET_LINK_NOTE, " ".join(flat))
        self.assertTrue(any("HTTP 404" in r for r in flat))
        self.assertTrue(any("listed more than once" in r and "(2x)" in r for r in flat))
        self.assertIn("URLs in sitemaps", g[3])
        self.assertIn("pages listed in the sitemaps", g[1][0])

    def test_tidy_titles(self):
        self.assertEqual(summ.tidy("???????? Attention, Kosovo!  Jobs ????????"), "Attention, Kosovo! Jobs")
        self.assertEqual(summ.tidy("America by 2026\u2033"), "America by 2026")
        self.assertEqual(summ.tidy("What? Really?"), "What? Really?")

    def test_hash_is_stable(self):
        d = self.make()
        a = summ.build(d, {"sites": ["a.com"]}, "2026-11-04")["sha256"]
        b = summ.build(d, {"sites": ["a.com"]}, "2026-11-04")["sha256"]
        self.assertEqual(a, b)

    def test_hash_ignores_the_build_date(self):
        d = self.make()
        a = summ.build(d, {"sites": ["a.com"]}, "2026-11-04")
        b = summ.build(d, {"sites": ["a.com"]}, "2026-11-05")
        self.assertNotEqual(a["values"][0], b["values"][0])
        self.assertEqual(a["sha256"], b["sha256"])

    def test_main_leaves_an_unchanged_grid_alone(self):
        d = self.make()
        out = os.path.join(d, "summary-tab.json")
        with contextlib.redirect_stdout(io.StringIO()) as first:
            summ.main(["--inventory", d, "--out", out, "--date", "2026-11-04"])
        before = Path(out).read_text(encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()) as second:
            summ.main(["--inventory", d, "--out", out, "--date", "2026-11-05"])
        self.assertTrue(json.loads(first.getvalue())["changed"])
        self.assertFalse(json.loads(second.getvalue())["changed"])
        self.assertEqual(Path(out).read_text(encoding="utf-8"), before)

    def test_rows_in_no_sitemap_grouped_by_what_they_do_today(self):
        d = self.make()
        with open(os.path.join(d, "library-rows-not-in-sitemap.csv"), "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(inv.NOT_IN_SITEMAP_FIELDS)
            w.writerow(["a.com", "Gone page", "https://a.com/gone-1/", "", "Published", "404", "", "not found"])
            w.writerow(["a.com", "Moved page", "https://a.com/moved/", "", "Published", "200", "https://a.com/new/",
                        "redirects to a page in the sitemap"])
            w.writerow(["a.com", "Hidden page", "https://a.com/hidden/", "", "Published", "200", "",
                        "loads, but is missing from the sitemap"])
            w.writerow(["a.com", "Secret matter", "https://a.com/legal-thing/", "", "Published", "200",
                        "https://a.com/legal-thing-2/", "redirects to a page not in the sitemap"])
        cfg = {"sites": ["a.com"], "summary": {"withhold_titles": [{"url_contains": "legal-thing", "label": "(withheld)"}]}}
        out = summ.build(d, cfg, "2026-11-04")
        e = [r for r in out["values"] if len(r) == 5 and r[0] == "a.com"]
        self.assertEqual([r[1] for r in e], ["Hidden page", "Moved page", "(withheld)", "Gone page"])
        self.assertEqual(e[1][3], "redirects to a page in the sitemap: https://a.com/new/")
        self.assertNotIn("legal-thing", json.dumps(out["values"]))
        flat = [" | ".join(str(c) for c in r) for r in out["values"]]
        self.assertTrue(any("missing from the sitemap" in r and "https://a.com/hidden/" in r and r.startswith("a.com | Page loads")
                            for r in flat))

    def test_only_single_cell_rows_are_merged(self):
        out = summ.build(self.make(), {"sites": ["a.com"]}, "2026-11-04")
        g = out["values"]
        self.assertEqual(out["merge_rows"][:2], [1, 2])
        for r in out["merge_rows"]:
            self.assertEqual(len(g[r - 1]), 1, f"row {r} has column labels a merge would delete")
        a_header, b_header = out["section_header_rows"][:2]
        self.assertNotIn(a_header, out["merge_rows"])  # A. BY SITE carries column labels
        self.assertNotIn(b_header, out["merge_rows"])  # B. TOPICS carries the "Pages" label

    def test_owners_named_in_section_headers(self):
        d = self.make()
        cfg = {"sites": ["a.com"], "summary": {"section_owners": {"D": "Liana (relationships)", "F": "website desk"}}}
        out = summ.build(d, cfg, "2026-11-04")
        heads = [out["values"][i - 1][0] for i in out["section_header_rows"]]
        self.assertTrue(any(h.startswith("D.") and h.endswith("Owner: Liana (relationships).") for h in heads))
        self.assertTrue(any(h.startswith("F.") and h.endswith("Owner: website desk.") for h in heads))
        self.assertFalse(any(h.startswith("E.") and "Owner:" in h for h in heads))


class FakeNet:
    """Stands in for published_inventory.fetch: maps a URL to a response tuple or a callable returning one."""

    def __init__(self, responses):
        self.responses, self.calls = responses, []

    def __call__(self, url, tries=3, limit=None):
        self.calls.append(url)
        r = self.responses.get(url)
        if callable(r):
            r = r()
        return r if r is not None else (404, {}, b"", url)


class Guards(unittest.TestCase):
    INDEX = (b'<?xml version="1.0"?><sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
             b'<sitemap><loc>https://a.com/post-sitemap.xml</loc></sitemap>'
             b'<sitemap><loc>https://a.com/page-sitemap.xml</loc></sitemap></sitemapindex>')
    URLSET = (b'<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
              b'<url><loc>https://a.com/x/</loc><lastmod>2026-11-01</lastmod></url></urlset>')
    POSTS = "https://a.com/wp-json/wp/v2/posts?per_page=100&_fields=id,link,title,date,modified,categories,tags"

    def setUp(self):
        self.saved = (inv.fetch, inv.time.sleep)
        inv.time.sleep = lambda _s: None

    def tearDown(self):
        inv.fetch, inv.time.sleep = self.saved

    def posts(self, n, start=0):
        return json.dumps([{"id": i, "link": f"https://a.com/p{i}/", "title": {"rendered": "t"},
                            "date": "2026-01-01T00:00:00"} for i in range(start, start + n)]).encode()

    def test_a_failed_child_sitemap_stops_the_run(self):
        inv.fetch = FakeNet({"https://a.com/sitemap_index.xml": (200, {}, self.INDEX, ""),
                             "https://a.com/post-sitemap.xml": (200, {}, self.URLSET, ""),
                             "https://a.com/page-sitemap.xml": (500, {}, b"", "")})
        with self.assertRaises(inv.GuardError) as cm:
            inv.sitemap_urls("a.com")
        self.assertIn("page-sitemap.xml", str(cm.exception))

    def test_a_child_sitemap_that_recovers_is_used(self):
        tries = {"n": 0}
        def flaky():
            tries["n"] += 1
            return (503, {}, b"", "") if tries["n"] == 1 else (200, {}, self.URLSET, "")
        inv.fetch = FakeNet({"https://a.com/sitemap_index.xml": (200, {}, self.INDEX, ""),
                             "https://a.com/post-sitemap.xml": (200, {}, self.URLSET, ""),
                             "https://a.com/page-sitemap.xml": flaky})
        rows = inv.sitemap_urls("a.com")
        self.assertEqual(sorted(k for k, _u, _m in rows), ["page", "post"])

    def test_a_missing_sitemap_index_stops_the_run(self):
        inv.fetch = FakeNet({})
        with self.assertRaises(inv.GuardError):
            inv.sitemap_urls("a.com")

    def test_rest_that_fails_a_later_page_stops_the_run(self):
        inv.fetch = FakeNet({self.POSTS + "&page=1": (200, {"x-wp-totalpages": "2"}, self.posts(100), ""),
                             self.POSTS + "&page=2": (500, {}, b"", "")})
        with self.assertRaises(inv.GuardError):
            inv.wp_rest("a.com")

    def test_closed_rest_means_read_each_page(self):
        inv.fetch = FakeNet({})
        self.assertEqual(inv.wp_rest("a.com"), ({}, {}, {}))

    def test_rest_without_a_page_count_stops_at_wordpress_400(self):
        inv.fetch = FakeNet({self.POSTS + "&page=1": (200, {}, self.posts(100), ""),
                             self.POSTS + "&page=2": (400, {}, b"", "")})
        out, _cats, _tags = inv.wp_rest("a.com")
        self.assertEqual(len(out), 100)

    def test_drop_limits(self):
        self.assertIsNone(inv.check_drop("a.com", 1000, 990))
        self.assertIn("--allow-drop", inv.check_drop("a.com", 1000, 900))
        self.assertIsNone(inv.check_drop("a.com", 100, 85))  # 15 fewer: under the 20-URL floor
        self.assertIsNotNone(inv.check_drop("a.com", 100, 75))
        self.assertIsNone(inv.check_drop("a.com", None, 5))  # first run: nothing to compare with
        self.assertIsNone(inv.check_drop("a.com", 1000, 900, {"max_drop_fraction": 0.2}))

    def test_source_change(self):
        self.assertIn("--allow-source-change", inv.check_source("a.com", "rest", "html"))
        self.assertIsNone(inv.check_source("a.com", None, "html"))
        self.assertIsNone(inv.check_source("a.com", "rest", "rest"))


class AddressToday(unittest.TestCase):
    LISTED = {"a.com/new"}

    def test_each_outcome_in_plain_words(self):
        c = inv.classify
        self.assertEqual(c("https://a.com/x/", 200, "https://a.com/x/", self.LISTED, "a.com/"),
                         "loads, but is missing from the sitemap")
        self.assertEqual(c("https://a.com/x/", 200, "https://a.com/new/", self.LISTED, "a.com/"),
                         "redirects to a page in the sitemap")
        self.assertEqual(c("https://a.com/x/", 200, "https://b.com/y/", self.LISTED, "a.com/"),
                         "redirects to a page not in the sitemap")
        self.assertEqual(c("https://a.com/x/", 200, "https://www.a.com/", self.LISTED, "a.com/"),
                         "redirects to the home page")
        self.assertEqual(c("https://a.com/x/", 404, "https://a.com/x/", self.LISTED), "not found")
        self.assertEqual(c("https://a.com/x/", 410, "", self.LISTED), "not found")
        self.assertEqual(c("https://a.com/x/", 401, "", self.LISTED), "needs a login or is blocked")
        self.assertEqual(c("https://a.com/x/", None, "", self.LISTED), "no answer")
        self.assertEqual(c("https://a.com/x/", 500, "", self.LISTED), "HTTP 500")
        self.assertEqual(c("https://docs.google.com/spreadsheets/d/1/edit", None, "", self.LISTED),
                         "points at a Google file, not a page")

    def test_inventory_and_summary_use_the_same_words(self):
        self.assertEqual(inv.TODAY_ORDER, summ.TODAY_ORDER)

    def test_old_address_of_a_moved_page(self):
        v = inv.old_url_verdict
        old, now = "https://a.com/2020/04/12/post/", "https://a.com/post/"
        self.assertEqual(v(old, now, 200, "https://a.com/post/"), "redirects to the current page")
        self.assertEqual(v(old, now, 200, old), "still loads at the old address")
        self.assertEqual(v(old, now, 200, "https://a.com/"), "redirects somewhere else")
        self.assertEqual(v(old, now, 404, old), "not found")
        self.assertEqual(v(old, now, None, ""), "no answer")

    def test_broken_old_addresses_listed_for_the_website_desk(self):
        d = Summary().make()
        with open(os.path.join(d, "library-old-urls.csv"), "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(inv.OLD_URL_FIELDS)
            w.writerow(["a.com", "https://a.com/2020/04/12/post/", "https://a.com/post/", "404", "", "not found"])
            w.writerow(["a.com", "https://a.com/2021/01/01/ok/", "https://a.com/ok/", "200", "https://a.com/ok/",
                        "redirects to the current page"])
        flat = [" | ".join(str(c) for c in r) for r in summ.build(d, {"sites": ["a.com"]}, "2026-11-04")["values"]]
        rows = [r for r in flat if "return 404 instead of redirecting" in r]
        self.assertEqual(len(rows), 1)
        self.assertIn("| 1 | https://a.com/2020/04/12/post/ → https://a.com/post/", rows[0])
        self.assertFalse(any("2021/01/01/ok" in r for r in flat))


class QuietWrites(unittest.TestCase):
    ROW = {"site": "a.com", "type": "post", "title": "T", "url": "https://a.com/t/", "published": "2026-01-01",
           "modified": "", "categories": "", "tags": "", "status": "200", "has_video": "", "library_tab": "",
           "topics_v1": "", "nine_triangles_v1": "", "factory_stage_v1": "", "people_in_title_v1": "", "notes": ""}

    def run_once(self, d, pages, when):
        stats = {"a.com": {"pages_in_sitemaps": pages}, "generated_utc": when}
        return inv.write_outputs(d, [dict(self.ROW)], [], [], stats, None)

    def stats(self, d):
        return json.loads(Path(d, "inventory-stats.json").read_text(encoding="utf-8"))

    def test_a_run_with_nothing_new_writes_nothing(self):
        d = tempfile.mkdtemp()
        self.assertIn("inventory-stats.json", self.run_once(d, 1, "2026-11-04T10:00Z"))
        self.assertEqual(self.run_once(d, 1, "2026-11-05T10:00Z"), [])
        self.assertEqual(self.stats(d)["generated_utc"], "2026-11-04T10:00Z")

    def test_a_real_change_is_written_with_the_new_time(self):
        d = tempfile.mkdtemp()
        self.run_once(d, 1, "2026-11-04T10:00Z")
        self.assertEqual(self.run_once(d, 2, "2026-11-05T10:00Z"), ["inventory-stats.json"])
        self.assertEqual(self.stats(d)["generated_utc"], "2026-11-05T10:00Z")


if __name__ == "__main__":
    unittest.main(verbosity=2)
