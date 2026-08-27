---
{
  "title": "Named entities link to the most helpful canonical destination",
  "severity": "error",
  "captured": "2026-08-22",
  "captured_from": "Dennis Yu, Codex task, 2026-08-22",
  "source": "https://blitzmetrics.com/how-to-inventory-a-podcast-on-youtube/",
  "applies_to": [
    "agent-behaviour",
    "design-review"
  ]
}
---

## Named entities link to the most helpful canonical destination

- **Route the first meaningful mention of a named entity to the page that best helps
  the reader understand or act on it.** Link once; do not turn every repeated name
  into a link. Use the entity's natural name for a person or company, and use 3–6
  descriptive words for a training or concept link.
- **People point to their verified personal-brand home.** Prefer the person's owned
  website over an author archive, search result or social profile. If no owned site can
  be verified, use the relevant first-party company page or a canonical article that
  establishes who the person is; otherwise leave the name plain.
- **Companies point to their owned company site.** Correct the entity name before
  linking it. A plausible domain for the wrong spelling teaches the wrong association.
- **Tools and concepts point to our canonical training when it exists.** In explanatory
  copy, use a destination-naming phrase such as "our Listen Notes inventory guide" for
  the definitive how-to page; do not point the bare product name at our domain. Put the
  product's natural name and official website on the execution step where the reader
  actually opens it. This preserves both education and a direct path to action without
  making the anchor lie about where it goes.
- **Verify every destination before publishing.** The name, page title and live content
  must identify the intended entity. SEO value is a by-product of a truthful,
  reader-helpful relationship; it is never a reason to guess a domain.

This extends `no-unnamed-link-text`: that rule makes the anchor truthful; this rule makes
the destination useful. When a bare entity name and a training page would conflict, the
destination-naming anchor above is the reconciliation. No generic fleet regex can identify
people, ownership or the right internal training page, so enforce this through the
entity-linking preflight and a live link audit.
