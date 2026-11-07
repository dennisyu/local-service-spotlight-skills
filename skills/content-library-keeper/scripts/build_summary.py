#!/usr/bin/env python3
"""Build the one-screen summary grid for a library sheet from published_inventory.py outputs.

The grid is the tab people glance at: counts per site, topics, one line per list
the agents work (how many items, which agent works it, where its rows are), and
the sitemap defects, one row per kind. It is management by exception: the rows of
every list stay in the repository files the agents read and work, and nobody is
handed a list to work by hand. Every count comes from inventory-stats.json, the
record of the run that made the files, so a list the run did not check says
"not checked this run" instead of showing an old count. The grid is generated:
rebuild it, never type into it. Output is a Sheets-style values grid plus the row
numbers of the section and column headers, so an agent can clear the tab, write
the grid and format it in one pass. "merge_rows" lists the only rows that may be
merged across the tab (their row has a single cell); merging any other header row
would delete its column labels.

    python3 build_summary.py --inventory library --config inventory-config.json \
        --out summary-tab.json [--date 2026-11-04]

Row 1 carries the date of the inventory run (inventory-stats.json "generated_utc";
--date only when the stats have none). The hash ("sha256") covers every row except
that dated first row, so the same data gives the same hash. When --out already holds a grid with
the same hash, the file is left untouched and the printed result says
"changed": false: leave the sheet tab alone too.

Optional config keys (same file as published_inventory.py):
  "summary": {
    "title": "PUBLISHED PAGES · COUNTS AND THE LISTS AGENTS WORK",
    "full_list_location": "GitHub owner/repo, folder library/",
    "rename_label": "Titles still using the old name",
    "rename_list_label": "Titles that still use the retired name",
    "list_repo_label": "GitHub owner/repo, folder library/",
    "withhold_titles": [{"url_contains": "some-slug", "label": "(title withheld here: see the full list)"}],
    "worklist_owners": {"rename": "library agent", "people": "content agent", "old_addresses": "redirect job",
                        "sitemap": "website agent"}
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
import sys
from collections import Counter

DEFAULTS = {
    "title": "PUBLISHED PAGES · COUNTS AND THE LISTS AGENTS WORK",
    "full_list_location": "the repository file library/published-inventory.csv",
    "rename_label": "Titles still using the old name",
    "rename_list_label": "Titles that still use the retired name",
    "list_repo_label": "the repository's library folder",
    "withhold_titles": [],
    "worklist_owners": {},
}
NOT_CHECKED = "not checked this run"
LINK_WITHHELD = "(link withheld here: see the full list)"
NOT_IN_SITEMAP_FILE = "library-rows-not-in-sitemap.csv"
TODAY_ORDER = [
    "loads, but is missing from the sitemap",
    "redirects to a page in the sitemap",
    "redirects to a page not in the sitemap",
    "redirects to the home page",
    "not found",
    "needs a login or is blocked",
    "no answer",
    "points at a Google file, not a page",
    "points at another site",
    "not checked",
]
LIVE_UNLISTED = TODAY_ORDER[0]
STATUS_FROM_REST = "published (REST API; not opened)"  # same words as published_inventory.STATUS_FROM_REST


def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def withheld(url, rules):
    """The label to show instead of a row's title when a withhold rule matches its address, else None."""
    for r in rules:
        if r.get("url_contains") and r["url_contains"] in (url or ""):
            return r.get("label") or "(title withheld here)"
    return None


