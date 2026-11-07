---
date: YYYY-MM-DD
agent: claude | codex | grok | cursor | ...
model: model name, or UNKNOWN
touched:
  - repo: <owner/repo>
  - site: <domain>
outcome: shipped | partial | blocked
runbook: runbooks/<agent>/<task-slug>.md | none (one-off)
---

# <Short title of the job>

**One paragraph.** What the job was and its state now. Someone should be able to read
only this and know whether to keep reading.

## What I was asked

The request in the human's words, not your paraphrase.

## What I found

Discoveries with evidence: file paths, status codes, counts, dates.

## What I changed

| What | Where | Verify |
|---|---|---|
| | | |

## What I got wrong

Assertions that turned out false, and the correction. If nothing, say "nothing surfaced".

## Conflicting documentation

Sources that disagreed, and which one won.

## Blocked on

What stopped you, and exactly who or what unblocks it, with a recheck date.

## Next action

The single next thing. One line.

Verified: <what you opened> — <what you saw> — <when>
