# Skill inventory — canonical facts and per-environment evidence

Canonical state is commit-bound. Record the exact commit in each acceptance
receipt; a remembered audit date is not a release identity.

This file separates what the marketplace makes **available** from what is actually
**installed, enabled, tested, scheduled, or observed**. Never infer one state from
another.

## Canonical marketplace

| Field | Current fact |
|---|---|
| Repository | `https://github.com/dennisyu/local-service-spotlight-skills` |
| Marketplace manifest | `.claude-plugin/marketplace.json` |
| Skill and bundle membership | Derived from the manifest at the recorded commit |
| Validation | Pull-request and main-branch GitHub workflow |
| Contribution path | Branch → checks → review → merge |

This repository is now the identifiable source of truth. The install guide at
`https://localservicespotlight.com/install/` is the member-facing front door, not
a competing copy of the skill files.

`gct-screen` and `social-amplification-engine` are Available after merge only, not
Installed. The screen evaluates one GCT triangle through evidence gates; it does not
use an invented weighted score and it does not create client or execution authority.
SAE course Stages 2–4 Goals/Content/Targeting remain the execution taxonomy after an
accepted engagement and roster gate.

## Available bundles

The manifest is the only bundle inventory. Its `plugins` array owns every bundle
name and each bundle's `skills` array; the validator checks those references and
the description's derived count. Do not copy that list or its totals here.

## Per-account installation register

Repository inspection cannot determine this table. Add a row only from the named
account/workspace and attach a receipt from `ACCEPTANCE.md`.

| Account/workspace | Surface | Bundle | Commit/version | Installed | Enabled | Fresh-chat tested | Receipt |
|---|---|---|---|---|---|---|---|
| _Not yet evidenced_ | — | — | — | Unknown | Unknown | Unknown | — |

## Scheduled-job register

Cloud and local Cowork schedules live in different runtimes. A cloud-only listing
cannot prove that a desktop job exists or is healthy. Likewise, a schedule object
does not prove a firing completed.

Track the operational register outside this public repository if it contains
client names or private output links, but require these fields:

| Job ID | Owner | Runtime/machine | Skill | Commit/version | Schedule + timezone | Last attempted | Last succeeded + output | Last failed + error | Next expected | Alert route |
|---|---|---|---|---|---|---|---|---|---|---|

Use these states:

1. **Scheduled** — definition exists.
2. **Attempted** — scheduler emitted a timestamped run ID.
3. **Observed success** — expected artifact exists and passes its assertions.
4. **Observed failure** — unedited error and run ID were recorded.
5. **Missing run** — no receipt after the expected time plus grace period.

“Claude says everything is great” is not evidence for any of these states.

## Open operational checks

1. Complete the fresh-account marketplace acceptance test and attach its receipt.
2. Complete the manual update propagation test, then separately test unattended
   third-party auto-update on every supported Claude surface.
3. Export the cloud scheduled-task inventory into the required register fields.
4. Export each desktop Cowork job from the machine that owns it.
5. Add watchdog alerts for missing receipts, not just explicit failures.
6. Run a harmless end-to-end canary on one Spotlight site before fleet rollout.
7. Reconcile the fleet by commit/version; do not use file timestamps or agent
   summaries as a substitute.

Update this document when canonical facts change. Update the private operational
register after every firing. Report diffs and failed assertions, not just totals.
