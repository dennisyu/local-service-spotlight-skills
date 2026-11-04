#!/usr/bin/env python3
"""Render LIBRARY-MAP.md from a values export of a library sheet's Library Map tab.

The library sheet is the master. This script turns a plain export of its
*Library Map* tab into the dated Markdown copy that agents without Google access
read. Nobody edits the Markdown by hand: export the tab, run this, commit.

Input: a JSON file holding either the raw Sheets "values.get" response
({"range": "...", "values": [[...], ...]}) or just the list of rows.
The header row is the first row whose first cell is "#" (row 4 in the template).

Usage:
    python3 render_library_map.py MAP.json --out LIBRARY-MAP.md \
        [--sheet-id SPREADSHEET_ID] [--title "Your Library"] [--date 2026-11-04] [--by "the library agent"]

--sheet-id shortens links that point back into the same spreadsheet to
"(this sheet, tab gid N)", because readers of the copy usually cannot open them.

Standard library only.
"""
import argparse
import datetime as dt
import json
import re
import sys

HEADER_FIRST_CELL = "#"
# Columns shown in the Markdown copy, by header text in the sheet.
WANTED = [
    ("#", "#"),
    ("Kind", "Kind"),
    ("Collection (what it holds)", "Collection"),
    ("Status", "Status"),
    ("Where it lives", "Master lives in"),
    ("If two places disagree, this wins", "If two places disagree, this wins"),
    ("Rows now (live count)", "Rows now"),
    ("Owner: function → who today", "Owner (function → who today)"),
    ("Next action", "Next action"),
]


def sheet_url_re(sheet_id):
    if not sheet_id:
        return None
    return re.compile(r"https://docs\.google\.com/spreadsheets/d/%s/edit[^\s#]*#gid=(\d+)" % re.escape(sheet_id))


def load_rows(path):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    rows = data.get("values") if isinstance(data, dict) else data
    if not isinstance(rows, list) or not rows:
        raise SystemExit("render_library_map: no rows found in %s" % path)
    return rows


def find_header(rows):
    for i, row in enumerate(rows):
        if row and str(row[0]).strip() == HEADER_FIRST_CELL:
            return i
    raise SystemExit("render_library_map: header row starting with '#' not found")


def cell(text, url_re=None):
    """Make one sheet cell safe for a Markdown table cell."""
    text = str(text if text is not None else "").strip()
    if url_re is not None:
        text = url_re.sub(r"(this sheet, tab gid \1)", text)
    text = text.replace("|", "\\|").replace("\r", " ").replace("\n", " ")
    return re.sub(r"\s{2,}", " ", text)


def render(rows, date, by, sheet_id="", title="the library sheet"):
    h = find_header(rows)
    header = [str(c).strip() for c in rows[h]]
    index = {}
    for name, _label in WANTED:
        if name not in header:
            raise SystemExit("render_library_map: column %r missing from header %r" % (name, header))
        index[name] = header.index(name)
    body = [r for r in rows[h + 1:] if r and str(r[0]).strip()]
    url_re = sheet_url_re(sheet_id)
    lines = [
        "# Library Map — snapshot",
        "",
        "**This is a dated copy of the *Library Map* tab in %s.** The sheet tab is the master; this copy "
        "exists so agents without access to the sheet can read the map. If they differ, the sheet wins. "
        "Generated %s by %s with `render_library_map.py`; do not edit by hand." % (title, date, by),
        "",
        "Status words: **MASTER** = update it there · **LENS** = generated, never type in it · "
        "**LEGACY** = frozen history, read only · **EXTERNAL MASTER** = the master lives outside the sheet.",
        "",
        "| " + " | ".join(label for _n, label in WANTED) + " |",
        "|" + "---|" * len(WANTED),
    ]
    for r in body:
        vals = []
        for name, _label in WANTED:
            i = index[name]
            vals.append(cell(r[i] if i < len(r) else "", url_re))
        lines.append("| " + " | ".join(vals) + " |")
    lines += ["", "%d collections." % len(body), ""]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("export", help="JSON export of the Library Map tab")
    ap.add_argument("--out", default="LIBRARY-MAP.md")
    ap.add_argument("--sheet-id", default="", help="spreadsheet id whose own links are shortened")
    ap.add_argument("--title", default="the library sheet", help="how to name the sheet in the header")
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--by", default="the library agent")
    a = ap.parse_args(argv)
    text = render(load_rows(a.export), a.date, a.by, a.sheet_id, a.title)
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write(text)
    print("wrote %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
