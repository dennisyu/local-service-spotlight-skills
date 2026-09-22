# Tripwires — the Recurring-run escalation gate

Evaluate in Phase 3.5 against `locked-config-gbp.md`. Clean → deliver. Any fired → finish the analysis, write the internal draft, emit the banner **"This week needs Local Service Spotlight review before it reaches the owner: <reasons>"**, and set next week to First-Run.

## Escalation tripwires (data-trust breaks)

| # | Tripwire | Condition |
|---|---|---|
| T1 | Location missing or renamed | A locked `location_id` is absent from `gbp_list_locations`, or its title changed |
| T2 | Verification lost | `place_id` was non-null at lock time and is null now, or `openInfo.status` changed away from OPEN |
| T3 | Clarity regression | Clarity worse than `baselines.clarity_baseline` |
| T4 | Duplicate appeared | A new roster row shares this location's `place_id` |
| T5 | Profile edited | H14 fires on category, phone, address, or website (hours changes surface, they do not escalate) |
| T6 | Tool failure | Any Standard Pull tool returned an error after two retries; the report would be built on a partial pull |
| T7 | Zero-impression window | impressions_total = 0 for the full current period where the baseline was non-zero |

## Surface, don't escalate (business signals, shown to the owner plainly)

- Primary action swing beyond ±35% vs `baselines.primary_prior_period`: lead with it, decomposed per Phase 2.6.
- New 1–2 star review without a reply (H10): first opportunity in the report.
- Review velocity stalled (H11).
- Keyword mix shift (a new non-brand term entering the top 5).
- Single-day spike (H15): shown to the owner as a with/without comparison and a check, never as growth.
- Profile advertises a service the client does not take (surfaced by reading the description and service items against the locked `services_not_offered` list): the start-here item until fixed.

Near-threshold (±20%) on an escalation tripwire → escalate. Every fired tripwire and surfaced swing is written to `run_history`.
