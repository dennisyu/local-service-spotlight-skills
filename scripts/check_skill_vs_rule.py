#!/usr/bin/env python3
"""Refuse a skill that is really a house rule.

    python3 scripts/check_skill_vs_rule.py                 # skills added vs origin/main
    python3 scripts/check_skill_vs_rule.py --all           # every skill (reports, never fails)
    python3 scripts/check_skill_vs_rule.py --base <ref>    # compare against another ref
    python3 scripts/check_skill_vs_rule.py --self-test

Why this exists
---------------
An agent asked to "make this a global rule" reaches for the tool it has, and the
tool it has is `skill-creator`. So it writes a skill. The rule then lives in one
account's skill list instead of ``standards/``, which means it never gets stamped
into the 31 skills, never reaches anyone who installed the pack, and never gets a
machine check. It looks shipped and propagates to nobody.

That happened on 2026-09-04 with `visuals-above-the-fold`, which is a rule and was
first proposed as a skill. Documentation alone would not have stopped it — the
agent that wrote it had the whole pack loaded. So the gate is mechanical.

The distinction
---------------
A **skill** is a JOB: it has a trigger somebody types, inputs, a procedure, a
deliverable, and a definition of done. It answers "do this thing for me."

A **rule** is a CONSTRAINT on how every job is done. It has no inputs and no
deliverable. It answers "never do it that way." Rules go in ``standards/``, one
file each, where ``sync_shared_rules.py`` stamps them into every skill.

Ratchet, not retrofit
---------------------
Only skills ADDED by the change under review are gated. Existing skills predate
the rule and are reported, never failed — the same policy
``commits-name-the-agent`` uses. A rule you cannot land without rewriting 31 files
is a rule that gets reverted.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"

# A body with a procedure has one of these.
PROCEDURE = re.compile(r"^\s{0,3}(?:\d+[.)]\s|\|\s*\d+\s*\|)", re.M)
# Headings that mark a job's shape.
DONE = re.compile(r"^#{2,4}\s.*definition of done|^\*\*definition of done", re.M | re.I)
# A description that names when to reach for it.
TRIGGER = re.compile(r"\buse (?:this|it|when|to|for|after|before|instead)\b", re.I)
# Rule-shaped language.
PROHIBITION = re.compile(
    r"\b(?:never|do not|don't|must not|must be|must contain|always|no \w+ may"
    r"|is forbidden|is banned|is required)\b", re.I
)

# A skill that calls itself a rule is a rule. This is the signal the first
# version of this gate missed: `visuals-above-the-fold` was proposed as a skill
# whose description opened "Layout rule for any article..." — it announced what
# it was, and nothing was reading. Matches only the self-describing form ("is a
# rule", "Layout rule for", "the standard for"), never an incidental mention.
SELF_DECLARED_RULE = re.compile(
    r"(?:^|[:.]\s|\b(?:a|the|our|this|house|global|layout|design|editorial|"
    r"content|writing|style)\s+)"
    r"(rule|standard|policy|guardrail|convention|house rule|principle)"
    r"\b\s*(?:for|that|:|which|about|on\b|applies|governs|$)",
    re.I,
)

SHARED_RULE_BLOCK = re.compile(
    r"<!-- shared-rule:[a-z0-9-]+:start -->.*?<!-- shared-rule:[a-z0-9-]+:end -->",
    re.S,
)
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def body_of(text: str) -> tuple[str, str]:
    """Return (frontmatter, body-with-shared-rules-removed)."""
    m = FRONTMATTER.match(text)
    fm = m.group(1) if m else ""
    body = text[m.end():] if m else text
    return fm, SHARED_RULE_BLOCK.sub("", body)


def describe(fm: str) -> str:
    m = re.search(r'^description:\s*"?(.*?)"?\s*$', fm, re.M | re.S)
    return m.group(1) if m else ""


def judge(path: Path, text: str) -> list[str]:
    """Return the reasons this file fails the job test. Empty means it is a job."""
    fm, body = body_of(text)
    problems: list[str] = []

    # 1. Does it announce itself as a rule?
    name = re.search(r"^name:\s*\"?([^\"\n]+)", fm, re.M)
    title = re.search(r"^#\s+(.+)$", body, re.M)
    for label, blob in (("description", desc_text := describe(fm)),
                        ("title", title.group(1) if title else ""),
                        ("name", name.group(1) if name else "")):
        m = SELF_DECLARED_RULE.search(blob)
        if m:
            problems.append(
                f"BLOCKING: the {label} calls this a {m.group(1).lower()} "
                f"(\u201c{blob.strip()[:90]}\u2026\u201d) \u2014 a skill that describes itself as "
                f"a rule is a rule"
            )
            break

    has_procedure = bool(PROCEDURE.search(body))
    lines = [ln for ln in body.splitlines() if ln.strip()]
    banned = sum(1 for ln in lines if PROHIBITION.search(ln))
    ratio = banned / len(lines) if lines else 0.0

    # THE GATE. A body with no procedure that is mostly prohibitions is a
    # constraint on other people's work, not work. This is the only condition
    # that blocks a merge, because it is the only one that reliably separates
    # `no-black-buttons` from `weekly-brand-maa` — measured against all 31
    # skills in the pack, it fires on none of them.
    if not has_procedure and ratio > 0.20:
        problems.append(
            f"BLOCKING: no procedure, and {banned} of {len(lines)} lines are "
            f"prohibitions ({ratio:.0%}) — this constrains other work rather than "
            f"being work"
        )
    elif not has_procedure and len(lines) < 25:
        problems.append(
            "BLOCKING: no numbered procedure and too short to be one — a job has "
            "steps somebody follows"
        )

    return problems


def advisories(path: Path, text: str) -> list[str]:
    """Conventions worth following. Reported, never blocking — 26 of the 31
    skills already in the pack would fail at least one, and a gate that rejects
    the corpus it guards is a gate somebody switches off."""
    fm, body = body_of(text)
    notes: list[str] = []
    if not TRIGGER.search(describe(fm)):
        notes.append(
            "description never says when to reach for it — the description is the "
            "activation surface, so it should carry the words someone types "
            "(\"Use when...\", \"Use to...\")"
        )
    if not DONE.search(body):
        notes.append(
            "no \"Definition of done\" section — 12 of 31 skills have one; a job "
            "that cannot say what finished looks like tends not to finish"
        )
    return notes


def added_skills(base: str) -> list[Path]:
    try:
        out = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=A", f"{base}...HEAD"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout
    except subprocess.CalledProcessError:
        return []
    return [
        ROOT / p for p in out.split()
        if p.startswith("skills/") and p.endswith("/SKILL.md")
    ]


ADVICE = """
  This is how a rule gets lost. Put it in standards/ instead:

      python3 scripts/new_standard.py "<the rule, in a few words>" \\
          --from "<who said it, where, when>" \\
          --applies-to agent-behaviour        # or published-html
      # write the rule, then:
      python3 scripts/sync_shared_rules.py

  One file there reaches all 31 skills and everyone who installed the pack. A
  skill reaches only the person who installed that skill.

  If it really is a job, give it the four things a job has: a trigger phrase in
  the description, a numbered procedure, a stated deliverable, and a "Definition
  of done" section.
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default="origin/main",
                    help="ref to diff against (default origin/main)")
    ap.add_argument("--all", action="store_true",
                    help="report on every skill; never fails")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    if args.all:
        targets = sorted(SKILLS_DIR.glob("*/SKILL.md"))
        print(f"Reporting on all {len(targets)} skill(s) — informational, never fails.\n")
        blocking = advisory = 0
        for p in targets:
            text = p.read_text(encoding="utf-8")
            problems, notes = judge(p, text), advisories(p, text)
            if problems:
                blocking += 1
            if notes:
                advisory += 1
            if problems or notes:
                print(f"  {p.relative_to(ROOT)}")
                for why in problems:
                    print(f"      BLOCK  {why}")
                for why in notes:
                    print(f"      note   {why}")
        print(f"\n{blocking} of {len(targets)} read as a rule rather than a job "
              f"(these would block if added today).")
        print(f"{advisory} of {len(targets)} miss a convention (never blocks).")
        print("Existing skills are grandfathered; only newly added ones are gated.")
        return 0

    targets = added_skills(args.base)
    if not targets:
        print(f"No skills added against {args.base} — nothing to gate.")
        return 0

    print(f"Gating {len(targets)} newly added skill(s) against {args.base}.\n")
    failed = False
    for p in targets:
        text = p.read_text(encoding="utf-8")
        problems, notes = judge(p, text), advisories(p, text)
        if problems:
            failed = True
            print(f"  FAIL {p.relative_to(ROOT)}")
            for why in problems:
                print(f"      - {why}")
        else:
            print(f"  OK   {p.relative_to(ROOT)} — reads as a job")
        for why in notes:
            print(f"      note: {why}")
    if failed:
        print(ADVICE)
        return 1
    return 0


