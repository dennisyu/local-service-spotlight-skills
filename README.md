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

The canonical bundle names and memberships live only in
[`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json). Read that
manifest when auditing what should appear; do not maintain a second bundle list
in documentation.

## Skills, agents, and scheduled jobs

- A **skill** is a written recipe Claude can use when asked.
- An **agent** carries out a multi-step assignment using skills and tools.
- A **scheduled job** tells an agent when to run.
- A **receipt** is timestamped evidence that a run succeeded or failed.

Creating a schedule is not proof that it ran. See [ACCEPTANCE.md](ACCEPTANCE.md)
for installation, update, and fleet-job checks. Sanitized exact-byte publication
evidence for public fleet pages follows the tracked
[agent-fleet receipt contract](receipts/agent-fleet/README.md); private scheduler
details never belong there.

## House rules travel inside every applicable skill

Every rule the team has learned lives once, as one file, in
[`standards/`](standards/) — never ship a black button, nothing autoplays with
sound, no popup on load, every link and entity claim resolves, personal-brand
heroes are immersive, and the rule about rules: capture what you learn in the
same session.

`scripts/sync_shared_rules.py` stamps every rule into `AGENTS.md`. Universal
agent-behaviour rules also enter every distributed `SKILL.md`; published-page and
design rules enter the skills whose frontmatter declares the matching
`rule-scopes`. The rules therefore arrive where they apply even though
`standards/` itself is not distributed. CI derives the applicable target set and
rejects a pull request when any required copy is missing or stale.

The same file also carries machine-check configuration and paired examples;
`scripts/fleet_check.py` compiles simple checks and dispatches structural kinds
to separately reviewed shared code:

```bash
python3 scripts/fleet_check.py --self-test          # prove the checks bite
python3 scripts/fleet_check.py --targets fleet.example.txt
```

Fleet-file targets tagged `current-live` enforce the generic 30-day
re-verification SLA. Use that tag only for the canonical current page; omit it
for immutable receipts, archived HTML, and other historical evidence. The
scheduled-jobs fleet has its stricter 36-hour SLA by canonical URL regardless
of tags.

One file therefore produces the agent instruction, human checklist, check
configuration, and examples — Content · Checklist · Software with less room for
drift. Self-tests and independent hostile review reduce drift between structural
implementations and their prose; they cannot make disagreement impossible.

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
