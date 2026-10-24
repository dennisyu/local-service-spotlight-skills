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

What it can and cannot see (independently audited 23 Oct 2026):
- With a transcript (--srt or --words) the hook check uses the first WORD.
  Without one it can only see the first SOUND, so a music or tone intro passes;
  the receipt names the check `hook_first_audio` and says so.
- Without a transcript, a click or a thump is not a start: sound counts only
  once a burst holds at least 0.15 s of it (gaps under 0.25 s join a burst).
- Pause counts use a silence threshold set relative to the file's own loudness
  (25 LU under integrated, clamped to -60..-30 dB), so a quiet file and the same
  file normalised count the same pauses. When room noise reaches that threshold
  it would hide every pause, so the threshold is raised to sit 6 dB over the
  measured noise floor; when that would put it within 10 dB of the speech, the
  pause checks say WARN "unmeasurable" instead of passing.
- Black frames are checked on every frame, including near-black screens (90% of
  pixels black) and flashes as short as two frames at the file's own frame
  rate, plus letterbox bars. Cover art in an audio file is not video.
- Re-audited 23 Oct 2026 (round 2): frame-based black minimum, noise floor,
  sustained-sound start, caption sanitising and bad-input messages added.

Usage:
    video_qa.py <video> [--profile video-style.json] [--srt captions.srt |
                --words words.json] [--out <dir>] [--no-frames]

