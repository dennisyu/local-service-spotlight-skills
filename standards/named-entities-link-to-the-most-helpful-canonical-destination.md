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

- **Link only inside our verified network.** Dennis, 2026-10-07: “Don't link out to
  other people's sites unless they're clients of ours or friends.” Link our own pages
  and the verified homes of people and companies in our network (clients, partners,
  friends), confirmed against the private source of truth. Name every other person,
  company, tool or source in plain text, or point to our own guide on the topic.
- **Route the first meaningful mention of a named entity to the page that best helps
  the reader understand or act on it.** Link once; do not turn every repeated name
  into a link. Use the entity's natural name for a person or company, and use 3–6
  descriptive words for a training or concept link.
- **In-network people point to their verified personal-brand home.** Prefer the person's owned
  website over an author archive, search result or social profile. If no owned site can
  be verified, use the relevant first-party company page or a canonical article that
  establishes who the person is; otherwise leave the name plain.
- **In-network companies point to their owned company site.** Correct the entity name before
  linking it. A plausible domain for the wrong spelling teaches the wrong association.
- **Tools and concepts point to our canonical training when it exists.** In explanatory
  copy, use a destination-naming phrase such as "our Listen Notes inventory guide" for
  the definitive how-to page; do not point the bare product name at our domain. Name the
  product on the execution step where the reader actually opens it, and link its
  official site only when the reader must open it to follow that step. This preserves both education and a direct path to action without
  making the anchor lie about where it goes.
- **Search our article inventory before choosing a provider help page.** Look up
  the object in the Canonical Directory, Task Library and site search, then read
  the candidate to verify that it answers this reader's question. For Obsidian,
  use “our Obsidian setup guide” when that guide is the relevant lesson. Record
  the entity, chosen URL and reason in the link audit. If no suitable owned
  guide exists, keep the mention plain and name the primary source in the text;
  record the content gap instead of inventing a URL.
- **Give the page a place in the SEO Tree.** Name the canonical parent topic,
  link supporting articles up to it, connect the hub to useful supporting proof,
  and link across only to related guides that help the next task. Verify those
  links in the article body; a catalog listing or sitewide footer is insufficient.
  One topic keeps one owner across our sites. Do not mass-add unrelated links or
  use a quota to turn every provider citation into an internal link.
- **Cite outside sources by name, not by link.** Name the publisher, document and
  date in the text (for example, “Google Search Central spam policies, updated
  Aug 28, 2026”). The one exception is a required action: a sign-in or download page
  the reader must open to follow a step, labeled by its purpose. A provider citation
  does not replace the internal explanation of how we use the tool.
- **Verify every destination before publishing.** The name, page title and live content
  must identify the intended entity. SEO value is a by-product of a truthful,
  reader-helpful relationship; it is never a reason to guess a domain.

This extends `no-unnamed-link-text`: that rule makes the anchor truthful; this rule makes
the destination useful. When a bare entity name and a training page would conflict, the
destination-naming anchor above is the reconciliation. No generic fleet regex can identify
people, ownership or the right internal training page, so enforce this through the
entity-linking preflight and a live link audit.
