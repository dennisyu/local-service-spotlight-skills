#!/usr/bin/env python3
"""Measure a finished video against a written style profile and write a receipt.

WHY THIS EXISTS (23 Oct 2026)
Our Descript lane reported what it did ("35 fillers removed, 59:48 -> 42:21") but
never measured what it shipped. Nobody could say how loud a published video was,
whether dead air survived at the start, or whether a black flash sat at a cut.
"Claude edited it" is not evidence; the rendered file is. This script turns the
file into numbers and a PASS / WARN / FAIL verdict any agent or human can check,
whichever editor produced it (Descript, ffmpeg, video-use, a VA in CapCut).

It never plays sound. Everything is measured from the stream with ffmpeg.

What it can and cannot see (five independent audits, 23-24 Oct 2026):
- The file must decode. A decoder error, a stream that ends early against what
  the container claims (in time AND, where the container counts them, in
  frames), a WAV whose header promises more audio than it holds, or an Ogg/Opus
  file without its end page is a FAIL (`decodes_cleanly`), never a clean
  receipt for the part that played. A held last frame (a screen recorder that
  writes frames only on change) and a stream-copied cut (pre-roll frames the
  player discards) are not truncation. An MP3 cut short by under half a second
  can pass: nothing in the file says it was longer. A live-recorded WebM with no
  duration is measured by what decodes. A picture that stops before the sound
  is a WARN (`picture_ends_early`).
- With a transcript (--srt or --words) the hook check uses the first WORD;
  "[Music]", "(applause)", "*music*" cues are not words. If nothing is audible
  where the transcript puts that word, the sound wins and the receipt says the
  transcript may be for another cut. Without a transcript it can only see the
  first SOUND: a start needs 30% sound in its first half second and 0.15 s of
  sound; a short sound followed by 2 s of dead air (a cough, a thump) is skipped
  and listed; and when the file's own talk reads as tonal (spectral flatness),
  noise-like sound (static, typing that clicks like noise) is skipped too.
  Keyboard sounds that ring read as tonal and can still count as the start
  without a transcript. Audio that starts after the picture counts as dead air
  at the head; audio that stops early, at the tail (trailing dead air over
  min(10 s, a quarter of the video) is a FAIL).
- Pauses come from the peak level of every 10 ms window. Silence is 25 LU under
  the file's own loudness (clamped to -60..-30 dB), raised over the local noise
  floor wherever that floor would reach it: the quietest half-second within
  +/-2 s, plus its own spread + 3 dB (6 to 12 dB; pink and brown noise swing
  wider than white). A steady tone or hum (under 3 dB of movement, under the
  talk) is not talk; brick-limited talk is. A quiet flat sound well under the
  talk (noise that a gain control or compressor lifted inside a pause) is
  silence. A sound blip under 80 ms between silences (a click) does not break a
  pause. Where noise sits within 10 dB of the talk, or where 30 s pass without
  a quarter-second of quiet (talk over a music bed or a crowd, or a tight
  jump-cut edit), pauses cannot be heard by level and that stretch is
  unmeasurable: a quarter of the file or more makes the pause checks WARN, less
  adds a note. With word timing, masked time inside the transcript is measured
  by the gaps between words instead.
- A breath, a cough, a sniff or a thump inside dead air does not end it when
  word timing (--words) shows no word there: the whole gap counts toward the
  2-second FAIL. A short phrase between two pauses ("Okay.") is a word and
  ends it. An SRT spreads its words evenly over each cue, so with --srt alone
  the receipt cannot tell a cough from a word inside a cue: it lists stretches
  whose silence alone reaches 2 s around half a second of sound or less as a
  `possible_pauses` WARN, and says once (`word_timing` WARN) that gaps inside a
  cue are not checked. With word timing, a gap of 2 s between words that the
  level calls sound (the talk stops under a music bed or a crowd) is a
  `talk_gaps` WARN.
  Known limits: without word timing, a gap inside one cue that a music bed or a
  crowd fills (anywhere between about 10 dB under the talk and the silence
  threshold) is not flagged beyond that word_timing WARN. Pause COUNTS
  move with noise and beds (8 on a clean minute of the replay, 14 to 19 with
  noise under it).
- Black is judged frame by frame and timed by display time, so one black frame
  held for a second in a sparse screen recording is a second of black. A run of
  two or more black frames (nothing on screen brighter than RGB ~31, #1F1F1F) or
  0.08 s of them inside the video is a FAIL; a mostly dark frame with something
  on it (a dead screen with a camera tile, a dark-theme slide, a title card or a
  terminal on black) is a near-black WARN with the frame saved for a human to
  look at. A blank screen in a lighter gray is not flagged. Opening on black is
  a FAIL, ending on black a WARN. Letterbox bars are reported at any bit depth.
  Cover art in an audio file is not video; a video with no audio track gets its
  picture checked and a WARN for the missing sound.

Usage:
    video_qa.py <video> [--profile video-style.json] [--srt captions.srt |
                --words words.json] [--out <dir>] [--no-frames]

Writes <out>/qa-receipt.json, <out>/qa-receipt.md, a contact sheet,
real-frame thumbnail candidates (never generated art) and a frame from each
near-black run. Exit codes: 0 = PASS or WARN, 1 = FAIL, 2 = could not measure.
"""
from __future__ import annotations

import argparse
import bisect
import datetime as _dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_PROFILE = {
    "loudness": {"target_lufs": -14.0, "pass_tolerance_lu": 1.0,
                 "warn_tolerance_lu": 2.5, "true_peak_max_dbtp": -1.0},
    "pauses": {"silence_threshold_db": "auto", "relative_silence_lu": 25.0,
               "threshold_bounds_db": [-60.0, -30.0], "warn_pause_s": 0.6,
               "fail_pause_s": 2.0, "max_warn_pauses_per_minute": 3.0,
               # Level analysis: peak of every window_s, noise floor per block.
               "window_s": 0.01, "floor_block_s": 0.5, "floor_span_s": 2.0,
               "block_floor_percentile": 5, "noise_floor_percentile": 10,
               "speech_percentile": 95,
               "noise_floor_margin_db": 6.0, "max_noise_margin_db": 12.0,
               "steady_spread_db": 3.0, "min_speech_margin_db": 10.0,
               "bridge_sound_s": 0.08, "max_talk_without_gap_s": 30.0,
               "talk_gap_s": 0.25, "min_analysis_s": 1.0, "masked_warn_frac": 0.25,
               # A quiet, flat sound run (noise lifted by automatic gain or a
               # compressor) is not talk: under the talk by this much, this flat.
               "flat_noise_under_db": 15.0, "flat_noise_spread_db": 6.0,
               # Pad around each transcribed word when deciding whether a short
               # sound inside a pause is talk.
               "word_pad_s": 0.15,
               # A short sound joins two silences into one pause only with this
               # much silence on each side (a breath inside dead air, not choppy talk).
               "join_min_silence_s": 0.4},
    # A record-button click, typing or a cough is not a hook.
    "hook": {"max_first_speech_s": 2.0, "min_sound_s": 0.15, "merge_gap_s": 0.25,
             "min_density": 0.3, "density_window_s": 0.5, "max_skip_sound_s": 0.6,
             "transcript_lag_s": 1.0,
             # Talk has tonal windows (spectral flatness at or under voiced_flatness);
             # noise-like typing, clicks and static do not. A start needs
             # min_voiced_s of tonal sound within 0.3 s; noise-like sound longer
             # than max_unvoiced_lead_s before it is skipped (ffmpeg 5.0+; older
             # builds skip this rule). Keyboard sounds that ring read as tonal.
             "voiced_flatness": 0.3, "min_voiced_s": 0.05, "max_unvoiced_lead_s": 0.5,
             # ...and only when at least this share of the file's loud sound
             # windows reads as voiced (clean talk ~1.0; talk under hiss far less).
             "voiced_min_frac": 0.8},
    # Tail silence over max is a WARN; over the smaller of fail_s and fail_frac of
    # the video (a microphone that died) it is a FAIL.
    "tail": {"max_trailing_silence_s": 1.5, "fail_trailing_silence_s": 10.0,
             "fail_trailing_frac": 0.25},
    # Near-black: at least pic_th of pixels at or under pix_th of the luma range.
    # Black: no pixel brighter than that (nothing on screen at all). A run counts
    # at min_black_frames frames OR min_black_s of display time (a held frame).
    "black": {"min_black_frames": 2, "min_black_s": 0.08, "pic_th": 0.90,
              "pix_th": 0.12, "scan_height": 180,
              "letterbox_min_px": 8, "near_black_frames_saved": 10},
    "frames": {"contact_sheet_tiles": 16, "thumbnail_candidates": 6},
}

# ffmpeg prints tiny times in scientific notation ("silence_start: 2.26757e-05");
# a parser without the exponent reads that as 2.27 s and hides the dead air.
_FLOAT = r"(-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?|-?inf|nan)"
SILENT_LUFS = -69.0  # ebur128 reports about -70 LUFS for digital silence
NOT_MEASURED = object()  # sentinel: the first-sound scan was not run
MIN_LOUDNESS_S = 0.4     # ebur128 needs one 400 ms block for an integrated reading


def deep_merge(base: dict, override: dict) -> dict:
    out = json.loads(json.dumps(base))
    for key, val in (override or {}).items():
        if isinstance(val, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], val)
        else:
            out[key] = val
    return out


def _check_types(merged: dict, default: dict, where: str = "qa") -> None:
    """A string where a number belongs gives a cryptic TypeError mid-run; name
    the key instead. 'auto' is the one string a numeric key may hold."""
    for key, dval in default.items():
        val = merged.get(key)
        path = f"{where}.{key}"
        if isinstance(dval, dict):
            if not isinstance(val, dict):
                raise ValueError(f"profile key {path} must be an object")
            _check_types(val, dval, path)
        elif isinstance(dval, bool):
            continue
        elif isinstance(dval, (int, float)) or (key == "silence_threshold_db"):
            ok = (isinstance(val, (int, float)) and not isinstance(val, bool)) or (
                key == "silence_threshold_db" and val == "auto")
            if not ok:
                raise ValueError(f"profile key {path} must be a number, got {val!r}")
        elif isinstance(dval, list) and dval and all(
                isinstance(x, (int, float)) for x in dval):
            if not (isinstance(val, list) and all(
                    isinstance(x, (int, float)) and not isinstance(x, bool) for x in val)):
                raise ValueError(f"profile key {path} must be a list of numbers")
        elif isinstance(dval, list) and not isinstance(val, list):
            raise ValueError(f"profile key {path} must be a list")


