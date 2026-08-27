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
4. Install `blitzmetrics-everything`.
5. Confirm all 28 expected skills are listed and enabled.
6. Start a fresh chat and use a literal trigger phrase from one selected skill.
7. Confirm the selected skill activates and its output matches its contract.
8. Restart Claude, return to a fresh chat, and repeat the activation check.

Pass only when all eight steps have evidence. A visible marketplace card alone is
not a pass.

## B. Update propagation

1. Note the currently installed marketplace commit or version.
2. Merge a harmless, identifiable canary change through a pull request.
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

## F. Grok Build native plugin install

Run the native manifest validator from the repository root:

```bash
grok plugin validate .
```

For a fresh-environment install receipt, isolate the canary from existing Grok
plugins, install the canonical repository, and verify the stable plugin identity
and full inventory:

```bash
grok_canary_dir=$(mktemp -d /tmp/blitzmetrics-grok-canary.XXXXXX)
GROK_HOME="$grok_canary_dir" grok plugin install dennisyu/blitzmetrics-skills --trust
GROK_HOME="$grok_canary_dir" grok plugin details blitzmetrics-everything
GROK_HOME="$grok_canary_dir" grok inspect --json | python3 -c 'import json,sys; d=json.load(sys.stdin); p=next(p for p in d["plugins"] if p["name"] == "blitzmetrics-everything"); assert p["enabled"] and p["provides"]["skills"] == 27; print("Grok canary passed: blitzmetrics-everything, 27 skills")'
```

After installing in the account being accepted, start a fresh headless agent and
test actual skill activation:

```bash
grok -p 'Use the skill-registry skill. In one sentence, identify the numbered registry system that is the only canonical source.'
```

Pass when `grok plugin validate .` succeeds, the inventory command prints the
exact canary line above, and the model answer identifies **System 1, the canonical
GitHub marketplace**. Record the Grok version, repository commit, plugin version,
all command output, account/environment, tester, and timestamp. Installation and
discovery do not by themselves prove activation.
