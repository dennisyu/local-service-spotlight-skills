---
name: definitive-article-writer
description: Write the ONE canonical page that owns a topic or a person's name — comprehensive, source-linked, structured so Google ranks it and AI quotes it, with every thin post orbiting it. Use instead of publishing competing posts.
rule-scopes: published-html, design-review
---

# Definitive Article Writer

**Use this when** you want to own a topic — or a person's name — in Google and in AI answers. One comprehensive canonical page beats a dozen thin blog posts, because humans and machines both cite the page that settles the question. Step 9 of the Local Service Spotlight method.

## Inputs
- The topic or person, plus every fact you can prove: numbers, dates, names, clients, quotes, media.
- The mined transcript from `content-factory` stage 2, if the article starts from a recording.
- Your proof inventory from `positive-mentions-harvester` — third-party corroboration to cite.
- Every existing page on the subject — yours and competitors' — so you know what to absorb and what to beat.

## Steps
1. **Audit first.** If a canonical hub already exists on your site, improve it. Never publish a second page on the same topic — that's content vandalism; you'd split your own authority.
2. **Outline every question** a prospect, buyer, journalist, or AI could ask about the subject. Definitive means nothing left to ask. Boil the ocean — good enough is not enough.
3. **Write facts, not fluff.** Open with a 2–3 sentence plain-language summary — who, what, why it matters — because that's the block AI lifts verbatim. Every claim carries a number, a name, or a source link. Publish nothing you couldn't defend in diligence.
4. **Structure for machines.** H2s phrased as the questions people actually ask. Schema markup (Person, Article, FAQ). The entity's name spelled identically everywhere. A stable URL that never changes.
5. **Build the orbit.** Internal-link every related thin post INTO this page; link this page out to its sources and sibling hubs. Thin posts orbit the hub — they feed it, never compete with it.
6. **Make it the target.** Every clip, social post, podcast show-note, bio, and profile points at this URL. One topic, one URL — the Task Library principle.

## Anatomy — what's on the page, in order
- Plain-language summary (2–3 sentences a machine can quote).
- The facts: numbers, dates, names, each tied to its source.
- The story and strongest quotes from the recording.
- Embedded media — the interview or talk this came from.
- FAQ — the questions you outlined, answered directly.
- Links out to sources, across to sibling hubs.
A definitive article is a facts/SOP hub, not an essay. If a section doesn't inform or prove, cut it.

## Why AI quotes it
- AI engines lift the page that states facts plainly, with consistent entity spelling and sourced numbers.
- Corroboration decides ties: your harvested mentions (step 2) and entity plumbing (step 5) confirm what this page claims.
- A stable URL accumulates citations; a renamed one starts over. Pick the URL once.

## Failure modes — what kills a definitive article
- Publishing a second post on the same topic because writing fresh feels easier than improving the hub.
- Adjectives instead of numbers. "Leading expert" proves nothing; "110+ locations, $310M+" does — that's how you describe Zach Peyton.
- Changing the URL or title to chase keywords — you reset your own authority to zero.
- Letting it go stale. The hub is living: every new recording, deal, or mention updates it.

## Output
- One canonical, source-linked, schema-marked article at a stable URL — the page Google ranks and AI quotes for this subject.
- The orbit list: existing posts to re-link into the hub, plus every clip and profile that should point here.

## For DealCon — agency owners & acquirers
**If you run an agency:** the definitive article on your niche is what prospects read before the sales call — it pre-sells you as the documented authority, justifies premium pricing, and becomes a productized deliverable you can sell to every client.
**If you buy & sell companies:** a definitive article on you-as-acquirer — thesis, buy box, closed deals, references — is what sellers and brokers find before they reply; that's off-market deal flow. Post-close, write one per acquired brand so its authority survives the transition.
**Your edge:** name the topic where you hold facts no competitor can publish — your deal count, your niche data, your named clients. Write that page before someone adjacent to you does.

