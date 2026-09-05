#!/usr/bin/env python3
"""Embed every shared house rule in every applicable distributed skill.

Each file in ``standards/`` becomes one generated block, keyed by its filename
stem, inside ``AGENTS.md``. Universal agent-behaviour rules enter every
``skills/*/SKILL.md``; other rules follow the skill's declared ``rule-scopes``.

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
import unicodedata
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


def _comparable_marker_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    normalized = "".join(
        ""
        if unicodedata.category(character) == "Cf"
        else "-"
        if character == "_"
        or unicodedata.category(character) == "Pd"
        or character in {"\u2212", "\ufe58"}
        else ":"
        if character in {"∶", "꞉", "ː", "︰", "ꓽ", "։"}
        else character
        for character in normalized
    )
    normalized = re.sub(r"\s*:\s*", ":", normalized)
    normalized = re.sub(r"\s+", "", normalized)
    return normalized.strip()


def standards() -> list[tuple[str, str]]:
    """Return [(slug, rendered block)] for every standard, sorted by slug."""
    return [(s.slug, s.block()) for s in load_standards(STANDARDS_DIR)]


def plan() -> list[tuple[Path, list, list]]:
    """Return (target, applicable rules, intentionally out-of-scope rules).

    AGENTS.md carries everything. A skill carries the universal agent rules plus
    whatever scopes it declares in its frontmatter. The third value lets sync
    remove a block when a skill drops a scope; out-of-scope rules are not linked
    from standalone distributions that do not contain ``AGENTS.md``/``standards``.
    """
    all_rules = load_standards(STANDARDS_DIR)
    out = [(ROOT / "AGENTS.md", all_rules, [])]
    for skill in sorted((ROOT / "skills").glob("*/SKILL.md")):
        keep = standards_for(all_rules, skill_scopes(skill))
        rest = [s for s in all_rules if s not in keep]
        out.append((skill, keep, rest))
    return out


def targets() -> list[Path]:
    skill_files = sorted((ROOT / "skills").glob("*/SKILL.md"))
    return [ROOT / "AGENTS.md", *skill_files]


def upsert(text: str, slug: str, block: str) -> str:
    """Replace this rule's block in place, or append it if not present."""
    start, end = marker(slug)
    if start in text or end in text:
        if text.count(start) != 1 or text.count(end) != 1:
            raise StandardError(
                f"shared-rule markers for {slug!r} are missing or duplicated"
            )
        before, rest = text.split(start, 1)
        _, after = rest.split(end, 1)
        text = before.rstrip() + "\n\n" + block + after
    else:
        text = text.rstrip() + "\n\n" + block
    return text.rstrip() + "\n"


def orphan_blocks(text: str, known: set[str]) -> list[str]:
    """Rule blocks present in a file whose standards/ source no longer exists."""
    found = set(
        re.findall(r"<!-- shared-rule:([a-z0-9-]+):(?:start|end) -->", text)
    )
    return sorted(found - known)


def validate_generated_markers(text: str) -> None:
    """Reject missing, duplicate, or reversed generated-marker pairs."""
    # Canonical markers are single-line HTML comments.  Scan comment openers
    # separately so a missing final ``-->`` cannot hide stale teaching.
    cursor = 0
    while True:
        opener = text.find("<!--", cursor)
        if opener < 0:
            break
        closer = text.find("-->", opener + 4)
        if closer < 0:
            candidate = text[opener + 4 :]
            comparable = _comparable_marker_text(candidate.rstrip(" >-"))
            if "shared-rule:" in comparable or "shared-rule-index:" in comparable:
                raise StandardError(
                    f"confusable or malformed shared-rule marker {candidate.strip()!r}"
                )
            break
        cursor = closer + 3
    for raw_comment in re.findall(r"<!--(.*?)-->", text, re.DOTALL):
        stripped = raw_comment.strip()
        comparable = _comparable_marker_text(stripped)
        if "shared-rule:" in comparable or "shared-rule-index:" in comparable:
            exact_rule = re.fullmatch(
                r"shared-rule:[a-z0-9]+(?:-[a-z0-9]+)*:(?:start|end)",
                stripped,
            )
            exact_index = stripped in {
                "shared-rule-index:start",
                "shared-rule-index:end",
            }
            if (
                exact_rule is None
                and not exact_index
            ) or comparable != stripped:
                raise StandardError(
                    f"confusable or malformed shared-rule marker {stripped!r}"
                )
    slugs = set(
        re.findall(r"<!-- shared-rule:([a-z0-9-]+):(?:start|end) -->", text)
    )
    for slug in sorted(slugs):
        start, end = marker(slug)
        if text.count(start) != 1 or text.count(end) != 1:
            raise StandardError(
                f"shared-rule markers for {slug!r} are missing or duplicated"
            )
        if text.index(start) >= text.index(end):
            raise StandardError(f"shared-rule markers for {slug!r} are reversed")
    start_count = text.count(INDEX_START)
    end_count = text.count(INDEX_END)
    if start_count or end_count:
        if start_count != 1 or end_count != 1:
            raise StandardError("shared-rule-index markers are missing or duplicated")
        if text.index(INDEX_START) >= text.index(INDEX_END):
            raise StandardError("shared-rule-index markers are reversed")


def drop_block(text: str, slug: str) -> str:
    """Remove a generated block whose standards/ source is gone."""
    start, end = marker(slug)
    if start not in text or end not in text:
        return text
    before, rest = text.split(start, 1)
    _, after = rest.split(end, 1)
    return (before.rstrip() + "\n" + after.lstrip("\n")).rstrip() + "\n"


def drop_index(text: str) -> str:
    start_count = text.count(INDEX_START)
    end_count = text.count(INDEX_END)
    if not start_count and not end_count:
        return text
    if start_count != 1 or end_count != 1:
        raise StandardError("shared-rule-index markers are missing or duplicated")
    if text.index(INDEX_START) >= text.index(INDEX_END):
        raise StandardError("shared-rule-index markers are reversed")
    before, rest = text.split(INDEX_START, 1)
    _, after = rest.split(INDEX_END, 1)
    return (before.rstrip() + "\n" + after.lstrip("\n")).rstrip() + "\n"


def sync(check: bool = False, prune: bool = False) -> tuple[list[Path], list[tuple[Path, str]]]:
    changed: list[Path] = []
    orphans: list[tuple[Path, str]] = []

    for path, keep, rest in plan():
        current = path.read_text(encoding="utf-8") if path.exists() else ""
        validate_generated_markers(current)
        expected = current
        wanted = {s.slug for s in keep}

        # a rule the file should no longer carry: source deleted, or now out of scope
        for slug in orphan_blocks(current, wanted):
            if prune or any(s.slug == slug for s in rest):
                expected = drop_block(expected, slug)
            else:
                orphans.append((path, slug))

        for standard in keep:
            expected = upsert(expected, standard.slug, standard.block())

        # Remove the legacy out-of-scope index. Standalone skill installs do not
        # include the repository paths it linked, and an out-of-scope rule is not
        # secretly binding on work the skill does not govern.
        expected = drop_index(expected)

        if current == expected:
            continue
        changed.append(path)
        if not check:
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
