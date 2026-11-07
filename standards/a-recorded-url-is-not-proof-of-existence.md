---
{
  "title": "A recorded URL is not proof of existence",
  "severity": "error",
  "captured": "2026-10-26",
  "captured_from": "agent-ops-log 2026-10-22 people-photo-inventory runbook; Dorrie incident 2026-09-28 (Google rolled back a half-made album after a re-auth wall timed out)",
  "applies_to": [
    "agent-behaviour"
  ]
}
---

## A recorded URL is not proof of existence

- **Writing a URL, ID, or handle into your notes proves nothing.** Platforms roll back
  half-made artifacts when a sensitive action is interrupted — on 2026-09-28 Google
  Photos silently deleted an album whose creation run hit a "verify it's you" wall and
  timed out; the recorded URL 404'd within minutes. An agent building on that recorded
  URL would have built on nothing.
- **Re-fetch after every interruption.** After any verification wall, timeout, crash, or
  session recovery, re-open each artifact created since the last confirmed checkpoint and
  confirm it still exists before recording it or building on it. Treat "created, then the
  run broke" as "unknown" until re-fetched.
- **Re-auth walls have grace windows — measure them and burst inside them.** When a
  platform periodically demands the owner re-verify, one verification typically unlocks a
  bounded run of actions (observed: ~40 album creations per window, 3 measurements). Note
  the observed window size in the ops log, queue work so bursts fit inside it, and keep
  each item close behind the previous one.
- **Report unverified items as unverified.** A queue entry marked "existence unconfirmed"
  is a workable state; a queue entry silently assumed to exist is a future incident.
  Exemption: none for recorded identifiers — but a *verified* artifact (fetched, status
  checked, content confirmed) may be treated as existing until the next interruption.
