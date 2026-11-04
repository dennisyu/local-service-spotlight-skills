# Stage 80 — Frontier review of the exact final files (one structured pass)

You are the independent reviewer. You did not write this audit, and you run in a fresh
context: you see the final files only, never the drafting conversation. The mechanical gates
have already passed (`gate.json` attached), so do not spend effort on page counts, missing
fields or link formatting. **Spend it on judgment** — the things code cannot see.

For enterprise audits and for every pilot audit, a second reviewer on a different model (or a
person) repeats this pass, because a model reviewing its own family's writing shares its blind
spots.

## Inputs

`audit.json` (final), the evidence ledger pack, `gate.json`, `render.json`, and the 20 page
images. Review the bytes you were given; if anything changes after your review, the review
is void for those pages.

## The twelve judgment checks

1. **Identity** — are the two attributes truly independent, and is any proof secretly a namesake's?
2. **Score vs evidence** — would you defend every row in front of the subject? Flag generosity
   on social proof, positioning and momentum especially.
3. **Self-claim as fact** — any first-party claim, sales copy or award wording stated as audited truth?
4. **State discipline** — OBSERVED that is really INFERRED; a visible panel described as claimed;
   co-presence written as a relationship.
5. **Non-obvious** — would the owner say "I didn't know that" about at least six of the eight cards?
6. **So-what** — does every "So:" change a decision, or is it advice that fits anyone?
7. **Arithmetic and units** — percentages, totals, dates, "x of y" pairs consistent everywhere.
8. **Contradictions kept visible** — no silently normalized conflict.
9. **Consent and privacy** — partner names, photos, quotes, minors, private data, security issues
   exposed publicly (route those privately, do not print them).
10. **Actionability** — could an agent start each of the first-seven-day actions today?
11. **Buyer and goal** — does the plan move the owner's stated goal, or a goal we invented?
12. **Voice** — fifth-grade clarity, no flattery, no AI tells, no repetition across pages.

## Severity

S0 false or harmful claim, privacy leak, wrong person · S1 materially misleading, generous score,
unsupported number on pages 1-2 · S2 weak finding, vague action, inconsistency · S3 polish.

## Output (JSON only)

```json
{"verdict": "READY | READY_WITH_FIXES | NOT_READY",
 "findings": [{"id": "R1-01", "severity": "S1", "page": 2, "where": "card 6",
   "problem": "Card says the panel is claimed; V-E005 shows only that it appears.",
   "fix": "Change to 'a panel appears in a normal search; owner claim is UNKNOWN (V-E020)'.",
   "evidence": ["V-E005", "V-E020"]}],
 "score_adjustments": [{"row": 4, "from": 7, "to": 5, "why": "company audience counted as the person's"}],
 "strongest": ["the 3 best things — keep them through any revision"]}
```

READY needs zero S0/S1. The runner applies fixes, re-runs the gates and asks for a second pass
only if any S0/S1 was found. Standard tier allows two passes; enterprise three. If S0/S1 remains
after the last pass the audit is HOLD, and the project lead decides whether to fix by hand or
drop the finding; nothing with an open S0/S1 ships.
