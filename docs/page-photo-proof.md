# Verify page photos from their actual sources

Every visitor-facing HTML page needs a relevant real photograph. Illustrations,
process diagrams, logos and videos are useful additions. They do not replace
the photograph or establish a claimed relationship.

For a vertical spotlight page, show real founders and operators in that vertical.
Use the approved photo/video library and previously published original material
first. Name the people only when the source establishes who they are. Describe
the activity: an interview, shared event, client project or visit. Coappearance
alone does not establish endorsement, a partnership or a business result.
Show an existing relevant source video when available; preserve a visible photo
and source link when the player is unavailable. Quote only the actual words with
a source and timestamp. Keep source dates unknown when unknown.

`scripts/page_photo_proof.py` checks a static public output directory against a
private manifest. It inventories all `.html` and `.htm` files, checks page/photo
hashes, screens raster signatures and matching marked images, checks source
links and captions outside statically hidden/template content, and requires a
different reviewer's exact-byte source and content review declaration. It holds
duplicate HTML attributes, unsupported `<base>`, qualifying `srcset` and `<picture>` markup rather than
certifying fallback `src` bytes while a browser selects something else.
Run it before publishing and after obtaining
the served final HTML/assets for readback:

```bash
python3 scripts/page_photo_proof.py --root /absolute/public-output \
  --manifest /absolute/private/page-photo-proof.json
```

Keep this manifest outside the published root. Its paths are relative to that
root. A page cannot be omitted because it is a utility, privacy or thank-you
page. True redirects and machine-only formats do not produce content HTML and
therefore do not enter this inventory. Dynamic sites must export every actual
rendered route to this structure or supply an equivalent site-specific checker;
checking one homepage cannot certify a whole site.

Dynamic publishers may retain exact HTML without rewriting its image URLs. Set
an asset's optional `served_url` to the literal public HTTPS URL in its `<img
src>`. Keep `asset.path` as the actual retained local photo file; its byte hash
and independent review remain required. `served_url` participates in
`provenance_digest`, so changing it invalidates the prior review. Relative/local
images continue to work unchanged. This mapping does not fetch the endpoint or
prove it currently serves those bytes: retain the actual source capture and have
the independent source/browser review inspect it. `srcset`/`picture`, implicit
remote mappings and HTML rewrites that change the reviewed page hash do not
satisfy this contract.

Example manifest structure (all values are illustrative, not real evidence):

```json
{
  "version": 1,
  "assets": {
    "roofing-interview": {
      "kind": "photo",
      "path": "assets/roofing-interview.jpg",
      "sha256": "ACTUAL_PHOTO_SHA256",
      "source_url": "https://example.com/original-interview/",
      "permission_basis": "Recorded approved-library use and its source locator",
      "caption": "People and activity confirmed by the original source.",
      "context": "Interview about the operator's business; no result claim."
    }
  },
  "pages": [
    {
      "path": "index.html",
      "sha256": "ACTUAL_PAGE_SHA256",
      "photo_ids": ["roofing-interview"],
      "prepared_by": "executing-agent-session",
      "review": {
        "reviewer": "different-fresh-reviewer-session",
        "result": "PASS",
        "page_sha256": "ACTUAL_PAGE_SHA256",
        "asset_sha256": {"roofing-interview": "ACTUAL_PHOTO_SHA256"},
        "asset_provenance_sha256": {"roofing-interview": "FULL_ASSET_RECORD_SHA256"},
        "source_identity_context_and_permission_checked": true,
        "caption_and_claims_checked": true
      }
    }
  ]
}
```

`asset_provenance_sha256` commits the review to every field of the asset record,
including its source, permitted use, context, caption, path and byte hash. Compute
it with `provenance_digest(asset)` from `scripts/page_photo_proof.py`: SHA256 of
UTF-8 JSON using `sort_keys=True`, `separators=(",", ":")`, `ensure_ascii=False`
and `allow_nan=False`. Changing any field invalidates the old review declaration;
the author must not regenerate a review digest without an actual renewed review.

In the actual page, pair the image with an honest caption and source link:

```html
<figure>
  <img src="assets/roofing-interview.jpg" alt="Source-verified people and activity"
       data-lss-real-image="verified" data-lss-asset-id="roofing-interview">
  <figcaption>Source-verified caption.
    <a href="https://example.com/original-interview/">Original interview</a>
  </figcaption>
</figure>
```

`CONSISTENT` means the declared evidence agrees with these exact files. It cannot
authenticate a reviewer or prove a source's truth, usage rights, image decoding,
actual photo identity, CSS visibility, relevance, painted content or a live delivery.
A matching raster signature can still belong to corrupt bytes or a rasterized
diagram. Actual image loading/decoding and photo identity require the separate
rendered and source reviews below. A forged declaration
remains false evidence. The reviewer must inspect the original source and exact
final page; do not fill the review fields from the author's assumptions.

Run `scripts/rendered_visual_check.mjs` and fresh-context visual review at
1280×800 and 390×844 on the actual URL for loaded, useful, above-the-fold
content and readable title. Test videos silently (muted and volume zero before
playback), record video playback separately, and retain source links if blocked.
Preserve destination authority, holds, publisher and rollback; a checker result
never authorizes a release. A source-file change requires a new hash and review.

Source rules: `every-public-page-has-real-imagery`, `every-article-has-pictures`,
`process-real-content-never-generate`, `visuals-above-the-fold` and
`qa-from-a-different-context-window`. This procedure adds no schedule or fleet
installation. File source distribution, runtime activation, actual execution,
independent acceptance and publication as separate states.

## Required publisher integration

Marker `PHOTO-PROVENANCE-PUBLISH-GATE-2026-11-05` applies at the actual writer's
effect boundary. The canonical
[`publication_photo_gate.py`](../scripts/publication_photo_gate.py) performs no
network request or content write. Publishing code, rather than the candidate's
author, supplies its expected candidate paths, SHA256 values and canonical URLs:

```python
from scripts.publication_photo_gate import admit, revalidate

