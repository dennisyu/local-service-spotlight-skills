# How knowledge propagates here

*Written for anyone — no code required. If you only read one page in this
repository, read this one.*

---

## The goal

**Something learned once should become something every agent checks
automatically, forever, without anyone having to remember it.**

That is the whole objective. Not "write it down." Not "tell the team." Those
both depend on a human remembering at the exact moment it matters, and that
human is usually mid-task, three hours in, with the rule nowhere in sight.

The test of whether we have achieved it is simple:

> A rule is stated on Monday. On Friday, an agent nobody briefed — working for
> someone we have never met, on a site we have never seen — declines to break it.

If that happens without a person in the loop, the machinery works. If it does
not, the machinery is decoration.

---

## The four steps, and the one that was missing

Getting from "Dennis said something" to "every agent obeys it" takes four steps.
Skip any one and the chain breaks silently.

| | Step | What it means | Was it working? |
|---|---|---|---|
| 1 | **Capture** | The lesson gets written down once, in the one place that counts | **No** |
| 2 | **Distribute** | That writing physically reaches every place an agent reads | Only for one rule |
| 3 | **Enforce** | An agent or a page that ignores it gets caught | Partly |
| 4 | **Feed back** | A violation found in the wild sharpens the rule | No |

Step 2 is the part that already existed and was excellent — the design was
right, it was just wired to a single file. Step 1 is the part that was missing
entirely, and step 1 is where knowledge actually leaks.

Here is the proof, and it is not hypothetical:

> The black-button rule was published on **17 May 2026**, with an article, an
> illustrated explanation, and a WordPress plugin to enforce it. On
> **15 August 2026** — ninety days later — an agent with the *entire skill pack
> loaded* shipped a black button onto a paying client's site.

Nothing was broken. Nobody was careless. The rule simply never entered the one
directory that agents actually read, so from the agent's point of view the rule
did not exist. **A rule that lives only in an article is a rule the next agent
will break.**

---

## The mechanics, in plain language

Think of it as a stamp and a stack of envelopes.

**One rule lives in one file.** It goes in a folder called `standards/`. One
file, one rule, plain English — the black-button rule is a page of text saying
what to do, why, and how to check. That file is the *only* place the rule is
written down. There is no second copy anyone maintains.

**Skills are the envelopes.** The pack contains 27 skills — content factory, SEO
audit, weekly brand MAA, and so on. Each one is a self-contained folder. When
someone installs the pack from a QR code at a conference, what lands on their
machine is those folders. **They do not get the `standards/` directory. They do
not get this repository.** So a rule that merely *links* to the standards folder
would ride along until it reached them and then evaporate.

**So we stamp the rule into every envelope.** One command —
`python3 scripts/sync_shared_rules.py` — reads every file in `standards/` and
copies its text, word for word, into `AGENTS.md` and into all 27 skill files. It
marks each copy with an invisible tag so it knows which text it owns:

```
<!-- shared-rule:no-black-buttons:start -->
   … the rule, exactly as written in standards/no-black-buttons.md …
<!-- shared-rule:no-black-buttons:end -->
```

Nobody types those copies and nobody edits them. The command writes them. Today
that is **10 rules × 28 files = 280 copies**, all generated, all identical to
their source.

**The build refuses to let a copy go stale.** Every time a change is proposed,
an automatic check re-runs the stamp and compares. If one copy differs from the
source by a single character, the check fails and the change cannot be merged.
Drift is not caught late; it is impossible.

**The result:** adding a house rule to the entire fleet — and to every person who
ever installed the pack — is *dropping one markdown file into `standards/` and
running one command.* No code change. No editing 27 files. Nothing to remember.

---

## What one file produces

This is the part worth understanding, because it is what makes the system
recursive rather than merely tidy. **A single standard file generates three
different things**, which is exactly Content · Checklist · Software:

```
                    standards/no-black-buttons.md
                                 │
        ┌────────────────────────┼────────────────────────┐
        ▼                        ▼                        ▼
   CONTENT                  CHECKLIST                 SOFTWARE
   the rule text,           the same words,           the machine checks
   stamped into             read by a person          in the file header,
   AGENTS.md and            before they touch         compiled into the
   all 27 skills            a site                    live fleet sweep
        │                        │                        │
        ▼                        ▼                        ▼
   every agent              every person             every published page
   that reads any           doing site work          swept on a schedule
   skill, anywhere
```

The header of each standard carries the patterns that detect a violation in real
HTML. `scripts/fleet_check.py` compiles those into the sweep. **The sweep is
generated from the rule — never written next to it.** That distinction is the
whole point: the moment the checker is a separate hand-written script, the two
drift, and you get a checker that passes sites which break the rule, which is
worse than having no checker, because now you trust it.

