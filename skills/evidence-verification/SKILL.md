---
name: evidence-verification
description: Establish what is actually TRUE about a client and prove it with records a stranger can check. Find the hard anchors hiding in public registries (Secretary of State, bar admission, ISBN, patents, ORCID, authority files), verify identity by matching a second fact rather than a matching name, and never let "we haven't looked yet" render as "they scored badly." The upstream skill every authority skill depends on — knowledge-panel-entity-seo, grokipedia-authority and ai-search-visibility all fail the same way when the underlying facts are wrong.
---

# Evidence Verification

**Use this when** you are about to assert something about a client in public — a schema field, an encyclopedia submission, an audit score, a bio, a Knowledge Panel claim — and you want to be certain it is true, and provable by someone who does not trust you.

This skill exists because of a specific, repeatable failure. In July 2026 our records described a client as a *style and image coach in Austria*. She is a *sewing author in South Tyrol, Italy*. The error had been flagged in a research note five weeks earlier and never actioned. It was one submission away from putting a false description of a real person into an encyclopedia — which would then be scraped by every AI assistant that reads it.

Nothing about that failure was exotic. A field was wrong, a note said so, nobody carried it through, and the next system downstream treated the field as fact.

## The one idea

**A fact about a client is not established until a stranger can check it without asking you.**

Your client's own website is not evidence of anything except what your client wants to say. A testimonial is not evidence. A follower count is not evidence. What counts is a record held by someone with no stake in the outcome: a government registry, a national library, a court, a standards body, a publisher, a newsroom.

Everything below is machinery for finding those records and refusing to fake them.

---

## Part 1 — Find the anchors nobody looked up

Most clients already have hard, verifiable public records. Nobody has searched for them. Work this list in order of how cheap the win is.

### The business registry — the anchor almost every client has
Every LLC, corporation and partnership is registered with a state or national authority, and those records are **free, public, and name the officers**. In the US it is the Secretary of State (or Corporation Commission); in the UK, Companies House; most countries have an equivalent.

What you get: legal entity name, charter or company number, formation date, status, registered address, and — the part that matters — **named officers, managers and registered agents**.

Worked example. A client was known to us only as "Roland." No surname in eleven email threads, none in the client tracker. His business was a registered Louisiana company:

> JUNKS ABOVE LLC · charter 42116285K · filed 30 December 2015 · Active, in good standing ·
> Officer: **ROLAND LEBLANC**, title Manager · domicile 4626 D'Hemecourt St, New Orleans

Two minutes in a public database produced a surname, a title, a formation date, and a verifiable charter number. **Nearly every local-service client on a roster is an LLC owner**, which means most clients sitting at zero corroboration have an anchor like this waiting, unclaimed.

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

In the Roland example the identity proof was not the name. It was that the registry's domicile address and the address on the shop's website were the same street address. Same name in the same city would have been a guess. Same name *and* same address is an identification.

The inverse error is just as costly. A client was filed as a "namesake trap" — the Wikidata item matching her name was assumed to be somebody else. Five weeks later the record was followed properly through its authority file to the national library, which showed it was **her own item all along**. The stale warning had been suppressing her score and excluding her from work for over a month. **A warning that has been disproved is worse than no warning**, because nobody re-examines someone the file says is unsafe to touch.

So:
- Two identifiers agreeing = identified.
- One identifier = a hypothesis, and it must be labelled as one.
- A namesake flag must carry the evidence and the date it was established, so it can be re-tested rather than inherited forever.

---

## Part 3 — Read negation

Research prose records absence as often as presence. Your own notes will say:

> "Confirmed to have NO Knowledge Panel, NO Wikipedia, NO Wikidata and NO Grokipedia."

A keyword matcher scanning that sentence finds *Wikipedia*, *Wikidata* and *Knowledge Panel* and records three anchors the client does not have. That is exactly what happened to a client audit in August 2026: the sentence documenting that he had nothing was read as proof that he had everything, and it promoted him to "ready to submit."

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

Then enforce it with a test that fails if any scored entity has a score of zero, and another that checks the UNKNOWN action text describes *our* next step rather than the client's deficiency. Wording drifts; tests do not.

---

## Part 5 — Carry the evidence into the artifact

