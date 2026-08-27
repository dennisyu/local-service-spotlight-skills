---
name: boil-the-ocean
description: Operating principles for the whole skill pack — how to run every Local Service Spotlight skill on persistent, looping, max-effort agents (Claude Fable 5 and peers from OpenAI and Google) — loop until the Definition of done passes, self-verify, compound with memory, document every run. Read before running any skill; this governs HOW they all execute.
---

# Boil the Ocean — operating principles for persistent agents

This file is the operating layer beneath all ten skills in this pack: it changes nothing about WHAT each skill does and everything about HOW an agent runs it. It matters now because the agents running these skills — Claude Fable 5 and similarly capable models from OpenAI and Google — loop, self-correct, hold memory, and finish end-to-end, so stopping at 90% stopped being a constraint and became a choice.

## The principle

Retire "don't boil the ocean." That advice kept teams focused when implementation was expensive. Garry Tan's February 2026 post (https://garryslist.org/posts/boil-the-ocean) names the turn: AI compresses implementation time 10–100x, so raise ambitions 10x and take on the whole problem.

The working rule: **always prefer the complete approach over the 90% shortcut** — full coverage, edge cases, error paths, the test, the doc. The delta between "mostly done" and "done" now costs seconds, so the marginal cost of completeness is near zero.

This was already the house rule. Dennis has taught "always boil the ocean — because good enough is not enough" for years; in his words: "do the whole thing, do it right, with tests and docs; ship the finished product, not a plan." Persistent agents are the first workers that can hold that bar on every run — without fatigue, without being asked twice.

## How to run every skill now (Fable 5 and friends)

Eight rules. They apply to every skill in this pack, on every run.

1. **Loop until the Definition of done passes.** Every skill states its output or done-bar. Run, check, fix, run again — 90% is a draft, not a deliverable.
2. **Self-verify every run.** Before reporting done, grade your own output against the skill's QA checklist or Definition of done, line by line. No gut calls.
3. **Use memory to compound.** Read prior outputs, notes, and the upstream skills' results before starting. Never start from scratch twice — the second run begins where the first ended.
4. **Document every run as a meta-article example.** What happened, what broke, what you'd change — the write-up is the fuel for recursive self-improvement (below).
5. **Prefer full coverage.** Handle the edge cases, write the test, write the doc. Sweep every source, not the first page of results.
6. **Persist through obstacles.** Fix root causes, not workarounds — a workaround is a deviation you re-pay on every future run.
7. **When blocked, surface it and keep moving.** Name the blocker, what you need, and what you did instead — then finish everything that isn't blocked.
8. **Do it yourself — never hand a human an action you can perform.** If you have the access and the capability, execute. A numbered click-path emailed to a teammate is not a deliverable; it is the work, relabelled and queued behind someone else's inbox. Writing instructions is only correct when you genuinely cannot act: no credential, no permission, or a decision that is legitimately the human's to make. "It would be tidier if they did it," "they own that system," and "they'll want to review it" are not blockers — if you can reach it, finish it, then tell them what you changed so nobody duplicates the work. When a guardrail stops a write, that is rule 7, not rule 8: name the blocker, get authorization, then come back and finish the job yourself.

## Recursive self-improvement

**Do → Document → QA → Example (Meta-Article) → Improve (SOP update) → ↺**

Every run of every skill feeds this loop: do the task per the SOP, document the run, QA it against the canonical instructions, publish the run as a worked example, fold the fixes back into the skill, run again. Each cycle the library gets sharper and needs less of you.

The loop is the `recursive-self-improvement-qa` skill (step 10 of this pack); https://blitzmetrics.com/knowledge-system-maintenance documents the maintenance standard behind it.

## Why this is positive-sum

- **Ephemeralization** (Buckminster Fuller): do more and more with less and less until you do everything with nothing. Every documented, agent-run skill takes fewer human hours per result each cycle.
- **Jevons Paradox for intelligence:** when intelligence gets cheap, the work doesn't shrink — the amount of work worth doing explodes. Efficiency means more usage, more clients served, more jobs. Not fewer.
- **The chain:** documented skills → agents that run them → a marketplace where those agents work and eventually earn → operators freed for the judgment work only they can do.
- **The mission:** that chain is the engine behind Dennis's goal of creating a million jobs — completeness at near-zero marginal cost, multiplied across everyone who installs the library.

