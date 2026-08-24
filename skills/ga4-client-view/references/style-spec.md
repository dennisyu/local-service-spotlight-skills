# GA4 Client-View — Display Standard

The canonical look of page 1. `render_page1.py` already implements the palette and
components; this file is the *rule set* for applying them consistently, so every
client's page 1 reads as one product. Source: Dennis's feedback across the beta
threads (Aug 2026).

## Palette (do not introduce new colors)

```
--brand #0e7490   --brand-d #0b5563     (primary / trend / bars)
--good  #15803d / soft #dcfce7          (green)
--warn  #b45309 / soft #fdf0d5          (amber)
--bad   #be123c / soft #fde7ec          (red)
--muted #64748b                         (grey / flat only)
```

## 1. Stoplight system — red / yellow / green, always

- **Red** = critical, broken, or **missing/untracked** — a `$0` where money should
  be, an untracked form, a dropped key event. A zero that means "we're blind here"
  is red, not grey.
- **Yellow** = watch / needs confirmation / hazy.
- **Green** = healthy / producing / resolved.
- **Grey** = flat (no change) only. Never used to soften a real red.

Applied in three places, all driven by the spec's `state` fields:
- **Pills** — `state` → `d-up`/`d-dn`/`d-wn`/`d-fl`. A missing metric shows an amber
  or red state, never a blank.
- **"What stands out" flags** — `state` → green ✓ / amber ! / red ↓.
- **"What to do next"** — the first move carries the `start` chip; ownership is shown
  per item.

Rule of thumb: if the line says "isn't tracking," "missing," "0," "dropped," or
"broken," its marker is **red**.

## 2. Prepared by (human owner)

`prepared_by: {name, role, photo}` renders top-right: a round avatar + name + role.
Every page names the human in charge (e.g. Riley for Fairmount). Photo optional;
without it, name/role text still shows.

## 3. Client logo

`logo` renders top-left beside the eyebrow + client name, embedded as a data URI.
Falls back to the styled client name if absent. Keep the brand top-bar regardless.

## 4. Charts — the same two, every client

- **Left: 13-week trend** of the primary conversion (line + area, direct-labeled
  peak and endpoint). Endpoint goes red only on a genuine decline (`last_state`).
- **Right: channel breakdown** (fixed-track horizontal bars, single-hue, deeper for
  larger magnitude; value label + optional right annotation).
- A **map visual** (local rankings or job-location dots) is a future addition —
  GA4 doesn't carry rank positions or job addresses, so it waits on a data source.
  If trustworthy city-level lead geography exists, an interim bubble-map of leads by
  city is the fallback. Not rendered until that source is decided.

## 5. Action ownership — who does what

Every `todo` item names an owner: `start` (the single first move), `us` (we're on
this), or a named `client` owner. No generic "you." One `start` per page.

## 6. Source-citations footer

`citations` renders a footer: project link · GA4-data link · report date · prepared-by.
Cite where the project lives and where the live data is, always.

## 7. Voice — "we," never "you / they"

All page-1 copy (pulse, callout, flags, actions) uses "we" to show we're on the
client's team. "We're getting your phone leads tracked to a source," not "your leads
aren't tracking." No em dashes anywhere (use commas, periods, colons, parentheses).

## 8. Exec-summary structure (locked order)

Header (logo · client · prepared-by · period) → one-paragraph pulse → 4 KPI pills →
optional callout → the two charts → "What stands out" (stoplight flags) → "What to
do next" (owned checklist, one `start`) → citations footer. Identical across clients.

## 9. Reconciliation with the Success Tracker (Dennis's six-phase model)

The exec-summary order above is confirmed against the Local Service Spotlight Success Tracker.
Carry these principles from it:

- **Plumbing first.** Phase 1 of the six-phase engine (Plumbing → Goals → Content →
  Targeting → Boosting → Optimization) is tracking/data-trust. Lead with it. A client
  with no lead tracking (or a broken tag) is "stuck at Phase 1" — frame the report
  around finishing the plumbing, not around numbers we can't trust yet.
- **Real outcomes over vanity ("MRI, not witch doctor").** Where a POS/revenue-tied
  number exists (tracked job value, orders, revenue), **feature it** — it is the money
  number, more important than sessions or vanity counts. Never headline likes/followers.
- **Stoplight = check-engine light.** Dennis's Standards-of-Excellence thresholds are a
  check-engine light; our red/yellow/green pills are the same idea. Red when a number
  trips the wire (missing tracking, a metric past its threshold).
- **Owned actions, our side and theirs.** Every phase has an owner on our team and the
  client's. That is the owned "what to do next": `us` vs. a named client owner.
- **Prepared by a real human.** The responsible person's name/face on the report.

## 10. Locked consistency rules (v1.1 — 2026-08-20)

Every report obeys these so they read as one product. No per-client deviation.

1. **Pills: exactly four, always** — Leads · Calls · Forms · Lead rate (or the model's
   named equivalents). Never swap a pill for something else.
2. **Revenue goes in the top summary, not a pill.** When the client has a POS/revenue
   number (tracked job value, orders, revenue), render it as the `outcome` strip
   directly under the pulse — a green highlighted band. Clients without one simply omit
   it; the four pills stay identical.
3. **Chart titles are fixed** — left "Weekly leads · {13 weeks | recent weeks}", right
   "Leads by channel". When data forces a short trend or a tracked-vs-untracked split,
   keep the title and explain in the one-line caption; never rename the chart.
4. **Voice is "we," not "you."** Lead with "we"/"the account"; reserve "you/your" for the
   direct ask in "what to do next." No "You generated…".
5. **Owned actions carry one of two tags** — `us` renders **✓ we're on this**; `client`
   renders **→ {contact}** (the arrow). Show at least one of each where the MAA supports
   it. `start` is the single first move (no tag).
6. **The tracking gap is red.** The standing "no source on calls" / "no lead tracking"
   item is the `callout` with `state:"bad"` (red-toned) — the incomplete Phase-1 plumbing,
   surfaced red per "missing = red." One red callout per report; don't also duplicate it
   as a red flag.
7. **Prepared-by is our responsible human** (Dennis's intent), name shown, photo when we
   have it. The client contact appears only as a `→` action owner, never as prepared-by.
8. **Logo** embeds from a per-client asset file when we have one; otherwise the styled
   client name. Auto-grabbing from the client site is unreliable inside the cloud sandbox
   (image bytes are blocked), so logos are a one-time per-client file the team supplies
   (or sourced when this layer runs on-device).
