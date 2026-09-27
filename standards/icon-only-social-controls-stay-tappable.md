---
{
  "title": "Icon-only social controls stay tappable and separate",
  "severity": "error",
  "captured": "2026-09-05",
  "captured_from": "Dennis Yu, Codex request, 2026-09-05: mobile social icons were jammed together; fix the owning template, verify the fleet carefully, and prevent recurrence in article and design guidance.",
  "applies_to": [
    "published-html",
    "design-review"
  ],
  "checks": [
    {
      "id": "obvious-unnamed-empty-i-link",
      "kind": "forbid_regex",
      "pattern": "<a\\b(?![^>]*\\s(?:aria-label|aria-labelledby|title)\\s*=\\s*[\"'][^\"']+[\"'])[^>]*>\\s*<i\\b(?![^>]*\\s(?:aria-label|aria-labelledby|title)\\s*=\\s*[\"'][^\"']+[\"'])[^>]*>\\s*</i>\\s*</a>",
      "message": "an icon-only link made from an empty <i> has no accessible name; label the link and verify its computed accessible name",
      "examples": {
        "violating": [
          "<a class=\"social-link\" href=\"https://example.com/profile\"><i class=\"fab fa-linkedin\"></i></a>",
          "<a href=\"/social\" aria-label=\"\"><i class=\"icon-social\"></i></a>"
        ],
        "clean": [
          "<a class=\"social-link\" href=\"https://example.com/profile\" aria-label=\"LinkedIn\"><i aria-hidden=\"true\" class=\"fab fa-linkedin\"></i></a>",
          "<a href=\"/social\" title=\"Follow Dennis on Facebook\"><i class=\"icon-social\"></i></a>",
          "<a href=\"/social\"><i aria-label=\"Instagram\" class=\"icon-social\"></i></a>",
          "<a href=\"/social\"><svg role=\"img\" aria-label=\"YouTube\"><path d=\"M0 0\"></path></svg></a>",
          "<a href=\"/social\"><i aria-hidden=\"true\"></i><span class=\"sr-only\">X</span></a>"
        ]
      }
    }
  ]
}
---

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
