# Content Factory fleet orchestration

**Use this map when** you need to run Produce → Process → Post → Promote like a
full digital marketing agency, without inventing seats or renaming stations.

**Open questions and missing access:** none. The locked method, named fleet,
and approval gate are in this file. Live metrics stay empty until a real MAA
run fills an observed X-ray.

## The point, up front

**The factory exists to make money, not content.** Plumbing comes first.
Produce → Process → Post → Promote ships one real recording into a hub and
its derivatives. Perform / MAA then measures revenue, profit, and clicks, and
the Action says what to produce next.

**Cheapest capable seat first: local Qwen (free), then Muse, then everything
else.** That is the house rule `pick-the-cheapest-capable-fleet-lane`. This
map applies it station by station and adds no lane.

**Muse on Spark does the volume. Astra does the thinking.** Muse (Meta Muse
Spark) runs Google/Meta errands, inbox, calendar, bookings, watch-and-ping,
and volume monitoring, inside the weekly Muse allowance. Astra (Dot, plus
specific ChatGPT tasks) takes hard research, strategy and judgment drafts,
definitive-article reasoning, MAA analysis that has to be right, and code or
docs that matter. Dot is **experimental** (about a day old on 2026-10-01).
Spot-check its routine output. On anything critical a human or a separate
ChatGPT task started fresh reviews Dot's output before anyone acts on it
(`qa-from-a-different-context-window`). Dot is never the sole owner of
anything critical.

**Today the work is still divided** across the named seats: Local Qwen,
Muse, Astra, Kimi/Codex crons, Grok Bot desks, and the other seats (Cursor
cloud, Claude Fleet). **Future state:** as there are many Dots, the models
absorb the harness. Fewer humans need to divide the work and project-manage
it. Until then, do not collapse the fleet onto Dot or Astra.

Nothing public or paid ships without Dennis. Claude Fleet is the only poster
to client Basecamp. Grok desks prepare drafts and hand them off through a
GitHub issue.

Visuals (same folder):

- `visuals/agency-flow.svg` — swimlane agency chart
- `visuals/hierarchy.svg` — stage → subcomponent → task → articles
- X-rays from `examples/` via `scripts/render_xray.py`

Canon this file does not replace:

