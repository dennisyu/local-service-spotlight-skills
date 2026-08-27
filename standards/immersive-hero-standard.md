---
{
  "title": "Personal-brand heroes are immersive, not boxed",
  "severity": "warn",
  "captured": "2026-08-16",
  "captured_from": "Dennis Yu, Cowork session, 2026-08-15: 'with all personal brand sites, I want to have a hero image or set of images/videos that are powerful, enveloping, immersive and high class for public figures — not the cheesy template we have now with a small box with a picture. Help us propagate this across all our personal brand sites.' Entered standards/ 2026-08-16; before that it existed only as a kit handed over in chat, which reached no site but the one being worked on.",
  "applies_to": ["published-html", "design-review"],
  "target_tags": ["personal-brand"],
  "checks": [
    {
      "id": "hero-fills-the-viewport",
      "kind": "require_regex",
      "pattern": "(?:min-)?height\\s*:\\s*\\d{2,3}\\s*(?:s|d|l)?vh",
      "message": "no viewport-height section found — the hero is probably a boxed template, not a full-bleed one. Confirm by eye; this check is a proxy, not proof.",
      "examples": {
        "violating": [
          "<section class=\"hero\"><div class=\"box\" style=\"width:320px\"><img src=\"me.jpg\"></div></section>"
        ],
        "clean": [
          "<section class=\"gpx\" style=\"height:94svh;min-height:600px\">…</section>",
          "<div class=\"hero\" style=\"min-height: 80vh\">…</div>"
        ]
      }
    }
  ]
}
---

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
