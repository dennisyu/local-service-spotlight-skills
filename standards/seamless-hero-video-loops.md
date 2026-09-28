---
{
  "title": "Hero background videos must loop without a visible snap",
  "severity": "warn",
  "captured": "2026-09-27",
  "captured_from": "Dennis Yu, 2026-09-27: 'That site has the shaky video we see in our other person brand sites. RCA and RCF across all of them.' Root-caused on alexiltchev.com: the 8s hero drift video restarts with a last-to-first frame jump 45x larger than its average per-frame change, so the whole hero visibly snaps every 8 seconds. Related August 2026 defect on tannerlaycock.com: a Ken Burns stills montage built with ffmpeg zoompan after downscaling to output size, joined with hard cuts (whole-pixel rounding shake plus a zoom snap at every picture change). Both defects live in the encoded file, not the browser, and the August fix never became a standard, so the family recurred.",
  "applies_to": ["published-html", "design-review"],
  "target_tags": ["personal-brand"]
}
---

## Hero background videos must loop without a visible snap

A hero `<video loop>` that jumps at the loop point makes the whole first screen
shudder every few seconds. Two fleet defects, one family:

**Defect 1 — drift loop with a hard restart (alexiltchev.com, Sep 2026).** An
8-second slow-drift clip whose end frame never returns to its start frame.
Measured on the shipped file: mean consecutive-frame change 0.36 (160x90
grayscale), last-to-first change 16.02 — a **45x snap** every 8 seconds.

**Defect 2 — Ken Burns montage with hard cuts (tannerlaycock.com, Aug 2026).**
Stills run through ffmpeg `zoompan` *after* scaling to the 1280x720 output
size, then concatenated with hard cuts. Input size == output size rounds x/y to
whole pixels every frame (the shake); each cut snaps the zoom from ~1.10 back
to 1.00 (the jitter on each picture). Fixed 2026-08-18 with high-res zoompan +
0.6s xfades.

The rule, fleet-wide:

- **A looping hero must be seamless: the last frame flows into the first with no
  visible jump.** Measure it, don't eyeball it. Decode the shipped mp4 at
  160x90 grayscale; take the mean absolute difference of consecutive frames
  (avg step) and of last-to-first (loop pop). The loop pop must be **under 5x**
  the avg step. alexiltchev.com shipped at 45x.
- **A one-way drift is never a loop.** If the clip drifts in one direction, make
  it seamless by construction: ping-pong it (clip + reversed clip = a perfect
  loop), or crossfade the tail into the head with `xfade`, or ship the static
  poster frame when no motion is intended.
- **Stills montages: zoom from high resolution, fade between pictures.** Run
  `zoompan` on stills at **2x the output resolution or higher**, then scale
  down. Join clips with `xfade` (0.5s or more) — never hard cuts, never
  `-c copy` concat. Never `zoompan` an input already at output size.
- **The poster must match the loop's first frame.** A poster from a different
  moment flashes a different image on every load.

Pre-publish checklist — run before any personal-brand site goes live or gets a
new hero video:

- [ ] Loop-pop ratio measured on the shipped file: under 5x.
- [ ] Two full loop restarts watched at full size: no visible snap.
- [ ] Stills montage: sources at 2x output size or higher; every join is an xfade.
- [ ] Poster frame matches the loop's first frame.
- [ ] Video is `muted`, `playsinline`, `loop`, `preload="metadata"` with a poster
  (see `nothing-plays-uninvited`).

No `checks` block: loop seamlessness is a property of the encoded video bytes,
not the page HTML, so no honest regex exists and none is claimed. Enforcement
is the sweep script (the Software leg of CCS): `check_hero_loops.py` runs
monthly against the figurehead map and fails any hero at 5x or above.
