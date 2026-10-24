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

Usage:
    video_qa.py <video> [--profile video-style.json] [--out <dir>] [--no-frames]

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
    "pauses": {"silence_threshold_db": -38.0, "warn_pause_s": 0.6,
               "fail_pause_s": 2.0, "max_warn_pauses_per_minute": 3.0},
    "hook": {"max_first_speech_s": 2.0},
    "tail": {"max_trailing_silence_s": 1.5},
    "black": {"min_black_s": 0.5},
    "frames": {"contact_sheet_tiles": 16, "thumbnail_candidates": 6},
}

_FLOAT = r"(-?\d+(?:\.\d+)?|-?inf|nan)"


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
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    return deep_merge(DEFAULT_PROFILE, raw.get("qa", raw))


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, errors="replace")


def probe(path: str) -> dict:
    res = run(["ffprobe", "-v", "error", "-show_entries",
               "format=duration,bit_rate,size:stream=codec_type,codec_name,width,height,"
               "r_frame_rate,sample_rate,channels", "-of", "json", path])
    if res.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {res.stderr.strip()[:400]}")
    data = json.loads(res.stdout)
    fmt = data.get("format", {})
    info = {"duration_s": float(fmt.get("duration", 0) or 0),
            "size_bytes": int(fmt.get("size", 0) or 0),
            "bit_rate": int(fmt.get("bit_rate", 0) or 0),
            "video": None, "audio": None}
    for st in data.get("streams", []):
        if st.get("codec_type") == "video" and info["video"] is None:
            num, _, den = str(st.get("r_frame_rate", "0/1")).partition("/")
            fps = float(num) / float(den or 1) if float(den or 1) else 0.0
            info["video"] = {"codec": st.get("codec_name"), "width": st.get("width"),
                             "height": st.get("height"), "fps": round(fps, 3)}
        elif st.get("codec_type") == "audio" and info["audio"] is None:
            info["audio"] = {"codec": st.get("codec_name"),
                             "sample_rate": int(st.get("sample_rate", 0) or 0),
                             "channels": st.get("channels")}
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


def measure_audio(path: str, prof: dict) -> dict:
    thr = prof["pauses"]["silence_threshold_db"]
    d = min(prof["pauses"]["warn_pause_s"], prof["tail"]["max_trailing_silence_s"])
    res = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vn", "-af",
               f"ebur128=peak=true,silencedetect=noise={thr}dB:d={d}",
               "-f", "null", "-"])
    if res.returncode != 0:
        raise RuntimeError(f"audio scan failed: {res.stderr.strip()[-400:]}")
    return {"stderr": res.stderr}


def measure_video(path: str, prof: dict) -> list[dict]:
    d = prof["black"]["min_black_s"]
    res = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-an", "-vf",
               f"fps=5,scale=320:-2,blackdetect=d={d}:pix_th=0.10",
               "-f", "null", "-"])
    if res.returncode != 0:
        raise RuntimeError(f"video scan failed: {res.stderr.strip()[-400:]}")
    return parse_black(res.stderr)


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
        # thumbnail= picks the most representative of the next 50 frames, which
        # skips blinks and motion blur. A real frame, never generated art.
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{t:.2f}",
             "-i", path, "-vf", "thumbnail=50,scale=1280:-2", "-frames:v", "1",
             str(dest)])
        if dest.exists() and dest.stat().st_size > 0:
            thumbs.append({"file": dest.name, "at_s": round(t, 2), "score": score})
    return {"contact_sheet": sheet.name if sheet.exists() else None,
            "thumbnail_method": "face+sharpness" if times and times[0][1] is not None
            else "even spacing",
            "thumbnail_candidates": thumbs}


