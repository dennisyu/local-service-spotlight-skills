---
name: client-access-checklist
description: The standard set of accounts and permissions we capture before any content ships — Search Console, CMS admin, GA4, Tag Manager, DNS, Google Business Profile, video, social, ads. Use at kickoff on any new client or site, whenever a build is about to publish, and whenever you are asked "do we have access to X". Turns access from something we remember into something we audit.
author: Dennis Yu — Local Service Spotlight
references:
  - https://blitzmetrics.com/verify-client-sites-google-search-console/
  - https://blitzmetrics.com/digital-plumbing/
  - Access-Checklist/ACCESS-CHECKLIST.md
  - Access-Checklist/RCA-2026-07-27-anthonyhilb-gsc.md
  - TaskLibrary/skills/digital-plumbing/
---

# Client Access Checklist

**Use this when** starting any engagement, standing up any site, or about to publish content
anywhere. Also use it the moment you catch yourself about to write a "needs the client's login"
list — generate that list from here rather than from memory.

**The rule this skill enforces:** a build is not done when the content is live. It is done when
the content is live **and we can see what it does.**

## Why (read this once, it changes how you work)

We published sixteen articles to a client site on June 14, 2026. Six of them were never indexed
by Google. We did not find out for six weeks, because that site had no Search Console property —
and it had no Search Console property because our coverage audits took their list of sites from
the hosting fleet, and this was a site we publish to but do not host. It was structurally
incapable of showing up as a gap.

The same audit found that site had no analytics of any kind. A fleet-wide sweep found **127 more
properties in the same condition, 50 of them on our own hosting.**

Nobody skipped a step. The step wasn't on the list. This skill is the list.

## The nine rows

Rows 1–4 are the gate. Content does not ship until they are green.

| # | Access | What "green" means |
|---|--------|--------------------|
| 1 | **Google Search Console** | Property verified · our operating account added · sitemap submitted, Success |
| 2 | **CMS / website admin** | Admin login **and** an application password in `.credentials.json` so agents publish without a human |
| 3 | **Google Analytics 4** | Property live, tag firing, internal traffic filtered, linked to GSC |
| 4 | **Google Tag Manager** | Container published with a real ID — an empty container is a false green |
| 5 | **Registrar + DNS** | Login or a named responsive contact; record where DNS is hosted |
| 6 | **Google Business Profile** | Claimed; we hold manager access (this is NOT the same as a personal Knowledge Panel) |
| 7 | **YouTube / video** | Channel access or a reliable export path — this is the raw material for repurposing |
| 8 | **Social profiles** | Handles confirmed and recorded for `sameAs`; access where amplification is in scope |
| 9 | **Ad accounts** | Business Manager access with the right role, if ads are in scope |

## Steps

1. **Check the register first.** `Access-Checklist/ACCESS-REGISTER.json` may already have the
   property. Then check `.credentials.json` for an application password before asking anyone for a
   login — we frequently already have access nobody remembered.
2. **Run the audit for this domain:** `python3 Access-Checklist/access_audit.py --domain <domain>`.
   It reports verification evidence, analytics, sitemap, robots reference, and publish access from
   public HTML in seconds. Do this before asking the client for anything, so you ask only for what
   is genuinely missing.
3. **Ask once, ask completely.** One message listing every missing row with the exact emails and
   roles. Ten small asks over six weeks is how access work dies.
4. **Verify Search Console** per `blitzmetrics.com/verify-client-sites-google-search-console/`:
   URL-prefix property → copy the HTML-tag token → paste into the site's head → Verify → submit
   sitemap.
5. **Add users.** The site owner's Google account = Owner. Your operating/service account = Full.
   Your own account = Full. ⚠ **The Add-user click is a HUMAN step** — agents do not modify
   access controls. Prepare everything, then hand off.
   *(This file ships in public download packs. The specific role addresses we use are in the
   internal runbook — `Access-Checklist/ACCESS-CHECKLIST.md` — never in a distributed skill.)*
6. **Install GA4 and GTM** before the first article, not after.
7. **Record everything** in the register and `.credentials.json`, then re-run the audit to confirm
   the rows went green. Access you did not record is access you do not have.
8. **Route what you cannot get.** Blocked is a status, not an ending. Anything an agent cannot do
   goes to your ops owner as a written to-do with a FULL spec — not a hint. Host or server work
   goes to whoever owns the server, in writing. Name the owner and name a date: a blocker with an
   owner and a date is progress; a blocker in your head is not.
   *(Internal routing targets live in the internal runbook, not in this shipped file.)*

