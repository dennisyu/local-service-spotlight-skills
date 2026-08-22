---
name: security-audit
description: Continuously verify that a website is still the site you published — no injected spam, no rogue admin, no hidden plugin, no different page served to Googlebot than to humans. Use to stand up monitoring on a new property, to run a point-in-time compromise check, to investigate a "my site looks hacked" report, or as the daily read-only sweep across a network of sites. Read-only by default; it finds and proves, it does not clean.
author: Dennis Yu — Local Service Spotlight
references:
  - https://localservicespotlight.com/security-audit/
  - DealCon-Skills/evidence-verification.md
  - DealCon-Skills/seo-audit.md
  - DealCon-Skills/client-access-checklist.md
  - Fleet-Security-2026-07-27/README.md
  - Sigrun-SOMBA/security/monitor.py
rule-scopes: published-html, design-review
---

# Security Audit

**Use this when** you are responsible for a site staying the site you published — which, on
a managed network, is every day, not the day someone complains.

This skill exists because of a specific pattern we kept losing to: **we found out from the
outside.** A first-degree LinkedIn connection messaged at 6:19am asking whether we had been
hacked. A Search Console email about video markup turned out to be three sites serving a spam
storefront. A client forwarded a newsletter about a WordPress vulnerability and asked whether
it affected his sites — it did, and the sweep that question triggered found more. Every one of those was discoverable from outside, for free, with no
credentials, on any morning before it was reported to us.

## The one idea

**A site is compromised the moment it stops matching its own baseline — not the moment
somebody notices.**

So the job is not "look for malware." Malware you have never seen is invisible to you. The
job is to **write down what the site is when it is known-good, and then diff it every day.**
A new external script domain is suspicious whether or not you recognise the payload. A new
admin user is suspicious whether or not you know what they did.

---

## The seven checks

All read-only. All runnable against any WordPress property with a REST endpoint and an
application password. Six can run credential-free from outside.

| # | Check | What a failure looks like |
|---|---|---|
| 1 | **External resource inventory** | A script, iframe or link to a domain that was not in yesterday's baseline |
| 2 | **Spam-injection markers** | Known link-spam domains, casino/pharma keyword blocks, hidden-link patterns in the rendered HTML |
| 3 | **Users** | A new account, or an existing account whose role escalated |
| 4 | **Plugins** | A new or removed plugin, a status flip, a version *downgrade*, or a version that is not a real published release |
| 5 | **Reachability** | A critical page that stopped returning 200 |
| 6 | **Cloak check** | The page served to Googlebot differs from the page served to a human |
| 7 | **Did checks 3 and 4 actually run?** | An unreadable REST endpoint, an unparseable 200, or an empty baseline |

### Check 7 is the one that makes the other six trustworthy
An endpoint that 403s and a site with zero plugins produce the same empty list. Without a
guard, "we could not read the plugin list" silently renders as "no plugins changed" — the
monitor reports **clean** on the day it went blind. So: an unreadable endpoint is its own
ALERT, naming the real cause, and that half of the diff is **SKIPPED** — never reported as
mass deletion, and never allowed to pass as clean.

This generalises past security. *Any* check whose failure mode resembles its success mode
needs a third state.

---

## Three states, never two

The hardest bug in this whole skill is the two-valued answer. When the monitor asked
wordpress.org "what versions of this plugin exist?", a `None` reply meant two opposite
things: **the plugin is premium and not listed there** (fine, forever) and **wordpress.org
did not answer** (a real blind spot). Both printed the same alert line, so a paid plugin
alerted every single morning — and an alert that fires every morning is an alert nobody
reads.

The fix is the shape, not the wording:

- **NOT_LISTED** — a definitive answer (404, or a 200 whose body is `false`). Advances the
  baseline, logged as INFO, and states plainly that the version was *not verified upstream*.
- **UNREACHABLE** — timeout, 5xx, unparseable. Still ALERTs, names the upstream service
  rather than accusing the plugin, and retries with backoff so one network blip cannot
  manufacture a security alert.
- **A real version set** — compare normally.

And delete the hand-maintained exception list. We had a `PREMIUM_SLUGS` constant listing
which plugins to excuse; hand-maintained lists drift behind the thing they describe.
wordpress.org answers the question itself, so ask it.

---

## Prove the monitor can fail

A check that cannot fail is not a check. Before you trust a clean result, run **live negative
tests** against the real baseline in memory (never writing to the baseline file):

- control → expect 0 alerts
- inject a rogue admin → expect exactly 1
- remove a plugin → expect exactly 1
- tamper a version → expect exactly 1

Only then is "clean" an earned result. When we did this the first time, the test suite went
from 55 to 116 assertions and immediately caught a defect the live path would never have
reached: the new retry branch called `time.sleep()` and `time` was never imported — code that
only executes during a wordpress.org outage, which is exactly when the monitor matters most.

---

## What the real incidents taught

**A hidden plugin is not in the plugin list, by design.** One backdoor shipped as "Web Media
Optimizer" and filtered *itself* out of `all_plugins`, stripped its own action links, and
removed itself from update checks. A clean plugin audit meant nothing. It was found by
requesting its file path directly and comparing the status code against a control path that
should not exist: real file → 200, control → 307. **Probe for the thing, do not ask the list.**

**Payload and repair are two halves.** The same compromise had a dropper in `mu-plugins/`
and a hidden fake plugin. Removing one and declaring victory is how a backdoor self-heals.

**Cloaking is invisible from a browser.** Three sites answered 500 to humans and 200 with a
spam storefront to Googlebot. Nobody clicking around would ever see it.

