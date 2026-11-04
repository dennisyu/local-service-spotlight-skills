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
