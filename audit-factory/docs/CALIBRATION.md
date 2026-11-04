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
| Factory blind test — Sonnet 5.5 on company audit B's ledger (Nov 4) | 340 | 104 | 20 / 20 | 0 | 842 | solid |
| Factory blind test — Haiku 5.5 on the same ledger (Nov 4) | 312 | 57 | 20 / 20 | 0 | 383 | solid |

Dennis's own grades point the same way: on Oct 21 he graded a Codex audit **B−** "because it
doesn't have the detailed visuals and depths of thought like you see in our other analyses"
(that audit is not in this table), and ruled a Muse v1 audit below the Claude bar until it was
rebuilt to a written visual standard — after which Muse's next audit measured frontier. Two
rows are not 20-page audits (a 15-page and a 46-page ChatGPT build), and density is a review
trigger, not proof of quality.

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

## Blind test — can a cheaper model find Claude's insights? (2026-11-04)

**Method.** Company audit B's evidence ledger (Claude's research, Oct 26) with Claude's 14
written insights and its research-lane notes removed (`ledger.blind_copy`). Sonnet 5.5 and
Haiku 5.5 each ran stages 30-70 from these cards in their own session, checking their drafts
with the gates and the renderer, with no web access and no sight of the original PDF. No
frontier synthesis and no frontier review: this isolates what the kit alone does.

| | Claude, Oct 26 (all-Claude) | Sonnet 5.5 + kit | Haiku 5.5 + kit |
|---|---|---|---|
| Content gates / render gates | — | PASS 38/38 · PASS | PASS · HOLD (page 2 ran 4.9% long) |
| Fix rounds | 2 rounds of fresh-context design + content review, with re-runs | 2 | 3 (the limit) |
| Claude's 14 insights found on page 2 | 14 | 8 — Claude's first eight | 6, plus 1 new (a name collision) |
| Brand Authority | older 7-part rubric, no total | 48 / 100 | 44 / 100 |
| Actions (agent-run share) | — | 31 (81%) | 20 (70%) |
| Tokens (deduplicated) · list price | ~1.1 billion · $364-647 | 96K out, 7.6M cache reads · ≈ $2.50 | 142K out, 4.0M cache reads · ≈ $0.70 |

**Neither found** Claude's five deeper insights: fragmented entity signals, tier-1 press that is
broad but shallow, quotable third-party proof left unused, the head-to-head competitor that
wins with fewer assets, and facts in the work order that the evidence does not support. Those
are judgment calls, which is why the standard tier keeps Opus on synthesis and review.

**Both overflowed page 2 on their first render**, because stage 50 allowed 35-70-word card
bodies and only about 50 fit. Fixed the same day: the card now says 30-50 words, G24 checks a
600-word page-2 budget before rendering, and R02 reports how far a page runs over and which card
is tallest.

**What this shows:** with a frontier-researched ledger, Sonnet on this kit reproduces most of
the top insights at about 1/150th of the cost, and Haiku is good enough for drafting but not for
synthesis. **What it does not show:** research quality from a cheap harvest, or how much the
frontier review adds. The next calibration run measures both.

## Score calibration evidence

The October 27 replay of a Claude-researched audit on DeepSeek V3.2 cost $0.018 and reproduced
the diagnosis faithfully, but ran **+5 generous** on exactly the qualitative rows (social proof
+3, positioning +2, momentum +2) and miscited a "claimed" panel. Claude's own first review of
its draft caught the same failure (57 → 52). Both patterns are now code:
`GENEROUS_7`, `GENEROUS_9`, `SELF_CLAIM_CAP`, `CONTRADICTED` (a high score resting on evidence
of something broken) and `UNKNOWN_SUPPORT` in `factory20/score.py`.
