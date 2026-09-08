# Tripwires — the Recurring-run escalation gate

**Tags:** #framework #ga4 #recurring #safety

The guardrail that replaces the human-review gate on an owner-triggered weekly run. A Recurring Re-Run has no person in the loop that week, so it must **self-detect when it's out of its depth and route the week back to the team** rather than deliver something wrong to the owner. Evaluate every tripwire in Phase 3.5, after Data Clarity, against the client's `locked-config-ga4.md`.

Two outcomes only:
- **Clean** — no tripwire fired → deliver the owner-facing report.
- **Escalate** — one or more fired → finish the analysis, write the internal draft, and emit the banner: **"This week needs Local Service Spotlight review before it reaches the owner: <reason(s)>."** Do not format it as owner-delivered. Do not auto-post.

## Escalation tripwires (data-trust breaks — hold for team)

| # | Tripwire | Condition | Why it escalates |
|---|---|---|---|
| T1 | **New candidate lead event** | Q1 shows a case/list-building-patterned event not in locked-config `lead_events`. | Could be a real new lead type OR a tracking change — either way the locked classification is stale; a human must classify and re-lock. |
| T2 | **Property switch / ghost** | Pre-flight liveness fails on the locked `live_id`, or a new same-brand live sibling appears, or the live id ≠ locked id. | The property identity changed; every number could be from the wrong dataset. |
| T3 | **Clarity regression** | Data Clarity grade is worse than `baselines.data_clarity_baseline` (e.g. baseline Hazy → now Opaque). | The data got less trustworthy than the last good week; the report's confidence assumptions no longer hold. |
| T4 | **Reconciliation break** | Reconstructed case-leads vs GA4 keyEvents gap > 1.5× where locked-config expected a clean match. | Lead counting itself is unreliable this week. |
| T5 | **New contamination cluster** | A spam / foreign-datacenter city cluster appears in the current window that wasn't in the baseline (Singapore/Ashburn-type surge). | Junk traffic is distorting the picture; a human should confirm the screen before the owner sees channel/city reads. |
| T6 | **Fix regression** | A `fix_status: APPLIED:<date>` integration issue reappears (e.g. the booking-tool referral overwrite returns after exclusion was saved). | A previously-solved problem broke; needs a person, not a report line. |

## Surface-don't-escalate (business signals — put in the owner report, prominently)

These are NOT data-trust breaks; the owner should see them, framed plainly:

- **Large lead swing.** Headline leads move beyond ±35% vs `baselines.headline_leads_prior`. Lead **first** with it, explain where it concentrated (loss/gain decomposition), and — if there's a plausible client-side cause — ask in Start-here. (RDR −35% is a surface item, not an escalation.)
- **A channel collapsing or spiking** with real (engaged) traffic. Report it in the channels W&O.
- **A known-but-unfixed integration issue** already in locked-config (e.g. booking-tool overwrite still live): report the fix-progress line per recurring-run voice; escalate only if it *regressed* (T6) or crossed a new severity (e.g. C8 share jumps past 25%).

## Notes

- **Near-threshold (±20%) on an escalation tripwire → escalate.** For owner-facing safety, resolve ambiguity toward team review, not toward silent delivery. (This is the opposite default from a first-run watch item — the cost of a wrong owner-facing report is higher than a false escalation.)
- Every fired tripwire and every surfaced swing is written to the locked-config `run_history` for the week.
- If the run escalates, next week defaults to **First-Run mode** until the team clears it (a fired tripwire means the config may need re-locking).
