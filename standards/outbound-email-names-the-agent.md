---
{
  "title": "Outbound email names the agent",
  "severity": "error",
  "captured": "2026-08-22",
  "captured_from": "Dennis Yu via Website Builder / Training → Ops, 2026-08-22",
  "applies_to": [
    "agent-behaviour"
  ]
}
---

## Outbound email names the agent

- Every email an agent drafts or hands off ready-to-send—and every delivered copy
  when a human approves and sends it—must end with a one-line attribution naming
  the agent/model and its function.
- The controlling default remains `agents-draft-humans-send`: the agent stages the
  message and a human dispatches it. In that case use exact provenance such as
  `Drafted by Codex (Ops); sent by Dennis Yu`. A draft that has not been dispatched
  says only `Drafted by Codex (Ops)`.
- Use `Sent by` or `Sent via` for an agent only when an exact execution receipt proves
  that agent had scoped send authority and performed the dispatch. Under the default
  human-send rule, `Sent via Claude` or similar is false and forbidden.
- `From:` is the authenticated transport identity; the closer records authorship and
  dispatch provenance. Do not attribute a human send to a model or a model draft to a
  human.
- Place the agent line after the body and before any mail-client legal footer.
- Do not invent a fake human VA signature to hide that an agent wrote it.
- The closer never grants send authority and never substitutes for an approval or
  execution receipt.
