"""The video finishing lane is only worth having if its checks can fail.

Two kinds of tests:
- pure-Python tests of caption chunking, transcript parsing, word snapping and
  receipt parsing (always run);
- media tests that synthesize a deliberately bad video with ffmpeg, prove QA
  fails it for the right reasons, run finish.py, and prove QA then passes the
  loudness and hook checks (skipped when ffmpeg is not installed).
Nothing in these tests plays audio.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "skills" / "content-agent" / "scripts"
sys.path.insert(0, str(SCRIPTS))


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


video_qa = _load("video_qa")
finish = _load("finish")
CAP = finish.DEFAULT_STYLE["captions"]


def w(word, start, end):
    return {"word": word, "start": start, "end": end}


class CaptionChunking(unittest.TestCase):
    def test_never_more_than_max_words(self):
        words = [w(f"w{i}", i * 0.3, i * 0.3 + 0.25) for i in range(10)]
        cues = finish.chunk_words(words, CAP)
        self.assertTrue(all(len(c["words"]) <= CAP["max_words"] for c in cues))
        self.assertEqual(sum(len(c["words"]) for c in cues), 10)

    def test_breaks_on_punctuation_and_pause(self):
        words = [w("Record", 0.0, 0.3), w("once.", 0.32, 0.6),
                 w("Then", 0.62, 0.8), w("ship", 1.5, 1.8)]
        texts = [" ".join(x["word"] for x in c["words"])
                 for c in finish.chunk_words(words, CAP)]
        self.assertEqual(texts, ["Record once.", "Then", "ship"])

    def test_cues_never_overlap_and_never_flash(self):
        words = [w("a", 0.0, 0.05), w("b", 0.4, 0.45), w("c", 0.5, 0.55),
                 w("d", 2.0, 2.05)]
        cues = finish.chunk_words(words, CAP)
        for a, b in zip(cues, cues[1:]):
            self.assertLessEqual(a["end"], b["start"])
        self.assertGreaterEqual(cues[-1]["end"] - cues[-1]["start"], CAP["min_cue_s"])

    def test_uppercase_and_highlights_in_ass_only(self):
        words = finish.mark_keywords(
            [w("spend", 0, 1), w("$1", 1, 2), w("a", 2, 3), w("dollar", 3, 4),
             w("a", 4, 5), w("day.", 5, 6)], ["Dollar a Day"])
        cue = {"words": words}
        ass = finish.cue_text(cue, CAP, ass=True)
        self.assertIn("{\\c&H00FFFF&}$1{\\r}", ass)
        self.assertIn("{\\c&H00FFFF&}DOLLAR{\\r} {\\c&H00FFFF&}A{\\r} "
                      "{\\c&H00FFFF&}DAY.{\\r}", ass)
        self.assertIn("$1{\\r} A {\\c", ass)   # the lone "a" before it stays white
        self.assertTrue(ass.startswith("SPEND"))
        self.assertEqual(finish.cue_text(cue, CAP, ass=False), "SPEND $1 A DOLLAR A DAY.")

    def test_ass_control_characters_cannot_leak(self):
        cue = {"words": [w("a\\Nb", 0, 1), w("{\\b1}x", 1, 2)]}
        txt = finish.cue_text(cue, dict(CAP, uppercase=False, highlight_numbers=False),
                              ass=True)
        self.assertNotIn("\\", txt)
        self.assertNotIn("{", txt)

    def test_merged_cues_respect_max_chars(self):
        words = [w("reputation,", 0.0, 0.5), w("not", 0.52, 0.6), w("people-", 0.62, 0.7)]
        for cue in finish.chunk_words(words, CAP):
            self.assertLessEqual(len(" ".join(x["word"] for x in cue["words"])),
                                 CAP["max_chars"])

    def test_shift_drops_cues_before_the_new_start(self):
        cues = [{"words": [], "start": 0.0, "end": 0.5},
                {"words": [], "start": 2.0, "end": 2.5}]
        out = finish.shift_cues(cues, 1.0)
        self.assertEqual(len(out), 1)
        self.assertAlmostEqual(out[0]["start"], 1.0)


class TranscriptInputs(unittest.TestCase):
    def test_speaker_labels_only_strip_names(self):
        srt = ("1\n00:00:01,000 --> 00:00:02,000\nStep one: open it\n\n"
               "2\n00:00:02,000 --> 00:00:03,000\n[Speaker 2]: Hi\n\n"
               "3\n00:00:03,000 --> 00:00:04,000\nSo here's the thing: go\n")
        words = [x["word"] for x in finish.words_from_srt(srt)]
        self.assertEqual(words[:3], ["Step", "one:", "open"])
        self.assertIn("Hi", words)
        self.assertNotIn("[Speaker", words)
        self.assertIn("thing:", words)

    def test_clip_text_is_validated(self):
        self.assertEqual(finish.parse_clip("3193.8-3227.1"), (3193.8, 3227.1))
        with self.assertRaises(ValueError):
            finish.parse_clip("5-2")
        with self.assertRaises(ValueError):
            finish.parse_clip("abc")

    def test_srt_spreads_words_and_strips_speaker_labels(self):
        srt = ("1\n00:00:01,000 --> 00:00:03,000\nDennis Yu: Hello there world\n\n"
               "2\n00:00:03,500 --> 00:00:04,000\n<i>Next</i>\n")
        words = finish.words_from_srt(srt)
        self.assertEqual([x["word"] for x in words], ["Hello", "there", "world", "Next"])
        self.assertAlmostEqual(words[1]["start"], 1.6667, places=3)
        self.assertAlmostEqual(words[-1]["end"], 4.0)

    def test_scribe_spacing_and_events_are_ignored(self):
        data = {"words": [{"text": "Hi", "start": 0, "end": 0.2, "type": "word"},
                          {"text": " ", "start": 0.2, "end": 0.3, "type": "spacing"},
                          {"text": "(laughs)", "start": 0.3, "end": 0.9,
                           "type": "audio_event"},
                          {"text": "um", "start": 1.0, "end": 1.2, "type": "word"}]}
        self.assertEqual([x["word"] for x in finish.normalize_words(data)], ["Hi", "um"])

    def test_faster_whisper_segments(self):
        data = {"segments": [{"words": [{"word": " Go", "start": 0.1, "end": 0.3}]}]}
        self.assertEqual(finish.normalize_words(data), [w("Go", 0.1, 0.3)])

    def test_descript_text_on_asr_clock(self):
        # Real case, 23 Oct 2026: local Whisper heard "state law", Descript had
        # "scale". Keep Descript's words, take Whisper's word timing.
        text = [w("Don't", 10.0, 10.2), w("be", 10.2, 10.4), w("mad", 10.4, 10.6),
                w("at", 10.6, 10.8), w("the", 10.8, 11.0), w("scale,", 11.0, 11.2),
                w("right?", 11.2, 11.4)]
        timed = [w("Don't", 10.05, 10.2), w("be", 10.25, 10.35), w("mad", 10.4, 10.6),
                 w("at", 10.65, 10.7), w("the", 10.72, 10.8), w("state", 10.85, 11.0),
                 w("law.", 11.05, 11.3)]
        out = finish.align_text_to_timing(text, timed)
        self.assertEqual([x["word"] for x in out],
                         ["Don't", "be", "mad", "at", "the", "scale,", "right?"])
        self.assertEqual(out[0]["start"], 10.05)
        self.assertAlmostEqual(out[5]["start"], 10.85)
        self.assertLessEqual(out[-1]["end"], 11.3)

    def test_unheard_words_keep_order_and_crosstalk_drops(self):
        # Descript: "it's a 24 ... not people- Right who"; ASR heard neither
        # "a" nor the other person's "Right".
        text = [w("it's", 1.0, 1.2), w("a", 1.2, 1.4), w("24.", 1.4, 1.6),
                w("people-", 2.0, 2.2), w("Right", 2.2, 2.4), w("who", 2.4, 2.6)]
        timed = [w("it's", 1.0, 1.15), w("24.", 1.3, 1.6), w("people", 2.0, 2.3),
                 w("who", 2.5, 2.6)]
        out = finish.align_text_to_timing(text, timed)
        self.assertEqual([x["word"] for x in out], ["it's", "a", "24.", "people-", "who"])
        starts = [x["start"] for x in out]
        self.assertEqual(starts, sorted(starts))
        cues = finish.chunk_words(out, CAP)
        self.assertEqual(" ".join(x["word"] for x in cues[-1]["words"]), "who")

    def test_clip_edges_snap_to_word_boundaries(self):
        words = [w("one", 0.0, 0.4), w("two", 0.5, 0.9), w("three", 1.0, 1.4),
                 w("four", 1.6, 2.0)]
        s, e = finish.snap_to_words(words, 0.7, 1.5, 0.08)
        self.assertAlmostEqual(s, 0.92)   # after "two" ends, never inside it
        self.assertAlmostEqual(e, 1.48)   # "three" plus pad, before "four"


class Reframe(unittest.TestCase):
    def test_vertical_crop_from_landscape(self):
        flt, ow, oh = finish.reframe_filter(1920, 1080, "9:16", 0.5)
        self.assertEqual((ow, oh), (1080, 1920))
        self.assertIn("crop=608:1080:656:0", flt)

    def test_crop_stays_inside_the_active_picture(self):
        flt, _, _ = finish.reframe_filter(1920, 1056, "9:16", 0.5, 0, 12)
        self.assertIn("crop=594:1056:663:12", flt)

    def test_focus_clamps_inside_frame(self):
        flt, _, _ = finish.reframe_filter(1920, 1080, "9:16", 0.0)
        self.assertIn("crop=608:1080:0:0", flt)


class ReceiptParsing(unittest.TestCase):
    def test_ebur128_summary(self):
        text = ("[Parsed_ebur128_0] Summary:\n\n  Integrated loudness:\n    I:   -24.0 LUFS\n"
                "    Threshold: -34.2 LUFS\n\n  Loudness range:\n    LRA:   5.5 LU\n\n"
                "  True peak:\n    Peak:   -6.1 dBFS\n")
        self.assertEqual(video_qa.parse_ebur128_summary(text),
                         {"integrated_lufs": -24.0, "lra_lu": 5.5, "true_peak_dbtp": -6.1})

    def test_scientific_notation_is_not_misread(self):
        # ffmpeg prints tiny times like 2.26757e-05; reading that as 2.27 s hid
        # three seconds of dead air in the first version (audit, 23 Oct 2026).
        sil = video_qa.parse_silences(
            "silence_start: 2.26757e-05\nsilence_end: 3.0 | silence_duration: 3\n", 10.0)
        self.assertEqual(sil[0]["start"], 0.0)
        self.assertEqual(sil[0]["end"], 3.0)

    def test_relative_silence_threshold(self):
        prof = video_qa.load_profile(None)
        self.assertEqual(video_qa.silence_threshold(prof, -24.0), -49.0)
        self.assertEqual(video_qa.silence_threshold(prof, -14.0), -39.0)
        self.assertEqual(video_qa.silence_threshold(prof, -80.0), -60.0)
        self.assertEqual(video_qa.silence_threshold(prof, -2.0), -30.0)
        prof["pauses"]["silence_threshold_db"] = -38
        self.assertEqual(video_qa.silence_threshold(prof, -24.0), -38.0)

    def test_trailing_silence_uses_the_audio_end(self):
        info = {"duration_s": 4.0, "audio": {"duration_s": 3.9}, "video": None}
        checks = {c["check"]: c["status"] for c in video_qa.evaluate(
            info, {"integrated_lufs": -14.0, "true_peak_dbtp": -2.0},
            [{"start": 0.9, "end": 3.9, "dur": 3.0}], [], video_qa.load_profile(None),
            first_audio=0.0)}
        self.assertEqual(checks["trailing_silence"], "WARN")
        self.assertEqual(checks["pauses_over_fail"], "PASS")
        self.assertEqual(checks["black_frames"], "N/A")

    def test_hook_uses_first_word_when_given(self):
        prof = video_qa.load_profile(None)
        base = ({"duration_s": 60.0, "video": None},
                {"integrated_lufs": -14.0, "true_peak_dbtp": -2.0}, [], [], prof)
        named = {c["check"]: c for c in video_qa.evaluate(*base, first_speech=4.2,
                                                          first_audio=0.0)}
        self.assertEqual(named["hook_first_speech"]["status"], "FAIL")  # music intro
        named = {c["check"]: c for c in video_qa.evaluate(*base, first_audio=0.5)}
        self.assertEqual(named["hook_first_audio"]["status"], "PASS")
        self.assertIn("not first word", named["hook_first_audio"]["note"])

    def test_silent_audio_cannot_pass(self):
        checks = {c["check"]: c["status"] for c in video_qa.evaluate(
            {"duration_s": 5.0, "video": None}, {"integrated_lufs": -70.0,
                                                 "true_peak_dbtp": -90.0},
            [], [], video_qa.load_profile(None), first_audio=None)}
        self.assertEqual(checks["integrated_loudness"], "FAIL")
        self.assertEqual(checks["hook_first_audio"], "FAIL")

    def test_open_silence_runs_to_end(self):
        text = "silence_start: 0\nsilence_end: 1.5 | silence_duration: 1.5\nsilence_start: 9.2\n"
        sil = video_qa.parse_silences(text, 10.0)
        self.assertEqual(sil[-1], {"start": 9.2, "end": 10.0, "dur": 0.8})

    def test_quiet_late_hook_and_dead_air_all_fail(self):
        info = {"duration_s": 60.0}
        loud = {"integrated_lufs": -24.0, "true_peak_dbtp": -6.0}
        sil = [{"start": 0.0, "end": 3.0, "dur": 3.0},
               {"start": 20.0, "end": 23.0, "dur": 3.0}]
        checks = {c["check"]: c["status"] for c in video_qa.evaluate(
            dict(info, video=None), loud, sil, [], video_qa.load_profile(None))}
        self.assertEqual(checks["integrated_loudness"], "FAIL")
        self.assertEqual(checks["hook_first_audio"], "FAIL")
        self.assertEqual(checks["pauses_over_fail"], "FAIL")

    def test_black_at_the_end_is_a_warning_not_a_body_fail(self):
        prof = video_qa.load_profile(None)
        black = [{"start": 55.0, "end": 59.8, "dur": 4.8}]
        checks = {c["check"]: c["status"] for c in video_qa.evaluate(
            {"duration_s": 60.0, "video": {"width": 320, "height": 240}},
            {"integrated_lufs": -14.0, "true_peak_dbtp": -2.0}, [], black, prof)}
        self.assertEqual(checks["black_frames"], "PASS")
        self.assertEqual(checks["black_close"], "WARN")

    def test_profile_overrides_merge(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump({"qa": {"loudness": {"target_lufs": -16.0}}}, fh)
        prof = video_qa.load_profile(fh.name)
        self.assertEqual(prof["loudness"]["target_lufs"], -16.0)
        self.assertEqual(prof["loudness"]["true_peak_max_dbtp"], -1.0)

    def test_example_style_file_loads(self):
        example = REPO / "skills" / "content-agent" / "references" / "video-style.example.json"
        style = finish.load_style(str(example))
        self.assertEqual(style["qa"]["loudness"]["target_lufs"], -14.0)
        self.assertTrue(style["captions"]["uppercase"])


HAVE_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))
if os.environ.get("LSS_REQUIRE_FFMPEG") and not HAVE_FFMPEG:
    # CI sets this so the media tests can never silently turn into skips.
    raise RuntimeError("LSS_REQUIRE_FFMPEG is set but ffmpeg/ffprobe are missing")


@unittest.skipUnless(HAVE_FFMPEG, "ffmpeg not installed")
class MediaRoundTrip(unittest.TestCase):
    """A quiet video with dead air at the head and a long pause must fail QA,
    and finish.py must fix what it claims to fix."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="lss-video-test-"))
        cls.src = cls.tmp / "bad.mp4"
        tone = "0.04*sin(2*PI*440*t)*(between(t,2.6,9)+between(t,11.6,16))"
        subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", "testsrc2=s=320x240:r=25:d=16",
            "-f", "lavfi", "-i", f"aevalsrc='{tone}':s=48000:d=16",
            "-vf", "drawbox=c=black:t=fill:enable='lt(t,1)'",
            "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac",
            "-shortest", str(cls.src)], check=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_qa_fails_the_bad_video_for_the_right_reasons(self):
        rec = video_qa.qa(str(self.src), video_qa.load_profile(None),
                          self.tmp / "bad.qa", frames=False)
        checks = {c["check"]: c["status"] for c in rec["checks"]}
        self.assertEqual(rec["verdict"], "FAIL")
        self.assertEqual(checks["integrated_loudness"], "FAIL")
        self.assertEqual(checks["hook_first_audio"], "FAIL")
        self.assertEqual(checks["pauses_over_fail"], "FAIL")
        self.assertEqual(checks["black_open"], "FAIL")
        self.assertTrue((self.tmp / "bad.qa" / "qa-receipt.md").exists())

    def test_finish_trims_head_and_hits_loudness_target(self):
        out = self.tmp / "fixed.mp4"
        style = finish.load_style(None)
        rep = finish.finish(str(self.src), str(out), style, trim_head=True,
                            loudness=True, words=None, burn=False, keywords=[])
        self.assertGreater(rep["start_s"], 2.0)
        self.assertEqual(rep["warnings"], [])
        rec = video_qa.qa(str(out), style["qa"], self.tmp / "fixed.qa", frames=False)
        checks = {c["check"]: c["status"] for c in rec["checks"]}
        self.assertEqual(checks["integrated_loudness"], "PASS")
        self.assertEqual(checks["true_peak"], "PASS")
        self.assertEqual(checks["hook_first_audio"], "PASS")
        self.assertNotIn("black_open", checks)
        # finish.py never hides a problem it did not fix: the 2.6 s pause remains.
        self.assertEqual(checks["pauses_over_fail"], "FAIL")
        self.assertAlmostEqual(rec["probe"]["duration_s"], rep["expected_duration_s"],
                               delta=0.25)

    def _make(self, name, vf=None, tone=None, d=8, audio=True, video=True):
        out = self.tmp / name
        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
        if video:
            cmd += ["-f", "lavfi", "-i", f"testsrc2=s=320x240:r=25:d={d}"]
        if audio:
            cmd += ["-f", "lavfi", "-i",
                    f"aevalsrc='{tone or '0.2*sin(2*PI*440*t)'}':s=48000:d={d}"]
        if vf:
            cmd += ["-vf", vf]
        if video:
            cmd += ["-c:v", "libx264", "-preset", "ultrafast"]
        cmd += ["-c:a", "aac", "-shortest", str(out)] if audio else [str(out)]
        subprocess.run(cmd, check=True)
        return out

    def test_click_then_dead_air_fails_the_hook(self):
        src = self._make("click.mp4", tone="0.5*sin(2*PI*1000*t)*lt(t,0.01)"
                                           "+0.2*sin(2*PI*440*t)*gte(t,3)")
        rec = video_qa.qa(str(src), video_qa.load_profile(None), self.tmp / "click.qa",
                          frames=False)
        c = {x["check"]: x for x in rec["checks"]}
        self.assertEqual(c["hook_first_audio"]["status"], "FAIL")
        self.assertGreater(rec["first_audio_s"], 2.5)

    def test_black_flash_and_near_black_screen_are_caught(self):
        src = self._make("flash.mp4", vf="drawbox=c=black:t=fill:enable='between(t,3,3.12)',"
                         "drawbox=x=0:y=0:w=320:h=228:c=black:t=fill:"
                         "enable='between(t,5,6)'")
        rec = video_qa.qa(str(src), video_qa.load_profile(None), self.tmp / "flash.qa",
                          frames=False)
        c = {x["check"]: x for x in rec["checks"]}
        self.assertEqual(c["black_frames"]["status"], "FAIL")
        self.assertEqual(c["black_frames"]["measured"], 2)

    def test_letterbox_is_reported(self):
        src = self._make("bars.mp4", vf="scale=320:200,pad=320:240:0:20:black")
        rec = video_qa.qa(str(src), video_qa.load_profile(None), self.tmp / "bars.qa",
                          frames=False)
        self.assertIn("letterbox", {x["check"] for x in rec["checks"]})

    def test_audio_only_marks_black_check_not_applicable(self):
        src = self._make("tone.m4a", video=False, d=3)
        rec = video_qa.qa(str(src), video_qa.load_profile(None), self.tmp / "tone.qa",
                          frames=False)
        c = {x["check"]: x["status"] for x in rec["checks"]}
        self.assertEqual(c["black_frames"], "N/A")

    def test_trim_head_on_silence_trims_nothing(self):
        src = self._make("silent.mp4", tone="0", d=3)
        out = self.tmp / "silent-out.mp4"
        rep = finish.finish(str(src), str(out), finish.load_style(None), trim_head=True,
                            loudness=True, words=None, burn=False, keywords=[])
        self.assertEqual(rep["start_s"], 0.0)
        self.assertEqual(len(rep["warnings"]), 2)   # nothing trimmed, loudness skipped
        self.assertAlmostEqual(rep["expected_duration_s"], 3.0, delta=0.1)

    def test_letterbox_bars_are_found(self):
        boxed = self.tmp / "boxed.mp4"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
                        "-i", "testsrc2=s=320x200:r=25:d=2", "-vf",
                        "pad=320:240:0:20:black", "-c:v", "libx264", "-preset",
                        "ultrafast", str(boxed)], check=True)
        w_, h_, x_, y_ = finish.active_area(str(boxed), 0.0, 2.0)
        self.assertEqual((w_, x_), (320, 0))
        self.assertTrue(196 <= h_ <= 204 and 18 <= y_ <= 22, (h_, y_))

    @unittest.skipUnless(shutil.which("fc-match"), "fontconfig not installed")
    def test_burned_captions_change_the_caption_band_only(self):
        family = subprocess.run(["fc-match", "-f", "%{family}", "sans"],
                                capture_output=True, text=True).stdout.split(",")[0]
        style = finish.load_style(None)
        style["captions"]["font"] = family
        words = [w("Record", 3.0, 3.4), w("once", 3.5, 3.9), w("ship", 4.0, 4.6)]
        plain, burned = self.tmp / "plain.mp4", self.tmp / "burned.mp4"
        # Same words for both so both clips snap to the same word boundaries;
        # only the second burns them into the picture.
        for dst, burn in ((plain, False), (burned, True)):
            rep = finish.finish(str(self.src), str(dst), style, trim_head=False,
                                loudness=False, words=words, burn=burn, keywords=[],
                                clip=(2.5, 5.5))
            self.assertEqual(rep["clip_snapped_to_words"], [2.92, 4.68])
        self.assertTrue(burned.with_suffix(".captions.srt").exists())

        def band(path, y0, y1):
            raw = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error",
                                  "-ss", "1.2", "-i", str(path), "-frames:v", "1",
                                  "-vf", f"crop=320:{y1 - y0}:0:{y0},format=gray",
                                  "-f", "rawvideo", "-"], capture_output=True).stdout
            return raw

        low_a, low_b = band(plain, 150, 200), band(burned, 150, 200)
        top_a, top_b = band(plain, 0, 40), band(burned, 0, 40)
        diff = sum(abs(a - b) for a, b in zip(low_a, low_b)) / max(len(low_a), 1)
        top = sum(abs(a - b) for a, b in zip(top_a, top_b)) / max(len(top_a), 1)
        self.assertGreater(diff, 5.0)     # captions landed in the lower band
        self.assertLess(top, diff / 4)    # and nowhere near the top


if __name__ == "__main__":
    unittest.main()
