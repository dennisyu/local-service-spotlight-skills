# Audit Factory 20 — frontier-grade 20-page audits at volume prices

**What this is, in one paragraph:** our best audits come from Claude, but a Claude-only audit
costs about $360-650 in API terms and burns a $200 plan in two days. This factory splits the
work so a frontier model does only the two jobs that need judgment — finding the insights and
reviewing the final file — while cheaper models, plain code and Muse do everything else. The
design and the quality checks live in code, so any model fills in the same proven template and
gets told exactly what to fix. Standard tier: about **$5 per audit**.

## Why Claude's audits were better (and why that is fixable)

Measured on finished PDFs ([docs/CALIBRATION.md](docs/CALIBRATION.md)): frontier audits carry
460-470 words and 95-100 specific numbers per page with evidence on every page; thin ones carry
200-270 words and 8-39 numbers. Four causes, each with a fix here:

| Cause | Evidence | Fix in this kit |
|---|---|---|
| **The bar was tacit** — rules said what not to do, not how to produce insight | a 148 KB skill, ~85% house rules unrelated to the audit run | short stage cards, generation first ([stages/](stages/)) |
| **Every audit was hand-designed** — only a frontier model could lay out 20 bespoke pages | Muse reached frontier density only after writing a page-level visual bar | a fixed component renderer: models write `audit.json`, code draws |
| **Research stopped early** | same subject: Opus tried 4 name spellings and scored; Sonnet stopped at a namesake | a mandatory query-variant protocol ([stages/10-collect.md](stages/10-collect.md)) |
| **QA was open-ended and expensive** | one audit: 7 Opus review rounds ≈ 40% of 1.1 billion tokens | free deterministic gates first, then one structured frontier pass |

And one cause that was not about models at all: the October cheap-lane pipeline filed work
orders for Gemini and Cursor "lanes" that were never running processes; ten days and five
chases later nothing had happened. **One runner owns an audit end to end.**

## Quickstart (no keys needed)

```bash
cd audit-factory
pip install -r requirements.txt && python -m playwright install chromium   # skip the second step if Chromium exists
python -m factory20 gate   fixtures/demo/audit.json --ledger fixtures/demo/ledger.json
python -m factory20 render fixtures/demo/audit.json --ledger fixtures/demo/ledger.json --out demo.pdf
python -m factory20 measure demo.pdf any-other-audit.pdf      # grade any agent's PDF
python -m factory20 cost --per-month 200                       # per-stage and monthly cost by tier
python -m factory20 basecamp fixtures/demo/audit.json --ledger fixtures/demo/ledger.json --out todos.json
```

## Tiers

| Tier | Frontier model does | Everything else | Cost / audit* |
|---|---|---|---:|
| `lean` | final review (Opus 5.5, 1 pass) | Gemini Flash-Lite, GPT-6.1 Terra, DeepSeek V4.1 Flash, Sonnet synthesis | ≈ $2.70 |
| `standard` | synthesis + review (Opus 5.5, ≤ 2 passes) | Haiku harvest, Sonnet identity/score/pages/actions | ≈ $5.40 ($4.70 batched) |
| `muse` | synthesis + review (Opus 5.5) | drafting inside Muse's own session at zero marginal cost | ≈ $4.20 |
| `enterprise` | synthesis + review (Fable 5.1, ≤ 3 passes) + a human read | Opus drafting, Sonnet harvest | ≈ $17.80 |
| reference | the Oct 23 all-Claude Cowork run, API-equivalent | — | $364-647 |

*Token budgets per stage are in [config/routing.json](config/routing.json); about $0.50 of every
tier is data (SERP, backlinks, keywords). Claude prices verified 2026-11-04; others from dated
third-party tables — re-check before quoting.

## Running a real audit

```
runs/<subject>/
  brief.json        subject, goal, prepared_for, prepared_by, dates, palette,  ← you write
                    do_not_print (confidential numbers, embargoed titles, private names; gate G74)
  ledger.json       stages 10-20 (collect + harvest) or an existing ledger
  identity.json  score.json  synthesis.json  pages.json  actions.json         ← stages 30-70
  audit.json  gate.json  audit.pdf  audit.pdf.render.json  review.json  run.json
```

`python -m factory20 run runs/<subject> --tier standard` calls each stage's model from
`routing.json`, checks the output, retries once with the failure list, escalates one rung if it
still fails, then assembles, gates and renders. Set `ANTHROPIC_API_KEY` and `OPENROUTER_API_KEY`
(one key covers DeepSeek, Gemini and GPT). For an app session with no key — **Muse, ChatGPT or
Claude.ai** — use the `muse` tier: the runner writes `prompts/<stage>.md`, the session answers it
into `outputs/<stage>.json`, and the run continues. The same agent does both halves, so nothing
waits on another agent.

## Quality control

1. **Gates (free, every draft):** 40 content gates — page structure, evidence linkage, namesake
   leakage, insight-card anatomy, the page-2 word budget, headline claims, buzzwords, density,
   specificity, a visual on every page, identity, score calibration, the action contract,
   privacy (including the brief's do-not-print list), the install QR — plus 5 render gates for
   page count, overflow, fill, links and a decoded QR. Every message says what to fix; an
   overflow says by how much and which card is tallest. `HOLD` never ships.
2. **One structured frontier review** ([stages/80-review.md](stages/80-review.md)) on the exact
   final files: twelve judgment checks code cannot do, S0-S3 severity, a second pass only if S0/S1
   was found.
3. **Monthly calibration:** a person grades three random audits on the same twelve checks; any
   disagreement becomes a gate or a card change.

## Files

| Path | What |
|---|---|
| `factory20/` | ledger, scoring, gates, renderer, components, cost, router, pipeline, Basecamp export, CLI |
| `stages/` | the ten stage cards any model can follow |
| `config/routing.json` | prices, stage budgets, tier → model routing, escalation ladder |
| `schema/audit.schema.json` | the `audit.json` contract |
| `fixtures/demo/` | a complete SYNTHETIC 20-page exemplar (every fact invented) |
| `docs/CALIBRATION.md` | the measurements behind every threshold |
| `../tests/test_audit_factory.py` | 60 tests: every gate has a failing mutation |
