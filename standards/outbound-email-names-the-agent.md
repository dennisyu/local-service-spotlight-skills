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

- Every outbound email an agent **sends** (or hands off ready-to-send) must end with a
  one-line closer that names which agent wrote it: Grok Bot, Claude, ChatGPT, Codex,
  Cursor, Perplexity, Gemini, or the desk name (e.g. `— Grok Bot (Ops)` /
  `Sent via Claude`).
- Name the agent even when `From:` is a human (Dennis). The From address is delivery;
  the closer is transparency.
- Place the agent line after the body and before any mail-client legal footer.
- Do not invent a fake human VA signature to hide that an agent wrote it.
- This does not override send-approval gates. When a desk is authorized to send, the
  signature is mandatory. When only drafting, still include the agent name in the draft.
