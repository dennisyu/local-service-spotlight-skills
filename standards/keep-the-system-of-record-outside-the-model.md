---
{
  "title": "Keep the system of record outside any one model",
  "severity": "error",
  "captured": "2026-08-16",
  "captured_from": "Dennis Yu, Office Hours, 2026-08-13 00:18:20: 'the kind of sharing and coordinating happens outside of Claude's stuff. It's in the harness that we build, where we have metadata and Obsidian and whatnot, because we never want to be tied to Claude… We never want to be held hostage accidentally. We always store our metadata and these other items outside… we want to be able to switch between any model instantly, and for that new model to have access to all the work that we've done.'",
  "applies_to": [
    "agent-behaviour"
  ]
}
---

## Keep the system of record outside any one model

- **Standards, SOPs, metadata and completed work live in files and repositories we own**,
  not inside one vendor's memory, project or chat history.
- **The test:** if the model changed tomorrow, could a new one pick up every piece of work
  in progress from the artifacts alone? If not, something important is stored in the wrong
  place.
- **Write it down where it can be read by anything.** Plain markdown, plain JSON, in a
  repository — not a proprietary format tied to one product.
- This is also why rules are copied into distributed skills rather than linked: the copy
  survives being separated from the system that made it.
