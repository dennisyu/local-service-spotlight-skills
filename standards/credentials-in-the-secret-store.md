---
{
  "title": "Fleet credentials live in the secret store — never in chat, email, memory, or a skill",
  "severity": "error",
  "captured": "2026-09-04",
  "captured_from": "Dennis Yu, Cowork session, 2026-09-04: fleet WP app-password access rebuild; decision to make AWS SSM the single source of truth for fleet credentials.",
  "applies_to": ["agent-behaviour"]
}
---

## Credentials live in the secret store

- **The store is the source.** Every fleet WordPress Application Password (and every token an
  agent uses) lives in the secret store and is read at the moment of use — not typed, pasted,
  or remembered. If the store has the key, a routine publish has no login step.
- **One store is the single source of truth** (decided 2026-09-04): a managed secret store
  holding SecureString entries of {"username","app_password"} per domain, encrypted,
  IAM-scoped, and access-audited, reachable from every runtime — the cloud runner and Cowork /
  cross-runtime agents alike. The runtime's local credential file is a read-through fallback
  until the resolver is migrated to read the store first. A store the current agent cannot
  read is, for that agent, no store at all — which is what used to force a human login.
- **Never place a credential anywhere that ships or persists in the clear** — not chat, not
  email, not a memory file, not a skill file, not a URL or query string. Use it in the
  `Authorization` header and nowhere else.
- **A credential delivered by chat or email is compromised on arrival.** Store it, use it, and
  schedule a rotation; careful handling afterward does not undo an insecure delivery.
- **Fetch at run time; never cache a secret into an artifact.** An agent that has the store
  does not ask a human to log in.
- **Do not scrape credentials out of a dashboard's site API via browser JS** — the agent
  safety classifier blocks it, correctly. Read from the secret store instead.
- **Least privilege.** Agents authenticate with an identity scoped to read the WP secrets and
  decrypt, nothing more — never a human's full account.
- **Addresses, account IDs, secret paths and site lists are configuration, not content** —
  they live in the internal runbook, never in a distributed skill or a public article. The
  public article teaches the pattern with placeholders.
- **Default publishing path is now plain REST with the app password; cookie+nonce is the
  fallback.** The fleet's `Authorization`-header strip was fixed 2026-09-04. Re-probe before
  assuming the strip; it changed once and can change back.
