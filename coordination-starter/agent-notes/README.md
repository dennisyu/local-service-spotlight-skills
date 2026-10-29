# Run receipts

One dated Markdown file per substantive run, linked from the existing task.
Use `YYYY-MM-DD-agent-task.md`; preserve the same task ID across sessions.

Record these fields:

- Task ID, request, outcome owner, worker/runtime and reviewer.
- Source locations, exact revisions or UNKNOWN, allowed actions and stop rule.
- Original acceptance criteria and actual inputs.
- What changed, artifact reference and revision/hash.
- Checks, source/destination observations, failures, correction and remaining gaps.
- Receiver's exact-artifact read and acknowledgment, or NOT_DELIVERED.
- Independent reviewer verdict with evidence, or NOT_CHECKED.
- Learn → Do → Teach correction, canonical procedure changed and cold replay.
- Next action, next owner and next recheck time with timezone.
- `Verified:` observation and time, or `Verified: NO` with missing evidence.

Use `../handoff.example.json` as a synthetic shape example, not evidence. Keep real
receipts private. A checker can validate their consistency, not their truth.
