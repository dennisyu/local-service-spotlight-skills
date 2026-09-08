---
name: Agents-first reassignment
description: >-
  Use when reassigning work off an unavailable or non-delivering human — agents
  first, humans only if no SOP/agent path; covers Josh Hamby/Healey and Basecamp
  agent-claim pattern.
---
# Agents-first reassignment

Use when work must leave an unavailable or non-delivering human (reassign Basecamp todos, client stewardship, Ops routing).

## Rule (2026-09-08)

Assign **agents first** wherever possible. Use **humans only** when there is no agent/SOP path. Nearly everything has an SOP.

Applies to every seat: Grok Bot desks, Cursor, Codex, Claude, Kimi, local Qwen.

Marker: `AGENTS-FIRST-REASSIGNMENT-2026-09-08`.

## People currently off assignment

- **Josh Hamby** — unavailable (car accident). Do not assign. Do not chase email.
- **Josh Healey** (`josh@jdhealey.xyz`) — off assignment (non-delivery). Do not assign. Do not chase for delivery.

## Basecamp pattern

Basecamp assignees are humans. For agent ownership:

1. Unassign the unavailable/non-delivering person (`assignee_ids: []`).
2. Comment an **agent claim** naming the owning desk (Austin IT, Mario sites, Tanner ops chase, Trenton content, Cursor/Codex code, etc.).
3. Route the job to that agent (SendToAgent / Agent Collab / Cursor cloud). Do **not** park on Ops humans by default.
4. Never make Hezekiah (Zek) a paste-layer dependency.

## Closeout

Ops email when a person is newly off assignment. Shared user memory + Agent Collab post for non-Grok seats. Agent note after substantive pass. Outbound email still names the agent; public social posts never include agent receipts.