Writes <out>/qa-receipt.json, <out>/qa-receipt.md, a contact sheet and
real-frame thumbnail candidates (never generated art).
Exit codes: 0 = PASS or WARN, 1 = FAIL, 2 = could not measure.
"""
from __future__ import annotations

import argparse
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
               # Noise floor guard: the threshold must clear the room noise's peaks
               # (silencedetect is per-sample, so one noisy sample breaks a pause).
               "noise_floor_percentile": 10, "speech_percentile": 95,
               "noise_floor_margin_db": 6.0, "min_speech_margin_db": 10.0},
    # A record-button click is not a hook: sound counts once a burst (gaps under
    # merge_gap_s joined) holds min_sound_s of it.
    "hook": {"max_first_speech_s": 2.0, "min_sound_s": 0.15, "merge_gap_s": 0.25},
    "tail": {"max_trailing_silence_s": 1.5},
    # min_black_frames at the file's own frame rate; min_black_s caps it for
    # files whose rate cannot be read.
    "black": {"min_black_frames": 2, "min_black_s": 0.08, "pic_th": 0.90, "pix_th": 0.10,
              "scan_height": 180, "letterbox_min_px": 8},
    "frames": {"contact_sheet_tiles": 16, "thumbnail_candidates": 6},
}

# ffmpeg prints tiny times in scientific notation ("silence_start: 2.26757e-05");
# a parser without the exponent reads that as 2.27 s and hides the dead air.
_FLOAT = r"(-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?|-?inf|nan)"
SILENT_LUFS = -69.0  # ebur128 reports about -70 LUFS for digital silence
NOT_MEASURED = object()  # sentinel: the first-sound scan was not run


def deep_merge(base: dict, override: dict) -> dict:
    out = json.loads(json.dumps(base))
    for key, val in (override or {}).items():
        if isinstance(val, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], val)
        else:
            out[key] = val
    return out


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
    return deep_merge(DEFAULT_PROFILE, raw.get("qa", raw))


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, errors="replace")


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


def probe(path: str) -> dict:
    """Container facts, with the picture size as DISPLAYED (phone rotation applied).
    Cover art inside an audio file (attached_pic) is not treated as video."""
    res = run(["ffprobe", "-v", "error", "-show_entries",
               "format=duration,bit_rate,size:stream=codec_type,codec_name,width,height,"
               "r_frame_rate,avg_frame_rate,sample_rate,channels,duration:"
               "stream_disposition=attached_pic:stream_tags=rotate:"
               "stream_side_data=rotation", "-of", "json", path])
    if res.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {res.stderr.strip()[:400]}")
    data = json.loads(res.stdout)
    fmt = data.get("format", {})
    info = {"duration_s": float(fmt.get("duration", 0) or 0),
            "size_bytes": int(fmt.get("size", 0) or 0),
            "bit_rate": int(fmt.get("bit_rate", 0) or 0),
            "video": None, "audio": None}
    for st in data.get("streams", []):
        if (st.get("codec_type") == "video" and info["video"] is None
                and not (st.get("disposition") or {}).get("attached_pic")):
            # avg_frame_rate is the real cadence; r_frame_rate can be a timebase
            # (1000/1, 90000/1) on variable-rate phone and webm files.
            fps = next((r for r in (_rate(st.get("avg_frame_rate")),
                                    _rate(st.get("r_frame_rate"))) if 0 < r <= 240), 0.0)
            w, h, rot = st.get("width"), st.get("height"), _rotation(st)
            if rot in (90, 270):
                w, h = h, w
            info["video"] = {"codec": st.get("codec_name"), "width": w, "height": h,
                             "fps": round(fps, 3), "rotation": rot}
        elif st.get("codec_type") == "audio" and info["audio"] is None:
            dur = st.get("duration")
            info["audio"] = {"codec": st.get("codec_name"),
                             "sample_rate": int(st.get("sample_rate", 0) or 0),
                             "channels": st.get("channels"),
                             "duration_s": float(dur) if dur not in (None, "N/A")
                             else None}
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


def parse_black(text: str) -> list[dict]:
    out = []
    for m in re.finditer(r"black_start:\s*" + _FLOAT + r"\s+black_end:\s*" + _FLOAT
                         + r"\s+black_duration:\s*" + _FLOAT, text):
        out.append({"start": float(m.group(1)), "end": float(m.group(2)),
                    "dur": float(m.group(3))})
    return out


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


def _percentile(values: list[float], pct: float) -> float:
    vals = sorted(values)
    return vals[min(len(vals) - 1, max(0, int(len(vals) * pct / 100.0)))]


def window_peaks(path: str, start: float = 0.0, seconds: float | None = None,
                 sample_rate: int | None = None, window_s: float = 0.05) -> list[float]:
    """Peak level (dBFS, loudest channel) of each ~50 ms window. Digital silence
    reads -120. One ffmpeg pass; about 20 s for a 66-minute file on 2 cores."""
    n = max(64, int(round((sample_rate or 48000) * window_s)))
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-loglevel", "error"]
    if start:
        cmd += ["-ss", f"{start:.3f}"]
    if seconds:
        cmd += ["-t", f"{seconds:.3f}"]
    cmd += ["-i", path, "-vn", "-map", "0:a:0", "-af",
            f"asetnsamples=n={n}:p=0,astats=metadata=1:reset=1:measure_perchannel=none:"
            "measure_overall=Peak_level,ametadata=mode=print:"
            "key=lavfi.astats.Overall.Peak_level:file=-", "-f", "null", "-"]
    res = run(cmd)
    if res.returncode != 0:
        raise RuntimeError(f"level scan failed: {res.stderr.strip()[-400:]}")
    out = []
    for m in re.finditer(r"Peak_level=(\S+)", res.stdout):
        try:
            v = float(m.group(1))
        except ValueError:
            v = -120.0
        out.append(-120.0 if v != v or v < -120.0 else min(v, 0.0))
    return out


def noise_guard(prof: dict, threshold_db: float, peaks: list[float]) -> dict:
    """silencedetect calls a stretch silent only if EVERY sample stays under the
    threshold, so room noise whose peaks reach the threshold hides every pause
    (audit round 2: white noise at -35 dB RMS hid a 2.5 s dead gap). Raise the
    threshold to clear the noise floor; when that would crowd the speech, say the
    pauses cannot be measured rather than passing them."""
    pp = prof["pauses"]
    guard = {"threshold_db": threshold_db, "raised": False, "measurable": True,
             "floor_db": None, "speech_db": None, "note": ""}
    if len(peaks) < 20:
        return guard
    floor = round(_percentile(peaks, pp.get("noise_floor_percentile", 10)), 1)
    speech = round(_percentile(peaks, pp.get("speech_percentile", 95)), 1)
    guard.update(floor_db=floor, speech_db=speech)
    if floor <= -100.0:
        return guard  # digital silence between words: nothing to clear
    need = round(floor + pp.get("noise_floor_margin_db", 6.0), 1)
    if need > threshold_db:
        if pp.get("silence_threshold_db", "auto") == "auto":
            guard.update(threshold_db=need, raised=True,
                         note=f"threshold raised over a {floor} dB noise floor")
        else:
            guard.update(measurable=False,
                         note=f"noise floor peaks at {floor} dB, over the fixed "
                              f"{threshold_db} dB threshold")
            return guard
    if guard["threshold_db"] > speech - pp.get("min_speech_margin_db", 10.0):
        guard.update(measurable=False,
                     note=f"the quiet parts ({floor} dB peaks) sit within "
                          f"{round(speech - floor, 1)} dB of the talk ({speech} dB "
                          "peaks): noise, music or a steady tone hides any pause, so "
                          "pauses cannot be measured from the sound level")
    return guard


def measure_loudness(path: str, start: float = 0.0, seconds: float | None = None) -> dict:
    cmd = ["ffmpeg", "-hide_banner", "-nostats"]
    if start:
        cmd += ["-ss", f"{start:.3f}"]
    if seconds:
        cmd += ["-t", f"{seconds:.3f}"]
    cmd += ["-i", path, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"]
    res = run(cmd)
    if res.returncode != 0:
        raise RuntimeError(f"loudness scan failed: {res.stderr.strip()[-400:]}")
    return parse_ebur128_summary(res.stderr)


def detect_silences(path: str, threshold_db: float, min_s: float, duration: float,
                    start: float = 0.0, seconds: float | None = None) -> list[dict]:
    """Silences on the window's own timeline (0 = start of the window)."""
    cmd = ["ffmpeg", "-hide_banner", "-nostats"]
    if start:
        cmd += ["-ss", f"{start:.3f}"]
    if seconds:
        cmd += ["-t", f"{seconds:.3f}"]
    cmd += ["-i", path, "-vn", "-af", f"silencedetect=noise={threshold_db}dB:d={min_s}",
            "-f", "null", "-"]
    res = run(cmd)
    if res.returncode != 0:
        raise RuntimeError(f"silence scan failed: {res.stderr.strip()[-400:]}")
    return parse_silences(res.stderr, seconds or duration)


