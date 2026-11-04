"""Measure any audit PDF, whoever built it (Claude, Muse, Codex, ChatGPT, a person).

These are the numbers that separated Claude's October audits from the thin cheap-lane
drafts, measured from the PDFs themselves (see docs/CALIBRATION.md):

  metric                          Claude audits    thin drafts
  words per page (mean)           460-473          200-270
  numbers per page                95-100           8-38
  pages with >= 3 cited ids       20 of 20         0-3 of 20
  thin pages (< 150 words)        0                0-8

They are review triggers, not proof of quality: a page can be dense and wrong. Use them to
catch the outline-expanded-to-twenty-pages failure before a reviewer spends tokens.
"""
from __future__ import annotations

import re
import subprocess

FOOT = re.compile(r"Evidence (?:on this page|this page)[^:]*:(.*)", re.I)
IDTOK = re.compile(r"\b([A-Z]{1,2}(?:-[A-Z])?)-?(\d{1,4})(?:\s*[–—-]\s*\1?-?(\d{1,4}))?\b")
INLINE_ID = re.compile(r"\b[A-Z]{1,2}(?:-[A-Z])?-?\d{2,4}\b")
WORD = re.compile(r"[A-Za-z][A-Za-z'\-]+")
NUM = re.compile(r"(?<![A-Za-z])[\$#]?\d[\d,\.]*%?")

BANDS = {  # minimums for each grade
    "frontier": {"words": 380, "numbers": 45, "cited_pages": 18, "thin": 0},
    "solid": {"words": 280, "numbers": 25, "cited_pages": 10, "thin": 1},
}


def _page_text(pdf: str, i: int) -> str:
    return subprocess.run(["pdftotext", "-layout", "-f", str(i), "-l", str(i), pdf, "-"],
                          capture_output=True, text=True).stdout


def _footer_ids(text: str) -> set[str]:
    ids: set[str] = set()
    for line in text.splitlines():
        m = FOOT.search(line)
        if not m:
            continue
        for pre, a, b in IDTOK.findall(m.group(1)):
            a, b = int(a), int(b) if b else int(a)
            if b - a > 200:
                b = a
            ids.update(f"{pre}{k}" for k in range(a, b + 1))
    return ids


def measure(pdf: str) -> dict:
    from pypdf import PdfReader

    reader = PdfReader(pdf)
    n = len(reader.pages)
    texts = [_page_text(pdf, i) for i in range(1, n + 1)]
    w = [len(WORD.findall(t)) for t in texts]
    cited = []
    for t in texts:
        ids = _footer_ids(t) or set(INLINE_ID.findall(t))
        cited.append(len(ids))
    links = 0
    for pg in reader.pages:
        for a in pg.get("/Annots") or []:
            a = a.get_object()
            if a.get("/Subtype") == "/Link" and a.get("/A") and a["/A"].get("/URI"):
                links += 1
    alltext = "\n".join(texts)
    m = {
        "pages": n,
        "words_per_page": round(sum(w) / n, 1) if n else 0,
        "numbers_per_page": round(len(NUM.findall(alltext)) / n, 1) if n else 0,
        "pages_with_3plus_ids": sum(1 for c in cited if c >= 3),
        "thin_pages": sum(1 for x in w if x < 150),
        "link_annotations": links,
        "words_by_page": w,
    }
    m["grade"] = grade(m)
    return m


def grade(m: dict) -> str:
    scale = 20 / m["pages"] if m.get("pages") else 1
    for name, b in BANDS.items():
        if (m["words_per_page"] >= b["words"] and m["numbers_per_page"] >= b["numbers"]
                and m["pages_with_3plus_ids"] * scale >= b["cited_pages"] and m["thin_pages"] <= b["thin"]):
            return name
    return "thin"
