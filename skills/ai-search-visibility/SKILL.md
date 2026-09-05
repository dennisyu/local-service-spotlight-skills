---
name: ai-search-visibility
description: Control how ChatGPT, Perplexity, and Google AI Overviews describe you when a buyer, seller, or client researches you — audit the answers, trace them to sources, feed the AIs your canonical facts. Use to win the AI first impression before any deal conversation.
rule-scopes: published-html, design-review
---

# AI Search Visibility

**Use this when** you want AI to give the right answer about you — because buyers, sellers, and premium clients now ask ChatGPT before they ever reply to your email. Step 6 of the Local Service Spotlight method.

## Inputs
- Your name, niche, entity home, and every profile URL.
- Entity-clarity findings and Person schema from `knowledge-panel-entity-seo`.
- Your differentiation sentence and top-5 proof points from `personal-brand-strategist`.
- Prior test-grid answers, if you've run this before — you'll diff against them.

## The buyer's test grid (run verbatim)
| Who's asking | What they type | What you need back |
|---|---|---|
| Premium client | "Who is [your name]?" | Your differentiation plus two proof points |
| Seller vetting a buyer | "[your name] [company] acquisitions" | Your buy box and deal history, accurate |
| Anyone in your niche | "Best [niche] expert for [buy box]" | You, named, your entity home cited |
| Skeptic | "Is [your name] legit?" | Third-party proof, not your own claims |
| Podcast host | "[your name] interviews" | Your featured interview and core topics |

## Where the answers come from
- **ChatGPT** — training data plus live browsing; your entity home and high-authority mentions feed it.
- **Perplexity** — live retrieval with cited URLs; it quotes specific pages, so your definitive article matters most here.
- **Google AI Overviews** — the Knowledge Graph plus top-ranked pages; everything you fixed in Step 5 compounds here.

## Steps
1. Run the grid in all three engines. Paste raw answers — no cleanup, no cherry-picking.
2. Mark every line **thin, missing, or wrong**. Wrong includes stale titles and another person's facts bleeding in — entity collision surfacing in AI.
3. Trace each weakness to its source: the page, profile, mention, or schema field the model is reading — or can't find.
4. Check for a **definitive article** on your topic. No canonical page means the models improvise; hand that gap to `definitive-article-writer`.
5. Produce **5 ranked actions**: a page to strengthen, a mention to earn, a fact to add to the entity home, an inconsistency to clean, an article to write.
6. Re-test in 30 days and diff. This is MAA: metrics (the grid) → analysis (the trace) → action (the five fixes).

## Output
- Verbatim current-state AI answers, a gap list traced to specific sources, and 5 ranked actions to make AI describe you the way you want for deals.

## For DealCon — agency owners & acquirers
**If you run an agency:** when a prospect asks AI "who should run marketing for my [industry] business" and you're the named answer, the call starts closed — inbound at premium pricing.
**If you buy & sell companies:** sellers vet acquirers in ChatGPT now. When AI states your buy box and closed deals accurately, qualified sellers self-select toward you — off-market deal flow.
**Your edge:** name the one question in your niche you must be the answer to, then aim all five fixes at that single question.

## Run on a persistent agent (Fable 5)
- **Loop to done:** run the full grid in all three engines, verbatim, every time — and loop until every thin, missing, or wrong line is traced to a specific source and covered by one of the 5 ranked actions.
- **Self-verify:** paste raw answers, no cherry-picking, then grade them against the differentiation sentence and proof points held in memory.
- **Compound with memory:** store each run's verbatim answers so the 30-day re-test is a diff, not a fresh audit — the trend across runs is the real metric.
- **Log the run:** the before/after diff is the meta-article — and the proof a client or counterparty can check.

See `boil-the-ocean.md` for the full operating principles.

