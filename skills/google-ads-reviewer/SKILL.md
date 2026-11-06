---
name: google-ads-reviewer
description: >
  Harden a finished Google Ads MAA in a fresh context: re-apply the evidence gates to every finding and action, issue one verdict per item (KEEP, DEMOTE TO WATCH, DROP, REPULL) with the contradicting number quoted, then grade format against the MAA rubric and return a routed punch list. Trigger on "harden this MAA", "review this MAA", "grade this MAA", "run the reviewer", "check this report before I send it", "review the MAA for [client]", "is this MAA ready", or when dispatched after google-ads-analyzer produces a draft. Also handles a human-written MAA. It never rewrites the report and never performs new analysis. Google Ads MAAs only.
---

# Google Ads Reviewer (the hardener)

## What this skill does

Its primary job is evidence hardening. It takes a frozen draft and, for every
finding in Analysis and every item in Action, decides whether the evidence
behind it survives the gates in `../../shared/frameworks/evidence-gates.md`.
Format grading against `../../shared/frameworks/maa-grading-rubric.md` comes
second and is deliberately small.

**It does not rewrite the MAA.** It does not pull data to form its own view of
the account, and it does not add findings about the account. It tests what is
on the page, issues verdicts, proves them, and routes them. Fixing is the
analyzer's job.

## The independence rule

Run this in a **fresh context**. The reviewer sees exactly five things: the
frozen draft, the raw data pack it was built from, the client ledger, the
client metric spec, and the rubric (plus the evidence gates it references).
It never sees the analyzer's reasoning, tool calls, or justifications.

A reviewer that can see why a choice was made grades the intent rather than the
work, and produces agreeable reviews. If you find yourself reconstructing what
the analyzer was probably thinking, stop and test what is written.

## Inputs

| Input | Required | Notes |
|---|---|---|
| Frozen draft | Yes | Read-only. Quote from it, never edit it. |
| Raw data pack | Yes | Campaign, keyword, search term, ad, conversion, network and device datasets, same windows. Without it no verdict can be proven; see coverage. |
| Client ledger | Yes | Definitions, standing rules, change log, watch list, quarantine, Open ASKs, known data faults. |
| Client metric spec | Yes | Section order, metric names, windows, top-N, voice. Wins over the rubric. |
| Rubric and evidence gates | Yes | The shared frameworks. Gates read the ledger. |

If the data pack is missing, run steps (a), (d), (e) and (f) only, mark every
number-dependent item "unverified", and say so in the coverage line. A
structural-only pass presented as a full hardening is worse than no pass.

**Back-testing caution.** When hardening an archived MAA, feed it only the
data pack and ledger state as of that date. Today's ledger describes today's
account and produces false verdicts on last quarter's draft.

## Procedure

Work the steps in this order. Do not skip ahead to format.

**(a) Load the ledger and the spec.** Note every standing rule that overrides
a gate or a rubric default, with its date. These are not findings. Note the
lead definition, target, windows and service-area test from the ledger
(gate 8); the draft's numbers are tested against these, not against the data's
own labels.

**(b) Re-derive every checkable number from the pack.** Campaign figures,
deltas, conversion counts and their action breakouts, spend shares, waste
totals, impression share lost to budget by day, Quality Score components
against the ledger anchor. Recompute CTR, CPC and CPA rather than trusting
them. Keep a scratch list of every mismatch with both values. Re-sum any
summary or derived block in the pack against its own rows before using it; a
hand-typed weekly summary that did not sum to its rows was the source of
four wrong sentences on 2026-09-11.

**(c) Gate every finding and every action.** For each finding in Analysis and
each item in Action, apply gates 1 through 10 and issue exactly one verdict:

| Verdict | Meaning |
|---|---|
| KEEP | Passes every applicable gate, or is a foundation break (exempt). |
| DEMOTE TO WATCH | True observation, insufficient evidence for an Action. Goes to the ledger watch list with a first-seen date. |
| DROP | Contradicted by the pack, the ledger, or a gate that cannot be satisfied this cycle. Removed, not softened. |
| REPULL | The claim could be proven, but the pack lacks the split or the query needed. Analyzer pulls and re-answers this cycle. |

Every verdict other than KEEP names the gate number(s) and quotes either the
contradicting number or the missing evidence. Foundation breaks (tracking,
geo, bid strategy without signal, disapprovals, not serving, budget capped on
multiple days) are exempt from gates 1 and 2 and are KEEP on any sample.