## Definition of done

- [ ] Every one of the nine rows has a status and an owner — including the ones we chose to skip
- [ ] Rows 1–4 green, or a routed blocker naming exactly what we cannot see until it clears
- [ ] Property present in `ACCESS-REGISTER.json`; credentials in `.credentials.json`
- [ ] `access_audit.py --domain <domain>` re-run and the gaps it reports match what you expect
- [ ] Sitemap submitted, and referenced in robots.txt
- [ ] The client-facing "what we need from you" list was generated from this checklist, not memory

## Traps met in the field

- **Rank Math's `updateSettings` REST endpoint cannot safely write one setting.** It replaces three
  whole option groups and will destroy settings. Use a browser REST nonce or the
  `bm-site-verification` module. Never inject a verification token through it.
- **Block-theme sites with no SEO plugin have no head-injection route over REST.** That is what
  `GSC-Fleet-Coverage/bm-site-verification.php` exists for — built and tested, pending deploy.
- **Some of our own sites 403 Google's `Google-Site-Verification/1.0` fetcher** while serving
  Googlebot normally. Allowlist the user agent before blaming the token.
- **Flush the sitemap cache before submitting.** One site listed 1,059 URLs against 1,447 published
  articles; submitting as-is would have hidden 393 articles.
- **An empty GTM container reads as installed.** Check for a real `GTM-XXXXXX` ID, not just the
  presence of `gtm.js`.
- **A missing verification meta tag does not prove there is no Search Console** — DNS TXT, GA, and
  GTM verification leave no HTML trace. `GSC_UNCONFIRMED` means *check the account*.

## Related

- `weekly-brand-maa.md` — the weekly loop that consumes this access; its indexation check is what
  exposed the gap
- `measurement-analytics.md` — what to do with the data once you can see it
- `personal-brand-website-agent.md` — the build this checklist gates
- `TaskLibrary/skills/digital-plumbing/` — task-level SOPs for each row
- `boil-the-ocean.md` — why the answer is the finished access, not a plan to get it

## Learned in the field

*Appended automatically by the self-improvement loop (Skill-Learnings/): dated lessons from real runs. Newest at the bottom.*

<!-- learning:2026-07-28-a-shipped-skill-must-not-carry-your-own-address -->
**July 28, 2026** (from: skill-pack-propagation daily run, July 28, 2026)

### A skill that ships must not carry your address, your staff, or your routing

`client-access-checklist` was mandated into every pack on July 27, 2026 and went live in all
seven public downloads. Written for internal use, it told the reader to add
`access@localservicespotlight.com` and `668sierra@gmail.com` as Full users on the **client's**
Search Console, and to route blocked work to a named staff member and an internal team alias.

`weekly-brand-maa` was worse in effect: it instructed the agent to "always send one combined
summary email to Dennis (668sierra@gmail.com)." Every workshop attendee who installed that pack
had an agent whose weekly job was to email *us* about *their* clients.

That is not only a privacy leak; it is a functional bug. An instruction that names a specific
person is correct in exactly one installation and wrong in every other one.

**Rules:**

1. **Before a skill is mandated into distributed packs, read it as a stranger who just
   downloaded it.** Every "we", "our account", named person and internal alias is a defect.
   Ask: *if a competitor installed this, what did I just hand them, and who would it email?*
2. **Addresses, owners and destinations are CONFIGURATION, not content.** Say "the owner
   address configured for this agent"; keep the actual values in the internal runbook and the
   credentials file — the two places that never ship.
3. **Grep the built artifact, not the source folder.** These files were fine in the folder they
   were written for; the defect only exists once the mandate copies them somewhere else. Add
   the sweep to the run: fetch each LIVE download and search it for your own addresses. That
   check takes seconds and is the only one that reflects what a stranger actually receives.
4. **Generalising a skill for distribution is part of mandating it, not a follow-up.** The
   mandate that copies a file into ten packs is the moment its audience changes.

Learned July 28, 2026.

<!-- learning:2026-07-28-an-app-password-belongs-to-whoever-minted-it -->
**July 28, 2026** (from: sigrun-website-request-intake, jagodapasko.com credential handoff, July 28, 2026)

