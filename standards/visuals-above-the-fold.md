---
{
  "title": "Visual and interactive content sits above the fold",
  "severity": "warn",
  "captured": "2026-09-04",
  "captured_from": "Dennis Yu, Cowork session, 2026-09-04: 'I think it's a general problem we have with articles written by AI where there's a ton of text, and the photos, the visual stuff, and the interactive bits are below the fold, so they don't get seen. Can we make this a global rule?' Traced to dennisyu.com/the-unwritable-part/, where the calculator sat at 20% scroll depth behind four screens of prose. Extended by Dennis Yu, Codex GPT-6 continuation, 2026-09-05: 'Every page should have a diagram or a picture or an embedded video above the fold' across the entire fleet.",
  "source": "https://dennisyu.com/the-unwritable-part/",
  "applies_to": [
    "published-html",
    "agent-behaviour"
  ],
  "checks": [
    {
      "id": "visual-before-the-second-section",
      "kind": "require_regex",
      "pattern": "</h1>(?:(?!<(?:img|figure|svg|picture|video|canvas|iframe)[\\s>/]|<input[^>]{0,200}type=[\"\\']?range|<h2[\\s>])[\\s\\S])*(?:<h2[\\s>](?:(?!<(?:img|figure|svg|picture|video|canvas|iframe)[\\s>/]|<input[^>]{0,200}type=[\"\\']?range|<h2[\\s>])[\\s\\S])*)?(?:<(?:img|figure|svg|picture|video|canvas|iframe)[\\s>/]|<input[^>]{0,200}type=[\"\\']?range)",
      "message": "source-order warning: inspect the first screen; visual markup does not prove a relevant loaded picture, diagram or video clears the fold",
      "examples": {
        "violating": [
          "<article><h1>Deck resurfacing</h1><p>Prose.</p><h2>One</h2><p>More prose.</p><h2>Two</h2><p>Still prose.</p><figure><img src=\"deck.jpg\" alt=\"Deck\"></figure></article>",
          "<article><h1>What the work is worth</h1><p>Prose.</p><h2>The problem</h2><p>Prose.</p><h2>The guardrails</h2><p>Prose.</p><h2>What I got wrong</h2><p>Prose.</p><input id=\"share\" type=\"range\"></article>"
        ],
        "clean": [
          "<article><h1>Deck resurfacing</h1><p>One short lead-in.</p><figure><img src=\"deck.jpg\" alt=\"Resurfaced deck\"></figure><h2>One</h2><p>Then the prose.</p></article>",
          "<article><h1>What the work is worth</h1><p>Set your numbers.</p><input id=\"share\" type=\"range\" min=\"5\" max=\"85\"><h2>Where they come from</h2><p>Prose.</p></article>",
          "<article><h1>Deck resurfacing</h1><p>Lead-in.</p><h2>One</h2><p>Prose.</p><svg viewBox=\"0 0 10 10\"></svg><h2>Two</h2></article>"
        ]
      }
    }
  ],
  "rendered_gate": {
    "version": 1,
    "viewports": [
      {
        "width": 390,
        "height": 844
      },
      {
        "width": 1280,
        "height": 800
      }
    ],
    "min_visible_height": 160,
    "min_visible_width": 220,
    "min_visible_fraction": 0.4,
    "min_viewport_fraction": 0.08,
    "min_unoccluded_fraction": 0.9
  }
}
---


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
