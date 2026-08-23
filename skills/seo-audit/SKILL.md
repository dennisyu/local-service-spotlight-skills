---
name: seo-audit
description: Run a full technical + content + authority SEO audit on any site and score it out of 100 on the seven-component Local Service Spotlight SEO & Growth rubric, with every finding tied to a URL a stranger can open. Use when a client asks "how is my SEO", when a site is about to be rebuilt, when a monthly re-audit is due, or before promising anyone a ranking outcome. Produces a dated score, a delta against the last run, and a fix list ordered by cost-to-fix — not a list of everything that is wrong.
author: Dennis Yu — Local Service Spotlight
references:
  - https://blitzmetrics.com/quickaudit/
  - https://blitzmetrics.com/website-qa-audit/
  - https://blitzmetrics.com/seo-tree/
  - https://dennisyu.com/seo-audits/
  - DealCon-Skills/weekly-brand-maa.md
  - DealCon-Skills/evidence-verification.md
  - DealCon-Skills/client-access-checklist.md
rule-scopes: published-html, design-review
---

# SEO Audit

**Use this when** you need to say something true and defensible about a site's search
performance — to a client, in a pitch, in a monthly tracker, or to yourself before you
promise anyone a result.

An SEO audit is not a crawl dump. A crawl tool produces 400 issues sorted by its own
severity guess; that is a data export, not an audit. An audit is a **judgement**: this is
where the site stands, this is what is costing the most, this is the order to fix it, and
here is the number so next month can be compared to this month.

## The one idea

**Every finding names a URL, and every score component moves for a reason you can point at.**

A score with no evidence under it is a vibe with a number attached. If you say Technical is
55, you must be able to open the four things that made it 55. This is what makes the monthly
re-audit possible at all: next month you are not re-forming an opinion, you are checking
whether those four specific things changed.

---

## The rubric — seven components, 100 points

These weights are the standing Local Service Spotlight SEO & Growth score. They live **here** and
nowhere else. Any job that needs them reads this file. (Until 2026-08-02 they existed only
inside one scheduled task's parameter block, which meant no other audit could be compared to
it and nobody could find the definition — the exact failure this file exists to end.)

| # | Component | Weight | What it measures |
|---|---|---|---|
| 1 | **Technical** | 18% | Indexability, crawl access, sitemaps, robots.txt, status codes, redirects, HTTPS, Core Web Vitals, mobile rendering |
| 2 | **On-Page & Schema** | 16% | Titles, H1s, meta descriptions, internal linking, JSON-LD structured data, canonicals |
| 3 | **Content & Keywords** | 18% | Coverage of the money terms, depth on category/service pages, cannibalisation, thin pages |
| 4 | **Authority** | 14% | Referring domains, link quality and growth, brand mentions, Domain Rating trend |
| 5 | **Local** | 12% | Google Business Profile completeness, NAP consistency, local pack presence, reviews, location pages |
| 6 | **AI Search Readiness** | 12% | Whether AI crawlers are allowed, entity clarity, schema an LLM can parse, citability, Knowledge Panel/Wikidata presence |
| 7 | **Conversion** | 10% | Does the traffic have somewhere to go — offer clarity, forms, calls, tracking that proves it |

Score each component 0–100 on its own, then weight. Report the weighted total **and the
seven raw components**, because the total hides which lever to pull.

**Never report a component you did not check.** Score it `UNKNOWN` and say what access you
need. A component scored 0 because nobody looked reads identically to a component scored 0
because the site is broken — see `evidence-verification.md`, Part 4.

### AI Search Readiness is the one people skip
It is the component most sites fail worst and know least about. Start with `robots.txt`:
count how many AI and image crawlers are blocked (`GPTBot`, `OAI-SearchBot`, `ClaudeBot`,
`PerplexityBot`, `Google-Extended`, `Applebot-Extended`, `GoogleOther-Image`,
`facebookexternalhit`). One real client was blocking **40+** of them while paying for content
marketing — invisible to every AI assistant their buyers were asking, and nobody had opened
the file.

---

## How to run it

1. **Get access first, or say plainly that you did not have it.** Search Console before
   anything else — see `client-access-checklist.md`. An audit without GSC is an outside-in
   audit and must be labelled as one. It is still worth doing; it is not worth pretending.
2. **Crawl what a stranger gets.** Anonymous, cache-busted, no cookies. Then crawl again as
   Googlebot. If those two differ, stop the audit and open a security incident — see
   *Cloaking*, below.
3. **Pull the numbers.** Domain Rating, organic traffic and value, keyword counts by
   position band, top pages, referring domains, and the same set for 3–6 competitors. The
   competitor set is what turns "2,094 visits/mo" into "2,094 against a peer at 24,833."
4. **Score the seven components**, each against its own evidence list.
5. **Delta it.** Against last month, and against the original baseline. Arrows, not prose.
6. **Order the fix list by cost-to-fix, not by severity.** A 5-minute robots.txt edit that
   unblocks every AI crawler outranks a 6-week content programme, even if the content
   programme is "more important."