On **July 28, 2026** ops handed over a WordPress Application Password in the same message
as a username, and the two did not go together — the key had been minted under `admin`, not
under the member address quoted beside it. Authenticating as the named user returned
`rest_not_logged_in` and looked exactly like a bad credential. It was a good credential
pointed at the wrong name.

**Probe before you diagnose.** Run `?rest_route=/wp/v2/users/me&context=edit` across every
plausible username — the site admin, the member's address, the account the site was
provisioned under — before reporting a key as broken. The response names the real owner and
its capabilities in one call.

Two related rules for fleet WordPress work:

1. `permalink_structure` cannot be set through the API. It is not in `wp/v2/settings`, and
   authenticated XML-RPC is blocked at the fleet edge (400 on any credentialed call, while
   unauthenticated `system.listMethods` returns 200). Pretty permalinks are a wp-admin-only
   step, so ask for them at provisioning time instead of discovering it after launch — a
   site left on plain permalinks serves every page as `?page_id=N` and drops a typed
   `/about/` on the homepage.
2. Rapid sequential requests trip the fleet WAF into serving a 4,735-byte stub with HTTP 200
   on every URL, which reads as a total outage. Space requests a few seconds apart, send a
   full Chrome User-Agent, and re-fetch once before believing a bad result.

<!-- learning:2026-07-28-the-credential-may-already-be-in-your-inbox -->
**July 28, 2026** (from: sigrun-website-request-intake, jagodapasko.com, July 28, 2026)

On **July 28, 2026** a run reported a member's site as blocked on a missing WordPress
Application Password for the fifth straight day. The member had emailed that exact password
**sixteen hours earlier**, replying on the same thread the DNS instructions went out on. The
run had checked the ops Basecamp thread and the credentials file, and stopped there. A
finished website sat unpublished for a day because nobody read the member's own reply.

**When a task is blocked on something a person was asked to send, search every channel that
person can reply on before declaring the block.** Concretely, before reporting any
credential as missing: search the mail thread the request went out on, search the member's
address for the last 72 hours, check the ops channel, and check the credentials file. Say
which channels were searched in the status report, so the next run can see the gap rather
than inherit it.

Two things that followed from checking:

- The member's own key authenticated as **her** administrator account, while the ops-issued
  key authenticated as the shared fleet `admin`. Prefer the member's own credential for
  writes to the member's own site — it keeps authorship on her rather than on the service
  account, which is the same problem the admin-authorship fleet fix exists to clean up.
- Two valid keys arrived from two directions within a day because nobody recorded that the
  first had landed. Record the credential and its channel the moment it arrives, even when
  the publish happens later.

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

<!-- learning:2026-07-29-a-blocker-with-a-deadline-becomes-a-todo-on-that-date -->
**July 29, 2026** (from: sigrun-website-request-intake daily run, July 29, 2026)

A status line repeated daily is not an escalation. Christine Boers-Doets's site was finished on July 8,
2026 and sat serving the WordPress sample page for twelve days waiting on one WordPress Application
Password — four clicks by one person. Across five consecutive daily runs it appeared as a bullet in a
status comment on a thread that person reads, and across five consecutive days nothing happened. The
member emailed twice asking why her URL did not work; her programme lead escalated on her behalf. Every
report was accurate and every report was ignorable, because a bullet in a status update has no owner, no
due date and no place it shows up again tomorrow.

The rule: when a run identifies work it cannot do itself, it names the person, writes the exact steps,
and sets the date on which a status line becomes a task. On that date it files the task — for us, a
Basecamp to-do assigned to the named owner, carrying the full spec (which site, which screen, what to
name the key, what to paste back, what happens once it lands). July 28's run wrote the deadline into the
ledger — "if it is not posted by the 7/29 run, escalate it to a to-do" — and July 29's run fired it. That
handoff is the whole mechanism: the run that spots the block sets the trigger, the next run pulls it.
Without the written trigger the item just ages inside green reports.

Two details that make the to-do land instead of adding noise. Write the ask as the smallest true unit of
work — "four clicks, here they are" beats "unblock Christine" — because an owner estimates before they
act. And carry forward what the last identical task taught: on the previous site the key was minted under
a different WordPress user than the username quoted beside it, so the to-do asks for the username too.

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

<!-- learning:2026-07-30-a-credential-that-arrives-is-not-a-credential-that-works -->
**July 30, 2026** (from: Sigrun website-request intake, July 30, 2026 — Christine Boers-Doets application password)

