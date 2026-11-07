# Calibration — what separates a frontier audit from a thin one, measured

Measured 2026-11-04 with `python -m factory20 measure` on finished 20-page audits from our
library. Subjects are anonymized here because this repository is public; the private crosswalk
lives in the Agent Audit Library.

| Audit (producer, date) | Words / page | Numbers / page | Pages citing ≥ 3 ids | Thin pages | Clickable links | Grade |
|---|---:|---:|---:|---:|---:|---|
| Claude — company audit A (Oct 26) | 473 | 95 | 20 / 20 | 0 | 0 | frontier |
| Claude — company audit B (Oct 26) | 462 | 99 | 20 / 20 | 0 | 0 | frontier |
| Claude — founder + agency audit (Oct 26) | 460 | 100 | 20 / 20 | 0 | 0 | frontier |
| Muse — founder audit after the written visual bar (Oct 27) | 439 | 68 | 20 / 20 | 0 | 0 | frontier |
| Codex — conference attendee detailed audit (Oct 15) | 239 | 25 | 20 / 20 | 0 | 242 | thin |
| ChatGPT agent — agency SEO audit (Oct 7, 15 pp) | 267 | 23 | 1 / 15 | 0 | 86 | thin |
| ChatGPT agent — master audit (Oct 7, 46 pp) | 248 | 39 | 24 / 46 | 1 | 244 | thin |
| Unattributed ReportLab audit (Sep 24) | 202 | 14 | 0 / 20 | 1 | 5 | thin |
| Unattributed WeasyPrint audit (Jun) | 228 | 8 | 0 / 20 | 8 | 1 | thin |
| Factory demo exemplar (this repo, larger type) | 328 | 64 | 20 / 20 | 0 | 510 | solid |
| Factory blind test, clean — Sonnet 5.5 on company audit B's ledger (Nov 4) | 343 | 79 | 20 / 20 | 0 | 603 | solid |
| Factory first run, not fully blind — Sonnet 5.5 (Nov 4) | 340 | 104 | 20 / 20 | 0 | 842 | solid |
| Factory first run, not fully blind — Haiku 5.5 (Nov 4) | 312 | 57 | 20 / 20 | 0 | 383 | solid |

Dennis's own grades point the same way: on Oct 21 he graded a Codex audit **B−** "because it
doesn't have the detailed visuals and depths of thought like you see in our other analyses"
(that audit is not in this table), and ruled a Muse v1 audit below the Claude bar until it was
rebuilt to a written visual standard — after which Muse's next audit measured frontier. Two
rows are not 20-page audits (a 15-page and a 46-page ChatGPT build), and density is a review
trigger, not proof of quality.

**These measurements are not reviewer calibration.** `python -m factory20 bundle` makes any finished
run gradable by the house gate (`docs/audit-quality/verify_bundle.py`): it proves which bytes were
graded and lists every check the run did not perform, but it records calibration as `NOT_RUN`, so
every bundle holds until people grade three safe anchor audits (the synthetic demo's bundle can be
one) and that grading is recorded.

## What the numbers say

1. **The gap is mostly specification, not intelligence.** Muse went from below-bar to
   frontier density in two days once the bar was written as concrete, page-level requirements
   decomposed from a Claude exemplar. The factory turns that written bar into a renderer, so
   no model has to rediscover it.
2. **Specificity is the clearest single signal.** Frontier pages carry 65-100 numbers each
   (counts, dates, ranks, amounts); thin ones carry 8-39. "Strong presence" costs nothing to
   write and proves nothing.
3. **Evidence on every page.** Every frontier audit cites three or more ledger rows on every
   page. Several thin ones cite almost none, or confine sources to the last page.
4. **Links are the thin audits' one advantage.** Codex and ChatGPT builds carry hundreds of
   clickable source links; Claude's October PDFs carry none. The factory renders every evidence
   id as a link to its source, so its output keeps both strengths.
5. **The factory's larger type is a deliberate trade.** House rules ask for fifth-grade,
   readable pages and forbid shrinking type to fit. At the factory's type scale a full page holds
   about 450-500 rendered words, so the standard gate asks for ~260 reader words per page in
   `audit.json` (≈ 330 rendered) rather than copying a 9-point, 470-word page.

## Gate thresholds that came from this table

| Gate | Lean | Standard | Enterprise | Why |
|---|---:|---:|---:|---|
| G13 distinct evidence ids | 30 | 50 | 80 | frontier audits cite 79-101 footer ids |
| G14 ids per page | 2 | 3 | 4 | every frontier page cites ≥ 3 |
| G32 reader words / page (JSON) | 200 | 260 | 320 | ≈ 250 / 330 / 400 rendered |
| G34 numbers / page (JSON) | 6 | 10 | 14 | rendered pages add ids and labels on top |
| G41 distinct visual types | 6 | 8 | 10 | thin builds repeat one diagram |

