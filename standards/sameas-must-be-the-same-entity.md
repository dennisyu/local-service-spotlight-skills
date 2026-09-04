---
{
  "title": "A sameAs must be the same entity, not the same name",
  "severity": "error",
  "captured": "2026-09-04",
  "captured_from": "Dennis Yu, Cowork session, 2026-09-04, asking what the two Wikidata 404s on localservicespotlight.com were. The 404s were the small half. The Person schema also claimed sameAs https://en.wikipedia.org/wiki/Dennis_Yu, which resolves 200 and is Dennis Yu Yun-kong, a Hong Kong New Wave horror director active 1980-1990. The link-resolution sweep passed it, because it resolves.",
  "source": "https://en.wikipedia.org/wiki/Dennis_Yu",
  "applies_to": ["published-html", "agent-behaviour"],
  "checks": [
    {
      "id": "no-known-entity-collision",
      "kind": "forbid_regex",
      "pattern": "en\\.wikipedia\\.org/wiki/Dennis_Yu\\b",
      "message": "sameAs claims the English Wikipedia article Dennis_Yu, which is Dennis Yu Yun-kong the Hong Kong film director — a different person",
      "examples": {
        "violating": [
          "\"sameAs\":[\"https://twitter.com/dennisyu\",\"https://en.wikipedia.org/wiki/Dennis_Yu\"]"
        ],
        "clean": [
          "\"sameAs\":[\"https://twitter.com/dennisyu\",\"https://www.linkedin.com/in/dennisyu\"]",
          "<a href=\"https://en.wikipedia.org/wiki/Dennis_Yu_Yun-kong\">the film director</a>"
        ]
      }
    }
  ],
  "target_tags": []
}
---

## A sameAs must be the same entity, not the same name

- **Every `sameAs`, every entity claim, and every `@id` must point at a page that
  is provably the same person or organisation** — not a page with a matching
  name, and not a page you have not opened.
- **A resolving URL proves nothing about identity.** The link sweep can only ask
  whether a URL returns 200. `en.wikipedia.org/wiki/Dennis_Yu` returns 200 and is
  a Hong Kong horror director. The check passed; the claim was false.
- **Verify by a second fact, never by the name.** Occupation, employer, birth
  year, a work you can name. If a second fact does not match, it is a different
  entity. This is `evidence-verification`'s core discipline applied to schema.
- **A wrong entity claim is worse than no claim.** It tells Google two people are
  one person, which is the entity collision `knowledge-panel-entity-seo` exists to
  repair. You are not adding a weak signal, you are adding a wrong one.
- **A `sameAs` that 404s asserts an entity that does not exist.** Remove it. Never
  substitute a guessed identifier — a Q-number you have not opened is a
  fabrication, however plausible its shape.
- **Deleted Wikidata items leave the ID valid-looking forever.** When an item is
  deleted for notability, the URL keeps its shape and starts 404ing. Removing the
  claim is the fix. Re-creating the item is a separate decision with its own
  notability bar; do not make it silently as part of a schema edit.
- The check below catches one known collision by name. The general rule cannot be
  grepped — verification is reading the page and matching a second fact.
