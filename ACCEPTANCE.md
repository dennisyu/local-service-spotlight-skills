# Acceptance checks and receipts

Use these checks before you trust a skill to do work for your business. Show that
the right skill loaded, made the expected result, and used only approved access.
Keep the proof so another person can check it.

Start at [START-HERE.md](START-HERE.md) for setup and use
[Learn, Do, Teach in practice](docs/agent-setup/LEARN-DO-TEACH.md) for the learning loop.
Repository checks prove source consistency. They do not prove that a named
account installed or activated a skill, or that a scheduled job ran.

Record every run with:

- date and time, including timezone;
- product, surface, plan and execution environment (for example Claude web,
  desktop or Cowork; do not infer access from the model name);
- account or workspace tested;
- marketplace commit SHA or displayed version;
- result, output link, and screenshot or error text;
- tester's name or actual agent identity;
- practice or authorized real work, original acceptance criteria and input provenance;
- approved effects, checks performed, limitations and recovery target when applicable.

Do not record passwords, tokens, or private client data here.

## A. Fresh-account marketplace install

1. Start with an account or workspace that does not already have this marketplace.
2. Add `https://github.com/dennisyu/local-service-spotlight-skills` as a marketplace.
3. Compare the displayed bundles with the tested commit's marketplace manifest;
   record the expected and displayed names and counts.
4. Install `lss-everything`.
5. Compare the enabled skill list with the `lss-everything` array in the tested
   commit and record both displayed and expected counts.
6. Start a fresh chat and use a literal trigger phrase from one selected skill.
7. Confirm the selected skill activates and its output matches its contract.
8. Restart Claude, return to a fresh chat, and repeat the activation check.

Pass only when all eight steps have evidence. A visible marketplace card alone is
not a pass.

## B. Update propagation

1. Note the currently installed marketplace commit or version.
2. Merge a harmless, identifiable canary change through a pull request. For a
   propagation check, use an agent-behavior rule such as
   `silent-media-playback`, whose scope requires it in every skill in the tested manifest; a narrower
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

## D. Independent execution and review

- **Executor:** performs the authorized workflow and writes a run receipt.
- **Reviewer:** independently retrieves the original acceptance criteria, source
  inputs and actual destination, then tests the executor's claims and omissions.
- **Decision owner:** resolves consequential decisions within their authority.
  Routine authorized documentation changes follow the reviewed pull-request route
  and selective-review rule; there is no blanket per-item Dennis merge gate.

Claude as executor and Codex as reviewer is one arrangement, not a requirement
that depends on those products. A different model alone does not prove review
independence. Use a fresh context and the original artifacts rather than only the
builder's summary. Record reviewer identity, tested revision, disagreements,
checks and result. Preserve required specialist review and explicit holds.

Keep one writer per task or environment. Use a branch, job claim/lock and stable
run ID; the reviewer must not edit the same production file or schedule while
the executor is using it. Neither a source merge nor reviewer agreement creates
missing access, changes a production schedule or grants a new privilege.

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
3. Count the copies and compare that result with the scope-derived skill count;
   published-HTML and design-review rules may have fewer copies than an
   agent-behavior rule, but every total must match the validator's derived scope.
4. On a canary account, sync the commit and start a fresh chat. Ask the agent to
   state the house rule without naming the file. Record the reply verbatim.

Step 4 establishes that a named account could retrieve the rule in that test.
It does not prove compliance. Follow it with a fresh task that exercises the rule
and inspect observable behavior or the actual artifact; use section E for media.
Steps 1–3 prove source consistency only.

**Enforcement — the sweep can actually fail**

5. `python3 scripts/fleet_check.py --self-test` exits 0. Every check flags its
   violating samples and clears its clean ones.
6. Sweep the fleet and keep the JSON:
   `python3 scripts/fleet_check.py --targets <your fleet file> --json report.json`
7. Record, per URL: findings, rules **not applied** (wrong target tag), and pages
   **not swept** (fetch failed). A page that could not be fetched is not clean.
8. Confirm at least one known-bad fixture is caught. Add a reviewer-selected
   failure beyond the checker's own examples when practical, plus an unreachable
   target or missing-input case. Use local fixtures or approved test targets,
   never break a live customer page. A failed fetch must be reported as not
   swept; passing declared samples does not establish broad coverage.

**Keep source propagation separate from account and job evidence.** A prepared
rule is a source change; after merge it is **Available** in that repository or
release. **Delivered** requires the intended receiver to open the exact artifact
revision. Stamping it into distributed skill files does not prove **Installed**
or **Enabled** in an account. Record those states from the named runtime, and
record **Tested** only after the selected skill loads and produces a checked
fresh result. **Scheduled** means the job definition exists; **Observed** means
a real firing left a timestamped output or failure.

Record the commit SHA, the fleet file used, counts of blocking/warning/not-swept,
and the tester. Do not record client URLs here if the list is not public.

## G. Existing-access reuse canary

After installing or syncing `reuse-agent-access`, start a fresh session in each
runtime being claimed. Name one service already within the user's authorized
scope, request a harmless read, and record which installed skill loaded.

Pass only when the intended app, execution device, browser profile or connector,
non-secret account identity, task scope, and actual read result are established.
Do not export credentials or use a write as the canary. Record platform consent
or secure login still required as `NEEDS_USER_ACTION`, not a successful read.
A connected extension alone does not pass; one domain does not prove all domains.

Check a second fresh session for reuse when persistence is claimed. Keep the
receipt in the existing private access register with the tested source/installed
revision and timestamp. Publish only a redacted distribution result. No schedule,
credential migration or fleet-wide access claim is created by this check.


## H. Cold-operator Learn, Do, Teach replay

Run this after a substantive new workflow or an important correction. A replay
may be safe public/synthetic practice or authorized real work; label which. Use
real task evidence separately before claiming production mastery.

1. Pin the guide and input revisions, task ID, permitted effects, destination,
   acceptance criteria and stop conditions. Verify the receiver can read the
   same references through their own supported access.
2. Give a fresh person or agent only those materials. Do not supply the author's
   diagnosis, unstated steps or expected solution. Keep sensitive inputs on
   the approved private rail.
3. Have the operator check for an existing task, claim one owner, execute the
   procedure, run its checks and record an artifact reference. If two agents
   try to claim it, the second must reconcile the current claim instead of
   duplicating the work. A written claim is not an atomic lock; use supported
   serialization or arbitration where concurrent writes are possible.
4. The receiver opens the exact final artifact/revision and acknowledges it. A
   producer save, issue filing, notification attempt or summary is not delivery.
5. A separate reviewer checks the result against original criteria at the actual
   destination. Challenge one relevant failure in a fixture: stale source,
   duplicate task, denied access, missing receipt or incomplete output. The
   procedure must stop or report the gap rather than mark it successful.
6. Record any author help required, ambiguous step, unverified judgment, failed
   check, correction and next action. Amend the master, rerun affected checks
   and repeat the failed part with a fresh context.

Pass for the tested scope only when the operator completes the criteria without
unstated author coaching and the reviewer can inspect the result. Missing access
is a recorded blocked test, not proof that the method succeeded. Publish a
redacted receipt linking the source change, test method, evidence and limits; do
not publish private account identifiers or client records.

Do not manufacture all-model consensus from several agents in one runtime.
Record which actual agents/models reviewed, what they read, their dissent and
what was changed. Cross-runtime adoption still needs each receiver's own receipt.
