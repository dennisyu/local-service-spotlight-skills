---
{
  "title": "Name the agent on every outbound email",
  "severity": "error",
  "captured": "2026-08-22",
  "captured_from": "Dennis Yu via Website Builder feedback to Ops, 2026-08-22",
  "applies_to": [
    "agent-behaviour"
  ]
}
---

## Name the agent on every outbound email

- **Every outbound email an agent sends** (Gmail send/reply) MUST end with a one-line
  signature naming which agent sent it — for example `Sent by Grok Bot (BlitzMetrics Ops)`,
  `Sent by Claude`, `Sent by ChatGPT`, `Sent by Codex`, `Sent by Cursor`, or
  `Sent by Perplexity`.
- Do this even when sending as Dennis (`From: dennis@…`). The agent identity is for
  internal transparency, not a second From address.
- Place the line after the body and before any legal/footer boilerplate if one exists.
- If the surface is not email (Basecamp, Slack), still name the agent in the
  receipt/agent-note; **email is the hard requirement**.