## Notes — Dennis's method

- Dennis's rule, verbatim: "The marginal cost of completeness is near zero with AI — do the whole thing, do it right, with tests and docs; ship the finished product, not a plan."
- This file governs execution; each skill still owns its inputs, steps, and outputs. Where they meet, the skill's Definition of done wins — this file just forbids stopping short of it.
- Boil the ocean on coverage, proof, and verification — never on adjectives, scope creep, or invented work. Completeness is not padding.
- Rules 1 and 2 travel together: a persistent agent that loops without verifying just automates its own mistakes.
- Install this file alongside the ten skills (Project knowledge, Skills, or your `memory/` folder) so every chat that runs a skill runs it this way.
- Date every run. "We keep the skills current" is a claim; a dated meta-article trail is the proof.

## Model landscape — kept current (August 1, 2026)

Reviewed the past month's releases. The persistent-agent thesis this file is built on is now shipping infrastructure, not a bet:

- **Claude Opus 5** (July 24, 2026) added a 1M-token context window and a per-turn reasoning-effort dial — low, medium, high, xhigh. Treat that dial as a routing lever, not a preference: raise effort for the one hard call inside a skill instead of moving the whole run to a pricier model, and drop it for the mechanical steps. Escalate effort before you escalate model.
- **Claude Sonnet 5** (June 30, 2026) is the cheap agentic workhorse — it plans, drives browsers and terminals, and self-checks. Route bulk skill runs here: draft, collect, sweep, first pass. It is now the sensible default for any step that chains several tool calls; smaller models stay right for single-shot classification and extraction inside a step.
- **Claude Fable 5** returned July 1, 2026 after a two-and-a-half-week export-control suspension. It stays the ceiling for verification and the hard calls — and that outage is the lesson worth keeping. Never let a scheduled run hard-depend on a single model. A routing table without a fallback tier is a 4am job that fails at 4am for reasons nobody in the building controls.
- **Scheduled agent tasks now run in the cloud** (July 7, 2026) — a recurring job keeps going with the laptop closed. The carve-out matters more than the headline: work that touches local files or drives a browser still needs the desktop app open. Know which of your scheduled skills are which before you assume the schedule is covered.
- **The MCP spec revision dated 2026-07-28** moved to a stateless core and is not fully backward compatible. Before upgrading any connector a skill depends on, check which revision it speaks — a routine version bump is no longer automatically safe.
- **Every major vendor now ships this file's assumptions.** OpenAI's GPT-5.6 (July 9, 2026) exposes Sol, Terra, and Luna as an explicit cheap-to-flagship ladder and adds programmatic tool calling, where the model writes a small program to coordinate tools instead of round-tripping each one. Google's Gemini 3.6 Flash and 3.5 Flash-Lite (July 21, 2026) fold computer use in as a built-in tool. A tiered ladder, real tool use, long-horizon runs — that is the shape of the whole field now, not one vendor's bet. Gemini 3.5 Pro had not shipped as of this review.
- **Managed Agents** run skills on a schedule with vault-stored secrets and browser/CLI access — this file's "persistent, looping agent" is a product surface, not just a way of working. This library is itself kept current by one.

Rule of thumb after this month: pick the cheapest tier that clears the bar, turn the effort dial before you turn to a bigger model, and give every scheduled job a fallback. See `model-judgment` for the full routing ladder.
## Definitive article & links

- The source idea: https://garryslist.org/posts/boil-the-ocean — Garry Tan, "Boil the ocean" (Feb 2026)
- Keeping the library current: https://blitzmetrics.com/knowledge-system-maintenance
- The engine the skills run on: https://blitzmetrics.com/content-factory/
- The standard at scale — the BlitzMetrics Task Library: https://blitzmetrics.com/task-library-dashboard/
- Applies to: all ten skills, `personal-brand-strategist` through `recursive-self-improvement-qa`.

## Learned in the field

*Appended automatically by the self-improvement loop (Skill-Learnings/): dated lessons from real runs. Newest at the bottom.*

<!-- learning:2026-07-18-login-free-first -->
**July 18, 2026** (from: skill-pack-propagation follow-up session with Dennis, July 18, 2026)

