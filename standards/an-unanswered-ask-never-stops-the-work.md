---
{
  "title": "An unanswered ask never stops the work",
  "severity": "error",
  "captured": "2026-09-04",
  "captured_from": "Dennis Yu / Local Service Spotlight public standard: An unanswered ask never stops the work. Original capture date is retained in captured. Public-safety clarification authorized by the owner on 2026-10-29; this reusable copy omits private conversation, personnel, account and incident details.",
  "applies_to": [
    "agent-behaviour"
  ]
}
---

## An unanswered ask never stops the work

- **Silence is not a blocker, it is a trigger.** When someone does not reply, the work
  continues on the rescue path you chose before you sent the ask. "Waiting on them" is
  never a status an agent reports twice.
- **Try to need them less before you try to reach them harder.** In order: do it yourself;
  route around; engineer the dependency so it cannot block again; only then ask. Most asks
  disappear at step one once you actually test them, because "I need this from them" is
  usually "I would prefer this from them."
- **Only three things justify asking a human at all** — binding authority, credentials or
  physical access nobody else holds, and a fact that exists only in their head. Preference,
  convenience, and "they would probably want to weigh in" are not gates.
- **Every ask ships with its rescue, decided before sending**: a deadline, a named fallback
  action, and you as the owner of that fallback. Put it in the message. "If I do not hear
  back by Friday I will assume X and proceed" turns silence into a decision, and usually
  produces the reply anyway.
- **Shrink the ask until it can be answered in ten seconds.** One question, one message, a
  yes or no where possible, plus what you already tried. A question that makes someone
  reconstruct context is a question that does not get answered.
- **When the deadline passes, execute the rescue quietly.** Do not re-send the same ask.
  Do not hand the chase to whoever is busiest. Log the miss for the periodic reliability
  record and move on: a pattern is a management conversation, held later with evidence in
  hand, not an interruption now.
- **The second time the same dependency blocks, stop treating it as a people problem.**
  Build the thing that makes their non-response harmless — a watchdog, a fallback route, a
  second credential, a cached copy. Building it once costs less than chasing it forever.
- Use the selective-review standard in `agents-draft-humans-send`: execute routine
  rescue work, messages, and publication within recorded authority. Silence never supplies
  missing authority or clears an explicit hold. Stage only the consequential decision
  that still requires advance review, and continue the independent work.
- Rescue toward the function, not the person — see `assign-work-to-a-function`. A rescue
  aimed at an individual who is away is not a rescue.
- **A parked ask carries a date or it is not parked, it is dropped.** Any status row that
  says "waiting on", "blocked on" or "pending <person>" must also say when someone
  comes back to it. A team can check this with a linter that rejects a pending row
  without a timezone-aware recheck date and an accountable next owner. Test a row
  with those fields and one without them before trusting the check. Record actual
  runtime loading and scheduled execution separately; a written rule proves neither.
- Canonical public statement: https://dennisyu.com/unanswered-ask/.
  Public disclosure guide: https://dennisyu.com/agent-disclosure/.
  Marker `UNANSWERED-ASK-RESCUE-2026-09-04`.
