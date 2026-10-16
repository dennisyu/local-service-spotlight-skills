# Tool recipes — exactly what works

Verified 3 August 2026. Copy these shapes; the failure modes below are all things
that actually happened, not hypotheticals.

---

## 1. ChatGPT with web search — best source capture

`mcp__remote-devices__dataforseo__ai_optimization_chat_gpt_scraper`

```json
{
  "keyword": "Who is Paul Ryazanov?",
  "language_code": "en",
  "location_name": "United Kingdom",
  "force_web_search": true
}
```

Returns items of `type: chat_gpt_text` / `chat_gpt_table` / `chat_gpt_ad`, each with:

- `sources[]` — `{title, domain, url, source_name, publication_date}`. **This is the citation list.**
- `brand_entities[]` — `{title, category, markdown}`. `category` is one of `people`,
  `company`, `local_business`, `tv_show`… and `title` is the model's own one-line
  characterisation of the entity. For a person audit this is gold: it is literally
  the model's summary of who they are. Capture it verbatim.
- `chat_gpt_table` items carry a structured `table.table_content` — use it when the
  answer is a ranked agency list, since it gives you the competitor set for free.

Always set `location_name` to the client's actual market. "Best ecommerce agency in
Manchester" returns a different answer from a US IP.

## 2. Gemini / Perplexity / Claude

`mcp__remote-devices__dataforseo__ai_optimization_llm_response`

```json
{
  "llm_type": "perplexity",
  "model_name": "sonar-pro",
  "user_prompt": "Who is {name}? What is he known for, and what sources support that?",
  "web_search": true
}
```

Get valid model names first with `ai_optimization_llm_models` — it **requires**
`llm_type`; calling it bare throws a validation error. Verified working as of Aug 2026:

| llm_type | model_name | Notes |
|---|---|---|
| `perplexity` | `sonar-pro` | Richest citation list — 20+ numbered sources on a person query. Best single engine for evidence-base mapping. |
| `gemini` | `gemini-3.5-flash` | Returns `annotations[]` grounding each *sentence* to a source. Use it to show which claim rests on which domain. |
| `claude` | `claude-sonnet-4-5` | Fewest but highest-precision citations. Good hallucination control check. |
| `chat_gpt` | — | Prefer the scraper above; it captures `brand_entities`. |

Asking "…and what sources support that?" measurably increases the number of
citations returned. Keep that clause in every identity prompt.

Cost per call runs roughly $0.03–$0.07. A full 9-prompt audit is well under a dollar.

## 3. Ahrefs — the AI citation index

`mcp__Ahrefs__site-explorer-ai-responses-count`

```json
{
  "target": "example.com",
  "mode": "subdomains",
  "select": "chatgpt,google_ai_overviews,google_ai_mode,gemini,perplexity,copilot,grok",
  "output": "json"
}
```

Valid select fields are **only** those seven (plus `google_ai_overviews_keywords`,
`google_ai_mode_keywords`). Passing `chatgpt_citation_links` errors out — the API
returns `{citations, pages}` per engine automatically.

Costs 105 units per target. Expect **0 for personal domains** — see the
troubleshooting table in SKILL.md before you report that as a result.

## 4. Ahrefs — referring domains, spam-filtered

**This is the call that changes what you report.** `is_spam` is a selectable field
and a filterable one.

```json
{
  "target": "example.com",
  "mode": "subdomains",
  "select": "domain,domain_rating,first_seen,positions_source_domain,links_to_target",
  "where": {"field": "is_spam", "is": ["eq", false]},
  "order_by": "first_seen:desc",
  "history": "live",
  "limit": 100,
  "output": "csv"
}
```

- The API caps at **100 rows per call** regardless of `limit`. Page with
  `first_seen` ranges in `where`, or just pull the clean set — on a spam-hit
  profile it is small enough to fit in one call.
- Get the true total from `site-explorer-backlinks-stats`, then
  `spam = live_refdomains − clean count`.
- Spam signature to recognise by eye: `.shop` / `.store` TLDs, keyword-salad
  hostnames (`tier-one-and-domain-rating-trusted-exchange.store`), exactly 1 link
  to target, `positions_source_domain: 0`, DR clustered at 20/25/31/32, all
  first-seen inside a few weeks.
- Report both numbers. "27 clean of 407 live" is honest; quoting either alone is not.

## 5. Ahrefs — trend series

- `site-explorer-domain-rating-history` — `{target, date_from, date_to, history_grouping: "monthly"}`
- `site-explorer-refdomains-history` — same shape. **Note this one is not
  spam-filtered**, so a hockey stick here may be entirely spam. Cross-check against
  the clean list before you put it in a chart with a positive framing.
- `site-explorer-metrics` — org keywords, top-3 keywords, traffic, traffic value.
  Monetary values are **USD cents** — divide by 100.

## Known dead ends — do not spend time here

| Call | What happens |
|---|---|
| `brand-radar-*-entities` without `prompts: "ahrefs"` | `Custom prompts require a report_id` |
| `brand-radar-*-entities` with `prompts: "ahrefs"` | `Missing addon: Brand Radar ["Chatgpt"]` — per-engine paid add-on |
| `ai_opt_llm_ment_agg_metrics` with a person's name as `keyword` | Word-matches. "Dennis Yu" → *Yu Yu Hakusho*, Dennis Trillo, an anime series. Silent, confident, wrong. |
| Ahrefs GSC tools (`gsc-*`) for a domain with no Ahrefs project | Require `project_id`. Check `management-projects` first; if the client's domain is not a project, GSC data has to come from Search Console directly. |
| `ai_optimization_llm_models` with no `llm_type` | Validation error — the parameter is required. |
