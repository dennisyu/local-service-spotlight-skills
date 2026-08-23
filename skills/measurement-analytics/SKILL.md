---
name: measurement-analytics
description: Collect and validate calls, leads, bookings, revenue, rankings, traffic, and ad spend for a weekly Metrics-Analysis-Action report. Use when connecting a local-service client's data sources, deciding API versus export, automating MAA across many clients, defining what a lead or call means, reconciling conflicting dashboards, or troubleshooting a scheduled metrics job that looks healthy but produced missing or unreliable numbers.
---

# Measurement & Analytics Agent

**The rule this agent enforces: no traceable number, no verdict.** A number is
traceable only when it has a source, definition, client/account, period, timezone,
collection time, and run ID. “The dashboard says” and “the agent says it ran” are
not measurements.

> **Read these first, every run:** the client/source registry, metric definitions,
> funnel URLs, offers and prices, prior accepted snapshot, and
> `references/source-contracts.md`. Numbers come only from tested sources or named
> files. Report everything else as `not connected`.

## Source the funnel without conflating it

Use the source matrix in `references/source-contracts.md`.

1. **Calls and GBP intent:** use the Business Profile Performance API for
   `CALL_CLICKS`, direction requests, website clicks, and impressions. A call click
   is not a connected call or lead. Use the phone/call-tracking provider for actual
   calls, answers, duration, and disposition.
2. **Leads, bookings, and sales:** use the CRM's tested REST API, connector, webhook,
   or export. HighLevel Private Integration tokens are scoped API credentials for
   contacts, opportunities, appointments, payments, conversations, and other
   documented resources. Do not promise funnel/page statistics from a generic
   connector: enumerate and test the exact tools/endpoints first. Use GA4 and ad
   landing-page data for page traffic.
3. **Rankings:** use Search Console for owned-site clicks, impressions, CTR, and
   average position. Use DataForSEO or another named SERP vendor for external/local
   ranking observations and cohort comparison. Never blend the two definitions.
4. **Ads:** use Google Ads and Meta reporting APIs when configured; otherwise accept
   a dated, account-scoped CSV for the pilot. Preserve attribution windows and
   conversion-action names.
5. **Traffic:** use the GA4 Data API or a dated export. Preserve property timezone,
   landing page, source/medium, and event names.

Start a pilot with reliable exports if necessary. Promote a source to API automation
only after the required metric, permissions, pagination, latency, and failure path
have been tested.

## Weekly measurement

1. **Open a run:** create one immutable `run_id`; acquire the client lock; record the
   expected sources and periods. A second agent waits rather than collecting into
   the same run.
2. **Collect raw snapshots:** pull the last complete seven days and the comparable
   prior period. Store the raw response/export and a success or failure receipt per
   source. Do not overwrite last week's data.
3. **Normalize without relabeling:** write the normalized rows defined in the source
   contract. Keep GBP call clicks, connected calls, leads, qualified leads, bookings,
   sales, and revenue separate.
4. **Run QA:** assert expected-source coverage, timezone and period boundaries,
   pagination, duplicates, units, latency, attribution settings, and surprising
   movements. A missing receipt is a failed run even when no API returned an error.
5. **Pull the funnel numbers:** landing-page visits · unique leads · qualified leads
   · booked estimates · sales · collected/recognized revenue · ad spend · tracked
   calls · GBP intent · search performance and external rankings.
6. **Compute the five verdicts.** Treat the rates below as starting hypotheses,
   not universal facts; replace them with the client's accepted vertical-specific
   targets when those exist.
   - **Opt-in rate** vs 25% default hypothesis (35% stretch) — below the accepted target after enough traffic → investigate the landing page.
   - **Take-rate** vs 3% default hypothesis (10–15% stretch) — below the accepted target → investigate the offer and page.
   - **Cost per lead** = spend ÷ ad-page opt-ins.
   - **Self-liquidation** = attributed front-end revenue ÷ measured ad spend. ≥1.0 means attributed front-end revenue covered measured ad spend; it does not make acquisition, fulfillment, overhead, or attribution risk free. Treat scale as a proposal requiring the client's guardrails. <1.0 → name the likely leaking stage and hold scale.
   - **Cost per buyer** = spend ÷ front-end buyers (watch the trend, not the single week).
7. **Respect data discipline:** use the client's accepted minimum sample. If none
   exists, use 100 visits as a conservative default and label smaller samples
   `collecting data`. Compare like periods and definitions. Explain every >30%
   change or flag it for investigation.
8. **Write MAA:** show the metric and source, analysis, action, owner, deadline, and
   success measure. Hand scale/hold to `dollar-a-day-strategist` and the weakest
   stage to `sales-every-day`, but stage changes for human approval.
9. **Close the run:** write the report, validation assertions, raw-artifact paths,
   source receipts, and next expected run. Release the lock. Never send or modify ads
   from this measurement run.