Research that stays in a research file is wasted. Whatever you produce at the end — a submission, an audit, a schema block, a pitch — must carry the specific verifiable anchors, not a summary of them.

A generator that says *"active professional presence; any press, podcast appearances, books"* has thrown away everything that mattered and produced filler that reads as unsourced. Compare:

> **Before:** "Documented independently; entity home with structured data; active professional presence."
>
> **After:** "Independently verifiable: published by Springer Nature; ISBN 978-3-662-62443-2; authority records GND 130452106, VIAF, ISNI; Wikidata Q108866818; existing German Wikipedia article."

The second one a reviewer can check in four clicks. The first one is a shrug.

And when there is **no** hard anchor, say so loudly in the artifact rather than dressing up the absence. A package that admits "no third-party anchor found — expect rejection, surface one proof first" is more useful than one that bluffs and gets bounced.

---

## Part 6 — Fix at the source, in the same run

Every failure in this document has the same shape: someone found the problem, wrote it down, and moved on.

- The wrong niche was recorded in a research note five weeks before it nearly shipped.
- The disproved namesake trap was resolved in one file and left standing in another.
- The "does this have any hard anchor?" check existed in two places; adding a new anchor type updated one and not the other.

So:
1. **Fix the source record**, not just the output. If the roster is wrong, fix the roster.
2. **Make the contradiction self-detecting.** If two records disagree about the same identifier, that is a testable condition. Write the test; do not rely on someone noticing.
3. **One authoritative definition.** If a rule is expressed in two places, they will diverge — usually at the moment someone extends the system, which is the worst possible time.
4. **A note saying "X is wrong and should be corrected" is not a correction.** Either fix it in the same run or file it somewhere that fails until it is fixed.

---

## How to run it

1. **Inventory** — list every client, partner and entity. Mark active/inactive from the authoritative source, and record a *reason* for every inactive one.
2. **Probe what already exists** — before researching anything, check whether the entity already has a Wikipedia page, Wikidata item, Knowledge Panel or Grokipedia page. Run controls first: a known-good lookup and a deliberately nonsense one. **A check that cannot fail is not a check.** (Our first fleet run found pages already existed for a client and for one of our own companies — nobody knew, and nobody was checking them for accuracy.)
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
- **grokipedia-authority** — the encyclopedia submission. Its "Insufficient Citations" rejections are this skill's absence, showing up downstream.
- **ai-search-visibility** — what ChatGPT and Perplexity say about a client is assembled from exactly these records.
- **positive-mentions-harvester** — finds the press; this skill decides which of it is a real anchor.
- **client-access-checklist** — access is the precondition for measuring; verified identity is the precondition for publishing.
- **recursive-self-improvement-qa** — the discipline in Part 6 is that skill applied to facts instead of code.

## Learned in the field

*Appended automatically by the self-improvement loop (Skill-Learnings/): dated lessons from real runs. Newest at the bottom.*

<!-- learning:2026-08-02-a-row-in-a-table-is-not-a-page -->
**August 2, 2026** (from: grokipedia-fleet)

**August 2, 2026** (from: grokipedia-fleet)

We had 24 skills and nowhere to send someone who asked what one of them was.

Each skill existed in three places — a markdown file in the repo, a file inside every pack
zip, and a single row in a table on `/skill-packs/`. All three are real. None of them is a
page. There was no URL for "what is evidence-verification and why would I run it," which
means there was nothing for a search engine to rank, nothing for an AI assistant to cite,
and nothing to link to in a client email.

That is the same mistake we diagnose in clients every week. A capability that exists but has
no citable address does not exist to anything that reads the web.

Fixed by generating one page per skill from the master `.md` files — 24 pages at
`/skills-<slug>/`, each carrying the same five-rung ladder block as the rest of the system
tree, each linking up to the pack directory and across to the Task Library.

Three things worth carrying forward:

**Generate, never hand-write.** The pages are built from the skill files that already exist,
so a skill and its page cannot describe different things. The moment someone edits a page in
wp-admin, the next run overwrites it and nobody finds out for weeks. Say GENERATOR-OWNED in
the file header, and mean it.

**A new tier of pages needs a new line in the verifier, the same day.** Twenty-four pages went
live at once, entirely outside the daily link-graph check. That is precisely how
`aibuilderspotlight.com/skill-pack` linked to nothing for weeks inside green reports. The
verifier now checks that every master skill on disk has a page linked from the directory, and
samples three live pages per run on a rotating index so all of them get covered over time.

