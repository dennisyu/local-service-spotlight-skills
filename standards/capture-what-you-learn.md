---
{
  "title": "Capture what you learn as a standard, in the same session",
  "severity": "error",
  "captured": "2026-08-16",
  "captured_from": "Dennis Yu / Local Service Spotlight public standard: Capture what you learn as a standard, in the same session. Original capture date is retained in captured. Public-safety clarification authorized by the owner on 2026-10-29; this reusable copy omits private conversation, personnel, account and incident details.",
  "applies_to": [
    "agent-behaviour"
  ]
}
---

## Capture what you learn as a standard, in the same session

- **A lesson kept only in an article, chat, recording or context window may be
  absent from the instructions the next operator loads.** Capture its reusable
  criteria in the canonical standard, distribute the applicable source copies,
  and test the receiving runtime before claiming adoption.
- When anyone — the client, the account owner, an audit, or your own failure — states a
  rule that should hold next time, **your job is not to remember it. It is to write
  `standards/<slug>.md` before the session ends.** Memory does not survive a session
  boundary. A file does.
- Scaffold it in one command, which forces every field including where the rule came
  from:

  ```bash
  python3 scripts/new_standard.py "no autoplay with sound" \
    --from "Dennis Yu, Cowork session, 2026-08-16" --applies-to published-html
  ```

- Then write the rule, run `python3 scripts/sync_shared_rules.py`, and open the pull
  request. The sync copies the rule into `AGENTS.md` and each distributed `SKILL.md`
  whose declared scope applies. This prepares source copies; it does not update an
  existing installation. Record the released revision, required sync action and a
  fresh-session activation test for each account being claimed.
- **Give the rule a machine check whenever one is honest.** A `checks` block in the
  header is consumed by the fleet sweep when that sweep actually runs against an
  applicable target. Every check must carry passing and failing examples. Exercise
  a separate failing case too: a pattern that matches nothing can look healthy.
  Record scheduling and actual firing separately; a check in source creates neither.
- **Where a machine check would be dishonest, say so and leave `checks` out.** Judgement
  rules still need a qualified reviewer to apply them to the actual result. Reading
  a rule is not evidence of compliance, and a regex cannot certify judgement.
- **Provenance is required, not decoration.** `captured_from` is how the team sees which
  channels leak. Missing provenance is a reason to inspect the capture path; it does
  not establish how many recordings exist or whether an undocumented process ran.
- **When a new rule contradicts an existing one, resolve it in the file and say so
  out loud.** Two standards that disagree are worse than one that is wrong, because
  every agent that reads both will pick whichever it happened to see last. Write the
  reconciliation into the newer rule and flag it to the account owner for confirmation.
- The order is Checklist → Content → Software. Write the checkable rule first, publish
  the article that teaches it second, and let the sweep be generated from the rule
  rather than hand-written beside it when the declarative check types suffice.
  Complex checks need maintained code and tests linked from the rule. CCS means
  Content, Checklists, Software; this checklist-first capture sequence preserves
  that framework. An article alone leaves checks and adoption unproved.
- **Close the learning loop with another operator.** Link the actual run, correction,
  standard, teaching content and software check. Give a fresh operator only the
  guide and permitted inputs; record the tested revision, result, failures and help
  required. Fix ambiguity in the master and replay the affected steps. Saying the
  lesson was shared does not prove another operator can use it.
