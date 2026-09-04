---
name: client-relationship-cadence
description: The canonical SOP for recurring client-relationship agents that are NOT a scored metrics loop — monthly/weekly jobs whose real work is checking for replies/approvals since last run, doing exactly one safe incremental improvement, and keeping a human relationship warm without spamming it. Use this instead of weekly-brand-maa.md when the entity isn't being scored against a Personal Brand Score or SOW milestones — it's a person or small client you're quietly maintaining momentum with. Each scheduled agent passes a PARAMETERS block and follows this file.
author: Dennis Yu — Local Service Spotlight
references:
  - weekly-brand-maa.md (the sibling SOP for scored metrics-loop agents — use that one instead if the entity has a Personal Brand Score, SOW targets, or a metrics baseline to track)
  - boil-the-ocean.md
  - recursive-self-improvement-qa.md
  - https://blitzmetrics.com/meta-article-prompt/
---

# Client Relationship Cadence — canonical SOP

**Use this when** a scheduled agent's real job is relationship maintenance, not metrics tracking: a monthly brand-refresh check-in on a friend/peer (no scored rubric), or a client project still mid-build where you're waiting on THEM (logins, approvals, content sign-off) between runs. The two current examples are `igor-ivitskiy-monthly-brand-refresh` (monthly relationship refresh + content update) and `junks-above-daily-progress` (weekly client-project cadence pending a handoff meeting) — different cadences, same shape. Never improvise the method — if something's missing, flag it and propose the fix back into this file (see `recursive-self-improvement-qa`).

## PARAMETERS the caller provides
```
entity_name:        # the person or client
context_docs:       # absolute path(s) to read FIRST — canonical brief, project plan, "easy checklist", baseline notes
comms_channels:      # where to check for replies/approvals since last run — email thread id/search terms, Basecamp project + thread URLs
approval_gate:       # what specifically needs their sign-off before it goes live (e.g. "draft posts 498/499", "GoDaddy login", "Instagram photo permission") and what to do the moment each one arrives
safe_increment_policy: # what "one incremental improvement needing no new access" is allowed to touch this run (e.g. repurpose existing public material into a draft post, fix one Yoast title, tidy one QA item) — and what's explicitly off-limits (never enter passwords into a login form, never publish new content without review, never permanently delete data)
notify_rule:         # when to post/reply vs. stay quiet (e.g. "only if something material changed"; "one friendly nudge if no checklist progress in 7+ days AND no nudge sent in the past 14 days")
state_file:          # where the running "state of the project" note lives — update it every run, don't just append noise
voice:               # tone to write in (e.g. entity's own casual voice for client-facing drafts; Dennis's direct voice for outreach email)
```

## STEP 0 — Load context
Read every file in `context_docs` (there is no memory between runs — the docs + the last state note ARE the memory). Read the current `state_file` if it exists to see what happened last run.

## STEP 1 — Check for movement since last run
Search `comms_channels` (Gmail thread, Basecamp project/thread) for anything new: replies, approvals, completed checklist items, sent credentials. For each item found:
- **An approval arrived** → execute exactly what was approved (e.g. publish the specific posts that were greenlit), nothing more.
- **Credentials arrived that violate `safe_increment_policy`** (e.g. a password sent in plain text) → do NOT use them to log in. Flag it to Dennis as top priority instead. Never enter a password into a login form on the entity's behalf.
- **Nothing new** → say so plainly and move to Step 2.

## STEP 2 — One safe increment
Do exactly ONE incremental improvement that fits `safe_increment_policy` and needs no new access — draft-only for anything public-facing unless it was already pre-approved. Prefer real, repurposable material (the entity's own site, public press, existing reviews) over generic filler. Then QA whatever you touched (fetch the live pages, check nav/contact info/schema still parse) before moving on.

## STEP 2.5 — Put the ask where it can be tracked, and OWN the chase

**Standing since August 1, 2026 (Dennis).** *"I want it so there's no follow-up on me."* An ask that lives in an email thread has no owner, no state and no due date — it survives only as long as someone remembers it. Two of these agents had been staging email drafts for months and calling that follow-up. It isn't; it's a notification.

**Every ask goes in the client's Basecamp project as a to-do, assigned to the person who has to do it, including the client.** Not a message, not a bullet in a status post, not an email paragraph. A to-do has an owner and a state; everything else is prose.

- **Give the client access on day one.** A client-visible to-do that the client cannot see is worse than no to-do, because it looks done from the inside. Convention: project named `Google Knowledge Panel: <Name>`, tools = message board + todoset, internal team + the client as a **Client** (not Team), one client-visible list for their asks and one internal list for ours. Basecamp gotchas are in [[basecamp-lexxy-editor-gotcha]] — in particular, client visibility on a message cannot be set until the project actually has a client, so **add the client before you post**.
- **Assign to the real owner, not the nearest human.** Rotating a password on the *client's own site* is the client's to-do, not ops'. A PHP fix is a developer's, not a VA's. Routing work to whoever is closest is how one person becomes the bottleneck for every client.
- **When you must route through ops, make it a routing job, not a research job.** Title it with the verb and the time cost — "Route X to someone with file access (2 min)" — and carry the full spec so the person who receives it needs no context from anyone.
- **Bundle defects by owner, not by discovery date.** Four separate small fixes in one codebase is one trip for one person, not four to-dos on four days.

**Then chase it.** The next run re-reads every open to-do and decides whether reality moved, **by checking the artifact rather than the reply** — an unanswered to-do whose work is visibly done should be closed, not nudged. For what is genuinely still open, post one consolidated comment on the to-do and escalate on a written schedule: run 1 friendly nudge · run 2 nudge naming the cost in their terms · run 3 hand it to the human with the exact ask. **Write the next escalation date into `state_file`** — the next run is a different session with no memory of the promise, so an undated intention is not a mechanism (see the twelve-day Christine gap in [[blocked-work-becomes-muzamil-todo]]).

Escalating to the principal is the *last* rung, not the first. If a run ends with "Dennis needs to chase this," ask first whether an agent could have checked it, an owner could have been named, or a date could have been set instead.

## STEP 3 — Notify per `notify_rule`
Most runs should NOT generate a client-facing message — only post/reply when something material happened (an approval was executed, a real update shipped) or the specific nudge condition in `notify_rule` is met. Silence is a valid, correct outcome for this step; don't manufacture an update to justify the run. Internal-only notes (to Dennis) can be more frequent than client-facing ones.

## STEP 4 — Update state and log
Overwrite/update `state_file` with a short "state of the project" summary: what's approved, what's still pending from the entity, what was shipped this run, what the next milestone is. This is what the NEXT run (and any human who opens the file) reads first — keep it current, not additive noise.

## STEP 5 — Report back
Tell Dennis, concisely: what moved, what you did, what's still waiting on the entity, and anything ambiguous or broken (don't guess silently — flag it). Per the standing continuous-enhancement policy: act first, then inform; never silently change things without reporting exactly what changed.

