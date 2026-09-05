# Skill inventory — canonical facts and per-environment evidence

Last canonical repository audit: 4 September 2026.

This file separates what the marketplace makes **available** from what is actually
**installed, enabled, tested, scheduled, or observed**. Never infer one state from
another.

## Canonical marketplace

| Field | Current fact |
|---|---|
| Repository | `https://github.com/dennisyu/local-service-spotlight-skills` |
| Marketplace manifest | `.claude-plugin/marketplace.json` |
| Skills in `lss-everything` | 32 after merge of `personal-brand-audit` |
| Topical bundles | 4 |
| Validation | Pull-request and main-branch GitHub workflow |
| Contribution path | Branch → checks → review → merge |

This repository is now the identifiable source of truth. The install guide at
`https://localservicespotlight.com/install/` is the member-facing front door, not
a competing copy of the skill files.

`personal-brand-audit` is Available after merge only, not Installed. It orchestrates the
evidence, authority, reputation, GEO, entity, Content Factory, and Dollar-a-Day skills into
an exact 20-page visual audit and agent action plan. Availability does not prove that any
account installed, enabled, or tested it. The GCT screen still does not create client or
execution authority.

## Available bundles

| Bundle | Skills available |
|---|---:|
| `lss-everything` | 32 |
| `authority-and-reputation` | 8 |
| `content-engine` | 7 |
| `client-operations` | 10 |
| `quality-and-standards` | 7 |

The four topical bundles partition the 32-skill master: every skill appears in exactly one
topical bundle. `lss-everything` remains the one complete install.

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

1. After merge, update the public install guide from the current production
   `1.3.0` / 31-skill text to the merged manifest version/count, then verify the
   repository, `lss-everything`, version, and count anonymously at
   `https://localservicespotlight.com/install/`.
2. Generate the public `personal-brand-audit` skill page from the merged source and verify
   the anonymous page, links, and install handoff. Do not use `/skills/` as the install rail.
3. Complete the fresh-account marketplace acceptance test and attach its receipt.
4. Complete the manual update propagation test, then separately test unattended
   third-party auto-update on every supported Claude surface.
5. Export the cloud scheduled-task inventory into the required register fields.
6. Export each desktop Cowork job from the machine that owns it.
7. Add watchdog alerts for missing receipts, not just explicit failures.
8. Run a harmless end-to-end canary on one Spotlight site before fleet rollout.
9. Reconcile the fleet by commit/version; do not use file timestamps or agent
   summaries as a substitute.

Update this document when canonical facts change. Update the private operational
register after every firing. Report diffs and failed assertions, not just totals.
