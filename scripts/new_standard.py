#!/usr/bin/env python3
"""Scaffold a new house rule so capturing one costs a single command.

    python3 scripts/new_standard.py "No autoplay with sound" \
        --from "Dennis Yu, Cowork session, 2026-08-16" \
        --applies-to published-html --source https://blitzmetrics.com/...

Why this exists: the gap that loses knowledge is not disagreement about the
rule, it is the friction between hearing a rule and having a file that enforces
it. Every field this asks for is a field that makes the rule survive — above all
``--from``, because a rule with no traceable origin cannot be re-checked against
what was actually said.

The scaffold is deliberately un-mergeable: the body carries a sentinel that the
parser rejects, so a half-captured rule fails CI instead of sitting in
``standards/`` looking finished.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from standards_lib import SCOPES, SEVERITIES, SLUG_RE, STANDARDS_DIR  # noqa: E402


SENTINEL = "TODO(write-the-rule)"


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return re.sub(r"-{2,}", "-", slug)


def scaffold(
    title: str,
    slug: str,
    captured_from: str,
    severity: str,
    applies_to: list[str],
    source: str | None,
    captured: str,
) -> str:
    header = {
        "title": title,
        "severity": severity,
        "captured": captured,
        "captured_from": captured_from,
    }
    if source:
        header["source"] = source
    header["applies_to"] = applies_to
    if "published-html" in applies_to:
        header["checks"] = []

    body = f"""## {title}

- {SENTINEL}: state the rule in one sentence, in the imperative.
- Say *why* — the cost of breaking it, ideally the incident that produced it.
- Say how to get it right, concretely enough to act on without further reading.
- Name the exemption, if there is one, and how to mark it.
"""

    guidance = ""
    if "published-html" in applies_to:
        guidance = f"""
Fill in `checks` so the live sweep enforces this. Each check needs `id`, `kind`
(`forbid_regex`, `require_regex`, `resolve_urls`), `message`, `pattern`, and
`examples` with at least one `violating` and one `clean` sample. Then:

    python3 scripts/fleet_check.py --self-test

If an honest machine check is not possible, delete `checks` entirely and say so
in the body. A regex that covers nothing is worse than admitting nothing covers it.
"""

    return (
        "---\n"
        + json.dumps(header, indent=2, ensure_ascii=False)
        + "\n---\n\n"
        + body
        + guidance
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("title", help="the rule, in a few words")
    parser.add_argument(
        "--from",
        dest="captured_from",
        required=True,
        help="who said it, where, and when — required; provenance is how we see "
        "which channels are leaking",
    )
    parser.add_argument("--slug", help="override the derived filename stem")
    parser.add_argument("--severity", choices=SEVERITIES, default="error")
    parser.add_argument(
        "--applies-to",
        nargs="+",
        choices=SCOPES,
        default=["agent-behaviour"],
    )
    parser.add_argument("--source", help="canonical article URL, if one exists")
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args()

    slug = args.slug or slugify(args.title)
    if not SLUG_RE.match(slug):
        parser.error(f"derived slug {slug!r} is not kebab-case; pass --slug")

    path = STANDARDS_DIR / f"{slug}.md"
    if path.exists():
        parser.error(
            f"standards/{slug}.md already exists — amend the existing rule rather "
            f"than creating a second source of truth for it"
        )

    STANDARDS_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(
        scaffold(
            title=args.title,
            slug=slug,
            captured_from=args.captured_from,
            severity=args.severity,
            applies_to=list(args.applies_to),
            source=args.source,
            captured=args.date,
        ),
        encoding="utf-8",
    )

    print(f"Created standards/{slug}.md")
    print()
    print("Next:")
    print(f"  1. Write the rule in standards/{slug}.md (remove the {SENTINEL} line)")
    if "published-html" in args.applies_to:
        print("  2. Fill in checks, then: python3 scripts/fleet_check.py --self-test")
        print("  3. python3 scripts/sync_shared_rules.py")
        print("  4. Commit on a branch and open a pull request")
    else:
        print("  2. python3 scripts/sync_shared_rules.py")
        print("  3. Commit on a branch and open a pull request")
    print()
    print("The sync copies this rule into AGENTS.md and every distributed SKILL.md,")
    print("so it reaches every agent and every member who installed the pack.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