## Notes — Dennis's method
- Same engine as the Knowledge Panel: **clear entity + agreeing sources**. Fix it for Google and you largely fix it for the AIs that read Google's view of you.
- AI quotes canonical pages. ONE definitive article per topic; thin posts orbit it and link back. Competing with your own hub is content vandalism.
- Specificity survives the model. Zach Peyton's facts — Superior Fence & Rail, largest US fence franchise, 110+ locations, $310M+ — get repeated verbatim. Vague bios get paraphrased into mush.
- George Paladichuk built NaiL AI so that when roofers ask AI about AI, he is the named answer. Pick your question and own it the same way.
- Don't argue with the output — fix the sources. Models repeat what the web agrees on about you.
- Run this before every raise, listing, or launch. The answer changes as the web changes — know it before your counterparty does.

## Definitive article & pairings
- Reference: https://blitzmetrics.com/definitive-article-guide/ · https://blitzmetrics.com/how-my-ai-agents-document-and-improve-themselves-meta-articles-definitive-articles/
- Pairs with: → dollar-a-day-strategist → content-factory → definitive-article-writer

## Learned in the field

*Appended automatically by the self-improvement loop (Skill-Learnings/): dated lessons from real runs. Newest at the bottom.*

<!-- learning:2026-07-20-ahrefs-free-dr-endpoint-auth-deadline -->
**July 20, 2026** (from: anthony-hilb-seo-tracker (weekly-brand-maa) — refiled from a stray root note by skill-pack-propagation on July 21, 2026)

Ahrefs' free Domain Rating endpoint stops accepting unauthenticated calls on August 1, 2026.
> **⚠ RESOLVED August 3, 2026 — read this first: use `site-explorer-domain-rating`, always.**
> Everything in this section down to "Rules for any skill that pulls Ahrefs Domain Rating" is
> the historical record of a deprecation that no longer needs tracking. Do not act on the dates.

The `public-domain-rating-free` MCP call still returns the normal DR value today but now
carries a deprecation warning: "Unauthenticated access to this endpoint will be removed on
2026-08-01. Requests will require a free API key." Every weekly/monthly tracker that pulls DR
(anthony-hilb, wtp, trenton-sandler, cxotalk, family-law, somba, and any future tracker) will
start erroring from August if its call path is unauthenticated.

Rules for any skill that pulls Ahrefs Domain Rating:

**RESOLVED — August 3, 2026. Use `site-explorer-domain-rating`. Always.** There is no date left to
track and no key to register. The three dated rules below are superseded, kept only as the record.

Why the free endpoint was retired from our skills rather than migrated:

- **We already hold the key.** The workspace MCP authenticates with a paid Lite key
  (`subscription-info-limits-and-usage` returns real workspace data, so auth demonstrably works).
  The "free API key" in Ahrefs' warning is for callers who hold no key at all. Registering a second
  one would have added a credential to manage in exchange for nothing.
- **Identical numbers.** Verified August 3, 2026 across two domains: anthonyhilb.com returned DR 10
  from both endpoints, michaelkrigsman.com DR 1.0 from both.
- **The authenticated endpoint is MORE accurate.** `public-domain-rating-free` lags the authenticated
  series by about a day, which is exactly what put a wrong DR 11 into the anthony-hilb 2026-07-20
  snapshot. Switching removes a known defect; it is not merely deprecation-proofing.
- **Cost is not a constraint.** ~50 units per call against a 100,000/month Lite allowance. For many
  domains at once, `batch-analysis` takes up to 100 targets in ONE call at ~18 units each, verified
  to return DR values identical to the single endpoint.

**The meta-lesson, which is the part worth keeping.** This block carried a hard-coded vendor date into
six skill files, and only ONE of them ever received the July 27 correction from August 1 to August 10.
The other five still read "Until August 1, 2026" on August 3 — a deadline that was both wrong and
already expired, still instructing agents to prefer the dying endpoint. A conditional written around a
vendor's date has to be re-verified in every copy, forever; an unconditional instruction needs nothing.
**Prefer the instruction that cannot go stale over the one that is merely correct today** — and when a
correction lands, grep for the other copies in the same breath. Same shape as the "a standing contract
recorded in one file is not a standing contract" rule in `Skill-Learnings/README.md`.