def load_profile(path: str | None) -> dict:
    if not path:
        return json.loads(json.dumps(DEFAULT_PROFILE))
    try:
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
    except OSError as exc:
        raise ValueError(f"could not read profile {path}: {exc.strerror or exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"profile {path} is not valid JSON: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError(f"profile {path} must be a JSON object")
    merged = deep_merge(DEFAULT_PROFILE, raw.get("qa", raw))
    _check_types(merged, DEFAULT_PROFILE)
    return merged


def run(cmd: list[str], cwd: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, errors="replace", cwd=cwd)


def _rotation(stream: dict) -> int:
    rot = 0
    try:
        rot = int(float(stream.get("tags", {}).get("rotate", 0)))
    except (TypeError, ValueError):
        rot = 0
    for sd in stream.get("side_data_list", []) or []:
        if "rotation" in sd:
            try:
                rot = int(float(sd["rotation"]))
            except (TypeError, ValueError):
                pass
    return rot % 360


def _rate(text) -> float:
    num, _, den = str(text or "0/1").partition("/")
    try:
        n, d = float(num), float(den or 1)
    except ValueError:
        return 0.0
    return n / d if d else 0.0


def _float(val) -> float | None:
    try:
        f = float(val)
    except (TypeError, ValueError):
        return None
    return f if f == f else None


def _tag_duration(stream: dict) -> float | None:
    """Matroska/WebM keep stream length in a DURATION tag ("00:00:30.000000000")."""
    tag = (stream.get("tags") or {}).get("DURATION")
    m = re.fullmatch(r"(\d+):(\d+):(\d+(?:\.\d+)?)", str(tag or "").strip())
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else None


def _tag_length(stream: dict, start: float) -> float | None:
    """Matroska writes the stream's END time in its DURATION tag; the length is that
    minus the stream's start (audio delayed 0.8 s is 0.8 s shorter, not truncated)."""
    end = _tag_duration(stream)
    return None if end is None else max(0.0, end - max(0.0, start))


def container_truncation(path: str) -> str | None:
    """What the container's own header says about a cut-off file, for formats whose
    decoders stop quietly at the end of the data: a WAV data chunk larger than the
    bytes present, an Ogg/Opus stream without its end-of-stream page."""
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as fh:
            head = fh.read(12)
            if head[:4] in (b"RIFF", b"RF64") and head[8:12] == b"WAVE":
                pos = 12
                while pos + 8 <= size:
                    fh.seek(pos)
                    cid, raw = fh.read(4), fh.read(4)
                    if len(raw) < 4:
                        break
                    csz = int.from_bytes(raw, "little")
                    if cid == b"data":
                        if csz not in (0, 0xFFFFFFFF) and pos + 8 + csz > size + 1:
                            return (f"the WAV header promises {csz:,} bytes of audio but "
                                    f"the file holds {size - pos - 8:,} (cut off)")
                        return None
                    pos += 8 + csz + (csz & 1)
            elif head[:4] == b"OggS":
                fh.seek(max(0, size - 65536))
                tail = fh.read()
                i = tail.rfind(b"OggS")
                if i >= 0 and i + 5 < len(tail) and not tail[i + 5] & 0x04:
                    return "the Ogg stream has no end-of-stream page (cut off)"
    except OSError:
        return None
    return None


def probe(path: str) -> dict:
    """Container facts, with the picture size as DISPLAYED (phone rotation applied).
    Cover art inside an audio file (attached_pic) is not treated as video."""
    res = run(["ffprobe", "-v", "error", "-show_entries",
               "format=duration,bit_rate,size,start_time:stream=codec_type,codec_name,"
               "width,height,r_frame_rate,avg_frame_rate,sample_rate,channels,duration,"
               "start_time,pix_fmt,color_range,color_transfer,nb_frames:"
               "stream_disposition=attached_pic:"
               "stream_tags=rotate,DURATION:stream_side_data=rotation", "-of", "json", path])
    if res.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {res.stderr.strip()[:400]}")
    data = json.loads(res.stdout)
    fmt = data.get("format", {})
    info = {"duration_s": _float(fmt.get("duration")) or 0.0,
            "start_s": _float(fmt.get("start_time")) or 0.0,
            "size_bytes": int(fmt.get("size", 0) or 0),
            "bit_rate": int(fmt.get("bit_rate", 0) or 0),
            "video": None, "audio": None}
    for st in data.get("streams", []):
        if (st.get("codec_type") == "video" and info["video"] is None
                and not (st.get("disposition") or {}).get("attached_pic")):
            # A timebase (1000/1, 90000/1) is not a frame rate; of the sane ones take
            # the higher, because a variable-rate screen recording reports a low
            # average while its busy stretches run at the nominal rate.
            rates = [r for r in (_rate(st.get("avg_frame_rate")),
                                 _rate(st.get("r_frame_rate"))) if 0 < r <= 240]
            fps = max(rates) if rates else 0.0
            w, h, rot = st.get("width"), st.get("height"), _rotation(st)
            if rot in (90, 270):
                w, h = h, w
            pix = str(st.get("pix_fmt") or "")
            vstart = _float(st.get("start_time")) or 0.0
            info["video"] = {"codec": st.get("codec_name"), "width": w, "height": h,
                             "fps": round(fps, 3), "rotation": rot, "start_s": vstart,
                             "duration_s": _float(st.get("duration")) or _tag_length(st, vstart),
                             "nb_frames": int(st["nb_frames"]) if str(st.get("nb_frames", ""))
                             .isdigit() else None,
                             "transfer": st.get("color_transfer"),
                             "full_range": st.get("color_range") == "pc"
                             or pix.startswith("yuvj")}
        elif st.get("codec_type") == "audio" and info["audio"] is None:
            astart = _float(st.get("start_time")) or 0.0
            info["audio"] = {"codec": st.get("codec_name"),
                             "sample_rate": int(st.get("sample_rate", 0) or 0),
                             "channels": st.get("channels"), "start_s": astart,
                             "duration_s": _float(st.get("duration")) or _tag_length(st, astart)}
    return info


def parse_ebur128_summary(text: str) -> dict:
    """Parse the Summary block ffmpeg's ebur128 filter prints at the end."""
    tail = text[text.rfind("Summary:"):] if "Summary:" in text else text
    out = {}
    for key, pat in (("integrated_lufs", r"I:\s+" + _FLOAT + r"\s+LUFS"),
                     ("lra_lu", r"LRA:\s+" + _FLOAT + r"\s+LU"),
                     ("true_peak_dbtp", r"Peak:\s+" + _FLOAT + r"\s+dBFS")):
        m = re.search(pat, tail)
        if m:
            out[key] = float(m.group(1))
    return out


def parse_silences(text: str, duration: float) -> list[dict]:
    """Pair silence_start / silence_end lines; an open start runs to EOF."""
    silences, start = [], None
    for line in text.splitlines():
        m = re.search(r"silence_start:\s*" + _FLOAT, line)
        if m:
            start = max(0.0, float(m.group(1)))
            continue
        m = re.search(r"silence_end:\s*" + _FLOAT, line)
        if m and start is not None:
            end = float(m.group(1))
            silences.append({"start": round(start, 3), "end": round(end, 3),
                             "dur": round(end - start, 3)})
            start = None
    if start is not None and duration > start:
        silences.append({"start": round(start, 3), "end": round(duration, 3),
                         "dur": round(duration - start, 3)})
    return silences


def silence_threshold(prof: dict, integrated_lufs: float | None) -> float:
    """Absolute dB from the profile, or 'auto' = N LU under the file's loudness."""
    pp = prof["pauses"]
    thr = pp.get("silence_threshold_db", "auto")
    if thr != "auto":
        return float(thr)
    lo, hi = pp.get("threshold_bounds_db", [-60.0, -30.0])
    if integrated_lufs is None or integrated_lufs != integrated_lufs \
            or integrated_lufs <= SILENT_LUFS:
        return float(lo)
    return round(max(lo, min(hi, integrated_lufs - pp.get("relative_silence_lu", 25.0))), 1)


def measure_loudness(path: str, start: float = 0.0, seconds: float | None = None) -> dict:
    cmd = ["ffmpeg", "-nostdin", "-hide_banner", "-nostats"]
    if start:
        cmd += ["-ss", f"{start:.3f}"]
    if seconds:
        cmd += ["-t", f"{seconds:.3f}"]
    cmd += ["-i", path, "-vn", "-map", "0:a:0", "-af", "ebur128=peak=true",
            "-f", "null", "-"]
    res = run(cmd)
    if res.returncode != 0:
        raise RuntimeError(f"loudness scan failed: {first_error(res.stderr)}")
    return parse_ebur128_summary(res.stderr)


def first_error(stderr: str) -> str:
    """The line that says what went wrong, not the last six lines of a dump."""
    lines = [l.strip() for l in stderr.splitlines() if l.strip()]
    keys = ("error", "invalid", "not supported", "could not", "unable", "no such",
            "does not contain", "not found", "failed", "unknown")
    for line in lines:
        low = line.lower()
        if line.startswith(("{", "}", '"')):
            continue
        if any(k in low for k in keys):
            return line[:300]
    return " | ".join(lines[-3:])[:300] if lines else "no output from ffmpeg"


# ---------------------------------------------------------------- audio levels

def _percentile(values: list[float], pct: float) -> float:
    vals = sorted(values)
    return vals[min(len(vals) - 1, max(0, int(len(vals) * pct / 100.0)))]


_FILTERS: dict = {}


def has_filter(name: str) -> bool:
    """Whether this ffmpeg build has a filter (aspectralstats needs ffmpeg 5.0+)."""
    if name not in _FILTERS:
        res = run(["ffmpeg", "-hide_banner", "-filters"])
        _FILTERS[name] = bool(re.search(rf"^\s*\S+\s+{re.escape(name)}\s", res.stdout, re.M))
    return _FILTERS[name]


def audio_scan(path: str, start: float = 0.0, seconds: float | None = None,
               sample_rate: int | None = None, window_s: float = 0.01) -> dict:
    """Peak level (dBFS, loudest channel) and spectral flatness (of the loudest
    channel; 0 = a pure tone, 1 = white noise) of every ~10 ms window, from one
    decode pass that also collects decoder errors and how much audio actually
    decoded. Digital silence reads -120. Voiced speech sits under 0.15 flatness,
    keyboard clicks and other noise bursts near 0.8. About 50 s for a 66-minute
    file on 2 cores. `flatness` is None when ffmpeg lacks aspectralstats."""
    sr = sample_rate or 48000
    n = max(16, int(round(sr * window_s)))
    spectral = has_filter("aspectralstats")
    cmd = ["ffmpeg", "-nostdin", "-hide_banner", "-nostats", "-loglevel", "error"]
    if start:
        cmd += ["-ss", f"{start:.3f}"]
    if seconds:
        cmd += ["-t", f"{seconds:.3f}"]
    chain = f"asetnsamples=n={n}:p=0,"
    if spectral:
        chain += (f"aspectralstats=win_size={n}:overlap=0:measure=flatness,"
                  "astats=metadata=1:reset=1:measure_perchannel=Peak_level:")
    else:
        chain += "astats=metadata=1:reset=1:measure_perchannel=none:"
    chain += "measure_overall=Peak_level,ametadata=mode=print:file=-"
    cmd += ["-i", path, "-vn", "-map", "0:a:0", "-af", chain, "-f", "null", "-"]
    res = run(cmd)
    peaks, flat = [], []
    fl: dict = {}
    pk: dict = {}

    def num(text: str) -> float | None:
        try:
            v = float(text)
        except ValueError:
            return None
        return v if v == v else None

    for line in res.stdout.splitlines():
        if line.startswith("frame:"):
            fl, pk = {}, {}
            continue
        m = re.match(r"lavfi\.(aspectralstats|astats)\.(\w+)\.(flatness|Peak_level)=(\S+)",
                     line)
        if not m:
            continue
        kind, ch, val = m.group(1), m.group(2), num(m.group(4))
        if kind == "aspectralstats":
            fl[ch] = val
        elif ch != "Overall":
            pk[ch] = val if val is not None else -120.0
        else:
            peaks.append(-120.0 if val is None or val < -120.0 else min(val, 0.0))
            if spectral:
                loud = max(pk, key=pk.get) if pk else None
                flat.append(fl.get(loud) if loud is not None else None)
    if res.returncode != 0 and not peaks:
        raise RuntimeError(f"audio could not be decoded: {first_error(res.stderr)}")
    errors = [l.strip() for l in res.stderr.splitlines() if l.strip()]
    w = n / float(sr)
    return {"peaks": peaks, "window_s": w, "decoded_s": round(len(peaks) * w, 3),
            "errors": errors, "flatness": flat if spectral else None}


def classify_levels(peaks: list[float], w: float, prof: dict,
                    integrated_lufs: float | None) -> dict:
    """Label every window silent (0), sound (1) or unmeasurable (2).

    The threshold starts at the relative rule (silence_threshold) and is raised
    block by block to clear the local noise floor: the half-second block with the
    lowest 5th percentile within +/- floor_span_s gives the floor (even fast talk
    drops to the room's level between words somewhere in 4 s; steady noise never
    drops below itself), and the margin over it is that quiet block's own spread
    plus 3 dB, between 6 and 12 dB (pink and brown noise swing wider than white;
    audit round 4). A block whose own spread is under steady_spread_db is a tone
    or hum, not talk, and counts as silence unless something rises 6 dB over it.
    A block is unmeasurable where the raised threshold sits within
    min_speech_margin_db of the talk. Files shorter than min_analysis_s use the
    relative threshold alone (too little sound to estimate a floor).
    After labelling: sound blips shorter than bridge_sound_s between silences (a
    mouse click, a noise spike) are silence, and any stretch of max_talk_without_gap_s
    with no silence of talk_gap_s is unmeasurable: real talk breathes (the
    66-minute replay's longest stretch was 20.4 s), so a minute with no gap at all
    is talk over a music bed or crowd, where pauses cannot be heard by level."""
    pp = prof["pauses"]
    n = len(peaks)
    base = silence_threshold(prof, integrated_lufs)
    fixed = pp.get("silence_threshold_db", "auto") != "auto"
    margin = float(pp.get("noise_floor_margin_db", 6.0))
    max_margin = float(pp.get("max_noise_margin_db", 12.0))
    steady_db = float(pp.get("steady_spread_db", 3.0))
    smargin = float(pp.get("min_speech_margin_db", 10.0))
    fpct, spct = pp.get("noise_floor_percentile", 10), pp.get("speech_percentile", 95)
    bpct = pp.get("block_floor_percentile", 5)
    audible = [p for p in peaks if p > -100.0]
    gfloor = round(_percentile(audible, fpct), 1) if audible else -120.0
    loud = [p for p in audible if p >= gfloor + margin]
    if len(loud) >= 10:
        speech = round(_percentile(loud, spct), 1)
    else:
        speech = round(max(audible), 1) if audible else -120.0
    has_sound = speech > -100.0
    short = n * w < float(pp.get("min_analysis_s", 1.0))
    B = max(1, int(round(pp.get("floor_block_s", 0.5) / w)))
    nb = max(1, -(-n // B))
    lo5, hi95 = [], []
    for b in range(nb):
        chunk = sorted(peaks[b * B:(b + 1) * B]) or [-120.0]
        lo5.append(chunk[min(len(chunk) - 1, int(len(chunk) * bpct / 100.0))])
        hi95.append(chunk[min(len(chunk) - 1, int(len(chunk) * 0.95))])
    span = max(0, int(round(pp.get("floor_span_s", 2.0) / (B * w))))
    thr, masked, steady = [], [], []
    for b in range(nb):
        q = min(range(max(0, b - span), min(nb, b + span + 1)), key=lambda k: lo5[k])
        spread = hi95[q] - lo5[q]
        m = margin if spread >= max_margin else min(max_margin, max(margin, spread + 3.0))
        need = -120.0 if short else lo5[q] + m
        if fixed:
            t, msk = base, has_sound and not short and need > base
        else:
            t = max(base, need)
            msk = has_sound and not short and t > speech - smargin
        thr.append(round(t, 1))
        masked.append(bool(msk))
        # A steady block is a tone or hum only when it sits under the talk; brick-
        # limited speech is flat too, but at the talk's own level.
        steady.append(not short and lo5[b] > -100.0 and hi95[b] - lo5[b] < steady_db
                      and hi95[b] < speech - margin)
    state = bytearray(n)
    for i, p in enumerate(peaks):
        b = i // B
        if masked[b]:
            state[i] = 2
        elif p < thr[b] or (steady[b] and p < lo5[b] + margin):
            state[i] = 0
        else:
            state[i] = 1
    noise_masked = sum(1 for x in state if x == 2)
    if not short:  # under a second there is too little to call anything a blip
        _bridge_blips(state, max(1, int(round(pp.get("bridge_sound_s", 0.08) / w))))
        _flat_noise_to_silence(state, peaks, speech - float(pp.get("flat_noise_under_db", 15.0)),
                               float(pp.get("flat_noise_spread_db", 6.0)),
                               max(1, int(round(0.1 / w))))
        _mask_gapless_talk(state, w, float(pp.get("max_talk_without_gap_s", 30.0)),
                           float(pp.get("talk_gap_s", 0.25)))
    gapless = sum(1 for x in state if x == 2) - noise_masked
    return {"state": state, "block": B, "thresholds": thr, "masked_blocks": masked,
            "base_threshold_db": base, "floor_db": gfloor, "speech_db": speech,
            "noise_masked_s": round(noise_masked * w, 2),
            "gapless_masked_s": round(max(0, gapless) * w, 2)}


def _flat_noise_to_silence(state: bytearray, peaks: list[float], under: float,
                           max_spread: float, min_windows: int) -> None:
    """A sound run that stays well under the talk and barely moves is noise that a
    gain control or compressor lifted inside a pause, not talk: silence."""
    for s_, i0, i1 in _runs(state):
        if s_ != 1 or i1 - i0 < min_windows:
            continue
        vals = sorted(peaks[i0:i1])
        p10 = vals[int(len(vals) * 0.10)]
        p95 = vals[min(len(vals) - 1, int(len(vals) * 0.95))]
        if p95 < under and p95 - p10 < max_spread:
            state[i0:i1] = bytes(i1 - i0)


def _bridge_blips(state: bytearray, max_windows: int) -> None:
    """A sound run of at most max_windows with silence on both sides (or silence on
    one side and the file edge on the other) is a click or a noise spike: silence."""
    runs = _runs(state)
    for k, (s, i0, i1) in enumerate(runs):
        if s != 1 or i1 - i0 > max_windows:
            continue
        before = runs[k - 1][0] if k > 0 else 0
        after = runs[k + 1][0] if k + 1 < len(runs) else 0
        if before == 0 and after == 0 and len(runs) > 1:
            state[i0:i1] = bytes(i1 - i0)


def _mask_gapless_talk(state: bytearray, w: float, max_s: float, gap_s: float) -> None:
    """Mark as unmeasurable every stretch of max_s or longer that never falls silent
    for gap_s: pauses there are covered by a music bed, a crowd or noise."""
    if max_s <= 0:
        return
    runs = _runs(state)
    cuts = [(i0, i1) for s, i0, i1 in runs if s == 0 and (i1 - i0) * w >= gap_s]
    edges = [0] + [x for c in cuts for x in c] + [len(state)]
    for a, b in zip(edges[0::2], edges[1::2]):
        if (b - a) * w >= max_s:
            state[a:b] = bytes([2]) * (b - a)


def _runs(state: bytearray) -> list[tuple[int, int, int]]:
    out, i, n = [], 0, len(state)
    while i < n:
        j = i
        s = state[i]
        while j < n and state[j] == s:
            j += 1
        out.append((s, i, j))
        i = j
    return out


def _first_voice(voice: list[tuple[float, float]], a: float, b: float,
                 need: float, within: float = 0.3) -> float | None:
    """The first moment in [a, b] where voiced windows add up to `need` seconds
    within `within` seconds; None when the stretch has no voice."""
    i = bisect.bisect_left(voice, (a,)) - 1
    i = max(i, 0)
    while i < len(voice) and voice[i][0] < b:
        vs, ve = voice[i]
        if ve <= a:
            i += 1
            continue
        t0 = max(vs, a)
        total, j = 0.0, i
        while j < len(voice) and voice[j][0] < t0 + within:
            total += max(0.0, min(voice[j][1], t0 + within) - max(voice[j][0], t0))
            j += 1
        if total >= need - 1e-9:
            return t0
        i += 1
    return None


def pick_start(sound: list[tuple[float, float]], masked: list[tuple[float, float]],
               length: float, hp: dict, fail_pause_s: float,
               voice: list[tuple[float, float]] | None = None):
    """The first real start. A candidate is the onset of a sound run whose next
    density_window_s is at least min_density sound (typing and clicks are sparse,
    even when talk follows straight after them). From there, runs closer than
    merge_gap_s form one burst, which needs min_sound_s of sound; a short burst
    (under max_skip_sound_s) followed by fail_pause_s of silence is skipped and
    reported (a cough before dead air). With `voice` (voiced intervals from the
    spectral flatness), a burst with no voice in it (typing, clicks, a noise) is
    skipped, and one that runs unvoiced for more than max_unvoiced_lead_s starts
    at its voice; both are reported with no_voice. Returns (start, skipped,
    masked), where masked=True means an unmeasurable stretch comes before any
    start."""
    win = hp.get("density_window_s", 0.5)
    need = hp.get("min_density", 0.3) * win
    gap_join = hp.get("merge_gap_s", 0.25)
    first_masked = masked[0][0] if masked else None
    skipped = []
    k, n = 0, len(sound)
    while k < n:
        a = sound[k][0]
        if first_masked is not None and first_masked <= a:
            return None, skipped, True
        cover, j = 0.0, k
        while j < n and sound[j][0] < a + win:
            cover += min(sound[j][1], a + win) - sound[j][0]
            j += 1
        if cover < need:
            k += 1
            continue
        end, total, j = sound[k][1], sound[k][1] - sound[k][0], k + 1
        while j < n and sound[j][0] - end < gap_join:
            total += sound[j][1] - sound[j][0]
            end = sound[j][1]
            j += 1
        if total < hp.get("min_sound_s", 0.15):
            k = j
            continue
        nxt = sound[j][0] if j < n else length
        gap_end = nxt
        if first_masked is not None and end <= first_masked < nxt:
            gap_end = None  # what follows cannot be measured: do not skip on it
        if (gap_end is not None and total < hp.get("max_skip_sound_s", 0.6)
                and gap_end - end >= fail_pause_s):
            skipped.append({"at_s": round(a, 3), "sound_s": round(total, 3),
                            "silence_after_s": round(gap_end - end, 3)})
            k = j
            continue
        if voice is not None:
            v = _first_voice(voice, a, end, hp.get("min_voiced_s", 0.05))
            if v is None:
                skipped.append({"at_s": round(a, 3), "sound_s": round(total, 3),
                                "no_voice": True})
                k = j
                continue
            if v - a > hp.get("max_unvoiced_lead_s", 0.5):
                skipped.append({"at_s": round(a, 3), "sound_s": round(v - a, 3),
                                "no_voice": True})
                return round(v, 3), skipped, False
        return round(a, 3), skipped, False
    return None, skipped, first_masked is not None


def first_sustained_sound(silences: list[dict], length: float,
                          min_sound_s: float = 0.15, merge_gap_s: float = 0.25,
                          min_density: float = 0.3, fail_pause_s: float = 2.0) -> float | None:
    """pick_start() over the gaps between silencedetect-style silences."""
    runs, t = [], 0.0
    for s in sorted(silences, key=lambda x: x["start"]):
        if s["start"] > t:
            runs.append((t, s["start"]))
        t = max(t, s["end"])
    if t < length:
        runs.append((t, length))
    hp = {"min_sound_s": min_sound_s, "merge_gap_s": merge_gap_s,
          "min_density": min_density, "density_window_s": 0.5, "max_skip_sound_s": 0.6}
    return pick_start(runs, [], length, hp, fail_pause_s)[0]


def analyze_audio(path: str, prof: dict, start: float = 0.0,
                  seconds: float | None = None, sample_rate: int | None = None,
                  integrated_lufs: float | None = None, scan: dict | None = None) -> dict:
    """Silences (on the window's own timeline), the first real start, and how much
    of the audio could be measured at all."""
    pp, hp = prof["pauses"], prof["hook"]
    scan = scan or audio_scan(path, start, seconds, sample_rate, pp.get("window_s", 0.01))
    peaks, w = scan["peaks"], scan["window_s"]
    length = scan["decoded_s"]
    cl = classify_levels(peaks, w, prof, integrated_lufs)
    state = cl["state"]
    runs = _runs(state)
    min_d = min(pp["warn_pause_s"], prof["tail"]["max_trailing_silence_s"])

    def span(i0, i1):
        return round(i0 * w, 3), round(min(i1 * w, length), 3)

    voice, voiced_frac = None, None
    flat = scan.get("flatness")
    if flat:
        vf = float(hp.get("voiced_flatness", 0.3))
        # Self-check first: the rule is used only when this recording's own talk
        # reads as voiced. Hiss (white noise under the talk) lifts the flatness of
        # every window, and there the rule would mistake talk for noise.
        loud = [flat[i] for i in range(min(len(state), len(flat)))
                if state[i] == 1 and flat[i] is not None
                and peaks[i] >= cl["speech_db"] - 10.0]
        if len(loud) >= 50:
            voiced_frac = round(sum(1 for f in loud if f <= vf) / len(loud), 3)
    if voiced_frac is not None and voiced_frac >= float(hp.get("voiced_min_frac", 0.8)):
        voice, i0 = [], None
        for i in range(len(state) + 1):
            on = (i < len(state) and state[i] == 1 and i < len(flat)
                  and flat[i] is not None and flat[i] <= vf)
            if on and i0 is None:
                i0 = i
            elif not on and i0 is not None:
                voice.append(span(i0, i))
                i0 = None
    silences, sound, masked_iv, runs_s = [], [], [], []
    for s, i0, i1 in runs:
        a, b = span(i0, i1)
        runs_s.append((s, a, b))
        if s == 0 and b - a >= min_d:
            silences.append({"start": a, "end": b, "dur": round(b - a, 3)})
        elif s == 1:
            sound.append((a, b))
        elif s == 2:
            masked_iv.append((a, b))
    if length < float(pp.get("min_analysis_s", 1.0)):
        # A clip under a second: the first sound is the start, no burst rules.
        first, skipped, hook_masked = (sound[0][0] if sound else None), [], False
    else:
        first, skipped, hook_masked = pick_start(sound, masked_iv, length, hp,
                                                 pp["fail_pause_s"], voice)
    masked_s = round(sum(b - a for a, b in masked_iv), 2)
    thr = cl["thresholds"]
    raised_s = round(sum(1 for t in thr if t > cl["base_threshold_db"] + 0.05)
                     * cl["block"] * w, 1)
    noise = {"base_threshold_db": cl["base_threshold_db"],
             "threshold_db_range": [min(thr), max(thr)] if thr else [None, None],
             "raised_s": min(raised_s, length), "floor_db": cl["floor_db"],
             "speech_db": cl["speech_db"], "masked_s": masked_s,
             "masked_frac": round(masked_s / length, 3) if length else 0.0,
             "hook_measurable": not hook_masked,
             # Where an unmeasurable stretch begins when it hides the start: the
             # start is at least this late, so a late one can still FAIL.
             "hook_masked_from_s": masked_iv[0][0] if hook_masked and masked_iv else None,
             "tail_measurable": not (state and state[-1] == 2), "note": ""}
    if masked_s >= 0.05:
        why = []
        if cl["noise_masked_s"] >= 0.05:
            why.append(f"noise, music or a tone within {pp.get('min_speech_margin_db', 10.0):g} "
                       "dB of the talk")
        if cl["gapless_masked_s"] >= 0.05:
            why.append(f"{pp.get('max_talk_without_gap_s', 30.0):g} s or more without a "
                       "quarter-second of quiet (a music bed or crowd under the talk, or a "
                       "tight jump-cut edit)")
        noise["note"] = (f"{masked_s:.1f}s ({noise['masked_frac']:.0%}) could not be "
                         f"measured by level: {'; '.join(why)}")
    elif noise["raised_s"] > 0:
        noise["note"] = (f"threshold raised over room noise for {noise['raised_s']:.0f}s "
                         f"(up to {max(thr)} dB)")
    noise["first_any_sound_s"] = sound[0][0] if sound else None
    noise["voiced_frac"] = voiced_frac
    noise["voice_rule"] = voice is not None
    return {"silences": silences, "first_sound": first, "skipped": skipped,
            "noise": noise, "decoded_s": length, "errors": scan["errors"],
            "runs": runs_s, "min_pause_s": min_d, "voice": voice}


# ---------------------------------------------------------------- transcript vs level

def talk_spans(words: list[dict] | None, pad: float = 0.15) -> tuple[str, list]:
    """('word', padded word intervals) when the words carry real word timing,
    ('cue', cue intervals) when they come from an SRT/VTT spread across cues,
    ('none', []) without a transcript."""
    if not words:
        return "none", []
    if all(w.get("timing") == "cue" for w in words):
        cues: dict = {}
        for w in words:
            a, b = cues.get(w.get("cue"), (w["start"], w["end"]))
            cues[w.get("cue")] = (min(a, w["start"]), max(b, w["end"]))
        return "cue", sorted(cues.values())
    return "word", sorted((w["start"] - pad, w["end"] + pad) for w in words)


def merge_pauses(runs: list[tuple[int, float, float]], timing: str, spans: list,
                 max_skip: float, allow: tuple[str, ...] = ("none",),
                 min_side: float = 0.4) -> list[dict]:
    """Join silences across a short sound (under max_skip, with at least min_side
    of silence on each side, so the syllables of choppy talk never chain) whose
    verdict is in `allow`. A sound is 'talk' when a transcribed word overlaps it (word timing);
    with cue timing a sound inside a cue is 'unknown' and one outside every cue is
    'none'; without a transcript every short sound is 'unknown'. (Spectral
    flatness cannot stand in for word timing here: a breath, a sniff or a thump
    is band-limited and reads as tonal as a vowel.) Called with
    allow=('none',) it gives the pauses we can stand behind (a breath, a cough, a
    sniff, a thump inside dead air does not end it); with ('none', 'unknown') it
    gives the stretches a person should look at."""
    def verdict(a: float, b: float) -> str:
        hit = any(x < b and y > a for x, y in spans)
        if timing == "word":
            return "talk" if hit else "none"
        if timing == "cue":
            return "unknown" if hit else "none"
        return "unknown"

    out, i, n = [], 0, len(runs)
    while i < n:
        k, a, b = runs[i]
        if k != 0:
            i += 1
            continue
        end, j, joined, snd = b, i + 1, 0, 0.0
        while j + 1 < n and runs[j][0] == 1 and runs[j + 1][0] == 0:
            sa, sb = runs[j][1], runs[j][2]
            before = runs[j - 1][2] - runs[j - 1][1]
            after = runs[j + 1][2] - runs[j + 1][1]
            if (sb - sa >= max_skip or before < min_side or after < min_side
                    or verdict(sa, sb) not in allow):
                break
            end, j, joined, snd = runs[j + 1][2], j + 2, joined + 1, snd + sb - sa
        out.append({"start": round(a, 3), "end": round(end, 3), "dur": round(end - a, 3),
                    "joined": joined, "sound_s": round(snd, 3)})
        i = j
    return out


# ---------------------------------------------------------------- picture

def black_min_s(prof: dict, fps: float | None) -> float:
    """Time equivalent of min_black_frames at the file's rate (half a frame of
    slack), capped at min_black_s. Runs are counted in frames; this is reported."""
    bp = prof["black"]
    cap = float(bp["min_black_s"])
    if not fps or fps <= 0:
        return cap
    return round(min(cap, (bp.get("min_black_frames", 2) - 0.5) / fps), 4)


def measure_video(path: str, prof: dict, info: dict | None = None) -> dict:
    """Black and near-black runs from every frame's luma statistics, with each run
    timed by DISPLAY time (a black frame held for a second in a sparse screen
    recording is a second of black), plus how much of the picture decoded.

    Per frame, on a limited-range copy scaled to scan_height: near-black when the
    90th-percentile luma is at or under the pix_th level (90% of the picture is
    dark); black when even the brightest pixel is (nothing on screen at all). A run
    is 'black' when it holds min_black_frames consecutive black frames or
    min_black_s of black display time, otherwise 'near-black' (a dead screen with a
    camera tile, a dark-theme slide, a title card or terminal on black)."""
    import tempfile
    bp = prof["black"]
    v = (info or {}).get("video") or {}
    level = int(round(16 + bp["pix_th"] * 219))
    if abs(bp.get("pic_th", 0.90) - 0.90) > 1e-6:
        raise ValueError("black.pic_th must be 0.90 (the scan reads the 90th-percentile "
                         "luma of each frame)")
    work = tempfile.mkdtemp(prefix="vqa-")
    try:
        res = run(["ffmpeg", "-nostdin", "-hide_banner", "-nostats", "-loglevel", "error",
                   "-i", os.path.abspath(path), "-an", "-map", "0:v:0", "-vf",
                   f"scale=-2:{bp['scan_height']}:out_range=tv,format=yuv420p,signalstats,"
                   "metadata=mode=print:key=lavfi.signalstats.YHIGH:file=yhigh.txt,"
                   "metadata=mode=print:key=lavfi.signalstats.YMAX:file=ymax.txt",
                   "-f", "null", "-"], cwd=work)
        hi_txt = Path(work, "yhigh.txt").read_text(errors="replace") \
            if Path(work, "yhigh.txt").exists() else ""
        mx_txt = Path(work, "ymax.txt").read_text(errors="replace") \
            if Path(work, "ymax.txt").exists() else ""
    finally:
        shutil.rmtree(work, ignore_errors=True)
    if res.returncode != 0 and not hi_txt:
        raise RuntimeError(f"video scan failed: {first_error(res.stderr)}")
    pat = (r"frame:(\d+)\s+pts:\S+\s+pts_time:" + _FLOAT +
           r"\s+lavfi\.signalstats\.{key}=" + _FLOAT)
    highs = {int(m.group(1)): (float(m.group(2)), float(m.group(3)))
             for m in re.finditer(pat.replace("{key}", "YHIGH"), hi_txt)}
    maxes = {int(m.group(1)): float(m.group(3))
             for m in re.finditer(pat.replace("{key}", "YMAX"), mx_txt)}
    order = sorted(highs)
    fps = v.get("fps") or 25.0
    times = [highs[n][0] for n in order]
    shows = [max(0.0, b - a) for a, b in zip(times, times[1:])]
    if times:
        # The last frame shows until the stream ends: a screen recording that only
        # writes frames on change can hold its last frame for seconds.
        end = None
        if v.get("duration_s"):
            end = (v.get("start_s") or 0.0) + v["duration_s"]
        last = 1.0 / fps
        if end is not None and end - times[-1] > last and v.get("nb_frames") \
                and len(order) >= v["nb_frames"]:
            last = end - times[-1]
        shows.append(last)
    decoded = round(times[-1] + shows[-1], 3) if times else None
    near = [highs[n][1] <= level for n in order]
    black = [maxes.get(n, 255.0) <= level for n in order]
    min_frames = int(bp.get("min_black_frames", 2))
    min_s = float(bp.get("min_black_s", 0.08))
    out, i, total = [], 0, len(order)
    while i < total:
        if not near[i]:
            i += 1
            continue
        j = i
        while j < total and near[j]:
            j += 1
        disp = sum(shows[i:j])
        best_f, best_s, run_f, run_s = 0, 0.0, 0, 0.0
        for k in range(i, j):
            if black[k]:
                run_f, run_s = run_f + 1, run_s + shows[k]
                best_f, best_s = max(best_f, run_f), max(best_s, run_s)
            else:
                run_f, run_s = 0, 0.0
        if j - i >= min_frames or disp >= min_s:
            out.append({"start": round(times[i], 3), "end": round(times[i] + disp, 3),
                        "dur": round(disp, 3), "frames": j - i, "first_frame": i,
                        "last_frame": j - 1, "frame_count": total,
                        "black_frames": sum(black[i:j]),
                        "kind": "black" if (best_f >= min_frames or best_s >= min_s)
                        else "near-black"})
        i = j
    errors = [l.strip() for l in res.stderr.splitlines()
              if l.strip() and re.search(r"error|invalid|corrupt|partial file", l, re.I)]
    return {"runs": out, "decoded_s": decoded, "errors": errors, "frames": len(order)}


def parse_black(text: str) -> list[dict]:
    """blackdetect output (kept for callers of the round-1 scanner)."""
    out = []
    for m in re.finditer(r"black_start:\s*" + _FLOAT + r"\s+black_end:\s*" + _FLOAT
                         + r"\s+black_duration:\s*" + _FLOAT, text):
        out.append({"start": float(m.group(1)), "end": float(m.group(2)),
                    "dur": float(m.group(3)), "kind": "black"})
    return out


def active_area(path: str, start: float, seconds: float = 4.0) -> tuple[int, int, int, int]:
    """The picture inside any letterbox bars (Zoom and webinar exports often carry
    a few black rows). (0, 0, 0, 0) when nothing could be detected."""
    res = run(["ffmpeg", "-nostdin", "-hide_banner", "-nostats", "-ss", f"{start:.3f}",
               "-t", f"{seconds:.3f}", "-i", path, "-an", "-vf",
               "cropdetect=limit=0.094:round=2:reset=0", "-f", "null", "-"])
    found = re.findall(r"crop=(\d+):(\d+):(\d+):(\d+)", res.stderr)
    if not found:
        return (0, 0, 0, 0)
    w, h, x, y = (int(v) for v in max(set(found), key=found.count))
    return (w, h, x, y)


def letterbox(path: str, info: dict, prof: dict) -> dict | None:
    """Bars that persist at three points of the video; None when there are none."""
    v, dur = info["video"], info["duration_s"]
    bars = []
    for frac in (0.1, 0.5, 0.9):
        w, h, x, y = active_area(path, max(0.0, dur * frac - 1.0), min(2.0, dur))
        if not w or not h:
            return None
        bars.append((v["width"] - w, v["height"] - h))
    lim = prof["black"]["letterbox_min_px"]
    side, top = min(b[0] for b in bars), min(b[1] for b in bars)
    if side >= lim or top >= lim:
        return {"side_px_total": side, "top_bottom_px_total": top}
    return None


def grab_frames(path: str, duration: float, outdir: Path, prof: dict,
                near_black: list[dict] | None = None) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    tiles = int(prof["frames"]["contact_sheet_tiles"])
    cols = 4
    rows = max(1, -(-tiles // cols))
    step = max(duration / (tiles + 1), 0.04)
    sheet = outdir / "contact-sheet.jpg"
    run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-i", path,
         "-vf", f"fps=1/{step:.3f},scale=480:-2,tile={cols}x{rows}:padding=4",
         "-frames:v", "1", str(sheet)])
    n = int(prof["frames"]["thumbnail_candidates"])
    times = pick_thumbnail_times(path, duration, n, outdir)
    thumbs = []
    for i, (t, score) in enumerate(times):
        dest = outdir / f"thumb-candidate-{i + 1:02d}.jpg"
        # Save exactly the frame that was scored: a real frame, never generated art.
        run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-ss",
             f"{t:.3f}", "-i", path, "-frames:v", "1", "-vf", "scale=1280:-2",
             "-q:v", "2", str(dest)])
        if dest.exists() and dest.stat().st_size > 0:
            thumbs.append({"file": dest.name, "at_s": round(t, 3), "score": score})
    looks = []
    for i, b in enumerate((near_black or [])[:int(prof["black"]["near_black_frames_saved"])]):
        t = b["start"] + b["dur"] / 2
        dest = outdir / f"near-black-{i + 1:02d}.jpg"
        run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-ss",
             f"{t:.3f}", "-i", path, "-frames:v", "1", "-vf", "scale=960:-2",
             "-q:v", "3", str(dest)])
        if dest.exists() and dest.stat().st_size > 0:
            looks.append({"file": dest.name, "at_s": round(t, 3)})
    return {"contact_sheet": sheet.name if sheet.exists() else None,
            "thumbnail_method": "face+sharpness" if times and times[0][1] is not None
            else "even spacing",
            "thumbnail_candidates": thumbs, "near_black_frames": looks}