**A page tier needs a line in the runner too, or it becomes a slower clock than its source.**
The daily job rewrites the master skill files every morning. Without a regeneration step the
published pages would keep describing whatever the skill said the day they were generated,
while the directory printed a fresh "last updated" date next to them — a stale page wearing a
current timestamp, which is worse than an obviously old one. This is the third time the same
defect has appeared in this system (Dorine's mirror pack, the cloud runtime mirror, now the
skill pages). **Any artifact derived from a source that changes daily needs its own step in
the daily job.** Look for the pattern rather than waiting to be bitten by it a fourth time.

One smaller thing, worth its own note: the page generator imported `propagate_all_packs` just
to read its `MANDATED` list. That module parses `sys.argv` at import time, so the generator's
own argument errors came out under the propagator's name and usage text. **Never import a
module that acts at import time in order to read one constant from it** — parse the constant
out of the source instead.

<!-- learning:2026-08-02-a-placeholder-that-reads-as-a-sentence-will-be-printed-as-one -->
**August 2, 2026** (from: SOMBA audit-cover regeneration, second pass — 30 live audits still carried the placeholder nine hours after the fix was declared closed)

# A placeholder that reads as a sentence will eventually be printed as one

**2026-08-02 (second pass, same day)**

## What happened

Earlier on 2 Aug we found that `gct.py`'s keyword archetypes had been printing invented
positioning lines on audit covers — "personal auth**ority**" → author → "helps aspiring authors
finish their book" — and that 27 members whose niche matched nothing were shown the raw
fill-in-the-blank: *"Helping your ideal client a specific, nameable result."*

We fixed the cover, regenerated all 104 audits, verified every cover line was distinct and
grounded, added `tools/test_audit_grounding.py` to block a recurrence, and told the client it
was closed.

It was not closed. Nine hours later, while browser-testing an unrelated new feature on
Claudius Krucker's dashboard, the same string appeared on screen. **Thirty of the live audits
still contained it** — in the "a sharper version to try" card and on the agent-team page. It
was also one build away from Jane Omorogbe's personal-brand *website*, because `site.py` reads
the same triple, and Agnieszka Figielek's site was set to go live describing her zero-emission
building academy as helping "families planning a build or renovation" — the same substring
collision that mislabelled Claudius, on a public site rather than a PDF.

Three of the thirty unmatched members are Sigrun's mentors: Ina, Jagoda, Katrin. So the three
people who raised the complaint would have opened their own audits and found the complaint
still true.

## Why the first fix missed it

The test asserted the right property (`no fabricated line`) against the wrong scope (`the cover
element`). It parsed `<h1 class="mission serif">` out of each audit and checked that one string.
That is exactly where we had been looking when we found the bug, and looking there again is not
verification — it is re-reading your own patch.

`grep -c "a specific, nameable result" audits/*.html` would have taken four seconds and returned
30. Nobody ran it, because the fix felt complete.

## The two lessons

**1. Scope a regression test to the string, not to the place you found it.**
If the defect is "this text must never describe a member", the test is a scan of every built
document — audits, dashboard, team board, member websites — not an assertion about one element.
`tools/test_receipts.py` now scans 113 built files for four forbidden strings.

**2. A placeholder that reads as a sentence will be rendered as a sentence.**
The deeper mistake was ever having a fallback value that is grammatical, first-person and
member-shaped. Every caller was supposed to check `matched(p)` first. Callers forget; that is
what callers do. The durable fix is for the value itself to be harmless:

- `UNMATCHED` is now ordinary English that asserts nothing and reads naturally in every
  sentence template we own — `("the people you serve", "get the result you're known for",
  "your method")`.
- `gct()` returns `suggested=None` when nothing matched, so "here is a better line for you"
  cannot be fabricated at all. A forgetful caller now gets a `None` — loud — rather than a
  plausible sentence about a person who does not exist.

Design rule to carry forward: **make the unsafe value unusable, not merely conditional.** A
guard you must remember is a guard that will be forgotten. This is the same shape as the
`git_askpass` bug from this morning (a branch that could never fire) and the frozen team-board
roster (a hand-maintained list beside a generated one) — in all three, correctness depended on
a human remembering something at the call site.

