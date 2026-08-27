---
name: "skill-registry"
description: "Keep every BlitzMetrics / Local Service Spotlight skill centrally available and activatable. Use when adding a new skill, auditing the skill inventory, wiring a skill into a scheduled job or agent, reconciling what is installed against the canonical pack, or when someone asks 'is this skill part of our framework', 'where do our skills live', 'why isn't this skill running', or 'add this to the skill pack'."
---

# Skill Registry

**Use this whenever a new capability gets built.** A method that lives in a chat thread, a Google Doc, or a loose `.skill` file is not part of the framework — nothing propagates it, no agent can find it, and no scheduled job can activate it. This skill is the intake gate that prevents that.

## The five states and systems to audit

Know which one you are touching. They propagate very differently.

| # | System | What it proves | What it does not prove | Who can write to it |
|---|---|---|---|---|
| 1 | **Canonical GitHub marketplace** | A skill is available in a validated commit | Any account installed or synced it | Maintainers, by reviewed pull request |
| 2 | **Installed plugins and account skills** | A named account can see the capability | A fresh chat can activate it correctly | The account/workspace owner |
| 3 | **Cloud scheduled tasks** | A schedule exists for one cloud account | A firing succeeded | Authorized scheduler tools |
| 4 | **Local Cowork scheduled jobs** | A schedule exists on one machine | Cloud health or another machine's state | The desktop app on that machine |
| 5 | **Fleet copies and run receipts** | A site has a version and a run left evidence | The rest of the fleet matches it | The deployment job and receipt store |

**System 1 is the only canonical source.** The member install guide is the front
door, while `https://github.com/dennisyu/local-service-spotlight-skills` is the source Claude
subscribes to. Account skills are per-person. If a capability matters to more than
one person, put it in the marketplace and verify each target environment with a
receipt.

## Intake gate — run this for every new skill

Do not consider a skill "done" until all seven pass.

1. **Does it exist as a `SKILL.md` with valid frontmatter?** `name` (kebab-case, matching the directory) and a third-person `description` containing the literal phrases someone would actually type.
2. **Is it under the canonical repository's `skills/` directory** — not a loose file or chat attachment?
3. **Is it listed in `blitzmetrics-everything`** and every appropriate topical bundle?
4. **Did repository and official marketplace validation pass on a pull request?** Never publish from `/upload/main`.
5. **Can a fresh chat activate it?** Test a literal trigger phrase from the description and save the receipt.
6. **Can a scheduled job activate it?** Name the exact skill in a complete standalone prompt and verify the first firing, not just the schedule definition.
7. **Is its state recorded accurately** in `references/inventory.md` and the operational register — Available, Installed, Enabled, Tested, Scheduled, or Observed?

If a step cannot be completed in this session, **say so explicitly and name who has to do it.** Reporting a skill as "shipped" when it is sitting in a chat thread is the specific failure this gate exists to prevent.

## Shipping it so people actually install it

Building the skill is not the hard part. The loss is in the last inch — someone
downloads a pack and never installs it, because nothing told them a download is
not an install. → `references/distribution.md`

The short version:

- **Use the GitHub marketplace for groups.** Send members to the install guide,
  then give Claude the canonical repository URL. Use `.plugin` instead of `.zip`
  only for direct-file fallback. Convert legacy packs with
  `scripts/pack2plugin.py`.
- **Say the install step out loud every time you deliver one.** "This is
  delivered, not installed — accept the card above."
- **Report only the state evidenced.** Delivered, installed, enabled, tested,
  scheduled, and observed are separate states.
- **Link the install guide** from every place a file can be downloaded.

## Updating packs regularly

Use `references/update-contract.md`. Keep update checking separate from skill
authoring: a scheduled checker compares the environment's accepted commit with
GitHub `main`, validates a candidate, and deploys to one canary. It never rewrites a
skill or commits to `main`.

Promote a candidate only after a fresh-chat activation receipt passes for every
changed skill. Roll out in small cohorts with one publisher, one environment lock,
stable release/run IDs, a separate auditor, and the prior accepted commit recorded
for rollback. A no-change week still writes a receipt so silence cannot be confused
with a job that failed to run.

