---
{
  "title": "Pick the cheapest capable fleet lane",
  "severity": "error",
  "captured": "2026-10-01",
  "captured_from": "Account owner, PR 60 review, 2026-10-01: cost order is local Qwen (free), then Muse, then everything else; Muse Spark for high-volume work; Astra/Dot for hard reasoning, with Dot experimental and never the sole owner of critical work; keep the existing agent split until there are many Dots",
  "applies_to": [
    "agent-behaviour"
  ]
}
---

## Pick the cheapest capable fleet lane

- **Route each job to the cheapest fleet lane that can actually do it.** Cost
  order: local Qwen (free) first, then Muse, then everything else. This rule
  picks the *seat* that runs the job. `model-judgment` still picks the *model
  tier* inside that seat. They are two ladders, not one. There is no separate
  skill-router skill; this file is the fleet router.
- **Muse (Meta Muse Spark) is the default for high-volume work that does not
  need frontier intelligence.** Inbox, calendar, bookings, errands,
  watch-and-ping monitoring, volume monitoring, and Google/Meta chores go
  here. It is heavily subsidized: the Maximum plan is about 3 billion Muse
  tokens **per week**, not per month. A Muse token is Meta's own meter — do
  not equate it to an OpenAI token. Do not buy more Muse capacity; fit the
  volume work inside the weekly allowance. Treat Muse as non-frontier: do not
  put disputes, must-be-right research, or code/docs that matter on it.

| Lane | Takes | Hard stop |
|---|---|---|
| **Local Qwen** (Trenton on Dennis's Macs) | Offline bulk text only: transcript triage, Content Factory first drafts, MAA and GCT first passes, bulk rewrites. Cheapest seat — free | No browser, no logins, no publishing. Runs only while a Mac is awake |
| **Muse (Meta Muse Spark) / Happy** | High-volume work that does not need frontier intelligence: inbox, calendar, bookings, errands, Google (Photos, Docs, Gmail), Meta, watch-and-ping monitoring, volume monitoring | Hard reasoning, disputes, research that has to be right, or code/docs that matter. Do not buy more Muse capacity |
| **Astra** (Dot, and specific ChatGPT tasks) | Hard reasoning, disputes, research that has to be right, and code/docs that matter. Fewer tokens than Muse, so spend them on work that has to be right | Dot is experimental (about a day old on 2026-10-01). Spot-check its routine output. Never the sole owner of anything critical: a human or a separate ChatGPT task started fresh reviews Dot's output before anyone acts on it (`qa-from-a-different-context-window`). This holds until this file says otherwise |
| **Kimi and Codex crons** | Cheap recurring scheduled jobs that are already live here, or that Muse cannot own | Do not keep a job here after a fitter lane is live. Do not default new high-volume work here |
| **Grok desks** (Grok Bot agents such as Q, Tanner, Austin, Trenton, Alex) | Judgment calls, publishing, and routing only | Keep turns short. Not the high-volume default |
| **Any other seat** (Cursor, Claude, and the rest) | Work already assigned to it, and new work that only that seat can reach | Sits in "everything else" in the cost order. Do not move Muse- or Qwen-capable volume onto it |

Qwen is cheaper than Muse, yet Muse is the *default* for volume because most
volume needs a browser or a login, which Qwen cannot do. Tie-break: a job
that is offline bulk text with no browser or login, and that can wait for a
Mac to be awake, goes to Qwen first. A job that needs a browser or a login,
or that must fire on a schedule whether or not a Mac is awake, goes to Muse.
A fallback model inside one seat is fine — `model-judgment` requires one for
unattended jobs — but a second lane for the same job is not.

Lanes are seats, not desk names. Trenton appears twice because that desk has
both a local-Qwen seat on the Macs and a Grok Bot seat; route by the seat the
job needs.

- **Until there are many Dots, keep dividing work across the existing
  agents.** "Many Dots" means the models absorb the harness so humans do not
  have to split tasks and project-manage them. Until that is true, do not
  collapse the fleet onto Dot or Astra. Use the split in this table.
- **Rule of thumb.** Offline bulk text with no browser or login that can wait
  for a Mac → Qwen first (free). Other high-volume work that does not need
  frontier intelligence → Muse. Hard reasoning, a dispute, research that has
  to be right, or code/docs that matter → Astra, spot-checked while Dot is
  new and never Dot alone on anything critical. Recurring mechanical work
  already on a Kimi or Codex cron stays there until a Muse task is live. A
  decision or a public post that needs a Grok desk stays on that desk, in a
  short turn. Every other seat keeps the work already assigned to it.
- **Never run the same job on two lanes.** When a job moves, the new lane
  must be live before the old one is turned off.
- This rule picks the seat. It does not grant permission to send, publish,
  spend, or delete. Those still need the existing approval rails. Do not put
  passwords, tokens, or account inventories in this file or in any public
  copy of it.

### Worked example — weekly Google Photos person-albums

On 2026-10-01 the weekly Google Photos person-albums job was on an enabled
Kimi cron. It stays there until Happy creates the Monday 9:17 AM PT Muse task
from the Happy/Muse runbook. Then the Kimi cron is turned off so the job never
runs twice. It is not a Qwen/Trenton job: it needs a Google Photos login and a
browser. It is not an Astra/Dot job: it is high-volume album work, not hard
reasoning.

No regex can honestly decide which lane a job needs. Enforce this by reading
the lane table before you schedule or claim a job, and by naming the live
lane in the job's receipt.
