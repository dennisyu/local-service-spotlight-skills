# Distribution — from source to working capability

Most failures happen after a skill is written. A repository can be valid while a
member never installed it, a schedule can exist without firing, and an agent can
report success without checking the expected artifact.

## Preferred path for groups

Use the GitHub marketplace for shared skills:

```text
Member-facing instructions: https://localservicespotlight.com/install/
Marketplace source for Claude: https://github.com/dennisyu/local-service-spotlight-skills
Maintainer changes: branch → pull request → checks → merge
```

Do not send members to GitHub's `/upload/main` URL. It is a maintainer upload form,
not an installer, and it encourages direct writes to the canonical branch.

The marketplace gives every member the same update channel. Do not promise that
every third-party update applies unattended: that depends on Claude surface and
settings. Record **manual sync verified** and **auto-update verified** separately.

## File delivery fallback

Use marketplace installation for a group. When a marketplace is unavailable, the
file extension determines the fallback experience:

| Extension | What it does | Use it for |
|---|---|---|
| `.plugin` | Installable plugin package | A pack delivered directly |
| `.skill` | Standalone account skill | One person's one-off skill |
| `.zip` | Download only | Manual fallback, not the primary member path |

Convert legacy pack directories or ZIPs with the repository's converter:

```bash
python3 scripts/pack2plugin.py PACK.zip --out ./dist
python3 scripts/pack2plugin.py ./packs/*.zip --out ./dist --dry-run
```

It finds `SKILL.md` files at any depth, repairs names to match their normalized
directories, strips release suffixes from plugin names, excludes common macOS
cruft, copies top-level `agents/` and `commands/`, and writes a `.plugin` archive.
It rejects unsafe ZIP traversal paths and never modifies the input.

## The evidence ladder

Use exactly these terms in reports:

| State | Required proof |
|---|---|
| Available | File is in a merged, validated marketplace commit |
| Delivered | Link or file reached the recipient |
| Installed | Named account/workspace shows the bundle |
| Enabled | Named account/workspace permits its use |
| Tested | Fresh chat triggers the expected skill behavior |
| Scheduled | Job definition exists with an owner and next run |
| Observed | Timestamped firing has an output or an unedited failure |

Do not report `Delivered` as `Installed`, `Scheduled` as `Observed`, or a passing
repository check as a passing account test.

## What an install guide must answer

A nontechnical member needs, in this order:

1. One-sentence definitions of skill, plugin, agent, schedule, and receipt.
2. The plan/surface requirements and any workspace admin setting.
3. One recommended marketplace path with the exact repository URL.
4. The exact current menu labels and clicks.
5. A fresh-chat trigger test and the expected result.
6. How to sync an update and confirm commit/version.
7. Which features are desktop/Cowork-only.
8. Symptom-based troubleshooting and a human escalation route.

The guide is not accepted until a first-time member completes it without private
coaching and produces an acceptance receipt.

## Safe ownership between agents

- Claude runs the production task and writes an immutable run receipt.
- Codex audits source, receipts, assertions, and failures on a separate branch.
- A human approves merges and production schedule/credential changes.
- Only one actor may hold a lock for a production job or canonical file at a time.

This makes the auditor independent without allowing two agents to overwrite the
same state. Detailed checks are in the repository root `ACCEPTANCE.md`.

## Definition of done

- Repository and official marketplace validators pass.
- Pull request is reviewed; no direct-to-main upload was used.
- Fresh-account install and fresh-chat activation have receipts.
- Update propagation is tested on the relevant Claude surface.
- Every recurring job has an owner, runtime, exact skill version, next expected
  run, durable receipt, and missed-run alert.
