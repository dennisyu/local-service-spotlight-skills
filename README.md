# Local Service Spotlight Skills for Claude

The canonical marketplace for the released Local Service Spotlight skills used across
authority, content, client operations, and quality assurance.

## Install

Members should start with the illustrated guide:
[localservicespotlight.com/install](https://localservicespotlight.com/install/).
When Claude asks for the marketplace repository, paste:

```text
https://github.com/dennisyu/local-service-spotlight-skills
```

Then install `lss-everything`.

If you already added `https://github.com/dennisyu/blitzmetrics-skills` or
installed `blitzmetrics-everything`, remove that marketplace and add this one.
GitHub redirects the old repository URL. Claude still needs a fresh install of
`lss-everything` because plugin names are keyed in the account.

The guide and repository have different jobs:

- The **install guide** tells a nontechnical member where to click and how to test.
- This **GitHub repository** is the source Claude reads and maintainers review.
- GitHub's `/upload/main` page is for maintainers and is not an install link.

The repository is one update channel, so members do not need a new ZIP for every
release. Sync behavior varies by Claude surface and settings: third-party
marketplace auto-update may need to be enabled, or a member may need to choose
**Sync** or **Update**. An update is verified only after the account shows the new
commit/version and a fresh chat passes an activation test.

## What was installed

Start a new chat and ask in plain language. For example:

> “Harvest my positive mentions.”
>
> “Run my weekly brand MAA.”
>
> “How do I show up in ChatGPT?”

Claude should select the relevant skill. Seeing the plugin in a list proves it is
installed; a successful fresh-chat trigger proves that skill is working.

## Bundles

Most people should install `lss-everything`.

| Bundle | What it covers |
|---|---|
| `lss-everything` | Every skill listed in the current marketplace manifest |
| `authority-and-reputation` | Knowledge Panel, AI search, reviews, and proof |
| `content-engine` | Articles, video, repurposing, and distribution |
| `client-operations` | Onboarding, cadence, access, reporting, and audits |
| `quality-and-standards` | Nine Triangles, verification, QA, judgment, outbound closeout, and the registry |

## Skills, agents, and scheduled jobs

- A **skill** is a written recipe Claude can use when asked.
- An **agent** carries out a multi-step assignment using skills and tools.
- A **scheduled job** tells an agent when to run.
- A **receipt** is timestamped evidence that a run succeeded or failed.

Creating a schedule is not proof that it ran. See [ACCEPTANCE.md](ACCEPTANCE.md)
for installation, update, and fleet-job checks.

## House rules travel inside every skill

Every rule the team has learned lives once, as one file, in
[`standards/`](standards/) — never ship a black button, nothing autoplays with
sound, no popup on load, every link and entity claim resolves, personal-brand
heroes are immersive, and the rule about rules: capture what you learn in the
same session.

`scripts/sync_shared_rules.py` stamps each rule verbatim into `AGENTS.md` and every
distributed `SKILL.md` file, so the rules arrive with the pack even though `standards/`
itself is not distributed. CI rejects a pull request when even one copy is
missing or stale.

The same file also carries the patterns that detect a violation in real HTML, and
`scripts/fleet_check.py` compiles them into a live sweep:

```bash
python3 scripts/fleet_check.py --self-test          # prove the checks bite
python3 scripts/fleet_check.py --targets fleet.example.txt
```

One file therefore produces the agent instruction, the human checklist, and the
automated check — Content · Checklist · Software from a single source, so the
rule and the thing that enforces it cannot disagree.

**Adding a house rule to the whole fleet is dropping one markdown file into
`standards/`.** How and why, in plain language:
[HOW-KNOWLEDGE-PROPAGATES.md](HOW-KNOWLEDGE-PROPAGATES.md).

## For maintainers

The `skills/` folder is the single source of truth. Bundles in
`.claude-plugin/marketplace.json` are selections over it; skills are not copied
between bundles.

Never commit from GitHub's `/upload/main` page. Create a branch and pull request,
then let the validation workflow check the manifest, local references, converter,
and Claude marketplace format. Full instructions are in
[CONTRIBUTING.md](CONTRIBUTING.md).

Do not rename an existing skill or bundle without a migration. Installed copies
and scheduled prompts are keyed by name, so a rename can create a duplicate and
silently break jobs that call the old name.