## Run on a persistent agent (Fable 5)
- **Loop to done:** outline every question, then loop until none are left unanswered — definitive means nothing left to ask. Walk the anatomy top to bottom: summary, sourced facts, media, FAQ, orbit links.
- **Self-verify:** run the failure modes as a checklist on your own draft — no second post on the topic, no adjective without a number, URL stable, nothing stale.
- **Compound with memory:** check memory and the site for an existing hub FIRST — improve it, never duplicate it — and carry the orbit list forward so every new asset points home.
- **Log the run:** note which questions the inputs couldn't answer — that's next month's capture list for `content-factory`.

See `boil-the-ocean.md` for the full operating principles.

## Notes — Dennis's method
- Harry Gold's harryjgold.com started as one Zoom interview — one capture, one canonical hub, everything else orbits it. Dennis's podcast-appearances page runs the same play: 236+ appearances tracked on one URL that every episode links back to.
- George Paladichuk's NaiL AI shows the niche version: own the definitive page on one tight topic — AI for roofing — and the category cites you by default.
- Write for the diligence reader. Facts with sources survive a buyer's scrutiny and an AI's retrieval; adjectives survive neither.
- One URL per task or topic is the backbone of the Local Service Spotlight Task Library — and each agent's own documentation is itself a definitive article (see `recursive-self-improvement-qa`).

## Definitive article & pairings
- Reference: https://blitzmetrics.com/definitive-article-guide/ · https://dennisyu.com/podcast-appearances/
- Pairs with: content-factory → **definitive-article-writer** → recursive-self-improvement-qa

## Learned in the field

*Appended automatically by the self-improvement loop (Skill-Learnings/): dated lessons from real runs. Newest at the bottom.*

<!-- learning:2026-07-19-backdated-content-contradiction -->
**July 19, 2026** (from: michaelkrigsman.com QA run (filed into the loop by skill-pack-propagation 2026-07-19))

Never backdate WordPress posts below the visible byline. On the Krigsman build, rendered
byline dates and the WP/schema datePublished diverged on 8 of 16 articles by up to 9
months — a self-contradiction any journalist or Google can see, and an EEAT risk. The
honest scheme: set the visible byline to "Episode NNN, recorded {air date}" and set
datePublished to the REAL publish date. Air date and publish date are different facts;
show both truthfully rather than forcing datePublished to match a backdated byline.

<!-- learning:2026-07-19-repurposed-article-disclosure-sweep -->
**July 19, 2026** (from: michaelkrigsman.com QA run (filed into the loop by skill-pack-propagation 2026-07-19))

When repurposing podcast or show episodes into articles, ALWAYS check each source episode
for an underwriter/sponsor block and mirror that disclosure in the article deck. On the
Krigsman build, 6 of 16 articles covered underwritten episodes with no disclosure —
including 3 underwritten by the exact sponsor (Gartner) the client engagement centers on.
Both the episode page and its /transcript page carry the underwriter block, so check both.
Undisclosed sponsorship in a repurposed piece is an EEAT and trust liability; the fix is a
one-line disclosure in the deck, not a rewrite.

