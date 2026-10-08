#!/usr/bin/env python3
"""Bounded, local-file hero QA. Measurements are triage, never visual approval.

Replaces the September handoff checker’s suppressed cut logging, undeclared
numpy dependency, and success exit on defective clips. No default fleet crawl.
Exit 1 = machine defects; 2 = machine checks clear, visual review still required.
"""
import argparse
import hashlib
import json
import re
import statistics
import subprocess
from pathlib import Path


def run(args):
    return subprocess.run(args, capture_output=True, check=True, timeout=60)


def analyze(path):
    path = Path(path)
    if not path.is_file() or path.stat().st_size > 50 * 1024 * 1024:
        raise ValueError("Require an existing local clip of at most 50 MiB")
    probe = json.loads(run(["ffprobe", "-v", "error", "-show_streams",
                           "-show_format", "-of", "json", str(path)]).stdout)
    streams = probe["streams"]
    video = next(s for s in streams if s["codec_type"] == "video")
    duration = float(probe["format"]["duration"])
    if not 0 < duration <= 60:
        raise ValueError("Analyze a trimmed hero clip, not a full session (max 60s)")
    raw = run(["ffmpeg", "-v", "error", "-i", str(path), "-map", "0:v:0",
               "-vf", "scale=160:90,format=gray", "-an", "-f", "rawvideo", "-"]).stdout
    stride = 160 * 90
    if len(raw) % stride or len(raw) < 3 * stride:
        raise ValueError("Incomplete decode or fewer than three frames")
    frames = [raw[i:i + stride] for i in range(0, len(raw), stride)]
    def mad(a, b):
        return sum(abs(x-y) for x, y in zip(a, b)) / stride
    steps = [mad(a, b) for a, b in zip(frames, frames[1:])]
    mean = statistics.mean(steps)
    seam = mad(frames[-1], frames[0])
    ratio = seam / mean if mean > 1e-9 else None
    # showinfo is INFO level. The old '-v error' silently hid every cut.
    cuts_log = run(["ffmpeg", "-hide_banner", "-loglevel", "info", "-i", str(path),
                    "-vf", "select='gt(scene,0.35)',showinfo", "-an", "-f", "null", "-"]).stderr.decode()
    cuts = [float(t) for t in re.findall(r"pts_time:([0-9.]+)", cuts_log)]
    timestamp_output = run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                            "-show_entries", "frame=best_effort_timestamp_time",
                            "-of", "csv=p=0", str(path)]).stdout.decode()
    times = [float(line.split(',')[0]) for line in timestamp_output.splitlines()
             if line.split(',')[0].strip()]
    intervals = [b-a for a, b in zip(times, times[1:])]
    defects = []
    if any(s["codec_type"] == "audio" for s in streams):
        defects.append("AUDIO_TRACK_IN_BACKGROUND_EXPORT")
    if mean <= 1e-9:
        defects.append("FROZEN_VIDEO_REQUIRES_SOURCE_REVIEW")
    if ratio is not None and ratio >= 5:
        defects.append("LOOP_SEAM_REVIEW_REQUIRED")
    if cuts:
        defects.append("HARD_CUT_REVIEW_REQUIRED")
    if not intervals or min(intervals) <= 0 or max(intervals)-min(intervals) > 0.001:
        defects.append("FRAME_PACING_REVIEW_REQUIRED")
    result = {
        "schema": 1, "file": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "bytes": path.stat().st_size, "width": video["width"], "height": video["height"],
        "duration_seconds": duration, "decoded_frames": len(frames),
        "pixel_format": video.get("pix_fmt"), "audio_tracks": sum(s["codec_type"] == "audio" for s in streams),
        "mean_frame_mad": mean, "last_first_mad": seam, "seam_ratio": ratio,
        "scene_cut_times_seconds": cuts,
        "min_frame_interval": min(intervals) if intervals else None,
        "max_frame_interval": max(intervals) if intervals else None,
        "machine_defects": defects,
        "verdict": "REJECT_OR_REVIEW" if defects else "VISUAL_REVIEW_REQUIRED",
        "limitations": "Pixel differences do not prove camera stability, real footage, crop quality, rights, face integrity, or browser playback. No automatic release pass."
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", help="Exact local exported hero clip; URLs and default fleet sweeps are unsupported")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = analyze(args.file)
        code = 1 if result["machine_defects"] else 2
    except (OSError, ValueError, KeyError, StopIteration, subprocess.SubprocessError) as error:
        result = {"verdict": "ERROR", "error": str(error)}
        code = 1
    output = json.dumps(result, indent=2, allow_nan=False)
    if args.output:
        try:
            args.output.write_text(output + "\n")
        except OSError as error:
            print(json.dumps({"verdict": "ERROR", "error": str(error)}))
            return 1
    print(output)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
