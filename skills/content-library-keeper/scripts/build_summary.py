#!/usr/bin/env python3
"""Build the summary-and-worklists grid for a library sheet from published_inventory.py outputs.

The grid is the tab people actually read: counts per site, topics, and the short
worklists they act on. It is generated, so it is rebuilt from the inventory files,
never typed into. Output is a Sheets-style values grid plus the row numbers of the
section and column headers, so an agent can clear the tab, write the grid, and
re-apply bold headers in one pass. "merge_rows" lists the only rows that may be
merged across the tab (their row has a single cell); merging any other header row
would delete its column labels.

    python3 build_summary.py --inventory library --config inventory-config.json \
        --out summary-tab.json [--date 2026-11-04]

The hash ("sha256") covers every row except the dated first row, so building the
same data on another day gives the same hash. When --out already holds a grid with
the same hash, the file is left untouched and the printed result says
"changed": false: leave the sheet tab alone too.

Optional config keys (same file as published_inventory.py):
  "summary": {
    "title": "PUBLISHED PAGES · SUMMARY AND WORKLISTS",
    "full_list_location": "GitHub: owner/repo, file library/published-inventory.csv",
    "rename_label": "Titles still using the old name",
    "rename_note": "C. RENAME WORKLIST — ...",
    "rename_site_order": ["site-a.com", "site-b.com"],
    "registry_label": "the people registry",
    "withhold_titles": [{"url_contains": "some-slug", "label": "(title withheld here: see the full list)"}],
    "vault_label": "In Obsidian vault",
    "section_owners": {"C": "content desk", "D": "relationships", "E": "library agent", "F": "website desk"}
  }

A withhold rule hides the title and the address (and any redirect target) of every
matching row, so a sensitive page is not named in a tab many people read.

Standard library only. Reads local files; no network.
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import re
import sys
from collections import Counter

DEFAULTS = {
    "title": "PUBLISHED PAGES · SUMMARY AND WORKLISTS",
    "full_list_location": "the repository file library/published-inventory.csv",
    "rename_label": "Titles matching the rename pattern",
    "rename_note": "C. RENAME WORKLIST — live pages whose title still uses a retired name. Check each one: product names and history posts may stay.",
    "rename_site_order": [],
    "registry_label": "the people registry",
    "withhold_titles": [],
    "vault_label": "In notes vault",
    "section_owners": {},
}
SHEET_LINK_NOTE = "(old tab linked to this spreadsheet instead of the article)"
LINK_WITHHELD = "(link withheld here: see the full list)"
NOT_IN_SITEMAP_FILES = ("library-rows-not-in-sitemap.csv", "library-rows-not-live.csv")  # new name, then old
TODAY_ORDER = [
    "loads, but is missing from the sitemap",
    "redirects to a page in the sitemap",
    "redirects to a page not in the sitemap",
    "redirects to the home page",
    "not found",
    "needs a login or is blocked",
    "no answer",
    "points at a Google file, not a page",
    "not checked",
]
LIVE_UNLISTED = TODAY_ORDER[0]


def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def tidy(title):
    """Clean a title for people to read: collapse spaces, drop '????' left where an old export lost emoji,
    and a stray trailing inch mark."""
    t = " ".join(str(title or "").split())
    t = re.sub(r"(^|\s)\?{2,}(?=\s|$)", " ", t).strip()
    return re.sub(r"[″]+$", "", t).strip()


def withheld(url, rules):
    """The label to show instead of a row's title when a withhold rule matches its address, else None."""
    for r in rules:
        if r.get("url_contains") and r["url_contains"] in (url or ""):
            return r.get("label") or "(title withheld here)"
    return None


def withhold(title, url, rules):
    """The title to show: the rule's label when a withhold rule matches the address, else the title."""
    return withheld(url, rules) or title


