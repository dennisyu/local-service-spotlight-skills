# Review Output Format

The reviewer emits exactly this, nothing above the header. The verdict ledger
comes first because hardening is the primary job; format follows; grade closes.

---

## Template

```
# MAA Hardening - {Client} - {report date}

## Verdict ledger

| Finding | Location | Gate(s) | Verdict | Evidence |
|---|---|---|---|---|
| {quoted, under 20 words} | Analysis para N / Action N | {numbers or none} | {KEEP / DEMOTE TO WATCH / DROP / REPULL} | {contradicting number quoted, missing evidence named, or "Passes"} |

Open ASKs added to ledger: {list, or "none"}

## Format punch list

### 1. {Short title} - {BLOCK|WARN|STYLE} - {dimension} - {REWRITE|REPULL|ASK}

> {verbatim quoted line from the MAA}

**Problem:** {what is wrong}
**Evidence:** {the contradicting data, the spec clause, or the rubric rule}
**Fix:** {what specifically to change}

## Grade

**Grade:** {A|B|C|F}
**Verdict:** {Ship | Ship with fixes | Revise | Hold}
**To move up one grade:** {the single most important change}
**Coverage:** {Full - draft, data pack, ledger, spec | Partial - no data pack, numbers unverified | ...}
```

---

## Field rules

**Verdict ledger.** One row for every finding in Analysis and every item in
Action, in document order. No row may be skipped; a clean item gets KEEP and
"Passes". Every non-KEEP row names at least one gate number and quotes the
number or names the missing evidence. Foundation breaks are KEEP with the
gate column reading "exempt".

**Open ASKs.** Human-only questions surfaced during hardening are written to
the ledger's Open ASKs with today's date and listed here. They never route to
the analyzer.

**Format punch list.** Ordered by tier, BLOCK first, then by impact. Numbered
so the analyzer and the log can reference them. STYLE capped at two, and none
while any BLOCK is open. Quoted line is verbatim, as a blockquote; for an
omission, quote the surrounding line and say what is missing. Exactly one
return path per finding: REWRITE if fixable from data in hand, REPULL if it
needs more data, ASK if it needs a person.

**Grade.** Per the rubric. Any DROP, a contradicted number, or internal labels
in client copy caps at F. Any BLOCK caps at C. If the grade is A, write
"already at the bar" rather than inventing a change.

**Verdict.**

| Verdict | When |
|---|---|
| Ship | All KEEP and no findings, or STYLE only. |
| Ship with fixes | DEMOTE or REPULL rows, or WARN findings, none blocking the narrative. |
| Revise | Any DROP or any BLOCK. Returns to the analyzer for the one revision round. |
| Hold | An item that cannot close without a human answer (ASK). |

**Coverage.** Never omit. If the data pack was missing, say numbers were
unverified so nobody reads a structural pass as a full hardening.

---

## On the re-check (after the one revision round)

Add this block above the verdict ledger:

```
## Prior round

| # | Prior verdict or finding | Status |
|---|---|---|
| 1 | {short title, verdict} | Applied / Reworded, not applied / Unaddressed / Applied, new issue introduced |
```

"Reworded, not applied" is the important one. Anything still contested after
this round goes to the human as two lines per side, hardener then analyzer,
and the MAA proceeds with those items flagged.

---

## Worked example

```
# MAA Hardening - Ridgeline Painting - 2026-08-28

## Verdict ledger

| Finding | Location | Gate(s) | Verdict | Evidence |
|---|---|---|---|---|
| "Restrict `house painting near me` to phrase match after 48 clicks and one lead" | Action 2 | 1, 4 | DEMOTE TO WATCH | Pack: 48 clicks, 20 on Search Partners; Search-only 28 clicks, 1 conv. Below 30-click floor after split. Add to watch list, first seen 2026-08-28. |
| "Last week's negatives did not land; the exclusion terms are not in the account" | Analysis para 3 | 6 | DROP | Negatives query returned exactly 200 rows against a 190-item list. No absence claim on a capped set; query the 190 terms directly. |
| "Brand campaign shows zero impressions for six days, pointing to weak brand demand" | Analysis para 4 | 3 | DROP | Ledger quarantine: brand campaign launched 2026-08-23 during site rebuild, exits 2026-09-06. Draft may say "launched 8/23, still in ramp". |
| "Exterior leads rose to 11 at $212 CPL, under the $250 target, on 214 clicks" | Analysis para 1 | none | KEEP | Passes. Pack: 11 counted calls per ledger definition, $2,332 spend, 214 clicks. |
| "Mobile CPL doubled on Interior, pointing to a landing page speed problem" | Analysis para 5 | 4 | REPULL | Pack has no device split for Interior. Pull device by campaign for 7D and 30D before any verdict. |

Open ASKs added to ledger: none

## Format punch list

### 1. Enum name in client copy - BLOCK - voice and tone - REWRITE

> Interior is running on MAXIMIZE_CONVERSIONS with no target set.

**Problem:** API enum in client-facing copy.
**Evidence:** Rubric, dimension 8: every enum is translated.
**Fix:** "Interior is running on Maximize Conversions with no target set."

## Grade

**Grade:** F
**Verdict:** Revise
**To move up one grade:** apply the two DROPs and the DEMOTE; the remaining draft is a B.
**Coverage:** Full - draft, 8/28 data pack with network split, ledger dated 8/27, metric spec.
```
