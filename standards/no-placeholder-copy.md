---
{
  "title": "Placeholder copy never reaches production",
  "severity": "error",
  "captured": "2026-08-16",
  "captured_from": "Found live on georgepaladichuk.com, 2026-08-15: a hero stat block reading '$34K Monthly MRR' that no one could source, sitting on a paying client's public site. Written up the same week; entered standards/ 2026-08-16.",
  "applies_to": ["published-html", "design-review"],
  "checks": [
    {
      "id": "template-placeholder-strings",
      "kind": "forbid_regex",
      "pattern": "(?:lorem ipsum|your (?:photo|logo|text|headline|name) here|placeholder (?:text|copy|image)|\\[\\s*placeholder|replace this (?:text|copy)|xxx-xxx-xxxx|example@example\\.com|john appleseed)",
      "message": "template placeholder copy is live on the page",
      "examples": {
        "violating": [
          "<p>Lorem ipsum dolor sit amet, consectetur adipiscing.</p>",
          "<img alt=\"Your photo here\" src=\"placeholder.jpg\">",
          "<a href=\"tel:xxx-xxx-xxxx\">Call us today</a>"
        ],
        "clean": [
          "<p>George rebuilt the shop's route book in six weeks.</p>",
          "<a href=\"tel:+16125551212\">Call us today</a>"
        ]
      }
    }
  ]
}
---

## Placeholder copy never reaches production

- **A number on a page is a claim.** Every stat needs a definition, a date, and someone
  who can say where it came from. If the same figure appears twice on a site it has to be
  the same figure.
- **Builder placeholder text is a defect, not a cosmetic issue.** "Lorem ipsum", "Your
  photo here", `xxx-xxx-xxxx`, `example@example.com` — each one tells a visitor the page
  was never finished, on the page where you are asking them to trust you.
- **A testimonial needs a real, nameable person.** No initials-only quotes, no
  "a client in Minneapolis".
- **The sweep only catches the obvious half, and you need to know which half.** A
  placeholder that looks like a real number — a hero stat reading "$34K Monthly MRR" that
  nobody can source — is indistinguishable from a true one to any regex. That exact
  string sat live on a paying client's site. The only defence is that whoever publishes a
  number can name its source before it goes up.
