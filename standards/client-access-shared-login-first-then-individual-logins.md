---
{
  "title": "Client access: shared login first, then individual logins",
  "severity": "error",
  "captured": "2026-11-25",
  "captured_from": "Dennis Yu, Claude Code session, 2026-11-25: stated while unblocking a client's Netlify site fix that had waited on one person's access. The how-to steps are the agents' reading, revised after an independent review. Client and former teammate not named in this public copy.",
  "applies_to": [
    "agent-behaviour"
  ]
}
---

## Client access: shared login first, then individual logins

Marker: `CLIENT-ACCESS-SHARED-FIRST-2026-11-25`.

**Outside Local Service Spotlight, never ask a client to add access@localservicespotlight.com
or Dennis.** Wherever this rule says access@ or Dennis, read your own team's shared login and
your own owner. If your team has no shared login yet, setting one up is your owner's call.

- **When we need access to a client's platform, always start with our main team login,
  access@localservicespotlight.com,** so anyone on the team can get in. That goes for
  Netlify, GitHub, Shopify, GoDaddy, WordPress and so on.
- **For clients that matter more and where we do more work, also ask for dedicated
  individual logins:** one for each person working the account and one for each AI agent.
- **Why:** a client's Netlify-hosted site sat unfixed because access depended on one person.
  Only the client's account owner could invite people. A teammate had arranged Netlify access
  for access@ in late October 2026, but nobody recorded or tested it. When that teammate was no
  longer available, nobody could confirm it worked. Shared plus individual logins mean the work
  never hangs on one teammate.

The steps below are how agents carry this out, offered for Dennis's correction. Where a step
cites another rule, that rule already says the same.

- **Use what already works, then ask once for the rest.** Test the access we already have
  first (`reuse-existing-authorized-access`). Then send one ask: access@ first, then each person
  and agent by name, each with the smallest role that covers all the work we do on that
  account, not just today's task. Send it to whoever can grant it; often only the client's
  account owner can invite.
- **While the ask is out, keep going.** Do every part of the work that does not need the new
  access, and put a date on the ask (`an-unanswered-ask-never-stops-the-work`).
- **If the platform charges per seat, say that access@ plus Dennis is enough** and leave out
  the other individual logins.
- **Ask for invitations, not passwords** (`client-access-checklist`). The client adds access@
  and each person or agent as their own user. The team shares only access@ and keeps its
  password only in the team's approved secret store. Never ask for a client's own password or
  pass around anyone's personal login. Where a platform's own rules call for a partner link or
  one login per real person, as ad and social accounts often do, follow them.
- **Record every grant in the private access register** (the access inventory): platform,
  identity, role, who granted it and the date. No passwords or keys go in it.
- **Verify each grant with one harmless read before calling it working**
  (`reuse-existing-authorized-access`). Whoever holds that identity checks it through an
  already authorized route, for example by opening the site list or a deploy log. Log the date
  and result beside the grant. An invite sent is not an invite accepted, and an accepted invite
  is not a working login.
- **Ask only for identities that already exist.** A new mailbox, or a new platform account
  needed to accept an invite, is Dennis's call. If an agent has no identity yet, ask for the
  rest and record the gap.
- **This rule sets what the ask says, not who sends it.** Sending, and anything that needs a
  yes first, follows `agents-own-it`, `agents-draft-humans-send` and
  `human-review-when-it-matters`.

No machine check covers this rule, on purpose. It governs what an agent asks a client for and
what the team records privately, and neither appears in published HTML. A regex over messages
could find the address but not whether the right logins were asked for, granted and tested.
The dated read test beside each grant in the access register is the evidence.