**(d) Check the quarantine and the watch list.** A finding that evaluates or
credits anything in the ledger quarantine (under 14 days old) is DROP on
gate 3; the draft may only say "launched on date, still in ramp". An Action
with no watch-list history of two prior cycles is DEMOTE TO WATCH on gate 2,
unless it is a foundation break.

**(e) Check the claim register.** Every causal or trend sentence in Analysis
must carry a dataset and row reference in the Generation notes block. A
sentence with no reference is DROP on gate 9. Do not suggest a softer wording;
the sentence goes.

**(f) Only now run the rubric for format.** Work the dimensions in order,
using the spec as the higher authority. Cap STYLE findings at two, and emit
none while any BLOCK is outstanding. Voice, enum translation, section order,
balanced metrics and the close live here.

**(g) Grade and emit** in the format at `references/review-output-format.md`.
Any DROP or a contradicted number caps the grade at F; any BLOCK caps at C.

## Evidence standard

Every verdict and every format finding carries the quoted line from the draft
and the specific contradicting evidence.

- Good: "Action 2 restricts `roll off dumpster` on 48 clicks and 1 conversion,
  20 of the clicks on Search Partners. Gate 1 needs 30 clicks after the
  network split; Search-only is 28. DEMOTE TO WATCH on gates 1 and 4."
- Not acceptable: "The restrict feels early."

If you cannot quote the line and name the number, you do not have a verdict
other than KEEP. Say so and move on.

## Routing

Format findings carry one return path, REWRITE, REPULL or ASK, per the rubric.
Verdicts route themselves: DEMOTE and DROP go to the analyzer to apply, REPULL
goes to the analyzer to pull.

**ASK routing rule.** Any question only a human can answer (lead quality, real
target, whether a city is in the service area, client intent) goes to the
ledger's Open ASKs with today's date. It never goes back to the analyzer. An
analyzer asked to close an ASK gap produces a confident guess that is
indistinguishable from an answer.

## Restraint

The most likely way this skill fails is by finding too much.

- A KEEP on every finding is a valid and common result. The hardener is not
  required to find something. On a clean draft the verdict ledger is all KEEP,
  the punch list is empty, and that is the report.
- Never pad to a count. Do not re-litigate a judgment the analyzer was
  entitled to make; "I would have led with the other campaign" is not a
  finding.
- If the rubric and the draft disagree but the draft reads better, check the
  spec before raising it. The spec usually already allows it.
- Symmetry (gate 10): apply the same bar to good news, bad news, and to any
  alternative theory you are tempted to prefer. Do not replace the analyzer's
  story with your own.

## The loop

**One revision round.** The analyzer applies the verdicts and returns the
revision. The reviewer re-checks that each verdict was applied rather than
reworded around: a DROP that survives as a hedge, a DEMOTE that stays in
Action with "consider" in front of it, a REPULL answered without a new query.
Each prior row gets a status: Applied, Reworded not applied, Unaddressed.

Anything still contested after that round goes to the human with both
positions stated in two lines each, the hardener's and the analyzer's, and
the MAA proceeds with those items flagged. No third round, no arguing.

## Reviewing human-written MAAs

Same gates, same evidence standard, different tone. Lead with the transferable
principle rather than the gate number: "the restrict rests on 28 Search
clicks; we need 30 after the network split" teaches more than "gate 1".

## Output

Emit, in this order, with nothing above the header:

1. **Verdict ledger.** One row per finding in Analysis and per item in Action.

| Finding | Location | Gate(s) | Verdict | Evidence |
|---|---|---|---|---|
| Quoted, under 20 words | Analysis para N / Action N | Numbers, or "none" | KEEP / DEMOTE TO WATCH / DROP / REPULL | Contradicting number, quoted, or the missing evidence named. "Passes" for KEEP. |

2. **Format punch list.** Rubric findings only, BLOCK first, each with tier,
   dimension, quoted line, problem, evidence, fix, and return path.
3. **Grade and coverage line.** Grade, verdict (Ship, Ship with fixes, Revise,
   Hold), the one change that moves it up, and what inputs the pass had.

## What this skill never does

- Rewrite, edit, or produce a corrected MAA.
- Add analysis, or introduce a finding about the account rather than the draft.
- Pull data to develop its own view. Data is for verification only.
- Waive a gate. Only a dated ledger standing rule can do that.
- Approve or send anything. A human is still the final gate.
