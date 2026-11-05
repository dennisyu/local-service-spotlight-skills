"""Synthetic consistency tests; these do not establish source truth or site acceptance."""
import base64
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from scripts.page_photo_proof import check, digest, provenance_digest


class PagePhotoProofTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "assets").mkdir()
        self.photo = self.root / "assets/people.png"
        # Tiny fixture only. The independent rendered gate rejects tiny images.
        self.photo.write_bytes(base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a6ioAAAAASUVORK5CYII="))
        self.page = self.root / "index.html"
        self.page.write_text('<main><figure><img src="assets/people.png" alt="Interview participants" data-lss-real-image="verified" data-lss-asset-id="interview"><figcaption>Source-checked interview. <a href="https://example.com/original/">Original source</a></figcaption></figure></main>')
        self.manifest = {
            "version": 1,
            "assets": {"interview": {"kind": "photo", "path": "assets/people.png", "sha256": digest(self.photo),
                "source_url": "https://example.com/original/", "permission_basis": "Synthetic approved-library fixture",
                "caption": "Source-checked interview.", "context": "Synthetic interview, no endorsement claim"}},
            "pages": [{"path": "index.html", "sha256": digest(self.page), "photo_ids": ["interview"], "prepared_by": "fixture-author",
                "review": {"reviewer": "different-fixture-reviewer", "result": "PASS", "page_sha256": digest(self.page),
                    "asset_sha256": {"interview": digest(self.photo)}, "source_identity_context_and_permission_checked": True,
                    "caption_and_claims_checked": True}}]}
        self.manifest["pages"][0]["review"]["asset_provenance_sha256"] = {
            "interview": provenance_digest(self.manifest["assets"]["interview"])}

    def errors(self):
        return check(self.root, self.manifest)

    def refresh_page_hash(self):
        self.manifest["pages"][0]["sha256"] = digest(self.page)
        self.manifest["pages"][0]["review"]["page_sha256"] = digest(self.page)

    def test_consistent_declared_bundle(self):
        self.assertEqual(self.errors(), [])

    def test_omitted_route_holds(self):
        (self.root / "contact.html").write_text("<main>No photo</main>")
        self.assertTrue(any("inventory" in x for x in self.errors()))

    def test_changed_page_invalidates_review(self):
        self.page.write_text(self.page.read_text() + "<p>New claim</p>")
        self.assertTrue(any("review" in x for x in self.errors()))

    def test_changed_photo_invalidates_asset_and_review_hash(self):
        self.photo.write_bytes(self.photo.read_bytes() + b"changed")
        self.assertTrue(any("photo bytes changed" in x for x in self.errors()))

    def test_author_cannot_self_review(self):
        self.manifest["pages"][0]["review"]["reviewer"] = "fixture-author"
        self.assertTrue(any("independent" in x for x in self.errors()))

    def test_missing_review_or_provenance_holds(self):
        for field in ("source_url", "permission_basis", "context", "caption"):
            with self.subTest(field=field):
                altered = deepcopy(self.manifest)
                altered["assets"]["interview"].pop(field)
                self.assertTrue(check(self.root, altered))

    def test_svg_renamed_to_photo_holds(self):
        self.photo.write_text("<svg><rect width='600' height='400'/></svg>")
        self.manifest["assets"]["interview"]["sha256"] = digest(self.photo)
        self.manifest["pages"][0]["review"]["asset_sha256"]["interview"] = digest(self.photo)
        self.assertTrue(any("diagram/text cannot count" in x for x in self.errors()))

    def test_diagram_only_page_holds(self):
        self.page.write_text('<main><svg data-lss-visual-proof="verified" aria-label="A roof diagram"><rect width="600" height="400"/></svg></main>')
        self.refresh_page_hash()
        self.assertTrue(any("no matching marked photo" in x for x in self.errors()))

    def test_logo_in_navigation_does_not_count(self):
        self.page.write_text(self.page.read_text().replace("<main>", "<nav>").replace("</main>", "</nav>"))
        self.refresh_page_hash()
        self.assertTrue(any("no matching marked photo" in x for x in self.errors()))

    def test_hidden_ancestor_and_template_do_not_count(self):
        for wrapper in ('<main hidden>', '<main aria-hidden="true">', '<template>'):
            with self.subTest(wrapper=wrapper):
                original = self.page.read_text()
                self.page.write_text(original.replace('<main>', wrapper))
                self.refresh_page_hash()
                self.assertTrue(any("no matching marked photo" in x for x in self.errors()))
                self.page.write_text(original)

    def test_missing_source_link_or_caption_holds(self):
        self.page.write_text(self.page.read_text().replace('href="https://example.com/original/"', 'href="https://example.com/other/"').replace("Source-checked interview.", "Different caption."))
        self.refresh_page_hash()
        self.assertTrue(any("source link absent" in x for x in self.errors()))
        self.assertTrue(any("caption absent" in x for x in self.errors()))

    def test_hidden_caption_or_source_does_not_count(self):
        original = self.page.read_text()
        for attribute in ('hidden', 'aria-hidden="true"'):
            with self.subTest(attribute=attribute):
                self.page.write_text(original.replace('<figcaption>', f'<figcaption {attribute}>'))
                self.refresh_page_hash()
                errors = self.errors()
                self.assertTrue(any("source link absent" in x for x in errors))
                self.assertTrue(any("caption absent" in x for x in errors))

    def test_template_caption_and_source_do_not_count(self):
        original = self.page.read_text()
        self.page.write_text(original.replace('<figcaption>', '<template><figcaption>').replace('</figcaption>', '</figcaption></template>'))
        self.refresh_page_hash()
        self.assertTrue(any("source link absent" in x for x in self.errors()))
        self.assertTrue(any("caption absent" in x for x in self.errors()))

    def test_base_override_is_unsupported(self):
        self.page.write_text('<base href="https://example.com/unreviewed/">' + self.page.read_text())
        self.refresh_page_hash()
        self.assertTrue(any("base URL overrides" in x for x in self.errors()))

    def test_srcset_is_unsupported(self):
        self.page.write_text(self.page.read_text().replace('<img ', '<img srcset="https://example.com/unreviewed.png 1x" '))
        self.refresh_page_hash()
        self.assertTrue(any("srcset/picture" in x for x in self.errors()))

    def test_duplicate_attributes_cannot_change_browser_selected_proof(self):
        original = self.page.read_text()
        for injected in ('src="https://example.com/unreviewed.png"', 'data-lss-asset-id="unreviewed"',
                         'data-lss-real-image="unknown"', 'alt="Different identity"'):
            with self.subTest(injected=injected):
                self.page.write_text(original.replace('<img ', f'<img {injected} '))
                self.refresh_page_hash()
                self.assertTrue(any("duplicate HTML attributes" in x for x in self.errors()))

    def test_picture_is_unsupported(self):
        self.page.write_text(self.page.read_text().replace('<img ', '<picture><source srcset="https://example.com/unreviewed.png"><img ').replace('<figcaption>', '</picture><figcaption>'))
        self.refresh_page_hash()
        self.assertTrue(any("srcset/picture" in x for x in self.errors()))

    def test_provenance_changes_invalidate_review(self):
        for field, value in (("permission_basis", "Different permission"), ("context", "Different context"),
                             ("source_url", "https://example.com/different/"), ("caption", "Different caption"),
                             ("path", "different.png"), ("kind", "diagram")):
            with self.subTest(field=field):
                altered = deepcopy(self.manifest)
                altered["assets"]["interview"][field] = value
                self.assertTrue(any("provenance changed" in x for x in check(self.root, altered)))

    def test_missing_provenance_review_digest_holds(self):
        self.manifest["pages"][0]["review"].pop("asset_provenance_sha256")
        self.assertTrue(any("review digest missing" in x for x in self.errors()))

    def test_explicit_reviewed_served_url_uses_retained_photo_bytes(self):
        asset = self.manifest["assets"]["interview"]
        asset["served_url"] = "https://example.com/wp-content/uploads/people.png"
        self.page.write_text(self.page.read_text().replace('src="assets/people.png"',
                             'src="' + asset["served_url"] + '"'))
        self.refresh_page_hash()
        self.assertTrue(any("provenance changed" in x for x in self.errors()))
        self.manifest["pages"][0]["review"]["asset_provenance_sha256"]["interview"] = provenance_digest(asset)
        self.assertEqual(self.errors(), [])
        self.photo.write_bytes(self.photo.read_bytes() + b"changed")
        self.assertTrue(any("photo bytes changed" in x for x in self.errors()))

    def test_unlisted_or_unsafe_remote_image_cannot_satisfy_proof(self):
        original = self.page.read_text()
        for url in ("http://example.com/people.png", "https://user:password@example.com/people.png",
                    "https://example.com/people.png#fragment"):
            with self.subTest(url=url):
                asset = self.manifest["assets"]["interview"]
                asset["served_url"] = url
                self.manifest["pages"][0]["review"]["asset_provenance_sha256"]["interview"] = provenance_digest(asset)
                self.page.write_text(original.replace('src="assets/people.png"', 'src="' + url + '"'))
                self.refresh_page_hash()
                self.assertTrue(any("served_url" in x for x in self.errors()))
        asset["served_url"] = "https://example.com/reviewed.png"
        self.manifest["pages"][0]["review"]["asset_provenance_sha256"]["interview"] = provenance_digest(asset)
        self.assertTrue(any("no matching marked photo" in x for x in self.errors()))

    def test_snapshot_parses_only_copied_html_and_photo_bytes(self):
        snapshot = {path.relative_to(self.root).as_posix(): path.read_bytes()
                    for path in self.root.rglob('*') if path.is_file()}
        self.page.write_text('<main>No qualifying photo</main>')
        self.photo.write_text('<svg>not the reviewed raster</svg>')
        self.assertEqual(check(self.root, self.manifest, snapshot=snapshot), [])
        self.assertTrue(check(self.root, self.manifest))
        snapshot['assets/people.png'] = bytearray(b'not immutable bytes')
        self.assertTrue(any('immutable bytes' in e for e in check(self.root, self.manifest, snapshot=snapshot)))

    def test_remote_image_must_have_the_matching_reviewed_asset_id(self):
        asset = self.manifest['assets']['interview']
        asset['served_url'] = 'https://example.com/people.png'
        self.page.write_text(self.page.read_text().replace('src="assets/people.png"',
                             'src="https://example.com/people.png"').replace(
                             'data-lss-asset-id="interview"', 'data-lss-asset-id="other"'))
        self.refresh_page_hash()
        self.manifest['pages'][0]['review']['asset_provenance_sha256']['interview'] = provenance_digest(asset)
        self.assertTrue(any('no matching marked photo' in e for e in self.errors()))

    def test_unknown_marked_photo_holds(self):
        self.page.write_text(self.page.read_text() + '<img src="assets/people.png" alt="Other photo" data-lss-real-image="verified" data-lss-asset-id="other">')
        self.refresh_page_hash()
        self.assertTrue(any("omitted from page provenance" in x for x in self.errors()))

    def test_asset_cannot_escape_public_root(self):
        self.manifest["assets"]["interview"]["path"] = "../outside.png"
        self.assertTrue(any("escapes" in x for x in self.errors()))

    def test_bad_shapes_hold(self):
        for manifest in (None, [], {"version": 1}, {"version": 1, "assets": {}, "pages": [{}]}):
            self.assertTrue(check(self.root, manifest))

    def test_malformed_review_holds(self):
        self.manifest["pages"][0]["review"] = []
        self.assertTrue(any("independent" in x for x in self.errors()))


if __name__ == "__main__":
    unittest.main()
