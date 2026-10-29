---
name: evidence-verification
description: Establish what is actually TRUE about a client and prove it with records a stranger can check. Find the hard anchors hiding in public registries (Secretary of State, bar admission, ISBN, patents, ORCID, authority files), verify identity by matching a second fact rather than a matching name, and never let "we haven't looked yet" render as "they scored badly." The upstream skill every authority skill depends on — knowledge-panel-entity-seo, grokipedia-authority and ai-search-visibility all fail the same way when the underlying facts are wrong.
---

# Evidence Verification

**Use this when** you are about to assert something about a client in public — a schema field, an encyclopedia submission, an audit score, a bio, a Knowledge Panel claim — and you want to be certain it is true, and provable by someone who does not trust you.

A repeatable failure occurs when a source record has the wrong profession or location, a research note identifies the error, and downstream systems still treat the unchanged record as fact. Correct the authoritative record and every dependent artifact before any public submission. A note describing a correction is not evidence that the correction landed.

## The one idea

**A fact about a client is not established until a stranger can check it without asking you.**

Your client's own website is not evidence of anything except what your client wants to say. A testimonial is not evidence. A follower count is not evidence. What counts is a record held by someone with no stake in the outcome: a government registry, a national library, a court, a standards body, a publisher, a newsroom.

Everything below is machinery for finding those records and refusing to fake them.

---

## Part 1 — Find the anchors nobody looked up

Most clients already have hard, verifiable public records. Nobody has searched for them. Work this list in order of how cheap the win is.

### The business registry — the anchor almost every client has
Identify the official registry for the entity type and jurisdiction. US Secretary of State or Corporation Commission records and UK Companies House are examples. Check current public availability, fees, fields and privacy rules; not every business form has the same registration requirements or publicly named officers.

What you get: legal entity name, charter or company number, formation date, status, registered address, and — the part that matters — **named officers, managers and registered agents**.

Portable lookup method: when a business contact is incompletely identified, search the appropriate official registry by the verified legal or trading entity. In the authorized private evidence record, retain the registry source, legal entity, relevant officer role, formation date, status and record locator when available. Match a second independent attribute before linking the record to a person. Public registry availability and fields vary; do not assume every business has an accessible record or republish unnecessary personal addresses.

### The rest of the ladder, by profession
| If the client is… | Look here | What it proves |
|---|---|---|
| Any business owner | Secretary of State / Companies House | Legal name, role, entity, formation date |
| An attorney | State bar admission; reported case citations | Licensure, jurisdiction, practice history |
| A doctor, dentist, therapist | State licensing board; NPI registry | Credential, specialty, standing |
| Any author | ISBN; national library (Library of Congress, DNB, BnF) | Authorship, publisher, date |
| An academic | ORCID, Google Scholar, institutional page | Publications, citations, affiliation |
| An inventor | Patent office (USPTO, EPO) | Named inventor, filing date |
| A contractor or tradesperson | State contractor licence board | Licence number, class, standing |
| A restaurateur or retailer | Health permits, liquor licence, local press | Operating record |
| A speaker | Conference programmes and archives | Named role at a named event |
| A nonprofit officer | IRS Form 990 (public) | Named officer, compensation, role |
| Anyone with a Wikipedia article | Wikidata QID + authority files (GND, VIAF, ISNI) | Everything, instantly |

### Weighting: not all anchors are equal
A registration proves someone **runs a business**. It does not prove anyone independent found them **notable**. Weight accordingly, and say so out loud when you report:

1. **Strongest** — Wikipedia article, national-library authority record, book with an ISBN from a real publisher, sustained national press where they are the subject
2. **Strong** — a single national press piece as subject, a named award, an academic publication record, a patent
3. **Real but modest** — business registration with a charter number, professional licence, named speaking role
4. **Not an anchor** — their own website, their own bio, follower counts, testimonials, directory listings they submitted themselves, press releases

Never let a category-3 anchor alone trigger a public submission. It is enough to establish identity; it is not enough to establish notability.

---

## Part 2 — Verify identity with a second fact

A matching name is not a match. This is the single most expensive mistake in entity work, because the output looks completely normal when it is wrong.

**Rule: confirm on a second, independent attribute** — an address, a formation date, a brand name, a co-founder, a licence number, a photograph.

For a registry lookup, compare the official record with an independently obtained business attribute, such as a permitted business address, domain or formation detail. Record what matched and what remains uncertain. A matching name and city alone are insufficient; a shared address can also require further disambiguation.

The inverse error is a false namesake warning. Follow a candidate record through its linked authority files and independent sources before rejecting the match. When evidence resolves a warning, retire it in the owning record and recompute dependent eligibility and scores. Preserve the resolution evidence so a stale warning is not inherited.

So:
- Two identifiers agreeing = identified.
- One identifier = a hypothesis, and it must be labelled as one.
- A namesake flag must carry the evidence and the date it was established, so it can be re-tested rather than inherited forever.

---

## Part 3 — Read negation

Research prose records absence as often as presence. Your own notes will say:

> "Confirmed to have NO Knowledge Panel, NO Wikipedia, NO Wikidata and NO Grokipedia."

A naive keyword matcher can find *Wikipedia*, *Wikidata* and *Knowledge Panel* in that negated sentence and falsely record three positive anchors. Use the sentence as a synthetic negative fixture: it must never promote an entity to "ready to submit."

Any automated anchor detection **must check for negation before the match** — `no`, `not`, `never`, `without`, `lacks`, `missing`, `zero`, `none`, `absent`. Scan a short window to the left and stop at a clause break so a negation in one sentence cannot suppress a real anchor in the next.

And when you add a new anchor type later, add it to the negation guard **in the same edit**. This is the kind of check that silently stops applying the moment someone extends the system.

---

## Part 4 — "Not researched" is not "failing"

This is the rule that protects the client relationship, and it is easy to get wrong in a way nobody notices until a client sees the report.

If nobody has researched a client yet, that is a gap in **our** knowledge. It is not a judgement about them. A system that scores unresearched entities as zero produces a report where "we never looked" and "we looked and they have nothing" are visually identical — and the client cannot tell which one you meant.

Build the distinction into the data model, not the wording:

- **UNKNOWN** — no research done. No score at all, not a zero. Goes to a research queue with the specific questions to answer.
- **BUILD** — researched, no anchor found yet. A real, honest finding.
- **NEARLY / READY** — researched, anchors found.

Enforce it with a test that fails if an UNKNOWN entity receives any numeric score, including zero, and another that checks the UNKNOWN action text describes the research owner's next step rather than the client's deficiency. A researched zero remains distinct from missing research. Wording drifts; tests do not.

---

## Part 5 — Carry the evidence into the artifact

Research that stays in a research file is wasted. Whatever you produce at the end — a submission, an audit, a schema block, a pitch — must carry the specific verifiable anchors, not a summary of them.

A generator that says *"active professional presence; any press, podcast appearances, books"* has thrown away everything that mattered and produced filler that reads as unsourced. Compare:

> **Generic wording to reject:** "Documented independently; entity home with structured data; active professional presence."
>
> **Evidence template, not a factual example:** "Independently verifiable: [publisher and primary URL]; [ISBN and catalogue record]; [authority-file identifier and URL]; [matched knowledge-base item and URL]; [existing article URL, if verified]."

Populate each field only from verified records matched to the subject. Omit unsupported fields; placeholders must not ship in an actual submission.

And when there is **no** hard anchor, say so loudly in the artifact rather than dressing up the absence. A package that admits "no third-party anchor found — expect rejection, surface one proof first" is more useful than one that bluffs and gets bounced.

---

## Part 6 — Fix at the source, in the same run

Test these reusable failure modes:

- A research note corrects a niche, but the authoritative record remains unchanged.
- A namesake warning is resolved in one artifact and remains active in another.
- A new anchor type is added to one duplicated detector but not its negation guard.

