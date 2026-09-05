---
{
  "title": "Visual and interactive content sits above the fold",
  "severity": "error",
  "captured": "2026-09-04",
  "captured_from": "Dennis Yu, Cowork session, 2026-09-04: 'I think it's a general problem we have with articles written by AI where there's a ton of text, and the photos, the visual stuff, and the interactive bits are below the fold, so they don't get seen. Can we make this a global rule?' Traced to dennisyu.com/the-unwritable-part/, where the calculator sat at 20% scroll depth behind four screens of prose.",
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
      "message": "no visual-like markup appears before the second section — inspect the rendered first screen; this source-order check does not measure the fold",
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
  "target_tags": [
    "article"
  ]
}
---

## Visual and interactive content sits above the fold

- **The visual is the hook, not the reward.** A chart, diagram, photograph,
  calculator or interactive tool must be at least partly visible in the first
  screen, *after* the site's own header and title. Two or three sentences of
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
  published. Check at 1440x860 and 390x844 as an anonymous first visit, before
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
- **Exemption:** a page whose whole purpose is a single block of prose — a
  disclosure, a policy, a legal notice — is exempt. Tag it, do not silently skip
  it.

The sweep only catches the blatant case: a headline with no visual anywhere near
it. Whether the visual actually clears the fold is a judgement call, verified by
opening the published page — see `verify-by-opening-the-live-artifact`.
