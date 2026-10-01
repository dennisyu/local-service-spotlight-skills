# Content Factory X-ray schema

One JSON (or YAML) file is a snapshot of **one** business, **one** project, or
**one** piece of content. An agent fills the file from evidence, then runs
`scripts/render_xray.py` to draw the X-ray.

This is a status and effectiveness picture. It is not a second Content Factory
and it does not rename Produce → Process → Post → Promote.

## When to generate one

- A Friday or Monday MAA needs a picture of what is done, in progress, or
  missing across the line.
- A client, project, or single recording is about to be reviewed.
- Dot (or any watch lane) flagged a stall and a human asked for the snapshot.
- You are writing a meta article and need to show which stations this run
  actually touched.

Do **not** generate an X-ray to decorate a page. Do **not** invent metrics to
fill empty cells. Missing is a valid state. Example files in `examples/` are
labeled `data_class: example` and must stay labeled that way.

## Command

```bash
python3 skills/content-factory/scripts/render_xray.py \
  skills/content-factory/examples/xray-business.example.json \
  --out /tmp/xray-business
```

Writes `<id>.svg`, `<id>.html`, and `<id>.json` (the normalized snapshot) into
`--out`. Add `--png` when a Chromium binary is on PATH and you need a PNG.

## Top-level object

| Field | Type | Required | Notes |
|---|---|---|---|
| `schema_version` | string | yes | `"1.0"` |
| `kind` | string | yes | `business` \| `project` \| `content` |
| `id` | kebab-case string | yes | File stem and stable snapshot id |
| `title` | string | yes | What the reader is looking at |
| `subject` | string | yes | Business, project, or content name |
| `period` | string | yes | Dated window the metrics cover |
| `generated_at` | ISO date or datetime | yes | When this snapshot was built |
| `data_class` | string | yes | `example` or `observed`. Example files **must** be `example` |
| `disclaimer` | string | yes when `example` | Must contain `EXAMPLE DATA` |
| `owner_function` | string | yes | Function, not a person — `content`, `web`, `analytics`, `client-success`, `it` |
| `canonical_hub` | URL or null | no | Definitive article or site hub |
| `approval_gate` | string | yes | `dennis` for anything public or paid |
| `stages` | array | yes | Exactly the six stations below, in this order |
| `loop` | object | yes | How MAA Action feeds Produce |
| `articles` | array | no | Definitive and meta articles hanging off this snapshot |

## Locked stage ids

Use these ids and labels. Do not rename them.

| `id` | `label` | Factory? |
|---|---|---|
| `plumbing` | Plumbing | Before the factory |
| `produce` | Produce | Factory |
| `process` | Process | Factory |
| `post` | Post | Factory |
| `promote` | Promote | Factory |
| `perform` | Perform / MAA | After the factory |

## Stage object

| Field | Type | Notes |
|---|---|---|
| `id` | string | One of the locked ids |
| `label` | string | Must match the locked label |
| `status` | string | `done` \| `in_progress` \| `missing` |
| `effectiveness` | string | `working` \| `watch` \| `weak` \| `unknown` \| `missing` |
| `owner` | string | Named desk or lane from the fleet map — do not invent one |
| `lane` | string | `qwen` \| `muse` \| `astra` \| `kimi-codex` \| `grok-desk` \| `cursor` \| `claude-fleet` |
| `handoff_in` | string | Artifact + place (Drive, GitHub issue, Buzz, Basecamp) |
| `handoff_out` | string | Artifact + place |
| `metrics` | array | MAA numbers for this station. Empty is allowed |
| `subcomponents` | array | See below |

`effectiveness` is about **results**, not activity. A station can be `done` and
still `weak` if the MAA numbers are bad. A station can be `in_progress` and
`working` if the early numbers are already earning. `unknown` means the metric
is not connected — that is not zero.

## Subcomponent → task → articles

```
stage
  └── subcomponent      (Capture, Transcribe & mine, Definitive article, …)
        └── task        (one repeatable job)
              └── articles[]   kind = definitive | meta
```

| Field | On | Notes |
|---|---|---|
| `id`, `label` | subcomponent, task | kebab-case id, human label |
| `status` | both | `done` \| `in_progress` \| `missing` |
| `owner` | task | Named fleet seat |
| `skill` | task | Repo skill that owns the recipe, or null |
| `articles` | task | Zero or more `{kind, title, url, execution_id, status}` |

A **definitive** article is the reusable recipe or hub. A **meta** article is
one execution of that recipe. Do not count a meta article as a second recipe.

## Metric object

| Field | Type | Notes |
|---|---|---|
| `name` | string | Prefer `revenue`, `profit`, `clicks`. Others are allowed and sit after those three |
| `value` | number or null | Null when not connected |
| `unit` | string | `usd`, `clicks`, `leads`, `posts`, … |
| `source` | string | Where the number came from, or `example` |
| `example` | boolean | `true` on every invented illustration number |

Color coding (effectiveness of the metric itself):

| Band | When |
|---|---|
| `working` | The source says this number is doing the job |
| `watch` | Mixed or early; do not scale yet |
| `weak` | The source says this is failing |
| `unknown` | `value` is null or the source is missing |
| `missing` | The station was never run, so there is no number |

The renderer colors the station from its `effectiveness` field. It does not
infer a band from the raw number. An agent who invents a band to make the
picture pretty has forged the X-ray.

## Loop object

```json
{
  "metrics_summary": "EXAMPLE DATA — clicks and revenue for the period.",
  "analysis": "Why the numbers moved, in one or two sentences.",
  "action": "The 1–3 things that get produced next.",
  "feeds_produce": "The exact next capture or draft the Action requests."
}
```

## Example vs observed

- `data_class: example` — illustration only. Banner must read **EXAMPLE DATA**.
  Never present these numbers as a client's real MAA.
- `data_class: observed` — every metric names a real source and a date. Null
  stays null. Do not backfill.

The three files in `examples/` are example data. Copy the shape, not the
numbers.
