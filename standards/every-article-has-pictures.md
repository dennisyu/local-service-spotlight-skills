---
{
  "title": "Every article has pictures",
  "severity": "error",
  "captured": "2026-08-16",
  "captured_from": "Dennis Yu, Mats and Leo, 2026-07-19 01:22:22: 'We have article guidelines. We always use picture. Every every article always has pictures.' Reinforced by Dennis Yu, Cowork session, 2026-08-15, on a client About page: it 'doesn't have pictures, videos, diagrams, colors, bold points, and things like that to be visually interesting.' Extended by Dennis Yu's Codex request on 2026-10-23 for recognizable service/network icons and helpful diagrams in the agent article cluster.",
  "applies_to": [
    "published-html"
  ],
  "checks": [
    {
      "id": "article-has-an-image",
      "kind": "require_regex",
      "pattern": "<(?:img|figure|svg|picture)\\b",
      "message": "page contains no image, figure or diagram",
      "examples": {
        "violating": [
          "<article><h1>Deck resurfacing</h1><p>Long text with no image at all.</p></article>"
        ],
        "clean": [
          "<article><figure><img src=\"deck.jpg\" alt=\"Resurfaced deck\"></figure><p>…</p></article>"
        ]
      }
    }
  ],
  "target_tags": [
    "article"
  ]
}
---

## Every article has pictures

- **No article ships as a wall of text.** Every published piece carries images — real
  photographs, screenshots, or diagrams that carry meaning, not decorative stock.
- **A diagram beats a paragraph** wherever the point is a structure, a sequence or a
  comparison.
- **Use recognizable service or network icons when they help readers identify a
  named tool.** Pair the approved mark with its visible name. Record the asset
  source and permitted use; do not invent a brand mark or imply endorsement.
- **Give each explanatory diagram one clear job.** Use it to show a sequence,
  relationship or comparison supported by the text and sources. Label what each
  arrow means and distinguish an illustrated example from an observed result.
  For agent diagrams, keep apps, models, execution locations and access routes
  distinct; a shared logo or line does not establish shared permissions.
- Icons support recognition; they do not replace the meaningful visual required
  by `every-public-page-has-real-imagery` and `visuals-above-the-fold`. Keep labels
  readable on a phone and provide an accessible text equivalent. Decorative
  duplicate icons should not repeat a label to screen readers; icon-only links
  follow `icon-only-social-controls-stay-tappable`.
- Caption them. An uncaptioned image is decoration; a captioned one is evidence.
- Images also carry the provenance required by `process-real-content-never-generate` —
  a photograph of the work actually done proves more than any sentence about it.
