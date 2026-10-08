#!/usr/bin/env python3
"""Embed every shared house rule in every self-contained distributed skill.

Each file in ``standards/`` becomes one generated block, keyed by its filename
stem, inside ``AGENTS.md`` and every ``skills/*/SKILL.md``.

Adding a house rule is therefore a file drop:

    standards/no-black-buttons.md   ->   <!-- shared-rule:no-black-buttons:start -->

No code change, no bundle edit, and CI rejects any copy that goes stale. This is
what makes "everything we learn propagates" true by construction rather than by
somebody remembering to do it.

Why copy at all, instead of linking? Because a skill is distributed on its own.
Someone who installs one bundle gets the ``SKILL.md`` files and nothing else —
no ``standards/`` directory, no repository. A rule that is only linked is a rule
that rides along until it reaches the user and then vanishes. A rule that is
copied in arrives with them.

The JSON header of a standard is machine configuration for the fleet sweep, not
guidance, so only the prose body is embedded. Blocks are written in sorted slug
order so output is deterministic.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from standards_lib import (  # noqa: E402
    StandardError,
    load_standards,
    markers,
    skill_scopes,
    standards_for,
)


ROOT = Path(__file__).resolve().parents[1]
STANDARDS_DIR = ROOT / "standards"


def marker(slug: str) -> tuple[str, str]:
    return markers(slug)


INDEX_START = "<!-- shared-rule-index:start -->"
INDEX_END = "<!-- shared-rule-index:end -->"


def standards() -> list[tuple[str, str]]:
    """Return [(slug, rendered block)] for every standard, sorted by slug."""
    return [(s.slug, s.block()) for s in load_standards(STANDARDS_DIR)]


def plan() -> list[tuple[Path, list, list]]:
    """(target, rules to embed in full, rules to name in the index) per file.

    AGENTS.md carries everything. A skill carries the universal agent rules plus
    whatever scopes it declares in its frontmatter, and an index naming the rest
    so a rule can never be invisible — only elsewhere.
    """
    all_rules = load_standards(STANDARDS_DIR)
    out = [(ROOT / "AGENTS.md", all_rules, [])]
    for skill in sorted((ROOT / "skills").glob("*/SKILL.md")):
        keep = standards_for(all_rules, skill_scopes(skill))
        rest = [s for s in all_rules if s not in keep]
        out.append((skill, keep, rest))
    return out


def index_block(rest: list) -> str:
    if not rest:
        return ""
    lines = "\n".join(f"- **{s.title}** (`{s.slug}`)" for s in rest)
    return (
        f"{INDEX_START}\n"
        "## Other house rules that apply to this work\n\n"
        "These are not repeated here because they govern published pages rather "
        "than agent behaviour. They are binding all the same — read the full text "
        "in `AGENTS.md` or `standards/` before touching a website.\n\n"
        f"{lines}\n"
        f"{INDEX_END}"
    )


def targets() -> list[Path]:
    skill_files = sorted((ROOT / "skills").glob("*/SKILL.md"))
    return [ROOT / "AGENTS.md", *skill_files]


def upsert(text: str, slug: str, block: str) -> str:
    """Replace this rule's block in place, or append it if not present."""
    start, end = marker(slug)
    body = block.removeprefix(start + "\n").removesuffix("\n" + end)
    heading = body.splitlines()[0]
    if start in text or end in text:
        if (text.count(start) != 1 or text.count(end) != 1
                or text.index(start) > text.index(end)):
            raise StandardError(
                f"shared-rule markers for {slug!r} are missing or duplicated"
            )
        before, rest = text.split(start, 1)
        previous_body, after = rest.split(end, 1)
        previous_heading = next(
            (line for line in previous_body.splitlines() if line.startswith("## ")), None
        )
        outside = (before + "\n" + after).splitlines()
        if heading in outside or (previous_heading and previous_heading in outside):
            raise StandardError(
                f"ambiguous shared rule {slug!r}: unmarked heading outside its markers"
            )
        text = before.rstrip() + "\n\n" + block + after
    else:
        # Lost delimiters do not mean lost prose. Recover only an exact,
        # standalone canonical section; guessing at edited prose risks data loss.
        matches = list(re.finditer(r"(?m)^" + re.escape(heading) + r"$", text))
        if matches:
            if len(matches) != 1:
                raise StandardError(f"ambiguous unmarked shared rule {slug!r}")
            offset = matches[0].start()
            following = re.search(
                r"(?m)^(?:## |<!-- shared-rule[:-])", text[matches[0].end():]
            )
            stop = matches[0].end() + following.start() if following else len(text)
            section = text[offset:stop]
            if section.rstrip() != body:
                raise StandardError(
                    f"edited unmarked shared rule {slug!r}; restore its markers "
                    "after reconciling with standards/"
                )
            # Preserve surrounding content and whitespace byte for byte.
            text = text[:offset] + block + section[len(body):] + text[stop:]
        else:
            text = text.rstrip() + "\n\n" + block
    return text.rstrip() + "\n"