7. **Write the one-page visual report.** Score then vs now, the traffic table, what shipped,
   what is still open, top three next actions. One page. The 40-page audit is read by nobody.

---

## Traps that have actually bitten us

Each of these produced a wrong finding in a real client audit before it became a rule.

### Decode XML entities before fetching sitemap children
A sitemap index returned 200 and listed five child sitemaps; all five fetched as **404, zero
bytes**. The obvious read was that the client's sitemap fix was cosmetic. The child URLs
contained `&amp;` — fetching the raw, un-decoded string requested a URL that does not exist.
The sitemaps were fine. **Decode entities before you request the URL**, and treat "all N
children failed identically" as a smell about your fetcher, not the site.

### A parameter that names a missing data source has an expiry date
An audit's parameters said `gsc_property: not configured`. The run believed it and wrote
"No Google Search Console property is configured" into a client-facing report as a finding
with an owner — while a teammate had been posting GSC data weekly in the client's own
Basecamp thread. **Check the client's channel before you report a data source as missing.**
Configuration facts go stale between the day a task is written and the day it runs.

### An empty result from a cross-origin fetch is not an empty result
Five in-page `fetch` calls to a search endpoint returned zero results and the conclusion was
"no history exists." They had failed silently on same-origin policy. **A search that returns
nothing and a search that never ran look identical.** Prove the fetch can succeed at all —
run a control query you know has hits — before you report an absence.

### A client-rendered shell is not a thin page
A plain HTTP fetch of a JS-rendered site returns a near-empty body. Score that as "no
content" and you have audited your own fetcher. If the static fetch returns a shell, render
it in a browser before scoring On-Page or Content.

### Cloaking: check what Googlebot sees, every time
On 2026-07-27, three sites on one host returned **HTTP 500 to every human and HTTP 200 with a
spam storefront to Googlebot**, plus a fake 1,733-URL sitemap regenerated per request. From
the human side the sites looked merely broken. This check costs one extra request and is the
difference between "site is down" and "site is compromised and feeding spam to Google."
Divergence between the human render and the bot render is a **security finding**, not an SEO
finding — hand it to `security-audit.md` and do not publish anything to that site.

---

## What you deliver

- A dated one-page report: weighted score, seven components, delta arrows vs last run.
- A findings table where **every row has a URL** and a cost-to-fix estimate.
- A "what shipped since last time" section — this is what makes the client believe the next one.
- An explicit list of what you could not check and what access would fix that.

## Definition of done
- Every score component traces to evidence a stranger can open.
- Anything unchecked says `UNKNOWN`, never 0.
- The human render and the bot render were compared.
- The fix list is ordered by cost-to-fix and the top item is doable this week.
- The report is one page, and the numbers on it can be recomputed next month the same way.

## Learned in the field

*Appended automatically by the self-improvement loop (Skill-Learnings/): dated lessons from real runs. Newest at the bottom.*

<!-- learning:2026-08-01-decode-xml-entities-before-fetching-sitemap-children -->
**August 1, 2026** (from: wtp-monthly-seo-reaudit run (Western Trading Post, first tracked run))

### Decode XML entities before fetching sitemap child URLs — or you will report a healthy sitemap as dead

Checking whether a client's `/sitemap.xml` fix had shipped, the index at `/xmlsitemap.php`
returned 200 and listed five child sitemaps. Fetching each child returned **404 with zero
bytes, all five**. The obvious read was that the sitemap fix was cosmetic — index alive,
every child dead, zero URLs discoverable by Google. That was about to be the report's
headline finding, and it was completely wrong.

`<loc>` values are XML-escaped. The real URL is `?type=pages&page=1`; the sitemap contains
`?type=pages&amp;page=1`. Fetching the raw captured string sends a literal `&amp;`, the
parameters break, and the server 404s. Decoding entities first, all five children return
**200 with 4,516 URLs**.

**Rules:**

1. **Always entity-decode `<loc>` values before fetching them** — `&amp; &lt; &gt; &quot; &apos;`.
   This bites hardest on sitemaps with query-string pagination, which is the norm on
   BigCommerce, Shopify and most hosted carts.
2. **A 100% failure rate across every child is a smell, not a finding.** Real breakage is
   usually partial. When every single item in a set fails identically, suspect the harness
   before the target — the same instinct that `max_crawl_pages` taught on the SERP side.
3. **Never report an infrastructure catastrophe from a single method.** Confirm with a second
   path (browser navigation to one child URL, or Search Console's sitemap report) before
   telling a client their sitemap is dead. The credibility cost of a false alarm this size is
   far higher than the minute it takes to check.

Same run, same discipline, two more times: a robots.txt parser that reported "zero crawlers
blocked" was **prove-red tested against a synthetic blocking file first** (it correctly caught
2/2) before its zero on the live file was trusted, and cross-checked against a raw count of
bare `Disallow: /` lines. And a **+46% referring-domain jump** — exactly the shape of a
mode/measurement artifact — was confirmed as real by pulling `refdomains-history` and seeing a
steady 13-week climb before it was narrated as growth.