Superseded, retained as the record:
1. ~~Until August 2026 keep using `public-domain-rating-free` first — it works and costs 0 units.~~
2. ~~If it errors, fall back once to `site-explorer-domain-rating` and state the switch in the report.~~
3. ~~Permanent fix: register a free API key (about a 5-minute setup).~~

Learned July 20, 2026. Resolved August 3, 2026.

<!-- learning:2026-07-27-serp-depth-needs-max-crawl-pages -->
**July 27, 2026** (from: cxotalk-weekly-maa run)

### DataForSEO `depth` alone does NOT go past page 1 — you need `max_crawl_pages`

Checking whether michaelkrigsman.com still ranked for "michael krigsman":

```
serp_organic_live_advanced { keyword, location_name, language_code, depth: 30 }
```

returned **9 organic results** and no michaelkrigsman.com. Combined with a live Chrome
render that also didn't show it, the obvious read was "the entity home dropped off page
one." That would have been the report's headline — and it would have been wrong.

`depth` sets how many results to *return*; `max_crawl_pages` (default **1**) sets how many
SERP pages to *crawl*. Re-running with `max_crawl_pages: 4` returned 21 results and showed
**four** michaelkrigsman.com URLs — homepage at rank_group 7, `/about/` 9, `/home/` 12,
`/connect/` 14. The real story was the opposite of the false one: the site went from 1
ranking URL to 4.

**Rules:**

1. Any "did we lose a ranking?" check must pass `max_crawl_pages` ≥ 3. `depth` alone is a
   page-1 query, no matter how large you set it.
2. Never report a disappearance from a single SERP pull. Two pulls one minute apart
   genuinely disagreed on this keyword (one had the homepage at #7, the other didn't have
   the domain at all). Volatility at the page-1/page-2 boundary is real — report
   "contested foothold," with both observations, rather than a clean win or loss.
3. A logged-in browser render is a *third* opinion, not a tiebreaker. Personalization makes
   it systematically different from a clean datacenter pull; prior runs quoted "#8 clean /
   #3 browser" for the same query on the same day.

Severity note: this nearly reported a client's site as having fallen out of the SERP
entirely. Learned July 27, 2026.

<!-- learning:2026-07-29-a-redirect-you-ship-is-a-redirect-you-own -->
**July 29, 2026** (from: SEO-tree link audit, July 29, 2026)

### A URL you ship inside a skill pack is a URL you have to keep alive

Our own published packs told every installer's agent to read
`localservicespotlight.com/ai-agent-application-password/` for login-free publishing. That URL
had become a **double 301** — one hop to a renamed article, a second hop to its current home.
It still resolved, so nothing complained. It was sitting in `boil-the-ocean.md` and
`video-repurposing-agent.md` across four public packs, in two generators, in the daily
checklist, in the project's own CLAUDE.md, and on the trunk page of the whole system.

A redirect chain is not a broken link, which is exactly why it survives: every check passes,
every page loads, and the crawler quietly discounts the destination. Sixteen references were
repointed at the final URL, at the source, so the next rebuild ships the fix to everyone.

**Rules:**

1. **Cite the URL that answers 200, never a URL that answers 301.** Follow every external link
   you are about to write into a skill file, and record where it ends up, not where you started.
2. **A URL inside a downloadable pack is published surface area.** It reaches people you cannot
   email later. Treat a link in a shipped skill file with the same care as a link on a page.
3. **Fix at the source, then let propagation do the distribution.** Editing a live page fixes
   one copy; editing the skill file fixes every copy on the next run.
4. **Add the dead URL to the checker, not just to your memory.** `verify_link_graph.py` now
   fails if any node reintroduces it and if any node sits behind a redirect hop at all.
5. **A short URL does not need a redirect plugin.** WordPress core's
   `redirect_guess_404_permalink` 301s an unmatched path to the single post whose slug it
   prefixes, so `/persistent` reaches `/persistent-agents/` for free. Do NOT publish a stub page
   on the short slug to fake this — a thin page that competes with the article is the exact
   content-vandalism the definitive-article standard exists to prevent. Assert the short URL's
   final destination on every run, because the guess turns into a 404 the day a second matching
   slug ships.

