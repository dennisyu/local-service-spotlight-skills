---
{
  "title": "Every URL we say out loud resolves",
  "severity": "error",
  "captured": "2026-08-16",
  "captured_from": "Dennis Yu, Cowork session, 2026-08-16, on finding dennisyu.com/install/ and /skills/ both dead: 'I hate to keep fixing the same stuff over and over again.' Both paths are what conference audiences are told to visit and what the QR code points at. They had returned 404 with zero redirects for an unknown period; the same paths resolved fine on blitzmetrics.com and localservicespotlight.com, so nobody noticed. Fixed and this rule written the same session.",
  "applies_to": ["published-html"],
  "target_tags": ["hub"],
  "checks": [
    {
      "id": "canonical-short-paths-resolve",
      "kind": "require_paths",
      "paths": ["/install/", "/skills/", "/activate/"],
      "allow_status": [200, 301, 302],
      "message": "a short path we send people to from stage does not resolve",
      "examples": {
        "builds": [
          {
            "target": "https://dennisyu.com/",
            "urls": [
              "https://dennisyu.com/install/",
              "https://dennisyu.com/skills/",
              "https://dennisyu.com/activate/"
            ]
          },
          {
            "target": "https://blitzmetrics.com/some/deep/page/?x=1",
            "urls": [
              "https://blitzmetrics.com/install/",
              "https://blitzmetrics.com/skills/",
              "https://blitzmetrics.com/activate/"
            ]
          }
        ]
      }
    }
  ]
}
---

## Every URL we say out loud resolves

- **A URL spoken from a stage, printed on a QR code, or read into a podcast has no
  inbound link.** No crawler finds it, no internal link audit sees it, and no analytics
  records it until a human types it and fails. It is the one class of URL that dies
  completely silently, and the people who hit the 404 are the warmest audience we ever
  get.
- **Every hub domain answers the same short paths.** `/install/`, `/skills/` and
  `/activate/` resolve on every site we tell an audience to visit — 200, or a 301 to the
  page that actually serves that intent. Never a 404.
- **Say it once, spell it the same way everywhere.** If the talk says "slash install",
  every hub answers `/install/`. Do not rely on one domain having a page while another
  has a redirect and a third has nothing.
- **A short path is a promise, so keep it even after the page moves.** When the
  destination is renamed, repoint the redirect in the same change. The short path
  outlives every page it has ever pointed at.
- **Redirect within the domain the audience was told to visit** where a suitable page
  exists. A cross-domain hop from a QR code loses the brand impression at the exact
  moment it was earned.
- **Check it from outside, logged out.** An editor screen saying "saved" is not a
  resolving URL, and a page cache can serve a stale 404 long after the rule exists.
  See `verify-by-opening-the-live-artifact`.
- Adding a spoken path to a talk, a slide or a business card means adding it to this
  rule's `paths` list in the same week. That is the whole maintenance cost, and it is
  what stops this being rediscovered every few months.
