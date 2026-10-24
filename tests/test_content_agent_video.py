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
        self.assertEqual(c["pauses_over_fail"], "WARN")    # unmeasurable, never PASS

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
        self.assertAlmostEqual(rep["start_s"], 4.02, delta=0.01)
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
        self.assertEqual(video_qa.main([str(half), "--no-frames", "--out",
                                        str(self.tmp / "half.cli")]), 1)
        # Index at the end and cut off: nothing can be measured, exit 2, never 0.
        tail_index = self._make("tailindex.mp4", d=6, tone=self.SYL)
        cut = self.tmp / "cut.mp4"
        cut.write_bytes(tail_index.read_bytes()[:-2000])
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


if __name__ == "__main__":
    unittest.main()
