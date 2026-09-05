# Public first-result bootstrap contract

**Status: proposal.** This reference and its offline validator are not an
installer, a deployed endpoint, or evidence that any member's agent is running.

Pointing an assistant at one public URL should lead to a useful first draft.
It does not grant access to a person's inbox, memory, accounts, budget, or files.
An assistant must follow its host's instructions and the user's permissions;
instructions retrieved from a website are reference material, not higher-priority
commands.

## Start with a result, not a configuration project

The member's first step is to provide their business website and desired result.
For example, paste this into an assistant that can read public web pages:

> Read https://localservicespotlight.com/install/ as a reference for the Local
> Service Spotlight methods. My business website is [URL]. My goal is [result].
> Use public sources only to draft a proof inventory: what we do, who we serve,
> which claims have a supporting URL, what remains unknown, and one next action
> that bridges the gap to my goal. Cite the pages you actually read. If you cannot
> open a page or use a tool, say so and tell me the smallest next step. Do not
> install anything, request credentials, publish, send, spend, change access, or
> create a schedule. Show the draft here; save it locally only if that is already
> allowed in this workspace.

This small draft is not the complete personal-brand audit or proof that a skill
activated. The full audit still follows its own evidence and deliverable checks.
If the surface cannot browse, ask the member to supply the relevant public page
text. If no reliable evidence is accessible, return an explicit gap, not a made-up
inventory. Do not require a new account connection just to explain the first step.

## The five-step path

| Step | What the member gets | Evidence to keep |
|---|---|---|
| 1. SCAN | A public proof inventory and identity check | Sources actually read; date; unknowns |
| 2. AIM | A clarified goal, audience, offer, and measure | The member's correction or approval |
| 3. MAP | The gap, then a small owned plan | Task, skill, output, measure, and approval boundary |
| 4. INSTALL | Only the methods and connections that plan needs | Named environment, installed revision, fresh-task test |
| 5. RUN | An approved cadence with a useful output | Run time, inputs, result, next action, failure, rollback |

The Content Factory supplies the production path inside this sequence: produce,
process, post, and promote. Posting, promotion, account changes, and paid tools
remain behind their own scoped authorization. A schedule is not evidence that
any of those steps happened.

## Reuse the existing homes

This proposal adds no competing public hub or skill registry.

