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
- Muse watch-and-ping (or any desk) flagged a stall and a human asked for the
  snapshot.
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
`--out`. Add `--png` when a Chromium binary is on PATH and you need a PNG; the
PNG is sized to the drawing, so nothing is clipped and there is no blank strip.

Exit codes: `0` rendered, `2` the snapshot failed validation (the reason is on
stderr), `1` the PNG step failed after the SVG and HTML were written.

Every station box grows to fit its text. Long task lists show the first four
tasks and `+N more`; long handoffs wrap to two lines; more than five metric
chips show `+N more`. Nothing is silently cut.

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
| `owner` | string | The desk accountable for the station, named in `fleet-orchestration.md` — do not invent one |
| `lane` | string | The seat doing most of the station's work: `qwen` \| `muse` \| `astra` \| `kimi-codex` \| `grok-desk` \| `cursor` \| `claude-fleet` \| `other` |
| `handoff_in` | string | Artifact + place (Drive, GitHub issue, Buzz, Basecamp) |
| `handoff_out` | string | Artifact + place |
| `metrics` | array | MAA numbers for this station. Empty is allowed |
| `subcomponents` | array | See below |

### Owner and lane are two different answers

`owner` answers "who is accountable" and `lane` answers "which seat does the
work". They differ on purpose. Austin's desk owns Plumbing while Muse on Spark
does the Google logins; Trenton's desk owns Process while Local Qwen drafts
and Astra reasons. Put the accountable desk in `owner`. A seat name
(`Muse / Happy`, `Kimi/Codex crons`, `Claude Fleet`) is allowed in `owner`
only when that seat owns the station outright. Astra or Dot is never an
`owner`: Dot is experimental and never the sole owner of anything critical, so
the accountable desk stays in `owner` and `astra` goes in `lane`.

The lane values are the seats from `pick-the-cheapest-capable-fleet-lane`, in
its cost order. `qwen` is free and comes first for offline bulk text that can
wait for a Mac. `muse` is the volume lane. Everything else is cost order 3:
`astra` (Dot plus specific ChatGPT tasks), `kimi-codex` (crons already live),
`grok-desk` (judgment, publishing decisions, routing), and the rule's "any
other seat" — `cursor`, `claude-fleet`, or `other` for a seat the rule does not
name (a tool run from a desk, for example Descript). Name that seat in the task
label when you use `other`. Do not add a lane value to this list; the rule
picks the seat, this file only records it.

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
| `id`, `label` | subcomponent, task | kebab-case id, non-empty human label. Both are validated |
| `status` | both | `done` \| `in_progress` \| `missing` |
| `owner` | task | The desk accountable for the task, from the fleet map. Required |
| `lane` | task | Optional. The seat that runs this task when it differs from the station's lane. Same values as the stage `lane` |
| `skill` | task | Repo skill that owns the recipe, or null |
| `articles` | task | Zero or more `{kind, title, url, execution_id, status}` |

Article fields: `kind` is `definitive` or `meta`; `title` is non-empty;
`status` uses the same three values; `url` is a string or null. A `meta`
article must carry an `execution_id`, because a meta article records one
execution (`every-task-execution-writes-a-meta-article`). The renderer rejects
a meta article without one.

A **definitive** article is the reusable recipe or hub. A **meta** article is
one execution of that recipe. Do not count a meta article as a second recipe.

## Metric object

| Field | Type | Notes |
|---|---|---|
| `name` | string | Prefer `revenue`, `profit`, `clicks`. Others are allowed and sit after those three |
| `value` | number or null | Null when not connected. A string is rejected; a number in quotes is not a number |
| `unit` | string | `usd`, `clicks`, `leads`, `posts`, … `usd` values render with a `$` sign |
| `source` | string | Where the number came from, or `example` |
| `example` | boolean | `true` on every invented illustration number. The chip then ends in `*`, and the legend says what `*` means |

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
numbers. Their owner and lane choices are one valid reading of the fleet map
for that scenario, not a roster: check `fleet-orchestration.md` for the station
you are describing before you copy a name.
