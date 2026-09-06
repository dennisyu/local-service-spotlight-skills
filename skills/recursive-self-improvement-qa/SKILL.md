---
name: recursive-self-improvement-qa
description: After every task execution, write a meta article with run evidence, compare it with the canonical recipe and prior runs, and propose supported improvements. Publish or change the recipe under existing authorization.
---

# Recursive Self-Improvement QA

**Use this when** you want agents and SOPs that get sharper every run instead of going stale. The loop behind "one page per agent." Step 10 of the Local Service Spotlight method — the skill that improves the other nine.

## Inputs
- The skill/SOP that just ran, and its definitive article — the canonical instructions for the task.
- The actual output of the most recent run, including whatever went sideways.
- Previous meta articles for this skill, if any — the loop's memory.

## The loop
1. **Execute** the canonical task recipe within the authorized scope. Check its trigger, starting state, inputs and prerequisite outputs before following its ordered steps. Record necessary deviations and the reason; do not guess missing instructions.
2. **Write** a meta article for this execution using the [meta-article guidelines](https://blitzmetrics.com/meta-article-prompt/). Link the exact canonical task, recipe/skill revision and run evidence. Include a distinct execution ID, inputs, actions, output, pass/fail checks, deviations, measured effort, lessons and downstream handoff. A failed or partial run still gets a record with that status. The recipe and the run record are separate articles.
3. **Compare** the result with the canonical acceptance criteria and prior meta articles. Flag evidenced gaps in inputs, steps, checks and handoffs. Preserve UNKNOWN when evidence is missing.
4. **Propose** the smallest supported recipe or skill correction for each real defect. Record the decision, version accepted changes and link them to the originating execution. A clean run may need no recipe change.
5. **Close** the run with its written meta article, result and next owner. Publishing the meta article, merging a skill change, changing a live recipe or starting another run follows existing authorization. Keep draft, reviewed, published and verified states distinct; required writing does not authorize those actions.

## The QA checklist — run it every time
- Did the output match what the definitive article promised? Where, exactly, did it differ?
- Where did the agent guess? Determine whether the cause was missing evidence, access, an instruction or a wrong assumption; propose the supported fix.
- What input was missing or wrong at the start? Fix the Inputs section, not just this run.
- Could a worker repeat the run from the SOP alone, without asking you anything? If not, it isn't done.
- Does every produced asset link back to its canonical hub — no content vandalism?
- Is every fact sourced, and every name spelled exactly as the entity is spelled everywhere else?
- Voice check: direct, concrete, second person, no fluff. Cut every sentence that doesn't instruct.
- Did this run produce anything worth productizing — a reusable template, prompt, or standard?

## The Task Library model
The [Task Library](https://local-service-spotlight.github.io/task-library/) maps each repeatable task to its canonical recipe and skill. Link prerequisites and the downstream handoff, with observable acceptance checks. Topic hubs, references, comparisons and supporting stories have separate roles; an opening audit does not turn them into task recipes.
- **Workers** execute the checklist. **Managers** enforce it. **The architect** revises the system when flags repeat.
- One page per task, one URL per page — and every run makes the page better.
- That's how a library compounds instead of rotting: the documentation IS the asset.

## When to run it
- After any of the other nine skills executes — loop the run before you move on. Literal invocation: "Run recursive-self-improvement-qa on the skill that just executed."
- Weekly, on whichever skill produced the most flags.
- Before a sale or audit: the sharpened library is what the buyer is actually paying for.

## Output
- A written meta article for the run, linked to the canonical task/revision and evidence, with a distinct execution ID and accurate publication status.
- A QA punch-list: one fix per flag, each assigned.
- Any supported recipe/skill change, with its review decision, version and actual release status. No defect means no forced rewrite.

## For DealCon — agency owners & acquirers
**If you run an agency:** delivery quality that improves without you is the difference between selling a job and selling a company — a self-improving task library is the asset a buyer pays the multiple for.
**If you buy & sell companies:** in diligence, ask for the target's task library; if the process lives in the founder's head, you're buying a job, not a business. Post-close, install this loop so platform playbooks transfer to every bolt-on and sharpen as they go.
**Your edge:** name the task you've redone from scratch three times this quarter — that's the first skill.md to put in the loop.

## Run on a persistent agent (Fable 5)
- **Loop to done:** run this review after every task execution. Done means the meta article is written, acceptance results are evidenced and gaps have a supported next action/owner. Publication or another execution requires the existing authority. Meta writing is part of this run, not an endless series of meta-of-meta executions.
- **Self-verify:** run the QA checklist completely, every time — a skipped line is tomorrow's deviation, and the checklist audits you too.
- **Compound with memory:** prior meta articles are the loop's memory — read them before judging this run, so versions compound (v1.1, v1.2) instead of resetting.
- **Log the run:** count distinct execution IDs per canonical task and reporting period, not drafts, edits, retries or derivative pages. Keep failed/partial and unpublished history with its statuses. Preserve dated public-article volume separately; older examples without IDs cannot establish task frequency.

See `boil-the-ocean.md` for the full operating principles.

## Notes — Dennis's method
- One canonical recipe per task; one meta article per execution. The recipe teaches the work, and accumulated run evidence guides its improvement.
- This is recursive self-improvement applied to marketing ops. The library you installed today should be measurably sharper in 90 days — if it isn't, the loop isn't running.
- Boil the ocean on the checklist. Completeness beats good-enough, because every unwritten rule becomes tomorrow's deviation.
- Standardize, then improve: you can't sharpen a process that changes shape every run. SOP first, loop second.

## Definitive article & pairings
- Reference: https://localservicespotlight.com/meta-articles/ · https://blitzmetrics.com/meta-article-prompt/ · https://local-service-spotlight.github.io/task-library/ · https://blitzmetrics.com/always-boil-the-ocean-because-good-enough-is-not-enough/
- Pairs with: definitive-article-writer → **recursive-self-improvement-qa** → loop back through all nine, starting at personal-brand-strategist

## Learned in the field

*Appended automatically by the self-improvement loop (Skill-Learnings/): dated lessons from real runs. Newest at the bottom.*

<!-- learning:2026-07-18-close-the-loop-every-run -->
**July 18, 2026** (from: skill-pack-propagation follow-up session with Dennis, July 18, 2026)

Every run that executes this or any skill must END by filing what it learned: drop a note in Skill-Learnings/inbox/ (id, date, source, skills, lesson) at the project root. The harvest → propagate pipeline turns those notes into re-dated skills, rebuilt packs, and a refreshed public directory — multiple pack updates per day is the healthy signal. If the packs have not changed in a week, treat THAT as the defect: find where lessons are dying (not being filed, not harvested, or not propagated) and fix the pipeline, not just the symptom.

<!-- learning:2026-07-18-zero-work-is-a-signal -->
**July 18, 2026** (from: pack-propagation pipeline audit, July 18, 2026)

When a pipeline stage reports ZERO work for a surface that should have changed, treat the zero as a defect signal, not a clean bill. July 18, 2026 case: source skills were edited, yet two pack surfaces reported "refreshed 0" — their source-folder lookup had silently failed since July 13 (a zip top-folder name mismatch and a flat zip with no top folder), so they shipped stale content while stamping fresh dates. Fixes that must travel with this lesson: (1) every auto-discovery gets an explicit override map for the exceptions; (2) a failed lookup prints a loud WARN naming the fix, never a quiet skip; (3) after any run, diff EXPECTED changed surfaces against ACTUAL and investigate every mismatch before calling it done.

<!-- learning:2026-07-19-cadence-label-audit -->
**July 19, 2026** (from: skill-pack-propagation daily run)

When a job's cadence changes (this loop went weekly -> daily on 2026-07-18), audit the
automation script's OWN hardcoded strings, not just the runbook/SKILL.md doc. Found
propagate_all_packs.py still writing "Kept current automatically by propagate_all_packs.py
(weekly)" into every pack's VERSION.txt, and its module docstring still called itself
"ONE weekly job" — a full day after the switch to daily. Fixed both on 2026-07-19. Rule:
whenever a doc's cadence/date language changes, grep the executing script for the old
cadence word ("weekly", "monthly") before closing out the change — the runbook and the
code it describes must be re-dated together, or the automation quietly contradicts its
own SKILL.md.

<!-- learning:2026-07-19-javascript-tool-repl-semantics -->
**July 19, 2026** (from: michaelkrigsman.com QA run (filed into the loop by skill-pack-propagation 2026-07-19))

Tooling gotcha for in-page QA: the claude-in-chrome javascript_tool has REPL semantics —
the LAST TOP-LEVEL EXPRESSION is what gets returned. An async IIFE returns {} (an arrow
body needs an explicit `return`). Write top-level `await` code and END with a bare
`({...})` expression to return your result object. Use `var`, not `let`, so re-runs on the
same page do not throw redeclaration errors. (Mapped here to recursive-self-improvement-qa
because that is the QA workflow that uses javascript_tool for verification; there is no
standalone chrome-usage source skill — flagged for Dennis in the 2026-07-19 run summary.)

<!-- learning:2026-07-19-transcript-quote-verification -->
**July 19, 2026** (from: michaelkrigsman.com QA run (filed into the loop by skill-pack-propagation 2026-07-19))

Verify verbatim quotes at scale without blowing context: navigate Chrome to the source
transcript page, then match IN-PAGE via javascript_tool. Normalize both sides (lowercase,
curly to straight apostrophes, strip punctuation, collapse whitespace), test full-quote
containment, else slide an 8-word shingle window. Return one letter per quote (E = exact,
P = partial, M = missing). This verified 148 quotes across 16 client-rendered pages for
near-zero context cost. Partials are usually disfluency cleanups — pull plus/minus 300
characters around an anchor phrase to adjudicate before ever calling something a misquote.

<!-- learning:2026-07-19-date-badge-bump-must-not-silently-noop -->
**July 19, 2026** (from: skill-pack-propagation daily run (run 2))

A pack surface can update its .zip link and STILL serve a stale visible date — the exact
June-10 failure this loop exists to prevent. Root cause found 2026-07-19: bump_dates() used
`(Kept current|Last updated)(</b>)?[^A-Za-z0-9<]{0,12}(date)`, and that character class
cannot span the WORD "updated" in `Kept current</b> — updated July 18, 2026`. So the regex
matched nothing, the badge never bumped, and the run printed `dates [] -> July 19, 2026`,
which READS like success but actually means zero replacements. dennisyu.com/dealcon and
/wichita sat at "July 18, 2026" while serving July 19 zips; aibuilderspotlight.com/skill-pack
and dunkerspotlight.com/set-up-claude had no badge at all.
Rules: (1) allow non-tag text between the label and the date and require a real month name;
(2) treat an EMPTY match list on a pack-serving surface as a DEFECT and fail loud — never
log it as a no-op; (3) if a surface serves a pack but has no date badge, INSERT one rather
than only replacing; (4) always confirm the bump with a cache-busted fetch asserting today's
day+year actually renders, not just that the .zip URL changed.

<!-- learning:2026-07-19-harvest-scan-root-for-strays -->
**July 19, 2026** (from: skill-pack-propagation daily run (run 2))

A learning is only in the loop if it lands in Skill-Learnings/inbox/ in the one-lesson
front-matter format. On 2026-07-19 the michaelkrigsman.com QA run dropped 5 lessons as a
single non-conforming digest in the Skill-Learnings/ ROOT (fields named "target:" not
"skills:", five lessons in one file) — so harvest saw an empty inbox and NONE of them
reached the source skills. That is a silent leak that masquerades as a legitimate
zero-change day (the exact failure the loop is supposed to catch). This run split the
digest into 5 proper inbox notes by hand and harvested them. Permanent fix: make
harvest_learnings.py ALSO scan the Skill-Learnings/ root for stray *.md that are not
README/inbox/applied and print a loud "[STRAY] unharvested learning outside inbox" warning
(and exit non-zero on stray files), so mis-filed learnings surface instead of rotting.
Also worth adding to the note format: reject front-matter that uses "target:" instead of
"skills:".

<!-- learning:2026-07-19-republish-network-preflight -->
**July 19, 2026** (from: skill-pack-propagation daily run (run 2))

The login-free republish depends on the MAC's CURRENT network, not just credentials. On the
2026-07-19 run the Mac was on a venue/guest-WiFi content filter that returned a 200 HTML
"WARNING - BLOCKED URL … blocked at the direction of the venue" page for dennisyu.com,
aibuilderspotlight.com, dunkerspotlight.com, and localservicespotlight.com, while
blitzmetrics.com (different host) stayed reachable. The block returns HTTP 200 with a block
page, so a naive `assert status == 200` PASSES — you must parse the body (expect JSON) to
detect it. Rule: preflight `GET /wp-json/wp/v2/users/me` on EVERY target domain and confirm
the response is valid JSON BEFORE rebuilding/uploading; if any domain returns non-JSON,
report the surface as PENDING (network-blocked) and abort with no partial edits, rather than
letting uploads fail mid-run and leave pages half-swapped. propagate can still finish the
local rebuild + stamp; only the live push waits for an unfiltered network.

<!-- learning:2026-07-20-frozen-oneshot-scripts-regress-dates -->
**July 20, 2026** (from: Repurposing Suite absorption run — re-running apply_republish.py (frozen at "July 18, 2026") regressed live "Kept current" badges from July 19 back to July 18 on four pages)

Before running any republish or date-bumping script, check whether it hardcodes a date (a `TODAY_HUMAN = "July 18, 2026"`-style constant) and refuse to run it on any other day — a frozen one-shot re-run later silently moves live dates BACKWARD, which is worse than not bumping at all. The durable pattern is the generalized daily script (`republish_<today>.py`) that computes the date and reads the currently-linked URL from the live page instead of hardcoding either. Related: two sessions can work the same pipeline at once — before rebuilding zips or writing today's script, look for a fresh `_republish_urls_<today>.json`, `_pack-backups-<today>/`, or an already-written dated script, and converge instead of duplicating. Learned July 20, 2026.

<!-- learning:2026-07-20-new-skill-registration-points -->
**July 20, 2026** (from: Shipping video-repurposing-agent everywhere — the skill was live in every zip while the /skill-packs/ page still didn't list it, because the page renders from a hardcoded roster, not the dates map)

A new skill is not "shipped everywhere" until it is registered at every hardcoded roster, and there are four of them: (1) the pack source folders or the MANDATED list in propagate_all_packs.py (which puts it in every zip), (2) CORE_SKILLS in Skill-Pack-Directory/build_skillpacks_index.py (the /skill-packs/ page lists ONLY skills with a roster row — the _pack-skill-dates.json entry alone changes nothing visible), (3) for SOMBA: ORDER + TITLE + JOB + USE in Sigrun-SOMBA/build_agents.py plus the pack README run-order list, and (4) the skill's own "Pairs with" chains in sibling skills. After registering, verify by fetching the LIVE page and searching for the slug — a green propagation log with a missing roster row still renders a page that hides the skill. Learned July 20, 2026.

<!-- learning:2026-07-20-sandbox-mount-deadlock-host-fallback -->
**July 20, 2026** (from: Weekly fleet-hub-audit run — sandbox "Resource deadlock avoided" escalated from writes to READS (couldn't even cat _batch_audit.py), so the whole 24-chunk pipeline ran host-side via Desktop Commander instead)

The sandbox mount lock can escalate beyond single-file writes: a session can lose READ access to mounted project files ("Resource deadlock avoided" on cat/open), which silently no-ops any python script run from the sandbox against those files. When that happens, don't fight it file-by-file — move the WHOLE pipeline host-side (Desktop Commander start_process): macOS python3 runs stdlib-only audit scripts unmodified, and a strictly-sequential `for s in 0 8 … 88; do python3 chunk.py $s 8; done` loop in ONE host process preserves the WAF-safety of one-chunk-per-call while escaping the sandbox's 45s cap entirely. Three host-side gotchas learned the same run: (1) Desktop Commander MCP requests time out around 2 minutes no matter what timeout_ms you pass — never bake `sleep 150+` into a command; do instant file-size polls (`ls -la chunk_* | awk '$5>2'`) or long-poll a running process with read_process_output; (2) heredoc (`python3 - <<'EOF'`) commands are intermittently rejected with "Command not allowed" — keep fallbacks as `python3 -c` one-liners or run reads from the sandbox once the lock clears (it can clear for files the host process rewrites); (3) detached `( … ) &` subshells lose their output when the parent exits — don't use them for polling. Learned July 20, 2026.

<!-- learning:2026-07-20-consent-scanner-blanks-inline-apps -->
**July 20, 2026** (from: Sigrun SOMBA member dashboards (sigrun.com) — refiled from a stray root note by skill-pack-propagation on July 21, 2026)

A cookie-consent plugin can silently kill an inline JavaScript app for logged-out visitors while
every logged-in test looks perfectly healthy. On sigrun.com the /somba-member/ page rendered BLANK
for members for three days while rendering fine for admins and in Elementor preview. Root cause:
the consent plugin (WPConsent) pattern-matches INLINE SCRIPT CONTENT server-side and rewrites any
matching tag to type="text/plain" until the visitor accepts cookies. Member data (facebook,
linkedin, youtube profile URLs) matched tracker signatures; on a second page, random base64
ciphertext happened to match the TikTok-pixel signature. Admin sessions and editor previews bypass
the scanner entirely, so the outage was invisible to every internal check.

Rules for any skill that ships large inline <script> apps to WordPress:
1. If a script-driven page is blank for visitors but fine for admins, check for a consent or
   security plugin rewrite FIRST: fetch the page anonymously (no cookies, full Chrome UA) and grep
   your own script tag for type="text/plain" or data-*consent* attributes.
2. Ship app payloads as an inert base64 <template> element plus a tiny keyword-clean loader
   (createElement('script') + TextDecoder('utf-8') — NOT bare atob, which mojibakes UTF-8).
   Consent scanners only rewrite script/iframe tags, and base64 is also immune to wptexturize.
3. Never allow tracker-ish tokens (ttq, fbq(, gtag(, tiktok, facebook., linkedin., youtube.) inside
   loader code that must not be consent-gated.
4. Anonymous verification is the only verification: logged-in browsers and editor previews lie.
5. Bonus privacy pattern: per-member token links via AES-GCM envelope encryption — the page carries
   only ciphertext and the token lives in the URL FRAGMENT (#t=...), so it never reaches server logs.
Learned July 20, 2026.

<!-- learning:2026-07-20-generated-page-source-of-truth -->
**July 20, 2026** (from: skill-pack-propagation daily run, second pass ~05:15 (first pass ran 02:44))

A live edit to a GENERATED page is not done until the generator's data knows about
it. The 02:44 pass uploaded fresh zips and live-edited localservicespotlight.com/skill-packs/
to the new -5/-4/-3 URLs, but never wrote those URLs into the PACKS list in
Skill-Pack-Directory/build_skillpacks_index.py — so the very next propagate_all_packs.py
run (05:10 same day) regenerated the page from the stale list and quietly reverted the
directory to day-old zip links for ~2.5 hours. Rule: for any surface rendered by a
builder script, the builder's data block (PACKS) is the ONLY durable place — after
every media upload, write the returned source_url + today's ISO date (+ skill count)
into PACKS and re-run `build_skillpacks_index.py --publish`; treat a live-page edit
without the matching generator-data edit as NOT done. Cheap start-of-run check: diff
the live page's zip URLs against PACKS before uploading anything — a mismatch means
the previous pass skipped this step. Learned July 20, 2026.

<!-- learning:2026-07-21-a-proposed-fix-is-not-a-fix -->
**July 21, 2026** (from: skill-pack-propagation daily run)

A learning note that ends with "permanent fix: make the script do X" has not fixed anything. On
July 19, 2026 a note prescribed the exact remedy for mis-filed learnings — have
harvest_learnings.py scan the Skill-Learnings/ root for stray *.md, print
"[STRAY] unharvested learning outside inbox", and exit non-zero. The note was harvested into the
source skills and the prescription was never written into the code. Two days later two more real
learnings (the Ahrefs free-DR deprecation and the WPConsent inline-script outage) were sitting in
that same root, unharvested, reaching no skill — the identical leak, on a loop that had already
diagnosed itself in writing.

Rule: when a run proposes a permanent fix to a tool, implement it in the same run, or the note is
just a nicely-worded IOU. Before filing a note that prescribes a code change, grep the target file
for the behavior you are about to prescribe — if it is already prescribed and still absent, that
is the highest-priority work item of the run, ahead of the run's nominal task. Closing the loop
means the code changed, not that the lesson was written down eloquently.
Learned July 21, 2026.

<!-- learning:2026-07-21-date-badge-regex-cannot-cross-tags -->
**July 21, 2026** (from: skill-pack-propagation daily run)

The "Kept current — updated <date>" bump has now silently failed twice for the same reason, and
both times the zip link kept updating while the visible badge froze — the exact stale-content
failure the job exists to prevent, wearing a green checkmark.

- Generation 1 (fixed July 19, 2026) died on `Kept current</b> — updated July 18, 2026`: the
  separator class `[^A-Za-z0-9<]{0,12}` could not span the word "updated".
- Generation 2 (found July 21, 2026) died on
  `<strong>Kept current</strong> &mdash; updated <strong>July 18, 2026</strong>`: the separator
  `[^<]{0,40}` cannot cross the `<strong>` that WRAPS the date. blitzmetrics.com/task-library-dashboard
  and /build-agents therefore displayed "July 18, 2026" for three consecutive daily runs while
  their TaskLibrary zip was re-uploaded each day.

Two rules, both permanent:
1. The separator between the label and the date must tolerate bounded inline TAGS, not just text:
   `(?:[^<]|<[^>]{0,60}>){0,80}?` between `(?:Kept current|Last updated)` and the month-name date.
   Anchor on a real month name so it can't drift onto an unrelated number.
2. Zero matches is a DEFECT, not a no-op. If a page's raw content contains the label at all and
   the date pattern matched nothing, print `[DEFECT]` and exit non-zero. A silent "NOCHANGE" is
   how a broken pattern survives three days. Verifying the RENDERED page (cache-busted) for
   today's day+year string is the only proof that counts.
Learned July 21, 2026.

<!-- learning:2026-07-21-fleet-500-triage-and-partial-publish -->
**July 21, 2026** (from: skill-pack-propagation daily run — BlitzAdmin fleet outage)

When a publish target returns HTTP 500, three cheap probes localize the fault before anyone
guesses at credentials — and they turn "the site is down" into an actionable bug report.

1. AUTH IS NOT THE SUSPECT UNTIL PROVEN. Run GET /wp-json/wp/v2/users/me with app-password Basic
   auth and a full Chrome UA against a KNOWN-GOOD site first. On July 21, 2026 dennisyu.com and
   blitzmetrics.com both returned 200 with the administrator identity while every BlitzAdmin
   fleet site returned 500 — so the app passwords were fine and the diagnosis moved to the host
   in one step instead of repeating the July 6, 2026 "blitzmetrics app password is broken"
   misdiagnosis.
2. PROBE THE LAYER, NOT THE PAGE. Compare endpoints that load different amounts of WordPress:
   /wp-login.php and /wp-admin/admin-ajax.php returned 200 (core, DB and every plugin load fine)
   while /, /feed/, /wp-json/ and /?rest_route=/ all returned 500. Those four are exactly the
   paths that run the main query — so the fatal lives in a hook at parse_request / wp() /
   template_redirect, NOT in the theme's functions.php and NOT in the database. That single
   sentence is what a host or developer needs; "the site is 500ing" is not.
3. CHECK WHETHER STATIC ASSETS STILL SERVE. /wp-content/uploads/*.zip returned 200 on all three
   dead sites, so every QR-linked pack download kept working while the landing pages were dark.
   Say that explicitly in the report — it is the difference between "attendees can't download"
   and "attendees can download but can't read the page".

And the publishing rule that follows: publish to the healthy hosts, record the unreachable ones,
and NEVER bump a "Kept current" date on a surface you could not actually refresh. A pack whose
date says today but whose zip is yesterday's is worse than an honestly stale date.
Learned July 21, 2026.

<!-- learning:2026-07-21-monitor-false-positives-are-security-failures -->
**July 21, 2026** (from: sigrun-security-monitor daily run)

A monitor that alerts on something harmless every single day has already failed, because the next
real alert arrives in a channel nobody reads. The sigrun.com security monitor scanned rendered HTML
for spam words with a plain substring test. On July 20, 2026 the /my-dashboard/ token gateway
shipped, embedding an AES-GCM envelope as one unbroken 1,036,296-character base64 run. Random
base64 spelled "pORn" inside it. The monitor alerted on July 20 and again on July 21 — four
consecutive ALERT lines in security/log.md, every one of them our own page, on a service whose
entire purpose was catching the next infection on day one instead of waiting for anyone to
notice it.

Rules for any content-scanning monitor:

1. Strip data before scanning prose. Any unbroken run of 200+ base64 characters is a token, an
   inline font, or a data: URI — never text. Substitute it out, then scan.
2. Split markers by class. Domains and CSS hiding patterns ("znaki.fm", "1xbet",
   "position:absolute;left:-9") contain punctuation that cannot occur inside base64, so a raw
   substring test is safe. Plain English words ("casino", "viagra", "porn") need a leading
   word-boundary against the stripped text.
3. Require a leading boundary, not a trailing one. Injected spam is nearly always inflected —
   "casinos", "pornography", "viagra-online". A trailing boundary makes the monitor miss the real
   attack while still flagging the noise.
4. Keep collision-prone words out of the word list entirely. "escort" fires on legit prose
   ("escorted"); if such a term is needed, express it with punctuation as a raw marker.
5. Pin both directions in tests. Every fix to a detector needs a test that the false positive stays
   silent AND a test that a genuine injection still fires, including one page that contains both a
   token blob and real spam. security/test_monitor.py, 16 assertions, runs in under a second.

Diagnose before you escalate: the run's first move was to locate the exact offending byte offset
and print its surrounding context, which showed the match sitting inside our own
`<template id="smb-vault">`. Drafting the alert email the runbook called for would have sent
operations chasing our own code.
Learned July 21, 2026.

<!-- learning:2026-07-22-payload-surfaces-and-inspect-before-upload -->
**July 22, 2026** (from: skill-pack-propagation daily run)

First routine refresh of the two LSS master pack pages (business-authority-pack 70357,
entrepreneur-skill-pack 73392) since their July 20, 2026 launch surfaced a class of surface the
daily republish flow could not see: PAYLOAD surfaces, where the zip link, the "Kept current"
badge AND the footer date all live inside one base64-encoded document in the page raw. A plain
fragment-swap reports NOCHANGE on a page that is actually stale — the silent-noop failure the
badge lib exists to prevent, one layer deeper.

Rules from the run (reference implementation: Skill-Pack-Directory/republish_2026-07-22.py):

1. Payload surfaces get decode -> swap -> bump -> re-encode, and the RENDERED verify must also
   decode the rendered page's payload before asserting the new URL and date are live.
2. The master pages' footer is a bare "Updated <Month D, YYYY>" with no Kept-current/Last-updated
   label, so DATE_PAT can never reach it. FOOT_PAT (capital-U "Updated", case-sensitive so the
   lowercase badge text stays DATE_PAT's) bumps it — applied ONLY to payload surfaces, because on
   plain pages the same pattern would falsify dated changelog lines (task-library-dashboard
   keeps one).
3. Inspect the live page BEFORE uploading media, and curate the upload list from what the pages
   actually link. Today's checklist said dealcon carries two zips and build-agents serves
   agent-pack.zip; live inspect showed one zip on dealcon and the TaskLibrary zip on build-agents.
   Trusting the checklist would have made an orphan media upload (the July 21, 2026 run made
   exactly that: a TaskLibrary zip on dennisyu.com that nothing links). The REPUBLISH checklist
   template in propagate_all_packs.py is now corrected to the verified surface list, including
   the two payload surfaces and the two Spotlight surfaces it omitted.
Learned July 22, 2026.

<!-- learning:2026-07-23-directory-packs-need-manifest-driven-url-swap -->
**July 23, 2026** (from: skill-pack-propagation daily run)

The /skill-packs/ directory (LSS page 72143, generated by build_skillpacks_index.py) is the one
surface propagate_all_packs.py republishes on its own — but it renders the download URLs and
per-location dates HARD-CODED in its PACKS list. On a change day propagate rebuilds every zip and
re-publishes the directory, yet PACKS still points at YESTERDAY's media (e.g.
Business-Authority-Pack-1.zip) carrying yesterday's date. The page publishes "successfully" while
serving a stale download — the exact June 10 failure mode, one layer up from the individual pack
pages the badge lib already guards. A date bump alone is not enough here; the LINK is what rots.

Rules:

1. On any day a pack's zip changes, its /skill-packs/ card needs a manifest-driven URL swap, not
   just a date bump. The new media URL is the source_url WordPress returned for today's upload
   (it suffixes duplicates -1, -2, ...), so it can only be read from
   _republish_urls_<today>.json — never hand-typed, never guessed by incrementing yesterday's -N.
2. Swap by host + filename stem + optional -N suffix (the same pattern republish_*.py swap_urls
   uses), so a card already on today's URL is left alone and a shared zip (DealCon-Skills-v3 backs
   BOTH /dealcon and /wichita cards) re-points every card at once.
3. Bump a card's date ONLY if its download URL actually changed, and assert url_swaps ==
   date_bumps before writing the file. Equal counts prove every re-pointed card got re-dated and
   no unchanged card was silently touched; a mismatch is a defect that must stop the write, not a
   warning to print past.
4. Verify the RENDERED directory cache-busted after --publish: assert every new -N URL is present
   AND every prior -N URL is GONE. "New URL present" alone still passes if a stale link survives
   elsewhere on the page — check both directions, the same discipline verifyzips uses.

Reference: Skill-Pack-Directory/update_index_packs.py — run after `republish_<today>.py upload`
and before `build_skillpacks_index.py --publish`. Closed the gap 2026-07-23: 8 cards re-pointed
(Business, Entrepreneur, PBAP, DealCon, Wichita, AI-Builder, Dunker, TaskLibrary), live directory
verified with zero stale URLs remaining.
Learned July 23, 2026.

<!-- learning:2026-07-24-detach-long-publishers-verify-by-state -->
**July 24, 2026** (from: skill-pack-propagation daily run, July 24, 2026)

Launch any long-running publish driver detached with its output captured to a log file
(`nohup python3 driver.py apply > _apply-<date>.log 2>&1 &`), then poll the log — never
run it in the foreground of an orchestrator/tool call that can time out. On July 24, 2026
a timed-out tool call orphaned a mid-flight 8-surface publish: the process kept running
but its stdout was lost, and one surface's POST failed with no visible error. Recovery
discipline: (1) before relaunching anything, `pgrep` for the live process — never run two
publishers concurrently; (2) after it exits, verify by STATE, not by stdout — a read-only
inspect of every surface's raw content is ground truth even when the log is gone; (3) heal
by re-running the idempotent apply, which skips already-current surfaces and only touches
the stragglers. Verification you can re-derive from live state beats any transcript.

<!-- learning:2026-07-25-partial-set-days-diff-not-restamp -->
**July 25, 2026** (from: skill-pack-propagation daily run)

On a partial-change day, the propagation manifest diff -- not zip bytes -- decides which
surfaces republish. propagate_all_packs.py rebuilds and restamps EVERY zip's VERSION.txt
daily, so local bytes always differ from live even for packs with zero changed skill files;
byte-comparing would republish everything and manufacture "Kept current" bumps. On July 25,
2026 TaskLibrary had zero changed files: trim the day's driver to the changed UPLOADS +
SURFACES only, leave unchanged surfaces' dates untouched (their older day+year stamp is the
honest one), and let update_index_packs.py bump only index locations whose download URL
actually changed.

<!-- learning:2026-07-26-verify-the-format-each-surface-actually-renders -->
**July 26, 2026** (from: skill-pack-propagation daily run)

Verify against the format the surface actually renders, not the format you wrote. On July 26, 2026 the
pack republish verified clean on all six pack pages, then flagged localservicespotlight.com/skill-packs/
as stale. It was not stale. The two families of surface print the same date differently: the pack pages
render the full month ("July 26, 2026", written by the republish driver's DATE_PAT and FOOT_PAT), while
the directory index renders the abbreviated month ("Jul 26, 2026", written by build_skillpacks_index.py).
Both satisfy the day + year rule, so both are correct — and neither string contains the other, because
"July 26, 2026" does not contain "Jul 26, 2026". A cross-surface checker that hard-codes one literal is
wrong in both directions: it cries stale on a page that is current, or, if the assertion is ever inverted,
it passes a page that is genuinely months old.

So when a check spans surfaces built by different generators, resolve the expected string per surface —
match a date PATTERN and compare the parsed date to today, rather than testing for one rendered literal.
Fetch the page and read what it prints before you write the assertion; where a page carries a base64
payload, decode it first or the date you are looking for is not in the haystack at all. The same applies
to the zip inventory: a directory page lists packs owned by other jobs, so "every zip URL must be one I
uploaded today" is a false alarm by construction — scope the assertion to the packs this run owns.

The cost of getting this wrong is not a red line in a log. A verifier that reports a false failure every
run is one nobody reads, and the whole point of this pipeline is that the June 10 stale-download incident
should be caught before a client finds it. False positives are a verification failure, not cosmetics — fix
the checker, and pin it with a case from each generator so the two formats cannot silently drift apart.

<!-- learning:2026-07-26-classify-diffs-dont-just-diff -->
**July 26, 2026** (from: sigrun-security-monitor daily task)

### A monitor must CLASSIFY changes, not just diff them

Applies to any monitoring or audit skill that compares today's state to a stored baseline —
security monitors, fleet audits, SERP monitors, delta audits, Wikidata audits.

**What happened.** The sigrun.com security monitor fired 16 ALERT lines. All 16 were one
thing: WP Engine's managed auto-updater moved eight plugins forward by exactly one release
overnight (Elementor 4.1.5→4.2.0, Yoast 28.0→28.1, and six more). The monitor did a plain
set difference on `{plugin, version, status}` objects, so every bump printed twice — once
as the new version "CHANGED/ADDED", once as the old version "REMOVED."

Worse than the noise: nothing in the design ever cleared it. The baseline only moves when a
human runs `--baseline`, so the same 16 lines would have printed every morning
indefinitely. That is the exact failure mode that makes a monitor worthless: the alerts are
there and nobody is reading them.

**The rule.** A diff tells you something changed. A monitor's job is to say whether that
change is *expected*. Any monitor whose baseline can only be refreshed by hand will
eventually be refreshed by nobody, and then it is decoration. So for every field you diff,
answer up front: what does a legitimate change to this field look like, and can I verify it
automatically?

- **Verifiable and expected** → INFO, and advance the baseline for that one field only.
  Plugin version went up and api.wordpress.org confirms that exact version is a published
  release of that exact slug? Routine. Log it, move the row, stay silent.
- **Unverifiable** → ALERT. An upstream lookup that failed means *we do not know*, which is
  not the same as fine. Never let a failed check fall through to a pass.
- **Expected-shaped but wrong** → ALERT loudly, and name the risk in the message. A
  *downgrade* is the tell — that is how a patched vulnerability gets reintroduced. A version
  string upstream never published is a tampered plugin folder.
- **Never softened** → the fields that carry the actual threat. New/removed items, status
  flips, and anything user- or permission-related stay strict-diff with no exceptions.

**Two traps to design against.**

1. *Auto-advancing the baseline is only safe when the advance is earned.* Advance one row
   per verified item, never "accept everything I saw today." Otherwise the first real
   intrusion silently becomes the new normal.
2. *A poisoned wave.* Real tampering will arrive hidden inside a legitimate-looking batch.
   Test it: take a valid 8-plugin update wave, smuggle in one downgrade and one rogue slug,
   and assert that both still fire and only the clean seven advance. If your classifier
   handles a batch as a batch instead of per-item, this is where it breaks.

Receipts: `classify_plugins()` plus 31 new offline tests (upstream lookup stubbed, so the
suite never depends on the network); pre-change baseline retained; the run went from 16
ALERT to exit 0 with 8 INFO lines, then fully silent on the next run. Same underlying lesson
as the July 21, 2026 `pORn` false positive, one layer up: **false positives are a security
failure, not cosmetics** — fix the detector, not the symptom, and pin it with a test in both
directions.
Learned July 26, 2026.

<!-- learning:2026-07-27-a-site-going-down-can-masquerade-as-resolved -->
**July 27, 2026** (from: weekly-fleet-hub-audit (Fleet-Publishing-System))

### Diff on signals, not list membership — a site going down looks exactly like a gap being "resolved"

Week-over-week gap diffs compare list membership in `fleet-audit-gaps.json`. When
philmershon.com and thyrellpardjo.com went unreachable this week they dropped out of
`needs_hub`, which a naive diff reads as "resolved" — when in fact the site got worse,
not better.

**Rule: before reporting anything as RESOLVED, check that the subject is still
reachable.** A domain leaving a gap list while its homepage status is non-200 is a
regression, not a fix. Cross-check every "resolved" against `homepage_up` from the same
run, and report it as a regression when the site is down.

Same shape as the standing rule "verify the replacement text, not just the absence of the
old text": **absence of a problem marker is not evidence of the good outcome.** Whenever a
check is written as "X is no longer present," ask what else could remove X, and assert the
positive condition instead.
Learned July 27, 2026.

<!-- learning:2026-07-27-normalise-http-header-case-at-the-boundary -->
**July 27, 2026** (from: weekly-fleet-hub-audit (Fleet-Publishing-System, impact_fleet.py))

### Never read a metric out of `dict(resp.headers)` — case-insensitivity is lost

`urllib`'s `resp.headers` is an `email.message.Message`, whose `.get()` **is**
case-insensitive. `dict(resp.headers)` is a plain dict and **is not**. Our fleet host
returns WordPress pagination headers title-cased as `X-Wp-Total`, so every
`hdr.get("X-WP-Total", default)` lookup missed and fell through to its default:

```
dict(resp.headers).get("X-WP-Total")  -> None
resp.headers.get("X-WP-Total")        -> 1682
actual keys: ['X-Wp-Total', 'X-Wp-Totalpages']
```

`total_posts` collapsed to `len(posts)` = 10 (the `per_page` cap) on all 91 sites and
`posts_30d` to 0 on all 91. The fleet reported "0 sites posting in 30 days" while
seankelly.io had published 1,028 posts in that window. Content velocity contributed a
constant to every Business Impact Score since the 2026-07-19 launch, and the
content-dispatch queue was flagging active sites as dormant. It scored wrong for 8 days.

**Standing rule for every collector we write:** if a value is read out of an HTTP
response header, normalise the case at the boundary. Never `dict(resp.headers)`.
Applies equally to `requests` (its own `CaseInsensitiveDict` is safe — but
`dict(r.headers)` throws that away), `http.client`, and `urllib`. Fix shipped as a
`CIHeaders(dict)` class that lowercases keys on ingest and on lookup (`get`,
`__getitem__`, `__contains__`); post-fix verification: seankelly.io 1,682 total /
1,028 in 30d.

**Companion rule — a defaulted metric must be distinguishable from a real zero.**
`hdr.get(key, 0)` returning 0 for "header absent" is indistinguishable from a site that
genuinely posted nothing. Uniform values across an entire fleet are the tell. Any
collector that produces a fleet-wide constant (0 everywhere, or the page-size cap
everywhere) should fail loudly rather than score: if >90% of rows return the identical
value for a metric that should vary, print a `[WARN]` line instead of publishing it.
Learned July 27, 2026.

<!-- learning:2026-07-27-read-vendor-deprecation-warnings-live -->
**July 27, 2026** (from: cxotalk-weekly-maa run)

### A vendor date transcribed into an SOP silently rots — read the warning string on each call

`public-domain-rating-free`'s deprecation warning now reads **2026-08-10**, not the
2026-08-01 recorded in the July 20, 2026 learning. Ahrefs pushed it back 9 days.

**General rule: read the warning string on each call rather than trusting a date transcribed
into a skill file.** Vendors move deprecation dates in both directions, so a hard-coded date
in an SOP is wrong in a way nobody notices — it either panics a run early or lets it walk
off a cliff late. Where a date must be written down, write it as "as of <Month D, YYYY> the
API said X" so the staleness is visible on the page.

**Degradation-banner rule confirmed a second time.** Basecamp again rendered its "isn't
fully functional right now" banner during the run. Per the July 24, 2026 learning it was
treated as a hint, not a verdict — the post was attempted anyway and succeeded on the first
try, verified server-side by fresh navigation (comment count 24 → 25). Two-for-two. The
banner is stale often enough that deferring on it should be considered a bug, not caution.
Learned July 27, 2026.

<!-- learning:2026-07-27-a-reported-defect-nobody-clears-is-an-unfixed-defect -->
**July 27, 2026** (from: skill-pack-propagation daily run, July 27, 2026)

### "Report it and move on" is how a loop dies quietly — clear the queue or it isn't a queue

On July 27, 2026 the harvester opened with three failures, all of them correctly detected,
correctly printed, and correctly non-fatal:

- `2026-07-21-monitor-false-positives...` — targeted a skill slug (`security-monitoring`)
  that has never existed. **Stuck in inbox 6 days.**
- `2026-07-26-classify-diffs-dont-just-diff.md` — filed with no front-matter block, so it
  parsed as nothing. Stuck 1 day.
- Two multi-lesson notes sitting in `Skill-Learnings/` root, never in `inbox/` at all.

The SOP said such notes "stay in inbox and must be reported." They *were* reported — every
single day, in a report that ran green everywhere else. Six days of learnings reached no
skill while propagation kept publishing healthy-looking small diffs. Repairing them turned a
3-note day into 9 notes, 34 skill-file updates, 11 distinct skills, and a full 9-surface
republish including two surfaces that had been idle since July 24, 2026.

This is the *exact* failure the July 21 and July 26 notes describe — "a monitor that alerts
on something harmless every day has already failed, because the next real alert arrives in a
channel nobody reads" — one layer up, and the harmless-looking alert was the loop reporting
its own starvation. The notes warning about it were themselves the ones stuck.

**Rules:**

1. **A run that detects a malformed input must fix it or escalate it by name — never just
   print it.** Rewriting a mis-slugged or front-matter-less note into the correct format is
   the job, not a favour. Confirm the target by reading the candidate skill files, not by
   guessing from the slug.
2. **A queue with the same item in it two runs running is a failure, and the second run owns
   it.** If an item can't be repaired automatically, say so in the summary as a blocker with
   its age in days — "3 notes harvested" hides "and 2 have been stuck since the 21st."
3. **Never add an alias map to make a bad slug resolve.** `README.md` is right that typos
   must surface. Correct the note; don't teach the harvester to accept wrong input, which
   only moves the silence somewhere harder to see.
4. **Count age, not volume.** The health metric for this loop isn't notes-per-day, it's
   oldest-unharvested-note. That number should never exceed 1 day.
Learned July 27, 2026.

<!-- learning:2026-07-27-verify-a-pack-changed-by-hashing-members-not-by-the-refreshed-count -->
**July 27, 2026** (from: skill-pack-propagation daily run, July 27, 2026)

### Decide whether a pack really changed by hashing its members against the pre-run backup

Propagation prints `refreshed N md` per pack, but that counts files *copied from source*, not
files whose bytes differ — and `VERSION.txt` is restamped every run regardless. Neither number
answers the question the republish step actually asks: *did this pack's content change?*
Getting it wrong is expensive in both directions. Skip a real change and a QR-linked zip
serves stale content (the June 10, 2026 incident). Republish a no-op and the "Kept current —
updated <date>" badge lies, because the badge means *content updated*, not *checked*.

On July 27, 2026 the TaskLibrary packs showed `refreshed 1 md` and the two blitzmetrics
surfaces had been legitimately skipped on July 25 and 26. Rather than trust either signal:

```python
import zipfile, hashlib
h = lambda p: {n: hashlib.sha256(zipfile.ZipFile(p).read(n)).hexdigest()
               for n in zipfile.ZipFile(p).namelist() if not n.endswith('/')}
old, new = h('_pack-backups-<today>/X.zip.bak'), h('X.zip')
changed = [k for k in new if k in old and old[k] != new[k]]
```

Result: `['TaskLibrary-Skills/boil-the-ocean.md', 'TaskLibrary-Skills/VERSION.txt']` — a real
content diff, so blitzmetrics went back into the surface set on evidence. Had it come back
`['VERSION.txt']` alone, the correct action was to skip and record why.

**Rule: before republishing or skipping a pack, diff its zip members by hash against
`_pack-backups-<today>/<pack>.zip.bak`, and discount `VERSION.txt`. A restamp is not a
change.** Put the finding in the checklist line so the skip is auditable next run.
Learned July 27, 2026.

<!-- learning:2026-07-28-a-checker-with-a-literal-in-it-cries-wolf -->
**July 28, 2026** (from: skill-pack-propagation daily run, July 28, 2026 (verify_directory_and_somba.py))

### A checker with a literal in it eventually checks the wrong thing

The verifier written *this same run* failed twice against surfaces that were perfectly healthy:

1. It asserted the live bundle was `Sigrun-Agent-Pack-1.zip`. A second publish cycle two hours
   later made it `-2`, and the checker reported four failures on a correct set of pages.
2. It then checked every date against one constant, `Jul 28, 2026`. Three formats render across
   these surfaces — the directory abbreviates the month, the members' "Kept current" badge
   spells it out (`July 28, 2026`), and the top bar uses `28 Jul 2026`. One more false failure.

Both are the July 26 lesson ("verify the format each surface actually renders") arriving from a
new direction: the thing that went stale was the *verifier*, and a verifier does not get
verified by anything.

**Rules:**

1. **Derive expectations from the artifact of the run you are verifying** — read the upload
   manifest, the VERSION.txt, the config — never from a value you typed while writing the check.
2. **A checker that cries wolf is worse than no checker.** After two false alarms nobody reads
   the third, and the third is the real one. Treat a false failure as a P1 on the checker.
3. **Check per surface, not per system.** If two pages render a date differently, that is two
   checks. Collapsing them into one constant guarantees one of them is wrong.
4. **When a check fails, prove the SUBJECT is broken before you touch it.** Both failures here
   would have "fixed" a healthy page had the message been taken at face value.

Learned July 28, 2026.

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

<!-- learning:2026-07-28-in-the-catalogue-is-not-on-the-pipeline -->
**July 28, 2026** (from: skill-pack-propagation, Dennis asking "are we also propagating to sigrun.com?")

### Being in the catalogue is not being on the pipeline — and ownership is per FILE, not per folder

`sigrun.com/somba-agents/` had been on the published skill-pack directory since July 9, 2026.
It was on no pipeline at all. `harvest_learnings.py` excluded its source folder and
`propagate_all_packs.py` excluded its zip, both for the same stated reason: another job,
`somba-skill-weekly-update`, "owned" it.

That job does not own it in the sense that mattered. It **mirrors** the source folder
downstream into a member's copy and reports the diff. It never writes a lesson *into* the
source. So the source sat unchanged from June 28 to July 28 while the weekly report said, every
week, truthfully: *"No skills changed since last week — you're already on the latest."* Every
job green. Every claim true. The pack rotting anyway.

Meanwhile the sibling packs accumulated 71, 47 and 47 dated field lessons. That library had 1.

**Rules:**

1. **A pack in the catalogue is on the pipeline, or it is decoration.** When you add a
   location to a published directory, add it to the loop in the same change. If you cannot,
   the directory entry is a promise you are not keeping.
2. **Ownership is per FILE, not per folder.** "Another job owns that folder" is almost never
   true at file granularity. Write down which job owns which *file*: here, harvest owns
   `skills/*.md`, the pack's own builder owns the zip and the HTML, the mirror job owns the
   mirror. Three writers, zero collisions, and the exclusion was never needed.
3. **A mirror is not a source. Never write into a mirror** — the next mirror run overwrites you.
4. **Measure coverage on the FOLDER, not the note.** A per-note report cannot show a folder
   nobody is writing to; it has nothing to print. `harvest_learnings.py` now prints LEARNING
   COVERAGE per source folder every run and exits non-zero on `[STARVED]` — a folder inside
   the loop carrying zero lessons while its siblings carry dozens.
5. **When a report can only be green, it is not a check.** Any comparison of a thing against
   itself ("source vs. my snapshot of the source") reports health it cannot actually observe.
   Ask of every green line: *what state of the world would make this line say something else?*
   If you cannot name one, the line is decoration too.

Learned July 28, 2026.

<!-- learning:2026-07-28-joining-a-loop-means-inheriting-its-history -->
**July 28, 2026** (from: skill-pack-propagation daily run, July 28, 2026)

### Joining a loop means inheriting its history — backfill, don't start the clock at zero

When `Sigrun-SOMBA/skills` finally joined the learning loop, the obvious move was to add it to
the source list and let tomorrow's notes flow in. That would have been wrong in a quiet way: the
pack has existed for a month, its siblings each carry 47–71 dated field lessons, and it would
have started at 1. Members downloading it would get agents that had apparently never learned
anything — while the marketing claim on the page is precisely that these agents improve.

The fix was a `--replay-applied` mode: re-run every archived note against the current source
folders, guarded by the same `<!-- learning:ID -->` markers that make normal harvesting
idempotent, in date order, moving nothing. 42 archived notes → **51 lessons into 17 files**, in
one command, with zero risk to the folders that already had them.

**Rules:**

1. **A new member of a loop inherits the loop's history.** Design every append-only loop with a
   replay mode from the start; it costs a few lines because the marker guard already exists.
2. **Idempotent markers are what make replay safe.** If your appends are guarded by a stable ID,
   replay is free, re-runnable, and can be scoped to one target (`--dirs=`) without touching
   anything else.
3. **Archive, don't delete.** The replay was only possible because applied notes were kept in
   `applied/<date>/`. A processed-work archive is a rebuild capability, not clutter.
4. **A backfill is part of the onboarding, not a nice-to-have.** "Add it to the list" is half
   the change; the other half is making the new member indistinguishable from an old one.

Learned July 28, 2026.

<!-- learning:2026-07-28-a-passing-marker-check-can-ship-a-broken-page -->
**July 28, 2026** (from: sigrun-website-request-intake, first publish of jagodapasko.com, July 28, 2026)

On **July 28, 2026** the fleet publisher pushed a member's finished site to a new WordPress
install and reported a clean pass: 12 of 12 content and brand markers found, Person schema
present, WordPress starter content trashed. A screenshot taken thirty seconds later showed
a page nobody would call finished — the block theme printed its own `<h1>Home</h1>` above
the hero, and `main.is-layout-constrained.has-global-padding` had squeezed a full-bleed
design into a 645px column inside a 1717px viewport. Not one marker moved, because markers
are strings and none of them touch layout.

**A string check proves content arrived; it cannot prove content is readable.** So the
first publish to any new install gets a human-eye pass — screenshot the front page and each
subpage at desktop width before calling the job done. Automated verification stays, it just
stops being the last word.

Three concrete rules that came out of it:

1. Suppressing a block theme's header and footer with `:has()` is not enough. Also hide
   `.wp-block-post-title` and force the layout wrappers open, scoped to your own pages:
   `body:has(.SCOPE) .wp-site-blocks, body:has(.SCOPE) main, body:has(.SCOPE) main >
   .wp-block-group, body:has(.SCOPE) .entry-content { max-width:none!important;
   width:auto!important; margin-left:0!important; margin-right:0!important;
   padding-left:0!important; padding-right:0!important; }` plus `max-width:none!important`
   on their direct children.
2. Fix at the generator, never in the published HTML. The correction belongs in the build
   script so a re-run cannot regress it, then rebuild and republish.
3. Diff the client's supplied assets against what actually renders. Eight of her photos were
   uploaded and only six were placed; the other two surfaced by diffing the media list
   against the image references across all pages, and both were added. Make that diff part
   of the build rather than something a person notices later.

<!-- learning:2026-07-28-a-surface-with-no-checker-fails-quietly -->
**July 28, 2026** (from: skill-pack-propagation daily run, July 28, 2026)

On **July 28, 2026** `blitzmetrics.com/task-library-dashboard` served the previous day's
zip while every check in the pipeline reported green. Nothing was broken in the checkers —
the page simply had no checker. The verifier covered the directory and the member library
thoroughly and stopped there, so six plain surfaces and two payload pages were publishing
into a blind spot. The stale page was found only because a check was written that day for
an unrelated reason.

**Coverage is a property of the checked set, not of the checks.** A green run means "every
surface I look at is correct," which says nothing about surfaces nobody looks at. So audit
the *list*, not just the results: enumerate every surface the pipeline writes to, diff that
against the surfaces the verifiers read back, and treat any surface in the first list and
not the second as an open defect. Do this whenever a surface is added — the moment a page
joins the publish table it must join the verify table, in the same change.

Three properties that made the eventual checker trustworthy:
- **Read back anonymously, cache-busted.** Trusting the write path's own success report is
  what hid this; the POST silently 403'd. Assert against what the public actually receives.
- **Derive expectations from the run's artifacts**, never from literals — read the expected
  zip URL out of `_republish_urls_<date>.json` and the expected date from today. A checker
  with a hardcoded value drifts into crying wolf, then gets ignored.
- **Exit non-zero.** A verifier that prints a defect and returns 0 is a log entry, not a gate.

And when the fix lands, fix the *class*: patch the shared driver rather than the one page,
delete the one-off repair script so nobody runs it next week, and wire the new verifier into
the generated checklist so it runs every day without anyone remembering it. A repair that
lives only in today's session is a repair scheduled to be needed again.

<!-- learning:2026-07-28-a-user-agent-without-its-escort-is-still-a-robot -->
**July 28, 2026** (from: skill-pack-propagation daily run, July 28, 2026)

Sending a full Chrome User-Agent is necessary but no longer sufficient to get past a
Cloudflare-fronted WordPress site. On **July 28, 2026** the REST POST to
`blitzmetrics.com/task-library-dashboard` returned 403 with a "Just a moment..."
interstitial while the POST to `blitzmetrics.com/build-agents` — same site, same app
password, same full UA — returned 200. The obvious reads (expired app password, WAF
hates this page, transient rate limit) were all wrong.

Isolate before theorizing, and isolate with a **no-op probe**: POST the page's own
current content back to it, unchanged, so the request is real but the page cannot be
damaged. Run it twice each way. Result was deterministic — UA-only `403, 403`, full
browser header set `200, 200`. That rules out a cooldown, which a single retry never
can: a retry that succeeds after a pause is indistinguishable from a fix that works.

The rule: a browser UA arriving **without the headers a real browser sends beside it**
is itself a bot signature. Send the escort — `Accept`, `Accept-Language`, `sec-ch-ua`,
`sec-ch-ua-mobile`, `sec-ch-ua-platform`, `Sec-Fetch-Dest/Mode/Site`, plus `Origin` and
`Referer` on writes. Put them in one constant applied to *every* request, not to the one
page that failed; the next surface to trip the rule should cost nothing. In
`republish_daily.py` this is `BROWSER_HEADERS`.

Two corollaries worth carrying:
- **A 403 is not an authentication failure.** Verify auth with `GET /wp-json/wp/v2/users/me`
  before touching credentials. A working GET plus a failing POST means the body or the
  headers, never the password.
- **For uptime probing, a bot-shaped request can manufacture an outage.** A monitor that
  probes with a bare UA can collect 403s from a perfectly healthy site and report a
  fleet-wide failure. Probe with the same full header set, and treat a 403 carrying a
  challenge interstitial as *inconclusive* — never as down, never as up.

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

<!-- learning:2026-07-29-edit-the-generator-not-the-page -->
**July 29, 2026** (from: applying the SEO-tree block across 13 surfaces on 6 domains, July 29, 2026)

### Before editing any live page, ask what regenerates it

Twelve pages needed the same block. Two of them — `localservicespotlight.com/skill-packs/` and
`/asset-tracker/` — are rebuilt from scratch by their own Python generators on a schedule.
Editing those live would have looked like a clean success: HTTP 200, block in the rendered DOM,
verification green. The next scheduled rebuild would have erased it, silently, and the job that
erased it would still have reported success.

So the work split three ways and each page went through exactly one owner: generated pages got
the block added to their generator, plain pages through REST, base64 payload pages by decoding,
inserting, re-encoding. One owner per file, always.

**Rules:**

1. **Establish the owner before the edit.** Search the project for the page's slug. If a script
   writes it, that script is the only thing allowed to write it.
2. **Two writers on one artifact is a bug even when both succeed.** The loser is whoever ran
   first, and nobody finds out until a reader notices something missing weeks later.
3. **When a live page and a local template have drifted, do NOT "restore" from the template.**
   Our trunk page had picked up three hand-added blocks since its last build; republishing the
   template would have deleted all three. Diff first, then make surgical marker-guarded edits.
4. **Every surgical edit replaces exactly once and raises on zero matches.** A `sub_once()` that
   throws when its anchor is gone turns silent drift into a loud failure the same morning.
5. **Mark generated blocks with a data attribute, not a comment.** `data-system-tree="<node>"`
   survives every filter WordPress runs over content, and gives the checker something exact to
   assert and the updater something exact to replace.

Learned July 29, 2026.

<!-- learning:2026-07-29-daily-date-stamps-need-unconditional-rebuild -->
**July 29, 2026** (from: skill-pack-propagation daily run, July 29, 2026)

Gate a page builder on *content* change and its *date* stamps go stale silently. On July 29, 2026 the
pack propagation run finished with two red checks — `top-bar date is today` and `outer pill updated` on
the gated SOMBA library — while every zip, every download link and all eight plain surfaces went green.
Nothing was broken in the packs. The runbook said to run the page builder "only if the agent count
changed," but that builder is the sole writer of two DAILY stamps (the top-bar `29 Jul 2026` and the
`SKILL PACK UPDATED 29 JUL 2026` pill); the republish driver only ever bumps the footer badge. On any day
the count holds steady and the propagation job runs before the partner job, those two stamps keep
yesterday's date and the checks fail for surfaces this job does not own — which reads as someone else's
outage and gets waved through.

The rule: a conditional rebuild is only safe when the condition covers EVERY field the builder owns.
Enumerate them first. If a builder writes anything that changes on a clock rather than on content — a
date, a "last verified," a freshness pill — the gate must be unconditional, because time changes it every
day and no content diff will ever announce that. Fixed by making the builder step ALWAYS run and recording
in the checklist which fields it owns and which the republish driver owns, so the next run repairs the
cause instead of re-reporting the symptom.

Corollary worth keeping: when a check fails on a surface another job owns, that is still this run's
finding to chase to root cause. Two green re-runs four hours apart, with a partner job in between, is not
proof the pipeline is healthy — it is proof the ordering was lucky.

<!-- learning:2026-07-29-a-4735-byte-response-is-a-write-failure-not-a-waf -->
**July 29, 2026** (from: sigrun-website-request-intake daily run, July 29, 2026)

Check that your tool could WRITE its output before you diagnose the server. On July 28, 2026 a run
recorded a gotcha that read: "hammering a fleet site with rapid sequential curl calls trips the WAF into
serving a 4,735-byte stub with http 200 for every URL — it looks exactly like the site breaking." On July
29 the same signature appeared again: nine URLs on jagodapasko.com, every one `200 4735`, identical byte
count on pages that differ by 8,000 bytes. There is no WAF stub. `curl -o /tmp/pg.html` was writing to a
file left behind by an earlier session's sandbox, owned by `nobody:nogroup` and not writable by the
current user. curl aborts the transfer when the write fails and still reports `http_code 200` with a
truncated `size_download`. Reproduced deliberately: the same URL fetched to the stale path returned 4,735
bytes; fetched to a fresh `mktemp -d` path it returned 103,652. The 4,735 is a property of the local
filesystem, not of the remote host.

The rule: write every fetch into a directory you just created (`W=$(mktemp -d)`), never into a fixed
`/tmp/<name>` that a previous run or a previous session may own. When a response looks wrong, run
`ls -l` on the output path and compare `size_download` against `wc -c` of the file before forming any
theory about the server. Identical byte counts across URLs that should differ is the tell — real pages
are never the same size by accident.

The wider lesson is about what a gotcha costs when it is wrong. That note had already been carried into
the ledger as fleet behaviour, and it prescribed the exact wrong remedy — space the requests out and wait
— which would have made every future run slower while leaving the real cause in place. A diagnosis that
blames a remote system you cannot inspect should be held to a higher bar than one that blames your own
process: reproduce it deliberately, with a control, before writing it down as a standing fact. Corrected
here, and the superseded claim is named so nobody re-derives it.

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

<!-- learning:2026-07-30-nothing-to-harvest-is-not-nothing-to-propagate -->
**July 30, 2026** (from: skill-pack-propagation daily run, July 30, 2026)

A stage whose inputs have more than one writer must re-read them unconditionally. On July 30, 2026 the
harvest step printed `inbox empty - nothing to harvest.` and the propagate step in the SAME run found
**62 stale pack files** across 6 canonical skills. Both were correct. Four July 29 notes had been
harvested into the source skills by OTHER daily jobs — two at 05:03 and two at 15:44 — after this job's
last propagate at 04:41 and republish at 04:43. Yesterday's zips were built before those writes existed,
so every live surface served packs missing four learnings for up to 23 hours.

The tempting optimization is right there: the harvest found nothing, so skip the rebuild, it is a no-op.
It is not a no-op. `harvest_learnings.py` is one writer to the source skills, not the only one — every job
that files a learning also harvests it, and a human can edit a skill directly. Gate propagation on the
harvest's own output and those writes never reach a zip. Worse, the run stays green: the manifest is
rewritten from the same stale build it just compared against, so the next day's diff is clean too, and
the packs quietly converge on "consistently wrong." That is the June 10, 2026 incident class exactly —
QR-linked zips serving content nobody could see was old.

The rule: propagate must diff against the SOURCE FILES, never against whether this job's harvest did
anything. Generalising yesterday's builder lesson one level up — a conditional is only safe when the
condition observes every input the step consumes; if any input has a writer outside this job's control,
there is no safe condition and the step runs every time.

Two things that make this checkable instead of theoretical. `Skill-Learnings/applied/**` mtimes are the
ground truth for when a learning actually reached the source skills: compare them against the previous
run's propagate timestamp and you know exactly what today's run is carrying and what yesterday's missed
— evidence a content hash gives you as a number but not as a story. And when a run reports changes it
cannot explain from its own actions, that gap is the finding: the first read of 62-updated-with-0-harvested
looked like a self-perpetuating date diff — a script re-stamping files it just wrote, manufacturing work
forever. Ruling that out took one check (source mtimes were untouched at 07-29 15:45, so the script was
not rewriting them) and one diff against a correct baseline. Diffing yesterday's `_pack-backups-*/*.bak`
was the wrong baseline and nearly sold the wrong story: those backups are taken at the START of a run, so
they hold the day-BEFORE content and will always show a day's learnings as "new." Compare against what the
last run PUBLISHED, not against what it saved before overwriting.

<!-- learning:2026-07-31-a-learning-written-is-not-a-runner-fixed -->
**July 31, 2026** (from: skill-pack-propagation daily run, July 31, 2026)

Writing the fix down is not shipping the fix. On July 29, 2026 this pipeline diagnosed a real defect
correctly — the SOMBA library builder was gated on "did the agent count change," but it is the sole
writer of two CLOCK stamps (the top-bar `31 Jul 2026` and the outer `SKILL PACK UPDATED` pill), so on
any steady-count day both went stale and the verifier went red for surfaces this job does not own. The
learning note said "Fixed by making the builder step ALWAYS run." The daily checklist said the same.
Two days later, on July 31, 2026, `run_skill_pack_propagation.sh` still carried the original
`if [ "$SOMBA_N" != "$LAST_N" ]` gate, untouched since July 28. The same audit found the runner called
one of three verifiers while the checklist had said "all three verifiers, every run" since July 29.

Both surfaces of the loop were honest. The prose was right, the runner was wrong, and nothing compared
them — because the artifacts that carry a fix are different objects: the learning note, the generated
checklist, the README, and the executable. A change lands in whichever one you had open.

The rule: when a run diagnoses a defect, name the EXECUTABLE that must change and confirm the edit in
that file before the note is filed — `grep` the old condition and prove it is gone. "Documented" and
"fixed" are separate states; a note in the past tense about a script you did not edit is a false
report that will read as green forever. Corollary: when a runbook and a runner disagree, the runner is
what actually executes — treat the divergence itself as the P1, not the drift it happened to cause.

Fixed July 31, 2026: the gate is out (the builder runs unconditionally, logging whether the count moved),
`verify_pack_surfaces.py` and `System-Hub/verify_link_graph.py` were added as steps 7 and 8, the step
labels renumbered 1/8..8/8, and Skill-Pack-Directory/README.md rewritten to match. All three verifiers
ran green afterward, including the two SOMBA checks that were red on July 29.

<!-- learning:2026-07-31-an-unknown-flag-is-not-a-no-op -->
**July 31, 2026** (from: skill-pack-propagation daily run, July 31, 2026)

`--help` is not a safe probe. On July 31, 2026, mid-run, `python3 harvest_learnings.py --help` was
typed to check the script's interface before filing a note. The script read only the three flags it
knew (`--dry-run`, `--replay-applied`, `--dirs=`) and silently ignored the rest, so `--help` fell
through to the default action and performed a real harvest: eight source skill files rewritten, the
inbox emptied, and the published packs instantly one revision behind their own sources. Nothing
errored. The output looked exactly like a successful intentional run, and the only reason the
divergence did not ship was that the operator recognised it in the log.

The general shape: a script that MUTATES state and treats an unrecognised argument as "proceed with
the default" has inverted its own safety. Someone typing a flag the script does not know is, by
definition, unsure what it does — that is the worst possible moment to run the destructive path.
Argument parsing that only whitelists is not parsing; it is a filter with a trapdoor underneath.

The rule: every state-changing script exits non-zero on an unrecognised argument and ships a `--help`
that prints and exits 0. Never probe an unfamiliar script by guessing a flag — read its argv handling
first, or run it with the flag it documents for dry runs. Where a `--dry-run` exists, it is the probe.

Corollary on recovery: when an accidental write does happen, finish the loop rather than unwinding it.
Reverting eight source files would have left the applied/ ledger, the manifests and the live packs in
three different states; re-running propagate + republish took four minutes and left every artifact
consistent, with the lesson genuinely carried into all 13 packs.

Fixed July 31, 2026: harvest_learnings.py now rejects unknown arguments with exit 2 and prints usage
on --help/-h/help, verified against --help (exit 0), --bogus (exit 2), --dry-run and a bare run.

<!-- learning:2026-08-01-a-mirror-on-a-slower-clock-is-a-fork -->
**August 1, 2026** (from: skill-pack-propagation — root-causing the "don't touch SOMBA" note, August 1, 2026)

Ownership is per-FILE, never per-folder — and a rule written about a folder starves what it was
meant to protect. The daily pack job carried a standing instruction: "Do NOT touch SOMBA/Dorine
packs." On July 28, 2026 `Sigrun-SOMBA/skills` deliberately joined the daily learning loop, and the
same job took over its lessons, its mandated skills, its bundle build and its live library page. The
instruction was never updated. From then on every run had to reason its way past its own prompt to
do its actual work — and the reasoning had to be redone from scratch each morning, because nothing
recorded the conclusion.

Worse, the one folder the rule really did protect went stale under it. Dorine's pack MIRRORS
`Sigrun-SOMBA/skills` and was refreshed weekly, by a job whose checker compares the source against
its own last snapshot. Once the source moved to a daily beat, weekly checking could not keep up, and
because the comparison never involves the clock, the Monday report said "no skills changed since
last week — you're already on the latest" while being five days behind. Measured August 1, 2026:
2 skills missing, 13 of 17 stale, under a clean report.

The general shape: **a mirror on a slower cadence than its source is not a mirror, it is a fork.**
The moment you put a folder on a faster loop, enumerate everything downstream of it and move those
to the same beat — or the downstream copy silently becomes a different product with the same name.
And any freshness check that compares a copy against its own previous snapshot can only ever detect
what it already looked at; it must be checked against the SOURCE, by hash, every run.

The fix that generalizes: a blanket "don't touch X" is a smell. Replace it with a table naming the
single writer of each file, and let every job read from anything while writing only its own rows.
Ownership expressed as folders collides with reality the first time two jobs legitimately need
different files in the same directory — and the usual resolution is that one of them stops running.

Fixed August 1, 2026: `propagate_all_packs.py` grew a third pack kind, MIRROR_PACKS — it calls the
mirror's OWN refresher on the daily beat (so the writer never changes, only the cadence) and then
hash-checks the mirror against its source, printing `[DRIFT]` and failing the run if the refresher
ran and the mirror is still behind. The prompts on both sides now carry the per-file table instead
of the blanket rule.

<!-- learning:2026-08-01-test-the-failure-path-or-it-is-decoration -->
**August 1, 2026** (from: skill-pack-propagation — auditing run_skill_pack_propagation.sh, August 1, 2026)

Every failure guard in the daily runner was dead for four days and nothing noticed, because a
broken failure path is invisible on days when nothing fails.

The runner guarded each step as `cmd 2>&1 | tee -a "$LOG" || { say "STEP FAILED"; exit N; }`. In a
shell pipeline `||` tests the LAST command — `tee` — and `tee` effectively never fails. So from the
day the runner was written (July 28, 2026) to August 1, a failing propagate, republish, directory
publish or verifier printed its error into the log and the run carried straight on to `=== DONE ===`
and exited 0. Six guards, all inert. Only step 1 was correct, and only because it happened to
capture `${pipestatus[1]}` into a variable for a different reason.

Demonstrated rather than reasoned about: a two-line script running `python3 -c "sys.exit(7)" | tee`
under the same idiom printed "GUARD DID NOT FIRE" and exited 0. Ten seconds of proof beats any
amount of reading the line and believing it.

The general rule: **an error path that has never been executed is not error handling, it is
decoration.** Whenever you write "and if this fails, stop" — make it fail once, on purpose, and
watch it stop. This applies to a shell guard, an exception handler, an alert threshold, a retry
limit, and a verifier's non-zero exit. The happy path gets exercised every single run; the failure
path only gets exercised the day it matters, which is the worst day to discover it never worked.

Two corollaries found in the same audit:
- A status a script only PRINTS is a status nothing acts on. `propagate_all_packs.py` had statuses
  for MISSING and BUILDFAIL that appeared in its report and never touched its exit code, so the
  caller branching on that exit code could not see them. Report AND return.
- `${pipestatus[N]}` must be captured on the very next statement — any intervening command resets
  it. That fragility is why the fix is a `run()` function rather than an idiom copied per step.

Fixed August 1, 2026: `run_skill_pack_propagation.sh` now routes every step through
`run <exit-code> <message> <command...>`, which branches on `${pipestatus[1]}`; `propagate_all_packs.py`
exits 1 on any MISSING / BUILDFAIL / MIRRORFAIL / DRIFT; and `build_skillpacks_index.py --publish`
exits 1 when the publish call actually fails instead of printing "PUBLISH FAIL" and exiting 0.
Verified by forcing a mid-pipeline failure and confirming the run stopped with the right code.

<!-- learning:2026-08-01-a-resolved-flag-must-be-retired-at-the-source -->
**August 1, 2026** (from: grokipedia-readiness)

**August 1, 2026** (from: grokipedia-readiness)

When research clears a warning, retire the warning where it lives. A resolution written somewhere
else is a second opinion, and the code keeps reading the first one.

On June 30 the Wikidata triage filed Claudia Witticke as a namesake trap: `Q133434182` looked like
a near-empty "seamstress" stub that could not be confirmed as hers. On July 27 a rotation check
disproved it — following the item's `GND 1268215171` to the DNB record gives *Witticke, Claudia /
Land Italien / Beruf Näherin / Gründerin von "Leidenschaft Nähen"*, and "Leidenschaft Nähen" is
the exact brand on her own domain. The rotation wrote that up correctly and promoted her to
tier A. It did not delete the trap entry.

So for five weeks the same file asserted both things at once, and the engine believed the older
one. The cost was not cosmetic:

- identity scored 14/20 instead of 20/20, dropping her from **92.4 to 86.4**
- she carried a `namesake-collision` flag, which under the standing *disambiguate or don't* rule
  meant the monthly drip would skip her — indefinitely, and for a reason that had already been
  disproved

A stale warning is worse than a missing one, because it is load-bearing. Nobody re-examines a
member the file says is unsafe to touch.

Two fixes, and the second is the one that generalises:

1. Retire the entry at the source. Move it to a `namesake_resolved` key with the evidence and the
   date, so the history survives without the live list lying.
2. Make the contradiction self-detecting. A trap says "the only match for this name is someone
   else"; a tier-A entry says "this member has an item". If both name the **same qid**, they cannot
   both be true. The engine now resolves that in favour of the newer evidence, prints
   `[STALE-TRAP]`, and a unit test fails until the underlying file is cleaned.

The general rule: when two records in one system disagree about the same identifier, that is a
detectable condition, not a judgement call. Write the check. Silent contradictions get obeyed by
whichever code path happens to read first, and the loudest possible failure is cheaper than a
member who quietly never ships.

A corollary found in the same file: the rotation note also recorded that the roster's niche and
country for her were wrong ("Style / image coaching, AT" for a sewing author in South Tyrol,
Italy). That was flagged and not actioned either — and it would have shipped a false claim about a
real person into an encyclopedia. **A note that says "X is wrong and should be corrected" is not a
correction.** Either fix it in the same run or file it where something will fail until it is fixed.

<!-- learning:2026-08-01-confirmation-screen-is-not-confirmation -->
**August 1, 2026** (from: grokipedia-readiness)

**August 1, 2026** (from: grokipedia-readiness)

A confirmation screen is a rendering decision. It is not evidence that the write happened.
When a submission matters, read the response the server actually sent.

Grokipedia's Suggest-Article modal has two failure modes that look identical on screen:

| What happened | What the screen showed |
|---|---|
| Rate-limited, nothing created | modal clears, empty form, no error |
| Submitted successfully | modal clears, empty form, no error |
| Submitted successfully | "Thank you!" screen |

The July 4 run recorded that exceeding the rate limit returns a visible
`Rate limit exceeded: max 1 requests per 600 seconds`. On August 1 it returned nothing at all —
the form just reset. So the note that was written to prevent a misdiagnosis became the cause of
one: the first Witticke attempt looked exactly like the successful Nichterl attempt that preceded
it, except Nichterl had shown the Thank-you screen and Witticke had not.

Guessing in either direction is expensive. Assume failure and you re-submit, and duplicates are
the one thing this job must not produce — the July run already left two identical
`Annelie Salminen (writer)` rows in the activity log. Assume success and the member silently never
gets submitted at all, and nobody notices until the next monthly run.

The resolution is to stop reading the UI. Wrap `window.fetch` before clicking Submit and capture
the POST body:

```js
if (!window.__hooked) {
  window.__cap = []; const of = window.fetch;
  window.fetch = async function (...a) {
    const r = await of.apply(this, a);
    if ((a[1] && a[1].method) === 'POST') {
      const c = r.clone(); window.__cap.push({ s: r.status, b: (await c.text()).slice(0, 300) });
    }
    return r;
  };
  window.__hooked = 1;
}
```

`{"success":true,"id":"<uuid>"}` is the fact. Everything else is decoration. Attempts 1 and 2
produced no POST at all; attempt 3 returned success and the Article Requests counter moved
106 → 107 with exactly one new row.

Two general rules fall out of this:

1. **Verify a write at the layer that performed it**, not the layer that reports it. This is the
   same shape as the Elementor lesson (a 200 on the REST write is not a live render) and the
   scheduled-task lesson (a draft is not staged until a re-fetch confirms it).
2. **A documented gotcha has a shelf life.** It describes a third-party system on the day it was
   written. When a run's behaviour contradicts the note, the note is the thing to re-check first —
   and then to correct in place, so the next run inherits the truth rather than the fossil.

<!-- learning:2026-08-01-numbers-about-artifacts-must-be-derived-everywhere -->
**August 1, 2026** (from: monthly-agent-library-refresh)

**August 1, 2026** (from: monthly-agent-library-refresh)

When you make a number derive itself from the artifact, apply the fix to **every surface that
prints that number**, not just the one where you noticed it.

On July 28, 2026 the Skill Pack directory's counts were made derived-from-the-zip, because it
advertised "18 skills" for a 19-skill download. That fix was correct and it was applied to the
directory alone. Four days later every *other* surface was still printing hand-typed counts frozen
at whatever the pack held the day someone wrote them:

| Surface | Printed | Zip shipped |
|---|---|---|
| /dealcon | 10 skills | 19 |
| task-library-dashboard | 239 skills | 247 |
| build-agents | 239 skills | 247 |

Three of three. The DealCon page had been offering ten skills for a nineteen-skill pack — the nine
added since were invisible to anyone deciding whether to install it.

The fix is `bump_counts()` in `pack_republish_lib.py`, wired into the daily republish so every
button is rewritten from its own pack's `VERSION.txt` before publishing. `n=None` (unreadable zip)
is a no-op, never a zero, and the unit word is preserved so "agents" does not become "skills".

**Rule:** after fixing a class of defect, grep for every other place the same class can live before
closing it out. A generator fix that lands on one of five surfaces is a fix that will be rediscovered.

---

Also learned this run, same family:

**A "Kept current" label near a date makes that date live.** The backlink added to two pages read
"How this page is kept current. The August 1, 2026 refresh found…" — a historical statement. But
`DATE_PAT` matches the lowercase label too, so the daily job would have rewritten that date every
morning and the sentence would have claimed a different refresh date each day. Caught by running
the job's own `inspect` after editing and seeing two BADGE-DATE hits where there should be one, then
simulating tomorrow's stamp against live content to prove the historical date held.

**Rule:** never put the words "kept current" or "last updated" within ~80 characters of a date you
intend to stay fixed. After adding prose containing a date to a surface a dated job owns, run that
job's inspect and simulate the next run before walking away.

<!-- learning:2026-08-01-a-guard-that-names-one-spelling-catches-one-spelling -->
**August 1, 2026** (from: skill-pack-propagation)

**August 1, 2026** (from: skill-pack-propagation)

When you write a guard against a mistake, guard the **class** of mistake. A guard that
hard-codes the one instance you saw catches that instance and nothing else — and it is worse
than no guard, because its existence is why nobody looks again.

On July 19, 2026 a note used `target:` where the field is `skills:`, so the harvester grew a
check that rejected `target:` with a helpful message. On August 1 three notes arrived from two
unrelated jobs (grokipedia-readiness ×2, monthly-agent-library-refresh ×1) using **`targets:`**
— plural — as a YAML block list. Every one walked straight past a guard written for the
singular and landed on the generic `missing 'skills:' in front-matter`.

That error is the most misleading one the harvester can produce: it tells you to add a field
that is plainly there in the file. Three correct lessons sat unharvested behind a message that
sent you looking for the wrong problem, and one had additionally been filed outside `inbox/`
where nothing would ever pick it up.

There was a second, deeper bug underneath, and it is the more general one. The front-matter
parser kept only lines containing `:`. A block list —

    skills:
      - boil-the-ocean

— gives the key an EMPTY value and then drops the item lines entirely, because a list item has
no colon. **A parser that filters lines by a delimiter silently discards every structure whose
continuation lines lack that delimiter.** It does not error. It just quietly returns less than
the file said.

What was changed:

- Block lists parse, under `skills:` or any alias, terminated by the next key.
- The alias set is the family, not the instance: `targets`, `target`, `skill`, `skill-slugs`,
  `skill_slugs`. A real `skills:` always wins.
- Slugs written as filenames (`boil-the-ocean.md`) have the `.md` stripped — that is how people
  naturally write them, because it is what they were looking at when they wrote the note.
- Aliases are now **accepted and reported** (`[FORMAT]` naming the file), not rejected.
  Rejecting was the wrong trade: it stalls a correct lesson at the door over the name of its
  envelope, and the whole point of the queue metric is that lessons must not sit. **Loud and
  applied beats clean and stuck.** The note still gets fixed, because the line names the file.

The line to hold: accepting a *format* variant is not the same as guessing at a *target*. A
slug matching no source file still stays in the inbox and is still reported — one of these
three named `wikidata-notability`, which exists nowhere, and the right destination
(`knowledge-panel-entity-seo`) was established by opening the candidate files and finding
namesake/Wikidata handling in them, not by picking the nearest-looking name.

**Test the matrix, not the case.** The fix shipped with 16 rows covering every way a note has
been or could plausibly be written — and, deliberately, the four inline forms that already
worked, because the failure mode of a parser rewrite is breaking what it used to handle.

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

<!-- learning:2026-08-01-derive-the-list-dont-maintain-it -->
**August 1, 2026** (from: agent-runtime cloud mirror — why two weeks of work never reached it)

A hand-written list of what to copy drifts from the thing it describes, and the drift is
invisible until something downstream tries to run.

The cloud runtime mirror is built by a script with an allowlist: these directories, these
root files. The list was written from memory on July 17. It omitted the daily job's entry
point and the entire Skill-Learnings folder — the write-back half of the self-improvement
loop. The mirror synced cleanly, reported success, and was committed and pushed. Nothing
was wrong with the sync. The list was wrong, and a list cannot notice that it is wrong.

Nobody would have found it by reading. It surfaces the first time a cloud agent clones the
repo and the run dies on a missing file — which is the worst possible moment, because by
then the whole point of the exercise is to trust the thing.

The fix is not a better list or a more careful reviewer. It is to stop maintaining a list:
derive what's required from the code that requires it. A test now reads the runner and pulls
out every script it invokes, reads the propagator and pulls out every pack zip, source pack,
mirror pack and builder, reads the harvest script and pulls out every source folder — then
asserts each one is present. Add a pack tomorrow and the test starts demanding it, with no
one remembering to update anything.

**Any list that must be kept in sync with code by hand is a bug waiting for a bad day.**
Where a list already exists — mandated skills, published surfaces, pack sources, sync
allowlists, verifier rosters — ask whether it can be computed from the thing it mirrors.
If it can, compute it. If it genuinely cannot, write a test that fails when the two diverge.
Prefer the derivation; a test is the fallback, not the goal.

That test paid for itself on its first run. It found that the mirror-sync step invoked its
script by a path that only exists when the job runs from the project folder — so running the
job inside the cloud runtime, which is the entire purpose of the migration, would have failed
on the very step added to make cloud runs possible. Detected and skipped now, in the same
change that added the test.

Corollary, learned the same day: exclusion lists rot the same way. The mirror excluded
secrets by FILENAME — a list of the places someone thought to worry about. Four live client
credentials sat in places nobody had listed (a file called auth.txt, two hardcoded scripts,
a run log) and were pushed to a shared repo. The replacement reads file CONTENT. Same shape
of lesson: enumerate the property, not the instances.

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

<!-- learning:2026-08-01-retry-every-caller-not-the-one-that-failed -->
**August 1, 2026** (from: skill-pack-propagation)

**August 1, 2026** (from: skill-pack-propagation)

A network call with no retry is a coin flip you take once per item. Put it in a loop over 19
items and you have not written a 19-item job, you have written a job that fails whenever the
worst of 19 flips comes up tails.

The SOMBA library rebuild died twice this morning with `TimeoutError: The read operation timed
out` on a WordPress REST POST — once at agent 13, once at agent 6. **Different agent each time
is the signature that matters.** A deterministic bug fails at the same place; a moving failure
point is the network, and the fix is not in the page that happened to be in flight.

The cost was wildly out of proportion to the cause. That script is the sole writer of the two
DAILY clock stamps on /somba-agents/, so one dropped TCP read at agent 6 of 19 meant: the
library page kept yesterday's date, the run exited 31 before publishing anything, and the next
verifier would have gone red on a surface that was entirely healthy — which reads like someone
else's outage and gets waved through.

Two things to copy:

1. **Harden every caller in the pipeline, not the one that failed.** After fixing the SOMBA
   script I checked the step-4 driver `republish_daily.py` and found the identical hole:
   `HTTPError` was caught and returned, but `TimeoutError`/`URLError` propagated and would have
   taken down all ten surfaces. It makes an order of magnitude more calls than the script that
   actually broke — including multi-MB zip uploads on 180-second timeouts — so it was always
   the likelier victim. **The component that failed first is rarely the most exposed; it is
   just the one that got unlucky first.** Grep the whole pipeline for the same call shape.

2. **Retry the transient, never the refusal.** 5xx and 429 get retried; 4xx is returned
   immediately. A bad app password fails identically four times in a row — retrying it only
   makes the truth arrive slower. `HTTPError` subclasses `URLError`, so it must be caught
   FIRST or every 401 gets retried as if it were a dropped connection.

Two constraints worth stating because they decide whether retrying is even legal:

- **Idempotency is what buys you the retry.** These POSTs set page content to a fixed computed
  value, so a re-send converges — and a read that timed out may well have SUCCEEDED server-side
  anyway. Media uploads are the one non-idempotent call; retrying can leave a duplicate, which
  is acceptable here only because the design already tolerates it (WP suffixes -1/-2 and every
  caller uses the returned `source_url`). Check that before adding a retry, don't assume it.
- **Print every retry.** A silent retry turns a degrading endpoint into an invisible one — the
  run goes green for weeks while the link rots. The log line is what tells you the network is
  getting worse before it starts costing you runs.

Verified in production the same run: `[retry 1/3] POST pages/21053: TimeoutError ... retrying
in 2s`, then the rebuild carried on and all 19 agents published. That was the third abort of the
morning, absorbed.

**And test the retry by making it retry.** Both fixes shipped with a unit test that injects
`TimeoutError`, a 502, a 429 and a 401 into a fake `urlopen` — 7/7 and 9/9. A retry wrapper
that has never actually been made to retry is decoration, and the branch you never execute is
the branch that is wrong. The `republish_daily` test pins the `(status, body)` contract too,
because a rewrite that quietly starts raising where callers expect a return value is a worse
bug than the one being fixed.

<!-- learning:2026-08-02-a-blip-that-impersonates-a-dead-credential -->
**August 2, 2026** (from: git.adectra.com denying a token that worked minutes earlier, twice, in both directions)

An intermittent failure that reports itself as a permanent one will get you to fix the
wrong thing, loudly, in front of other people.

The agent-runtime token authenticated a push at 23:15 and was refused at 23:40 with
`HTTP Basic: Access denied ... incorrect, expired, or improperly scoped`. That reads as
final. I bisected it properly — a stub returning that token unconditionally failed the
same way, and the other token succeeded against the other repo from the same machine
seconds later, so it was not the code, the network or the IP — and concluded the token had
been revoked server-side. An email was drafted asking Daniel to reissue it.

At 01:00 the same token worked. Nothing had changed. Twenty minutes after that, inside a
single script, `git fetch` was denied and `git push` authenticated — same token, same
directory, seconds apart.

The bisect was not wrong. The hypotheses it eliminated stayed eliminated. What it lacked
was the axis I never varied: **time**. Every branch I tested was "which credential", none
was "does this reproduce".

**Before concluding a credential is dead, retry it later.** A single failed authentication
is evidence about that request, not about the credential. Two failures a minute apart are
still one sample of the server's mood. Vary time before you vary anything else — it is the
cheapest axis and the one most likely to be the answer for anything crossing a network.

Two things changed as a result.

The nightly job's push to the ledger now retries five times with backoff, and only calls it
a failure when the error text is NOT one of the transient shapes (`HTTP Basic: Access
denied`, `Could not resolve`, `Connection reset`, `timed out`). Before this, one blip at
4:33am would have failed the run and left the audit ledger a day behind, with an alert
saying the token was expired. **A scheduled job that talks to a network without a retry is
a job that reports other people's outages as your bugs.**

And a rule about probing: I had just hammered six nonexistent project paths in a loop to
find the right one, twice each. Whether or not that tripped a throttle, it is the correct
suspect and it was free to avoid. **Probing with a credential is not free.** Enumerate
candidates from what you know, not by asking the server twelve times.

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

<!-- learning:2026-08-02-the-filter-excluded-the-people-who-had-to-test-it -->
**August 2, 2026** (from: SOMBA team dashboards — three weeks of "it doesn't work" was one filter clause)

A filter written for the common case silently removes the people who most need the thing,
and a bug hidden inside encrypted output is invisible to every check that reads the output.

Two defects, same afternoon, both in the SOMBA member dashboards, both the reason Sigrun's
team spent three weeks reporting things that "didn't work."

**1. The filter that excluded its own testers.** `dash.py` built the dashboard payload from
`role == "client"`. Reasonable on its face — the dashboards are for the 100 paying members.
But the mentors (role=team) and Sigrun (role=benchmark) are exactly the people who have to
SEE a student's dashboard to teach and support it, and the filter left them out of the
payload entirely, so there was no page to open and no token to mint. The team could only
ever be handed a PDF. Ina asked for "the same experience our students get" four times across
two weeks; the answer was one clause. **When you filter to the majority case, ask who is in
the minority and whether they are the ones who most need in.** The people who test, support,
demo, or audit a thing are almost never in its main audience, and a role filter drops them
without a word.

**2. The bug you cannot grep for.** Every one of ~100 personal dashboards had shown a dead
"your audit PDF" button since 20 July. It survived that long because the dashboard page is
served as AES-encrypted ciphertext — the whole point of the design — so a `grep` of the live
page, an anonymous fetch, even the publisher's own "no @@PDF left" assertion all saw nothing
wrong: the publisher resolved the placeholder, but the *encrypted* build read the template
raw and sealed the placeholder inside the ciphertext. It was found only by decrypting a
member's vault entry with that member's real token — i.e. by looking from the consumer's
side, not the producer's. **When output is encrypted, minified, or otherwise opaque, no
producer-side check can see a defect in it. Verify from where the user stands: decrypt it,
render it, click it.** Two consumers of one templated file, and only one of them resolved
the template — the classic shape (same as the git-askpass dispatcher the day before): a
second code path that was supposed to mirror the first, quietly didn't.

The general rule under both: **verify a thing the way its user meets it, not the way you
built it.** A build-side "looks fine" is worth very little when the audience, the encryption,
or a second code path sits between your check and their experience.

<!-- learning:2026-08-02-the-prompt-does-not-carry-the-path -->
**August 2, 2026** (from: git_askpass.py picking the wrong GitLab token, and blaming the man who sent it)

A dispatcher whose match never fires does not raise an error. It quietly takes the other
branch, and the failure surfaces somewhere that blames an innocent party.

We hold two GitLab project access tokens. `git_askpass.py` chose between them by sniffing
the prompt string git passes it:

    key = "dennis_os_token" if "dennis-os" in PROMPT else "agent_runtime_token"

That first branch can never fire. Git's askpass prompt is `Password for
'https://oauth2@git.adectra.com'` — the host, never the project path. So every repository
silently received the agent-runtime token, and because these are PROJECT tokens, the wrong
one is not "less privileged", it is a hard 403:

    remote: HTTP Basic: Access denied ... the token was either incorrect, expired,
    or improperly scoped

Read that message with the wrong-token hypothesis in hand and it is obvious. Read it cold
and it says the token is bad. Two sentences were already drafted to Daniel telling him the
token he sent did not work, and a paragraph of this file's ancestor claimed the dennis-os
project had never been created. Both were false. The project existed; the token was fine.

It took ninety seconds to prove: run `ls-remote` with a stub that unconditionally returns
the dennis-os token. Reachable, first try. That single bisect is the whole lesson.

**When you dispatch on a string, verify what is actually in the string** — not what the
API's name suggests is in it. Print it once. A dispatcher with one input has one way to be
wrong and no way to notice. The fix takes every source that could name the target: an
explicit env override, then the repo's own `remote.origin.url` (`git config` needs no auth,
so no recursion), then the prompt, then the working directory. Any one naming the project
is enough.

**Corollary, and the expensive half: an authentication error tells you the credential
presented was wrong, not that the credential you meant to present was wrong.** Before
escalating a 401 or 403 to a human — especially a human who did you a favour — prove which
credential actually went over the wire. The failure was ours; the email would have made it
theirs.

Same shape as the dead `cmd | tee || exit N` guards found the day before: control flow that
reads correct, tests something else, and fails open. Both were found by running the failure
path instead of reading it. The family resemblance is the point — when a check exists, ask
what it is actually checking, not what it is named after.

<!-- learning:2026-08-02-we-believed-our-output-over-the-humans-it-described -->
**August 2, 2026** (from: SOMBA audit covers — three members said the tagline was wrong and we assumed they were)

When the subject of a generated document says it is wrong about them, they are the authority.
We are not.

The audit cover carries one sentence in the member's own voice, under their photo: the most
authoritative line in an eleven-page document about a real person. It was produced by matching
keywords in their stated niche against 29 pre-written positioning templates, first regex wins.
It matched on fragments of words:

- "personal auth**or**ity" contains "author" → an executive coach was told she helps people
  finish a book. She checked, found the phrase existed nowhere in her real online presence,
  and concluded we had invented it. She was exactly right.
- "community **build**er" → a coworking founder was told he serves families renovating houses.
  "I have not met any human who thought I was in the family house business."
- "copy**writ**er" → a copywriter for solo entrepreneurs got the book-coach line too.
- And **27 of 104** matched nothing and were shown the unfilled template itself, verbatim:
  "Helping your ideal client a specific, nameable result."

The technical defects are ordinary — missing word boundaries, and no guard on the no-match
branch. What matters is the response. Members raised this in the first workshop. The team's
recorded reading was that the member had "misled the agent with her own internet presence."
That is the failure worth keeping: **a confident generated artifact was treated as evidence
about a person, and the person was treated as mistaken about themselves.** It took a
five-minute grep to show who was right, and nobody ran it for weeks, because the output looked
finished and finished things do not get questioned.

Three rules out of it.

**The subject outranks the artifact.** If someone says a document describes them wrongly,
that is a bug report from the only person with ground truth. Reproduce it before explaining
it away — and never write the explanation into a client thread first.

**Never render an inference in the subject's own voice.** The archetype line was genuinely
useful; it is still there, in the card explicitly labelled "a sharper version to try." A guess
presented as a suggestion invites a conversation. The same guess printed as a mission statement
under someone's photo is just a false claim about them. The label is not decoration — it is the
entire difference.

**A fallback that reads like prose will ship as prose.** "Helping your ideal client a specific,
nameable result" is a fill-in-the-blank, but it is shaped like a sentence, so it slid onto 27
covers and through every review. Make unfilled states impossible to mistake for filled ones, or
assert nothing at all — the cover now prints the member's own words, and a test fails the build
if an invented or unfilled line ever reaches an audit again.

<!-- learning:2026-08-02-a-count-in-a-second-place-is-a-second-source-of-truth -->
**August 2, 2026** (from: skill-pack-propagation daily run — evidence-verification joined MANDATED and three separate scripts disagreed about how many agents exist)

### A count written in a second place is a second source of truth, and it will be wrong on exactly the day something changes

`evidence-verification` was added to the MANDATED tier. Propagation put it into every pack
correctly. Then three scripts, none of which had changed, each broke in a different way —
because each of them stored its own idea of how many agents there are.

1. **`build_agent_pages.py`** had a two-way coverage gate added on 2026-07-28. It fired
   correctly: `FATAL: skills/ contains ['evidence-verification'] but order does not list them`.
   This is the gate working. It cost one run and told me exactly what to edit.
2. **`build_agents.py`** had no such gate. It built the member bundle from its own `ORDER`
   list, quietly produced **19 agents out of 20**, and exited 0. No error, no install zip, no
   hub card. The new skill would have been absent from the file members actually download,
   and nothing anywhere would have said so.
3. **`verify_directory_and_somba.py`** hardcoded `19` in seven assertions and `18` in two
   more. Once the pack correctly became 20, the verifier reported **7 failures against
   healthy surfaces**.

Three failures, one cause. The number of agents was written down in four places and derived
in none.

**What makes #3 the worst one:** that file already carried a comment, written after an
earlier incident, saying *"A checker with a literal in it eventually checks the wrong thing —
and a checker that cries wolf is worse than no checker."* The lesson had been learned, written
down, and applied to the bundle URL in the same file — and then the next set of assertions
was written with literals anyway. **A principle documented in a file is not a principle
enforced by that file.** The comment sat four lines above nine hardcoded numbers.

**What makes #2 the most dangerous:** it is the silent one. #1 and #3 announced themselves.
#2 shipped a wrong artifact and reported success. A missing item is invisible by construction
— you cannot notice the absence of a thing you never listed — so the *only* place it can be
caught is a check that compares what exists against what was declared, in both directions.
`build_agent_pages.py` grew that check on 2026-07-28; `build_agents.py`, its sibling reading
the same folder for the same purpose, never got it. **When you add a coverage gate, add it to
every script that reads that source, not just the one that failed today.**

**Fixed at the source, this run:**
- Registered `evidence-verification` in all five structures in `build_agents.py`
  (ORDER/TITLE/JOB/USE/NEW_ON), all four in `build_agent_pages.py`
  (order/NEW_CARD_COPY/BOOTSTRAP_LINES/BADGES), and META in `build_agent_catalog.py`.
- Added the two-way orphan gate to `build_agents.py`, and proved it by planting a fake
  orphan skill and confirming the build refused to run.
- Rewrote the verifier to derive `N_AGENTS`, `N_NUMBERED` and the last numbered agent from
  `agents_manifest.json` — the artifact the run itself writes — so it cannot disagree with
  what shipped. Replaced the two named-slug assertions with a manifest-vs-bundle diff that
  catches *any* dropped agent, not the two someone thought to name.

**The rule:** if a script needs to know how many of something there are, it derives that from
the source or from the run's own manifest. If it cannot, the count belongs in exactly one file
that every other reads. And when a placement rule exists ("append, never insert — members have
notes"), follow the precedent already in the file rather than inventing a second convention.

**Corollary for gates:** a gate that fires is a good day. The run that "passed" is the one to
be suspicious of when a source folder changed and no count moved.

<!-- learning:2026-08-02-a-fix-in-one-copy-of-a-script-is-not-a-fix -->
**August 2, 2026** (from: Sigrun website intake — Christine's publish package still carried the render bug fixed in Jagoda's builder five days earlier)

### "Port this fix to the other packages" is a note, and notes do not execute

On 2026-07-28 a first publish to a fleet WordPress install rendered visibly broken in two ways a
marker-based verifier passed clean: the block theme printed its own `<h1>` above our hero, and
`main.is-layout-constrained.has-global-padding` squeezed a full-bleed design into a 645px column
inside a 1717px viewport. Both were fixed in that member's `build_pages.py`, and the run log
recorded the right instruction: *port it to any other member package before its first publish.*

Five days later the next member's package still had the pre-fix CSS — three lines that hid the
header and footer and nothing else. And hers was the package everyone described as "publishes with
one command the moment an Application Password lands." The one command would have produced the
same broken page, on a client site, for the second time on the same project.

Nothing was neglected. The instruction was written down, in the right place, by the run that found
the bug. It just lived in prose, next to a directory of per-member copies of the same script, and
prose has no way to reach a copy.

**Rules:**

1. **A per-entity copy of a build script is a fix-propagation bug waiting to happen.** The moment
   there are two, a fix lands in one. Generate all of them from one function; adding an entity
   becomes a row in a table, not a new file to keep in sync.
2. **When a run's own log says "port this," that is the run admitting it did not finish.** Either
   port it in the same run or make the port unnecessary by moving the logic somewhere shared.
   Leaving it as an instruction transfers a known defect to whoever reads the log next — and
   nobody read it.
3. **The most dangerous artifact is the one described as "one command away."** It gets no further
   review precisely because it is considered ready. Re-derive a ready-to-ship artifact from source
   before shipping it, especially if it was built before a fix you know about.
4. **Regenerating found a second defect in the same pass:** the config carried hand-typed taglines,
   and one already disagreed with the member's own page ("architect-led renovation guidance" vs the
   page's "Certified Passive Building Designer"). A fact the artifact already states should be read
   off the artifact, not maintained beside it.

Learned August 2, 2026.

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

<!-- learning:2026-08-03-crawlability-must-be-tested-on-served-html -->
**August 3, 2026** (from: cxotalk-weekly-maa run)

### Never diagnose crawlability from rendered text — the client who corrected us was right for four weeks

For four consecutive reports, this engagement's #1 technical recommendation was: *"~40M words of
CXOTalk transcripts are client-rendered and invisible to the crawlers ChatGPT and Perplexity depend
on — server-render them."* It was the headline of the strategy, it was in every ANALYSIS section,
and it was **false**.

The client disputed it in writing on 7/28: *"I checked this carefully and I do not believe that
transcripts on cxotalk.com are hidden by JS."* Tested properly, he was right:

| Check | Result |
|---|---|
| Raw same-origin `fetch`, **no JS executed**, `/episode/{slug}` | HTTP 200, 660KB HTML, **59,761 chars** body text after stripping `<script>`, **97 speaker turns** |
| Same, `/episode/{slug}/transcript` | Identical — 59,761 chars, 97 turns |
| `robots.txt` | 916 bytes; only `Baiduspider` is `Disallow: /`. The file **explicitly names** "Googlebot, bingbot, Applebot, ClaudeBot, GPTBot, etc." as covered by the permissive `User-agent: *` group |

**The mechanism of the error.** Reading the *rendered* page returns **~349 words** from
`document.body.innerText`, because the transcript sits inside a collapsed/tabbed element.
`innerText` returns only **visible** text. The content was fully present in the served HTML the
entire time. A visible-text read was mistaken for a crawler's view, and nobody re-tested it for a
month because each week's report inherited the previous week's premise.

**Rules:**

1. **Test crawlability against the SERVED HTML, never the rendered view.** Same-origin
   `fetch(url)` → `DOMParser` → strip `script/style/noscript` → **`textContent`**. Never
   `innerText`, never `get_page_text`, never a screenshot. Those three answer "what can a human
   see," which is a different question and frequently the opposite answer.
2. **`innerText` vs `textContent` is the whole bug.** Collapsed accordions, inactive tabs,
   `height:0` containers and offscreen panels are invisible to `innerText` and perfectly visible
   to a crawler. Any conclusion of the form "the content isn't in the HTML" that was reached via
   `innerText` is unsupported.
3. **Check robots.txt in the same pass, and read it verbatim.** A JS thesis and a blocking thesis
   are two different claims; we asserted both and both were wrong. Quote the actual `User-agent`
   groups rather than characterising them.
4. **A recommendation that survives four reports without being re-tested is a belief, not a
   finding.** Standing recommendations need a re-verification cadence, because the cost of being
   wrong compounds: every week it went unchallenged, it displaced whatever the real fix was.
5. **When a client contradicts your technical claim, test their version first, not yours.** The
   instinct is to defend. The client here had checked something we hadn't, and one raw fetch
   settled it in under a minute. Being corrected and saying so plainly is cheaper than four more
   weeks of confident wrongness — and it upgraded the diagnosis (the citation gap is an
   authority/entity problem, not a plumbing one), which is a better answer than the one we lost.

**Same run, same family, caught before it shipped:** the week's first Ahrefs metrics pull passed
`country=us` where prior runs passed no country filter, returning 394 keywords vs 464 — a false
17% "collapse" that would have been the report's lead. Re-pulling the *prior week's date* under
*today's exact config* reproduced last week's numbers exactly, proving config drift rather than
decline. **Any alarming metric move must be re-pulled at the prior date under the current config
before it is narrated.** Two near-misses in one run, both of the same shape: *the measurement
apparatus changed, the world did not.*

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