def pick_thumbnail_times(path: str, duration: float, n: int, outdir: Path,
                         samples: int = 48) -> list[tuple[float, float | None]]:
    """Rank sampled frames by face size and sharpness when OpenCV is installed.

    A face filling the frame makes a thumbnail; a screen share does not. Without
    OpenCV this falls back to even spacing and says so in the receipt.
    """
    even = [(duration * (i + 1) / (n + 1), None) for i in range(n)]
    try:
        import cv2  # optional; OpenCV 4.x (5.x dropped the Haar CascadeClassifier)
        cascade = cv2.CascadeClassifier(cv2.data.haarcascades +
                                        "haarcascade_frontalface_default.xml")
        if cascade.empty():
            return even
    except (ImportError, AttributeError):
        return even
    probe_dir = outdir / ".thumb-probe"
    probe_dir.mkdir(parents=True, exist_ok=True)
    scored = []
    for i in range(samples):
        t = duration * (i + 0.5) / samples
        f = probe_dir / f"p{i:03d}.jpg"
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{t:.2f}",
             "-i", path, "-frames:v", "1", "-vf", "scale=640:-2", str(f)])
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
        # replay: camera frames 0.03 Canny edge density, screen shares 0.08–0.16).
        # A face inside a screenshot is not the speaker; keep it, rank it low.
        busy = float((cv2.Canny(gray, 100, 200) > 0).mean())
        screen = 0.25 if busy > 0.06 else 1.0
        sharp = min(cv2.Laplacian(gray, cv2.CV_64F).var(), 600) / 600
        scored.append((t, round(big * big * 100 / crowd * screen + sharp, 3)))
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
             prof: dict) -> list[dict]:
    dur = info["duration_s"]
    checks = []

    def add(name, status, measured, expected, note=""):
        checks.append({"check": name, "status": status, "measured": measured,
                       "expected": expected, "note": note})

    lp = prof["loudness"]
    il = loud.get("integrated_lufs")
    if il is None or il != il or il == float("-inf"):
        add("integrated_loudness", "FAIL", None, f"{lp['target_lufs']} LUFS",
            "could not measure; silent or missing audio")
    else:
        off = abs(il - lp["target_lufs"])
        status = ("PASS" if off <= lp["pass_tolerance_lu"]
                  else "WARN" if off <= lp["warn_tolerance_lu"] else "FAIL")
        add("integrated_loudness", status, f"{il:.1f} LUFS",
            f"{lp['target_lufs']} ±{lp['pass_tolerance_lu']} LU",
            "" if status == "PASS" else
            f"{il - lp['target_lufs']:+.1f} LU from target; run finish.py loudness")
    tp = loud.get("true_peak_dbtp")
    if tp is not None:
        status = "PASS" if tp <= lp["true_peak_max_dbtp"] else (
            "FAIL" if tp > 0 else "WARN")
        add("true_peak", status, f"{tp:.1f} dBTP", f"≤ {lp['true_peak_max_dbtp']} dBTP",
            "clipping" if tp > 0 else "")

    pp = prof["pauses"]
    lead = silences[0] if silences and silences[0]["start"] <= 0.05 else None
    trail = silences[-1] if silences and silences[-1]["end"] >= dur - 0.05 else None
    first_speech = lead["end"] if lead else 0.0
    hook_max = prof["hook"]["max_first_speech_s"]
    add("hook_first_speech", "PASS" if first_speech <= hook_max else "FAIL",
        f"{first_speech:.2f}s", f"≤ {hook_max}s",
        "" if first_speech <= hook_max else "dead air before the hook; trim the head")
    tail_s = trail["dur"] if trail and trail is not lead else 0.0
    tail_max = prof["tail"]["max_trailing_silence_s"]
    add("trailing_silence", "PASS" if tail_s <= tail_max else "WARN",
        f"{tail_s:.2f}s", f"≤ {tail_max}s")

    body = [s for s in silences if s is not lead and s is not trail]
    long_pauses = [s for s in body if s["dur"] >= pp["fail_pause_s"]]
    warn_pauses = [s for s in body if pp["warn_pause_s"] <= s["dur"] < pp["fail_pause_s"]]
    minutes = max(dur / 60.0, 1 / 60.0)
    rate = len(warn_pauses) / minutes
    add("pauses_over_fail", "FAIL" if long_pauses else "PASS",
        len(long_pauses), f"0 pauses ≥ {pp['fail_pause_s']}s",
        "; ".join(f"{s['start']:.1f}s ({s['dur']:.1f}s)"
                  for s in sorted(long_pauses, key=lambda s: -s["dur"])[:5]))
    add("pauses_over_warn_rate",
        "PASS" if rate <= pp["max_warn_pauses_per_minute"] else "WARN",
        f"{rate:.2f}/min ({len(warn_pauses)} total)",
        f"≤ {pp['max_warn_pauses_per_minute']}/min of {pp['warn_pause_s']}–"
        f"{pp['fail_pause_s']}s pauses")

    bp = prof["black"]
    edge = 0.6  # blackdetect runs at 5 fps on a scaled copy; allow one sample of slop
    head_black = [b for b in black if b["start"] <= edge]
    tail_black = [b for b in black if b["end"] >= dur - edge and b not in head_black]
    body_black = [b for b in black if b not in head_black and b not in tail_black]
    add("black_frames", "FAIL" if body_black else "PASS", len(body_black),
        f"0 black runs ≥ {bp['min_black_s']}s inside the video",
        "; ".join(f"{b['start']:.1f}s ({b['dur']:.1f}s)" for b in body_black[:5]))
    if head_black:
        add("black_open", "FAIL", f"{head_black[0]['dur']:.2f}s", "0s",
            "video opens on black; the hook frame must be the first frame")
    if tail_black:
        add("black_close", "WARN", f"{tail_black[-1]['dur']:.2f}s", "0s",
            "video ends on black; trim it or put the next step on screen")
    return checks


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
             f"- Measured: {rec['measured_at']} with {rec['tool']}", "",
             "| Check | Status | Measured | Expected | Note |",
             "|---|---|---|---|---|"]
    for c in rec["checks"]:
        lines.append(f"| {c['check']} | {c['status']} | {c['measured']} | "
                     f"{c['expected']} | {c['note']} |")
    if rec.get("frames"):
        lines += ["", f"Contact sheet: `{rec['frames'].get('contact_sheet')}`. "
                  "Thumbnail candidates are real frames: " +
                  ", ".join(f"`{t['file']}` @{t['at_s']}s"
                            for t in rec["frames"].get("thumbnail_candidates", []))]
    lines += ["", "Nothing here was played aloud. A human still judges taste: "
              "hook strength, story, and whether each cut keeps meaning."]
    return "\n".join(lines) + "\n"


