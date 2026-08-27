---
{
  "title": "Process real content; never generate it",
  "severity": "warn",
  "captured": "2026-08-16",
  "captured_from": "Dennis Yu, Zoom, three independent occasions. Richard Rossi, 2026-07-20 00:18:20: 'I'm a big proponent of using AI to amplify our relationships and to use it to do assistant stuff, not to generate. We never… like, with Leanne and I, we both preach we never generate content with AI. We process real videos and experiences and things off of our phone and all that… Not… not makeup out of thin air.' Sean K Fay, 2026-07-23 00:55:22: 'Can we make sure the provenance of this traces back to the raw ingredients of EEAT… so when an LLM comes in and looks at the article, it can see that this is based on real experience, and it has as little AI manipulation as possible.' Office Hours, 2026-07-16 00:11:19, on Google Business Profile posts: 'the key with GBP posts is that things be consistent with repurposing other content, not generate. Most people use the tools to generate… Which is garbage.'",
  "applies_to": [
    "published-html",
    "agent-behaviour"
  ],
  "checks": [
    {
      "id": "article-cites-a-source",
      "kind": "require_regex",
      "pattern": "(?:youtube\\.com/(?:embed|watch)|youtu\\.be/|player\\.vimeo\\.com|<video\\b|<audio\\b|podcasts\\.apple\\.com|open\\.spotify\\.com|<blockquote\\b|<cite\\b|<figcaption\\b)",
      "message": "no source artifact on the page — no video, audio, captioned figure or attributed quote tying it back to something real",
      "examples": {
        "violating": [
          "<article><h1>Five tips</h1><p>Here are five tips.</p></article>"
        ],
        "clean": [
          "<article><iframe src=\"https://www.youtube.com/embed/abc\"></iframe><p>…</p></article>",
          "<article><blockquote>We fixed it on the call.</blockquote><cite>George Paladichuk</cite></article>",
          "<figure><img src=\"call.png\"><figcaption>From the 7 Aug call</figcaption></figure>"
        ]
      }
    }
  ],
  "target_tags": [
    "article"
  ]
}
---

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