Learned July 29, 2026.

<!-- learning:2026-07-29-a-check-that-cannot-fail-is-not-a-check -->
**July 29, 2026** (from: redirect-chain audit, July 29, 2026)

### A check built on a branch that can never run reports perfect health forever

Two scripts written the same day counted redirect hops like this:

    try:
        r = urllib.request.urlopen(req)      # HEAD
        return hops, r.status
    except urllib.error.HTTPError as e:      # <-- catch the 301 here
        ...follow Location, hops += 1

That `except` can never fire. `urlopen` installs `HTTPRedirectHandler` by default and follows
301/302 transparently, returning the FINAL response. So the counter returned **0 hops for every
URL on earth** — including one we had already proved by hand was a double 301. The first audit
printed "34 rules · 0 chained" and read as good news.

Fixing the counter turned that into: 6 chains on one site, 18 on another, one self-redirecting
rule with 12,190 hits looping forever, and the busiest rule on the site (829,576 hits) throwing
away a trailing slash and buying a second hop on every single request.

**Rules:**

1. **Before trusting a checker, make it fail on purpose.** Feed it a case you KNOW is bad. If it
   passes, the checker is broken — not the world. Both scripts now call a `selftest()` that
   fetches a URL known to redirect and aborts the whole run if it measures zero hops.
2. **Any library call with "convenience" behaviour is a checker's enemy.** Following redirects,
   retrying, normalising, caching: all of it hides the exact signal a verifier exists to see.
   Measure at the lowest level that still answers the question.
3. **A `try/except` around a network call deserves the same scrutiny as the happy path.** An
   `except` clause that cannot be reached is dead code that looks like diligence.
4. **Zero is a suspicious answer.** Zero orphans, zero chains, zero errors on the first run of a
   brand-new check almost always means the check is not wired to anything. Confirm one true
   positive exists before believing the zero.

Learned July 29, 2026.

<!-- learning:2026-07-29-read-the-plugin-source-before-writing-to-its-table -->
**July 29, 2026** (from: collapsing 24 redirect chains across localservicespotlight.com + dennisyu.com, July 29, 2026)

### When a plugin's REST API is undocumented, download the plugin and read it

Two redirect tables needed surgical edits and neither API was documented in a way that answered
the only question that mattered: *what happens to the fields I do not send?* Guessing against a
live table with 34 and 192 rules on it was not acceptable, and probing by trial risked detaching
real redirects carrying thousands of hits.

So both plugins were downloaded from the wordpress.org repo at the exact installed version and
read. Ten minutes, and it turned two unknowns into contracts:

- **RankMath Redirections** has no route that LISTS redirections. The read path is
  `status/exportSettings` (redirections ride along in the export). The write path is
  `updateRedirection`, which is really the post-metabox save handler: it rebuilds the rule from
  `(redirection_id, url_to, sources, header_code)`. **Omit `redirectionSources` and the source is
  rebuilt EMPTY**, silently detaching the rule from the URL it exists to catch. It also rejects an
  empty `objectID`, which a standalone rule does not have — pass an id matching no post, because
  a real one makes that post's metabox claim it owns a redirect.
- **Redirection plugin** (`redirection/v1/redirect`) sanitises the whole payload and then does a
  full row `UPDATE`. A partial patch drops every field you left out. The payload has to be the
  GET item echoed back with only the target changed — and `hits` / `last_access` must be OMITTED,
  because the sanitiser maps them onto `last_count` / `last_access` and rewrites the counters.
- Its import path is safe but useless for repairs: `set_redirections()` skips any row whose
  source already matches an existing rule, so re-importing corrected copies changes nothing.

**Rules:**

1. **Read the source before the first write, not after the first surprise.** `curl` the versioned
   zip from wordpress.org, unzip, read the sanitiser and the update method. Cheaper than one bad
   write to a production table.
2. **Find out whether update means PATCH or REPLACE.** If the model sanitises into a fresh array
   and calls `$wpdb->update` with it, every field you omit is erased.
