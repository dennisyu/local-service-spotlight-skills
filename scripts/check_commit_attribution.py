#!/usr/bin/env python3
"""Fail a pull request that adds a commit not naming the agent that wrote it.

The rule is ``standards/commits-name-the-agent.md``. This is its enforcement.

Why a script and not a ``checks`` block: the standards sweep matches regexes
against published HTML. This rule is about git history, so it needs its own
reader — but it follows the same contract as ``fleet_check.py``. ``--self-test``
proves offline that the classifier flags its violating samples and clears its
clean ones, so the check cannot rot into something that passes forever.

Attribution is satisfied by either form:

    Agent: Claude Code
    Co-Authored-By: Cursor <cursoragent@cursor.com>

A commit a human typed says ``Agent: none``. Silence is the only failure.

The cutoff date is read from the standard's own ``captured`` field, so the rule
is never retroactive and the two facts can never drift apart.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from standards_lib import StandardError, parse_standard  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
STANDARD = ROOT / "standards" / "commits-name-the-agent.md"

TRAILER_RE = re.compile(r"^\s*(agent|co-authored-by)\s*:\s*(.+?)\s*$", re.IGNORECASE)
IDENTITY_RE = re.compile(r"^\s*(?P<name>.*?)\s*(?:<(?P<email>[^>]*)>)?\s*$")

#: A human declaring they typed it themselves. Not a loophole: it is a claim on
#: the record, which is exactly what an unsigned commit fails to be.
HUMAN_VALUES = {"none", "human", "hand", "manual", "n/a", "no agent"}

#: Names and addresses the coding agents already sign with, so the tools that
#: behave correctly today need no new behaviour to pass this check.
AGENT_NAME_RE = re.compile(
    r"\b(claude|cursor|codex|chatgpt|gpt-\d|copilot|gemini|grok|devin|aider"
    r"|windsurf|cowork|perplexity|jules|amp|goose|cline|opencode)\b",
    re.IGNORECASE,
)
AGENT_EMAIL_RE = re.compile(
    r"(@anthropic\.com$|@cursor\.com$|@openai\.com$|^copilot@|@google\.com$"
    r"|@x\.ai$|@cognition\.ai$|\[bot\]@)",
    re.IGNORECASE,
)

#: GitHub's own merge/squash button, and the repository's own automation. Their
#: committer identity already answers "who did this", so requiring a trailer
#: would only add noise no human writes.
EXEMPT_COMMITTER_EMAILS = {"noreply@github.com"}
EXEMPT_AUTHOR_RE = re.compile(r"\[bot\]|^actions@github\.com$", re.IGNORECASE)


@dataclass(frozen=True)
class Commit:
    sha: str
    author_name: str
    author_email: str
    committer_email: str
    date: str  # YYYY-MM-DD, author date
    parents: int
    subject: str
    message: str


@dataclass(frozen=True)
class Verdict:
    state: str  # "agent" | "human" | "exempt" | "unattributed"
    who: str
    reason: str

    @property
    def ok(self) -> bool:
        return self.state != "unattributed"


def trailers(message: str) -> list[tuple[str, str]]:
    """Every ``Agent:``/``Co-Authored-By:`` line in the message, in order.

    Deliberately scans the whole message rather than only git's final trailer
    block: a real signature buried mid-message is still a signature, and missing
    one would accuse an agent that did the right thing.
    """
    found = []
    for line in message.splitlines():
        match = TRAILER_RE.match(line)
        if match:
            found.append((match.group(1).lower(), match.group(2).strip()))
    return found


def looks_like_agent(value: str) -> bool:
    parts = IDENTITY_RE.match(value)
    name = (parts.group("name") or "") if parts else value
    email = (parts.group("email") or "") if parts else ""
    return bool(AGENT_NAME_RE.search(name) or AGENT_EMAIL_RE.search(email))


def classify(commit: Commit) -> Verdict:
    if commit.parents > 1:
        return Verdict("exempt", "git", "merge commit")
    if commit.committer_email.lower() in EXEMPT_COMMITTER_EMAILS:
        return Verdict("exempt", "GitHub", "created by GitHub's merge/squash button")
    if EXEMPT_AUTHOR_RE.search(commit.author_email) or EXEMPT_AUTHOR_RE.search(
        commit.author_name
    ):
        return Verdict("exempt", commit.author_name, "repository automation")

    for key, value in trailers(commit.message):
        if key == "agent":
            if value.strip().lower() in HUMAN_VALUES:
                return Verdict("human", commit.author_name, "declared hand-written")
            return Verdict("agent", value, "Agent: trailer")
        if key == "co-authored-by" and looks_like_agent(value):
            return Verdict("agent", value, "Co-Authored-By: trailer")

    return Verdict(
        "unattributed",
        commit.author_name,
        "no Agent: or agent Co-Authored-By: trailer — cannot tell who wrote this",
    )


FORMAT = "%H%x1f%an%x1f%ae%x1f%ce%x1f%ad%x1f%P%x1f%s%x1f%B%x1e"


def read_commits(rev_range: str, cwd: Path | None = None) -> list[Commit]:
    raw = subprocess.run(
        ["git", "log", f"--format={FORMAT}", "--date=format:%Y-%m-%d", rev_range],
        cwd=str(cwd or ROOT),
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    commits = []
    for record in raw.split("\x1e"):
        record = record.strip("\n")
        if not record.strip():
            continue
        sha, an, ae, ce, date, parents, subject, message = record.split("\x1f", 7)
        commits.append(
            Commit(
                sha=sha,
                author_name=an,
                author_email=ae,
                committer_email=ce,
                date=date,
                parents=len(parents.split()) if parents.strip() else 0,
                subject=subject,
                message=message,
            )
        )
    return commits


def cutoff() -> str:
    """The date the rule was captured. Commits older than this are grandfathered."""
    try:
        return parse_standard(STANDARD).captured
    except (StandardError, FileNotFoundError, OSError):
        return ""


def default_range() -> str:
    """The commits this change actually adds.

    In GitHub Actions a pull request supplies its base ref; everywhere else the
    honest default is "what is on this branch and not on main".
    """
    base = os.environ.get("GITHUB_BASE_REF") or ""
    if base:
        for candidate in (f"origin/{base}", base):
            if _rev_exists(candidate):
                return f"{candidate}..HEAD"
    for candidate in ("origin/main", "main"):
        if _rev_exists(candidate):
            return f"{candidate}..HEAD"
    return "HEAD~1..HEAD"


def _rev_exists(rev: str) -> bool:
    return (
        subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", rev],
            cwd=str(ROOT),
            capture_output=True,
        ).returncode
        == 0
    )


# --------------------------------------------------------------------------- #
# Self-test: the check must be able to fail, and must not fire on clean input.
# --------------------------------------------------------------------------- #

def _sample(message: str, **over) -> Commit:
    base = dict(
        sha="0" * 40,
        author_name="Dennis Yu",
        author_email="668sierra@gmail.com",
        committer_email="668sierra@gmail.com",
        date="2026-08-23",
        parents=1,
        subject=message.splitlines()[0],
        message=message,
    )
    base.update(over)
    return Commit(**base)


VIOLATING = [
    _sample("Stamp shared rules for email/examples/CF four-stages standards"),
    _sample("fix: restore skill\n\nSigned-off-by: Dennis Yu <668sierra@gmail.com>"),
    _sample("Add rule\n\nCo-Authored-By: Dennis Yu <dennis@blitzmetrics.com>"),
    _sample("Tidy up\n\nAgent"),
]

CLEAN = [
    _sample("Add rule\n\nAgent: Claude Code"),
    _sample("Add rule\n\nagent: Cursor"),
    _sample("Add rule\n\nAgent: none"),
    _sample("Add rule\n\nAgent: human"),
    _sample("Add rule\n\nCo-authored-by: Cursor <cursoragent@cursor.com>"),
    _sample("Add rule\n\nCo-Authored-By: Claude Opus 5 <noreply@anthropic.com>"),
    _sample(
        "Add rule\n\nCo-Authored-By: Dennis Yu <d@x.com>\nCo-Authored-By: Codex "
        "<codex@openai.com>"
    ),
    _sample("Merge pull request #20", parents=2),
    _sample("Separate GCT outcomes (#20)", committer_email="noreply@github.com"),
    _sample(
        "Bump pinned versions",
        author_name="github-actions[bot]",
        author_email="41898282+github-actions[bot]@users.noreply.github.com",
    ),
]


def self_test() -> int:
    failures = []
    for commit in VIOLATING:
        verdict = classify(commit)
        if verdict.ok:
            failures.append(
                f"  did NOT flag a violating sample ({verdict.state}): {commit.subject!r}"
            )
    for commit in CLEAN:
        verdict = classify(commit)
        if not verdict.ok:
            failures.append(f"  wrongly flagged a clean sample: {commit.message!r}")

    if failures:
        print("Self-test FAILED:")
        print("\n".join(failures))
        return 1

    print(
        f"Self-test passed: the attribution check flags all {len(VIOLATING)} violating "
        f"samples and clears all {len(CLEAN)} clean ones."
    )
    return 0


# --------------------------------------------------------------------------- #


def run(rev_range: str, since: str, census: bool) -> int:
    commits = read_commits(rev_range)
    if not commits:
        print(f"No commits in {rev_range} — nothing to check.")
        return 0

    unattributed, grandfathered, signed = [], [], []
    for commit in commits:
        verdict = classify(commit)
        if verdict.ok:
            signed.append((commit, verdict))
        elif since and commit.date < since:
            grandfathered.append(commit)
        else:
            unattributed.append(commit)

    if census:
        by_agent: dict[str, int] = {}
        for commit, verdict in signed:
            key = f"{verdict.state}: {verdict.who}"
            by_agent[key] = by_agent.get(key, 0) + 1
        print(f"Attribution census over {rev_range} ({len(commits)} commits)")
        for key, count in sorted(by_agent.items(), key=lambda kv: (-kv[1], kv[0])):
            print(f"  {count:>4}  {key}")
        if grandfathered:
            print(f"  {len(grandfathered):>4}  unattributed (before {since})")
        if unattributed:
            print(f"  {len(unattributed):>4}  unattributed (on or after {since})")

    if grandfathered and not census:
        print(
            f"{len(grandfathered)} commit(s) predate the rule ({since}) and are not "
            f"failed. Attribution is not retroactive."
        )

    if not unattributed:
        if not census:
            print(
                f"Every commit in {rev_range} names its writer "
                f"({len(signed)} attributed)."
            )
        return 0

    print()
    print(
        f"{len(unattributed)} commit(s) do not name the agent that wrote them "
        f"(standards/commits-name-the-agent.md):"
    )
    for commit in unattributed:
        print(f"  {commit.sha[:8]}  {commit.date}  {commit.author_name}")
        print(f"            {commit.subject}")
    print()
    print("Add one trailer to each, as the last block of the commit message:")
    print()
    print("    Agent: Claude Code        # or Cursor, Codex, Gemini, Grok…")
    print("    Agent: none               # if a human typed it")
    print()
    print("To repair the tip of the branch:  git commit --amend")
    print("For older commits:                git rebase -i " + rev_range.split("..")[0])
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--range",
        dest="rev_range",
        help="git revision range to check (default: what this branch adds to main)",
    )
    parser.add_argument(
        "--since",
        help="ignore commits authored before this YYYY-MM-DD "
        "(default: the rule's own 'captured' date)",
    )
    parser.add_argument(
        "--census",
        action="store_true",
        help="print who wrote what instead of only the violations",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="prove offline that the check flags violations and clears clean input",
    )
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()

    since = args.since if args.since is not None else cutoff()
    return run(args.rev_range or default_range(), since, args.census)


if __name__ == "__main__":
    raise SystemExit(main())
