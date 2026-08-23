---
{
  "title": "Every commit names the agent that wrote it",
  "severity": "error",
  "captured": "2026-08-23",
  "captured_from": "Dennis Yu, Cowork session, 2026-08-23, on six consecutive red CI runs from PR #21: 'which agent is pushing this and are all agents identifying themselves so we know who it is?' Every one of the six commits was authored 'Dennis Yu <668sierra@gmail.com>' with no trailer. One of them truncated skills/software-subscription-audit/SKILL.md from 366 lines to a single byte, and the only way to find the culprit was to read six diffs by hand. A second agent (Cursor, which does sign) repaired it. 69 of the repository's first 80 commits carried no attribution at all.",
  "applies_to": ["agent-behaviour"]
}
---

## Every commit names the agent that wrote it

- **Every commit an agent authors carries a trailer naming that agent** — either
  `Agent: Claude Code` / `Agent: Cursor` / `Agent: Codex`, or the
  `Co-Authored-By: <Agent> <email>` line the coding tools already emit. One line,
  last block of the message, blank line above it.
- **Name the agent even when the git author is a human.** Agents run under
  Dennis's `user.name` and `user.email`, so the author field says who owns the
  account, never who wrote the change. Same rule as
  `outbound-email-names-the-agent`: the address is delivery, the trailer is
  transparency.
- **A commit typed by a human says so** — `Agent: none` — rather than staying
  silent. Silence is the failure mode this rule exists to remove: an unsigned
  commit is indistinguishable from an agent that skipped the rule.
- **Why:** when CI goes red at 9pm across six pushes, the first question is which
  fleet member to correct, and an unattributed commit makes that unanswerable
  without reading every diff. Attribution is what turns a bad push into a fixed
  agent instead of a repeated incident.
- **Never attribute a change to an agent that did not make it**, and never invent
  a human author to hide that an agent wrote it.
- Merge and squash commits created by GitHub itself, and commits from
  `github-actions[bot]`, are already attributable by their committer and are
  exempt.
- Enforced by `python3 scripts/check_commit_attribution.py` in CI over the commits
  a pull request adds. Commits authored before this rule's `captured` date are
  reported and not failed — the rule is not retroactive, only unavoidable from here.
