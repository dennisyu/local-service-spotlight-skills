---
{
  "title": "Reuse existing authorized access before asking for another login",
  "severity": "error",
  "captured": "2026-09-21",
  "captured_from": "Dennis Yu, Codex access-provisioning session, 2026-09-21: reduce repeated agent logins and publish the reusable method",
  "applies_to": [
    "agent-behaviour"
  ]
}
---

## Reuse existing authorized access before asking for another login

- **Before asking for another login, test the access already authorized for this
  task.** Check an existing connector, then the intended signed-in browser profile
  through a supported bridge. Repeated provisioning wastes the user's time.
- Identify the executing app, device or cloud computer, browser profile and account.
  A model name is not an access environment. An installed skill is not a connection,
  and a connected browser is not proof that the target site is signed in.
- Prefer supported session reuse or an app's own authorized import flow. Keep raw
  passwords, cookies and tokens out of prompts, logs, skills and public repositories;
  do not extract browser databases or build a shared credential dump.
- Reuse consent that already covers the same action, account and scope. Do not ask
  for it again merely because the model changed. Authentication does not authorize
  new actions; honor fresh platform consent, MFA, passkeys, CAPTCHA and access limits.
  Silence never supplies missing approval.
- Verify one harmless read in the intended account and record only non-secret access
  metadata in the existing private register. Report installed, connected, signed-in
  and tested states separately. A successful site does not prove every site works.
- Publish the procedure and supported capability limits, never the user's access
  inventory. Use `reuse-agent-access` for the full workflow when that skill is installed.

This is a runtime judgment rule. An HTML regex cannot prove account identity,
consent scope or session reuse; enforce it with a read-only check and its receipt.
It supplements access and action-approval rules rather than granting new authority.