def pick_thumbnail_times(path: str, duration: float, n: int, outdir: Path,
                         samples: int = 48) -> list[tuple[float, float | None]]:
    """Rank sampled frames by face size and sharpness when OpenCV 4.x is installed.

    A face filling the frame makes a thumbnail; a screen share does not. Without
    OpenCV, or on any OpenCV error, this falls back to even spacing and the
    receipt says so. It never aborts the QA run.
    """
    even = [(duration * (i + 1) / (n + 1), None) for i in range(n)]
    probe_dir = outdir / ".thumb-probe"
    try:
        import cv2  # optional; OpenCV 4.x (5.x dropped the Haar CascadeClassifier)
        cascade = cv2.CascadeClassifier(cv2.data.haarcascades +
                                        "haarcascade_frontalface_default.xml")
        if cascade.empty():
            return even
        probe_dir.mkdir(parents=True, exist_ok=True)
        scored = []
        for i in range(samples):
            t = duration * (i + 0.5) / samples
            f = probe_dir / f"p{i:03d}.jpg"
            run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-ss",
                 f"{t:.3f}", "-i", path, "-frames:v", "1", "-vf", "scale=640:-2", str(f)])
            img = cv2.imread(str(f)) if f.exists() and f.stat().st_size > 0 else None
            if img is None:
                continue
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            if gray.mean() < 25:  # black or near-black frame
                continue
            fh = gray.shape[0]
            faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6,
                                             minSize=(int(fh * 0.12), int(fh * 0.12)))
            big = max((h for (_, _, _, h) in faces), default=0) / float(fh)
            # A screen share full of photos has many small faces; a speaker on
            # camera has one or two big ones. Reward the big face, punish the crowd.
            crowd = max(1, len(faces) - 1)
            # Screen shares are dense with text edges (measured Oct 2026 on a Zoom
            # replay: camera frames 0.03 Canny edge density, screen shares
            # 0.08–0.16). A face inside a screenshot is not the speaker.
            busy = float((cv2.Canny(gray, 100, 200) > 0).mean())
            screen = 0.25 if busy > 0.06 else 1.0
            sharp = min(cv2.Laplacian(gray, cv2.CV_64F).var(), 600) / 600
            scored.append((t, round(big * big * 100 / crowd * screen + sharp, 3)))
    except Exception:  # noqa: BLE001 - a thumbnail helper must never sink the receipt
        return even
    finally:
        shutil.rmtree(probe_dir, ignore_errors=True)
    if not scored:
        return even
    scored.sort(key=lambda x: -x[1])
    picked: list[tuple[float, float]] = []
    gap = duration / (n * 3)
    for t, s in scored:  # keep picks apart so the candidates differ
        if all(abs(t - p) >= gap for p, _ in picked):
            picked.append((t, s))
        if len(picked) == n:
            break
    return picked  # best first


