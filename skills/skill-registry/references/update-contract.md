# Skill-pack update contract

Use this contract for a person, mastermind, agency, or fleet that needs regular
updates without agents overwriting one another.

## One canonical route

```text
Source:  GitHub main branch
Change:  branch → pull request → automated checks → human merge
Install: Claude marketplace repository URL
Update:  compare commit → canary sync → activation test → cohort rollout
Proof:   immutable receipt per account/site/run
```

The canonical repository is
`https://github.com/dennisyu/local-service-spotlight-skills`. A ZIP is a dated snapshot and
must include its source commit; it is not the update channel.

## Scheduled update checker

Run weekly at a named local time and owner. The checker must:

1. Read the latest `main` commit from GitHub and the last accepted commit from the
   environment receipt. Do not compare file modification times.
2. If they match, write a no-change receipt and stop.
3. If they differ, show the changed skill names, deleted/renamed paths, manifest
   changes, and scheduled prompts that call those names.
4. Run `python3 scripts/validate_marketplace.py`, repository tests, and Claude's
   marketplace validator on the candidate.
5. Sync one canary account/site. Start a fresh chat and trigger every changed skill
   with a literal phrase from its description.
6. Promote only after the canary receipt passes. Roll out in small cohorts, stopping
   on the first failed or missing receipt.
7. Store the accepted commit, previous commit, environment, surface, tester/agent,
   timestamps, validation result, activation result, and rollback target.

The checker may discover and test an update. It may not invent skill changes or
commit directly to `main`.

## Publisher, executor, auditor

- **Publisher:** proposes source changes on one branch and never grades its own
  rollout.
- **Executor:** syncs the approved commit and writes run receipts.
- **Auditor:** reads source and receipts, checks assertions, and opens a separate
  corrective branch. It does not edit the same environment during execution.
- **Human owner:** merges source changes and approves production schedule,
  credential, or rollback decisions.

Use a stable `release_id`, `run_id`, and environment lock. If a lock exists, another
agent reports `waiting_on_lock`; it does not start a competing deployment.

## Receipt states

| State | Required evidence |
|---|---|
| Available | Merged commit containing the skill |
| Candidate | Commit passed repository validation |
| Synced | Named environment reports the candidate commit/version |
| Activated | Fresh chat invoked the expected changed skill |
| Observed | Scheduled firing produced expected output or an unedited error |
| Accepted | Canary/cohort assertions passed and rollback target was recorded |

Never report Accepted from a prose summary. Compute it from receipts.

## Failure and rollback

- Stop on failed validation, missing skill, unexpected rename, activation failure,
  missing receipt, or output assertion failure.
- Keep the prior accepted commit as the rollback target.
- Re-sync the prior commit or restore the prior package according to the Claude
  surface's supported controls.
- Record the failure before rollback so it remains auditable.
- Open a corrective branch; do not hot-edit downstream copies.

## Member communication

Every release notice must say:

- what changed and why;
- the source commit/version;
- whether action is required on that Claude surface;
- which fresh-chat phrase verifies it;
- where to report a failure;
- whether manual sync or unattended auto-update was actually observed.

Do not say “everything updates automatically” without a receipt from that exact
surface and account.
