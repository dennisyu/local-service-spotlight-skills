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
import re
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
               "2\n00:00:03,500 --> 00:00:04,000\n<i>Next</i>\n\n"
               "3\n00:00:04,000 --> 00:00:05,000\nDennis Yu: again\n")
        words = finish.words_from_srt(srt)
        self.assertEqual([x["word"] for x in words],
                         ["Hello", "there", "world", "Next", "again"])
        self.assertAlmostEqual(words[1]["start"], 1.6667, places=3)
        self.assertAlmostEqual(words[-2]["end"], 4.0)

    def test_scribe_spacing_and_events_are_ignored(self):
        data = {"words": [{"text": "Hi", "start": 0, "end": 0.2, "type": "word"},
                          {"text": " ", "start": 0.2, "end": 0.3, "type": "spacing"},
                          {"text": "(laughs)", "start": 0.3, "end": 0.9,
                           "type": "audio_event"},
                          {"text": "um", "start": 1.0, "end": 1.2, "type": "word"}]}
        self.assertEqual([x["word"] for x in finish.normalize_words(data)], ["Hi", "um"])

    def test_faster_whisper_segments(self):
        data = {"segments": [{"words": [{"word": " Go", "start": 0.1, "end": 0.3}]}]}
        self.assertEqual(finish.normalize_words(data),
                         [dict(w("Go", 0.1, 0.3), timing="word")])

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
        self.assertAlmostEqual(s, 0.42)   # "two" kept whole, never cut inside it
        self.assertAlmostEqual(e, 1.48)   # "three" plus pad, before "four"
        s, e = finish.snap_to_words(words, 0.88, 1.5, 0.08)
        self.assertAlmostEqual(s, 0.92)   # an edge in the last 50 ms of "two" skips it


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
        # 3 s of a 4 s clip is three quarters of it: the microphone died, a FAIL.
        self.assertEqual(checks["trailing_silence"], "FAIL")
        self.assertEqual(checks["pauses_over_fail"], "PASS")
        self.assertEqual(checks["black_frames"], "N/A")
        info = {"duration_s": 60.0, "audio": {"duration_s": 59.9}, "video": None}
        checks = {c["check"]: c["status"] for c in video_qa.evaluate(
            info, {"integrated_lufs": -14.0, "true_peak_dbtp": -2.0},
            [{"start": 56.9, "end": 59.9, "dur": 3.0}], [], video_qa.load_profile(None),
            first_audio=0.0)}
        self.assertEqual(checks["trailing_silence"], "WARN")   # 3 s of 60: untidy

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


class AuditRound2(unittest.TestCase):
    """Second independent audit, 23 Oct 2026: each test pins one finding."""

    def test_black_minimum_is_two_frames_at_the_files_rate(self):
        prof = video_qa.load_profile(None)
        self.assertEqual(video_qa.black_min_s(prof, 25.0), 0.06)
        self.assertEqual(video_qa.black_min_s(prof, 30.0), 0.05)   # 2 frames = 0.067 s
        self.assertEqual(video_qa.black_min_s(prof, 60.0), 0.025)  # 2 frames = 0.033 s
        self.assertEqual(video_qa.black_min_s(prof, None), 0.08)
        self.assertEqual(video_qa.black_min_s(prof, 12.0), 0.08)   # capped
        self.assertAlmostEqual(video_qa._rate("30000/1001"), 29.97, places=2)
        self.assertEqual(video_qa._rate("0/0"), 0.0)

    def test_a_click_is_not_a_start_but_a_split_word_is(self):
        # click at 0.30-0.305 s, then dead air until 4.0 s
        sil = [{"start": 0.0, "end": 0.3, "dur": 0.3}, {"start": 0.305, "end": 4.0,
                                                        "dur": 3.695}]
        self.assertEqual(video_qa.first_sustained_sound(sil, 10.0), 4.0)
        # "O-kay": 0.08 s syllable, 0.06 s stop, then the rest of the word
        sil = [{"start": 0.0, "end": 1.0, "dur": 1.0}, {"start": 1.08, "end": 1.14,
                                                        "dur": 0.06}]
        self.assertEqual(video_qa.first_sustained_sound(sil, 10.0), 1.0)
        self.assertIsNone(video_qa.first_sustained_sound(
            [{"start": 0.0, "end": 10.0, "dur": 10.0}], 10.0))
        self.assertEqual(video_qa.first_sustained_sound([], 10.0), 0.0)

    def test_noise_floor_raises_the_threshold_or_gives_up(self):
        prof = video_qa.load_profile(None)
        w = 0.01

        def talk(quiet):  # 0.3 s of talk then 0.2 s of quiet, for 20 s
            return ([-6.0] * 30 + [quiet] * 20) * 40

        clean = video_qa.classify_levels(talk(-120.0), w, prof, -15.0)
        self.assertEqual(max(clean["thresholds"]), -40.0)   # 25 LU under, not raised
        noisy = video_qa.classify_levels(talk(-30.0), w, prof, -15.0)
        self.assertEqual(max(noisy["thresholds"]), -24.0)   # 6 dB over the noise
        self.assertFalse(any(noisy["masked_blocks"]))
        self.assertEqual(noisy["state"][45], 0)              # the quiet is silence
        drowned = video_qa.classify_levels(talk(-14.0), w, prof, -15.0)
        self.assertTrue(all(drowned["masked_blocks"]))       # noise 8 dB under talk
        prof["pauses"]["silence_threshold_db"] = -45
        fixed = video_qa.classify_levels(talk(-30.0), w, prof, -15.0)
        self.assertEqual(max(fixed["thresholds"]), -45.0)    # a fixed threshold stays
        self.assertTrue(all(fixed["masked_blocks"]))

    def test_dense_talk_is_not_mistaken_for_noise(self):
        # Fast talk: 1.8 s of sound, one 60 ms gap at room level, repeated. The
        # first design (10th percentile of 2 s blocks) read this as a noise floor.
        prof = video_qa.load_profile(None)
        peaks = ([-8.0] * 180 + [-68.0] * 6) * 20
        cl = video_qa.classify_levels(peaks, 0.01, prof, -16.0)
        self.assertFalse(any(cl["masked_blocks"]))
        self.assertEqual(max(cl["thresholds"]), -41.0)

    def test_unmeasurable_pauses_warn_instead_of_passing(self):
        noise = {"measurable": False, "note": "the quiet parts sit within 3 dB"}
        checks = {c["check"]: c["status"] for c in video_qa.evaluate(
            {"duration_s": 60.0, "video": None},
            {"integrated_lufs": -14.0, "true_peak_dbtp": -2.0}, [], [],
            video_qa.load_profile(None), first_audio=0.0, noise=noise)}
        for name in ("hook_first_audio", "trailing_silence", "pauses_over_fail",
                     "pauses_over_warn_rate"):
            self.assertEqual(checks[name], "WARN", name)
        self.assertEqual(checks["black_frames"], "N/A")
        # with a transcript the hook is still judged on the first word
        checks = {c["check"]: c["status"] for c in video_qa.evaluate(
            {"duration_s": 60.0, "video": None},
            {"integrated_lufs": -14.0, "true_peak_dbtp": -2.0}, [], [],
            video_qa.load_profile(None), first_speech=0.4, noise=noise)}
        self.assertEqual(checks["hook_first_speech"], "PASS")

    def test_srt_sidecar_is_sanitised_like_the_ass(self):
        words = finish.normalize_words([
            {"word": "{\\b1}bold", "start": 0.0, "end": 0.4},
            {"word": "Line\\Nbreak", "start": 0.5, "end": 0.9},
            {"word": "line\nsecond", "start": 1.0, "end": 1.4},
            {"word": "<font color=red>red</font>", "start": 1.5, "end": 1.9}])
        self.assertEqual(words[2]["word"], "line second")
        cues = finish.chunk_words(words, dict(CAP, max_words=1))
        srt = finish.build_srt(cues, CAP)
        for bad in ("\\", "{", "}", "<font", "</font>"):
            self.assertNotIn(bad, srt)
        self.assertIn("LINE SECOND", srt)
        ass = finish.build_ass(cues, CAP, 320, 240)
        events = [l for l in ass.splitlines() if l.startswith("Dialogue:")]
        self.assertEqual(len(events), 4)                  # nothing split onto a new line
        self.assertTrue(all("SECOND" in l or "LINE SECOND" not in l for l in events))

    def test_hyphenated_keywords_light_up(self):
        words = [w("Run", 0, 1), w("a", 1, 2), w("Dollar-a-Day", 2, 3), w("test", 3, 4)]
        hot = [x["word"] for x in finish.mark_keywords(words, ["Dollar a Day"]) if x.get("hot")]
        self.assertEqual(hot, ["Dollar-a-Day"])
        hot = [x["word"] for x in finish.mark_keywords(words, ["a Day"]) if x.get("hot")]
        self.assertEqual(hot, [])                          # never half of a word

    def test_bad_inputs_are_one_plain_line_and_exit_2(self):
        import contextlib
        import io
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "x.mp4"
            src.write_bytes(b"not really a video")
            bad_words = Path(tmp) / "w.json"
            bad_words.write_text('[{"word": "hi", "end": 1.0}]')
            cases = [["--profile", str(Path(tmp) / "nope.json")],
                     ["--words", str(bad_words)],
                     ["--reframe", "9x16"], ["--focus-x", "1.5"], ["--clip", "5-2"]]
            for extra in cases:
                err = io.StringIO()
                with contextlib.redirect_stderr(err):
                    code = finish.main([str(src), "-o", str(Path(tmp) / "o.mp4")] + extra)
                self.assertEqual(code, 2, extra)
                self.assertEqual(len(err.getvalue().strip().splitlines()), 1, extra)
                self.assertNotIn("Traceback", err.getvalue())
            with self.assertRaisesRegex(ValueError, "entry 0 .*no 'start' time"):
                finish.read_words_file(str(bad_words))

    def test_audio_codec_follows_the_output_container(self):
        self.assertEqual(finish.audio_codec_args("o.wav", "aac", "192k", False),
                         ["-c:a", "pcm_s16le"])
        self.assertEqual(finish.audio_codec_args("o.wav", "pcm_s24le", "192k", True),
                         ["-c:a", "pcm_s24le"])
        self.assertEqual(finish.audio_codec_args("o.mp4", "aac", "192k", True),
                         ["-c:a", "copy"])
        self.assertEqual(finish.audio_codec_args("o.mp4", "pcm_s16le", "192k", True),
                         ["-c:a", "aac", "-b:a", "192k"])


class AuditRound3(unittest.TestCase):
    """Third independent audit, 23 Oct 2026: each test pins one finding."""

    def test_music_and_sound_cues_are_not_words(self):
        srt = ("WEBVTT\n\n00:00.000 --> 00:04.000\n[Music]\n\n"
               "00:04.000 --> 00:06.000 align:start\n(applause) Hello there\n\n"
               "00:06.000 --> 00:08,5\n♪ ♪\n")
        words = finish.words_from_srt(srt)
        self.assertEqual([x["word"] for x in words], ["Hello", "there"])
        self.assertEqual(words[0]["start"], 4.0)
        self.assertEqual(finish._ts("00:00:01,5"), 1.5)       # not 1.005
        self.assertEqual(finish.normalize_words(
            [{"word": "[Music]", "start": 0, "end": 4}, {"word": "Hi", "start": 4, "end": 5}]
        )[0]["word"], "Hi")
        self.assertFalse(finish.is_sound_tag("(and founder)"))  # real words stay

    def test_a_cough_or_typing_before_dead_air_is_not_the_start(self):
        hp = video_qa.load_profile(None)["hook"]
        cough = [(0.3, 0.55), (4.0, 9.0)]                     # 0.25 s, then 3.45 s quiet
        start, skipped, masked = video_qa.pick_start(cough, [], 9.0, hp, 2.0)
        self.assertEqual(start, 4.0)
        self.assertEqual(skipped[0]["at_s"], 0.3)
        typing = [(0.2 + i * 0.1, 0.215 + i * 0.1) for i in range(30)] + [(4.0, 9.0)]
        self.assertEqual(video_qa.pick_start(typing, [], 9.0, hp, 2.0)[0], 4.0)
        word = [(0.5, 0.75), (1.35, 3.0)]                      # "So," then the sentence
        self.assertEqual(video_qa.pick_start(word, [], 9.0, hp, 2.0)[0], 0.5)
        talk_then_dead = [(0.0, 3.0)]                          # never skip real talk
        self.assertEqual(video_qa.pick_start(talk_then_dead, [], 60.0, hp, 2.0)[0], 0.0)

    def test_trailing_dead_air_fails_when_the_microphone_dies(self):
        checks = {c["check"]: c for c in video_qa.evaluate(
            {"duration_s": 60.0, "audio": {"duration_s": 60.0}, "video": None},
            {"integrated_lufs": -14.0, "true_peak_dbtp": -2.0},
            [{"start": 3.0, "end": 60.0, "dur": 57.0}], [], video_qa.load_profile(None),
            first_audio=0.0)}
        self.assertEqual(checks["trailing_silence"]["status"], "FAIL")

    def test_late_start_hidden_by_music_still_fails(self):
        noise = {"hook_measurable": False, "hook_masked_from_s": 20.0, "masked_frac": 0.5,
                 "note": "music"}
        checks = {c["check"]: c["status"] for c in video_qa.evaluate(
            {"duration_s": 60.0, "video": None},
            {"integrated_lufs": -14.0, "true_peak_dbtp": -2.0}, [], [],
            video_qa.load_profile(None), first_audio=None, noise=noise)}
        self.assertEqual(checks["hook_first_audio"], "FAIL")
        measured = [c for c in video_qa.evaluate(
            {"duration_s": 60.0, "video": None},
            {"integrated_lufs": -14.0, "true_peak_dbtp": -2.0}, [], [],
            video_qa.load_profile(None), first_audio=None, noise=noise)
            if c["check"] == "hook_first_audio"][0]["measured"]
        self.assertEqual(measured, "≥ 20.00s")   # a lower bound, said as one

    def test_too_short_for_loudness_is_a_warning_not_silence(self):
        checks = {c["check"]: c["status"] for c in video_qa.evaluate(
            {"duration_s": 0.3, "audio": {"duration_s": 0.3}, "video": None},
            {"integrated_lufs": -70.0, "true_peak_dbtp": -6.0}, [], [],
            video_qa.load_profile(None), first_audio=0.0)}
        self.assertEqual(checks["integrated_loudness"], "WARN")

    def test_edge_flashes_are_labelled_by_where_they_are(self):
        prof = video_qa.load_profile(None)
        info = {"duration_s": 6.0, "video": {"width": 320, "height": 240, "fps": 30.0}}
        late = [{"start": 5.5, "end": 5.6, "dur": 0.1, "frames": 3, "first_frame": 165,
                 "kind": "black"}]
        c = {x["check"]: x["status"] for x in video_qa._video_checks(info, late, prof, None)}
        self.assertEqual(c["black_frames"], "FAIL")
        self.assertNotIn("black_close", c)
        early = [{"start": 0.067, "end": 0.133, "dur": 0.067, "frames": 2,
                  "first_frame": 2, "kind": "black"}]
        c = {x["check"]: x["status"] for x in video_qa._video_checks(info, early, prof, None)}
        self.assertEqual(c["black_frames"], "FAIL")
        self.assertNotIn("black_open", c)

    def test_caption_text_survives_and_srt_tags_cannot_form(self):
        cue = {"words": [w("x<b", 0, 1), w("y>z", 1, 2), w("vector<int>", 2, 3),
                         w("C++", 3, 4), w("{\\b1}bold", 4, 5), w("<i>it</i>", 5, 6)]}
        cap = dict(CAP, uppercase=False, highlight_numbers=False)
        srt = finish.build_srt([dict(cue, start=0.0, end=6.0)], cap)
        text = srt.splitlines()[2]
        self.assertNotIn("<", text)
        self.assertNotIn(">", text)
        self.assertIn("vector\u2039int\u203a", srt)
        self.assertIn("C++", srt)
        self.assertIn(" bold ", srt)            # override tag removed, word kept
        self.assertIn(" it", srt)
        ass = finish.cue_text(cue, cap, ass=True)
        self.assertNotIn("{\\b1}", ass)

    def test_keyword_forms_people_actually_write(self):
        words = [w("Dollar-a-Day's", 0, 1), w("GCT\u2019s", 1, 2),
                 w("Dollar\u2011a\u2011Days", 2, 3), w("today", 3, 4)]
        hot = [x["word"] for x in finish.mark_keywords(words, ["Dollar a Day", "GCT"])
               if x.get("hot")]
        self.assertEqual(hot, ["Dollar-a-Day's", "GCT\u2019s", "Dollar\u2011a\u2011Days"])

    def test_copy_only_into_containers_that_take_the_codec(self):
        self.assertEqual(finish.audio_codec_args("o.m4a", "mp3", "192k", True),
                         ["-c:a", "aac", "-b:a", "192k"])
        self.assertEqual(finish.audio_codec_args("o.mov", "opus", "192k", True),
                         ["-c:a", "aac", "-b:a", "192k"])
        self.assertEqual(finish.audio_codec_args("o.mkv", "opus", "192k", True),
                         ["-c:a", "copy"])

    def test_more_bad_inputs_are_plain_lines(self):
        import contextlib
        import io
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "x.mp4"
            src.write_bytes(b"x")
            prof = Path(tmp) / "p.json"
            prof.write_text('{"qa": {"loudness": {"target_lufs": "-14"}}}')
            for extra in (["--reframe", "9:0"], ["--reframe", "0:16"],
                          ["--profile", str(prof)]):
                err = io.StringIO()
                with contextlib.redirect_stderr(err):
                    code = finish.main([str(src), "-o", str(Path(tmp) / "o.mp4")] + extra)
                self.assertEqual(code, 2, extra)
                self.assertEqual(len(err.getvalue().strip().splitlines()), 1, extra)
            with self.assertRaisesRegex(ValueError, "target_lufs must be a number"):
                video_qa.load_profile(str(prof))


class AuditRound4(unittest.TestCase):
    """Fourth independent audit, 23 Oct 2026: each test pins one finding."""

    PROF = video_qa.load_profile(None)

    def test_a_click_or_noise_spike_does_not_split_a_dead_gap(self):
        talk = ([-6.0] * 30 + [-120.0] * 20) * 10       # 5 s of talk with short gaps
        gap = [-120.0] * 125 + [-6.0] * 2 + [-120.0] * 125  # 20 ms click mid-gap
        cl = video_qa.classify_levels(talk + gap + talk, 0.01, self.PROF, -15.0)
        longest = max((b - a) * 0.01 for s, a, b in video_qa._runs(cl["state"]) if s == 0)
        self.assertGreaterEqual(longest, 2.5)             # one gap, not two halves

    def test_a_steady_tone_or_hum_is_not_talk(self):
        tone = [-27.0, -26.8] * 250                       # 5 s, 0.2 dB of movement
        talk = ([-6.0] * 30 + [-120.0] * 20) * 10
        cl = video_qa.classify_levels(tone + talk, 0.01, self.PROF, -15.0)
        self.assertEqual(set(cl["state"][:450]), {0})      # the tone reads as silence
        self.assertEqual(cl["state"][500], 1)

    def test_a_minute_of_talk_that_never_breathes_is_unmeasurable(self):
        syllables = [-6.0] * 15 + [-45.0] * 5 + [-9.0] * 15 + [-120.0] * 5
        bed = ([-6.0] * 20 + [-30.0] * 15) * 1000          # 35 s, gaps filled by a bed
        cl = video_qa.classify_levels(bed, 0.01, self.PROF, -15.0)
        self.assertEqual(set(cl["state"]), {2})
        breathing = (syllables * 8 + [-120.0] * 40) * 12   # a 0.4 s breath every 3.6 s
        cl = video_qa.classify_levels(breathing, 0.01, self.PROF, -15.0)
        self.assertNotIn(2, set(cl["state"]))

    def test_typing_straight_into_talk_is_not_the_start(self):
        hp = self.PROF["hook"]
        typing = [(round(i * 0.18, 2), round(i * 0.18 + 0.01, 2)) for i in range(17)]
        talk = [(3.0 + i * 0.25, 3.0 + i * 0.25 + 0.125) for i in range(20)]
        start = video_qa.pick_start(typing + talk, [], 10.0, hp, 2.0)[0]
        self.assertGreaterEqual(start, 2.8)

    def test_a_transcript_cannot_hide_dead_air(self):
        checks = {c["check"]: c for c in video_qa.evaluate(
            {"duration_s": 10.0, "video": None},
            {"integrated_lufs": -14.0, "true_peak_dbtp": -2.0}, [], [], self.PROF,
            first_speech=0.05, first_audio=3.05)}
        self.assertEqual(checks["hook_first_speech"]["status"], "FAIL")
        self.assertIn("another cut", checks["hook_first_speech"]["note"])

    def test_talk_gaps_under_a_music_bed_are_flagged_with_a_transcript(self):
        words = [w("a", 0.0, 0.3), w("b", 0.4, 0.7), w("c", 3.5, 3.8)]
        checks = {c["check"]: c["status"] for c in video_qa.evaluate(
            {"duration_s": 10.0, "video": None},
            {"integrated_lufs": -14.0, "true_peak_dbtp": -2.0}, [], [], self.PROF,
            first_speech=0.0, first_audio=0.0, words=words)}
        self.assertEqual(checks["talk_gaps"], "WARN")

    def test_frame_one_flash_is_inside_the_video_at_any_rate(self):
        for fps in (30.0, 120.0):
            info = {"duration_s": 4.0, "video": {"width": 320, "height": 240, "fps": fps}}
            run = [{"start": 1 / fps, "end": 3 / fps, "dur": 2 / fps, "frames": 2,
                    "first_frame": 1, "last_frame": 2, "frame_count": int(4 * fps),
                    "kind": "black"}]
            c = {x["check"]: x["status"] for x in video_qa._video_checks(info, run, self.PROF,
                                                                       None)}
            self.assertEqual(c["black_frames"], "FAIL", fps)
            self.assertNotIn("black_open", c, fps)

    def test_matroska_duration_tag_is_an_end_time(self):
        st = {"tags": {"DURATION": "00:00:20.000000000"}}
        self.assertAlmostEqual(video_qa._tag_length(st, 0.8), 19.2)

    def test_caption_leftovers(self):
        cap = dict(CAP)
        words = [w("</b>", 0, 0.5), w("{\\b1}bold", 0.5, 1.0), w("C:\\path\\to", 1.0, 1.5)]
        srt = finish.build_srt(finish.chunk_words(words, dict(cap, max_words=1)), cap)
        self.assertNotIn("\n\n\n", srt)
        self.assertEqual(srt.count("-->"), 2)              # the tag-only word made no cue
        self.assertIn("C:\\PATH\\TO", srt)
        ass = finish.cue_text({"words": words}, cap, ass=True)
        self.assertNotIn("&H00FFFF", ass)                  # no digit left to highlight
        vtt = finish.words_from_srt("WEBVTT\n\n00:00.000 --> 00:01.000\nTom &amp; Jerry\n")
        self.assertEqual([x["word"] for x in vtt], ["Tom", "&", "Jerry"])
        for cue in ("(clapping)", "(door closes)", "（音楽）", "*music*"):
            self.assertTrue(finish.is_sound_tag(cue), cue)
        self.assertFalse(finish.is_sound_tag("*really*"))

    def test_utf16_and_empty_transcripts(self):
        import contextlib
        import io
        with tempfile.TemporaryDirectory() as tmp:
            u16 = Path(tmp) / "u16.srt"
            u16.write_text("1\n00:00:00,500 --> 00:00:02,000\nHello there\n", encoding="utf-16")
            self.assertEqual([x["word"] for x in finish.read_srt_file(str(u16))],
                             ["Hello", "there"])
            empty = Path(tmp) / "empty.srt"
            empty.write_text("")
            src = Path(tmp) / "x.mp4"
            src.write_bytes(b"x")
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                code = finish.main([str(src), "-o", str(Path(tmp) / "o.mp4"),
                                    "--srt", str(empty)])
            self.assertEqual(code, 2)
            self.assertIn("holds no words", err.getvalue())


class AuditRound5(unittest.TestCase):
    """Fifth independent audit, 24 Oct 2026: each test pins one finding."""

    PROF = video_qa.load_profile(None)
    # silence 1.5 s | a 0.3 s breath | silence 1.5 s, between two stretches of talk
    RUNS = [(1, 0.0, 2.0), (0, 2.0, 3.5), (1, 3.5, 3.8), (0, 3.8, 5.3), (1, 5.3, 8.0)]

    def test_a_breath_inside_dead_air_does_not_end_the_pause(self):
        words = [w("talk", 0.2, 1.9), w("again", 5.4, 7.9)]
        kind, spans = video_qa.talk_spans([dict(x, timing="word") for x in words])
        self.assertEqual(kind, "word")
        sure = video_qa.merge_pauses(self.RUNS, kind, spans, 0.6, ("none",))
        self.assertEqual([round(x["dur"], 2) for x in sure], [3.3])  # one 3.3 s pause
        said = words + [w("okay", 3.5, 3.8)]                         # a real one-word reply
        kind, spans = video_qa.talk_spans([dict(x, timing="word") for x in said])
        sure = video_qa.merge_pauses(self.RUNS, kind, spans, 0.6, ("none",))
        self.assertEqual([round(x["dur"], 2) for x in sure], [1.5, 1.5])

    def test_without_word_timing_the_stretch_is_flagged_not_failed(self):
        cue = [dict(w("talk", 0.0, 8.0), timing="cue", cue=1)]      # one cue over it all
        for words in (cue, None):
            kind, spans = video_qa.talk_spans(words)
            sure = video_qa.merge_pauses(self.RUNS, kind, spans, 0.6, ("none",))
            look = video_qa.merge_pauses(self.RUNS, kind, spans, 0.6, ("none", "unknown"))
            self.assertEqual(max(x["dur"] for x in sure), 1.5, kind)
            self.assertEqual(max(x["dur"] for x in look), 3.3, kind)
        checks = {c["check"]: c["status"] for c in video_qa.evaluate(
            {"duration_s": 8.0, "video": None},
            {"integrated_lufs": -14.0, "true_peak_dbtp": -2.0}, [], [], self.PROF,
            first_speech=0.0, first_audio=0.0,
            possible_pauses=[{"start": 2.0, "end": 5.3, "dur": 3.3, "joined": 1}])}
        self.assertEqual(checks["possible_pauses"], "WARN")

    def test_a_sound_outside_every_cue_is_not_talk(self):
        cues = [dict(w("a", 0.0, 2.0), timing="cue", cue=1),
                dict(w("b", 5.3, 8.0), timing="cue", cue=2)]
        kind, spans = video_qa.talk_spans(cues)
        self.assertEqual(kind, "cue")
        sure = video_qa.merge_pauses(self.RUNS, kind, spans, 0.6, ("none",))
        self.assertEqual(max(x["dur"] for x in sure), 3.3)

    def test_choppy_syllables_never_chain_into_a_pause(self):
        runs, t = [], 0.0
        for _ in range(40):                                         # 10 s of short bursts
            runs += [(1, t, t + 0.125), (0, t + 0.125, t + 0.25)]
            t += 0.25
        look = video_qa.merge_pauses(runs, "none", [], 0.6, ("none", "unknown"))
        self.assertLess(max(x["dur"] for x in look), 0.2)

    def test_gain_pumped_noise_inside_a_gap_is_silence(self):
        talk = ([-6.0] * 30 + [-120.0] * 20) * 10
        gap = [-55.0] * 60 + [-36.0, -35.0, -37.0, -36.0] * 30 + [-55.0] * 70  # lifted noise
        cl = video_qa.classify_levels(talk + gap + talk, 0.01, self.PROF, -15.0)
        longest = max((b - a) * 0.01 for s, a, b in video_qa._runs(cl["state"]) if s == 0)
        self.assertGreaterEqual(longest, 2.4)

    def test_brick_limited_talk_is_not_a_steady_tone(self):
        phrase = [-2.0, -1.7, -2.2, -1.9] * 50                       # 2 s pinned at -2 dBFS
        talk = (phrase + [-60.0] * 40) * 5                           # with real breaths
        cl = video_qa.classify_levels(talk, 0.01, self.PROF, -7.0)
        for k in range(5):
            middle = cl["state"][k * 240 + 20:k * 240 + 180]
            self.assertEqual(set(middle), {1}, k)                   # loud talk is talk

    def test_noise_like_sound_before_the_voice_is_not_the_start(self):
        hp = self.PROF["hook"]
        sound = [(0.12, 6.0)]                                       # typing runs into talk
        voice = [(3.19, 3.4), (3.45, 6.0)]
        start, skipped, _ = video_qa.pick_start(sound, [], 10.0, hp, 2.0, voice)
        self.assertEqual(start, 3.19)
        self.assertTrue(skipped[0]["no_voice"])
        start, skipped, _ = video_qa.pick_start([(0.1, 1.0), (4.0, 6.0)], [], 10.0, hp,
                                                2.0, [(4.1, 6.0)])
        self.assertEqual(start, 4.0)                                # the voiceless burst
        self.assertEqual(skipped[0]["at_s"], 0.1)                   # is skipped and listed
        start, _, _ = video_qa.pick_start([(0.5, 3.0)], [], 10.0, hp, 2.0, [(0.6, 3.0)])
        self.assertEqual(start, 0.5)                                # "s" before a vowel
        self.assertEqual(video_qa.pick_start([(0.5, 3.0)], [], 10.0, hp, 2.0, None)[0], 0.5)

    def test_hook_compares_the_transcript_with_what_is_audible(self):
        checks = {c["check"]: c for c in video_qa.evaluate(
            {"duration_s": 10.0, "video": None},
            {"integrated_lufs": -14.0, "true_peak_dbtp": -2.0}, [], [], self.PROF,
            first_speech=0.05, first_audio=3.29, noise={"first_any_sound_s": 0.05})}
        self.assertEqual(checks["hook_first_speech"]["status"], "PASS")  # "So" is audible
        self.assertNotIn("another cut", checks["hook_first_speech"]["note"])

    def test_tight_edit_is_unmeasurable_for_the_right_reason(self):
        syll = [-6.0] * 15 + [-30.0] * 3 + [-9.0] * 15 + [-45.0] * 2
        cl = video_qa.classify_levels(syll * 120, 0.01, self.PROF, -15.0)  # 42 s, no gap
        self.assertGreater(cl["gapless_masked_s"], 10.0)
        self.assertEqual(cl["noise_masked_s"], 0.0)

    def test_speaker_label_after_a_sound_cue_is_stripped(self):
        got = finish.words_from_srt(
            "1\n00:00:00,000 --> 00:00:02,000\n[Music] Dennis Yu: We start now\n\n"
            "2\n00:00:02,000 --> 00:00:03,000\nDennis Yu: Go\n")
        self.assertEqual([x["word"] for x in got], ["We", "start", "now", "Go"])
        self.assertTrue(all(x["timing"] == "cue" for x in got))

    def test_long_form_sidecar_reads_like_sentences(self):
        words = [w(f"word{i}", i * 0.3, i * 0.3 + 0.25) for i in range(60)]
        side = dict(CAP, **finish.DEFAULT_STYLE["sidecar_captions"])
        cues = finish.chunk_words(words, side)
        self.assertLessEqual(len(cues), 6)                          # not 20 three-word cues
        srt = finish.build_srt(cues, side)
        self.assertIn("word1", srt)                                 # not ALL CAPS
        self.assertTrue(all(len(line) <= 42 for line in srt.splitlines()))

    def test_letterbox_advice_fits_long_form(self):
        info = {"duration_s": 60.0, "video": {"width": 1920, "height": 1080, "fps": 30.0}}
        bars = {"top_bottom_px_total": 0, "side_px_total": 240}
        c = {x["check"]: x for x in video_qa._video_checks(info, [], self.PROF, bars)}
        self.assertIn("long-form", c["letterbox"]["note"])