def first_sustained_sound(silences: list[dict], length: float,
                          min_sound_s: float = 0.15,
                          merge_gap_s: float = 0.25) -> float | None:
    """Start of the first burst of sound that holds at least min_sound_s of it.
    Sound runs closer than merge_gap_s join one burst, so a word broken by a stop
    consonant stays whole, while a lone click or thump followed by dead air does
    not count as the start. None when no burst qualifies."""
    runs, t = [], 0.0
    for s in sorted(silences, key=lambda x: x["start"]):
        if s["start"] > t:
            runs.append((t, s["start"]))
        t = max(t, s["end"])
    if t < length:
        runs.append((t, length))
    bursts: list[dict] = []
    for a, b in runs:
        if bursts and a - bursts[-1]["end"] < merge_gap_s:
            bursts[-1]["end"] = b
            bursts[-1]["sound"] += b - a
        else:
            bursts.append({"start": a, "end": b, "sound": b - a})
    return next((round(b["start"], 3) for b in bursts if b["sound"] >= min_sound_s), None)


def first_sound_s(path: str, threshold_db: float, start: float = 0.0,
                  seconds: float = 30.0, min_sound_s: float = 0.15,
                  merge_gap_s: float = 0.25) -> float | None:
    """Seconds from `start` to the first SUSTAINED sound above threshold (50 ms
    resolution; clicks ignored, see first_sustained_sound). None when the window
    holds no such sound."""
    sil = detect_silences(path, threshold_db, 0.05, seconds, start, seconds)
    return first_sustained_sound(sil, seconds, min_sound_s, merge_gap_s)


def black_min_s(prof: dict, fps: float | None) -> float:
    """Shortest black run reported: min_black_frames at the file's own rate
    (half a frame of slack), never longer than min_black_s. Two frames is
    0.08 s at 25 fps but 0.067 s at 30 and 0.033 s at 60, so a fixed number of
    seconds misses short flashes on faster video (audit round 2)."""
    bp = prof["black"]
    cap = float(bp["min_black_s"])
    if not fps or fps <= 0:
        return cap
    return round(min(cap, (bp.get("min_black_frames", 2) - 0.5) / fps), 4)