---

## The order matters: Checklist first, then Content

The instinct is to write the article first. The article is the visible artifact
— it can be shared, it looks finished, it teaches. That instinct is exactly what
loses rules, because once the article exists the work *feels* done, and the
enforceable form never gets written. Ninety days of black buttons is what that
feels like in practice.

So the order is inverted:

1. **Checklist** — write the checkable rule in `standards/`. Ten minutes.
2. **Content** — write the article that teaches it, from the rule.
3. **Software** — the sweep is generated automatically. Zero minutes.

The article is downstream of the rule, not upstream. Same output, and the rule
cannot be lost on the way.

---

## Capturing a rule: the one command

When anyone states a rule — you, a client, an audit, or an agent's own mistake —
the response is not to remember it. It is:

```bash
python3 scripts/new_standard.py "No autoplay with sound" \
  --from "Dennis Yu, Cowork session, 2026-08-16" \
  --applies-to published-html
```

Then write the rule in the file it creates, run the stamp, open a pull request.
Roughly ten minutes end to end.

Two details that carry more weight than they look:

**`--from` is required.** Every rule records where it was said. Not bureaucracy —
it is how we see *which channels leak*. Look at the current set: rules captured
from articles, from chat sessions, from agent failures. **Zero captured from a
Zoom call**, and there are several dozen recorded. That is not a suspicion any
more, it is visible at a glance, and it names the next thing to fix.

**A half-written rule cannot be merged.** The scaffold contains a marker the
build rejects. So a rule that was started and abandoned fails loudly instead of
sitting in `standards/` looking enforced while enforcing nothing.

---

## What the sweep does, and what it honestly cannot

`scripts/fleet_check.py` fetches live pages and runs every machine-checkable rule
against them. A real run, today:

```
  https://georgepaladichuk.com/       clean against all 7 applicable rule(s)
  https://localservicespotlight.com/  [FAIL] sameAs target does not resolve
                                             HTTP 404 — wikidata.org/wiki/Q138846724
```

Three design decisions keep it trustworthy:

- **Every check must prove itself.** Each rule's header carries samples that
  *should* trip it and samples that should *not*, and the build runs them. The
  most common way an automated check fails is not a crash — it is a pattern that
  matches nothing and reports every site clean forever. That cannot ship here.
- **Rules can be scoped.** The immersive-hero rule applies to personal-brand
  sites, not product sites, so it is tagged and does not fire on
  blitzmetrics.com. A sweep that cries wolf gets ignored, and then the real
  findings go unread with it.
- **It says what it did not check.** Judgement rules — "a photograph has to earn
  full bleed" — cannot honestly be reduced to a pattern, so they are listed at
  the bottom of every report as *not verified by this sweep*. And a page that
  failed to load is reported as **not swept**, never as clean. A sweep that
  could not reach a page has not found it clean; it has found nothing.

That last habit comes straight from `ACCEPTANCE.md`, which already says the
thing most dashboards will not: *`Scheduled` does not mean `Observed`.*

---

## Where it still leaks

Written plainly, because a propagation system that hides its own gaps is the
problem it claims to solve.

- **Recorded calls produce nothing.** Several dozen Zoom recordings exist. Zero
  standards have come from them. It is the largest known reservoir of uncaptured
  rules, and nothing currently reads it.
- **The sweep is not yet scheduled.** The code runs and the findings are real,
  but until it is wired into the Friday fleet audit it only runs when someone
  types the command. *Available is not Scheduled, and Scheduled is not Observed.*
- **Enforcement stops at published HTML.** Rules about how an agent behaves — mute
  before playback, capture what you learn — reach every skill but nothing verifies
  obedience. Distribution is solved; verification is not.
- **A rule can still be wrong.** Nothing here makes a rule correct, only
  consistent. `no-autoplay-with-sound` narrows a published rule to reconcile it
  with the hero standard, and it says so in the file and needs confirming.

---

## The short version, for the stage

> We keep every rule we have learned in one folder, one file per rule. A script
> stamps every one of those rules into every skill we ship, so when you install
> the pack the rules come with it — you do not have to know they exist. The build
> refuses to merge if any copy has drifted. And the same file that states the rule
> also contains the test for it, so the rule and the thing that checks the rule
> can never disagree.
>
> Adding a new rule to everyone, everywhere, is dropping one file in a folder.

---

*See also: [`CONTRIBUTING.md`](CONTRIBUTING.md) for the pull-request route,
[`ACCEPTANCE.md`](ACCEPTANCE.md) for what counts as proof that something
actually happened, and [`standards/`](standards/) for the rules themselves.*
