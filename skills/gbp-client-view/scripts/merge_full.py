# -*- coding: utf-8 -*-
"""Merge the page-1 one-pager PDF with the full MAA PDF into one deliverable.

Usage:
    python3 merge_full.py <page1.pdf> <maa.pdf> <out_full.pdf>

Page 1 is the client-facing executive summary; pages 2+ are the full MAA.
The MAA PDF is produced separately (e.g. exporting the agent's markdown report,
or the Google Doc, to PDF). Needs pypdf (`pip install pypdf`).
"""
import sys
from pypdf import PdfWriter, PdfReader

def merge(page1, maa, out):
    w = PdfWriter()
    for path in (page1, maa):
        r = PdfReader(path)
        for pg in r.pages:
            w.add_page(pg)
    with open(out, "wb") as f:
        w.write(f)
    print("wrote", out, "-", len(PdfReader(out).pages), "pages")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("usage: python3 merge_full.py <page1.pdf> <maa.pdf> <out_full.pdf>"); sys.exit(1)
    merge(sys.argv[1], sys.argv[2], sys.argv[3])