## Related

- `receipts.py` — every claim now carries its inputs and its rule; a claim with no basis is not
  returned at all, so "unsourceable" is a structural impossibility rather than a test finding.
- `tools/test_receipts.py` — the whole-document scan, plus a check that receipts.py's restated
  score arithmetic still equals `score.py` for all 104 members.

<!-- learning:2026-08-03-a-compromised-site-must-not-outscore-a-clean-one -->
**August 3, 2026** (from: weekly-fleet-hub-audit v2, fleet-wide proof enrichment)

### Rankings are evidence about *someone's* work — check whose before you score them

The fleet scoreboard rates every site on PROVE: Domain Rating, organic traffic, and the
breadth of keywords it ranks for. On August 3, 2026 the two sites whose keyword breadth
looked strongest were **philmershon.com (15 ranking keywords)** and
**theathletespotlight.com (5)**. Both readings were the attacker's, not the client's.

Pulling the keywords themselves rather than the count showed philmershon.com — a speaker
coach — ranking for `hollymoviehd`, `borat thong`, `nintendo store`, `jupiter 125 black
colour`, `silver aranjanam for baby boy`. Fourteen of its fifteen keywords were junk. On
theathletespotlight.com it was five of five: `activa 6g best colour`, `bici decathlon`,
`charola de unicel`. Selecting `best_position_url` alongside the keyword named the cause —
every junk term ranked on an injected path:

    /product-similar-image/?<digits>
    /product/category/<digits>
    /shop/manufacturer-site?&transition=top<digits>

with a per-site numeric suffix (`…1310` on one, `…1760` on the other): one kit, two of our
sites. Uncorrected, philmershon.com scored **impact 40**; netting the injected rankings out
drops it to **21** — an eight-point BIS swing. A compromised site was being rewarded for
being compromised, and would have been reported as a fleet-best performer.

**Rules:**

1. **Never score a ranking you have not attributed to a URL.** `org_keywords` is a count of
   things Google associates with the domain, not a count of the client's wins. Select
   `best_position_url` and read the paths before any keyword number reaches a score or a
   report.
2. **Net hostile rankings out of the score and raise them as an action instead.** Traffic
   attributed to injected URLs gets discounted in the same proportion. Infection is a
   dispatch item, never a credit.
3. **Judge the keywords by fit with the person, not by how spammy they look.** `nintendo
   store` is a fine keyword — for a games retailer. The tell is a *speaker coach* ranking
   for it. The GCT already states who each site is for; compare against that.
4. **A clean sitemap and a clean REST API do not mean a clean site.** Both sites' sitemaps
   and post lists were entirely legitimate, and their real content is real. The injection
   lives beside WordPress, in URL space the CMS never enumerates — so any check that walks
   the sitemap or `/wp-json/wp/v2/posts` is structurally unable to find it. What Google has
   indexed is a separate source of truth from what the CMS will admit to.
5. **404 today does not mean clean.** These URLs now return 404 to human and Googlebot
   alike from a datacenter IP, while still ranking. That is consistent with cleaned-but-
   still-indexed *and* with a cloak keyed to something the probe can't reproduce. Say which
   of those you have ruled out; removal still has to be requested in Search Console either
   way, because the junk keeps ranking after the files are gone.

Companion to the same day's `classify-the-metric-dont-just-count-it` (referring domains,
same disease one metric over): fleet median referring domains is 368 against a median of
**26 dofollow**, because a `.shop`/`.store` link-spam blast hits every site daily. Report
`refdomains_dofollow`; `refdomains` is noise. billybatt.com reads as 324 referring domains
and is actually **2 dofollow, both of them ours** — the authority problem the number
appears to have solved is entirely intact. Ahrefs exposes an `is_spam` flag; use it.

Learned August 3, 2026.

<!-- learning:2026-08-03-buckets-must-partition-the-thing-they-explain -->
**August 3, 2026** (from: weekly-fleet-hub-audit v2, phase 1 down-site triage)

### If a report splits a set into buckets, assert that the buckets add up

