# decisions/DECISIONS.md — the decision registry

Every decision the human makes directly — in any chat, call, or message —
gets filed here the same day by the agent who heard it. Agents executing a
decision cite its ID here instead of asking the human to approve
agent-to-agent steps again.

## Format

### D-YYYY-MM-DD-01 — (short title)
- **Quote:** "(the human's words, verbatim)"
- **When / where:** (date, time, channel)
- **Scope:** (what this covers)
- **Reversibility:** reversible / irreversible

## Tiers

- **A — execute on the filing.** Reversible, routine operational work.
- **B — execute after a registry check.** Work implementing a registered
  decision; the work order cites the decision ID + quote.
- **C — the human's direct word required.** Only: irreversible or
  destructive actions outside standing authority; money commitments beyond
  standing test-spend authority; personal/sensitive material; credential or
  security changes; first-of-kind external commitments in the human's name.
  Everything not in Tier C is A or B by default.
