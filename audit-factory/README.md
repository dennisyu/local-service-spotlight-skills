# Audit Factory 20 — frontier-grade 20-page audits at volume prices

**What this is, in one paragraph:** our best audits come from Claude's frontier model, but an
all-Claude audit cost about **$280 at list price** (the Oct 23 run, measured from its own token
counts) and quickly burns a $200 subscription. This factory splits the work so the frontier
model (Opus 5.5) does only the two jobs that need judgment — writing the findings and reviewing
the final file — while cheaper models (Claude's own Haiku and Sonnet, or Gemini, GPT and
DeepSeek), plain code and the runner do everything else. The design and the quality checks live
in code, so any model fills in the same proven template and is told exactly what to fix.
Standard tier: **about $5 per audit** in API fees by the conservative planning estimate (stage
budgets, research included). Counted from the prompts and replies of a real 20-page audit, one
pass from an existing evidence ledger comes to about **$1.26 on standard and $0.71 on the
one-key OpenRouter tier** — estimates until the first live bill, which the pilot records.

## Why Claude's audits were better (and why that is fixable)

Measured on finished PDFs ([docs/CALIBRATION.md](docs/CALIBRATION.md)): the audits Dennis graded
best carry 460-470 words and 95-100 specific numbers per page with evidence on every page; the
ones he graded lower carry 200-270 words and 8-39 numbers. Four causes, each with a fix here:

| Cause | Evidence | Fix in this kit |
|---|---|---|
| **The bar was tacit** — rules said what not to do, not how to produce insight | a 148 KB skill, ~85% house rules unrelated to the audit run | short stage cards, generation first ([stages/](stages/)) |
| **Every audit was hand-designed** — only a frontier model could lay out 20 bespoke pages | Muse reached frontier density only after a page-level visual bar was written | a fixed component renderer: models write `audit.json`, code draws |
| **Research stopped early** | same subject: Opus tried 4 name spellings and scored; Sonnet stopped at a namesake | a mandatory query-variant protocol ([stages/10-collect.md](stages/10-collect.md)) |
| **QA was open-ended and expensive** | one audit: 7 Opus review rounds, about $142 of its $301 | free deterministic gates first, then one structured frontier pass |

And one cause that was not about models at all: the October cheap-lane pipeline filed work
orders for Gemini and Cursor "lanes" that were never running processes; ten days and five
chases later nothing had happened. **One runner owns an audit end to end.**

## What is code today, and what the runner does

| Step | Today | Run by |
|---|---|---|
| 10 Collect | **no collector code yet** — the runner researches with its own search and data tools (web search, Ahrefs, Knowledge Graph) following the card | the runner |
| 20 Harvest | **no harvest code yet** — the runner (or cheap helpers it starts) turns captured sources into ledger rows following the card | the runner |
| 30-70 Identity → actions | `factory20 run` calls each stage's model, checks the output, retries with the failure list, escalates one rung | code + routed models |
| Gates, render, fix rounds | code: 39 content gates, 5 render gates, then up to 3 fix rounds that send the exact failure list back to the writer | code + routed models |
| 80 Review | code calls the review model in a fresh context (final files only, no drafting history); S0/S1 sends fixes back and re-reviews | code + review model |
| 90 Deliver | `factory20 basecamp` writes the to-do list; filing and the Basecamp post follow [stages/90-deliver.md](stages/90-deliver.md) | the runner |

Collectors for steps 10-20 are the next engineering job; until they exist, the pilot measures
steps 30-90 on fresh research done by the runner.

## Quickstart (no keys needed)

```bash
cd audit-factory
pip install -r requirements.txt && python -m playwright install chromium   # the browser this Playwright version needs
python -m factory20 gate   fixtures/demo/audit.json --ledger fixtures/demo/ledger.json
python -m factory20 render fixtures/demo/audit.json --ledger fixtures/demo/ledger.json --out demo.pdf
python -m factory20 measure demo.pdf any-other-audit.pdf      # grade any agent's PDF
python -m factory20 cost --per-month 200                       # per-stage and monthly cost by tier
python -m factory20 openrouter-check                           # OpenRouter routes still listed at our prices (no key)
python -m factory20 basecamp fixtures/demo/audit.json --ledger fixtures/demo/ledger.json --out todos.json
# the whole line with replayed model answers, no keys:
python -m factory20 init runs/demo --from-demo                 # brief.json + ledger.json + assets/
python -m factory20 run runs/demo --tier standard --fake fixtures/demo/audit.json --no-render
```

## Setup for agencies and AI builders

1. **Python 3.11+** and `pip install -r requirements.txt`; Chromium through Playwright
   (`python -m playwright install chromium`), and `pdftoppm` (poppler) for the QR check.