def grid_hash(grid):
    """Hash of the grid without its first row, which carries the build date."""
    return hashlib.sha256(json.dumps(grid[1:], ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


class SummaryError(RuntimeError):
    """The inventory files needed for the summary are missing."""


def site_names(cfg):
    return [x for x in (cfg.get("sites") or []) if isinstance(x, str) and x]


def build(inv_dir, cfg, date):
    s = {**DEFAULTS, **(cfg.get("summary") or {})}
    owners = s.get("worklist_owners") or {}
    def owner(key):
        return f" Worked by: {owners[key]}." if owners.get(key) else ""
    rules = s["withhold_titles"]
    stats_path = os.path.join(inv_dir, "inventory-stats.json")
    try:
        with open(stats_path, encoding="utf-8") as fh:
            stats = json.load(fh)
    except (OSError, ValueError) as e:
        raise SummaryError(f"no readable {stats_path} ({e}); run the inventory first")
    pages = read_csv(os.path.join(inv_dir, "published-inventory.csv"))
    sites = site_names(cfg) or sorted({p["site"] for p in pages})
    not_listed = read_csv(os.path.join(inv_dir, NOT_IN_SITEMAP_FILE))
    def count(st):
        return st.get("pages_in_sitemaps", 0)
    total = sum(count(stats.get(x, {})) for x in sites)
    if stats.get("generated_utc"):
        date = stats["generated_utc"][:10]

    grid, headers, colheads = [], [], []
    def add(row=None):
        grid.append(list(row) if row else [])
        return len(grid)

    # The sitemap defects are worked out first: section C counts them and section D lists them.
    defects = []
    for site in sites:
        rep = [p for p in pages if p["site"] == site and "x in sitemaps" in (p.get("notes") or "")]
        if rep:
            ex = [p for p in rep if not p["url"].rstrip("/").endswith(site)][:2] or rep[:1]
            def times(p):
                for part in (p.get("notes") or "").split(" | "):
                    if part.startswith("listed "):
                        return part.split()[1]
                return ""
            defects.append([site, "Same page listed more than once in the sitemaps. Full list: the notes column of published-inventory.csv",
                            len(rep), ", ".join(f"{LINK_WITHHELD if withheld(p['url'], rules) else p['url']} ({times(p)})" for p in ex)])
        # One row per kind of defect, with a count and at most two examples: the full list
        # stays in the repository file the row names.
        groups = {}
        for p in pages:
            if p["site"] == site and p.get("status") not in ("200", "in sitemap", STATUS_FROM_REST, "", None):
                what = ("Listed in sitemap but did not answer" if p["status"] == "unreachable"
                        else f"Listed in sitemap but returns HTTP {p['status']}")
                groups.setdefault(what + ". Full list: the status column of published-inventory.csv", []).append(p["url"])
        private = []
        for r in not_listed:
            if r["site"] != site or r.get("today") != LIVE_UNLISTED:
                continue
            if "private" in (r.get("status_in_library") or "").lower():
                private.append(r["url"])  # meant to be gone, yet it loads: a privacy check, never a sitemap fix
            elif not withheld(r.get("url"), rules):
                groups.setdefault("Page loads but is missing from the sitemap. Full list: the today column of "
                                  "library-rows-not-in-sitemap.csv", []).append(r["url"])
        for what, urls in groups.items():
            shown = [u for u in urls if not withheld(u, rules)][:2]
            defects.append([site, what, len(urls), ", ".join(shown) if shown else LINK_WITHHELD])
        if private:
            defects.append([site, "A page the old list marks Private loads for anyone. Check that it is meant to be "
                                  "public; do not add it to the sitemap. Full list: library-rows-not-in-sitemap.csv",
                            len(private), LINK_WITHHELD])

    add([f"{s['title']} (generated {date} from each site's sitemap)"])
    add([f"A quick look for people: how many pages each site has, and which agent works each list. The lists themselves are in "
         f"{s['full_list_location']}, where the agents read and work them; a person is asked only for what an agent cannot do. "
         "Do not type here; the library agent regenerates this tab."])
    add()

    # A. by site
    headers.append(add(["A. BY SITE", "URLs in sitemaps", "Posts", "Pages", "Pages with video", s["rename_label"],
                        "Listed twice in sitemaps", "Not HTTP 200 (pages opened one by one)"]))
    sums = [0] * 7
    for site in sites:
        st = stats.get(site, {})
        bt = st.get("by_type", {})
        vals = [count(st), bt.get("post", 0), bt.get("page", 0), st.get("with_video", 0),
                st.get("rename_hits", 0) if stats.get("rename_pattern") else NOT_CHECKED,
                st.get("listed_twice_or_more", 0), st.get("non_200", 0)]
        sums = [a + b if isinstance(a, int) and isinstance(b, int) else NOT_CHECKED for a, b in zip(sums, vals)]
        add([site] + vals)
    total_row = add([f"All {len(sites)} sites" if len(sites) != 1 else "Total"] + sums)
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

    # C. the lists the agents work: a count and an owner each, never the rows themselves. Every count is
    # read from the stats of the run that wrote the files; a list that run did not check says so.
    renamed = sum(stats.get(x, {}).get("rename_hits", 0) for x in sites) if stats.get("rename_pattern") else NOT_CHECKED
    kept = sum(stats.get(x, {}).get("rename_kept", 0) for x in sites) if stats.get("rename_pattern") else 0
    rename_what = s["rename_list_label"] + (f" ({kept} more keep the name on purpose: a domain, history, a registered app)"
                                            if kept else "")
    gaps = (stats["people"].get("real_with_no_title_page", 0) if isinstance(stats.get("people"), dict) else NOT_CHECKED)
    old_404 = (sum(v.get("not found", 0) for v in (stats.get("library_old_urls_today") or {}).values())
               if stats.get("library_matching") and stats.get("library_old_urls_checked", True) else NOT_CHECKED)
    headers.append(add(["C. LISTS THE AGENTS WORK", "Items", "Worked by", f"Full list ({s['list_repo_label']})"]))
    for what, n, key, where in (
            (rename_what, renamed, "rename", f"library/{cfg.get('rename_file') or 'rename-worklist.csv'}"),
            ("People we know with no page naming them (real relationships, most relationship sources first)", gaps,
             "people", "library/people-coverage.csv"),
            ("Old dated addresses that return 404 instead of redirecting to the page", old_404, "old_addresses",
             "library/library-old-urls.csv"),
            ("Sitemap defects (listed in section D)", sum(int(r[2]) for r in defects), "sitemap",
             "library/published-inventory.csv (status and notes columns)")):
        add([what, n, owners.get(key, ""), where if n != NOT_CHECKED else "(not rebuilt this run)"])
    add()

    # D. sitemap defects: the only rows small and urgent enough to list
    opened = sum(stats.get(x, {}).get("pages_opened", 0) for x in sites)
    scope = (f" Pages opened one by one this run: {opened:,} of {total:,}; the rest came from the WordPress REST API, "
             "so their status was not checked page by page.") if opened and opened < total else ""
    headers.append(add(["D. SITEMAP DEFECTS." + scope + owner("sitemap")]))
    colheads.append(add(["Site", "Defect", "Count", "Example"]))
    for row in defects:
        add(row)
    if not defects:
        add(["(none)"])
    # Rows whose single cell may be merged across the tab. A header row with more than one
    # cell (A, B, C) carries column labels: merging it would delete them.
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
    try:
        out = build(a.inventory, cfg, a.date)
    except SummaryError as e:
        print(f"STOPPED, nothing written: {e}", file=sys.stderr)
        return 2
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