**General form of all three: when a check returns the answer you were hoping for, or an answer
too dramatic to be ordinary, make it prove itself before it reaches the client.**

Learned August 1, 2026.

<!-- learning:2026-08-01-read-the-channel-before-reporting-a-missing-data-source -->
**August 1, 2026** (from: wtp-monthly-seo-reaudit run (Western Trading Post) — GSC reported as "not configured" while a teammate posted GSC data weekly in the same thread)

### A task parameter that names a missing data source is a claim with an expiry date — check the client's own channel first

This monthly audit's parameters said `gsc_property: not configured — Ahrefs + direct crawl only`. The run
believed it, wrote "**No Google Search Console property is configured**" into the client-facing report as a
finding with an owner, and listed "get GSC verified" as an action.

Then the run opened the client's Basecamp thread to post — and found our own operations teammate posting
**Search Console data in that thread every single week**: ~120K impressions, 3.5% CTR, average position 8.4,
top queries with click and impression counts. The property existed. It had existed the whole time.

Two costs, and the second is worse than the first:

1. We nearly asked a client for access they had already granted — the exact move that burns an ask and makes
   the retainer look inattentive.
2. **We did the analysis without the best data we had.** Ahrefs estimates rankings; Search Console reports
   what actually happened. The GSC query table turned out to contain the single most valuable finding of the
   engagement — 4,419 monthly impressions on one dead craftsman's name, landing on a sold lot page. That
   insight was sitting in a teammate's weekly report for six weeks and the "authoritative" monthly audit
   never opened it.

**Rules:**

1. **Before reporting any data source as missing or unavailable, read the client's own channel** — the
   Basecamp thread, the shared drive, the weekly report someone else files. A per-client agent's parameters
   are a snapshot of what was true when the task was written; access changes and nobody edits the task.
2. **When you find the parameters wrong, fix the parameters, not just the report.** File it as an ask against
   *yourself* in the ledger. A correction that lives only in one month's write-up gets re-derived — and
   re-published as a false finding — next month.
3. **Sibling reporting is a data source, not just context.** The existing 2026-07-20 learning already says
   "check sibling scheduled tasks' outputs before declaring a metric blocked." Extend it: check what *humans*
   on the account are already reporting, in the channel you are about to post into. Read the channel before
   you write to it.
4. Corollary on credit: when you use a teammate's numbers, say whose they are. The client should see one team,
   and the teammate should see their work being built on rather than quietly re-derived.

This is the same family as the 2026-07-31 lesson that "blocked is a claim that needs evidence" — but a rung
earlier. There, a real blocker was misdiagnosed. Here, a **non-existent** blocker was inherited from a config
file and published without anyone testing it once.

Learned August 1, 2026.

<!-- learning:2026-08-02-same-origin-required-before-trusting-an-empty-search -->
**August 2, 2026** (from: WTP auction-tracking investigation — five Basecamp searches returned zero because they ran cross-origin from a client site)

### An in-page `fetch` to another origin fails silently — and an empty search result looks exactly like "no history exists"

Asked to mine years of Basecamp history for prior conversations about a client's auction platform, the run
issued five in-page `fetch` calls to Basecamp's search endpoint and got **zero results for every query**. The
obvious conclusion was that the team had never discussed it.

The tab was sitting on `auction.westerntradingpost.com`. Every one of those fetches was cross-origin and was
rejected by the browser before it left. The catch block swallowed it. Zero results was never an answer about
Basecamp; it was an answer about CORS.

Run properly, the same searches returned 11 hits, and the history contained the single most valuable fact of
the whole investigation: the client's tag stack was **already installed** on the auction platform, and a
9-month-old access request had dissolved into an unrecorded phone call.

**Rules:**

1. **Check `location.host` before trusting any in-page `fetch` result.** If you are not on the origin you are
   querying, the result is meaningless. Navigate first, then query.
2. **A search that returns zero needs a positive control before you report "nothing exists."** Run a query you
   *know* has hits through the identical code path. If the control also returns zero, the harness is broken,
   not the archive. This is the same prove-red discipline used for the robots.txt parser — extend it to every
   negative finding, because a negative finding is the easiest kind to fake.
3. **A second failure mode stacked on the first here:** even same-origin, Basecamp's search results are
   client-rendered, so `fetch` + `DOMParser` returned a shell with zero result anchors while the live page
   showed 53. When a fetch of a modern web app returns structurally empty results, read the **rendered DOM**
   after navigation instead. Two different mechanisms, one identical symptom: a confident, wrong "nothing
   found."
4. **"No prior discussion" is a claim about an archive, and archives are exactly where an agent's memory
   advantage lives.** Getting it wrong does not just lose a fact — it wastes the institutional knowledge the
   client already paid for, and re-asks colleagues questions they answered months ago.

Learned August 2, 2026.