## Wiring a skill into a scheduled job

A scheduled task starts a **fresh session with no memory of the conversation that created it**. So:

- Write the trigger prompt as a complete standalone instruction.
- Name the skill explicitly in the prompt (`Use the geo-visibility-audit skill.`). Do not rely on implicit triggering in an unattended run.
- Name the client, the properties, and where the output goes — the fresh session knows none of it.
- State the deliverable and its destination (post to thread X, save to folder Y). An unattended run with no destination produces nothing anyone sees.
- Give every firing a stable run ID and require a durable success or failure receipt. A schedule object is not a successful run.
- Add a watchdog for a missing receipt after the expected time plus a grace period. Explicit failures are not the only failure mode.
- Use the **scheduled-task tools** (`create_trigger`, `send_later`, `list_triggers`, `update_trigger`, `delete_trigger`). Never use the in-process cron tools — anything they schedule dies when the session ends and the job silently never runs.

Cron is UTC. Convert from the owner's local time, and shift the day fields if the conversion crosses midnight.

## Wiring a skill into an agent

Put an agent definition in the plugin's `agents/` directory when the skill should
run as a delegated, self-contained job — a weekly audit, a fan-out across clients,
or anything a person would otherwise babysit. Keep execution and audit separate:
Claude writes the production receipt; Codex checks the source, receipt, output
assertions, and error on a separate branch; a human approves merges and production
schedule or credential changes.

## Reconciliation — run monthly, or when something feels missing

1. List the canonical marketplace commit and all 28 available skills.
2. List what each target account and fleet site actually reports as its commit/version and installed skills.
3. Diff them. **Every target behind the canonical commit is a propagation failure; every untracked local skill is an orphan.**
4. For each recurring scheduled job, confirm the skill it names still exists under that exact name. Renaming a skill silently breaks every job that calls it.
5. Check the local desktop scheduled jobs separately. They do not appear in a cloud listing, so a cloud-only audit will report them as absent when they are running fine — and will miss them entirely when they are broken.
6. Reconcile each scheduled job's last attempted, succeeded, failed, and next expected timestamps against its durable receipts.
7. Record canonical facts in `references/inventory.md`, private client facts in the operational register, and report failed assertions and diffs rather than totals alone.

## Field lessons

- **A `.skill` file delivered into a chat is a delivery, not an installation.** You get no signal whether the person saved it. Report it as delivered, never as saved, and follow up.
- **Sessions cannot install skills.** The skill files on disk are a read-only cache; editing them changes nothing durable. Package and deliver, or publish the plugin — those are the only two real paths.
- **The description is the activation surface.** A skill nobody can trigger is inventory, not capability. Write descriptions with the words people actually type, then test by using one of those phrases cold.
- **Name the gap out loud.** When a capability exists but is not yet propagating, saying so plainly is more valuable than a clean-looking summary that hides it.

## Pairs with

`skill-creator` (authoring and evals) · `cowork-plugin` (packaging and publishing) · the weekly MAA cadence.
Inventory and the current gap list: `references/inventory.md`.
For scheduled marketplace checks, canary rollout, locks, receipts, and rollback:
`references/update-contract.md`.

<!-- shared-rule:silent-media-playback:start -->
## Silent media playback

- Never let audio from browser, video, audio, presentation, or application testing play through the user's speakers unless the user explicitly asks to hear it.
- Before starting any media playback, mute the player and set its volume to zero. Keep it muted for the full test, including replays, reloads, new tabs, and alternate players.
- Apply this rule to the primary agent and every delegated agent. Include the mute requirement whenever work that may involve media playback is delegated.
- If the mute state cannot be controlled and verified before playback, do not start playback. Use metadata, captions, transcripts, frames, screenshots, network state, or player state instead.
- Only unmute when the user explicitly requests audible playback in the current task.
<!-- shared-rule:silent-media-playback:end -->
