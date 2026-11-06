---
name: google-ads-client-view
description: >
  Render a finished Google Ads MAA into a client-facing report. Produces a
  markdown client view AND a paste-ready HTML version (built for Basecamp, works
  in any rich-text editor), both led by a one-paragraph summary, two 13-week
  trend charts (leads, cost per lead), emoji-flagged critical items, and a
  separated client to-do, with the full analysis rewritten in client
  language below (per the client ledger's render spec). It does NO new
  analysis: every line is DERIVED from the source MAA, never invented. Runs as
  the final step after the weekly MAA is written. Trigger on "render the client
  view", "Basecamp version of the MAA", "client report for {client}", or
  "client-facing version of this MAA". Google Ads only.
---

# Google Ads Client View, MAA Render Stage

## What this skill does

Takes a completed Google Ads MAA (from `google-ads-analyzer`) and produces the
client-facing layer that sits on top of it, in two formats:

1. A **markdown client view** (`{Client}_Client-View_{date}.md`), self-contained,
   with the two trend charts embedded as images. Reads cleanly in any markdown
   preview.
2. A **paste-ready HTML version** (`{Client}_Client-View_{date}.html`) whose body
   is rich text (headings, bold, bullets, blockquote, emoji), so it survives a
   copy-paste into a client comms tool. It is tuned for **Basecamp** (the markup
   is restricted to what Basecamp's editor keeps on paste), and the same
   constraints make it safe for most rich-text editors. The two charts are
   dragged in as PNGs.

The Full analysis section below the summary is **rewritten in client language**,
not reproduced verbatim. It is still a projection of the MAA (see the Cardinal
Rule), but it strips the internal material the client's render spec lists and
carries only the Actions with a client-visible outcome. The goal is to solve "too
dense for the average owner" by leading with a 30-second read and by filtering
the internals, not by adding new analysis.

**Size check:** the client view should run about one third of the MAA's length.
If it is over half the MAA's length, it has not been filtered. Cut again.

## What this skill does NOT do

- **No analysis.** It never diagnoses, re-weights, or second-guesses the MAA. If
  a finding is not in the MAA, it does not appear in the client view.
- **No edits to the source MAA.** The dated MAA is read-only here. The analysis
  artifact stays pure.
- **No metric invention, no severity reclassification.** See the Cardinal Rule.

## Where it sits in the pipeline

```
google-ads-analyzer  ->  {OUTPUT_DIR}/{Client}/{Client}_MAA_{date}.md
                                        |
                                        v  (final step, every week)
google-ads-client-view  ->  reads that frozen MAA + trend data
                        ->  emits the .md and .html client views + 2 PNG charts
```

It is the **last** step and runs **every** week (unconditionally). Unlike the
copy optimizer or LP auditor, which fire on a detected trigger and add expertise,
this runs always and adds presentation only.

---

## THE CARDINAL RULE: derive, don't invent

Every line in the client view must trace to a specific line in the source MAA. If
you cannot point to where the MAA says it, **delete it.**

This rule exists because the naive version of this layer invents client-friendly
claims the MAA never made (e.g. "phone tracking is solid" when the MAA's CRM
check actively *questions* lead quality), or frames an our-side structural item as
a client-facing crisis. Both are the failure mode of writing the summary as
original prose instead of projecting it from the analysis.

Concrete prohibitions:
- **Never add a metric** not present in the MAA.
- **Never upgrade a hedge into confidence.** If the MAA says "one caution, single
  week of data," the summary may not present that result as proven.
- **Never invent reassurance** ("tracking is solid", "everything's healthy").
- **Never editorialize on charts** ("lower is better", "how many leads the ads
  drove"). Label them with the plain metric name only. Owners know their business.
- **Never reclassify severity.** An our-side action stays our-side; only genuine
  client decisions go in "what we need from you" or the red flags.

---

## Step 1: Load the source MAA (read-only)

Read the latest dated Google Ads MAA for the client:
`{OUTPUT_DIR}/{Client Name}/{Client}_MAA_{YYYY-MM-DD}.md` (see `CONFIGURATION.md`
for `{OUTPUT_DIR}`). That MAA is the **only** source of findings, numbers, and
actions for the client view. If the client is multi-platform and the MAA bundles
several channels, use only the Google Ads section.

If a per-client spec exists (campaign list, top-N metric, target CPA), read it for
the chart target line. If no dated MAA exists for the period, stop, there is
nothing to render, build the MAA first.

**Read the client ledger's render spec before rendering.** Section 8 of the
client ledger (format: `../../shared/frameworks/ledger-template.md`) holds the
per-client render spec: action count norm, bullet norms, tone notes, status-dot
conventions, chart target line, and the strip list for the Full analysis
section. **The ledger overrides the defaults in this skill** wherever the two
disagree. If the ledger has no render spec yet, use the defaults here and note
that in the run.

## Step 2: Build the 13-week chart data

The charts plot history, so they need the trailing ~13 weeks, not just this week.
Preferred source, in order:

1. **`{OUTPUT_DIR}/{Client Name}/trend.csv`**, a per-client trend file you append
   to each week. Columns: `week,leads,cpl_week,cpl_30d`. This is the deterministic
   path, no prose parsing.
2. **Fallback:** if the trend file is absent, assemble the series by reading the
   `Conversions` and `CPA` lines from the trailing weekly MAAs in the client's
   output folder, oldest to newest, primary campaign. Be consistent about which
   campaign or account total you use, and match whatever the MAA's bottom-line
   paragraph uses so the chart and the summary agree. Write the assembled rows to
   `trend.csv` so the next run is deterministic.

Then run the bundled generator (it does the plotting; do not hand-draw SVG):

```
python3 scripts/render_charts.py \
  --data {trend.csv} \
  --outdir "{OUTPUT_DIR}/{Client Name}/" \
  --client "{Client display name}" \
  --date {YYYY-MM-DD} \
  --target {client target CPA; omit if unknown}
```

It writes `{slug}_chart_leads_{date}.png` and `{slug}_chart_cost-per-lead_{date}.png`.
Blank `cpl_week` / `cpl_30d` cells are skipped (zero-conversion or unreported
weeks). The target line is drawn only if `--target` is given. The script needs
`matplotlib` (`pip install matplotlib`).

**Sanity check:** the chart's latest points must equal the MAA's bottom-line
numbers (this week's CPA, the 30-day average). If they do not match, the trend
data is wrong. Fix it before continuing.

## Step 3: Project the summary (each section maps to the MAA)

Build the client view in this fixed order. The right column is the ONLY place
each section may draw from.

| Client-view section | Source in the MAA |
|---|---|
| Header + status dot (🟢/🟡/🔴) | Overall tone of the MAA. 🟢 on track, 🟡 watch, 🔴 needs attention. Do not overclaim a 🟢 if the MAA hedges. |
| **The bottom line** (1 paragraph) | The MAA's opening / bottom-line paragraph, lightly trimmed. Plain language, no QS/IS/CPA jargon above the fold. **Keep it confident: do not end the above-the-fold summary on a caveat.** On a strong week the client's first read should carry the win; a hedge like "bookings were light, we're keeping an eye on it" belongs down in the 🟡 section, not in the opening paragraph. Trim a trailing caveat sentence rather than leading the eye to it. |
| **The trend** (2 charts) | The PNGs from Step 2. Caption only if needed; no value judgments. |
| **What's working ✅** | The positive findings already stated in Analysis. Each bullet a real finding (e.g. "new ad drove 10 conversions at $21.49"), not a vibe. |
| **What needs attention 🔴 / 🟡** | Client-facing critical/decision items only. Use 🔴 only for something actively costing the client (budget cap losing leads, broken tracking) or a decision that cannot wait. An **our-side visibility gap**, e.g. "we can't yet confirm booked jobs", is 🟡 (watch), not 🔴: a caution, not a crisis. Our-side fixes do NOT go here at all. **When a 🟡 item is really an arrangement, not a problem, frame it as the arrangement.** Write the shared plan and the client's low-effort role in it ("we'll rely on you to flag it if lead quality dips"), not our deficiency ("we still cannot tie leads to jobs"). Same fact, calmer read. Drop the alarm-style bold headline when the item is a heads-up rather than a crisis. |
| **What we need from you 👉** | The **client-tagged** Action items (owner tagged inline in the MAA's single Action list). Keep the ask plus the one-line why. **Carry only genuine asks, do not pad.** One real ask is correct and beats three padded ones. A resolved former ask drops off; it does not get reworded to fill the section. |
| **What we did this week** | The **agency-tagged** Action items (staged dispatches, launches, negatives), phrased as done/in-progress, no action needed. |
| **Full analysis** | The MAA **rewritten in client language** per the ledger's render spec, metrics in skill bullet format (see Step 4 and "Rewriting the Full analysis"). Derived only; no new findings. |

Severity routing test for each finding: *Is there a decision only the client can
make, and is something actively costing them or blocked until they act?* goes to
🔴 / "what we need from you". *Is it a caution or an our-side visibility gap
we're flagging but not blocked on?* goes to 🟡 (watch), not 🔴. *Did we already
handle or stage it?* goes to "what we did". *Is it a positive result?* goes to
"what's working". Route "what we need from you" vs "what we did" off the
**inline owner tag** in the MAA's single Action list, not off per-person section
headers.

**Action handling.** Carry only Actions with a client-visible outcome. Drop
internal-only items (file maintenance, script dry-runs, ledger updates, API
caveats). After removing internal-only items, **re-check every "See Action N"
cross-reference** in the surviving text: the numbering has shifted, so each
reference must point at the renumbered item or be rewritten in words. A dangling
"See Action 4" that now points at a different action is a trace failure.

**"Render" means this skill.** When the user says "render," "render the report,"
or "render the client view" for a Google Ads MAA, even mid-conversation,
outside a full MAA run, produce these two outputs from the templates. Never
satisfy a render request with an ad-hoc visualization/widget or a hand-built
HTML mockup; that is not the deliverable and breaks the established pattern.

## Step 4: Render both outputs

### 4a. Markdown client view

Use `references/markdown-template.md` as the structural pattern. Embed the charts
as markdown images pointing at the two PNGs (same folder). Keep the section order
from Step 3. The Full analysis section is the client-language rewrite of the MAA
(rules below), metrics in bullet format.

### Rewriting the Full analysis (client language)

The rewrite is still projection, not new analysis: every sentence traces to an
MAA line, and the Cardinal Rule applies in full. What changes is the register and
what gets carried. Follow the client ledger's render spec (section 8); where it
is silent, apply this default strip list:

- Quality Score component names (Expected CTR, Ad Relevance, Landing Page
  Experience) and per-keyword QS tables
- Ad group names, ad IDs, file paths, API resource names
- Cross-client references
- Method debates and self-corrections ("first we thought X, then Y")
- Daily spend tables
- Auction-insight blocks
- Budget-verification mechanics
- API caveats and data-pull notes
- Script names and dry-run mechanics
- Internal file-maintenance items (ledger, trend.csv, config updates)
- Owner tags in the top-level sections (the routing already happened in
  "what we need from you" vs "what we did")

Plain labels, not abbreviations: write **Cost per click** (not CPC), **Cost per
lead** (not CPA), **Click-through rate** (not CTR), **Impression share** spelled
out. Campaign-level metric bullets stay: Cost, Impressions, Clicks,
Click-through rate, Cost per click, Leads, Cost per lead.

Carry only Actions with a client-visible outcome (a change the client will
notice in the account, the ads, the leads, or the bill). If a finding survives
the strip list but reads as agency-internal, it goes too.

### 4b. Paste-ready HTML version (Basecamp-tuned)

Use `references/basecamp-template.html` as the structural pattern (reuse the
layout, not the sample content). The body that gets pasted must use only what a
restrictive rich-text editor keeps on paste:

- **Keep:** headings, **bold**, *italic*, bulleted and numbered lists,
  blockquote, links, emoji.
- **Drop / never rely on:** inline SVG, `<table>`, CSS-styled boxes, background
  colors, custom font color. Encode criticality with **emoji + bold**, not color.
- **Charts = dragged-in PNGs.** Most editors embed PNG/JPG inline but cannot take
  SVG. Put a clearly marked placeholder where each chart goes, e.g.
  `[CHART] Drag in: {filename}.png`, and tell the user to drag the two PNGs there.
- **Emoji legend:** ✅ working, 🔴 needs attention/decision, 👉 what we need from
  you, 📊 charts, 🟢/🟡/🔴 status dot.
- **Metrics stay in bullet format** in the Full analysis section, the core
  bullets per Search/PMax campaign (Cost, Impressions, Clicks, Click-through
  rate, Cost per click, Leads, Cost per lead), plain labels per the rewrite
  rules. Do not flatten metrics into a paragraph.
- Include a short **how-to banner** at the top of the HTML file (outside the paste
  body) telling the user: select the report body, copy, paste into the comms tool,
  then drag the two PNGs into the `[CHART]` spots.

> **Adapting beyond Basecamp:** these constraints are Basecamp's, and they are a
> safe subset for most rich-text editors (email, Notion, Google Docs paste, help
> desks). If your tool accepts richer markup, you can relax them, but the
> emoji-over-color and dragged-in-PNG approach is the most portable default.

**Style:** no em dashes anywhere in either output. Use commas, periods, or
hyphens. Match the client's existing MAA voice.

## Step 5: Trace check (REQUIRED, before writing any file)

Before the .md or .html is written, build a scratch table (not shipped) with one
row per sentence in **the bottom line**, **what's working**, **what needs
attention**, and **what we need from you**:

| Client-view sentence | MAA line it derives from (quoted) | Hedge preserved? |
|---|---|---|

Rules:

1. Every sentence must quote the MAA line it derives from. Paraphrase is fine
   in the left column; the right column is a **quote**.
2. A sentence with no source line is **deleted**, not softened and not
   "supported later."
3. Flag any hedge that was upgraded to confidence (MAA says "early", "one
   week", "cannot yet confirm"; the sentence says it as fact). Restore the hedge
   or delete the sentence.

This step is not optional and not a re-read at the end. On a live render it
caught **six invented claims** in a summary that read as perfectly plausible.
Do it before the files exist so nothing has to be unwritten.

## Step 6: Output

Write to `{OUTPUT_DIR}/{Client Name}/`:

- `{Client}_Client-View_{YYYY-MM-DD}.md`
- `{Client}_Client-View_{YYYY-MM-DD}.html`
- `{slug}_chart_leads_{YYYY-MM-DD}.png`
- `{slug}_chart_cost-per-lead_{YYYY-MM-DD}.png`

Increment a `_v2`, `_v3` suffix if a file for that date already exists (never
overwrite). Present all four files when done. Do **not** touch the source MAA.

This is a **draft for review before posting**, same as the MAA itself. Never
auto-publish to the client comms tool.

## Step 7: Verify before presenting (required)

Re-run the trace-check from Step 5 against the written files, then confirm:

1. **Every** summary line maps to a line in the source MAA. List any that do not,
   they must be removed, not "supported later."
2. No invented metrics; no hedge upgraded to confidence; no chart editorializing.
3. The chart endpoints equal the MAA's bottom-line numbers.
4. Metrics in Full analysis are in bullet format, all core bullets per campaign,
   plain labels (Cost per click, Cost per lead).
5. The Full analysis carries nothing on the strip list (ledger render spec, or
   the defaults in Step 4a), and every "See Action N" reference points at the
   renumbered item.
6. Size check: client view is about one third of the MAA length, and never
   over half.
7. The HTML paste body contains no `<svg>`, `<table>`, or color-dependent meaning.
8. No em dashes in either output.

If any check fails, fix and re-verify. For high-stakes clients, run the
trace-check as a fresh read of the MAA against the summary (a subagent is ideal).

## Connected

- `google-ads-analyzer`, produces the MAA this stage renders.
- `../../shared/frameworks/methodology.md`, the MAA doctrine (MAA = analysis,
  not a task list).
- `references/markdown-template.md`, `references/basecamp-template.html`, output
  patterns.
- `scripts/render_charts.py`, deterministic chart generator.
- `../../shared/frameworks/ledger-template.md`, section 8 is the per-client
  render spec this skill reads first.

## Changed in 1.5.0

- Full analysis is now rewritten in client language per the ledger's render
  spec (section 8), with a default strip list and plain metric labels. It was
  previously reproduced verbatim.
- Size check added: about one third of the MAA length, never over half.
- Trace check is now a required Step 5 that runs before any file is written,
  with a scratch table quoting the MAA source line per sentence.
- Ledger render spec read added to Step 1; ledger overrides skill defaults.
- Action handling: internal-only items dropped, "See Action N" references
  re-checked after renumbering.

## Agent identification (1.5.0, audience rule changed 2026-10-02)

**Client-facing thread (the usual case for a client view):** neither output
carries the identification line, the "Sent by" line, the agent receipt or a
Verified line. The report opens on its title and ends on the Action list. AI is
assumed (Dennis's direction, relayed by Daniel 2026-10-02; same rule as
`clients/_shared/agent-receipt.md`). After the operator posts, read the comment
back from Basecamp and record the recording ID and the read-back in the client
ledger instead.

**Internal thread (team-only):** keep both lines from
`../../shared/frameworks/agent-receipt.md`: first line
`Automated weekly Google Ads MAA by the google-ads-analyzer agent, hardened by google-ads-reviewer, rendered by google-ads-client-view. {Client}, {date}.`
and last lines `Sent by google-ads-client-view / {operator}'s desk` /
`Agent receipt: Basecamp — google-ads-client-view [Claude] · action: drafted · human review: reviewed by {operator} before posting`.

Check the thread's audience in the client ledger (section 1) before rendering.
