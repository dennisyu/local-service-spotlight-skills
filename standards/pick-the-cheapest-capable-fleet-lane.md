---
{
  "title": "Pick the cheapest capable fleet lane",
  "severity": "error",
  "captured": "2026-10-01",
  "captured_from": "Account owner, PR 60 review, 2026-10-01: Muse Spark for high-volume work; Astra/Dot for hard reasoning; keep the existing agent split until there are many Dots",
  "applies_to": [
    "agent-behaviour"
  ]
}
---

## Pick the cheapest capable fleet lane

- **Muse (Meta Muse Spark) is the default for high-volume work that does not
  need frontier intelligence.** Inbox, calendar, bookings, errands,
  watch-and-ping monitoring, volume monitoring, and Google/Meta chores go
  here. It is heavily subsidized: the Maximum plan is about 3 billion Muse
  tokens **per week**, not per month. A Muse token is Meta's own meter — do not equate it to an
  OpenAI token. Do not buy more Muse capacity; the seat is already
  over-provisioned. Reliability is mid on hard reasoning, so do not put
  disputes, must-be-right research, or code/docs that matter on Muse.
- **Route each job to the cheapest fleet lane that can actually do it.** This
  picks the *seat* that should run the job. `model-judgment` still picks the
  *model tier* inside that seat. They are two ladders, not one. There is no
  separate skill-router skill; this file is the fleet router.

| Lane | Takes | Hard stop |
|---|---|---|
| **Local Qwen** (Trenton on Dennis's Macs) | Offline bulk text only: transcript triage, Content Factory first drafts, MAA and GCT first passes, bulk rewrites. Cheapest seat — free | No browser, no logins, no publishing. Runs only while a Mac is awake |
| **Muse (Meta Muse Spark) / Happy** | High-volume work that does not need frontier intelligence: inbox, calendar, bookings, errands, Google (Photos, Docs, Gmail), Meta, watch-and-ping monitoring, volume monitoring | Hard reasoning, disputes, research that has to be right, or code/docs that matter. Do not buy more Muse capacity |
| **Astra** (Dot, and specific ChatGPT tasks) | Hard reasoning, disputes, research that has to be right, and code/docs that matter. Fewer tokens, higher hit rate | Dot is about a day old. Spot-check it. Never the sole owner of anything critical: a human or a separate ChatGPT task checks Dot's output before anyone acts on it |
| **Kimi and Codex crons** | Cheap recurring scheduled jobs that are already live here, or that Muse cannot own | Do not keep a job here after a fitter lane is live. Do not default new high-volume work here |
| **Grok desks** (Grok Bot agents such as Q, Tanner, Austin, Trenton, Alex) | Judgment calls, publishing, and routing only | Keep turns short. Not the high-volume default |
| **Any other seat** (Cursor, Claude, and the rest) | Work already assigned to it | Sits in "everything else" in the cost order. Do not move Muse- or Qwen-capable volume onto it |

Cost order: local Qwen (free, offline bulk text), then Muse, then everything
else. Muse is the *default* for volume because most volume needs a browser or
a login, which Qwen cannot do. When a job is offline bulk text with no browser
or login and a Mac is awake, Qwen goes first; otherwise Muse.

- **Until there are many Dots, keep dividing work across the existing
  agents.** "Many Dots" means the models absorb the harness so humans do not
  have to split tasks and project-manage them. Until that is true, do not
  collapse the fleet onto Dot or Astra. Use the split in this table.
- **Rule of thumb.** Offline bulk text with no browser or login → Qwen
  first (free). Other high-volume work with no frontier intelligence → Muse. Hard reasoning, a dispute,
  research that has to be right, or code/docs that matter → Astra, with a
  human spot-check while Dot is new. Recurring mechanical work already on a
  Kimi or Codex cron stays there until a Muse task is live. A decision or a
  public post that needs a Grok desk stays on that desk, in a short turn.
- **Never run the same job on two lanes.** When a job moves, the new lane
  must be live before the old one is turned off.
- This rule picks the seat. It does not grant permission to send, publish,
  spend, or delete. Those still need the existing approval rails. Do not put
  passwords, tokens, or account inventories in this file or in any public
  copy of it.

### Worked example — weekly Google Photos person-albums

The weekly Google Photos person-albums job stays on the existing enabled
Kimi cron until Happy creates the Monday 9:17 AM PT Muse task from the
Happy/Muse runbook. Then the Kimi cron is turned off so the job never runs
twice. It is not a Qwen/Trenton job: it needs a Google Photos login and a
browser. It is not an Astra/Dot job: it is high-volume album work, not hard
reasoning.

No regex can honestly decide which lane a job needs. Enforce this by reading
the lane table before you schedule or claim a job, and by naming the live
lane in the job's receipt.
