# One task record, one outcome owner

Before real work the owner records the authoritative location here. During local
practice it is this folder. After authorization it may be a private repository or
another supported shared system. Do not maintain competing boards in two apps.

## Task and claim

Use one stable task ID from request through receipt and retries. JOBS lists work
without an owner; NOW records claims and checkpoints for those same tasks. Each
claim names the outcome owner, worker/runtime, reviewer, write scope, source
revision, start time, next recheck time, allowed actions and acceptance test.

The shared system needs a serialized or version-checked claim write. Read the
authoritative latest state, propose the claim, commit/save against that revision,
and read it back. A rejected version or competing claim stops execution until
reconciled. A Markdown row is not a distributed lock. A stale claim cannot safely
be stolen without checking prior actions and reconciling with its owner.

## Handoff

Record the actual supported receiver channel here before claiming unattended
handoff. If there is none, mark it UNKNOWN. A repository change sends no work to
another assistant unless its connector/notification/pickup has actually worked.

Send the existing task ID, exact artifact location and revision, scope, acceptance
criteria, owner, reviewer and next action. The receiver reads the same artifact
and leaves an acknowledgment with evidence and a timezone-aware time. Until that
read, status is NOT_DELIVERED. Record a denied read without widening permissions.

## Completion and recovery

A separate reviewer opens the source and result. VERIFIED means its observed
PASS matches the original acceptance criteria. BLOCKED names the failed step,
evidence, owner, recheck time and bounded next action. Reconcile uncertain writes
before retrying; never repeat an external action merely because a receipt is late.

For a public lesson, remove private details and retain only evidence approved for
public use. Internal delivery, public publication and installed adoption are
separate results. Source changes, account updates and schedules need separate
receipts. No schedule is created by these instructions.
