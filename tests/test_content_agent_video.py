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


if __name__ == "__main__":
    unittest.main()
