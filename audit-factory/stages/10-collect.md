# Stage 10 — Collect (code first, model last)

**Goal:** capture every public source a buyer, a search engine or an AI model would see, before
anyone writes a word. Thin audits are almost always thin collection: in a same-subject test,
the stronger model tried four name spellings and found the person; the weaker one stopped after
two searches and reported nothing. This card makes the persistence mandatory.

## Run every query variant (do not stop at the first namesake)

For a person: bare name · name + company · name + city · name + role · name in native script ·
every known handle spelling · the supplied profile slug as an anchor · the company alone ·
the company + city. For a company: legal name · brand name · each surface's name · domain ·
brand + city + category.

## Collectors (all scripted; record time, locale, signed-in state for each)

| Source | How | Save |
|---|---|---|
| Google SERP, desktop + mobile, subject's city | DataForSEO SERP (≈$0.002-0.004/query) | `captures/serp/*.json` |
| Knowledge Graph Explorer (subject, company, each ranked association) | https://localservicespotlight.com/knowledge-graph-explorer/ | `captures/kg/*.json` |
| Normal Google panel check (name and name + role) | SERP feature parse + screenshot | `captures/panel/*` |
| Owned site crawl (every page, status, title, schema, links, forms, embeds) | crawler + structured-data extract | `captures/site/*.json` |
| Lighthouse mobile, 3 runs median | Lighthouse CLI | `captures/lighthouse.json` |
| Google Business Profile, reviews (all text), BBB, Yelp, Angi | DataForSEO business data or export | `captures/reviews/*.json` |
| YouTube channel + per-video views/dates | YouTube Data API | `captures/youtube.json` |
| Podcasts, press, awards, talks | SERP + publisher pages | `captures/media/*.html` |
| Social profiles (public counts, last post date) | public pages | `captures/social/*.json` |
| Backlinks summary, referring domains, top pages | DataForSEO / Ahrefs | `captures/links.json` |
| Keyword volume for the buy-box topics | DataForSEO keywords | `captures/keywords.json` |
| AI engines: one known-item and one discovery prompt each (ChatGPT, Gemini, Perplexity, Claude) | live session, screenshot + cited URLs | `captures/ai/*` |
| Screenshots of every page you will cite visually | headless Chromium | `assets/*.png` |
| Private inputs only if authorized (intake form, photos, analytics) | owner share | `captures/private/*` (label REPORTED) |

Write `sources.jsonl`: one line per capture with `url`, `kind`, `captured_at`, `query`,
`locale`, `status`, `path`. A failed fetch is a row with `status: "blocked"` — an access
limit, not a finding.

Keep the full capture in `captures/` as evidence, but **crop or redact private fields in
screenshots before use**: whatever goes into `assets/` prints in the client PDF. Knowledge
panels list spouses and children; profiles show home addresses and personal phones. Crop to
the part you will cite and blank anything on `brief.do_not_print`. Gate G75 reads the images
with OCR and holds the audit on a hit, but it is a backstop (it misses stylised or tiny text).

## Done when

At least 120 sources for a person+company audit (60 for a micro business), every query
variant above run and logged, every review text captured, at least one AI known-item and one
discovery capture per engine, and screenshots for every visual you expect to cite.