def orphan_blocks(text: str, known: set[str]) -> list[str]:
    """Rule blocks present in a file whose standards/ source no longer exists."""
    found = set(re.findall(r"<!-- shared-rule:([a-z0-9-]+):start -->", text))
    return sorted(found - known)


def drop_block(text: str, slug: str) -> str:
    """Remove a generated block whose standards/ source is gone."""
    start, end = marker(slug)
    if start not in text or end not in text:
        return text
    before, rest = text.split(start, 1)
    _, after = rest.split(end, 1)
    return (before.rstrip() + "\n" + after.lstrip("\n")).rstrip() + "\n"


def drop_index(text: str) -> str:
    if INDEX_START not in text or INDEX_END not in text:
        return text
    before, rest = text.split(INDEX_START, 1)
    _, after = rest.split(INDEX_END, 1)
    return (before.rstrip() + "\n" + after.lstrip("\n")).rstrip() + "\n"


def sync(check: bool = False, prune: bool = False) -> tuple[list[Path], list[tuple[Path, str]]]:
    changed: list[Path] = []
    orphans: list[tuple[Path, str]] = []
    updates: list[tuple[Path, str]] = []

    for path, keep, rest in plan():
        current = path.read_text(encoding="utf-8") if path.exists() else ""
        expected = drop_index(current)
        wanted = {s.slug for s in keep}

        # a rule the file should no longer carry: source deleted, or now out of scope
        for slug in orphan_blocks(current, wanted):
            if prune or any(s.slug == slug for s in rest):
                expected = drop_block(expected, slug)
            else:
                orphans.append((path, slug))

        for standard in keep:
            try:
                expected = upsert(expected, standard.slug, standard.block())
            except StandardError as exc:
                raise StandardError(f"{path.relative_to(ROOT)}: {exc}") from exc

        block = index_block(rest)
        if block:
            expected = expected.rstrip() + "\n\n" + block + "\n"

        if current == expected:
            continue
        changed.append(path)
        updates.append((path, expected))

    # Preflight all files so a damaged later target cannot leave earlier skills
    # partly updated. Check mode never writes.
    if not check:
        for path, expected in updates:
            path.write_text(expected, encoding="utf-8")
    return changed, orphans


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail when generated rule blocks are stale instead of updating them",
    )
    parser.add_argument(
        "--prune",
        action="store_true",
        help="also remove blocks whose standards/ file is gone (renaming or "
        "retiring a rule)",
    )
    args = parser.parse_args()

    try:
        rules = standards()
        if not rules:
            print("No files in standards/ — nothing to sync.")
            return 0
        changed, orphans = sync(check=args.check, prune=args.prune)
    except StandardError as exc:
        # A malformed rule must read like a fixable mistake, not a crash.
        print(f"Cannot sync — {exc}")
        return 1

    if orphans:
        print("Orphan rule blocks (no matching file in standards/):")
        for path, slug in orphans:
            print(f"- {path.relative_to(ROOT)}: {slug}")
        print(
            "Retiring or renaming a rule? Run: "
            "python3 scripts/sync_shared_rules.py --prune\n"
            "Otherwise restore standards/<slug>.md"
        )
        return 1

    names = ", ".join(slug for slug, _ in rules)
    if args.check and changed:
        print(f"Shared rules ({names}) are stale in:")
        for path in changed:
            print(f"- {path.relative_to(ROOT)}")
        print("Run: python3 scripts/sync_shared_rules.py")
        return 1
    if changed:
        print(f"Updated {len(rules)} shared rule(s) in {len(changed)} file(s).")
    else:
        print(f"Shared rules are current ({len(rules)}): {names}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