## NON-NEGOTIABLES
- Never enter a password into any login form, even one the entity sent you directly.
- Never publish new client-facing content without the approval gate being satisfied, unless the run's own policy explicitly pre-approves a category of change.
- Never spam the relationship — an unnecessary update is worse than no update.
- Every fact you report has a verifiable source (a real reply, a real page fetch) — never fabricate progress.

## Currently called by
- `igor-ivitskiy-monthly-brand-refresh` — monthly cadence, comms_channels = Gmail thread `19929d6921b94285`, approval_gate = n/a (BlitzMetrics-owned article, no client sign-off needed, but WP auth is currently broken — see `blitzmetrics-app-password-broken` — use the Chrome+nonce method), safe_increment_policy = append a dated Update section, never rewrite the original narrative.
- `junks-above-daily-progress` — weekly cadence until handoff meeting, comms_channels = Gmail thread "this is Dennis Yu" with uhhroland@gmail.com + Basecamp project 47842096, approval_gate = the "Easy Checklist for Roland" items (hosting login, admin-email confirm, Google access, Instagram permission, public email confirm) plus the two draft posts (498/499), safe_increment_policy = one repurposed draft or one QA fix per run, no visual overhaul, no publishing without Roland's OK, never enter his GoDaddy password.

## See also
`weekly-brand-maa.md` (the scored-metrics sibling SOP) · `boil-the-ocean.md` (operating principles) · `recursive-self-improvement-qa.md` (loop this run before moving on — propose fixes back into this file when you had to guess)

## Learned in the field

*Appended automatically by the self-improvement loop (Skill-Learnings/): dated lessons from real runs. Newest at the bottom.*

<!-- learning:2026-07-27-dont-retro-charge-silence-when-bootstrapping-a-ledger -->
**July 27, 2026** (from: cxotalk-weekly-maa run)

### Bootstrapping an ASK-LEDGER retroactively: don't retro-charge silence

STEP 6.7 has required `ASK-LEDGER.md` since July 24, 2026, but this client's ledger didn't
exist and had to be back-filled from three prior reports. Two judgment calls keep a
back-filled counter honest, and should be the default whenever a ledger is created late:

1. **Start counting at the first run that had the SOP's discipline available**, not at the
   ask's original date. Charging someone four misses for a period when nobody was tracking
   misses produces a number that feels like an accusation and can't be defended.
2. **Collapse bunched runs into one window.** This task fired 7/17, 7/19 and 7/20 — three
   times in four days. Counting each as a separate miss would have put a client at Rung 4
   ("recommend off-channel contact") for going quiet over a weekend. One window, one count.

The payoff of doing it honestly: the finished ledger showed that **two of the three
highest-count asks were ours or ops', not the client's** — the delivery-channel param and a
GA4/GSC request nobody had chased. A ledger that inflates client counts hides our own drift.
Learned July 27, 2026.

<!-- learning:2026-08-01-admin-form-save-is-not-a-save -->
**August 1, 2026** (from: igor-ivitskiy-monthly-brand-refresh)

**A WordPress admin form that returns "Post updated" has not necessarily saved your fields — re-read them.**

Creating a KG Entity record on blitzmetrics.com, the run set 7 ACF fields via JS, clicked
Publish, and got a clean `Post updated.` notice with a real post ID. Every text, url and
textarea field had silently discarded its value. Only the `true_false` toggles persisted.
Had the run trusted the success notice, it would have reported a populated registry entry
that was in fact blank — the same failure the other 34 records in that registry already had.

Adopt as standing practice:

1. **After any admin-form write, re-read the field values from the reloaded form** (or the
   public render), never the success notice. `Post updated`, HTTP 200 and a returned post ID
   all describe the *request*, not the *data*. Same rule as `DELETE /elementor/v1/cache`
   returning 200 while the page still serves stale HTML.
2. **When one field type saves and another does not, suspect the field-key contract, not
   your input.** ACF resolves values by field key and requires keys prefixed `field_`. A
   locally-registered group using bare names (`data-key="kgmid"`) fails `acf_update_value()`
   for value-bearing types. Read `data-key` on `.acf-field` before blaming the form fill.
3. **A silent write failure that predates you is a finding, not a footnote.** The empty
   fields explained why 32 of 35 entity records were blank — a registry that had looked
   populated because rows existed. Count the rows that carry *data*, not the rows.
4. **Publish the defect in the meta article.** It converts a blocked task into the most
   useful paragraph on the page, and it is how the next person finds the one-line fix.

<!-- learning:2026-08-01-asks-belong-in-a-tracker-with-an-owner -->
**August 1, 2026** (from: igor-ivitskiy-monthly-brand-refresh)

**An ask staged in an email draft is a notification, not follow-up. Put it in the tracker, assign an owner, and chase it yourself.**

Dennis, August 1, 2026: *"I want it so there's no follow-up on me... all the operations and
follow-up and messaging and communication should be handled by agents."* The Igor run had done
what these agents always did — staged a beautiful Gmail draft carrying three client asks — and
that pattern quietly makes the principal the routing layer for every client.

