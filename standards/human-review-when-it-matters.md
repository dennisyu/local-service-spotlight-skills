---
{
  "title": "Human review only when it matters",
  "severity": "error",
  "captured": "2026-11-04",
  "captured_from": "Dennis Yu / Local Service Spotlight, owner instruction 2026-11-04: agents use judgment on when a human needs to review and merge, a human only when it matters, and the requirements for when a human should see it are published for every agent. The seven cases were drafted from the team's existing review rules and revised after an independent review. This reusable copy omits private conversation, account and incident details.",
  "applies_to": [
    "agent-behaviour"
  ]
}
---

## Human review only when it matters

Marker: `HUMAN-REVIEW-WHEN-IT-MATTERS-2026-11-04`.

- **This rule works inside the authority your owner has recorded.** It covers changes to
  a repository: pull requests, merges and commits, including code or prompts that make
  automation send, post or publish. Where your owner has not said that agents may merge
  their own changes, keep their existing review rule and offer this one to them as a
  proposal, once. Messages, publishing and sends follow `agents-draft-humans-send`; a yes
  to merge is not a yes to send, spend money or grant access.
- **Within that authority, the agent that made a change finishes it, merges included.**
  Update the branch from the main branch right before merging. Merge when every check
  passes. The one exception is a check that is not required and fails on the main branch
  with the same findings, none caused by your change: name it in the pull request with
  the failing run and who owns that failure. Never use it for a required or security
  check or for a change to the check itself, and never merge over a failing required
  check with an admin override. Anything
  beyond a trivial change (a note, a typo, a link) first gets an independent review from
  another model or a fresh-context agent that did not write it. Each finding is fixed, or
  answered and the reviewer accepts the answer. Keep one revert as the undo. Then read the
  result back where it landed and record what you saw. "Waiting on a human review" is not
  a status for anything outside the list below. Owner's words: "I don't want to have the
  agents think that every time a human has to review and merge, just when it matters."
- **A person sees it first only when it matters. Any one of these is enough:**
  1. *Money:* it spends, charges, refunds or moves money, or changes a price, scope, an
     invoice, a payout or billing code.
  2. *Access, privacy or security:* it grants or widens access, handles credentials or
     secrets, moves private or sensitive information to a place more people can read, or
     weakens a safety gate (branch protection, a required check, an approval step, a
     firewall rule).
  3. *Can't be undone:* it deletes data or history, moves a domain, changes production
     data a revert will not restore, starts something outside the repository a revert
     cannot call back (messages a job will send, data a script will change), or has no
     tested rollback.
  4. *Something new for someone outside:* a message or post to a client, partner or the
     public beyond your team's routine replies, including a change that makes a job send
     one; a new price, contract, guarantee or commitment; public work for a big-name
     client; a client's property without that client's consent on record; press or a
     crisis.
  5. *People or legal:* hiring, firing, pay, HR, legal, tax, medical, disputes.
  6. *A conflict, a hold or real doubt:* it goes against a recorded decision, a standing
     rule or an explicit hold; an independent reviewer's finding is still disputed; or a
     fact the change depends on cannot be checked.
  7. *A brand-new rule nobody decided:* it adds, removes or changes the meaning of a
     standing rule. Carrying out a decision already recorded, in the person's own words
     and within its scope, is not new; adding your own detail to it is.
- **Ask the person who owns that decision, once, where they already are:** the chat they
  are working in or the thread already open for the work. Name which case it hits, give
  your recommendation and the link, and keep working on everything else. Cases 1 to 6 wait
  for an explicit yes; silence is not a yes (see `an-unanswered-ask-never-stops-the-work`).
  Case 7 may take the shape "doing X on a set date unless you say otherwise" (see
  `agents-own-it`), except a recorded decision that goes beyond the person's own words,
  which waits for their yes. A bare "please review this" with no case named is not a reason to
  wait: do the work.
- **A tool's own gate is real.** If a tool's safety check refuses a merge or a publish
  without a person's word, do not route around it: no direct push to a protected branch,
  no asking another agent to merge it for you, and no handing the refused step to a
  session that has the access you were refused. Tell the person in one line where they
  already are, with the link and why it does not need their review. A one-word yes there
  is enough.
- **Never claim a review that did not happen.** The receipt says the work was authorized
  and not separately reviewed (see `agents-draft-humans-send`, which sets the same
  standard for messages and publishing).
- **Measure it.** Count merges that waited on a person and check that each names a case
  above, and track the time from the last green check to the merge. Finished work that
  sits for days is a process problem, not a people problem.