# ---------------------------------------------------------------- verdicts

def verdict_for(values: list[str]) -> str:
    if "FAIL" in values:
        return "FAIL"
    if "WARN" in values:
        return "WARN"
    return "PASS"


def evaluate(info: dict, loud: dict, silences: list[dict], black: list[dict],
             prof: dict, first_speech: float | None = None,
             first_audio=NOT_MEASURED, threshold_db: float | None = None,
             bars: dict | None = None, noise: dict | None = None,
             decode: dict | None = None, words: list[dict] | None = None,
             possible_pauses: list[dict] | None = None) -> list[dict]:
    """Turn measurements into checks. `first_speech` (first transcribed word) wins
    over `first_audio` (first real sound, None = none found); without either, the
    leading silence is used. `noise` is analyze_audio()'s summary: unmeasurable
    stretches turn the hook, tail and pause checks into WARN instead of PASS.
    `decode` = {"ok": bool, "note": str}: a file that does not decode is a FAIL.
    Statuses: PASS, WARN, FAIL, or N/A for a check that could not apply."""
    dur = info["duration_s"]
    audio_end = (info.get("audio") or {}).get("duration_s") or dur
    checks = []

    def add(name, status, measured, expected, note=""):
        checks.append({"check": name, "status": status, "measured": measured,
                       "expected": expected, "note": note})

    if decode is not None:
        add("decodes_cleanly", "PASS" if decode.get("ok", True) else "FAIL",
            "yes" if decode.get("ok", True) else "no", "whole file decodes, no errors",
            decode.get("note", ""))
    if "audio" in info and info["audio"] is None:
        add("audio", "WARN", "none", "an audio track",
            "no audio stream: loudness, hook and pauses cannot be checked (fine for "
            "silent b-roll, a defect for anything with talk)")
        return checks + _video_checks(info, black, prof, bars)

    lp = prof["loudness"]
    il = loud.get("integrated_lufs")
    silent = il is None or il != il or il <= SILENT_LUFS
    if silent and 0 < audio_end < MIN_LOUDNESS_S:
        add("integrated_loudness", "WARN", None, f"{lp['target_lufs']} LUFS",
            f"audio is {audio_end:.2f}s, shorter than one 400 ms loudness block")
    elif silent:
        add("integrated_loudness", "FAIL", None if il is None else f"{il:.1f} LUFS",
            f"{lp['target_lufs']} LUFS", "silent or unmeasurable audio")
    else:
        off = abs(il - lp["target_lufs"])
        status = ("PASS" if off <= lp["pass_tolerance_lu"]
                  else "WARN" if off <= lp["warn_tolerance_lu"] else "FAIL")
        add("integrated_loudness", status, f"{il:.1f} LUFS",
            f"{lp['target_lufs']} ±{lp['pass_tolerance_lu']} LU",
            "" if status == "PASS" else
            f"{il - lp['target_lufs']:+.1f} LU from target; run finish.py --loudness")
    tp = loud.get("true_peak_dbtp")
    if tp is not None and not silent:
        status = "PASS" if tp <= lp["true_peak_max_dbtp"] else (
            "FAIL" if tp > 0 else "WARN")
        add("true_peak", status, f"{tp:.1f} dBTP", f"≤ {lp['true_peak_max_dbtp']} dBTP",
            "clipping" if tp > 0 else "")

    pp, tl = prof["pauses"], prof["tail"]
    noise = noise or {}
    legacy_ok = noise.get("measurable", True)
    masked_frac = noise.get("masked_frac", 0.0 if legacy_ok else 1.0)
    hook_ok = noise.get("hook_measurable", legacy_ok)
    tail_ok = noise.get("tail_measurable", legacy_ok)
    noise_note = noise.get("note", "")
    lead = silences[0] if silences and silences[0]["start"] <= 0.05 else None
    trail = (silences[-1] if silences and silences[-1]["end"] >= audio_end - 0.15
             else None)
    hook_max = prof["hook"]["max_first_speech_s"]
    lag = prof["hook"].get("transcript_lag_s", 1.0)
    # Compare the transcript with the first AUDIBLE sound, not the first start the
    # burst rules accept: a short "So," before dead air is still audible.
    heard = (noise or {}).get("first_any_sound_s", first_audio)
    if (first_speech is not None and isinstance(heard, (int, float))
            and not isinstance(heard, bool) and heard - first_speech > lag):
        # Nothing is audible where the transcript puts the first word: trust the
        # sound, and say the transcript is out of step with this file.
        name, start_s = "hook_first_speech", first_audio
        start_s = heard
        note = (f"the transcript puts the first word at {first_speech:.2f}s but nothing "
                f"is audible until {heard:.2f}s; is the transcript for another cut?")
    elif first_speech is not None:
        name, start_s, note = "hook_first_speech", first_speech, "first transcribed word"
    else:
        name = "hook_first_audio"
        # None = measured, no real start; NOT_MEASURED = fall back to the lead silence.
        start_s = (first_audio if first_audio is not NOT_MEASURED
                   else (lead["end"] if lead else 0.0))
        note = ("first real SOUND, not first word (clicks, typing, noise and a cough "
                "before dead air are skipped); give --srt or --words to check the "
                "first word")
    masked_from = noise.get("hook_masked_from_s")
    if first_speech is None and not hook_ok and masked_from is not None \
            and masked_from > hook_max:
        add(name, "FAIL", f"≥ {masked_from:.2f}s", f"≤ {hook_max}s",
            f"dead air before the hook: nothing starts for {masked_from:.2f}s, then "
            "noise or music hides the exact start; trim the head")
    elif first_speech is None and not hook_ok:
        add(name, "WARN", "unmeasurable", f"≤ {hook_max}s",
            f"{noise_note or 'the start cannot be told from noise or music'}; "
            "give --srt or --words to check the first word")
    elif start_s is None:
        add(name, "FAIL", "no sound", f"≤ {hook_max}s", "no audible start found")
    else:
        ok = start_s <= hook_max
        add(name, "PASS" if ok else "FAIL", f"{start_s:.2f}s", f"≤ {hook_max}s",
            note if ok else f"dead air before the hook; trim the head. ({note})")

    tail_s = trail["dur"] if trail and trail is not lead else 0.0
    tail_warn = tl["max_trailing_silence_s"]
    tail_fail = min(tl.get("fail_trailing_silence_s", 10.0),
                    tl.get("fail_trailing_frac", 0.25) * max(dur, 0.001))
    tail_fail = max(tail_fail, tail_warn)
    if not tail_ok:
        add("trailing_silence", "WARN", "unmeasurable", f"≤ {tail_warn}s", noise_note)
    else:
        status = ("PASS" if tail_s <= tail_warn else
                  "FAIL" if tail_s > tail_fail else "WARN")
        add("trailing_silence", status, f"{tail_s:.2f}s", f"≤ {tail_warn}s",
            "" if status == "PASS" else
            f"the audio goes dead for the last {tail_s:.1f}s"
            + ("; did the microphone stop?" if status == "FAIL" else ""))

    body = [s for s in silences if s is not lead and s is not trail]
    long_pauses = [s for s in body if s["dur"] >= pp["fail_pause_s"]]
    warn_pauses = [s for s in body if pp["warn_pause_s"] <= s["dur"] < pp["fail_pause_s"]]
    minutes = max(dur / 60.0, 1 / 60.0)
    rate = len(warn_pauses) / minutes
    thr_note = f"silence = under {threshold_db} dB" if threshold_db is not None else ""
    if noise_note:
        thr_note = f"{thr_note} ({noise_note})" if thr_note else noise_note
    unmeasurable = masked_frac >= pp.get("masked_warn_frac", 0.25)
    if long_pauses:
        add("pauses_over_fail", "FAIL", len(long_pauses),
            f"0 pauses ≥ {pp['fail_pause_s']}s inside the video",
            "; ".join([f"{s['start']:.1f}s ({s['dur']:.1f}s)"
                       for s in sorted(long_pauses, key=lambda s: -s["dur"])[:5]]
                      + ([thr_note] if thr_note else [])))
    elif unmeasurable:
        add("pauses_over_fail", "WARN", "unmeasurable",
            f"0 pauses ≥ {pp['fail_pause_s']}s inside the video", thr_note)
    else:
        add("pauses_over_fail", "PASS", 0,
            f"0 pauses ≥ {pp['fail_pause_s']}s inside the video", thr_note)
    # The transcript hears pauses in TALK that the level cannot: the speaker stops
    # while a music bed or a crowd 20-25 dB down keeps sounding (audit round 4).
    if words:
        ws = sorted(words, key=lambda x: x["start"])
        talk_gaps = []
        for a_w, b_w in zip(ws, ws[1:]):
            gs, ge = a_w["end"], b_w["start"]
            if ge - gs >= pp["fail_pause_s"] and not any(
                    min(s_["end"], ge) - max(s_["start"], gs) >= 0.5 * (ge - gs)
                    for s_ in long_pauses):
                talk_gaps.append((gs, ge - gs))
        if talk_gaps:
            add("talk_gaps", "WARN", len(talk_gaps),
                f"0 gaps ≥ {pp['fail_pause_s']}s between transcribed words",
                "the talk stops while other sound continues (a music bed, a crowd, "
                "noise); check each is meant: "
                + "; ".join(f"{g:.1f}s ({d:.1f}s)" for g, d in talk_gaps[:5]))
    if words and all(x.get("timing") == "cue" for x in words):
        add("word_timing", "WARN", "cue-level (SRT/VTT)", "word-level (--words)",
            "an SRT spreads its words evenly across each cue, so a gap inside a cue (the "
            "talk stops under music or a crowd) and a breath or cough inside dead air "
            "cannot be pinned; add --words from transcribe_words.py")
    if possible_pauses:
        add("possible_pauses", "WARN", len(possible_pauses),
            f"0 stretches of {pp['fail_pause_s']}s+ broken only by a short sound",
            "silent except for a short sound that may be a breath, a cough or a one-word "
            "reply; listen to each (word timing from --words decides this "
            "automatically): " + "; ".join(f"{x['start']:.1f}s ({x['dur']:.1f}s)"
                                           for x in possible_pauses[:6]))
    expected_rate = (f"≤ {pp['max_warn_pauses_per_minute']}/min of {pp['warn_pause_s']}–"
                     f"{pp['fail_pause_s']}s pauses")
    if unmeasurable:
        add("pauses_over_warn_rate", "WARN", "unmeasurable", expected_rate, thr_note)
    else:
        add("pauses_over_warn_rate",
            "PASS" if rate <= pp["max_warn_pauses_per_minute"] else "WARN",
            f"{rate:.2f}/min ({len(warn_pauses)} total)", expected_rate, thr_note)
    return checks + _video_checks(info, black, prof, bars)


