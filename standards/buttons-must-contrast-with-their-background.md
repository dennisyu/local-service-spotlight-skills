---
{
  "title": "A button must contrast with what it sits on",
  "severity": "warn",
  "captured": "2026-08-16",
  "captured_from": "Dennis Yu, Isaac Hall new website, 2026-07-22 00:16:33, reviewing the live site: 'Even on mouse over, it changes, but the button is the same color as the background.' Same call 00:21:03: 'I found some basic usability just in looking through the site, on the button and the background being the same color.'",
  "applies_to": [
    "design-review"
  ]
}
---

## A button must contrast with what it sits on

- **A call to action must be visibly separate from the section behind it** at rest, not
  only on hover. A visitor on a phone never hovers, and a button that only appears on
  hover does not exist.
- **Check the button against every background it appears on.** The same component sits on
  white, on the hero image and on the dark footer; one of those is usually where it
  disappears.
- Text on the button needs at least **4.5:1** against the button fill, and the fill itself
  needs to be clearly distinct from the section fill.
- This is the general case of `no-black-buttons`. Black is the most common way to break it;
  it is not the only way.
