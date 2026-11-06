---
name: personal-brand-website-agent
description: Build your entity home — your name as the domain, a facts-first homepage structured to earn a Knowledge Panel and become the one URL Google and AI treat as the truth about you. Use to create or audit a personal brand site.
rule-scopes: published-html, design-review
---

# Personal Brand Website Agent

**Use this when** you're ready to build (or fix) the authoritative URL about you — your name as the domain, a facts page that every profile, podcast, and press mention points back to. Step 4 of the Local Service Spotlight method.

> **Read these first, every run:** your **brand-voice document** and your **ideal-client context file**. If they exist in this Project / chat, use them so everything this agent writes already sounds like you and speaks to your person. If they don't exist yet, build a quick version before continuing — don't start from a blank page.

## Inputs

- Positioning brief from `personal-brand-strategist`: buy box, one-sentence differentiation, top-5 proof points.
- Scored proof from `positive-mentions-harvester` and the 30-day plan from `reputation-gap-analyzer`.
- Real numbers (years, clients, locations, dollars), one consistent headshot, every profile URL you own.

## Build pipeline (Dennis's order — don't skip steps)

1. **Research and disambiguate.** Google your name. List every same-name person and what makes you unmistakably you. Google must be able to tell you apart before it will trust your page.
2. **Register your name as the domain.** yourname.com, exactly. Taken? Add a middle initial — harryjgold.com — never a brand name or a pun.
3. **Generate the site** on the standard template below.
4. **Wire DNS** and confirm the site resolves on https.
5. **Publish**, then run `knowledge-panel-entity-seo` the same day.

## Homepage structure (this exact order)

