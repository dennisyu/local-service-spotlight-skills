# Preserve real hero footage and reject motion defects before release

Dennis requested a root-cause correction for the shaky DigiMarCon hero while
preserving immersive real conference video. The current page remains unchanged.
This commit updates the existing PR57 checking/standard path; it does not install
a worker, alter a scheduled sweep, publish a replacement, or resolve a site hold.

## Current public evidence

Exact asset: https://dennisyu.com/wp-content/uploads/2026/08/dennis-yu-stage-hero-loop.mp4

SHA256: `41004ff041a7f20c9492d36bee0f5ce76f4c17fbaa7e45146787d6de5b887e95`.
1280x720, H.264/yuv420p,30 fps, 20 seconds, 600 frames, 1,439,193 bytes, no audio.
Cuts occur at 5, 10 and 15 seconds. Uniform encoded intervals are 33.333–33.334 ms.
Last/first grayscale MAD 58.349 versus adjacent mean 0.883 at 160x90 is seam triage,
not a camera-shake or perceptual-quality score. Fixed photographic poses and
global crop/zoom are consistent with a photo montage. Its historical encoding
recipe is not recovered. Live desktop/mobile video transform was none; no hero
parallax was found. The page is served by Caddy's static route, so a guessed
WordPress edit is not an established publishing path.

## Bounded source assessment

Preserved owned source media and hashes locally; no media bytes, private access
links, credentials or signed URLs are committed here. A 360p Chicago player copy
was rejected; this does not establish the original source's resolution. The
official large-original download was blocked by Chrome's client policy; no
protection bypass or credential/security change was made.

Charlotte selected 90–100 seconds: real action at native 1080p/25fps. Rejected for
soft face detail and the unchanged mobile hero's composition. This is an excerpt
decision, not rejection of the entire 80-minute recording.

Miami selected 894–904 seconds after inspecting the known 15-minute stage region.
Native 1080p/25fps, 9.4-second silent dissolved export, 852,086 bytes, SHA256
`99fc304cd9e2e7aacecc5d00b0cc6bf1febcbb76d7aaab8d3e2bcb99b26302a0`.
Uniform 40 ms encoded intervals, 235 frames, no detected scene cuts/audio. Seam ratio
5.235 remains triage. Mobile 47% focal position improved speaker framing without
rewriting copy. Rejected selected dissolve: 100 ms join contact sheet shows body
outline overlap, and face detail remains soft at actual hero size. No added
zoom, stabilization, reversed human action, frozen scene or synthetic media.
No claim of uninterrupted visual playback or stabilized footage is made.

Own conference footage review was requested; missing archive rights metadata is
unknown, with no identified restriction. It is not a separate blanket approval
gate. No alternate client page was edited.

## Root checking change

- Keep the existing standard slug; authentic source and camera/CSS/export
  diagnosis precede edits. Add stable-segment, crop, face, seam, silent playback,
  reduced-motion, failure, version, preimage and publishing receipts.
- Add an exact-local-export checker with bounded size/duration and stdlib only.
  Detect cuts using visible INFO showinfo output, decoded timing, freezes,
  audio and loop discontinuity. Exit 1 means defect/error; exit 2 always requires
  visual review. No automatic quality approval or fleet-wide crawl.
- Five portable regressions cover known cuts, frozen clip, exact review exit 2,
  actual missing dependency and actual unwritable receipt. Synthetic fixtures
  are test-only and never hero candidates. CI runs them with ffmpeg.
- Classify this as design-review/encoded-media acceptance, not an invented
  published-HTML regex. Regenerate only the owning standard block/index in
  AGENTS and distributed skills using the existing sync script.

CCS: content is the diagnosis/standard; checklist is the acceptance list;
software is the bounded checker and CI regression suite. LDT: learn from the
actual preserved live bytes, do bounded real-source exports and reject defective
ones, teach through the existing PR and synchronized instructions.

## Validation and release boundary

Five clip-checker regressions pass. Shared-rule sync check, marketplace structure
validation, fleet-check self-tests and congruency checks pass. 121 repository
Python tests pass. Fresh independent QA found and then verified correction of
two tests that could pass for the wrong reason. Derived shared-rule changes
were confined to this standard block/index. Local existing browser-fixture tests
could not run because Playwright is absent; the existing CI installs its runtime.
Marketplace CLI validation and remote CI remain separate receipts.

This draft source correction is not site deployment. Production remains held by
the authoritative runtime domain record: no further production change without
explicit approval. Before release, obtain/select usable original footage that
passes actual motion/face/mobile review, verify the static publishing owner/path,
integrate the loading/fallback controller, and honor that explicit hold.

Agent receipt: Codex · action: prepared tested PR source correction · human
review: authorized, not separately reviewed. Existing PR author: dennisyu;
historical outcome owner: Happy/Muse; no duplicate PR or merge.
