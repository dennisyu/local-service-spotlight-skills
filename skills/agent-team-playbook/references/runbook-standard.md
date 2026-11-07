# Runbooks — every recurring task, written so another agent can run it

Copy this file to `runbooks/README.md` in your shared repo.

**If an agent stops tomorrow, its work should not stop with it.** Each agent keeps a list
of the jobs it runs, and each job has a page that explains it well enough for a stranger
— a different agent on a different model — to run it cold.

## The rule

1. **Every agent keeps a registry** at `runbooks/<agent>/INDEX.md` listing every
   recurring task it owns.
2. **Every recurring task gets a runbook** at `runbooks/<agent>/<task-slug>.md`, using the
   eight sections in the template.
3. **The bar is cold-start competence.** A competent agent that has never seen the task
   can run it from the runbook alone — without asking anyone, and without the chat that
   created it.
4. **New recurring work gets its runbook at creation**, in the same commit as the job.
5. **One-off work** gets a same-day receipt in `agent-notes/`, not a runbook.
6. **Never a credential.** Name the store and the key; never the value. The checker scans
   every runbook for credential-shaped text.

## The registry contract (`INDEX.md`)

A markdown table whose header contains **Task**, **Cadence** and **Runbook**. Each
Runbook cell is a path (`<slug>.md` or `runbooks/<agent>/<slug>.md`), the same path
followed by `(to write)` while the deadline in `runbooks/agents.json` has not passed, or
`(retired)` / `(disabled)`. Every runbook file in the folder must be listed.

## The runbook contract (eight sections)

1. **Purpose** — what the task achieves and why it exists.
2. **Trigger / cadence** — schedule, event, or manual; timezone; where the schedule lives.
3. **Inputs** — data, files, accounts, sessions needed. Names and locations only.
4. **Steps** — the exact procedure or prompt, in order, with real commands and queries.
5. **Output** — format, destination, and what "done" looks like.
6. **Receipt** — where proof-of-run lands and how a verifier checks it.
7. **Failure modes** — what breaks, what it looks like, what to do; include the
   "silent when healthy" trap — the run that looks fine and delivered nothing.
8. **Owner + history** — current owner, who ran it before, and the date (YYYY-MM-DD) of
   the last successful run.

A section that only says `TODO`, `TBD`, `to write`, `...` or a `<placeholder>` counts as
missing.

### Handover-ready = a cold read with zero questions

Passing the checker means the runbook is complete in shape, not that it is clear. Clarity is proved
one way: an agent that has never seen the job — on a different model from the author — reads only
the runbook and lists every question it would have to ask before running the job. Record the result
as the last line of **Owner + history**:

    Cold read: YYYY-MM-DD by <agent / model> — N open questions

List the questions under **Failure modes** in a subsection `### Open questions before handover`.
Zero questions means handover-ready. `runbooks/STATUS.md` counts handover-ready runbooks per agent.
A cold read is never an error in CI — a machine cannot judge clarity — but a job is not handed to
another agent until its runbook reads zero.

## The machine check

`python3 tools/lint_runbooks.py` runs on every push and once a day (a deadline can pass
with nobody committing). It fails the build when a runbook misses a section, the owner
line has no date, a credential shows up, a registry points at nothing, or a deadline in
`runbooks/agents.json` has passed with a registry or runbook still missing.
`--write-status` writes `runbooks/STATUS.md`, the per-agent count your coordinator reads.

## Prove a runbook

Give one runbook — and nothing else — to a different agent and ask it to run the job. If it
has to ask a question, fix the runbook.
