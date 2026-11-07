# Dennis Yu's agent setup and Local Service Spotlight skills

**Setting up agents to work together? Start with
[START-HERE.md](START-HERE.md).** It includes a copyable workspace, one practice
task, a fresh-session handoff, failure recovery and evidence checks. It works as
a public instruction route for any assistant that can read it; actual file,
connector and execution capabilities must be tested in that assistant's account.

| Your goal | Use |
|---|---|
| Coordinate your own agents | [Portable setup](START-HERE.md) and [workspace templates](coordination-starter/README.md) |
| Install a supported skills package | [Illustrated install guide](https://localservicespotlight.com/install/) and product-specific routes below |
| Understand Learn → Do → Teach and CCS | [Worked learning loop](docs/agent-setup/LEARN-DO-TEACH.md) |
| Let an agent navigate the source | [agent-setup.json](agent-setup.json) and [llms.txt](llms.txt) |

This is the **public reusable source**. Dennis's private operational repositories
are implementation examples, not prerequisites or credentials for your team.

Use these guides to turn your business's proof into work you can check. Pick a
task, such as checking a customer claim or drafting an article. Read the steps,
make one draft, and check the result before you share it.

This is the maintained source for the Local Service Spotlight Claude marketplace.

Its current package list and skill counts come from `.claude-plugin/marketplace.json`.

## Install skills, or read the instructions directly

Claude marketplace packaging is one distribution route. ChatGPT/Codex, Muse,
Grok Bot and other assistants should begin with the portable setup and use only
their actually supported file/connector/instruction route. Reading a skill is not
installing it. Grok **Build** below is a different product surface from Grok Bot;
one surface's plugin command does not configure the other.

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

### Grok Build

Review the repository, then install it with Grok Build's native plugin command:

```bash
grok plugin install dennisyu/local-service-spotlight-skills --trust
grok plugin details lss-everything
```

`--trust` is required for a non-interactive install. Grok plugins can also contain
executable hooks and MCP servers, so inspect any repository before trusting it;
this repository currently distributes skills only.

Run this deterministic inventory canary:

```bash
grok inspect --json | python3 -c 'import json,sys; d=json.load(sys.stdin); p=next(p for p in d["plugins"] if p["name"] == "lss-everything"); assert p["enabled"] and p["provides"]["skills"] > 0; print("Grok canary passed: lss-everything, %s skills discovered" % p["provides"]["skills"])'
```

Then test a fresh task using authorized capacity. Keep the runtime's selected-
skill/load evidence as well as its checked output:

```bash
grok -p 'Use the skill-registry skill. In one sentence, identify the numbered registry system that is the only canonical source.'
```

The answer should identify **System 1, the canonical GitHub marketplace**. The inventory command checks recorded plugin discovery. The expected answer alone
does not prove activation: retain the runtime's actual selection/load evidence
and inspect the fresh result. Without that evidence, mark activation UNVERIFIED.

## What was installed

Start a new chat and ask in plain language. For example:

> “Harvest my positive mentions.”
>
> “Run my weekly brand MAA.”
>
> “Run a full personal-brand audit.”
>
> “How do I show up in ChatGPT?”
>
> “Map my second ring from my LinkedIn connections export.”

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
| `lss-everything` | All 39 skills |
| `authority-and-reputation` | Personal-brand audit intake plus its installed authority/reputation lanes; use `lss-everything` for the full workflow |
| `content-engine` | Articles, video, repurposing, and distribution |
| `client-operations` | Onboarding, cadence, access, reporting including GA4, and audits |
| `quality-and-standards` | Agents-first reassignment, Nine Triangles, verification, QA, judgment, outbound closeout, and the registry |

## Reuse access across agents

If your agents keep asking you to sign in, use
[`reuse-agent-access`](skills/reuse-agent-access/SKILL.md), included in
`lss-everything` and `client-operations`. It checks an authorized connector or
signed-in browser before requesting another login. The
[product route guide](skills/reuse-agent-access/references/product-routes.md)
explains which apps can reuse Chrome and which keep separate sessions.
Instructions are portable; passwords, cookies and personal access inventories
stay private. After syncing, start a fresh chat and ask the skill to verify one
harmless read on the site you name. Record the installed revision and result;
publication alone does not install tools or grant access.

## Skills, agents, and scheduled jobs

- A **skill** is a written recipe an assistant can load through a supported route.
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
each applicable `SKILL.md`; agent-behavior rules reach every skill in the
manifest. The rules
arrive with the pack even though `standards/` itself is not distributed. CI
rejects a pull request when even one required copy is missing or stale.

The same file also carries the patterns that detect a violation in real HTML, and
`scripts/fleet_check.py` compiles them into a live sweep:

```bash
python3 scripts/fleet_check.py --self-test          # prove the checks bite
python3 scripts/fleet_check.py --targets fleet.example.txt
```

One file supplies the agent instruction and human checklist. For rules with an
honest machine check, it also supplies test definitions — Content · Checklist ·
Software. Tests establish only their declared scope; judgment, live execution
and installed-account adoption still require separate evidence.

**Adding a house rule begins with one markdown file in `standards/`, then review,
source checks and a tested consumer update.** How and why, in plain language:
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