Rules to adopt:

1. **Every ask becomes a to-do with an owner**, in the client's project. Prose in a message,
   a bullet in a status post, or a paragraph in an email all share the same defect: no owner,
   no state, no date. Only a to-do can be closed.
2. **Invite the client before you write to them.** A client-visible list the client cannot
   reach looks complete from the inside — the worst failure mode, because it reports green.
   On Basecamp, client visibility on a message literally cannot be toggled until the project
   has a client, so the order is: enable clients → add them → post → flip visibility.
3. **Assign to the true owner, not the nearest human.** Rotating a password on the *client's
   own* site is the client's job. A PHP fix is a developer's, not a VA's. Defaulting to
   "assign it to ops" is exactly how one person becomes everyone's bottleneck — the thing
   this rule exists to prevent.
4. **Where routing through ops is unavoidable, ship a routing job, not a research job.** Put
   the verb and the time cost in the title ("Route X to someone with file access — 2 min") and
   carry the whole spec, so the receiver needs no context from anyone.
5. **Bundle by owner, not by discovery date.** Four defects in one codebase is one trip.
6. **Chase by checking the artifact, not the reply.** Next run, re-read every open to-do and
   verify against reality — did the page change, did the score move — then close what is done
   and escalate what is not, on a date written into the state file. The next run has no memory
   of your intention; only the date survives.

<!-- learning:2026-08-02-automate-for-the-cohort-not-the-pilot -->
**August 2, 2026** (from: somba-skill-weekly-update)

**August 2, 2026** (from: somba-skill-weekly-update)

We had automated weekly delivery for one member out of roughly a hundred, and left the other
ninety-nine on a hand-written page that had not been updated in two weeks.

Dorine Holman was an early pilot. Building her a personal mirror folder, a personal checker
script, a line in the propagator, and a dedicated Monday job was the right way to prove the
idea worked. What went wrong is that it stayed that way after it worked. An audit found her
folder holds **21 skill files, every one byte-identical** to the shared source — a full private
copy of something everybody already receives.

Meanwhile the surface all 100 members actually read carried news items typed by hand into
`patch_news.py`, with a hard-coded date string frozen at 20 Jul. So the effort was exactly
inverted: **automated and current for one person, manual and stale for everyone.**

Dennis's question was the right one — "are we doing something special for her? We should do
things in a central, solvable way and less one-offs." The rewrite serves everyone through the
dashboard and Agent Library they already have. Same work, roughly a hundred times the audience.

Three things to carry forward:

**A pilot has an exit condition, and it should be written down when the pilot starts.** "Prove
it with one member, then generalise" is a good plan. "Prove it with one member" alone becomes
permanent infrastructure with an audience of one, and nobody notices because it keeps working.
When you build for a single person to test something, write the graduation step into the job
itself.

**Count the audience of every automation you own.** If a scheduled job serves one member of a
cohort, that is either a deliberate bespoke engagement or an un-generalised pilot. Both are
fine; not knowing which is not. The tell here was cheap: one folder, 21 identical files.

**Check the direction of the asymmetry.** The individual got the generated, always-current
version and the group got the hand-maintained one. That is worth looking for elsewhere — the
effort usually flows to whoever asked most recently, not to wherever it does the most good.

Guard added: the rewritten job now says plainly that if something is worth telling one member it
is worth telling all of them, and that no member-specific branch may be added to the pipeline.
The one-off that remains — Dorine's mirror folder — is left in place on purpose, because
deleting a real person's synced files is a decision for a human, not a cleanup. But it is
frozen: not extended, and no second member's mirror gets created beside it.

<!-- shared-rule:silent-media-playback:start -->
## Silent media playback

- Never let audio from browser, video, audio, presentation, or application testing play through the user's speakers unless the user explicitly asks to hear it.
- Before starting any media playback, mute the player and set its volume to zero. Keep it muted for the full test, including replays, reloads, new tabs, and alternate players.
- Apply this rule to the primary agent and every delegated agent. Include the mute requirement whenever work that may involve media playback is delegated.
- If the mute state cannot be controlled and verified before playback, do not start playback. Use metadata, captions, transcripts, frames, screenshots, network state, or player state instead.
- Only unmute when the user explicitly requests audible playback in the current task.
<!-- shared-rule:silent-media-playback:end -->

<!-- shared-rule:agents-draft-humans-send:start -->
## Agents draft; a human sends and publishes

- **An agent may write anything and send nothing.** Email, DMs, social posts, client
  messages, public pages — staged and ready, never dispatched.
- **Stage it so approving is one click**, not one more round of work: the full text, the
  recipient, the subject, and where it will appear.
- This is a security control, not a confidence rating. It holds even when the draft is
  obviously correct, because the failure it prevents is the one nobody predicted.
- It is the boundary on `be-proactive-see-it-through`: act freely on reversible work,
  stop at anything that reaches another person or the public.
<!-- shared-rule:agents-draft-humans-send:end -->

<!-- shared-rule:ask-blocking-questions-up-front:start -->
## Ask every blocking question up front

- **Front-load every question and every missing access into the planning step**, before
  the long work starts. The person who briefed you intends to walk away; a question
  raised at minute ninety costs them the whole ninety minutes.
- **Do not guess to avoid asking.** A guess that turns out wrong is discovered at the end,
  when it is most expensive to undo.
- Open every plan with an explicit **open questions and missing access** block. If the
  list is empty, say so — that is information too.
- Once the questions are answered, work continuously to the end rather than stopping to
  check in on things you could have decided.
<!-- shared-rule:ask-blocking-questions-up-front:end -->

<!-- shared-rule:assign-work-to-a-function:start -->
## Assign work to a function, not a person

- **Every task is owned by a function** — web, content, analytics, client success — and
  people sit inside functions. People join, leave and go on holiday; the function does not.
- **Escalate to a function too.** "I told Muzamil" is not an escalation if Muzamil is
  away; "escalated to the web function" is.
