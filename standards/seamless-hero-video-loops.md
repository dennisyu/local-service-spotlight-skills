---
{
  "title": "Keep immersive heroes authentic and verify their motion",
  "severity": "error",
  "captured": "2026-09-27",
  "captured_from": "Dennis Yu: dennisyu.com/digimarcon still has shaky video; preserve immersive real video and solve the root cause. Extends the existing seamless-hero-video-loops proposal (skills PR 57), rather than replacing its record.",
  "applies_to": ["design-review"],
  "target_tags": ["personal-brand"]
}
---

## Keep immersive heroes authentic and verify their motion

Preserve relevant real footage. A photo zoom montage is not a moving-camera
recording, even when exported as MP4. Do not satisfy a request for authentic
video with stock, AI animation, frozen frames, or a smoothed slideshow.

- Identify the exact live URL, served route, export hash, original recording,
  rights/provenance, current production owner and any existing proposal before
  making a second export. Preserve original files and publishing preimages.
- Review representative motion and two complete restarts at desktop and mobile
  sizes, silently. Separate intentional pans and subject movement from camera
  shake, output-grid stepping, cuts, loop seams, CSS transforms, mobile crop
  changes, dropped frames and network stalls. Stills alone cannot certify this.
- Prefer stable existing real segments. Apply light stabilization to the original
  recording only when camera shake is actually diagnosed. Review faces, hands,
  straight edges and every crop; reject warp, breathing zoom and excessive crop.
- Preserve forward action in real footage. Reversing speech, gestures or people
  to obtain a low seam score is not a default repair. A dissolve also needs
  review for duplicate faces and a distracting ghost image.
- Preserve source resolution. Record intrinsic dimensions, output dimensions,
  crop and file size; do not call an upscaled player proxy a high-resolution
  source. Inspect the actual face at the intended hero size.
- Use a first-frame poster and silent, inline playback, with a pause control.
  Respect reduced motion before attaching the source and when the preference
  changes. Pause when offscreen. A CSS-hidden video can still download/play.
  Handle autoplay rejection and loading failure by retaining a meaningful poster.
- Use versioned replacement URLs; never overwrite the preserved live source.
  Verify the candidate first, then use the observed official publishing rail.
  A successful WordPress edit does not verify a Caddy static page.

### Clip acceptance checklist

- [ ] Original recording, owner/rights receipt, stable segment timestamps and hashes recorded.
- [ ] Export analyzed with `tools/check_hero_loops.py exact-local-export.mp4 --output receipt.json`.
- [ ] Machine warnings reconciled. A low MAD/seam ratio is triage, not proof of stability.
- [ ] Complete muted playback reviewed; reviewer, hash, viewport, observations and date recorded.
- [ ] Two restarts reviewed on 1280×800 and 390×844; no seam/ghosting/face warp.
- [ ] Mobile focal crop retains the actual speaker and desktop copy remains readable.
- [ ] Poster, blocked/failed autoplay, loading error, reduced-motion changes and offscreen pause verified.
- [ ] Browser frame pacing tested with video playback quality/frame callback telemetry where supported.
- [ ] Publishing source, exact route, approval/hold, preimage, rollback and post-release anonymous QA recorded.

### CCS and LDT

Content: this root-cause rule and the preserved DigiMarCon diagnosis. Checklist:
the acceptance list above. Software: the local-file checker detects encoded cuts,
loop discontinuity, freeze, audio and timestamp irregularity, fails explicitly,
and always leaves semantic/playback approval to a qualified reviewer.

Learn: the live DigiMarCon MP4 was four five-second photographic zoom sequences;
its hard scene cuts and restart were encoded, while the hero transform was none.
Do: preserve the file, obtain authentic source, compare forward and dissolved
real-footage candidates, reject inadequate proxies and unresolved transitions.
Teach: extend PR 57's standard/checking path and distribute only after review;
proposal, merge, skill installation and live release are separate receipts.

This encoded-media acceptance rule uses the design-review scope. It does not
claim a published-HTML regex check; the bounded clip checker runs on export bytes.
No HTML regex can establish genuine motion, stabilization, rights or a seamless
perceptual loop. No automated test is represented as continuous visual review.

### Existing proposal history retained

This updates `standards/seamless-hero-video-loops.md` on the existing OPEN
skills PR 57 (`standard/seamless-hero-video-loops`, base `71bed3d862274f7b5a5bd226329b165fdf2eb457`).
Its September history documented a drift-loop restart on alexiltchev.com and
an output-grid zoom/hard-cut montage on tannerlaycock.com. This task changes
no asset or page on those sites. The former 5× seam threshold remains a review
trigger; it is not a universal perceptual quality score or proof of camera shake.
Stills may be suitable when intentionally chosen as still imagery, but are not
an acceptable substitute for Dennis's requested immersive real footage here.