def _video_checks(info: dict, black: list[dict], prof: dict,
                  bars: dict | None) -> list[dict]:
    checks = []
    dur = info["duration_s"]

    def add(name, status, measured, expected, note=""):
        checks.append({"check": name, "status": status, "measured": measured,
                       "expected": expected, "note": note})

    if info["video"] is None:
        add("black_frames", "N/A", None, "video only", "no video stream")
        return checks
    bp = prof["black"]
    fps = info["video"].get("fps") or 0
    frame = 1.0 / fps if fps else 0.04
    head, tail, body = [], [], []
    for b in black:
        long_run = b["dur"] >= 0.5
        if "first_frame" in b:  # frame-indexed scan: the first frame opens the video
            opens = b["first_frame"] == 0 or (long_run and b["start"] <= 0.5)
        else:
            opens = b["start"] <= frame * 0.5 + 0.01 or (long_run and b["start"] <= 0.5)
        if "last_frame" in b and "frame_count" in b:
            closes = b["last_frame"] == b["frame_count"] - 1 or (
                long_run and b["end"] >= dur - 0.5)
        else:
            closes = b["end"] >= dur - (frame + 0.05) or (long_run and b["end"] >= dur - 0.5)
        if opens:
            head.append(b)
        elif closes:
            tail.append(b)
        else:
            body.append(b)
    hard = [b for b in body if b.get("kind", "black") == "black"]
    near = [b for b in body if b.get("kind") == "near-black"]
    frames = bp.get("min_black_frames", 2)
    add("black_frames", "FAIL" if hard else "PASS", len(hard),
        f"0 runs of {frames}+ black frames (or {bp.get('min_black_s', 0.08)}s of a held "
        "black frame) inside the video",
        "; ".join(f"{b['start']:.2f}s ({b['dur']:.2f}s)" for b in hard[:5]))
    if near:
        add("near_black", "WARN", len(near),
            f"0 runs of {frames}+ frames ≥ {round(bp['pic_th'] * 100)}% dark",
            "mostly dark with something on screen: a dead screen with a camera tile, a "
            "dark-theme slide, or a title card on black; look at the near-black frame(s) "
            "saved with this receipt: "
            + "; ".join(f"{b['start']:.2f}s ({b['dur']:.2f}s)" for b in near[:5]))
    if head:
        h = head[0]
        hard_open = h.get("kind", "black") == "black"
        add("black_open", "FAIL" if hard_open else "WARN", f"{h['dur']:.2f}s", "0s",
            "video opens on black; the hook frame must be the first frame"
            if hard_open else "video opens near-black; check the first frame")
    if tail:
        add("black_close", "WARN", f"{tail[-1]['dur']:.2f}s", "0s",
            "video ends on black; trim it or put the next step on screen")
    if bars:
        add("letterbox", "WARN",
            f"{bars['top_bottom_px_total']}px top+bottom, {bars['side_px_total']}px sides",
            "no bars", "bars waste picture: a short cut with finish.py --reframe drops "
            "them; for long-form, crop in the editor or leave them")
    return checks


