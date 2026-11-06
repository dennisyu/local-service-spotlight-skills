---
name: recursive-self-improvement-qa
description: After every task execution, write a meta article with run evidence, compare it with the canonical recipe and prior runs, and propose supported improvements. Publish or change the recipe under existing authorization.
---

# Recursive Self-Improvement QA

**Use this when** you want agents and SOPs that get sharper every run instead of going stale. The loop behind "one page per agent." Step 10 of the Local Service Spotlight method — the skill that improves the other nine.

## Inputs
- The skill/SOP that just ran, and its definitive article — the canonical instructions for the task.
- The actual output of the most recent run, including whatever went sideways.
- Previous meta articles for this skill, if any — the loop's memory.

## The loop
1. **Execute** the canonical task recipe within the authorized scope. Check its trigger, starting state, inputs and prerequisite outputs before following its ordered steps. Record necessary deviations and the reason; do not guess missing instructions.
2. **Write** a meta article for this execution using the [meta-article guidelines](https://blitzmetrics.com/meta-article-prompt/). Link the exact canonical task, recipe/skill revision and run evidence. Include a distinct execution ID, inputs, actions, output, pass/fail checks, deviations, measured effort, lessons and downstream handoff. A failed or partial run still gets a record with that status. The recipe and the run record are separate articles.
3. **Compare** the result with the canonical acceptance criteria and prior meta articles. Flag evidenced gaps in inputs, steps, checks and handoffs. Preserve UNKNOWN when evidence is missing.
4. **Propose** the smallest supported recipe or skill correction for each real defect. Record the decision, version accepted changes and link them to the originating execution. A clean run may need no recipe change.
5. **Close** the run with its written meta article, result and next owner. Publishing the meta article, merging a skill change, changing a live recipe or starting another run follows existing authorization. Keep draft, reviewed, published and verified states distinct; required writing does not authorize those actions.

## The QA checklist — run it every time
- Did the output match what the definitive article promised? Where, exactly, did it differ?
- Where did the agent guess? Determine whether the cause was missing evidence, access, an instruction or a wrong assumption; propose the supported fix.
- What input was missing or wrong at the start? Fix the Inputs section, not just this run.
- Could a worker repeat the run from the SOP alone, without asking you anything? If not, it isn't done.
- Does every produced asset link back to its canonical hub — no content vandalism?
- Is every fact sourced, and every name spelled exactly as the entity is spelled everywhere else?
- Voice check: direct, concrete, second person, no fluff. Cut every sentence that doesn't instruct.
- Did this run produce anything worth productizing — a reusable template, prompt, or standard?

## The Task Library model
The [Task Library](https://local-service-spotlight.github.io/task-library/) maps each repeatable task to its canonical recipe and skill. Link prerequisites and the downstream handoff, with observable acceptance checks. Topic hubs, references, comparisons and supporting stories have separate roles; an opening audit does not turn them into task recipes.
- **Workers** execute the checklist. **Managers** enforce it. **The architect** revises the system when flags repeat.
- One page per task, one URL per page — and every run makes the page better.
- That's how a library compounds instead of rotting: the documentation IS the asset.

## When to run it
- After any of the other nine skills executes — loop the run before you move on. Literal invocation: "Run recursive-self-improvement-qa on the skill that just executed."
- Weekly, on whichever skill produced the most flags.
- Before a sale or audit: the sharpened library is what the buyer is actually paying for.

## Output
- A written meta article for the run, linked to the canonical task/revision and evidence, with a distinct execution ID and accurate publication status.
- A QA punch-list: one fix per flag, each assigned.
- Any supported recipe/skill change, with its review decision, version and actual release status. No defect means no forced rewrite.

## For DealCon — agency owners & acquirers
**If you run an agency:** delivery quality that improves without you is the difference between selling a job and selling a company — a self-improving task library is the asset a buyer pays the multiple for.
**If you buy & sell companies:** in diligence, ask for the target's task library; if the process lives in the founder's head, you're buying a job, not a business. Post-close, install this loop so platform playbooks transfer to every bolt-on and sharpen as they go.
**Your edge:** name the task you've redone from scratch three times this quarter — that's the first skill.md to put in the loop.

## Run in a supported persistent-agent runtime
- **Loop to done:** run this review after every task execution. Done means the meta article is written, acceptance results are evidenced and gaps have a supported next action/owner. Publication or another execution requires the existing authority. Meta writing is part of this run, not an endless series of meta-of-meta executions.
- **Self-verify:** run the QA checklist completely, every time — a skipped line is tomorrow's deviation, and the checklist audits you too.
- **Compound with memory:** prior meta articles are the loop's memory — read them before judging this run, so versions compound (v1.1, v1.2) instead of resetting.
- **Log the run:** count distinct execution IDs per canonical task and reporting period, not drafts, edits, retries or derivative pages. Keep failed/partial and unpublished history with its statuses. Preserve dated public-article volume separately; older examples without IDs cannot establish task frequency.

See `boil-the-ocean.md` for the full operating principles.

## Notes — Dennis's method
- One canonical recipe per task; one meta article per execution. The recipe teaches the work, and accumulated run evidence guides its improvement.
- This is recursive self-improvement applied to marketing ops. The library you installed today should be measurably sharper in 90 days — if it isn't, the loop isn't running.
- Boil the ocean on the checklist. Completeness beats good-enough, because every unwritten rule becomes tomorrow's deviation.
- Standardize, then improve: you can't sharpen a process that changes shape every run. SOP first, loop second.

## Definitive article & pairings
- Reference: https://localservicespotlight.com/meta-articles/ · https://blitzmetrics.com/meta-article-prompt/ · https://local-service-spotlight.github.io/task-library/ · https://blitzmetrics.com/always-boil-the-ocean-because-good-enough-is-not-enough/
- Pairs with: definitive-article-writer → **recursive-self-improvement-qa** → loop back through all nine, starting at personal-brand-strategist

## Operational lessons

These portable lessons describe checks and failure modes, not a report of a
particular account or client. Verify current vendor contracts before use.

- Classify upstream changes by operational effect rather than treating every diff as equivalent. Review additions, corrections, removals and renames against active consumers before release.

- Check source ingestion before calling an empty queue healthy. Reconcile existing applied IDs and backfill unprocessed history when joining an established learning loop.

- A rule needs a canonical source, provenance, scope and testable acceptance criteria. Translate the safe general lesson into public instructions; retain private operational history outside distributed packages.

- Assign file-level writers and identify page generators. Edit the owning source and exercise the normal rebuild, rather than shipping a patch that the next generator will erase.

- For a batch generator, preflight the whole requested batch before output writes: sources, resources, transformations, rendering and the actual destination plan. Resolve physical destinations and check expected parent and target types. An invalid planned item must stop the batch before its first output write.

- Validate catalog entries, standalone explanations, package members and graph links as separate objects. A capability cannot be reliably found or taught from an internal filename alone.

- Derive every visible count from its authoritative artifact. Compare summaries, menus, delivery messages and notices against that source, not against one another.

- A correction becomes propagated only after the exact receiving revision is loaded and tested. A note to port it or a scheduled job definition is not an execution receipt.

- Test checkers with independently selected bad and clean fixtures. Zero findings can mean no check ran; self-comparison cannot detect consistent error. For a generator release, add a reviewer-chosen negative case outside the producer's suite. Preserve contrary findings, fix the cause and retest affected checks on the exact final source and output after corrections.

- Preserve distinctions between absent, unsupported, unreachable, denied, failed and not checked. Separate branches and assertions must produce distinct outcomes.

- Reconcile processes and destinations after timeouts before retrying potentially completed external actions. Use supported serialization, stable run IDs and bounded retries.

- Fail closed if a required guard is absent or cannot run. Preserve interpreter and pipeline exit-status behavior; a skipped checker cannot report success.

- API and plugin writes may replace omitted fields. Read the exact version's contract, preserve required fields and counters, validate one safe case, then re-read the destination.

- Framework-controlled forms can show a success banner while fields remain unchanged. Use supported input mechanisms and re-read the server state.

- A credential arriving, a provisioner completing and a connector being installed are separate from a successful scoped read. Record only the non-secret identity, approved scope and actual probe outcome.

- Treat an expired or resolved warning as a source-state correction. Update its owning record with evidence; a contradictory note elsewhere leaves the original failure active.

- Check current endpoint semantics and the caller's approved access before acting on vendor notices. Do not publish workspace keys, plan allowances, account identities or internal routes in reusable skills.

- Reject plausible placeholder prose and unsupported positioning. Missing strategy stays unknown; label synthetic practice and do not present it as a real outcome.

- Assert inventory and bucket completeness explicitly. A missing item can vanish from a report without causing an error unless the input/output totals are reconciled.

- Before declaring content inaccessible, inspect actual rendered and source behavior, status and permissions. An empty text extraction or a cross-origin request failure is not proof of absence.

- Before invoking `--help`, verify that the script implements it without side effects. Test invalid flags and dry-run in an isolated fixture.

- Keep one outcome owner and an existing task record for unresolved exceptions. Authorized rescue work may continue, but silence cannot grant new privileges or clear an explicit hold.

- Inspect the complete result path after a correction: source, generated artifact, final public destination, download or install route, activation, message and any scheduled firing. Preserve independent review and unverified limits.

Apply the maintained [Learn, Do, Teach method](https://github.com/dennisyu/local-service-spotlight-skills/blob/main/docs/agent-setup/LEARN-DO-TEACH.md)
and [acceptance checks](https://github.com/dennisyu/local-service-spotlight-skills/blob/main/ACCEPTANCE.md).

## Shared rules — harness layer (referenced, not inlined)

This skill operates under the fleet's shared-rule appendix, which lives ONCE at the
harness layer instead of being pasted into this file:

- **Appendix file:** the shared-rule appendix (35 blocks) — canonical
  blocks live in this repo's `standards/` directory; the harness carries the
  appendix as one file generated from them, and standalone exports inline it
  at packaging time (`sync_shared_rules.py --export`). It comprises fleet standards,
  coordination/ownership rules, QA gates, and field lessons that apply pack-wide).
- **How to use it:** the appendix is part of this skill's instructions. Read the
  blocks relevant to the task at hand before acting; where a block sets a gate,
  threshold, filing rule, or prohibition, it binds exactly as if it were printed here.
- **Precedence:** if a core instruction above and an appendix block conflict, the
  more specific instruction wins; if still tied, the appendix's QA/safety gate wins
  and the conflict is noted in the run's receipt.
- **What changed:** nothing about the rules — only their address. The core above is
  the recipe; the appendix is the standing orders every recipe runs under.
