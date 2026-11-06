# Agent receipt convention

Every piece of agent-authored text that lands on an INTERNAL surface (team-only
Basecamp threads, agent notes, email to the team) carries two things: an opening line that says an agent
produced it, and a closing receipt line in the house format. A reader should
never have to infer that a post came from an automation.

## Opening line (first line of the post)

```
Automated {what} by the {agent name} agent. {Client}, {YYYY-MM-DD}.
```

Examples:
- `Automated daily Google Ads health check by the google-ads-daily-check agent. Target Painting, 2026-09-08.`
- `Automated weekly Google Ads MAA draft by the google-ads-analyzer agent, hardened by google-ads-reviewer. American AF Dumpsters, 2026-09-11.`

## Receipt line (last line of the post)

```
Sent by {agent name} / {operator name}'s desk
Agent receipt: {channel} — {agent name} [{model}] · action: {verb} · human review: {status}
```

This matches the format the CTO's own agents use on email ("Sent by Grok Bot / Q" then "Agent receipt: Gmail — Q [Grok] · action: sent · human review: reviewed by Dennis"). `{channel}` is where the post lands: Basecamp, Gmail, Slack.

- `{channel}`: Basecamp, Gmail, Slack, as applicable.
- `{operator name}`: the human whose account the agent runs under and who is
  accountable for it (for this suite, the agency lead named in the roster or
  ledger).
- `{agent name}`: the skill name, e.g. `google-ads-daily-check`.
- `{model}`: the model that ran it, e.g. `Claude`.
- `action`: one of `reported` (read-only findings, nothing changed),
  `drafted` (a deliverable for human review), `staged` (a script or change
  prepared but not run), `changed` (an account change was executed; only ever
  after human approval).
- `human review`: one of `reviewed by {name} before posting`,
  `posted by {name}, not separately reviewed`,
  `authorized, not separately reviewed` (for scheduled runs where the
  operator has pre-authorized posting; not used by this suite today).

Example:

```
Sent by google-ads-daily-check / Daniel's desk
Agent receipt: Basecamp — google-ads-daily-check [Claude] · action: reported · human review: reviewed by Daniel before posting
```

## Rules

- The opening line and receipt line are part of the block the agent writes;
  they are not added by hand later. A paste-ready block without both is
  incomplete.
- When the operator edits the block before posting, the receipt line stays
  and `human review` reads `reviewed by {name} before posting`.
- **Audience rule (changed 2026-10-02 in this tree; matches `clients/_shared/agent-receipt.md`
  of 2026-09-30 and Dennis's direction relayed by Daniel on 2026-10-02):** client- and
  partner-facing posts (client-visible Basecamp threads, client email, public posts)
  carry NONE of the opening line, the "Sent by" line, the receipt line or a Verified
  line. AI is assumed. Internal posts (team-only threads, agent notes, email to the
  team) keep the opening line and the receipt. For client-facing work, record the
  receipt, the read-back and the posted recording ID in the client ledger instead.
- The receipt line never claims a review that did not happen.
