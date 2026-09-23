---
name: shared-memory
description: How to read and write Dennis's second brain — the shared Obsidian vaults that every agent uses as team memory. Use whenever you need context about Dennis, his business, past work, or durable decisions, and write back what you learn so the next agent starts smarter.
---

# Shared memory (Dennis's second brain)

Dennis's second brain is his shared knowledge store that every agent reads and
writes. **Obsidian vaults are one part of it** — one vault per client, one per
project, and one team memory every agent can read — alongside his other
documentation systems (Google Drive/Docs, the GitHub agent-runtime records,
Basecamp threads, and his published articles/skills). Treat all of these as
the shared source of truth across Claude, ChatGPT/Codex, Grok, and every other
agent. No agent keeps important context only in its own session.

Reference: https://blitzmetrics.com/obsidian-cowork-layer-shared-memory-across-agents/

## Read first

- Before starting work, check the vault for existing context: who and what is
  involved, past decisions, current status, house style.
- The answer to "who is X, what matters about them, what's the current status" is
  the same file for every agent. Don't re-derive it — read it.
- On a Cowork-style runtime, the workspace folder itself is the vault. On other
  runtimes, use whatever shared folder or memory system maps to the same vault.

## Write back

- Session N+1 must be more informed than session N **because session N wrote to
  the vault.**
- Write durable learnings as Markdown: decisions made, preferences stated,
  facts about people and projects, what worked, what failed and why.
- Keep it public-safe and topic-level. No secrets, credentials, tokens, private
  financial/health details, or anything Dennis wouldn't want in a shared file.
- Update existing notes rather than duplicating them. One canonical note per topic.

## What goes where

- Per-client and per-project vaults hold that client/project's context.
- The team memory holds cross-cutting knowledge: Dennis's preferences, methods,
  standards, relationship notes, and operating rules every agent should follow.

## Compounding

- Within a project: every session adds to the hub.
- Across projects: patterns from one build stay visible when the next starts.
- Across agents: an email answered Monday, an article drafted Tuesday, and a
  fact-check done Wednesday all read the same notes.
