---
{
  "title": "Pick the cheapest capable fleet lane",
  "severity": "error",
  "captured": "2026-10-01",
  "captured_from": "Account owner, fleet-lane agreement, 2026-10-01",
  "applies_to": [
    "agent-behaviour"
  ]
}
---

## Pick the cheapest capable fleet lane

- **Route each job to the cheapest fleet lane that can actually do it.** This
  picks the *seat* that should run the job. `model-judgment` still picks the
  *model tier* inside that seat. They are two ladders, not one. There is no
  separate skill-router skill; this file is the fleet router.

| Lane | Takes | Hard stop |
|---|---|---|
| **Local Qwen** (Trenton on Dennis's Macs) | Offline bulk text: transcript triage, Content Factory first drafts, MAA and GCT first passes, bulk rewrites | No browser, no logins, no publishing. Runs only while a Mac is awake |
| **Muse / Happy** | Anything in Google (Photos, Docs, Gmail) or Meta, plus email and correspondence. Most headroom | Prefer a cheaper lane when one can actually finish the job |
| **Kimi and Codex crons** | Cheap recurring scheduled jobs | Do not keep a job here after a fitter lane is live |
| **Grok desks** (Grok Bot agents such as Q, Tanner, Austin, Trenton, Alex) | Judgment calls, publishing, and routing only | Keep turns short. Grok overages can cost Dennis up to $1K a week |

- **Rule of thumb.** Needs a browser or a login → not Qwen. Needs Google or
  Meta → Muse/Happy. Recurring and mechanical → a Kimi or Codex cron. A
  decision or a public post → a Grok desk. When more than one lane could do
  it, take the cheapest one that still fits.
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
browser.

No regex can honestly decide which lane a job needs. Enforce this by reading
the lane table before you schedule or claim a job, and by naming the live
lane in the job's receipt.
