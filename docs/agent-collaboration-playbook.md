# How to equip your AI agents to work together

This is the public playbook behind the Local Service Spotlight agent fleet. It answers the question we hear most often: **"How do I get my Claude, Codex, Grok, or other agents to share knowledge and pick up each other's work the way yours do?"**

Everything below is implemented in this repository, so you can inspect the working version instead of trusting a description.

## The short answer

Agents coordinate through files, not through conversations. Give them one canonical repository of written skills and standards, one operational log of everything they do, and a scheduled review that turns experience back into documentation. Any agent — any vendor — that can read markdown can then join the fleet.

## How do agents share one source of truth?

One public GitHub repository holds every skill as a portable `SKILL.md` file (see `skills/`). The same repository installs into Claude, Grok Build, and other agent hosts, so every agent reads identical instructions. Bundles in `.claude-plugin/marketplace.json` are selections over the same `skills/` folder — skills are never copied between bundles, so there is nothing to drift.

## How does a hard-won lesson reach every agent?

A lesson is written once as a single markdown file in `standards/`. A sync script stamps that rule verbatim into `AGENTS.md` and every applicable `SKILL.md`, and CI rejects any pull request where a required copy is missing or stale. One file produces the agent instruction, the human checklist, and the automated check — the rule and the thing that enforces it cannot disagree. The full story: [HOW-KNOWLEDGE-PROPAGATES.md](../HOW-KNOWLEDGE-PROPAGATES.md).

## How does a new agent pick up a task it has never seen?

The fleet keeps a private operations log — one markdown file per operation, each recording:

- who approved the work and what triggered it,
- which agent did it and through what access path,
- the exact scope, commands, and tools used,
- verification evidence proving the end state,
- rollback steps and backup locations.

An agent arriving cold greps the log for the system it is about to touch, reads the matching runbook, and can reconstruct — or undo — any past operation without asking a human. The rule that makes it work: *an agent that changes production state without logging it has not finished the job.*

## How do you know an agent actually did the job?

Receipts, not claims. Every installation, update, and scheduled job has acceptance checks — see [ACCEPTANCE.md](../ACCEPTANCE.md). A plugin in a list proves installation; a good answer alone does not prove that the installed skill was used.

## How does the system keep improving?

A scheduled weekly review reads the operations log, scores entries against the documentation standard, extracts reusable patterns, and promotes them here as pull requests — including improvements to the standard itself. Documentation is a loop, not a project.

## How do I copy this for my own team?

1. Create one canonical repository of skills — written recipes, one folder each, portable across agent hosts.
2. Add an `AGENTS.md` at the root: the operating manual every agent reads first.
3. Keep a private ops log with the entry format above; make logging part of the definition of done.
4. Write every house rule once and sync it mechanically into every skill — never maintain copies by hand.
5. Require receipts: verification evidence inside every log entry and every install.
6. Schedule a recurring review that reads the log and feeds lessons back into the repository.

Start small: one skill, one log, one rule. The loop compounds.

## What has the review loop promoted lately?

The weekly ops-log review promotes reusable lessons here, newest first.

### 001 — Always-on instructions earn their slot (promoted 2026-10-19)

Provenance: Dennis Yu, Claude Code session, 2026-10-17, asking for the
fleet's account-preferences block to be trimmed:

> please trim the block and help us be more efficient, even in ways that I
> didn't think to ask. of course, effectiveness is more important than
> efficiency, but we want both.

The block was rewritten in place from 667 words (4,846 characters) to 373
words (2,602 characters), with a 98-word short version derived for
token-tight contexts. The rule that came out of the trim:

- **A rule enters an always-on block only when it passes two tests:** it
  applies to most conversations, and an agent would get it wrong without
  being told. A rule that fails either test moves to the job prompt or the
  skill that actually needs it, where it is read exactly when it matters.
- **Every stale line is a tax paid on every run of every job.** An always-on
  block is re-read by every seat on every task; length is a standing cost
  and a standing dilution of the rules that do belong.
- **Replace superseded rules in the same edit.** Never stack a "this
  supersedes that" note on the old rule — two overlapping instructions make
  every reader pick one, and they will not all pick the same one.
- **One statement per rule.** Job-specific rules live in the job's own
  prompt or skill, not in the global block.
- **The canonical text lives in a repository and is edited there first**,
  then copied to each surface. Never edit one surface ad hoc; the copies
  drift and nobody can say which is current.
- **Measure the block and record the delta** — words and characters before
  and after each edit. What gets measured stays lean. Keep a short version
  for token-tight contexts, and name which contexts get which version.

**Propagation.** This is a universal agent-behaviour rule, so its final home
is `standards/`, from where the sync stamps it into `AGENTS.md` and every
distributed skill. The ready-to-use standard file is in the appendix below;
promoting it is one file drop plus one sync command. Until that drop lands,
this entry is the rule's canonical text.

## Appendix — ready-to-scaffold standard for lesson 001

Save as `standards/always-on-instructions-earn-their-slot.md`, then run
`python3 scripts/fleet_check.py --self-test` and
`python3 scripts/sync_shared_rules.py`. The sync regenerates `AGENTS.md` and
the distributed `SKILL.md` copies; those regenerated files go in the same
pull request as the new standard. Standard file text:

```markdown
---
{
  "title": "Always-on instructions earn their slot",
  "severity": "error",
  "captured": "2026-10-19",
  "captured_from": "Dennis Yu, Claude Code session, 2026-10-17: 'please trim the block and help us be more efficient, even in ways that I didn't think to ask. of course, effectiveness is more important than efficiency, but we want both.'",
  "applies_to": ["agent-behaviour"]
}
---

## Always-on instructions earn their slot

- **A rule enters an always-on block only when it passes two tests:** it
  applies to most conversations, and an agent would get it wrong without
  being told. A rule that fails either test moves to the job prompt or the
  skill that actually needs it, where it is read exactly when it matters.
- **Every stale line is a tax paid on every run of every job.** An always-on
  block is re-read by every seat on every task. Length is not a style issue;
  it is a standing cost and a standing dilution of the rules that do belong.
- **Replace superseded rules in the same edit.** Never stack a "this
  supersedes that" note on top of the old rule — two overlapping
  instructions make every reader pick one, and they will not all pick the
  same one. Edit the canonical text so only the current rule exists.
- **One statement per rule.** Two ideas in one bullet means one of them gets
  dropped by a reader in a hurry. Split it or cut it.
- **Job-specific rules live in the job's own prompt or skill**, not in the
  global block. The global block is for what every job gets wrong without it.
- **The canonical text lives in a repository and is edited there first**,
  then copied to each surface. Never edit one surface ad hoc; the copies
  drift and nobody can say which is current.
- **Measure the block and record the delta.** Word and character counts
  before and after each edit go into the change record. What gets measured
  stays lean.
- **Keep a short version** for token-tight contexts, derived from the
  canonical block, and name which contexts get which version.

No regex can honestly decide whether a rule earns an always-on slot; that is
a judgement about frequency and counterfactuality. Enforce this by reviewing
the block on a cadence — trim it the way code gets refactored, and record
the delta each time.
```
