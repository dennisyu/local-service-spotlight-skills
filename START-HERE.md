# Set up your AI agents with Dennis Yu's method

If you want ChatGPT, Claude, Codex, Grok, Muse or another assistant to share work,
start with one task and one record your agents can actually read. This guide gives
you a small workspace, a handoff exercise and a way to check the result. Use tools
you already have; a second subscription is not required for the first exercise.

| You need | Start here | Proof to keep |
|---|---|---|
| Understand the system | [Current company guide](https://dennisyu.com/how-agents-run-the-company/) | Task owner, permissions and acceptance criteria |
| Create your own workspace | [Starter files](templates/agent-workspace/README.md) | Your workspace location and source revision |
| Let another agent continue | Steps 3–5 below | Receiver read of the exact artifact revision |
| Install skills in a supported product | [Illustrated installation guide](https://localservicespotlight.com/install/) | Installed revision and fresh activation result |
| Turn a lesson into a repeatable method | [Learn → Do → Teach](docs/agent-setup/LEARN-DO-TEACH.md) | Corrected procedure, negative test and cold replay |

This public repository is the maintained source for reusable instructions and
skills. Dennis's operating repositories are private and are **not dependencies**
for your setup. Create your own private workspace for your team's decisions and
work. A public article may describe his implementation; it does not grant access
to his clients, tools, agents or credentials.

## 1. Give your assistant this request

```text
Use Dennis Yu's public agent setup guide:
https://github.com/dennisyu/local-service-spotlight-skills/blob/main/START-HERE.md
Read it and the linked starter README, then identify your actual read/write tools.
Use only an already authorized local workspace for the first practice task.
Record the source commit or UNKNOWN, outcome owner, acceptance test and limits.
Prepare the starter files without overwriting an existing team record.
Do not install, connect accounts, send, publish, spend, change access or schedule.
Run the practice and a fresh-session continuation where supported.
Report what you opened, what passed, what failed and what remains unverified.
If a required tool or read is unavailable, mark that step BLOCKED; do not invent it.
```

An assistant that can only read web pages can explain the setup and draft a
record. It has not created a workspace. A file-capable agent can do the local
exercise. A connected repository worker can later maintain the shared record,
within the owner's authority. Record the actual app, runtime and tested tools;
the model name alone establishes none of these capabilities.

## 2. Prepare a workspace you control

Read the [starter README](templates/agent-workspace/README.md). If you have an
existing team record, integrate the missing fields there instead of making a
second board. For a new local practice workspace, a shell-capable agent can run:

```bash
git clone https://github.com/dennisyu/local-service-spotlight-skills.git
cd local-service-spotlight-skills
git rev-parse HEAD
python3 scripts/check_agent_setup.py
# mkdir fails safely if this destination already exists; choose a new destination.
mkdir ../my-agent-workspace && cp -R templates/agent-workspace/. ../my-agent-workspace/
python3 scripts/check_agent_setup.py --workspace ../my-agent-workspace
```

Keep the printed source revision. If the checkout has local changes, record the
base commit **and** hashes of the actual instructions used; do not attribute
uncommitted instructions to that commit. If cloning is unavailable, use the public file
links or a supported repository download. Reading instructions is not installing
a skill. Never paste tokens into a prompt or put secrets in a repository.

After the local exercise, the owner may authorize a **private** GitHub repository
or another supported shared record. Use least-privilege access for each actual
agent account; verify a harmless read before writes. A public fork is a source
copy, not a safe home for private operational records.

## 3. Claim one bounded practice task

Use task ID `practice-001`: write `practice-result.md` explaining the difference
between a source update and a tested installation. Cite [ACCEPTANCE.md](ACCEPTANCE.md).
Allowed actions are reading this public source and writing local practice files.
Acceptance: correctly distinguish Available, Installed, Enabled and Tested, and
identify one thing the exercise does not prove.

Copy [task-template.md](templates/agent-workspace/task-template.md) to your task's
record. In your workspace, add the task to `status/JOBS.md`, then claim it in
`status/NOW.md` with one outcome owner, worker, reviewer, write scope, source
revision and recheck time. Keep the same task ID on both views. They describe one
task; they are not two independent queues.

Before shared work, read the current authoritative record. Submit the claim
through that record's serialized or version-checked write route and read it back
before acting. If a competing claim or revision conflict appears, stop and
coordinate. Markdown tables alone are not an atomic lock. An expired recheck
time is a reason to reconcile ownership, not permission to repeat an external action.

## 4. Make the result and hand it off

Write the practice result. Record its exact location and revision; for a local
file, use a content hash (for example `sha256sum practice-result.md`). Keep the
task ID, owner, scope, source and next action in a dated `agent-notes/` record.

Open a **fresh session** and provide only the record location, task ID and
revision. The receiver must open the record and result, restate the owner,
allowed actions and next step, and acknowledge the same artifact revision.
If it cannot read them, status is `BLOCKED` or `NOT_DELIVERED`. A save receipt
does not prove another agent received anything.

A fresh chat in the same app or a worker started without inherited conversation
can test cold-context retrieval. Label which one you used. A fresh worker does
not establish a separate product session, account, model or autonomous wake-up.

An existing supported agent channel or an observed pickup schedule can carry the
handoff. A repository file does not wake up another app. Do not claim autonomous
delivery when a person attached a record for this one test. Label it a manual
fresh-session continuation; it remains useful evidence of record portability.

## 5. Check the result independently

The reviewer opens the acceptance criteria, original source and actual result,
rather than grading the builder's summary. Record PASS, FAIL or BLOCKED with
evidence. A separate session tests context portability; a different reviewer
tests the result. Sessions on the same model are not cross-model consensus.

Start with the [pending receipt](templates/agent-workspace/handoff.pending.json).
Leave `receiver_ack` null and review NOT_CHECKED until those observations exist.
Use the [complete format example](templates/agent-workspace/handoff.example.json) and
[field contract](templates/agent-workspace/handoff.schema.json) for a receipt:

```bash
python3 scripts/check_agent_setup.py --receipt path/to/your-receipt.json --require-verified
```

The example is a **synthetic format fixture**, not a completed real handoff.
Replace its fields with evidence from your exercise. The checker tests recorded
consistency, exact artifact/revision matches and separate reviewer identity. It
cannot authenticate the evidence, make remote reads, enforce a lock or prove
runtime behavior. Keep private receipts in your own workspace.

## 6. Learn, do, teach; then propagate the correction

**Learn** the current method and success criteria. **Practice** safely with public
or synthetic inputs. **Do** authorized real work and verify its actual result.
**Teach** the observed correction with enough detail that another operator can
reproduce it without the original chat. Practice is not proof of client results.

CCS means **Content · Checklist · Software**. Explain the lesson with evidence,
turn it into explicit checks, and automate the parts that can honestly be tested.
In this repository, capture a checkable rule in `standards/` first, then derive
the teaching and checks from it. This implementation order does not rename CCS.
See the [worked learning loop](docs/agent-setup/LEARN-DO-TEACH.md) and
[propagation method](HOW-KNOWLEDGE-PROPAGATES.md).
The [October 29 cold-test record](reviews/2026-10-29-portable-agent-setup.md)
shows what was exercised, what it exposed and what remains unverified.

Use these distinct adoption states: **Available → Delivered → Installed → Enabled
→ Tested → Scheduled → Observed**. They are evidence fields, not a requirement
that every task must be scheduled. Record business outcomes separately. Updating
GitHub proves source availability after merge; it does not update every account.

## 7. Move a passing practice into your own private team repository

When the owner's request authorizes repository setup, a capable agent should
complete this step through its existing supported GitHub connection. Confirm
the intended owner/account and repository name, search for an existing team
record, and preserve it if one exists. Do not silently create a public repository
or copy Dennis's operational records.

The owner can give that agent this bounded setup request:

```text
Create or integrate my agent workspace at <approved-owner>/<approved-repository>.
Use the public starter's tested revision and my existing GitHub connection.
Confirm the account and existing repository before changing anything.
For a new repository, require PRIVATE visibility and initialize only the reviewed
starter/task files, never credentials or the whole source-download directory.
Read back visibility, default-branch commit and required files after the write.
Have each participating agent use its own supported authorized access to perform
a harmless read of the same probe and record the exact revision it read.
Set one claim authority, one outcome owner and the actual handoff route.
Test claim conflict handling and one bounded handoff before unattended work.
Do not invite people, grant new privileges, send, publish, spend or schedule.
Keep unsupported steps BLOCKED with the exact missing capability.
```

Finish only when the intended private repository and both agents' reads are
verified. Then repeat the practice against that shared record and preserve the
receiver's actual acknowledgment. A local pass does not prove shared access,
claim serialization or unattended pickup. Add a schedule only when needed and
authorized, then verify its first firing separately using [ACCEPTANCE.md](ACCEPTANCE.md).

## Problems and recovery

| Observation | Next action |
|---|---|
| Public GitHub source cannot be read | Record URL/error; use a supported public download or reader. Do not guess content. |
| A private Dennis repository returns 404 | Continue with this public starter and your own workspace. Do not request his private data. |
| No file/repository tools | Mark creation BLOCKED; keep a clearly labeled draft and route to an authorized capable worker. |
| Another worker owns the task | Read its latest receipt and reconcile on the same task. |
| Receiver cannot read the artifact | Repair an authorized shared route; keep NOT_DELIVERED until its actual read. |
| A check fails | Preserve failure, repair the defect and rerun the same acceptance test. |
| Installed skill is stale | Use the product's supported update route and fresh-session activation test; preserve rollback. |

For source defects, search existing GitHub issues before opening one, include the
public source revision and reproducible failure, and omit private records. Use
[CONTRIBUTING.md](CONTRIBUTING.md) for fixes. Machine-readable navigation is in
[agent-setup.json](agent-setup.json) and [llms.txt](llms.txt); neither installs
anything or guarantees search-engine indexing.
