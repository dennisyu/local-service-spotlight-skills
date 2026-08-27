---
{
  "title": "Nothing plays at the visitor uninvited",
  "severity": "error",
  "captured": "2026-08-16",
  "captured_from": "BlitzMetrics definitive article, 2026-05-17: 'Next on the list: no autoplay video on landing pages, no popup on page load, and no unnamed link text.' Scope confirmed by Dennis Yu, Cowork session, 2026-08-16: background video is fine — 'just not the ones where videos play and are irritating, because that's the intention behind that rule.' The rule is therefore written around the irritation, not around the <video> tag.",
  "source": "https://blitzmetrics.com/why-we-dont-use-black-buttons/",
  "applies_to": ["published-html", "design-review"],
  "checks": [
    {
      "id": "video-autoplay-unmuted",
      "kind": "forbid_regex",
      "pattern": "<video\\b(?![^>]*\\bmuted\\b)[^>]*\\bautoplay\\b",
      "message": "video autoplays without muted — sound starts at the visitor",
      "examples": {
        "violating": [
          "<video src=\"hero.mp4\" autoplay loop playsinline></video>",
          "<video autoplay class=\"bg\" poster=\"p.jpg\"><source src=\"a.mp4\"></video>"
        ],
        "clean": [
          "<video src=\"hero.mp4\" autoplay muted playsinline loop poster=\"hero.jpg\"></video>",
          "<video src=\"testimonial.mp4\" controls preload=\"none\"></video>"
        ]
      }
    },
    {
      "id": "audio-autoplay",
      "kind": "forbid_regex",
      "pattern": "<audio\\b[^>]*\\bautoplay\\b",
      "message": "audio element autoplays; audio never autoplays, muted or not",
      "examples": {
        "violating": ["<audio src=\"intro.mp3\" autoplay></audio>"],
        "clean": ["<audio src=\"intro.mp3\" controls preload=\"none\"></audio>"]
      }
    },
    {
      "id": "embed-autoplay-unmuted",
      "kind": "forbid_regex",
      "pattern": "<iframe\\b(?![^>]*mute(?:d)?=1)[^>]*autoplay=1",
      "message": "embedded player autoplays without mute=1",
      "examples": {
        "violating": [
          "<iframe src=\"https://www.youtube.com/embed/abc?autoplay=1\"></iframe>"
        ],
        "clean": [
          "<iframe src=\"https://www.youtube.com/embed/abc?autoplay=1&amp;mute=1\"></iframe>",
          "<iframe src=\"https://www.youtube.com/embed/abc\"></iframe>"
        ]
      }
    }
  ]
}
---

## Nothing plays at the visitor uninvited

The test is not "is there a video." The test is **would this irritate someone who
just arrived.** Motion the visitor chose to look at is atmosphere; sound and
motion that grab at them are an ambush, and the first thing they learn about you
is that your site did that.

- **Background video in a hero is encouraged.** It is how the immersive standard
  gets met. Ship it with all four of `muted`, `playsinline`, `loop` and a `poster`
  image. `playsinline` is not optional — without it, iOS yanks the video full
  screen the moment it starts, which is the loudest version of the thing this rule
  exists to prevent.
- **Sound never starts on its own.** A hero film may absolutely have an audio
  track. It loads muted with a visible, labelled unmute control, and the visitor
  decides. That satisfies both halves: the video is there, the ambush is not.
- **`<audio>` never autoplays**, muted or not. There is no case for it.
- **Embedded players count.** `?autoplay=1` on a YouTube or Vimeo iframe must be
  paired with `mute=1`, or dropped.
- **Anything that cannot meet the muted conditions ships without `autoplay`**,
  behind a poster frame and a play control.
- Judge the rest by the same intent, even where no regex covers it: a video that
  covers the content, one that cannot be paused, one that restarts on every scroll,
  or one that pushes the call to action off the screen is irritating whether or not
  it makes a sound.
- This is the published-page half of `silent-media-playback`. That rule stops an
  agent putting sound through *your* speakers while it tests; this one stops a site
  putting sound through a *visitor's* speakers.
