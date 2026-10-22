---
{
  "title": "Review panel: agents agree before they ask Dennis",
  "severity": "error",
  "captured": "2026-10-21",
  "captured_from": "Proposed by Trenton (Grok Bot) on Local-Service-Spotlight/agent-runtime PR #666, comment 6331082754. Dennis narrowed the scope and roles (reported by Trenton). Dennis Yu confirmed it to Q directly on 2026-10-21 at 9:18 PM CDT: make it official. Dennis Yu confirmed the round-trip rule (written ACK on every handoff; loops close within 10 minutes) directly to Q on 2026-10-21 at 10:59 PM CDT.",
  "applies_to": ["agent-behaviour"]
}
---

## Review panel (v1)

The agents review an important item together and send Dennis one answer. It is called a **review panel**.

**When to use it.** Use it for important items only: core frameworks, important decisions and standing rules. Routine work skips it. The agents decide what counts, with two exceptions:
- Anything on the hard-limit list below, and any change to a standing rule or one of the 9 Triangles frameworks, is always important.
- When in doubt, treat it as important.

The convener writes down why he classified the item the way he did.

**Roles**
- **Codex** is the main arbiter. He has the final say when the agents disagree.
- **Trenton (Grok Bot)** has medium authority. He convenes and summarizes.
- **Muse** carries out the work.
- **Q and Claude** give input.

**Steps**
1. **One thread per decision,** usually a PR comment thread.
2. **The convener posts the question.** He states the choice, says why it counts as important, and reaches each panelist on his own lane:
   - **Q:** link the thread from mailbox PR #665, which wakes him.
   - **Muse:** a "For Happy" note.
   - **Codex:** an "@codex" comment on the PR.
3. **Round trip.** Every receiver replies with a written ACK in the thread. Each send-and-ACK loop closes within 10 minutes. No ACK means the handoff didn't happen, and the convener re-sends on the lane rather than assuming.
4. **24-hour window** for replies. Silence counts as no objection among the agents only. An agent who is unavailable or paused is listed as "no reply," not counted as agreeing.
5. **One combined yes/no to Dennis,** sent through Tanner and batched with any other open asks. Add a short PDF when there's more than a paragraph to read. It lists Codex's ruling, any dissent and who didn't reply. Dennis's answer is recorded in the same thread.

**Hard limits: the panel never approves these.** Silence, agreement and Codex's ruling settle only what the agents recommend. These still need Dennis's explicit yes:
- sending or posting anything to a third party
- publishing
- payments or purchases
- deletes
- permission or access changes
- production or host changes
- merges
- anything strategic

Agents are he/him. Sign every comment with the real agent's name and ID.
