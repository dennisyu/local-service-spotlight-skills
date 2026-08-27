# BlitzMetrics Skills for Claude and Grok

The canonical marketplace for the 28 BlitzMetrics and Local Service Spotlight
skills used across authority, content, client operations, and quality assurance.
Claude and Grok Build load the same `skills/` source, so the operating method does
not fork by model.

## Install

### Claude

Members should start with the illustrated guide:
[localservicespotlight.com/install](https://localservicespotlight.com/install/).
When Claude asks for the marketplace repository, paste:

```text
https://github.com/dennisyu/local-service-spotlight-skills
```

Then install `blitzmetrics-everything`.

The guide and repository have different jobs:

- The **install guide** tells a nontechnical member where to click and how to test.
- This **GitHub repository** is the source Claude and Grok read and maintainers review.
- GitHub's `/upload/main` page is for maintainers and is not an install link.

The repository is one update channel, so members do not need a new ZIP for every
release. Sync behavior varies by Claude surface and settings: third-party
marketplace auto-update may need to be enabled, or a member may need to choose
**Sync** or **Update**. An update is verified only after the account shows the new
commit/version and a fresh chat passes an activation test.

### Grok Build

Review the repository, then install it with Grok Build's native plugin command:

```bash
grok plugin install dennisyu/local-service-spotlight-skills --trust
grok plugin details blitzmetrics-everything
```

`--trust` is required for a non-interactive install. Grok plugins can also contain
executable hooks and MCP servers, so inspect any repository before trusting it;
this repository currently distributes skills only.

Run this deterministic inventory canary:

```bash
grok inspect --json | python3 -c 'import json,sys; d=json.load(sys.stdin); p=next(p for p in d["plugins"] if p["name"] == "blitzmetrics-everything"); assert p["enabled"] and p["provides"]["skills"] == 27; print("Grok canary passed: blitzmetrics-everything, 27 skills")'
```

Then prove that a fresh agent can activate one of the shared skills (this uses one
model request):

```bash
grok -p 'Use the skill-registry skill. In one sentence, identify the numbered registry system that is the only canonical source.'
```

The answer should identify **System 1, the canonical GitHub marketplace**. A
passing inventory command proves discovery; the model canary proves activation.

## What was installed

Start a new chat and ask in plain language. For example:

> “Harvest my positive mentions.”
>
> “Run my weekly brand MAA.”
>
> “How do I show up in ChatGPT?”
>
> “Map my second ring from my LinkedIn connections export.”

The active model should select the relevant skill. Seeing the plugin in a list
proves it is installed; a successful fresh-chat trigger proves that skill is
working.

## Bundles

Most people should install `blitzmetrics-everything`.

| Bundle | What it covers |
|---|---|
| `blitzmetrics-everything` | All 28 skills |
| `authority-and-reputation` | Knowledge Panel, AI search, reviews, proof, and relationship paths |
| `content-engine` | Articles, video, repurposing, and distribution |
| `client-operations` | Cadence, access, reporting, and audits |
| `quality-and-standards` | Nine Triangles, verification, QA, judgment, and the registry |

## Skills, agents, and scheduled jobs

- A **skill** is a written recipe Claude or Grok can use when asked.
- An **agent** carries out a multi-step assignment using skills and tools.
- A **scheduled job** tells an agent when to run.
- A **receipt** is timestamped evidence that a run succeeded or failed.

Creating a schedule is not proof that it ran. See [ACCEPTANCE.md](ACCEPTANCE.md)
for installation, update, and fleet-job checks.

## Workplace-safe media testing

Every distributed skill carries the same silent-playback guardrail: an agent must
mute the player and set volume to zero before testing video or audio. The rule
also applies to delegated agents, reloads, replays, new tabs, and alternate
players. If mute cannot be controlled and verified, the agent must use captions,
transcripts, metadata, screenshots, frames, or player state instead of pressing
Play.

The human-readable source is
[`standards/silent-media-playback.md`](standards/silent-media-playback.md).
`scripts/sync_shared_rules.py` embeds that source in every `SKILL.md`, and the
repository validator rejects a pull request when even one copy is missing or
stale. That is Content · Checklist · Software in a form anyone can inspect.

## For maintainers

The `skills/` folder is the single source of truth. Bundles in
`.claude-plugin/marketplace.json` are selections over it; skills are not copied
between bundles.

Never commit from GitHub's `/upload/main` page. Create a branch and pull request,
then let the validation workflow check the manifest, local references, converter,
Claude marketplace format, and Grok adapter alignment. Full instructions are in
[CONTRIBUTING.md](CONTRIBUTING.md).

Do not rename an existing skill or bundle without a migration. Installed copies
and scheduled prompts are keyed by name, so a rename can create a duplicate and
silently break jobs that call the old name.
