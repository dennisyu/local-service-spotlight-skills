# -*- coding: utf-8 -*-
"""Render a page-1 HTML one-pager to a print-ready PDF with headless Chromium.

Usage:
    python3 render_pdf.py <in.html> <out.pdf>

Uses Playwright's bundled/where-configured Chromium. In this environment Chromium
is pre-installed (PLAYWRIGHT_BROWSERS_PATH is set) so do NOT run
`playwright install`. Prints margins/background match the @page CSS in the HTML.
"""
import sys
from playwright.sync_api import sync_playwright

def render(in_html, out_pdf):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("file://" + in_html)
        page.pdf(path=out_pdf, format="Letter", print_background=True,
                 margin={"top": "0.42in", "bottom": "0.42in", "left": "0.5in", "right": "0.5in"})
        browser.close()
    print("wrote", out_pdf)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python3 render_pdf.py <in.html> <out.pdf>"); sys.exit(1)
    import os
    render(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]))
