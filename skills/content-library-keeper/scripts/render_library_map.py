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

When --out already holds the same map and only the "Generated <date>" line would
change, the file is left untouched, so a day with no map change leaves nothing
to commit.

Standard library only.
"""
import argparse
import datetime as dt
import json
import os
import re
import sys

HEADER_FIRST_CELL = "#"
# Columns shown in the Markdown copy: (header text in the sheet, label in the copy, required).
# A header matches exactly or with a parenthesised suffix, e.g. "Freshness (checked 2026-11-04)".
# A label of None means "use the sheet's own header text".
WANTED = [
    ("#", "#", True),
    ("Kind", "Kind", True),
    ("Collection (what it holds)", "Collection", True),
    ("Status", "Status", True),
    ("Where it lives", "Master lives in", True),
    ("If two places disagree, this wins", "If two places disagree, this wins", True),
    ("Rows now (live count)", "Rows now", True),
    ("Owner: function → who today", "Owner (function → who today)", True),
    ("Factory stage · Triangle", "Factory stage · Triangle", False),
    ("Freshness", None, False),
    ("Next action", "Next action", True),
]
DATE_LINE = re.compile(r"Generated \d{4}-\d{2}-\d{2} by ")


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


def find_column(header, name):
    """Index of the header cell named `name`, allowing a parenthesised suffix; None if absent."""
    if name in header:
        return header.index(name)
    for i, h in enumerate(header):
        if h.startswith(name + " ("):
            return i
    return None


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
    columns = []  # (index in the row, label)
    for name, label, required in WANTED:
        i = find_column(header, name)
        if i is None:
            if required:
                raise SystemExit("render_library_map: column %r missing from header %r" % (name, header))
            continue
        columns.append((i, label or header[i]))
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
        "| " + " | ".join(label for _i, label in columns) + " |",
        "|" + "---|" * len(columns),
    ]
    for r in body:
        lines.append("| " + " | ".join(cell(r[i] if i < len(r) else "", url_re) for i, _label in columns) + " |")
    lines += ["", "%d collections." % len(body), ""]
    return "\n".join(lines)


def same_but_date(a, b):
    """True when two renders differ at most in their "Generated <date>" line."""
    return DATE_LINE.sub("Generated <date> by ", a) == DATE_LINE.sub("Generated <date> by ", b)


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
    if os.path.exists(a.out):
        with open(a.out, encoding="utf-8") as fh:
            if same_but_date(fh.read(), text):
                print("unchanged %s" % a.out)
                return 0
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write(text)
    print("wrote %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
