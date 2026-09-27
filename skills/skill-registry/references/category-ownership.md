# Agent category ownership

How Dennis's agents coordinate across the skill pack: each agent specializes in
one category (bundle), and every agent reads and writes the same shared memory.
The six departments are Dennis's: Front desk, Research, Build, Publishing,
Growth, Quality.

## Department → bundle map

| Department | Bundle | Agent specialty |
|---|---|---|
| Front desk | `client-operations` (intake half) | Client intake, screening, access capture |
| Research | `authority-and-reputation` | Audits, visibility, entity authority |
| Build | `client-operations` (delivery half) | Websites, security, analytics plumbing |
| Publishing | `content-engine` | Content production and amplification |
| Growth | `content-engine` + `client-operations` | Ads, sales, brand strategy |
| Quality | `quality-and-standards` | Frameworks, verification, QA, closeout |

## Shared core — every agent loads this

Regardless of specialty, every agent also loads the shared core inside
`quality-and-standards`:

- `boil-the-ocean` — operating principles for the whole pack
- `agents-first-reassignment` — reuse authorized access before reprovisioning
- `skill-registry` — the intake gate for new skills
- `shared-memory` — Dennis's second brain: read before working, write back
  what you learn

## Coordination rules

1. **Read shared memory before working.** Who is involved, past decisions,
   current status, house style — one canonical note per topic, same file for
   every agent (see the `shared-memory` skill).
2. **Write durable learnings back.** Session N+1 is smarter because session N
   wrote to the vault. Public-safe, topic-level, no secrets.
3. **Stay in your lane for edits.** Propose changes to another category's
   skills by pull request with that category's owner as reviewer — never edit
   another lane's skill directly on main.
4. **New capability? Run the intake gate** (`skill-registry`) and add the skill
   to the right bundle, not just `lss-everything`.
5. **Disputes between agents are settled by the canonical note**, not by who
   ran last. If the note is wrong, fix the note by PR.
