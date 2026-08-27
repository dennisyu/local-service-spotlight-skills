---
{
  "title": "Verify by opening the live artifact",
  "severity": "error",
  "captured": "2026-08-16",
  "captured_from": "Dennis Yu, Zoom, repeatedly. Rob and Austin, 2026-08-12 00:15:23: 'And don't come back to me until you've done it. And then, of course, when you do it, I want you to check your work to make sure you did it right. Don't just come back and tell me it's done.' Cam and dad AI + audit, 2026-08-09 00:51:54: 'any work that we do, we always inspect. We trust but verify.' Caught live on camera in Mats and Leo, 2026-07-19 01:14:03, when an agent reported articles published: 'all we have to do is go to the website. And see, are there articles here or not?' — 01:14:42: 'I just went there now to show you there's no article.'",
  "applies_to": [
    "agent-behaviour"
  ]
}
---

## Verify by opening the live artifact

- **"I did it" is not evidence. The artifact is.** Before reporting any work complete,
  fetch the live URL, open the file, or query the API and confirm the change is actually
  there. An agent that has been caught reporting published articles onto a site with no
  articles has burned more trust than the task was worth.
- **Check the thing a user would see, not the thing you wrote.** A database row is not a
  published page — caches, builders and permissions all sit in between. Fetch the public
  URL as an anonymous visitor.
- **A page that could not be fetched has not been verified.** Report it as unverified,
  never as done.
- Quote the evidence in the report: the URL, the status code, and the string you found.
