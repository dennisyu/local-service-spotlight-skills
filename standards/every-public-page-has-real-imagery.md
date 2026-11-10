---
{
  "title": "Every public page shows real people or real work",
  "severity": "warn",
  "captured": "2026-08-21",
  "captured_from": "Dennis Yu, Codex task, 2026-08-21: 'On any page, not just the thank you page, we want to have a real image, not just a bunch of texts. Remember that is a rule across all of our websites because we want to be personal, personable, not just have text.' Reconciled with Dennis Yu's 2026-09-05 GPT-6 continuation allowing a diagram, picture or embedded video on every page. Strengthened by Dennis Yu, Codex roofing launch request, 2026-11-03: every page needs a real photo; show existing roofing relationships, original pictures/videos and founders instead of unsupported AI text. Dennis Yu, Codex continuation, 2026-11-05: make website agents actually use the checks, verify enforcement across publishing workflows with Codex, and document proof in GitHub. Amended by Dennis Yu, 2026-11-10 ~22:10 +07, in Cowork: 'yes, update the rule, since we want to publish more, not hold things up. not always will we have fresh photos' -- a missing or un-reviewed photo no longer holds publication; only a new photo of a real person without a recorded source and permission basis does.",
  "applies_to": [
    "published-html",
    "design-review"
  ],
  "checks": [
    {
      "id": "verified-real-image-present",
      "kind": "require_regex",
      "pattern": "<img\\b(?=[^>]*\\sdata-lss-real-image\\s*=\\s*(?:\"verified\"|'verified'))(?=[^>]*\\salt\\s*=\\s*(?:\"[^\"]*[^\\s\"][^\"]*\"|'[^']*[^\\s'][^']*'))(?=[^>]*\\ssrc\\s*=\\s*(?:\"(?!\\s*data:)[^\"]*[^\\s\"][^\"]*\"|'(?!\\s*data:)[^']*[^\\s'][^']*'))[^>]*>",
      "message": "page has no declared source-verified real photo; diagrams/video alone do not satisfy the photo requirement; declaration still needs provenance and rendered review",
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
          "<div data-lss-visual-proof=\"unknown\" aria-label=\"Unreviewed diagram\"></div>",
          "<svg data-lss-visual-proof=\"verified\" aria-label=\"How the actual booking process works\"><rect width=\"200\" height=\"100\"/><text>Book a visit</text></svg>",
          "<section data-lss-visual-proof=\"verified\" aria-label=\"Dennis speaking at the source event\" style=\"background-image:url(speaking.jpg)\"></section>"
        ],
        "clean": [
          "<main><figure><img src=\"target-project.webp\" alt=\"Target Painting exterior project\" data-lss-real-image=\"verified\"><figcaption>A completed Target Painting project.</figcaption></figure></main>"
        ]
      }
    }
  ]
}
---


## Every public page shows real people or real work

- **Every visitor-facing content page must contain at least one meaningful real
  photograph of the actual business: its people, its work, its customers with
  permission, its product or its place.** This includes conversion and utility pages such as
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
- **For vertical spotlight, founder, About and relationship pages, show the real
  people behind the vertical.** Inspect the approved library and original
  published interviews, visits, events and client work before drafting. Show
  relevant photographs of our people with the named operators when the sources
  support that context. Include existing relevant source videos and stories;
  a name list, generic roof drawing or unrelated celebrity photo is not proof.
- Describe only the connection the source establishes. Coappearance does not
  prove endorsement, partnership or results. Testimonials need the original
  words and source/timestamp; captions must identify only verified people,
  activity and date (or leave the date unknown). Preserve source links and
  recorded permission; public availability alone is not a usage-rights grant.
- **If no fresh photograph exists, publish anyway — do not hold the page**
  (Dennis, 2026-11-10). Reuse a real photo already published on our properties
  when it truthfully fits (same person, business or work, honest caption); if none
  fits, publish with an evidence-backed diagram or verified video under
  `visuals-above-the-fold` and log the photo gap as a follow-up on the page's task.
  Never fill the gap with stock or generated imagery — leave it empty and logged.
