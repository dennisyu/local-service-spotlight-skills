---
{
  "title": "No unnamed link text",
  "severity": "warn",
  "captured": "2026-08-16",
  "captured_from": "BlitzMetrics definitive article, 2026-05-17: 'Next on the list: no autoplay video on landing pages, no popup on page load, and no unnamed link text. Same plugin shape, different selectors.' Extended 2026-08-16 with the anchor-target rule from Dennis Yu, Mats and Leo, 2026-07-19 01:27:15: 'if we mentioned A, we should link to A. If we mention B, we should link to B.' The defect that prompted it, same call 01:25:50: 'we have two links in the beginning to prime acquisition groups. So we don't want to do that because they both have the exact same anchor text… It doesn't make any sense to do that.'",
  "source": "https://blitzmetrics.com/why-we-dont-use-black-buttons/",
  "applies_to": ["published-html", "design-review"],
  "checks": [
    {
      "id": "generic-anchor-text",
      "kind": "forbid_regex",
      "pattern": "<a\\b[^>]*>\\s*(?:click here|read more|learn more|continue reading|download|more|here|this|link)\\s*</a>",
      "message": "anchor text says nothing about its destination",
      "examples": {
        "violating": [
          "<a href=\"/about\">Read more</a>",
          "<a href=\"/contact\">Click here</a>"
        ],
        "clean": [
          "<a href=\"/about\">Read George's story</a>",
          "<a href=\"/audit\">Download the 2026 audit checklist</a>"
        ]
      }
    },
    {
      "id": "image-only-link-without-name",
      "kind": "forbid_regex",
      "pattern": "<a\\b(?![^>]*aria-label)[^>]*>\\s*<img\\b(?![^>]*alt\\s*=\\s*\"[^\"]+\")[^>]*>\\s*</a>",
      "message": "image-only link has no accessible name (no alt text, no aria-label)",
      "examples": {
        "violating": [
          "<a href=\"/\"><img src=\"logo.png\"></a>",
          "<a href=\"https://x.com/gp\"><img src=\"x.svg\" alt=\"\"></a>"
        ],
        "clean": [
          "<a href=\"/\"><img src=\"logo.png\" alt=\"George Paladichuk home\"></a>",
          "<a href=\"/\" aria-label=\"Home\"><img src=\"logo.png\"></a>"
        ]
      }
    }
  ]
}
---

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