2. **Model keys** for a live run. Simplest: one `OPENROUTER_API_KEY` and an `openrouter*` tier,
   which sends every call — Claude included — through OpenRouter ([below](#run-it-through-openrouter-one-key)).
   Otherwise `ANTHROPIC_API_KEY` for the Claude stages plus `OPENROUTER_API_KEY` for DeepSeek in
   the lean tier. No key? Use the manual provider: the runner writes `prompts/<stage>.md` and
   reads `outputs/<stage>.json`, so an app session that can read and write files in the run
   folder can answer each stage. Keys come from your own secret store; never put one in a file.
3. **Data accounts** for research (steps 10-20): a web search tool, a backlink and keyword tool
   (Ahrefs or similar), and Google's Knowledge Graph API. Budget about $0.50 of data per audit.
4. **Your own fleet** in [config/agents.json](config/agents.json): which running agent picks up
   each function's to-dos and who chases them. A function with no running agent fails the export.

## Tiers

| Tier | Frontier model does | Everything else | Planning* | From a ledger† |
|---|---|---|---:|---:|
| `lean` | final review (Opus 5.5, 1 pass) | Gemini Flash-Lite, GPT-6.1 Terra, DeepSeek V4.1 Flash, Sonnet findings | ≈ $2.70 | ≈ $0.62 |
| `standard` | findings + review (Opus 5.5, ≤ 2 passes) | Haiku harvest and fixes, Sonnet identity/score/pages/actions | ≈ $5.40 ($4.70 batched) | ≈ $1.26 |
| `muse` | findings + review (Opus 5.5) | pages and actions drafted in an app session's own subscription | ≈ $4.20 | ≈ $0.80 |
| `enterprise` | findings + review (Fable 5.1, ≤ 3 passes) + a person's read | Opus drafting, Sonnet harvest | ≈ $17.80 | ≈ $2.99 |
| `openrouter` | the standard tier's models, all through one OpenRouter key | — | ≈ $5.40 | ≈ $1.26 |
| `openrouter-lean` | final review (Opus 5.5, 1 pass) | Sonnet identity, score and the eight findings; DeepSeek V4.1 Flash pages, actions and fixes — one key | ≈ $2.90 | ≈ $0.71 |
| `openrouter-budget` | none — **experimental, not measured** | Grok 4.7 judgment, DeepSeek drafting, GPT-6.1 Sol review; Sonnet only if a cheaper model fails twice | ≈ $2.20 | ≈ $0.49 |
| reference | the Oct 23 all-Claude Cowork run, measured tokens at list price | — | $281 ($301 with its website package) | — |

*Planning estimate: the stage budgets in [config/routing.json](config/routing.json), research
included (about $0.50 of every tier is data: SERP, backlinks, keywords), sized generously.
†From a ledger: one pass from an existing evidence ledger (stages 30-80), counted from the
prompts and replies of a real 20-page audit (`measured_profile` in routing.json) with one fix
round and one review pass; `cost` also prints a worst case (three fix rounds, every review
pass, 25% retries). The review and fix sizes in it are assumptions until the first live run.
Either way `run.json` logs the real cost of every call. Claude prices verified 2026-11-04;
OpenRouter prices read from OpenRouter's own models list the same day; others from dated
third-party tables — re-check before quoting. All tiers run the same gates; the lean tiers use
lower density thresholds (`gates.TIERS`). Every tier has a spending cap (`max_usd`).

**Confidential briefs never reach a flagged model.** When `brief.json` lists `do_not_print`
items, the router skips any model marked `"confidential_ok": false` (DeepSeek and Qwen, after
the Oct 25 bake-off) on the first draft, on every fix round and on the review, and uses the next
safe rung on the tier's ladder. Through OpenRouter such a run also accepts only
zero-data-retention endpoints; if a model has none, the audit holds rather than fall back.

## Run it through OpenRouter (one key)

One OpenRouter key reaches Claude, DeepSeek, GPT and Grok, with one bill. OpenRouter passes model
prices through with no markup and charges a fee when you buy credits
([its FAQ](https://openrouter.ai/docs/faq#pricing-and-fees)); Claude's per-token prices there match
Anthropic's (OpenRouter's models list, 2026-11-04). So the `openrouter` tier is the standard tier
on one key, and `openrouter-lean` is the few-dollar tier. What the kit does on every call:

- asks only for providers that do not collect prompts (`provider.data_collection: "deny"`), and
  zero-retention endpoints only (`provider.zdr: true`) when the brief is confidential;
- records the charge OpenRouter reports in the reply, not an estimate, in `run.json`;
- retries rate limits and server errors (honouring `Retry-After`), stops at once on a bad key or
  empty credits, and stops the whole run at its spending cap — a held audit says why;
- writes pages 3-19 in four calls that share a cached prefix, because a real audit's pages run
  about 19,000 output tokens, more than one reply should carry.

```bash
export OPENROUTER_API_KEY=...              # from your own secret store; never commit it
python -m factory20 openrouter-check       # every route still listed, at the prices assumed
python -m factory20 init runs/demo --from-demo
python -m factory20 run runs/demo --tier openrouter-lean --max-usd 3
```

**At volume:** the GitHub Actions workflow *Audit Factory on OpenRouter* runs the public demo
audit on any tier with a cap you choose, using the repository secret `OPENROUTER_API_KEY`, and
keeps the PDF and receipts for 30 days. It runs only when someone with write access starts it;
on pull requests it only re-checks models and prices. Real client audits belong in a private
repository or on your own machine, never in a public workflow.

**Status, 2026-11-04:** the adapter is tested against a local stand-in for OpenRouter's API
(20 tests: request shape, privacy flags, retries, empty credits, the cap, page batches, whole
runs on each one-key tier) and every route is checked against OpenRouter's live models list. A
live OpenRouter run of this kit has not happened yet; the first one is next, and its bill and
judge score go into [docs/CALIBRATION.md](docs/CALIBRATION.md). Earlier evidence: on Oct 27 a
Claude-researched 20-page audit was replayed on DeepSeek V3.2 through OpenRouter for $0.018 of
drafting — the diagnosis held, but its score ran 5 points generous and one citation was wrong,
which is why the score clamps and the Claude review sit around the cheap drafting.

## Running a real audit

```
runs/<subject>/
  brief.json        subject, goal, prepared_for, prepared_by, dates, palette,  ← you write
                    do_not_print (confidential numbers, embargoed titles, private names; gate G74)
                    allowed_phones (the business's own listed numbers; gate G71)
  ledger.json       stages 10-20 (collect + harvest) or an existing ledger
  identity.json  score.json  synthesis.json  pages.json  actions.json         ← stages 30-70
  audit.json  gate.json  audit.pdf  audit.pdf.render.json  review.json  run.json
```

`python -m factory20 init runs/<subject> --ledger L --brief B` makes the folder;
`python -m factory20 run runs/<subject> --tier standard` reuses any stage file already present,
calls each missing stage's model from `routing.json`, checks the output, retries once with the
failure list and escalates one rung if it still fails. Then it assembles, gates and renders,
runs up to three fix rounds (pages 1-2 go back to the findings model, pages 3-19 to the fix
model), and finishes with the fresh-context review: `READY` needs zero S0/S1 findings. The
verdict is `READY` or `HOLD`; `--no-review` stops after the gates (`REVIEW_READY`).
`--max-usd` overrides the tier's spending cap; reaching it holds the audit with the amount spent.

## Quality control

1. **Gates (free, every draft):** 39 content gates (28 must pass, 11 warn) — page structure,
   cited ids that exist in the ledger and at least three per page, namesake leakage, insight-card
   anatomy, the page-2 word budget, headline claims, buzzwords, density, specificity, a visual on
   every page, identity, score calibration, the action contract, approval before any client-facing
   change, privacy (including the brief's do-not-print list), the install QR — plus 5 render gates
   (3 must pass, 2 warn) for page count, overflow, fill, links and a decoded QR. Every message says
   what to fix; an overflow says by how much and which card is tallest. `HOLD` never ships.
2. **One structured frontier review** ([stages/80-review.md](stages/80-review.md)) on the exact
   final files, in a fresh context that never saw the drafting: twelve judgment checks code cannot
   do, S0-S3 severity, a second pass only if S0/S1 was found. For enterprise audits and the pilot,
   a second, different model reviews too.
3. **Monthly calibration:** a person grades three audits on the same twelve checks; any
   disagreement becomes a gate or a card change. The first calibration uses three anchor audits
   whose grades are already agreed, which is the reviewer calibration the house audit rule asks for.

## Files

| Path | What |
|---|---|
| `factory20/` | ledger, scoring, gates, renderer, components, cost, router, pipeline, OpenRouter check, Basecamp export, CLI |
| `stages/` | the ten stage cards any model can follow |
| `config/routing.json` | prices, stage budgets, tier → model routing, escalation ladder, confidential flags |
| `config/agents.json` | which running agent picks up each function's to-dos, and who chases them |
| `schema/audit.schema.json` | the `audit.json` contract |
| `fixtures/demo/` | a complete SYNTHETIC 20-page exemplar (every fact invented) |
| `docs/CALIBRATION.md` | the measurements behind every threshold, and the blind tests |
| `../tests/test_audit_factory.py` | 70 tests: every gate has a failing mutation |
| `../tests/test_audit_factory_openrouter.py` | 20 tests: the OpenRouter path against a local stand-in for its API, no key, no spend |
| `../.github/workflows/audit-factory-openrouter.yml` | the price check on pull requests, and the manual demo run on one OpenRouter key |