def prof_hook_max(prof: dict) -> float:
    return float(prof["hook"]["max_first_speech_s"])


def first_word_s(words: list[dict] | None) -> float | None:
    return min((w["start"] for w in words), default=None) if words else None


def sha256_head(path: str, limit: int = 64 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read(limit))
    return h.hexdigest()


def render_markdown(rec: dict) -> str:
    lines = [f"# Video QA receipt — {rec['verdict']}", "",
             f"- File: `{rec['file']}` ({rec['probe']['size_bytes']:,} bytes, "
             f"sha256 of first 64 MiB `{rec['sha256_head'][:16]}…`)",
             f"- Duration: {rec['probe']['duration_s']:.2f}s",
             f"- Silence threshold: {rec.get('silence_threshold_db')} dB"
             + (f" ({rec['noise_floor']['note']})"
                if (rec.get("noise_floor") or {}).get("note") else ""),
             f"- Measured: {rec['measured_at']} with {rec['tool']}", "",
             "| Check | Status | Measured | Expected | Note |",
             "|---|---|---|---|---|"]
    for c in rec["checks"]:
        lines.append(f"| {c['check']} | {c['status']} | {c['measured']} | "
                     f"{c['expected']} | {c['note']} |")
    fr = rec.get("frames")
    if fr:
        lines += ["", f"Contact sheet: `{fr.get('contact_sheet')}`. "
                  f"Thumbnail candidates ({fr.get('thumbnail_method')}), "
                  "real frames, best first: " +
                  ", ".join(f"`{t['file']}` @{t['at_s']}s"
                            for t in fr.get("thumbnail_candidates", []))]
        if fr.get("near_black_frames"):
            lines += ["", "Near-black frames to look at: " +
                      ", ".join(f"`{t['file']}` @{t['at_s']}s"
                                for t in fr["near_black_frames"])]
    if rec.get("skipped_sounds"):
        lines += ["", "Sounds skipped as the start: " + ", ".join(
            f"{s['at_s']}s ({s['sound_s']}s with no voice in it: typing, clicks or noise)"
            if s.get("no_voice") else
            f"{s['at_s']}s ({s['sound_s']}s, then {s['silence_after_s']}s of silence)"
            for s in rec["skipped_sounds"])]
    lines += ["", "The JSON lists the ten longest silences. Nothing here was played "
              "aloud. A human still judges taste: hook strength, story, and whether "
              "each cut keeps meaning."]
    return "\n".join(lines) + "\n"


