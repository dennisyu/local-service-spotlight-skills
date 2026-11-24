#!/usr/bin/env python3
"""Check that the public install guide matches the released marketplace manifest.

    python3 scripts/check_install_guide.py                       # fetch the live guide
    python3 scripts/check_install_guide.py --html-file page.html # offline check

The audit acceptance tests say a reachable but stale install guide fails: the guide
must name the repository, the lss-everything bundle, and the same released version
and master-skill count as .claude-plugin/marketplace.json. A Nov 2026 audit run
found the guide one minor version behind; this makes that a one-command check.
Exit 0 = matches; 1 = stale or missing facts; 2 = fetch failed.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GUIDE_URL = "https://localservicespotlight.com/install/"
REPO = "github.com/dennisyu/local-service-spotlight-skills"
BUNDLE = "lss-everything"


def manifest_facts(root: Path = ROOT) -> dict:
    data = json.loads((root / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    version = (data.get("metadata") or {}).get("version") or data.get("version")
    bundle = next((p for p in data.get("plugins", []) if p.get("name") == BUNDLE), {})
    skills = bundle.get("skills")
    return {"version": version, "skill_count": len(skills) if isinstance(skills, list) else None}


def page_text(raw: str) -> str:
    raw = re.sub(r"<(script|style)\b.*?</\1>", " ", raw, flags=re.S | re.I)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", raw)))


def compare(text: str, facts: dict) -> list[str]:
    problems = []
    if REPO not in text:
        problems.append(f"guide does not name {REPO}")
    if BUNDLE not in text:
        problems.append(f"guide does not name the {BUNDLE} bundle")
    versions = sorted(set(re.findall(r"(?<![\d.])\d+\.\d+\.\d+(?![\d.])", text)))
    if facts["version"] not in versions:
        problems.append(f"guide shows version(s) {versions or 'none'}; released manifest is {facts['version']}")
    counts = sorted({int(n) for n in re.findall(r"\b(\d+) (?:master )?skills\b", text)})
    if facts["skill_count"] is not None and facts["skill_count"] not in counts:
        problems.append(f"guide shows skill count(s) {counts or 'none'}; manifest lists {facts['skill_count']}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--url", default=GUIDE_URL)
    ap.add_argument("--html-file", type=Path)
    a = ap.parse_args()
    facts = manifest_facts()
    if a.html_file:
        raw = a.html_file.read_text(encoding="utf-8", errors="replace")
    else:
        try:
            req = urllib.request.Request(a.url, headers={"User-Agent": "Mozilla/5.0 (install-guide check)"})
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read().decode("utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001
            print(json.dumps({"state": "FETCH_FAILED", "url": a.url, "error": str(exc)[:200]}))
            return 2
    problems = compare(page_text(raw), facts)
    print(json.dumps({"state": "STALE" if problems else "MATCHES", "manifest": facts, "problems": problems}, indent=1))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
