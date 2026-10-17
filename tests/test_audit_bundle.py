"""Actual temporary-file regressions; synthetic fixtures are never client QA."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'docs/audit-quality'))
import verify_bundle as bundle


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.receipt = json.loads((ROOT / 'tests/fixtures/audit-tier-base.json').read_text())
        report = b'Synthetic report bytes; no real audit or calibration is claimed.\n'
        final_hash = hashlib.sha256(report).hexdigest()
        # Bind all fixture final-artifact assertions to real temporary bytes.
        self.receipt = json.loads(json.dumps(self.receipt).replace('a' * 64, final_hash))
        self.receipt['artifacts'][0]['path'] = 'report.pdf'
        (self.root / 'report.pdf').write_bytes(report)
        self.manifest = {'schema_version': bundle.VERSION, 'receipt': {},
                         'artifacts': {'report': {'path': 'report.pdf', 'sha256': final_hash}},
                         'evidence': {}}
        (self.root / 'evidence').mkdir()
        for i, row in enumerate(self.receipt['evidence']):
            name = 'evidence/%s.json' % i
            capture = 'evidence/%s-capture.txt' % i
            (self.root / capture).write_text(json.dumps({'synthetic': True, 'asserted_record': row}))
            (self.root / name).write_text(json.dumps({'schema_version':'UAQG-EVIDENCE-SNAPSHOT-1.0.0',
                'synthetic':True,'evidence_id':row['id'],'original_locator':row['locator'],
                'capture':{'path':capture,'sha256':bundle.sha(self.root / capture)}}))
            self.manifest['evidence'][row['id']] = {'path': name, 'sha256': bundle.sha(self.root / name)}
        self.write()

    def write(self):
        self.receipt['bundle_evidence'] = [dict(id=k, **v) for k,v in self.manifest['evidence'].items()]
        (self.root / 'run.json').write_text(json.dumps(self.receipt))
        self.manifest['receipt'] = {'path': 'run.json', 'sha256': bundle.sha(self.root / 'run.json')}
        (self.root / 'bundle-manifest.json').write_text(json.dumps(self.manifest))

    def check(self, mode='exercise'):
        return bundle.verify(self.root, 'bundle-manifest.json', mode)

    def hold(self, reason=None, mode='exercise'):
        r = self.check(mode)
        self.assertEqual(r['decision'], 'HOLD', r)
        if reason:
            self.assertTrue(any(reason in s for s in r['reasons']), r)

    def test_real_file_exercise(self):
        r = self.check()
        self.assertEqual(r['decision'], 'EXERCISE_PASS', r)
        self.assertEqual(r['receipt_decision'], 'RELEASE_READY')
        self.assertEqual(set(r['checker_sha256']), set(bundle.BOUND_FILES))

    def test_default_refuses_synthetic_production(self):
        self.hold('synthetic exercise', mode='production')

    def test_non_synthetic_cannot_use_exercise(self):
        self.receipt['synthetic'] = False; self.write()
        self.hold('exercise requires')

    def test_synthetic_false_relabel_does_not_clear_production(self):
        self.receipt['synthetic'] = False; self.write()
        self.hold('origin differs', mode='production')

    def test_evidence_rehash_manifest_alone_cannot_change_receipt_commitment(self):
        row = next(iter(self.manifest['evidence'].values()))
        (self.root / row['path']).write_text('unrelated bytes')
        row['sha256'] = bundle.sha(self.root / row['path'])
        (self.root / 'bundle-manifest.json').write_text(json.dumps(self.manifest))
        self.hold('reviewed receipt commitment')

    def test_changed_underlying_capture_holds(self):
        row = next(iter(self.manifest['evidence'].values()))
        snapshot = json.loads((self.root / row['path']).read_text())
        (self.root / snapshot['capture']['path']).write_text('changed actual source')
        self.hold('changed file')

    def test_artifact_cannot_replace_capture(self):
        row = next(iter(self.manifest['evidence'].values()))
        snapshot = json.loads((self.root / row['path']).read_text())
        snapshot['capture'] = self.manifest['artifacts']['report']
        (self.root / row['path']).write_text(json.dumps(snapshot))
        row['sha256'] = bundle.sha(self.root / row['path']);self.write()
        self.hold('separate source/review record')

    def test_hardlink_cannot_alias_final_as_capture(self):
        row = next(iter(self.manifest['evidence'].values()))
        os.link(self.root / 'report.pdf', self.root / 'evidence/report-link.txt')
        snapshot = json.loads((self.root / row['path']).read_text())
        snapshot['capture'] = {'path':'evidence/report-link.txt', 'sha256':bundle.sha(self.root / 'report.pdf')}
        (self.root / row['path']).write_text(json.dumps(snapshot))
        row['sha256'] = bundle.sha(self.root / row['path']);self.write()
        self.hold('separate source/review record')

    def test_changed_final_bytes_hold(self):
        (self.root / 'report.pdf').write_bytes(b'Changed after review')
        self.hold('changed file')

    def test_rehashing_manifest_cannot_reuse_old_review(self):
        (self.root / 'report.pdf').write_bytes(b'Changed after review')
        self.manifest['artifacts']['report']['sha256'] = bundle.sha(self.root / 'report.pdf')
        self.write(); self.hold('differs from reviewed receipt')

    def test_missing_and_changed_evidence(self):
        row = next(iter(self.manifest['evidence'].values()))
        (self.root / row['path']).write_text('Different review')
        self.hold('changed file')
        (self.root / row['path']).unlink(); self.hold()

    def test_receipt_tampering(self):
        (self.root / 'run.json').write_text('{}')
        self.hold('changed file')

    def test_manifest_cannot_drop_evidence(self):
        self.manifest['evidence'].pop(next(iter(self.manifest['evidence'])))
        self.write(); self.hold('bind every evidence snapshot')

    def test_manifest_cannot_drop_artifact(self):
        self.manifest['artifacts'] = {}; self.write(); self.hold('snapshot IDs differ')

    def test_path_escape_and_absolute_hold(self):
        for path in ['../outside.pdf', '/etc/passwd']:
            self.manifest['artifacts']['report']['path'] = path
            self.write(); self.hold('within bundle')

    def test_symlink_hold(self):
        (self.root / 'alias.pdf').symlink_to(self.root / 'report.pdf')
        self.manifest['artifacts']['report']['path'] = 'alias.pdf'
        self.write(); self.hold('symlinks')

    def test_duplicate_json_key_hold(self):
        (self.root / 'bundle-manifest.json').write_text('{"schema_version":"x","schema_version":"y"}')
        self.hold('duplicate JSON key')

    def test_nonfinite_json_hold(self):
        (self.root / 'bundle-manifest.json').write_text('{"bad":NaN}')
        self.hold('nonfinite')

    def test_legacy_cannot_bypass(self):
        self.receipt['schema_version'] = 'old'; self.write(); self.hold('current tier receipt')

    def test_missing_calibration_hold(self):
        self.receipt['quality']['calibration']['status'] = 'NOT_RUN'
        self.write(); self.hold('uncalibrated')

    def test_self_review_hold(self):
        self.receipt['independent_review']['reviewer_id'] = self.receipt['author_id']
        self.write(); self.hold('self-review')

    def test_stale_review_hold(self):
        self.receipt['independent_review']['artifacts'][0]['sha256'] = 'b'*64
        self.write(); self.hold('stale')

    def test_unknown_source_hold(self):
        self.receipt['checks'][0]['status'] = 'UNKNOWN'
        self.write(); self.hold('required check')

    def test_open_major_defect_hold(self):
        # Missing typed closure cannot be hidden by numeric quality.
        self.receipt['defects'] = [{'id':'F1','severity':'S1','closed':False,
                                   'disposition':None,'closure_review_receipt':None}]
        self.write(); self.hold()

    def test_cli_exit_status(self):
        cmd = [sys.executable, str(ROOT / 'docs/audit-quality/verify_bundle.py'), '--root', str(self.root)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertEqual(json.loads(r.stdout)['decision'], 'HOLD')
        r = subprocess.run(cmd + ['--mode', 'exercise'], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(json.loads(r.stdout)['decision'], 'EXERCISE_PASS')


if __name__ == '__main__':
    unittest.main()