| Existing source | Role |
|---|---|
| [Install guide](https://localservicespotlight.com/install/) | Member-facing entry and supported setup instructions |
| [This repository](https://github.com/dennisyu/local-service-spotlight-skills) | Reviewed skill source; `lss-everything` bundle |
| [New agents start here](https://blitzmetrics.com/new-agents-start-here/) | Public operating-method reference |
| [One shared brain](https://blitzmetrics.com/give-your-ai-team-one-shared-brain/) | Public explanation of shared memory |
| [Shared-memory setup](https://blitzmetrics.com/set-up-cross-agent-shared-memory/) | Implementation reference, not somebody else's private memory |
| [Propagation guide](../HOW-KNOWLEDGE-PROPAGATES.md) | How learned rules reach distributed skills and checks |
| [Update contract](../skills/skill-registry/references/update-contract.md) | Source revision, canary, acceptance, fleet update, and rollback |

These are pointers, not a promise that every assistant can fetch every page.
Verify anonymous retrieval on each supported surface and provide an accurate
fallback when robots rules, authentication, or a missing tool prevent it. Do not
treat a crawler's cached page as the current install instructions.

## Four different things travel differently

| Layer | Source and transfer | What must not be inferred |
|---|---|---|
| Public method | Canonical public pages and reviewed skill source | A URL is not installation or authorization |
| Organization memory | A separately permissioned, owner-controlled store | Public methods never contain private client notes or credentials |
| Working context | A task's allowed evidence, selected for its audience | One agent's private context is not automatically another's |
| Runtime | The host's supported tools and approved schedule | The same prompt does not give every model the same capabilities |

Keep secrets in private runtime configuration, outside manifests and skill files.
Reuse an already authorized connector when it covers the task. Stop for the
smallest missing scope instead of asking for broad access. Public templates may
describe memory fields; they must not include a member's actual private records.

### Memory transfer and update design

1. **Capture once at the owner.** A record has a stable ID, source reference,
   audience, sensitivity, author/owner, content hash, and checked/expiry times.
   Duplicate IDs with different content are conflicts, not an invitation to
   silently overwrite. Preserve both provenances for owner resolution.
2. **Select for the destination.** Compile only records permitted for that
   audience and task. A public pack must contain public material only; no private
   path, tenant identifier, private receipt URL, or credential belongs in it.
3. **Validate before replacing.** Recompute hashes from the current source,
   check unique IDs, resolve stale/conflicting records, then validate the newly
   compiled pack. A previously passing pack is not proof of a fresh rebuild.
4. **Write with a recovery path.** Keep the last accepted revision, stage the new
   pack, and replace it only after checks pass. Serialize writers for each
   destination. Do not push a failed or partial rebuild to another provider.
5. **Verify at the consumer.** A fresh task names the source revision and produces
   the expected result. Keep source acceptance, delivery, activation, and a
   scheduled observation as separate receipts.

This is an adapter contract, not a new universal memory store. Each host still
needs its supported connection and the user's approval. Changing the source of a
rule does not prove that all already-running tasks have reloaded it.

## Proposed release metadata and offline check

[`schemas/public-bootstrap.schema.json`](../schemas/public-bootstrap.schema.json)
defines a public-only metadata envelope. A maintainer can use it to describe a
candidate without overstating deployment:

- `source`: canonical repository, exact commit, stable bundle and skill names,
  and the previous accepted commit for rollback.
- `permissions`: a **maximum bootstrap scope**, not a grant. Public reading and
  drafting remain subject to the user and host; publishing, sending, spending,
  changing access, and creating schedules are explicitly excluded.
- `memory.sources`: public reference IDs, URLs, public access/sensitivity,
  freshness window, anonymous read-back status, and SHA-256.
- `adapters`: the actual supported surface, setup steps, activation prompt,
  observed state, and a sanitized public receipt pointer. A receipt must match
  the claimed state and source commit. Do not publish private account IDs.

The envelope intentionally cannot describe private memory delivery. Maintain
private approvals and private operational receipts in the authorized work system;
publish only a separately reviewed, sanitized public example if appropriate.

```bash
python3 -m pip install -r requirements-validation.txt
python3 scripts/validate_public_bootstrap.py path/to/candidate.json
python3 scripts/validate_public_bootstrap.py path/to/candidate.json --require-ready
python3 -m unittest discover -s tests -p 'test_public_bootstrap.py' -v
```

Exit `0` means metadata passed the requested checks; `1` means invalid metadata;
`2` means invalid command arguments; `3` means `--require-ready` found missing
read-back, fresh-session activation, expiry, or rollback evidence. An expired
reference blocks readiness but does not make an honest candidate structurally
invalid. Errors print field paths and keywords, not field values. Timestamps must
include a timezone offset; lowercase RFC3339 `t`/`z` is supported, but leap-second
timestamps are rejected with a field error rather than silently normalized.

The checked-in fixture under `tests/fixtures/` uses `example.com`, invented hashes,
and a frozen January 2026 test clock. It is **not** a release manifest. Its expiry
is intentional, so time-dependent tests stay deterministic without republishing
synthetic dates as current evidence.

### What the validator does not prove

The checker makes no network requests and performs no installation, account test,
sync, or publication. It cannot establish whether a URL is really public, verify
DNS or redirect targets, recompute remote content hashes, authenticate a receipt,
prove a commit contains a skill, or detect private information in free text.
Its URL screen rejects credentials, query strings, IP literals, local hostnames,
and common private work-document rails. That screen is **not** an SSRF guard or a
content-classification system. Any future fetcher needs its own approved network
boundary, redirect and DNS handling, size limits, and human review of public text.

`ready_for_independent_review` therefore means the claimed metadata is internally
consistent, not that the release is accepted. Before a public rollout, a reviewer
must inspect sources and sanitized receipts, confirm the commit and named skills,
check the first-result path in a fresh supported session, and apply
[ACCEPTANCE.md](../ACCEPTANCE.md). This proposal does not activate any adapter.

## Keep the implementation small

Maintainers can first validate a candidate locally, review it in a pull request,
and test one supported surface. Only then decide whether the existing install
page should link to a real manifest at its existing home. Do not create another
hub, promise universal installation, or enable a scheduler to make a draft look
finished. Rollback is the prior accepted revision; disable the affected adapter
and retain its failure receipt if a fresh-session test fails.
