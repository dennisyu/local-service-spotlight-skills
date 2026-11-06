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

Standard v2 (adopted 2026-11-05, fleet decision D-2026-11-05-05) moves the
copying to where the constraint actually lives — distribution, not authoring:

- In the SOURCE tree, a skill may adopt the referenced form: its ``SKILL.md``
  carries a "## Shared rules — harness layer (referenced, not inlined)" pointer
  block instead of the copied blocks. This script VALIDATES referenced skills
  (a referenced skill that also carries inlined blocks fails the check) and
  never re-inlines them.
- ``AGENTS.md`` always carries every block in full — it is the in-repo
  harness-layer copy the references point at, alongside ``standards/``.
- Skills that still carry blocks keep the legacy behaviour: blocks are
  embedded and checked exactly as before, until their conversion wave.
- A skill with NO blocks and NO pointer is "not yet converted": the source
  sync reports it as migration-pending and leaves it alone (it is covered in
  the source tree by ``AGENTS.md``/``standards/``, and at export — below).
  Under the pre-v2 script such a file read as "stale" and a plain sync
  inlined into it; that is precisely the authoring-state copying v2 ends.
- ``--export DIR`` builds a standalone tree (``AGENTS.md`` + ``skills/``) in
  which EVERY skill carries its blocks inlined, whatever its source state —
  the distribution guarantee above, satisfied at packaging time.

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

REFERENCED_HEADING = "## Shared rules — harness layer (referenced, not inlined)"


def is_referenced(text: str) -> bool:
    """True when a skill file has adopted the Standard v2 referenced form."""
    return REFERENCED_HEADING in text


def referenced_problems(path: Path, text: str) -> list[str]:
    """A referenced skill must carry the pointer only — no inlined blocks."""
    problems = []
    blocks = sorted(set(re.findall(r"<!-- shared-rule:([a-z0-9-]+):start -->", text)))
    if blocks:
        problems.append(
            f"{path.relative_to(ROOT)}: referenced form but carries inlined "
            f"shared-rule block(s): {', '.join(blocks)}"
        )
    if INDEX_START in text or INDEX_END in text:
        problems.append(
            f"{path.relative_to(ROOT)}: referenced form but carries a "
            "shared-rule index block"
        )
    return problems


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


def expected_text(
    current: str, keep: list, rest: list, prune: bool = False
) -> tuple[str, list[str]]:
    """The fully-inlined text a file should carry, plus orphan slugs found."""
    expected = drop_index(current)
    wanted = {s.slug for s in keep}
    orphans: list[str] = []

    # a rule the file should no longer carry: source deleted, or now out of scope
    for slug in orphan_blocks(current, wanted):
        if prune or any(s.slug == slug for s in rest):
            expected = drop_block(expected, slug)
        else:
            orphans.append(slug)

    for standard in keep:
        expected = upsert(expected, standard.slug, standard.block())

    block = index_block(rest)
    if block:
        expected = expected.rstrip() + "\n\n" + block + "\n"
    return expected, orphans


def sync(
    check: bool = False, prune: bool = False
) -> tuple[list[Path], list[tuple[Path, str]], list[str], list[Path]]:
    changed: list[Path] = []
    orphans: list[tuple[Path, str]] = []
    problems: list[str] = []
    pending: list[Path] = []

    for path, keep, rest in plan():
        current = path.read_text(encoding="utf-8") if path.exists() else ""

        # Standard v2 referenced form: validate, never re-inline. AGENTS.md is
        # exempt — it is the harness-layer copy and always carries the blocks.
        if path.name != "AGENTS.md" and is_referenced(current):
            problems.extend(referenced_problems(path, current))
            continue

        # Not yet converted (no blocks, no pointer): report, never inline.
        if (
            path.name != "AGENTS.md"
            and not re.search(r"<!-- shared-rule:[a-z0-9-]+:start -->", current)
            and INDEX_START not in current
        ):
            pending.append(path)
            continue

        expected, file_orphans = expected_text(current, keep, rest, prune)
        orphans.extend((path, slug) for slug in file_orphans)

        if current == expected:
            continue
        changed.append(path)
        if not check:
            path.write_text(expected, encoding="utf-8")
    return changed, orphans, problems, pending


def export_tree(target: Path) -> list[Path]:
    """Write a standalone tree in which every skill carries its blocks inlined.

    This is the distribution-time half of Standard v2: whatever form a skill
    has in the source tree (referenced or legacy), its exported copy is
    self-contained, satisfying the constraint in this module's docstring.
    """
    if target.exists() and any(target.iterdir()):
        raise StandardError(f"export target {target} exists and is not empty")
    written: list[Path] = []
    for path, keep, rest in plan():
        current = path.read_text(encoding="utf-8") if path.exists() else ""
        expected, _ = expected_text(current, keep, rest, prune=True)
        dest = target / path.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(expected, encoding="utf-8")
        written.append(dest)
    return written


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
    parser.add_argument(
        "--export",
        metavar="DIR",
        help="build a standalone tree in DIR with every skill's shared-rule "
        "blocks inlined (Standard v2 distribution mode); the source tree is "
        "not modified",
    )
    args = parser.parse_args()

    try:
        rules = standards()
        if not rules:
            print("No files in standards/ — nothing to sync.")
            return 0
        if args.export:
            written = export_tree(Path(args.export))
            print(
                f"Exported {len(written)} file(s) with shared rules inlined to "
                f"{args.export} (source tree unchanged)."
            )
            return 0
        changed, orphans, problems, pending = sync(
            check=args.check, prune=args.prune
        )
    except StandardError as exc:
        # A malformed rule must read like a fixable mistake, not a crash.
        print(f"Cannot sync — {exc}")
        return 1

    if problems:
        print("Referenced-form violations (Standard v2):")
        for problem in problems:
            print(f"- {problem}")
        return 1

    if pending:
        print(
            "Not yet converted to the referenced form (Standard v2 migration "
            "pending; covered by AGENTS.md/standards in-tree and inlined at "
            "export):"
        )
        for path in pending:
            print(f"- {path.relative_to(ROOT)}")

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
