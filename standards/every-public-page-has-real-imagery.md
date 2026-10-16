---
{
  "title": "Every public page shows real people or real work",
  "severity": "error",
  "captured": "2026-08-21",
  "captured_from": "Dennis Yu, Codex task, 2026-08-21: 'On any page, not just the thank you page, we want to have a real image, not just a bunch of texts. Remember that is a rule across all of our websites because we want to be personal, personable, not just have text.' Reconciled with Dennis Yu's 2026-09-05 GPT-6 continuation allowing a diagram, picture or embedded video on every page.",
  "applies_to": [
    "published-html",
    "design-review"
  ],
  "checks": [
    {
      "id": "verified-real-image-present",
      "kind": "require_regex",
      "pattern": "(?:<img\\b(?=[^>]*\\sdata-lss-real-image\\s*=\\s*(?:\"verified\"|'verified'))(?=[^>]*\\salt\\s*=\\s*(?:\"[^\"]*[^\\s\"][^\"]*\"|'[^']*[^\\s'][^']*'))(?=[^>]*\\ssrc\\s*=\\s*(?:\"(?!\\s*data:)[^\"]*[^\\s\"][^\"]*\"|'(?!\\s*data:)[^']*[^\\s'][^']*'))[^>]*>|<(?:svg|video|iframe|section|div)\\b(?=[^>]*\\sdata-lss-visual-proof\\s*=\\s*(?:\"verified\"|'verified'))(?=[^>]*\\s(?:aria-label|title)\\s*=\\s*(?:\"[^\"]*[^\\s\"][^\"]*\"|'[^']*[^\\s'][^']*'))[^>]*>)",
      "message": "page has no declared source-verified image or labeled visual proof marker; declaration still needs rendered/source review",
      "examples": {
        "violating": [
          "<main><img src=\"logo.svg\" alt=\"Target Painting logo\"><p>Text-only content page.</p></main>",
          "<main><img src=\"project.webp\" alt=\"Finished exterior\"><p>The photo has no verified provenance marker.</p></main>",
          "<main><img alt=\"Photo\" data-lss-real-image=\"verified\"><p>The declaration has no source.</p></main>",
          "<main><img src=\"project.webp\" alt=\"   \" data-lss-real-image=\"verified\"><p>The alt text is blank.</p></main>",
          "<main><img src=\"data:image/gif;base64,R0lGODlhAQABAAAAACw=\" alt=\"Tracking pixel\" data-lss-real-image=\"verified\"></main>",
          "<main><img data-src=\"project.webp\" alt=\"Finished project\" data-lss-real-image=\"verified\"></main>",
          "<main><img src=\"project.webp\" data-alt=\"Finished project\" data-lss-real-image=\"verified\"></main>",
          "<main><img src=\"project.webp\" alt=\"Finished project\" foo-data-lss-real-image=\"verified\"></main>",
          "<svg data-lss-visual-proof=\"verified\" aria-label=\" \"></svg>",
          "<div data-lss-visual-proof=\"unknown\" aria-label=\"Unreviewed diagram\"></div>"
        ],
        "clean": [
          "<main><figure><img src=\"target-project.webp\" alt=\"Target Painting exterior project\" data-lss-real-image=\"verified\"><figcaption>A completed Target Painting project.</figcaption></figure></main>",
          "<svg data-lss-visual-proof=\"verified\" aria-label=\"How the actual booking process works\"><rect width=\"200\" height=\"100\"/><text>Book a visit</text></svg>",
          "<section data-lss-visual-proof=\"verified\" aria-label=\"Dennis speaking at the source event\" style=\"background-image:url(speaking.jpg)\"></section>"
        ]
      }
    }
  ]
}
---


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
