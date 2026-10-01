---
{
  "title": "Pick the cheapest capable fleet lane",
  "severity": "error",
  "captured": "2026-10-01",
  "captured_from": "Account owner, PR 60 review, 2026-10-01: Muse is the default main lane; add Dot on Astra as a watch lane",
  "applies_to": [
    "agent-behaviour"
  ]
}
---

## Pick the cheapest capable fleet lane

- **Default to Muse.** It is the primary agent because it is the most
  token-efficient seat: about $80/mo premium versus about $200 for Max-tier
  models, and its roughly 3 billion token allowance goes orders of magnitude
  further than the other seats. Send a job off Muse only when another lane is
  the only fit, or when local Qwen can finish free offline bulk text.
- **Route each job to the cheapest fleet lane that can actually do it.** This
  picks the *seat* that should run the job. `model-judgment` still picks the
  *model tier* inside that seat. They are two ladders, not one. There is no
  separate skill-router skill; this file is the fleet router.

| Lane | Takes | Hard stop |
|---|---|---|
| **Local Qwen** (Trenton on Dennis's Macs) | Offline bulk text only: transcript triage, Content Factory first drafts, MAA and GCT first passes, bulk rewrites. Cheapest seat — free | No browser, no logins, no publishing. Runs only while a Mac is awake |
| **Muse / Happy** | Default main lane. Anything in Google (Photos, Docs, Gmail) or Meta, plus email, correspondence, and any job another lane is not required for. Most headroom | Leave Muse only for free offline Qwen work, or for a job only another lane can do |
| **Kimi and Codex crons** | Cheap recurring scheduled jobs that are already live here, or that Muse cannot own | Do not keep a job here after a fitter lane is live. Do not default new work here |
| **Grok desks** (Grok Bot agents such as Q, Tanner, Austin, Trenton, Alex) | Judgment calls, publishing, and routing only | Keep turns short. Not the default. Other seats burn their allowance and spill into extra usage, which has cost up to $1,000 a week per agent |
| **Dot on Astra** | Monitoring and watch work. Stronger and more proactive at watching than the other agents | Early, known bugs. Human spot-checks required. Never the sole owner of anything critical |

Cost order: local Qwen (free, offline only), then Muse, then everything else.

- **Rule of thumb.** Start on Muse. Offline bulk text with no browser or login
  may move to Qwen. Recurring mechanical work already on a Kimi or Codex cron
  stays there until a Muse task is live. A decision or a public post that
  needs a Grok desk stays on that desk, in a short turn. Watch-only work may
  sit on Dot with a human spot-check, never as the only owner.
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
browser. It is not a Dot job: it is production work, not a watch.

No regex can honestly decide which lane a job needs. Enforce this by reading
the lane table before you schedule or claim a job, and by naming the live
lane in the job's receipt.