3. **Audit every redirect engine a site has, not the first one you find.** dennisyu.com runs
   RankMath Redirections AND the Redirection plugin at once. `X-Redirect-By` proved the plugin
   wins; fixing the RankMath copies changed nothing a visitor could see — 2 of 13 "fixes" held
   and the rest still measured 3-4 hops. **`X-Redirect-By` on the response is the ground truth
   for who is actually in charge.**
4. **Never auto-rewrite a regex rule.** Its source is a pattern, not a URL, so hops cannot be
   measured, and its target may contain capture groups. Report it and stop.
5. **A rule pointing at itself is a live infinite loop, not a chain.** Detect "never lands after
   N hops" as its own class and never auto-repair it — the correct destination is an editorial
   decision. One such rule had taken 12,190 hits.
6. **Check the trailing slash on high-volume rules.** A target of `/$1` where WordPress canonical
   wants `/$1/` costs an extra 301 on every request. On the busiest rule on the site that was
   829,576 requests each paying for a hop nobody needed.

Learned July 29, 2026.

<!-- learning:2026-08-03-prefer-the-instruction-that-cannot-go-stale -->
**August 3, 2026** (from: Ahrefs free-DR deprecation follow-up after the anthony-hilb-seo-tracker run)

### A conditional built on a vendor's date rots in every copy except the one you corrected

The anthony-hilb report flagged that Ahrefs' `public-domain-rating-free` endpoint stops accepting
unauthenticated calls on August 10, 2026 — seven days out, and the date of the tracker's own next
run — and recommended a "5-minute free API key registration." Chasing that down produced two
findings, and the second is the one that generalises.

**1. The registration was never necessary, and checking took one call.** The workspace MCP already
authenticates with a paid Lite key. The "free API key" in Ahrefs' warning is aimed at callers who
hold no key at all. `site-explorer-domain-rating` returns the identical number on the key we already
have — verified across two domains the same day (anthonyhilb.com DR 10 from both endpoints,
michaelkrigsman.com DR 1.0 from both) — for ~50 units against a 100,000/month allowance. It is also
*more accurate*: the free endpoint lags the authenticated series by about a day, which is precisely
what wrote a wrong DR 11 into the 2026-07-20 snapshot. So the "deprecation fix" was really a defect
fix that had been available all along.

**Rule: before scheduling work to satisfy a vendor's new requirement, check whether the credential
you already hold satisfies it.** A deprecation notice describes the vendor's default caller, not
your setup.

**2. The instruction had already rotted in five of six copies.** The block telling agents to prefer
the free endpoint lived in six skill files. On July 27 the cutoff moved from August 1 to August 10,
and exactly ONE file — `weekly-brand-maa.md` — received the correction. On August 3 the other five
still read *"Until August 1, 2026 keep using `public-domain-rating-free` first"*: a deadline that was
both wrong and two days expired, still actively instructing agents toward the dying endpoint. Nobody
noticed, because each file was individually plausible and nothing compares them.

The fix was not to propagate the new date. It was to **delete the date**: the rule is now
unconditional — *use `site-explorer-domain-rating`, always* — with the dated version struck through
beneath it as the record, plus a pointer at the top of the section so an agent reading top-to-bottom
cannot hit the stale narrative first.

**Rules:**

1. **Prefer the instruction that cannot go stale over the one that is merely correct today.** "Use X"
   survives indefinitely. "Use X until DATE, then Y" is a maintenance obligation in every copy,
   forever, and it fails silently and invisibly — an expired conditional reads exactly like a live one.
2. **When a correction lands on a duplicated instruction, grep for the other copies in the same
   breath.** This is the same shape as the standing rule in `Skill-Learnings/README.md` that "a
   standing contract recorded in one file is not a standing contract," and the same shape as the
   July 29→31 gap between a rebuild gate being learned and the runner being changed. Three
   independent recurrences means the default is wrong: assume duplication until a grep proves
   otherwise.
