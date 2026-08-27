---
{
  "title": "Silent media playback",
  "severity": "error",
  "captured": "2026-08-16",
  "captured_from": "Already in standards/ before the standards index existed; the original statement was not recorded. Header added 2026-08-16 so every rule carries provenance. If you know where this rule was first stated, replace this line — a rule you cannot trace is a rule you cannot re-check against its source.",
  "applies_to": ["agent-behaviour"]
}
---

## Silent media playback

- Never let audio from browser, video, audio, presentation, or application testing play through the user's speakers unless the user explicitly asks to hear it.
- Before starting any media playback, mute the player and set its volume to zero. Keep it muted for the full test, including replays, reloads, new tabs, and alternate players.
- Apply this rule to the primary agent and every delegated agent. Include the mute requirement whenever work that may involve media playback is delegated.
- If the mute state cannot be controlled and verified before playback, do not start playback. Use metadata, captions, transcripts, frames, screenshots, network state, or player state instead.
- Only unmute when the user explicitly requests audible playback in the current task.
