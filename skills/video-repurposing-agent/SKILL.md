---
name: video-repurposing-agent
description: Watch a YouTube channel, judge which new videos deserve repurposing, and turn winners into verified article packages on the right site — staged by default and published only under exact action authority. Use when a client or member wants real recordings feeding their Content Factory.
rule-scopes: published-html, design-review
---

# Video Repurposing Agent — the daily channel watchdog

**Use this when** someone records on YouTube but their websites do not know it. This
agent closes that gap on a schedule: check the channel, triage new videos, and move the
worthwhile ones through transcript → article package → grade → stage. Publishing and
cross-linking are separate approved states.

Built July 20, 2026 by merging Daniel Goodrich's Repurposing Suite v0.2 (the YouTube Data API watch loop, effort routing, and grader caps he validated on Escape Fitness LIFTS — 247 episodes inventoried, first article graded A- for 251 API units) into the Content Factory method. Daniel's grader was already scoring "per Jennifer rubric," so the two systems merged without a seam.

## The client card (fill once, reuse every run)
One block per client/member — keep it in the project or a `client.json`:
- **Channel URL** (and channel_id once resolved — cache it).
- **Sites and authority**: personal-brand site URL, company site URL, or both. Default
  mode is `draft`. `live` is valid only with a current scoped approval receipt naming the
  site, action class, executor, and time window; a stored Application Password or prior
  publication is not standing approval.
- **Voice + context files**: brand-voice doc, ideal-client file, links file (real domains, offer pages) — read them every run; never invent a link or offer.
- **Network entities**: name → URL map of the people, companies, and partners this client is tied to.
- **Extra banned words** (client-specific), batch cap per run (default 3), and the hub URLs nothing may compete with.
- Never store credentials in the card. Secrets live in the OS keychain or `.credentials.json`, and never appear in chat, reports, or output files.

## Step 1 — Daily watch (the part that runs before anyone is awake)
- First run: pull the channel's full uploads playlist and write `inventory.json` (id, title, publishedAt, duration, views, thumbnail, status per video).
- Every run after: poll newest-first and STOP at the first video already in the inventory — append only what's new. Log "0 new videos" as a valid result; never invent work.
- How to read the channel, in order of preference: (1) YouTube Data API — playlistItems.list + videos.list, 1 unit per 50 videos, if API credentials exist; (2) keyless — the channel's public uploads page or RSS (`/feeds/videos.xml?channel_id=`) — fine for daily new-video detection with zero setup.
- Schedule it off-peak (our standard: ~4am local, one run per client per day). Say in the log which read path ran.

## Step 2 — Triage: is this video worth repurposing, and how hard?
Score each new video against the client's GCT (Goals · Content · Targeting) and decide out loud:

| Tier | When | Article shape | Cross-links | Revision budget → target grade |
|---|---|---|---|---|
| **SKIP** | Off-topic for the GCT, duplicate of an existing article's ground, under ~2 minutes with no standalone claim, or pure promo | Log the reason, mark `skipped` — that IS the deliverable for this video | — | — |
| **LIGHT** | One reusable idea; short clip or single-point video | 600–1,000 words, embed only | 1–2 | 1 → B |
| **MODERATE** | Solid episode; one clear theme | 1,000–1,500 words + diagram if it strengthens the point | 2–3 | 2 → B+ |
| **STRONG** | Signature content: named guests, real numbers, a framework, a story only this client can tell | 1,500+ words + required SVG diagram | 3–5 | 3 → A- |

