---
{
  "title": "Every link and every entity claim resolves",
  "severity": "error",
  "captured": "2026-08-16",
  "captured_from": "Dennis Yu / Local Service Spotlight public standard: Every link and every entity claim resolves. Original capture date is retained in captured. Public-safety clarification authorized by the owner on 2026-10-29; this reusable copy omits private conversation, personnel, account and incident details.",
  "applies_to": [
    "published-html"
  ],
  "checks": [
    {
      "id": "schema-sameas-resolves",
      "kind": "resolve_urls",
      "within": "\"sameAs\"\\s*:\\s*\\[[^\\]]*\\]",
      "extract": "\"(https?://[^\"]+)\"",
      "limit": 25,
      "message": "sameAs target does not resolve \u2014 the entity claim points at nothing",
      "examples": {
        "extracts": [
          {
            "html": "{\"@type\":\"Person\",\"name\":\"A\",\"sameAs\":[\"https://x.com/a\",\"https://www.linkedin.com/in/b\"],\"url\":\"https://site.com\"}",
            "urls": [
              "https://x.com/a",
              "https://www.linkedin.com/in/b"
            ]
          },
          {
            "html": "{\"sameAs\":[\"https:\\/\\/www.wikidata.org\\/wiki\\/Q1\"]}",
            "urls": [
              "https://www.wikidata.org/wiki/Q1"
            ]
          }
        ]
      }
    },
    {
      "id": "outbound-links-resolve",
      "kind": "resolve_urls",
      "extract": "<a\\b[^>]*href=\"(https?://[^\"]+)\"",
      "skip_same_host": true,
      "limit": 40,
      "message": "outbound link does not resolve",
      "examples": {
        "extracts": [
          {
            "html": "<a href=\"https://www.linkedin.com/in/x\">LinkedIn</a> <a href=\"/about/\">About</a>",
            "urls": [
              "https://www.linkedin.com/in/x"
            ]
          }
        ]
      }
    }
  ]
}
---

## Every link and every entity claim resolves

- **A broken entity claim is worse than no claim.** `sameAs` is how a site tells Google,
  Bing and every AI answer engine "this person is that entity". Pointed at a deleted or
  wrong target, it does not merely fail — it actively teaches the wrong association.
- **Verify every `sameAs` target returns 200 before publishing schema, and re-verify
  quarterly.** Targets can be deleted or change identity after publication.
  Recheck the current destination rather than relying on a past successful read.
- **Only anchors count.** `preconnect`, `dns-prefetch`, `canonical` and `alternate`
  hints are not links a visitor can follow, and treating them as links reports
  `googletagmanager.com` as a dead link on every site that loads analytics — noise that
  teaches people to ignore the sweep.
- **Request every outbound link before publishing.** A dead social link in a footer
  appears on every page of the site, which makes one careless paste a site-wide defect.
- Treat `401`, `403`, `405` and `429` from Instagram, Facebook, X and LinkedIn as *pass*.
  Those platforms block automated requests by policy; that is not a broken link, and
  reporting it as one trains people to ignore the sweep. `404`, `410`, `5xx`, DNS
  failure and connection timeout are real.
- When a target is genuinely gone, remove the claim rather than leaving it. An honest
  smaller `sameAs` set outperforms a larger one containing a lie.