The fleet audit deliberately splits unreachable sites two ways so a WAF block is never
reported as an outage: `genuinely_down` (DNS/TLS/connection failure) and `waf_suspect`
(403 from our crawler's IP). The runbook says to read those two lists rather than the raw
"Homepage NOT reachable" line, because the raw line conflates them.

On August 3, 2026 the raw line said **4** and the two buckets said **1 + 2**.

The missing site was **owenhemsath.com, returning a real HTTP 500** — a genuine outage on
our own AWS fleet host, up and healthy the week before. The classifier had always produced
a third kind, `http_NNN`, for real 4xx/5xx; nothing ever consumed it. So a site could be
hard-down and appear in *no* dispatch list, while every summary line in the report stayed
true. Following the runbook exactly would have made a live outage invisible for a week.

Fixed in `audit_fleet.py` and `_combine_batches.py`: an `http_error` bucket plus an
explicit `down_unclassified = down − (genuinely_down ∪ waf_suspect ∪ http_error)` that
prints a loud warning when non-empty. Proven able to fail before being trusted — injecting
a bogus `_home_kind` into a scratch copy put the site in `down_unclassified` and printed
the warning.

**Rules:**

1. **Every partition gets a residual bucket and an assertion.** Whenever a report explains
   a total by splitting it into categories, compute `total − Σ(categories)` and surface it
   loudly. Categories that came from an enum will silently drop members the day the enum
   grows a value.
2. **A value the producer emits and no consumer reads is a latent hole**, not dead code.
   Grep the consumer for every value the producer can return.
3. **The conflated line is the honest one.** When a summary offers both a raw total and a
   nicer breakdown, treat any disagreement between them as the finding.
4. **Read deltas for artifacts before narrating them.** The same run's `needs_hub` went
   84 → 85 with "1 resolved: owenhemsath.com" — which reads as progress and was the outage:
   `needs_hub` requires `homepage_up == yes`, so a site leaves the list by going *down*.
   Any queue gated on reachability shrinks when sites break. State that in the report rather
   than counting it as work completed.

Learned August 3, 2026.

<!-- learning:2026-08-03-a-timed-out-tool-call-is-not-a-stopped-process -->
**August 3, 2026** (from: skill-pack-propagation daily run, August 3, 2026 — the runner was launched twice against live production sites)

A timeout is a fact about the observer, never about the observed. When a tool call that
started a long job returns "Request timed out", the job is still running; what ended was
the wait, not the work. On August 3, 2026 the daily propagation runner was started, its
tool call timed out mid-step-3, the session's process list showed no active sessions
because the *wrapper* had detached, and the run was relaunched as though it had died. It
had not: the original was three minutes in and already uploading zips. For ninety seconds
two copies of a pipeline that publishes to eight live WordPress sites ran concurrently,
interleaving their output into one log — one at step 3 rebuilding agent pages while the
other at step 4 swapped the zip URLs underneath it. The duplicate was killed by PID and
the original finished clean, but nothing in the tool's error had said which was true.

Before relaunching anything that mutates shared state, confirm the previous attempt is
actually dead — by process table (`ps -eo pid,ppid,etime,command | grep <script>`), by
lock file, or by a heartbeat the job itself writes. A session-level "no active sessions"
answers only whether *this session* is still attached, which is a different question. The
same discipline applies to any probe: a fetch that times out means the request did not
complete, not that the site is down; a publish call that times out means the response was
lost, not that the write was — re-read the target's state before retrying, or an idempotent
retry becomes a double write. Vary time before you vary anything else, and prove the prior
run is stopped before you start another.

<!-- learning:2026-08-03-a-check-that-can-quietly-not-check-reports-green-either-way -->
**August 3, 2026** (from: skill-pack-propagation, August 3, 2026 — adding a concurrency gate exposed two ways a gate can disable itself)

A guard that can silently decline to run is worse than no guard, because it still prints
the green line. Adding one concurrency gate to the daily runner on August 3, 2026 exposed
two instances within ten minutes. First, the runner invoked it as `[[ -x ./tools/x.sh ]]
&& run it` — so a lost executable bit, from a zip round-trip or a clone or a copy that
did not preserve mode, would skip the gate and say nothing. Gate on existence, invoke
through the interpreter (`zsh ./tools/x.sh`), and make ABSENT a hard failure, not a skip.
Second, the runtime-completeness test derived its required-file list by scanning the
runner for `python3 <path>.py` invocations — correct, and blind to the `./tools/x.sh` the
runner had just gained. It printed "COMPLETE — all 31 referenced paths are present" while
the new gate was absent from the cloud runtime entirely. A derivation that understands
only one of the languages its source is written in is a hand-maintained list wearing a
derivation's clothes; it drifts exactly like one, but with more credibility.

The general form: for every automated check, ask what makes it a no-op — a missing file,
a permission bit, a resource already held, an empty input, a regex that matches nothing —
and make each of those loud and distinguishable from a pass. The self-test added that day
correctly declines to run against a live lock, which is right; the runner then reported
"guard OK ()" with an empty count, which was not. "NOT CHECKED" and "PASSED" must never
render the same. When you extend a pipeline, extend the thing that verifies the pipeline
in the same change, and confirm the verifier actually fails before you trust it passing.

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
  at eighth-grade reading level or below, name who this is for, what it does, why
  it matters and the useful outcome. Keep the topic-specific visual beside that
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
- This does not loosen `agents-draft-humans-send`. Rescue means doing the *work* yourself,
  never dispatching messages, publishing, spending or deleting on someone's behalf because
  they went quiet. Where the rescue would cross that line, stage it and say so.
- Rescue toward the function, not the person — see `assign-work-to-a-function`. A rescue
  aimed at an individual who is away is not a rescue.
- **A parked ask carries a date or it is not parked, it is dropped.** Any status row that
  says "waiting on", "blocked on" or "pending <person>" must also say when someone
  comes back to it. In the agent runtime this is failure mode `F10 Silence as a status`
  and `tools/lint_unanswered_ask.py` fails the build on a row without a date. The first
  run of that linter found two real ones: one five days old, one thirteen days old and
  not actually blocked on anybody.
- Canonical public statement, indexable and pulled at runtime by every scheduled agent:
  https://dennisyu.com/unanswered-ask/ — linked from https://dennisyu.com/agent-disclosure/
  and from the new-agent bootstrap box. Marker `UNANSWERED-ASK-RESCUE-2026-09-04`.
<!-- shared-rule:an-unanswered-ask-never-stops-the-work:end -->

<!-- shared-rule:every-article-and-project-starts-with-specific-gct:start -->
## Every article and project starts with specific GCT in plain language

- **Write the specific Goals, Content, Targeting before work begins.** Goals name
  the change the reader or project needs; Content names the source-backed lesson,
  proof or deliverable that will produce that change; Targeting names the people
  and situation it serves. “Publish an article” or “use AI” is an activity, not
  the desired outcome. Use the same brief for the article and the project behind it.
- **Put who, what, why and the useful outcome in the first 2–3 sentences.** Write
  the opening and initial orientation at US eighth-grade reading level or below.
  Use familiar words and short sentences; explain unavoidable terms on first use.
  Put commands, architecture details and specialist terms after this orientation.
  Readers should not have to know the acronym GCT to understand the page.
- **Explain jargon on its first meaningful mention and link the owned explainer.**
  Give the familiar phrase before the specialist label: “the result we want, the
  material we will use, and who it serves — our
  [Goals, Content, Targeting (GCT) brief](https://blitzmetrics.com/gct-business-strategy/).”
  Apply this to other frameworks, acronyms and unfamiliar task terms. Verify the owned
  destination teaches the term; use honest descriptive anchors. If no suitable owned
  explanation exists, define the term in place and record the gap instead of inventing
  a link. Keep this explanation short so it does not bury the lead visual.
- **Make the opening specific enough to judge.** For a shared-memory guide:
  “Use this guide if you work with more than one AI assistant and keep repeating
  the same facts. It shows how to give them one set of notes, so each assistant
  can pick up where the last one stopped.” The project brief also names the
  source files, checks and expected handoff; never invent facts to fill the brief.
- **Check meaning as well as a reading score.** Save the exact opening text and
  its readability result in the audit. A score is a diagnostic, not proof that
  the prose makes sense. A reviewer must still identify the audience, task,
  reason and outcome from those sentences. Unchecked readability stays UNKNOWN.
- **Keep the useful visual with the short opening.** Follow
  `visuals-above-the-fold`: the topic-specific picture or diagram may come first,
  or immediately after the short opening, whichever makes the first screen
  useful. A long GCT card, checklist, changelog or navigation block must not bury
  that visual.

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