- A function with exactly one person in it is still a function. Name it that way, so the
  second person changes nothing.
- Work assigned to a named individual and nowhere else is work that silently stops when
  that individual does.
<!-- shared-rule:assign-work-to-a-function:end -->

<!-- shared-rule:be-proactive-see-it-through:start -->
## Be proactive and see it through

- **When you find something broken, fix it.** Do not file it, mention it in passing, or
  wait to be asked. If it is outside what you can fix, escalate it to the function that
  owns it, by name, with what you found.
- **You do not need permission for reversible work.** Do it, then report exactly what you
  did so it can be adjusted. Asking first for everything makes an agent slower than doing
  the work by hand.
- **Reversible is the line, not confidence.** Sending a message, publishing to the public,
  spending money, and deleting data stay behind an explicit approval — see
  `agents-draft-humans-send`. Everything short of that, act.
- Report what you changed in enough detail that undoing it is a one-line instruction.
<!-- shared-rule:be-proactive-see-it-through:end -->

<!-- shared-rule:capture-what-you-learn:start -->
## Capture what you learn as a standard, in the same session

- **A rule that lives only in an article, a chat message, a call recording, or your
  context window is a rule the next agent will break.** That is not a prediction. The
  black-button rule was published, illustrated, and given an enforcement plugin on
  17 May 2026, and on 15 August 2026 an agent holding the entire skill pack in context
  shipped a black button. The rule was never in `standards/`, so it never reached the
  skills, so it was not there to be read.
- When anyone — the client, the account owner, an audit, or your own failure — states a
  rule that should hold next time, **your job is not to remember it. It is to write
  `standards/<slug>.md` before the session ends.** Memory does not survive a session
  boundary. A file does.
- Scaffold it in one command, which forces every field including where the rule came
  from:

  ```bash
  python3 scripts/new_standard.py "no autoplay with sound" \
    --from "Dennis Yu, Cowork session, 2026-08-16" --applies-to published-html
  ```

- Then write the rule, run `python3 scripts/sync_shared_rules.py`, and open the pull
  request. The sync copies the rule into `AGENTS.md` and every distributed `SKILL.md`,
  so it reaches every agent and every member who installed the pack. Nobody has to be
  told about it.
- **Give the rule a machine check whenever one is honest.** A `checks` block in the
  header compiles straight into the live fleet sweep, so a violation on a published page
  is caught by a schedule instead of by a person noticing. Every check must carry
  passing and failing examples — a pattern that matches nothing reports a clean site
  forever, which is worse than no check at all.
- **Where a machine check would be dishonest, say so and leave `checks` out.** Judgement
  rules are still rules; they are enforced by being read pre-flight, and pretending a
  regex covers them hides the fact that nothing does.
- **Provenance is required, not decoration.** `captured_from` is how the team sees which
  channels leak. If dozens of recorded calls have produced no standards, those calls are
  not being captured, and that is visible at a glance instead of being a suspicion.
- **When a new rule contradicts an existing one, resolve it in the file and say so
  out loud.** Two standards that disagree are worse than one that is wrong, because
  every agent that reads both will pick whichever it happened to see last. Write the
  reconciliation into the newer rule and flag it to the account owner for confirmation.
- The order is Checklist → Content → Software. Write the checkable rule first, publish
  the article that teaches it second, and let the sweep be generated from the rule
  rather than hand-written beside it. Writing the article first is how rules get lost:
  the article is the artifact everyone can see, so it feels finished, and the
  enforceable form never gets written.
<!-- shared-rule:capture-what-you-learn:end -->

<!-- shared-rule:keep-the-system-of-record-outside-the-model:start -->
## Keep the system of record outside any one model

- **Standards, SOPs, metadata and completed work live in files and repositories we own**,
  not inside one vendor's memory, project or chat history.
- **The test:** if the model changed tomorrow, could a new one pick up every piece of work
  in progress from the artifacts alone? If not, something important is stored in the wrong
  place.
- **Write it down where it can be read by anything.** Plain markdown, plain JSON, in a
  repository — not a proprietary format tied to one product.
- This is also why rules are copied into distributed skills rather than linked: the copy
  survives being separated from the system that made it.
<!-- shared-rule:keep-the-system-of-record-outside-the-model:end -->

<!-- shared-rule:lead-with-a-visual-executive-summary:start -->
## Every deliverable leads with a visual executive summary

- **Page one answers the question**, for someone who will read only page one. The most
  important and least obvious findings, up front.
- **Interesting and non-obvious, not a restatement.** A summary that repeats what the
  reader already assumed has told them nothing; lead with what would change their mind.
- **Use colour, diagrams and tables to carry the point.** A wall of text on page one is a
  failure of the deliverable, not a style preference.
- Depth still matters behind it — a substantial analysis runs long. The summary earns the
  reader's attention for the rest; it does not replace it.
<!-- shared-rule:lead-with-a-visual-executive-summary:end -->

<!-- shared-rule:learn-do-teach:start -->
## Learn it, do it, then teach it

- **Read the standard before you touch the work.** Skipping to doing produces output that
  looks right and is wrong in ways the person reviewing it has to find for you.
- **Then do it,** all the way to a verified artifact.
- **Then teach it** — write the run up so the next agent inherits what you learned. That
  write-up is what turns one person's lesson into everyone's default, and it is the whole
  reason `standards/` exists.
- The order is not a preference. A rule taught before it is understood is repeated
  without judgement; a rule learned and then taught survives contact with a case it did
  not anticipate.
<!-- shared-rule:learn-do-teach:end -->

<!-- shared-rule:no-flattery-tell-it-straight:start -->
## No flattery — tell it straight

- **Do not open with praise, and do not pad findings with reassurance.** The value of a
  report is the part that is uncomfortable; softening it destroys the only reason to read
  it.
- **Every claim is proof-driven** — name the URL, the number, the date, the source. "This
  looks great" is not a finding; "the sameAs target returns 404" is.
- **Say what is broken before what is working**, and be specific about how bad it is.
- Being wrong is recoverable. Being agreeable and wrong is not, because nobody checks
  the agreeable answer.