<!-- learning:2026-08-03-a-capability-with-no-skill-file-cannot-propagate -->
**August 3, 2026** (from: SEO-audit discoverability + security-audit generalization build — 49 published SEO audits with no hub, a rubric that lived inside one task's parameters, and a jammed harvest queue that turned out to be the same problem)

### A capability with no skill file cannot propagate, cannot be taught, and cannot absorb its own lessons

Dennis asked to be "clearly known for doing SEO audits." The assumption going in was that
this was a marketing problem — write something, publish it. It was not. An inventory of our
own properties found **49 published SEO audits** already live, plus 341 audit-family URLs
across three domains. The work existed. What did not exist was any way to see it as a body
of work: **no hub page, 38 of the 49 with zero inbound links from any sibling audit, 35 with
zero outbound links.** Forty-nine deliverables, each an island.

The root cause was one level deeper than the missing page. There was **no `seo-audit` skill
file.** The seven-component SEO & Growth rubric — the thing that makes two audits
comparable — existed only inside the parameter block of a single scheduled task
(`wtp-monthly-seo-reaudit`). One job could score a site. Nothing else could, because there
was nowhere else to read the definition from.

And that had a visible symptom nobody had connected to it: **three learning notes had been
jammed in the harvest inbox since the previous day, all naming `seo-audit`**, all
unresolvable, aging toward the stale-queue gate. The morning run reported them as a queue
defect. They were not a queue defect. They were the loop correctly reporting that a skill
our own runs believed in did not exist. **A jammed learning note is a missing-capability
alarm, not a filing error.** Creating the skill cleared all three on the next run.

Same shape on the security side: seven real checks, a 116-assertion test suite, and a
track record of caught compromises — all of it existing only as one client site's
`monitor.py`. Nothing generalized to the network because there was no file to generalize
*into*.

**The rule:** when you find yourself doing something well and repeatedly, check whether it
has a canonical skill file. If it does not, that is the deliverable — before the landing
page, before the marketing. The file is what lets the capability propagate to every pack,
teach itself to the next agent, and accumulate lessons. Publishing a page about a
capability with no skill file behind it produces a claim; publishing the skill produces a
system.

**Second-order effect worth expecting:** adding two mandated skills tripped every coverage
gate that had been built in the preceding days — the SOMBA orphan check, the numbering
lists, the count derivations. All of them fired correctly and named exactly what to edit.
Ten registration points across three builders, caught by gates rather than by users. That
is what those gates are for, and a day where several fire at once is a good day, not a
messy one.

### Corollary — measure your own work before describing it

Before writing a word of the hub page, the 49 audits were fetched anonymously and measured:
status, transfer size, time to last byte, inbound and outbound sibling links, `h1`, meta
description, JSON-LD. That is our own `seo-audit` skill run against our own SEO audits, and
it produced the specific numbers the page and this note are built on — including one page
taking **9.9 seconds** to load and three returning **403 to every programmatic client**
(browser-verified fine, so: invisible to AI crawlers, visible to humans).

Running the skill on yourself first is not a nice touch. It is how you find out whether the
claim you are about to publish is true.

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

<!-- shared-rule:analytics-on-every-page:start -->
## Analytics goes on before anything gets optimised

- **Measurement is the first build step, not the last.** A page with no analytics cannot
  be improved, only redecorated, and every argument about it becomes a matter of taste.
- **The invisible plumbing outranks the visual design** — tracking, CRM connection,
  conversion events, schema and page structure come before fonts and colours.
- **Confirm the tag actually fires on the live page**, not that it exists in a settings
  screen. See `verify-by-opening-the-live-artifact`.
- Instrument the business outcome, not the vanity metric: calls, booked jobs and revenue,
  not impressions.
<!-- shared-rule:analytics-on-every-page:end -->

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

<!-- shared-rule:buttons-must-contrast-with-their-background:start -->
## A button must contrast with what it sits on

- **A call to action must be visibly separate from the section behind it** at rest, not
  only on hover. A visitor on a phone never hovers, and a button that only appears on
  hover does not exist.
- **Check the button against every background it appears on.** The same component sits on
  white, on the hero image and on the dark footer; one of those is usually where it
  disappears.
- Text on the button needs at least **4.5:1** against the button fill, and the fill itself
  needs to be clearly distinct from the section fill.
- This is the general case of `no-black-buttons`. Black is the most common way to break it;
  it is not the only way.
<!-- shared-rule:buttons-must-contrast-with-their-background:end -->

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

<!-- shared-rule:every-article-has-pictures:start -->
## Every article has pictures

- **No article ships as a wall of text.** Every published piece carries images — real
  photographs, screenshots, or diagrams that carry meaning, not decorative stock.
- **A diagram beats a paragraph** wherever the point is a structure, a sequence or a
  comparison.
- Caption them. An uncaptioned image is decoration; a captioned one is evidence.
- Images also carry the provenance required by `process-real-content-never-generate` —
  a photograph of the work actually done proves more than any sentence about it.
<!-- shared-rule:every-article-has-pictures:end -->

<!-- shared-rule:immersive-hero-standard:start -->
## Personal-brand heroes are immersive, not boxed

A public figure's hero is the whole first screen, not a card with a headshot in it. The
standard, fleet-wide:

- **Full bleed and viewport height.** The hero occupies the first screen: `height:94svh`
  with `min-height:600px` and `max-height:1000px`. Use `svh`, not `vh` — mobile browser
  chrome makes `vh` overshoot and push the call to action below the fold.
- **The subject is the background, not a thumbnail.** No small boxed portrait, no framed
  inset, no stock-photo collage. The photograph is edge-to-edge and the type sits on it.
- **Join the image to the type with a mask, not a hard edge.** A horizontal
  `mask-image: linear-gradient(to right, transparent 0%, rgba(0,0,0,.35) 16%, #000 42%)`
  dissolves the photo into the text column so the two read as one composition.
  **Override it to a vertical mask on mobile** — a horizontal mask on a narrow screen
  fades the subject's face.
- **Control the crop with a focal variable**, e.g. `--focal: 56% 4%`, so the frame can be
  nudged per person without rewriting the block. Check the top of the head is not clipped.
- **Reset `box-sizing` on your own block.** These themes scope `border-box` to a theme
  wrapper, not `*`. A new hero inherits `content-box`, so `height:100%` plus padding
  overflows an `overflow:hidden` section and silently clips the calls to action out of
  frame — the page looks fine and the buttons are simply gone.
- **One primary call to action, in the brand colour, above the fold on a 1366×768
  laptop.** Verify at desktop, laptop and mobile widths before calling it done.
- **A proof rail under the fold, not claims inside the hero** — credentials, logos, or
  named results on a solid brand-colour band.
- **Motion is optional and must be silent.** A background video is permitted only when it
  is `muted`, `playsinline` and `loop`, with a poster image; see `nothing-plays-uninvited`.
- **The photograph has to earn full bleed.** Composed portraits and documentary
  photography can carry a hero; selfies cannot, at any resolution. When the only assets
  are selfies, use the typographic hero — it never looks cheap. See
  `photo-earns-full-bleed`.
<!-- shared-rule:immersive-hero-standard:end -->

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

<!-- shared-rule:links-must-resolve:start -->
## Every link and every entity claim resolves

- **A broken entity claim is worse than no claim.** `sameAs` is how a site tells Google,
  Bing and every AI answer engine "this person is that entity". Pointed at a deleted or
  wrong target, it does not merely fail — it actively teaches the wrong association.
- **Verify every `sameAs` target returns 200 before publishing schema, and re-verify
  quarterly.** Entities get deleted. A Wikidata item asserted on a client site was
  deleted on 7 July 2026 and the claim stood until an audit found it five weeks later.
- **Only anchors count.** `preconnect`, `dns-prefetch`, `canonical` and `alternate`
  hints are not links a visitor can follow, and treating them as links reports
  `googletagmanager.com` as a dead link on every site that loads analytics — noise that
  teaches people to ignore the sweep.
- **Request every outbound link before publishing.** A dead social link in a footer
  appears on every page of the site, which makes one careless paste a site-wide defect.
- Treat `401`, `403`, `405` and `429` from Instagram, Facebook, X and LinkedIn as *pass*.
  Those platforms block automated requests by policy; that is not a broken link, and
  reporting it as one trains people to ignore the sweep. `404`, `410`, `5xx`, DNS
  failure and connection timeout are real.
- When a target is genuinely gone, remove the claim rather than leaving it. An honest
  smaller `sameAs` set outperforms a larger one containing a lie.
<!-- shared-rule:links-must-resolve:end -->

<!-- shared-rule:no-black-buttons:start -->
## Never ship a black button

- A call-to-action button must use the site's brand colour, never black. Black buttons
  camouflage against dark heroes, navigation and footers, carry no brand signal, and
  measurably lose conversions. This is the single most repeated finding across hundreds
  of Local Service Spotlight website audits.
- Nobody ships a black button on purpose. It is the default in every builder —
  Gutenberg's `has-black-background-color` preset, Elementor's dark fill, Astra starter
  themes, any Bootstrap-derived `btn-dark`. It looks correct on the white editor canvas
  and disappears on the dark section it ships into. Assume the default is wrong and
  override it deliberately.
- Determine the brand colour, do not guess it: fetch the live pages, count hex values,
  and take the most-used non-neutral. Where a site has two strong non-neutrals, the
  darker is usually navigation and the brighter is the CTA — as gold `#f5a623` is to
  teal `#22698a` on Local Service Spotlight.
- Verify contrast before publishing. Text on a CTA needs at least 4.5:1. A gold or
  yellow button needs dark text, not white.
- Before reporting any site work as done, confirm the published HTML contains none of:
  `background:#000`, `background-color:#000`, `btn-dark`, `btn-black`, `button-black`,
  `bg-black`, or an applied `has-black-background-color` class.
- An element may keep a black fill only with a documented exemption class where black
  genuinely belongs — a logo lockup, an icon button on a dark rail. Mark it with the
  fleet's existing exemption class, `bm-keep-black` or `lss-keep-black`,
  so the sweep can see the exemption was
  deliberate. Exempt one element, never a default.
- Full reasoning and the enforcement-plugin pattern:
  https://blitzmetrics.com/why-we-dont-use-black-buttons/
<!-- shared-rule:no-black-buttons:end -->

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

<!-- shared-rule:no-placeholder-copy:start -->
## Placeholder copy never reaches production

- **A number on a page is a claim.** Every stat needs a definition, a date, and someone
  who can say where it came from. If the same figure appears twice on a site it has to be
  the same figure.
- **Builder placeholder text is a defect, not a cosmetic issue.** "Lorem ipsum", "Your
  photo here", `xxx-xxx-xxxx`, `example@example.com` — each one tells a visitor the page
  was never finished, on the page where you are asking them to trust you.
- **A testimonial needs a real, nameable person.** No initials-only quotes, no
  "a client in Minneapolis".
- **The sweep only catches the obvious half, and you need to know which half.** A
  placeholder that looks like a real number — a hero stat reading "$34K Monthly MRR" that
  nobody can source — is indistinguishable from a true one to any regex. That exact
  string sat live on a paying client's site. The only defence is that whoever publishes a
  number can name its source before it goes up.
<!-- shared-rule:no-placeholder-copy:end -->

<!-- shared-rule:no-popup-on-load:start -->
## No popup on page load

- **Nothing covers the page before the visitor has read anything.** A modal that opens on
  load, on a timer, or on scroll-depth before the first section is finished interrupts
  the only moment you had their full attention, and it is the single most common reason a
  first-time visitor closes the tab.
- The permitted triggers are **click** and **exit intent on desktop**. A newsletter offer
  earns its place in the page, after the proof, as a section — not as an ambush.
- This applies to cookie and consent banners too: they may be present, but they must not
  block the content or be dismissable only by accepting.
- **Coverage is partial and you should know it.** These checks catch the three signatures
  that cover most of the fleet — Elementor's `page_load` trigger, the `auto_open` popup
  type, and load triggers declared in markup. A popup wired up in custom JavaScript will
  pass the sweep. When you touch a site, look at it once with a fresh session and no
  cookies; that is the only reliable test.
<!-- shared-rule:no-popup-on-load:end -->

<!-- shared-rule:no-unnamed-link-text:start -->
## No unnamed link text

- **Link text must name its destination when read on its own.** Screen readers and search
  engines both pull links out of context; "read more" out of context is nothing. Write
  "Read George's story", not "Read more".
- The banned set in practice: *click here, read more, learn more, continue reading,
  download, more, here, this, link.* If the anchor text is one of those words and nothing
  else, rewrite it.
- **An image-only link still needs a name.** A logo or social icon wrapped in an anchor
  needs meaningful `alt` text on the image or an `aria-label` on the link. `alt=""` is
  correct for decoration and wrong for a link — a link with no name is a link nobody can
  follow by voice or by ear.
- **An anchor points at the thing it names.** If the text says a company, the link goes to
  that company; if it says "LinkedIn", it goes to linkedin.com. Two links with identical
  anchor text going to different destinations on the same page is always a defect — one of
  them is lying.
- Expect the first sweep of an existing WordPress site to report this on archive and
  blog templates, where "Read more" is the theme default. That is one template edit, not
  a per-post fix, and it is why this rule reports rather than blocks.
<!-- shared-rule:no-unnamed-link-text:end -->

<!-- shared-rule:nothing-plays-uninvited:start -->
## Nothing plays at the visitor uninvited

The test is not "is there a video." The test is **would this irritate someone who
just arrived.** Motion the visitor chose to look at is atmosphere; sound and
motion that grab at them are an ambush, and the first thing they learn about you
is that your site did that.

- **Background video in a hero is encouraged.** It is how the immersive standard
  gets met. Ship it with all four of `muted`, `playsinline`, `loop` and a `poster`
  image. `playsinline` is not optional — without it, iOS yanks the video full
  screen the moment it starts, which is the loudest version of the thing this rule
  exists to prevent.
- **Sound never starts on its own.** A hero film may absolutely have an audio
  track. It loads muted with a visible, labelled unmute control, and the visitor
  decides. That satisfies both halves: the video is there, the ambush is not.
- **`<audio>` never autoplays**, muted or not. There is no case for it.
- **Embedded players count.** `?autoplay=1` on a YouTube or Vimeo iframe must be
  paired with `mute=1`, or dropped.
- **Anything that cannot meet the muted conditions ships without `autoplay`**,
  behind a poster frame and a play control.
- Judge the rest by the same intent, even where no regex covers it: a video that
  covers the content, one that cannot be paused, one that restarts on every scroll,
  or one that pushes the call to action off the screen is irritating whether or not
  it makes a sound.
- This is the published-page half of `silent-media-playback`. That rule stops an
  agent putting sound through *your* speakers while it tests; this one stops a site
  putting sound through a *visitor's* speakers.
<!-- shared-rule:nothing-plays-uninvited:end -->

<!-- shared-rule:order-proof-by-authority:start -->
## Order proof by authority, strongest first

- **Testimonials, logos and mentions are never in random order.** Score each on the
  30-point scale — 10 for who said it, 10 for where it was said, 10 for what they actually
  said — and lead with the highest.
- **A visitor reads the first two and leaves.** Whatever is in position one is, in
  practice, your entire proof section.
- **Video beats text.** The same endorsement on camera is more persuasive and harder to
  fake than the same words in a pull quote; capture it as video wherever it exists.
- Cut the bottom of the list rather than padding it. A short list of strong proof
  outperforms a long list containing weak proof.
<!-- shared-rule:order-proof-by-authority:end -->

<!-- shared-rule:photo-earns-full-bleed:start -->
## A photograph has to earn full bleed

- **Judge the genre before the pixels.** Composed portraits, stage photography and
  third-party documentary shots can carry a full-bleed hero. Phone selfies, webcam grabs,
  cropped group photos and screenshots cannot — at any resolution, under any treatment.
  Resolution and file size say nothing about whether an image can be six feet wide behind
  a headline.
- **Open every candidate before you rank it.** Selecting by filename, dimensions or
  weight is how a selfie ends up presented as a hero option. If you have not looked at
  the image, you have not evaluated it.
- **When the only assets are selfies, use the typographic hero.** A confident type
  composition on a brand-colour field never looks cheap; an enlarged selfie always does.
  Say plainly that better photography is the unblock, and what to shoot.
- **Full bleed magnifies everything.** Soft focus, a cluttered background, a bad crop and
  mixed colour temperature are all invisible in a thumbnail and unmissable at full width.
- Related: `immersive-hero-standard` for the construction; this rule is only about
  whether a given photograph is allowed to be the hero at all.
<!-- shared-rule:photo-earns-full-bleed:end -->

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

<!-- shared-rule:spoken-urls-must-resolve:start -->
## Every URL we say out loud resolves

- **A URL spoken from a stage, printed on a QR code, or read into a podcast has no
  inbound link.** No crawler finds it, no internal link audit sees it, and no analytics
  records it until a human types it and fails. It is the one class of URL that dies
  completely silently, and the people who hit the 404 are the warmest audience we ever
  get.
- **Every hub domain answers the same short paths.** `/install/`, `/skills/` and
  `/activate/` resolve on every site we tell an audience to visit — 200, or a 301 to the
  page that actually serves that intent. Never a 404.
- **Say it once, spell it the same way everywhere.** If the talk says "slash install",
  every hub answers `/install/`. Do not rely on one domain having a page while another
  has a redirect and a third has nothing.
- **A short path is a promise, so keep it even after the page moves.** When the
  destination is renamed, repoint the redirect in the same change. The short path
  outlives every page it has ever pointed at.
- **Redirect within the domain the audience was told to visit** where a suitable page
  exists. A cross-domain hop from a QR code loses the brand impression at the exact
  moment it was earned.
- **Check it from outside, logged out.** An editor screen saying "saved" is not a
  resolving URL, and a page cache can serve a stale 404 long after the rule exists.
  See `verify-by-opening-the-live-artifact`.
- Adding a spoken path to a talk, a slide or a business card means adding it to this
  rule's `paths` list in the same week. That is the whole maintenance cost, and it is
  what stops this being rediscovered every few months.
<!-- shared-rule:spoken-urls-must-resolve:end -->

<!-- shared-rule:every-public-page-has-real-imagery:start -->
## Every public page shows real people or real work

- **Every visitor-facing content page must contain at least one meaningful image
  of the actual business: its people, its work, its customers with permission,
  its product, or its place.** This includes conversion and utility pages such as
  Contact, Estimate, Pricing, Financing, Warranty, Privacy, and Thank You. Do not
  ship a wall of text.
- A logo, icon, tracking pixel, abstract decoration, AI-generated image, or stock
  photograph does not satisfy the rule. Neither does an unrelated real photo
  added merely to pass a count. The image must help a visitor understand or trust
  the page.
- Use the business's approved source library. Give the image honest alt text and,
  when useful, a caption that explains what it proves. Describe only what the
  source establishes: never relabel one project photo as work completed in every
  city, and never infer a person, location, service, or result from a filename.
- If no suitable approved image exists, request one and block that page from
  publication. Do not manufacture evidence with image generation or stock.
- Build QA must inventory every rendered content route and fail when any route
  lacks a verified real image. Keep a provenance allowlist or equivalent asset
  record so logos and decorative images cannot make the check pass. Mark at least
  one qualifying `<img>` per page with `data-lss-real-image="verified"` only
  after that provenance check. Also inspect the rendered desktop and mobile page;
  a hidden, broken, or contextless image does not count.
- Machine-only documents and routes that never render as visitor content—such as
  `robots.txt`, XML sitemaps, feeds, and true HTTP redirects—are exempt. A
  browser-rendered redirect placeholder is not exempt; replace it with a real
  redirect or make the page comply.

The fleet check proves only that a page declares the verified marker and supplies
a nonblank, non-data source plus nonblank alt text. It cannot prove that the
source loads, is visible, is meaningfully sized, or is truthful. Enforce those
claims with each site's provenance-aware build validator plus a human visual
review. Never add the marker merely to make the sweep pass.
<!-- shared-rule:every-public-page-has-real-imagery:end -->

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
- **Historical quotations, transcripts, captions, and archival artifacts stay
  verbatim.** Do not silently rewrite a speaker's words. If an old stage line appears
  in quoted material, label it as historical and state the current four stages outside
  the quotation. This preservation exception is not permission to teach the old terms
  as the current system.
- SAE course map (Plumbing → Goals → Content → Targeting → Amplification →
  Optimization) is separate; the Content Factory block inside it is still only
  Produce → Process → Post → Promote.
<!-- shared-rule:content-factory-four-stages:end -->

<!-- shared-rule:explain-with-linked-examples:start -->
## Explain with linked examples

- When explaining a concept (GCT, Content Factory, Dollar-a-Day, MAA, SAE, Nine
  Triangles, or similar), always **show and link** at least one concrete example.
  A definition alone is incomplete.
- Prefer live canonical URLs on Local Service Spotlight, the canonical method host,
  Dennis's site, and the Nine Triangles site. Never invent example URLs.
- Use descriptive Markdown links to the exact page. A bare domain, an internal skill
  slug, a search-result URL, or a phrase such as "a client-safe MAA" is not a linked
  example. Open the exact target and verify that it resolves before handoff.
- Pattern: one sentence what it is, one sentence why it matters, then the linked
  example(s).
- Verified starters (each returned HTTP 200 on 2026-08-22; re-check before use):
  - GCT → [Goals, Content, Targeting](https://theninetriangles.com/gct/).
  - Content Factory → [Content Factory](https://blitzmetrics.com/content-factory/)
    and [the four stages](https://blitzmetrics.com/the-4-stages-of-the-content-factory/),
    naming Produce → Process → Post → Promote.
  - MAA → [Metrics, Analysis, Action](https://theninetriangles.com/maa/) and a
    [scheduled MAA example](https://blitzmetrics.com/18-scheduled-tasks-every-agency-owner-should-build-in-claude/).
  - Dollar-a-Day → [the method and public proof](https://blitzmetrics.com/dad/).
  - SAE → [the canonical operating guide](https://blitzmetrics.com/social-amplification/).
  - Nine Triangles → [the complete map](https://theninetriangles.com/).
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
- **Sender and thread integrity outrank the address preference.** In an existing
  conversation, preserve the exact authenticated account, thread, `From:`, `To:`,
  `Cc:`, and `Reply-To:` route. Do not silently start a new thread, change the
  audience, or switch sender identities to make an address look on-brand. A delivery
  rail that explicitly forbids email, such as Basecamp notifications, still controls.
- Select an `@localservicespotlight.com` `From:` identity for a new message, or retain
  one already used in a thread, only when that exact identity is configured and verified
  on the authenticated account **and** its use is authorized for the intended audience.
  Never spoof it, assume an alias can send, or substitute it for an unverified legacy
  identity. If it is unavailable, preserve the verified sender and report the naming
  exception; transport metadata is not a reason to repeat the old brand in the body.
- A ready-to-send handoff records the authenticated account, exact thread, `From:`,
  `To:`, `Cc:`, and whether the sender identity was verified and authorized. The
  agent-transparency closer does not prove any of those delivery facts.
- This does not rewrite old articles or legal entity paperwork. It is a public-facing
  naming rule for new work.
<!-- shared-rule:lss-is-the-public-company:end -->

<!-- shared-rule:outbound-email-names-the-agent:start -->
## Outbound email names the agent

- Every email an agent drafts or hands off ready-to-send—and every delivered copy
  when a human approves and sends it—must end with a one-line attribution naming
  the agent/model and its function.
- The controlling default remains `agents-draft-humans-send`: the agent stages the
  message and a human dispatches it. In that case use exact provenance such as
  `Drafted by Codex (Ops); sent by Dennis Yu`. A draft that has not been dispatched
  says only `Drafted by Codex (Ops)`.
- Use `Sent by` or `Sent via` for an agent only when an exact execution receipt proves
  that agent had scoped send authority and performed the dispatch. Under the default
  human-send rule, `Sent via Claude` or similar is false and forbidden.
- `From:` is the authenticated transport identity; the closer records authorship and
  dispatch provenance. Do not attribute a human send to a model or a model draft to a
  human.
- Place the agent line after the body and before any mail-client legal footer.
- Do not invent a fake human VA signature to hide that an agent wrote it.
- The closer never grants send authority and never substitutes for an approval or
  execution receipt.
<!-- shared-rule:outbound-email-names-the-agent:end -->