**Not every scare is an incident, and saying so is the deliverable.** A "lickfix malware"
report turned out to be a Cloudflare bot-challenge interstitial. Sixteen independent checks
came back clean and the honest answer was *no active malware*. An audit that can only
conclude "compromised" is not an audit.

**Rate-limit yourself.** Chained manual runs against one host earned a 429 that got logged as
an ALERT. Space runs out, and annotate self-inflicted noise in the log immediately so nobody
reads it as an incident six weeks later.

---

## Running it across a network

1. **Baseline every property** the day you take it on. No baseline, no monitoring — and say
   so out loud rather than implying coverage you do not have.
2. **Run daily, read-only, from a residential IP** with a full browser User-Agent. Datacenter
   IPs and minimal UAs get edge-blocked and you will audit the WAF instead of the site.
3. **Alert on change, log on clean.** The log is the evidence that the quiet days were checked.
4. **Never auto-remediate.** Writing to a compromised site destroys evidence and usually does
   not reach the interceptor anyway. Diagnose fully, package the fix, hand it to a human with
   host access.
5. **Count what you do not cover.** If the network is 198 sites and you can enumerate 49, the
   report says 49 of 198 — not "the fleet is clean."

## Definition of done
- Every monitored property has a dated known-good baseline in version control.
- Every check has a third state for "could not determine."
- The negative tests pass — the monitor demonstrably catches a planted change.
- The uncovered count is stated in every report.
- No cleaning was performed by the audit itself.

## Learned in the field

*Appended automatically by the self-improvement loop (Skill-Learnings/): dated lessons from real runs. Newest at the bottom.*

<!-- learning:2026-08-02-one-message-for-two-opposite-facts -->
**August 2, 2026** (from: sigrun.com security monitor — a paid plugin alerted every morning forever because "not listed" and "unreachable" printed the same line)

### When one code path can produce a message for two opposite facts, the message is wrong in both cases

The sigrun.com monitor verifies each plugin version against api.wordpress.org. Its lookup returned `None` for
two situations that have nothing in common:

- **wordpress.org answered, and it does not distribute this plugin** — true of every paid add-on (Elementor
  Pro, Yoast Premium, WPConsent Premium) and of the site's own custom plugin.
- **wordpress.org could not be reached at all** — a timeout, a 5xx, a WAF interstitial.

Both printed `upstream UNVERIFIABLE ... lookup failed`. One sentence, two opposite meanings, and the failure
runs in both directions:

1. **It never clears.** A paid plugin nobody had hand-added to the `PREMIUM_SLUGS` allowlist alerted every
   single morning, forever, and the only way to silence it was for a human to edit a hardcoded set. That is
   alert fatigue attached to a scheduled job. This monitor exists to catch the next infection on day one — and a daily alert everyone learns to skim rebuilds the exact condition it was built to remove.
2. **It hides the real thing.** During a wordpress.org outage, every ordinary plugin bump prints that same
   "UNVERIFIABLE" line. A genuinely tampered plugin folder arriving in that window would have been visually
   identical to the routine noise. The one line a human most needs to trust said the same thing whether the
   news was "nothing to see" or "someone edited your plugins."

**Rules:**

1. **Distinguish "answered no" from "did not answer."** A 404 is data. A timeout is the absence of data. Any
   function that collapses them into one return value has thrown away the more important half. Return a
   three-state result, not a nullable one.
2. **A hand-maintained allowlist is a clock that runs slower than the thing it describes.** `PREMIUM_SLUGS`
   had two entries and the site had four unlisted plugins. Derive the answer from the authority (wordpress.org
   already knows) instead of restating it locally.
3. **Retry before you alarm; vary time before you vary anything else.** A one-second network blip should not
   be able to manufacture a security alert. Backoff-retry the unreachable case, then report it.
4. **Dispatch on type and fail CLOSED.** The sentinel chain `if known is UNREACHABLE ... elif nv in known`
   would substring-match on a sentinel (`"1.1" in "NOT_LISTED"`) or raise `TypeError` on `None` if identity
   ever missed. Check the *shape* of the good case first and let everything unexpected fall through to the
   alert branch — a security check must never be able to pass by accident.
5. **Test the path that only runs during the emergency.** The new retry code called `time.sleep()` with `time`
   unimported. It executes only when wordpress.org is down — i.e. only when the monitor matters — so no live
   run would ever have caught it. Any branch that fires only under failure conditions needs a test that
   simulates those conditions, because production will never rehearse it for you.
6. **Prove red before you trust green.** Reconstructing the pre-change code and running the new suite against
   it produced 17 failures and a `TypeError`. Without that step, 116 passing assertions prove only that the
   tests agree with the code that was just written.

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

<!-- shared-rule:definitive-articles-show-what-they-are-and-where-they-fit:start -->
## Definitive articles show what they are and where they fit

- **The marker is a reviewed semantic claim, not a workflow status.** Mark a page as a
  Definitive Article, Definitive SOP or Definitive Framework only after a reviewer has
  confirmed that its labels, steps, links, evidence and canonical ownership agree with
  the accepted source of truth. A complete Task Library task, an all-tasks-complete hub
  or a `READY` state is useful workflow evidence, but none is sufficient by itself.
- **Mark the reviewed canonical hub visibly.** Put the appropriate marker above the
  opening summary so a reader can distinguish the maintained source of truth from a
  supporting post before scrolling. Supporting stories, updates and meta-articles point
  to the hub; they do not wear the marker themselves.
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

No fleet regex enforces this honestly: the crawler cannot infer whether a page is the
canonical hub, which framework governs it, or which boxes should be highlighted. Enforce
it in the definitive-article preflight and visual review.
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
