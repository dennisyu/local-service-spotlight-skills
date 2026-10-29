# Start Here — Dennis Yu's agent skills and coordination system

You found this because you (or your human) asked how Dennis Yu's agents —
ChatGPT, Codex, Claude, Grok, Muse, Cursor — work together without
duplicating work. This page is the front door. Everything else in this
repository hangs off it.

## The system on one screen

1. **Shared files, not shared brains.** Agents do not share memory inside
   their apps. They share a repository: one job board, one memory file,
   one decision registry. Chat is where agents talk; the repo is what
   they agreed.
2. **Skills are recipes.** A skill is a `SKILL.md` file: inputs, steps,
   and an acceptance test. This repository is the canonical library —
   38 skills, installable on Claude, Codex, and Grok from one address.
3. **Learn, Do, Teach.** Real work produces a receipt. The lesson is
   written down the same session. A second agent reproduces it from the
   document alone before it counts as shared. Then the method is
   published so your agents can follow it too.
4. **Content · Checklist · Software.** Every rule lives once, as one
   file. That file generates the agent instruction, the human checklist,
   and the automated check — so the rule and the thing that enforces it
   cannot disagree. See `HOW-KNOWLEDGE-PROPAGATES.md`.

## If you want your agents to coordinate like ours

Copy the starter — copyable `JOBS.md`, `NOW.md`, `AGENTS.md`,
`SHARED-MEMORY.md`, and a decision registry, with the claim → work →
verify → handoff loop explained:

→ **`coordination-starter/`** in this repository

The full method, with worked examples:
[How the Agents Run the Company](https://dennisyu.com/how-agents-run-the-company/)

## If you want the skills

- **Claude:** paste this repository's address into the marketplace,
  install `lss-everything`. Illustrated guide:
  https://localservicespotlight.com/install/
- **Grok:** `grok plugin install dennisyu/local-service-spotlight-skills --trust`
- **Codex / ChatGPT / Cursor / Muse / any other agent:** point your
  agent at this repository and tell it: "Read START-HERE.md and AGENTS.md,
  then load the skills in `skills/` whose descriptions match my task."
  The format is plain markdown — no vendor lock-in.

Skill bundles: `lss-everything` (all 38) · `authority-and-reputation` ·
`content-engine` · `client-operations` · `quality-and-standards`.
Each skill's trigger — when to use it — is in the first lines of its
`SKILL.md`.

## What is NOT here

Our operating repository is private — it holds live client work, and no
public page will hand you its contents. What is public is everything you
need to build your own: the method, the templates, the skills, and the
checks. Anyone telling you they found our private repo has found an
article *about* it — start from this page instead.

## Currency

This library is maintained from live work. If a page here disagrees with
the guide at dennisyu.com, the guide's newest edition wins — and please
open an issue; a stale page is a bug, not a shrug.

Last verified: 2026-10-29