class AuditRound6(unittest.TestCase):
    """Sixth independent audit, 24 Oct 2026: each test pins one finding."""

    PROF = video_qa.load_profile(None)

    def _kw(self, peak):
        return {"peak_of": lambda a, b: peak, "loud_db": -12.8 - 12.0}

    def test_a_mistimed_word_next_to_a_pause_does_not_join_it(self):
        # "panel," | 0.5 s | "but" (heard 0.8 s late by the ASR) | 1.0 s | "There"
        runs = [(1, 0.0, 1.0), (0, 1.0, 1.5), (1, 1.5, 2.0), (0, 2.0, 3.0), (1, 3.0, 4.0)]
        words = [dict(w("panel,", 0.4, 0.95), timing="word"),
                 dict(w("but", 2.3, 2.7), timing="word"),
                 dict(w("There", 3.0, 3.4), timing="word")]
        kind, spans = video_qa.talk_spans(words, 0.15, runs)
        loud = video_qa.merge_pauses(runs, kind, spans, 0.6, ("none",), **self._kw(-13.0))
        self.assertEqual(max(x["dur"] for x in loud), 1.0)          # a real word: no join
        quiet = video_qa.merge_pauses(runs, kind, spans, 0.6, ("none",), **self._kw(-31.0))
        self.assertEqual(max(x["dur"] for x in quiet), 2.0)         # a breath: one pause

    def test_an_interjection_only_descript_heard_is_still_talk(self):
        srt = ("1\n00:00:00,000 --> 00:00:01,000\nso this\n\n"
               "2\n00:00:02,000 --> 00:00:02,400\nYeah.\n\n"
               "3\n00:00:03,500 --> 00:00:04,500\nworks well\n")
        text = finish.words_from_srt(srt)
        timed = [w("so", 0.0, 0.4), w("this", 0.5, 0.9), w("works", 3.5, 3.9),
                 w("well", 4.0, 4.4)]
        caption = finish.align_text_to_timing(text, timed)
        self.assertNotIn("Yeah.", [x["word"] for x in caption])      # not caption text
        qa_words = finish.align_text_to_timing(text, timed, keep_unheard=True)
        yeah = [x for x in qa_words if x["word"] == "Yeah."]
        self.assertTrue(yeah and yeah[0]["caption"] is False)
        runs = [(1, 0.0, 0.9), (0, 0.9, 2.0), (1, 2.0, 2.4), (0, 2.4, 3.5), (1, 3.5, 4.4)]
        kind, spans = video_qa.talk_spans(qa_words, 0.15, runs)
        sure = video_qa.merge_pauses(runs, kind, spans, 0.6, ("none",), **self._kw(-30.0))
        self.assertLess(max(x["dur"] for x in sure), 2.0)
        self.assertEqual(video_qa.first_word_s(qa_words), 0.0)

    def test_a_word_stretched_back_over_a_pause_is_cut_to_its_sound(self):
        runs = [(1, 30.0, 31.55), (0, 31.55, 32.95), (1, 32.95, 33.35), (0, 33.35, 34.5),
                (1, 34.5, 35.0)]
        have = dict(w("have", 31.52, 34.74), timing="word")         # 3.2 s "word"
        self.assertEqual(video_qa.clamp_words([have], runs)[0]["start"], 34.5)
        partly = dict(w("have", 33.76, 35.14), timing="word")       # starts inside a gap
        self.assertEqual(video_qa.clamp_words([partly], runs)[0]["start"], 34.5)
        kind, spans = video_qa.talk_spans([dict(w("already", 31.0, 31.52), timing="word"),
                                           have], 0.15, runs)
        sure = video_qa.merge_pauses(runs, kind, spans, 0.6, ("none",), **self._kw(-30.0))
        self.assertGreaterEqual(max(x["dur"] for x in sure), 2.9)   # the soft "mm" is not talk

    def test_the_hook_waits_for_the_first_audible_sound(self):
        checks = {c["check"]: c for c in video_qa.evaluate(
            {"duration_s": 10.0, "video": None},
            {"integrated_lufs": -14.0, "true_peak_dbtp": -2.0}, [], [], self.PROF,
            first_speech=1.9, first_audio=2.29, noise={"first_any_sound_s": 2.29})}
        self.assertEqual(checks["hook_first_speech"]["status"], "FAIL")
        self.assertEqual(checks["hook_first_speech"]["measured"], "2.29s")

    def test_talk_gaps_allow_for_early_word_clocks(self):
        words = [dict(w("a", 0.0, 1.0), timing="word"), dict(w("b", 2.7, 3.0), timing="word")]

        def gaps(silences):
            c = {x["check"]: x for x in video_qa.evaluate(
                {"duration_s": 10.0, "video": None},
                {"integrated_lufs": -14.0, "true_peak_dbtp": -2.0}, silences, [],
                self.PROF, first_speech=0.0, first_audio=0.0, words=words)}
            return c.get("talk_gaps", {}).get("status")
        self.assertEqual(gaps([]), "WARN")                           # 1.7 s under a bed
        self.assertIsNone(gaps([{"start": 1.0, "end": 2.6, "dur": 1.6}]))  # a real pause
        self.assertEqual(gaps([{"start": 1.0, "end": 1.7, "dur": 0.7},     # a long sigh
                               {"start": 2.0, "end": 2.6, "dur": 0.6}]), "WARN")

    def test_our_null_muxer_is_not_the_files_fault(self):
        err = ("[null @ 0x55] Application provided invalid, non monotonically increasing "
               "dts to muxer in stream 0: 50 >= 50\n[h264 @ 0x56] error while decoding MB\n")
        self.assertEqual(video_qa.file_errors(err, r"error|invalid"),
                         ["[h264 @ 0x56] error while decoding MB"])

    def test_noise_like_means_flatter_than_the_room(self):
        state = bytearray([0] * 100 + [1] * 50)
        peaks = [-40.0] * 150
        hiss = [0.85] * 100
        talk_under_hiss = video_qa._tonal_windows(state, peaks, hiss + [0.6] * 50, 0.01,
                                                  0.3, 0.15)
        self.assertTrue(all(talk_under_hiss[100:]))
        typing = video_qa._tonal_windows(state, peaks, [0.7] * 100 + [0.85] * 50, 0.01,
                                         0.3, 0.15)
        self.assertFalse(any(typing[100:]))

    def test_more_speaker_label_forms(self):
        srt = ("1\n00:00:00,000 --> 00:00:02,000\nSpeaker 1: one\n\n"
               "2\n00:00:02,000 --> 00:00:04,000\nDennis Yu (Host): two\n\n"
               "3\n00:00:04,000 --> 00:00:06,000\n>> DENNIS: three >> four\n\n"
               "4\n00:00:06,000 --> 00:00:08,000\nStep 1: open it\n")
        self.assertEqual([x["word"] for x in finish.words_from_srt(srt)],
                         ["one", "two", "three", "four", "Step", "1:", "open", "it"])

    def test_sidecar_lines_fit_and_short_sentences_merge(self):
        side = dict(CAP, **finish.DEFAULT_STYLE["sidecar_captions"])
        long = ["extraordinarily", "comprehensive", "understanding", "of", "everything"]
        words = [w(t, i * 0.4, i * 0.4 + 0.35) for i, t in enumerate(long * 4)]
        srt = finish.build_srt(finish.chunk_words(words, side), side)
        body = [l for l in srt.splitlines() if l and "-->" not in l and not l.isdigit()]
        self.assertTrue(all(len(l) <= 42 for l in body), body)
        talk = [w("Okay.", 0.0, 0.3), w("So", 0.3, 0.5), w("here", 0.5, 0.8),
                w("we", 0.8, 1.0), w("go.", 1.0, 1.4)]
        self.assertEqual(len(finish.chunk_words(talk, side)), 1)

    def test_transcription_cache_knows_the_model_and_leaves_no_temp_file(self):
        import contextlib
        import io
        tw = _load("transcribe_words")
        with tempfile.TemporaryDirectory() as tmp:
            media = Path(tmp) / "not_media.mp4"
            media.write_bytes(b"not media")
            out = Path(tmp) / "w.json"
            out.write_text(json.dumps({"backend": "local", "model": "tiny.en", "words": [],
                                       "media_key": tw.media_key(str(media), 0.0, 0.0)}))
            before = set(Path(tempfile.gettempdir()).glob("tmp*.wav"))
            with contextlib.redirect_stdout(io.StringIO()), \
                    contextlib.redirect_stderr(io.StringIO()):
                code = tw.main([str(media), "-o", str(out), "--model", "small.en"])
            self.assertEqual(code, 2)                                # not served from cache
            self.assertEqual(set(Path(tempfile.gettempdir()).glob("tmp*.wav")), before)


class AuditRound7(unittest.TestCase):
    """Seventh independent audit, 24 Oct 2026: each test pins one finding."""

    PROF = video_qa.load_profile(None)

    def _ev(self, **kw):
        base = dict(first_speech=0.0, first_audio=0.0)
        base.update(kw)
        return {c["check"]: c for c in video_qa.evaluate(
            {"duration_s": 60.0, "video": None},
            {"integrated_lufs": -14.0, "true_peak_dbtp": -2.0}, kw.pop("silences", []),
            [], self.PROF, **{k: v for k, v in base.items() if k != "silences"})}

    def test_a_crowd_that_keeps_the_level_up_still_shows_a_stop(self):
        words = [dict(w("200?", 30.0, 32.8), timing="word"), dict(w("If", 36.4, 36.8), timing="word")]
        crowd = [(32.8, 33.6), (33.65, 35.9), (35.95, 36.4)]          # peaks as loud as talk
        c = self._ev(words=words, loud_runs=crowd)
        self.assertEqual(c["talk_gaps"]["status"], "WARN")
        short = [dict(w("a", 30.0, 32.8), timing="word"), dict(w("b", 34.8, 35.2), timing="word")]
        self.assertNotIn("talk_gaps", self._ev(words=short, loud_runs=[(32.8, 34.8)]))

    def test_the_srt_opening_survives_an_asr_that_missed_it(self):
        srt = ("1\n00:00:00,400 --> 00:00:03,500\nSo think about how easy it is\n\n"
               "2\n00:00:04,000 --> 00:00:05,000\nWhy are we\n")
        timed = [w("Why", 4.0, 4.3), w("are", 4.3, 4.5), w("we", 4.5, 4.8)]
        out = finish.align_text_to_timing(finish.words_from_srt(srt), timed, keep_unheard=True)
        self.assertEqual(out[0]["word"], "So")
        self.assertEqual((out[0]["timing"], out[0]["heard"], out[0].get("caption", True)),
                         ("cue", False, True))
        self.assertEqual(video_qa.first_word_s(out), 0.4)

    def test_words_only_the_asr_heard_are_talk_not_captions(self):
        srt = "1\n00:00:00,000 --> 00:00:02,000\nhello there\n"
        timed = [w("hello", 0.0, 0.4), w("there", 0.5, 0.9), w("is", 1.6, 1.8),
                 w("it", 1.8, 2.0)]
        out = finish.align_text_to_timing(finish.words_from_srt(srt), timed, keep_unheard=True)
        extra = [x for x in out if x["word"] in ("is", "it")]
        self.assertTrue(extra and all(x["heard"] and x["caption"] is False for x in extra))
        kind, spans = video_qa.talk_spans(out, 0.15)
        self.assertTrue(any(a <= 1.7 <= b and sure for a, b, sure in spans))

    def test_a_loud_cough_right_after_a_word_is_listed(self):
        runs = [(1, 30.0, 32.8), (0, 32.8, 33.05), (1, 33.05, 33.95), (0, 33.95, 35.84),
                (1, 35.84, 37.0)]
        words = [dict(w("200?", 32.3, 32.8), timing="word"), dict(w("If", 35.85, 36.2), timing="word")]
        kind, spans = video_qa.talk_spans(words, 0.15, runs)
        kw = {"peak_of": lambda a, b: -14.0, "loud_db": -24.8}
        sure = video_qa.merge_pauses(runs, kind, spans, 0.6, ("none",), **kw)
        look = video_qa.merge_pauses(runs, kind, spans, 0.6, ("none", "unknown"), **kw)
        self.assertLess(max(x["dur"] for x in sure), 2.0)              # not failed
        self.assertGreaterEqual(max(x["dur"] for x in look), 2.8)      # but listed

    def test_the_pause_rate_is_a_note_until_the_edit_enforces_it(self):
        many = [{"start": 1.0 + i * 3, "end": 1.7 + i * 3, "dur": 0.7} for i in range(12)]
        c = self._ev(silences=many)
        self.assertEqual(c["pauses_over_warn_rate"]["status"], "NOTE")
        strict = video_qa.deep_merge(self.PROF, {"pauses": {"rate_advisory": False}})
        c = {x["check"]: x["status"] for x in video_qa.evaluate(
            {"duration_s": 60.0, "video": None},
            {"integrated_lufs": -14.0, "true_peak_dbtp": -2.0}, many, [], strict,
            first_speech=0.0, first_audio=0.0)}
        self.assertEqual(c["pauses_over_warn_rate"], "WARN")
        self.assertEqual(video_qa.verdict_for(["PASS", "NOTE"]), "PASS")

    def test_an_srt_for_another_cut_is_named(self):
        words = [dict(w("a", i, i + 0.3), timing="cue" if i % 5 else "word",
                      heard=not i % 5) for i in range(20)]
        c = self._ev(words=words)
        self.assertEqual(c["transcript_match"]["status"], "WARN")

    def test_a_label_on_one_line_is_text(self):
        srt = ("1\n00:00:00,000 --> 00:00:02,000\nRemember: this matters\n\n"
               "2\n00:00:02,000 --> 00:00:04,000\nGoogle: the answer\n")
        self.assertEqual([x["word"] for x in finish.words_from_srt(srt)][:2],
                         ["Remember:", "this"])

    def test_long_tokens_and_pauses_in_the_sidecar(self):
        url = "https://blitzmetrics.com/a-very-long-path/that-keeps-going/and-going"
        self.assertTrue(all(len(l) <= 42 for l in finish._wrap(url, 42).splitlines()))
        side = dict(CAP, **finish.DEFAULT_STYLE["sidecar_captions"])
        talk = [w("Okay.", 0.0, 0.3), w("So", 2.1, 2.3), w("here", 2.3, 2.6),
                w("we", 2.6, 2.8), w("go.", 2.8, 3.4)]
        self.assertEqual(len(finish.chunk_words(talk, side)), 2)      # 1.8 s apart

    def test_a_loud_steady_hum_holds_no_talk(self):
        talk = ([-6.0] * 30 + [-120.0] * 20) * 10
        hum = [-13.0, -12.8] * 400                                     # 8 s, 7 dB under talk
        cl = video_qa.classify_levels(talk + hum + talk, 0.01, self.PROF, -15.0)
        self.assertEqual(set(cl["state"][800:1000]), {0})              # silence, not masked

    def test_a_loud_bed_under_the_opening_is_audible(self):
        import random
        rnd = random.Random(3)
        bed = [rnd.choice([-4.0, -6.0, -9.0, -5.0]) for _ in range(400)]  # 4 s, moving
        peaks = bed + ([-6.0] * 30 + [-120.0] * 20) * 40
        scan = {"peaks": peaks, "window_s": 0.01, "decoded_s": len(peaks) * 0.01,
                "errors": [], "flatness": None}
        aud = video_qa.analyze_audio(None, self.PROF, scan=scan, integrated_lufs=-12.0)
        self.assertGreater(aud["noise"]["masked_s"], 1.0)
        self.assertEqual(aud["noise"]["first_any_sound_s"], 0.0)     # talk may be under it


class AuditRound8(unittest.TestCase):
    """Eighth independent audit, 24 Oct 2026: each test pins one finding."""

    PROF = video_qa.load_profile(None)
    TALK = [-6.0] * 30 + [-120.0] * 20

    def test_room_noise_lifted_into_the_next_word_is_silence(self):
        import random
        rnd = random.Random(5)
        ramp = [-60.0 + i for i in range(30)]                          # auto-gain attack
        lift = [-31.0 + rnd.uniform(-2, 2) for _ in range(200)]        # 2 s, 25 dB under
        peaks = self.TALK * 10 + [-62.0] * 15 + ramp + lift + self.TALK * 10
        st = video_qa.classify_levels(peaks, 0.01, self.PROF, -16.0)["state"]
        gap = st[515:745]                                              # one run with the word
        self.assertGreater(gap.count(0), 200)

    def test_talk_level_is_counted_window_by_window(self):
        peaks = [-30.0] * 200 + [-5.0] * 50                            # noise, then a word
        spans = video_qa.talk_loud_spans([(1, 0.0, 2.5)], peaks, 0.01, 0.0, -14.0)
        self.assertEqual(len(spans), 1)
        self.assertGreaterEqual(spans[0][0], 1.8)                      # not the whole run

    def test_a_soft_word_under_noise_is_not_bridged_away(self):
        chain = ([1] * 4 + [0] * 3) * 10                               # a word's peaks, flickering
        peaks = [-70.0] * 60 + [-40.0 if x else -70.0 for x in chain] + [-70.0] * 60
        st = bytearray([0] * 60 + chain + [0] * 60)
        heard = video_qa._talk_guard(len(st), peaks, [(55, 135)], -20.0, 15)  # a soft word
        video_qa._bridge_blips(st, 8, heard)
        self.assertEqual(st[60:130].count(1), 40)
        click = bytearray([0] * 50 + [1] * 5 + [0] * 50 + [1] * 30)
        video_qa._bridge_blips(click, 8, video_qa._talk_guard(135, [-10.0] * 135,
                                                              [(110, 135)], -20.0, 15))
        self.assertEqual(click[50:55].count(1), 0)                     # a click still is
        # A word the ASR stretched back over a pause (talk-level sound only at its
        # end) vouches for nothing before that sound: the bed's flicker is a pause.
        bed = bytearray(([0] * 2 + [1] * 3) * 40 + [1] * 30)
        peaks = [-45.0] * 200 + [-10.0] * 30
        video_qa._bridge_blips(bed, 8, video_qa._talk_guard(230, peaks, [(50, 230)], -20.0, 15))
        self.assertEqual(bed[0:180].count(1), 0)

    def test_an_untitled_chapter_track_is_not_a_decode_error(self):
        line = "[mov,mp4,m4a,3gp,3g2,mj2 @ 0x55] Referenced QT chapter track not found"
        self.assertEqual(video_qa.file_errors(line + "\n"), [])
        self.assertTrue(video_qa.file_errors("[aac @ 0x1] Error decoding AAC frame\n"))

    def test_descripts_label_on_the_first_cue_only_is_stripped(self):
        srt = ("1\n00:00:00,000 --> 00:00:02,000\nDennis: So everything we\n\n"
               "2\n00:00:02,000 --> 00:00:04,000\nwere doing here\n\n"
               "3\n00:00:04,000 --> 00:00:05,000\nBob Smith: Yeah\n\n"
               "4\n00:00:05,000 --> 00:00:06,000\nDennis: and so\n\n"
               "5\n00:00:06,000 --> 00:00:07,000\nBob Smith: Right\n")
        self.assertEqual([x["word"] for x in finish.words_from_srt(srt)],
                         ["So", "everything", "we", "were", "doing", "here", "Yeah",
                          "and", "so", "Right"])

    def test_more_label_shapes(self):
        for lab in ("SPEAKER 1:", "dennis yu:", "Ludwig van Beethoven:"):
            srt = (f"1\n00:00:00,000 --> 00:00:02,000\n{lab} hello there\n\n"
                   f"2\n00:00:02,000 --> 00:00:04,000\n{lab} and more\n")
            self.assertEqual([x["word"] for x in finish.words_from_srt(srt)][:2],
                             ["hello", "there"], lab)

    def test_a_hum_as_loud_as_the_talk_keeps_the_pause_edges(self):
        hum = [-15.0 + (0.2 if i % 2 else 0.0) for i in range(250)]
        talk = [-6.0] * 30 + [-15.0] * 20                              # syllables over the hum
        peaks = talk * 20 + [-6.0] * 25 + hum + [-6.0] * 5 + talk * 20
        st = video_qa.classify_levels(peaks, 0.01, self.PROF, -14.0)["state"]
        longest = max(b - a for s, a, b in video_qa._runs(st) if s == 0)
        self.assertGreaterEqual(longest, 245)                          # 2.5 s, not 2.0

    def test_a_cough_kept_before_an_early_first_word_is_a_warn(self):
        c = {x["check"]: x for x in video_qa.evaluate(
            {"duration_s": 60.0, "video": None},
            {"integrated_lufs": -14.0, "true_peak_dbtp": -2.0}, [], [], self.PROF,
            first_speech=1.58, first_audio=0.08,
            noise={"first_any_sound_s": 0.08, "hook_measurable": True})}
        self.assertEqual(c["hook_first_speech"]["status"], "WARN")
        self.assertIn("cough", c["hook_first_speech"]["note"])

    def test_a_loud_cough_attached_to_a_word_is_listed(self):
        runs = [(1, 30.0, 33.7), (0, 33.7, 35.69), (1, 35.69, 37.0)]  # "200?"+cough, 1.99 s
        words = [dict(w("200?", 32.3, 32.8), timing="word"),
                 dict(w("If", 35.7, 36.0), timing="word")]
        kind, spans = video_qa.talk_spans(words, 0.15, runs)
        runs = video_qa.split_word_edges(runs, spans, 0.4, lambda a, b: True)
        kw = {"peak_of": lambda a, b: -10.0, "loud_db": -20.0}
        sure = video_qa.merge_pauses(runs, kind, spans, 0.6, ("none",), **kw)
        look = video_qa.merge_pauses(runs, kind, spans, 0.6, ("none", "unknown"), **kw)
        self.assertLess(max(x["dur"] for x in sure), 2.0)
        self.assertGreaterEqual(max(x["dur"] for x in look), 2.5)

    def test_word_rules_stay_where_the_words_file_reaches(self):
        runs = [(1, 0.0, 10.0), (0, 10.0, 11.0), (1, 11.0, 12.0), (0, 12.0, 13.2),
                (1, 13.2, 14.0)]
        far = [(5.0, 6.0, True)]                                       # heard words, far off
        inside = video_qa.merge_pauses(runs, "word", far, 0.6, ("none",))
        outside = video_qa.merge_pauses(runs, "word", far, 0.6, ("none",),
                                        cover=video_qa.word_cover([(5.0, 6.0)], 2.5))
        self.assertGreaterEqual(max(x["dur"] for x in inside), 3.0)    # a 1 s sigh joins
        self.assertLess(max(x["dur"] for x in outside), 2.0)           # cue rules: it doesn't

    def test_a_string_where_true_or_false_belongs_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "style.json"
            p.write_text(json.dumps({"qa": {"pauses": {"rate_advisory": "false"}}}))
            with self.assertRaises(ValueError) as cm:
                video_qa.load_profile(str(p))
        self.assertIn("rate_advisory", str(cm.exception))

    def test_a_token_wider_than_the_frame_is_shrunk_to_fit(self):
        cue = {"start": 0.0, "end": 1.0, "words": [w("localservicespotlight.com", 0.0, 1.0)]}
        ass = finish.build_ass([cue], CAP, 1080, 1920)
        m = re.search(r"\{\\fs(\d+)\}", ass)
        self.assertIsNotNone(m)
        room = 1080 - 2 * round(1080 * 0.06)
        self.assertLessEqual(finish._text_px("LOCALSERVICESPOTLIGHT.COM", CAP["font"],
                                             CAP["bold"], int(m.group(1))), room)
        short = {"start": 0.0, "end": 1.0, "words": [w("hello", 0.0, 1.0)]}
        self.assertNotIn("\\fs", finish.build_ass([short], CAP, 1080, 1920).split("[Events]")[1])


class AuditRound9(unittest.TestCase):
    """Ninth independent audit, 24 Oct 2026: each test pins one finding."""

    PROF = video_qa.load_profile(None)

    def test_a_clip_start_moves_back_into_the_silence_before_the_sound(self):
        runs = [(1, 0.0, 4.0), (0, 4.0, 4.6), (1, 4.6, 8.0)]          # talk resumes at 4.6
        cut, ok = finish.settle_start(runs, 5.4, 3.9, 5.32, 0.08)      # word clock 0.8 s late
        self.assertTrue(ok)
        self.assertAlmostEqual(cut, 4.52, places=2)
        # The previous word ends after that silence: no pause to move to.
        cut, ok = finish.settle_start(runs, 5.4, 4.7, 5.32, 0.08)
        self.assertFalse(ok)
        self.assertEqual(cut, 5.32)
        # A start already in the silence before the word stays in it.
        quiet = [(1, 0.0, 4.0), (0, 4.0, 5.38), (1, 5.38, 8.0)]
        cut, ok = finish.settle_start(quiet, 5.4, 3.9, 5.32, 0.08)
        self.assertTrue(ok and 4.0 <= cut <= 5.32)

    def test_a_clip_end_moves_on_to_the_silence_after_the_sound(self):
        runs = [(1, 0.0, 10.6), (0, 10.6, 11.4), (1, 11.4, 14.0)]      # "foundation." ends 10.6
        cut, ok = finish.settle_end(runs, 10.0, 11.5, 10.08, 0.08)     # ASR said 10.0
        self.assertTrue(ok)
        self.assertAlmostEqual(cut, 10.68, places=2)
        cut, ok = finish.settle_end(runs, 10.0, 10.3, 10.08, 0.08)     # next word at 10.3
        self.assertFalse(ok)

    def test_an_early_word_clock_keeps_or_moves_the_edge_into_the_pause(self):
        early = [(1, 0.0, 3.0), (0, 3.0, 3.6), (1, 3.6, 5.0)]         # sound at 3.6, clock 3.2
        self.assertEqual(finish.settle_start(early, 3.2, 2.5, 3.12, 0.08), (3.12, True))
        tail = [(1, 0.0, 3.15), (0, 3.15, 3.6), (1, 3.6, 5.0)]        # 3.12 is in the last tail
        cut, ok = finish.settle_start(tail, 3.2, 2.5, 3.12, 0.08)
        self.assertTrue(ok)
        self.assertAlmostEqual(cut, 3.52, places=2)
        late_end = [(1, 0.0, 1.375), (0, 1.375, 2.0)]                 # the clock ends at 1.45
        self.assertEqual(finish.settle_end(late_end, 1.45, 2.0, 1.53, 0.08), (1.53, True))
        silent = [(0, 0.0, 3.0)]
        self.assertTrue(finish.settle_start(silent, 0.5, 0.0, 0.42, 0.08)[1])
        self.assertTrue(finish.settle_end(silent, 1.45, 3.0, 1.53, 0.08)[1])

    def test_a_clip_at_a_pause_keeps_the_word_the_asr_stretched_back_over_it(self):
        class Levels:                                                  # the source's level runs
            total = 20.0

            def near(self, t):
                return [(1, 0.0, 5.0), (0, 5.0, 6.2), (1, 6.2, 6.6), (0, 6.6, 7.5),
                        (1, 7.5, 20.0)]
        words = [dict(w("is", 4.6, 5.0), timing="word", heard=True),
                 dict(w("We're", 5.05, 6.3), timing="word", heard=True),  # back over the pause
                 dict(w("not", 6.3, 6.5), timing="word", heard=True),
                 dict(w("next", 7.5, 7.9), timing="word", heard=True)]
        rep = {"warnings": []}
        ws, s, e = finish.place_clip(Levels(), words, 6.15, 6.6, 0.08, 0.4, rep)
        self.assertEqual(rep["warnings"], [])
        self.assertTrue(5.0 < s < 6.2)                                 # "We're" is in the clip
        self.assertEqual(next(x for x in ws if x["word"] == "We're")["start"], 6.2)
        self.assertAlmostEqual(e, 6.68, places=2)                      # "not" ends at 6.6

    def test_a_word_clocked_in_the_pause_after_it_keeps_its_sound(self):
        # The replay's "And" (said 1518.73-1519.19) was timed 1519.3, inside the
        # pause after it; "what's" claims the sound after the pause.
        runs = [(1, 1515.9, 1518.06), (0, 1518.06, 1518.73), (1, 1518.73, 1519.19),
                (0, 1519.19, 1520.22), (1, 1520.22, 1522.0)]
        cut, ok = finish.settle_start(runs, 1519.3, 1517.82, 1519.22, 0.08, nxt=1519.86)
        self.assertTrue(ok)
        self.assertAlmostEqual(cut, 1518.65, places=2)
        # Without a next word claiming that sound, the word is the sound after.
        self.assertEqual(finish.settle_start(runs, 1519.3, 1517.82, 1519.22, 0.08,
                                             nxt=1521.0)[0], 1519.22)

    def test_only_a_word_whose_clock_starts_in_silence_is_clamped(self):
        runs = [(0, 0.0, 3.04), (1, 3.04, 3.4), (0, 3.4, 4.23), (1, 4.23, 4.86)]
        words = [dict(w("Wow", 2.64, 3.3), timing="word", heard=True),     # early, in silence
                 dict(w("that's", 3.3, 4.46), timing="word", heard=True)]  # back over 0.83 s
        got = finish.clamp_stretched(words, runs, 0.4)
        self.assertEqual(got[0]["start"], 3.04)
        self.assertEqual(got[1]["start"], 4.23)
        tail = [dict(w("Wow", 3.04, 4.1), timing="word", heard=True)]   # runs on over a pause
        self.assertEqual(finish.clamp_stretched(tail, runs, 0.4)[0]["start"], 3.04)

    def test_a_zero_length_edge_word_does_not_pin_the_cut_inside_it(self):
        words = [w("local.", 2061.48, 2061.88), w("Helping.", 2063.12, 2063.12),
                 w("We", 2063.46, 2063.46)]
        s, e = finish.snap_to_words(words, 2050.0, 2063.256, 0.08)
        self.assertGreater(e, 2063.12)

    def test_tip_and_take_openers_are_not_speaker_labels(self):
        srt = ("1\n00:00:00,500 --> 00:00:03,000\nPro Tip: reply to every review.\n\n"
               "2\n00:00:03,100 --> 00:00:06,000\nIt takes two minutes a day.\n\n"
               "3\n00:00:06,100 --> 00:00:09,000\nGoogle Maps: that is where they find you.\n\n"
               "4\n00:00:09,100 --> 00:00:12,000\nHot Take: most agencies skip it.\n")
        got = [x["word"] for x in finish.words_from_srt(srt)]
        for word in ("Pro", "Tip:", "Google", "Maps:", "Hot", "Take:"):
            self.assertIn(word, got)
        labelled = ("1\n00:00:00,000 --> 00:00:02,000\nDennis: So open\n\n"
                    "2\n00:00:02,000 --> 00:00:04,000\nGoogle Maps: and search\n")
        self.assertEqual([x["word"] for x in finish.words_from_srt(labelled)],
                         ["So", "open", "Google", "Maps:", "and", "search"])

    def test_channel_peaks_are_read_from_astats(self):
        err = ("[Parsed_astats_0 @ 0x1] Channel: 1\n[Parsed_astats_0 @ 0x1] Peak level dB: -8.1\n"
               "[Parsed_astats_0 @ 0x1] Channel: 2\n[Parsed_astats_0 @ 0x1] Peak level dB: -inf\n"
               "[Parsed_astats_0 @ 0x1] Overall\n[Parsed_astats_0 @ 0x1] Peak level dB: -8.1\n")
        self.assertEqual(finish.astats_peaks(err), [-8.1, -120.0])
        self.assertEqual(finish._kbps("192k"), 192.0)

    def test_a_pause_near_the_line_under_room_noise_is_listed_not_failed(self):
        c = {x["check"]: x for x in video_qa.evaluate(
            {"duration_s": 60.0, "video": None},
            {"integrated_lufs": -14.0, "true_peak_dbtp": -2.0},
            [{"start": 20.0, "end": 22.12, "dur": 2.12, "near_fail": 8.3},
             {"start": 40.0, "end": 41.0, "dur": 1.0}], [], self.PROF, first_speech=0.3)}
        self.assertEqual(c["pauses_over_fail"]["status"], "PASS")
        self.assertEqual(c["pauses_near_fail"]["status"], "WARN")
        self.assertIn("+8.3 dB", c["pauses_near_fail"]["note"])

    def test_a_stop_filled_with_pumped_hiss_is_a_talk_gap(self):
        words = [dict(w("end.", 9.0, 10.0), timing="word", heard=True),
                 dict(w("Next", 12.4, 12.8), timing="word", heard=True)]
        sil = [{"start": 10.5, "end": 11.8, "dur": 1.3}]               # the gain cut it short
        kw = dict(first_speech=0.3, words=words, loud_runs=[(10.0, 12.4)])
        hiss = {x["check"]: x for x in video_qa.evaluate(
            {"duration_s": 60.0, "video": None}, {"integrated_lufs": -14.0,
                                                   "true_peak_dbtp": -2.0},
            sil, [], self.PROF, voiced_runs=[], **kw)}
        self.assertEqual(hiss["talk_gaps"]["status"], "WARN")
        talk = {x["check"]: x for x in video_qa.evaluate(
            {"duration_s": 60.0, "video": None}, {"integrated_lufs": -14.0,
                                                   "true_peak_dbtp": -2.0},
            sil, [], self.PROF, voiced_runs=[(10.0, 12.4)], **kw)}
        self.assertNotIn("talk_gaps", talk)                            # a voice in the gap

    def test_a_partial_words_file_does_not_join_pauses_past_its_reach(self):
        runs = [(1, 0.0, 30.0), (0, 30.0, 31.0), (1, 31.0, 31.3), (0, 31.3, 32.4),
                (1, 32.4, 40.0)]
        spans = [(1.0, 2.0, True)]                                     # words for the start only
        cover = video_qa.word_cover([(1.0, 2.0)], 2.5)
        no_srt = video_qa.merge_pauses(runs, "word", spans, 0.6, ("none",), cover=cover,
                                       cues=False)
        self.assertLess(max(x["dur"] for x in no_srt), 2.0)            # a word, maybe: not joined

    def test_edges_inside_sound_and_a_dead_channel_are_warned(self):
        pk = [-8.0] * 10 + [-60.0] * 300 + [-8.0] * 10
        aud = {"scan": {"channel_peaks_db": {"0": -6.0, "1": -110.0}},
               "noise": {"base_threshold_db": -45.0}}
        talk = [w("so", 0.0, 0.3), w("end", 2.9, 3.2)]
        got = {x["check"]: x for x in video_qa._edge_and_channel_checks(
            pk, 0.01, aud, -20.0, 0.0, 0.0, self.PROF, None, None, "cue", words=talk,
            file_len=3.2)}
        self.assertIn("opens", got["cut_inside_sound"]["measured"])
        self.assertIn("closes", got["cut_inside_sound"]["measured"])
        self.assertEqual(got["one_channel"]["status"], "WARN")
        calm = [-60.0] * 10 + [-8.0] * 300 + [-60.0] * 10
        aud = {"scan": {"channel_peaks_db": {"0": -6.0, "1": -9.0}},
               "noise": {"base_threshold_db": -45.0}}
        self.assertEqual(video_qa._edge_and_channel_checks(
            calm, 0.01, aud, -20.0, 0.0, 0.0, self.PROF, None, None, "cue", words=talk,
            file_len=3.2), [])

    def test_a_clean_tight_start_or_music_at_the_edge_is_not_a_cut_word(self):
        aud = {"scan": {"channel_peaks_db": {"0": -6.0, "1": -6.5}},
               "noise": {"base_threshold_db": -45.0}}
        args = (0.01, aud, -20.0, 0.0, 0.0, self.PROF, None, None, "cue")
        rise = [-120.0, -120.0, -120.0, -59.0, -48.0, -14.0] + [-8.0] * 300 + [-60.0] * 10
        talk = [w("Preparation", 0.04, 0.6), w("end", 2.6, 3.0)]
        self.assertEqual(video_qa._edge_and_channel_checks(rise, *args, words=talk,
                                                           file_len=3.16), [])
        attack = [-30.0, -22.0, -19.0, -17.0, -15.0, -13.0] + [-8.0] * 300 + [-60.0] * 10
        so = [w("So", 0.0, 0.3), w("end", 2.6, 3.0)]                  # a word's own rise
        self.assertEqual(video_qa._edge_and_channel_checks(attack, *args, words=so,
                                                           file_len=3.16), [])
        music = [-8.0] * 320                                           # no word near the edges
        late = [w("Hello", 10.0, 10.4), w("bye", 12.0, 12.3)]
        self.assertEqual(video_qa._edge_and_channel_checks(music, *args, words=late,
                                                           file_len=31.0), [])
        self.assertEqual(video_qa._edge_and_channel_checks(music, *args), [])  # no transcript
        five = dict(aud, scan={"channel_peaks_db": {"0": -6.0, "1": -6.0, "2": -6.0,
                                                    "3": -120.0}})
        self.assertEqual(video_qa._edge_and_channel_checks([-60.0] * 50, 0.01, five, -20.0,
                                                           0.0, 0.0, self.PROF, None, None,
                                                           "cue"), [])  # normal 5.1
        backup = dict(aud, scan={"channel_peaks_db": {"0": -11.2, "1": -31.2}})
        got = video_qa._edge_and_channel_checks([-60.0] * 50, 0.01, backup, -20.0, 0.0, 0.0,
                                                self.PROF, None, None, "cue")
        self.assertEqual(got[0]["check"], "one_channel")                  # a -20 dB backup

    def test_talk_far_beyond_the_words_file_is_warned(self):
        got = {x["check"]: x for x in video_qa._edge_and_channel_checks(
            [-60.0] * 100, 0.01, {}, -20.0, 0.0, 0.0, self.PROF,
            [(0.0, 50.0), (60.0, 120.0)], [(0.0, 52.5)], "word")}
        self.assertEqual(got["word_coverage"]["status"], "WARN")