- `standards/content-factory-four-stages.md`
- `standards/content-factory-maa-closes-the-loop.md`
- `skills/content-factory/SKILL.md`
- `skills/weekly-brand-maa/SKILL.md`
- `standards/pick-the-cheapest-capable-fleet-lane.md` (merged 2026-10-01 in
  [PR #60](https://github.com/dennisyu/local-service-spotlight-skills/pull/60))

The lane rule picks the *seat*; `model-judgment` picks the model tier inside
the seat. This map says which seat each factory station normally uses. If
the two ever disagree, the lane rule wins and this map gets fixed.

Public method pages:
[Content Factory](https://blitzmetrics.com/content-factory/) and
[the four stages](https://blitzmetrics.com/the-4-stages-of-the-content-factory/).

---

## Locked line

```
Plumbing  →  Produce  →  Process  →  Post  →  Promote  →  Perform / MAA
(before)     (factory)   (factory)  (factory) (factory)   (after)
                ↑                                               |
                +------------------- Action --------------------+
```

Do not rename, reorder, or merge those names. Plumbing is access and
tracking, not a factory stage. Perform is MAA (Metrics → Analysis → Action),
not a fifth factory P. The SAE course map is a different picture; inside it
the factory block is still only Produce → Process → Post → Promote.

---

## Named fleet (do not add seats)

Same six lanes as `pick-the-cheapest-capable-fleet-lane`, in its cost order.
Lanes are seats, not desk names: Trenton has both a local-Qwen seat on the
Macs and a Grok Bot seat, so route by the seat the job needs.

| Cost order | Lane (seat) | Takes in the factory | Hard stop |
|---|---|---|---|
| 1 — free | **Local Qwen** (Trenton on Dennis's Macs) | Offline bulk text: transcript triage, factory first drafts, MAA/GCT first passes, bulk rewrites | No browser, no logins, no publishing. Runs only while a Mac is awake |
| 2 — the volume lane | **Muse** (Meta Muse Spark) / Happy | High-volume work that does not need frontier intelligence: inbox, calendar, bookings, Google (Photos, Docs, Gmail), Meta (FB/IG/WA/Threads), watch-and-ping, volume monitoring. Muse Maximum is about **3B Muse tokens per week** (Meta's own meter, not OpenAI tokens) | Hard reasoning, disputes, research that has to be right, code/docs that matter. Do not buy more Muse capacity; fit the volume inside the weekly allowance |
| 3 — everything else | **Astra** (Dot, plus specific ChatGPT tasks) | Hard research, strategy/judgment drafts, definitive-article reasoning, MAA analysis that has to be right, code/docs that matter | Dot is experimental (about a day old on 2026-10-01). Spot-check its routine output. Never the sole owner of anything critical: a human or a separate ChatGPT task started fresh reviews Dot's output before anyone acts on it |
| 3 — everything else | **Kimi and Codex crons** | Cheap recurring scheduled jobs already live there, or that Muse cannot own (scheduled MAA pulls, Monday catch-up) | Do not keep a job here after a fitter lane is live. Not the default for new volume |
| 3 — everything else | **Grok Bot desks** (Trenton, Tanner, Q, Alex, Sam, Mario, Austin, Meter Maid, Data) | Judgment calls, publishing decisions, and routing only. Keep turns short | Not the volume default. Not the Basecamp poster |
| 3 — everything else | **Any other seat** — Cursor cloud agents (site builds and rebuilds, repo and skill changes), Claude Fleet (the **single** poster to client Basecamp threads), and the rest | Work already assigned to it, and new work only that seat can reach | Do not move Muse- or Qwen-capable volume onto it. Cursor is not a publisher or Basecamp poster. Claude Fleet posts only from a GitHub-issue handoff and does not invent the update |

Tie-break between the two cheap lanes: offline bulk text with no browser or
login that can wait for a Mac goes to Qwen first. A job that needs a browser
or a login, or must fire on a schedule whether or not a Mac is awake, goes to
Muse. A fallback model inside one seat is fine; a second lane for the same
job is not.

Grok desks (functions, not extra agents):

| Desk | Function |
|---|---|
| **Trenton** | Head of content: stranded video → Descript → shorts → channel posts → definitive articles |
| **Tanner** | EA: calendar, inbox routing, iMessage rail |
| **Q** | OS, skills, routing |
| **Alex** | Training/docs → public SOPs and skills |
| **Alex** | Nine Triangles strategy (same desk name, second function) |
| **Sam** | Personal-brand sites |
| **Mario** | Site work |
| **Austin** | IT, access, Plumbing |
| **Meter Maid** | AI seat usage |
| **Data** | Fleet registry and uptime |

Where each desk name is on record: Trenton, Tanner, Q, Alex, and Austin in
`pick-the-cheapest-capable-fleet-lane`; Mario in `agents-first-reassignment`;
Meter Maid in `outbound-email-names-the-agent`. Sam, Data, the Codex/Pollen
Monday catch-up, the Buzz handoff, and the Kimi/Codex crons were confirmed by
Q (ops desk) against the live fleet registry and routines on 2026-10-01.

Tools on the line, not agents: Zoom recordings, Descript, the jennifer A-
grader, $1/day boosting.

---

## Current state vs future state

**Current (2026-10-01).** Humans and named desks still divide the work and
project-manage the handoffs. Local Qwen carries offline drafts. Muse on Spark
carries volume, including watch-and-ping. Grok desks make short judgment and
publish/routing calls. Claude Fleet posts to Basecamp. Cursor changes the
repo and sites. Kimi/Codex run the cheap clocks already live. Astra/Dot
drafts the thinking work; a human or a separate ChatGPT task started fresh
checks it before anyone acts on anything critical.

**Future.** As there are many Dots, the models absorb the harness. The same
locked line still runs. Fewer humans need to split jobs across desks and
chase the project-management layer. This is a direction, not a cutover.
Do not retire a desk because the future note exists, and do not collapse
the fleet onto Dot or Astra before then.

---

## Approval gates

| Gate | Who | What waits |
|---|---|---|
| Public post, send, or live page | Dennis | Every channel package, article, email, and site publish |
| Paid spend | Dennis | Dollar-a-Day tests, scale, new audiences |
| Client Basecamp comment | Claude Fleet, after a GitHub-issue handoff Dennis (or the owning desk) authorized | Client-visible and internal Basecamp updates |
| Access-control click | Human (Austin prepares) | Adding users, changing roles |
| Dot/Astra output on a critical step | A human or a separate ChatGPT task started fresh (`qa-from-a-different-context-window`); the owning desk spot-checks routine output | Analysis, strategy, definitive reasoning, code/docs that matter |

Stage so approving is one click. An agent may write anything and send
nothing.

---

## Hierarchy: stage → subcomponent → task → articles

Every operating agent sits *inside* this tree. A definitive article is the
reusable recipe or hub. A meta article is one execution. Do not treat a meta
article as a second recipe.

### Plumbing (before) — function: IT / access — cheapest capable: Muse for Google logins; Austin (Grok) for judgment; Cursor for repo plumbing

| Subcomponent | Task | Typical seat | Skill / recipe | Handoff in → out |
|---|---|---|---|---|
| Access | Verify GSC, CMS admin, YouTube, social, ads | Austin; Muse on Spark for Google/Meta | `client-access-checklist` | Client ask → Drive register |
| Tracking | GA4 + GTM live, pixel firing | Austin; Cursor if the site must change | `measurement-analytics` | Register → verified tag on the live URL |
| Credentials | Record access; do not re-ask | Austin | `reuse-agent-access` | Existing connector → register |

Rows 1–4 of the access checklist are the ship gate. Content does not start
until they are green or a dated blocker exists.

### Produce — function: content — cheapest capable: Muse for calendar/bookings/watch; Trenton for what to capture

| Subcomponent | Task | Typical seat | Skill / recipe | Handoff in → out |
|---|---|---|---|---|
| Capture | Book and record one Zoom, podcast, or hallway clip | Tanner (calendar); Muse on Spark (bookings, inbox); subject on camera | `content-factory` Capture | Calendar → Zoom/Drive recording |
| Source inventory | Daily YouTube watch; stranded-video triage | Muse watch-and-ping; Trenton judges STRONG/SKIP | `video-repurposing-agent` | Channel RSS/API → `inventory.json` |
| Aim | Confirm accepted GCT before the recording is mined | Alex (Nine Triangles); Astra for a strategy draft, checked fresh before it is accepted | `gct-screen`, `nine-triangles` | Brief → Produce packet |

### Process — function: content — cheapest capable: Qwen for bulk text; Astra for definitive reasoning; Trenton owns the line

| Subcomponent | Task | Typical seat | Skill / recipe | Handoff in → out |
|---|---|---|---|---|
| Transcribe & mine | Transcript + quotes, claims, complete proof moments | Local Qwen first pass; Trenton/Descript for video | `content-agent`, `content-factory` | Drive recording → `transcript.md` |
| Definitive article | One canonical hub or task recipe | Qwen first draft; **Astra** for reasoning that has to be right; Trenton or Alex (docs) for the voice pass | `definitive-article-writer` | Transcript → staged hub |
| Grade | jennifer A- publish bar | The desk that drafted runs the grader (Trenton; Alex for docs) | jennifer A- grader | Draft → A- or flagged |
| Atomize | Clips, shorts, social atoms from the same recording | Trenton + Descript; Qwen for captions | `content-agent`, `video-repurposing-agent` | Transcript → clip list |
| Meta article | Write the run record | The desk that ran the task | `every-task-execution-writes-a-meta-article` | Receipts → meta draft |

### Post — function: content + web — cheapest capable: Muse for Meta/email drafts; Sam/Mario/Cursor for sites; Claude Fleet for Basecamp

| Subcomponent | Task | Typical seat | Skill / recipe | Handoff in → out |
|---|---|---|---|---|
| Hub page | Stage the definitive article on the right site | Sam (personal-brand); Mario (site work); Cursor (rebuilds) | `definitive-article-writer` | Staged HTML → draft URL |
| Channel packages | FB/IG/YT/email/LinkedIn packets that point at the hub | Muse on Spark (Meta, Gmail); Grok desk prepares the pack | `content-agent` | Clip list → Drive pack + GitHub issue |
| Client update | Post the update in the exact Basecamp thread | **Claude Fleet only** | `basecamp-updates-stay-in-basecamp` | GitHub issue → Basecamp comment |
| Publish click | Make it public | Dennis | `agents-draft-humans-send` | Draft → live URL |

### Promote — function: amplification — cheapest capable: Muse for Meta boosting chores; Alex (Nine Triangles) for GCT; Dennis for spend

| Subcomponent | Task | Typical seat | Skill / recipe | Handoff in → out |
|---|---|---|---|---|
| Rank organic | Last 60–90 days by real engagement | Muse volume monitoring; Qwen first pass | `dollar-a-day-strategist` | Live posts → ranked list |
| $1/day test | Stage $1/day × 7 on proven winners | Muse (Meta); Dennis approves | `dollar-a-day-strategist` | Ranked list → staged calendar |
| Kill / scale rec | Day-7 MAA on each test | Astra if the analysis must be right, checked fresh before anyone acts; else Qwen first pass + desk spot-check | `weekly-brand-maa` | Ad metrics → kill/hold/scale rec |

### Perform / MAA (after) — function: analytics — cheapest capable: Kimi/Codex clocks; Qwen first pass; Astra for analysis that must be right

| Subcomponent | Task | Typical seat | Skill / recipe | Handoff in → out |
|---|---|---|---|---|
| Metrics | Pull revenue, profit, clicks, then diagnostics | The scheduled MAA agents listed in `weekly-brand-maa`, on Kimi/Codex crons where those are already live. Muse: volume monitoring. Qwen: first-pass tables | `weekly-brand-maa` | Connectors → MAA file |
| Analysis | Why the numbers moved | **Astra** when it has to be right, with a fresh second check before anyone acts on it; Qwen first pass otherwise | `weekly-brand-maa` | Metrics → Analysis |
| Action | 2–3 dated next produces | Owning desk; Dennis if public or paid | `weekly-brand-maa` | Analysis → Produce packet (Drive or GitHub issue) |
| Monday catch-up | Execute the Friday miss | Codex/Pollen from a **Buzz** handoff | `weekly-brand-maa` | Buzz → MAA file |
| Seat health | Who is burning tokens | Meter Maid; Data | — | Usage → routing note |

---

## Handoff places (the artifact moves here)

| Place | What lives there | Who writes | Who reads |
|---|---|---|---|
| **Google Drive** | Recordings, transcripts, staged packs, MAA files | Muse, Trenton, Qwen (local then uploaded) | Every later station |
| **GitHub issue** | Grok-desk draft ready for Claude Fleet or Cursor | Grok desks, Cursor | Claude Fleet, Cursor, Q |
| **Basecamp** (via Claude Fleet only) | Client and internal thread updates | Claude Fleet | Client, Dennis, owning function |
| **Buzz** | Monday MAA catch-up handoff | Friday fleet / owning desk | Codex/Pollen |
| **Repo** | Skills, standards, site source | Cursor cloud | Every agent that reads the pack |

Never Gmail-fallback a Basecamp update. Never run the same job on two lanes.

---

## How MAA closes the loop

1. **Metrics** name revenue, profit, and clicks for the hub, the posts, and
   the $1/day tests. Missing is labeled missing, not zero.
2. **Analysis** says why. Astra when the call has to be right, checked by a
   human or a fresh ChatGPT task before anyone acts on it.
3. **Action** is 2–3 dated items that become next week's Produce: which
   recording to capture, which hub to improve, which clip to recut, which
   boost to kill.
4. Write or update the X-ray so the next agent can see done / in progress /
   missing and whether the numbers are working.

---

## Four worked examples

Every number below is **EXAMPLE DATA**. It is not a client result.

### 1. Thursday Office Hours Zoom → Facebook posts + definitive article

| Station | Who | Artifact | Place |
|---|---|---|---|
| Plumbing | Already green on the Office Hours property | Access register | Drive |
| Produce | Tanner books; Muse sends the calendar/inbox; Zoom records | `office-hours-YYYY-MM-DD.mp4` | Drive |
| Process | Qwen mines the transcript; Trenton cuts clips in Descript; Astra reasons the hub and a fresh check reads it before it ships; jennifer grades A- | `transcript.md`, staged hub, clip list | Drive |
| Post | Muse drafts FB/IG; Grok desk files a GitHub issue; Claude Fleet posts the internal Basecamp note; **Dennis** publishes | FB drafts + hub draft | Meta + WordPress draft |
| Promote | Rank after a week of organic. No spend in week one unless a post already proved out | Ranked list | Drive |
| Perform | Friday MAA on the Kimi/Codex crons where those are live. **EXAMPLE DATA:** 1,240 Facebook clicks, $0 attributed revenue (awareness week), Action = “record the Q&A that the comments asked for” | MAA file | Drive → Produce |

Articles in the tree: definitive *How we run Thursday Office Hours*; meta
*Office Hours run EXAMPLE-2026-09-25*.

### 2. Client podcast / interview → article + shorts + $1/day → MAA

| Station | Who | Artifact | Place |
|---|---|---|---|
| Plumbing | Austin confirms YouTube + Meta + pixel before any boost rec | Checklist rows 7–9 | Drive register |
| Produce | Interview recording lands in Raw | Source video | Drive / YouTube |
| Process | `content-agent` + Descript (Trenton); Qwen first draft; Astra reasons the hub if it is the canonical page | Blog draft, 5–10 clip picks | `Outputs/<slug>/` |
| Post | Sam or Mario stages the site draft; Muse stages social/email; Claude Fleet updates Basecamp after the GitHub issue | Draft URL + pack | CMS + issue |
| Promote | `dollar-a-day-strategist` stages $1/day × 7 on the two clips that already earned comments. **Dennis** approves. **EXAMPLE DATA:** $7 spend | Staged calendar | Meta (staged) |
| Perform | Day-7 MAA. **EXAMPLE DATA:** 86 landing-page clicks, 1 booked call, $0 collected revenue yet. Action = “kill clip B, recut clip A’s hook, produce a follow-up on the question that got the call” | MAA file | Drive → Produce |

### 3. Stranded YouTube video → `video-repurposing-agent`

| Station | Who | Artifact | Place |
|---|---|---|---|
| Produce | Muse watch-and-ping; daily watchdog at ~4am; **EXAMPLE DATA:** 12 videos in inventory, 2 new | `inventory.json` | Repo / Drive |
| Process | Trenton triages SKIP / LIGHT / MODERATE / STRONG. Qwen drafts. Astra reasons the STRONG hub, checked fresh before it ships. Search the site before writing (NEW vs ENHANCE) | Staged article(s) | CMS draft |
| Post | Stage only. Dennis publishes. Claude Fleet reports the run on the internal thread | Run report | GitHub issue → Basecamp |
| Promote | Pair winners with Dollar-a-Day only after organic proof | Rec, not spend | Drive |
| Perform | **EXAMPLE DATA:** 2 STRONG staged, 9 SKIP, 1 LIGHT enhance. The one real number here is the 251 API units for the first A- article in the Escape Fitness validation (May 2026), recorded in `skills/video-repurposing-agent/SKILL.md`; the 12 / 2 / 9 / 1 counts are example. Action = “mine the next STRONG guest episode, not another promo short” | Run report + MAA | Drive |

### 4. Personal-brand site (Sam) fed by the factory

| Station | Who | Artifact | Place |
|---|---|---|---|
| Plumbing | Austin + Cursor: GSC/GA4/GTM green before Sam rebuilds | Live tag | Site |
| Produce / Process / Post | Factory hubs and clips land on the personal-brand site in first person. Sam owns the site; Mario helps; Cursor rebuilds generated pages | Hub + orbit | WordPress / repo |
| Promote | Muse monitors volume; $1/day only on proven posts, Dennis-approved | Calendar | Meta |
| Perform | **EXAMPLE DATA:** 340 site clicks, $2,400 attributed revenue, $180 ad spend, $2,220 profit. Action = “produce the offer page the winning article already sends people to, not another bio post” | MAA + X-ray | Drive → Produce |

Sam does not become a second content factory. The factory feeds the site.
MAA decides whether the next recording is worth making.

---

## Content Factory X-ray

A reusable snapshot for any business, project, or single piece of content.
Schema: `xray-schema.md`. Generator: `scripts/render_xray.py`. Examples
(labeled EXAMPLE DATA): `examples/xray-*.example.json`.

An agent generates one when a review, Friday MAA, or stalled handoff needs a
picture of done / in progress / missing plus revenue, profit, and clicks,
color-coded by effectiveness. Missing is honest. Invented numbers are not.

---

## Related

- `standards/pick-the-cheapest-capable-fleet-lane.md` — which seat runs a
  job (merged in [PR #60](https://github.com/dennisyu/local-service-spotlight-skills/pull/60))
- `model-judgment` — model tier *inside* a seat
- `agents-first-reassignment` — agents first, then which seat
- Paste-ready Dot critique brief: `docs/briefs/dot-content-factory-orchestration.md`