def qa(path: str, profile: dict, outdir: Path, frames: bool = True) -> dict:
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("ffmpeg and ffprobe must be on PATH")
    info = probe(path)
    if info["audio"] is None:
        raise RuntimeError("no audio stream")
    aud = measure_audio(path, profile)
    loud = parse_ebur128_summary(aud["stderr"])
    silences = parse_silences(aud["stderr"], info["duration_s"])
    black = measure_video(path, profile) if info["video"] else []
    checks = evaluate(info, loud, silences, black, profile)
    rec = {"file": os.path.basename(path), "sha256_head": sha256_head(path),
           "measured_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
           "tool": "content-agent/scripts/video_qa.py", "probe": info,
           "loudness": loud, "silences_detected": len(silences),
           "longest_silences": sorted(silences, key=lambda s: -s["dur"])[:10],
           "black_runs": black, "checks": checks,
           "verdict": verdict_for([c["status"] for c in checks]), "profile": profile}
    if frames and info["video"]:
        rec["frames"] = grab_frames(path, info["duration_s"], outdir, profile)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "qa-receipt.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
    (outdir / "qa-receipt.md").write_text(render_markdown(rec), encoding="utf-8")
    return rec


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("video")
    ap.add_argument("--profile", help="video-style.json (uses its 'qa' block)")
    ap.add_argument("--out", help="receipt directory (default <video>.qa/)")
    ap.add_argument("--no-frames", action="store_true",
                    help="skip contact sheet and thumbnail candidates")
    args = ap.parse_args(argv)
    out = Path(args.out or (args.video + ".qa"))
    try:
        rec = qa(args.video, load_profile(args.profile), out, frames=not args.no_frames)
    except Exception as exc:  # report, never pretend
        print(f"QA could not measure {args.video}: {exc}", file=sys.stderr)
        return 2
    print(render_markdown(rec))
    return 1 if rec["verdict"] == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