- Build QA must inventory every rendered content route and fail when any route
  lacks a source-verified meaningful real photograph. Keep a provenance allowlist or equivalent asset
  record so logos and decorative images cannot make the check pass. Mark at least
  one qualifying `<img>` per page with `data-lss-real-image="verified"` only
  after that provenance check. For a diagram, video or photographic background,
  use `data-lss-visual-proof="verified"` with an honest aria-label/title after
  source review. This supplemental marker does not satisfy the photo check.
  Bind each qualifying photograph to its source URL, permission basis, honest
  caption/context, provenance-record hash, asset hash and page hash. Use `data-lss-asset-id` and the
  private manifest contract in [page-photo-proof](https://github.com/dennisyu/local-service-spotlight-skills/blob/main/docs/page-photo-proof.md),
  or an equivalent provenance-aware site validator. Run
  `scripts/page_photo_proof.py` against every static HTML route before release
  and against the final served files after publication readback. For a page that adds a
  new photo of an identifiable person, missing source or permission basis must
  HOLD; every other finding is reported and logged, not a publication hold.
  Also inspect the rendered desktop and mobile page;
  a hidden, broken, or contextless image does not count.
- **A publishing route must enforce this before its content write or release —
  for pages that add a new photo of an identifiable person** (Dennis, 2026-11-10).
  A write that adds no new image bytes (every image hash is already publicly served
  on that domain or is in the write's retained preimage, as in a WordPress-to-Astro
  migration) needs no fresh admission, screenshots or photo review: the publisher
  records the hash comparison in its receipt and proceeds.
  Marker `PHOTO-PROVENANCE-PUBLISH-GATE-2026-11-05`. Use the canonical
  `scripts/publication_photo_gate.py` or an equivalent reviewed integration at
  the actual publisher's effect boundary. The publisher supplies its exact
  candidate HTML hashes and canonical destinations; the gate checks retained
  photo/provenance bytes, independent review, actual response-body captures and
  desktop/mobile JavaScript-on/off screenshot evidence. Revalidate that frozen
  commitment immediately before dispatch. Missing evidence, a changed page,
  asset, permission record, receipt or screenshot, an omitted route, or a stale
  review stops dispatch. A checklist, a marker-only sweep, a pack installation,
  or a caller's declared PASS cannot replace the publisher call. Keep held and
  unintegrated routes visible; neither a merged gate nor one agent's successful
  exercise proves every publisher or runtime enforced it.
- Machine-only documents and routes that never render as visitor content—such as
  `robots.txt`, XML sitemaps, feeds, and true HTTP redirects—are exempt. A
  browser-rendered redirect placeholder is not exempt; replace it with a real
  redirect or make the page comply.

The fleet check proves only that a page declares a verified image marker with
a non-data source and nonblank alt. It cannot prove that the
source loads, is visible, is meaningfully sized, or is truthful. Enforce those
claims with each site's provenance-aware build validator plus a human visual
review. Never add the marker merely to make the sweep pass.

Dennis's 2026-11-03 roofing launch correction strengthens the photo requirement
and supersedes the 2026-09-05 diagram/video-only fallback. Diagrams and embedded
video remain valid above-fold visuals, but every visitor-facing content page
also needs a relevant real photograph. An unrelated image never satisfies this
rule. The source checker is an evidence-consistency tool, not a truth or
permission certification; fresh-context source/content and rendered design
review remain required. Distribution in a repository does not prove a site's
build or publisher actually ran it.

## Amendment — publish more, hold less (Dennis Yu, 2026-11-10)

Dennis, 2026-11-10 ~22:10 +07: "yes, update the rule, since we want to publish more,
not hold things up. not always will we have fresh photos." Where anything above
conflicts, this governs:

1. **Only one thing holds publication:** a page that adds a *new* photo of an
   identifiable person (not previously published by us) without a recorded source
   and permission basis. Fix that one photo or swap it for an already-published one;
   the rest of the page is not held.
2. **Migrations and republishes that add no new image bytes are not held** and need
   no fresh render capture or photo review. Prove it with a hash comparison against
   what the domain already serves (or the retained preimage) and put it in the receipt.
3. **A page without a fresh photo is published**, using existing real photos where
   they truthfully fit, otherwise a real diagram or video, with the gap logged.
4. Unchanged: no stock or generated imagery, honest captions, never infer a person,
   place or result from a photo, and the client-property and privacy rules elsewhere.
   A real photo on every page stays the goal; it is no longer a gate.
