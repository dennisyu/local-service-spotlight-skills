# page1-spec — the JSON contract

`render_page1.py` consumes one JSON object (or a list of them, one per page). Every
field is DERIVED from the source MAA. See `example-fairmount.json` for a complete,
valid instance.

## Top-level fields

| Field | Type | Notes |
|---|---|---|
| `eyebrow` | string | Fixed: `"Website Performance · GA4"`. |
| `client` | string | Client display name (the big H1). |
| `subline` | string | One line: vertical · geography · `GA4 property {id}`. |
| `logo` | string \| null | Path to a logo image; embedded as a data URI. Null → styled name only. |
| `prepared_by` | object \| null | `{ "name", "role", "photo" }`. `photo` path optional. |
| `period` | string | e.g. `"Jul 16 – Aug 12, 2026"`. |
| `period2` | string | e.g. `"vs. prior 28 days"`. |
| `pulse` | string (HTML) | The business-pulse paragraph, "we" voice, `<b>` allowed. |
| `outcome` | object \| null | Revenue/POS strip under the pulse (rule 2). `{ "label", "value", "delta", "state", "sub" }`. Omit when the client has no revenue number. |
| `pills` | array[4] | KPI tiles — exactly four (Leads · Calls · Forms · Lead rate). See below. |
| `callout` | object \| null | `{ "k": heading, "body": HTML, "state": "bad"? }`. Use `state:"bad"` (red) for the tracking-gap callout (rule 6). Omit if the MAA foregrounds no single data-trust story. |
| `left_chart` | object | The 13-week trend — see Charts. |
| `right_chart` | object | The channel/lens breakdown — see Charts. |
| `flags` | array | "What stands out" — see below. |
| `todo` | array | "What to do next" — see below. |
| `citations` | object | `{ "project_url", "ga4_url", "date" }`. |

## Pills (exactly 4)

```json
{ "lab": "Calls", "val": "266", "sub": "163 line + 103 clicks", "delta": "▼ −3.6%", "state": "bad" }
```

- `state` drives the stoplight chip: `good` → green, `bad` → red, `watch` → amber,
  `flat` → grey. **A missing/untracked metric is `watch` (amber) with a `⚠` delta,
  or `bad` (red) when it means we're blind on the money question** — never a blank
  grey that hides the gap.
- `delta` is the literal chip text (include the arrow: `▲ ▼ ⚠`). Omit for no chip.
- Keep the four labels stable across clients where the model allows: Leads · Calls ·
  Forms · Lead rate (or the model's equivalents; an e-commerce store may show `—`
  placeholders and carry the story in the callout).

## Charts

**Trend (`left_chart`)** — the primary conversion over ~13 weeks:
```json
{ "type": "trend", "title": "Weekly leads · last 13 weeks",
  "values": [55,43,...,62], "hi_idx": 9, "last_state": "good",
  "first_lab": "13 wks ago", "last_lab": "last wk", "caption": "..." }
```
- `hi_idx` direct-labels the peak. `last_state:"bad"` colours the endpoint red **only
  when the MAA reads the latest move as a genuine decline**; otherwise omit (defaults
  to brand color).

**Bars (`right_chart`)** — channel (or model-lens) breakdown:
```json
{ "type": "bars", "title": "Leads by channel · last 28 days",
  "rows": [["Google Ads",78,"4.2%"],["Organic search",20,"4.1%"]],
  "maxval": 78, "labW": 104, "barTrack": 120, "caption": "..." }
```
- Each row is `[label, value, right_annotation]`. `right_annotation` is optional text
  (share, % change). `labW` widens for long labels; `barTrack` is the fixed bar
  width so the value and the right annotation never collide.

## Flags ("what stands out")

```json
{ "state": "good", "text": "<b>Job value up 105%.</b> ..." }
```
`state`: `good`→green ✓, `watch`→amber !, `bad`→red ↓. Any flag naming a tracking
gap or lost leads is `bad`.

## Todo ("what to do next")

```json
{ "role": "start", "text": "<b>Confirm which system feeds calls...</b>" }
{ "role": "us",    "text": "Pulling the source detail ..." }
{ "role": "client","text": "Keep leaning on Google Ads ...", "owner": "Riley" }
```
- `role`: `start` (the single first move, one per page), `us` (we're on this), or
  `client` (owner named via `owner`, or left generic). Route from the MAA's inline
  owner tags — do not invent an owner.

## Derivation mapping (MAA → spec)

| Spec field | MAA source |
|---|---|
| `pulse` | Business-pulse / bottom-line paragraph, trimmed to a confident lead. |
| `pills` | Headline number + companions (the "M" — the metrics the MAA opens on). |
| `callout` | A single foregrounded data-trust finding (off-domain checkout, spam-in-Direct, no tracking). |
| `left_chart.values` | The MAA's 13-week trend of the primary conversion. |
| `right_chart.rows` | The channel (or model-lens) Winners table, top rows. |
| `flags` | "What it means" points, each routed to a stoplight state. |
| `todo` | "What to do next" actions with their owner tags. |
| `citations` | Project URL, GA4 property URL, report date. |

If the MAA doesn't support a field, omit it (callout, a fourth flag) rather than
inventing. The Cardinal Rule governs every field.
