# Making the public agent setup reproducible

On October 29, 2026, Dennis Yu asked us to improve the route from “ask your AI or
Google for Dennis's agent instructions” to a setup another team can actually use.
Search already found useful articles. The main gap was a small, public starting
point that an outside agent could follow without Dennis's private context.

## What changed and why

| Finding | Correction | Acceptance evidence |
|---|---|---|
| GitHub opened with Claude packaging | Cross-assistant [START-HERE.md](../START-HERE.md), machine index and copyable workspace | Source/navigation checker and a cold local setup |
| Source updates were described as automatic fleet adoption | Corrected explanation and generated LDT/capture instructions | Source sync, marketplace validation and independent diff review |
| Teach lacked a reproducible next-operator test | [Worked LDT/CCS guide](../docs/agent-setup/LEARN-DO-TEACH.md), original criteria and cold replay | A second worker opened the pinned record, source and actual result |
| A copy example could run after failed directory creation | Guarded `mkdir ... && cp ...` | Existing sentinel remained unchanged; new destination initialized |
| Cold reader needed an explicit task and pending receipt | Added task template and null-ACK / NOT_CHECKED receipt | Pending receipt passes consistency, fails verified-completion gate |
| Reusable skills carried private incident/account detail and internal fleet assumptions | Replaced incident appendices with portable technical lessons, removed personnel details, and made routing rules capability based | Canonical-master edits, regeneration and independent public-safety review |

The baseline inspected was
[`0095d089d8fa9a27177b4aae35dcb5c110e1da0e`](https://github.com/dennisyu/local-service-spotlight-skills/tree/0095d089d8fa9a27177b4aae35dcb5c110e1da0e).
The source package version for this correction is **1.9.1**. Resolve the exact
release commit from GitHub or `git rev-parse HEAD`; the version number alone
does not establish what any account has installed.

## What the cold exercise actually did

A worker started without the author's conversation, read the public candidate
guide and acceptance method, copied the starter into a new local workspace,
claimed `practice-001`, and wrote an explanation of Available, Installed,
Enabled and Tested. It recorded the source base commit **and hashes of the actual
candidate instructions**, because the new files were not yet in the base commit.

Its first receipt stayed NOT_DELIVERED with review NOT_CHECKED. A separate worker,
also without inherited conversation, received only the task ID and pinned record
reference. It opened the record, verified all 15 pinned source-snapshot hashes,
opened the actual result, and compared it with the original acceptance criteria.
The result's SHA-256 was
`cb01d4db77416119d49f3aa234b681b785324a46c5fa55460ee8243f391e7280`.
The [actual practice result](../docs/agent-setup/examples/practice-result.md) is
preserved verbatim so readers can inspect those exact bytes. Its relative
`source-snapshot/` references describe the pinned local exercise inputs; the
maintained public criteria are in [ACCEPTANCE.md](../ACCEPTANCE.md).
The review passed at **2026-10-29 18:44 America/New_York**. The reviewer also
repaired a stale next-action paragraph in the local checkpoint and independently
introduced a stale acknowledgment fixture, which the checker rejected.

The first worker exposed the missing task/pending-receipt scaffolds and source
revision ambiguity. We corrected the guide and had another source reviewer
check those additions. This is the learning loop in a small, bounded case:
reproduce, find ambiguity, repair the source, test the correction, and teach it.

These were fresh-context workers in the same harness. This proves a **manual
local continuation exercise and separate-producer review**. It does not prove
different-model consensus, a separate product session, autonomous wake-up,
installation, account activation or a client/business outcome.

## Checks and deliberate failures

The reviewed candidate passed **228 Python tests**, including **23 new setup
validator tests**, plus source/navigation validation, generated-rule sync,
marketplace validation, scope congruency and declared fleet-check self-tests.
Reviewers also ran the documented synthetic unmuted-video exercise without
playing media. These are local/source checks; hosted product and browser
acceptance remain separate where relevant.

Reproduce the main checks from the source root:

```bash
python3 scripts/check_agent_setup.py
python3 scripts/check_agent_setup.py --receipt templates/agent-workspace/handoff.pending.json
python3 scripts/check_agent_setup.py --receipt templates/agent-workspace/handoff.pending.json --require-verified
```

The third command must **fail**: a pending receipt is not verified completion.
The complete synthetic format fixture can pass consistency without establishing
any real read; the tool prints that limit. Keep actual provider/local evidence
and independent review rather than treating editable receipt text as attestation.

The unit tests additionally reject wrong artifact revisions, absent acknowledgments,
self-review, missing evidence, timestamps without timezones, path escapes,
symlink escapes and missing source targets. Use the current
[acceptance procedure](../ACCEPTANCE.md) to test a receiving account and
unattended run before claiming broader adoption.

## Release and remaining work

Sync applicable accounts through their supported update route, record the exact
source/installed revision and ask a fresh session to exercise the changed method.
Retain the previous accepted revision for recovery. Reading this review is not
installation and creates no schedule.

Article updates on the associated public sites are a separate publishing result.
Prepared patches are not live publication. Confirm each ordinary public URL
after the established publisher releases its exact reviewed candidate. Broader
cross-product and cross-model review requires the actual receiver's response;
this source review does not invent that consensus.
