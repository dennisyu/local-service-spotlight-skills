# Local Service Spotlight Skills for Claude

Use these guides to turn your business's proof into work you can check. Pick a
task, such as checking a customer claim or drafting an article. Read the steps,
make one draft, and check the result before you share it.

This is the maintained source for the Local Service Spotlight Claude marketplace.
Its current package list and skill counts come from `.claude-plugin/marketplace.json`.

## Install

Members should start with the illustrated guide:
[localservicespotlight.com/install](https://localservicespotlight.com/install/).
When Claude asks for the marketplace repository, paste:

```text
https://github.com/dennisyu/local-service-spotlight-skills
```

Then install `lss-everything`.

If you already added `https://github.com/dennisyu/blitzmetrics-skills` or
installed `blitzmetrics-everything`, record the installed package, version and
active jobs first. The old repository URL redirects here, but an old installed
package may still be stale. Follow the current install guide to test the new
`lss-everything` package and preserve a recovery path before retiring an exact
obsolete copy. Do not remove an uninspected marketplace.

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
> “Run a full personal-brand audit.”
>
> “How do I show up in ChatGPT?”

Claude may select the relevant skill, or you can use the supported skill picker.
Record which installed skill was actually selected or loaded, then inspect its
fresh output. A plugin in a list proves installation; a good answer alone does
not prove that the installed skill was used.

The [personal-brand-audit skill](skills/personal-brand-audit/SKILL.md) is the front
door for the full proof inventory, exact 20-page visual PDF, top-connection map, and
agent installation/action plan. Its QR and printed install link use
`https://localservicespotlight.com/install/`, never `/skills/` or a legacy ZIP page.
The complete workflow routes through eight skills and therefore requires
`lss-everything`; the smaller authority bundle supports intake and its installed
authority/reputation lanes, but is not a complete audit installation.

Every full run also queries the canonical [Local Service Spotlight Knowledge Graph
Explorer](https://localservicespotlight.com/knowledge-graph-explorer/) and keeps four
receipts separate: `RESOLVED`, `AMBIGUOUS`, `NO_SAFE_OBJECT_RETURNED`, or `UNKNOWN` graph
object status with a separate safe KGMID; a normal Google name-query panel observation
with date, locale, location, and personalization caveats; owner claim status, which remains
`UNKNOWN` without the owner-side Google claim dashboard or a Google claim receipt; and the
same identity-safe graph fields for the report's related public-association entities. An
Explorer object is not a visible or claimed Knowledge Panel, and a public association is
not friendship or endorsement.

## Bundles

Most people should install `lss-everything`.

| Bundle | What it covers |
|---|---|
| `lss-everything` | All 32 skills |
| `authority-and-reputation` | Personal-brand audit intake plus its installed authority/reputation lanes; use `lss-everything` for the full workflow |
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

`scripts/sync_shared_rules.py` stamps every rule verbatim into `AGENTS.md` and
each applicable `SKILL.md`; agent-behavior rules reach all 32 skills. The rules
arrive with the pack even though `standards/` itself is not distributed. CI
rejects a pull request when even one required copy is missing or stale.

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
