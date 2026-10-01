---
{
  "title": "Content Factory MAA closes the loop",
  "severity": "error",
  "captured": "2026-10-01",
  "captured_from": "Account owner, Content Factory fleet orchestration brief, 2026-10-01",
  "applies_to": [
    "agent-behaviour"
  ]
}
---

## Content Factory MAA closes the loop

- **The factory is not done when content ships.** After Promote, run Perform /
  MAA — Metrics, then Analysis, then Action. The Action names what gets
  produced next. Content for its own sake is a failed run.
- **Measure business impact first:** revenue, profit, and clicks. Diagnostic
  metrics sit under those. See `weekly-brand-maa` and
  `report-business-impact-not-volume`.
- **Do not invent fleet seats or capabilities.** Use only the named lanes and
  desks in `skills/content-factory/references/fleet-orchestration.md`. Seat
  choice follows the cheapest capable lane
  (`standards/pick-the-cheapest-capable-fleet-lane.md` on PR #60 when merged).
- **Muse on Spark takes volume. Astra takes thinking.** Muse (Spark) does
  high-volume, non-frontier work: Google/Meta errands, inbox, calendar,
  bookings, watch-and-ping, and volume monitoring. Astra (Dot, plus specific
  ChatGPT tasks) takes hard research, strategy and judgment drafts,
  definitive-article reasoning, MAA analysis that has to be right, and
  code/docs that matter. Dot is experimental and one day old — spot-check it;
  it is never the sole owner of anything critical. Until there are more Dots,
  the named desks still divide the work.
- **Nothing public or paid without Dennis.** Stage by default. Claude Fleet is
  the single poster to client Basecamp threads. Grok desks prepare drafts and
  hand them off through a GitHub issue.

The locked line stays Plumbing (before) → Produce → Process → Post → Promote →
Perform / MAA (after). Do not rename those stations. The full agency map,
hierarchy, worked examples, and X-ray generator live in the content-factory
reference, not in this short rule.

No regex can honestly certify a handoff or a business-impact Action. Enforce
this by reading the map before you claim a job, and by writing an X-ray when
you need a checkable snapshot.
