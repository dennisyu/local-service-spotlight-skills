#!/usr/bin/env python3
"""Build the summary-and-worklists grid for a library sheet from published_inventory.py outputs.

The grid is the tab people actually read: counts per site, topics, and the short
worklists they act on. It is generated, so it is rebuilt from the inventory files,
never typed into. Output is a Sheets-style values grid plus the row numbers of the
section and column headers, so an agent can clear the tab, write the grid, and
re-apply bold headers in one pass.

    python3 build_summary.py --inventory library --config inventory-config.json \
        --out summary-tab.json [--date 2026-11-04]

Optional config keys (same file as published_inventory.py):
  "summary": {
    "title": "PUBLISHED PAGES · SUMMARY AND WORKLISTS",
    "full_list_location": "GitHub: owner/repo, file library/published-inventory.csv",
    "rename_label": "Titles still using the old name",
    "rename_note": "C. RENAME WORKLIST — ...",
    "rename_site_order": ["site-a.com", "site-b.com"],
    "registry_label": "the people registry",
    "withhold_titles": [{"url_contains": "some-slug", "label": "(title withheld here: see the full list)"}],
    "vault_label": "In Obsidian vault"
  }

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
}
SHEET_LINK_NOTE = "(old tab linked to this spreadsheet instead of the article)"


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


def withhold(title, url, rules):
    for r in rules:
        if r.get("url_contains") and r["url_contains"] in (url or ""):
            return r.get("label") or "(title withheld here)"
    return title


def build(inv_dir, cfg, date):
    s = {**DEFAULTS, **(cfg.get("summary") or {})}
    sites = list(cfg.get("sites") or [])
    stats = json.load(open(os.path.join(inv_dir, "inventory-stats.json"), encoding="utf-8"))
    pages = read_csv(os.path.join(inv_dir, "published-inventory.csv"))
    if not sites:
        sites = sorted({p["site"] for p in pages})
    rename_rows = read_csv(os.path.join(inv_dir, cfg.get("rename_file") or "rename-worklist.csv"))
    people = read_csv(os.path.join(inv_dir, "people-coverage.csv"))
    not_live = read_csv(os.path.join(inv_dir, "library-rows-not-live.csv"))
    total = sum(stats.get(x, {}).get("live_urls", 0) for x in sites)

    grid, headers, colheads = [], [], []
    def add(row=None):
        grid.append(list(row) if row else [])
        return len(grid)

    add([f"{s['title']} (generated {date} from each site's live sitemap)"])
    add([f"The full list of all {total:,} live pages, with titles, dates, topics and people named, is in "
         f"{s['full_list_location']}. This tab holds the counts and the lists people act on. "
         "Do not type here; the library agent regenerates it."])
    add()

    # A. by site
    headers.append(add(["A. BY SITE", "Live pages", "Posts", "Pages", "Pages with video", "In old library tabs",
                        "Missing from old tabs", "Old-tab rows no longer live", s["rename_label"],
                        "Listed twice in sitemaps"]))
    sums = [0] * 9
    for site in sites:
        st = stats.get(site, {})
        bt = st.get("by_type", {})
        vals = [st.get("live_urls", 0), bt.get("post", 0), bt.get("page", 0), st.get("with_video", 0),
                st.get("in_library", 0), st.get("missing_from_library", 0),
                stats.get("library_rows_not_live", {}).get(site, 0),
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
    headers.append(add([s["rename_note"]]))
    colheads.append(add(["Site", "Title", "URL", "Published"]))
    order = s["rename_site_order"] or sites
    rank = {site: i for i, site in enumerate(order)}
    by_date = sorted(rename_rows, key=lambda r: r.get("published") or "", reverse=True)
    for r in sorted(by_date, key=lambda r: rank.get(r["site"], len(rank))):  # stable: newest first within a site
        add([r["site"], withhold(tidy(r["title"]), r["url"], s["withhold_titles"]), r["url"], r.get("published", "")])
    add()

    # D. people with no page
    headers.append(add([f"D. PEOPLE WE KNOW WITH NO PAGE NAMING THEM — real relationships in {s['registry_label']} "
                        "whose name is in no live page title (honor them next). More sources = stronger relationship evidence."]))
    colheads.append(add(["Name", "Where we know them from", s["vault_label"], "In fleet memory"]))
    gaps = [p for p in people if p.get("real_relationship") == "Y" and str(p.get("pages_with_name_in_title")) == "0"]
    def nsrc(p):
        return len([x for x in (p.get("relationship_sources") or "").split(",") if x.strip()])
    # Strongest evidence first: more sources, then already in the notes vault, then by name.
    for p in sorted(gaps, key=lambda p: (-nsrc(p), p.get("in_vault") != "y", p["name"])):
        add([p["name"], p.get("relationship_sources", ""), p.get("in_vault", ""), p.get("in_fleet_memory", "")])
    add()

    # E. old rows no longer live
    headers.append(add(["E. OLD LIBRARY ROWS NO LONGER LIVE — the page is not in its site's sitemap now "
                        "(deleted, redirected, private or renamed). Check before reusing the link."]))
    colheads.append(add(["Site", "Title", "URL in old tab", "Status in old tab"]))
    for r in not_live:
        url = r.get("url", "")
        if "docs.google.com/spreadsheets" in url:
            url = SHEET_LINK_NOTE
        add([r["site"], withhold(tidy(r.get("title", "")), r.get("url", ""), s["withhold_titles"]), url,
             r.get("status_in_library", "")])
    add()

    # F. sitemap defects
    headers.append(add(["F. SITEMAP DEFECTS FOR THE WEBSITE DESK"]))
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
                 len(rep), ", ".join(f"{p['url']} ({times(p)})" for p in ex)])
        for p in pages:
            if p["site"] == site and p.get("status") not in ("200", "in sitemap", "", None):
                add([site, f"Listed in sitemap but returns HTTP {p['status']}", 1, p["url"]])
    body = json.dumps(grid, ensure_ascii=False, sort_keys=True)
    return {"generated": date, "values": grid, "section_header_rows": headers, "column_header_rows": colheads,
            "total_row": total_row, "rows": len(grid),
            "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest()}


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
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "values"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