def _coalesce(runs: list[tuple[int, float, float]]) -> list[tuple[int, float, float]]:
    out: list[list] = []
    for k, a, b in runs:
        if out and out[-1][0] == k and a <= out[-1][2] + 0.011:
            out[-1][2] = max(out[-1][2], b)
        else:
            out.append([k, a, b])
    return [tuple(x) for x in out]


def _merge_gap(silences: list[dict], start: float, end: float) -> list[dict]:
    """Add the stretch [start, end] (audio missing from the file) as silence."""
    if end - start < 0.05:
        return silences
    out = sorted(silences + [{"start": round(start, 3), "end": round(end, 3),
                              "dur": round(end - start, 3)}], key=lambda s: s["start"])
    merged: list[dict] = []
    for s in out:
        if merged and s["start"] <= merged[-1]["end"] + 0.02:
            merged[-1]["end"] = max(merged[-1]["end"], s["end"])
            merged[-1]["dur"] = round(merged[-1]["end"] - merged[-1]["start"], 3)
        else:
            merged.append(dict(s))
    return merged


def qa(path: str, profile: dict, outdir: Path, frames: bool = True,
       words: list[dict] | None = None) -> dict:
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("ffmpeg and ffprobe must be on PATH")
    info = probe(path)
    if info["audio"] is None and info["video"] is None:
        raise RuntimeError("no audio or video stream to measure")
    if info["audio"] is None:
        return _qa_video_only(path, info, profile, outdir, frames)
    loud = measure_loudness(path)
    aud = analyze_audio(path, profile, sample_rate=info["audio"]["sample_rate"],
                        integrated_lufs=loud.get("integrated_lufs"))
    a, v = info["audio"], info["video"]
    a_start = a["start_s"] or 0.0
    vid = measure_video(path, profile, info) if v else {"runs": [], "decoded_s": None,
                                                        "errors": [], "frames": None}
    if not info["duration_s"]:
        # A live-recorded WebM carries no duration: use what actually decoded.
        info["duration_s"] = max(aud["decoded_s"], vid["decoded_s"] or 0.0)
        if v and not v.get("duration_s") and vid["decoded_s"]:
            v["duration_s"] = vid["decoded_s"]
    claimed_a = a["duration_s"] or (None if v else info["duration_s"])
    problems = []
    cut = container_truncation(path)
    if cut:
        problems.append(cut)
    if aud["errors"]:
        problems.append(f"{len(aud['errors'])} audio decoder error(s), first: "
                        f"{aud['errors'][0][:160]}")
    if claimed_a and claimed_a - aud["decoded_s"] > 0.5:
        problems.append(f"audio decoded {aud['decoded_s']:.2f}s of the "
                        f"{claimed_a:.2f}s the file claims (truncated?)")
    if v:
        claimed_v = v["duration_s"] or info["duration_s"]
        # Short in time AND (when the container counts frames) short in frames: a
        # held last frame is short in neither, a stream-copied cut drops its
        # pre-roll frames but keeps its length, a cut-off file is short in both.
        short = (vid["decoded_s"] is not None and claimed_v
                 and claimed_v - vid["decoded_s"] > 0.5)
        all_frames = (v.get("nb_frames") and vid.get("frames") is not None
                      and vid["frames"] >= v["nb_frames"] - 1)
        if short and not all_frames:
            extra = (f", {vid['frames']} of {v['nb_frames']} frames"
                     if v.get("nb_frames") and vid.get("frames") is not None else "")
            problems.append(f"video decoded {vid['decoded_s']:.2f}s of the "
                            f"{claimed_v:.2f}s the file claims{extra} (truncated?)")
        if vid["errors"]:
            problems.append(f"{len(vid['errors'])} video decoder error(s), first: "
                            f"{vid['errors'][0][:160]}")
    decode = {"ok": not problems, "note": "; ".join(problems)}
    # Put the audio on the file's timeline: audio that starts after the picture is
    # dead air at the head, audio that stops before it is dead air at the tail.
    head_gap = max(0.0, a_start - (v["start_s"] if v else a_start))
    if v:
        v_end = v["start_s"] + (v["duration_s"] or info["duration_s"])
        file_len = v_end - v["start_s"]
    else:
        file_len = aud["decoded_s"]
    audio_end_on_file = head_gap + aud["decoded_s"]
    pp = profile["pauses"]
    # Every silence/sound/unmeasurable run on the file's timeline, with missing
    # audio at either end as silence; then pauses joined across short non-talk
    # sounds (a breath, a cough), judged against the transcript when there is one.
    runs = [(k, round(x + head_gap, 3), round(y + head_gap, 3)) for k, x, y in aud["runs"]]
    if head_gap >= 0.05:
        runs.insert(0, (0, 0.0, round(head_gap, 3)))
    if file_len - audio_end_on_file >= 0.05:
        runs.append((0, round(audio_end_on_file, 3), round(file_len, 3)))
    runs = _coalesce(runs)
    timing, spans = talk_spans(words, pp.get("word_pad_s", 0.15))
    max_skip = profile["hook"].get("max_skip_sound_s", 0.6)
    side = float(pp.get("join_min_silence_s", 0.4))
    sure = merge_pauses(runs, timing, spans, max_skip, ("none",), side)
    look = merge_pauses(runs, timing, spans, max_skip, ("none", "unknown"), side)
    min_d = aud["min_pause_s"]
    silences = [{"start": x["start"], "end": x["end"], "dur": x["dur"]}
                for x in sure if x["dur"] >= min_d]
    end_on_file = max(file_len, audio_end_on_file)
    # Without word timing a short phrase between two pauses looks the same as a
    # cough, so only stretches whose SILENCE alone reaches fail_pause_s, broken by
    # half a second of sound at most, are listed.
    possible = [x for x in look
                if x["dur"] - x["sound_s"] >= pp["fail_pause_s"] and x["joined"] > 0
                and x["sound_s"] <= 0.5
                and x["start"] > 0.05 and x["end"] < end_on_file - 0.15
                and not any(y["start"] <= x["start"] + 0.01 and y["end"] >= x["end"] - 0.01
                            and y["dur"] >= pp["fail_pause_s"] for y in sure)]
    if timing == "word" and words and aud["noise"]["masked_s"] > 0:
        # Where the level cannot hear pauses, word timing can: masked time inside
        # the transcript's span is measured by the talk-gap check instead.
        w0, w1 = min(x["start"] for x in words), max(x["end"] for x in words)
        outside = sum(max(0.0, min(y, w0) - x) + max(0.0, y - max(x, w1))
                      for k, x, y in runs if k == 2)
        aud["noise"]["masked_by_level_s"] = aud["noise"]["masked_s"]
        aud["noise"]["masked_frac"] = round(outside / end_on_file, 3) if end_on_file else 0.0
        aud["noise"]["note"] += "; inside the transcript, word timing measures the talk gaps"
    first_audio = None if aud["first_sound"] is None else round(aud["first_sound"] + head_gap, 3)
    if aud["noise"].get("first_any_sound_s") is not None:
        aud["noise"]["first_any_sound_s"] = round(aud["noise"]["first_any_sound_s"]
                                                  + head_gap, 3)
    if aud["noise"].get("hook_masked_from_s") is not None:
        aud["noise"]["hook_masked_from_s"] = round(aud["noise"]["hook_masked_from_s"]
                                                   + head_gap, 3)
    elif head_gap > prof_hook_max(profile) and aud["first_sound"] is None \
            and not aud["noise"]["hook_measurable"]:
        aud["noise"]["hook_masked_from_s"] = round(head_gap, 3)
    eval_info = dict(info, audio=dict(a, duration_s=max(file_len, audio_end_on_file)))
    bars = letterbox(path, info, profile) if v else None
    checks = evaluate(eval_info, loud, silences, vid["runs"], profile,
                      first_speech=first_word_s(words), first_audio=first_audio,
                      threshold_db=aud["noise"]["base_threshold_db"], bars=bars,
                      noise=aud["noise"], decode=decode, words=words,
                      possible_pauses=possible)
    if v and audio_end_on_file - file_len > 0.5:
        checks.append({"check": "picture_ends_early", "status": "WARN",
                       "measured": f"{audio_end_on_file - file_len:.2f}s",
                       "expected": "picture and sound end together",
                       "note": "the picture stops before the sound; players freeze the "
                               "last frame or show black"})
    rec = {"file": os.path.basename(path), "sha256_head": sha256_head(path),
           "measured_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
           "tool": "content-agent/scripts/video_qa.py", "probe": info,
           "loudness": loud, "silence_threshold_db": aud["noise"]["base_threshold_db"],
           "noise_floor": aud["noise"], "decode": decode,
           "audio_decoded_s": aud["decoded_s"], "video_decoded_s": vid["decoded_s"],
           "audio_head_gap_s": round(head_gap, 3),
           "audio_tail_gap_s": round(max(0.0, file_len - audio_end_on_file), 3),
           "black_min_s": black_min_s(profile, v["fps"]) if v else None,
           "first_audio_s": first_audio, "first_word_s": first_word_s(words),
           "transcript_timing": timing, "possible_pauses": possible,
           "skipped_sounds": [dict(x, at_s=round(x["at_s"] + head_gap, 3))
                              for x in aud["skipped"]],
           "silences_detected": len(silences),
           "longest_silences": sorted(silences, key=lambda s: -s["dur"])[:10],
           "black_runs": vid["runs"], "letterbox": bars,
           "checks": checks, "verdict": verdict_for([c["status"] for c in checks]),
           "profile": profile}
    if frames and v:
        rec["frames"] = grab_frames(path, info["duration_s"], outdir, profile,
                                    [b for b in vid["runs"] if b["kind"] == "near-black"])
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "qa-receipt.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
    (outdir / "qa-receipt.md").write_text(render_markdown(rec), encoding="utf-8")
    return rec