<!-- shared-rule:no-flattery-tell-it-straight:end -->

<!-- shared-rule:pre-audit-before-the-client-does:start -->
## Audit our own work before anyone else can

- **Assume an outside expert will audit everything you ship**, and build so that audit
  comes back clean. That assumption is what makes the work honest rather than merely
  presentable.
- **Run the adversarial pass yourself, before delivery.** Find the broken thing while it
  is still cheap and while finding it is a credit rather than a defence.
- **Give the client the same auditing tools you use.** Work that only survives because
  nobody looked closely is not work worth selling.
- Ship the audit result alongside the deliverable, including what it found.
<!-- shared-rule:pre-audit-before-the-client-does:end -->

<!-- shared-rule:process-real-content-never-generate:start -->
## Process real content; never generate it

- **Every published piece starts from something real** — a recording, a call, a job
  actually done, a person actually speaking. AI processes that raw material; it does not
  invent the material.
- **The provenance must survive to the page.** Link the video, embed the clip, name the
  person, cite the date. A reader — and a language model reading on their behalf — should
  be able to trace the claim back to the moment it was said.
- **Repurpose one source across every surface** rather than generating a fresh piece per
  channel. The article, the short, the profile post and the email come from the same
  recording.
- An article with no traceable source is indistinguishable from an invented one, and will
  eventually be treated as invented.
- The sweep looks for a source artifact — an embed, a captioned figure, or an attributed
  quote — and reports rather than blocks, because a well-sourced piece can still fail the
  proxy. Treat a hit as "check where this came from", not as proof it was generated.
<!-- shared-rule:process-real-content-never-generate:end -->

<!-- shared-rule:qa-from-a-different-context-window:start -->
## QA comes from a different context window

- **Self-QA is necessary and never sufficient.** The agent that made a mistake is the
  agent least able to see it, because the reasoning that produced the mistake is still
  in its context.
- **Audit work with a second agent started fresh**, given the artifact and the standard
  but not the first agent's reasoning. Delegate it explicitly rather than re-reading your
  own output.
- The auditor's job is to **refute**, not to confirm. Brief it that way.
- This applies to your own work most of all. If you cannot spawn an auditor, say the work
  is unaudited rather than implying it was checked.
<!-- shared-rule:qa-from-a-different-context-window:end -->

<!-- shared-rule:report-business-impact-not-volume:start -->
## Report business impact, never volume

- **Count outcomes, not output.** Posts published, words written and tasks closed are
  activity. Calls, booked jobs, leads and revenue are results.
- **Trace the chain and show it**: published thing → ranking or traffic → call or lead →
  booked job → revenue. Where the chain breaks, say where it breaks rather than reporting
  the last link that looked good.
- **Impressions and clicks are context, not the headline.** Never lead with them.
- If the business impact cannot be measured yet, say that plainly and fix the measurement
  first — see `analytics-on-every-page`.
<!-- shared-rule:report-business-impact-not-volume:end -->

<!-- shared-rule:verify-by-opening-the-live-artifact:start -->
## Verify by opening the live artifact

- **"I did it" is not evidence. The artifact is.** Before reporting any work complete,
  fetch the live URL, open the file, or query the API and confirm the change is actually
  there. An agent that has been caught reporting published articles onto a site with no
  articles has burned more trust than the task was worth.
- **Check the thing a user would see, not the thing you wrote.** A database row is not a
  published page — caches, builders and permissions all sit in between. Fetch the public
  URL as an anonymous visitor.
- **A page that could not be fetched has not been verified.** Report it as unverified,
  never as done.
- Quote the evidence in the report: the URL, the status code, and the string you found.
<!-- shared-rule:verify-by-opening-the-live-artifact:end -->

<!-- shared-rule:basecamp-updates-stay-in-basecamp:start -->
## Basecamp updates stay in Basecamp

- Never use Gmail Reply, Reply All, Forward, Send, or Draft to
  `notifications@app.basecamp.com` or `notifications@3.basecamp.com`. Those
  visible From addresses are notification infrastructure, not destinations.
- Post the update in the exact existing Basecamp thread through an authorized
  Basecamp connector, API, or the Basecamp UI. The company delivery rail is
  Basecamp itself, so do not substitute a per-message
  `*@replies.app.basecamp.com` email token even when one is present.
- Before any Gmail mutation, inspect the resolved To and Cc fields. If either
  contains a generic Basecamp notifications address, stop without creating or
  sending the message.
- Changing the Gmail From identity does not repair this failure. In the
  incident that produced this rule, the connector resolved the visible From
  address as the recipient and discarded Basecamp's unique Reply-To route; the
  result was an `Email Received in Error` bounce and no Basecamp comment.
- A Basecamp update is complete only after readback proves the live thread URL
  or recording ID, the expected author, and a unique phrase from the comment.
  A Gmail SENT item is not proof. If no Basecamp write path exists, report the
  blocker and put the intended update in the run result; do not fall back to
  email.
- Embed this rail directly in every scheduled or cloud task that may touch
  Basecamp. Such runs may not load repository instructions before using an
  already-authorized Gmail tool.
- This rule controls the delivery path; it does not grant permission to post or
  weaken any existing human approval requirement.
<!-- shared-rule:basecamp-updates-stay-in-basecamp:end -->

<!-- shared-rule:screen-gct-before-amplification:start -->
## Screen GCT before amplification

- **Qualification is an evidence gate, not an execution grant.** A passing business-fit
  screen still needs independent review, an accepted scope/agreement receipt, and the
  authoritative Ops roster decision before onboarding or recurring work.
- **Gate outcome and evidence quality are separate.** Every GCT gate records outcome
  `UNKNOWN | MET | NOT_MET` and evidence state
  `UNKNOWN | OBSERVED | VERIFIED | CONTRADICTED | EXPIRED`. Unknown is never zero or
  failure; preserve the exact question, owner, due date, and blocked action.
