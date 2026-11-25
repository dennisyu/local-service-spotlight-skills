---
{
  "title": "Decide where follow-up work runs; don't make the person pick",
  "severity": "error",
  "captured": "2026-11-25",
  "captured_from": "Dennis Yu, Claude Code session, 2026-11-25",
  "applies_to": [
    "agent-behaviour"
  ]
}
---

## Decide where follow-up work runs; don't make the person pick

Marker: `START-OR-HERE-2026-11-25`.

Words used here:

- A **session** is a separate chat with its own history in the sidebar. Outside the Claude
  app, read "session" as any separate agent run.
- **Start** (some cards say **New session**) hands the job to a new session with a brief (a
  short note that explains the job). That session then owns it.
- **Do it here** keeps the work in the current chat.
- Work **fits this chat** when it builds on what was done, found or decided here.

The rule:

1. **If the person asked for work that fits this chat, just do it.** Don't ask them to pick
   where it runs. If they said where it runs, do that; their ask is the OK.
2. **For a new, separate task, or work nobody asked for, get the person's OK first.** That's
   what the session card is for. Say your pick and why in one line, right next to it.
3. **Pick Do it here when a new helper would need most of this chat explained.** Example: the
   fix for a bug you just tracked down here.
4. **Pick Start when the work ends in its own result somewhere else:** a pull request, a
   document or another project.
5. **Pick Do it here when it's a few minutes of work.** Otherwise pick Start, and lean that way
   when this chat is long.
6. **Never ask "which do you prefer?" when you already know the answer.**

When rules 3 to 5 disagree, rule 3 wins. A few minutes' work stays here even if it ends in a
pull request. A long chat tips close calls to Start.

- **Why:** the card is a permission step. The app needs the person's OK before a new session
  starts work they didn't ask for, so an agent can't skip the card. Stating the pick turns it
  into one click instead of a question. This rule came from a card that showed both buttons
  with no recommendation. Owner's words: "...and then agents can just decide. If you already
  know what the right answer is, why would you even make me choose?"
- **Example:** a client-access rule was set in a long working session. The agent then proposed
  adding it to the shared skills repo. Start was right: the brief stood on its own, the work
  ended in its own pull request in another repo, and the working chat was long. The line next
  to the card could read: "My pick: Start. The brief stands on its own, the work ends in its
  own pull request in another repo, and this chat is long."

How this fits other rules:

- `be-proactive-see-it-through`: rule 2's OK is the app's gate on starting a new session.
  Reversible work you'd do here needs no card: do it and report it.
- `agents-own-it` bans the approval cards and "should I?" asks that agents invent, but keeps a
  product's own approval step: stop and report it in one line. The session card is that kind
  of step, so put your pick on it. Without a card, ask first only where your platform requires
  an OK. Never use Start to move a refused or gated step to another session.
- `agents-draft-humans-send`: the card only decides whether and where a separate task or
  unrequested work starts. It is not a review of the work. Sending, publishing and other
  consequential actions still follow that rule.
- `ask-blocking-questions-up-front`: rule 6 is its other half. Ask only what you can't decide,
  once, and still name your pick.
- `qa-from-a-different-context-window`: independent review is part of the work, not a
  follow-up. Run it in a fresh context (a helper agent is enough), with no card, whatever
  rules 1 to 5 say.

No machine check covers this rule. Whether work fits this chat, whether a helper would need it
explained and whether you already know the answer are judgment calls, and no regex over
messages or pages can make them. The evidence is the one-line pick next to each card.
