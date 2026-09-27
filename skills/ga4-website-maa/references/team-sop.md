# Team SOP — First-Run → enable Recurring; owner GA4 connection

**Tags:** #framework #ga4 #ops #hybrid

The operating procedure for the hybrid model: the team validates the first run and locks the config; then the owner (or a schedule) can re-run the weekly pulse, protected by the tripwire gate. This is the human process around the skill — follow it before flipping any client to owner-facing Recurring mode.

## A. Owner GA4 connection pre-flight (before the first run)

The agent reads GA4 through the Google Analytics MCP. Before First-Run, confirm the data path exists:

1. **Access.** The owner grants at least Viewer on the GA4 property to the account the MCP runs under (or connects their own GA4 in the app). No access → the run cannot start; this is a connection step, not an analysis failure — say so plainly.
2. **Right property.** Run pre-flight liveness (P1) and confirm the live property vs any ghost/duplicate (P2). Record the live id and known ghosts in the locked-config. Do not proceed on a ghost.
3. **Distinguish "not connected" from "not implemented."** No live property anywhere accessible → is GA4 (a) not shared with us, or (b) never installed? (a) → ask for access; (b) → propose setup as step one. Never fabricate an analysis. (SKILL Phase 0.)

## B. First-Run (team-operated, gated)

1. Run the full skill in First-Run mode against the live property.
2. **Lock the classification with the owner/CRM in the loop:** confirm which events are real case leads (verify `form_submit`/booking counts against a known tally where possible), the service area, and the `out_of_area_leads` intent (spam vs franchise/other). Seed `locked-config-ga4.md`.
3. **Verify, don't assume, integration fixes.** For each known issue (e.g. booking-tool referral overwrite), record `fix_status` by *checking*, not by memory — re-verify by date that any claimed fix actually landed. (RDR: the exclusion was recommended earlier and is still `NOT_APPLIED` as of 2026-07-22.)
4. **Human review** the client report before it reaches the owner. This gate stays for every First-Run.
5. Set `baselines` from this validated period; set `mode_ready: recurring` only once the report passes external grade ≥ A− and the config is complete.

## C. Enable Recurring (owner-facing)

- Flip `mode_ready: recurring`. Schedule or hand the owner the weekly trigger.
- Every Recurring run passes the **tripwire gate** (`tripwires.md`) before delivery. A clean week reaches the owner directly; a tripped week is held with the review banner and routed to the team.
- **A fired tripwire drops the client back to First-Run** next cycle until the team clears it and (if needed) re-locks the config.

## D. Cadence & review

- Recurring cadence: weekly (or the owner's chosen interval), windows fixed at 28d vs prior 28d.
- **Spot-check quota:** even in Recurring mode, the team externally grades one owner-delivered report per client per month to catch silent drift (self-grades run ~a full letter high — First-Run RDR self A− vs external B+). Log the grade of record.
- Any system-level gap (would change how *every* client is analyzed) → Decisions-Log + flag the skill; client-specific facts → the locked-config, not the log.

## E. What the owner should never have to do

Choose a property, read a grade, interpret a raw chart, or judge whether a tracking anomaly is real. If a week needs any of those judgments, that's exactly what the tripwire gate catches and routes to the team. The owner's job is to read a plain-English pulse and answer the occasional Start-here question.