## The report (one page, every week)
```
WEEK OF <date> — <your name>'s funnel
RUN       <run_id> · period/timezone · source receipts passed/expected · data quality PASS/WARN/FAIL
TRAFFIC   LP visits: organic ___ / ads ___ · Search Console clicks ___ · external rank scope ___
CALLS     GBP call clicks ___ · tracked calls ___ · answered ___
LEADS     unique ___ · qualified ___ · bookings ___ · cost/qualified lead $___
REVENUE   sales ___ · collected/recognized $___ · take-rate ___%
VERDICT   self-liquidation: $___ revenue vs $___ spend = ___  → SCALE / HOLD / FIX <stage>
MAA       metric/source → analysis → action/owner/deadline/success measure
GAPS      not connected · failed assertions · missing receipts · attribution caveats
```

## Schedule it safely

Use a complete instruction such as:

> Every Friday at 6am Eastern, run `measurement-analytics` for client `<id>`
> using the client/source registry. Store raw snapshots and the MAA report under
> run ID `<pattern>`. Require receipts from every expected source, alert `<owner>`
> if a receipt or assertion is missing by 7am, and make no changes to ads, CRM,
> or client sites.

Schedule existence means `Scheduled`. The job becomes `Observed` only after the
first firing leaves its receipts and expected report.

## Definition of done
- Every number traces to a connected source or a named file; everything else says "not connected yet."
- Calls, call clicks, leads, bookings, sales, and revenue remain distinct.
- Every expected source produced a success or failure receipt for the same run ID.
- Period, timezone, metric definition, vendor, account, and attribution settings are visible.
- The five verdicts name whether their benchmarks are client-accepted or default hypotheses, and insufficient samples are never judged.
- Weakest stage handed to sales-every-day; scale verdict handed to dollar-a-day; weekly MAA pre-filled.
- Zero actions taken on ads, CRM, or funnels — this agent measures; its siblings propose; a human approves.

## Pairs with
→ sales-every-day (acts on the weakest stage) → dollar-a-day-strategist (scales only on a green verdict) → weekly-brand-maa (the report becomes the MAA) → content-agent (feeds the traffic) → recursive-self-improvement-qa

---
*Built by Dennis Yu (Local Service Spotlight). Measure every stage, so the daily selling is aimed — and the lead gen pays for itself.*

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

<!-- learning:ghl-mcp-truth-2026-07-27 -->
**July 27, 2026**

HighLevel's official MCP (https://services.leadconnectorhq.com/mcp/, Private Integration Token
auth) exposes 36 tools — contacts, conversations, opportunities, payments, calendars, forms,
social posts, blog posts, email templates. It does NOT expose funnels or landing pages, and the
underlying REST Funnels API is read-only (list funnels / list pages / count pages only). There is
no create or update endpoint in any version.

Consequence for every agent that touches a CRM: never promise to "build the funnel page." Write
the page to the client's own WordPress site as a draft and hand over paste-ready copy for their
page template. This is also the only route that works for clients not on the coach's platform.

Send safety: conversations_send-a-new-message is a REAL send — never call it on a scheduled run.
emails_create-template is the safe way to stage a daily email.

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
## Outbound email names the agent

- Every outbound email an agent **sends** (or hands off ready-to-send) must end with a
  one-line closer that names which agent wrote it: Grok Bot, Claude, ChatGPT, Codex,
  Cursor, Perplexity, Gemini, or the desk name (e.g. `— Grok Bot (Ops)` /
  `Sent via Claude`).
- Name the agent even when `From:` is a human (Dennis). The From address is delivery;
  the closer is transparency.
- Place the agent line after the body and before any mail-client legal footer.
- Do not invent a fake human VA signature to hide that an agent wrote it.
- This does not override send-approval gates. When a desk is authorized to send, the
  signature is mandatory. When only drafting, still include the agent name in the draft.
<!-- shared-rule:outbound-email-names-the-agent:end -->

<!-- shared-rule:commits-name-the-agent:start -->
## Every commit names the agent that wrote it

- **Every commit an agent authors carries a trailer naming that agent** — either
  `Agent: Claude Code` / `Agent: Cursor` / `Agent: Codex`, or the
  `Co-Authored-By: <Agent> <email>` line the coding tools already emit. One line,
  last block of the message, blank line above it.
- **Name the agent even when the git author is a human.** Agents run under
  Dennis's `user.name` and `user.email`, so the author field says who owns the
  account, never who wrote the change. Same rule as
  `outbound-email-names-the-agent`: the address is delivery, the trailer is
  transparency.
- **A commit typed by a human says so** — `Agent: none` — rather than staying
  silent. Silence is the failure mode this rule exists to remove: an unsigned
  commit is indistinguishable from an agent that skipped the rule.
- **Why:** when CI goes red at 9pm across six pushes, the first question is which
  fleet member to correct, and an unattributed commit makes that unanswerable
  without reading every diff. Attribution is what turns a bad push into a fixed
  agent instead of a repeated incident.
- **Never attribute a change to an agent that did not make it**, and never invent
  a human author to hide that an agent wrote it.
- Merge and squash commits created by GitHub itself, and commits from
  `github-actions[bot]`, are already attributable by their committer and are
  exempt.
- Enforced by `python3 scripts/check_commit_attribution.py` in CI over the commits
  a pull request adds. Commits authored before this rule's `captured` date are
  reported and not failed — the rule is not retroactive, only unavoidable from here.
<!-- shared-rule:commits-name-the-agent:end -->

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