So:
1. **Fix the source record**, not just the output. If the roster is wrong, fix the roster.
2. **Make the contradiction self-detecting.** If two records disagree about the same identifier, that is a testable condition. Write the test; do not rely on someone noticing.
3. **One authoritative definition.** If a rule is expressed in two places, they will diverge — usually at the moment someone extends the system, which is the worst possible time.
4. **A note saying "X is wrong and should be corrected" is not a correction.** Either fix it in the same run or file it somewhere that fails until it is fixed.

---

## How to run it

1. **Inventory** — list every client, partner and entity. Mark active/inactive from the authoritative source, and record a *reason* for every inactive one.
2. **Probe what already exists** — before researching anything, check whether the entity already has a Wikipedia page, Wikidata item, Knowledge Panel or Grokipedia page. Run controls first: a known-good lookup and a deliberately nonsense one. **A check that cannot fail is not a check.** Record existing pages and inspect their accuracy rather than assume they are absent.
3. **Hunt anchors** — work Part 1's ladder, cheapest first. Business registry before anything else.
4. **Verify identity** — second attribute, always. Record which two facts agreed.
5. **Score honestly** — UNKNOWN where you have not looked.
6. **Carry evidence into the artifact** — specific records, and a loud warning where there are none.
7. **Report the corrections you made**, not just the findings. A run that fixed two wrong records delivered more value than one that found three new anchors.

## What good looks like
- Every assertion traces to a record a stranger can pull up.
- Every identification names the two facts that agreed.
- Nobody is scored on evidence they do not have, in either direction.
- The count of unresearched entities is stated plainly and never disguised as a low score.
- Corrections to source records are reported in the same run they were found.

## Related skills
- **knowledge-panel-entity-seo** — consumes these verified facts as schema. Wrong facts here become wrong structured data there, which Google then believes.
- **grokipedia-authority** — source-backed encyclopedia preparation. When a provider reports insufficient citations, inspect the actual rejection and evidence gaps; do not infer the cause from this skill alone.
- **ai-search-visibility** — independently tests answers against verified records and disclosed sources; an undisclosed source remains UNKNOWN.
- **positive-mentions-harvester** — finds the press; this skill decides which of it is a real anchor.
- **client-access-checklist** — access is the precondition for measuring; verified identity is the precondition for publishing.
- **recursive-self-improvement-qa** — the discipline in Part 6 is that skill applied to facts instead of code.

## Operational lessons

These portable lessons describe checks and failure modes, not a report of a
particular account or client. Verify current vendor contracts before use.

- A source file, a package member, a catalog row and a standalone public explanation are distinct artifacts. Verify the one the reader or receiving agent actually needs.

- Reject plausible placeholder sentences and inferred positioning presented as fact. Unknown data stays unknown; review cover text and summaries as well as the underlying table.

- Inspect the actual keywords and landing pages before crediting search visibility. Spam or compromise can inflate traffic and keyword counts; those numbers are not evidence of the owner's authority.

- When a report partitions a set, assert that every item belongs to an intended category and the category totals reconcile. Keep unreachable, access-denied and suspected WAF cases distinct.

- A tool timeout does not establish that its child process stopped. Reconcile the process, stable run ID and destination before retrying a non-idempotent action.

- Required guards must fail closed when missing or unable to run. Invoke scripts through their documented interpreter when appropriate; do not silently skip a guard because an executable bit changed. Preserve and check pipeline exit status.