3. **A date copied out of a vendor's warning is the least durable thing in a skill file.** Where one
   must be written down, write it as "as of <Month D, YYYY> the API said X" so the staleness is
   visible on the page — and pair it with a dateless instruction that stays correct if nobody ever
   revisits it.
4. **Check the whole fleet of callers, not the one that surfaced the problem.** Of 31 scheduled task
   prompts, only two named the dying endpoint and two others were already on the authenticated one.
   Grepping the mirrored prompt set answered in one call what would otherwise have been six file
   reads and a guess.

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
  request. The sync copies every rule into `AGENTS.md`; universal agent-behaviour rules
  enter every distributed `SKILL.md`, while published-page/design rules enter only the
  skills declaring their scope. That makes each standalone skill carry the full rules
  that actually govern its work without links to repository files it does not ship.
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
- Treat `401`, `403`, `405` and `429` from Instagram, Facebook, X and LinkedIn as *pass*;
  LinkedIn's non-standard bot-block `999` is also a pass only on LinkedIn hosts.
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

<!-- shared-rule:public-documentation-auditable-truth:start -->
## Public documentation has one auditable truth

- **Publish one truth, not a fresh island inside a stale page.** A generator must own
  every claim derived from the same source: visible dates, counts, status cards,
  tables, changelog, links, metadata, and JSON-LD. On 2026-08-31 the Scheduled Jobs
  Fleet page showed a July 22 headline and eight automations around an August 25
  generated table with 53 rows. WordPress and RankMath carried the newer timestamp
  while the manual TechArticle schema carried the older one. Updating one HTML
  marker was therefore not an update to the document.
- **Render facts from typed canonical data.** Do not hand-copy a count, version,
  repository name, bundle name, cadence, or job status into prose. Generate it from
  the marketplace manifest, scheduler API, or other named owner. Label the unit:
  released skills, Task Library task records, scheduler definitions, observed jobs,
  and partner-specific agent roles are different things even when a page calls all of
  them “agents.”
- **Separate the clocks.** `last_checked` is when a named verifier compared the page
  with its sources. `last_changed` is when the public meaning last changed.
  `last_published` is when that revision reached the live URL. A no-change run advances
  only `last_checked` and still leaves a receipt. A generator write that changes only
  an inventory block does not advance the surrounding article's `last_changed` unless
  every dependent claim was reconciled.
  The live `https://blitzmetrics.com/scheduled-jobs-fleet/` target has a concrete
  daily-refresh SLA: its structural fleet sweep blocks when `last_checked` is more
  than 36 hours old. Other live public targets explicitly tagged `current-live`
  have a 30-day re-verification SLA. Immutable receipt/history targets and pages
  without that live-target policy have no inferred max-age rule; their freshness
  remains an explicit target policy or judgment check, never a guess from old HTML.
