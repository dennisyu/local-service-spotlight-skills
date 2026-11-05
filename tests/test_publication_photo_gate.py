"""Synthetic consistency fixtures, never real browser/source/reviewer evidence."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from scripts import publication_photo_gate as gate
from scripts.page_photo_proof import digest, provenance_digest


def png_header(width, height):
    # Deliberately a software-only header fixture. It is not a decoded image or
    # a browser screenshot; these tests cannot establish real evidence origin.
    return b'\x89PNG\r\n\x1a\n' + struct.pack('>I', 13) + b'IHDR' + struct.pack('>II', width, height) + b'\x08\x02\0\0\0fixture'


class PublicationPhotoGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root, self.captures = self.base / 'public', self.base / 'captures'
        self.root.mkdir()
        self.captures.mkdir()
        (self.root / 'people.png').write_bytes(png_header(640, 480))
        self.page = self.root / 'index.html'
        self.page.write_text('<main><h1>People doing the work</h1><figure><img src="people.png" alt="Interview participants" data-lss-real-image="verified" data-lss-asset-id="people"><figcaption>Interview participants. <a href="https://example.test/original/">Original source</a></figcaption></figure></main>')
        self.page_sha = digest(self.page)
        asset = {'kind': 'photo', 'path': 'people.png', 'sha256': digest(self.root / 'people.png'),
                 'source_url': 'https://example.test/original/', 'permission_basis': 'Synthetic fixture only',
                 'caption': 'Interview participants.', 'context': 'Synthetic interview, no endorsement'}
        self.manifest = {'version': 1, 'assets': {'people': asset}, 'pages': [
            {'path': 'index.html', 'sha256': self.page_sha, 'photo_ids': ['people'], 'prepared_by': 'synthetic-author',
             'review': {'reviewer': 'synthetic-independent-reviewer', 'result': 'PASS', 'page_sha256': self.page_sha,
                        'asset_sha256': {'people': asset['sha256']},
                        'asset_provenance_sha256': {'people': provenance_digest(asset)},
                        'source_identity_context_and_permission_checked': True, 'caption_and_claims_checked': True}}]}
        self.url = 'https://example.test/article/'
        self.render_url = 'http://127.0.0.1:8766/article/'
        now = datetime.now(timezone.utc).isoformat()
        self.receipt = {'version': 1, 'collector': 'cua', 'requestedUrl': self.render_url,
                        'observedAt': now, 'geometry': 'PASS', 'observations': []}
        screenshot_hashes = {}
        for w, h in ((1280, 800), (390, 844)):
            for js in (True, False):
                name = f'{w}x{h}-{js}.png'
                (self.captures / name).write_bytes(png_header(w, h))
                source_name = name + '.html'
                (self.captures / source_name).write_bytes(self.page.read_bytes())
                screenshot_hashes[name] = digest(self.captures / name)
                self.receipt['observations'].append({'viewport': {'width': w, 'height': h}, 'javaScriptEnabled': js,
                    'geometry': 'PASS', 'httpStatus': 200, 'loaded': True, 'overflow': False,
                    'label': 'Interview participants', 'finalUrl': self.render_url,
                    'bbox': {'x': 20, 'y': 100, 'width': 350, 'height': 262},
                    'visible': {'width': 350, 'height': 262, 'fraction': 1, 'viewportFraction': 350 * 262 / (w * h), 'unoccludedFraction': 1},
                    'headings': [{'readableLine': True, 'lines': [{'fontSize': 32, 'visibleFraction': 1, 'unoccludedFraction': 1}]}],
                    'layoutStability': {'status': 'STABLE', 'matchingMeasurementAndScreenshot': True},
                    'sourceBinding': 'paired_http_capture', 'sourceSha256': self.page_sha,
                    'sourceCapture': {'path': source_name, 'sha256': self.page_sha},
                    'screenshot': name, 'screenshotSha256': screenshot_hashes[name]})
        self.proof = {'version': 1, 'synthetic': False, 'pages': [
            {'path': 'index.html', 'url': self.url, 'render_url': self.render_url, 'collector': 'cua',
             'page_sha256': self.page_sha, 'receipt': {'path': 'receipt.json', 'sha256': ''},
             'review': {'reviewer': 'synthetic-independent-reviewer', 'result': 'PASS', 'observed_at': now,
                        'page_sha256': self.page_sha, 'receipt_sha256': '', 'screenshot_sha256': screenshot_hashes,
                        'meaningful_real_photo_checked': True, 'source_permission_and_context_checked': True,
                        'title_and_first_screen_checked': True}}]}
        self.manifest_path, self.proof_path = self.base / 'photos.json', self.base / 'render-proof.json'
        self.expected = {'index.html': {'sha256': self.page_sha, 'url': self.url}}
        self.save()

    def save(self):
        self.manifest_path.write_text(json.dumps(self.manifest))
        (self.captures / 'receipt.json').write_text(json.dumps(self.receipt))
        value = digest(self.captures / 'receipt.json')
        self.proof['pages'][0]['receipt']['sha256'] = value
        self.proof['pages'][0]['review']['receipt_sha256'] = value
        self.proof_path.write_text(json.dumps(self.proof))

    def admit(self):
        return gate.admit(self.root, self.manifest_path, self.proof_path, self.captures, self.expected)

    def test_consistent_declared_fixture_and_revalidation(self):
        value = self.admit()
        self.assertEqual(value.status, 'EVIDENCE_CONSISTENT')
        self.assertIs(gate.revalidate(value), value)

    def test_original_text_only_page_refused_even_with_declared_pass(self):
        self.page.write_text('<main><h1>Roofing marketing</h1><p>No real photographs.</p></main>')
        updated = digest(self.page)
        self.expected['index.html']['sha256'] = updated
        self.manifest['pages'][0]['sha256'] = updated
        self.manifest['pages'][0]['review']['page_sha256'] = updated
        self.save()
        with self.assertRaisesRegex(gate.Hold, 'no matching marked photo'):
            self.admit()

    def test_manifest_declarations_without_actual_captures_refused(self):
        for path in self.captures.glob('*.png'):
            path.unlink()
        with self.assertRaisesRegex(gate.Hold, 'missing evidence'):
            self.admit()

    def test_missing_contract_and_synthetic_contract_refused(self):
        self.proof_path.unlink()
        with self.assertRaises(gate.Hold):
            self.admit()
        self.proof['synthetic'] = True
        self.save()
        with self.assertRaisesRegex(gate.Hold, 'synthetic'):
            self.admit()

    def test_wrong_canonical_destination_or_candidate_hash_refused(self):
        for field, value in (('url', 'https://other.test/'), ('sha256', '0' * 64)):
            with self.subTest(field=field):
                original = self.expected['index.html'][field]
                self.expected['index.html'][field] = value
                with self.assertRaises(gate.Hold):
                    self.admit()
                self.expected['index.html'][field] = original

    def test_photo_and_provenance_mutation_refused(self):
        self.manifest['assets']['people']['permission_basis'] = 'Changed permission'
        self.save()
        with self.assertRaisesRegex(gate.Hold, 'provenance changed'):
            self.admit()

    def test_self_or_stale_review_refused(self):
        original = deepcopy(self.proof)
        self.proof['pages'][0]['review']['reviewer'] = 'synthetic-author'
        self.save()
        with self.assertRaisesRegex(gate.Hold, 'independent'):
            self.admit()
        self.proof = original
        self.proof['pages'][0]['review']['observed_at'] = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        self.save()
        with self.assertRaisesRegex(gate.Hold, 'stale'):
            self.admit()

    def test_stale_capture_and_missing_js_off_refused(self):
        self.receipt['observedAt'] = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        self.save()
        with self.assertRaisesRegex(gate.Hold, 'stale'):
            self.admit()
        self.receipt['observedAt'] = datetime.now(timezone.utc).isoformat()
        self.receipt['observations'].pop()
        self.save()
        with self.assertRaisesRegex(gate.Hold, 'four required'):
            self.admit()

    def test_changed_screenshot_or_wrong_dimensions_refused(self):
        observation = self.receipt['observations'][0]
        path = self.captures / observation['screenshot']
        path.write_bytes(png_header(1, 1))
        with self.assertRaisesRegex(gate.Hold, 'screenshot'):
            self.admit()

    def test_jpeg_viewport_capture_uses_retained_header_dimensions(self):
        observation = self.receipt['observations'][0]
        original = observation['screenshot']
        body = (b'\xff\xd8\xff\xe0\x00\x02\xff\xc0\x00\x11\x08' +
                struct.pack('>HH', 800, 1280) + b'\x03' + b'\x01\x11\x00' * 3 + b'\xff\xd9')
        name = '1280x800-True.jpg'
        (self.captures / name).write_bytes(body)
        observation['screenshot'] = name
        observation['screenshotSha256'] = digest(self.captures / name)
        reviewed = self.proof['pages'][0]['review']['screenshot_sha256']
        reviewed.pop(original)
        reviewed[name] = observation['screenshotSha256']
        self.save()
        self.assertEqual(self.admit().status, 'EVIDENCE_CONSISTENT')

    def test_area_arithmetic_and_distinct_case_captures_required(self):
        observation = self.receipt['observations'][0]
        original = deepcopy(observation)
        observation['visible']['viewportFraction'] = .5
        self.save()
        with self.assertRaisesRegex(gate.Hold, 'arithmetic'):
            self.admit()
        self.receipt['observations'][0] = original
        second = self.receipt['observations'][1]
        second['screenshot'] = original['screenshot']
        second['screenshotSha256'] = original['screenshotSha256']
        self.save()
        with self.assertRaisesRegex(gate.Hold, 'own screenshot'):
            self.admit()

    def test_missing_or_changed_response_bytes_refused(self):
        capture = self.captures / self.receipt['observations'][0]['sourceCapture']['path']
        capture.write_text('<p>Different served source</p>')
        with self.assertRaisesRegex(gate.Hold, 'captured response'):
            self.admit()

    def test_weak_geometry_or_covered_title_cannot_hide_behind_pass(self):
        observation = self.receipt['observations'][0]
        observation['visible']['width'] = 5
        self.save()
        with self.assertRaisesRegex(gate.Hold, 'canonical threshold'):
            self.admit()
        observation['visible']['width'] = 350
        observation['headings'][0]['lines'][0]['visibleFraction'] = .1
        self.save()
        with self.assertRaisesRegex(gate.Hold, 'title'):
            self.admit()

    def test_collector_cannot_impersonate_canonical_renderer(self):
        self.proof['pages'][0]['collector'] = 'rendered_visual_check'
        self.save()
        with self.assertRaisesRegex(gate.Hold, 'collector'):
            self.admit()

    def test_new_route_and_private_proof_leak_refused(self):
        (self.root / 'privacy.html').write_text('<h1>No photograph</h1>')
        with self.assertRaisesRegex(gate.Hold, 'inventory'):
            self.admit()
        (self.root / 'privacy.html').unlink()
        inside = self.root / 'photos.json'
        inside.write_bytes(self.manifest_path.read_bytes())
        with self.assertRaisesRegex(gate.Hold, 'outside public root'):
            gate.admit(self.root, inside, self.proof_path, self.captures, self.expected)

    def test_symlink_capture_refused(self):
        capture = self.captures / self.receipt['observations'][0]['screenshot']
        retained = self.base / 'retained.png'
        capture.rename(retained)
        capture.symlink_to(retained)
        with self.assertRaisesRegex(gate.Hold, 'symlink'):
            self.admit()

    def test_changed_file_after_admission_and_during_check_refused(self):
        value = self.admit()
        (self.root / 'new.css').write_text('body {display:none}')
        with self.assertRaisesRegex(gate.Hold, 'changed after admission'):
            gate.revalidate(value)
        (self.root / 'new.css').unlink()
        actual_check = gate.page_photo_proof.check
        def mutate(root, manifest):
            result = actual_check(root, manifest)
            (self.root / 'people.png').write_bytes(png_header(800, 600))
            return result
        with patch.object(gate.page_photo_proof, 'check', side_effect=mutate):
            with self.assertRaisesRegex(gate.Hold, 'changed during admission'):
                self.admit()


if __name__ == '__main__':
    unittest.main()