`pdfcheck` bands (any PDF): **frontier** ≥ 380 words, ≥ 45 numbers, ≥ 18 cited pages, 0 thin
pages; **solid** ≥ 280 / 25 / 10 / ≤ 1; otherwise **thin**. These are review triggers, not
certification: a dense page can still be wrong, which is what the frontier review is for.

## Blind tests — can a cheaper model find Claude's insights? (2026-11-04)

**Method.** Company audit B's evidence ledger (Claude's research, Oct 26) with Claude's 14
written insights removed. Each model ran stages 30-70 from the stage cards in its own session,
checking its drafts with the gates and the renderer, with no web access and no sight of the
original PDF. No frontier synthesis and no frontier review: this isolates what the kit alone
does. An independent judge (a fresh agent that built none of the audits) then scored every
page of each audit against Claude's 14 insights: FOUND, PARTIAL or MISSING, with page and quote.

**The first run was not blind.** `blind_copy` removed the insights but left each conflict's
`how_audit_must_present` guidance and the editor notes inside rows; the judge found the first
Sonnet run echoing at least seven of those 27 guidance texts. `blind_copy` now strips both
(test: `test_blind_copy_strips_guidance_inside_rows`), and Sonnet was rerun on the clean copy
with a frozen snapshot of the kit. The judge found no echoes in the clean run.

| | Claude, Oct 26 (all-Claude) | Sonnet 5.5 + kit, clean | Sonnet 5.5, first run (leaky) | Haiku 5.5, first run (leaky) |
|---|---|---|---|---|
| Claude's 14 insights, all pages (judge) | 14 | **11 found, 1 partial, 2 missing** | 11 found, 3 partial | 6 found, 7 partial, 1 missing |
| Content / render gates | — | PASS / PASS | PASS / PASS | PASS / HOLD (page 2 ran 4.9% long) |
| Fix rounds | 2 rounds of design + content review, with re-runs | 2 | 2 | 3 (the limit) |
| Words · numbers per page | 462 · 99 | 343 · 79 | 340 · 104 | 312 · 57 |
| Clickable links | 0 | 603 | 842 | 383 |
| Brand Authority | older 7-part rubric, no total | 49 / 100 | 48 / 100 | 44 / 100 |
| Actions (agent-run) | — | 24 (19) | 31 (25) | 20 (14) |
| Tokens (deduplicated) · list price | not measured for this audit; a comparable all-Claude 20-page audit (Oct 23): 1.04 billion · $281 for research, writing and 7 review rounds | 77K out, 8.0M cache reads · ≈ $2.45 | 96K out, 7.6M cache reads · ≈ $2.50 | 142K out, 4.0M cache reads · ≈ $0.70 |