A credential that ARRIVES is not a credential that WORKS. Christine Boers-Doets' WordPress Application
Password was the single blocker on a finished site for 13 days. The morning it finally came in — pasted
by Muzamil in an email alongside Jagoda's — the reflex was to mark the blocker cleared, store the key,
and publish. That would have been wrong for the second time on this same project. The key does not
authenticate. Tested against the live `.nl` install under 15 usernames (the two real users the REST API
lists, plus admin, operations, blitzadmin and nine more): every one returns `rest_not_logged_in`, the
same 401 a request with no credentials gets.

The rule: probe a freshly-received credential against the LIVE target before you advance a status, store
it, or report the block cleared. And probe it with a check you have PROVEN can both pass and fail in the
same breath — a check that cannot fail is not a check. Here the proof was a positive and a negative
control run right next to the real test: Jagoda's key returned 200 on `/wp/v2/users/me?context=edit` and
on `/wp/v2/settings`, and a deliberately bogus key returned 401. Only against those two poles does
Christine's key returning 401 mean something. Without them, 401 could just as easily have been the whole
site rejecting Basic auth, and "her key is bad" would have been an unfounded guess.

The same-batch control is what turned a vague "the credential doesn't work" into a precise, actionable
finding. Jagoda's key came from the identical email and authenticated cleanly — so it is not the email,
not the paste channel, not the fleet, not the WAF. The fault is isolated to this one key or the install
it was minted on. That specificity is the difference between an email that says "please look at
Christine's password" (which generates a reply asking what's wrong) and one that says "re-mint it on the
`.nl` install, SiteId 2360, the christineboers profile" (which gets done).

The most likely cause carries its own reusable lesson: on a domain that was re-mapped between TLDs, the
old and new installs are SEPARATE WordPress sites. Christine's site moved from `.com` (SiteId 2348) to
`.nl` (SiteId 2360); the `.com` now resolves to a GoDaddy/Fastly parking page and its old WordPress on
our IP no longer serves. An Application Password minted on the old install fails on the new one with the
exact same `rest_not_logged_in` as a wrong password — indistinguishable by status code alone. When a key
fails, name which install it was probably minted on rather than reporting "bad credential"; the fix
(re-mint on the correct install) is invisible until you do.

One trap worth flagging: `/wp/v2/users` only lists users who have published posts, so the real service
account can be invisible to it. Jagoda's working key belonged to WP user #1 `admin`, which the public
user list never showed. So when a key fails on the two listed users, try likely service usernames
(admin / operations / blitzadmin) before concluding anything — the account it was minted under may not
be one the API will name for you. Here all 15 still failed, which is itself the finding, not a reason to
stop early.

<!-- learning:2026-08-01-a-named-blocker-needs-a-recheck-date -->
**August 1, 2026** (from: skill-pack-propagation — closing out the agent-runtime cloud migration, August 1, 2026)

A plan that says "blocked on <person>" quietly becomes a plan that is blocked on nobody reading
their reply. The cloud-migration runbook had said "Phase 1: waiting on Josh or Austin to create
the repo and issue a bot token" since July 17, 2026. Daniel created the project and sent BOTH
access tokens on July 21, replying to that very thread. Nobody opened it. The runbook, the
project memory and every status summary kept reporting a human blocker for eleven more days,
while the thing they were waiting for sat in the inbox — and the whole migration, plus the
audit-trail benefit that depends on it, stalled for a reason that had already gone away.

The general shape: **a blocker recorded as a person is only as fresh as the last time someone
checked the channel that would clear it.** Writing "waiting on X" creates an obligation to
re-read, and nothing in the plan carried that obligation. Every named external dependency needs
one of: a re-check date, an owner for the re-check, or — best — an automated probe that tests
the actual precondition rather than trusting the note. Here the probe is two seconds of work:
`git ls-remote` against the repo would have returned success on July 21 and every day after.

Test the PRECONDITION, not the memo about the precondition. This is the same error as trusting
a "no skills changed" report instead of hashing the files: in both cases a status line was
believed because it was written down, when the underlying state was one cheap call away.

Corollary on credentials that arrive by email: treat them as already-exposed. Both GitLab tokens
came through in plaintext, so they were compromised the moment they were sent, regardless of what
we do next. Store them in the one secret file, use them, and schedule a rotation — do not pretend
that careful handling afterwards undoes an insecure delivery.