def measure_video(path: str, prof: dict, fps: float | None = None) -> list[dict]:
    bp = prof["black"]
    res = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-an", "-vf",
               f"scale=-2:{bp['scan_height']},blackdetect=d={black_min_s(prof, fps)}:"
               f"pic_th={bp['pic_th']}:pix_th={bp['pix_th']}", "-f", "null", "-"])
    if res.returncode != 0:
        raise RuntimeError(f"video scan failed: {res.stderr.strip()[-400:]}")
    return parse_black(res.stderr)


def active_area(path: str, start: float, seconds: float = 4.0) -> tuple[int, int, int, int]:
    """The picture inside any letterbox bars (Zoom and webinar exports often carry
    a few black rows). (0, 0, 0, 0) when nothing could be detected."""
    res = run(["ffmpeg", "-hide_banner", "-nostats", "-ss", f"{start:.3f}", "-t",
               f"{seconds:.3f}", "-i", path, "-an", "-vf",
               "cropdetect=limit=24:round=2:reset=0", "-f", "null", "-"])
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


def grab_frames(path: str, duration: float, outdir: Path, prof: dict) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    tiles = int(prof["frames"]["contact_sheet_tiles"])
    cols = 4
    rows = max(1, -(-tiles // cols))
    step = max(duration / (tiles + 1), 0.04)
    sheet = outdir / "contact-sheet.jpg"
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", path, "-vf",
         f"fps=1/{step:.3f},scale=480:-2,tile={cols}x{rows}:padding=4",
         "-frames:v", "1", str(sheet)])
    n = int(prof["frames"]["thumbnail_candidates"])
    times = pick_thumbnail_times(path, duration, n, outdir)
    thumbs = []
    for i, (t, score) in enumerate(times):
        dest = outdir / f"thumb-candidate-{i + 1:02d}.jpg"
        # Save exactly the frame that was scored: a real frame, never generated art.
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{t:.3f}",
             "-i", path, "-frames:v", "1", "-vf", "scale=1280:-2", "-q:v", "2",
             str(dest)])
        if dest.exists() and dest.stat().st_size > 0:
            thumbs.append({"file": dest.name, "at_s": round(t, 3), "score": score})
    return {"contact_sheet": sheet.name if sheet.exists() else None,
            "thumbnail_method": "face+sharpness" if times and times[0][1] is not None
            else "even spacing",
            "thumbnail_candidates": thumbs}


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
            run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss",
                 f"{t:.3f}", "-i", path, "-frames:v", "1", "-vf", "scale=640:-2", str(f)])
            img = cv2.imread(str(f))
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


def verdict_for(values: list[str]) -> str:
    if "FAIL" in values:
        return "FAIL"
    if "WARN" in values:
        return "WARN"
    return "PASS"


