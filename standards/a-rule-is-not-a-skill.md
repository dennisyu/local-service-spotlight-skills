---
{
  "title": "A rule is not a skill",
  "severity": "error",
  "captured": "2026-09-04",
  "captured_from": "Dennis Yu, Cowork session, 2026-09-04: 'How do we make it so that we have guardrails so agents don't go out of control, creating skills that you said really should be rules?' Traced to that same session, where an agent asked to make a layout rule global proposed it as a skill instead of a standard — with the whole pack loaded.",
  "applies_to": ["agent-behaviour"]
}
---

## A rule is not a skill

- **Before writing a skill, answer one question: is this a job, or a constraint on
  every job?** A job has a trigger somebody types, inputs, a procedure, a
  deliverable and a finish line. A constraint has none of those — it has a
  prohibition and a reason.
- **A constraint goes in `standards/`, never in `skills/`.** One file, captured
  with `scripts/new_standard.py`, stamped into every skill by
  `scripts/sync_shared_rules.py`. That is what makes it reach the 31 skills and
  everyone who installed the pack.
- **If you find yourself writing "always", "never", or "must" as the point of the
  document rather than as advice inside it, stop.** You are writing a rule.
- **The tell is self-description.** A skill whose own description says "layout
  rule for", "the standard for", or "our policy on" has told you what it is.
  Believe it.
- **Why it matters:** a rule filed as a skill lives in one account's skill list.
  It is never stamped into any SKILL.md, never reaches a member who installed the
  pack, and never gets a machine check. It looks shipped and propagates to
  nobody — the same failure as the black button that shipped ninety days after
  its rule was published, for the same reason.
- **When the answer is genuinely "both"** — a rule with real craft behind it —
  split it. The constraint goes to `standards/`; the how-to goes into the skill
  that already owns that work, not into a new one. Adding a skill is a permanent
  claim on the routing surface: every near-duplicate description makes activation
  worse for both skills. Adding a standard costs nothing at run time, because
  standards are stamped in rather than selected.
- Enforced by `python3 scripts/check_skill_vs_rule.py` in CI over skills a pull
  request adds. Existing skills are grandfathered and reported, never failed.