- **Sign the document without replacing the expert.** Keep the human subject/author,
  and separately name the maintaining function/job, namespaced public agent identity
  (`agent:<slug>` or `job:<slug>`), exact runtime-reported model
  (otherwise the literal `UNKNOWN`), actual human reviewer or an honest pending-review
  state, public-safe source URL and revision, public-safe capture alias, and success or
  failure result. Never invent a reviewer or imply that an agent is the human expert.
  `data-source-url` points to an approved public source or sanitized source manifest;
  `data-capture-run-id` is a public alias, never a private scheduler/job ID. Private
  prompts, schedules, paths, tokens and source records stay in the private receipt. If
  no truthful public-safe source can be linked, the page does not satisfy this public
  contract. Generic pages use the tracked append-only public documentation actor
  registry and a concrete public human name rather than a role/team phrase. Its
  canonical discovery artifact is
  <https://github.com/dennisyu/local-service-spotlight-skills/blob/main/standards/public-documentation-actor-registry.json>
  and its machine schema is
  <https://github.com/dennisyu/local-service-spotlight-skills/blob/main/standards/public-documentation-actor-registry.schema.json>.
  Published registry versions are immutable; the numerically newest current
  selection authorizes fresh generic-page audits and may revoke an old actor.
  The fleet
  scope additionally uses hash-selected versioned actor, reviewed-human, and model
  registries; raw strings must exactly equal a registered member.
  Multi-part and culturally unspaced Unicode names are valid; fleet
  publication separately restricts that name to its reviewed source-controlled roster.
  For the fleet, the source is the resolving sanitized manifest at
  `receipts/agent-fleet/sources/<sourceRevision>.json`, not the receipt-contract README.
  Standalone agents discover the source ledger at
  <https://github.com/dennisyu/local-service-spotlight-skills/tree/main/receipts/agent-fleet/sources>,
  the public receipt/registry contract at
  <https://github.com/dennisyu/local-service-spotlight-skills/blob/main/receipts/agent-fleet/README.md>,
  the fleet identity-registry schema at
  <https://github.com/dennisyu/local-service-spotlight-skills/blob/main/receipts/agent-fleet/identity-registry.schema.json>,
  and the definitive live article at
  <https://blitzmetrics.com/scheduled-jobs-fleet/>.
  The source-only manifest is stable across retries: it binds the canonical source
  repository, full revision, generator-contract version, configured, archived,
  invalid, and public-definition counts, plus the selected actor/human/model registry
  versions and exact identity-registry SHA-256, but no candidate hash, run identity,
  or clock. The content-addressed identity-registry artifact is committed before the
  source manifest; published registry versions remain immutable, while a newer current
  version may revoke an identity for new fleet evidence without invalidating old
  hash/version-bound receipts.
  Multiple candidates from one source revision reuse its exact URL/bytes; a new source
  revision gets a new append-only manifest. If a current fleet identity-registry
  pointer advances, fresh evidence may not reuse a same-revision manifest that selected
  the prior current registry: create a reviewed source commit and new source manifest
  bound to the current registry. Historical receipts still resolve their old
  hash-selected immutable version. The candidate remains blocked until that
  manifest resolves. Every substantive
  run keeps a private receipt even when no public meta
  article is authorized.
- **Use one visible, semantic provenance rail.** Put the audit fields in an `<aside>`
  or `<section>`. Before the deterministic publication receipt resolves, mark it
  `data-document-provenance="pending-external-verification"`; use
  `data-document-provenance="receipt-linked"` only when the named committed receipt
  already exists at render time and the rail names the real human reviewer. Exact
  candidate bytes emitted pending remain intrinsically pending after their URL later
  resolves; consumers read the external verdict. Re-rendering them linked creates a
  new candidate. `receipt-linked` means only that the receipt exists. Keep the two
  result layers separate:
  `data-scheduler-capture-result` reports only the upstream scheduler capture, while
  `data-publication-verification-result` is `pending` on a pending candidate and is
  `success` or `failure` only on a receipt-linked rendering that mirrors the receipt.
  An exact fleet candidate is not rewritten merely to certify itself; consumers resolve
  its deterministic external receipt. Reject the legacy generic `data-capture-result`
  because it cannot say which layer it describes. Use
  `data-verification-scope="external-exact-live-bytes"` for an exact response contract.
  The fleet's concrete value is
  `external-exact-raw-wp-body-and-inclusive-marker-slice`: the verifier separately
  proves the exact raw owned WordPress post-content body (including outside whitespace)
  and the unique inclusive anonymous slice from the exact
  `<!-- BM-FLEET-PAGE:START -->` through `<!-- BM-FLEET-PAGE:END -->` byte markers.
  It records the SHA-256 and byte length of the whole anonymous response and checks the
  single Article owner and its `dateModified`. The local candidate permits only
  whitespace outside its sole ordered marker pair.
  Put every enforced attribute on the rail itself: author, maintaining function, agent,
  model, reviewer, public scheduler-capture ID/result, publication-verification result,
  deterministic publication receipt ID, public ledger index and mutable discovery URL,
  public source URL/revision, and both clocks. Expose those values in reader-visible
  text. Make the source and resolving ledger index actual visible links; expose the
  expected discovery URL as text rather than a knowingly unresolved anchor while the
  receipt is pending. Once the state is `receipt-linked`, expose exactly one visible
  link whose `href` is that discovery URL, so ordinary link resolution can prove the
  named receipt exists. The fleet also puts the receipt-contract README in
  `data-source-contract-url` and exposes that exact URL through a distinct visible link
  with a non-empty reader-facing label. Use visible `<time>` elements that render the corresponding dates,
  whose `datetime` values exactly match the clocks in either order, and whose
  `Checked`/`Changed` labels are inside, immediately before, or immediately after the time.
