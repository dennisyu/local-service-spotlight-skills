---
name: cross-post-watch
description: "Mirror the owner's original Facebook posts to X immediately and to LinkedIn as one best post per rolling 24 hours, word for word, with verified publication and a state file that prevents duplicates. Use when a personal-brand owner wants their own agent to distribute their Facebook posts to LinkedIn and X without doubling their work or cannibalizing LinkedIn reach."
author: Dennis Yu — Local Service Spotlight
---

# Cross-Post Watch

One post, three audiences. The watch mirrors the owner's original
Facebook posts to X right away, and to LinkedIn once a day — the best
post of the day, not every post. It runs on the owner's standing
authorization: the agent posts by default and never asks for per-post
approval.

## The cadence rule (the point of this skill)

The platforms are not the same, so the cadence is not the same.

- **X mirrors everything, immediately.** X tolerates and rewards
  volume; every qualifying Facebook post goes to X as soon as the
  watch sees it.
- **LinkedIn gets one post per rolling 24 hours.** LinkedIn scores a
  post over roughly 18 hours, and a second post inside that window
  cannibalizes the first (the algorithm research consensus, including
  Richard van der Blom's studies: never two posts within 24 hours;
  a few strong posts a week beat daily volume). So LinkedIn posts
  queue, and once a day the agent picks the single best one.
- **A weak day skips LinkedIn.** If nothing queued clears the bar,
  LinkedIn gets nothing that day. A skipped day is the system
  working, not failing.

## What the owner needs

- A public Facebook profile or Page where they post original content.
- A LinkedIn profile and an X account.
- An agent with a scheduler and a browser. The agent signs in with the
  owner's own saved logins, held in the owner's own credential store —
  this skill never sees, stores, or transmits passwords.

## State the watch keeps

One state file, updated after every verified post:

- `last_crossposted_id` / `last_crossposted_at` — the X watermark.
  Nothing at or before it is ever reposted.
- `linkedin_last_posted_at` / `linkedin_last_url` — the LinkedIn gate
  anchor: when the last LinkedIn cross-post was verified live.
- `linkedin_queue` — Facebook post IDs already on X but not yet on
  LinkedIn. Each queued post's exact text, media file, and link are
  saved as artifacts next to the state file so a later run can post
  them without re-fetching.

## The loop

Runs three times a day on weekdays (morning, midday, evening) are
proven; the cadence of the watch matters less than the LinkedIn gate.

1. **Fetch** the owner's recent Facebook timeline.
2. **Filter** to original posts only: their own text, their own
   photos or video, or their own link. Skip shares and reposts of
   other people's content, Stories, and anything the owner would not
   want amplified (when in doubt, skip). Check each post's comments —
   owners often put the link in their own comment; carry that link
   into the cross-posts.
3. **Post to X** immediately, oldest first. Copy the owner's words
   EXACTLY — no rewrites, no added hashtags, no footers. Attach the
   same image or link. Text over X's character limit goes out as a
   numbered thread split at sentence boundaries, words unchanged.
   Verify the post is live on the profile before counting it done,
   then advance the watermark and add the post to the LinkedIn queue.
4. **Fill the LinkedIn slot** once per run, after X. If fewer than 24
   hours have passed since `linkedin_last_posted_at`, do nothing —
   the queue waits. If the gate is open, read every queued post and
   pick the single best:
   1. personal stakes / lived experience;
   2. named people and people stories;
   3. specific, checkable results or claims;
   4. substantive lessons from the owner's work.

   Link-only announcements and pure instruction/process posts rank
   last — if one of those is the strongest thing queued, skip the
   slot and leave the queue intact.
5. **Post the winner to LinkedIn** with its saved text, image, and
   link, after a dedup check of the profile for the same text.
   Verify it is live, remove it from the queue, and set
   `linkedin_last_posted_at` to the verified publication time.

## Formatting standard (LinkedIn)

Never a wall of text. Preserve the Facebook original's paragraph line
breaks — a blank line between paragraphs, ideally one sentence per
paragraph, splitting long blocks at sentence boundaries. Only line
breaks may change: never add, remove, or reorder words or
punctuation. Verify the published post actually shows the breaks.

## Safety and authorization

- Post only what the owner posted publicly themselves. Never invent,
  paraphrase, or "improve" their words.
- Never repost: dedup against the destination profile whenever there
  is any doubt, and let the state file — not memory — say what has
  already gone out.
- The watch runs on standing authorization the owner grants once.
  Revoking it stops the watch; nothing in this skill widens it.
- Report one line when something posts or the run is blocked
  ("Cross-posted to LinkedIn (best-of-24h): …", "Cross-post blocked:
  X sign-in expired"). Otherwise stay silent — a closed LinkedIn gate
  and a skipped slot are routine, not news.

## Why it works

Distribution is not one setting. Each platform's scoring window is a
constraint, and automation that ignores it taxes the very reach it was
built to create. Mirroring everything everywhere is a default; this
watch is the strategy version: volume where volume wins, restraint
where restraint wins, and the owner's exact words everywhere.