class _Levels:
    """Level runs for place_clip without decoding a file."""
    def __init__(self, runs, total=60.0):
        self.runs, self.total = runs, total

    def near(self, t):
        return self.runs


class AuditRound10(unittest.TestCase):
    """Tenth independent audit, 24 Oct 2026: each test pins one finding."""

    PROF = video_qa.load_profile(None)

    def test_a_clip_asked_for_at_a_pause_keeps_a_word_clocked_early_into_it(self):
        # The replay's "Why?": a 0.7 s pause ends at 2462.86; Whisper starts the
        # word 0.25 s early, inside the pause; the editor asks for 2462.825.
        runs = [(1, 2450.0, 2462.16), (0, 2462.16, 2462.86), (1, 2462.86, 2463.35),
                (0, 2463.35, 2463.6), (1, 2463.6, 2490.0), (0, 2490.0, 2491.0)]
        words = [dict(w("again.", 2461.7, 2462.1), timing="word", heard=True),
                 dict(w("Why?", 2462.61, 2463.4), timing="word", heard=True),
                 dict(w("Why", 2463.7, 2463.9), timing="word", heard=True),
                 dict(w("done.", 2489.5, 2489.95), timing="word", heard=True)]
        rep = {"warnings": []}
        ws, s, e = finish.place_clip(_Levels(runs, 2600.0), words, 2462.825, 2490.166,
                                     0.08, 0.4, rep)
        self.assertTrue(2462.16 <= s <= 2462.86, s)                  # in the pause, before "Why?"
        self.assertTrue(2490.0 <= e <= 2490.1, e)                    # in the pause after "done."
        self.assertEqual(rep["warnings"], [])
        self.assertEqual(rep["clip_edges_at_pause"], ["start", "end"])
        cap = finish.words_in(ws, s, e, rep["clip_sound"])
        self.assertEqual(cap[0]["word"], "Why?")
        self.assertAlmostEqual(cap[0]["start"], 2462.86, places=2)   # on its sound

    def test_a_mid_phrase_edge_keeps_the_word_it_falls_in(self):
        runs = [(1, 0.0, 30.0)]
        words = [dict(w("one", 1.0, 1.4), timing="word", heard=True),
                 dict(w("two", 1.5, 1.9), timing="word", heard=True),
                 dict(w("three", 2.0, 2.4), timing="word", heard=True)]
        rep = {"warnings": []}
        _, s, e = finish.place_clip(_Levels(runs), words, 1.7, 2.45, 0.08, 0.4, rep)
        self.assertAlmostEqual(s, 1.42)                              # "two" whole, not cut
        self.assertTrue(any("not at a pause" in x for x in rep["warnings"]))

    def test_an_edge_on_a_cue_boundary_keeps_that_cues_first_word(self):
        # The replay's "If": Descript's cue starts at 10.0, Whisper clocked the
        # word 0.3 s early and ended it before the cue began.
        words = [dict(w("know.", 9.2, 9.6), timing="word", heard=True, cue_end=9.9),
                 dict(w("If", 9.7, 9.98), timing="word", heard=True, cue_start=10.0),
                 dict(w("you", 10.1, 10.3), timing="word", heard=True, cue_start=10.0),
                 dict(w("ask.", 10.4, 10.9), timing="word", heard=True, cue_end=11.0)]
        first, last = finish.edge_words(words, 10.0, 11.0)
        self.assertEqual((first["word"], last["word"]), ("If", "ask."))
        s, _ = finish.snap_to_words(words, 10.0, 11.0, 0.08)
        self.assertTrue(9.6 <= s <= 9.7, s)                           # before "If", after "know."

    def test_the_caption_span_is_chosen_by_word_not_by_instant(self):
        # A zero-length "And" shares its instant with the next word's start; the
        # clip asked for "So" onward, and its captions must not open on "And".
        words = [dict(w("And", 5.0, 5.0), timing="word", heard=True),
                 dict(w("So", 5.0, 5.3), timing="word", heard=True),
                 dict(w("done.", 7.5, 7.9), timing="word", heard=True)]
        got = finish.words_in(words, 4.98, 8.0, span=[["So", 5.3], ["done.", 7.9]])
        self.assertEqual([x["word"] for x in got], ["So", "done."])
        # Without a span (no clip), time decides, and the instant word counts.
        self.assertEqual(finish.words_in(words, 4.98, 8.0)[0]["word"], "And")

    def test_the_sound_edges_of_a_cut_that_lands_in_talk_are_the_cut(self):
        runs = [(0, 0.0, 1.0), (1, 1.0, 5.0), (0, 5.0, 6.0), (1, 6.0, 9.0)]
        self.assertEqual(finish.sound_edges(runs, 2.0, 4.5), (2.0, 4.5))
        self.assertEqual(finish.sound_edges(runs, 0.5, 5.5), (1.0, 5.0))
        self.assertEqual(finish.sound_edges(runs, 5.2, 5.8), (None, None))

    def test_the_loudness_ladder_tries_bitrate_then_target_and_keeps_the_best(self):
        from unittest import mock
        with tempfile.TemporaryDirectory() as d:
            part = os.path.join(d, ".out.partial.mp4")
            Path(part).write_bytes(b"0")
            cmd = ["ffmpeg", "-i", "in", "-af",
                   "loudnorm=I=-14.0:TP=-2.0:LRA=11:linear=true,aresample=48000",
                   "-c:a", "aac", "-b:a", "192k", part]
            seq = iter([{"integrated_lufs": -14.6, "true_peak_dbtp": -0.1},
                        {"integrated_lufs": -14.6, "true_peak_dbtp": -2.0},
                        {"integrated_lufs": -14.3, "true_peak_dbtp": -2.0}])
            calls = []

            def render(c, work, out):
                calls.append(list(c))
                Path(out).write_bytes(b"1")
                return subprocess.CompletedProcess(c, 0, "", "")
            rep = {"warnings": []}
            with mock.patch.object(finish.video_qa, "measure_loudness", lambda p: next(seq)), \
                    mock.patch.object(finish, "_run_render", render):
                out, _, loud = finish._settle_loudness(cmd, Path(d), part, None,
                                                       finish.load_style(None), rep)
            self.assertEqual(calls[0][calls[0].index("-b:a") + 1], "320k")  # bitrate first
            self.assertIn("TP=-2.0", calls[0][calls[0].index("-af") + 1])   # target kept
            self.assertIn("I=-13.4", calls[1][calls[1].index("-af") + 1])   # then the shortfall
            self.assertEqual(loud["integrated_lufs"], -14.3)
            self.assertEqual(rep["loudness_passes"]["kept"], 2)
            self.assertEqual(os.listdir(d), [".out.partial.mp4"])            # no leftovers
            self.assertEqual(rep["warnings"], [])

    def test_a_loudness_shortfall_that_cannot_be_closed_is_reported(self):
        from unittest import mock
        with tempfile.TemporaryDirectory() as d:
            part = os.path.join(d, ".o.partial.mp4")
            Path(part).write_bytes(b"0")
            cmd = ["ffmpeg", "-af", "loudnorm=I=-14.0:TP=-2.0:LRA=11", "-c:a", "aac",
                   "-b:a", "256k", part]
            seq = iter([{"integrated_lufs": -15.9, "true_peak_dbtp": -1.9},
                        {"integrated_lufs": -15.5, "true_peak_dbtp": -1.9},
                        {"integrated_lufs": -15.4, "true_peak_dbtp": -1.9}])
            rep = {"warnings": []}
            with mock.patch.object(finish.video_qa, "measure_loudness", lambda p: next(seq)), \
                    mock.patch.object(finish, "_run_render",
                                      lambda c, w_, o: Path(o).write_bytes(b"1")):
                _, _, loud = finish._settle_loudness(cmd, Path(d), part, None,
                                                     finish.load_style(None), rep)
            self.assertEqual(loud["integrated_lufs"], -15.4)
            self.assertTrue(any("lands at -15.4 LUFS" in x and "moved it +0.1 LU" in x
                                for x in rep["warnings"]))

    def test_channel_correlation_from_the_fold_down(self):
        self.assertGreater(finish.channel_corr(-31.96, -51.96, -37.16), 0.95)  # -20 dB backup
        self.assertLess(finish.channel_corr(-31.93, -31.93, -102.8), -0.95)    # inverted
        self.assertLess(abs(finish.channel_corr(-20.0, -20.0, -23.01)), 0.05)  # unrelated
        err = ("[Parsed_astats_1 @ 0x1] Channel: 1\n[Parsed_astats_1 @ 0x1] Peak level dB: -11.2\n"
               "[Parsed_astats_1 @ 0x1] RMS level dB: -32.0\n[Parsed_astats_1 @ 0x1] Channel: 2\n"
               "[Parsed_astats_1 @ 0x1] Peak level dB: -inf\n[Parsed_astats_1 @ 0x1] RMS level dB: -inf\n")
        self.assertEqual(finish.astats_channels(err), [{"peak": -11.2, "rms": -32.0},
                                                       {"peak": -120.0, "rms": -120.0}])

    def test_a_cue_gap_hides_no_pause_from_the_receipt(self):
        def ev(silences, words):
            return {x["check"]: x for x in video_qa.evaluate(
                {"duration_s": 60.0, "video": None},
                {"integrated_lufs": -14.0, "true_peak_dbtp": -2.0}, silences, [], self.PROF,
                first_speech=0.3, words=words)}
        # Pumped room noise as loud as talk fills a 2.4 s stop the SRT shows as a
        # gap between cues; the ASR stretched both edge words into it.
        words = [dict(w("pause.", 9.0, 10.6), timing="word", heard=True, cue_start=5.0,
                      cue_end=10.0),
                 dict(w("Next", 11.6, 12.8), timing="word", heard=True, cue_start=12.4,
                      cue_end=15.0)]
        c = ev([{"start": 10.3, "end": 10.9, "dur": 0.6}], words)
        self.assertEqual(c["talk_gaps"]["status"], "WARN")
        self.assertEqual(c["talk_gaps"]["at"], [[10.0, 2.4]])
        # A word the ASR heard wholly inside the gap is talk the SRT left out.
        inside = words + [dict(w("Yeah", 10.8, 11.1), timing="word", heard=True)]
        self.assertNotIn("talk_gaps", ev([{"start": 10.3, "end": 10.7, "dur": 0.4}], inside))

    def test_a_word_gap_over_the_limit_with_a_near_limit_silence_is_listed(self):
        words = [dict(w("end.", 9.0, 9.4), timing="word", heard=True),
                 dict(w("Next", 11.7, 12.0), timing="word", heard=True)]
        c = {x["check"]: x for x in video_qa.evaluate(
            {"duration_s": 60.0, "video": None},
            {"integrated_lufs": -14.0, "true_peak_dbtp": -2.0},
            [{"start": 9.5, "end": 11.49, "dur": 1.99}], [], self.PROF, first_speech=0.3,
            words=words)}
        self.assertEqual(c["talk_gaps"]["status"], "WARN")

    def test_a_recurring_sentence_opener_stays_text(self):
        srt = ("1\n00:00:00,000 --> 00:00:02,500\nUpdate: the open house moved.\n\n"
               "2\n00:00:03,000 --> 00:00:05,500\nBring your questions.\n\n"
               "3\n00:00:06,000 --> 00:00:08,500\nUpdate: parking is free.\n")
        got = [x["word"] for x in finish.words_from_srt(srt)]
        self.assertEqual(got.count("Update:"), 2)


