---
name: "geo-visibility-audit"
description: "Measure how AI models actually see a person or brand — query ChatGPT, Gemini, Perplexity and Claude live, score identity vs discovery presence, name every citing source, and produce the weekly MAA GEO block. Use when asked for GEO rankings, AI citations, LLM visibility, AI share of voice, 'are we showing up in ChatGPT', or when a weekly MAA needs a GEO section. Also use to troubleshoot why Ahrefs Brand Radar or a mentions database reports zero for a person's name."
rule-scopes: published-html, design-review
---

# GEO Visibility Audit

**Use this when** someone asks how a client shows up in AI answers — or when a weekly MAA needs its GEO block. Runs for a person, a company, or both at once. Takes about 15 minutes of tool time.

**The core insight this skill exists to encode:** indexed AI-citation tools cannot see individuals. They sample prompts by search volume, and a person's name has almost none. Reporting their zero as a finding is a measurement artefact. **You must query the engines live.**

## Inputs

- The person's name, plus every spelling and transliteration they use (Paul/Pavlo, diacritics, maiden names).
- Their owned properties: personal domain, company domain, community/event domain.
- Their claimed positioning — what they *want* to be known for. Get this from the `personal-brand-strategist` brief if one exists.
- Their buy box: who hires them, for what, where. This is what generates the discovery prompts.

## The method

### 1. Build the prompt ladder — two tiers, always

The whole audit turns on separating these. → `references/prompt-ladder.md`

**Known-item tier** — the prompt names the person or their company. Tests whether the entity exists in the model and is described correctly.
- "Who is {name}?"
- "Who is the CEO of {company}?"
- "Who runs {community/event}?"
- "Is {company} any good? What do reviews say?"

**Discovery tier** — the prompt describes a *need*. Tests whether they get recommended to a stranger. This is where the money is.
- "Best {category} agency in {geo}"
- "Top {category} experts to follow in {year}"
- "Who are the top {category} speakers in {geo}?"
- One long, high-intent buyer question written in the voice of their actual buyer, with revenue, platform and constraint named.

Minimum 4 known-item and 5 discovery. Run known-item across **all four engines**; discovery can be ChatGPT-led with one Perplexity long-tail.

### 2. Query the engines live, capture the sources

Exact working calls in `references/tool-recipes.md`. Summary:
- **ChatGPT** — `ai_optimization_chat_gpt_scraper`, `force_web_search: true`. Returns `sources[]` with domain + title, and `brand_entities[]` which tells you how the model *categorises* the person. Set `location_name` to their market.
- **Gemini / Perplexity / Claude** — `ai_optimization_llm_response`, `web_search: true`. Perplexity returns the richest citation list; Gemini returns grounding annotations mapped to specific sentences.

Record for every prompt: engine, named yes/no, every source domain, and who won instead when they lost. **The losers' source pages are the action list** — the model just told you which directory it shops at.

### 3. Score it

| Metric | How |
|---|---|
| Engines recognising | of 4, on the identity prompt |
| Distinct citing domains | unique domains across all answers |
| Citation instances | total source links returned |
| Third-party share | citations not on an owned domain ÷ total |
| Known-item won | x of n |
| Discovery won | x of n |
| Claim consistency | for each claim, how many of 4 engines surfaced it |

Third-party share is the one to watch. An answer sourced only from the client's own site reads as self-assertion and is fragile. Corroboration is what makes an entity durable.

### 4. Cross-check the link profile — and filter spam before you report it

Pull referring domains with `is_spam` in the select and **report the clean count, never the raw count.** Link-farm blasts arrive automatically once a domain starts ranking; a raw "+23 referring domains this week" can be 23 spam domains and zero real ones. → `references/tool-recipes.md`

Then check that the clean domains and the citing domains are the same names. When they are, you can show the causal chain end to end: placement → link → citation. That is the most persuasive thing in the whole report.

### 5. Write it up

Report structure and the MAA block in `references/report-template.md`. Build the visual report with the `dataviz` skill — validate the palette, never eyeball it.

## Output

- HTML report, self-contained, light + dark, hover tooltips, table view behind every chart.
- A GEO block for the weekly MAA (6 lines, pasteable).
- An action list where every item names the specific page or directory to get onto, taken from the losing answers.

## Definition of done

- Every engine queried live in this run — no numbers carried over from last week without a re-run.
- Every citing domain named. "15 domains" without the list is not a finding.
- Every discovery loss names who won and which source page the model used.
- Spam-filtered link numbers, with the raw number shown beside it so nobody thinks we hid it.
- At least one item in the action list is something the client can do this week.

## Troubleshooting — read this before reporting a zero

| Symptom | Cause | Do this |
|---|---|---|
| Ahrefs `site-explorer-ai-responses-count` returns 0 for a personal domain | Ahrefs replays a fixed prompt panel sampled by ask-volume. A person's name has none. | Query live. Report the live result; note the index gap rather than the zero. |
| `Missing addon: Brand Radar ["Chatgpt"]` | Per-engine paid add-on. | Note it, price it, move on. It would still be volume-sampled. |
| Mentions database returns nonsense for a name | Keyword databases word-match. "Dennis Yu" matched *Yu Yu Hakusho* and Dennis Trillo. | Never use keyword-matched mention data for people. Live query only. |
| Model returns a different person with the same name | Real name collision. | Add a disambiguator to the prompt ("the ecommerce consultant"), and flag it — it is a Knowledge Panel risk worth its own action. |
| Model describes them accurately but cites only their own site | No corroboration yet. | This is the finding. Third-party share is the metric; the action is placements, not more self-published articles. |

## Field lessons

- **Publishing volume does not create citations.** One client published 299 articles on his personal domain and the indexed AI citation count stayed at zero, while his company site — with a Clutch profile and a Trustpilot page — earned 11. Directory and review presence beats owned-content volume for discovery-tier prompts, every time.
- **The losing answer is more useful than the winning one.** A win tells you it worked. A loss hands you the exact URL of the roundup page the model reads.
- **Check every language and spelling the person lives in.** An English-only audit of a non-English person measures your search, not their authority.
- **Our own knowledge-base articles get cited.** Once a client has a page on blitzmetrics.com, Perplexity started using it as a corroborating source. Publishing the client's knowledge base is itself a GEO placement — say so in the report.
- **Never criticise the previous week's report to make this week's look better.** Show what the older method could not see, then hand over the method that can.

