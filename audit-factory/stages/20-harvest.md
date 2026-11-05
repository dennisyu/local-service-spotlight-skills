# Stage 20 — Harvest sources into ledger rows

You turn captured sources into evidence rows. **One fact per row, copied, not interpreted.**
You never score, rank or recommend in this stage.

## Output (JSON)

```json
{"items": [
  {"id": "V-E012", "topic": "reviews", "claim": "Share of reviews that mention an insurance claim",
   "value": "236 of 386 (61%) mention 'insurance', 'adjuster' or 'claim'",
   "source_url": "https://maps.example/vega-roofing", "source_name": "Google Business Profile",
   "published": "2026-11-02", "state": "OBSERVED", "evidence_class": "INDEPENDENTLY-CORROBORATED",
   "subject_match": "CONFIRMED", "polarity": "positive", "notes": "counted all 386 review texts"}
]}
```

## Field rules

- `id`: prefix letter for the subject + `-E` + three digits, never reused.
- `claim`: what the row establishes, in 4-12 words. `value`: the exact observed value with its
  numbers, dates and quoted wording. Keep numbers as written by the source.
- `state`: OBSERVED (the source shows it) · INFERRED (your arithmetic or a bounded synthesis —
  say how in `notes`) · UNKNOWN (checked, not established) · REPORTED (owner or private source).
- `evidence_class`: INDEPENDENTLY-CORROBORATED (a third party shows it) · PLATFORM-DATA (a
  measurement tool) · SELF-CLAIM (the subject's own site or profile says it) ·
  FIRM-UNATTRIBUTED (an unnamed company page or press release) · NOT-APPLICABLE.
  **A first-party bio is SELF-CLAIM even when you observed it directly.**
- `subject_match`: CONFIRMED only after stage 30 resolves identity; a same-name person goes in
  `ambiguous` with `subject_match: "AMBIGUOUS"` and is never used as proof.
- `published` is the source's date; the capture date lives in `sources.jsonl`.
- `polarity`: `positive` (proves something works or exists), `negative` (proves something is
  broken, missing, stale or lost) or `neutral`. Code uses it to stop a high score resting on
  evidence of failure; when you omit it, code guesses from the wording.

## Also write

- `conflicts`: when two sources disagree on the same fact (dates, counts, names, prices), one
  group per metric with every value and its source. Do not pick a winner.
- `unknowns`: each question you checked and could not answer, with what you checked.

## Self-check before you hand off

Every row has a URL or a private locator · numbers are copied exactly · no row contains advice
or adjectives like "strong" or "impressive" · every same-name result is in `ambiguous` ·
every disagreement is in `conflicts`.