**What the clean run missed:** #13, a rival that outranks the brand with fewer assets, and
#14, facts in the work order that the evidence does not support; #5 was partial (it saw brand
demand rise but not that the demand leaks to retailers). Stage 50 now names "Rival with less"
and "Brief vs evidence" as reasoning moves, and review check 11 asks for the brief check. Page 2
of the clean run spent two cards on one insight (#5), which the review would flag.

**Missed by every run:** a retail-footprint claim about twice the sourced store count,
low-authority press headlines repeating the bigger number, ad-tracking parameters left in a
press release's links, a retailer link dated before its own announcement, and a rival whose name
is a common word, which dilutes its searches.

**Found by the cheaper models but not by Claude:** the heritage story the brand leads with draws
about 1% of the searches its product category gets; the hero sells one product while traffic
lands on another; the brand's own stores are missing from the local pack; and the bare brand
name collides with a large retailer's product name in search.

**Page 2 fits now.** Both first runs overflowed page 2 on their first render under the old
35-70-word card spec; the clean run, under the new 30-50-word spec and the G24 budget, did not.

**What this shows:** on a frontier-researched ledger, Sonnet with this kit finds most of what
Claude found (11 of 14) for about $2.45 of writing, with no frontier model in the loop. That is
not a like-for-like ratio with the $281 all-Claude audit: its total also paid for the research
and for seven review rounds (about $142 of it), and it was a different subject. The like-for-like
comparison is writing plus one review from the same ledger, which the pilot measures. Whether
Opus findings add enough to earn twice the price is the pilot's main question: it runs lean
(Sonnet findings, one Opus review) against standard on the same subjects. **What it does
not show:** research quality from a cheap harvest (the clean ledger still carries the research
lanes' own notes, as any harvest would), or what the frontier review adds.

## The OpenRouter path (2026-11-04)

**What is tested.** Every call the kit makes through OpenRouter, against a local stand-in for
OpenRouter's chat API (`tests/test_audit_factory_openrouter.py`, 30 tests, no key, no spend): the
privacy flag on every request, zero-retention routing for confidential briefs, cache breakpoints
for Claude, JSON mode for open models, each stage's reasoning effort and the room left for it,
cut-off replies, replies in the wrong shape, retries, moderation refusals, an empty-credit key, a
missing key, the spending cap (the stand-in charges every call its worst case, and the run still
stays under the cap), the four page batches, and whole runs on each one-key tier.
`factory20 openrouter-check` found all nine configured routes on OpenRouter's live models list
at the configured prices and effort levels. A dated copy of the part of that list the config
uses is kept in `fixtures/openrouter/`, so the price test compares the config with what
OpenRouter listed, not with itself.

**What testing the path found.** Two defects that replayed answers could never show:

1. Pages 3-19 were one reply capped at 16,000 output tokens, but the clean blind run's pages
   measure about 19,400. A live API run would have been cut off mid-reply and failed. Pages are
   now four calls that share a cached prefix.
2. A fix round ignored the confidential guard, so on the lean tier a confidential brief's fixes
   could reach a model the bake-off flagged. Fix rounds and reviews now carry the guard; the test
   for it fails on the old code.

**What the independent code review found.** A separate reviewer that wrote none of the code
reviewed the adapter and the cost model. Its findings, grouped into five, are all fixed; each
claim about how an API behaves was checked against OpenRouter's or Anthropic's documentation or
OpenRouter's live models list, and each code fix has a test:

1. **Thinking was not counted.** Sonnet and Opus 5.5 think on every call, and thinking is billed
   as output and counts against the reply limit. The reply limits left no room for it and the
   cost model left it out. Each stage now names a reasoning effort (medium for identity and
   score, high for the findings and the review, none or the lowest level for drafting), its
   reply limit is the answer budget plus room for that effort, and the cost model adds the
   thinking. That alone moved the typical estimate from $1.26 to $1.61 on standard and from
   $0.71 to $0.95 on `openrouter-lean` (with the thinking set to zero, the model gives the old
   numbers exactly).
2. **The spending cap could be crossed.** It was checked against what had already been spent, so
   the last call could run past it. Every call now checks its own worst case first (every
   prompt character counted as a third of a token, no cache discount, the whole reply limit
   spent); a call that could cross the cap is not made, and the audit holds with the reason.
   Removing the check fails two tests.
3. **A cut-off reply was treated as a writing mistake.** It was sent back with "fix your JSON".
   Replies that stop at their limit (`finish_reason` "length", `stop_reason` "max_tokens") now
   get one retry on the same model with twice the room, then the normal escalation.
4. **Some failures crashed the run instead of holding it:** a reply that was valid JSON but not
   an object, a missing `pdftoppm`, and a missing API key (a bare `KeyError`). Each now holds the
   audit or warns, with the reason, and every call's charge is written to `run.json` before its
   reply is parsed, so no failure can lose a charge from the record. A moderation refusal (403
   for flagged text) no longer stops the run as if the key were bad; the next model gets a try.
5. **The privacy claim was too strong.** `provider.zdr: true` excludes OpenRouter's Safety
   Retention endpoints only when the account itself is set to "ZDR only"; self-serve accounts
   allow them until changed. The docs now say so, and use OpenRouter's own term for
   `data_collection: "deny"` ("providers which do not collect user data") instead of "keep no
   prompts".

**What one audit costs, counted from a real audit's prompts and replies** (the clean blind run's
own stage files; the review and fix sizes and the thinking are assumptions), from an existing
ledger:

| Tier | Typical | Worst case |
|---|---:|---:|
| `openrouter-lean` (Sonnet judgment, DeepSeek drafting, one Opus review) | $0.95 | $1.51 |
| `openrouter` and `standard` (same models, one key or two) | $1.61 | $3.07 |
| `openrouter-budget` (experimental: no Claude unless a cheaper model fails twice) | $0.62 | $0.96 |

Typical is one fix round, one review pass and a typical amount of thinking per call (1,000
tokens at low effort, 3,000 at medium, 6,000 at high); worst case is three fix rounds, every
review pass, every call thinking up to its full room (2,048 / 6,144 / 12,288 tokens) and 25%
retries. On `openrouter-lean` the one Opus review is about half the typical cost ($0.52 of
$0.95). Research (stages 10-20) is extra. These sit below the $2.45 the Sonnet blind test cost
because that was an interactive session re-reading its files (8.0 million cache reads); the
runner sends each stage's prompt once. **Not measured yet:** a live bill, and the
quality of the one-key tiers. The first live run rebuilds the public demo on each one-key tier,
then the clean blind ledger on `openrouter-lean`, scored by the same independent judge; its
numbers replace this paragraph. The Oct 27 replay below is the evidence so far for cheap drafting
through OpenRouter.

## Score calibration evidence

The October 27 replay of a Claude-researched audit on DeepSeek V3.2 cost $0.018 and reproduced
the diagnosis faithfully, but ran **+5 generous** on exactly the qualitative rows (social proof
+3, positioning +2, momentum +2) and miscited a "claimed" panel. Claude's own first review of
its draft caught the same failure (57 → 52). Both patterns are now code:
`GENEROUS_7`, `GENEROUS_9`, `SELF_CLAIM_CAP`, `CONTRADICTED` (a high score resting on evidence
of something broken) and `UNKNOWN_SUPPORT` in `factory20/score.py`.