Apply the maintained [Learn, Do, Teach method](https://github.com/dennisyu/local-service-spotlight-skills/blob/main/docs/agent-setup/LEARN-DO-TEACH.md)
and [acceptance checks](https://github.com/dennisyu/local-service-spotlight-skills/blob/main/ACCEPTANCE.md).

<!-- shared-rule:silent-media-playback:start -->
## Silent media playback

- Never let audio from browser, video, audio, presentation, or application testing play through the user's speakers unless the user explicitly asks to hear it.
- Before starting any media playback, mute the player and set its volume to zero. Keep it muted for the full test, including replays, reloads, new tabs, and alternate players.
- Apply this rule to the primary agent and every delegated agent. Include the mute requirement whenever work that may involve media playback is delegated.
- If the mute state cannot be controlled and verified before playback, do not start playback. Use metadata, captions, transcripts, frames, screenshots, network state, or player state instead.
- Only unmute when the user explicitly requests audible playback in the current task.
<!-- shared-rule:silent-media-playback:end -->

<!-- shared-rule:agents-draft-humans-send:start -->
## Selective human review; agents finish authorized work

Marker: `SELECTIVE-HUMAN-REVIEW-2026-10-07`.

- **Done is better than perfect.** Complete routine work within the user's recorded
  authority, including factual replies, ordinary project coordination, approved client
  tweaks, and publishing on authorized properties. Do not require Dennis to review
  every draft, message, change, or publication in advance. Review friction has a cost.
- **Ask in advance only for a consequential decision or missing authority:** new
  commitments or changes to pricing/scope, contracts, financial transactions outside
  existing authority, personnel decisions, sensitive disclosures, new access/security
  privileges, destructive or hard-to-reverse changes, disputed client intent, crisis/press
  statements, or material claims whose facts cannot be verified. Existing explicit holds
  and client consent requirements still apply. An assigned owner or qualified reviewer
  may resolve matters within their authority; do not make Dennis the default bottleneck.
- **Prepare the concrete result before asking.** Name the exact decision, risk, recipient
  or property, and recommended action. Continue independent authorized work while waiting.
  Uncertainty about polish alone is not a reason to stop.
- **Verify and report after acting.** Check facts, destination, duplication, release
  results, and an appropriate rollback/recovery path. Preserve any required independent
  QA. Log what shipped and what needs follow-up; fix ordinary misses promptly.
- **Authority is not human review.** Never imply Dennis reviewed an item he did not.
  Use the existing identity/receipt rules and mark authorized work accurately.
  This policy does not supply missing credentials, bypass platform approval gates,
  authorize impersonation, or authorize changes on a client's property without consent.
<!-- shared-rule:agents-draft-humans-send:end -->

<!-- shared-rule:ask-blocking-questions-up-front:start -->
## Ask every blocking question up front

- **Front-load every question and every missing access into the planning step**, before
  the long work starts. The person who briefed you intends to walk away; a question
  raised at minute ninety costs them the whole ninety minutes.
- **Do not guess to avoid asking.** A guess that turns out wrong is discovered at the end,
  when it is most expensive to undo.
- After the short plain-language context, put an explicit **open questions and
  missing access** block near the start of every plan. If the list is empty, say
  so — that is information too.
- Once the questions are answered, work continuously to the end rather than stopping to
  check in on things you could have decided.

### Audit intake refinement — Dennis Yu, October 2, 2026

Only a truly blocking identity or action-authority question stops that lane.
Premium/conference GCT clarification is relevant and optional after the base
proof audit. Do not interpret front-loading as a generic questionnaire required
to receive value. Record inferred/UNKNOWN strategy, offer confirm/edit/continue,
and deliver qualified findings and conditional priorities without a reputation
penalty. Use the maintained shared audit run contract.
<!-- shared-rule:ask-blocking-questions-up-front:end -->

<!-- shared-rule:assign-work-to-a-function:start -->
## Assign work to a function, not a person

- **Every task is owned by a function** — web, content, analytics, client success — and
  people sit inside functions. People join, leave and go on holiday; the function does not.
- **Escalate to a function too.** "I told one colleague" is not an escalation if that
  colleague is away; "escalated to the web function" is.
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
- **Use selective review, not a blanket send/publish gate.** Complete routine work,
  including messages and publication, within recorded authority. Bring only consequential
  decisions or missing authority for advance review — see `agents-draft-humans-send`.
  Keep verification and recovery proportional to the actual risk.
- Report what you changed in enough detail that undoing it is a one-line instruction.
<!-- shared-rule:be-proactive-see-it-through:end -->

<!-- shared-rule:capture-what-you-learn:start -->
## Capture what you learn as a standard, in the same session

- **A lesson kept only in an article, chat, recording or context window may be
  absent from the instructions the next operator loads.** Capture its reusable
  criteria in the canonical standard, distribute the applicable source copies,
  and test the receiving runtime before claiming adoption.
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
  request. The sync copies the rule into `AGENTS.md` and each distributed `SKILL.md`
  whose declared scope applies. This prepares source copies; it does not update an
  existing installation. Record the released revision, required sync action and a
  fresh-session activation test for each account being claimed.
- **Give the rule a machine check whenever one is honest.** A `checks` block in the
  header is consumed by the fleet sweep when that sweep actually runs against an
  applicable target. Every check must carry passing and failing examples. Exercise
  a separate failing case too: a pattern that matches nothing can look healthy.
  Record scheduling and actual firing separately; a check in source creates neither.
- **Where a machine check would be dishonest, say so and leave `checks` out.** Judgement
  rules still need a qualified reviewer to apply them to the actual result. Reading
  a rule is not evidence of compliance, and a regex cannot certify judgement.
- **Provenance is required, not decoration.** `captured_from` is how the team sees which
  channels leak. Missing provenance is a reason to inspect the capture path; it does
  not establish how many recordings exist or whether an undocumented process ran.
- **When a new rule contradicts an existing one, resolve it in the file and say so
  out loud.** Two standards that disagree are worse than one that is wrong, because
  every agent that reads both will pick whichever it happened to see last. Write the
  reconciliation into the newer rule and flag it to the account owner for confirmation.
- The order is Checklist → Content → Software. Write the checkable rule first, publish
  the article that teaches it second, and let the sweep be generated from the rule
  rather than hand-written beside it when the declarative check types suffice.
  Complex checks need maintained code and tests linked from the rule. CCS means
  Content, Checklists, Software; this checklist-first capture sequence preserves
  that framework. An article alone leaves checks and adoption unproved.
- **Close the learning loop with another operator.** Link the actual run, correction,
  standard, teaching content and software check. Give a fresh operator only the
  guide and permitted inputs; record the tested revision, result, failures and help
  required. Fix ambiguity in the master and replay the affected steps. Saying the
  lesson was shared does not prove another operator can use it.
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
- **Open with the reader's decision and the value of this deliverable.** In the
  first two or three sentences, connect the strongest supported finding to the
  reader's situation and the action it enables. Follow
  `every-article-and-project-starts-with-specific-gct`; a title, biography,
  table of contents or methodology paragraph alone does not orient the reader.
  On a multi-page document or deck, each later page or section also leads with
  its useful takeaway, without repeating the whole introductory pitch.
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
- **Practice safely, then do it.** A public or synthetic rehearsal helps a new
  operator learn the procedure. Label it as practice; it does not prove a client
  result, production readiness, or mastery. Real Do requires an authorized task,
  its original acceptance criteria, a checked artifact and destination evidence.
- **Then teach it** — preserve the inputs and source revisions, steps, choices,
  mistakes, fixes, checks and limits in a reusable guide. Keep private evidence
  private and use only approved public examples. Update the canonical standard
  and its Content, Checklist and Software forms instead of creating a competing SOP.
- **Test the teaching with a fresh operator.** Another person or agent must work
  from the guide and permitted inputs without the author filling in missing steps.
  Record the tested revision, independent result, help required and failures. Fix
  the guide and repeat the affected part. A replay proves only the tested scope;
  agreement, publication, or a successful synthetic case alone does not prove mastery.
- **Check that the checker can fail.** Run a known bad case and a clean case; where
  practical add an independently chosen failure beyond the checker's own examples.
  Report what software did not check, including meaning, permissions and actual
  runtime behavior. Preserve the separate account and job evidence in the release
  receipt rather than treating source consistency as adoption.
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

- For an authorized project update, identify the exact existing thread and its
  intended audience before writing. Use the team's approved source-system
  connector, API or interface; the task still needs communication authority.
- A notification is a cue to read the source record, not a destination. Do not
  address a message to a generic notification sender or assume that changing
  the sender identity makes a failed delivery route valid.
- In this workflow, keep the update in its original project thread rather than
  substituting an email route. If the approved write route is unavailable,
  record BLOCKED with the failed step, evidence, owner and bounded next action.
- Read the destination after the write. Verify the intended thread, expected
  author and distinctive new content, and retain its location and observation
  time. A successful send/save response alone does not establish delivery.
- Ensure each participating runtime loads the current delivery policy before
  acting, including scheduled workers. Source publication alone is not evidence
  that those workers loaded or followed it.
- This rule describes a reusable delivery safeguard. It names no account,
  project, recipient, private incident or active deployment, and it grants no
  permission to post, send or change access.
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

- **Name the kind of canonical page before judging it.** A task-definitive article
  is the maintained recipe for one repeatable task. A topic, entity or framework hub
  explains its subject and links to the task recipes it owns; it need not pretend to
  execute one task. Supporting stories, opinion pieces, tool comparisons, references,
  historical posts and meta-articles remain distinct. A repaired opening, lead visual,
  incoming link or prior fleet-audit label does not promote any of them to a task SOP.
- **A task recipe must let another worker repeat and check the work.** Require all of:
  the trigger and starting state; required inputs and access; linked prerequisite tasks
  and their expected outputs; ordered steps with decision points; the measurable output
  and observable pass/fail criteria; and the downstream task, receiving owner/function
  and handoff artifact. Link the canonical task in the
  [Task Library](https://local-service-spotlight.github.io/task-library/) and its parent in the
  [Content Factory](https://blitzmetrics.com/content-factory/). Do not invent a task,
  prerequisite, threshold or relationship to fill a box. Mark a missing required field
  as a gap and hold task-definitive certification until the source supports it.
- **Keep the recipe separate from each execution record.** Every task execution writes
  a [meta article recording the run](https://localservicespotlight.com/meta-articles/)
  using the [meta-article guidelines](https://blitzmetrics.com/meta-article-prompt/).
  It links to the exact canonical task, the recipe revision used and the run evidence.
  Writing is required; publishing the meta article and changing the canonical recipe
  follow the existing authorization for those actions. The run record feeds reviewed
  improvements back into the recipe and skill; it never becomes a second recipe.
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
- **Derive each named metric from evidence; never type it into two sources.** One
  generated manifest owns the exact hub URL, mapped Task Library tasks, counted and held
  evidence records, known execution IDs or explicit missing-ID states, audit time,
  metric names, counts and strength bands. The article and Task Library render from
  that manifest. Keep historical public-example volume separate from verified task
  execution frequency. If a metric cannot be checked, report `unknown`; if only a lower
  bound is proved, report `partial`. Never turn either into zero.
- **Preserve dated public-example counts as article volume.** An earlier review may
  establish that a hub had a stated number of qualifying public meta articles on its
  audit date without establishing execution IDs. Keep that dated evidence and its
  inspectable sources. It remains historical public-example volume; it is not a claim
  of that many distinct task runs. Missing IDs do not erase verified article evidence.
- **Count task execution frequency separately.** Deduplicate each canonical task's
  executions by ID and state the reporting period and result statuses. Revisions,
  retries within one run, translations, clips and syndicated copies do not create
  executions. A separately scoped rerun has its own ID and evidence. Keep failed/partial
  and unpublished runs in internal history with their statuses. Older articles without
  a reliable run identity cannot establish execution frequency; that metric remains
  UNKNOWN or PARTIAL even when their dated article-volume count is valid.
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
- **Lead with the specific GCT and the article's own evidence.** In 2–3 sentences
  at fifth-grade reading level or below, name who this is for, what it does, why
  it matters and the useful outcome. Use the reader's actual situation and the
  mechanism or evidence that makes the outcome useful; follow
  `every-article-and-project-starts-with-specific-gct`. A generic benefit claim
  or an acronym definition is not a passing opening. Keep the topic-specific visual beside that
  short opening in the first screen; it may lead. A checklist is secondary and
  must not push it below the fold. Keep the most
  specific primary visual or proof for that article above the fold: the actual framework
  diagram on a framework hub, the task-specific screenshot or flow on a software SOP,
  or the real photograph, artifact or result that proves the work. A generic system map
  must never displace that evidence or push it below the fold. Keep the audience in
  the opening; move extended background, history and secondary evidence below it.
- **Show where a task fits after its first-screen orientation.** A Content Factory task
  needs a responsive context diagram lower in the article: Produce → Process → Post →
  Promote in the maintained order, only the work this task performs highlighted, and
  linked prerequisites → this task → the next task. Show the meta-record feedback into
  the canonical recipe. This context map is additional to the topic-specific lead
  visual. Keep access/tracking before the factory and measurement after it when those
  boundaries apply. An unverified placement stays a stated gap; it is not permission
  to invent a station or certify a task with an unknown handoff.
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

Before writing or reviewing an article, open the current [Article Guidelines](https://localservicespotlight.com/article-guidelines/) and [link-building guide](https://blitzmetrics.com/link-building/). Use the [internal-linking process](https://blitzmetrics.com/internal-linking/) to connect pages and the [entity-linking decision tree](https://blitzmetrics.com/entity-linking/) to choose destinations. These are complementary owners, not competing copies. The older Blog Posting Guidelines and dated downloads are historical references, not the maintained writing standard. Record the checked URLs, date and available page revision or content hash in the existing work record, separately from the installed skill commit. If a current source is unavailable or conflicts with a copied instruction, record the gap and resolve it before claiming the review passed.

- **Route the first meaningful mention of a named entity to the page that best helps
  the reader understand or act on it.** Link once; do not turn every repeated name
  into a link. Use the entity's natural name for a person or company, and use 3–6
  descriptive words for a training or concept link.
- **People point to their verified personal-brand home.** Prefer the person's owned
  website over an author archive, search result or social profile. If no owned site can
  be verified, use the relevant first-party company page or a canonical article that
  establishes who the person is; otherwise leave the name plain.
- **Program members and clients get exactly one link per article — to their personal brand site.** Anyone in the AI Builder program, or any client, named in an article gets one link to their verified personal-brand site, on the first mention, and no repeat links later in that article. Standing rule from Dennis Yu (2026-10-08): one article, one link per person.
- **Companies point to their owned company site.** Correct the entity name before
  linking it. A plausible domain for the wrong spelling teaches the wrong association.
- **Tools and concepts point to our canonical training when it exists.** In explanatory
  copy, use a destination-naming phrase such as "our Listen Notes inventory guide" for
  the definitive how-to page; do not point the bare product name at our domain. Put the
  product's natural name and official website on the execution step where the reader
  actually opens it. This preserves both education and a direct path to action without
  making the anchor lie about where it goes.
- **Search our article inventory before choosing a provider help page.** Look up
  the object in the Canonical Directory, Task Library and site search, then read
  the candidate to verify that it answers this reader's question. For Obsidian,
  use “our Obsidian setup guide” when that guide is the relevant lesson. Record
  the entity, chosen URL and reason in the link audit. If no suitable owned
  guide exists, keep a conceptual mention plain or cite the precise primary
  source needed for the claim; record the content gap instead of inventing a URL.
- **Give the page a place in the SEO Tree.** Name the canonical parent topic,
  link supporting articles up to it, connect the hub to useful supporting proof,
  and link across only to related guides that help the next task. Verify those
  links in the article body; a catalog listing or sitewide footer is insufficient.
  One topic keeps one owner across our sites. Do not mass-add unrelated links or
  use a quota to turn every provider citation into an internal link.
- **Keep primary citations and execution links when they do a different job.**
  A provider's API reference can substantiate a technical claim; its download or
  sign-in page can be the required action. Label those links by their purpose
  and retain them alongside our training when useful. A provider citation does
  not replace the internal explanation of how we use the tool.
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
  calculator or interactive tool must be substantially visible in the first
  screen alongside the page title. This applies to every fleet page, including
  home, money, relationship, article, archive, resource and policy pages. Two or three sentences of
  lead-in above it is the maximum.
- **A blank or hidden block is a failed visual.** A colored shell, empty SVG,
  broken image, loading placeholder, clipped labels or content visible only after
  scrolling does not pass. The first screen must show a meaningful part of the
  picture or diagram with readable labels, not just its border or a thin strip.
  Give the figure an honest caption or accessible description of what it teaches.
- **If the page has an interactive tool, the tool leads.** The prose becomes the
  explanation of it, not the preamble to it. Reword any copy that points "below"
  into a back-reference to the tool at the top.
- **No prose run longer than about two screens** without a figure, pull quote,
  callout or list breaking it.
- **Why:** `every-article-has-pictures` only asks whether an image exists. A page
  can satisfy it and still bury the picture four screens down, where nobody
  scrolls. Check the rendered first screen so an image count cannot hide that
  failure.
- **Server-render the initial state of any interactive block.** WP Rocket and
  similar optimisers delay inline JavaScript until the visitor's first
  interaction, so a block that builds its own DOM paints as an empty shell —
  worst of all when it is now the first thing on the page. Bake the default state
  into the markup and make the script idempotent (`el.innerHTML = ''` before it
  populates) so it replaces that markup instead of appending a second copy.
- **Verify by measuring on the live URL, not the local render.** Site chrome is
  routinely 300–400px, so a layout that clears the fold locally can fail once
  published. Check at 1280x800 and 390x844 as an anonymous first visit, before
  any click, scroll or other interaction. Capture the viewport and record the
  visible content and its position, working media/labels, and overflow. Also
  confirm the initial figure survives delayed or unavailable JavaScript.
  Verify the saved source separately from the served page: source equality,
  HTTP 200 and an image tag alone do not prove a working above-fold visual.
- **Check what WordPress serves, including the CSS.** Paragraph formatting can
  insert markup into an unprotected inline style block and discard its first
  rule. Use a valid Custom HTML block (`wp:html`) and avoid blank lines inside
  inline CSS. Compare the served markup and applied browser styles after the
  save; a correct editor source does not prove the browser received valid CSS.
- **Minimum visible proof:** on both required viewports, the loaded visual must
  expose at least 220px of width and 160px of height, at least 40% of its own area,
  and 8% of the viewport area. At least 90% of sampled visible points must be
  unobscured by navigation, sticky bars or overlays. These are minimum acceptance
  limits, not a design target. Show the face, action or diagram's useful labels;
  geometric success cannot approve an irrelevant crop.
- **Measure painted content, not letterboxing.** For contain/scale-down/none
  images, use intrinsic aspect ratio, content-box dimensions and object-position
  to measure the photo pixels that are actually displayed. Empty padding and
  letterboxing cannot meet the visible-area or minimum-width requirement.
  CSS backgrounds currently require background-size:cover for an automated
  geometry pass. Contain, auto and explicit sizes stay unmeasured and fail that
  gate until their painted bounds receive a dedicated measurement/review.
- **Keep the title readable in that same first screen.** At least one natural
  H1 (or level-one accessible heading) text line must be visible at 18px or
  larger, with at least 90% of its text-line area visible and unobscured. A long
  title may wrap; the visual may sit beside, above or below it. Do not fill the
  viewport with a photo that hides the entire page title.
- **A background must actually show through.** Loading the photo URL is not
  enough. Opaque descendant panels and before/after overlays count as covers,
  including pointer-events:none. Transparent text or a light tint can coexist
  with the photo, but the useful visible crop still needs screenshot review.
- **The content earns the space.** A logo, social icon, navigation, cookie banner,
  decorative gradient, generic stock photo or unrelated portrait does not count.
  Use an authentic relevant moment, playable captioned source video with a loaded
  poster, or a specific diagram that teaches the page's point. Open the source
  and the rendered screenshot. A coappearance alone never proves endorsement.
- **Every page means every page.** The former prose/policy exemption is removed
  by Dennis's 2026-09-05 instruction. A short policy can use a concise diagram
  explaining its actual process. Do not invent a person or pad a page with stock.
- **Keep media invited and silent during QA.** First paint must not autoplay.
  YouTube uses youtube-nocookie.com, rel=0, cc_load_policy=1 and a page-language
  cc_lang_pref. A click-to-play poster counts only when the real relevant image
  loads and its destination/player is verified. An iframe rectangle, thumbnail
  URL or screenshot of a broken player is not playable video proof. Follow
  youtube-captions-on-by-default; never invent missing caption tracks. During
  testing mute and set volume zero before any playback; use silent metadata and
  posters if playback cannot be safely controlled.
- **Use the browser gate in every builder and publisher.** After generating the
  actual source, run scripts/rendered_visual_check.mjs on its preview and again
  on the ordinary anonymous live URL after publication, with fresh screenshot
  receipts for both viewports and JavaScript-disabled first paint. No selector,
  geometry failure, missing image or measurement error is a pass. The checker
  reads the numeric limits from this standard's rendered_gate header. Store the
  selected visual, source/permission receipt, relevant lesson, crop/label review,
  URL, timestamp and screenshot hashes in the existing proof inventory. Review
  those actual screenshots before marking a page compliant; the script reports
  geometry only and never invents a semantic or playback verdict.
- **Reconcile hero style with this rule.** A composed full-bleed hero is welcome
  where it works. If the usable evidence is a selfie or small authentic moment,
  pair a restrained type layout with that image at an honest size above the fold,
  or use a useful diagram. The older typographic-only fallback does not authorize
  a first screen without a meaningful visual.

The HTML sweep remains an early source-order warning; it cannot measure the
fold. The rendered browser gate plus source-backed editorial review is the
publication acceptance gate. A merged standard, a regenerated skill, an installed
pack and a live-page pass are separate receipts. No whole-fleet success claim is
valid while unsampled URLs, Not Active stops or per-site holds are omitted.
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
- Use the selective-review standard in `agents-draft-humans-send`: execute routine
  rescue work, messages, and publication within recorded authority. Silence never supplies
  missing authority or clears an explicit hold. Stage only the consequential decision
  that still requires advance review, and continue the independent work.
- Rescue toward the function, not the person — see `assign-work-to-a-function`. A rescue
  aimed at an individual who is away is not a rescue.
- **A parked ask carries a date or it is not parked, it is dropped.** Any status row that
  says "waiting on", "blocked on" or "pending <person>" must also say when someone
  comes back to it. A team can check this with a linter that rejects a pending row
  without a timezone-aware recheck date and an accountable next owner. Test a row
  with those fields and one without them before trusting the check. Record actual
  runtime loading and scheduled execution separately; a written rule proves neither.
- Canonical public statement: https://dennisyu.com/unanswered-ask/.
  Public disclosure guide: https://dennisyu.com/agent-disclosure/.
  Marker `UNANSWERED-ASK-RESCUE-2026-09-04`.
<!-- shared-rule:an-unanswered-ask-never-stops-the-work:end -->

<!-- shared-rule:every-article-and-project-starts-with-specific-gct:start -->
## Every opening makes its reader, value and purpose clear

- **Write the specific Goals, Content, Targeting before work begins.** Goals name
  the change the reader or project needs; Content names the source-backed lesson,
  proof or deliverable that will produce that change; Targeting names the people
  and situation it serves. “Publish an article” or “use AI” is an activity, not
  the desired outcome. Use the same brief for the article and the project behind it.
- **For an audit, a missing attendee strategy is an open decision, not a gate.**
  Dennis's October 2, 2026 premium/conference instructions require a base audit
  from existing evidence first. Record supplied, inferred or UNKNOWN goals,
  content and targeting; show a confirm/edit/continue hypothesis when useful.
  Ask only relevant questions whose answers change a recommendation. The
  attendee may continue without answering. Deliver qualified findings and
  conditional sales priorities; missing GCT never lowers reputation. The
  agent's editorial brief still states what this base report helps its reader do.
  See `skills/personal-brand-audit/references/audit-run-contract.md`.
- **Apply the same opening standard to every format.** Documents, reports, PDFs,
  presentations, articles, homepages, landing pages, service pages, relationship
  pages and task guides must earn attention at the beginning. Improve their
  maintained owner in place. A report leads with the decision its evidence
  enables; a guide leads with the task the reader can accomplish; a buying page
  leads with the relevant customer need and the offer's supported value. Do not
  paste a sales pitch or "for entrepreneurs" onto a page whose reader needs
  something else.
- **Put the reader's situation, why it matters and the useful outcome in the
  first 2–3 sentences.** The first line offers a specific reason to continue:
  a recognizable problem, a consequential finding or a true moment with a clear
  lesson. Explain what this page or document helps the reader do and how the
  offered method, evidence or tool helps. The reader may be named directly or
  made unmistakable through their situation. They should not have to scroll
  through history, credentials, an abstract definition or a system description
  to find the point. Write the opening at US fifth-grade reading level or below.
  Use familiar words and short sentences; explain unavoidable terms on first use.
  Put commands, architecture details and specialist terms after this orientation.
  Readers should not have to know the acronym GCT to understand the page.
- **Explain the connection in that same short opening.** Name one useful
  connection and say what it does: the larger process this work serves, a guide
  whose checked result the reader needs first, or the next task that uses this
  result. Link the maintained owned guide on its first useful mention. For
  example: “Use this check before you publish an article, so readers can follow
  its steps. It is the review step in our Content Factory, which turns one
  recording into useful posts and guides.” Verify that the linked page teaches
  the stated process. A list of related links or an unexplained framework name
  does not explain the relationship. When no suitable guide exists, explain
  the connection in place and record the missing guide. Keep the full workflow
  map farther down the page; the opening needs one clear connection, not the
  whole system.
- **Make the value concrete without inflating the promise.** On an entrepreneur's
  Money Tree page, explain how existing customer stories, interviews and useful
  articles connect to what customers can buy. That gives a prospect relevant
  proof and a clear next step. On another page, name that reader's actual useful
  outcome: choose a service, check a result, prepare for a workshop or complete
  a task. "Build authority," "unlock potential" and "follow the stories" alone
  do not explain the benefit. Do not claim increased conversions, revenue,
  speed or certainty unless the evidence supports that exact claim.
- **Use confident, source-backed language.** State the supported value directly.
  Keep authentic moments and compact receipts; do not add doubt, reassurance,
  hype, false urgency, invented statistics or status borrowing. A necessary
  disclosure stays next to its claim. A true story may lead, but its relevance
  and takeaway must become clear in that same short opening.
- **Explain jargon on its first meaningful mention and link the owned explainer.**
  Give the familiar phrase before the specialist label: “the result we want, the
  material we will use, and who it serves — our
  [Goals, Content, Targeting (GCT) brief](https://blitzmetrics.com/gct-business-strategy/).”
  Apply this to other frameworks, acronyms and unfamiliar task terms. Verify the owned
  destination teaches the term; use honest descriptive anchors. If no suitable owned
  explanation exists, define the term in place and record the gap instead of inventing
  a link. Keep this explanation short so it does not bury the lead visual.
- **Make the opening specific enough to judge.** For a shared-memory guide:
  “Use this guide if your AI helpers keep asking you for the same facts. It gives
  them one set of notes, so they can pick up where the last helper stopped. Use
  it as part of [setting up an AI agent](https://blitzmetrics.com/build-agents/),
  a helper that uses tools to do a job.” The project brief also names the
  source files, checks and expected handoff; never invent facts to fill the brief.
- **Review meaning before accepting a score.** Save the exact opening and its
  artifact revision in the existing editorial or proof inventory. Have a
  reviewer identify the reader/situation, the reason to care, the useful outcome
  and the mechanism or evidence supporting it, quoting the actual words. Also
  quote the connection, name the linked destination when one exists, and check
  that it supports the relationship being claimed. Then
  check that the promised outcome is delivered by the body and next step.
  Record PASS, FAIL or UNKNOWN with a concrete reason and the readability
  diagnostic. A short paragraph, keyword, grade score, audience label or
  conversion word alone never passes this gate. If the opening could be moved
  unchanged to an unrelated subject, rewrite it. Unchecked meaning or readability
  stays UNKNOWN; the check belongs in the internal receipt, not public copy.
- **Keep the useful visual with the short opening.** Follow
  `visuals-above-the-fold`: the topic-specific picture or diagram may come first,
  or immediately after the short opening, whichever makes the first screen
  useful. A long GCT card, checklist, changelog or navigation block must not bury
  that visual.

### Money Tree opening example

Before: "A useful conversation becomes a story. The story points to something
you can learn, build or do with us. Here is how those connections look on my site."

After: "Help your next customer see your work and decide what to buy. A
[Money Tree](https://dennisyu.com/money-tree/) links real stories and guides to
the services you sell. It adds clear buying paths to your
[SEO Tree](https://blitzmetrics.com/seo-tree/), the map that links each page to
its main topic."

This is a writing example, not a measured conversion claim. Adapt it to the real
reader, proof and contents of the artifact; do not duplicate it across the fleet.

The maintained public writing standard is
https://localservicespotlight.com/article-guidelines/; the definitive-hub method
is https://blitzmetrics.com/definitive-article-guide/. The older
`/blog-posting-guidelines/` page is an archive and SEO leaf. Improve these owners
in place rather than publishing a competing guideline. No regex can honestly
certify a specific GCT or human comprehension; enforce this in editorial review.
<!-- shared-rule:every-article-and-project-starts-with-specific-gct:end -->

<!-- shared-rule:every-task-execution-writes-a-meta-article:start -->
## Every task execution writes a meta article

- **Write the run record every time the task is executed.** Follow the
  [meta-article guidelines](https://blitzmetrics.com/meta-article-prompt/) and the
  [recipe and run-record relationship](https://localservicespotlight.com/meta-articles/).
  A task's definitive article is the reusable recipe. Its meta article records one
  actual execution. Writing the meta article is required even when publication is
  pending or the run ends failed, partial or blocked after work began. A plan that
  never executes is a plan, not an execution example.
- **Make the record checkable.** Include a stable execution ID; canonical task URL and
  recipe/skill revision; trigger and starting state; date and operator; inputs and
  prerequisite outputs; steps taken and deviations; output and pass/fail results;
  evidence links; lessons; and the next action, artifact and receiving function. Record
  steps, time, token use and cost when measured; preserve UNKNOWN when unavailable.
  Protect credentials and private data, and retain the full record in an authorized
  location when a public-safe version cannot include them.
- **Writing and publishing are different states.** Write and save the meta draft under
  the task's existing authority. Publish or send it only through the applicable
  authorized rail. Preserve draft, reviewed, published and verified states accurately.
  An internal agent note, task comment or publication receipt is useful evidence but
  does not replace the structured meta article. Required writing grants no new send,
  publish, merge, spend or access authority.
- **Close the learning loop with evidence.** Compare this run and prior meta articles
  with the canonical recipe. Propose the smallest supported correction for a missing
  input, ambiguous step, failed check or handoff. Record the decision and version any
  accepted recipe/skill change, using the existing review and publishing authority.
  Link the change back to the run evidence. No improvement is needed when the evidence
  reveals no defect; do not rewrite a working recipe just to show activity.
- **Count distinct executions once per canonical task.** Use the execution ID to
  deduplicate drafts, edits, derivatives and retries within a run. A separately scoped
  rerun has a new ID and its own evidence. Keep failed/partial and unpublished records
  in internal history with their status. Verified execution frequency and dated public
  example volume are separate metrics. Existing reviewed public-article counts remain
  valid as historical article volume even when those articles lack execution IDs; they
  do not establish task frequency. Preserve the evidence and audit date. Execution
  uncertainty remains UNKNOWN or PARTIAL; do not infer a run from a mere link.
- **Do not create a documentation loop with no end.** Writing and revising the meta
  article is part of the original execution. It does not recursively require another
  meta article unless a separate documentation task is explicitly scoped and executed.

No text pattern can prove that a task ran, an artifact passed, or two pages describe
separate executions. Enforce this through the run record, evidence manifest and review.
<!-- shared-rule:every-task-execution-writes-a-meta-article:end -->

<!-- shared-rule:skills-packs-plugins-and-jobs-have-distinct-states:start -->
## Skills, packs, plugins, workers and jobs have distinct states

Use these terms to choose the setup your business needs. Start with one guide and one job. Check the result before you add more tools.

- A **skill** is a written recipe for a kind of task. A **skill pack** is a selected group of skills. A **plugin** is a package for a particular app; it may contain skills, tool connections or other components. Name only what the reviewed package contains. Use the [owned explainer](https://localservicespotlight.com/plugin/) and [pack library](https://localservicespotlight.com/skill-packs/).
- An **agent** is the AI worker doing an assigned task with approved tools and access. A **job** is an assigned run with inputs, checks and a result. A **scheduled job** adds a saved time or supported event; installing instructions does not create a worker or schedule. Link the [agent guide](https://blitzmetrics.com/build-agents/) and [job guide](https://blitzmetrics.com/persistent-agents/).
- **Access** is permission to reach a source or tool in the named account and environment. Record required access, granted scope, observed connection and remaining human action separately. A downloaded ZIP, installed plugin or ready document proves none of them. Never infer approval from a package, task status or connected account.
- **Document-ready** means the recipe has its required content and review. Task Library `complete` is a contributor-supplied document-status claim. It does not by itself prove that the guide meets the required content and review standard, or that a client task ran. Record independent document review, installed-skill activation, source access, scheduled firing, business success and semantic certification separately. Record actual executions separately with their IDs, outputs and checks.
- Make the ZIP a useful first start: include a short start file, a one-task draft prompt, a manifest and dated source information. Say whether it is a guide archive or a platform-installable package. A downloaded snapshot does not update itself. Do not tell readers to delete old copies without considering their rollback and active-job dependencies.
- Use the current maintained marketplace URL and exact package name. Derive any counts from its manifest, with a revision/date; do not equate the broad Task Library with the smaller curated marketplace. Mark older names and installation receipts as historical, and verify actual installed copies before claiming parity.
- Check external platform claims against current official docs for that product, surface, plan and environment. Keep package format, installation, activation, connectors, local-file access and scheduling separate. No blanket promise that every job works on a free plan, on a phone, or while the laptop sleeps. Confirm the actual first run, output and failure handling before calling a schedule observed.
<!-- shared-rule:skills-packs-plugins-and-jobs-have-distinct-states:end -->

<!-- shared-rule:lead-with-the-point-in-plain-words:start -->
## Lead with the point, in plain words

- **Write it so a fifth grader gets it, and put what matters most first, in bold.** This
  covers every surface a human reads: email, Basecamp comments, texts, briefs, run
  summaries, client updates.
- **The subject line is the outcome**, not the job name, and it says whether the reader
  has to do anything. In a synthetic message example, `Two draft checks passed — nothing
  needs you` beats `Daily checks — ops QA: <date>`. This is a format example, not a
  report of an actual run.
- **The first line is one bold sentence**: what happened, then `Nothing needs you` or
  `Needs you: <the one thing>`. Then at most three bold bullets — money, risk, or a
  decision only the reader can make. Say what it means, not what ran.
- **Everything technical goes below a line that reads
  `Details (skip unless something looks wrong)`** — unchanged and complete. Above that
  line: no file names, exit codes, IDs, hashes, timestamps, cron strings or script names.
  Under 150 words, sentences under 15 words, fifth-grade reading level.
- **Nothing is deleted and nothing is softened.** Detail is not the problem, order is. A
  failure is the bold first line, not a footnote — a shorter top never means a cleaner
  story than the run actually had.
- This is `visuals-above-the-fold` applied to writing, and the sibling of
  `lead-with-a-visual-executive-summary`: put the thing that matters where the eye lands.
  A dense report is not a thorough report, it is an unread one.
<!-- shared-rule:lead-with-the-point-in-plain-words:end -->

<!-- shared-rule:reuse-existing-authorized-access:start -->
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
<!-- shared-rule:reuse-existing-authorized-access:end -->

<!-- shared-rule:pick-the-cheapest-capable-fleet-lane:start -->
## Pick the cheapest capable fleet lane

- **Route each job to the cheapest authorized lane that can actually do it.**
  Compare the available runtimes' capabilities, cost, allowance, availability,
  data-handling limits and required review. Lower-cost local text processing
  may suit offline bulk work; an authorized hosted runtime may suit work that
  needs a browser, connector or unattended availability. Verify those facts in
  the actual account rather than assuming a product name establishes them.
- **Choose the execution seat and model tier separately.** This rule picks the
  runtime that owns the job. `model-judgment` picks an appropriate model tier
  inside that runtime. A cheaper model without the required tools or reliability
  is not a capable lane. Include retry and review costs in the comparison.
- **Reserve stronger reasoning and independent review for demanding work.**
  Disputes, consequential research and consequential code or documentation need
  an appropriately capable worker. Experimental output must not be the sole
  basis for a critical action; a qualified person or separate fresh-context
  reviewer checks the original evidence and actual result first.

| Lane | Takes | Hard stop |
|---|---|---|
| **Offline text lane** | Authorized transcript triage, first drafts, preliminary analyses and bulk rewrites that need no external tools | No browser, login or publication unless separately supported and authorized. Confirm device availability before relying on it |
| **Hosted volume lane** | Bounded repetitive work with tested tools, access and sufficient allowance | Do not route consequential reasoning here merely because it is cheap. Verify unattended availability rather than inferring it from hosting |
| **Reasoning and review lane** | Hard reasoning, disputes, consequential research, code and documentation | Preserve independent review and specialist requirements. A model name alone does not establish competence |
| **Existing recurring lane** | A recurring job whose current owner, schedule and result have actually been observed | Retain one owner while testing a replacement; an instruction or saved schedule alone does not prove a successful firing |
| **Action or publishing lane** | Work requiring a specific authorized connector, account, destination or approval route | Stay within recorded authority. Access to one service or account does not establish access to another |
| **Specialized lane** | Work only a particular approved runtime can reach or perform | Record the capability that justifies the cost; do not move work solely because another product is available |

These are capability categories, not claims about any installed fleet. Record
the actual runtime and tested capability in the team's private job record.
One agent name may cover multiple execution environments; route by the environment
the task needs. Product prices, quotas and capabilities need current verification
for the specific plan and account. Token meters from different providers are not
automatically comparable. This rule does not authorize another subscription.

- **Keep one outcome owner and one active execution lane per job.** A fallback
  model within that lane can handle an approved failure path. It must not create
  a second independent owner or repeat an external action whose result is uncertain.
- **Migrate through a controlled cutover.** Test the replacement in a paused,
  dry-run or otherwise isolated state that cannot duplicate production effects.
  Reconcile pending runs and uncertain writes, pause the old trigger, transfer
  ownership through the authoritative task record, then enable the replacement.
  Verify its actual result and retain the previous configuration for rollback.
  If a safe cutover is unavailable, retain the current owner and record the blocker.
- **Instructions do not grant authority.** Sending, publishing, spending,
  installing, changing access and deleting require the owner's existing authority
  and applicable approval rails. Keep passwords, tokens, account inventories and
  private schedules out of this rule and its public copies.

### Synthetic example — recurring media indexing

This is a fictional routing exercise, not an account or schedule receipt. A
recurring media-indexing job needs an authorized browser session and availability
at its scheduled time. An offline text runner without those capabilities is
unsuitable even if its marginal model cost is lower. A tested hosted volume lane
may fit; a stronger reasoning lane is unnecessary unless the task's decisions
require it. Check actual access and allowance, then use the controlled cutover
above if changing an existing owner. No account connection or schedule is created
by this example.

No regex can honestly decide which lane a job needs. The owner and reviewer apply
the capability table to the actual task, and the receipt names the tested runtime,
permitted effects, cost evidence or UNKNOWN, result and remaining limitations.
<!-- shared-rule:pick-the-cheapest-capable-fleet-lane:end -->

<!-- shared-rule:audit-quality-gate:start -->
## Audit deliverables preserve evidence and pass independent quality review

- Apply the [Universal Audit Quality Gate](https://github.com/dennisyu/local-service-spotlight-skills/blob/69b00032c482826d6934ba24c04604d4dddf1b22/docs/audit-quality/README.md) to content, document, SEO, website and operational audit deliverables. Pin the actual standard/profile revision and adoption state. It assesses report quality; keep specialist exam weights, caps, coverage and pass lines separate.
- Preserve valid detail, proof, examples, citations and meaningful visuals. Map baseline items to final locations; justify corrections, outdated/incorrect removals and authorized privacy omissions. More than 10% extracted-text loss or any missing substantive item triggers semantic review, not an automatic verdict.
- Trace material claims to exact dated sources; distinguish FACT, DECIDED, PROPOSED and UNKNOWN from OBSERVED, REPORTED and INFERRED evidence. Missing evidence is null, never zero. Inspect hidden artifact content and public links for privacy.
- Fix authorized defects at the source, propagate to every dependent output, and retest the actual final artifacts. Require fresh-context content/privacy and design review of the exact final revision. Preserve all applicable holds and consequential human decision thresholds; do routine authorized work without unnecessary review requests.
- The proposed default quality profile uses weights 25/25/20/15/10/5 and threshold 85, plus hard gates. Calibrate before operational scoring; uncalibrated scores stay provisional. No critical/major defect or missing required evidence passes through a high score.
- Release through one authorized owner using current destination-specific access, preimage and rollback. Verify private recipient delivery or anonymous public body, canonical, mobile, links and downloads as applicable. Observed harmful live defects require authorized containment; unavailable readback alone stays unverified. Keep versioned receipts and previous editions.

- When adopting the proposed UAQG1.1.0 tier annex, pin the product profile separately from the specialist exam: paid/full, free/bounded diagnostic or bulk/screening. Lower cost narrows agreed coverage, never truth, privacy or review. Bind required checks and typed review receipts to every exact final artifact hash; preserve source locators, semantic page visuals, distinct link/access/media states and UNKNOWN time/cost. Paid/free material judgments need independent review. Validate every bulk record, review flags and a reproducible random sample, and keep unreviewed leads SCREENING. Preserve the six dimension meanings, weights and calibration gate; stop on missing access, exhausted allowance or a stale review. See the [tier contract and tests](https://github.com/dennisyu/local-service-spotlight-skills/blob/main/docs/audit-quality/tier-contracts.md).
- For every new audit governed by this pack, follow the [common execution gate](https://github.com/dennisyu/local-service-spotlight-skills/blob/main/docs/audit-quality/enforcement.md). Read current instructions in the actual runtime, retain all valid baseline detail, obtain exact-final independent review, and run `docs/audit-quality/verify_bundle.py` against the private final files and evidence snapshots before release and after delivery readback. Synthetic exercises never establish production acceptance. A bundle consistency result cannot certify source truth or supply missing calibration. Delivery plus verified filing is required; record runtime adoption and real-run results separately. Use the existing owner, publisher and review clock; no new access or job is implied.

No regular expression honestly certifies semantic fidelity, evidence quality or independent review. These are evidence-backed review gates; counters are screening aids. This public procedure is a proposed quality profile until its receiving owner records adoption; it grants no new account access, publication authority or schedules.
<!-- shared-rule:audit-quality-gate:end -->

<!-- shared-rule:update-the-canonical-master-never-start-a-silo:start -->
## Update the canonical master, never start a silo

- **Before you inventory assets or publish a definitive article, hub or list page, find
  the master that already owns that topic, read it, and make your work an update to
  it.** Your output is a delta against the master — added, changed, confirmed,
  dropped — never a fresh standalone list or a second canonical page or tracker for the
  same subject. Supporting pages link up to the master.
- This extends `named-entities-link-to-the-most-helpful-canonical-destination` (one
  topic, one owner in the SEO Tree) from links to whole runs, and generalises the
  in-place rule `positive-mentions-harvester` already applies to mentions inventories.
- **Why:** a partial list pasted into a prompt may omit items already in the
  maintained inventory. Treating it as the master can produce duplicate “new”
  findings, conflicting counts and a skipped part of the original request.
  Reconcile the actual master and requested scope before adding a second list.
  Supporting pages should strengthen the same topic owner rather than compete.

### Pre-flight, every run, before the first search or the first draft

1. **Resolve the master.** Look up the topic in `docs/canonical-masters.json` in the
   skills repository. If it is not there, or you do not have the repository, search
   whichever of these you can reach before concluding no master exists, and record
   which you could not reach: shared memory, the Canonical Directory and Task Library,
   site search across our domains by title *and* by likely slug (two slugs can serve
   one article), and the Drive or repository the team uses.
2. **Learn it (L of LDT).** Open the live master and read its method, its stated update
   cadence and its source of truth. If the master says the count comes from one place,
   that place is your baseline — not memory, not a number in the prompt.
3. **Treat anything pasted into your prompt as a skin, not the master.** A list,
   count or excerpt in a prompt is a copy that may be stale. Re-derive it from the
   master; if they disagree, the master wins and you report the gap.
4. **Claim the work** in your team's shared work-claims ledger, where one exists, with a
   claim id that names the work and the pass, for example
   `master:<topic-slug>:<pass>:<YYYY-MM-DD>`. If someone else holds it, stop and name
   the holder. If the ledger is unreachable, proceed and say a duplicate is possible.

### Doing the work (D of LDT)

- Deduplicate against the master's **source of truth** (`source_of_truth` in the
  registry), not against its visible table — which may be partial — and never against
  a list you were handed.
- Write your result as a delta that names, for each item, which of these it is:
  already in the master, net-new and verified, candidate needing a check, or dropped
  with a reason.
- Apply the delta **in place**: the master sheet first, then the hub, then every derived
  page (skin) that repeats its numbers, so they all show one number from one source. If
  the master sheet's location is unknown, do not create a new one; record the gap and
  apply the delta to the hub. Where those skills are installed, use `one-master-merge`
  when a second competing copy already exists and `congruency-audit` to confirm the
  master and its skins agree afterwards.
- **If no master exists, you are creating it.** Create exactly one, register it in
  `docs/canonical-masters.json` in the same change, and link it into its SEO Tree
  parent. If you do not have the repository, record the new master's location in your
  run's meta article instead.

### Closing the loop (T of LDT)

- Write the run's meta article and link it to the master.
- If the master's method was missing a step you needed, propose the smallest supported
  fix to the master's method (or its skill) in the same session, under existing
  authority — do not leave the fix only in your run notes.
- Update the master's `last_verified` in the registry with what you opened and when, or
  record it in the meta article if you do not have the repository. Do not copy the
  master's counts into the registry; that is a second source.

### How this maps to Content · Checklist · Software (CCS)

- **Content** is the master hub and its published method — the thing a reader and an
  agent both learn from.
- **Checklist** is this pre-flight. It is what turns "check what's already there" from a
  hope into a step every agent runs.
- **Software** is the registry file, the skill that owns each topic, and the claims
  ledger. The registry is hand-maintained, not generated, and a congruency audit is its
  only check. A registry entry whose owning skill is not in this repository is a known
  gap and is recorded as one, not papered over.
- CCS reads in build order when the Content already exists, as it did here: the master
  hub is the Content, this pre-flight compresses it into a Checklist, and the registry
  and skill are the Software. `capture-what-you-learn`'s Checklist-first order is for a
  brand-new rule that has no Content yet. Both hold.

### Exemption

None for inventories, definitive articles, hubs or list pages. A one-off answer in chat
that publishes nothing and creates no file needs no pre-flight. A supporting post or
meta article does not need its own master; it links up to the one it supports.

No regex can honestly prove an agent looked for the master before it started, so this
rule carries no `checks` block. It is enforced by being read pre-flight, by the
registry, and by a congruency audit catching two surfaces that publish different
numbers for the same thing.
<!-- shared-rule:update-the-canonical-master-never-start-a-silo:end -->

<!-- shared-rule:audit-method-and-correction-propagation:start -->
## Audit the business and propagate every correction

- Use the shared audit run contract in the maintained marketplace at
  `skills/personal-brand-audit/references/audit-run-contract.md`; its teaching
  edition is https://blitzmetrics.com/how-we-audit/. Start with the subject's
  business goal, offer and buyer, then proof inventory, gap, ranked actions,
  visual cited report, authorized implementation and weekly MAA.
- Deliver the base proof audit first. For premium/conference participants,
  confirm clear supplied GCT, label inferred strategy for confirm/edit, and
  ask only relevant optional questions. Continue without answers with
  conditional priorities; missing GCT never means low reputation. Preserve
  the base report and show changes after clarification.
- Pin the input, exam family, rubric/version, source hash and report template.
  The ten-row Brand Authority, seven-component SEO/Growth, Website QA checklist,
  local/GBP product and Reputation-to-Sales Gap are separate exams. Do not invent
  weights, substitute one for another, average them, or use an older report as
  the rubric. The 30-point scale ranks individual proof items only.
- UNKNOWN is not zero. Incomplete required evidence means a known subtotal and
  INCOMPLETE with no pass verdict, without renormalizing weights. Use N/A only
  under the pinned rubric's denominator rule. Calculate headlines from the rows;
  keep a documented cap separate from the raw total. Compare deltas only within
  the same exam/version and comparable coverage.
- A correct graph object, a panel visible in a normal name query, and a claimed
  panel require separate receipts. Query-match strength is not authority.
  Blocked or unperformed checks remain UNKNOWN. Public controls do not prove
  owner claim status, and coappearance does not prove friendship or endorsement.
- Correct one authoritative fact first, identify every dependent report,
  summary and leaderboard, and regenerate/inspect them at the new revision.
  A retired claim surviving in one final PDF blocks that batch. Test arithmetic,
  UNKNOWN, rubric version, entity/panel separation and correction propagation;
  inspect actual renders independently. A page count is not visual QA.
- Record actual tool/skill use, platform/model/effort or UNKNOWN, source and
  capture times, allowance constraints and human rework. Separate documented
  capabilities from observed executions. Publish useful teaching, keeping raw
  private dictation and customer information in authorized private records.
- State the inventory's source boundaries and counted unit. Public channel
  assets, feed releases, distinct conversations, guest appearances, clips,
  website posts and private camera/audio masters are different units. Enumerate
  every page of the declared public sources; retain unresolved external leads.
  Cross-posts and multipart releases need explicit joins, not a summed headline.
  Missing video does not prove audio-only. Raw-source holdings remain UNKNOWN
  unless actually inventoried; never divide public uploads by releases and call
  that a verified repurposing ratio.
- Make a substantive business report: first two pages answer the buyer's
  question, major findings pair evidence with an implication and action, and
  charts keep sample, denominator, date and precision beside the number. Report
  content performance by comparable format/date coverage; views are not sales.
  Use distinct commercial lanes until the current product and goal are verified.
  Existing automations/offers require observed-output and outcome checks, not a
  proposal to create them again. Every physical PDF page needs readable type,
  correct numbering, useful composition and an actual final visual review.
<!-- shared-rule:audit-method-and-correction-propagation:end -->

<!-- shared-rule-index:start -->
## Other house rules that apply to this work

These are not repeated here because they govern published pages rather than agent behaviour. They are binding all the same — read the full text in `AGENTS.md` or `standards/` before touching a website.

- **Analytics goes on before anything gets optimised** (`analytics-on-every-page`)
- **A button must contrast with what it sits on** (`buttons-must-contrast-with-their-background`)
- **Every article has pictures** (`every-article-has-pictures`)
- **Every public page shows real people or real work** (`every-public-page-has-real-imagery`)
- **Icon-only social controls stay tappable and separate** (`icon-only-social-controls-stay-tappable`)
- **Personal-brand heroes are immersive, not boxed** (`immersive-hero-standard`)
- **Every link and every entity claim resolves** (`links-must-resolve`)
- **Never ship a black button** (`no-black-buttons`)
- **Placeholder copy never reaches production** (`no-placeholder-copy`)
- **No popup on page load** (`no-popup-on-load`)
- **No unnamed link text** (`no-unnamed-link-text`)
- **Nothing plays at the visitor uninvited** (`nothing-plays-uninvited`)
- **Order proof by authority, strongest first** (`order-proof-by-authority`)
- **A photograph has to earn full bleed** (`photo-earns-full-bleed`)
- **Show the moment, not the resume** (`show-the-moment-not-the-resume`)
- **Every URL we say out loud resolves** (`spoken-urls-must-resolve`)
<!-- shared-rule-index:end -->