1. **Hero** — name, your one-sentence differentiation, two CTAs, and an authority image: you on a named stage, with your lighthouse (the marquee name you're tied to), or doing the unmistakable work.
2. **Stats bar** — 4 real, provable numbers. Marko Sipila's markosipila.com leads with 300+ HVAC Quote customers, not "passionate about HVAC."
3. **My Story** — factual career arc with dates and companies, written so AI can quote it.
4. **What I Do** — 3 cards aimed at your buy box, not every service you've ever sold.
5. **Featured interview** — your single best podcast or talk, embedded.
6. **What People Are Saying** — testimonials with name, title, and a link to where each was said. camhazzard.com runs a full sourced testimonial wall.
7. **As Seen On** — logos and links of real placements only.
8. **Connect** — every profile you own, mirrored exactly in Person schema `sameAs`.

## Copy rules

- Facts page, not a sales page. Every claim links to its source; funnels live elsewhere.
- No adjective without a receipt. "Award-winning" needs the award, the year, the link.
- Flag anything unconfirmed during drafting — it does not ship.
- Write for the machine that will quote you: clean headings, alt text, descriptive links.

## Steps

1. Draft all eight sections from the brief and scored proof only.
2. Build on the template — one page, eight sections, nothing exotic.
3. Wire Person schema JSON-LD: your site as canonical home, `sameAs` to every profile.

   ```json
   { "@context": "https://schema.org", "@type": "Person",
     "@id": "https://yourname.com/#person",
     "name": "", "jobTitle": "", "worksFor": { "@type": "Organization", "name": "" },
     "url": "https://yourname.com", "image": "",
     "sameAs": ["<LinkedIn>", "<X>", "<YouTube>", "<press/podcast profiles>"] }
   ```

4. Add About, Press, Blog, Gallery, and Connect pages; publish an accessibility statement in the footer (WCAG 2.2 AA target, honest conformance status, monitored contact email, dated — per the BlitzMetrics accessibility-statement standard).
5. Publish and hand off to `knowledge-panel-entity-seo`.

## Output

- Draft homepage copy with every claim sourced, then a live site at yourname.com with schema wired.

## For DealCon — agency owners & acquirers

**If you run an agency:** your entity home is the credibility anchor prospects check before they sign — and a named, transferable asset that makes the agency itself easier to price and sell. **If you buy & sell companies:** this is where a motivated seller lands at 11pm after your first call and decides whether to trust you — your thesis, your closed deals, your face, one URL. **Your edge:** the hero headline is your differentiation sentence; if it could sit on another DealCon attendee's site, rewrite it until it can't.

## Run on a persistent agent

- **Loop to done:** run the whole pipeline — research, domain, build, DNS, publish — and loop until the site resolves on https with all eight sections, schema wired, and every claim sourced. Draft copy is the midpoint, not the output.
- **Self-verify:** audit your own page against the copy rules before handoff — no adjective without a receipt, nothing unconfirmed ships, `sameAs` mirrors the Connect section exactly.
- **Compound with memory:** build from the stored brief, proof library, and 30-day plan — never re-interview the subject for facts the chain already holds.
- **Log the run:** record what the template needed that the inputs didn't supply — that's the upstream fix for the next build.

See `boil-the-ocean.md` for the full operating principles.

## Notes — Dennis's method

- NAME = the domain. The entity home is the URL Google treats as authoritative about you; everything else orbits it and links back.
- The homepage is the most authoritative set of **facts** about you, each tied to a source. Not a "hire me" carousel.
- Harry Gold's harryjgold.com was built from a single Zoom interview — proof beats production. Don't wait for perfect assets.
- One headshot everywhere — site, LinkedIn, podcast art. Different faces create entity confusion that Step 5 then has to undo.
- In Content Factory terms this is core plumbing: the hub your tracking, retargeting, and every definitive article hang off.
- Boil the ocean on proof, not on design. The template is fixed so your facts do the work.
- If you have a brand name (not your name) like a business, still build the entity home at YOUR name and link the two — the person is the asset that compounds.

## Definitive article & pairings

- Reference: https://blitzmetrics.com/knowledge-panel/ · https://blitzmetrics.com/task-library/
- Pairs with: → knowledge-panel-entity-seo → ai-search-visibility

## Learned in the field

*Appended automatically by the self-improvement loop (Skill-Learnings/): dated lessons from real runs. Newest at the bottom.*

<!-- learning:2026-07-19-backdated-content-contradiction --> **July 19, 2026** (from: michaelkrigsman.com QA run (filed into the loop by skill-pack-propagation 2026-07-19))

Never backdate WordPress posts below the visible byline. On the Krigsman build, rendered byline dates and the WP/schema datePublished diverged on 8 of 16 articles by up to 9 months — a self-contradiction any journalist or Google can see, and an EEAT risk. The honest scheme: set the visible byline to "Episode NNN, recorded {air date}" and set datePublished to the REAL publish date. Air date and publish date are different facts; show both truthfully rather than forcing datePublished to match a backdated byline.

<!-- learning:2026-07-20-consent-scanner-blanks-inline-apps --> **July 20, 2026** (from: a partner's member dashboards — refiled from a stray root note by skill-pack-propagation on July 21, 2026)

A cookie-consent plugin can silently kill an inline JavaScript app for logged-out visitors while every logged-in test looks perfectly healthy. On a partner's member site the member-dashboard page rendered BLANK for members for three days while rendering fine for admins and in Elementor preview. Root cause: the consent plugin (WPConsent) pattern-matches INLINE SCRIPT CONTENT server-side and rewrites any matching tag to type="text/plain" until the visitor accepts cookies. Member data (facebook, linkedin, youtube profile URLs) matched tracker signatures; on a second page, random base64 ciphertext happened to match the TikTok-pixel signature. Admin sessions and editor previews bypass the scanner entirely, so the outage was invisible to every internal check.

Rules for any skill that ships large inline <script> apps to WordPress:

1. If a script-driven page is blank for visitors but fine for admins, check for a consent or security plugin rewrite FIRST: fetch the page anonymously (no cookies, full Chrome UA) and grep your own script tag for type="text/plain" or data-*consent* attributes.
2. Ship app payloads as an inert base64 <template> element plus a tiny keyword-clean loader (createElement('script') + TextDecoder('utf-8') — NOT bare atob, which mojibakes UTF-8). Consent scanners only rewrite script/iframe tags, and base64 is also immune to wptexturize.
3. Never allow tracker-ish tokens (ttq, fbq(, gtag(, tiktok, facebook., linkedin., youtube.) inside loader code that must not be consent-gated.
4. Anonymous verification is the only verification: logged-in browsers and editor previews lie.
5. Bonus privacy pattern: per-member token links via AES-GCM envelope encryption — the page carries only ciphertext and the token lives in the URL FRAGMENT (#t=…), so it never reaches server logs. Learned July 20, 2026.

<!-- learning:2026-07-21-fleet-500-triage-and-partial-publish --> **July 21, 2026** (from: skill-pack-propagation daily run — BlitzAdmin fleet outage)

When a publish target returns HTTP 500, three cheap probes localize the fault before anyone guesses at credentials — and they turn "the site is down" into an actionable bug report.

1. AUTH IS NOT THE SUSPECT UNTIL PROVEN. Run GET /wp-json/wp/v2/users/me with app-password Basic auth and a full Chrome UA against a KNOWN-GOOD site first. On July 21, 2026 dennisyu.com and blitzmetrics.com both returned 200 with the administrator identity while every BlitzAdmin fleet site returned 500 — so the app passwords were fine and the diagnosis moved to the host in one step instead of repeating the July 6, 2026 "blitzmetrics app password is broken" misdiagnosis.
2. PROBE THE LAYER, NOT THE PAGE. Compare endpoints that load different amounts of WordPress: /wp-login.php and /wp-admin/admin-ajax.php returned 200 (core, DB and every plugin load fine) while /, /feed/, /wp-json/ and /?rest_route=/ all returned 500. Those four are exactly the paths that run the main query — so the fatal lives in a hook at parse_request / wp() / template_redirect, NOT in the theme's functions.php and NOT in the database. That single sentence is what a host or developer needs; "the site is 500ing" is not.
3. CHECK WHETHER STATIC ASSETS STILL SERVE. /wp-content/uploads/*.zip returned 200 on all three dead sites, so every QR-linked pack download kept working while the landing pages were dark. Say that explicitly in the report — it is the difference between "attendees can't download" and "attendees can download but can't read the page".

And the publishing rule that follows: publish to the healthy hosts, record the unreachable ones, and NEVER bump a "Kept current" date on a surface you could not actually refresh. A pack whose date says today but whose zip is yesterday's is worse than an honestly stale date. Learned July 21, 2026.

<!-- learning:2026-07-28-a-passing-marker-check-can-ship-a-broken-page --> **July 28, 2026** (from: a group website-request intake, first publish of jagodapasko.com, July 28, 2026)

On **July 28, 2026** the fleet publisher pushed a member's finished site to a new WordPress install and reported a clean pass: 12 of 12 content and brand markers found, Person schema present, WordPress starter content trashed. A screenshot taken thirty seconds later showed a page nobody would call finished — the block theme printed its own `<h1>Home</h1>` above the hero, and `main.is-layout-constrained.has-global-padding` had squeezed a full-bleed design into a 645px column inside a 1717px viewport. Not one marker moved, because markers are strings and none of them touch layout.

**A string check proves content arrived; it cannot prove content is readable.** So the first publish to any new install gets a human-eye pass — screenshot the front page and each subpage at desktop width before calling the job done. Automated verification stays, it just stops being the last word.

Three concrete rules that came out of it:

1. Suppressing a block theme's header and footer with `:has()` is not enough. Also hide `.wp-block-post-title` and force the layout wrappers open, scoped to your own pages: `body:has(.SCOPE) .wp-site-blocks, body:has(.SCOPE) main, body:has(.SCOPE) main > .wp-block-group, body:has(.SCOPE) .entry-content { max-width:none!important; width:auto!important; margin-left:0!important; margin-right:0!important; padding-left:0!important; padding-right:0!important; }` plus `max-width:none!important` on their direct children.
2. Fix at the generator, never in the published HTML. The correction belongs in the build script so a re-run cannot regress it, then rebuild and republish.
3. Diff the client's supplied assets against what actually renders. Eight of her photos were uploaded and only six were placed; the other two surfaced by diffing the media list against the image references across all pages, and both were added. Make that diff part of the build rather than something a person notices later.

<!-- learning:2026-07-28-an-app-password-belongs-to-whoever-minted-it --> **July 28, 2026** (from: jagodapasko.com credential handoff, July 28, 2026)

On **July 28, 2026** ops handed over a WordPress Application Password in the same message as a username, and the two did not go together — the key had been minted under `admin`, not under the member address quoted beside it. Authenticating as the named user returned `rest_not_logged_in` and looked exactly like a bad credential. It was a good credential pointed at the wrong name.

**Probe before you diagnose.** Run `?rest_route=/wp/v2/users/me&context=edit` across every plausible username — the site admin, the member's address, the account the site was provisioned under — before reporting a key as broken. The response names the real owner and its capabilities in one call.

Two related rules for fleet WordPress work:

1. `permalink_structure` cannot be set through the API. It is not in `wp/v2/settings`, and authenticated XML-RPC is blocked at the fleet edge (400 on any credentialed call, while unauthenticated `system.listMethods` returns 200). Pretty permalinks are a wp-admin-only step, so ask for them at provisioning time instead of discovering it after launch — a site left on plain permalinks serves every page as `?page_id=N` and drops a typed `/about/` on the homepage.
2. Rapid sequential requests trip the fleet WAF into serving a 4,735-byte stub with HTTP 200 on every URL, which reads as a total outage. Space requests a few seconds apart, send a full Chrome User-Agent, and re-fetch once before believing a bad result. *(Superseded: see the July 29, 2026 entry "a 4,735-byte response is a write failure, not a WAF" — the stub was a local write failure, not a WAF. Corrected there, and the superseded claim is named so nobody re-derives it.)*

<!-- learning:2026-07-28-the-credential-may-already-be-in-your-inbox --> **July 28, 2026** (from: jagodapasko.com, July 28, 2026)

On **July 28, 2026** a run reported a member's site as blocked on a missing WordPress Application Password for the fifth straight day. The member had emailed that exact password **sixteen hours earlier**, replying on the same thread the DNS instructions went out on. The run had checked the ops Basecamp thread and the credentials file, and stopped there. A finished website sat unpublished for a day because nobody read the member's own reply.

**When a task is blocked on something a person was asked to send, search every channel that person can reply on before declaring the block.** Concretely, before reporting any credential as missing: search the mail thread the request went out on, search the member's address for the last 72 hours, check the ops channel, and check the credentials file. Say which channels were searched in the status report, so the next run can see the gap rather than inherit it.

Two things that followed from checking:

- The member's own key authenticated as **her** administrator account, while the ops-issued key authenticated as the shared fleet `admin`. Prefer the member's own credential for writes to the member's own site — it keeps authorship on her rather than on the service account, which is the same problem the admin-authorship fleet fix exists to clean up.
- Two valid keys arrived from two directions within a day because nobody recorded that the first had landed. Record the credential and its channel the moment it arrives, even when the publish happens later.

<!-- learning:2026-07-29-a-catalogue-is-not-a-graph --> **July 29, 2026** (from: SEO-tree link audit across the 13 agent/skill surfaces, July 29, 2026)

### Being listed in the catalogue is not the same as being connected to the tree

Every one of our 13 published agent/skill pages was live, current, and listed on the master directory. An actual link audit — pull each page's rendered DOM, decode any base64 payload, extract links to the other twelve — found the graph full of holes:

- `aibuilderspotlight.com/skill-pack` and `dunkerspotlight.com/set-up-claude` linked **nothing at all**. Both dead ends.
- `a partner's member library` linked exactly one page — a partner's members' area with no route back into the system it belongs to.
- `blitzmetrics.com/task-library-dashboard`, the 239-skill page, linked neither the packs that contain those skills nor the agents that run them.
- `localservicespotlight.com/business-authority-pack` linked only its sibling pack — no path up.

None of this was visible in any report, because everything that existed was checked and everything that was checked was fine. Publishing a page and connecting a page are two different jobs, and only the first one had an owner.

**Rules:**

1. **Define the link tree in ONE file and render it from there.** Ours is `System-Hub/system_tree.py`: every node's rung, its sibling, and the block that draws the ladder. A tree that lives in twelve page bodies is twelve chances to drift.
2. **Put the whole ladder on every node with "you are here" marked.** A reader or a crawler landing on any leaf should be able to see the entire structure and their position in it without a back button. One shared block does this; twelve bespoke "related links" do not.
3. **Link one sibling each, arranged as a closed ring.** Every pack surface reachable from every other, and no two pages pointing at each other — reciprocal pairs read as link exchange, and a full mesh makes every page look identical.
4. **Verify links in the LIVE DOM, decoding payloads first.** Several of these pages render their whole UI from a base64 `data:text/html` iframe. A link check that reads only `post_content` sees an empty page and passes it.
5. **A gated page is verified by authenticated read-back, never a public GET.** A public fetch of a member-password page returns the password form; asserting against that certifies a broken publish as green.
6. **If nothing asserts a relationship, the relationship will rot.** Write the check the same day you build the structure — `verify_link_graph.py`, wired into the daily checklist, non-zero exit on any orphan, dead end, missing rung or redirect chain.

Learned July 29, 2026.

<!-- learning:2026-07-29-a-plugin-namespace-can-be-blocked-while-wp-v2-is-fine --> **July 29, 2026** (from: publishing blitzmetrics.com/persistent-agents/, July 29, 2026)

### A plugin's REST namespace can be blocked while wp/v2 works perfectly

Setting the SEO title and meta description on a new blitzmetrics.com article returned **403** on every POST to `/wp-json/rankmath/v1/updateMeta` and `/updateRedirection` — while POSTs to `/wp-json/wp/v2/posts/<id>` on the same host, same Application Password, same full browser header set, returned 200 all day. Probed both ways, JSON body and form-encoded, GET vs POST: `GET /wp-json/rankmath/v1/` is 200, every POST under it is 403, and the body is the host's own styled 403 page rather than a WordPress JSON error. That is a WAF rule scoped to a namespace, not a broken credential and not a capability problem.

The second trap was worse. RankMath does not register `rank_math_title` / `rank_math_description` with `show_in_rest`, so writing them through wp/v2's `meta` field returns **HTTP 200 and stores nothing**. Reading the post back with `context=edit` shows `meta: {}`. A publish job that trusts the 200 reports the SEO as set forever.

**Rules:**

1. **Diagnose a 403 by namespace and method before blaming the credential.** `GET /wp-json/<ns>/` plus a no-op POST tells you in two calls whether it is auth, capability, or an edge rule. Twelve days were once lost calling a WAF rule a broken app password.
2. **After any meta write, read it back.** If the field comes back empty, the write was accepted and discarded. A 200 is a receipt for a request, not evidence of a change.
3. **Know the fallbacks before you need them.** RankMath derives the meta description from the post excerpt and the SEO title from the post title when its own fields are empty — both writable through plain wp/v2. Setting `excerpt` produced the exact intended `<meta name="description">` in the rendered head. Verify in the head, not the API response.
4. **On WP Engine, purge before you verify.** `POST /wp-json/wpe/cache-plugin/v1/clear_all_caches`. A page trashed through the API kept returning 200 to an anonymous fetch until the cache was cleared, which reads exactly like a failed delete and invites a second, wrong repair.

Learned July 29, 2026.

<!-- learning:2026-07-29-edit-the-generator-not-the-page --> **July 29, 2026** (from: applying the SEO-tree block across 13 surfaces on 6 domains, July 29, 2026)

### Before editing any live page, ask what regenerates it

Twelve pages needed the same block. Two of them — `localservicespotlight.com/skill-packs/` and `/asset-tracker/` — are rebuilt from scratch by their own Python generators on a schedule. Editing those live would have looked like a clean success: HTTP 200, block in the rendered DOM, verification green. The next scheduled rebuild would have erased it, silently, and the job that erased it would still have reported success.

So the work split three ways and each page went through exactly one owner: generated pages got the block added to their generator, plain pages through REST, base64 payload pages by decoding, inserting, re-encoding. One owner per file, always.

**Rules:**

1. **Establish the owner before the edit.** Search the project for the page's slug. If a script writes it, that script is the only thing allowed to write it.
2. **Two writers on one artifact is a bug even when both succeed.** The loser is whoever ran first, and nobody finds out until a reader notices something missing weeks later.
3. **When a live page and a local template have drifted, do NOT "restore" from the template.** Our trunk page had picked up three hand-added blocks since its last build; republishing the template would have deleted all three. Diff first, then make surgical marker-guarded edits.
4. **Every surgical edit replaces exactly once and raises on zero matches.** A `sub_once()` that throws when its anchor is gone turns silent drift into a loud failure the same morning.
5. **Mark generated blocks with a data attribute, not a comment.** `data-system-tree="<node>"` survives every filter WordPress runs over content, and gives the checker something exact to assert and the updater something exact to replace.

Learned July 29, 2026.

<!-- learning:2026-07-29-audit-the-name-in-every-language-they-live-in --> **July 29, 2026** (from: jagodapasko.com second pass, July 29, 2026)

On **July 29, 2026** a client's audit from six weeks earlier recorded **2 proof items, 24 authority points, 0 power proof**, and described her third-party footprint as very thin. A single afternoon of searching found national television coverage on two networks, a broadcast documentary segment, three long-form interviews on three independent channels, and a verified fundraiser documenting 210+ evacuations. None of it was hidden. All of it was in **Polish**, and most of it lived on other people's channels rather than her own.

**A proof library built from English-language search of a non-English person is a measurement artefact, not a finding.** So before scoring anyone's authority:

1. Search the name in **every language the person has lived and worked in**, including with and without diacritics, and search their brand or company name separately.
2. Search for the *events* as well as the person — the coverage may name the work rather than the individual, and their own outbound links (a fundraiser page, a media page, a LinkedIn post) often point straight at press that no name-search returns.
3. Treat "third-party footprint is thin" as a **hypothesis that must survive a native-language search**, never as a conclusion from an English result set. Say which languages were searched, so the next run can see the gap instead of inheriting it.
4. Verify every video with oEmbed before publishing it — it returns the exact title, the real channel, and whether the thing is still public. Titles get paraphrased from memory otherwise, and paraphrasing someone else's video title onto a client's press page is how a credibility asset turns into an error.

**Reject search summaries that conflict with primary sources.** One auto-generated summary in this run asserted the client had been "a TV director turned brain-injury recovery mentor." It was a different person with a similar name, and it contradicted a verified twenty-year finance career. A name collision inside a research tool will happily produce fluent, specific, false biography — check every claim against a source that names the person unambiguously before it reaches a published page.

<!-- learning:2026-07-29-a-4735-byte-response-is-a-write-failure-not-a-waf --> **July 29, 2026** (from: a group website-request intake daily run, July 29, 2026)

Check that your tool could WRITE its output before you diagnose the server. On July 28, 2026 a run recorded a gotcha that read: "hammering a fleet site with rapid sequential curl calls trips the WAF into serving a 4,735-byte stub with http 200 for every URL — it looks exactly like the site breaking." On July 29 the same signature appeared again: nine URLs on jagodapasko.com, every one `200 4735`, identical byte count on pages that differ by 8,000 bytes. There is no WAF stub. `curl -o /tmp/pg.html` was writing to a file left behind by an earlier session's sandbox, owned by `nobody:nogroup` and not writable by the current user. curl aborts the transfer when the write fails and still reports `http_code 200` with a truncated `size_download`. Reproduced deliberately: the same URL fetched to the stale path returned 4,735 bytes; fetched to a fresh `mktemp -d` path it returned 103,652. The 4,735 is a property of the local filesystem, not of the remote host.

The rule: write every fetch into a directory you just created (`W=$(mktemp -d)`), never into a fixed `/tmp/<name>` that a previous run or a previous session may own. When a response looks wrong, run `ls -l` on the output path and compare `size_download` against `wc -c` of the file before forming any theory about the server. Identical byte counts across URLs that should differ is the tell — real pages are never the same size by accident.

The wider lesson is about what a gotcha costs when it is wrong. That note had already been carried into the ledger as fleet behaviour, and it prescribed the exact wrong remedy — space the requests out and wait — which would have made every future run slower while leaving the real cause in place. A diagnosis that blames a remote system you cannot inspect should be held to a higher bar than one that blames your own process: reproduce it deliberately, with a control, before writing it down as a standing fact. Corrected here, and the superseded claim is named so nobody re-derives it.

<!-- learning:2026-07-29-a-blocker-with-a-deadline-becomes-a-todo-on-that-date --> **July 29, 2026** (from: a group website-request intake daily run, July 29, 2026)

A status line repeated daily is not an escalation. Christine Boers-Doets's site was finished on July 8, 2026 and sat serving the WordPress sample page for twelve days waiting on one WordPress Application Password — four clicks by one person. Across five consecutive daily runs it appeared as a bullet in a status comment on a thread that person reads, and across five consecutive days nothing happened. The member emailed twice asking why her URL did not work; her programme lead escalated on her behalf. Every report was accurate and every report was ignorable, because a bullet in a status update has no owner, no due date and no place it shows up again tomorrow.

The rule: when a run identifies work it cannot do itself, it names the person, writes the exact steps, and sets the date on which a status line becomes a task. On that date it files the task — for us, a Basecamp to-do assigned to the named owner, carrying the full spec (which site, which screen, what to name the key, what to paste back, what happens once it lands). July 28's run wrote the deadline into the ledger — "if it is not posted by the 7/29 run, escalate it to a to-do" — and July 29's run fired it. That handoff is the whole mechanism: the run that spots the block sets the trigger, the next run pulls it. Without the written trigger the item just ages inside green reports.

Two details that make the to-do land instead of adding noise. Write the ask as the smallest true unit of work — "four clicks, here they are" beats "unblock Christine" — because an owner estimates before they act. And carry forward what the last identical task taught: on the previous site the key was minted under a different WordPress user than the username quoted beside it, so the to-do asks for the username too.

<!-- learning:2026-07-29-read-the-plugin-source-before-writing-to-its-table --> **July 29, 2026** (from: collapsing 24 redirect chains across localservicespotlight.com + dennisyu.com, July 29, 2026)

### When a plugin's REST API is undocumented, download the plugin and read it

Two redirect tables needed surgical edits and neither API was documented in a way that answered the only question that mattered: *what happens to the fields I do not send?* Guessing against a live table with 34 and 192 rules on it was not acceptable, and probing by trial risked detaching real redirects carrying thousands of hits.

So both plugins were downloaded from the wordpress.org repo at the exact installed version and read. Ten minutes, and it turned two unknowns into contracts:

- **RankMath Redirections** has no route that LISTS redirections. The read path is `status/exportSettings` (redirections ride along in the export). The write path is `updateRedirection`, which is really the post-metabox save handler: it rebuilds the rule from `(redirection_id, url_to, sources, header_code)`. **Omit `redirectionSources` and the source is rebuilt EMPTY**, silently detaching the rule from the URL it exists to catch. It also rejects an empty `objectID`, which a standalone rule does not have — pass an id matching no post, because a real one makes that post's metabox claim it owns a redirect.
- **Redirection plugin** (`redirection/v1/redirect`) sanitises the whole payload and then does a full row `UPDATE`. A partial patch drops every field you left out. The payload has to be the GET item echoed back with only the target changed — and `hits` / `last_access` must be OMITTED, because the sanitiser maps them onto `last_count` / `last_access` and rewrites the counters.
- Its import path is safe but useless for repairs: `set_redirections()` skips any row whose source already matches an existing rule, so re-importing corrected copies changes nothing.

**Rules:**

1. **Read the source before the first write, not after the first surprise.** `curl` the versioned zip from wordpress.org, unzip, read the sanitiser and the update method. Cheaper than one bad write to a production table.
2. **Find out whether update means PATCH or REPLACE.** If the model sanitises into a fresh array and calls `$wpdb->update` with it, every field you omit is erased.
3. **Audit every redirect engine a site has, not the first one you find.** dennisyu.com runs RankMath Redirections AND the Redirection plugin at once. `X-Redirect-By` proved the plugin wins; fixing the RankMath copies changed nothing a visitor could see — 2 of 13 "fixes" held and the rest still measured 3-4 hops. **`X-Redirect-By` on the response is the ground truth for who is actually in charge.**
4. **Never auto-rewrite a regex rule.** Its source is a pattern, not a URL, so hops cannot be measured, and its target may contain capture groups. Report it and stop.
5. **A rule pointing at itself is a live infinite loop, not a chain.** Detect "never lands after N hops" as its own class and never auto-repair it — the correct destination is an editorial decision. One such rule had taken 12,190 hits.
6. **Check the trailing slash on high-volume rules.** A target of `/$1` where WordPress canonical wants `/$1/` costs an extra 301 on every request. On the busiest rule on the site that was 829,576 requests each paying for a hop nobody needed.

Learned July 29, 2026.

<!-- learning:2026-07-30-a-credential-that-arrives-is-not-a-credential-that-works --> **July 30, 2026** (from: a group website-request intake, July 30, 2026 — Christine Boers-Doets application password)

A credential that ARRIVES is not a credential that WORKS. Christine Boers-Doets' WordPress Application Password was the single blocker on a finished site for 13 days. The morning it finally came in — pasted by Muzamil in an email alongside Jagoda's — the reflex was to mark the blocker cleared, store the key, and publish. That would have been wrong for the second time on this same project. The key does not authenticate. Tested against the live `.nl` install under 15 usernames (the two real users the REST API lists, plus admin, operations, blitzadmin and nine more): every one returns `rest_not_logged_in`, the same 401 a request with no credentials gets.

The rule: probe a freshly-received credential against the LIVE target before you advance a status, store it, or report the block cleared. And probe it with a check you have PROVEN can both pass and fail in the same breath — a check that cannot fail is not a check. Here the proof was a positive and a negative control run right next to the real test: Jagoda's key returned 200 on `/wp/v2/users/me?context=edit` and on `/wp/v2/settings`, and a deliberately bogus key returned 401. Only against those two poles does Christine's key returning 401 mean something. Without them, 401 could just as easily have been the whole site rejecting Basic auth, and "her key is bad" would have been an unfounded guess.

The same-batch control is what turned a vague "the credential doesn't work" into a precise, actionable finding. Jagoda's key came from the identical email and authenticated cleanly — so it is not the email, not the paste channel, not the fleet, not the WAF. The fault is isolated to this one key or the install it was minted on. That specificity is the difference between an email that says "please look at Christine's password" (which generates a reply asking what's wrong) and one that says "re-mint it on the `.nl` install, SiteId 2360, the christineboers profile" (which gets done).

The most likely cause carries its own reusable lesson: on a domain that was re-mapped between TLDs, the old and new installs are SEPARATE WordPress sites. Christine's site moved from `.com` (SiteId 2348) to `.nl` (SiteId 2360); the `.com` now resolves to a GoDaddy/Fastly parking page and its old WordPress on our IP no longer serves. An Application Password minted on the old install fails on the new one with the exact same `rest_not_logged_in` as a wrong password — indistinguishable by status code alone. When a key fails, name which install it was probably minted on rather than reporting "bad credential"; the fix (re-mint on the correct install) is invisible until you do.

One trap worth flagging: `/wp/v2/users` only lists users who have published posts, so the real service account can be invisible to it. Jagoda's working key belonged to WP user #1 `admin`, which the public user list never showed. So when a key fails on the two listed users, try likely service usernames (admin / operations / blitzadmin) before concluding anything — the account it was minted under may not be one the API will name for you. Here all 15 still failed, which is itself the finding, not a reason to stop early.

<!-- learning:2026-08-01-a-quiet-queue-may-be-a-disconnected-one --> **August 1, 2026** (from: a group website-request intake)

**A daily job can be perfectly correct and still be watching nothing. When a source returns the same answer for weeks, verify that anything upstream is connected to it.**

The group website intake read its Google Form sheet accurately every morning for sixteen consecutive days and truthfully reported "no new requests, 1 row." The read was never wrong. The form had never been shared with members. Seven people were waiting in queues the job could not see, because every real request arrived by email, by Basecamp, or directly to Dennis. The finding did not come from the data — it came from a client asking, on the project thread, "please share a list of who is waiting."

Adopt as standing practice:

1. **An unchanging source is a hypothesis, not a fact.** Two weeks of identical output means either nothing is happening or nothing is arriving. Those have different owners and different fixes. After N consecutive no-change runs, spend one call confirming the upstream path is live — that the form is published, the webhook fires, the inbox is monitored, the sheet is the one people actually submit to.
2. **Count the queue, not the source.** A pipeline's real backlog is the union of everything feeding it. Keep an explicit lane for out-of-band arrivals (here, `tracked_non_form`) and treat it as first-class, because in a system where the front door is closed it *is* the whole queue.
3. **Reconcile against sister pipelines before reporting scope.** Two agents were tracking overlapping subsets of the same work — this job knew two members, another knew eight. Neither was wrong; both were partial. One read of the other agent's outbound email closed the gap. When you know another automation touches the same domain, diff against it.
4. **"No changes" is only a safe report if you checked what would have made it change.** Green on an unconnected input reads exactly like green on a healthy one, and it buys silence for as long as nobody outside asks.

<!-- learning:2026-08-01-does-not-resolve-is-not-is-not-registered --> **August 1, 2026** (from: a group website-request intake)

**"Does not resolve" and "is not registered" look identical to `dig +short` and have completely different owners. Ask the TLD's own authoritative server, with controls.**

Four member domains were on a live ops ticket that said "point the A-record at the fleet." Two of them — `anneliesalminen.com` and `piamuggerud.com` — are not registered at all. There is no zone to add a record to. `dig +short A` returned empty for them, which reads as "DNS not configured yet" and had been reported that way for four weeks. Ops would have gone looking in GoDaddy for zones that do not exist.

Adopt as standing practice:

1. **Query the registry, not a resolver.** `dig @a.gtld-servers.net <domain> NS` and read the rcode: `NXDOMAIN` means no registry delegation (unregistered, or registered with no nameservers — either way the fix is at the registrar). `NOERROR` with an NS referral means registered and delegated, and only then is "add an A record" a real instruction.
2. **Run both controls in the same call or the result is unfalsifiable.** A made-up domain as the negative control (must return NXDOMAIN) and a known-good domain from the same batch as the positive control (must return an NS referral). Without them, an NXDOMAIN could be a network artifact. With them it is a finding you can put in front of a client.
3. **Before repointing any domain at the fleet, fetch its root and read the title.** The email-safety rule catches MX; it does not catch a working homepage. `lisasennhauserkelly.com` matched every "built but never provisioned" description in the queue while serving the member's real live business site at HTTP 200. Repointing it would have destroyed live work. Check for a live site *and* live email, separately.
4. **Correct a wrong public status the same day you find it.** Two of eight entries on a client-visible list were mis-diagnosed as waiting on our DNS. Left alone, the members would have waited on an action nobody could take. Naming the real blocker moved two items from an ops backlog to a one-message ask.

<!-- learning:2026-08-02-a-fix-in-one-copy-of-a-script-is-not-a-fix --> **August 2, 2026** (from: the group website intake — Christine's publish package still carried the render bug fixed in Jagoda's builder five days earlier)

### "Port this fix to the other packages" is a note, and notes do not execute

On 2026-07-28 a first publish to a fleet WordPress install rendered visibly broken in two ways a marker-based verifier passed clean: the block theme printed its own `<h1>` above our hero, and `main.is-layout-constrained.has-global-padding` squeezed a full-bleed design into a 645px column inside a 1717px viewport. Both were fixed in that member's `build_pages.py`, and the run log recorded the right instruction: *port it to any other member package before its first publish.*

Five days later the next member's package still had the pre-fix CSS — three lines that hid the header and footer and nothing else. And hers was the package everyone described as "publishes with one command the moment an Application Password lands." The one command would have produced the same broken page, on a client site, for the second time on the same project.

Nothing was neglected. The instruction was written down, in the right place, by the run that found the bug. It just lived in prose, next to a directory of per-member copies of the same script, and prose has no way to reach a copy.

**Rules:**

1. **A per-entity copy of a build script is a fix-propagation bug waiting to happen.** The moment there are two, a fix lands in one. Generate all of them from one function; adding an entity becomes a row in a table, not a new file to keep in sync.
2. **When a run's own log says "port this," that is the run admitting it did not finish.** Either port it in the same run or make the port unnecessary by moving the logic somewhere shared. Leaving it as an instruction transfers a known defect to whoever reads the log next — and nobody read it.
3. **The most dangerous artifact is the one described as "one command away."** It gets no further review precisely because it is considered ready. Re-derive a ready-to-ship artifact from source before shipping it, especially if it was built before a fix you know about.
4. **Regenerating found a second defect in the same pass:** the config carried hand-typed taglines, and one already disagreed with the member's own page ("architect-led renovation guidance" vs the page's "Certified Passive Building Designer"). A fact the artifact already states should be read off the artifact, not maintained beside it.

Learned August 2, 2026.

<!-- learning:2026-08-02-a-resent-credential-means-the-ask-was-ambiguous --> **August 2, 2026** (from: the group website intake — day 16 of a blocked publish; the third escalation was answered by re-sending the same failing key)

### When someone answers a request for a new credential by re-sending the old one, the request was ambiguous — not ignored

A member's finished site sat unpublished for sixteen days on one missing Application Password. Three escalations went out over four days: a comment on an assigned to-do, a line on the client thread, and an email. Each asked, in good faith, for "an Application Password for `<domain>`."

The reply arrived with a key and a link to where it had first been posted. It was the same key that had been failing since day 12 — minted on the member's *old* `.com` install, which is a separate WordPress from the live `.nl` site she was moved to. It returns 401 under every username, and the sender's own status export said `hasAppPass:false` for the new site.

Nobody dropped anything. The ask named a **domain** and a **credential type**, and the person doing the work reasonably read that as "send the password for that domain" — and one existed. The word that was missing was the verb, and the target.

**Rules:**

1. **Ask for the verb and the install, not the credential and the domain.** "Mint a NEW Application Password ON `<domain>` (SiteId NNNN), user `<login>`, name `cowork-<person>`" cannot be satisfied by forwarding an existing key. "Send me the app password for `<domain>`" can.
2. **Re-asking the same way gets the same answer.** After the second identical reply, change the wording rather than the channel. Three escalations through three channels all carried the same ambiguous sentence, so all three produced the same outcome.
3. **State the disqualifying evidence in the ask.** "The key on file returns 401 under all four usernames, tested today against a probe that returned 200 for a known-good key in the same run" tells the reader the existing key is not the answer, before they reach for it.
4. **When a domain is re-mapped between TLDs, the two are separate WordPress installs**, and a key minted on the old one fails on the new one with the same `rest_not_logged_in` as a wrong password. Name which install a key was likely minted on rather than reporting "bad credential."

Learned August 2, 2026.

<!-- learning:2026-08-02-successfully-set-up-is-not-reachable --> **August 2, 2026** (from: the group website intake — the fleet provisioned WordPress sites for two domains that do not exist, and mailed a success notice for each)

### A provisioner reporting success tells you the installer ran, not that anyone can reach the result

Four member domains went through our New Site form in one evening. Four "Your new WordPress site has been successfully set up at https://…" emails came back. Two of those domains return **NXDOMAIN at the .com registry** — no delegation, no nameservers, no zone. They are not registered.

The installs are real. A `Host:` header probe to the fleet IP returns proper WordPress pages with the members' names in the title. Everything downstream — the setup email, the fleet record, the status list posted to the client — says done. Nobody on the internet can type an address that reaches either one, and nothing in the pipeline is capable of noticing.

The same day, a related failure in the opposite direction: a member's site was recorded as `503 at check time` and left there. Re-checked once, it 301s to `www` and serves her real 837 KB business site. A single non-200 had been treated as a verdict.

**Rules:**

1. **Resolve the hostname before reporting a provisioning success.** One DNS lookup at the end of the installer separates "installed" from "reachable." Without it, "successfully set up" is a claim about our filesystem dressed as a claim about the member's site.
2. **`dig +short` cannot distinguish "not registered" from "registered, no records" — both print nothing.** Ask the TLD's own authoritative server (`dig @a.gtld-servers.net <domain> NS`) and read the rcode: NXDOMAIN means no registry delegation; NOERROR with a referral means registered. Run an invented domain and a known-good domain in the same call, or the result is unfalsifiable.
3. **Check our OWN records before escalating to the person.** Our build logs said all four domains were "registered 2026-07-01, GoDaddy, 1yr — gift." Two do not exist, which turns *"ask her where she registered it"* into *"check whether our own purchase completed"* — a question we can answer ourselves, and a far better thing to say to someone who was told her site was coming.
4. **A 503 is a moment, not a verdict.** Retry it, and follow the redirect — the root may 301 to `www` and only the `www` response carries the site. A non-200 feels like an answer, which is exactly why it gets recorded as one.
5. **Where a wrong action is unrecoverable, the refusal belongs in the tool.** Two of these domains serve live business sites and two do not exist; from the fleet's side all four look identical to "built, just needs provisioning." The publisher now refuses those four by name with the reason printed and an explicit override flag — and the refusal was tested for both outcomes, because a guard that has never been seen to fire is not known to work.

Learned August 2, 2026.

---

## Provenance

Migrated 2026-11-05 from the live skill page (localservicespotlight.com/skills-personal-brand-website-agent/, skill file last updated Aug 17, 2026) and the Goodrich stub snapshot d2804a33 (Goodrich-Dev/brand-agent-team), Wave 1.5 migration — this file is the fleet-owned source for the recipe.

Doctrine conflict, resolved for the live page: the stub's Step 2 put the lead-magnet opt-in above the fold ("the email capture is the first conversion") and its definition of done required an unmistakable lead-magnet→email→offer path. The live page's copy rules govern instead — "Facts page, not a sales page. Every claim links to its source; funnels live elsewhere" — so the opt-in rule and the funnel-path done-criterion were NOT carried into this file. Carried from the stub: the read-first brand-voice / ideal-client preamble (in Inputs) and the brand-name field note (in Notes — Dennis's method). The Person schema JSON-LD block in Steps follows the pack's canonical form in `knowledge-panel-entity-seo`. One dated lesson (July 28, 2026, app-password entry, rule 2) preserves a WAF claim that the July 29, 2026 entry in this same file corrects; both are kept, with the correction flagged inline, exactly as the live page carries them.