def evaluate(info: dict, loud: dict, silences: list[dict], black: list[dict],
             prof: dict, first_speech: float | None = None,
             first_audio=NOT_MEASURED, threshold_db: float | None = None,
             bars: dict | None = None, noise: dict | None = None) -> list[dict]:
    """Turn measurements into checks. `first_speech` (first transcribed word) wins
    over `first_audio` (first sound, None = measured silent); without either, the
    leading silence is used.
    `noise` is noise_guard()'s verdict: when pauses are unmeasurable, the pause,
    tail and first-sound checks say WARN instead of passing.
    Statuses: PASS, WARN, FAIL, or N/A for a check that could not apply."""
    dur = info["duration_s"]
    audio_end = (info.get("audio") or {}).get("duration_s") or dur
    checks = []

    def add(name, status, measured, expected, note=""):
        checks.append({"check": name, "status": status, "measured": measured,
                       "expected": expected, "note": note})

    lp = prof["loudness"]
    il = loud.get("integrated_lufs")
    silent = il is None or il != il or il <= SILENT_LUFS
    if silent:
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

    pp = prof["pauses"]
    measurable = (noise or {}).get("measurable", True)
    noise_note = (noise or {}).get("note", "")
    lead = silences[0] if silences and silences[0]["start"] <= 0.05 else None
    trail = (silences[-1] if silences and silences[-1]["end"] >= audio_end - 0.15
             else None)
    hook_max = prof["hook"]["max_first_speech_s"]
    if first_speech is not None:
        name, start_s, note = "hook_first_speech", first_speech, "first transcribed word"
    else:
        name = "hook_first_audio"
        # None = measured and silent; NOT_MEASURED = fall back to the leading silence.
        start_s = (first_audio if first_audio is not NOT_MEASURED
                   else (lead["end"] if lead else 0.0))
        note = ("first sustained SOUND, not first word (clicks ignored): a music or "
                "tone intro passes this check; give --srt or --words to check the "
                "first word")
    if first_speech is None and not measurable:
        add(name, "WARN", "unmeasurable", f"≤ {hook_max}s",
            f"{noise_note}; give --srt or --words to check the first word")
    elif start_s is None:
        add(name, "FAIL", "no sound", f"≤ {hook_max}s", "no audible start found")
    else:
        ok = start_s <= hook_max
        add(name, "PASS" if ok else "FAIL", f"{start_s:.2f}s", f"≤ {hook_max}s",
            note if ok else f"dead air before the hook; trim the head. ({note})")
    tail_s = trail["dur"] if trail and trail is not lead else 0.0
    tail_max = prof["tail"]["max_trailing_silence_s"]
    if not measurable:
        add("trailing_silence", "WARN", "unmeasurable", f"≤ {tail_max}s", noise_note)
        add("pauses_over_fail", "WARN", "unmeasurable",
            f"0 pauses ≥ {pp['fail_pause_s']}s inside the video", noise_note)
        add("pauses_over_warn_rate", "WARN", "unmeasurable",
            f"≤ {pp['max_warn_pauses_per_minute']}/min of {pp['warn_pause_s']}–"
            f"{pp['fail_pause_s']}s pauses", noise_note)
        return checks + _video_checks(info, black, prof, bars)
    add("trailing_silence", "PASS" if tail_s <= tail_max else "WARN",
        f"{tail_s:.2f}s", f"≤ {tail_max}s")

    body = [s for s in silences if s is not lead and s is not trail]
    long_pauses = [s for s in body if s["dur"] >= pp["fail_pause_s"]]
    warn_pauses = [s for s in body if pp["warn_pause_s"] <= s["dur"] < pp["fail_pause_s"]]
    minutes = max(dur / 60.0, 1 / 60.0)
    rate = len(warn_pauses) / minutes
    thr_note = f"silence = under {threshold_db} dB" if threshold_db is not None else ""
    if thr_note and noise_note:
        thr_note += f" ({noise_note})"
    add("pauses_over_fail", "FAIL" if long_pauses else "PASS",
        len(long_pauses), f"0 pauses ≥ {pp['fail_pause_s']}s inside the video",
        "; ".join([f"{s['start']:.1f}s ({s['dur']:.1f}s)"
                   for s in sorted(long_pauses, key=lambda s: -s["dur"])[:5]]
                  + ([thr_note] if thr_note else [])))
    add("pauses_over_warn_rate",
        "PASS" if rate <= pp["max_warn_pauses_per_minute"] else "WARN",
        f"{rate:.2f}/min ({len(warn_pauses)} total)",
        f"≤ {pp['max_warn_pauses_per_minute']}/min of {pp['warn_pause_s']}–"
        f"{pp['fail_pause_s']}s pauses", thr_note)
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
    min_s = black_min_s(prof, info["video"].get("fps"))
    edge = 0.1
    head_black = [b for b in black if b["start"] <= edge]
    tail_black = [b for b in black if b["end"] >= dur - edge - 0.5 and b not in head_black]
    body_black = [b for b in black if b not in head_black and b not in tail_black]
    add("black_frames", "FAIL" if body_black else "PASS", len(body_black),
        f"0 black or near-black runs of {bp.get('min_black_frames', 2)}+ frames "
        f"(≥ {min_s}s) inside the video",
        "; ".join(f"{b['start']:.2f}s ({b['dur']:.2f}s)" for b in body_black[:5]))
    if head_black:
        add("black_open", "FAIL", f"{head_black[0]['dur']:.2f}s", "0s",
            "video opens on black; the hook frame must be the first frame")
    if tail_black:
        add("black_close", "WARN", f"{tail_black[-1]['dur']:.2f}s", "0s",
            "video ends on black; trim it or put the next step on screen")
    if bars:
        add("letterbox", "WARN",
            f"{bars['top_bottom_px_total']}px top+bottom, {bars['side_px_total']}px sides",
            "no bars", "crop them (finish.py --reframe strips bars automatically)")
    return checks


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
    if rec.get("frames"):
        lines += ["", f"Contact sheet: `{rec['frames'].get('contact_sheet')}`. "
                  f"Thumbnail candidates ({rec['frames'].get('thumbnail_method')}), "
                  "real frames, best first: " +
                  ", ".join(f"`{t['file']}` @{t['at_s']}s"
                            for t in rec["frames"].get("thumbnail_candidates", []))]
    lines += ["", "The JSON lists the ten longest silences. Nothing here was played "
              "aloud. A human still judges taste: hook strength, story, and whether "
              "each cut keeps meaning."]
    return "\n".join(lines) + "\n"


