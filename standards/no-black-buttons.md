---
{
  "title": "Never ship a black button",
  "severity": "error",
  "captured": "2026-05-17",
  "captured_from": "BlitzMetrics definitive article published 2026-05-17; the most repeated finding across hundreds of BlitzMetrics website audits. Entered standards/ 2026-08-16 after an agent shipped a black CTA on georgepaladichuk.com while the rule existed only as an article.",
  "source": "https://blitzmetrics.com/why-we-dont-use-black-buttons/",
  "applies_to": ["published-html", "design-review"],
  "checks": [
    {
      "id": "black-fill-on-cta-tag",
      "kind": "forbid_regex",
      "pattern": "<(?:a|button)\\b[^>]*style=\"[^\"]*background(?:-color)?\\s*:\\s*#(?:000000|000)(?![0-9a-f])",
      "exempt_if_near": "keep-black",
      "message": "black inline fill on a link or button",
      "examples": {
        "violating": [
          "<a class=\"cta\" style=\"background:#000;color:#fff\">Book a call</a>",
          "<button style=\"background-color: #000000\">Get started</button>"
        ],
        "clean": [
          "<a class=\"cta\" style=\"background:#ffc833;color:#14161a\">Book a call</a>",
          "<div class=\"overlay\" style=\"background:#000;opacity:.4\"></div>",
          "<a class=\"logo bm-keep-black\" style=\"background:#000\">mark</a>"
        ]
      }
    },
    {
      "id": "black-button-utility-class",
      "kind": "forbid_regex",
      "pattern": "class=\"[^\"]*(?:btn-dark|btn-black|button-black|bg-black|has-black-background-color)(?![-\\w])",
      "exempt_if_near": "keep-black",
      "message": "black-button utility or preset class applied to an element",
      "examples": {
        "violating": [
          "<a class=\"btn btn-dark\" href=\"/contact\">Call now</a>",
          "<div class=\"wp-block-button__link has-black-background-color\">Start</div>"
        ],
        "clean": [
          "<a class=\"btn btn-primary\" href=\"/contact\">Call now</a>",
          "<section class=\"bg-black-friday-promo\">Sale</section>"
        ]
      }
    },
    {
      "id": "black-button-in-stylesheet",
      "kind": "forbid_regex",
      "pattern": "\\.(?:btn|button|wp-block-button__link)[\\w-]*[^{}]{0,200}\\{[^{}]{0,400}background(?:-color)?\\s*:\\s*#(?:000000|000)(?![0-9a-f])",
      "exempt_if_near": "keep-black",
      "message": "stylesheet rule paints a button black",
      "examples": {
        "violating": [
          ".btn-primary{padding:12px 20px;background:#000;color:#fff}",
          ".wp-block-button__link{background-color:#000000;border-radius:4px}"
        ],
        "clean": [
          ".btn-primary{padding:12px 20px;background:#ffc833;color:#14161a}",
          ".has-black-background-color{background-color:#000000 !important}",
          ".button.bm-keep-black,.wp-block-button__link.bm-keep-black{background-color:#000!important}"
        ]
      }
    }
  ]
}
---

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
