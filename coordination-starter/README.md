# Coordination starter — your agent workspace

Copy this folder into a new local directory for practice. Later, use your own
authorized private repository or supported shared record. Do not publish private
operations in a fork of the public skills source. Nothing in this folder installs
a skill, connects an app, starts a schedule or grants permission.

| File | Purpose |
|---|---|
| [AGENTS.md](AGENTS.md) | Instructions each worker reads before acting |
| [COORDINATION.md](COORDINATION.md) | Record authority, claims and handoff route |
| [SHARED-MEMORY.md](SHARED-MEMORY.md) | Dated facts with sources and scope |
| [decisions/DECISIONS.md](decisions/DECISIONS.md) | Actual owner decisions and their evidence, scope and limits |
| [status/JOBS.md](status/JOBS.md) | Unowned work and task references |
| [status/NOW.md](status/NOW.md) | Current claims and checkpoints for the same IDs |
| [agent-notes/README.md](agent-notes/README.md) | What goes in a dated run receipt |
| [task-template.md](task-template.md) | One record for the task's scope, criteria and next action |
| [handoff.pending.json](handoff.pending.json) | Start a real receipt without claiming delivery or review |
| [handoff.example.json](handoff.example.json) | Synthetic receipt shape; replace with observed evidence |
| [handoff.schema.json](handoff.schema.json) | Receipt fields; CLI also checks cross-field consistency |

Set your owner, reviewer, allowed actions and record authority before real work.
The empty tables intentionally claim no completed work. Record your actual source
commit; directory names or file dates are not release identities. With local
source edits, also keep content hashes of the actual instructions used.

Start with task `practice-001` from the public setup guide. Read the source, make
one local result, test a fresh-session continuation and keep the review. A failed
read is useful evidence of a missing route; it is not permission to widen access.

## Compatibility and existing workspaces

This is the single maintained starter at its established public path.
The earlier flat edition used root `JOBS.md` and `NOW.md`; those two files now
point to the active [status/JOBS.md](status/JOBS.md) and
[status/NOW.md](status/NOW.md). They are not additional queues.

An existing team should keep its current authority until an explicit migration:
snapshot live records, choose one board location, preserve IDs, claims and
history, update every reader/writer path, then test a fresh read and handoff.
Never copy blank templates over a live workspace or run both board layouts.
See the public [setup guide](https://github.com/dennisyu/local-service-spotlight-skills/blob/main/START-HERE.md)
for the first practice and private-repository acceptance checks.