class _NoisyLevels:
    """Level runs whose silence threshold rose 15 dB over a steady fan."""
    def __init__(self, runs, raised_db=15.0, floor_db=-43.0, base=80.0, total=200.0):
        n = int((total - base) / 0.01)
        self.r = finish.Runs(runs, base, [-54.0 + raised_db] * (n // 50 + 1), 0.5, -54.0,
                             [floor_db] * n, 0.01)
        self.total, self.style = total, finish.load_style(None)

    def near(self, t):
        return self.r


class _PeakLevels:
    """Level runs with a 10 ms peak per window: `loud` [(a, b, dB)] over a
    steady floor, the threshold raised 13 dB over it (room noise)."""
    def __init__(self, runs, loud, floor_db=-41.0, base=370.0, total=420.0):
        n = int((total - base) / 0.01)
        peaks = [floor_db] * n
        for a, b, db in loud:
            for k in range(int(round((a - base) / 0.01)), int(round((b - base) / 0.01))):
                peaks[k] = db
        self.r = finish.Runs(runs, base, [-41.0] * (n // 50 + 1), 0.5, -54.0, peaks, 0.01)
        self.total, self.style = total, finish.load_style(None)

    def near(self, t):
        return self.r


class AuditRound11(unittest.TestCase):
    """Eleventh independent audit, 24 Oct 2026: each test pins one finding."""

    PROF = video_qa.load_profile(None)
    RUNS = [(1, 90.0, 94.3), (0, 94.3, 94.6), (1, 94.6, 102.829), (0, 102.829, 104.209),
            (1, 104.209, 110.0)]

    def _words(self):
        cue = dict(cue_start=94.437, cue_end=103.389)
        return [dict(w("I'm", 94.62, 94.9), timing="word", heard=True, **cue),
                dict(w("using", 94.9, 95.3), timing="word", heard=True, **cue),
                dict(w("process", 102.3, 102.72), timing="word", heard=True, **cue),
                dict(w("this.", 102.75, 103.21), timing="word", heard=True, **cue),
                dict(w("Next", 104.3, 104.6), timing="word", heard=True, cue_start=104.25,
                     cue_end=106.0)]

    def test_a_clip_end_at_a_pause_under_room_noise_keeps_its_last_word(self):
        # np_fan50: the fan raised the threshold 15 dB and the soft end of
        # "this." read as silence from 102.829; the cut landed at 102.909.
        rep = {"warnings": []}
        _, s, e = finish.place_clip(_NoisyLevels(self.RUNS), self._words(), 94.437, 103.389,
                                    0.08, 0.4, rep)
        self.assertGreaterEqual(e, 103.29)              # past "this." (clock end + pad)
        self.assertLess(e, 104.209 - 0.3)               # clear of "Next"
        self.assertEqual(rep["clip_edges_at_pause"], ["start", "end"])
        # The same runs with no threshold rise (a quiet room): pad after the level.
        rep = {"warnings": []}
        _, _, e0 = finish.place_clip(_Levels(self.RUNS, 200.0), self._words(), 94.437,
                                     103.389, 0.08, 0.4, rep)
        self.assertAlmostEqual(e0, 102.909, places=3)
        self.assertTrue(any("before its last word" in x for x in rep["warnings"]))

    def test_noise_slack_needs_a_noisy_pause(self):
        style = finish.load_style(None)
        lv = _NoisyLevels(self.RUNS)
        self.assertAlmostEqual(finish.noise_slack(lv.r, 102.84, 104.2, style), 0.375)
        quiet = _NoisyLevels(self.RUNS, floor_db=-80.0)  # rise from music next to a quiet pause
        self.assertEqual(finish.noise_slack(quiet.r, 102.84, 104.2, style), 0.0)
        self.assertEqual(finish.noise_slack(self.RUNS, 102.84, 104.2, style), 0.0)

    def test_a_start_under_noise_keeps_at_most_a_little_slack(self):
        self.assertAlmostEqual(finish.cut_in_pause(10.0, 12.0, "start", 0.08, 0.5), 11.77)
        self.assertAlmostEqual(finish.cut_in_pause(10.0, 12.0, "start", 0.08, 0.0), 11.92)
        self.assertAlmostEqual(finish.cut_in_pause(10.0, 12.0, "end", 0.08, 0.0), 10.08)
        self.assertAlmostEqual(finish.cut_in_pause(10.0, 12.0, "end", 0.08, 0.3,
                                                   {"end": 10.5}), 10.58)
        # a word end far into the pause is not trusted past the reach
        self.assertAlmostEqual(finish.cut_in_pause(10.0, 12.0, "end", 0.08, 0.3,
                                                   {"end": 11.5}), 10.38)

    def test_an_aac_close_inside_a_word_is_seen(self):
        ws = [dict(w("word", 0.2, 1.0), timing="word")]
        talk = [-60.0] * 20 + [-15.0] * 78
        pk = talk + [-17.6, -16.5, -71.4, -120.0]      # AAC padding and roll-off
        c = video_qa._edge_and_channel_checks(pk, 0.01, {"noise": {"base_threshold_db": -45.0}},
                                              -20.0, 0.0, 0.06, self.PROF, None, None, "word",
                                              words=ws, file_len=1.06, audio_len=1.0, fps=25.0)
        hit = [x for x in c if x["check"] == "cut_inside_sound"]
        self.assertTrue(hit and "closes" in hit[0]["measured"], c)
        # A word that dies away by itself is not a cut.
        fade = talk + [-20.0, -26.0, -33.0, -40.0, -48.0, -56.0, -65.0]
        c = video_qa._edge_and_channel_checks(fade, 0.01, {"noise": {"base_threshold_db": -45.0}},
                                              -20.0, 0.0, 0.0, self.PROF, None, None, "word",
                                              words=ws, file_len=1.05, fps=25.0)
        self.assertFalse([x for x in c if x["check"] == "cut_inside_sound"])

    def test_an_aligner_slip_does_not_drag_a_cue_edge_far(self):
        # The aligner put "Jeff" 1.9 s from its cue: the cue rule ignores it.
        words = [dict(w("2,357.", 574.0, 574.6), timing="word", heard=True),
                 dict(w("Jeff", 574.6, 574.62), timing="word", heard=True, cue_start=576.5),
                 dict(w("so", 576.55, 576.8), timing="word", heard=True, cue_start=576.4)]
        first, _ = finish.edge_words(words, 576.5, 580.0)
        self.assertEqual(first["word"], "so")

    def test_a_recurring_day_or_price_stays_text_and_a_second_voice_is_a_label(self):
        def srt(lines):
            return "\n\n".join(f"{i + 1}\n00:00:{i * 3:02d},000 --> 00:00:{i * 3 + 2:02d},500\n{l}"
                               for i, l in enumerate(lines))

        def words(lines):
            return " ".join(x["word"] for x in finish.words_from_srt(srt(lines)))
        self.assertEqual(words(["Monday: post it.", "Tuesday: boost it.", "Monday: review."]),
                         "Monday: post it. Tuesday: boost it. Monday: review.")
        self.assertEqual(words(["Price: ten.", "Bring a friend.", "Price: still ten."]),
                         "Price: ten. Bring a friend. Price: still ten.")
        self.assertEqual(words(["Dennis: So we start.", "Amy: Yeah.", "Dennis: Right.",
                                "Google Maps: open it."]),
                         "So we start. Yeah. Right. Google Maps: open it.")

    def test_a_loudness_raise_that_barely_moves_stops_the_ladder(self):
        # Round 11: on a short clip under room noise loudnorm's dynamic mode
        # went -15.1, -15.2, -15.2: the second raise was a wasted render.
        from unittest import mock
        with tempfile.TemporaryDirectory() as d:
            part = os.path.join(d, ".o.partial.mp4")
            Path(part).write_bytes(b"0")
            cmd = ["ffmpeg", "-af", "loudnorm=I=-14.0:TP=-2.0:LRA=11", "-c:a", "aac",
                   "-b:a", "256k", part]
            seq = iter([{"integrated_lufs": -15.1, "true_peak_dbtp": -2.0},
                        {"integrated_lufs": -15.2, "true_peak_dbtp": -2.0}])
            calls = []

            def render(c, w_, o):
                calls.append(c)
                Path(o).write_bytes(b"1")
            rep = {"warnings": []}
            with mock.patch.object(finish.video_qa, "measure_loudness", lambda p: next(seq)), \
                    mock.patch.object(finish, "_run_render", render):
                _, _, loud = finish._settle_loudness(cmd, Path(d), part, None,
                                                     finish.load_style(None), rep, 2)
            self.assertEqual(len(calls), 1)                     # no third render
            self.assertEqual(loud["integrated_lufs"], -15.1)    # the better one kept
            msg = " ".join(rep["warnings"])
            self.assertIn("moved it -0.1 LU", msg)
            self.assertNotIn("multichannel", msg)               # stereo: not the reason
            # A raise that makes it worse stops the ladder too (-15.3, -15.7).
            seq = iter([{"integrated_lufs": -15.3, "true_peak_dbtp": -2.0},
                        {"integrated_lufs": -15.7, "true_peak_dbtp": -2.0}])
            calls.clear()
            rep = {"warnings": []}
            with mock.patch.object(finish.video_qa, "measure_loudness", lambda p: next(seq)), \
                    mock.patch.object(finish, "_run_render", render):
                _, _, loud = finish._settle_loudness(cmd, Path(d), part, None,
                                                     finish.load_style(None), rep, 2)
            self.assertEqual((len(calls), loud["integrated_lufs"]), (1, -15.3))


class AuditRound12(unittest.TestCase):
    """Twelfth independent audit, 24-25 Oct 2026: each test pins one finding."""

    PROF = video_qa.load_profile(None)

    def _light(self):
        # nz_ac44, --words only: "...that's what you need to do" and the level,
        # under a threshold raised 20 dB, reads "what you need to do" as silence.
        return [dict(w("level.", 308.6, 309.2), timing="word", heard=True),
                dict(w("That's", 309.3, 309.7), timing="word", heard=True),
                dict(w("what", 309.8, 309.95), timing="word", heard=True),
                dict(w("you", 309.95, 310.1), timing="word", heard=True),
                dict(w("need", 310.1, 310.35), timing="word", heard=True),
                dict(w("to", 310.35, 310.5), timing="word", heard=True),
                dict(w("do", 310.56, 310.8), timing="word", heard=True),
                dict(w("And", 311.4, 311.6), timing="word", heard=True)]

    def test_a_light_clip_end_keeps_words_the_level_reads_as_silence(self):
        runs = [(1, 296.0, 309.75), (0, 309.75, 311.28), (1, 311.28, 320.0)]
        words = [dict(w("Love's", 296.4, 296.76), timing="word", heard=True)] + self._light()
        rep = {"warnings": []}
        _, s, e = finish.place_clip(_NoisyLevels(runs, raised_db=19.8, base=290.0, total=330.0),
                                    words, 296.4, 310.8, 0.08, 0.4, rep)
        self.assertGreaterEqual(e, 310.8)                  # "do" kept (round 12 cut at 310.325)
        self.assertLess(e, 311.28)                         # "And" not
        self.assertEqual(rep["clip_word_span"][1][0], "do")

    def test_the_last_word_is_never_the_next_sentence_stretched_back(self):
        words = [dict(w("scam", 187.4, 187.88), timing="word", heard=True),
                 dict(w("and", 187.88, 188.78), timing="word", heard=True)]
        self.assertEqual(finish.word_before_pause(words, 187.9, 188.6, end=187.88)["word"],
                         "scam")

    def test_a_start_pause_holding_a_heard_word_starts_before_it(self):
        # A soft "Okay," the ASR heard wholly inside the level's "pause", just
        # after the requested START: talk, not the editor's pause.
        runs = [(1, 110.0, 121.75), (0, 121.75, 124.4), (1, 124.4, 130.0)]
        words = [dict(w("Okay,", 123.71, 123.95), timing="word", heard=True, cue_start=123.773,
                      cue_end=130.0),
                 dict(w("so", 124.45, 124.65), timing="word", heard=True, cue_start=123.773,
                      cue_end=130.0)]
        rep = {"warnings": []}
        _, s, _ = finish.place_clip(_Levels(runs, 200.0), words, 123.773, 129.0, 0.08, 0.4, rep)
        self.assertLess(s, 123.71)

    def test_a_cut_in_a_clear_word_gap_under_a_bed_is_a_note_not_a_warning(self):
        runs = [(2, 0.0, 30.0)]                            # a bed: no level pause at all
        words = [dict(w("first", 4.0, 4.4), timing="word", heard=True),
                 dict(w("Next", 5.0, 5.3), timing="word", heard=True),
                 dict(w("words", 5.3, 5.8), timing="word", heard=True),
                 dict(w("end.", 9.0, 9.5), timing="word", heard=True),
                 dict(w("More", 10.2, 10.5), timing="word", heard=True)]
        rep = {"warnings": []}
        _, s, e = finish.place_clip(_Levels(runs), words, 5.0, 9.5, 0.08, 0.4, rep)
        self.assertEqual(rep["warnings"], [])
        self.assertEqual(len(rep["notes"]), 2)
        self.assertIn("gap between words", rep["notes"][0])
        # ...in the middle of each gap: ASR clocks end words early and start
        # them late (a bed left up to 0.27 s of the last word's tail out).
        self.assertAlmostEqual(s, 4.7)
        self.assertAlmostEqual(e, 9.85)

    def test_a_first_word_timed_as_an_instant_keeps_its_sound(self):
        # nz fan47, --words: "And" timed 472.46-472.46, said 472.34-472.47.
        runs = [(1, 460.0, 471.68), (0, 471.68, 472.34), (1, 472.34, 472.47),
                (0, 472.47, 472.77), (1, 472.77, 480.0)]
        words = [dict(w("Right?", 471.6, 471.6), timing="word", heard=True),
                 dict(w("And", 472.46, 472.46), timing="word", heard=True),
                 dict(w("so", 472.46, 472.88), timing="word", heard=True),
                 dict(w("anyway,", 472.88, 473.16), timing="word", heard=True),
                 dict(w("done.", 478.0, 478.5), timing="word", heard=True)]
        rep = {"warnings": []}
        _, s, _ = finish.place_clip(_Levels(runs, 500.0), words, 472.46, 478.5, 0.08, 0.4, rep)
        self.assertLess(s, 472.34)
        self.assertEqual(rep["clip_word_span"][0][0], "And")

    def test_every_finish_warning_shows_in_the_rendered_receipt(self):
        rec = {"verdict": "WARN", "file": "x.mp4", "sha256_head": "0" * 64,
               "probe": {"size_bytes": 1, "duration_s": 1.0}, "measured_at": "now",
               "tool": "t", "checks": [{"check": "finish_report", "status": "WARN",
                                        "measured": 2, "expected": "-",
                                        "note": "finish.py reported: one | two"}]}
        row = [l for l in video_qa.render_markdown(rec).splitlines()
               if l.startswith("| finish_report")][0]
        self.assertEqual(row.replace("\\|", "").count("|"), 6)   # five cells
        self.assertIn("one \\| two", row)

    def test_talk_alone_in_one_channel_is_not_two_speakers(self):
        aud = {"noise": {"base_threshold_db": -45.0},
               "scan": {"channel_peaks_db": {"1": -3.0, "2": -4.0}}}

        def checks(own):
            return {x["check"] for x in video_qa._edge_and_channel_checks(
                [-30.0] * 100, 0.01, aud, -20.0, 0.0, 0.0, self.PROF, None, None, "none",
                roles={"own_talk_s": own})}
        self.assertNotIn("speakers_hard_panned", checks([0.0, 2.2]))   # wide stereo music
        self.assertIn("speakers_hard_panned", checks([1.5, 2.2]))      # two lavs taking turns

    # ---- found by the replay sweep after round 12 ----

    @staticmethod
    def _bed_runs(base, total, loud, bed_db=-30.0):
        """A stretch with no level pause (a bed under it all): 10 ms peaks at
        the bed's level, `loud` [(a, b, dB)] on top."""
        n = int((total - base) / 0.01)
        peaks = [bed_db] * n
        for a, b, db in loud:
            for k in range(int(round((a - base) / 0.01)), int(round((b - base) / 0.01))):
                peaks[k] = db
        return finish.Runs([(1, base, total)], base, [-41.0] * (n // 50 + 1), 0.5, -54.0,
                           peaks, 0.01)

    def test_a_cut_in_a_word_gap_goes_to_its_quietest_part(self):
        # The ASR ends "end." at 9.5; its sound decays to 9.7, then a quiet
        # dip, then the bed. The cut goes into the dip, not 0.35 s into the gap.
        r = self._bed_runs(0.0, 30.0, [(4.0, 4.4, -12.0), (5.0, 5.8, -12.0), (9.0, 9.6, -12.0),
                                       (9.6, 9.7, -22.0), (9.72, 9.8, -45.0),
                                       (10.2, 10.5, -12.0)])

        class L:
            total, style = 30.0, finish.load_style(None)

            def near(self, t):
                return r
        words = [dict(w("first", 4.0, 4.4), timing="word", heard=True),
                 dict(w("Next", 5.0, 5.3), timing="word", heard=True),
                 dict(w("words", 5.3, 5.8), timing="word", heard=True),
                 dict(w("end.", 9.0, 9.5), timing="word", heard=True),
                 dict(w("More", 10.2, 10.5), timing="word", heard=True)]
        rep = {"warnings": []}
        _, _, e = finish.place_clip(L(), words, 5.0, 9.5, 0.08, 0.4, rep)
        self.assertGreater(e, 9.72)
        self.assertLess(e, 9.81)                           # in the dip, not on the bed
        self.assertEqual([x for x in rep["warnings"] if "ends" in x], [])

    def test_words_only_descript_has_bound_the_gap(self):
        # The replay at 3039.589: the ASR heard "22?" and "Okay." but not
        # Descript's "I don't know." between them; the middle of the heard
        # gap was inside "know" at talk level. The cut stays in the real pause.
        r = self._bed_runs(3030.0, 3045.0, [(3038.1, 3039.2, -12.0), (3039.3, 3039.46, -15.0),
                                            (3039.47, 3039.62, -50.0), (3039.62, 3040.2, -12.0)])

        class L:
            total, style = 3100.0, finish.load_style(None)

            def near(self, t):
                return r
        # As align_text_to_timing returns them: the unheard words carry their
        # cue's times, their clocks are a placeholder instant.
        lost = dict(timing="word", heard=False, cue_start=3038.656, cue_end=3038.896)
        words = [dict(w("22?", 3038.16, 3038.64), timing="word", heard=True,
                      cue_start=3037.012, cue_end=3038.656),
                 dict(w("okay.", 3039.6, 3039.96), timing="word", heard=True,
                      cue_start=3039.589, cue_end=3040.141),
                 dict(w("I", 3039.865, 3039.865), **lost),
                 dict(w("don't", 3039.865, 3039.865), **lost),
                 dict(w("know.", 3039.865, 3039.865), **lost),
                 dict(w("done.", 3044.0, 3044.5), timing="word", heard=True,
                      cue_start=3043.9, cue_end=3044.5)]
        rep = {"warnings": []}
        _, s, _ = finish.place_clip(L(), words, 3039.589, 3044.5, 0.08, 0.4, rep)
        self.assertGreater(s, 3039.46)                     # not inside "know" (3039.12)
        self.assertLess(s, 3039.589)

    def test_a_pause_of_exactly_0_15_s_is_a_pause(self):
        # The replay at 710.604: with the words, the level's pause before "Wow,"
        # measured 710.454 to 710.604, 0.15 s less a float's last bit.
        runs = [(1, 709.374, 710.4540000000001), (0, 710.4540000000001, 710.604),
                (1, 710.604, 710.614), (0, 710.614, 710.624), (1, 710.624, 711.944)]
        self.assertEqual(finish.edge_pause(runs, 710.604, "start"), (710.4540000000001, 710.604))

    # ---- found by the fresh sweep after round 12 (nz_fan47, --words) ----

    FAN47_RUNS = [(1, 370.0, 378.51), (0, 378.51, 380.05), (1, 380.05, 380.29),
                  (0, 380.29, 381.26), (1, 381.26, 390.0)]

    def _fan47_words(self):
        return [dict(w("tools.", 378.0, 378.5), timing="word", heard=True),
                dict(w("But", 380.64, 381.0), timing="word", heard=True),
                dict(w("this", 381.0, 381.36), timing="word", heard=True),
                dict(w("is", 381.36, 381.46), timing="word", heard=True),
                dict(w("done.", 389.0, 389.5), timing="word", heard=True)]

    def test_a_first_word_clocked_in_silence_keeps_the_talk_before_it(self):
        # Whisper put "But" (said 380.04-380.45) at 380.64-381.0, in the silence
        # after it: no sound of its own there, so it is not soft talk.
        levels = _PeakLevels(self.FAN47_RUNS, [(370.0, 378.51, -20.0), (380.05, 380.29, -19.0),
                                               (381.26, 390.0, -15.0)])
        rep = {"warnings": []}
        _, s, _ = finish.place_clip(levels, self._fan47_words(), 380.64, 389.5, 0.08, 0.4, rep)
        self.assertLess(s, 380.05)                         # "But" kept (cut 380.465 before)
        self.assertGreater(s, 378.51)                      # "tools." not
        self.assertEqual(rep["clip_word_span"][0][0], "But")
        self.assertTrue(any("clocked in silence" in n for n in rep["notes"]))
        self.assertFalse(any("starts" in x for x in rep["warnings"]))

    def test_a_soft_first_word_in_the_pause_is_still_talk(self):
        # The same clocks, but "But" has sound of its own 8 dB over the noise:
        # soft talk the raised threshold missed, so the cut stays before it.
        levels = _PeakLevels(self.FAN47_RUNS, [(370.0, 378.51, -20.0), (380.05, 380.29, -19.0),
                                               (380.64, 381.0, -33.0), (381.26, 390.0, -15.0)])
        rep = {"warnings": []}
        _, s, _ = finish.place_clip(levels, self._fan47_words(), 380.64, 389.5, 0.08, 0.4, rep)
        self.assertGreater(s, 380.29)
        self.assertLess(s, 380.64)
        self.assertFalse(any("clocked in silence" in n for n in rep.get("notes", [])))

    def test_a_last_word_clocked_early_in_silence_keeps_its_talk(self):
        # The mirror: "answer." clocked inside the pause, said just after it.
        runs = [(1, 370.0, 385.0), (0, 385.0, 385.9), (1, 385.9, 386.3), (0, 386.3, 387.0),
                (1, 387.0, 395.0)]
        levels = _PeakLevels(runs, [(370.0, 385.0, -18.0), (385.9, 386.3, -17.0),
                                    (387.0, 395.0, -15.0)])
        words = [dict(w("So", 375.0, 375.3), timing="word", heard=True),
                 dict(w("the", 384.6, 384.95), timing="word", heard=True),
                 dict(w("answer.", 385.3, 385.6), timing="word", heard=True),
                 dict(w("Next", 387.05, 387.4), timing="word", heard=True)]
        rep = {"warnings": []}
        _, _, e = finish.place_clip(levels, words, 375.0, 385.6, 0.08, 0.4, rep)
        self.assertGreater(e, 386.3)                       # its sound kept
        self.assertLess(e, 387.0)                          # "Next" not
        self.assertEqual(rep["clip_word_span"][1][0], "answer.")

class _QuietRoom:
    """Level runs of a quiet room for place_clip: 10 ms peaks at `floor_db`
    with `loud` [(a, b, dB)] on top, the silence threshold at `thr_db` (not
    raised), and the runs given."""
    def __init__(self, runs, loud, base, total, floor_db=-70.0, thr_db=-46.0):
        n = int((total - base) / 0.01)
        peaks = [floor_db] * n
        for a, b, db in loud:
            for k in range(int(round((a - base) / 0.01)), int(round((b - base) / 0.01))):
                peaks[k] = db
        self.r = finish.Runs(runs, base, [thr_db] * (n // 50 + 1), 0.5, thr_db, peaks, 0.01)
        self.total, self.style = total + 100.0, finish.load_style(None)

    def near(self, t):
        return self.r


class AuditRound13(unittest.TestCase):
    """Thirteenth independent audit, 25 Oct 2026: each test pins one finding."""

    # seg3 (one of our own Descript publishes, no bed): Whisper heard
    # "realistically," (to 131.78) and "I" (from 132.26); between them an
    # unheard filler at talk level, with real dips only at 131.82-131.84 and
    # 132.15-132.17. Round 12 cut both clips at 132.07, mid-filler, PASS.
    SEG3_RUNS = [(1, 127.0, 131.83), (0, 131.83, 131.85), (1, 131.85, 133.0)]
    SEG3_LOUD = [(130.32, 131.78, -9.0), (131.78, 131.82, -29.0), (131.82, 131.85, -48.0),
                 (131.85, 132.15, -18.0), (131.93, 131.95, -14.6), (132.15, 132.18, -38.0),
                 (132.18, 132.58, -10.0)]

    def _seg3_words(self):
        return [dict(w("but", 122.2, 122.5), timing="word", heard=True),
                dict(w("realistically,", 130.32, 131.78), timing="word", heard=True),
                dict(w("I", 132.26, 132.3), timing="word", heard=True),
                dict(w("think,", 132.3, 132.58), timing="word", heard=True),
                dict(w("so.", 139.2, 139.7), timing="word", heard=True)]

    def test_a_gap_cut_never_lands_inside_an_unheard_filler(self):
        lv = _QuietRoom(self.SEG3_RUNS + [(0, 139.7, 140.2), (1, 140.2, 141.0)],
                        self.SEG3_LOUD + [(139.2, 139.7, -10.0)], 120.0, 141.0)
        rep = {"warnings": []}
        _, _, e = finish.place_clip(lv, self._seg3_words(), 122.2, 131.78, 0.08, 0.4, rep)
        self.assertGreaterEqual(e, 131.82)                 # "realistically," whole
        self.assertFalse(131.86 < e < 132.15)              # in a dip, never mid-filler
        self.assertLess(e, 132.26)                         # "I" not begun
        # (the end keeps the filler, past a dip from "realistically,": since
        # round 14 that is a warning, not a clean note)
        self.assertTrue(any("ends with 0.3" in x and "talk-level sound after its last word" in x
                            for x in rep["warnings"]))
        self.assertTrue(any("quiet moment" in n for n in rep.get("notes", [])))
        rep = {"warnings": []}
        _, s, _ = finish.place_clip(lv, self._seg3_words(), 132.26, 139.7, 0.08, 0.4, rep)
        self.assertFalse(131.86 < s < 132.15)              # never mid-filler (round 12: 132.07)
        self.assertLess(s, 132.18)                         # "I" whole

    def test_a_gap_with_nothing_quiet_in_it_still_warns(self):
        # bed20 98.42-106.82: talk the ASR half heard, 13-18 dB over the bed, all
        # through the "gap" after "lane,". Round 12 called its quietest 50 ms
        # (-22 dBFS, 12 dB under the talk) quiet and PASSed with a NOTE.
        loud = [(90.0, 105.0, -10.0), (105.0, 105.4, -10.0), (105.4, 106.4, -21.0),
                (106.4, 106.82, -10.0), (106.82, 107.1, -22.0), (107.1, 107.4, -10.0)]
        lv = _QuietRoom([(1, 90.0, 107.4), (0, 107.4, 115.0)], loud, 90.0, 115.0,
                        floor_db=-38.0, thr_db=-50.0)
        words = [dict(w("change", 98.42, 98.8), timing="word", heard=True),
                 dict(w("every", 105.0, 105.4), timing="word", heard=True),
                 dict(w("lane,", 106.4, 106.82), timing="word", heard=True),
                 dict(w("three", 107.1, 107.4), timing="word", heard=True)]
        rep = {"warnings": []}
        finish.place_clip(lv, words, 98.42, 106.82, 0.08, 0.4, rep)
        self.assertTrue(any("ends in a" in x and "never goes quiet" in x for x in rep["warnings"]))
        self.assertFalse(any("quiet" in n for n in rep.get("notes", [])))

    def test_a_gap_cut_waits_for_the_last_words_decay(self):
        # The replay at 1340.239: "company." decays at -27 to -35 dBFS to 1340.44
        # and under -50 by 1340.50; round 12 cut at 1340.35 with a NOTE.
        runs = [(1, 1330.0, 1340.47), (0, 1340.47, 1340.53), (1, 1340.53, 1350.0)]
        lv = _QuietRoom(runs, [(1330.0, 1340.2, -10.0), (1340.2, 1340.44, -30.0),
                               (1340.44, 1340.48, -42.0), (1340.48, 1340.53, -55.0),
                               (1340.53, 1341.5, -12.0)], 1330.0, 1350.0, thr_db=-45.0)
        words = [dict(w("So", 1317.4, 1317.6), timing="word", heard=True),
                 dict(w("company.", 1339.7, 1340.1), timing="word", heard=True),
                 dict(w("he's", 1340.5, 1340.58), timing="word", heard=True)]
        rep = {"warnings": []}
        _, _, e = finish.place_clip(lv, words, 1330.5, 1340.1, 0.08, 0.4, rep)
        self.assertGreaterEqual(e, 1340.47)                # the fade clear of the decay
        self.assertLessEqual(e, 1340.53)                   # "he's" not begun

    def test_an_instant_first_word_bounds_the_gap(self):
        # bedsn14 and hum46 at 396.62: "okay," timed as an instant, said
        # 396.36-396.61, run straight on from "want," with no quiet between.
        # Round 12 left out instants when it measured the gap, so it claimed a
        # 1.08 s gap and cut inside "okay," with only a NOTE.
        lv = _QuietRoom([(1, 390.0, 400.0)], [(390.0, 396.34, -10.0), (396.34, 396.61, -20.0),
                                              (396.62, 398.0, -10.0)], 390.0, 400.0)
        words = [dict(w("want,", 396.0, 396.34), timing="word", heard=True),
                 dict(w("okay,", 396.62, 396.62), timing="word", heard=True),
                 dict(w("here's", 396.62, 397.7), timing="word", heard=True),
                 dict(w("done.", 399.0, 399.5), timing="word", heard=True)]
        rep = {"warnings": []}
        _, s, _ = finish.place_clip(lv, words, 396.62, 399.5, 0.08, 0.4, rep)
        self.assertTrue(any(x.startswith("the clip starts") for x in rep["warnings"]))
        self.assertFalse(any("quiet moment" in n for n in rep.get("notes", [])))

    def test_an_instant_neighbour_does_not_eat_a_real_pause(self):
        # seg5 at 171.3: "ten," then a real 80 ms pause, then "right?" timed as an
        # instant at 171.66 (said 171.52-171.66). The search stops at its sound;
        # the gap on the clocks is 0.36 s, so the pause is found.
        # Under a bed (-34 dBFS) the instant's sound must not be walked back over
        # the bed into "ten," (an intermediate fix did, and WARNed).
        lv = _QuietRoom([(1, 165.0, 175.0)], [(165.0, 171.34, -10.0), (171.34, 171.37, -24.0),
                                              (171.37, 171.43, -34.0), (171.43, 171.49, -50.0),
                                              (171.49, 171.52, -34.0), (171.52, 171.66, -8.0),
                                              (171.66, 175.0, -12.0)], 165.0, 175.0,
                        floor_db=-34.0)
        words = [dict(w("so", 165.5, 165.8), timing="word", heard=True),
                 dict(w("ten,", 171.08, 171.3), timing="word", heard=True),
                 dict(w("right?", 171.66, 171.66), timing="word", heard=True),
                 dict(w("yes", 171.8, 172.1), timing="word", heard=True)]
        rep = {"warnings": []}
        _, _, e = finish.place_clip(lv, words, 165.5, 171.3, 0.08, 0.4, rep)
        self.assertGreaterEqual(e, 171.43)                 # in the dip under the bed
        self.assertLessEqual(e, 171.49)
        self.assertEqual([x for x in rep["warnings"] if "ends" in x], [])

    def test_one_voice_hard_panned_is_a_voice_not_music(self):
        # A guest's lav on the right input beside a centred host mic: 64.7 s of
        # its own talk in 99.1 s. Wide stereo music: 2.2 s in 104 s.
        self.assertTrue(video_qa.hard_panned({"own_talk_s": [0.0, 64.7], "talk_s": [60.0, 99.1]}))
        self.assertFalse(video_qa.hard_panned({"own_talk_s": [0.0, 2.2], "talk_s": [100.0, 104.0]}))
        self.assertTrue(video_qa.hard_panned({"own_talk_s": [1.5, 2.2]}))     # split mode

    def test_a_backslash_cannot_undo_the_pipe_escape(self):
        rec = {"verdict": "WARN", "file": "x.mp4", "sha256_head": "0" * 64,
               "probe": {"size_bytes": 1, "duration_s": 1.0}, "measured_at": "now",
               "tool": "t", "checks": [{"check": "finish_report", "status": "WARN",
                                        "measured": "a|b", "expected": "x \\| y",
                                        "note": "n"}]}
        row = [l for l in video_qa.render_markdown(rec).splitlines()
               if l.startswith("| finish_report")][0]
        # a pipe after an even run of backslashes (none included) splits a cell
        unescaped = len(re.findall(r"(?<!\\)(?:\\\\)*\|", row))
        self.assertEqual(unescaped, 6)                     # five cells


class _Room:
    """Level runs for place_clip: 10 ms peaks at `floor_db` with `loud`
    [(a, b, dB)] on top; the silence threshold raised to `thr_db` over a base
    of `base_db` (room noise or a bed), and the runs given."""
    def __init__(self, runs, loud, base, total, floor_db, thr_db, base_db):
        n = int(round((total - base) / 0.01))
        peaks = [floor_db] * n
        for a, b, db in loud:
            for k in range(int(round((a - base) / 0.01)), int(round((b - base) / 0.01))):
                peaks[k] = db
        self.r = finish.Runs(runs, base, [thr_db] * (n // 50 + 1), 0.5, base_db, peaks, 0.01)
        self.total, self.style = total + 100.0, finish.load_style(None)

    def near(self, t):
        return self.r


def _said(*ws, **extra):
    return [dict(w(*x), timing="word", heard=True, **extra) for x in ws]


class AuditRound14(unittest.TestCase):
    """Fourteenth independent audit, 25 Oct 2026: each test pins one finding."""

    # ac44 (and fan47, bedsn14) at 230.34: "right?" then a soft "It's" (said
    # 230.30-230.36 and 230.43-230.49, -31 to -34 dBFS) under an AC whose
    # raised threshold calls 230.30-230.57 a pause. Round 13 held "It's" as
    # talk, called the edge mid-phrase, then cut in the middle of that same
    # "pause" (230.435): Whisper heard "Costing Uncle Dennis", PASS.
    AC_RUNS = [(1, 225.0, 230.30), (0, 230.30, 230.57), (1, 230.57, 231.13),
               (0, 231.13, 231.6), (1, 231.6, 235.0)]
    AC_LOUD = [(229.48, 229.8, -18.0), (230.02, 230.18, -17.0), (230.18, 230.30, -28.0),
               (230.30, 230.36, -34.0), (230.43, 230.49, -31.0), (230.57, 231.13, -18.0),
               (231.6, 235.0, -18.0)]
    AC_WORDS = [("great,", 229.48, 229.8), ("right?", 230.02, 230.18), ("It's", 230.34, 230.52),
                ("costing", 230.52, 230.86), ("Uncle", 230.86, 231.08), ("Dennis", 231.6, 231.9)]

    def test_a_soft_first_word_in_a_noisy_pause_is_not_cut_in_half(self):
        lv = _Room(self.AC_RUNS, self.AC_LOUD, 225.0, 235.0, -40.0, -36.2, -51.4)
        rep = {"warnings": []}
        _, s, _ = finish.place_clip(lv, _said(*self.AC_WORDS), 230.34, 231.08, 0.08, 0.4, rep)
        self.assertLessEqual(s, 230.30)                    # never inside "It's" (230.435)
        self.assertTrue(any(x.startswith("the clip starts") for x in rep["warnings"]))
        # The same with Descript's cues (FULL): cue 90 starts where cue 89 ends.
        ws = _said(*self.AC_WORDS)
        for o in ws:
            o.update(cue_start=228.0, cue_end=230.309) if o["start"] < 230.3 else \
                o.update(cue_start=230.309, cue_end=233.0)
        rep = {"warnings": []}
        _, s, _ = finish.place_clip(lv, ws, 230.309, 231.08, 0.08, 0.4, rep)
        self.assertLessEqual(s, 230.30)
        self.assertTrue(any(x.startswith("the clip starts") for x in rep["warnings"]))

    def test_a_cut_that_keeps_an_unheard_filler_warns(self):
        # seg3 at 132.26: the only quiet moment before "I" is 131.82, before an
        # unheard filler (-18 dBFS); the dip after the filler is not quiet. The
        # short opened on the filler, PASS with a NOTE.
        loud = [(130.32, 131.78, -9.0), (131.78, 131.82, -29.0), (131.82, 131.85, -48.0),
                (131.85, 132.15, -18.0), (131.93, 131.95, -14.6), (132.15, 132.16, -27.6),
                (132.16, 132.18, -38.0), (132.18, 132.58, -10.0), (139.2, 139.7, -10.0)]
        lv = _QuietRoom(AuditRound13.SEG3_RUNS + [(0, 139.7, 140.2), (1, 140.2, 141.0)], loud,
                        120.0, 141.0)
        rep = {"warnings": []}
        _, s, _ = finish.place_clip(lv, AuditRound13()._seg3_words(), 132.26, 139.7, 0.08,
                                    0.4, rep)
        self.assertLess(s, 131.86)
        self.assertTrue(any(x.startswith("the clip starts with")
                            and "talk-level sound before its first word" in x
                            for x in rep["warnings"]))

    def test_a_cut_that_keeps_a_misclocked_next_word_warns(self):
        # ac44 at 111.68: "like," then "no," said 111.71-111.89 but clocked
        # 112.04-112.12; the gap's quiet moment is after the real "no,". The
        # short ended "I'm like, no," with only a NOTE (round 12 WARNed).
        runs = [(0, 104.5, 105.15), (1, 105.15, 111.90), (0, 111.90, 111.99), (1, 111.99, 113.0)]
        loud = [(105.15, 111.62, -15.0), (111.62, 111.68, -26.0), (111.68, 111.71, -32.0),
                (111.71, 111.87, -21.0), (111.87, 111.90, -30.0), (111.99, 113.0, -15.0)]
        lv = _Room(runs, loud, 100.0, 115.0, -40.0, -34.6, -52.9)
        words = _said(("So", 105.2, 105.4), ("Versus", 111.14, 111.38), ("I'm", 111.38, 111.56),
                      ("like,", 111.56, 111.68), ("no,", 112.04, 112.12), ("I'm", 112.16, 112.26),
                      ("not", 112.26, 112.4))
        rep = {"warnings": []}
        _, _, e = finish.place_clip(lv, words, 105.2, 111.68, 0.08, 0.4, rep)
        self.assertTrue(any(x.startswith("the clip ends with")
                            and "talk-level sound after its last word" in x
                            for x in rep["warnings"]))

    def test_an_end_never_runs_past_a_next_word_timed_as_an_instant(self):
        # seg4 at 136.68: "day," then "like" timed as an instant at 136.98 but
        # said before it, run straight on from "day,". settle_end took the
        # instant's clock as the next word's start and cut at 137.05, after
        # "like", PASS.
        runs = [(0, 129.5, 130.2), (1, 130.2, 136.97), (0, 136.97, 137.72), (1, 137.72, 140.0)]
        lv = _QuietRoom(runs, [(130.2, 136.95, -15.0), (136.95, 136.97, -36.0),
                               (137.72, 140.0, -15.0)], 125.0, 140.0)
        words = _said(("So", 130.28, 130.5), ("to", 135.84, 136.2), ("this", 136.2, 136.38),
                      ("day,", 136.38, 136.68), ("like", 136.98, 136.98), ("I", 136.98, 137.8))
        rep = {"warnings": []}
        _, _, e = finish.place_clip(lv, words, 130.28, 136.68, 0.08, 0.4, rep)
        self.assertLess(e, 136.97)                         # not after "like"
        self.assertTrue(any(x.startswith("the clip ends") for x in rep["warnings"]))

    def test_a_loud_bed_is_not_quiet_because_the_threshold_rose_over_it(self):
        # yt7hb at 10.0: a music bed at -17 dBFS between words at -4 to -6; the
        # threshold rose to -16 over it, and the NOTE called the bed quiet.
        n_runs = [(1, 0.0, 17.6), (0, 17.6, 18.2), (1, 18.2, 30.0)]
        loud = [(9.4, 9.82, -6.0), (10.0, 10.4, -4.0), (10.4, 17.5, -5.0), (17.6, 18.2, -60.0),
                (18.2, 30.0, -5.0)]
        words = _said(("one", 9.4, 9.82), ("two", 10.0, 10.4), ("three", 10.4, 16.9),
                      ("end.", 16.9, 17.5), ("next", 18.2, 18.5))
        rep = {"warnings": []}
        finish.place_clip(_Room(n_runs, loud, 0.0, 30.0, -17.0, -16.0, -50.0), words,
                          10.0, 17.5, 0.08, 0.4, rep)
        self.assertTrue(any(x.startswith("the clip starts in a") and "never goes quiet" in x
                            for x in rep["warnings"]))
        self.assertFalse(any("clip starts" in x and "quiet moment" in x
                             for x in rep.get("notes", [])))
        # Nor is a stretch the level could not measure, however low its peaks.
        u_runs = [(1, 0.0, 9.82), (2, 9.82, 10.0), (1, 10.0, 17.6), (0, 17.6, 18.2),
                  (1, 18.2, 30.0)]
        rep = {"warnings": []}
        finish.place_clip(_Room(u_runs, loud + [(9.82, 10.0, -60.0)], 0.0, 30.0, -17.0, -16.0,
                                -50.0), words, 10.0, 17.5, 0.08, 0.4, rep)
        self.assertFalse(any("clip starts" in x and "quiet moment" in x
                             for x in rep.get("notes", [])))

    def test_a_short_with_a_four_second_one_sided_guest_line_is_hard_panned(self):
        # lav_center_guestR, clip 41.6-56.4: 3.8 s of the guest's own talk (of
        # 8.1 s in that channel), 26 dB hard right; round 13 needed 5 s.
        self.assertTrue(video_qa.hard_panned({"own_talk_s": [0.0, 3.8], "talk_s": [5.5, 8.1]}))
        # Real stereo music in any 15 s: at most 0.4 s of one-sided "talk".
        self.assertFalse(video_qa.hard_panned({"own_talk_s": [0.4, 0.0], "talk_s": [13.0, 13.0]}))
        self.assertFalse(video_qa.hard_panned({"own_talk_s": [0.0, 2.2], "talk_s": [100.0, 104.0]}))

    def test_an_edge_at_a_pause_after_an_unheard_word_warns(self):
        # hum46 at 287.96: "stuff." then an unheard "right?" (-20 to -33 dBFS)
        # past a dip, then the pause the END adopted (it starts within 0.25 s).
        # The clip ended "All this stuff, right?", captions "ALL THIS STUFF.", PASS.
        runs = [(0, 279.0, 280.45), (1, 280.45, 287.92), (0, 287.92, 287.99),
                (1, 287.99, 288.2), (0, 288.2, 288.52), (1, 288.52, 290.0)]
        loud = [(280.45, 287.74, -20.0), (287.74, 287.88, -29.0), (287.88, 287.92, -36.0),
                (287.92, 287.99, -40.5), (287.99, 288.12, -20.0), (288.12, 288.2, -33.0),
                (288.52, 290.0, -20.0)]
        lv = _Room(runs, loud, 278.0, 290.0, -44.5, -41.2, -52.5)
        words = _said(("So", 280.5, 280.8), ("All", 287.0, 287.58), ("this", 287.58, 287.74),
                      ("stuff.", 287.74, 287.96), ("He's", 288.36, 288.66))
        rep = {"warnings": []}
        _, _, e = finish.place_clip(lv, words, 280.5, 287.96, 0.08, 0.4, rep)
        self.assertGreater(e, 288.2)                       # the pause the editor picked
        self.assertTrue(any(x.startswith("the clip ends with")
                            and "talk-level sound after its last word" in x
                            for x in rep["warnings"]))

    def test_an_end_settled_past_an_unheard_word_warns(self):
        # hum46 at 426.08 (the developer's own sweep after round 14): "parents'"
        # then an unheard "basement." (-23 to -27 dBFS) past a dip; settle_end
        # took the first pause after it and kept the word, PASS.
        runs = [(0, 419.0, 419.9), (1, 419.9, 426.57), (0, 426.57, 427.04), (1, 427.04, 429.0)]
        loud = [(419.9, 425.93, -20.0), (425.93, 426.06, -24.0), (426.06, 426.12, -33.0),
                (426.12, 426.16, -40.0), (426.16, 426.34, -27.0), (426.34, 426.37, -41.0),
                (426.37, 426.5, -23.0), (426.5, 426.57, -36.0), (427.04, 429.0, -20.0)]
        lv = _Room(runs, loud, 418.0, 429.0, -44.5, -40.6, -51.8)
        words = _said(("So", 420.0, 420.3), ("their", 425.78, 425.88),
                      ("parents'", 425.88, 426.08), ("and", 426.8, 427.16))
        rep = {"warnings": []}
        finish.place_clip(lv, words, 420.0, 426.08, 0.08, 0.4, rep)
        self.assertTrue(any(x.startswith("the clip ends with") for x in rep["warnings"]))

    def test_a_word_that_runs_on_past_its_clock_is_not_stray_talk(self):
        # A guard: the ASR ends "foundation." 0.3 s early; its sound runs on with
        # no dip, then a short stop burst after a closure, then the pause. The
        # tail is the word: no warning.
        runs = [(0, 9.0, 9.9), (1, 9.9, 15.42), (0, 15.42, 16.2), (1, 16.2, 18.0)]
        loud = [(9.9, 15.3, -12.0), (15.3, 15.34, -40.0), (15.34, 15.39, -18.0),
                (15.39, 15.42, -40.0), (16.2, 18.0, -12.0)]
        words = _said(("So", 10.0, 10.3), ("foundation.", 14.4, 15.0), ("Next", 16.2, 16.5))
        rep = {"warnings": []}
        _, _, e = finish.place_clip(_QuietRoom(runs, loud, 8.0, 18.0), words, 10.0, 15.0,
                                    0.08, 0.4, rep)
        self.assertGreater(e, 15.39)                       # the whole word
        self.assertEqual([x for x in rep["warnings"] if "ends" in x], [])

    def test_an_instants_sound_stops_at_a_pause_under_a_bed(self):
        # bed20 at 337.46: "It" timed as an instant (said 337.42-337.46) after
        # "maid." and a 0.16 s pause, under a bed 17 dB down. The walk ran back
        # over the bed into "maid." (337.06), hiding the pause.
        r = _Room([(1, 330.0, 345.0)], [(337.02, 337.15, -25.0), (337.42, 337.46, -21.0),
                                         (337.46, 337.56, -20.0)], 330.0, 345.0, -37.0,
                  -43.3, -49.8).r
        self.assertGreaterEqual(finish.instant_onset(r, 337.46, 337.16), 337.38)
        self.assertLessEqual(finish.instant_onset(r, 337.46, 337.16), 337.43)


class AuditRound15(unittest.TestCase):
    """Fifteenth independent audit, 25 Oct 2026: each test pins one finding.
    The levels are the measured ones at each edge, condensed."""

    def test_a_start_asked_just_before_a_soft_words_pause_keeps_the_word(self):
        # H1, ac44 at 230.18 ("right?"'s clock end) and 230.25: the level pause
        # (230.30-230.57) starts after the request, so the round-14 held-word
        # rule never ran; settle_start took the pause "It's" is clocked in and
        # cut in its middle (230.435): Whisper "Costing Uncle Dennis", PASS.
        lv = _Room(AuditRound14.AC_RUNS, AuditRound14.AC_LOUD, 225.0, 235.0, -40.0, -36.2, -51.4)
        for req in (230.18, 230.25):
            rep = {"warnings": []}
            _, s, _ = finish.place_clip(lv, _said(*AuditRound14.AC_WORDS), req, 231.08, 0.08,
                                        0.4, rep)
            self.assertLessEqual(s, 230.30, req)           # never inside "It's"
            self.assertTrue(any(x.startswith("the clip starts") for x in rep["warnings"]), req)
        # bedsn14 FULL (Descript's cue start 230.309), the pause from 230.36:
        # 230.464 with only a cue warning, Whisper "costing uncle dennis".
        runs = [(1, 225.0, 230.36), (0, 230.36, 230.57), (1, 230.57, 231.14),
                (0, 231.14, 231.6), (1, 231.6, 235.0)]
        loud = [(229.48, 229.8, -18.0), (229.97, 230.2, -17.0), (230.2, 230.36, -28.0),
                (230.36, 230.4, -36.7), (230.4, 230.43, -41.3), (230.43, 230.5, -32.0),
                (230.5, 230.57, -40.0), (230.57, 231.14, -18.0), (231.6, 235.0, -18.0)]
        ws = _said(("great,", 229.48, 229.8), ("right?", 230.06, 230.18), ("It's", 230.4, 230.52),
                   ("costing", 230.52, 230.86), ("Uncle", 230.86, 231.08), ("Dennis", 231.6, 231.9))
        for o in ws:
            o.update(cue_start=228.0, cue_end=230.309) if o["start"] < 230.3 else \
                o.update(cue_start=230.309, cue_end=233.0)
        rep = {"warnings": []}
        _, s, _ = finish.place_clip(_Room(runs, loud, 225.0, 235.0, -40.0, -35.2, -48.3), ws,
                                    230.309, 231.08, 0.08, 0.4, rep)
        self.assertLessEqual(s, 230.33)
        self.assertTrue(any(x.startswith("the clip starts where its first word is clocked")
                            for x in rep["warnings"]))

    # hum46 at 402.46 ("-spoken," clock end): "professional" clocked at 402.82
    # but said from 402.30 (a /p/ burst, voicing to 402.69), then a 30 ms
    # closure (402.70-402.73) and its /f/. No 0.15 s quiet in the gap: the
    # word-gap rule cut in the closure, dropping "pro", with only a NOTE.
    H2_RUNS = [(0, 397.4, 400.6), (1, 400.6, 401.74), (0, 401.74, 401.76), (1, 401.76, 402.1),
               (0, 402.1, 402.11), (1, 402.11, 402.7), (0, 402.7, 402.73), (1, 402.73, 404.2),
               (0, 404.2, 404.8), (1, 404.8, 410.0)]
    H2_LOUD = [(400.6, 401.7, -22.0), (401.7, 401.76, -41.0), (401.76, 402.05, -21.0),
               (402.05, 402.1, -36.0), (402.1, 402.11, -41.0), (402.11, 402.25, -18.0),
               (402.25, 402.3, -35.0), (402.3, 402.48, -20.0), (402.48, 402.69, -26.0),
               (402.69, 402.7, -34.0), (402.7, 402.73, -41.5), (402.73, 402.76, -37.5),
               (402.76, 402.8, -27.0), (402.8, 402.94, -36.5), (402.94, 404.2, -18.0),
               (404.8, 410.0, -20.0)]
    H2_WORDS = [("He's", 400.62, 401.0), ("so", 401.0, 401.6), ("well", 401.6, 401.92),
                ("-spoken,", 401.92, 402.46), ("professional", 402.82, 403.22),
                ("salesperson.", 403.22, 404.15), ("And", 404.85, 405.1), ("so", 405.1, 405.4)]

    def test_a_gap_cut_in_a_late_clocked_first_words_closure_warns(self):
        lv = _Room(self.H2_RUNS, self.H2_LOUD, 397.4, 410.0, -44.5, -40.6, -52.2)
        rep = {"warnings": []}
        _, s, _ = finish.place_clip(lv, _said(*self.H2_WORDS), 402.46, 404.15, 0.08, 0.4, rep)
        self.assertGreater(s, 402.6)                       # the cut stays; the edge is flagged
        self.assertTrue(any(x.startswith("the clip starts in a short dip right after")
                            for x in rep["warnings"]))
        # A guard: the same closure after a breath (-34.5 dBFS, 15 dB under the
        # word) leaves nothing word-loud out: a note, no warning.
        loud = [x for x in self.H2_LOUD if not 402.3 <= x[0] < 402.69] + [(402.3, 402.69, -34.5)]
        rep = {"warnings": []}
        _, s, _ = finish.place_clip(_Room(self.H2_RUNS, loud, 397.4, 410.0, -44.5, -40.6, -52.2),
                                    _said(*self.H2_WORDS), 402.46, 404.15, 0.08, 0.4, rep)
        self.assertEqual([x for x in rep["warnings"] if x.startswith("the clip starts")], [])
        self.assertTrue(any("clip starts" in x and "quiet moment" in x for x in rep["notes"]))

    def test_the_word_before_or_a_bed_is_not_dropped_talk(self):
        # The developer's sweeps after the H2 fix: of 19 distinct edges it
        # warned on, 2 were H2. The rest dropped the word before (its clock
        # ran early over the pause before it, "right?" before "She", or ended
        # early, "business." before "I") or a music bed between sentences.
        runs = [(1, 465.0, 467.95), (0, 467.95, 468.67), (1, 468.67, 468.9), (0, 468.9, 468.94),
                (1, 468.94, 471.0), (0, 471.0, 471.6), (1, 471.6, 474.0)]
        loud = [(465.0, 467.95, -18.0), (468.67, 468.9, -20.0), (468.94, 471.0, -15.0),
                (471.6, 474.0, -18.0)]
        words = _said(("now.", 467.5, 467.9), ("right?", 468.2, 468.8), ("She", 468.98, 469.2),
                      ("ran", 469.2, 469.5), ("home.", 469.5, 470.9), ("Then", 471.6, 471.9))
        rep = {"warnings": []}
        _, s, _ = finish.place_clip(_Room(runs, loud, 465.0, 475.0, -44.5, -40.6, -52.2), words,
                                    468.98, 470.9, 0.08, 0.4, rep)
        self.assertGreater(s, 468.89)                      # in the dip after "right?"
        self.assertEqual([x for x in rep["warnings"] if "short dip" in x], [])
        self.assertTrue(any("clip starts" in x and "quiet moment" in x for x in rep["notes"]))
        # A bed 14 dB under the next word, between "beautiful." and "And" (a
        # public short); "And" said from 19.88, clocked 19.96 on its decay.
        runs = [(1, 15.0, 19.84), (0, 19.84, 19.87), (1, 19.87, 23.0), (0, 23.0, 24.0),
                (1, 24.0, 25.0)]
        loud = [(15.0, 19.48, -15.0), (19.48, 19.52, -42.0), (19.52, 19.84, -30.0),
                (19.84, 19.87, -50.0), (19.87, 19.96, -16.0), (19.96, 20.02, -24.0),
                (20.02, 23.0, -16.0), (24.0, 25.0, -16.0)]
        words = _said(("really", 18.86, 19.02), ("beautiful.", 19.02, 19.34), ("And", 19.96, 20.02),
                      ("then", 20.02, 20.3), ("also.", 20.3, 22.9), ("Next", 24.0, 24.3))
        rep = {"warnings": []}
        _, s, _ = finish.place_clip(_QuietRoom(runs, loud, 14.0, 26.0, -70.0, -46.0), words,
                                    19.96, 22.9, 0.08, 0.4, rep)
        self.assertGreater(s, 19.8)
        self.assertLess(s, 19.88)                          # before "And"
        self.assertEqual([x for x in rep["warnings"] if "short dip" in x], [])
        # The word before's own last syllable, past a closure, ending 0.08 s
        # after its clock (the replay's "score." at 588.10, then "So").
        runs = [(0, 586.0, 586.5), (1, 586.5, 588.19), (0, 588.19, 588.24), (1, 588.24, 588.95),
                (0, 588.95, 589.4), (1, 589.4, 591.0)]
        loud = [(586.5, 587.84, -18.0), (587.84, 587.94, -21.0), (587.94, 587.97, -37.0),
                (587.97, 588.15, -13.0), (588.15, 588.19, -22.0), (588.19, 588.24, -52.0),
                (588.24, 588.31, -35.0), (588.31, 588.95, -13.0), (589.4, 591.0, -15.0)]
        words = _said(("confidence", 587.56, 587.84), ("score.", 587.84, 588.1), ("So", 588.34, 588.4),
                      ("you", 588.4, 588.88), ("see.", 589.4, 590.9))
        rep = {"warnings": []}
        _, s, _ = finish.place_clip(_QuietRoom(runs, loud, 585.0, 592.0, -70.0, -50.0), words,
                                    588.34, 590.9, 0.08, 0.4, rep)
        self.assertGreater(s, 588.18)
        self.assertLess(s, 588.25)                         # in the dip after "score."
        self.assertEqual([x for x in rep["warnings"] if "short dip" in x], [])

    def test_a_burst_long_after_the_word_before_is_not_a_dropped_syllable(self):
        # My real-clip renders after round 15 (cocsv, a public podcast promo, at
        # 12.92): "from" clocked to 11.82, then 1.1 s the ASR heard nothing in
        # (a music bed: Whisper on it alone writes "Thanks for watching!"),
        # "Off" clocked at 12.92. The gap cut at 12.90 after a bed burst
        # (12.69-12.87) and warned that "Off" may have lost its start.
        runs = [(0, 9.0, 10.09), (1, 10.09, 12.05), (0, 12.05, 12.08), (1, 12.08, 12.19),
                (0, 12.19, 12.24), (1, 12.24, 12.61), (0, 12.61, 12.64), (1, 12.64, 12.91),
                (0, 12.91, 12.98), (1, 12.98, 14.64), (0, 14.64, 15.2), (1, 15.2, 16.5)]
        loud = [(10.09, 10.48, -30.0), (10.57, 10.88, -22.4), (10.88, 11.06, -14.0),
                (11.06, 11.39, -17.0), (11.39, 11.67, -14.1), (11.67, 11.8, -26.0),
                (11.8, 11.98, -20.9), (11.98, 12.05, -30.0), (12.05, 12.08, -38.0),
                (12.08, 12.13, -24.0), (12.13, 12.19, -30.5), (12.19, 12.24, -36.0),
                (12.24, 12.26, -26.0), (12.26, 12.33, -20.0), (12.33, 12.39, -23.3),
                (12.39, 12.48, -26.1), (12.48, 12.61, -29.5), (12.61, 12.62, -33.7),
                (12.62, 12.63, -39.5), (12.63, 12.64, -36.9), (12.64, 12.68, -30.1),
                (12.68, 12.69, -27.1), (12.69, 12.71, -20.5), (12.71, 12.72, -17.8),
                (12.72, 12.82, -21.6), (12.82, 12.87, -23.7), (12.87, 12.89, -27.1),
                (12.89, 12.91, -31.2), (12.91, 12.94, -33.6), (12.94, 12.97, -37.7),
                (12.97, 12.98, -35.3), (12.98, 13.23, -23.9), (13.23, 13.41, -29.8),
                (13.41, 13.48, -38.0), (13.48, 13.62, -12.0), (13.62, 14.64, -15.0),
                (15.2, 16.5, -15.0)]
        r = _Room(runs, loud, 8.0, 17.0, -37.0, -32.8, -48.5).r
        self.assertEqual(finish.dropped_talk(r, 12.9, 11.82, -12.1, 11.22), 0.0)

    def test_a_start_at_the_previous_words_clock_end_does_not_reach_back_over_it(self):
        # H3, the clean mix at 56.16 ("Look,"'s clock end; said 56.03-56.35):
        # the pause before "Look," ends within the 0.25 s reach, so the clip
        # opened on "Look,", PASS (51 of 830 such starts kept the word before).
        runs = [(1, 54.0, 55.01), (0, 55.01, 56.03), (1, 56.03, 56.38), (0, 56.38, 56.47),
                (1, 56.47, 57.8), (0, 57.8, 58.3), (1, 58.3, 60.0)]
        loud = [(54.0, 55.01, -19.0), (56.03, 56.05, -30.0), (56.05, 56.21, -18.0),
                (56.21, 56.28, -31.0), (56.28, 56.35, -43.0), (56.35, 56.38, -50.0),
                (56.38, 56.47, -65.0), (56.47, 56.49, -40.0), (56.49, 57.8, -19.0),
                (58.3, 60.0, -19.0)]
        words = _said(("it.", 54.5, 54.95), ("Look,", 55.8, 56.16), ("digital", 56.64, 56.64),
                      ("marketing,", 56.64, 56.84), ("is", 56.9, 57.1), ("hard.", 57.1, 57.78),
                      ("So", 58.3, 58.5))
        rep = {"warnings": []}
        _, s, _ = finish.place_clip(_QuietRoom(runs, loud, 50.0, 60.0, -83.0, -53.4), words,
                                    56.16, 57.78, 0.08, 0.4, rep)
        self.assertGreater(s, 56.35)                       # after "Look,"
        self.assertLess(s, 56.47)                          # before "digital"
        self.assertEqual([x for x in rep["warnings"] if "starts" in x], [])
        # ac44 at 265.16 ("guy,"'s clock end, 0.04 s past the AC "pause" that
        # holds its soft start): the clip opened "guy, but you can see".
        runs = [(1, 260.2, 264.7), (0, 264.7, 265.12), (1, 265.12, 265.23), (0, 265.23, 265.75),
                (1, 265.75, 268.3), (0, 268.3, 268.9), (1, 268.9, 270.0)]
        loud = [(260.2, 264.7, -24.0), (264.7, 264.98, -37.0), (264.98, 265.07, -31.0),
                (265.07, 265.12, -36.0), (265.12, 265.23, -28.0), (265.23, 265.75, -41.0),
                (265.75, 268.3, -21.0), (268.3, 268.9, -43.0), (268.9, 270.0, -21.0)]
        words = _said(("like", 264.54, 264.72), ("this", 264.72, 264.9), ("guy,", 264.9, 265.16),
                      ("but", 265.62, 265.84), ("you", 265.84, 266.06), ("see.", 267.8, 268.24),
                      ("And", 268.95, 269.2))
        rep = {"warnings": []}
        _, s, _ = finish.place_clip(_Room(runs, loud, 260.2, 270.0, -43.0, -34.6, -52.1), words,
                                    265.16, 268.24, 0.08, 0.4, rep)
        self.assertGreater(s, 265.23)                      # after "guy,"
        self.assertLess(s, 265.75)

    def test_a_word_between_that_runs_into_the_next_is_kept_whole_and_warned(self):
        # My cue sweep after the reach fix (the round-12 auditor's LIGHT cue
        # starts, edges at the nearest Whisper word): "And" clocked 1.00-1.36
        # from inside the pause, said 1.29-1.42 straight into "then,"; asked
        # for at 1.36, the start was cut inside "And" with an "unbroken talk"
        # WARN, on 20 to 28 cue starts a mix. A whole word is the lesser harm.
        runs = [(0, 0.16, 1.29), (1, 1.29, 5.33), (0, 5.33, 5.8), (1, 5.8, 7.0)]
        loud = [(1.29, 5.33, -15.0), (5.8, 7.0, -15.0)]
        words = _said(("And", 1.0, 1.36), ("then,", 1.36, 1.6), ("once", 1.88, 1.94),
                      ("that", 1.94, 2.84), ("done.", 4.9, 5.3), ("Next", 5.8, 6.0))
        rep = {"warnings": []}
        _, s, _ = finish.place_clip(_QuietRoom(runs, loud, 0.0, 8.0, -80.0, -53.4), words,
                                    1.36, 5.3, 0.08, 0.4, rep)
        self.assertLess(s, 1.29)                           # "And" whole
        self.assertGreater(s, 0.16)
        self.assertTrue(any(x.startswith('the clip starts at the pause before "And"')
                            for x in rep["warnings"]))
        self.assertFalse(any("unbroken" in x for x in rep["warnings"]))

    def test_an_end_at_the_next_words_clock_start_does_not_reach_over_it(self):
        # H3's mirror, fan47 ending at 213.4 ("Proof"'s clock start): the pause
        # after "Proof" (213.57) begins within the reach; the clip ended
        # "...stuff, right? Proof", PASS.
        runs = [(0, 208.3, 209.0), (1, 209.0, 212.87), (0, 212.87, 212.9), (1, 212.9, 213.0),
                (0, 213.0, 213.08), (1, 213.08, 213.24), (0, 213.24, 213.33), (1, 213.33, 213.57),
                (0, 213.57, 213.73), (1, 213.73, 215.0), (0, 215.0, 215.6), (1, 215.6, 217.0)]
        loud = [(209.0, 212.81, -18.0), (212.81, 212.87, -30.0), (212.87, 212.9, -38.3),
                (212.9, 212.98, -28.0), (212.98, 213.0, -33.0), (213.0, 213.04, -38.2),
                (213.04, 213.08, -41.5), (213.08, 213.09, -31.3), (213.09, 213.19, -19.0),
                (213.19, 213.22, -29.0), (213.22, 213.25, -36.2), (213.25, 213.3, -39.5),
                (213.3, 213.38, -34.0), (213.38, 213.5, -22.0), (213.5, 213.57, -32.0),
                (213.57, 213.73, -38.0), (213.73, 215.0, -20.0), (215.6, 217.0, -20.0)]
        words = _said(("So", 209.1, 209.4), ("kind", 212.64, 212.74), ("of", 212.74, 212.86),
                      ("stuff,", 212.86, 213.02), ("right?", 213.16, 213.2), ("Proof", 213.4, 213.48),
                      ("of", 213.48, 213.7), ("that", 213.7, 213.96), ("works.", 213.96, 214.9),
                      ("Next", 215.6, 215.9))
        rep = {"warnings": []}
        _, _, e = finish.place_clip(_Room(runs, loud, 208.3, 217.0, -42.0, -36.9, -53.2), words,
                                    209.1, 213.4, 0.08, 0.4, rep)
        self.assertLess(e, 213.38)                         # before "Proof"
        self.assertTrue(any(x.startswith("the clip ends") for x in rep["warnings"]))

    def test_a_click_in_a_quiet_pause_does_not_make_its_word_talk(self):
        # L1, seg5 at 77.7: "It" clocked 77.70-77.92 inside a quiet 0.23 s pause
        # with a 20 ms click at 77.82; the held-word rule called the pause talk
        # and cut at 77.62 in "choose."'s decay, warning "unbroken talk".
        runs = [(0, 75.0, 76.67), (1, 76.67, 77.7), (0, 77.7, 77.93), (1, 77.93, 79.5),
                (0, 79.5, 80.0), (1, 80.0, 81.0)]
        loud = [(76.67, 77.62, -20.0), (77.62, 77.7, -38.0), (77.81, 77.82, -54.2),
                (77.82, 77.83, -37.4), (77.83, 77.84, -30.2), (77.84, 77.85, -49.3),
                (77.87, 77.88, -39.4), (77.93, 77.94, -41.7), (77.94, 79.5, -15.0),
                (80.0, 81.0, -15.0)]
        words = _said(("you", 77.2, 77.32), ("choose.", 77.32, 77.62), ("It", 77.7, 77.92),
                      ("can", 77.92, 77.98), ("be", 77.98, 78.1), ("anything.", 78.1, 79.45),
                      ("Then", 80.0, 80.3))
        rep = {"warnings": []}
        _, s, _ = finish.place_clip(_QuietRoom(runs, loud, 72.7, 82.0, -70.0, -46.6), words,
                                    77.7, 79.45, 0.08, 0.4, rep)
        self.assertGreaterEqual(s, 77.7)                   # in the editor's pause
        self.assertLess(s, 77.93)
        self.assertEqual([x for x in rep["warnings"] if "starts" in x], [])

    def test_a_start_at_an_instant_in_a_gap_that_never_goes_quiet_is_before_its_sound(self):
        # L3, bedsn14 at 56.64: "digital" timed as an instant (said from 56.43)
        # under a bed; the gap never goes quiet, the start stayed at the clock
        # less the pad (56.56), 0.13 s into the word.
        runs = [(0, 50.0, 54.8), (1, 54.8, 55.58), (0, 55.58, 56.04), (1, 56.04, 56.37),
                (0, 56.37, 56.41), (1, 56.41, 57.8), (0, 57.8, 58.3), (1, 58.3, 60.0)]
        loud = [(54.8, 55.58, -15.0), (55.58, 56.04, -38.5), (56.04, 56.22, -15.0),
                (56.22, 56.31, -26.0), (56.31, 56.36, -31.6), (56.36, 56.39, -36.7),
                (56.39, 56.41, -38.0), (56.41, 56.43, -31.9), (56.43, 56.49, -27.0),
                (56.49, 57.8, -15.0), (58.3, 60.0, -15.0)]
        words = _said(("it.", 55.0, 55.5), ("Look,", 55.8, 56.16), ("digital", 56.64, 56.64),
                      ("marketing,", 56.64, 56.82), ("is", 56.9, 57.1), ("hard.", 57.1, 57.78),
                      ("So", 58.3, 58.5))
        rep = {"warnings": []}
        _, s, _ = finish.place_clip(_Room(runs, loud, 50.0, 60.0, -45.0, -36.4, -50.9), words,
                                    56.64, 57.78, 0.08, 0.4, rep)
        self.assertLessEqual(s, 56.36)                     # before "digital"'s sound
        self.assertTrue(any(x.startswith("the clip starts") and "never goes quiet" in x
                            for x in rep["warnings"]))

    def test_an_end_keeps_its_pause_when_the_next_words_clock_spans_it(self):
        # The developer's sweep after the H3 fix: Whisper snaps a word's start
        # to the end of the word before, so "This" (said after the pause) is
        # clocked 248.52-249.22, across it. The fix took it for a word between
        # the request and the pause and cut "right?" at its clock, WARN.
        runs = [(0, 244.0, 244.5), (1, 244.5, 248.64), (0, 248.64, 249.1), (1, 249.1, 250.5),
                (0, 250.5, 251.0)]
        loud = [(244.5, 248.52, -15.0), (248.52, 248.64, -40.0), (249.1, 250.5, -15.0)]
        words = _said(("So", 244.5, 244.8), ("stuff,", 248.04, 248.24), ("right?", 248.32, 248.52),
                      ("This", 248.52, 249.22), ("guy", 249.22, 249.44), ("started", 249.44, 250.4))
        rep = {"warnings": []}
        _, _, e = finish.place_clip(_QuietRoom(runs, loud, 243.0, 252.0, -76.0, -51.8), words,
                                    244.5, 248.52, 0.08, 0.4, rep)
        self.assertGreater(e, 248.64)                      # in the pause, "right?" whole
        self.assertLess(e, 249.1)
        self.assertEqual([x for x in rep["warnings"] if "ends" in x], [])

    def test_an_end_keeps_its_pause_when_the_word_between_is_only_a_decay(self):
        # The developer's sweep after the reach fix: under reverb (rev7),
        # "Just" is clocked 273.78-273.90, into the reverb tail of "things.",
        # 0.5 s before it is said after the pause. The fix took it for a word
        # between the request and the pause and cut "things." at its clock,
        # WARN. The level there only decays: no sound of its own.
        runs = [(0, 268.8, 269.4), (1, 269.4, 274.02), (0, 274.02, 274.27), (1, 274.27, 276.0)]
        loud = [(269.4, 273.7, -18.0), (273.7, 273.8, -30.0), (273.8, 273.9, -36.0),
                (273.9, 274.02, -40.0), (274.27, 276.0, -18.0)]
        words = _said(("So", 269.4, 269.6), ("people", 273.04, 273.4), ("things.", 273.4, 273.78),
                      ("Just", 273.78, 273.9), ("fly", 273.9, 274.46), ("around,", 274.46, 274.84))
        rep = {"warnings": []}
        _, _, e = finish.place_clip(_Room(runs, loud, 268.0, 277.0, -46.0, -42.2, -46.4), words,
                                    269.4, 273.78, 0.08, 0.4, rep)
        self.assertGreater(e, 274.02)                      # in the pause, the tail kept
        self.assertLess(e, 274.27)
        # (since round 16 the receipt says the tail may hold a word: seg4's
        # soft "I would" looked the same and was a word)
        ends = [x for x in rep["warnings"] if "ends" in x]
        self.assertEqual(len(ends), 1)
        self.assertTrue(ends[0].startswith('the clip ends in a pause after "Just", clocked inside'))

    def test_a_word_clocked_into_a_quiet_pause_after_it_was_said_is_found(self):
        # The developer's sweep after the L1 fix: seg6's "And he's" said
        # 40.06-40.54, clocked "And" 40.54-40.90 inside the quiet pause after
        # it. A 10 ms fragment of the decay sat between the sound and the
        # pause, and one noise peak 6 dB over the pause's median: the word
        # read as sound of its own, not as talk, and the clip opened on
        # "like,", PASS.
        runs = [(1, 38.4, 39.23), (0, 39.23, 39.63), (1, 39.63, 40.54), (0, 40.54, 40.55),
                (1, 40.55, 40.56), (0, 40.56, 41.11), (1, 41.11, 41.39), (0, 41.39, 41.47),
                (1, 41.47, 42.42), (0, 42.42, 43.0), (1, 43.0, 44.0)]
        loud = [(38.4, 39.2, -16.0), (39.2, 39.23, -35.0), (39.63, 40.03, -12.0),
                (40.03, 40.4, -15.0), (40.4, 40.49, -25.0), (40.49, 40.51, -31.0),
                (40.51, 40.52, -41.5), (40.52, 40.54, -35.5), (40.54, 40.55, -51.8),
                (40.55, 40.56, -40.9), (40.56, 40.57, -49.5), (40.58, 40.6, -49.3),
                (40.7, 40.71, -67.0), (41.1, 41.11, -55.5), (41.11, 41.39, -20.0),
                (41.47, 42.42, -15.0), (43.0, 44.0, -15.0)]
        words = _said(("jump", 38.62, 38.78), ("training.", 38.8, 39.12), ("And", 40.54, 40.9),
                      ("he's", 40.9, 41.26), ("like,", 41.26, 41.36), ("just", 41.48, 41.62),
                      ("call", 42.0, 42.16), ("him.", 42.16, 42.4), ("So", 43.0, 43.2))
        rep = {"warnings": []}
        _, s, _ = finish.place_clip(_QuietRoom(runs, loud, 37.0, 45.0, -73.0, -47.7), words,
                                    40.54, 42.4, 0.08, 0.4, rep)
        self.assertLessEqual(s, 39.63)                     # before "And he's"
        self.assertGreater(s, 39.23)
        self.assertTrue(any("first word is clocked in silence" in x for x in rep.get("notes", [])))

    def test_a_level_stretch_serves_only_moments_well_inside_it(self):
        # The floors the clip rules read span 2.5 s each side of a cut; a
        # stretch measured for another clip that ends 1.5 s past the cut read
        # fan47's floor 4 dB high and lost the warning above (the developer's
        # sweep after round 15).
        calls = []
        orig = finish.level_runs
        finish.level_runs = lambda src, style, info, a, b, words=None: calls.append((a, b)) or \
            finish.Runs([(1, a, b)], a)
        try:
            lv = finish.LevelRuns("x.wav", {}, {"duration_s": 600.0})
            first = lv.near(100.0)
            self.assertIs(lv.near(102.4), first)
            self.assertIsNot(lv.near(103.0), first)       # within 2.5 s of its end
            self.assertIs(lv.near(1.0), lv.near(0.2))      # the file's own edge
        finally:
            finish.level_runs = orig
        self.assertEqual(calls[:2], [(95.0, 105.0), (98.0, 108.0)])


class _Exact:
    """Level runs for place_clip from a real file's own 10 ms peaks: `segs`
    [(t0, [dB, ...])] at their times, `loud` [(a, b, dB)] elsewhere, and
    `floor_db` around them; the silence threshold at `thr_db` over a base of
    `base_db`."""
    def __init__(self, runs, segs, base, total, floor_db, thr_db, base_db, loud=()):
        n = int(round((total - base) / 0.01))
        peaks = [floor_db] * n
        for a, b, db in loud:
            for k in range(int(round((a - base) / 0.01)), int(round((b - base) / 0.01))):
                peaks[k] = db
        for t0, ps in segs:
            k0 = int(round((t0 - base) / 0.01))
            peaks[k0:k0 + len(ps)] = ps
        self.r = finish.Runs(runs, base, [thr_db] * (n // 50 + 1), 0.5, base_db, peaks, 0.01)
        self.total, self.style = total + 100.0, finish.load_style(None)

    def near(self, t):
        return self.r


class AuditRound16(unittest.TestCase):
    """Sixteenth independent audit, 25 Oct 2026: each test pins one finding,
    on the real files' own 10 ms peaks around the edge."""

    def _place(self, lv, words, a, b):
        rep = {"warnings": []}
        _, s, e = finish.place_clip(lv, words, a, b, 0.08, 0.4, rep)
        return s, e, rep

    # H1, How_to (room noise): "painting," clocked 129.94-130.56 but said to
    # 130.33; a dip to -48 dBFS; "embroidery." said from 130.41, clocked
    # 130.70-130.96; the pause after it from 130.76. Asked to end at
    # "painting,"'s clock end, the clip kept "embroidery." with no warning
    # (the dip lay before the window the reach rule looked in), and the
    # captions left it out.
    HOWTO = [-26, -28, -25, -26, -26, -26, -23, -21, -24, -25, -25, -27, -25, -28, -28, -29, -31, -26,
             -23, -28, -31, -30, -31, -33, -38, -39, -40, -45, -47, -43, -46, -46, -45, -48, -49, -48, -52,
             -51, -51, -49, -48, -47, -47, -44, -43, -44, -42, -41, -39, -38, -34, -32, -33, -34, -35, -34,
             -34, -34, -35, -36, -35, -37, -40, -45, -46, -48, -49, -49, -50, -47, -46, -42, -42, -39, -33,
             -32, -33, -29, -32, -30, -29, -29, -29, -29, -30, -30, -31, -30, -29, -30, -30, -32, -33, -36,
             -36, -37, -40, -37, -38, -39, -39, -39, -38, -40, -43, -41, -44, -43, -43, -44, -43, -42, -38,
             -38, -37, -37, -37, -38, -37, -37, -33, -34, -35, -37, -36, -36, -36, -38, -41, -38, -39, -40,
             -38, -37, -37, -37, -37, -38, -36, -35, -37, -35, -35, -35, -35, -34, -34, -34, -35, -35, -36,
             -35, -35, -34, -35, -36, -36, -36, -38, -40, -39, -39, -37, -36, -36, -37, -36, -38, -38, -35,
             -34, -35, -34, -34, -34, -35, -36, -37, -36, -39, -38, -39, -44, -46, -47, -47, -48, -47, -48,
             -46, -47, -47, -45, -46, -35, -31, -35, -30, -31, -29]

    def test_an_end_keeps_no_word_after_a_dip_the_clock_hides(self):
        runs = [(0, 127.0, 127.5), (1, 127.5, 129.97), (0, 129.97, 130.13), (1, 130.13, 130.33),
                (0, 130.33, 130.41), (1, 130.41, 130.76), (0, 130.76, 131.64), (1, 131.64, 133.0)]
        lv = _Exact(runs, [(129.7, self.HOWTO)], 125.0, 135.0, -48.0, -44.6, -54.5,
                    loud=[(127.5, 129.7, -20.0), (131.7, 133.0, -20.0)])
        words = _said(("So", 127.5, 127.8), ("doing?", 129.76, 129.9), ("I'm", 129.94, 129.94),
                      ("art", 129.94, 129.94), ("painting,", 129.94, 130.56),
                      ("embroidery.", 130.7, 130.96), ("Art", 131.64, 131.81))
        for end in (130.56, 130.7):
            _, e, rep = self._place(lv, [dict(w) for w in words], 127.5, end)
            kept = e > 130.45
            # Kept, the receipt says so and the captions carry it; else cut before it.
            self.assertEqual(kept, any(x.startswith('the clip ends at the pause after "embroidery."')
                                       for x in rep["warnings"]))
            if kept:
                self.assertEqual(rep["clip_word_span"][1][0], "embroidery.")

    # H1, seg4: "like," then a 50 ms dip, then "kill him." said from 179.60,
    # "kill" clocked 179.72-179.74. Asked to end at "kill"'s clock start, the
    # 20 ms clock made "kill" the clip's last word: no warning, "kill him."
    # in the sound, out of the captions.
    KILL = [-75, -76, -76, -74, -68, -44, -23, -17, -12, -10, -9, -11, -12, -13, -15, -13, -18, -29, -33,
            -40, -47, -56, -60, -62, -47, -26, -35, -27, -27, -30, -21, -12, -11, -10, -10, -10, -9, -10,
            -10, -11, -11, -11, -11, -12, -12, -12, -13, -13, -15, -17, -19, -21, -20, -21, -24, -26, -28,
            -28, -32, -36, -43, -47, -51, -59, -62, -60, -71, -68, -67, -76, -68, -72, -71, -74, -73, -73,
            -73, -75, -73, -72, -68, -47, -41, -25, -19, -18, -16, -14, -12, -10, -10, -10, -10, -10, -10]

    def test_an_end_at_a_short_clocked_next_word_does_not_keep_it_unwarned(self):
        runs = [(0, 176.5, 177.0), (1, 177.0, 178.94), (0, 178.94, 179.41), (1, 179.41, 179.55),
                (0, 179.55, 179.6), (1, 179.6, 179.96), (0, 179.96, 180.17), (1, 180.17, 181.05)]
        lv = _Exact(runs, [(179.35, self.KILL)], 175.0, 183.0, -76.0, -46.8, -46.8,
                    loud=[(177.0, 178.94, -12.0), (180.3, 181.05, -10.0)])
        words = _said(("and", 177.0, 177.2), ("he's", 179.32, 179.46), ("like,", 179.46, 179.58),
                      ("kill", 179.72, 179.74), ("him.", 179.74, 180.08), ("He's", 180.22, 180.34),
                      ("like,", 180.34, 180.46))
        _, e, rep = self._place(lv, words, 177.0, 179.72)
        if e > 179.62:
            self.assertTrue(any(x.startswith('the clip ends at the pause after "kill him."')
                                for x in rep["warnings"]))
            self.assertEqual(rep["clip_word_span"][1][0], "him.")

    # H1, seg1: "year." then 0.13 s of quiet, then "Yeah." said 56.70-56.96,
    # clocked 56.88-56.90. Its 20 ms clock kept it out of the reach rule's
    # words between: asked to end at its clock start, the clip ended
    # "...last year. Yeah.", PASS.
    YEAH = [-9, -10, -6, -14, -9, -11, -10, -11, -12, -13, -13, -16, -15, -11, -13, -11, -10, -11, -11,
            -11, -11, -11, -12, -14, -16, -19, -22, -26, -28, -31, -32, -33, -34, -33, -40, -42, -23, -22,
            -20, -19, -17, -16, -15, -15, -15, -15, -15, -14, -15, -16, -16, -18, -24, -27, -35, -40, -44,
            -53, -63, -62, -64, -65, -64, -66, -65, -71, -64, -41, -34, -53, -41, -34, -29, -24, -20, -16,
            -14, -13, -11, -12, -10, -13, -14, -12, -19, -22, -22, -23, -23, -26, -24, -27, -26, -27, -35,
            -40, -49, -56, -64, -66, -67, -68, -71, -73, -71, -71, -72, -71, -75, -71, -71, -72, -74, -73]

    def test_an_end_at_a_next_words_20ms_clock_stops_before_its_sound(self):
        runs = [(0, 54.5, 55.0), (1, 55.0, 56.57), (0, 56.57, 56.7), (1, 56.7, 56.96), (0, 56.96, 57.59),
                (1, 57.59, 58.62)]
        lv = _Exact(runs, [(56.0, self.YEAH)], 53.0, 60.0, -74.0, -46.8, -46.8,
                    loud=[(55.0, 56.0, -10.0), (57.59, 58.62, -11.0)])
        words = _said(("So", 55.0, 55.3), ("last", 55.72, 56.12), ("year.", 56.12, 56.52),
                      ("Yeah.", 56.88, 56.9), ("Yeah,", 57.6, 57.7), ("I", 57.72, 57.82))
        _, e, rep = self._place(lv, words, 55.0, 56.88)
        self.assertGreater(e, 56.52)                       # "year." whole
        self.assertLessEqual(e, 56.7)                      # "Yeah." not begun

    # H1 (d), youtube-7Hb under a loud bed: "concept," then "or" said
    # 32.43-32.65 and clocked 32.62-32.66, at the end of its own sound; the
    # pause after it (32.65) started inside settle_end's 0.05 s slack past
    # "or"'s clock start, so the clip ended "...concept, or", PASS.
    OR = [-3, -5, -4, -6, -5, -8, -6, -10, -7, -10, -10, -12, -13, -16, -20, -21, -20, -22, -21, -21, -20,
          -24, -23, -16, -20, -20, -19, -17, -13, -4, -5, -5, -4, -5, -5, -8, -10, -15, -15, -15, -15, -15,
          -15, -14, -15, -15, -16, -12, -14, -13, -16, -15, -15, -17, -18, -21, -13, -10, -11, -11, -9, -10,
          -14, -13, -17, -15, -16, -17, -18, -16, -20, -22, -18, -24, -20, -22, -24, -21, -26, -20, -21,
          -24, -19, -16, -14, -14, -15, -11, -12, -11, -11, -11, -9, -10, -9, -10, -9, -9, -8, -9, -8, -7,
          -11, -14, -15, -18, -19, -19, -19, -18, -20, -20, -19, -21, -21, -20, -21, -20, -20, -20, -20,
          -20, -19, -20, -21, -19, -20, -20, -20, -20, -22, -20, -19, -20, -19, -21, -21, -21, -21, -21,
          -22, -15, -9, -5, -2, -2, -4, -9, -9, -10]

    def test_an_end_never_adopts_the_pause_after_a_next_word_said_before_it(self):
        runs = [(0, 29.5, 30.0), (1, 30.0, 31.74), (0, 31.74, 31.83), (1, 31.83, 31.84), (0, 31.84, 31.87),
                (1, 31.87, 32.14), (0, 32.14, 32.16), (1, 32.16, 32.3), (0, 32.3, 32.43), (1, 32.43, 32.65),
                (0, 32.65, 33.01), (1, 33.01, 33.36), (0, 33.36, 33.47), (1, 33.47, 34.5)]
        lv = _Exact(runs, [(31.6, self.OR)], 27.5, 37.5, -22.0, -18.0, -40.8,
                    loud=[(30.0, 31.6, -6.0), (33.1, 34.5, -8.0)])
        words = _said(("First", 30.0, 30.3), ("innate", 31.44, 31.7), ("concept,", 31.7, 32.3),
                      ("or", 32.62, 32.66), ("being", 32.66, 33.3), ("tough", 33.3, 33.74))
        for end in (32.3, 32.62):
            _, e, rep = self._place(lv, [dict(w) for w in words], 30.0, end)
            self.assertTrue(e <= 32.45 or any("clip ends" in x for x in rep["warnings"]))

    # H1 (c), copefl under a loud bed (-18 dBFS): "pocketbooks," then "or"
    # (-10 dBFS) and "bags." before the bed alone; the bed never lets the
    # level dip and rise 9 dB, so "or bags." read as a decay and the clip
    # ended on them, PASS. (The dip to the rise fell 0.01 dB short of 9 dB: these
    # peaks keep two decimals.)
    BAGS = [-19.91, -17.28, -16.73, -18.32, -19.08, -21.08, -13.19, -20.84, -17.8, -19.75, -8.22,
            -0.77, -0.08, -0.89, -1.64, -2.19, -3.2, -0.29, -6.92, -14.13, -19.02, -17.96, -17.3,
            -18.55, -19.21, -20.32, -16.63, -20.36, -10.9, -10.36, -9.93, -11.75, -14.66, -16.8,
            -15.43, -15.08, -16.48, -15.93, -19.19, -17.48, -17.23, -15.65, -18.25, -11.26, -7.64,
            -6.68, -6.97, -6.96, -6.53, -8.13, -9.49, -12.22, -14.41, -16.7, -14.84, -17.73, -22.88,
            -18.58, -18.36, -14.96, -14.62, -14.18, -14.25, -10.74, -13.32, -16.2, -16.63, -16.68,
            -16.0, -17.37, -16.87, -17.57, -19.47, -14.76, -13.42, -13.43, -8.93, -11.45, -10.1,
            -12.02, -12.2, -13.5, -14.5, -20.6, -16.77, -22.3, -17.37, -21.13, -18.34, -18.16,
            -18.19, -9.72, -8.25, -9.37, -9.37, -9.35, -9.71, -10.34, -12.84, -11.38, -14.41,
            -16.24, -14.84, -15.55, -17.36, -16.03, -18.36, -18.44, -17.59, -20.13, -18.21, -18.79,
            -15.49, -17.82, -18.08, -17.59, -19.39, -19.37, -17.89, -18.78, -18.28, -17.42, -18.29,
            -20.93, -19.24, -19.15, -19.09, -18.96, -16.68, -18.89, -17.15, -18.27, -19.59, -14.91,
            -16.08, -16.16, -16.23, -16.49, -16.75, -16.67]

    def test_an_end_under_a_bed_does_not_take_words_for_a_decay(self):
        runs = [(0, 41.5, 42.0), (1, 42.0, 43.06), (0, 43.06, 43.3), (1, 43.3, 43.39), (0, 43.39, 43.48),
                (1, 43.48, 43.52), (0, 43.52, 43.63), (1, 43.63, 43.72), (0, 43.72, 43.83),
                (1, 43.83, 43.84), (0, 43.84, 43.96), (1, 43.96, 44.01), (0, 44.01, 44.11),
                (1, 44.11, 44.2), (0, 44.2, 48.9)]
        lv = _Exact(runs, [(43.2, self.BAGS)], 39.1, 49.1, -18.0, -12.9, -42.4,
                    loud=[(42.0, 43.06, -5.0)])
        words = _said(("The", 42.0, 42.3), ("pocketbooks,", 43.36, 43.76), ("or", 43.98, 44.04),
                      ("bags.", 44.04, 44.36))
        _, e, rep = self._place(lv, words, 42.0, 43.98)
        self.assertTrue(e <= 43.96 or any("clip ends" in x for x in rep["warnings"]))

    # H1, seg2 (FULL, touching cues): "find it." runs straight into "Like,"
    # with no dip; the pause comes after "Like,". With no dip to rise from,
    # "Like," read as a decay and the clip ended "...and find it like", PASS.
    LIKE = [-17, -15, -14, -15, -15, -15, -15, -16, -16, -17, -17, -18, -19, -22, -25, -30, -26, -26, -32,
            -33, -46, -49, -53, -59, -61, -63, -61, -61, -62, -63, -21, -21, -14, -19, -17, -19, -15, -14,
            -12, -12, -14, -13, -13, -14, -14, -15, -16, -17, -17, -17, -16, -17, -16, -16, -12, -11, -11,
            -10, -10, -11, -12, -11, -11, -12, -12, -12, -13, -16, -16, -18, -21, -21, -19, -17, -15, -13,
            -12, -12, -13, -14, -15, -16, -17, -19, -15, -18, -19, -18, -23, -28, -35, -38, -50, -52, -44,
            -51, -60, -64, -63, -70, -64, -67, -67, -67, -64, -64]

    def test_an_end_keeps_no_word_that_runs_on_at_full_level_unwarned(self):
        runs = [(0, 144.0, 144.5), (1, 144.5, 145.14), (0, 145.14, 145.25), (1, 145.25, 145.86),
                (0, 145.86, 146.69), (1, 146.69, 147.5)]
        lv = _Exact(runs, [(144.94, self.LIKE)], 142.0, 150.0, -70.0, -45.7, -45.7,
                    loud=[(144.5, 144.94, -14.0), (146.69, 147.5, -12.0)])
        words = _said(("now", 144.5, 145.04), ("and", 145.04, 145.18), ("find", 145.18, 145.4),
                      ("it", 145.4, 145.62), ("like", 145.62, 145.88), ("it's", 145.88, 146.9),
                      ("still", 146.9, 147.08))
        _, e, rep = self._place(lv, words, 144.5, 145.62)
        if e > 145.7:
            self.assertTrue(any(x.startswith('the clip ends at the pause after "like"')
                                for x in rep["warnings"]))
            self.assertEqual(rep["clip_word_span"][1][0], "like")

    # H2, seg3: the word-gap rule cut in the 30 ms dip at 131.83 inside
    # "realistically," (clocked to 131.78): its "-ly", 0.26 s at -15 dBFS no
    # clock covers, was dropped with a NOTE ("...10 or 11, realistic.").
    SEG3 = [-13, -13, -12, -12, -11, -9, -10, -10, -10, -11, -11, -12, -14, -21, -23, -24, -23, -28, -30,
            -34, -42, -36, -43, -33, -16, -12, -12, -12, -15, -27, -29, -34, -45, -51, -48, -33, -37, -33,
            -22, -16, -16, -17, -17, -15, -15, -15, -16, -17, -17, -17, -18, -18, -18, -18, -19, -19, -19,
            -20, -21, -20, -21, -21, -18, -20, -18, -28, -39, -37, -21, -15, -13, -11, -10, -9, -9, -10,
            -10, -12, -26, -31, -38, -41, -26, -30, -28, -40, -38, -11, -11, -11]

    def test_an_end_in_a_dip_before_an_uncovered_syllable_warns(self):
        runs = [(0, 129.8, 130.3), (1, 130.3, 131.83), (0, 131.83, 131.85), (1, 131.85, 132.57),
                (0, 132.57, 133.2)]
        lv = _Exact(runs, [(131.5, self.SEG3)], 127.0, 135.0, -76.0, -46.1, -46.1,
                    loud=[(130.3, 131.5, -11.0), (132.4, 132.57, -12.0)])
        words = _said(("So", 130.3, 130.32), ("realistically,", 130.32, 131.78), ("I", 132.26, 132.3),
                      ("think,", 132.3, 132.58))
        for end in (131.78, 132.26):
            _, e, rep = self._place(lv, [dict(w) for w in words], 130.3, end)
            self.assertTrue(e >= 132.15 or any(x.startswith("the clip ends in a short dip right before")
                                               for x in rep["warnings"]))

    # H2, seg5: the cut at 84.72 left out "cycle?"'s last 0.15 s
    # ("...mid training psych"), NOTE only.
    SEG5 = [-29, -32, -30, -28, -32, -17, -15, -13, -13, -12, -11, -11, -11, -11, -13, -15, -15, -15, -16,
            -17, -18, -18, -17, -18, -19, -26, -29, -25, -24, -26, -27, -34, -12, -12, -12, -11, -11, -10,
            -11, -11, -14, -14, -15, -14, -16, -26, -32, -41, -51, -59, -63, -50, -42, -17, -15, -15, -14,
            -14, -15, -16, -15, -14, -15, -16, -18, -18, -21, -23, -26, -30, -31, -32, -32, -32, -32, -32,
            -32, -33, -33, -33, -35, -34, -38, -43, -62, -57, -51, -40, -18, -13]

    def test_an_end_cut_before_a_words_last_syllable_warns(self):
        runs = [(0, 83.3, 83.76), (1, 83.76, 84.68), (0, 84.68, 84.72), (1, 84.72, 85.04),
                (0, 85.04, 85.07), (1, 85.07, 85.59), (0, 85.59, 86.2)]
        lv = _Exact(runs, [(84.2, self.SEG5)], 79.75, 89.75, -76.0, -46.0, -46.0,
                    loud=[(83.76, 84.2, -14.0), (85.1, 85.59, -13.0)])
        words = _said(("you", 83.86, 84.0), ("mid", 84.0, 84.14), ("training", 84.14, 84.38),
                      ("cycle?", 84.38, 84.7), ("You", 84.88, 84.9), ("should", 84.9, 85.0),
                      ("still", 85.0, 85.16), ("be", 85.16, 85.26), ("able", 85.26, 85.38))
        _, e, rep = self._place(lv, words, 83.86, 84.7)
        self.assertTrue(e >= 84.86 or any(x.startswith("the clip ends in a short dip right before")
                                          for x in rep["warnings"]))

    # L1: the start-side dropped-syllable warning fired on correct cuts: the
    # previous word's own last syllable ran 0.12-0.14 s past its clock
    # ("seventeen" on seg3, "still," on seg4), and Whisper heard the wanted
    # word whole from each cut.
    SEV = [-25, -26, -26, -27, -26, -27, -32, -20, -11, -11, -11, -11, -11, -13, -14, -16, -17, -18, -18,
           -17, -17, -16, -18, -25, -29, -31, -31, -29, -30, -31, -28, -17, -13, -13, -13, -16, -16, -15,
           -15, -16, -15, -15, -15, -15, -15, -15, -16, -16, -16, -17, -18, -22, -24, -24, -28, -29, -34,
           -36, -39, -45, -49, -46, -34, -22, -18, -19, -21, -26, -18, -16, -14, -14, -14, -14, -15, -18,
           -25, -27, -35, -45, -46, -37, -39, -35, -36, -39, -40, -23, -16, -16]
    STILL = [-12, -12, -10, -8, -8, -8, -10, -9, -11, -13, -17, -21, -22, -25, -25, -26, -22, -28, -26, -23,
             -24, -27, -31, -44, -53, -56, -42, -22, -13, -12, -12, -12, -11, -11, -11, -12, -11, -11, -10,
             -11, -13, -15, -15, -14, -13, -13, -13, -15, -18, -22, -22, -24, -27, -33, -28, -46, -55, -41,
             -27, -19, -17, -16, -19, -26, -39, -47, -50, -51, -56, -61, -53, -52, -30, -9, -8, -8, -10,
             -10, -10, -9]

    def test_a_previous_words_short_run_past_its_clock_is_no_dropped_syllable(self):
        lv = _Exact([(0, 56.0, 56.5), (1, 56.5, 58.1), (0, 58.1, 58.11), (1, 58.11, 58.58),
                     (0, 58.58, 58.99), (1, 58.99, 60.5), (0, 60.5, 61.0)], [(57.5, self.SEV)],
                    53.05, 63.05, -75.0, -48.0, -48.0, loud=[(56.5, 57.5, -12.0), (58.99, 60.5, -12.0)])
        words = _said(("Like", 56.5, 56.8), ("17,", 57.58, 57.92), ("18?", 58.14, 58.38),
                      ("As", 58.99, 59.2), ("long", 59.2, 59.5), ("done.", 60.0, 60.5))
        s, _, rep = self._place(lv, words, 57.92, 60.5)
        self.assertFalse(any("short dip right after" in x for x in rep["warnings"]))
        self.assertTrue(58.04 <= s <= 58.13)              # in the dip before "18?"
        lv = _Exact([(0, 146.2, 146.72), (1, 146.72, 147.54), (0, 147.54, 147.56), (1, 147.56, 147.85),
                     (0, 147.85, 147.87), (1, 147.87, 147.95), (0, 147.95, 148.02), (1, 148.02, 148.88),
                     (0, 148.88, 149.4)], [(147.3, self.STILL)], 142.75, 152.75, -75.0, -44.9, -44.9,
                    loud=[(146.72, 147.3, -10.0), (148.1, 148.88, -12.0)])
        words = _said(("I", 147.12, 147.42), ("still,", 147.42, 147.7), ("the", 147.88, 147.98),
                      ("thoughts", 147.98, 148.16), ("go", 148.16, 148.3), ("in.", 148.3, 148.85))
        s, _, rep = self._place(lv, words, 147.7, 148.85)
        self.assertFalse(any("short dip right after" in x for x in rep["warnings"]))
        self.assertTrue(147.84 <= s <= 147.88)            # in the dip before "the"

    # L3, seg4: an end asked for at "like", timed as an instant at 136.98
    # (its sound before its clock), keeps it, as snap_to_words does; the
    # captions left it out.
    DAY = [-24, -20, -22, -22, -23, -20, -19, -15, -15, -14, -13, -15, -16, -17, -16, -15, -14, -15, -15,
           -16, -16, -16, -16, -18, -18, -18, -17, -16, -14, -15, -15, -14, -14, -14, -15, -16, -17, -22,
           -25, -25, -27, -24, -28, -26, -27, -29, -37, -46, -48, -60, -67, -66, -68, -65, -71, -69, -72,
           -72, -74, -74]

    def test_an_instant_kept_on_the_end_edge_is_in_the_captions(self):
        lv = _Exact([(0, 135.6, 136.11), (1, 136.11, 136.97), (0, 136.97, 137.72), (1, 137.72, 138.5),
                     (0, 138.5, 139.0)], [(136.5, self.DAY)], 131.95, 141.95, -74.0, -46.4, -46.4,
                    loud=[(136.11, 136.5, -15.0), (137.72, 138.5, -12.0)])
        words = _said(("this", 136.11, 136.38), ("day,", 136.38, 136.68), ("like", 136.98, 136.98),
                      ("I", 136.98, 137.8), ("did.", 137.8, 138.4))
        _, e, rep = self._place(lv, words, 136.11, 136.98)
        self.assertGreater(e, 136.97)                      # "like" kept, by design
        self.assertEqual(rep["clip_word_span"][1][0], "like")

    # The real rev7 decay the round-15 fix was built on, on its own peaks:
    # "Just" clocked into the reverb tail of "things." 9.3 dB under it, said
    # after the pause. The end stays in the editor's pause, unwarned.
    REV7 = [-21, -21, -20, -25, -26, -24, -25, -31, -29, -27, -28, -29, -31, -25, -22, -23, -23, -28, -30,
            -30, -27, -29, -30, -29, -28, -32, -30, -25, -25, -21, -24, -22, -26, -29, -26, -24, -27, -31,
            -28, -29, -30, -32, -34, -31, -35, -34, -34, -32, -32, -29, -30, -31, -30, -29, -31, -31, -33,
            -33, -31, -32, -33, -35, -35, -34, -38, -39, -40, -38, -38, -41, -41, -42, -42, -43, -44, -42,
            -44, -44, -45, -47, -48, -45, -46, -48, -46, -46, -42, -48, -48, -46, -44, -48, -48, -49, -45,
            -44, -43, -39, -41, -42, -34, -31, -28, -24, -20, -21, -15, -14, -16, -20]

    def test_the_real_reverb_decay_keeps_the_editors_pause(self):
        lv = _Exact([(0, 268.85, 269.38), (1, 269.38, 274.02), (0, 274.02, 274.27), (1, 274.27, 275.09)],
                    [(273.3, self.REV7)], 268.85, 278.85, -46.0, -42.2, -46.4,
                    loud=[(269.38, 273.3, -20.0), (274.4, 275.09, -18.0)])
        words = _said(("So", 269.4, 269.6), ("people", 273.04, 273.4), ("things.", 273.4, 273.78),
                      ("Just", 273.78, 273.9), ("fly", 273.9, 274.46), ("around,", 274.46, 274.84))
        _, e, rep = self._place(lv, words, 269.4, 273.78)
        self.assertGreater(e, 274.02)                      # in the pause, the tail kept
        self.assertLess(e, 274.27)
        self.assertEqual(rep["clip_word_span"][1][0], "things.")
        # The receipt says "Just" may be said in that tail (it is not, here).
        self.assertEqual([x for x in rep["warnings"] if "ends" in x and '"Just"' not in x], [])
        self.assertTrue(any(x.startswith('the clip ends in a pause after "Just", clocked inside')
                            for x in rep["warnings"]))

    # seg4 at 221.02: "little," then "I would" said softly with no dip
    # (-22 to -28 dBFS, 12 dB under it), "I" an instant at 221.02 and "would"
    # clocked 221.02-221.16, then the pause. The level reads the soft words as
    # "little,"'s tail, as it read rev7's reverb: the clip kept "I would" in
    # the sound and "would" out of the captions, PASS.
    SOFT = [-27, -26, -24, -20, -17, -15, -14, -13, -13, -15, -15, -15, -15, -15, -15, -17, -22, -16, -14,
            -14, -14, -14, -14, -14, -14, -13, -14, -14, -14, -14, -14, -14, -15, -16, -14, -14, -15, -16,
            -16, -16, -17, -20, -21, -22, -27, -27, -27, -28, -28, -24, -22, -26, -25, -27, -26, -25, -26,
            -26, -25, -34, -34, -35, -36, -39, -38, -43, -46, -46, -47, -40, -54, -60, -66, -68, -71, -67,
            -72, -69, -72, -70, -71, -76, -70, -75, -71, -70, -72, -73, -74, -71, -74, -72, -49, -38, -29,
            -30, -30, -14, -10, -10]

    def test_a_soft_word_read_as_a_tail_is_flagged_when_left_out_of_the_captions(self):
        lv = _Exact([(0, 218.6, 219.06), (1, 219.06, 220.16), (0, 220.16, 220.18), (1, 220.18, 221.2),
                     (0, 221.2, 221.43), (1, 221.43, 222.69)], [(220.5, self.SOFT)],
                    216.0, 225.0, -73.0, -48.1, -48.1, loud=[(219.06, 220.5, -14.0), (221.5, 222.69, -12.0)])
        words = _said(("like", 219.48, 219.6), ("VHS", 219.6, 220.04), ("when", 220.04, 220.24),
                      ("I", 220.24, 220.38), ("was", 220.38, 220.48), ("little,", 220.48, 220.78),
                      ("I", 221.02, 221.02), ("would", 221.02, 221.16), ("copy", 221.16, 221.62),
                      ("the", 221.62, 221.74))
        _, e, rep = self._place(lv, words, 219.06, 221.02)
        if e > 221.1 and rep["clip_word_span"][1][0] != "would":
            self.assertTrue(any(x.startswith('the clip ends in a pause after "would", clocked inside')
                                for x in rep["warnings"]))


    # The fix's own sweep, fan47 at 286.70: "right?" clocked 286.68-286.70 and
    # the END asked for at its clock end. Its 20 ms clock made it a word
    # between, and the clip ended inside its decay with a WARN; and since
    # round 12 the captions had left it out, the clip ending in the pause
    # after it ("...a game, right?").
    RIGHT = [-22, -21, -21, -23, -25, -26, -30, -28, -27, -27, -27, -26, -26, -27, -27, -28, -28, -28, -31,
             -31, -33, -36, -38, -39, -39, -42, -41, -41, -40, -40, -42, -41, -39, -44, -43, -41, -41, -40,
             -43, -40, -41, -41, -43, -41, -42, -41, -42, -40, -42, -43, -39, -43, -43, -42, -40, -40, -41,
             -39, -41, -41, -40, -42, -41, -40, -42, -41, -35, -35, -28, -24, -25, -25, -28, -26, -27, -26,
             -28, -30, -31, -32, -32, -36, -36, -37, -39, -43, -41, -42, -41, -43, -42, -40, -41, -40, -41,
             -42, -41, -40, -39, -40, -39, -42, -41, -40, -42, -40, -41, -40, -43, -43, -41, -43, -41, -41,
             -42, -44, -42, -41, -42, -44, -41, -38, -40, -41, -42, -42, -39, -39, -46, -44, -41, -44, -41,
             -43, -42, -41, -41, -41, -40, -42, -42, -40, -44, -42, -43, -44, -42, -41, -41, -43, -42, -40,
             -40, -41, -41, -42, -42, -33, -28, -24]

    def test_an_end_at_a_short_last_words_clock_end_keeps_it_in_sound_and_captions(self):
        lv = _Exact([(0, 284.0, 284.6), (1, 284.6, 285.5), (0, 285.5, 285.69), (1, 285.69, 286.1),
                     (0, 286.1, 286.58), (1, 286.58, 286.71), (0, 286.71, 287.48), (1, 287.48, 288.2)],
                    [(285.9, self.RIGHT)], 282.0, 291.0, -42.0, -33.1, -52.6,
                    loud=[(284.6, 285.9, -20.0)])
        words = _said(("side", 284.7, 285.08), ("at", 285.08, 285.28), ("a", 285.28, 285.48),
                      ("game,", 285.48, 285.96), ("right?", 286.68, 286.7), ("All", 287.38, 287.6),
                      ("this", 287.6, 287.74))
        _, e, rep = self._place(lv, words, 284.7, 286.7)
        self.assertGreater(e, 286.71)                      # in the pause after "right?"
        self.assertLess(e, 287.38)
        self.assertEqual([x for x in rep["warnings"] if "ends" in x], [])
        self.assertEqual(rep["clip_word_span"][1][0], "right?")

    def test_a_start_at_a_short_previous_words_clock_end_does_not_open_on_it(self):
        # The mirror at a start: a word between the reach pause and the
        # request, clocked 20 ms (said 1.80-1.98, clocked 1.98-2.00), with the
        # START asked for at its clock end. "start < request - 0.02" let it
        # out of the words between, and the clip opened on it unwarned.
        runs = [(0, 0.5, 1.0), (1, 1.0, 1.55), (0, 1.55, 1.8), (1, 1.8, 3.0), (0, 3.0, 3.6)]
        loud = [(1.0, 1.55, -15.0), (1.8, 1.98, -16.0), (1.98, 2.06, -45.0), (2.06, 3.0, -14.0)]
        lv = _QuietRoom(runs, loud, 0.0, 5.0, -76.0, -46.0)
        words = _said(("so", 1.0, 1.5), ("yeah.", 1.98, 2.0), ("Next", 2.06, 2.4), ("one.", 2.4, 3.0))
        s, _, rep = self._place(lv, words, 2.0, 3.0)
        self.assertTrue(s >= 1.95 or any(x.startswith('the clip starts at the pause before "yeah."')
                                         for x in rep["warnings"]))

    def test_a_kept_whole_start_opens_the_captions_with_an_srt_too(self):
        # The caption scan of this round's sweeps: with Descript's cues, the
        # captions opened on the requested cue's first word, so a word kept
        # whole before it (seg1's "put", "or", "rim" on the every-cue FULL
        # clips) was in the sound and out of the captions.
        runs = [(0, 0.16, 1.29), (1, 1.29, 5.33), (0, 5.33, 5.8), (1, 5.8, 7.0)]
        loud = [(1.29, 5.33, -15.0), (5.8, 7.0, -15.0)]
        words = _said(("And", 1.0, 1.36), ("then,", 1.36, 1.6), ("once", 1.88, 1.94),
                      ("that", 1.94, 2.84), ("done.", 4.9, 5.3), ("Next", 5.8, 6.0))
        for x, (cs, ce) in zip(words, [(0.1, 1.36)] + [(1.36, 5.3)] * 4 + [(5.8, 7.0)]):
            x["cue_start"], x["cue_end"] = cs, ce
        s, _, rep = self._place(_QuietRoom(runs, loud, 0.0, 8.0, -80.0, -53.4), words, 1.36, 5.3)
        self.assertLess(s, 1.29)                           # "And" whole
        self.assertEqual(rep["clip_word_span"][0][0], "And")

    # The fix above, in its own sweep: How_to at 67.51 under room noise, "you"
    # clocked inside the pause before "know," (so not among the words between)
    # and said into it; the captions, which had opened on "you", opened on
    # "know,". The earlier of the two opens them.
    YOU = [-38, -32, -33, -32, -32, -31, -31, -29, -30, -30, -29, -27, -28, -29, -30, -35, -34, -34, -33,
           -35, -37, -39, -37, -36, -34, -33, -33, -31, -29, -32, -30, -30, -31, -30, -30, -30, -31, -34,
           -36, -40, -39, -38, -39, -41, -43, -44, -46, -44, -45, -48, -48, -48, -48, -49, -46, -49, -47,
           -49, -49, -48, -51, -53, -38, -33, -31, -27, -31, -28, -26, -24, -24, -26, -24, -24, -28, -30,
           -31, -34, -37, -38, -36, -38, -40, -39, -43, -44, -42, -35, -33, -32, -33, -31, -31, -33, -32,
           -32, -32, -35, -31, -33, -38, -39, -40, -43, -38, -36, -34, -33, -28, -30]

    def test_a_kept_whole_start_keeps_an_earlier_caption_word(self):
        runs = [(0, 65.0, 65.5), (1, 65.5, 67.15), (0, 67.15, 67.32), (1, 67.32, 67.54), (0, 67.54, 67.56),
                (1, 67.56, 67.73), (0, 67.73, 67.74), (1, 67.74, 69.0), (0, 69.0, 69.6)]
        lv = _Exact(runs, [(66.7, self.YOU)], 62.5, 72.5, -48.0, -43.3, -60.0,
                    loud=[(65.5, 66.7, -30.0), (67.8, 69.0, -30.0)])
        words = _said(("so", 65.54, 65.84), ("information", 66.48, 66.86), ("made,", 66.86, 67.12),
                      ("you", 67.24, 67.32), ("know,", 67.32, 67.46), ("in", 67.56, 67.84),
                      ("case", 67.84, 68.0), ("no", 68.0, 68.48), ("one.", 68.48, 68.8))
        s, _, rep = self._place(lv, words, 67.51, 68.8)
        if s < 67.32:
            self.assertEqual(rep["clip_word_span"][0][0], "you")

HAVE_FFMPEG =bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))
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
        # Syllable-like bursts: a steady tone is indistinguishable from a hum, and
        # the checker rightly calls a hum unmeasurable.
        tone = ("0.04*sin(2*PI*440*t)*gt(sin(2*PI*4*t),0)*"
                "(between(t,2.6,9)+between(t,11.6,16))")
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

    def _make(self, name, vf=None, tone=None, d=8, audio=True, video=True, r=25):
        out = self.tmp / name
        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
        if video:
            cmd += ["-f", "lavfi", "-i", f"testsrc2=s=320x240:r={r}:d={d}"]
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
                                           "+0.2*sin(2*PI*440*t)*gt(sin(2*PI*4*t),0)*gte(t,3)")
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
        # The 3-frame full-black flash is a FAIL; the 95%-black screen is near-black,
        # which could be a dark slide, so it is a WARN with a saved frame.
        self.assertEqual(c["black_frames"]["status"], "FAIL")
        self.assertEqual(c["black_frames"]["measured"], 1)
        self.assertEqual(c["near_black"]["status"], "WARN")
        self.assertEqual(c["near_black"]["measured"], 1)

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

    # ---- audit round 2 (23 Oct 2026) ----

    def test_two_frame_flashes_are_caught_at_30_and_60_fps(self):
        for r, frames, caught in ((30, "between(n,90,91)", True),
                                  (60, "between(n,180,181)", True),
                                  (30, "eq(n,90)", False)):   # one frame = a cut, allowed
            src = self._make(f"flash{r}-{caught}.mp4", r=r, d=6,
                             vf=f"drawbox=c=black:t=fill:enable='{frames}'")
            rec = video_qa.qa(str(src), video_qa.load_profile(None),
                              self.tmp / f"flash{r}-{caught}.qa", frames=False)
            c = {x["check"]: x for x in rec["checks"]}
            self.assertEqual(c["black_frames"]["status"], "FAIL" if caught else "PASS",
                             (r, frames))

    def _speech(self, name, noise_amp=0.0, gain_db=0.0):
        """Syllable-like bursts with a 2.6 s dead gap, optional white noise."""
        out = self.tmp / name
        sp = ("0.5*sin(2*PI*220*t)*gt(sin(2*PI*4*t),0)*(between(t,0.3,3.0)+"
              "between(t,3.8,6.5)+between(t,9.0,12.0)+between(t,12.7,15.5))")
        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
               "-i", f"aevalsrc='{sp}':s=48000:d=16"]
        if noise_amp:
            cmd += ["-f", "lavfi", "-i", f"anoisesrc=a={noise_amp}:c=white:d=16:r=48000",
                    "-filter_complex",
                    f"[0][1]amix=inputs=2:normalize=0,volume={gain_db}dB"]
        cmd += ["-c:a", "pcm_s16le", str(out)]
        subprocess.run(cmd, check=True)
        return out

    def test_room_noise_cannot_hide_dead_air(self):
        results = []
        for name, amp, gain in (("clean.wav", 0.0, 0.0), ("noisy.wav", 0.0308, 0.0),
                                ("noisy-quiet.wav", 0.0308, -30.0),
                                ("noisy-loud.wav", 0.0308, 6.0)):
            rec = video_qa.qa(str(self._speech(name, amp, gain)),
                              video_qa.load_profile(None), self.tmp / (name + ".qa"))
            c = {x["check"]: x for x in rec["checks"]}
            results.append((c["pauses_over_fail"]["status"], c["pauses_over_fail"]["measured"],
                            c["pauses_over_warn_rate"]["measured"]))
        self.assertEqual(results[0][:2], ("FAIL", 1))
        self.assertEqual(len(set(results)), 1, results)   # same verdict at every level
        rec = video_qa.qa(str(self._speech("drowned.wav", 0.2)), video_qa.load_profile(None),
                          self.tmp / "drowned.qa")
        c = {x["check"]: x["status"] for x in rec["checks"]}
        # Never PASS: unmeasurable (WARN), or, since a steady hiss holds no talk
        # however loud (audit round 7), the gap itself (FAIL).
        self.assertIn(c["pauses_over_fail"], ("WARN", "FAIL"))

    def test_trim_head_cuts_to_the_first_word_not_the_intro(self):
        src = self._make("intro.mp4", d=9, tone=(
            "0.1*(sin(2*PI*261*t)+sin(2*PI*392*t))*lt(t,4)+"
            "0.5*sin(2*PI*220*t)*gt(sin(2*PI*4*(t-4.1)),0)*between(t,4.1,9)"))
        words = [w(f"w{i}", 4.1 + i * 0.25, 4.1 + i * 0.25 + 0.125) for i in range(18)]
        out = self.tmp / "intro-out.mp4"
        style = finish.load_style(None)
        rep = finish.finish(str(src), str(out), style, trim_head=True, loudness=False,
                            words=words, burn=False, keywords=[])
        self.assertEqual(rep["trim_head_to"], "first word")
        # The steady chord raises the silence threshold like room noise, so the
        # cut keeps the start's noise slack (at most 0.15 s; audit round 11)
        # before the first word: still nowhere near the intro's start.
        self.assertTrue(3.85 <= rep["start_s"] <= 4.03, rep["start_s"])
        rec = video_qa.qa(str(out), style["qa"], self.tmp / "intro-out.qa", frames=False,
                          words=rep["_out_words"])
        c = {x["check"]: x["status"] for x in rec["checks"]}
        self.assertEqual(c["hook_first_speech"], "PASS")

    def test_trim_head_skips_a_record_button_click(self):
        src = self._make("click2.mp4", d=9, tone=(
            "0.6*sin(2*PI*1000*t)*between(t,0.3,0.305)+"
            "0.5*sin(2*PI*220*t)*gt(sin(2*PI*4*(t-4.0)),0)*between(t,4.0,9)"))
        out = self.tmp / "click2-out.mp4"
        style = finish.load_style(None)
        rep = finish.finish(str(src), str(out), style, trim_head=True, loudness=False,
                            words=None, burn=False, keywords=[])
        self.assertEqual(rep["trim_head_to"], "first sustained sound")
        self.assertAlmostEqual(rep["start_s"], 3.92, delta=0.06)
        rec = video_qa.qa(str(out), style["qa"], self.tmp / "click2-out.qa", frames=False)
        c = {x["check"]: x["status"] for x in rec["checks"]}
        self.assertEqual(c["pauses_over_fail"], "PASS")

    def test_cover_art_in_an_mp3_is_not_video(self):
        out = self.tmp / "cover.mp3"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                        "-f", "lavfi", "-i", "sine=f=440:d=3", "-f", "lavfi", "-i",
                        "color=c=black:s=300x300:d=1", "-map", "0:a", "-map", "1:v",
                        "-c:a", "libmp3lame", "-c:v", "mjpeg", "-frames:v", "1",
                        "-disposition:v", "attached_pic", str(out)], check=True)
        self.assertIsNone(video_qa.probe(str(out))["video"])
        rec = video_qa.qa(str(out), video_qa.load_profile(None), self.tmp / "cover.qa")
        c = {x["check"]: x["status"] for x in rec["checks"]}
        self.assertEqual(c["black_frames"], "N/A")
        self.assertNotIn("frames", rec)

    def test_wav_output_stays_decodable(self):
        src = self._make("speech.m4a", video=False, d=4,
                         tone="0.3*sin(2*PI*220*t)*gte(t,1)")
        out = self.tmp / "speech-out.wav"
        style = finish.load_style(None)
        finish.finish(str(src), str(out), style, trim_head=True, loudness=True,
                      words=None, burn=False, keywords=[])
        rec = video_qa.qa(str(out), style["qa"], self.tmp / "speech-out.qa")
        self.assertEqual(rec["probe"]["audio"]["codec"], "pcm_s16le")
        c = {x["check"]: x["status"] for x in rec["checks"]}
        self.assertEqual(c["integrated_loudness"], "PASS")

    # ---- audit round 3 (23 Oct 2026) ----

    SYL = "0.3*sin(2*PI*220*t)*gt(sin(2*PI*4*t),0)"

    def _qa(self, src, words=None):
        rec = video_qa.qa(str(src), video_qa.load_profile(None),
                          Path(str(src) + ".qa"), frames=False, words=words)
        return rec, {x["check"]: x for x in rec["checks"]}

    def test_noise_in_part_of_the_file_cannot_hide_a_dead_gap(self):
        out = self.tmp / "partnoise.wav"
        sp = ("0.25*sin(2*PI*220*t)*gt(sin(2*PI*4*t),0)*lt(mod(t,6),5.2)*"
              "(lt(t,40)+gte(t,42.5))")
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
                        "-i", f"aevalsrc='{sp}':s=48000:d=60", "-f", "lavfi", "-i",
                        "anoisesrc=a=0.0308:c=white:r=48000:d=60", "-filter_complex",
                        "[1]volume='gte(t,30)':eval=frame[n];[0][n]amix=inputs=2:normalize=0",
                        "-c:a", "pcm_s16le", str(out)], check=True)
        rec, c = self._qa(out)
        self.assertEqual(c["pauses_over_fail"]["status"], "FAIL")
        self.assertIn("39.9s", c["pauses_over_fail"]["note"])

    def test_a_half_downloaded_file_fails(self):
        full = self.tmp / "full.mp4"   # index first, like a web download
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
                        "-i", "testsrc2=s=320x240:r=25:d=12", "-f", "lavfi", "-i",
                        f"aevalsrc='{self.SYL}':s=48000:d=12", "-c:v", "libx264", "-preset",
                        "ultrafast", "-c:a", "aac", "-movflags", "+faststart", "-shortest",
                        str(full)], check=True)
        half = self.tmp / "half.mp4"
        data = full.read_bytes()
        half.write_bytes(data[: len(data) // 2])
        rec, c = self._qa(half)
        self.assertEqual(c["decodes_cleanly"]["status"], "FAIL")
        self.assertEqual(rec["verdict"], "FAIL")
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(video_qa.main([str(half), "--no-frames", "--out",
                                            str(self.tmp / "half.cli")]), 1)
        # Index at the end and cut off: nothing can be measured, exit 2, never 0.
        tail_index = self._make("tailindex.mp4", d=6, tone=self.SYL)
        cut = self.tmp / "cut.mp4"
        cut.write_bytes(tail_index.read_bytes()[:-2000])
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(video_qa.main([str(cut), "--no-frames", "--out",
                                            str(self.tmp / "cut.cli")]), 2)

    def test_aac_inside_a_wav_fails_instead_of_measuring_wrong(self):
        bad = self.tmp / "aac.wav"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
                        "-i", f"aevalsrc='{self.SYL}':s=48000:d=6", "-c:a", "aac", str(bad)],
                       check=True)
        rec, c = self._qa(bad)
        self.assertEqual(c["decodes_cleanly"]["status"], "FAIL")

    def test_audio_that_starts_late_or_stops_early_is_dead_air(self):
        late = self.tmp / "late.mp4"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
                        "-i", "testsrc2=s=320x240:r=25:d=10", "-itsoffset", "3", "-f", "lavfi",
                        "-i", f"aevalsrc='{self.SYL}':s=48000:d=7", "-map", "0:v", "-map",
                        "1:a", "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac",
                        str(late)], check=True)
        rec, c = self._qa(late)
        self.assertEqual(c["hook_first_audio"]["status"], "FAIL")
        early = self.tmp / "early.mp4"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
                        "-i", "testsrc2=s=320x240:r=25:d=20", "-f", "lavfi", "-i",
                        f"aevalsrc='{self.SYL}':s=48000:d=8", "-c:v", "libx264", "-preset",
                        "ultrafast", "-c:a", "aac", str(early)], check=True)
        rec, c = self._qa(early)
        self.assertEqual(c["trailing_silence"]["status"], "FAIL")

    def test_speech_after_room_tone_fails_the_hook(self):
        out = self.tmp / "roomtone.wav"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
                        "-i", f"aevalsrc='{self.SYL}*gte(t,8)':s=48000:d=16", "-f", "lavfi",
                        "-i", "anoisesrc=a=0.0055:c=pink:r=48000:d=16", "-filter_complex",
                        "[0][1]amix=inputs=2:normalize=0", "-c:a", "pcm_s16le", str(out)],
                       check=True)
        rec, c = self._qa(out)
        self.assertEqual(c["hook_first_audio"]["status"], "FAIL")
        self.assertAlmostEqual(rec["first_audio_s"], 8.0, delta=0.1)

    def test_variable_frame_rate_flash_is_caught(self):
        out = self.tmp / "vfr.mp4"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
                        "-i", "testsrc2=s=320x240:r=30:d=10", "-f", "lavfi", "-i",
                        f"aevalsrc='{self.SYL}':s=48000:d=10", "-vf",
                        "drawbox=c=black:t=fill:enable='between(n,120,121)',"
                        "select='between(t,3,6)+not(mod(n,15))'", "-fps_mode", "vfr",
                        "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac",
                        "-shortest", str(out)], check=True)
        rec, c = self._qa(out)
        self.assertEqual(c["black_frames"]["status"], "FAIL")

    def test_dark_theme_slide_is_a_look_not_a_fail(self):
        slide = self.tmp / "slide.mp4"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
                        "-i", "testsrc2=s=320x240:r=25:d=2", "-f", "lavfi", "-i",
                        "color=c=0x0d1117:s=320x240:r=25:d=3", "-f", "lavfi", "-i",
                        "testsrc2=s=320x240:r=25:d=2", "-f", "lavfi", "-i",
                        f"aevalsrc='{self.SYL}':s=48000:d=7", "-filter_complex",
                        "[1:v]drawbox=x=100:y=110:w=120:h=4:c=white:t=fill[s];"
                        "[0:v][s][2:v]concat=n=3:v=1:a=0[v]", "-map", "[v]", "-map", "3:a",
                        "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac",
                        "-shortest", str(slide)], check=True)
        rec = video_qa.qa(str(slide), video_qa.load_profile(None), self.tmp / "slide.qa")
        c = {x["check"]: x["status"] for x in rec["checks"]}
        self.assertEqual(c["black_frames"], "PASS")
        self.assertEqual(c["near_black"], "WARN")
        self.assertTrue(rec["frames"]["near_black_frames"])   # a frame to look at

    def test_video_to_audio_only_output_and_no_stub_on_failure(self):
        src = self._make("vid.mp4", d=4, tone=self.SYL)
        style = finish.load_style(None)
        for ext in (".wav", ".mp3", ".m4a"):
            out = self.tmp / f"pod{ext}"
            finish.finish(str(src), str(out), style, trim_head=False, loudness=True,
                          words=None, burn=False, keywords=[])
            info = video_qa.probe(str(out))
            self.assertIsNone(info["video"], ext)
            self.assertIsNotNone(info["audio"], ext)
        with self.assertRaises(ValueError):
            finish.finish(str(src), str(self.tmp / "v.webm"), style, trim_head=False,
                          loudness=False, words=None, burn=False, keywords=[])
        with self.assertRaises(RuntimeError):
            finish.finish(str(src), str(self.tmp / "v.xyz"), style, trim_head=False,
                          loudness=False, words=None, burn=False, keywords=[])
        leftovers = [p.name for p in self.tmp.iterdir()
                     if p.name.startswith((".v.", "v.")) and p.suffix in (".webm", ".xyz")]
        self.assertEqual(leftovers, [])

    # ---- audit round 4 (23 Oct 2026) ----

    def _quiet_qa(self, src, words=None):
        return video_qa.qa(str(src), video_qa.load_profile(None),
                           Path(str(src) + ".qa"), frames=False, words=words)

    def test_brown_noise_cannot_hide_a_dead_gap(self):
        out = self.tmp / "brown.wav"
        sp = ("0.25*sin(2*PI*220*t)*gt(sin(2*PI*4*t),0)*lt(mod(t,6),5.2)*"
              "(lt(t,40)+gte(t,42.5))")
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
                        "-i", f"aevalsrc='{sp}':s=48000:d=60", "-f", "lavfi", "-i",
                        "anoisesrc=a=0.0308:c=brown:r=48000:d=60", "-filter_complex",
                        "[0][1]amix=inputs=2:normalize=0", "-c:a", "pcm_s16le", str(out)],
                       check=True)
        c = {x["check"]: x["status"] for x in self._quiet_qa(out)["checks"]}
        self.assertEqual(c["pauses_over_fail"], "FAIL")

    def _held(self, name, items):
        slide, black = self.tmp / "slide.png", self.tmp / "black.png"
        for f, src in ((slide, "testsrc2=s=320x240:d=1"), (black, "color=c=black:s=320x240:d=1")):
            if not f.exists():
                subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f",
                                "lavfi", "-i", src, "-frames:v", "1", str(f)], check=True)
        lst = self.tmp / f"{name}.txt"
        body = "ffconcat version 1.0\n" + "".join(
            f"file {'black.png' if b else 'slide.png'}\nduration {d}\n" for b, d in items)
        lst.write_text(body + "file slide.png\n")
        out = self.tmp / f"{name}.mp4"
        total = sum(d for _, d in items)
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat",
                        "-safe", "0", "-i", str(lst), "-f", "lavfi", "-i",
                        f"aevalsrc='{self.SYL}':s=48000:d={total}", "-fps_mode", "passthrough",
                        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-shortest", str(out)], check=True)
        return out

    def test_one_black_frame_held_for_a_second_fails(self):
        c = {x["check"]: x["status"]
             for x in self._quiet_qa(self._held("held", [(0, 3), (1, 1), (0, 3)]))["checks"]}
        self.assertEqual(c["black_frames"], "FAIL")
        c = {x["check"]: x["status"]
             for x in self._quiet_qa(self._held("heldopen", [(1, 1.5), (0, 3)]))["checks"]}
        self.assertEqual(c["black_open"], "FAIL")

    def test_a_fade_through_black_and_a_title_card_on_black(self):
        dip = self.tmp / "dip.mp4"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                        "-f", "lavfi", "-i", "testsrc2=s=320x240:r=30:d=3",
                        "-f", "lavfi", "-i", "color=c=black:s=320x240:r=30:d=1",
                        "-f", "lavfi", "-i", "testsrc2=s=320x240:r=30:d=3",
                        "-f", "lavfi", "-i", f"aevalsrc='{self.SYL}':s=48000:d=7",
                        "-filter_complex", "[0:v]fade=t=out:st=2.5:d=0.5[a];"
                        "[2:v]fade=t=in:st=0:d=0.5[b];[a][1:v][b]concat=n=3:v=1:a=0,"
                        "format=yuv420p[v]", "-map", "[v]", "-map", "3:a", "-c:v", "libx264",
                        "-preset", "ultrafast", "-c:a", "aac", "-shortest", str(dip)], check=True)
        c = {x["check"]: x["status"] for x in self._quiet_qa(dip)["checks"]}
        self.assertEqual(c["black_frames"], "FAIL")       # the held black inside the fade
        card = self.tmp / "card.mp4"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                        "-f", "lavfi", "-i", "testsrc2=s=320x240:r=25:d=2",
                        "-f", "lavfi", "-i", "color=c=black:s=320x240:r=25:d=2",
                        "-f", "lavfi", "-i", "testsrc2=s=320x240:r=25:d=2",
                        "-f", "lavfi", "-i", f"aevalsrc='{self.SYL}':s=48000:d=6",
                        "-filter_complex", "[1:v]drawbox=x=110:y=112:w=100:h=16:c=white:"
                        "t=fill[c];[0:v][c][2:v]concat=n=3:v=1:a=0[v]", "-map", "[v]",
                        "-map", "3:a", "-c:v", "libx264", "-preset", "ultrafast", "-c:a",
                        "aac", "-shortest", str(card)], check=True)
        c = {x["check"]: x["status"] for x in self._quiet_qa(card)["checks"]}
        self.assertEqual(c["black_frames"], "PASS")       # something is on screen
        self.assertEqual(c["near_black"], "WARN")

    def test_cut_off_wav_and_ogg_fail_to_decode_cleanly(self):
        wav = self.tmp / "long.wav"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
                        "-i", f"aevalsrc='{self.SYL}':s=48000:d=10", "-c:a", "pcm_s16le",
                        str(wav)], check=True)
        ogg = self.tmp / "long.ogg"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(wav),
                        "-c:a", "libvorbis", str(ogg)], check=True)
        for full in (wav, ogg):
            data = full.read_bytes()
            cut = self.tmp / f"cut{full.suffix}"
            cut.write_bytes(data[: len(data) * 6 // 10])
            self.assertIsNotNone(video_qa.container_truncation(str(cut)), full.suffix)
            self.assertIsNone(video_qa.container_truncation(str(full)), full.suffix)
            c = {x["check"]: x["status"] for x in self._quiet_qa(cut)["checks"]}
            self.assertEqual(c["decodes_cleanly"], "FAIL", full.suffix)

    def test_late_audio_in_matroska_is_not_truncation(self):
        mkv = self.tmp / "late.mkv"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
                        "-i", "testsrc2=s=320x240:r=25:d=10", "-itsoffset", "0.8", "-f",
                        "lavfi", "-i", f"aevalsrc='{self.SYL}':s=48000:d=9.2", "-map", "0:v",
                        "-map", "1:a", "-c:v", "libx264", "-preset", "ultrafast", "-c:a",
                        "aac", str(mkv)], check=True)
        c = {x["check"]: x["status"] for x in self._quiet_qa(mkv)["checks"]}
        self.assertEqual(c["decodes_cleanly"], "PASS")

    def test_video_without_audio_still_gets_the_picture_checked(self):
        mute = self.tmp / "mute.mp4"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
                        "-i", "testsrc2=s=320x240:r=25:d=3", "-vf",
                        "drawbox=c=black:t=fill:enable='between(t,1,1.2)'", "-c:v", "libx264",
                        "-preset", "ultrafast", str(mute)], check=True)
        c = {x["check"]: x["status"] for x in self._quiet_qa(mute)["checks"]}
        self.assertEqual(c["audio"], "WARN")
        self.assertEqual(c["black_frames"], "FAIL")

    # ---- fifth audit (24 Oct 2026) ----

    def _ff(self, *args):
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args],
                       check=True)

    def _words_for(self, spans):
        """Word timing that matches the SYL syllables inside the given spans."""
        out = []
        for a, b in spans:
            t = a
            while t + 0.375 <= b:
                out.append(dict(w("la", t, t + 0.375), timing="word"))
                t += 0.5
        return out

    def test_a_breath_in_dead_air_fails_with_word_timing(self):
        out = self.tmp / "breath.wav"
        expr = (f"{self.SYL}*(lt(t,8)+gte(t,11))"
                "+0.2*(random(0)-0.5)*sin(PI*(t-9.4)/0.3)*between(t,9.4,9.7)")  # breath
        self._ff("-f", "lavfi", "-i", f"aevalsrc='{expr}':s=48000:d=20", "-c:a",
                 "pcm_s16le", str(out))
        words = self._words_for([(0.0, 8.0), (11.0, 20.0)])
        c = {x["check"]: x["status"] for x in self._quiet_qa(out, words)["checks"]}
        self.assertEqual(c["pauses_over_fail"], "FAIL")
        c = {x["check"]: x["status"] for x in self._quiet_qa(out)["checks"]}
        self.assertEqual(c["pauses_over_fail"], "PASS")              # cannot be sure...
        self.assertEqual(c["possible_pauses"], "WARN")               # ...so it is flagged

    def test_noise_like_typing_into_talk_is_not_the_start(self):
        if not video_qa.has_filter("aspectralstats"):
            self.skipTest("ffmpeg without aspectralstats")
        out = self.tmp / "typing.wav"
        expr = ("0.4*(random(0)-0.5)*exp(-30*mod(t,0.125))*lt(t,2.5)"  # 8 keys a second
                f"+{self.SYL}*gte(t,3)")
        self._ff("-f", "lavfi", "-i", f"aevalsrc='{expr}':s=48000:d=30", "-c:a",
                 "pcm_s16le", str(out))
        rec = self._quiet_qa(out)
        c = {x["check"]: x for x in rec["checks"]}
        self.assertEqual(c["hook_first_audio"]["status"], "FAIL")
        self.assertGreaterEqual(float(c["hook_first_audio"]["measured"].rstrip("s")), 2.9)
        self.assertTrue(any(x.get("no_voice") for x in rec["skipped_sounds"]))

    def test_talk_under_hiss_is_not_mistaken_for_typing(self):
        out = self.tmp / "hiss.wav"
        self._ff("-f", "lavfi", "-i", f"aevalsrc='{self.SYL}*gte(t,0.5)':s=48000:d=20",
                 "-f", "lavfi", "-i", "anoisesrc=c=white:a=0.02:r=48000:d=20",
                 "-filter_complex", "[0][1]amix=inputs=2:normalize=0", "-c:a", "pcm_s16le",
                 str(out))
        c = {x["check"]: x["status"] for x in self._quiet_qa(out)["checks"]}
        self.assertEqual(c["hook_first_audio"], "PASS")

    def _hold_last_mp4(self, src, dst, extra_s):
        """Lengthen the last video sample, as a screen recorder that only writes a
        frame on change does (stts, mdhd, tkhd, elst and mvhd durations)."""
        import struct
        data = bytearray(Path(src).read_bytes())

        def boxes(a, b):
            while a + 8 <= b:
                size, typ = struct.unpack(">I4s", data[a:a + 8])
                yield a, size, typ
                a += size

        def find(a, b, path):
            for i, size, typ in boxes(a, b):
                if typ == path[0]:
                    return (i, size) if len(path) == 1 else find(i + 8, i + size, path[1:])
            return None

        mi, ms = find(0, len(data), [b"moov"])
        mv = find(mi + 8, mi + ms, [b"mvhd"])[0]
        mv_ts = struct.unpack(">I", data[mv + 20:mv + 24])[0]
        for ti, tsz, typ in boxes(mi + 8, mi + ms):
            hd = find(ti + 8, ti + tsz, [b"mdia", b"hdlr"]) if typ == b"trak" else None
            if not hd or data[hd[0] + 16:hd[0] + 20] != b"vide":
                continue
            md = find(ti + 8, ti + tsz, [b"mdia", b"mdhd"])[0]
            md_ts = struct.unpack(">I", data[md + 20:md + 24])[0]
            add_m, add_mv = int(extra_s * md_ts), int(extra_s * mv_ts)

            def bump(off, by):
                struct.pack_into(">I", data, off, struct.unpack(">I", data[off:off + 4])[0] + by)
            bump(md + 24, add_m)
            st = find(ti + 8, ti + tsz, [b"mdia", b"minf", b"stbl", b"stts"])[0]
            n = struct.unpack(">I", data[st + 12:st + 16])[0]
            last = st + 16 + (n - 1) * 8
            self.assertEqual(struct.unpack(">I", data[last:last + 4])[0], 1)
            bump(last + 4, add_m)
            tk = find(ti + 8, ti + tsz, [b"tkhd"])[0]
            bump(tk + 28, add_mv)
            el = find(ti + 8, ti + tsz, [b"edts", b"elst"])
            if el:
                bump(el[0] + 16, add_mv)
            tk_d = struct.unpack(">I", data[tk + 28:tk + 32])[0]
            if struct.unpack(">I", data[mv + 24:mv + 28])[0] < tk_d:
                struct.pack_into(">I", data, mv + 24, tk_d)
        Path(dst).write_bytes(bytes(data))

    def test_a_held_last_frame_and_a_copied_cut_are_not_truncation(self):
        slide = self.tmp / "slide.png"
        self._held("vfrbase", [(0, 3)])                                # makes slide.png
        lst = self.tmp / "vfr.txt"
        lst.write_text("ffconcat version 1.0\nfile slide.png\nduration 3\n"
                       "file slide.png\nduration 0.04\n")
        base = self.tmp / "vfr_base.mp4"
        self._ff("-f", "concat", "-safe", "0", "-i", str(lst), "-fps_mode", "passthrough",
                 "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", str(base))
        silent_v = self.tmp / "vfr_held_v.mp4"
        self._hold_last_mp4(base, silent_v, 5.0)
        held = self.tmp / "vfr_held.mp4"
        self._ff("-i", str(silent_v), "-f", "lavfi", "-i",
                 f"aevalsrc='{self.SYL}':s=48000:d=8", "-map", "0:v", "-map", "1:a",
                 "-c:v", "copy", "-c:a", "aac", "-t", "8", str(held))
        c = {x["check"]: x["status"] for x in self._quiet_qa(held)["checks"]}
        self.assertEqual(c["decodes_cleanly"], "PASS")
        self.assertNotIn("picture_ends_early", c)
        full = self._make("gop.mp4", d=10, tone=self.SYL, vf="format=yuv420p")
        cut = self.tmp / "copied_cut.mp4"
        self._ff("-ss", "3.3", "-i", str(full), "-c", "copy", str(cut))
        c = {x["check"]: x["status"] for x in self._quiet_qa(cut)["checks"]}
        self.assertEqual(c["decodes_cleanly"], "PASS")

    def test_picture_that_stops_before_the_sound_is_flagged(self):
        out = self.tmp / "shortpic.mp4"
        self._ff("-f", "lavfi", "-i", "testsrc2=s=320x240:r=25:d=4", "-f", "lavfi", "-i",
                 f"aevalsrc='{self.SYL}':s=48000:d=7", "-c:v", "libx264", "-preset",
                 "ultrafast", "-c:a", "aac", str(out))
        c = {x["check"]: x for x in self._quiet_qa(out)["checks"]}
        self.assertEqual(c["picture_ends_early"]["status"], "WARN")

    def test_a_live_webm_without_a_duration_is_measured_by_what_decodes(self):
        out = self.tmp / "live.webm"
        enc = subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i",
             "testsrc2=s=320x240:r=25:d=6", "-f", "lavfi", "-i",
             f"aevalsrc='{self.SYL}':s=48000:d=6", "-c:v", "libvpx", "-deadline",
             "realtime", "-cpu-used", "8", "-b:v", "200k", "-c:a", "libopus", "-f", "webm",
             "-"], capture_output=True, check=True)
        out.write_bytes(enc.stdout)                                    # no seek: no duration
        rec = self._quiet_qa(out)
        self.assertGreater(rec["probe"]["duration_s"], 5.5)

    def test_hdr_is_tone_mapped_when_the_picture_is_re_encoded(self):
        src = self.tmp / "hlg.mp4"
        self._ff("-f", "lavfi", "-i", "testsrc2=s=320x240:r=25:d=3", "-f", "lavfi", "-i",
                 f"aevalsrc='{self.SYL}':s=48000:d=3", "-c:v", "libx264", "-preset",
                 "ultrafast", "-pix_fmt", "yuv420p", "-color_primaries", "bt2020",
                 "-color_trc", "arib-std-b67", "-colorspace", "bt2020nc", "-c:a", "aac",
                 str(src))
        out = self.tmp / "hlg_vertical.mp4"
        rep = finish.finish(str(src), str(out), finish.load_style(None), trim_head=False,
                            loudness=False, words=None, burn=False, keywords=[],
                            reframe="9:16")
        trc = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                              "-show_entries", "stream=color_transfer", "-of", "csv=p=0",
                              str(out)], capture_output=True, text=True).stdout.strip()
        if finish.tonemap_filter("arib-std-b67"):
            self.assertEqual(rep.get("hdr_tonemapped"), "arib-std-b67")
            self.assertEqual(trc, "bt709")
        else:
            self.assertTrue(any("HDR" in x for x in rep["warnings"]))

    def test_a_failed_render_leaves_no_temp_folder(self):
        scratch = self.tmp / "tmpdirs"
        scratch.mkdir()
        style = finish.load_style(None)
        style["captions"]["font"] = "No Such Font LSS"               # fails after mkdtemp
        old = tempfile.tempdir
        tempfile.tempdir = str(scratch)
        try:
            for dst, burn in ((self.tmp / "nofont.mp4", True),
                              (self.tmp / "missing" / "out.mp4", False)):
                with self.assertRaises(Exception):
                    finish.finish(str(self.src), str(dst), style, trim_head=False,
                                  loudness=False, words=[w("hello", 3.0, 3.4)], burn=burn,
                                  keywords=[], reframe="9:16")
        finally:
            tempfile.tempdir = old
        self.assertEqual(list(scratch.iterdir()), [])

    def test_ten_bit_letterbox_and_a_dark_gray_dead_screen(self):
        tenbit = self.tmp / "bars10.mkv"
        self._ff("-f", "lavfi", "-i", "testsrc2=s=320x180:r=25:d=3", "-f", "lavfi", "-i",
                 f"aevalsrc='{self.SYL}':s=48000:d=3", "-vf",
                 "pad=320:240:0:30:black,format=yuv420p10le", "-c:v", "ffv1", "-c:a",
                 "flac", str(tenbit))
        c = {x["check"]: x["status"] for x in self._quiet_qa(tenbit)["checks"]}
        self.assertEqual(c["letterbox"], "WARN")
        gray = self.tmp / "gray30.mp4"
        self._ff("-f", "lavfi", "-i", "testsrc2=s=320x240:r=25:d=2", "-f", "lavfi", "-i",
                 "color=c=0x1E1E1E:s=320x240:r=25:d=2", "-f", "lavfi", "-i",
                 "testsrc2=s=320x240:r=25:d=2", "-f", "lavfi", "-i",
                 f"aevalsrc='{self.SYL}':s=48000:d=6", "-filter_complex",
                 "[0:v][1:v][2:v]concat=n=3:v=1:a=0,format=yuv420p[v]", "-map", "[v]",
                 "-map", "3:a", "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac",
                 str(gray))
        c = {x["check"]: x["status"] for x in self._quiet_qa(gray)["checks"]}
        self.assertEqual(c["black_frames"], "FAIL")

    # ---- sixth audit (24 Oct 2026) ----

    def test_uneven_frame_timing_is_not_a_decode_error(self):
        out = self.tmp / "jitter.mp4"
        self._ff("-f", "lavfi", "-i", "testsrc2=s=320x240:r=30:d=6", "-f", "lavfi", "-i",
                 f"aevalsrc='{self.SYL}':s=48000:d=6", "-vf",
                 "setpts='(N/30+0.002*(random(0)-0.5))/TB'", "-fps_mode", "passthrough",
                 "-enc_time_base", "1/90000", "-c:v", "libx264", "-preset", "ultrafast",
                 "-c:a", "aac", str(out))
        c = {x["check"]: x["status"] for x in self._quiet_qa(out)["checks"]}
        self.assertEqual(c["decodes_cleanly"], "PASS")

    def test_a_held_last_frame_in_matroska_is_not_truncation(self):
        lst = self.tmp / "vfr2.txt"
        self._held("vfrbase2", [(0, 3)])
        lst.write_text("ffconcat version 1.0\nfile slide.png\nduration 3\n"
                       "file slide.png\nduration 0.04\n")
        base = self.tmp / "vfr2_base.mp4"
        self._ff("-f", "concat", "-safe", "0", "-i", str(lst), "-fps_mode", "passthrough",
                 "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", str(base))
        held_v = self.tmp / "vfr2_held_v.mp4"
        self._hold_last_mp4(base, held_v, 5.0)
        held = self.tmp / "vfr2_held.mkv"
        self._ff("-i", str(held_v), "-f", "lavfi", "-i", f"aevalsrc='{self.SYL}':s=48000:d=8",
                 "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "ultrafast",
                 "-c:a", "flac", "-t", "8", str(held))
        c = {x["check"]: x["status"] for x in self._quiet_qa(held)["checks"]}
        self.assertEqual(c["decodes_cleanly"], "PASS")

    def test_a_soft_mm_in_dead_air_fails_even_when_the_asr_stretches_a_word(self):
        out = self.tmp / "mm.wav"
        expr = (f"{self.SYL}*(lt(t,8)+gte(t,11))"
                "+0.05*sin(2*PI*120*t)*sin(PI*(t-9.4)/0.4)*between(t,9.4,9.8)")  # soft "mm"
        self._ff("-f", "lavfi", "-i", f"aevalsrc='{expr}':s=48000:d=20", "-c:a",
                 "pcm_s16le", str(out))
        words = self._words_for([(0.0, 8.0), (11.0, 20.0)])
        nxt = next(i for i, x in enumerate(words) if x["start"] >= 11.0)
        words[nxt] = dict(words[nxt], start=7.95)                     # stretched back 3 s
        c = {x["check"]: x["status"] for x in self._quiet_qa(out, words)["checks"]}
        self.assertEqual(c["pauses_over_fail"], "FAIL")

    def test_a_late_word_clock_does_not_invent_dead_air(self):
        out = self.tmp / "late_word.wav"
        expr = (f"{self.SYL}*(lt(t,8)+gte(t,10))"                   # talk, 0.6 s, a word,
                "+0.3*sin(2*PI*220*t)*between(t,8.5,9)")             # 1 s, talk again
        self._ff("-f", "lavfi", "-i", f"aevalsrc='{expr}':s=48000:d=20", "-c:a",
                 "pcm_s16le", str(out))
        words = self._words_for([(0.0, 8.0), (10.0, 20.0)])
        words.append(dict(w("but", 9.3, 9.7), timing="word"))       # heard 0.8 s late
        words.sort(key=lambda x: x["start"])
        c = {x["check"]: x["status"] for x in self._quiet_qa(out, words)["checks"]}
        self.assertEqual(c["pauses_over_fail"], "PASS")

    # ---- seventh audit (24 Oct 2026) ----

    def test_an_inhale_before_the_first_word_is_not_the_start(self):
        out = self.tmp / "inhale.wav"
        expr = ("0.06*(random(0)-0.5)*sin(PI*(t-1.6)/0.4)*between(t,1.6,2.0)"
                f"+{self.SYL}*gte(t,2.25)")
        self._ff("-f", "lavfi", "-i", f"aevalsrc='{expr}':s=48000:d=20", "-c:a",
                 "pcm_s16le", str(out))
        words = self._words_for([(1.9, 20.0)])                          # ASR clock early
        c = {x["check"]: x for x in self._quiet_qa(out, words)["checks"]}
        self.assertEqual(c["hook_first_speech"]["status"], "FAIL")
        self.assertGreaterEqual(float(c["hook_first_speech"]["measured"].rstrip("s")), 2.2)

    def test_trim_head_keeps_talk_the_transcript_missed(self):
        src = self._make("missed_open.mp4", d=12, tone=f"{self.SYL}*gte(t,0.4)")
        words = self._words_for([(4.0, 12.0)])                          # opening not heard
        rep = finish.finish(str(src), str(self.tmp / "missed_open_out.mp4"),
                            finish.load_style(None), trim_head=True, loudness=False,
                            words=words, burn=False, keywords=[])
        self.assertLess(rep["start_s"], 0.5)
        self.assertTrue(any("before the first transcribed word" in x for x in rep["warnings"]))

    # ---- eighth audit (24 Oct 2026) ----

    def test_auto_gain_noise_running_into_a_word_still_fails_the_pause(self):
        out = self.tmp / "agc.wav"
        self._ff("-f", "lavfi", "-i", f"aevalsrc='{self.SYL}*(lt(t,8)+gte(t,10.75))':s=48000:d=20",
                 "-f", "lavfi", "-i", "anoisesrc=a=0.001:c=pink:r=48000:d=20:seed=7",
                 "-filter_complex", "[1]volume='if(between(t,8.25,10.75),20,1)':eval=frame[n];"
                 "[0][n]amix=inputs=2:normalize=0", "-c:a", "pcm_s16le", str(out))
        words = self._words_for([(0.0, 8.0), (10.75, 20.0)])
        rec = self._quiet_qa(out, words)
        c = {x["check"]: x["status"] for x in rec["checks"]}
        self.assertEqual(c["pauses_over_fail"], "FAIL")
        self.assertGreater(rec["longest_silences"][0]["dur"], 2.4)

    def test_untitled_chapters_decode_cleanly(self):
        meta = self.tmp / "chapters.txt"
        meta.write_text(";FFMETADATA1\n\n[CHAPTER]\nTIMEBASE=1/1000\nSTART=0\nEND=3000\n\n"
                        "[CHAPTER]\nTIMEBASE=1/1000\nSTART=3000\nEND=6000\n")
        src = self._make("chap_src.mp4", d=6, tone=self.SYL)
        out = self.tmp / "chap.mp4"
        self._ff("-i", str(src), "-i", str(meta), "-map_metadata", "1", "-map_chapters", "1",
                 "-c", "copy", str(out))
        c = {x["check"]: x["status"] for x in self._quiet_qa(out)["checks"]}
        self.assertEqual(c["decodes_cleanly"], "PASS")

    def test_mono_is_normalised_as_two_channels(self):
        src = self.tmp / "mono.mp4"
        self._ff("-f", "lavfi", "-i", "testsrc2=s=320x240:r=25:d=20", "-f", "lavfi", "-i",
                 "aevalsrc='0.03*sin(2*PI*220*t)*gt(sin(2*PI*4*t),0)':s=48000:d=20",
                 "-ac", "1", "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac",
                 "-shortest", str(src))
        out = self.tmp / "mono_loud.mp4"
        rep = finish.finish(str(src), str(out), finish.load_style(None), trim_head=False,
                            loudness=True, words=None, burn=False, keywords=[])
        self.assertTrue(rep.get("mono_to_stereo"))
        ch = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0",
                             "-show_entries", "stream=channels", "-of", "csv=p=0", str(out)],
                            capture_output=True, text=True).stdout.strip()
        self.assertEqual(ch, "2")
        c = {x["check"]: x["status"] for x in self._quiet_qa(out)["checks"]}
        self.assertEqual(c["integrated_loudness"], "PASS")

    def test_trim_head_cuts_a_cough_before_dead_air(self):
        cough = "0.5*(random(0)-0.5)*between(t,1.2,1.45)"
        src = self._make("cough_head.mp4", d=12, tone=f"{self.SYL}*gte(t,2.75)+{cough}")
        rep = finish.finish(str(src), str(self.tmp / "cough_head_out.mp4"),
                            finish.load_style(None), trim_head=True, loudness=False,
                            words=self._words_for([(2.75, 12.0)]), burn=False, keywords=[])
        self.assertGreater(rep["start_s"], 2.5)
        self.assertEqual(rep["trim_head_to"], "first word")
        self.assertTrue(any("cut a" in x and "cough" in x for x in rep["warnings"]))

    @unittest.skipUnless(shutil.which("fc-match"), "fontconfig not installed")
    def test_a_burned_domain_name_stays_inside_a_vertical_frame(self):
        family = subprocess.run(["fc-match", "-f", "%{family}", "sans"],
                                capture_output=True, text=True).stdout.split(",")[0]
        style = finish.load_style(None)
        style["captions"]["font"] = family
        src = self.tmp / "wide.mp4"
        self._ff("-f", "lavfi", "-i", "color=c=0x406080:s=1280x720:r=25:d=4", "-f", "lavfi",
                 "-i", f"aevalsrc='{self.SYL}':s=48000:d=4", "-c:v", "libx264", "-preset",
                 "ultrafast", "-c:a", "aac", "-shortest", str(src))
        words = [w("Go", 0.4, 0.7), w("to", 0.7, 0.9),
                 w("localservicespotlight.com", 0.9, 2.5), w("today", 2.5, 3.0)]
        out = self.tmp / "burn916.mp4"
        rep = finish.finish(str(src), str(out), style, trim_head=False, loudness=False,
                            words=words, burn=True, keywords=[], reframe="9:16")
        W, H = rep["reframe"]["size"]
        raw = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", "1.5",
                              "-i", str(out), "-frames:v", "1", "-vf", "format=gray", "-f",
                              "rawvideo", "-"], capture_output=True).stdout
        band = [raw[y * W:(y + 1) * W] for y in range(int(H * 0.6), int(H * 0.85))]
        self.assertTrue(any(max(r) > 200 for r in band))               # the caption is there
        edge = sum(1 for r in band for x in (0, 1, 2, W - 3, W - 2, W - 1) if r[x] > 200)
        self.assertEqual(edge, 0)                                      # and not cut off

    # ---- ninth audit (24 Oct 2026) ----

    def test_a_clip_starts_in_the_silence_before_a_late_word_clock(self):
        src = self._make("late_clip.mp4", d=12, tone=f"{self.SYL}*(lt(t,4)+gte(t,4.75))")
        # The ASR heard the phrase that resumes at 4.75 s 0.8 s late.
        words = self._words_for([(0.0, 4.0)]) + self._words_for([(5.55, 12.0)])
        out = self.tmp / "late_clip_out.mp4"
        rep = finish.finish(str(src), str(out), finish.load_style(None), trim_head=False,
                            loudness=False, words=words, burn=False, keywords=[],
                            clip=(5.2, 9.0))
        self.assertGreater(rep["clip_snapped_to_words"][0], 5.4)       # on the word clock
        self.assertTrue(4.55 < rep["clip_settled_on_sound"][0] < 4.75)  # before the sound
        # 9.0 s falls mid-phrase: no pause to end in, and the receipt says so.
        self.assertTrue(any("ends inside unbroken talk" in x for x in rep["warnings"]))
        rec = self._quiet_qa(out)
        c = {x["check"]: x for x in rec["checks"]}
        self.assertNotIn("opens", c.get("cut_inside_sound", {}).get("measured", ""))

    def test_trim_head_lands_before_a_late_first_word(self):
        src = self._make("late_head.mp4", d=12, tone=f"{self.SYL}*gte(t,3.0)")
        rep = finish.finish(str(src), str(self.tmp / "late_head_out.mp4"),
                            finish.load_style(None), trim_head=True, loudness=False,
                            words=self._words_for([(3.24, 12.0)]), burn=False, keywords=[])
        self.assertEqual(rep["trim_head_to"], "first word")
        self.assertTrue(2.8 < rep["start_s"] < 3.0)                    # not 3.16, after it

    def test_a_file_that_opens_inside_a_word_is_warned(self):
        out = self.tmp / "opens_loud.wav"
        self._ff("-f", "lavfi", "-i", f"aevalsrc='{self.SYL}':s=48000:d=10", "-c:a",
                 "pcm_s16le", str(out))
        c = {x["check"]: x for x in self._quiet_qa(out, self._words_for([(0.0, 10.0)]))
             ["checks"]}
        self.assertEqual(c["cut_inside_sound"]["status"], "WARN")
        self.assertIn("opens", c["cut_inside_sound"]["measured"])
        c = {x["check"]: x for x in self._quiet_qa(out)["checks"]}
        self.assertNotIn("cut_inside_sound", c)          # no transcript, no word to cut

    def test_one_channel_stereo_is_warned_and_copied_to_both(self):
        src = self.tmp / "left_only.mp4"
        self._ff("-f", "lavfi", "-i", "testsrc2=s=320x240:r=25:d=20", "-f", "lavfi", "-i",
                 f"aevalsrc='0.1*sin(2*PI*220*t)*gt(sin(2*PI*4*t),0)*gte(t,0.3)|0':s=48000:d=20",
                 "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", "-shortest",
                 str(src))
        c = {x["check"]: x["status"] for x in self._quiet_qa(src)["checks"]}
        self.assertEqual(c["one_channel"], "WARN")
        out = self.tmp / "left_only_loud.mp4"
        rep = finish.finish(str(src), str(out), finish.load_style(None), trim_head=False,
                            loudness=True, words=None, burn=False, keywords=[])
        self.assertTrue(rep.get("one_channel_to_both"))
        err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(out), "-vn",
                              "-af", "astats", "-f", "null", "-"],
                             capture_output=True, text=True).stderr
        peaks = finish.astats_peaks(err)
        self.assertEqual(len(peaks), 2)
        self.assertLess(abs(peaks[0] - peaks[1]), 1.0)                 # both channels speak
        c = {x["check"]: x["status"] for x in self._quiet_qa(out)["checks"]}
        self.assertEqual(c["integrated_loudness"], "PASS")
        self.assertNotIn("one_channel", c)

    def test_an_encoded_true_peak_over_the_ceiling_is_rendered_again(self):
        src = self.tmp / "clicky.mp4"
        self._ff("-f", "lavfi", "-i", "testsrc2=s=320x240:r=25:d=12", "-f", "lavfi", "-i",
                 f"aevalsrc='0.05*sin(2*PI*220*t)*gt(sin(2*PI*4*t),0)+0.9*eq(mod(n,48000),24000)'"
                 ":s=48000:d=12", "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac",
                 "-b:a", "320k", "-shortest", str(src))
        style = finish.load_style(None)
        style["finish"]["true_peak_headroom_db"] = -0.9   # aim over the ceiling on purpose
        out = self.tmp / "clicky_loud.mp4"
        rep = finish.finish(str(src), str(out), style, trim_head=False, loudness=True,
                            words=None, burn=False, keywords=[])
        passes = rep.get("loudness_passes")
        self.assertIsNotNone(passes)
        self.assertGreater(passes["first"]["dbtp"], -1.0)
        self.assertEqual(passes["retries"][0].get("bitrate"), "320k")   # bitrate first
        kept = passes["retries"][passes["kept"] - 1]
        self.assertLessEqual(kept["dbtp"], -1.0)
        self.assertEqual(rep["_out_loudness"]["true_peak_dbtp"], kept["dbtp"])
        c = {x["check"]: x["status"] for x in self._quiet_qa(out)["checks"]}
        self.assertEqual(c["true_peak"], "PASS")
        self.assertEqual(c["integrated_loudness"], "PASS")

    def test_a_pause_just_over_the_line_under_steady_noise_is_listed(self):
        for gap, want in ((2.0, "near"), (2.5, "fail")):               # 2.12 s and 2.62 s
            out = self.tmp / f"steady_noise_{gap}.wav"
            self._ff("-f", "lavfi", "-i",
                     f"aevalsrc='{self.SYL}*(lt(t,8)+gte(t,{8 + gap}))':s=48000:d=20",
                     "-f", "lavfi", "-i", "anoisesrc=a=0.02:c=pink:r=48000:d=20:seed=3",
                     "-filter_complex", "[0][1]amix=inputs=2:normalize=0", "-c:a",
                     "pcm_s16le", str(out))
            words = self._words_for([(0.0, 8.0), (8 + gap, 20.0)])
            c = {x["check"]: x["status"] for x in self._quiet_qa(out, words)["checks"]}
            if want == "near":
                self.assertEqual(c["pauses_over_fail"], "PASS")
                self.assertEqual(c["pauses_near_fail"], "WARN")
            else:
                self.assertEqual(c["pauses_over_fail"], "FAIL")

    # ---- tenth audit (24 Oct 2026) ----

    def test_a_clip_asked_for_at_a_pause_keeps_its_first_word(self):
        src = self._make("pause_clip.mp4", d=12, tone=f"{self.SYL}*(lt(t,4)+gte(t,4.75))")
        words = self._words_for([(0.0, 4.0)]) + self._words_for([(4.75, 12.0)])
        nxt = next(i for i, x in enumerate(words) if x["start"] >= 4.75)
        words[nxt] = dict(words[nxt], start=4.5)                      # clocked into the pause
        out = self.tmp / "pause_clip_out.mp4"
        rep = finish.finish(str(src), str(out), finish.load_style(None), trim_head=False,
                            loudness=False, words=words, burn=False, keywords=[],
                            clip=(4.7, 9.0))
        self.assertIn("start", rep.get("clip_edges_at_pause", []))
        self.assertTrue(4.0 < rep["start_s"] < 4.75)
        srt = out.with_suffix(".captions.srt").read_text()
        first = re.search(r"(\d\d):(\d\d):(\d\d),(\d{3}) -->", srt)
        self.assertLess(int(first.group(3)) + int(first.group(4)) / 1000, 0.2)  # on its sound

    def test_a_quiet_backup_channel_is_warned_and_replaced(self):
        src = self.tmp / "backup20.mp4"
        self._ff("-f", "lavfi", "-i", "testsrc2=s=320x240:r=25:d=20", "-f", "lavfi", "-i",
                 f"aevalsrc='{self.SYL}*gte(t,0.3)|0.1*{self.SYL}*gte(t,0.3)':s=48000:d=20",
                 "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", "-shortest",
                 str(src))
        c = {x["check"]: x["status"] for x in self._quiet_qa(src)["checks"]}
        self.assertEqual(c["one_channel"], "WARN")
        rep = finish.finish(str(src), str(self.tmp / "backup20_out.mp4"),
                            finish.load_style(None), trim_head=False, loudness=True,
                            words=None, burn=False, keywords=[])
        self.assertTrue(any(s.get("quiet_backup_channel") for s in rep["steps"]))
        self.assertTrue(rep.get("one_channel_to_both"))

    def test_a_polarity_inverted_channel_is_caught_before_it_cancels(self):
        src = self.tmp / "inverted.mp4"
        self._ff("-f", "lavfi", "-i", "testsrc2=s=320x240:r=25:d=10", "-f", "lavfi", "-i",
                 f"aevalsrc='{self.SYL}|-1*{self.SYL}':s=48000:d=10", "-c:v", "libx264",
                 "-preset", "ultrafast", "-c:a", "aac", "-shortest", str(src))
        rep = finish.finish(str(src), str(self.tmp / "inverted_out.mp4"),
                            finish.load_style(None), trim_head=False, loudness=True,
                            words=None, burn=False, keywords=[])
        self.assertTrue(any(s.get("inverted_channel") for s in rep["steps"]))
        tw = _load("transcribe_words")
        self.assertEqual(tw.mono_filter(str(src), 0, 0)[0], "-af")    # one channel, not the sum

    # ---- eleventh audit (24 Oct 2026) ----

    A_ = "sin(2*PI*220*t)*gt(sin(2*PI*4*t),0)"
    B_ = "sin(2*PI*330*t)*gt(sin(2*PI*4*t+1),0)"

    def test_an_aac_short_that_ends_inside_a_word_is_warned(self):
        src = self.tmp / "ends_mid_word.mp4"                      # ends 60 ms into a syllable
        self._ff("-f", "lavfi", "-i", "testsrc2=s=320x240:r=25:d=6.06", "-f", "lavfi", "-i",
                 f"aevalsrc='{self.SYL}*gte(t,0.3)':s=48000:d=6.06", "-c:v", "libx264",
                 "-preset", "ultrafast", "-c:a", "aac", "-b:a", "256k", "-shortest", str(src))
        c = {x["check"]: x for x in self._quiet_qa(src, self._words_for([(0.25, 6.06)]))
             ["checks"]}
        self.assertIn("closes", c["cut_inside_sound"]["measured"])

    def test_finish_warnings_reach_the_receipt(self):
        src = self._make("talk_on.mp4", d=10, tone=f"{self.SYL}*gte(t,0.3)")
        wf = self.tmp / "talk_on.words.json"
        wf.write_text(json.dumps([{"word": x["word"], "start": x["start"], "end": x["end"]}
                                  for x in self._words_for([(0.25, 10.0)])]))
        out = self.tmp / "talk_on_clip.mp4"
        script = Path(finish.__file__)
        subprocess.run([sys.executable, str(script), str(src), "-o", str(out), "--clip",
                        "3.3-6.6", "--words", str(wf)], capture_output=True, text=True)
        rec = json.loads((Path(str(out) + ".qa") / "qa-receipt.json").read_text())
        c = {x["check"]: x for x in rec["checks"]}
        self.assertEqual(c["finish_report"]["status"], "WARN")
        self.assertIn("unbroken talk", c["finish_report"]["note"])
        self.assertNotEqual(rec["verdict"], "PASS")

    def test_a_camera_scratch_track_is_copied_like_a_backup(self):
        src = self.tmp / "scratch.mp4"                            # same voice, 6 ms late, -20 dB
        late = self.SYL.replace("*t", "*(t-0.006)")
        self._ff("-f", "lavfi", "-i", "testsrc2=s=320x240:r=25:d=20", "-f", "lavfi", "-i",
                 f"aevalsrc='{self.SYL}*gte(t,0.3)|0.1*{late}*gte(t,0.3)':s=48000:d=20",
                 "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", "-shortest",
                 str(src))
        roles = video_qa.channel_roles(str(src))
        self.assertLess(roles["corr"], 0.8)                       # correlation cannot tell
        self.assertEqual(roles["own_talk_s"][1], 0.0)
        rep = finish.finish(str(src), str(self.tmp / "scratch_out.mp4"),
                            finish.load_style(None), trim_head=False, loudness=True,
                            words=None, burn=False, keywords=[])
        self.assertTrue(any(s.get("quiet_backup_channel") for s in rep["steps"]))

    def test_split_mode_speakers_are_folded_to_the_centre(self):
        src = self.tmp / "split.mp4"                              # one lav per input
        left = f"0.3*{self.A_}*lt(t,10)+0.0095*{self.B_}*gte(t,10)"
        right = f"0.3*{self.B_}*gte(t,10)+0.0095*{self.A_}*lt(t,10)"
        self._ff("-f", "lavfi", "-i", "testsrc2=s=320x240:r=25:d=20", "-f", "lavfi", "-i",
                 f"aevalsrc='{left}|{right}':s=48000:d=20", "-c:v", "libx264", "-preset",
                 "ultrafast", "-c:a", "aac", "-shortest", str(src))
        c = {x["check"]: x["status"] for x in self._quiet_qa(src)["checks"]}
        self.assertEqual(c["speakers_hard_panned"], "WARN")
        out = self.tmp / "split_out.mp4"
        rep = finish.finish(str(src), str(out), finish.load_style(None), trim_head=False,
                            loudness=True, words=None, burn=False, keywords=[])
        self.assertTrue(any(s.get("speakers_hard_panned") for s in rep["steps"]))
        roles = video_qa.channel_roles(str(out))
        self.assertLess(abs(roles["rms_db"][0] - roles["rms_db"][1]), 1.0)  # both voices, both ears
        c = {x["check"]: x["status"] for x in self._quiet_qa(out)["checks"]}
        self.assertNotIn("speakers_hard_panned", c)
        self.assertEqual(c["integrated_loudness"], "PASS")

    def test_one_guest_panned_to_one_side_is_folded_to_the_centre(self):
        # Round 13: the host on a centred mic in both channels, the guest's lav on
        # the right input only. Round 12 needed BOTH channels to carry their own
        # talk, so this passed clean with the guest 26 dB hard right.
        src = self.tmp / "guest_right.mp4"
        left = f"0.3*{self.A_}*lt(t,10)+0.0095*{self.B_}*gte(t,10)"
        right = f"0.3*{self.A_}*lt(t,10)+0.3*{self.B_}*gte(t,10)"
        self._ff("-f", "lavfi", "-i", "testsrc2=s=320x240:r=25:d=20", "-f", "lavfi", "-i",
                 f"aevalsrc='{left}|{right}':s=48000:d=20", "-c:v", "libx264", "-preset",
                 "ultrafast", "-c:a", "aac", "-shortest", str(src))
        roles = video_qa.channel_roles(str(src))
        self.assertLess(roles["own_talk_s"][0], 1.0)              # the host is in both
        self.assertGreaterEqual(roles["own_talk_s"][1], 5.0)      # the guest only right
        c = {x["check"]: x["status"] for x in self._quiet_qa(src)["checks"]}
        self.assertEqual(c["speakers_hard_panned"], "WARN")
        rep = finish.finish(str(src), str(self.tmp / "guest_right_out.mp4"),
                            finish.load_style(None), trim_head=False, loudness=True,
                            words=None, burn=False, keywords=[])
        self.assertTrue(any(s.get("speakers_hard_panned") for s in rep["steps"]))

    def test_a_short_opening_on_a_one_sided_guest_line_is_folded(self):
        # Round 14: a 15 s short opening on the guest's last 4 s (right input
        # only), then the host centred. Under 5 s of one-sided talk, round 13
        # neither folded nor warned, the guest 26 dB hard right.
        src = self.tmp / "guest_line.mp4"
        left = f"0.0095*{self.B_}*lt(t,4)+0.3*{self.A_}*gte(t,4)"
        right = f"0.3*{self.B_}*lt(t,4)+0.3*{self.A_}*gte(t,4)"
        self._ff("-f", "lavfi", "-i", "testsrc2=s=320x240:r=25:d=15", "-f", "lavfi", "-i",
                 f"aevalsrc='{left}|{right}':s=48000:d=15", "-c:v", "libx264", "-preset",
                 "ultrafast", "-c:a", "aac", "-shortest", str(src))
        roles = video_qa.channel_roles(str(src))
        self.assertLess(roles["own_talk_s"][1], 5.0)               # round 13's floor
        self.assertTrue(roles["hard_panned"])
        c = {x["check"]: x["status"] for x in self._quiet_qa(src)["checks"]}
        self.assertEqual(c["speakers_hard_panned"], "WARN")
        rep = finish.finish(str(src), str(self.tmp / "guest_line_out.mp4"),
                            finish.load_style(None), trim_head=False, loudness=True,
                            words=None, burn=False, keywords=[])
        self.assertTrue(any(s.get("speakers_hard_panned") for s in rep["steps"]))

    def test_the_transcriber_keeps_a_quiet_second_speaker(self):
        src = self.tmp / "host_briefly.wav"                       # host 1.5 s of 60, own lav
        host = "between(t,20,21.5)"
        left = f"0.3*{self.A_}*{host}+0.0095*{self.B_}*(1-{host})"
        right = f"0.3*{self.B_}*(1-{host})+0.0095*{self.A_}*{host}"
        self._ff("-f", "lavfi", "-i", f"aevalsrc='{left}|{right}':s=16000:d=60", "-c:a",
                 "pcm_s16le", str(src))
        roles = video_qa.channel_roles(str(src))
        self.assertGreaterEqual(roles["rms_db"][1] - roles["rms_db"][0], 15.0)
        tw = _load("transcribe_words")
        self.assertEqual(tw.mono_filter(str(src), 0, 0), ["-ac", "1"])   # both voices heard

    # ---- twelfth audit (24-25 Oct 2026) ----

    def test_a_short_word_the_asr_heard_is_not_a_click_to_the_clip_placer(self):
        # A 70 ms "do" under room noise: with the words, finish reads it as sound
        # (as the receipt does); without them it was bridged into the pause.
        out = self.tmp / "blip_word.wav"
        self._ff("-f", "lavfi", "-i",
                 f"aevalsrc='{self.SYL}*lt(t,5)+0.3*sin(2*PI*220*t)*between(t,5.5,5.57)"
                 f"+{self.SYL}*gte(t,7.5)':s=48000:d=12",
                 "-f", "lavfi", "-i", "anoisesrc=a=0.01:c=pink:r=48000:d=12:seed=5",
                 "-filter_complex", "[0][1]amix=inputs=2:normalize=0", "-c:a", "pcm_s16le",
                 str(out))
        info = video_qa.probe(str(out))
        style = finish.load_style(None)
        words = self._words_for([(0.0, 5.0)]) + [dict(w("do", 5.5, 5.57), timing="word")] + \
            self._words_for([(7.5, 12.0)])
        with_w = finish.level_runs(str(out), style, info, 1.0, 11.0, words)
        sound_at = [k for k, a, b in with_w if a <= 5.53 < b]
        self.assertEqual(sound_at, [1])

    # ---- sixteenth audit (25 Oct 2026) ----

    def test_a_clip_that_keeps_a_word_between_whole_finishes(self):
        # The keep-whole retry (round 15) cleared the whole report it was given.
        # finish.py passes its own report, so every real run that kept a word
        # between whole died with "finish failed: 'steps'" (caught rendering
        # the round-16 cases; the sweeps call place_clip with a fresh report).
        src = self._make("keep_whole.mp4", d=9, tone=f"{self.SYL}*(lt(t,3)+gte(t,4)*lt(t,7))")
        words = self._words_for([(0.0, 3.0)]) + [dict(w("And", 4.0, 4.1), timing="word"),
                                                  dict(w("then", 4.1, 4.375), timing="word")] + \
            self._words_for([(4.5, 7.0)])
        rep = finish.finish(str(src), str(self.tmp / "keep_whole_out.mp4"),
                            finish.load_style(None), trim_head=False, loudness=False,
                            words=words, burn=False, keywords=[], clip=(4.1, 6.875))
        self.assertTrue(2.875 < rep["start_s"] < 4.0)         # in the pause, "And" whole
        self.assertTrue(any(x.startswith('the clip starts at the pause before "And"')
                            for x in rep["warnings"]))
        self.assertFalse(any("unbroken" in x for x in rep["warnings"]))
        self.assertTrue(rep["steps"])
        self.assertEqual(rep["source"], "keep_whole.mp4")

    def test_finish_notes_reach_the_receipt_as_a_note(self):
        src = self._make("noted.mp4", d=4, tone=f"{self.SYL}*gte(t,0.3)")
        rec = video_qa.qa(str(src), video_qa.load_profile(None), Path(str(src) + ".qa"),
                          frames=False,
                          finish_warnings=["loudnorm fell back to dynamic mode (linear gain "
                                           "would have clipped)"],
                          finish_notes=["the cut sits in the middle of a 0.52s gap"])
        c = {x["check"]: x for x in rec["checks"]}
        self.assertNotIn("finish_report", c)
        self.assertEqual(c["finish_note"]["status"], "NOTE")
        self.assertEqual(c["finish_note"]["measured"], 2)
        self.assertIn("0.52s gap", c["finish_note"]["note"])
        self.assertEqual(rec["verdict"], video_qa.verdict_for(
            [x["status"] for x in rec["checks"] if x["check"] != "finish_note"]))


if __name__ == "__main__":
    unittest.main()