Fixed August 1, 2026: tokens stored in .credentials.json (read at push time by tools/git_askpass.py,
never embedded in a remote URL), 9,023 files pushed live, and the runtime mirror now re-syncs,
commits and pushes automatically as step 9/9 of the daily runner — so its freshness no longer
depends on anyone remembering.

<!-- learning:2026-08-01-a-quiet-queue-may-be-a-disconnected-one -->
**August 1, 2026** (from: sigrun-website-request-intake)

**A daily job can be perfectly correct and still be watching nothing. When a source returns the same answer for weeks, verify that anything upstream is connected to it.**

The Sigrun website intake read its Google Form sheet accurately every morning for sixteen
consecutive days and truthfully reported "no new requests, 1 row." The read was never wrong.
The form had never been shared with members. Seven people were waiting in queues the job
could not see, because every real request arrived by email, by Basecamp, or directly to
Dennis. The finding did not come from the data — it came from a client asking, on the
project thread, "please share a list of who is waiting."

Adopt as standing practice:

1. **An unchanging source is a hypothesis, not a fact.** Two weeks of identical output means
   either nothing is happening or nothing is arriving. Those have different owners and
   different fixes. After N consecutive no-change runs, spend one call confirming the
   upstream path is live — that the form is published, the webhook fires, the inbox is
   monitored, the sheet is the one people actually submit to.
2. **Count the queue, not the source.** A pipeline's real backlog is the union of everything
   feeding it. Keep an explicit lane for out-of-band arrivals (here, `tracked_non_form`) and
   treat it as first-class, because in a system where the front door is closed it *is* the
   whole queue.
3. **Reconcile against sister pipelines before reporting scope.** Two agents were tracking
   overlapping subsets of the same work — this job knew two members, another knew eight.
   Neither was wrong; both were partial. One read of the other agent's outbound email closed
   the gap. When you know another automation touches the same domain, diff against it.
4. **"No changes" is only a safe report if you checked what would have made it change.**
   Green on an unconnected input reads exactly like green on a healthy one, and it buys
   silence for as long as nobody outside asks.

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

<!-- learning:2026-08-01-does-not-resolve-is-not-is-not-registered -->
**August 1, 2026** (from: sigrun-website-request-intake)

**"Does not resolve" and "is not registered" look identical to `dig +short` and have completely different owners. Ask the TLD's own authoritative server, with controls.**

Four member domains were on a live ops ticket that said "point the A-record at the fleet."
Two of them — `anneliesalminen.com` and `piamuggerud.com` — are not registered at all. There
is no zone to add a record to. `dig +short A` returned empty for them, which reads as "DNS
not configured yet" and had been reported that way for four weeks. Ops would have gone
looking in GoDaddy for zones that do not exist.

Adopt as standing practice:

1. **Query the registry, not a resolver.** `dig @a.gtld-servers.net <domain> NS` and read the
   rcode: `NXDOMAIN` means no registry delegation (unregistered, or registered with no
   nameservers — either way the fix is at the registrar). `NOERROR` with an NS referral means
   registered and delegated, and only then is "add an A record" a real instruction.
2. **Run both controls in the same call or the result is unfalsifiable.** A made-up domain as
   the negative control (must return NXDOMAIN) and a known-good domain from the same batch as
   the positive control (must return an NS referral). Without them, an NXDOMAIN could be a
   network artifact. With them it is a finding you can put in front of a client.
3. **Before repointing any domain at the fleet, fetch its root and read the title.** The
   email-safety rule catches MX; it does not catch a working homepage.
   `lisasennhauserkelly.com` matched every "built but never provisioned" description in the
   queue while serving the member's real live business site at HTTP 200. Repointing it would
   have destroyed live work. Check for a live site *and* live email, separately.
4. **Correct a wrong public status the same day you find it.** Two of eight entries on a
   client-visible list were mis-diagnosed as waiting on our DNS. Left alone, the members
   would have waited on an action nobody could take. Naming the real blocker moved two items
   from an ops backlog to a one-message ask.

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

<!-- learning:2026-08-02-a-resent-credential-means-the-ask-was-ambiguous -->
**August 2, 2026** (from: Sigrun website intake — day 16 of a blocked publish; the third escalation was answered by re-sending the same failing key)

### When someone answers a request for a new credential by re-sending the old one, the request was ambiguous — not ignored