# --------------------------------------------------------------------------
# self-test: the gate proves it separates the two shapes
# --------------------------------------------------------------------------

A_JOB = '''---
name: thing-doer
description: "Do the thing for one client and hand back the report. Use when someone asks to run the thing."
---

# Thing doer

## Steps

1. Read the client profile.
2. Run the thing.
3. Write the report.

## Definition of done

A dated report exists at the named destination and a fresh reader can open it.
'''

A_RULE = '''---
name: no-black-buttons
description: "Buttons must never be black."
---

# No black buttons

- Never ship a black button.
- Do not use pure black for any interactive element.
- Always use the brand accent instead.
- Never override this in a child theme.
'''

# The real one. Proposed as a skill on 2026-09-04, has a numbered list, reads
# fluently, and is a house rule. If this ever stops failing, the gate is broken.
THE_ONE_THAT_GOT_THROUGH = '''---
name: visuals-above-the-fold
description: "Layout rule for any article, post or page written for Dennis's sites: the visual and interactive content goes above the fold, never buried under a wall of prose. Use whenever drafting, rewriting or publishing web content."
---

# Visuals above the fold

## The rule

1. **First screen carries something other than text.** A chart, diagram or
   interactive tool must be at least partly visible in the first viewport.
2. **The interactive piece leads.** The prose explains it, rather than preceding it.
3. **No prose run longer than two screens** without a figure breaking it.
'''

