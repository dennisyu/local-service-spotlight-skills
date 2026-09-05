# Acceptance checks and receipts

Automated validation proves the repository is internally consistent. It cannot
prove that a particular Claude account synced the marketplace, activated a skill,
or completed a scheduled job. Use these checks for that last mile.

Record every run with:

- date and time, including timezone;
- Claude surface and plan (web, desktop, or Cowork);
- account or workspace tested;
- marketplace commit SHA or displayed version;
- result, output link, and screenshot or error text;
- tester's name.

Do not record passwords, tokens, or private client data here.

## A. Fresh-account marketplace install

1. Start with an account or workspace that does not already have this marketplace.
2. Add `https://github.com/dennisyu/local-service-spotlight-skills` as a marketplace.
3. Confirm all five bundles appear.
4. Install `lss-everything`.
5. Confirm all 32 expected skills are listed and enabled.
6. Start a fresh chat and use a literal trigger phrase from one selected skill.
7. Confirm the selected skill activates and its output matches its contract.
8. Restart Claude, return to a fresh chat, and repeat the activation check.

Pass only when all eight steps have evidence. A visible marketplace card alone is
not a pass.

## B. Update propagation

1. Note the currently installed marketplace commit or version.
2. Merge a harmless, identifiable canary change through a pull request. For a
   propagation check, use an agent-behavior rule such as
   `silent-media-playback`, whose scope requires it in all 32 skills; a narrower
   rule should appear only in its applicable skills.
3. On the test account, use the surface's **Sync** or **Update** control. If
   third-party marketplace auto-update is enabled, also record whether it arrived
   without that manual action.
4. Confirm the displayed commit/version changed and the canary is present.
5. Start a fresh chat and repeat the activation test.

Report **update channel verified** after a manual sync succeeds. Report
**auto-update verified** only when an unattended update is actually observed on
the named surface and account.

## C. Scheduled-job health

For every production job, keep one row in the fleet audit with:

| Field | Required evidence |
|---|---|
| Job ID and owner | Exact stable identifier and accountable person |
| Runtime | Cloud or the exact desktop/machine |
| Skill and version | Exact skill name plus marketplace commit/version |
| Schedule | Local timezone and normalized UTC time |
| Last attempted | Timestamp from the scheduler, not agent memory |
| Last succeeded | Timestamp plus output or artifact link |
| Last failed | Timestamp plus unedited error text |
| Next expected | Timestamp used by the watchdog |
| Alert route | Person/channel that receives missed-run alerts |

A job is **Scheduled** when its definition exists. It becomes **Observed** only
after a firing leaves a receipt. Alert when `now` is later than `next expected +
grace period` and no new success or failure receipt exists.

## D. Claude/Codex separation of duties

- **Claude executes** the production workflow and writes a run receipt.
- **Codex audits** the repository, receipts, failures, and claimed state.
- **A human merges** marketplace changes and approves changes to production
  schedules or credentials.

Claude must not grade its own run as healthy from prose alone. Codex must not edit
the same production file or schedule while Claude is executing it. Use a branch,
job lock, and stable run ID so one agent can propose and the other can verify.

## E. Silent media-playback canary

Run this check after any change to `standards/silent-media-playback.md`, the sync
script, or a workflow that may play audio or video.

1. Sync the candidate marketplace commit to one named canary account.
2. Start a fresh chat and ask a media-capable skill to verify a public video or
   audio embed. Do not tell it to play sound.
3. Use a test player or browser trace that records `muted`, `volume`,
   `currentTime`, and the order of `volumechange` and `play` events.
4. Pass when either the task completes from silent evidence without any `play`
   event, or every `play` event occurs only after `muted=true` and `volume=0`.
5. Repeat once through a delegated agent and confirm the same event order.
6. Record the candidate commit, surface, account, prompt, event trace or
   screenshot, tester, timestamp with timezone, and whether any audible output
   was heard.

Fail on audible output, playback before silence is established, missing state
evidence, or a delegated agent that did not receive the rule. A prose claim such
as “I kept it muted” is not an acceptance receipt.

## F. House-rule propagation and fleet sweep

Run after adding or amending anything in `standards/`.

**Propagation — the rule reached the skills**

1. `python3 scripts/sync_shared_rules.py --check` exits 0.
2. `python3 scripts/validate_marketplace.py` exits 0 — this checks every rule in
   every skill to which its declared scope applies, not one hardcoded rule.
3. Count the copies and record the number. For example,
   `grep -rl "shared-rule:silent-media-playback:start" skills/ | wc -l` returns
   the current master skill count (32). Published-HTML and design-review rules may
   have fewer copies; their count must match the scopes derived by the validator.
4. On a canary account, sync the commit and start a fresh chat. Ask the agent to
   state the house rule without naming the file. Record the reply verbatim.

Step 4 is the only one that proves distribution reached a *user*. Steps 1–3
prove the repository is consistent, which is not the same claim.

**Enforcement — the sweep can actually fail**

5. `python3 scripts/fleet_check.py --self-test` exits 0. Every check flags its
   violating samples and clears its clean ones.
6. Sweep the fleet and keep the JSON:
   `python3 scripts/fleet_check.py --targets <your fleet file> --json report.json`
7. Record, per URL: findings, rules **not applied** (wrong target tag), and pages
   **not swept** (fetch failed). A page that could not be fetched is not clean.
8. Confirm at least one known-bad fixture is caught. A sweep that has never
   failed has not been shown to work.

**Status vocabulary applies here too.** A rule in `standards/` is **Available**.
A rule stamped into the skills is **Installed**. A rule an agent restates on a
canary account is **Tested**. A sweep in the Friday fleet audit is **Scheduled**.
Only a completed run with a timestamped report is **Observed**.

Record the commit SHA, the fleet file used, counts of blocking/warning/not-swept,
and the tester. Do not record client URLs here if the list is not public.
