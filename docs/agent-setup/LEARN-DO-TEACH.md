# Learn, Do, Teach in practice

Use this method when you want someone else's agent to repeat work you have
learned to do. Start with one useful task, publish enough detail to reproduce it,
and let a fresh operator reveal what the explanation missed.

For agent setup, use [START-HERE.md](../../START-HERE.md). This page explains how
to improve the instructions through evidence, practice and independent replay.

| LDT step | Operator action | CCS artifact |
|---|---|---|
| Learn | Read the current method, sources, scope and known failures | Content that explains why and when |
| Practice | Rehearse with safe public or synthetic inputs | Labeled exercise and checklist result |
| Do | Complete authorized real work and inspect the result where it landed | Real artifact and verification receipt |
| Teach | Turn the successful run and corrections into a repeatable method | Canonical guide, checklist and linked software checks |
| Replay and improve | A fresh operator tries it; correct gaps and repeat | New revision, regression evidence and scoped adoption receipt |

Learn → Do → Teach is the learning sequence. CCS means Content, Checklists,
Software. Practice is part of learning, not a replacement for real work.

## 1. Learn before changing anything

Read the current [LDT standard](../../standards/learn-do-teach.md), the relevant
skill and its linked sources. Record their exact revisions. State the task's
purpose, inputs, permitted effects, output destination, acceptance criteria and
stop conditions. Search the existing task record before claiming a new job.

Distinguish the permission to read public instructions from permission to change
a system. A public recipe, installed skill or connected account does not grant
new privileges or permission to publish somebody else's information.

## 2. Practice safely and label it

Use public inputs or synthetic fixtures before a first production run. Include a
clean case and a failure the method should catch. Keep the exercise separate from
real client records and do not create external side effects merely to test a rule.

A practice receipt records what was tested, which version, the input origin,
actual result, mistakes and corrections. It says **practice**, not "client
delivery," "production verified" or "mastery." A test in one runtime says
nothing about another runtime's access or behavior.

## 3. Do the real task within authority

Execute the approved work from the current source and original criteria. Keep a
stable task/run identifier and one outcome owner. Preserve a previous accepted
revision or an appropriate recovery path before changes that need one.

Open the actual output at the intended destination. Check completeness, accuracy,
access and unintended effects. Record failures and what was not checked. An
independent reviewer retrieves the original criteria and destination rather than
grading only the builder's summary. Do not claim a successful business outcome
from a tool's successful return or an observed scheduled firing.

## 4. Teach the successful method

Update the existing canonical guide instead of starting a competing procedure.
Include enough for a stranger to work without the author's private context:

- purpose, prerequisites, input format and source revisions;
- approved access, permitted effects and stop conditions;
- ordered steps, decisions, commands or tool operations where useful;
- an actual permitted example with before/after evidence;
- failures encountered, root cause, correction and recovery;
- acceptance checks, known limits and links to the relevant source standard;
- output location, verification method, update route and accountable owner.

Convert reusable lessons into the existing standard or a new scoped one. Use
[the capture procedure](../../HOW-KNOWLEDGE-PROPAGATES.md#capture-and-release-a-rule)
and [contribution route](../../CONTRIBUTING.md). Publish only approved public
examples. Private source evidence can remain private while its safe general
lesson is taught publicly.

Software checks should cover what they can honestly inspect. Preserve a clean
fixture, a known bad fixture and, where useful, a separate reviewer-selected
challenge. Keep semantic judgment, rights and runtime access as explicit review
items when software does not verify them.

## 5. Replay with a fresh operator

Give another person or agent the published method, pinned inputs, permissions
and acceptance criteria. Do not supply the author's diagnosis or fill in missing
steps during the run. A new context helps expose dependence on hidden knowledge.

Record the tested revision, operator/runtime, outputs, failures, author help and
reviewer's findings. If the operator needs an unstated step, amend the guide and
repeat the affected part. Pass only for the tested scope. A synthetic replay can
validate that exercise; a real-work competence claim needs authorized real-task
evidence. Use [acceptance section H](../../ACCEPTANCE.md#h-cold-operator-learn-do-teach-replay).

One agent's agreement with another is not all-model consensus. Name the actual
reviewers, what they inspected, their dissent and the resulting changes.

## Worked source correction: automatic updates

This guide accompanies a real documentation correction. In the repository's
[October 29 source baseline](https://github.com/dennisyu/local-service-spotlight-skills/blob/0095d089d8fa9a27177b4aae35dcb5c110e1da0e/HOW-KNOWLEDGE-PROPAGATES.md),
the propagation explanation promised updates to "every person who ever installed"
and said drift was impossible. Its own acceptance procedure required a canary
account update and fresh activation test.

| Step | What the correction does | What remains to prove |
|---|---|---|
| Learn | Compare the propagation explanation with acceptance sections B and F | Actual outside-account state is not inferred |
| Do | Correct the source explanation and source standards; preserve the historical incident | Merge, release and destination readback need their own receipts |
| Teach | Explain the difference between source sync, account update and runtime behavior | A cold operator must still apply the distinction to a new case |
| Check | Run the source sync/validation and inspect the diff against the original claim | A text comparison does not certify semantics or adoption |

The files in this change are source artifacts. Their presence in a candidate
checkout does not prove release, installation or an unattended update. Use the
pull request and exact merged revision for a publication receipt, then named
account evidence for adoption. See [ACCEPTANCE.md](../../ACCEPTANCE.md).

## Worked software rehearsal: an unmuted video

This is a **synthetic local practice exercise**, not a live website audit. It uses
the existing [media standard](../../standards/nothing-plays-uninvited.md) and a
separate markup variant to show that its static checker can reject a failure.
It does not play media or contact a website.

From a checkout of the tested source, run:

```bash
python3 - <<'PY'
from scripts.fleet_check import run_check
from scripts.standards_lib import load_standards

rule = next(r for r in load_standards() if r.slug == "nothing-plays-uninvited")
check = next(c for c in rule.checks if c.id == "video-autoplay-unmuted")
bad = "<video class='hero' autoplay='autoplay' playsinline></video>"
clean = "<video class='hero' muted autoplay='autoplay' playsinline></video>"
assert run_check(check, "https://example.test/", bad, rule.severity)
assert not run_check(check, "https://example.test/", clean, rule.severity)
print("PASS: synthetic unmuted case rejected; muted case clears selected static check")
PY
```

The expected message is `PASS: synthetic unmuted case rejected; muted case
clears selected static check`. A changed or broken checker should make this exercise fail, rather
than produce a success receipt. If imports or source loading fail, record the
setup error; do not call the behavior tested.

Then run `python3 scripts/fleet_check.py --self-test` for all declared samples.
The broader unit tests include a pattern that matches nothing and a pattern that
cries wolf; both must be caught. Inspect browser behavior separately before a
runtime claim: markup alone cannot show whether a script later starts sound.

## Keep source and adoption evidence separate

Record Available, Delivered, Installed, Enabled, Tested, Scheduled and Observed
only when their specific evidence exists. Some routes have no package-install
step; a one-off task has no schedule. An observed failure proves a firing, not
success. [The propagation guide](../../HOW-KNOWLEDGE-PROPAGATES.md#source-account-and-job-states-are-different)
contains the state definitions; [the acceptance checks](../../ACCEPTANCE.md)
define the receipts.

When a replay exposes an error, preserve it, fix the canonical source, rerun the
affected tests and update the receiving runtime through its supported route.
Record whether the correction was loaded and exercised. That closes the loop for
the tested operator; broader adoption remains a separate claim.