- **Verdicts are deterministic, not scored.** Evaluator disagreement, an `UNKNOWN`
  outcome, or any evidence state other than `VERIFIED` routes to
  `DISCOVERY_REQUIRED`. With no discovery condition, verified `NOT_MET` routes to
  `DEVELOP`. Only eight verified `MET` pairs can be `QUALIFIED_PENDING_REVIEW`.
- **Amplify what is already working.** Verified new-idea, no-proof, undifferentiated,
  overbroad-ICP, unfocused-offer, or capacity conditions route to one development action
  and re-screening. They do not earn plumbing, publishing, or ad spend as a consolation.
- **Fail closed on authority.** Prospect screening is public-read-only. Publishing,
  messaging, permissions, Basecamp delivery, and spend require exact scoped approval;
  `Not Active`, `HOLD`, missing roster evidence, or blocked plumbing stops execution.
- The public guide is https://blitzmetrics.com/social-amplification/. The operational
  control plane is the roster-driven Money Tree; derived output folders are not state.
<!-- shared-rule:screen-gct-before-amplification:end -->

<!-- shared-rule:content-factory-four-stages:start -->
## Content Factory four stages

- The Content Factory line is locked: **Produce → Process → Post → Promote**.
  Do not rename, reorder, or merge these four.
- **Plumbing** is onboarding / access / tracking **before** the factory
  (`client-access-checklist`). It is not a factory stage.
- **Perform** is MAA (Metrics → Analysis → Action) **after** the factory /
  promotion loop (`weekly-brand-maa`). It is not a factory stage.
- If copy still lists Plumbing / Publish / Promote / Perform as the factory's
  4 P's, or uses Publish instead of Post inside that line, rewrite to the locked
  names. Upstream skill: `skills/content-factory/SKILL.md`. Canon pages:
  https://blitzmetrics.com/content-factory/ and
  https://blitzmetrics.com/the-4-stages-of-the-content-factory/.
- SAE course map (Plumbing → Goals → Content → Targeting → Amplification →
  Optimization) is separate; the Content Factory block inside it is still only
  Produce → Process → Post → Promote.
<!-- shared-rule:content-factory-four-stages:end -->

<!-- shared-rule:explain-with-linked-examples:start -->
## Explain with linked examples

- When explaining a concept (GCT, Content Factory, Dollar-a-Day, MAA, SAE, Nine
  Triangles, or similar), always **show and link** at least one concrete example.
  A definition alone is incomplete.
- Prefer live canonical URLs: Task Library, Local Service Spotlight, blitzmetrics.com
  SEO leaves, dennisyu.com. Never invent example URLs.
- Pattern: one sentence what it is, one sentence why it matters, then the linked
  example(s).
- Starters: GCT → Task Library GCT task + theninetriangles.com; Content Factory →
  https://blitzmetrics.com/content-factory/ and name Produce → Process → Post →
  Promote; MAA → weekly-brand-maa / a client-safe Friday MAA; Dollar-a-Day → method
  page + one public-safe winner when available.
<!-- shared-rule:explain-with-linked-examples:end -->

<!-- shared-rule:lss-is-the-public-company:start -->
## Local Service Spotlight is the public company

- **Dennis's current company in new public copy is Local Service Spotlight**, plus the
  vertical spotlight sites (law firm, pest control, dunker, and the rest). Be specific
  to that vertical. Do not present a sunset brand as the current company.
- **Do not name the sunset brand (BlitzMetrics) in new public pages, client-facing
  emails, social posts, or new product copy.** Historical URLs and git history may
  still contain it. Do not add more.
- **The existing canon/audit domain remains a publish host** for definitive articles
  and audits. Linking that URL is fine. Calling it the current company is not.
- Prefer `@localservicespotlight.com` addresses in new mail. Legacy aliases may still
  deliver; they are not a reason to put the sunset name in the body.
- This does not rewrite old articles or legal entity paperwork. It is a public-facing
  naming rule for new work.
<!-- shared-rule:lss-is-the-public-company:end -->

<!-- shared-rule:outbound-email-names-the-agent:start -->
## Every outbound agent action names the agent

- **When agent-authored content reaches another person, name the agent in the
  message itself.** This covers sent email, Basecamp comments and messages,
  DMs, support replies, scheduled reports, and the human-visible receipt for a
  publish or system change. A GitHub commit or private log is supporting
  evidence, not a substitute for visible attribution.
- End with one compact line:

  `Agent receipt: <agent> [<model if known>] · action: <drafted|sent|posted|published|changed> · human review: <reviewed by Dennis|authorized, not separately reviewed|no human review recorded>`

- Put the name a human recognizes first: `Claude`, `Codex`, `Grok`, `Cursor`,
  or the actual agent name. A persona alone is ambiguous; write `Grok — Meter
  Maid`, not only `Meter Maid`. Include the exact model only when the runtime
  exposes it. Otherwise omit it or say `model UNKNOWN`; never infer it from the
  writing style, OAuth client, or vendor name.
- State review truthfully. `Reviewed by Dennis` requires evidence that Dennis
  reviewed that exact message or action. Permission to act is not review, so
  use `authorized, not separately reviewed` when that is what happened. If the
  record is missing, use `no human review recorded`.
- Resolve the exact destination, audience, thread or record before acting. If
  routing or authority is unclear, fail closed instead of sending to Dennis or
  asking him to relay the work.
- An outbound action is complete only after source-system read-back verifies
  the destination/audience, thread or record, intended content/result, and
  agent receipt. A toast, sent item, commit, or private note alone is not proof.
- Leave the next action with its real owner. For completed Gmail work, archive
  the exact thread after verified action and restore it after seven days only
  when no human reply arrived; automation and system notices are not human
  replies.
- Name the agent even when `From:` or the source-system creator is Dennis. That
  identity is the delivery account; the receipt is authorship and action
  transparency. Place the receipt after the body and before any automatic legal
  footer.
- If an agent only prepared material and a human sent the final version, use
  `Prepared with <agent>; sent by <human>` when attribution is appropriate. Do
  not label a purely human-authored message as agent-authored, and never invent
  a fake human assistant signature to hide agent authorship.