def qa(path: str, profile: dict, outdir: Path, frames: bool = True,
       words: list[dict] | None = None) -> dict:
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("ffmpeg and ffprobe must be on PATH")
    info = probe(path)
    if info["audio"] is None:
        raise RuntimeError("no audio stream: nothing to measure for loudness, hook "
                           "or pauses")
    loud = measure_loudness(path)
    base_thr = silence_threshold(profile, loud.get("integrated_lufs"))
    noise = noise_guard(profile, base_thr,
                        window_peaks(path, sample_rate=info["audio"]["sample_rate"]))
    thr = noise["threshold_db"]
    d = min(profile["pauses"]["warn_pause_s"], profile["tail"]["max_trailing_silence_s"])
    silences = detect_silences(path, thr, d, info["duration_s"])
    hp = profile["hook"]
    first_audio = first_sound_s(path, thr, 0.0, min(30.0, info["duration_s"]),
                                hp.get("min_sound_s", 0.15), hp.get("merge_gap_s", 0.25))
    fps = info["video"]["fps"] if info["video"] else None
    black = measure_video(path, profile, fps) if info["video"] else []
    bars = letterbox(path, info, profile) if info["video"] else None
    checks = evaluate(info, loud, silences, black, profile,
                      first_speech=first_word_s(words), first_audio=first_audio,
                      threshold_db=thr, bars=bars, noise=noise)
    rec = {"file": os.path.basename(path), "sha256_head": sha256_head(path),
           "measured_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
           "tool": "content-agent/scripts/video_qa.py", "probe": info,
           "loudness": loud, "silence_threshold_db": thr, "noise_floor": noise,
           "black_min_s": black_min_s(profile, fps) if info["video"] else None,
           "first_audio_s": first_audio, "first_word_s": first_word_s(words),
           "silences_detected": len(silences),
           "longest_silences": sorted(silences, key=lambda s: -s["dur"])[:10],
           "black_runs": black, "letterbox": bars, "checks": checks,
           "verdict": verdict_for([c["status"] for c in checks]), "profile": profile}
    if frames and info["video"]:
        rec["frames"] = grab_frames(path, info["duration_s"], outdir, profile)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "qa-receipt.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
    (outdir / "qa-receipt.md").write_text(render_markdown(rec), encoding="utf-8")
    return rec


def _load_words_arg(srt: str | None, words: str | None) -> list[dict] | None:
    if not srt and not words:
        return None
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import finish  # local helper; finish imports this module lazily-safe
    if words:
        return finish.read_words_file(words)
    return finish.read_srt_file(srt)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("video")
    ap.add_argument("--profile", help="video-style.json (uses its 'qa' block)")
    ap.add_argument("--srt", help="transcript SRT on this file's timeline (first-word hook)")
    ap.add_argument("--words", help="word-level JSON on this file's timeline")
    ap.add_argument("--out", help="receipt directory (default <video>.qa/)")
    ap.add_argument("--no-frames", action="store_true",
                    help="skip contact sheet and thumbnail candidates")
    args = ap.parse_args(argv)
    out = Path(args.out or (args.video + ".qa"))
    try:
        rec = qa(args.video, load_profile(args.profile), out, frames=not args.no_frames,
                 words=_load_words_arg(args.srt, args.words))
    except Exception as exc:  # report, never pretend
        print(f"QA could not measure {args.video}: {exc}", file=sys.stderr)
        return 2
    print(render_markdown(rec))
    return 1 if rec["verdict"] == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
