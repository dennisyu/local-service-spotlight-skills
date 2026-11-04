"""Offline tests for the content-library-keeper scripts (no network)."""
import contextlib
import csv
import importlib.util
import io
import json
import os
import re
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
        stats = {"a.com": {"pages_in_sitemaps": 3, "by_type": {"post": 2, "page": 1}, "with_video": 1, "in_library": 1,
                           "missing_from_library": 2, "rename_hits": 1, "rename_kept": 0, "listed_twice_or_more": 1},
                 "library_rows_not_in_sitemap": {"a.com": 2}, "rename_pattern": "old name", "library_matching": True,
                 "library_old_urls_today": {},
                 "people": {"registry_people_indexed": 4, "real_relationships": 3, "real_with_1plus_title_page": 1,
                            "real_with_no_title_page": 2},
                 "generated_utc": "2026-11-04T12:00Z"}
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
        with open(os.path.join(d, "library-rows-not-in-sitemap.csv"), "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh); w.writerow(inv.NOT_IN_SITEMAP_FIELDS)
            w.writerow(["a.com", "Secret matter", "https://a.com/legal-thing/", "", "Published", "404", "", "not found"])
            w.writerow(["a.com", "Sheet link", "https://docs.google.com/spreadsheets/d/x/edit", "", "", "", "",
                        "points at a Google file, not a page"])
        return d

    def test_counts_and_one_line_per_agent_list(self):
        d = self.make()
        cfg = {"sites": ["a.com"], "summary": {"withhold_titles": [{"url_contains": "legal-thing", "label": "(withheld)"}]}}
        out = summ.build(d, cfg, "2026-11-04")
        g = out["values"]
        flat = [" | ".join(str(c) for c in r) for r in g]
        self.assertEqual([g[i - 1][0][:2] for i in out["section_header_rows"]], ["A.", "B.", "C.", "D."])
        self.assertEqual(g[out["total_row"] - 1][1], 3)
        self.assertIn("URLs in sitemaps", g[3])
        self.assertNotIn("Missing from old tabs", g[3])  # the frozen old tabs are not a to-do
        self.assertIn("agent", g[1][0])
        self.assertTrue(any(r.startswith("SEO & AI search | 2") for r in flat))
        self.assertTrue(any(r.startswith("(no topic matched yet) | 1") for r in flat))
        lists = {r[0].split(" (")[0]: r[1] for r in g if len(r) == 4 and isinstance(r[1], int)}
        self.assertEqual(lists["Titles that still use the retired name"], 1)
        self.assertEqual(lists["People we know with no page naming them"], 2)  # real, no page
        self.assertEqual(lists["Old dated addresses that return 404 instead of redirecting to the page"], 0)
        self.assertEqual(lists["Sitemap defects"], 2)  # the 404 and the page listed twice
        # The rows themselves stay in the repository files: no person, title or old row is listed here.
        for word in ("Al One", "Bea Two", "Old Name tips", "Secret matter", "legal-thing"):
            self.assertNotIn(word, " ".join(flat))
        self.assertTrue(any("HTTP 404" in r and "https://a.com/gone/" in r for r in flat))
        self.assertTrue(any("listed more than once" in r and "(2x)" in r for r in flat))

    def test_hash_is_stable(self):
        d = self.make()
        a = summ.build(d, {"sites": ["a.com"]}, "2026-11-04")["sha256"]
        b = summ.build(d, {"sites": ["a.com"]}, "2026-11-04")["sha256"]
        self.assertEqual(a, b)

    def test_hash_ignores_the_run_date(self):
        d = self.make()
        a = summ.build(d, {"sites": ["a.com"]}, "2026-11-04")
        path = os.path.join(d, "inventory-stats.json")
        st = json.load(open(path, encoding="utf-8"))
        st["generated_utc"] = "2026-11-05T12:00Z"  # the next day's run found the same data
        json.dump(st, open(path, "w", encoding="utf-8"))
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

    def test_live_page_missing_from_the_sitemap_is_a_defect(self):
        d = self.make()
        with open(os.path.join(d, "library-rows-not-in-sitemap.csv"), "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(inv.NOT_IN_SITEMAP_FIELDS)
            w.writerow(["a.com", "Gone page", "https://a.com/gone-1/", "", "Published", "404", "", "not found"])
            w.writerow(["a.com", "Hidden page", "https://a.com/hidden/", "", "Published", "200", "",
                        "loads, but is missing from the sitemap"])
            w.writerow(["a.com", "Secret matter", "https://a.com/legal-thing/", "", "Published", "200", "",
                        "loads, but is missing from the sitemap"])
        cfg = {"sites": ["a.com"], "summary": {"withhold_titles": [{"url_contains": "legal-thing", "label": "(withheld)"}]}}
        out = summ.build(d, cfg, "2026-11-04")
        flat = [" | ".join(str(c) for c in r) for r in out["values"]]
        self.assertTrue(any(r.startswith("a.com | Page loads but is missing from the sitemap.") and
                            r.endswith("| 1 | https://a.com/hidden/") for r in flat))
        self.assertNotIn("legal-thing", json.dumps(out["values"]))
        self.assertNotIn("gone-1", json.dumps(out["values"]))  # an old row that is gone is history, not a task

    def test_rows_from_the_rest_api_are_not_sitemap_defects(self):
        d = self.make()
        rows = [{"site": "a.com", "type": "post", "title": "Fine", "url": "https://a.com/fine/", "published": "2025-01-01",
                 "status": inv.STATUS_FROM_REST, "topics_v1": "", "notes": ""},
                {"site": "a.com", "type": "page", "title": "Gone", "url": "https://a.com/gone/", "published": "",
                 "status": "404", "topics_v1": "", "notes": ""}]
        with open(os.path.join(d, "published-inventory.csv"), "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=inv.FIELDS, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
        flat = [" | ".join(str(c) for c in r) for r in summ.build(d, {"sites": ["a.com"]}, "2026-11-04")["values"]]
        self.assertTrue(any("returns HTTP 404" in r and "https://a.com/gone/" in r for r in flat))
        self.assertFalse(any("https://a.com/fine/" in r for r in flat))

    def test_defects_of_one_kind_share_one_row(self):
        d = self.make()
        rows = [{"site": "a.com", "type": "page", "title": f"Gone {i}", "url": f"https://a.com/gone-{i}/", "published": "",
                 "status": "404", "topics_v1": "", "notes": ""} for i in range(5)]
        rows.append({"site": "a.com", "type": "page", "title": "Private", "url": "https://a.com/legal-thing/",
                     "published": "", "status": "404", "topics_v1": "", "notes": ""})
        with open(os.path.join(d, "published-inventory.csv"), "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=inv.FIELDS, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
        cfg = {"sites": ["a.com"], "summary": {"withhold_titles": [{"url_contains": "legal-thing", "label": "(withheld)"}]}}
        g = summ.build(d, cfg, "2026-11-04")["values"]
        hits = [r for r in g if len(r) == 4 and str(r[1]).startswith("Listed in sitemap but returns HTTP 404")]
        self.assertEqual(len(hits), 1)  # five 404s are one row with a count, not five rows
        self.assertEqual(hits[0][2], 6)
        self.assertEqual(hits[0][3], "https://a.com/gone-0/, https://a.com/gone-1/")  # two examples at most
        self.assertNotIn("legal-thing", json.dumps(g))

    def test_only_single_cell_rows_are_merged(self):
        out = summ.build(self.make(), {"sites": ["a.com"]}, "2026-11-04")
        g = out["values"]
        self.assertEqual(out["merge_rows"][:2], [1, 2])
        for r in out["merge_rows"]:
            self.assertEqual(len(g[r - 1]), 1, f"row {r} has column labels a merge would delete")
        a, b, c, d = out["section_header_rows"]
        for h in (a, b, c):  # A, B and C carry column labels in their header row
            self.assertNotIn(h, out["merge_rows"])
        self.assertIn(d, out["merge_rows"])

    def test_each_list_names_the_agent_that_works_it(self):
        d = self.make()
        cfg = {"sites": ["a.com"], "summary": {"worklist_owners": {"people": "content agent", "sitemap": "website agent",
                                                                   "rename": "library agent"}}}
        out = summ.build(d, cfg, "2026-11-04")
        g = out["values"]
        owner_of = {r[0].split(" (")[0]: r[2] for r in g if len(r) == 4 and isinstance(r[1], int)}
        self.assertEqual(owner_of["People we know with no page naming them"], "content agent")
        self.assertEqual(owner_of["Titles that still use the retired name"], "library agent")
        self.assertTrue(g[out["section_header_rows"][3] - 1][0].endswith("Worked by: website agent."))

    def test_counts_come_from_the_runs_stats_not_old_files(self):
        # A run without a registry or a rename pattern leaves yesterday's CSVs on disk; the grid must not show them.
        d = self.make()
        path = os.path.join(d, "inventory-stats.json")
        st = json.load(open(path, encoding="utf-8"))
        del st["people"]
        st["rename_pattern"] = ""
        st["library_matching"] = False
        json.dump(st, open(path, "w", encoding="utf-8"))
        g = summ.build(d, {"sites": ["a.com"]}, "2026-11-04")["values"]
        items = {r[0].split(" (")[0]: r[1] for r in g if len(r) == 4 and r[0][:2] not in ("C.",)}
        self.assertEqual(items["Titles that still use the retired name"], summ.NOT_CHECKED)
        self.assertEqual(items["People we know with no page naming them"], summ.NOT_CHECKED)
        self.assertEqual(items["Old dated addresses that return 404 instead of redirecting to the page"], summ.NOT_CHECKED)

    def test_row_one_carries_the_inventory_date(self):
        g = summ.build(self.make(), {"sites": ["a.com"]}, "2030-01-01")["values"]
        self.assertIn("2026-11-04", g[0][0])  # the stats' generated_utc, not the day the grid was built

    def test_a_missing_stats_file_stops_cleanly(self):
        d = tempfile.mkdtemp()
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(summ.main(["--inventory", d, "--out", os.path.join(d, "x.json")]), 2)
        self.assertFalse(os.path.exists(os.path.join(d, "x.json")))

    def test_old_rows_on_another_site_are_not_sitemap_defects(self):
        d = self.make()
        with open(os.path.join(d, "library-rows-not-in-sitemap.csv"), "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh); w.writerow(inv.NOT_IN_SITEMAP_FIELDS)
            w.writerow(["a.com", "A video", "https://www.youtube.com/watch?v=x", "", "", "", "", "points at another site"])
        flat = [" | ".join(str(c) for c in r) for r in summ.build(d, {"sites": ["a.com"]}, "2026-11-04")["values"]]
        self.assertFalse(any("youtube.com" in r for r in flat))


class Renames(unittest.TestCase):
    def setUp(self):
        self.saved = dict(inv.CONFIG)

    def tearDown(self):
        inv.CONFIG.clear(); inv.CONFIG.update(self.saved)

    def test_domain_mentions_and_kept_pages_are_not_renames(self):
        inv.CONFIG.update({"rename_keep_pattern": r"oldco\.com", "rename_keep_urls": ["https://a.com/history/"]})
        rx = re.compile("oldco", re.I)
        row = lambda title, url="https://a.com/x/": {"title": title, "url": url}
        self.assertTrue(inv.needs_rename(row("Join OldCo Academy"), rx))
        self.assertFalse(inv.needs_rename(row("How We Fixed 404s on oldco.com"), rx))  # the domain is fine to name
        self.assertTrue(inv.needs_rename(row("OldCo tips for oldco.com"), rx))  # the company name is still there
        self.assertFalse(inv.needs_rename(row("OldCo in 2009", "https://a.com/history"), rx))  # kept on purpose
        self.assertFalse(inv.needs_rename(row("Nothing to see"), rx))
        self.assertFalse(inv.needs_rename(row("Join OldCo Academy"), None))


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

    def test_rest_that_does_not_answer_stops_the_run(self):
        inv.fetch = FakeNet({self.POSTS + "&page=1": (503, {}, b"", "")})
        with self.assertRaises(inv.GuardError):
            inv.wp_rest("a.com")

    def test_rest_answering_a_web_page_stops_the_run(self):
        # A site whose titles came from REST last run: a web page where JSON should be is a firewall, so stop.
        inv.fetch = FakeNet({self.POSTS + "&page=1": (200, {}, b"<html>checking your browser</html>", "")})
        with self.assertRaises(inv.GuardError):
            inv.wp_rest("a.com", prev_source="rest")

    def test_a_site_that_answers_every_address_with_a_page_has_no_rest(self):
        # A static host answers /wp-json with its normal page; on a site read from HTML that means "no REST".
        inv.fetch = FakeNet({self.POSTS + "&page=1": (200, {}, b"<html>a normal page</html>", "")})
        self.assertEqual(inv.wp_rest("a.com", prev_source="html"), ({}, {}, {}))
        self.assertEqual(inv.wp_rest("a.com"), ({}, {}, {}))

    def test_rest_false_never_calls_the_api(self):
        inv.fetch = FakeNet({})
        inv.CONFIG["site_options"] = {"a.com": {"rest": False}}
        try:
            self.assertEqual(inv.wp_rest("a.com", prev_source="rest"), ({}, {}, {}))
            self.assertEqual(inv.fetch.calls, [])
        finally:
            inv.CONFIG["site_options"] = {}

    def test_a_failed_pages_endpoint_stops_the_run_even_when_posts_answer(self):
        pages = "https://a.com/wp-json/wp/v2/pages?per_page=100&_fields=id,link,title,date,modified"
        inv.fetch = FakeNet({self.POSTS + "&page=1": (200, {"x-wp-totalpages": "1"}, self.posts(3), ""),
                             pages + "&page=1": (500, {}, b"", "")})
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

    def test_rest_rows_say_their_page_was_not_opened(self):
        index = (b'<?xml version="1.0"?><sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                 b'<sitemap><loc>https://a.com/post-sitemap.xml</loc></sitemap></sitemapindex>')
        urlset = (b'<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                  b'<url><loc>https://a.com/p0/</loc></url><url><loc>https://a.com/entity/x/</loc></url></urlset>')
        rest = "https://a.com/wp-json/wp/v2/{}?per_page=100&_fields={}&page=1"
        empty = (200, {"x-wp-totalpages": "1"}, b"[]", "")
        inv.fetch = FakeNet({
            "https://a.com/sitemap_index.xml": (200, {}, index, ""),
            "https://a.com/post-sitemap.xml": (200, {}, urlset, ""),
            self.POSTS + "&page=1": (200, {"x-wp-totalpages": "1"}, self.posts(1), ""),
            rest.format("pages", "id,link,title,date,modified"): empty,
            rest.format("categories", "id,name"): empty,
            rest.format("tags", "id,name"): empty,
        })
        d = tempfile.mkdtemp()
        with contextlib.redirect_stdout(io.StringIO()):
            stats, _changed = inv.build(["a.com"], d, None, None)
        with open(os.path.join(d, "published-inventory.csv"), encoding="utf-8") as fh:
            rows = {r["url"]: r for r in csv.DictReader(fh)}
        self.assertEqual(rows["https://a.com/p0/"]["status"], inv.STATUS_FROM_REST)
        self.assertNotIn("https://a.com/p0/", inv.fetch.calls)  # the REST row was never opened
        self.assertEqual(rows["https://a.com/entity/x/"]["status"], "404")  # REST did not list it, so it was opened
        self.assertEqual(stats["a.com"]["pages_opened"], 1)
        self.assertEqual(stats["a.com"]["non_200"], 1)
        self.assertEqual(stats["a.com"]["metadata_source"], "rest")

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


class ReviewFixes(unittest.TestCase):
    """Behaviour an independent review of the 2026-11-04 revision asked for."""
    URLSET = (b'<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">%s</urlset>')

    def setUp(self):
        self.saved = (inv.fetch, inv.time.sleep, dict(inv.CONFIG))
        inv.time.sleep = lambda _s: None

    def tearDown(self):
        inv.fetch, inv.time.sleep = self.saved[0], self.saved[1]
        inv.CONFIG.clear(); inv.CONFIG.update(self.saved[2])

    def site(self, urls, page=None, extra=None):
        """A static site (no REST) with one plain sitemap; page(url) gives each page's response."""
        body = self.URLSET % b"".join(b"<url><loc>%s</loc></url>" % u.encode() for u in urls)
        net = {"https://a.com/sitemap_index.xml": (404, {}, b"", ""), "https://a.com/sitemap-index.xml": (404, {}, b"", ""),
               "https://a.com/sitemap.xml": (200, {}, body, "")}
        for u in urls:
            net[u] = (lambda u=u: page(u)) if page else (200, {}, f"<title>Page {u}</title>".encode(), u)
        net.update(extra or {})
        return FakeNet(net)

    def run_build(self, d, list_dir=None):
        with contextlib.redirect_stdout(io.StringIO()):
            return inv.build(["a.com"], d, list_dir, None)

    def test_blocked_pages_stop_the_run_instead_of_blanking_titles(self):
        urls = [f"https://a.com/p{i}/" for i in range(50)]
        inv.fetch = self.site(urls, page=lambda u: (403, {}, b"", u))
        d = tempfile.mkdtemp()
        with self.assertRaises(inv.GuardError) as cm:
            self.run_build(d)
        self.assertIn("blocked", str(cm.exception))
        self.assertEqual(os.listdir(d), [])  # nothing written

    def test_a_firewall_page_answering_200_everywhere_stops_the_run(self):
        urls = [f"https://a.com/p{i}/" for i in range(50)]
        inv.fetch = self.site(urls, page=lambda u: (200, {}, b"<title>Just a moment...</title>", u))
        with self.assertRaises(inv.GuardError) as cm:
            self.run_build(tempfile.mkdtemp())
        self.assertIn("same title", str(cm.exception))

    def test_a_plain_sitemap_and_a_configured_path_are_read(self):
        inv.fetch = self.site(["https://a.com/x/"])
        self.assertEqual(inv.sitemap_urls("a.com"), [("page", "https://a.com/x/", "")])
        inv.CONFIG["site_options"] = {"a.com": {"sitemap": "/custom.xml"}}
        inv.fetch = FakeNet({"https://a.com/custom.xml": (200, {}, self.URLSET % b"<url><loc>https://a.com/y/</loc></url>", "")})
        self.assertEqual(inv.sitemap_urls("a.com"), [("page", "https://a.com/y/", "")])
        self.assertEqual(inv.fetch.calls, ["https://a.com/custom.xml"])

    def test_only_dated_addresses_match_a_moved_page(self):
        urls = ["https://a.com/post-name/", "https://a.com/category/seo/", "https://a.com/2021/02/03/kept/",
                "https://a.com/kept/"]
        old = {"values": [["1", "Moved post", "https://a.com/2020/04/12/post-name/", "", ""],
                          ["2", "An old page", "https://a.com/seo/", "", ""],
                          ["3", "Still dated", "https://a.com/2021/02/03/kept/", "", ""]]}
        lists = tempfile.mkdtemp()
        json.dump(old, open(os.path.join(lists, "a.com.json"), "w"))
        inv.CONFIG["check_rows_not_in_sitemap"] = False
        inv.CONFIG["check_old_urls"] = False
        inv.fetch = self.site(urls)
        d = tempfile.mkdtemp()
        self.run_build(d, lists)
        rows = {r["url"]: r for r in csv.DictReader(open(os.path.join(d, "published-inventory.csv"), encoding="utf-8"))}
        self.assertEqual(rows["https://a.com/post-name/"]["library_tab"], "yes")  # /2020/04/12/post-name/ moved here
        self.assertEqual(rows["https://a.com/category/seo/"]["library_tab"], "")  # sharing "seo" is not a match
        self.assertEqual(rows["https://a.com/kept/"]["library_tab"], "")  # its dated address is a page of its own
        self.assertEqual(rows["https://a.com/2021/02/03/kept/"]["library_tab"], "yes")
        olds = list(csv.DictReader(open(os.path.join(d, inv.OLD_URLS_FILE), encoding="utf-8")))
        self.assertEqual([o["old_url"] for o in olds], ["https://a.com/2020/04/12/post-name/"])
        gone = [r["url"] for r in csv.DictReader(open(os.path.join(d, inv.NOT_IN_SITEMAP_FILE), encoding="utf-8"))]
        self.assertEqual(gone, ["https://a.com/seo/"])

    def test_old_rows_that_link_to_another_site_are_labelled_and_not_opened(self):
        old = {"values": [["1", "A video", "https://www.youtube.com/watch?v=abc", "", ""]]}
        lists = tempfile.mkdtemp()
        json.dump(old, open(os.path.join(lists, "a.com.json"), "w"))
        inv.fetch = self.site(["https://a.com/x/"])
        d = tempfile.mkdtemp()
        self.run_build(d, lists)
        gone = list(csv.DictReader(open(os.path.join(d, inv.NOT_IN_SITEMAP_FILE), encoding="utf-8")))
        self.assertEqual(gone[0]["today"], inv.OFF_SITE)
        self.assertNotIn("https://www.youtube.com/watch?v=abc", inv.fetch.calls)

    def test_a_url_in_two_different_sitemaps_is_a_repeat(self):
        rows = inv.dedupe_sitemap([("post", "https://a.com/x/", ""), ("page", "https://a.com/x/", ""),
                                   ("video", "https://a.com/y/", ""), ("post", "https://a.com/y/", "")])
        repeats = {u: r for _k, u, _m, _v, r in rows}
        self.assertEqual(repeats["https://a.com/x/"], 2)  # listed as a post and as a page
        self.assertEqual(repeats["https://a.com/y/"], 1)  # a post with a video is listed once plus its video entry

    def test_a_bad_rename_pattern_stops_before_the_crawl(self):
        with self.assertRaises(SystemExit):
            inv.apply_config({"rename_keep_pattern": "blitz(metrics"})

    def test_people_with_no_page_come_first_by_evidence(self):
        reg = tempfile.mktemp(suffix=".json")
        json.dump([{"entity_id": "a", "type": "person", "name": "Ann Alpha", "sources": "crm"},
                   {"entity_id": "b", "type": "person", "name": "Bob Bravo", "sources": "crm, notes, mail"},
                   {"entity_id": "c", "type": "person", "name": "Cy Charlie", "sources": "crm, notes"}], open(reg, "w"))
        inv.fetch = self.site(["https://a.com/ann-alpha/"], extra={
            "https://a.com/ann-alpha/": (200, {}, b"<title>Ann Alpha</title>", "https://a.com/ann-alpha/")})
        d = tempfile.mkdtemp()
        with contextlib.redirect_stdout(io.StringIO()):
            inv.build(["a.com"], d, None, reg)
        order = [r["name"] for r in csv.DictReader(open(os.path.join(d, "people-coverage.csv"), encoding="utf-8"))]
        self.assertEqual(order, ["Bob Bravo", "Cy Charlie", "Ann Alpha"])  # no page and most sources first


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
        self.assertEqual(inv.STATUS_FROM_REST, summ.STATUS_FROM_REST)

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
        path = os.path.join(d, "inventory-stats.json")
        st = json.load(open(path, encoding="utf-8"))
        st["library_old_urls_today"] = {"a.com": {"not found": 1, "redirects to the current page": 1}}
        json.dump(st, open(path, "w", encoding="utf-8"))
        flat = [" | ".join(str(c) for c in r) for r in summ.build(d, {"sites": ["a.com"]}, "2026-11-04")["values"]]
        rows = [r for r in flat if "return 404 instead of redirecting" in r]
        self.assertEqual(len(rows), 1)  # one line in the agents' lists: a count and where the full map is
        self.assertIn("| 1 |", rows[0])
        self.assertIn("library/library-old-urls.csv", rows[0])
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
