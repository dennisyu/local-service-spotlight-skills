# Stage cards — how any agent produces a frontier-grade 20-page audit

Each card is one job, small enough for any model to hold in full. Run them in order. Every
stage reads files and writes files in one run folder; no stage waits on another agent.

| # | Card | Output file | Judgment? | Default model (standard tier) |
|---|---|---|---|---|
| 10 | `10-collect.md` | `captures/`, `sources.jsonl` | no — code | none (scripts + APIs) |
| 20 | `20-harvest.md` | `ledger.json` rows | no | Haiku 5.5 / Gemini Flash-Lite |
| 30 | `30-identity.md` | `identity.json` | **yes** | Sonnet 5.5 |
| 40 | `40-score.md` | `score.json` | **yes** (code clamps it) | Sonnet 5.5 |
| 50 | `50-synthesis.md` | `synthesis.json` | **the frontier slice** | **Opus 5.5** |
| 60 | `60-pages.md` | `pages.json` | no | Sonnet 5.5 · DeepSeek · Muse session |
| 70 | `70-actions.md` | `actions.json` | no | Sonnet 5.5 · Muse session |
| — | `python -m factory20 gate` + `render` | `gate.json`, `audit.pdf` | code | none |
| 80 | `80-review.md` | `review.json` | **frontier** | **Opus 5.5** (Fable for enterprise) |
| 90 | `90-deliver.md` | filed package, Basecamp to-dos | no | any agent |

## The five rules that close the gap

1. **Write content, never layout.** You fill `audit.json` blocks; the renderer draws every
   chart, card, badge and footer. A cheaper model cannot out-design the template, and does
   not need to.
2. **Every sentence carries a fact.** A number, a date, a name or a source in nearly every
   sentence. "Strong presence" is not a finding; "386 reviews at 4.9, 61% about claims" is.
3. **Finding → proof → so → action.** Every insight states the surprising fact, shows the
   proof with evidence ids, says what it changes ("So:"), and names the action id.
4. **UNKNOWN is honest, not a hiding place.** Mark what was not checked, but a summary that
   is mostly UNKNOWN means research is unfinished — go back to stage 10, do not write around it.
5. **The gates are the spec.** Run `python -m factory20 gate` after every draft. Fix every
   FAIL and WARN before asking for review. The frontier reviewer only sees work that already
   clears the mechanical bar.

## Who runs it

One runner owns a whole audit end to end: a Claude Code or Cowork session, Muse (Happy), a
ChatGPT session, a cron job or a person on a laptop. The runner calls cheaper models for
stages 20, 60 and 70 and the frontier model for 50 and 80 (via API, or by pasting the card
into a frontier chat when no key is available). **Never split stages across agents through
repo notes** — the October cheap-lane pipeline stalled ten days because two of its three
"lanes" were not running processes.

## Inputs you need before stage 10

Subject name and any known handles, owned domains, city and company; the client's stated goal
if given; delivery destination (Basecamp project, Drive folder). Missing goal is fine: infer
it, label it INFERRED, and continue.

For a local business, list its own published phone numbers in `brief.json` → `allowed_phones`
so name-address-phone checks can print them; gate G71 blocks every other number.

Put anything that must never print in `brief.json` → `do_not_print`: a confidential investor
figure, an embargoed book title, a private partner's name. Gate G74 fails the audit if any of
them appears on a page or in the action register, and its message never repeats them. In the
2026-10-25 bake-off on one evidence packet, two cheap models printed exactly these (a
confidential investor detail and an embargoed title) while the frontier models did not; the
list turns that judgment into a check any model passes.
