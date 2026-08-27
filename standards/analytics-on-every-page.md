---
{
  "title": "Analytics goes on before anything gets optimised",
  "severity": "error",
  "captured": "2026-08-16",
  "captured_from": "Dennis Yu, Office Hours, 2026-07-30 00:25:40: 'that's why we always start with analytics on everything. Analytics on… we'd like to even do analytics on people's email response times, right?' Office Hours, 2026-07-23 00:12:52: 'the loop, or the reward hacking loop, can be based on a business outcome, not on, like, how many views it got on social media… not SEO metrics, but real metrics.' Isaac Hall, 2026-07-22 00:13:00: 'it's not the website, it's not how it looks, because that's just vanity, it's the connection to the CRM, the tracking, it's like all the other stuff tied into the website.'",
  "applies_to": [
    "published-html"
  ],
  "checks": [
    {
      "id": "analytics-tag-present",
      "kind": "require_regex",
      "pattern": "(?:googletagmanager\\.com/(?:gtm|gtag)|GTM-[A-Z0-9]{4,}|gtag\\s*\\(\\s*['\"]config['\"]|G-[A-Z0-9]{8,}|plausible\\.io/js|static\\.hotjar\\.com|fbq\\s*\\(\\s*['\"]init['\"])",
      "message": "no analytics tag found on the page — it cannot be measured, so it cannot be optimised",
      "examples": {
        "violating": [
          "<html><head><title>Home</title></head><body><h1>Hi</h1></body></html>"
        ],
        "clean": [
          "<script src=\"https://www.googletagmanager.com/gtag/js?id=G-ABCD12345\"></script>",
          "<script>gtag('config', 'G-ABCD12345');</script>",
          "<!-- Google Tag Manager --><script>(function(w,d){})(window,document,'GTM-ABCD123');</script>"
        ]
      }
    }
  ]
}
---

## Analytics goes on before anything gets optimised

- **Measurement is the first build step, not the last.** A page with no analytics cannot
  be improved, only redecorated, and every argument about it becomes a matter of taste.
- **The invisible plumbing outranks the visual design** — tracking, CRM connection,
  conversion events, schema and page structure come before fonts and colours.
- **Confirm the tag actually fires on the live page**, not that it exists in a settings
  screen. See `verify-by-opening-the-live-artifact`.
- Instrument the business outcome, not the vanity metric: calls, booked jobs and revenue,
  not impressions.
