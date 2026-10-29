# Shared memory — durable facts, not a second task board

Keep dated, sourced facts that another authorized worker needs across sessions.
Record the source reference, relevant scope and last verification. If a fact
changes, update its existing entry and preserve the reason/history; do not leave
two contradictory current versions. Keep task claims in the task record and
[status/NOW.md](status/NOW.md), and decisions in
[decisions/DECISIONS.md](decisions/DECISIONS.md).

- Owner's preferred name, timezone and communication preferences.
- Approved project scope and the authoritative source for current status.
- Tested agent/runtime capabilities, their evidence and any known limits.
- A reusable lesson and the canonical procedure it updates.

These are prompts for entries, not verified facts or account entitlements.
Do not store secrets, credentials, health data or private client records here.
Keep necessary operational context in the intended private access tier.
Vendor memory is a cache; the team chooses one durable authority per record type.