- For a public page or code change, put the line in the delivery receipt or
  source-system update; do not add operational metadata to visitor-facing copy
  unless the publishing brief asks for it.
- This rule grants no authority to send, post, publish, spend, merge, or change
  access. Apply the existing approval and destination rules first. Once an
  outbound action is separately authorized, attribution is mandatory. When only
  drafting, include the agent name in the draft so it survives handoff.
- Scheduled prompts that may act externally must explicitly use the
  `outbound-action-closeout` skill and embed its routing, receipt, read-back,
  ownership, and fail-closed rails because an unattended session may not load
  repository rules or prior conversation.
<!-- shared-rule:outbound-email-names-the-agent:end -->

<!-- shared-rule:definitive-articles-show-what-they-are-and-where-they-fit:start -->
## Definitive articles show what they are, their evidence strength, and where they fit

- **The marker is a reviewed semantic claim, not a workflow status.** Mark a page as a
  Definitive Article, Definitive SOP or Definitive Framework only after a reviewer has
  confirmed that its labels, steps, links, evidence and canonical ownership agree with
  the accepted source of truth. A complete Task Library task, an all-tasks-complete hub,
  a taxonomy term or a `READY` state is useful workflow evidence, but none is sufficient
  by itself. An archive, alias, WIP page or semantically conflicted page gets no marker.
- **Mark the reviewed canonical hub visibly.** Put the appropriate marker above the
  opening summary so a reader can distinguish the maintained source of truth from a
  supporting post before scrolling. Supporting stories, updates and meta-articles point
  to the hub; they do not wear the marker themselves.
- **Keep certification, task priority and evidence volume separate.** Definitive status
  says the page is the reviewed canonical owner. Task importance decides which gap to
  work first. Meta-orbit strength measures only the number of verified completed-run
  meta-articles behind the hub. None of the three may be used as a proxy for another.
- **Derive the meta count from evidence; never type it into two sources.** One generated
  manifest owns the exact hub URL, mapped Task Library tasks, every counted and held
  evidence record, audit time, count and strength band. The article badge/footer and the
  Task Library render from that manifest. If the corpus cannot be checked, report
  `unknown`; if only a lower bound is proved, report `partial`. Never turn either into
  zero.
- **Count a primary worked example, not a generic cross-link.** A counted meta-article
  must be published, explicitly classified as a meta-article, document a completed run,
  materially execute the hub's task, and link to the exact canonical hub in its
  task-specific narrative or receipt. A shared framework map, compliance table,
  related-reading list, template, index, instructional page, archive, self-link or
  incidental concept mention does not make the post part of that hub's orbit. Preserve
  the reason for every excluded or held candidate.
- **Use fixed, transparent evidence bands.** Show the exact count next to the definitive
  pill and label 0 as `No verified examples`, 1–2 as `Emerging`, 3–5 as `Supported`,
  6–10 as `Strong`, and 11+ as `Deep`. This label measures documented-run volume only,
  not accuracy, freshness, traffic, quality or certification. Do not emit rating or
  review schema from it.
- **Make the graph work in both directions.** The Task Library task links to the final
  canonical article. The article's generated, collapsed evidence footer links to the
  exact filtered Task Library route and back to every counted meta-article. A stable
  `?task=` route opens one task and a stable `?article=` route opens the complete hub.
  A count without its inspectable source URLs is decoration, not evidence.
- **Lead with the result and the article's own evidence.** Give the 2–3 sentence
  plain-language summary first, then a compact outcome/checklist block. Keep the most
  specific primary visual or proof for that article above the fold: the actual framework
  diagram on a framework hub, the task-specific screenshot or flow on a software SOP,
  or the real photograph, artifact or result that proves the work. A generic system map
  must never displace that evidence or push it below the fold. Move audience explanation,
  history and secondary evidence below this primary orientation.
- **Use the larger system map as truthful context.** When an established framework has
  an exact relationship to the article, place its maintained detailed map after the
  article-specific primary visual and highlight only the subcomponents the article
  actually performs. Keep surrounding components visible but muted and caption what the
  highlight and handoff mean. On a framework hub, the canonical framework diagram is
  itself the primary visual and may serve both purposes.
- **A stage-only highlight or no map is valid.** If the task belongs to a stage but no
  named child station truthfully represents it, highlight only the stage and, where
  useful, its verified boundary or handoff. If no honest placement exists, omit the map
  and explain the cross-system relationship in text. Never activate a nearby box merely
  to make the diagram look complete.
- **Do not redraw a framework from memory.** Reuse the maintained labels, order, palette
  and relationships. A task-specific flow may accompany the system-placement view, but
  neither visual may make a relationship the accepted source does not support.

No fleet regex can enforce this honestly: a crawler cannot infer canonical ownership,
primary-parent evidence, truthful framework placement or whether a generic link documents
a completed run. Enforce it in the semantic preflight, source-backed orbit manifest,
bidirectional-link verifier and rendered desktop/mobile review.
<!-- shared-rule:definitive-articles-show-what-they-are-and-where-they-fit:end -->

<!-- shared-rule:named-entities-link-to-the-most-helpful-canonical-destination:start -->
## Named entities link to the most helpful canonical destination

- **Route the first meaningful mention of a named entity to the page that best helps
  the reader understand or act on it.** Link once; do not turn every repeated name
  into a link. Use the entity's natural name for a person or company, and use 3–6
  descriptive words for a training or concept link.
- **People point to their verified personal-brand home.** Prefer the person's owned
  website over an author archive, search result or social profile. If no owned site can
  be verified, use the relevant first-party company page or a canonical article that
  establishes who the person is; otherwise leave the name plain.
- **Companies point to their owned company site.** Correct the entity name before
  linking it. A plausible domain for the wrong spelling teaches the wrong association.
