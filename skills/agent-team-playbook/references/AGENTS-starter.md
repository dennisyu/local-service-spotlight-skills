# AGENTS.md — starter for a multi-agent team

Copy to `AGENTS.md` at the root of your shared repo and edit the names. Claude Code,
Codex, Cursor and most coding CLIs read this file at startup ([agents.md](https://agents.md)).
Scheduled cloud prompts often do not: make "read AGENTS.md from the repo" their first step.

---

# How agents work here

This repo is the team's memory. If it is not written here, it did not happen.

## Read before you start

1. This file.
2. `status/NOW.md` — work already claimed. Never start a second copy of a claimed job.
3. `status/JOBS.md` — work nobody owns yet. Claim what your desk can do.
4. The three newest files in `agent-notes/`.
5. The runbook for the job you are about to run: `runbooks/<agent>/<task>.md`.

## While you work

- **The human is not the courier.** If the next sentence is for another agent, write it
  on the job board or the shared thread and name that agent. Never ask the human to paste
  or relay.
- **An unanswered ask never stops the work.** Every ask carries a recheck date. At that
  date, do the work yourself if it is safe, then remove the dependency.
- **Name the store and key, never the value.** No password, token or key in any file.
- **The checker is never the doer.** Anything that ships is reviewed by a different model.

## When you finish

- End with a receipt in `agent-notes/YYYY-MM-DD-<agent>-<slug>.md` (template in
  `agent-notes/_TEMPLATE.md`) and the line
  `Verified: <what you opened> — <what you saw> — <when>`, or `Verified: NO — <what is missing>`.
- Recurring job? It needs a runbook in `runbooks/<agent>/` (standard: `runbooks/README.md`).
  New recurring job → runbook in the same commit.
- Handing work to someone? Put it on `status/JOBS.md` with an owner or function and a
  recheck date.

## Who does what

| Agent | Runtime | Owns |
|---|---|---|
| Coordinator | <your choice> | sweeps the board daily; one digest to the human; escalates only decisions nobody else may make |
| ... | ... | ... |

Keep this table short and true. The detail lives in each agent's `runbooks/<agent>/INDEX.md`.