- **Let the external verifier own the verdict.** The page never certifies its own bytes.
  The committed public receipt is one envelope; a separate local/private verification
  wrapper pins that receipt's ledger commit, path, immutable commit/blob URL and SHA-256,
  fetches the exact blob, then compares it with the candidate fields. The public receipt
  cannot contain its own commit hash. Publishing a second “verified” rendering would
  change the candidate bytes, so consumers resolve the pending/linked state at the
  external receipt. The mutable discovery URL is only a deterministic lookup; only the
  private wrapper's exact-commit URL plus blob SHA-256 is immutable proof.
  A verified fleet receipt binds the already-committed companion source manifest's exact
  SHA-256 from the later receipt commit's tree. It also carries an external browser attestation:
  `browserVisibilityVerified=true`, a public-safe browser verifier and run-receipt ID,
  and `browserCheckedAt`. The browser check must occur no earlier than Article/WordPress
  modification and no later than the receipt's `checkedAt`; the generator never writes
  that attestation for itself.
  `datePublished` stays separate. Schema `dateModified` is the actual WordPress
  publication-modified instant, not an alias for either visible evidence clock. The
  external verifier requires the single Article `dateModified` to equal the WordPress
  modified instant and to fall no earlier than the candidate's `last_checked` and no
  later than browser verification, which is no later than the receipt's `checkedAt`.
  The public-ledger validator can independently
  enforce the upper bound; the candidate-bound external verifier proves the lower one.
  Preserve all three clocks and allow only one publisher/Article owner.
- **Prove scheduled state with execution receipts.** “Scheduled” means a definition
  exists. “Observed” means a firing left an immutable timestamped success or failure
  receipt containing timezone, runtime, stable job/run ID, source revision, result,
  destination, and live readback. Expire one-shots after their run window and classify
  disabled, paused, archived, failed, and unknown work separately from active work.
- **Fail visibly and fail closed.** If a source cannot be fetched, a scheduled check
  leaves no receipt, a reviewer has not reviewed, or values conflict, show `unknown`,
  `stale`, or `verification failed`; do not stamp “updated.” Cache-fill time is never
  a content-modified time.
- **Keep the knowledge graph reciprocal.** Every pillar, spotlight, partner page,
  definitive article, task, skill, and authorized meta article links back to its
  canonical owner and forward to the relevant examples and receipts. Reuse the shared
  spine: The System · Content Factory · Task Library · canonical skills/install ·
  Scheduled Jobs · receipt/meta policy · changelog.

The source sweep proves one structurally renderable rail has the required same-element
fields, real ISO instants, visible labels/links, and matching semantic timestamps. It
ignores comments and inert/closed containers and evaluates inline plus ordinary,
unconditional same-document CSS for the supported tag/class/id/attribute selector
subset, including common explicit offscreen, zero-clip, zero-filter, transparent-text,
and extreme text-indent hiding declarations. It deliberately does not pretend to compute
external stylesheets, conditional media/container rules, layers, animation, occlusion,
or the complete browser cascade. The deterministic publication readback must therefore
inspect the rendered browser's computed `display`, `visibility`, `content-visibility`,
`opacity`, clipping, filter, mask, transform, position, text paint, non-empty client boxes,
viewport intersection, and sampled occlusion for the rail, both times, source, ledger,
and fleet receipt-contract links. Neither check can prove
that the named person reviewed the page, the source revision is genuine, or two numbers
mean the same unit. Those assertions require source comparison and immutable receipt
readback; the structural contract is necessary, never sufficient.
<!-- shared-rule:public-documentation-auditable-truth:end -->