A_RULE_WITH_STEPS_BUT_NO_DONE = '''---
name: half-a-skill
description: "Use when you need to do the half-thing."
---

# Half a skill

1. Do the first part.
2. Do the second part.
'''


def self_test() -> int:
    import tempfile
    problems: list[str] = []
    cases = [
        ("a real job", A_JOB, False),
        ("a rule dressed as a skill", A_RULE, True),
        ("a job missing its definition of done", A_RULE_WITH_STEPS_BUT_NO_DONE, False),
        ("the rule that got through as a skill", THE_ONE_THAT_GOT_THROUGH, True),
    ]
    for label, text, should_fail in cases:
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as fh:
            fh.write(text)
            path = Path(fh.name)
        found = judge(path, text)
        path.unlink()
        if should_fail and not found:
            problems.append(f"{label}: should have been flagged and was not")
        if not should_fail and found:
            problems.append(f"{label}: should have passed, was flagged for {found}")

    # the rule case must be flagged for the right reason, not by accident
    rule_reasons = " ".join(judge(Path("x"), A_RULE))
    if "prohibitions" not in rule_reasons:
        problems.append("the rule case was not flagged as prohibition-shaped")

    # the regression case must be caught for the self-declaration reason, not by
    # accident — it has a numbered list, so the procedure heuristic will not fire
    got = " ".join(judge(Path("x"), THE_ONE_THAT_GOT_THROUGH))
    if "calls this a rule" not in got:
        problems.append(
            "the 2026-09-04 regression case was not caught by self-declaration; "
            f"got: {got or 'nothing'}")

    # and the advisory path must still notice the missing Definition of done
    if not advisories(Path("x"), A_RULE_WITH_STEPS_BUT_NO_DONE):
        problems.append("missing Definition of done was not even reported")

    # the gate must not fire on the pack it guards
    fires = [p.parent.name for p in sorted(SKILLS_DIR.glob("*/SKILL.md"))
             if judge(p, p.read_text(encoding="utf-8"))]
    if fires:
        problems.append(
            "the gate blocks existing skills, which means it is miscalibrated: "
            + ", ".join(fires))

    if problems:
        print("Self-test FAILED:")
        for p in problems:
            print("  -", p)
        return 1
    print("Self-test passed: the gate separates a job from a rule, and says why.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
