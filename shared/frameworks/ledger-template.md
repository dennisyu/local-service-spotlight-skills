# Client Ledger Template

One file per client, read in full by the analyzer before any data pull and
appended by it at the end of every cycle. It replaces the memory a human
operator otherwise supplies by hand: definitions, standing rules, what changed
and when, what is on watch, what is quarantined, how the client view is
rendered, and which data sources are known to lie.

Target length 250 to 400 lines. Compact, dated, factual. Anything unconfirmed
carries `(verify)`. Older continuity files (a narrative log, a status wiki)
may still exist; the ledger is the compressed layer the drafter depends on,
and it wins on conflict unless a more recent dated entry exists elsewhere.

Location: `{OUTPUT_DIR}/{Client}/compiled/ledger.md` (BlitzBase-style
vaults) or `{OUTPUT_DIR}/{Client}/{Client}_Ledger.md` (simple mode).

---

```
# {Client} - Ledger
> Purpose line. Last updated YYYY-MM-DD.

## 1. Identity and access
CID, MCC, contacts and roles, comms channel, site platform, who owns the
website, data paths (MCP, email fallback subject string, UI reports), other
platforms present but out of scope (LSA, Meta).

## 2. Definitions
What counts as a lead and which conversion actions; counted vs raw calls;
target CPL and its source and the period it is judged on; primary campaigns
with IDs, bid strategy and budget; top-N rule; windows and cadence; delta
conventions; QS anchor keyword and its component reads; networks and devices
that matter; the service-area test (in / out / undecided, with sources).

## 3. Standing rules
One line each, dated, with who set it. House style specific to this client,
things never to surface to the client, "don't touch" items, evidence bars the
client has agreed to.

## 4. Change log
| Date | Change | Who | Source |
Every account change: launches, pauses, re-enables, negatives rounds with
round number, bid and budget moves and reversals, landing page repoints, site
rebuilds, scripts run. "Before engagement" rows for inherited state. This
replaces change_event, which is unreliable.

## 5. Watch list
| Item | First seen | Cycles observed | Current read | Promote-or-drop |
Every observation that is not yet an Action. Gate 2 reads this table.

## 6. Open ASKs
Questions only a human can answer, with date raised and owner. The analyzer
adds to this list instead of asking in chat or guessing.

## 7. Recent-change quarantine
Everything changed in the last 14 days, with the date it exits. Gate 3 reads
this list. On a new client the whole account is quarantined for two cycles.

## 8. Render spec
Action count norm, "what's working" bullet norm, sections the client view
strips, plain-label substitutions, tone notes learned from the operator's
edits, filename conventions, chart target line, status-dot conventions.

## 9. Weekly log
| Date | Leads | CPL | 30D CPL | Actions shipped |
One line per cycle. Backfilled 13 weeks at onboarding. Counts in the row are
read off the report file at the moment of writing (Action count from the
Action list, not from memory). The row records file state at that moment; a
later render or post gets its own dated change-log row and the weekly row is
left as written. Two rows on 2026-09-11 under-counted Actions by one and two
because the count was recalled rather than read.

## 10. Known data faults
Per source: MCP quirks, capped queries, filters that hide rows, email export
timing and column swaps, UI-only fields, script paths that fail silently,
internal files known to be stale and which entry wins.
```

---

## Maintenance rules

- Append, never rewrite past lines. Corrections are new dated lines.
- Every cycle adds: one weekly log row, change-log rows for anything shipped,
  watch-list updates (cycles observed +1, promote or drop as due), new ASKs,
  new quarantine entries with exit dates, new faults.
- When the operator supplies a fact in chat during a run, the response is a
  ledger line, not just an edit to the draft.
- Prune quarantine entries after exit and watch items after drop by moving
  them to a dated "Closed" note at the bottom of the section, so the history
  stays but the live tables stay short.
