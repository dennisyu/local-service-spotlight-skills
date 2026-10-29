---
{
  "title": "Pick the cheapest capable fleet lane",
  "severity": "error",
  "captured": "2026-10-01",
  "captured_from": "Dennis Yu / Local Service Spotlight public standard: Pick the cheapest capable fleet lane. Original capture date is retained in captured. Public-safety clarification authorized by the owner on 2026-10-29; this reusable copy omits private conversation, personnel, account and incident details.",
  "applies_to": [
    "agent-behaviour"
  ]
}
---

## Pick the cheapest capable fleet lane

- **Route each job to the cheapest authorized lane that can actually do it.**
  Compare the available runtimes' capabilities, cost, allowance, availability,
  data-handling limits and required review. Lower-cost local text processing
  may suit offline bulk work; an authorized hosted runtime may suit work that
  needs a browser, connector or unattended availability. Verify those facts in
  the actual account rather than assuming a product name establishes them.
- **Choose the execution seat and model tier separately.** This rule picks the
  runtime that owns the job. `model-judgment` picks an appropriate model tier
  inside that runtime. A cheaper model without the required tools or reliability
  is not a capable lane. Include retry and review costs in the comparison.
- **Reserve stronger reasoning and independent review for demanding work.**
  Disputes, consequential research and consequential code or documentation need
  an appropriately capable worker. Experimental output must not be the sole
  basis for a critical action; a qualified person or separate fresh-context
  reviewer checks the original evidence and actual result first.

| Lane | Takes | Hard stop |
|---|---|---|
| **Offline text lane** | Authorized transcript triage, first drafts, preliminary analyses and bulk rewrites that need no external tools | No browser, login or publication unless separately supported and authorized. Confirm device availability before relying on it |
| **Hosted volume lane** | Bounded repetitive work with tested tools, access and sufficient allowance | Do not route consequential reasoning here merely because it is cheap. Verify unattended availability rather than inferring it from hosting |
| **Reasoning and review lane** | Hard reasoning, disputes, consequential research, code and documentation | Preserve independent review and specialist requirements. A model name alone does not establish competence |
| **Existing recurring lane** | A recurring job whose current owner, schedule and result have actually been observed | Retain one owner while testing a replacement; an instruction or saved schedule alone does not prove a successful firing |
| **Action or publishing lane** | Work requiring a specific authorized connector, account, destination or approval route | Stay within recorded authority. Access to one service or account does not establish access to another |
| **Specialized lane** | Work only a particular approved runtime can reach or perform | Record the capability that justifies the cost; do not move work solely because another product is available |

These are capability categories, not claims about any installed fleet. Record
the actual runtime and tested capability in the team's private job record.
One agent name may cover multiple execution environments; route by the environment
the task needs. Product prices, quotas and capabilities need current verification
for the specific plan and account. Token meters from different providers are not
automatically comparable. This rule does not authorize another subscription.

- **Keep one outcome owner and one active execution lane per job.** A fallback
  model within that lane can handle an approved failure path. It must not create
  a second independent owner or repeat an external action whose result is uncertain.
- **Migrate through a controlled cutover.** Test the replacement in a paused,
  dry-run or otherwise isolated state that cannot duplicate production effects.
  Reconcile pending runs and uncertain writes, pause the old trigger, transfer
  ownership through the authoritative task record, then enable the replacement.
  Verify its actual result and retain the previous configuration for rollback.
  If a safe cutover is unavailable, retain the current owner and record the blocker.
- **Instructions do not grant authority.** Sending, publishing, spending,
  installing, changing access and deleting require the owner's existing authority
  and applicable approval rails. Keep passwords, tokens, account inventories and
  private schedules out of this rule and its public copies.

### Synthetic example — recurring media indexing

This is a fictional routing exercise, not an account or schedule receipt. A
recurring media-indexing job needs an authorized browser session and availability
at its scheduled time. An offline text runner without those capabilities is
unsuitable even if its marginal model cost is lower. A tested hosted volume lane
may fit; a stronger reasoning lane is unnecessary unless the task's decisions
require it. Check actual access and allowance, then use the controlled cutover
above if changing an existing owner. No account connection or schedule is created
by this example.

No regex can honestly decide which lane a job needs. The owner and reviewer apply
the capability table to the actual task, and the receipt names the tested runtime,
permitted effects, cost evidence or UNKNOWN, result and remaining limitations.
