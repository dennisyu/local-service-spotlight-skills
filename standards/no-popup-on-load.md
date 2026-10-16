---
{
  "title": "No popup on page load",
  "severity": "error",
  "captured": "2026-08-16",
  "captured_from": "BlitzMetrics definitive article, 2026-05-17: 'Next on the list: no autoplay video on landing pages, no popup on page load, and no unnamed link text. Same plugin shape, different selectors.'",
  "source": "https://blitzmetrics.com/why-we-dont-use-black-buttons/",
  "applies_to": ["published-html", "design-review"],
  "checks": [
    {
      "id": "elementor-page-load-trigger",
      "kind": "forbid_regex",
      "pattern": "\"page_load\"\\s*:\\s*\"yes\"",
      "message": "Elementor popup is set to trigger on page load",
      "examples": {
        "violating": ["{\"triggers\":{\"page_load\":\"yes\",\"page_load_delay\":3}}"],
        "clean": ["{\"triggers\":{\"click\":\"yes\",\"click_selector\":\".cta\"}}"]
      }
    },
    {
      "id": "popup-auto-open-trigger",
      "kind": "forbid_regex",
      "pattern": "\"type\"\\s*:\\s*\"auto_open\"",
      "message": "popup plugin is configured to auto-open",
      "examples": {
        "violating": ["{\"type\":\"auto_open\",\"settings\":{\"delay\":2000}}"],
        "clean": ["{\"type\":\"click_open\",\"settings\":{\"extra_selectors\":\".cta\"}}"]
      }
    },
    {
      "id": "markup-load-trigger",
      "kind": "forbid_regex",
      "pattern": "data-(?:popup-)?trigger\\s*=\\s*\"(?:load|onload|page_load|time_delay)\"",
      "message": "element declares a load-time popup trigger in markup",
      "examples": {
        "violating": [
          "<div class=\"modal\" data-popup-trigger=\"load\">Subscribe</div>",
          "<div data-trigger=\"time_delay\" data-delay=\"4000\">Wait!</div>"
        ],
        "clean": ["<div class=\"modal\" data-popup-trigger=\"click\">Subscribe</div>"]
      }
    }
  ]
}
---

## No popup on page load

- **Nothing covers the page before the visitor has read anything.** A modal that opens on
  load, on a timer, or on scroll-depth before the first section is finished interrupts
  the only moment you had their full attention, and it is the single most common reason a
  first-time visitor closes the tab.
- The permitted triggers are **click** and **exit intent on desktop**. A newsletter offer
  earns its place in the page, after the proof, as a section — not as an ambush.
- This applies to cookie and consent banners too: they may be present, but they must not
  block the content or be dismissable only by accepting.
- **Coverage is partial and you should know it.** These checks catch the three signatures
  that cover most of the fleet — Elementor's `page_load` trigger, the `auto_open` popup
  type, and load triggers declared in markup. A popup wired up in custom JavaScript will
  pass the sweep. When you touch a site, look at it once with a fresh session and no
  cookies; that is the only reliable test.