<!-- learning:2026-07-20-a-minus-terminator-and-entity-linking -->
**July 20, 2026** (from: Daniel Goodrich's blog-grader (validated May 28, 2026 on Escape Fitness, grading "per Jennifer rubric") merged into jennifer + the writer chain)

Two rules from the production grader loop, July 20, 2026. First, the A- terminator: A- is the publish bar — when a draft grades A-, it is DONE; never revise past it (an A is reserved for world-class national-publication journalism, and chasing it is how agents fall into infinite revision loops). Revision budgets before human escalation: 3 rounds for a definitive/STRONG piece, 2 for a standard article, 1 for a short post. Second, route every named entity through the Entity Linking Decision Tree: a person in the network links to their personal-brand site; a company in the network links to its site; anything out-of-network — people, tools, concepts — links to the public canonical article on that topic, else stays plain text; anchor text is 3–6 descriptive words; each entity links on first mention only, never twice. On a personal-brand site write first person in the owner's voice; on a company site write third person — a POV mismatch caps the grade at B.

<!-- learning:2026-07-28-a-number-about-an-artifact-belongs-to-the-artifact -->
**July 28, 2026** (from: skill-pack-propagation daily run, July 28, 2026)

### A number about an artifact belongs to the artifact — derive counts, never type them

Bringing one pack onto the pipeline surfaced the same defect in six places at once, all of them
a human-typed number describing a file:

- the directory advertised **"18 skills"** for downloads that contained 19, **"17 agents"** for
  a 19-agent library, and a card literally named **"Task Library (246 SOPs)"** beside a badge
  reading 247;
- the member library page said **"17 AI agents"** in its hero and **"all ten skills"** in its
  download section — the "ten" had been wrong since the pack passed 10 in early July;
- the pack's own `README.md`, the first file anyone opens, opened with **"Thirteen installable
  agents"** while shipping 16;
- the copy-paste installer prompt members actually paste into Claude listed **10 of 17 agents**,
  so anyone following it hired a team two-thirds the size of the one they downloaded.

None of this was noticed, because nothing compares a sentence to a zip.

**Rules:**

1. **Derive every count at render time from the artifact.** Read the pack's `VERSION.txt`
   (or count its members) and print that. A count in a source file is a claim; a count read
   from the zip is a fact. Use the SAME key (`Skills: N`) in every pack's VERSION.txt so one
   parser serves all of them.
2. **Never bake a number into a label.** "Task Library (246 SOPs)" goes stale on the next run;
   "Task Library" plus a derived badge never does.
3. **Generate the README from the same list that builds the zip.** A README that can disagree
   with its own package eventually will, and it is the first thing the customer reads.
4. **Generate any prompt you ask people to paste.** It is not documentation, it is the product.
5. **Check coverage in BOTH directions.** The library builder validated "every slug in `order`
   exists as a file" and never "every file appears in `order`" — so a new skill got no card, no
   link and no install zip, silently. The gap is always the direction nobody checks.
6. If you must keep a literal, make the run FAIL when it stops matching. A replacement that can
   silently match nothing is not a replacement, it is a wish.

Learned July 28, 2026.

<!-- learning:2026-07-29-a-catalogue-is-not-a-graph -->
**July 29, 2026** (from: SEO-tree link audit across the 13 agent/skill surfaces, July 29, 2026)

### Being listed in the catalogue is not the same as being connected to the tree

Every one of our 13 published agent/skill pages was live, current, and listed on the master
directory. An actual link audit — pull each page's rendered DOM, decode any base64 payload,
extract links to the other twelve — found the graph full of holes:

- `aibuilderspotlight.com/skill-pack` and `dunkerspotlight.com/set-up-claude` linked **nothing
  at all**. Both dead ends.
- `sigrun.com/somba-agents` linked exactly one page — a partner's members' area with no route
  back into the system it belongs to.
- `blitzmetrics.com/task-library-dashboard`, the 239-skill page, linked neither the packs that
  contain those skills nor the agents that run them.
- `localservicespotlight.com/business-authority-pack` linked only its sibling pack — no path up.

None of this was visible in any report, because everything that existed was checked and
everything that was checked was fine. Publishing a page and connecting a page are two different
jobs, and only the first one had an owner.

**Rules:**

1. **Define the link tree in ONE file and render it from there.** Ours is
   `System-Hub/system_tree.py`: every node's rung, its sibling, and the block that draws the
   ladder. A tree that lives in twelve page bodies is twelve chances to drift.
2. **Put the whole ladder on every node with "you are here" marked.** A reader or a crawler
   landing on any leaf should be able to see the entire structure and their position in it
   without a back button. One shared block does this; twelve bespoke "related links" do not.
3. **Link one sibling each, arranged as a closed ring.** Every pack surface reachable from
   every other, and no two pages pointing at each other — reciprocal pairs read as link
   exchange, and a full mesh makes every page look identical.
4. **Verify links in the LIVE DOM, decoding payloads first.** Several of these pages render
   their whole UI from a base64 `data:text/html` iframe. A link check that reads only
   `post_content` sees an empty page and passes it.
5. **A gated page is verified by authenticated read-back, never a public GET.** A public fetch
   of a member-password page returns the password form; asserting against that certifies a
   broken publish as green.
6. **If nothing asserts a relationship, the relationship will rot.** Write the check the same
   day you build the structure — `verify_link_graph.py`, wired into the daily checklist,
   non-zero exit on any orphan, dead end, missing rung or redirect chain.

Learned July 29, 2026.

<!-- learning:2026-07-29-a-plugin-namespace-can-be-blocked-while-wp-v2-is-fine -->
**July 29, 2026** (from: publishing blitzmetrics.com/persistent-agents/, July 29, 2026)

### A plugin's REST namespace can be blocked while wp/v2 works perfectly

Setting the SEO title and meta description on a new blitzmetrics.com article returned **403** on
every POST to `/wp-json/rankmath/v1/updateMeta` and `/updateRedirection` — while POSTs to
`/wp-json/wp/v2/posts/<id>` on the same host, same Application Password, same full browser
header set, returned 200 all day. Probed both ways, JSON body and form-encoded, GET vs POST:
`GET /wp-json/rankmath/v1/` is 200, every POST under it is 403, and the body is the host's own
styled 403 page rather than a WordPress JSON error. That is a WAF rule scoped to a namespace,
not a broken credential and not a capability problem.

The second trap was worse. RankMath does not register `rank_math_title` /
`rank_math_description` with `show_in_rest`, so writing them through wp/v2's `meta` field
returns **HTTP 200 and stores nothing**. Reading the post back with `context=edit` shows `meta:
{}`. A publish job that trusts the 200 reports the SEO as set forever.

**Rules:**

1. **Diagnose a 403 by namespace and method before blaming the credential.** `GET
   /wp-json/<ns>/` plus a no-op POST tells you in two calls whether it is auth, capability, or
   an edge rule. Twelve days were once lost calling a WAF rule a broken app password.
2. **After any meta write, read it back.** If the field comes back empty, the write was
   accepted and discarded. A 200 is a receipt for a request, not evidence of a change.
3. **Know the fallbacks before you need them.** RankMath derives the meta description from the
   post excerpt and the SEO title from the post title when its own fields are empty — both
   writable through plain wp/v2. Setting `excerpt` produced the exact intended
   `<meta name="description">` in the rendered head. Verify in the head, not the API response.
4. **On WP Engine, purge before you verify.** `POST /wp-json/wpe/cache-plugin/v1/clear_all_caches`.
   A page trashed through the API kept returning 200 to an anonymous fetch until the cache was
   cleared, which reads exactly like a failed delete and invites a second, wrong repair.

Learned July 29, 2026.

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

<!-- learning:2026-08-03-the-message-about-the-artifact-drifts-faster-than-the-artifact -->
**August 3, 2026** (from: somba-skill-weekly-update — first run under the "tell all ~100 members, not one" mandate; found the pack current and every sentence describing it stale)

### The message about the artifact drifts faster than the artifact

The SOMBA skill pack was in perfect shape. `skill-pack-propagation` had rebuilt it every morning,
the daily verifiers were green, the zip on sigrun.com matched the zip on disk. Three new agents had
shipped that week and eleven more had absorbed 51 field lessons. The artifact was flawless.

Every sentence describing it was wrong.

The library held **22 agents**. Five separate member-facing surfaces said **nineteen**, or twelve, or
seventeen, or ten:

| Surface | What it said | Why it was wrong |
|---|---|---|
| `agents_status.json` note + 2 news items | "Your Agent Library is NINETEEN agents" | hand-typed |
| `somba_theme.AGENTS` | a hand-typed roster of **12** | fed every member's dashboard grid — ten shipped agents were invisible on ~100 dashboards |
| `build_agents.py` | `Agent {n} of 10` | live pages literally read **"Agent 21 of 10"** on 21 pages |
| `_publish/build_delivery_summary_page.py` | "all seventeen agents" ×3 | written when it was seventeen |
| `docs/agents/README.md` | "The team (17 agents)" | mechanism derived, output never regenerated |

Nothing failed. Nothing could. **A hand-maintained number has no way to know it is wrong**, and the
job that was supposed to announce the changes — `patch_news.py` — carried a hand-typed news list and a
hard-coded `TODAY_H = "20 Jul 2026"`. It was not a script; it was a document that had to be edited by
hand before every run. It had sat unedited for two weeks while the thing it describes was rebuilt
daily.

**The rule: the pipeline that MAINTAINS an artifact and the copy that DESCRIBES it decay at different
rates, and only one of them has a test.** We had built real machinery around the artifact — hash
manifests, coverage gates that hard-fail when `skills/` and `ORDER` disagree, three daily verifiers,
a link-graph checker. Zero of it looked at the sentences. So the pack could not go stale and the story
about the pack could not stay fresh, and the daily report was green throughout.

Everything now derives from `agents_manifest.json`: the roster, the counts, the "Agent N of M", the
prose in the delivery page, and the news items themselves — which are produced by diffing today's pack
zip against the dated backup from seven days ago and resolving each changed skill's own
`<!-- learning:ID -->` markers to their note titles. The generator has no list to edit.

### Corollary — a guard that compares a thing to itself cannot see consistent error

`dash_weekly.py` already had a guard for exactly this: it asserted that no two visible news items
claimed different Agent-Library counts. It passed, twice over. First because it matched **one
phrasing** — "Agent Library is N agents" — and the worst offender read "arranges all nineteen into six
departments." Second, and more importantly, because **all three stale claims agreed with each other.**
A set of items that are consistently wrong is precisely what self-comparison is blind to. The guard now
compares the message against `agents_manifest.json` — the artifact — and fails on any count that is not
today's, in any phrasing, spelled or numeric.

Same shape as the 2026-08-01 mirror finding (a weekly check of a daily source comparing the source to
its own snapshot rather than to the clock). **Guards must terminate at something outside the system
they are guarding.**

### Corollary — a checker that fires on correct behaviour is worse than no checker

The verifier written for this run failed three times before it was right, and all three were the
checker's fault, not the surfaces':

1. It looked for `<script id="vault">`; the real payload is `<template id="smb-vault">`.
2. It flagged the niche "Coaching" as a member-data leak. It is Sigrun's own nav — "My Coaching
   Philosophy" — on every page of the site. Fixed by subtracting terms that also appear on a public
   control page, so the check discriminates member data from site chrome.
3. It asserted "the agent library links 22 agents" against an anonymous fetch of a **password-gated**
   page, and then against the outer HTML of a page that ships its whole body inside a base64
   `data:text/html` iframe. Both times it read 0 of 22 and reported failure about a healthy page.

Three red lines on a green system. Ship that and the next person learns to skim past red. **Before
believing a failure, reproduce the thing the checker claims to have read** — and when a surface is
gated or encoded, the check has to unlock and decode it, or it is asserting against a login form.

### Corollary — verify the whole sequence, not the step you touched

Rebuilding the bundle made the published zip stale by two bytes. Republishing it made the
`/skill-packs/` directory stale, because that directory is written by two *further* scripts
(`update_index_packs.py`, `build_skillpacks_index.py --publish`) that run after the republisher. Only
`verify_directory_and_somba.py` caught it. **When you re-run one stage of a pipeline by hand, you have
re-run one stage of a pipeline by hand** — the stages downstream of it are now describing the state you
just replaced.

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
- **Unknown is never zero or failure.** Preserve `UNKNOWN`, `CONTRADICTED`, and `EXPIRED`
  with the exact question, owner, due date, and blocked action. Missing evidence routes
  to `DISCOVERY_REQUIRED`; do not invent a weighted score to hide it.
- **Amplify what is already working.** Observed new-idea, no-proof, undifferentiated,
  overbroad-ICP, unfocused-offer, or capacity conditions route to one development action
  and re-screening. They do not earn plumbing, publishing, or ad spend as a consolation.
- **Fail closed on authority.** Prospect screening is public-read-only. Publishing,
  messaging, permissions, Basecamp delivery, and spend require exact scoped approval;
  `Not Active`, `HOLD`, missing roster evidence, or blocked plumbing stops execution.
- The public guide is https://blitzmetrics.com/social-amplification/. The operational
  control plane is the roster-driven Money Tree; derived output folders are not state.
<!-- shared-rule:screen-gct-before-amplification:end -->
