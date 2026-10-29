# AGENTS.md — read this first, every session

You are one of several AI agents sharing this repository. The human who owns
this team is not your messenger and not your approval clerk. Work from the
record.

## Before you work

1. Read `NOW.md` (what is active) and `JOBS.md` (the board).
2. Read `SHARED-MEMORY.md` for standing facts and `decisions/DECISIONS.md`
   for decisions already made. Do not ask the human to repeat either.
3. If your task is already claimed by another agent with a fresh timestamp,
   pick different work or coordinate in the task file. Do not duplicate.

## While you work

- Claim before you build: add your agent name + timestamp to the job row.
- Keep the working record in the task's file under `tasks/<job-id>/`.
- Stay inside the authority the human gave for this job. Decisions already
  in `decisions/DECISIONS.md` cover agent-to-agent steps — cite the
  decision ID instead of asking again.

## When you finish

- Verify the result at its destination (live page, sent message, real
  record), not from your draft.
- Update the job row in `JOBS.md`: status, link to the result, check run.
- Write the handoff in the task file: done / not done / next step.
- Post a short pointer in the channel the next agent watches.
- If the run taught a reusable lesson, update the relevant skill or
  `SHARED-MEMORY.md` in the same session.

## Never

- Never report "missing / failed / not sent" from a single check.
- Never put passwords, keys, or private client data in this repo.
- Never treat another agent's silence as agreement.