commitment = admit(public_root, private_photo_manifest, private_render_proof,
                   private_captures_root, {
    "article/index.html": {"sha256": exact_candidate_sha256,
                           "url": "https://example.com/article/"}
})
# Resolve destination authority and transaction controls separately.
revalidate(commitment)
# Only now may the existing authorized publisher dispatch these exact bytes.
```

`admit` raises `Hold` on missing, malformed or inconsistent evidence. It returns
an immutable `EVIDENCE_CONSISTENT` commitment, not a release approval.
`revalidate` checks the complete original public tree and original private
proof/capture/code bytes again. A new HTML route, changed CSS or photo, revised
review, or replaced screenshot cannot inherit an old result. All public HTML
routes must match the expected mapping and photo manifest. Private manifests
and captures stay outside the public root. Do not catch a failed gate and keep
publishing or add a bypass flag. A CMS adapter may retain its exact body fragment
as the candidate; its writer binds that fragment's actual bytes and destination
before a write.

The additional private rendered proof has this structure. Values below are
illustrative, not real evidence:

```json
{
  "version": 1,
  "synthetic": false,
  "pages": [{
    "path": "article/index.html",
    "url": "https://example.com/article/",
    "page_sha256": "ACTUAL_CANDIDATE_SHA256",
    "render_url": "http://127.0.0.1:8766/article/",
    "collector": "rendered_visual_check",
    "receipt": {"path": "article/receipt.json", "sha256": "ACTUAL_RECEIPT_SHA256"},
    "review": {
      "reviewer": "different-fresh-reviewer-session",
      "result": "PASS",
      "observed_at": "ACTUAL_TIME_WITH_TIMEZONE",
      "page_sha256": "ACTUAL_CANDIDATE_SHA256",
      "receipt_sha256": "ACTUAL_RECEIPT_SHA256",
      "screenshot_sha256": {
        "article/1280x800-js-on.png": "ACTUAL_SCREENSHOT_SHA256",
        "article/1280x800-js-off.png": "ACTUAL_SCREENSHOT_SHA256",
        "article/390x844-js-on.png": "ACTUAL_SCREENSHOT_SHA256",
        "article/390x844-js-off.png": "ACTUAL_SCREENSHOT_SHA256"
      },
      "meaningful_real_photo_checked": true,
      "source_permission_and_context_checked": true,
      "title_and_first_screen_checked": true
    }
  }]
}
```

The receipt retains four observations at the canonical viewports, with actual
PNG/JPEG screenshot files of those dimensions, source-body files, hashes,
loaded/visible visual measurements, a readable first-screen title, no horizontal
overflow and matching stable measurement/screenshot evidence. Numeric limits
come from `standards/visuals-above-the-fold.md`; a declared geometry PASS cannot
waive a failed measurement. Captures and independent review must be no older
than 24 hours, with five minutes of forward-clock tolerance. A changed page or
asset still requires new review inside that window.

The canonical renderer emits `collector: rendered_visual_check`. Each
observation records `sourceBinding: response_body`, `sourceSha256`, and
`sourceCapture: {path, sha256, bytes}` for the actual navigation response body,
beside its screenshot. The gate verifies those retained body bytes against the
candidate. Capture paths are relative to the receipt directory; the outer
proof's screenshot-review map is relative to `captures_root`.

Where the approved browser tool is CUA, use `collector: cua` in both the proof
page and receipt. Retain the same observed viewport, loaded/painted geometry,
title, overflow, `layoutStability: {status: STABLE,
matchingMeasurementAndScreenshot: true}`, actual screenshot and source fields.
Set `sourceBinding: paired_http_capture` and retain the exact separately captured
HTML body, labeling it as paired HTTP evidence instead of claiming the canonical
script or browser-response capture ran. A JavaScript-disabled case must actually
disable execution while retaining the same source bytes; stripping scripts
produces a different artifact. Preserve a missing or failed observation as HOLD.

For a non-Python publisher, the CLI requires all five paths:

```bash
python3 scripts/publication_photo_gate.py --root /absolute/candidate \
  --manifest /absolute/private/photos.json \
  --render-proof /absolute/private/render-proof.json \
  --captures /absolute/private/captures \
  --expected-pages /absolute/private/publisher-owned-candidate-mapping.json
```

The CLI is a source check; the writer must still bind the same candidate at its
effect boundary. A Python writer should retain and revalidate the commitment,
then use its reviewed transaction and rollback. A disconnected writer that does
not call the gate is unintegrated even if its agent read this document.

The native marketplace with repository source `./` can include root scripts;
the generic `pack2plugin.py` converter instead copies selected skill directories
and optional agent/command directories. Check the actual installation instead
of generalizing from either route. Private publishers may use an exact reviewed,
hash-pinned source mirror beside their maintained entry point, preserving the
module/renderer/standard dependencies and source revision. Instruction sync and
installed checker bytes need separate receipts. Test actual invocation and
rejected missing/changed-proof cases.

This gate checks retained-byte and declaration consistency. It cannot
authenticate a reviewer, source capture or screenshot, identify a person, grant
usage rights, or defeat a fully fabricated evidence bundle. An independent
reviewer must open the original sources and exact final artifacts. Synthetic
software fixtures and manufactured declarations are never operational proof.