- **Tools and concepts point to our canonical training when it exists.** In explanatory
  copy, use a destination-naming phrase such as "our Listen Notes inventory guide" for
  the definitive how-to page; do not point the bare product name at our domain. Put the
  product's natural name and official website on the execution step where the reader
  actually opens it. This preserves both education and a direct path to action without
  making the anchor lie about where it goes.
- **Verify every destination before publishing.** The name, page title and live content
  must identify the intended entity. SEO value is a by-product of a truthful,
  reader-helpful relationship; it is never a reason to guess a domain.

This extends `no-unnamed-link-text`: that rule makes the anchor truthful; this rule makes
the destination useful. When a bare entity name and a training page would conflict, the
destination-naming anchor above is the reconciliation. No generic fleet regex can identify
people, ownership or the right internal training page, so enforce this through the
entity-linking preflight and a live link audit.
<!-- shared-rule:named-entities-link-to-the-most-helpful-canonical-destination:end -->

<!-- shared-rule:visuals-above-the-fold:start -->
## Visual and interactive content sits above the fold

- **The visual is the hook, not the reward.** A chart, diagram, photograph,
  calculator or interactive tool must be at least partly visible in the first
  screen, *after* the site's own header and title. Two or three sentences of
  lead-in above it is the maximum.
- **If the page has an interactive tool, the tool leads.** The prose becomes the
  explanation of it, not the preamble to it. Reword any copy that points "below"
  into a back-reference to the tool at the top.
- **No prose run longer than about two screens** without a figure, pull quote,
  callout or list breaking it.
- **Why:** `every-article-has-pictures` only asks whether an image exists. A page
  can satisfy it and still bury the picture four screens down, where nobody
  scrolls. That is the exact failure this rule closes, and it shipped on
  dennisyu.com before anyone noticed.
- **Server-render the initial state of any interactive block.** WP Rocket and
  similar optimisers delay inline JavaScript until the visitor's first
  interaction, so a block that builds its own DOM paints as an empty shell —
  worst of all when it is now the first thing on the page. Bake the default state
  into the markup and make the script idempotent (`el.innerHTML = ''` before it
  populates) so it replaces that markup instead of appending a second copy.
- **Verify by measuring on the live URL, not the local render.** Site chrome is
  routinely 300–400px, so a layout that clears the fold locally can fail once
  published. Check at 1440x860 and 390x844.
- **Exemption:** a page whose whole purpose is a single block of prose — a
  disclosure, a policy, a legal notice — is exempt. Tag it, do not silently skip
  it.

The sweep only catches the blatant case: a headline with no visual anywhere near
it. Whether the visual actually clears the fold is a judgement call, verified by
opening the published page — see `verify-by-opening-the-live-artifact`.
<!-- shared-rule:visuals-above-the-fold:end -->

<!-- shared-rule:an-unanswered-ask-never-stops-the-work:start -->
## An unanswered ask never stops the work

- **Silence is not a blocker, it is a trigger.** When someone does not reply, the work
  continues on the rescue path you chose before you sent the ask. "Waiting on them" is
  never a status an agent reports twice.
- **Try to need them less before you try to reach them harder.** In order: do it yourself;
  route around; engineer the dependency so it cannot block again; only then ask. Most asks
  disappear at step one once you actually test them, because "I need this from them" is
  usually "I would prefer this from them."
- **Only three things justify asking a human at all** — binding authority, credentials or
  physical access nobody else holds, and a fact that exists only in their head. Preference,
  convenience, and "they would probably want to weigh in" are not gates.
- **Every ask ships with its rescue, decided before sending**: a deadline, a named fallback
  action, and you as the owner of that fallback. Put it in the message. "If I do not hear
  back by Friday I will assume X and proceed" turns silence into a decision, and usually
  produces the reply anyway.
- **Shrink the ask until it can be answered in ten seconds.** One question, one message, a
  yes or no where possible, plus what you already tried. A question that makes someone
  reconstruct context is a question that does not get answered.
- **When the deadline passes, execute the rescue quietly.** Do not re-send the same ask.
  Do not hand the chase to whoever is busiest. Log the miss for the periodic reliability
  record and move on: a pattern is a management conversation, held later with evidence in
  hand, not an interruption now.
- **The second time the same dependency blocks, stop treating it as a people problem.**
  Build the thing that makes their non-response harmless — a watchdog, a fallback route, a
  second credential, a cached copy. Building it once costs less than chasing it forever.
- This does not loosen `agents-draft-humans-send`. Rescue means doing the *work* yourself,
  never dispatching messages, publishing, spending or deleting on someone's behalf because
  they went quiet. Where the rescue would cross that line, stage it and say so.
- Rescue toward the function, not the person — see `assign-work-to-a-function`. A rescue
  aimed at an individual who is away is not a rescue.
<!-- shared-rule:an-unanswered-ask-never-stops-the-work:end -->

<!-- shared-rule-index:start -->
## Other house rules that apply to this work

These are not repeated here because they govern published pages rather than agent behaviour. They are binding all the same — read the full text in `AGENTS.md` or `standards/` before touching a website.

- **Analytics goes on before anything gets optimised** (`analytics-on-every-page`)
- **A button must contrast with what it sits on** (`buttons-must-contrast-with-their-background`)
- **Every article has pictures** (`every-article-has-pictures`)
- **Every public page shows real people or real work** (`every-public-page-has-real-imagery`)
- **Personal-brand heroes are immersive, not boxed** (`immersive-hero-standard`)
- **Every link and every entity claim resolves** (`links-must-resolve`)
- **Never ship a black button** (`no-black-buttons`)
- **Placeholder copy never reaches production** (`no-placeholder-copy`)
- **No popup on page load** (`no-popup-on-load`)
- **No unnamed link text** (`no-unnamed-link-text`)
- **Nothing plays at the visitor uninvited** (`nothing-plays-uninvited`)
- **Order proof by authority, strongest first** (`order-proof-by-authority`)
- **A photograph has to earn full bleed** (`photo-earns-full-bleed`)
- **Every URL we say out loud resolves** (`spoken-urls-must-resolve`)
<!-- shared-rule-index:end -->