A member's finished site sat unpublished for sixteen days on one missing Application Password. Three
escalations went out over four days: a comment on an assigned to-do, a line on the client thread, and
an email. Each asked, in good faith, for "an Application Password for `<domain>`."

The reply arrived with a key and a link to where it had first been posted. It was the same key that
had been failing since day 12 — minted on the member's *old* `.com` install, which is a separate
WordPress from the live `.nl` site she was moved to. It returns 401 under every username, and the
sender's own status export said `hasAppPass:false` for the new site.

Nobody dropped anything. The ask named a **domain** and a **credential type**, and the person doing
the work reasonably read that as "send the password for that domain" — and one existed. The word that
was missing was the verb, and the target.

**Rules:**

1. **Ask for the verb and the install, not the credential and the domain.** "Mint a NEW Application
   Password ON `<domain>` (SiteId NNNN), user `<login>`, name `cowork-<person>`" cannot be satisfied
   by forwarding an existing key. "Send me the app password for `<domain>`" can.
2. **Re-asking the same way gets the same answer.** After the second identical reply, change the
   wording rather than the channel. Three escalations through three channels all carried the same
   ambiguous sentence, so all three produced the same outcome.
3. **State the disqualifying evidence in the ask.** "The key on file returns 401 under all four
   usernames, tested today against a probe that returned 200 for a known-good key in the same run"
   tells the reader the existing key is not the answer, before they reach for it.
4. **When a domain is re-mapped between TLDs, the two are separate WordPress installs**, and a key
   minted on the old one fails on the new one with the same `rest_not_logged_in` as a wrong password.
   Name which install a key was likely minted on rather than reporting "bad credential."

Learned August 2, 2026.

<!-- learning:2026-08-02-successfully-set-up-is-not-reachable -->
**August 2, 2026** (from: Sigrun website intake — the fleet provisioned WordPress sites for two domains that do not exist, and mailed a success notice for each)

### A provisioner reporting success tells you the installer ran, not that anyone can reach the result

Four member domains went through our New Site form in one evening. Four "Your new WordPress site has
been successfully set up at https://…" emails came back. Two of those domains return **NXDOMAIN at
the .com registry** — no delegation, no nameservers, no zone. They are not registered.

The installs are real. A `Host:` header probe to the fleet IP returns proper WordPress pages with the
members' names in the title. Everything downstream — the setup email, the fleet record, the status
list posted to the client — says done. Nobody on the internet can type an address that reaches
either one, and nothing in the pipeline is capable of noticing.

The same day, a related failure in the opposite direction: a member's site was recorded as `503 at
check time` and left there. Re-checked once, it 301s to `www` and serves her real 837 KB business
site. A single non-200 had been treated as a verdict.

**Rules:**

1. **Resolve the hostname before reporting a provisioning success.** One DNS lookup at the end of the
   installer separates "installed" from "reachable." Without it, "successfully set up" is a claim
   about our filesystem dressed as a claim about the member's site.
2. **`dig +short` cannot distinguish "not registered" from "registered, no records" — both print
   nothing.** Ask the TLD's own authoritative server (`dig @a.gtld-servers.net <domain> NS`) and read
   the rcode: NXDOMAIN means no registry delegation; NOERROR with a referral means registered. Run an
   invented domain and a known-good domain in the same call, or the result is unfalsifiable.
3. **Check our OWN records before escalating to the person.** Our build logs said all four domains
   were "registered 2026-07-01, GoDaddy, 1yr — gift." Two do not exist, which turns *"ask her where
   she registered it"* into *"check whether our own purchase completed"* — a question we can answer
   ourselves, and a far better thing to say to someone who was told her site was coming.
4. **A 503 is a moment, not a verdict.** Retry it, and follow the redirect — the root may 301 to
   `www` and only the `www` response carries the site. A non-200 feels like an answer, which is
   exactly why it gets recorded as one.
5. **Where a wrong action is unrecoverable, the refusal belongs in the tool.** Two of these domains
   serve live business sites and two do not exist; from the fleet's side all four look identical to
   "built, just needs provisioning." The publisher now refuses those four by name with the reason
   printed and an explicit override flag — and the refusal was tested for both outcomes, because a
   guard that has never been seen to fire is not known to work.

Learned August 2, 2026.

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
  calculator or interactive tool must be at least partly visible in the first
  screen, *after* the site's own header and title. Two or three sentences of
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
  published. Check at 1440x860 and 390x844 as an anonymous first visit, before
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