## Pairs with

← `personal-brand-strategist` (what they claim) · ← `positive-mentions-harvester` (the proof to place)
→ `dataviz` (build the charts) → the weekly MAA thread.

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
- After the short plain-language context, put an explicit **open questions and
  missing access** block near the start of every plan. If the list is empty, say
  so — that is information too.
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


The typographic fallback still follows `visuals-above-the-fold`: pair the type
with the authentic small-format photograph or a useful topic-specific diagram
in the first screen. A text-only first screen is no longer an allowed fallback.
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
- **Open with the reader's decision and the value of this deliverable.** In the
  first two or three sentences, connect the strongest supported finding to the
  reader's situation and the action it enables. Follow
  `every-article-and-project-starts-with-specific-gct`; a title, biography,
  table of contents or methodology paragraph alone does not orient the reader.
  On a multi-page document or deck, each later page or section also leads with
  its useful takeaway, without repeating the whole introductory pitch.
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

- **Qualified testimonials, logos and mentions are never in random order.** After each
  record passes its truth, identity, permission, and relevance gates, score it on the
  30-point scale — 10 for who said it, 10 for where it was said, and 10 for what they
  actually said. Lead with the strongest useful proof for this reader.
- **A visitor reads the first two and leaves.** Whatever is in position one is, in
  practice, your entire proof section.
- **Who does not substitute for What.** A recognizable person's silent appearance can
  still be weak proof, and their name does not transfer status by proximity. The score
  controls selection and order; `show-the-moment-not-the-resume` controls the public
  telling. Start with what happened and why it matters, not the person's fame.
- **Video beats text when it preserves the meaningful moment.** The same attributable
  praise or useful exchange on camera is more persuasive and harder to fake than a pull
  quote. A contextless clip or photograph remains appearance evidence, not endorsement.
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


The typographic fallback still follows `visuals-above-the-fold`: pair the type
with the authentic small-format photograph or a useful topic-specific diagram
in the first screen. A text-only first screen is no longer an allowed fallback.
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

- **Every visitor-facing content page must contain at least one meaningful visual
  of the actual business: its people, its work, its customers with permission,
  its product, its place, or an accurate diagram of its actual process.** This includes conversion and utility pages such as
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
- If no suitable approved photograph exists, use a useful evidence-backed
  diagram or verified source-video poster under `visuals-above-the-fold`. Do not
  manufacture evidence with image generation or stock. If none is available,
  hold publication and record the specific source gap and next action.
- Build QA must inventory every rendered content route and fail when any route
  lacks source-verified meaningful visual proof. Keep a provenance allowlist or equivalent asset
  record so logos and decorative images cannot make the check pass. Mark at least
  one qualifying `<img>` per page with `data-lss-real-image="verified"` only
  after that provenance check. For a diagram, video or photographic background,
  use `data-lss-visual-proof="verified"` with an honest aria-label/title after
  source review. This alternate marker never makes an empty shell or unrelated
  image pass. Also inspect the rendered desktop and mobile page;
  a hidden, broken, or contextless image does not count.
- Machine-only documents and routes that never render as visitor content—such as
  `robots.txt`, XML sitemaps, feeds, and true HTTP redirects—are exempt. A
  browser-rendered redirect placeholder is not exempt; replace it with a real
  redirect or make the page comply.

The fleet check proves only that a page declares the verified marker and supplies
the required description (plus a non-data source and alt for img). It cannot prove that the
source loads, is visible, is meaningfully sized, or is truthful. Enforce those
claims with each site's provenance-aware build validator plus a human visual
review. Never add the marker merely to make the sweep pass.

Dennis's 2026-09-05 instruction explicitly accepts diagrams, pictures or embedded
video above the fold. That supersedes the earlier photo-only fallback without
weakening authenticity: an accurate process diagram is useful proof, and a
video poster must belong to the verified source. Do not add an unrelated photo
merely to satisfy the older marker check.
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
## Every outbound agent action names the agent

- **When agent-authored content reaches another person, name the agent in the
  message itself.** This covers sent email, Basecamp comments and messages,
  DMs, support replies, scheduled reports, and the human-visible receipt for a
  publish or system change. A GitHub commit or private log is supporting
  evidence, not a substitute for visible attribution.
- End with one compact line:

  `Agent receipt: <agent> [<model if known>] · action: <drafted|sent|posted|published|changed> · human review: <reviewed by Dennis|authorized, not separately reviewed|no human review recorded>`

- Put the name a human recognizes first: `Claude`, `Codex`, `Grok`, `Cursor`,
  or the actual agent name. A persona alone is ambiguous; write `Grok — Meter
  Maid`, not only `Meter Maid`. Include the exact model only when the runtime
  exposes it. Otherwise omit it or say `model UNKNOWN`; never infer it from the
  writing style, OAuth client, or vendor name.
- State review truthfully. `Reviewed by Dennis` requires evidence that Dennis
  reviewed that exact message or action. Permission to act is not review, so
  use `authorized, not separately reviewed` when that is what happened. If the
  record is missing, use `no human review recorded`.
- Resolve the exact destination, audience, thread or record before acting. If
  routing or authority is unclear, fail closed instead of sending to Dennis or
  asking him to relay the work.
- An outbound action is complete only after source-system read-back verifies
  the destination/audience, thread or record, intended content/result, and
  agent receipt. A toast, sent item, commit, or private note alone is not proof.
- Leave the next action with its real owner. For completed Gmail work, archive
  the exact thread after verified action and restore it after seven days only
  when no human reply arrived; automation and system notices are not human
  replies.
- Name the agent even when `From:` or the source-system creator is Dennis. That
  identity is the delivery account; the receipt is authorship and action
  transparency. Place the receipt after the body and before any automatic legal
  footer.
- If an agent only prepared material and a human sent the final version, use
  `Prepared with <agent>; sent by <human>` when attribution is appropriate. Do
  not label a purely human-authored message as agent-authored, and never invent
  a fake human assistant signature to hide agent authorship.
- For a public page or code change, put the line in the delivery receipt or
  source-system update; do not add operational metadata to visitor-facing copy
  unless the publishing brief asks for it.