def grid_hash(grid):
    """Hash of the grid without its first row, which carries the build date."""
    return hashlib.sha256(json.dumps(grid[1:], ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def build(inv_dir, cfg, date):
    s = {**DEFAULTS, **(cfg.get("summary") or {})}
    owners = s.get("section_owners") or {}
    def owner(section):
        return f" Owner: {owners[section]}." if owners.get(section) else ""
    rules = s["withhold_titles"]
    sites = list(cfg.get("sites") or [])
    stats = json.load(open(os.path.join(inv_dir, "inventory-stats.json"), encoding="utf-8"))
    pages = read_csv(os.path.join(inv_dir, "published-inventory.csv"))
    if not sites:
        sites = sorted({p["site"] for p in pages})
    rename_rows = read_csv(os.path.join(inv_dir, cfg.get("rename_file") or "rename-worklist.csv"))
    people = read_csv(os.path.join(inv_dir, "people-coverage.csv"))
    not_listed = []
    for name in NOT_IN_SITEMAP_FILES:
        not_listed = read_csv(os.path.join(inv_dir, name))
        if not_listed:
            break
    not_listed_counts = stats.get("library_rows_not_in_sitemap", stats.get("library_rows_not_live", {}))
    old_urls = read_csv(os.path.join(inv_dir, "library-old-urls.csv"))
    def count(st):
        return st.get("pages_in_sitemaps", st.get("live_urls", 0))
    total = sum(count(stats.get(x, {})) for x in sites)

    grid, headers, colheads = [], [], []
    def add(row=None):
        grid.append(list(row) if row else [])
        return len(grid)

    add([f"{s['title']} (generated {date} from each site's sitemap)"])
    add([f"The full list of all {total:,} pages listed in the sitemaps, with titles, dates, topics and people named, "
         f"is in {s['full_list_location']}. This tab holds the counts and the lists people act on. "
         "Do not type here; the library agent regenerates it."])
    add()

    # A. by site
    headers.append(add(["A. BY SITE", "URLs in sitemaps", "Posts", "Pages", "Pages with video", "In old library tabs",
                        "Missing from old tabs", "Old-tab rows not in sitemap", s["rename_label"],
                        "Listed twice in sitemaps"]))
    sums = [0] * 9
    for site in sites:
        st = stats.get(site, {})
        bt = st.get("by_type", {})
        vals = [count(st), bt.get("post", 0), bt.get("page", 0), st.get("with_video", 0),
                st.get("in_library", 0), st.get("missing_from_library", 0), not_listed_counts.get(site, 0),
                st.get("rename_hits", st.get("blitz_in_title", 0)), st.get("listed_twice_or_more", 0)]
        sums = [a + b for a, b in zip(sums, vals)]
        add([site] + vals)
    total_row = add(["All sites" if len(sites) != 4 else "All four sites"] + sums)
    add()

    # B. topics
    headers.append(add(["B. TOPICS (first-pass keyword tags v1; a page can have several)", "Pages"]))
    tc = Counter()
    none = 0
    for p in pages:
        tags = [t for t in (p.get("topics_v1") or "").split("; ") if t]
        none += not tags
        tc.update(tags)
    for name, n in sorted(tc.items(), key=lambda kv: (-kv[1], kv[0])):
        add([name, n])
    add(["(no topic matched yet)", none])
    add()

    # C. rename worklist
    headers.append(add([s["rename_note"] + owner("C")]))
    colheads.append(add(["Site", "Title", "URL", "Published"]))
    order = s["rename_site_order"] or sites
    rank = {site: i for i, site in enumerate(order)}
    by_date = sorted(rename_rows, key=lambda r: r.get("published") or "", reverse=True)
    for r in sorted(by_date, key=lambda r: rank.get(r["site"], len(rank))):  # stable: newest first within a site
        hidden = withheld(r["url"], rules)
        add([r["site"], hidden or tidy(r["title"]), LINK_WITHHELD if hidden else r["url"], r.get("published", "")])
    add()

    # D. people with no page
    headers.append(add([f"D. PEOPLE WE KNOW WITH NO PAGE NAMING THEM — real relationships in {s['registry_label']} "
                        "whose name is in no live page title (honor them next). More sources = stronger relationship evidence."
                        + owner("D")]))
    colheads.append(add(["Name", "Where we know them from", s["vault_label"], "In fleet memory"]))
    gaps = [p for p in people if p.get("real_relationship") == "Y" and str(p.get("pages_with_name_in_title")) == "0"]
    def nsrc(p):
        return len([x for x in (p.get("relationship_sources") or "").split(",") if x.strip()])
    # Strongest evidence first: more sources, then already in the notes vault, then by name.
    for p in sorted(gaps, key=lambda p: (-nsrc(p), p.get("in_vault") != "y", p["name"])):
        add([p["name"], p.get("relationship_sources", ""), p.get("in_vault", ""), p.get("in_fleet_memory", "")])
    add()

    # E. old rows in no sitemap, with what each address does today
    headers.append(add(["E. OLD LIBRARY ROWS IN NO SITEMAP — what each address did when the inventory last ran. "
                        "Redirects: point the row at the new address. Not found: restore the page or retire the row. "
                        "Loads: the page exists but search engines may not find it (see section F)." + owner("E")]))
    colheads.append(add(["Site", "Title", "URL in old tab", "What it does today", "Status in old tab"]))
    def today_rank(r):
        t = r.get("today") or "not checked"
        return TODAY_ORDER.index(t) if t in TODAY_ORDER else len(TODAY_ORDER) - 1
    for r in sorted(not_listed, key=today_rank):  # stable: file order within a group
        url = r.get("url", "")
        hidden = withheld(url, rules)
        today = r.get("today") or "not checked"
        if r.get("final_url") and today.startswith("redirects"):
            today = f"{today}: {LINK_WITHHELD if hidden else r['final_url']}"
        shown = SHEET_LINK_NOTE if "docs.google.com/spreadsheets" in url else url
        add([r["site"], hidden or tidy(r.get("title", "")), LINK_WITHHELD if hidden else shown, today,
             r.get("status_in_library", "")])
    add()

    # F. sitemap defects
    headers.append(add(["F. SITEMAP DEFECTS FOR THE WEBSITE DESK" + owner("F")]))
    colheads.append(add(["Site", "Defect", "Count", "Example"]))
    for site in sites:
        rep = [p for p in pages if p["site"] == site and "x in sitemaps" in (p.get("notes") or "")]
        if rep:
            ex = [p for p in rep if not p["url"].rstrip("/").endswith(site)][:2] or rep[:1]
            def times(p):
                for part in (p.get("notes") or "").split(" | "):
                    if part.startswith("listed "):
                        return part.split()[1]
                return ""
            add([site, "Same page listed more than once in the sitemaps. Full list: the notes column of published-inventory.csv",
                 len(rep), ", ".join(f"{LINK_WITHHELD if withheld(p['url'], rules) else p['url']} ({times(p)})" for p in ex)])
        for p in pages:
            if p["site"] == site and p.get("status") not in ("200", "in sitemap", "", None):
                what = ("Listed in sitemap but did not answer" if p["status"] == "unreachable"
                        else f"Listed in sitemap but returns HTTP {p['status']}")
                add([site, what, 1, LINK_WITHHELD if withheld(p["url"], rules) else p["url"]])
        for what, label in (("not found", "Old addresses of moved pages return 404 instead of redirecting to the page "
                                         "(old permalinks). Full list with each page's address now: library-old-urls.csv"),
                            ("redirects somewhere else", "Old addresses of moved pages redirect somewhere other than the page. "
                                                        "Full list: library-old-urls.csv")):
            bad = [r for r in old_urls if r["site"] == site and r.get("today") == what and not withheld(r.get("old_url"), rules)]
            if bad:
                add([site, label, len(bad), ", ".join(f"{r['old_url']} → {r['current_url']}" for r in bad[:2])])
        for r in not_listed:
            if r["site"] == site and r.get("today") == LIVE_UNLISTED and not withheld(r.get("url"), rules):
                add([site, "Page loads but is missing from the sitemap (an old library row points at it)", 1, r["url"]])
    # Rows whose single cell may be merged across the tab. A header row with more than one
    # cell (A. BY SITE, B. TOPICS) carries column labels: merging it would delete them.
    merge_rows = [1, 2] + [h for h in headers if len(grid[h - 1]) == 1]
    return {"generated": date, "values": grid, "section_header_rows": headers, "column_header_rows": colheads,
            "merge_rows": merge_rows, "total_row": total_row, "rows": len(grid), "sha256": grid_hash(grid)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--inventory", required=True, help="folder holding published_inventory.py outputs")
    ap.add_argument("--config", help="the same JSON config published_inventory.py uses")
    ap.add_argument("--out", required=True)
    ap.add_argument("--date", default=dt.date.today().isoformat())
    a = ap.parse_args(argv)
    cfg = {}
    if a.config:
        with open(a.config, encoding="utf-8") as fh:
            cfg = json.load(fh)
    out = build(a.inventory, cfg, a.date)
    old = None
    if os.path.exists(a.out):
        try:
            with open(a.out, encoding="utf-8") as fh:
                old = json.load(fh)
        except ValueError:
            old = None
    def meaning(d):  # everything except the build date and the dated first row (the hash covers the rest)
        return {k: v for k, v in d.items() if k not in ("generated", "values")}
    changed = not (isinstance(old, dict) and meaning(old) == meaning(out))
    if changed:
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=1)
    print(json.dumps({"changed": changed, **{k: v for k, v in out.items() if k != "values"}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
