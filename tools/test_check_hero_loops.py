"""Meaningful regressions for defective cuts, freeze and silent failure paths."""
import importlib.util
import json
import os
import sys
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('check_hero_loops.py')
spec = importlib.util.spec_from_file_location('hero_qa', SCRIPT)
qa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qa)


class RegressionTests(unittest.TestCase):
    def test_known_cut_times_are_detected(self):
        with tempfile.TemporaryDirectory() as d:
            file = Path(d) / 'cuts.mp4'
            cmd = ['ffmpeg', '-v', 'error']
            for color in ['black', 'white', 'black', 'white']:
                cmd += ['-f', 'lavfi', '-i', f'color=c={color}:s=160x90:r=30:d=5']
            cmd += ['-filter_complex', '[0:v][1:v][2:v][3:v]concat=n=4:v=1:a=0[v]',
                    '-map', '[v]', '-c:v', 'libx264', str(file)]
            subprocess.run(cmd, check=True)
            result = qa.analyze(file)
            self.assertEqual(result['scene_cut_times_seconds'], [5.0, 10.0, 15.0])
            self.assertIn('HARD_CUT_REVIEW_REQUIRED', result['machine_defects'])
            self.assertEqual(subprocess.run([sys.executable, str(SCRIPT), str(file)], stdout=subprocess.DEVNULL).returncode, 1)

    def test_frozen_export_cannot_pass(self):
        with tempfile.TemporaryDirectory() as d:
            file = Path(d) / 'freeze.mp4'
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
                            'color=c=red:s=160x90:r=30:d=1', '-c:v', 'libx264', str(file)], check=True)
            result = qa.analyze(file)
            self.assertIn('FROZEN_VIDEO_REQUIRES_SOURCE_REVIEW', result['machine_defects'])
            self.assertIsNone(result['seam_ratio'])

    def test_clean_motion_still_needs_visual_review(self):
        with tempfile.TemporaryDirectory() as d:
            file = Path(d) / 'motion.mp4'
            # Synthetic fixture only; never used in a hero candidate.
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
                            'testsrc2=s=160x90:r=30:d=1', '-filter_complex', '[0:v]split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1:a=0[v]', '-map', '[v]', '-c:v', 'libx264', str(file)], check=True)
            result = qa.analyze(file)
            self.assertEqual(result['machine_defects'], [])
            self.assertEqual(result['verdict'], 'VISUAL_REVIEW_REQUIRED')
            self.assertEqual(subprocess.run([sys.executable, str(SCRIPT), str(file)], stdout=subprocess.DEVNULL).returncode, 2)

    def test_missing_dependency_is_failure(self):
        with tempfile.TemporaryDirectory() as d:
            file = Path(d) / 'valid.mp4'
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
                            'testsrc2=s=160x90:r=30:d=1', '-c:v', 'libx264', str(file)], check=True)
            env = dict(os.environ, PATH='/nonexistent')
            result = subprocess.run([sys.executable, str(SCRIPT), str(file)], env=env, capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertNotIn(b'Traceback', result.stderr)
            self.assertIn(b'ffprobe', result.stdout + result.stderr)

    def test_missing_file_and_unwritable_receipt_fail_cleanly(self):
        with tempfile.TemporaryDirectory() as d:
            result = subprocess.run([sys.executable, str(SCRIPT), str(Path(d) / 'missing.mp4')], capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertNotIn(b'Traceback', result.stderr)
            file = Path(d) / 'valid.mp4'
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
                            'testsrc2=s=160x90:r=30:d=1', '-c:v', 'libx264', str(file)], check=True)
            # A regular file used as a parent is a portable unwritable destination.
            blocker = Path(d) / 'not-a-directory'
            blocker.write_text('fixture')
            result = subprocess.run([sys.executable, str(SCRIPT), str(file), '--output', str(blocker / 'receipt.json')], capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertNotIn(b'Traceback', result.stderr)
            self.assertIn(str(blocker / 'receipt.json'), json.loads(result.stdout)['error'])


if __name__ == '__main__':
    unittest.main()
