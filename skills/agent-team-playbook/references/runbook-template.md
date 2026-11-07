# <Task name — what it does, in plain words>

Copy this file to `runbooks/<agent>/<task-slug>.md`, fill every section, and add a row to
`runbooks/<agent>/INDEX.md` in the same commit. Standard: `runbooks/README.md`. Delete
this paragraph.

## 1. Purpose

What this task achieves and why it exists, in one or two lines a fifth grader follows.

## 2. Trigger / cadence

The schedule (with timezone), the event that fires it, or "manual — when <situation>".
Where the schedule actually lives (scheduler id, workflow file, Grok routine name).

## 3. Inputs

Data, files, accounts, connectors and sessions the task needs — names and locations
only. For anything secret: the store and the key name, never the value.

## 4. Steps

The exact procedure or prompt, in order. Real commands, real queries, real URLs. If a
prompt drives it, paste the prompt (or link the repo file holding it verbatim).

## 5. Output

Format, destination, and what "done" looks like when you look at it there.

## 6. Receipt

Where proof that it ran lands (file, URL, message id), and how a verifier checks it.

## 7. Failure modes

What breaks, what it looks like, what to do. Name the "silent when healthy" trap if the
task has one — the run that looks fine and delivered nothing.

## 8. Owner + history

Current owner (agent and runtime). Who ran it before. Date of the last successful run
(YYYY-MM-DD) and where that run's receipt is.