A 1-hour STRONG video may carry more than one article: if the transcript yields two distinct GCT-worthy themes with 6+ subtopics each, ship separate articles on separate hubs — never two pages on the same topic (that's content vandalism, competing with yourself).

## Step 3 — NEW vs ENHANCE (search before writing)
Before drafting, search the destination site (site: search + the site's own search) for the video's topic:
- **No live article owns it** → write NEW.
- **A live article already owns it** → ENHANCE: embed the video there, add the new material as sections, refresh the date — and log "enhanced X" instead of shipping a competitor page.
- **A thin/stub page holds the slug** → rebuild it in place.

## Step 4 — Destination and point of view
- **Personal-brand site** → first person, the owner's voice ("I"), relationship context by name. WordPress author = the person, never admin.
- **Company site** → third person; the subject is the company or featured guest.
- **Both** (only when both POVs have real material): two different articles — the personal cut (what I learned/did) and the company cut (what the company/guest delivered) — cross-linked to each other, each pointing at its own site's hub. Different angles, never the same article twice.
- The agent decides and states the routing + one-line reason in the run report.

## Step 5 — Transcript
In order of preference: the video's caption track (prefer a manually-uploaded track over auto-generated; API path: captions.list → captions.download, ~250 units per video — a 10,000-unit free day covers ~39 articles); the client's own transcript or Descript export; auto-captions scraped from the public player. Clean it: strip timestamps, cut filler, fix proper nouns against the client's known entities. Quotes used in the article stay verbatim.

## Step 6 — Write, link, illustrate
Hand the cleaned transcript + client card to `definitive-article-writer` (Brandon) with the tier's spec. Non-negotiables:
- Embed the source video at the top with one sentence of provenance; answer the article's question in the first paragraph.
- 6–12 verb-led H2s for a long video; paragraphs ≤5 lines; preserve real quotes (E-E-A-T Experience).
- **Entity Linking Decision Tree** — route every named entity: in-network person → their personal-brand site; in-network company → their site; out-of-network person/company or any tool/concept → the public canonical article on it, else plain text; Dennis Yu → dennisyu.com. Anchor text 3–6 descriptive words; link each entity on first mention only; 3+ in-network links on STRONG.
- Every article links UP to its hub (Content Factory rule) and sideways to 2–3 sibling articles; when we run both sites, link across them.
- Featured image = the video's own maxres thumbnail (`i.ytimg.com/vi/{id}/maxresdefault.jpg`) — a real frame, never a text-only card and never stock (blog-card thumbnails standard).
- Evergreen: no dates-as-news, no limited-time promos.

## Step 7 — Grade to done, then stage or execute
- Hand the draft to the configured QA judge. A- is the publish-readiness bar; revise
  within the tier's budget, then stop and flag with the penalty list when it cannot pass.
- `draft` stages the complete post plus verification checklist. `live` may execute only
  when the exact approval receipt still matches; then verify the URL with a cache-busted
  anonymous fetch and confirm images, links, schema, and canonical behavior.
- Mark the artifact lifecycle accurately: `staged`, `approved`, `executed`, or
  `verified`. Never label a draft `published`.

## Step 8 — Report
Append one run report: videos found / skipped (with reasons) / articles by lifecycle
state (grade, tier, destination, URL when executed) / enhancements / API units used /
anything a human must do. Deliver only through the configured authorized channel and
verify readback; otherwise save `UNPOSTED` and an internal blocker. Never Gmail-fallback
a Basecamp update.

## Output
- `inventory.json` — the channel's full state, every video accounted for.
- Published or staged article(s), graded A-/tier target, cross-linked, real-thumbnail featured images.
- A run report a human can read in 30 seconds, plus the log line that stops tomorrow's run from repeating today's work.

## Run on a persistent agent (Fable 5)
- **Loop to done:** a video is not processed at the first draft — loop until graded,
  staged, inventoried, and reported. Approved execution and live verification are
  separate states; do not manufacture them to close the loop.
- **Self-verify:** re-fetch every published URL cache-busted; grep the live HTML for the embed and the links you claim are there.
- **Compound with memory:** the inventory watermark, the client card, and the hub map make run 100 cheaper than run 1.
- **Know when to stop:** SKIP is a first-class verdict, zero-new-videos is a clean run, and A- terminates revision. Agents that can't stop are as broken as agents that can't start.

## Notes — Dennis's method
- The proof pattern is Marko Sipila's: phone-shot conference interviews → HVAC Quote's YouTube → repurposed articles → $1/day behind winners → 300+ customers. This agent is that loop with the human watching removed.
- Daniel Goodrich proved the watch-loop economics on Escape Fitness (May 2026): 247 episodes inventoried, transcript via the captions API, first article A- in two revisions, 251 of 10,000 free daily units. His three-skill split (orchestrator / writer / grader) is preserved here as steps 1–5 / 6 / 7.
- One credential can serve a whole managed fleet: clients invite a shared Local Service Spotlight access email as YouTube Studio collaborator (Editor), and the same OAuth token reads captions on every channel. Members installing self-serve skip OAuth entirely — the keyless path runs day one.
- Pair the output with `dollar-a-day-strategist`: the article that wins organically is the one that earns the $1/day.

## Definitive article & pairings
- Reference: blitzmetrics.com/inventory-youtube-channel/ · blitzmetrics.com/blog-posting-guidelines/ · blitzmetrics.com/content-factory/ · blitzmetrics.com/application-passwords/
- Pairs with: **video-repurposing-agent** → definitive-article-writer → jennifer → dollar-a-day-strategist → recursive-self-improvement-qa

<!-- shared-rule:silent-media-playback:start -->
## Silent media playback

- Never let audio from browser, video, audio, presentation, or application testing play through the user's speakers unless the user explicitly asks to hear it.
- Before starting any media playback, mute the player and set its volume to zero. Keep it muted for the full test, including replays, reloads, new tabs, and alternate players.
- Apply this rule to the primary agent and every delegated agent. Include the mute requirement whenever work that may involve media playback is delegated.
- If the mute state cannot be controlled and verified before playback, do not start playback. Use metadata, captions, transcripts, frames, screenshots, network state, or player state instead.
- Only unmute when the user explicitly requests audible playback in the current task.
<!-- shared-rule:silent-media-playback:end -->

<!-- shared-rule:agents-draft-humans-send:start -->
## Agents draft; a human sends and publishes

- **An agent may write anything and send nothing.** Email, DMs, social posts, client
  messages, public pages — staged and ready, never dispatched.
- **Stage it so approving is one click**, not one more round of work: the full text, the
  recipient, the subject, and where it will appear.
- This is a security control, not a confidence rating. It holds even when the draft is
  obviously correct, because the failure it prevents is the one nobody predicted.
- It is the boundary on `be-proactive-see-it-through`: act freely on reversible work,
  stop at anything that reaches another person or the public.
<!-- shared-rule:agents-draft-humans-send:end -->

<!-- shared-rule:analytics-on-every-page:start -->
## Analytics goes on before anything gets optimised

- **Measurement is the first build step, not the last.** A page with no analytics cannot
  be improved, only redecorated, and every argument about it becomes a matter of taste.
- **The invisible plumbing outranks the visual design** — tracking, CRM connection,
  conversion events, schema and page structure come before fonts and colours.
- **Confirm the tag actually fires on the live page**, not that it exists in a settings
  screen. See `verify-by-opening-the-live-artifact`.
- Instrument the business outcome, not the vanity metric: calls, booked jobs and revenue,
  not impressions.
<!-- shared-rule:analytics-on-every-page:end -->

<!-- shared-rule:ask-blocking-questions-up-front:start -->
## Ask every blocking question up front

- **Front-load every question and every missing access into the planning step**, before
  the long work starts. The person who briefed you intends to walk away; a question
  raised at minute ninety costs them the whole ninety minutes.
- **Do not guess to avoid asking.** A guess that turns out wrong is discovered at the end,
  when it is most expensive to undo.
- Open every plan with an explicit **open questions and missing access** block. If the
  list is empty, say so — that is information too.
- Once the questions are answered, work continuously to the end rather than stopping to
  check in on things you could have decided.
<!-- shared-rule:ask-blocking-questions-up-front:end -->

<!-- shared-rule:assign-work-to-a-function:start -->
## Assign work to a function, not a person

- **Every task is owned by a function** — web, content, analytics, client success — and
  people sit inside functions. People join, leave and go on holiday; the function does not.
- **Escalate to a function too.** "I told Muzamil" is not an escalation if Muzamil is
  away; "escalated to the web function" is.
- A function with exactly one person in it is still a function. Name it that way, so the
  second person changes nothing.
- Work assigned to a named individual and nowhere else is work that silently stops when
  that individual does.
<!-- shared-rule:assign-work-to-a-function:end -->

<!-- shared-rule:be-proactive-see-it-through:start -->
## Be proactive and see it through

- **When you find something broken, fix it.** Do not file it, mention it in passing, or
  wait to be asked. If it is outside what you can fix, escalate it to the function that
  owns it, by name, with what you found.
- **You do not need permission for reversible work.** Do it, then report exactly what you
  did so it can be adjusted. Asking first for everything makes an agent slower than doing
  the work by hand.
- **Reversible is the line, not confidence.** Sending a message, publishing to the public,
  spending money, and deleting data stay behind an explicit approval — see
  `agents-draft-humans-send`. Everything short of that, act.
- Report what you changed in enough detail that undoing it is a one-line instruction.
<!-- shared-rule:be-proactive-see-it-through:end -->

<!-- shared-rule:buttons-must-contrast-with-their-background:start -->
## A button must contrast with what it sits on

- **A call to action must be visibly separate from the section behind it** at rest, not
  only on hover. A visitor on a phone never hovers, and a button that only appears on
  hover does not exist.
- **Check the button against every background it appears on.** The same component sits on
  white, on the hero image and on the dark footer; one of those is usually where it
  disappears.
- Text on the button needs at least **4.5:1** against the button fill, and the fill itself
  needs to be clearly distinct from the section fill.
- This is the general case of `no-black-buttons`. Black is the most common way to break it;
  it is not the only way.
<!-- shared-rule:buttons-must-contrast-with-their-background:end -->

<!-- shared-rule:capture-what-you-learn:start -->
## Capture what you learn as a standard, in the same session

- **A rule that lives only in an article, a chat message, a call recording, or your
  context window is a rule the next agent will break.** That is not a prediction. The
  black-button rule was published, illustrated, and given an enforcement plugin on
  17 May 2026, and on 15 August 2026 an agent holding the entire skill pack in context
  shipped a black button. The rule was never in `standards/`, so it never reached the
  skills, so it was not there to be read.
- When anyone — the client, the account owner, an audit, or your own failure — states a
  rule that should hold next time, **your job is not to remember it. It is to write
  `standards/<slug>.md` before the session ends.** Memory does not survive a session
  boundary. A file does.
- Scaffold it in one command, which forces every field including where the rule came
  from:

  ```bash
  python3 scripts/new_standard.py "no autoplay with sound" \
    --from "Dennis Yu, Cowork session, 2026-08-16" --applies-to published-html
  ```

- Then write the rule, run `python3 scripts/sync_shared_rules.py`, and open the pull
  request. The sync copies the rule into `AGENTS.md` and every distributed `SKILL.md`,
  so it reaches every agent and every member who installed the pack. Nobody has to be
  told about it.
- **Give the rule a machine check whenever one is honest.** A `checks` block in the
  header compiles straight into the live fleet sweep, so a violation on a published page
  is caught by a schedule instead of by a person noticing. Every check must carry
  passing and failing examples — a pattern that matches nothing reports a clean site
  forever, which is worse than no check at all.
- **Where a machine check would be dishonest, say so and leave `checks` out.** Judgement
  rules are still rules; they are enforced by being read pre-flight, and pretending a
  regex covers them hides the fact that nothing does.
- **Provenance is required, not decoration.** `captured_from` is how the team sees which
  channels leak. If dozens of recorded calls have produced no standards, those calls are
  not being captured, and that is visible at a glance instead of being a suspicion.
- **When a new rule contradicts an existing one, resolve it in the file and say so
  out loud.** Two standards that disagree are worse than one that is wrong, because
  every agent that reads both will pick whichever it happened to see last. Write the
  reconciliation into the newer rule and flag it to the account owner for confirmation.
- The order is Checklist → Content → Software. Write the checkable rule first, publish
  the article that teaches it second, and let the sweep be generated from the rule
  rather than hand-written beside it. Writing the article first is how rules get lost:
  the article is the artifact everyone can see, so it feels finished, and the
  enforceable form never gets written.
<!-- shared-rule:capture-what-you-learn:end -->

<!-- shared-rule:every-article-has-pictures:start -->
## Every article has pictures

- **No article ships as a wall of text.** Every published piece carries images — real
  photographs, screenshots, or diagrams that carry meaning, not decorative stock.
- **A diagram beats a paragraph** wherever the point is a structure, a sequence or a
  comparison.
- Caption them. An uncaptioned image is decoration; a captioned one is evidence.
- Images also carry the provenance required by `process-real-content-never-generate` —
  a photograph of the work actually done proves more than any sentence about it.
<!-- shared-rule:every-article-has-pictures:end -->

<!-- shared-rule:immersive-hero-standard:start -->
## Personal-brand heroes are immersive, not boxed

A public figure's hero is the whole first screen, not a card with a headshot in it. The
standard, fleet-wide:

- **Full bleed and viewport height.** The hero occupies the first screen: `height:94svh`
  with `min-height:600px` and `max-height:1000px`. Use `svh`, not `vh` — mobile browser
  chrome makes `vh` overshoot and push the call to action below the fold.
- **The subject is the background, not a thumbnail.** No small boxed portrait, no framed
  inset, no stock-photo collage. The photograph is edge-to-edge and the type sits on it.
- **Join the image to the type with a mask, not a hard edge.** A horizontal
  `mask-image: linear-gradient(to right, transparent 0%, rgba(0,0,0,.35) 16%, #000 42%)`
  dissolves the photo into the text column so the two read as one composition.
  **Override it to a vertical mask on mobile** — a horizontal mask on a narrow screen
  fades the subject's face.
- **Control the crop with a focal variable**, e.g. `--focal: 56% 4%`, so the frame can be
  nudged per person without rewriting the block. Check the top of the head is not clipped.
- **Reset `box-sizing` on your own block.** These themes scope `border-box` to a theme
  wrapper, not `*`. A new hero inherits `content-box`, so `height:100%` plus padding
  overflows an `overflow:hidden` section and silently clips the calls to action out of
  frame — the page looks fine and the buttons are simply gone.
- **One primary call to action, in the brand colour, above the fold on a 1366×768
  laptop.** Verify at desktop, laptop and mobile widths before calling it done.
- **A proof rail under the fold, not claims inside the hero** — credentials, logos, or
  named results on a solid brand-colour band.
- **Motion is optional and must be silent.** A background video is permitted only when it
  is `muted`, `playsinline` and `loop`, with a poster image; see `nothing-plays-uninvited`.
- **The photograph has to earn full bleed.** Composed portraits and documentary
  photography can carry a hero; selfies cannot, at any resolution. When the only assets
  are selfies, use the typographic hero — it never looks cheap. See
  `photo-earns-full-bleed`.
<!-- shared-rule:immersive-hero-standard:end -->

<!-- shared-rule:keep-the-system-of-record-outside-the-model:start -->
## Keep the system of record outside any one model

- **Standards, SOPs, metadata and completed work live in files and repositories we own**,
  not inside one vendor's memory, project or chat history.
- **The test:** if the model changed tomorrow, could a new one pick up every piece of work
  in progress from the artifacts alone? If not, something important is stored in the wrong
  place.
- **Write it down where it can be read by anything.** Plain markdown, plain JSON, in a
  repository — not a proprietary format tied to one product.
- This is also why rules are copied into distributed skills rather than linked: the copy
  survives being separated from the system that made it.
<!-- shared-rule:keep-the-system-of-record-outside-the-model:end -->

<!-- shared-rule:lead-with-a-visual-executive-summary:start -->
## Every deliverable leads with a visual executive summary

- **Page one answers the question**, for someone who will read only page one. The most
  important and least obvious findings, up front.
- **Interesting and non-obvious, not a restatement.** A summary that repeats what the
  reader already assumed has told them nothing; lead with what would change their mind.
- **Use colour, diagrams and tables to carry the point.** A wall of text on page one is a
  failure of the deliverable, not a style preference.
- Depth still matters behind it — a substantial analysis runs long. The summary earns the
  reader's attention for the rest; it does not replace it.
<!-- shared-rule:lead-with-a-visual-executive-summary:end -->

<!-- shared-rule:learn-do-teach:start -->
## Learn it, do it, then teach it

- **Read the standard before you touch the work.** Skipping to doing produces output that
  looks right and is wrong in ways the person reviewing it has to find for you.
- **Then do it,** all the way to a verified artifact.
- **Then teach it** — write the run up so the next agent inherits what you learned. That
  write-up is what turns one person's lesson into everyone's default, and it is the whole
  reason `standards/` exists.
- The order is not a preference. A rule taught before it is understood is repeated
  without judgement; a rule learned and then taught survives contact with a case it did
  not anticipate.
<!-- shared-rule:learn-do-teach:end -->

<!-- shared-rule:links-must-resolve:start -->
## Every link and every entity claim resolves

- **A broken entity claim is worse than no claim.** `sameAs` is how a site tells Google,
  Bing and every AI answer engine "this person is that entity". Pointed at a deleted or
  wrong target, it does not merely fail — it actively teaches the wrong association.
- **Verify every `sameAs` target returns 200 before publishing schema, and re-verify
  quarterly.** Entities get deleted. A Wikidata item asserted on a client site was
  deleted on 7 July 2026 and the claim stood until an audit found it five weeks later.
- **Only anchors count.** `preconnect`, `dns-prefetch`, `canonical` and `alternate`
  hints are not links a visitor can follow, and treating them as links reports
  `googletagmanager.com` as a dead link on every site that loads analytics — noise that
  teaches people to ignore the sweep.
- **Request every outbound link before publishing.** A dead social link in a footer
  appears on every page of the site, which makes one careless paste a site-wide defect.
- Treat `401`, `403`, `405` and `429` from Instagram, Facebook, X and LinkedIn as *pass*.
  Those platforms block automated requests by policy; that is not a broken link, and
  reporting it as one trains people to ignore the sweep. `404`, `410`, `5xx`, DNS
  failure and connection timeout are real.
- When a target is genuinely gone, remove the claim rather than leaving it. An honest
  smaller `sameAs` set outperforms a larger one containing a lie.
<!-- shared-rule:links-must-resolve:end -->

<!-- shared-rule:no-black-buttons:start -->
## Never ship a black button

- A call-to-action button must use the site's brand colour, never black. Black buttons
  camouflage against dark heroes, navigation and footers, carry no brand signal, and
  measurably lose conversions. This is the single most repeated finding across hundreds
  of Local Service Spotlight website audits.
- Nobody ships a black button on purpose. It is the default in every builder —
  Gutenberg's `has-black-background-color` preset, Elementor's dark fill, Astra starter
  themes, any Bootstrap-derived `btn-dark`. It looks correct on the white editor canvas
  and disappears on the dark section it ships into. Assume the default is wrong and
  override it deliberately.
- Determine the brand colour, do not guess it: fetch the live pages, count hex values,
  and take the most-used non-neutral. Where a site has two strong non-neutrals, the
  darker is usually navigation and the brighter is the CTA — as gold `#f5a623` is to
  teal `#22698a` on Local Service Spotlight.
- Verify contrast before publishing. Text on a CTA needs at least 4.5:1. A gold or
  yellow button needs dark text, not white.
- Before reporting any site work as done, confirm the published HTML contains none of:
  `background:#000`, `background-color:#000`, `btn-dark`, `btn-black`, `button-black`,
  `bg-black`, or an applied `has-black-background-color` class.
- An element may keep a black fill only with a documented exemption class where black
  genuinely belongs — a logo lockup, an icon button on a dark rail. Mark it with the
  fleet's existing exemption class, `bm-keep-black` or `lss-keep-black`,
  so the sweep can see the exemption was
  deliberate. Exempt one element, never a default.
- Full reasoning and the enforcement-plugin pattern:
  https://blitzmetrics.com/why-we-dont-use-black-buttons/
<!-- shared-rule:no-black-buttons:end -->

<!-- shared-rule:no-flattery-tell-it-straight:start -->
## No flattery — tell it straight

- **Do not open with praise, and do not pad findings with reassurance.** The value of a
  report is the part that is uncomfortable; softening it destroys the only reason to read
  it.
- **Every claim is proof-driven** — name the URL, the number, the date, the source. "This
  looks great" is not a finding; "the sameAs target returns 404" is.
- **Say what is broken before what is working**, and be specific about how bad it is.
- Being wrong is recoverable. Being agreeable and wrong is not, because nobody checks
  the agreeable answer.
<!-- shared-rule:no-flattery-tell-it-straight:end -->

<!-- shared-rule:no-placeholder-copy:start -->
## Placeholder copy never reaches production

- **A number on a page is a claim.** Every stat needs a definition, a date, and someone
  who can say where it came from. If the same figure appears twice on a site it has to be
  the same figure.
- **Builder placeholder text is a defect, not a cosmetic issue.** "Lorem ipsum", "Your
  photo here", `xxx-xxx-xxxx`, `example@example.com` — each one tells a visitor the page
  was never finished, on the page where you are asking them to trust you.
- **A testimonial needs a real, nameable person.** No initials-only quotes, no
  "a client in Minneapolis".
- **The sweep only catches the obvious half, and you need to know which half.** A
  placeholder that looks like a real number — a hero stat reading "$34K Monthly MRR" that
  nobody can source — is indistinguishable from a true one to any regex. That exact
  string sat live on a paying client's site. The only defence is that whoever publishes a
  number can name its source before it goes up.
<!-- shared-rule:no-placeholder-copy:end -->

<!-- shared-rule:no-popup-on-load:start -->
## No popup on page load

- **Nothing covers the page before the visitor has read anything.** A modal that opens on
  load, on a timer, or on scroll-depth before the first section is finished interrupts
  the only moment you had their full attention, and it is the single most common reason a
  first-time visitor closes the tab.
- The permitted triggers are **click** and **exit intent on desktop**. A newsletter offer
  earns its place in the page, after the proof, as a section — not as an ambush.
- This applies to cookie and consent banners too: they may be present, but they must not
  block the content or be dismissable only by accepting.
- **Coverage is partial and you should know it.** These checks catch the three signatures
  that cover most of the fleet — Elementor's `page_load` trigger, the `auto_open` popup
  type, and load triggers declared in markup. A popup wired up in custom JavaScript will
  pass the sweep. When you touch a site, look at it once with a fresh session and no
  cookies; that is the only reliable test.
<!-- shared-rule:no-popup-on-load:end -->

<!-- shared-rule:no-unnamed-link-text:start -->
## No unnamed link text

- **Link text must name its destination when read on its own.** Screen readers and search
  engines both pull links out of context; "read more" out of context is nothing. Write
  "Read George's story", not "Read more".
- The banned set in practice: *click here, read more, learn more, continue reading,
  download, more, here, this, link.* If the anchor text is one of those words and nothing
  else, rewrite it.
- **An image-only link still needs a name.** A logo or social icon wrapped in an anchor
  needs meaningful `alt` text on the image or an `aria-label` on the link. `alt=""` is
  correct for decoration and wrong for a link — a link with no name is a link nobody can
  follow by voice or by ear.
- **An anchor points at the thing it names.** If the text says a company, the link goes to
  that company; if it says "LinkedIn", it goes to linkedin.com. Two links with identical
  anchor text going to different destinations on the same page is always a defect — one of
  them is lying.
- Expect the first sweep of an existing WordPress site to report this on archive and
  blog templates, where "Read more" is the theme default. That is one template edit, not
  a per-post fix, and it is why this rule reports rather than blocks.
<!-- shared-rule:no-unnamed-link-text:end -->

<!-- shared-rule:nothing-plays-uninvited:start -->
## Nothing plays at the visitor uninvited

The test is not "is there a video." The test is **would this irritate someone who
just arrived.** Motion the visitor chose to look at is atmosphere; sound and
motion that grab at them are an ambush, and the first thing they learn about you
is that your site did that.

- **Background video in a hero is encouraged.** It is how the immersive standard
  gets met. Ship it with all four of `muted`, `playsinline`, `loop` and a `poster`
  image. `playsinline` is not optional — without it, iOS yanks the video full
  screen the moment it starts, which is the loudest version of the thing this rule
  exists to prevent.
- **Sound never starts on its own.** A hero film may absolutely have an audio
  track. It loads muted with a visible, labelled unmute control, and the visitor
  decides. That satisfies both halves: the video is there, the ambush is not.
- **`<audio>` never autoplays**, muted or not. There is no case for it.
- **Embedded players count.** `?autoplay=1` on a YouTube or Vimeo iframe must be
  paired with `mute=1`, or dropped.
- **Anything that cannot meet the muted conditions ships without `autoplay`**,
  behind a poster frame and a play control.
- Judge the rest by the same intent, even where no regex covers it: a video that
  covers the content, one that cannot be paused, one that restarts on every scroll,
  or one that pushes the call to action off the screen is irritating whether or not
  it makes a sound.
- This is the published-page half of `silent-media-playback`. That rule stops an
  agent putting sound through *your* speakers while it tests; this one stops a site
  putting sound through a *visitor's* speakers.
<!-- shared-rule:nothing-plays-uninvited:end -->

<!-- shared-rule:order-proof-by-authority:start -->
## Order proof by authority, strongest first

- **Testimonials, logos and mentions are never in random order.** Score each on the
  30-point scale — 10 for who said it, 10 for where it was said, 10 for what they actually
  said — and lead with the highest.
- **A visitor reads the first two and leaves.** Whatever is in position one is, in
  practice, your entire proof section.
- **Video beats text.** The same endorsement on camera is more persuasive and harder to
  fake than the same words in a pull quote; capture it as video wherever it exists.
- Cut the bottom of the list rather than padding it. A short list of strong proof
  outperforms a long list containing weak proof.
<!-- shared-rule:order-proof-by-authority:end -->

<!-- shared-rule:photo-earns-full-bleed:start -->
## A photograph has to earn full bleed

- **Judge the genre before the pixels.** Composed portraits, stage photography and
  third-party documentary shots can carry a full-bleed hero. Phone selfies, webcam grabs,
  cropped group photos and screenshots cannot — at any resolution, under any treatment.
  Resolution and file size say nothing about whether an image can be six feet wide behind
  a headline.
- **Open every candidate before you rank it.** Selecting by filename, dimensions or
  weight is how a selfie ends up presented as a hero option. If you have not looked at
  the image, you have not evaluated it.
- **When the only assets are selfies, use the typographic hero.** A confident type
  composition on a brand-colour field never looks cheap; an enlarged selfie always does.
  Say plainly that better photography is the unblock, and what to shoot.
- **Full bleed magnifies everything.** Soft focus, a cluttered background, a bad crop and
  mixed colour temperature are all invisible in a thumbnail and unmissable at full width.
- Related: `immersive-hero-standard` for the construction; this rule is only about
  whether a given photograph is allowed to be the hero at all.
<!-- shared-rule:photo-earns-full-bleed:end -->

<!-- shared-rule:pre-audit-before-the-client-does:start -->
## Audit our own work before anyone else can

- **Assume an outside expert will audit everything you ship**, and build so that audit
  comes back clean. That assumption is what makes the work honest rather than merely
  presentable.
- **Run the adversarial pass yourself, before delivery.** Find the broken thing while it
  is still cheap and while finding it is a credit rather than a defence.
- **Give the client the same auditing tools you use.** Work that only survives because
  nobody looked closely is not work worth selling.
- Ship the audit result alongside the deliverable, including what it found.
<!-- shared-rule:pre-audit-before-the-client-does:end -->

<!-- shared-rule:process-real-content-never-generate:start -->
## Process real content; never generate it

- **Every published piece starts from something real** — a recording, a call, a job
  actually done, a person actually speaking. AI processes that raw material; it does not
  invent the material.
- **The provenance must survive to the page.** Link the video, embed the clip, name the
  person, cite the date. A reader — and a language model reading on their behalf — should
  be able to trace the claim back to the moment it was said.
- **Repurpose one source across every surface** rather than generating a fresh piece per
  channel. The article, the short, the profile post and the email come from the same
  recording.
- An article with no traceable source is indistinguishable from an invented one, and will
  eventually be treated as invented.
- The sweep looks for a source artifact — an embed, a captioned figure, or an attributed
  quote — and reports rather than blocks, because a well-sourced piece can still fail the
  proxy. Treat a hit as "check where this came from", not as proof it was generated.
<!-- shared-rule:process-real-content-never-generate:end -->

<!-- shared-rule:qa-from-a-different-context-window:start -->
## QA comes from a different context window

- **Self-QA is necessary and never sufficient.** The agent that made a mistake is the
  agent least able to see it, because the reasoning that produced the mistake is still
  in its context.
- **Audit work with a second agent started fresh**, given the artifact and the standard
  but not the first agent's reasoning. Delegate it explicitly rather than re-reading your
  own output.
- The auditor's job is to **refute**, not to confirm. Brief it that way.
- This applies to your own work most of all. If you cannot spawn an auditor, say the work
  is unaudited rather than implying it was checked.
<!-- shared-rule:qa-from-a-different-context-window:end -->

<!-- shared-rule:report-business-impact-not-volume:start -->
## Report business impact, never volume

- **Count outcomes, not output.** Posts published, words written and tasks closed are
  activity. Calls, booked jobs, leads and revenue are results.
- **Trace the chain and show it**: published thing → ranking or traffic → call or lead →
  booked job → revenue. Where the chain breaks, say where it breaks rather than reporting
  the last link that looked good.
- **Impressions and clicks are context, not the headline.** Never lead with them.
- If the business impact cannot be measured yet, say that plainly and fix the measurement
  first — see `analytics-on-every-page`.
<!-- shared-rule:report-business-impact-not-volume:end -->

<!-- shared-rule:verify-by-opening-the-live-artifact:start -->
## Verify by opening the live artifact

- **"I did it" is not evidence. The artifact is.** Before reporting any work complete,
  fetch the live URL, open the file, or query the API and confirm the change is actually
  there. An agent that has been caught reporting published articles onto a site with no
  articles has burned more trust than the task was worth.
- **Check the thing a user would see, not the thing you wrote.** A database row is not a
  published page — caches, builders and permissions all sit in between. Fetch the public
  URL as an anonymous visitor.
- **A page that could not be fetched has not been verified.** Report it as unverified,
  never as done.
- Quote the evidence in the report: the URL, the status code, and the string you found.
<!-- shared-rule:verify-by-opening-the-live-artifact:end -->

<!-- shared-rule:spoken-urls-must-resolve:start -->
## Every URL we say out loud resolves

- **A URL spoken from a stage, printed on a QR code, or read into a podcast has no
  inbound link.** No crawler finds it, no internal link audit sees it, and no analytics
  records it until a human types it and fails. It is the one class of URL that dies
  completely silently, and the people who hit the 404 are the warmest audience we ever
  get.
- **Every hub domain answers the same short paths.** `/install/`, `/skills/` and
  `/activate/` resolve on every site we tell an audience to visit — 200, or a 301 to the
  page that actually serves that intent. Never a 404.
- **Say it once, spell it the same way everywhere.** If the talk says "slash install",
  every hub answers `/install/`. Do not rely on one domain having a page while another
  has a redirect and a third has nothing.
- **A short path is a promise, so keep it even after the page moves.** When the
  destination is renamed, repoint the redirect in the same change. The short path
  outlives every page it has ever pointed at.
- **Redirect within the domain the audience was told to visit** where a suitable page
  exists. A cross-domain hop from a QR code loses the brand impression at the exact
  moment it was earned.
- **Check it from outside, logged out.** An editor screen saying "saved" is not a
  resolving URL, and a page cache can serve a stale 404 long after the rule exists.
  See `verify-by-opening-the-live-artifact`.
- Adding a spoken path to a talk, a slide or a business card means adding it to this
  rule's `paths` list in the same week. That is the whole maintenance cost, and it is
  what stops this being rediscovered every few months.
<!-- shared-rule:spoken-urls-must-resolve:end -->

<!-- shared-rule:every-public-page-has-real-imagery:start -->
## Every public page shows real people or real work

- **Every visitor-facing content page must contain at least one meaningful image
  of the actual business: its people, its work, its customers with permission,
  its product, or its place.** This includes conversion and utility pages such as
  Contact, Estimate, Pricing, Financing, Warranty, Privacy, and Thank You. Do not
  ship a wall of text.
- A logo, icon, tracking pixel, abstract decoration, AI-generated image, or stock
  photograph does not satisfy the rule. Neither does an unrelated real photo
  added merely to pass a count. The image must help a visitor understand or trust
  the page.
- Use the business's approved source library. Give the image honest alt text and,
  when useful, a caption that explains what it proves. Describe only what the
  source establishes: never relabel one project photo as work completed in every
  city, and never infer a person, location, service, or result from a filename.
- If no suitable approved image exists, request one and block that page from
  publication. Do not manufacture evidence with image generation or stock.
- Build QA must inventory every rendered content route and fail when any route
  lacks a verified real image. Keep a provenance allowlist or equivalent asset
  record so logos and decorative images cannot make the check pass. Mark at least
  one qualifying `<img>` per page with `data-lss-real-image="verified"` only
  after that provenance check. Also inspect the rendered desktop and mobile page;
  a hidden, broken, or contextless image does not count.
- Machine-only documents and routes that never render as visitor content—such as
  `robots.txt`, XML sitemaps, feeds, and true HTTP redirects—are exempt. A
  browser-rendered redirect placeholder is not exempt; replace it with a real
  redirect or make the page comply.

The fleet check proves only that a page declares the verified marker and supplies
a nonblank, non-data source plus nonblank alt text. It cannot prove that the
source loads, is visible, is meaningfully sized, or is truthful. Enforce those
claims with each site's provenance-aware build validator plus a human visual
review. Never add the marker merely to make the sweep pass.
<!-- shared-rule:every-public-page-has-real-imagery:end -->

<!-- shared-rule:basecamp-updates-stay-in-basecamp:start -->
## Basecamp updates stay in Basecamp

- Never use Gmail Reply, Reply All, Forward, Send, or Draft to
  `notifications@app.basecamp.com` or `notifications@3.basecamp.com`. Those
  visible From addresses are notification infrastructure, not destinations.
- Post the update in the exact existing Basecamp thread through an authorized
  Basecamp connector, API, or the Basecamp UI. The company delivery rail is
  Basecamp itself, so do not substitute a per-message
  `*@replies.app.basecamp.com` email token even when one is present.
- Before any Gmail mutation, inspect the resolved To and Cc fields. If either
  contains a generic Basecamp notifications address, stop without creating or
  sending the message.
- Changing the Gmail From identity does not repair this failure. In the
  incident that produced this rule, the connector resolved the visible From
  address as the recipient and discarded Basecamp's unique Reply-To route; the
  result was an `Email Received in Error` bounce and no Basecamp comment.
- A Basecamp update is complete only after readback proves the live thread URL
  or recording ID, the expected author, and a unique phrase from the comment.
  A Gmail SENT item is not proof. If no Basecamp write path exists, report the
  blocker and put the intended update in the run result; do not fall back to
  email.
- Embed this rail directly in every scheduled or cloud task that may touch
  Basecamp. Such runs may not load repository instructions before using an
  already-authorized Gmail tool.
- This rule controls the delivery path; it does not grant permission to post or
  weaken any existing human approval requirement.
<!-- shared-rule:basecamp-updates-stay-in-basecamp:end -->

<!-- shared-rule:screen-gct-before-amplification:start -->
## Screen GCT before amplification

- **Qualification is an evidence gate, not an execution grant.** A passing business-fit
  screen still needs independent review, an accepted scope/agreement receipt, and the
  authoritative Ops roster decision before onboarding or recurring work.
- **Gate outcome and evidence quality are separate.** Every GCT gate records outcome
  `UNKNOWN | MET | NOT_MET` and evidence state
  `UNKNOWN | OBSERVED | VERIFIED | CONTRADICTED | EXPIRED`. Unknown is never zero or
  failure; preserve the exact question, owner, due date, and blocked action.
- **Verdicts are deterministic, not scored.** Evaluator disagreement, an `UNKNOWN`
  outcome, or any evidence state other than `VERIFIED` routes to
  `DISCOVERY_REQUIRED`. With no discovery condition, verified `NOT_MET` routes to
  `DEVELOP`. Only eight verified `MET` pairs can be `QUALIFIED_PENDING_REVIEW`.
- **Amplify what is already working.** Verified new-idea, no-proof, undifferentiated,
  overbroad-ICP, unfocused-offer, or capacity conditions route to one development action
  and re-screening. They do not earn plumbing, publishing, or ad spend as a consolation.
- **Fail closed on authority.** Prospect screening is public-read-only. Publishing,
  messaging, permissions, Basecamp delivery, and spend require exact scoped approval;
  `Not Active`, `HOLD`, missing roster evidence, or blocked plumbing stops execution.
- The public guide is https://blitzmetrics.com/social-amplification/. The operational
  control plane is the roster-driven Money Tree; derived output folders are not state.
<!-- shared-rule:screen-gct-before-amplification:end -->

<!-- shared-rule:content-factory-four-stages:start -->
## Content Factory four stages

- The Content Factory line is locked: **Produce → Process → Post → Promote**.
  Do not rename, reorder, or merge these four.
- **Plumbing** is onboarding / access / tracking **before** the factory
  (`client-access-checklist`). It is not a factory stage.
- **Perform** is MAA (Metrics → Analysis → Action) **after** the factory /
  promotion loop (`weekly-brand-maa`). It is not a factory stage.
- If copy still lists Plumbing / Publish / Promote / Perform as the factory's
  4 P's, or uses Publish instead of Post inside that line, rewrite to the locked
  names. Upstream skill: `skills/content-factory/SKILL.md`. Canon pages:
  https://blitzmetrics.com/content-factory/ and
  https://blitzmetrics.com/the-4-stages-of-the-content-factory/.
- SAE course map (Plumbing → Goals → Content → Targeting → Amplification →
  Optimization) is separate; the Content Factory block inside it is still only
  Produce → Process → Post → Promote.
<!-- shared-rule:content-factory-four-stages:end -->

<!-- shared-rule:explain-with-linked-examples:start -->
## Explain with linked examples

- When explaining a concept (GCT, Content Factory, Dollar-a-Day, MAA, SAE, Nine
  Triangles, or similar), always **show and link** at least one concrete example.
  A definition alone is incomplete.
- Prefer live canonical URLs: Task Library, Local Service Spotlight, blitzmetrics.com
  SEO leaves, dennisyu.com. Never invent example URLs.
- Pattern: one sentence what it is, one sentence why it matters, then the linked
  example(s).
- Starters: GCT → Task Library GCT task + theninetriangles.com; Content Factory →
  https://blitzmetrics.com/content-factory/ and name Produce → Process → Post →
  Promote; MAA → weekly-brand-maa / a client-safe Friday MAA; Dollar-a-Day → method
  page + one public-safe winner when available.
<!-- shared-rule:explain-with-linked-examples:end -->

<!-- shared-rule:lss-is-the-public-company:start -->
## Local Service Spotlight is the public company

- **Dennis's current company in new public copy is Local Service Spotlight**, plus the
  vertical spotlight sites (law firm, pest control, dunker, and the rest). Be specific
  to that vertical. Do not present a sunset brand as the current company.
- **Do not name the sunset brand (BlitzMetrics) in new public pages, client-facing
  emails, social posts, or new product copy.** Historical URLs and git history may
  still contain it. Do not add more.
- **The existing canon/audit domain remains a publish host** for definitive articles
  and audits. Linking that URL is fine. Calling it the current company is not.
- Prefer `@localservicespotlight.com` addresses in new mail. Legacy aliases may still
  deliver; they are not a reason to put the sunset name in the body.
- This does not rewrite old articles or legal entity paperwork. It is a public-facing
  naming rule for new work.
<!-- shared-rule:lss-is-the-public-company:end -->

<!-- shared-rule:outbound-email-names-the-agent:start -->
## Outbound email names the agent

- Every outbound email an agent **sends** (or hands off ready-to-send) must end with a
  one-line closer that names which agent wrote it: Grok Bot, Claude, ChatGPT, Codex,
  Cursor, Perplexity, Gemini, or the desk name (e.g. `— Grok Bot (Ops)` /
  `Sent via Claude`).
- Name the agent even when `From:` is a human (Dennis). The From address is delivery;
  the closer is transparency.
- Place the agent line after the body and before any mail-client legal footer.
- Do not invent a fake human VA signature to hide that an agent wrote it.
- This does not override send-approval gates. When a desk is authorized to send, the
  signature is mandatory. When only drafting, still include the agent name in the draft.
<!-- shared-rule:outbound-email-names-the-agent:end -->