- This rule grants no authority to send, post, publish, spend, merge, or change
  access. Apply the existing approval and destination rules first. Once an
  outbound action is separately authorized, attribution is mandatory. When only
  drafting, include the agent name in the draft so it survives handoff.
- Scheduled prompts that may act externally must explicitly use the
  `outbound-action-closeout` skill and embed its routing, receipt, read-back,
  ownership, and fail-closed rails because an unattended session may not load
  repository rules or prior conversation.
<!-- shared-rule:outbound-email-names-the-agent:end -->

<!-- shared-rule:definitive-articles-show-what-they-are-and-where-they-fit:start -->
## Definitive articles show what they are, their evidence strength, and where they fit

- **Name the kind of canonical page before judging it.** A task-definitive article
  is the maintained recipe for one repeatable task. A topic, entity or framework hub
  explains its subject and links to the task recipes it owns; it need not pretend to
  execute one task. Supporting stories, opinion pieces, tool comparisons, references,
  historical posts and meta-articles remain distinct. A repaired opening, lead visual,
  incoming link or prior fleet-audit label does not promote any of them to a task SOP.
- **A task recipe must let another worker repeat and check the work.** Require all of:
  the trigger and starting state; required inputs and access; linked prerequisite tasks
  and their expected outputs; ordered steps with decision points; the measurable output
  and observable pass/fail criteria; and the downstream task, receiving owner/function
  and handoff artifact. Link the canonical task in the
  [Task Library](https://local-service-spotlight.github.io/task-library/) and its parent in the
  [Content Factory](https://blitzmetrics.com/content-factory/). Do not invent a task,
  prerequisite, threshold or relationship to fill a box. Mark a missing required field
  as a gap and hold task-definitive certification until the source supports it.
- **Keep the recipe separate from each execution record.** Every task execution writes
  a [meta article recording the run](https://localservicespotlight.com/meta-articles/)
  using the [meta-article guidelines](https://blitzmetrics.com/meta-article-prompt/).
  It links to the exact canonical task, the recipe revision used and the run evidence.
  Writing is required; publishing the meta article and changing the canonical recipe
  follow the existing authorization for those actions. The run record feeds reviewed
  improvements back into the recipe and skill; it never becomes a second recipe.
- **The marker is a reviewed semantic claim, not a workflow status.** Mark a page as a
  Definitive Article, Definitive SOP or Definitive Framework only after a reviewer has
  confirmed that its labels, steps, links, evidence and canonical ownership agree with
  the accepted source of truth. A complete Task Library task, an all-tasks-complete hub,
  a taxonomy term or a `READY` state is useful workflow evidence, but none is sufficient
  by itself. An archive, alias, WIP page or semantically conflicted page gets no marker.
- **Mark the reviewed canonical hub visibly.** Put the appropriate marker above the
  opening summary so a reader can distinguish the maintained source of truth from a
  supporting post before scrolling. Supporting stories, updates and meta-articles point
  to the hub; they do not wear the marker themselves.
- **Keep certification, task priority and evidence volume separate.** Definitive status
  says the page is the reviewed canonical owner. Task importance decides which gap to
  work first. Meta-orbit strength measures only the number of verified completed-run
  meta-articles behind the hub. None of the three may be used as a proxy for another.
- **Derive each named metric from evidence; never type it into two sources.** One
  generated manifest owns the exact hub URL, mapped Task Library tasks, counted and held
  evidence records, known execution IDs or explicit missing-ID states, audit time,
  metric names, counts and strength bands. The article and Task Library render from
  that manifest. Keep historical public-example volume separate from verified task
  execution frequency. If a metric cannot be checked, report `unknown`; if only a lower
  bound is proved, report `partial`. Never turn either into zero.
- **Preserve dated public-example counts as article volume.** An earlier review may
  establish that a hub had a stated number of qualifying public meta articles on its
  audit date without establishing execution IDs. Keep that dated evidence and its
  inspectable sources. It remains historical public-example volume; it is not a claim
  of that many distinct task runs. Missing IDs do not erase verified article evidence.
- **Count task execution frequency separately.** Deduplicate each canonical task's
  executions by ID and state the reporting period and result statuses. Revisions,
  retries within one run, translations, clips and syndicated copies do not create
  executions. A separately scoped rerun has its own ID and evidence. Keep failed/partial
  and unpublished runs in internal history with their statuses. Older articles without
  a reliable run identity cannot establish execution frequency; that metric remains
  UNKNOWN or PARTIAL even when their dated article-volume count is valid.
- **Count a primary worked example, not a generic cross-link.** A counted meta-article
  must be published, explicitly classified as a meta-article, document a completed run,
  materially execute the hub's task, and link to the exact canonical hub in its
  task-specific narrative or receipt. A shared framework map, compliance table,
  related-reading list, template, index, instructional page, archive, self-link or
  incidental concept mention does not make the post part of that hub's orbit. Preserve
  the reason for every excluded or held candidate.
- **Use fixed, transparent evidence bands.** Show the exact count next to the definitive
  pill and label 0 as `No verified examples`, 1–2 as `Emerging`, 3–5 as `Supported`,
  6–10 as `Strong`, and 11+ as `Deep`. This label measures documented-run volume only,
  not accuracy, freshness, traffic, quality or certification. Do not emit rating or
  review schema from it.
- **Make the graph work in both directions.** The Task Library task links to the final
  canonical article. The article's generated, collapsed evidence footer links to the
  exact filtered Task Library route and back to every counted meta-article. A stable
  `?task=` route opens one task and a stable `?article=` route opens the complete hub.
  A count without its inspectable source URLs is decoration, not evidence.
- **Lead with the specific GCT and the article's own evidence.** In 2–3 sentences
  at fifth-grade reading level or below, name who this is for, what it does, why
  it matters and the useful outcome. Use the reader's actual situation and the
  mechanism or evidence that makes the outcome useful; follow
  `every-article-and-project-starts-with-specific-gct`. A generic benefit claim
  or an acronym definition is not a passing opening. Keep the topic-specific visual beside that
  short opening in the first screen; it may lead. A checklist is secondary and
  must not push it below the fold. Keep the most
  specific primary visual or proof for that article above the fold: the actual framework
  diagram on a framework hub, the task-specific screenshot or flow on a software SOP,
  or the real photograph, artifact or result that proves the work. A generic system map
  must never displace that evidence or push it below the fold. Keep the audience in
  the opening; move extended background, history and secondary evidence below it.
- **Show where a task fits after its first-screen orientation.** A Content Factory task
  needs a responsive context diagram lower in the article: Produce → Process → Post →
  Promote in the maintained order, only the work this task performs highlighted, and
  linked prerequisites → this task → the next task. Show the meta-record feedback into
  the canonical recipe. This context map is additional to the topic-specific lead
  visual. Keep access/tracking before the factory and measurement after it when those
  boundaries apply. An unverified placement stays a stated gap; it is not permission
  to invent a station or certify a task with an unknown handoff.
- **Use the larger system map as truthful context.** When an established framework has
  an exact relationship to the article, place its maintained detailed map after the
  article-specific primary visual and highlight only the subcomponents the article
  actually performs. Keep surrounding components visible but muted and caption what the
  highlight and handoff mean. On a framework hub, the canonical framework diagram is
  itself the primary visual and may serve both purposes.
- **A stage-only highlight or no map is valid.** If the task belongs to a stage but no
  named child station truthfully represents it, highlight only the stage and, where
  useful, its verified boundary or handoff. If no honest placement exists, omit the map
  and explain the cross-system relationship in text. Never activate a nearby box merely
  to make the diagram look complete.
- **Do not redraw a framework from memory.** Reuse the maintained labels, order, palette
  and relationships. A task-specific flow may accompany the system-placement view, but
  neither visual may make a relationship the accepted source does not support.

No fleet regex can enforce this honestly: a crawler cannot infer canonical ownership,
primary-parent evidence, truthful framework placement or whether a generic link documents
a completed run. Enforce it in the semantic preflight, source-backed orbit manifest,
bidirectional-link verifier and rendered desktop/mobile review.
<!-- shared-rule:definitive-articles-show-what-they-are-and-where-they-fit:end -->

<!-- shared-rule:named-entities-link-to-the-most-helpful-canonical-destination:start -->
## Named entities link to the most helpful canonical destination

- **Route the first meaningful mention of a named entity to the page that best helps
  the reader understand or act on it.** Link once; do not turn every repeated name
  into a link. Use the entity's natural name for a person or company, and use 3–6
  descriptive words for a training or concept link.
- **People point to their verified personal-brand home.** Prefer the person's owned
  website over an author archive, search result or social profile. If no owned site can
  be verified, use the relevant first-party company page or a canonical article that
  establishes who the person is; otherwise leave the name plain.
- **Companies point to their owned company site.** Correct the entity name before
  linking it. A plausible domain for the wrong spelling teaches the wrong association.
- **Tools and concepts point to our canonical training when it exists.** In explanatory
  copy, use a destination-naming phrase such as "our Listen Notes inventory guide" for
  the definitive how-to page; do not point the bare product name at our domain. Put the
  product's natural name and official website on the execution step where the reader
  actually opens it. This preserves both education and a direct path to action without
  making the anchor lie about where it goes.
- **Search our article inventory before choosing a provider help page.** Look up
  the object in the Canonical Directory, Task Library and site search, then read
  the candidate to verify that it answers this reader's question. For Obsidian,
  use “our Obsidian setup guide” when that guide is the relevant lesson. Record
  the entity, chosen URL and reason in the link audit. If no suitable owned
  guide exists, keep a conceptual mention plain or cite the precise primary
  source needed for the claim; record the content gap instead of inventing a URL.
- **Give the page a place in the SEO Tree.** Name the canonical parent topic,
  link supporting articles up to it, connect the hub to useful supporting proof,
  and link across only to related guides that help the next task. Verify those
  links in the article body; a catalog listing or sitewide footer is insufficient.
  One topic keeps one owner across our sites. Do not mass-add unrelated links or
  use a quota to turn every provider citation into an internal link.
- **Keep primary citations and execution links when they do a different job.**
  A provider's API reference can substantiate a technical claim; its download or
  sign-in page can be the required action. Label those links by their purpose
  and retain them alongside our training when useful. A provider citation does
  not replace the internal explanation of how we use the tool.
- **Verify every destination before publishing.** The name, page title and live content
  must identify the intended entity. SEO value is a by-product of a truthful,
  reader-helpful relationship; it is never a reason to guess a domain.

This extends `no-unnamed-link-text`: that rule makes the anchor truthful; this rule makes
the destination useful. When a bare entity name and a training page would conflict, the
destination-naming anchor above is the reconciliation. No generic fleet regex can identify
people, ownership or the right internal training page, so enforce this through the
entity-linking preflight and a live link audit.
<!-- shared-rule:named-entities-link-to-the-most-helpful-canonical-destination:end -->

<!-- shared-rule:visuals-above-the-fold:start -->
## Visual and interactive content sits above the fold

- **The visual is the hook, not the reward.** A chart, diagram, photograph,
  calculator or interactive tool must be substantially visible in the first
  screen alongside the page title. This applies to every fleet page, including
  home, money, relationship, article, archive, resource and policy pages. Two or three sentences of
  lead-in above it is the maximum.
- **A blank or hidden block is a failed visual.** A colored shell, empty SVG,
  broken image, loading placeholder, clipped labels or content visible only after
  scrolling does not pass. The first screen must show a meaningful part of the
  picture or diagram with readable labels, not just its border or a thin strip.
  Give the figure an honest caption or accessible description of what it teaches.
- **If the page has an interactive tool, the tool leads.** The prose becomes the
  explanation of it, not the preamble to it. Reword any copy that points "below"
  into a back-reference to the tool at the top.
- **No prose run longer than about two screens** without a figure, pull quote,
  callout or list breaking it.
- **Why:** `every-article-has-pictures` only asks whether an image exists. A page
  can satisfy it and still bury the picture four screens down, where nobody
  scrolls. That is the exact failure this rule closes, and it shipped on
  dennisyu.com before anyone noticed.
- **Server-render the initial state of any interactive block.** WP Rocket and
  similar optimisers delay inline JavaScript until the visitor's first
  interaction, so a block that builds its own DOM paints as an empty shell —
  worst of all when it is now the first thing on the page. Bake the default state
  into the markup and make the script idempotent (`el.innerHTML = ''` before it
  populates) so it replaces that markup instead of appending a second copy.
- **Verify by measuring on the live URL, not the local render.** Site chrome is
  routinely 300–400px, so a layout that clears the fold locally can fail once
  published. Check at 1280x800 and 390x844 as an anonymous first visit, before
  any click, scroll or other interaction. Capture the viewport and record the
  visible content and its position, working media/labels, and overflow. Also
  confirm the initial figure survives delayed or unavailable JavaScript.
  Verify the saved source separately from the served page: source equality,
  HTTP 200 and an image tag alone do not prove a working above-fold visual.
- **Check what WordPress serves, including the CSS.** Paragraph formatting can
  insert markup into an unprotected inline style block and discard its first
  rule. Use a valid Custom HTML block (`wp:html`) and avoid blank lines inside
  inline CSS. Compare the served markup and applied browser styles after the
  save; a correct editor source does not prove the browser received valid CSS.
- **Minimum visible proof:** on both required viewports, the loaded visual must
  expose at least 220px of width and 160px of height, at least 40% of its own area,
  and 8% of the viewport area. At least 90% of sampled visible points must be
  unobscured by navigation, sticky bars or overlays. These are minimum acceptance
  limits, not a design target. Show the face, action or diagram's useful labels;
  geometric success cannot approve an irrelevant crop.
- **Measure painted content, not letterboxing.** For contain/scale-down/none
  images, use intrinsic aspect ratio, content-box dimensions and object-position
  to measure the photo pixels that are actually displayed. Empty padding and
  letterboxing cannot meet the visible-area or minimum-width requirement.
  CSS backgrounds currently require background-size:cover for an automated
  geometry pass. Contain, auto and explicit sizes stay unmeasured and fail that
  gate until their painted bounds receive a dedicated measurement/review.
- **Keep the title readable in that same first screen.** At least one natural
  H1 (or level-one accessible heading) text line must be visible at 18px or
  larger, with at least 90% of its text-line area visible and unobscured. A long
  title may wrap; the visual may sit beside, above or below it. Do not fill the
  viewport with a photo that hides the entire page title.
- **A background must actually show through.** Loading the photo URL is not
  enough. Opaque descendant panels and before/after overlays count as covers,
  including pointer-events:none. Transparent text or a light tint can coexist
  with the photo, but the useful visible crop still needs screenshot review.
- **The content earns the space.** A logo, social icon, navigation, cookie banner,
  decorative gradient, generic stock photo or unrelated portrait does not count.
  Use an authentic relevant moment, playable captioned source video with a loaded
  poster, or a specific diagram that teaches the page's point. Open the source
  and the rendered screenshot. A coappearance alone never proves endorsement.
- **Every page means every page.** The former prose/policy exemption is removed
  by Dennis's 2026-09-05 instruction. A short policy can use a concise diagram
  explaining its actual process. Do not invent a person or pad a page with stock.
- **Keep media invited and silent during QA.** First paint must not autoplay.
  YouTube uses youtube-nocookie.com, rel=0, cc_load_policy=1 and a page-language
  cc_lang_pref. A click-to-play poster counts only when the real relevant image
  loads and its destination/player is verified. An iframe rectangle, thumbnail
  URL or screenshot of a broken player is not playable video proof. Follow
  youtube-captions-on-by-default; never invent missing caption tracks. During
  testing mute and set volume zero before any playback; use silent metadata and
  posters if playback cannot be safely controlled.
- **Use the browser gate in every builder and publisher.** After generating the
  actual source, run scripts/rendered_visual_check.mjs on its preview and again
  on the ordinary anonymous live URL after publication, with fresh screenshot
  receipts for both viewports and JavaScript-disabled first paint. No selector,
  geometry failure, missing image or measurement error is a pass. The checker
  reads the numeric limits from this standard's rendered_gate header. Store the
  selected visual, source/permission receipt, relevant lesson, crop/label review,
  URL, timestamp and screenshot hashes in the existing proof inventory. Review
  those actual screenshots before marking a page compliant; the script reports
  geometry only and never invents a semantic or playback verdict.
- **Reconcile hero style with this rule.** A composed full-bleed hero is welcome
  where it works. If the usable evidence is a selfie or small authentic moment,
  pair a restrained type layout with that image at an honest size above the fold,
  or use a useful diagram. The older typographic-only fallback does not authorize
  a first screen without a meaningful visual.

The HTML sweep remains an early source-order warning; it cannot measure the
fold. The rendered browser gate plus source-backed editorial review is the
publication acceptance gate. A merged standard, a regenerated skill, an installed
pack and a live-page pass are separate receipts. No whole-fleet success claim is
valid while unsampled URLs, Not Active stops or per-site holds are omitted.
<!-- shared-rule:visuals-above-the-fold:end -->

<!-- shared-rule:an-unanswered-ask-never-stops-the-work:start -->
## An unanswered ask never stops the work

- **Silence is not a blocker, it is a trigger.** When someone does not reply, the work
  continues on the rescue path you chose before you sent the ask. "Waiting on them" is
  never a status an agent reports twice.
- **Try to need them less before you try to reach them harder.** In order: do it yourself;
  route around; engineer the dependency so it cannot block again; only then ask. Most asks
  disappear at step one once you actually test them, because "I need this from them" is
  usually "I would prefer this from them."
- **Only three things justify asking a human at all** — binding authority, credentials or
  physical access nobody else holds, and a fact that exists only in their head. Preference,
  convenience, and "they would probably want to weigh in" are not gates.
- **Every ask ships with its rescue, decided before sending**: a deadline, a named fallback
  action, and you as the owner of that fallback. Put it in the message. "If I do not hear
  back by Friday I will assume X and proceed" turns silence into a decision, and usually
  produces the reply anyway.
- **Shrink the ask until it can be answered in ten seconds.** One question, one message, a
  yes or no where possible, plus what you already tried. A question that makes someone
  reconstruct context is a question that does not get answered.
- **When the deadline passes, execute the rescue quietly.** Do not re-send the same ask.
  Do not hand the chase to whoever is busiest. Log the miss for the periodic reliability
  record and move on: a pattern is a management conversation, held later with evidence in
  hand, not an interruption now.
- **The second time the same dependency blocks, stop treating it as a people problem.**
  Build the thing that makes their non-response harmless — a watchdog, a fallback route, a
  second credential, a cached copy. Building it once costs less than chasing it forever.
- This does not loosen `agents-draft-humans-send`. Rescue means doing the *work* yourself,
  never dispatching messages, publishing, spending or deleting on someone's behalf because
  they went quiet. Where the rescue would cross that line, stage it and say so.
- Rescue toward the function, not the person — see `assign-work-to-a-function`. A rescue
  aimed at an individual who is away is not a rescue.
- **A parked ask carries a date or it is not parked, it is dropped.** Any status row that
  says "waiting on", "blocked on" or "pending <person>" must also say when someone
  comes back to it. In the agent runtime this is failure mode `F10 Silence as a status`
  and `tools/lint_unanswered_ask.py` fails the build on a row without a date. The first
  run of that linter found two real ones: one five days old, one thirteen days old and
  not actually blocked on anybody.
- Canonical public statement, indexable and pulled at runtime by every scheduled agent:
  https://dennisyu.com/unanswered-ask/ — linked from https://dennisyu.com/agent-disclosure/
  and from the new-agent bootstrap box. Marker `UNANSWERED-ASK-RESCUE-2026-09-04`.
<!-- shared-rule:an-unanswered-ask-never-stops-the-work:end -->

<!-- shared-rule:every-article-and-project-starts-with-specific-gct:start -->
## Every opening makes its reader, value and purpose clear

- **Write the specific Goals, Content, Targeting before work begins.** Goals name
  the change the reader or project needs; Content names the source-backed lesson,
  proof or deliverable that will produce that change; Targeting names the people
  and situation it serves. “Publish an article” or “use AI” is an activity, not
  the desired outcome. Use the same brief for the article and the project behind it.
- **Apply the same opening standard to every format.** Documents, reports, PDFs,
  presentations, articles, homepages, landing pages, service pages, relationship
  pages and task guides must earn attention at the beginning. Improve their
  maintained owner in place. A report leads with the decision its evidence
  enables; a guide leads with the task the reader can accomplish; a buying page
  leads with the relevant customer need and the offer's supported value. Do not
  paste a sales pitch or "for entrepreneurs" onto a page whose reader needs
  something else.
- **Put the reader's situation, why it matters and the useful outcome in the
  first 2–3 sentences.** The first line offers a specific reason to continue:
  a recognizable problem, a consequential finding or a true moment with a clear
  lesson. Explain what this page or document helps the reader do and how the
  offered method, evidence or tool helps. The reader may be named directly or
  made unmistakable through their situation. They should not have to scroll
  through history, credentials, an abstract definition or a system description
  to find the point. Write the opening at US fifth-grade reading level or below.
  Use familiar words and short sentences; explain unavoidable terms on first use.
  Put commands, architecture details and specialist terms after this orientation.
  Readers should not have to know the acronym GCT to understand the page.
- **Make the value concrete without inflating the promise.** On an entrepreneur's
  Money Tree page, explain how existing customer stories, interviews and useful
  articles connect to what customers can buy. That gives a prospect relevant
  proof and a clear next step. On another page, name that reader's actual useful
  outcome: choose a service, check a result, prepare for a workshop or complete
  a task. "Build authority," "unlock potential" and "follow the stories" alone
  do not explain the benefit. Do not claim increased conversions, revenue,
  speed or certainty unless the evidence supports that exact claim.
- **Use confident, source-backed language.** State the supported value directly.
  Keep authentic moments and compact receipts; do not add doubt, reassurance,
  hype, false urgency, invented statistics or status borrowing. A necessary
  disclosure stays next to its claim. A true story may lead, but its relevance
  and takeaway must become clear in that same short opening.
- **Explain jargon on its first meaningful mention and link the owned explainer.**
  Give the familiar phrase before the specialist label: “the result we want, the
  material we will use, and who it serves — our
  [Goals, Content, Targeting (GCT) brief](https://blitzmetrics.com/gct-business-strategy/).”
  Apply this to other frameworks, acronyms and unfamiliar task terms. Verify the owned
  destination teaches the term; use honest descriptive anchors. If no suitable owned
  explanation exists, define the term in place and record the gap instead of inventing
  a link. Keep this explanation short so it does not bury the lead visual.
- **Make the opening specific enough to judge.** For a shared-memory guide:
  “Use this guide if you work with more than one AI assistant and keep repeating
  the same facts. It shows how to give them one set of notes, so each assistant
  can pick up where the last one stopped.” The project brief also names the
  source files, checks and expected handoff; never invent facts to fill the brief.
- **Review meaning before accepting a score.** Save the exact opening and its
  artifact revision in the existing editorial or proof inventory. Have a
  reviewer identify the reader/situation, the reason to care, the useful outcome
  and the mechanism or evidence supporting it, quoting the actual words. Then
  check that the promised outcome is delivered by the body and next step.
  Record PASS, FAIL or UNKNOWN with a concrete reason and the readability
  diagnostic. A short paragraph, keyword, grade score, audience label or
  conversion word alone never passes this gate. If the opening could be moved
  unchanged to an unrelated subject, rewrite it. Unchecked meaning or readability
  stays UNKNOWN; the check belongs in the internal receipt, not public copy.
- **Keep the useful visual with the short opening.** Follow
  `visuals-above-the-fold`: the topic-specific picture or diagram may come first,
  or immediately after the short opening, whichever makes the first screen
  useful. A long GCT card, checklist, changelog or navigation block must not bury
  that visual.

### Money Tree opening example

Before: "A useful conversation becomes a story. The story points to something
you can learn, build or do with us. Here is how those connections look on my site."

After: "Your best customer stories should help your next customer decide to buy.
A Money Tree connects those stories, interviews and useful articles to the
services you sell, so people can see your work and take the next step. Explore
mine to see how the same approach can work on your site."

This is a writing example, not a measured conversion claim. Adapt it to the real
reader, proof and contents of the artifact; do not duplicate it across the fleet.

The maintained public writing standard is
https://localservicespotlight.com/article-guidelines/; the definitive-hub method
is https://blitzmetrics.com/definitive-article-guide/. The older
`/blog-posting-guidelines/` page is an archive and SEO leaf. Improve these owners
in place rather than publishing a competing guideline. No regex can honestly
certify a specific GCT or human comprehension; enforce this in editorial review.
<!-- shared-rule:every-article-and-project-starts-with-specific-gct:end -->

<!-- shared-rule:every-task-execution-writes-a-meta-article:start -->
## Every task execution writes a meta article

- **Write the run record every time the task is executed.** Follow the
  [meta-article guidelines](https://blitzmetrics.com/meta-article-prompt/) and the
  [recipe and run-record relationship](https://localservicespotlight.com/meta-articles/).
  A task's definitive article is the reusable recipe. Its meta article records one
  actual execution. Writing the meta article is required even when publication is
  pending or the run ends failed, partial or blocked after work began. A plan that
  never executes is a plan, not an execution example.
- **Make the record checkable.** Include a stable execution ID; canonical task URL and
  recipe/skill revision; trigger and starting state; date and operator; inputs and
  prerequisite outputs; steps taken and deviations; output and pass/fail results;
  evidence links; lessons; and the next action, artifact and receiving function. Record
  steps, time, token use and cost when measured; preserve UNKNOWN when unavailable.
  Protect credentials and private data, and retain the full record in an authorized
  location when a public-safe version cannot include them.
- **Writing and publishing are different states.** Write and save the meta draft under
  the task's existing authority. Publish or send it only through the applicable
  authorized rail. Preserve draft, reviewed, published and verified states accurately.
  An internal agent note, task comment or publication receipt is useful evidence but
  does not replace the structured meta article. Required writing grants no new send,
  publish, merge, spend or access authority.
- **Close the learning loop with evidence.** Compare this run and prior meta articles
  with the canonical recipe. Propose the smallest supported correction for a missing
  input, ambiguous step, failed check or handoff. Record the decision and version any
  accepted recipe/skill change, using the existing review and publishing authority.
  Link the change back to the run evidence. No improvement is needed when the evidence
  reveals no defect; do not rewrite a working recipe just to show activity.
- **Count distinct executions once per canonical task.** Use the execution ID to
  deduplicate drafts, edits, derivatives and retries within a run. A separately scoped
  rerun has a new ID and its own evidence. Keep failed/partial and unpublished records
  in internal history with their status. Verified execution frequency and dated public
  example volume are separate metrics. Existing reviewed public-article counts remain
  valid as historical article volume even when those articles lack execution IDs; they
  do not establish task frequency. Preserve the evidence and audit date. Execution
  uncertainty remains UNKNOWN or PARTIAL; do not infer a run from a mere link.
- **Do not create a documentation loop with no end.** Writing and revising the meta
  article is part of the original execution. It does not recursively require another
  meta article unless a separate documentation task is explicitly scoped and executed.

No text pattern can prove that a task ran, an artifact passed, or two pages describe
separate executions. Enforce this through the run record, evidence manifest and review.
<!-- shared-rule:every-task-execution-writes-a-meta-article:end -->

<!-- shared-rule:show-the-moment-not-the-resume:start -->
## Show the moment, not the resume

- **Public proof should let the reader witness a true moment, not watch the subject
  recite a resume.** Build each proof story from five parts: the scene, why it mattered,
  the person and their relevant role, one true human beat, and a compact receipt. The
  human beat may be funny, awkward, generous, surprising, or humble, but it must come
  from the source. Never manufacture personality or imitate another storyteller.
- **Use the narrowest relationship word the evidence supports.** `Interviewed`, `hosted`,
  `shared a meal`, `spoke at the same event`, and `worked on X` describe observable
  moments. Reserve `friend`, `partner`, `client`, `mentor`, and similar durable terms for
  a source or owner attestation that supports them. A verified photograph proves that
  people were together for that moment; it does not by itself prove praise, friendship,
  or endorsement.
- **Praise must be exact and named.** A testimonial or endorsement needs attributable
  positive language from an identified person or organization and a reviewable source.
  Anonymous praise, initials-only praise, and domain-only claims stay `HOLD`; do not
  turn missing identity into warmer copy.
- **Keep the receipt compact.** A caption or source line can name the artifact, date,
  format, and link. Explain evidence categories once in a short page-level key instead
  of attaching a disclaimer to every photograph and sentence. Keep a local qualifier
  only when omitting it would materially mislead. The full classification, permission,
  and audit trail belong in the canonical inventory, not in the reader's path.
- **Run the trophy-name test.** Remove the recognizable name from the paragraph. If no
  useful scene, lesson, decision, or outcome remains, the name is functioning as a trophy.
  Reframe around what happened and what the reader can take from it, or cut the item.
- **Run the courtroom test.** If the page repeatedly argues what each item does *not*
  prove, it sounds as though the author doubts the evidence. Keep the underlying gate
  strict, then state the supported fact once in ordinary language. Confidence comes from
  precise evidence, not from louder claims or repeated self-defense.
- **Reconciliation with `order-proof-by-authority`:** Who / Where / What scores rank
  evidence that already passed its truth and permission gates; they do not license status
  borrowing. Lead with the strongest *useful* moment for this reader. A high Who score
  cannot rescue a weak What score, and video outranks text because it preserves more of a
  meaningful moment, not because a famous face transfers authority by proximity.

No honest fleet regex can determine whether a paragraph contains a lived scene, whether
the humor is true, whether a relationship word outruns its evidence, or whether a name is
doing all the persuasive work. Phrase bans would also flag quotations, legal disclosures,
and accurate criticism. Enforce this standard through the source-backed editorial
preflight, the canonical proof inventory, and a rendered-page review using the two tests
above.


### Money pages and the site's Money Tree

- Each eligible site keeps a current public-safe Money Tree: the site's actual
  home/domain is the trunk, its buying/service destinations are branches, and
  relevant published stories, videos and other supporting pages are leaves.
  Link each real node to its canonical page. Do not manufacture branch traffic,
  customers or results. Use the existing agent-runtime money-tree renderer,
  source truth tables and cadence; do not create a competing client roster or clock.
- A small opening diagram is a navigation overview, not the whole inventory.
  Show the real breadth of the scoped tree through meaningful groups, readable
  branches and inspectable leaves. State the selection and coverage beside an
  overview, with a clear route to the complete map and text outline. Do not
  flatten a large tree into a handful of cards that imply those are all its
  offers, topics or proof. Do not add decorative leaves or fictitious nodes to
  make it look abundant. The full map and useful initial state remain available
  without interaction or JavaScript.
- Name exactly what each count measures and date it. "Published posts linking
  to this offer" is different from total relevant stories, customers, examples
  or all pages on the site. Deduplicate body links under the existing method;
  show a narrow count as a narrow count. Never disguise sparse link coverage by
  relabeling it as total proof, or expand the count without source evidence.
- Put that diagram where a visitor can find it, and use its relevant branch or
  useful full tree on the money page when it explains the offer. Every money
  page still has meaningful above-fold proof; the full tree need not replace a
  better authentic opening moment. Link the supporting leaf to the relevant
  buying branch and to the practical how-to where it helps the reader.
- Spread useful proof through the decision: one relevant visual at the opening,
  attributable example or demonstration beside each material outcome claim, and
  another relevant proof moment near the primary buying action. A purchase page
  cannot pass with one generic testimonial block at the bottom. If the evidence
  does not support a claim, narrow or remove the claim; never invent a result or
  count duplicated cards as additional proof.
- Public trees show only public structure and content evidence. Sessions, leads,
  booked jobs, conversion rates, revenue, client finances and private priorities
  stay in the authenticated client version, including in alt text, hidden HTML,
  JSON-LD, images and metadata. NOT_CONNECTED is not zero. Follow the existing
  agent-runtime money-tree public/private boundary and canonical Money Tree
  method at https://blitzmetrics.com/money-tree/.
- A relationship refresh adds a newly verified moment, useful lesson or relevant
  next step. It does not simply rotate names or strengthen the relationship word.
  Review priority connections and money pages weekly and all other eligible
  sites/pages monthly through existing owners and reconciled schedules. Record
  the actual next due date; unknown ownership or publication rails remain HOLD.
  Keep audit categories and review notes internal, with one compact public source
  line when useful. Never make the reader defend the author's legitimacy.
<!-- shared-rule:show-the-moment-not-the-resume:end -->

<!-- shared-rule:icon-only-social-controls-stay-tappable:start -->
## Icon-only social controls stay tappable and separate

- **Make every icon-only social link a real control, not a glyph-sized target.** Its
  computed hit area is at least 44 by 44 CSS pixels, and adjacent hit areas have a
  deliberate gap of at least 8 CSS pixels. The visible icon may be smaller inside that
  area. Do not use transparent overlap or negative margins to simulate spacing.
- **Give every control an accessible name.** Prefer a concise name on the link such as
  `aria-label="LinkedIn"`; visible or visually hidden text and a valid
  `aria-labelledby` relationship also work. Inspect the accessibility tree and confirm
  the computed name. A platform-shaped glyph, tooltip on hover, URL, or empty label does
  not name the control.
- **Fix the owning template first.** Trace the rendered control to the root header,
  footer, reusable block, or component and correct it there. Find and verify every
  responsive copy; builders often keep separate desktop, tablet, and mobile widgets,
  and a page-level override can leave another copy broken. Rebuild generated CSS and
  refresh static or caching layers through their supported path, then compare stored
  source with what an anonymous visitor receives.
- **Measure the rendered page at 390px wide and at desktop width.** Record each control's
  computed width, height, accessible name, and gap to its neighbour. Confirm controls do
  not overlap or clip and `document.documentElement.scrollWidth` is no greater than the
  viewport width. Check keyboard focus on desktop and touch layout on mobile. A source
  value, editor preview, or successful save is not rendered QA.
- **Do not copy a selector or patch blindly across sites.** Before a fleet change, match
  the exact site status and publishing authority, CMS/theme, builder or header renderer,
  owning template/component identifier, and the defective rendered signature. Back up
  each target, record before/after hashes and a rollback action, publish through that
  site's supported rail, and read it back. A mismatched fingerprint, unknown status,
  explicit hold, abnormal document, or missing rollback stays `HOLD`; it is not evidence
  that the rest of the fleet is fixed.

The fleet check deliberately catches only the unambiguous empty-`<i>` form of an unnamed
icon link. Static HTML cannot honestly prove computed hit-area size, separation,
responsive visibility, overflow, or every valid accessible-name relationship. Those
remain browser measurements on the rendered page; broad class-name or inline-style
regexes would create fragile false positives across different themes and builders.
<!-- shared-rule:icon-only-social-controls-stay-tappable:end -->

<!-- shared-rule:skills-packs-plugins-and-jobs-have-distinct-states:start -->
## Skills, packs, plugins, workers and jobs have distinct states

Use these terms to choose the setup your business needs. Start with one guide and one job. Check the result before you add more tools.

- A **skill** is a written recipe for a kind of task. A **skill pack** is a selected group of skills. A **plugin** is a package for a particular app; it may contain skills, tool connections or other components. Name only what the reviewed package contains. Use the [owned explainer](https://localservicespotlight.com/plugin/) and [pack library](https://localservicespotlight.com/skill-packs/).
- An **agent** is the AI worker doing an assigned task with approved tools and access. A **job** is an assigned run with inputs, checks and a result. A **scheduled job** adds a saved time or supported event; installing instructions does not create a worker or schedule. Link the [agent guide](https://blitzmetrics.com/build-agents/) and [job guide](https://blitzmetrics.com/persistent-agents/).
- **Access** is permission to reach a source or tool in the named account and environment. Record required access, granted scope, observed connection and remaining human action separately. A downloaded ZIP, installed plugin or ready document proves none of them. Never infer approval from a package, task status or connected account.
- **Document-ready** means the recipe has its required content and review. Task Library `complete` is a contributor-supplied document-status claim. It does not by itself prove that the guide meets the required content and review standard, or that a client task ran. Record independent document review, installed-skill activation, source access, scheduled firing, business success and semantic certification separately. Record actual executions separately with their IDs, outputs and checks.
- Make the ZIP a useful first start: include a short start file, a one-task draft prompt, a manifest and dated source information. Say whether it is a guide archive or a platform-installable package. A downloaded snapshot does not update itself. Do not tell readers to delete old copies without considering their rollback and active-job dependencies.
- Use the current maintained marketplace URL and exact package name. Derive any counts from its manifest, with a revision/date; do not equate the broad Task Library with the smaller curated marketplace. Mark older names and installation receipts as historical, and verify actual installed copies before claiming parity.
- Check external platform claims against current official docs for that product, surface, plan and environment. Keep package format, installation, activation, connectors, local-file access and scheduling separate. No blanket promise that every job works on a free plan, on a phone, or while the laptop sleeps. Confirm the actual first run, output and failure handling before calling a schedule observed.
<!-- shared-rule:skills-packs-plugins-and-jobs-have-distinct-states:end -->