def _qa_video_only(path: str, info: dict, profile: dict, outdir: Path,
                   frames: bool) -> dict:
    """A picture with no audio track: check the picture, say plainly what could not
    be checked."""
    vid = measure_video(path, profile, info)
    v = info["video"]
    claimed = v["duration_s"] or info["duration_s"]
    problems = list(vid["errors"][:1])
    if vid["decoded_s"] is not None and claimed and claimed - vid["decoded_s"] > 0.5:
        problems.append(f"video decoded {vid['decoded_s']:.2f}s of the {claimed:.2f}s "
                        "the file claims (truncated?)")
    decode = {"ok": not problems, "note": "; ".join(problems)}
    bars = letterbox(path, info, profile)
    checks = evaluate(info, {}, [], vid["runs"], profile, bars=bars, decode=decode)
    rec = {"file": os.path.basename(path), "sha256_head": sha256_head(path),
           "measured_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
           "tool": "content-agent/scripts/video_qa.py", "probe": info, "loudness": {},
           "silence_threshold_db": None, "decode": decode,
           "video_decoded_s": vid["decoded_s"], "black_runs": vid["runs"],
           "letterbox": bars, "checks": checks,
           "verdict": verdict_for([c["status"] for c in checks]), "profile": profile}
    if frames:
        rec["frames"] = grab_frames(path, info["duration_s"], outdir, profile,
                                    [b for b in vid["runs"] if b["kind"] == "near-black"])
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "qa-receipt.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
    (outdir / "qa-receipt.md").write_text(render_markdown(rec), encoding="utf-8")
    return rec


def _load_words_arg(srt: str | None, words: str | None) -> list[dict] | None:
    if not srt and not words:
        return None
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import finish  # local helper; finish imports this module lazily-safe
    timed = finish.read_words_file(words) if words else None
    text = finish.read_srt_file(srt) if srt else None
    for name, got in (("--words " + str(words), timed), ("--srt " + str(srt), text)):
        if got is not None and not got:
            raise ValueError(f"{name} holds no words; check the file and its encoding")
    if timed and text:
        # Descript's words on the word-level clock: exact talk gaps and pauses.
        return finish.align_text_to_timing(text, timed)
    return timed or text


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("video")
    ap.add_argument("--profile", help="video-style.json (uses its 'qa' block)")
    ap.add_argument("--srt", help="transcript SRT/VTT on this file's timeline "
                    "(first-word hook; talk gaps between cues)")
    ap.add_argument("--words", help="word-level JSON on this file's timeline (exact "
                    "talk gaps; give both to keep the SRT's words on this clock)")
    ap.add_argument("--out", help="receipt directory (default <video>.qa/)")
    ap.add_argument("--no-frames", action="store_true",
                    help="skip contact sheet and thumbnail candidates")
    args = ap.parse_args(argv)
    out = Path(args.out or (args.video + ".qa"))
    try:
        if not os.path.exists(args.video):
            raise ValueError(f"{args.video} does not exist")
        rec = qa(args.video, load_profile(args.profile), out, frames=not args.no_frames,
                 words=_load_words_arg(args.srt, args.words))
    except Exception as exc:  # report, never pretend
        print(f"QA could not measure {args.video}: {exc}", file=sys.stderr)
        return 2
    print(render_markdown(rec))
    return 1 if rec["verdict"] == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