Before declaring any WordPress publish step blocked on a human login, check the standing login-free path: .credentials.json → wp_sites[domain].app_pass, used over REST Basic Auth (docs: blitzmetrics.com/application-passwords/). July 18, 2026 lesson: a weekly job reported its publish leg as waits-on-login for a site whose app password had been publishing unattended for weeks. Also: send a FULL browser User-Agent string on REST calls — blitzmetrics.com's WAF 403s minimal UAs, which was misdiagnosed on July 6, 2026 as a broken app password. Verify auth with GET /wp-json/wp/v2/users/me before concluding anything is broken.

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

<!-- learning:2026-08-14-do-it-yourself -->
**August 14, 2026** (from: Ensiteful Marketing / ethanvandehey.com login triage with Dennis, August 14, 2026)

### Rule 8 was written the day an agent emailed a human a to-do list it could have executed

Ethan reported two things: a WordPress login that "did not work" and a personal site that "seems broken."
Both reports were wrong about the cause, and finding the real cause required refusing to stop at the
plausible answer.

**Read the artifact, not the summary.** The two Basecamp screenshots were the whole case, and they were
images. Fetching them cost four steps — CORS blocked a cross-origin fetch, so the images had to be
opened same-origin, which redirected to a presigned S3 URL that could then be downloaded and decoded.
Worth every step: screenshot one said *"Unknown email address"* (a credentials problem, not a broken
site) and screenshot two said `ERR_CONNECTION_REFUSED` (a TCP failure, not a WordPress error). Two
reports, two entirely different subsystems. **Guessing from the prose description would have produced two
wrong fixes.**

**Then check the thing everyone assumes is fine.** The credentials worked — verified by POSTing them and
getting a 302 into `/wp-admin/` with a live session. So why "unknown email address"? Because the account
had been created as `ethan@roof**ing**launchmarketing.com` while Ethan's real address is
`ethan@rooflaunchmarketing.com`. The extra "ing" was not a variant spelling: **the domain did not exist
at all** — NXDOMAIN on Google, Cloudflare and Quad9, no A record, no MX, no nameservers. Which meant the
obvious fallback advice, "just use Lost your password?", would have bounced into a void. *Verify the
identifier itself, not just whether the credential authenticates.*

**Sweeping past the reported problem found the bug nobody filed.** Because the display name was never
set, WordPress fell back to the login string and published Ethan's email address in three public places
on his own personal-brand site — author archive title, author URL, and `/wp-json/wp/v2/users`. A
harvestable address and a byline pointing at another company's domain, on a site being built for a
knowledge panel. Nobody reported it because nobody was looking.

### The actual lesson

The first pass ended by emailing Muzamil a tidy three-item click-path — correct the email, set the
display name, retire the generic `admin` account — after a guardrail blocked the write. Dennis's
response: *"if you can do it, don't make a human do it."*

Handing over instructions felt like diligence. It was not. It was the work, relabelled and queued behind
someone else's inbox — and every hour it sat there, Ethan stayed blocked and the email stayed public.
Worse, the human it was handed to passed it straight back: Ethan's reply was "Muzamil — please follow the
steps Dennis outlined." A click-path does not distribute work, it circulates it.

Once authorized, all three items took one pass: emails corrected on both sites, display names and author
slugs fixed, the `admin` account deleted with its 4 posts and 9 pages reassigned rather than orphaned,
then verified from outside — zero emails in the public REST on either site, `/author/admin/` returning
404, and all four login combinations tested green.

**A guardrail is rule 7, not rule 8.** Being blocked means name the blocker and get authorization. It
does not mean convert the task into homework for a human. The finished product is the deliverable; a
numbered list of steps is what you send only when you genuinely cannot act.

<!-- shared-rule:silent-media-playback:start -->
## Silent media playback

- Never let audio from browser, video, audio, presentation, or application testing play through the user's speakers unless the user explicitly asks to hear it.
- Before starting any media playback, mute the player and set its volume to zero. Keep it muted for the full test, including replays, reloads, new tabs, and alternate players.
- Apply this rule to the primary agent and every delegated agent. Include the mute requirement whenever work that may involve media playback is delegated.
- If the mute state cannot be controlled and verified before playback, do not start playback. Use metadata, captions, transcripts, frames, screenshots, network state, or player state instead.
- Only unmute when the user explicitly requests audible playback in the current task.
<!-- shared-rule:silent-media-playback:end -->
