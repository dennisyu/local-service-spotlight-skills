#!/usr/bin/env python3
"""Finish a lightly edited video: trim dead air at the head, hit the loudness
target, and add captions in the house style. One encode, then a QA receipt.

WHY THIS EXISTS (23 Oct 2026)
Descript (Studio Sound + Underlord) does the edit well. What it did not give us
was a measured finish: our content-agent skill said "no burned-in captions" and
nothing measured loudness, so shorts went out quiet and silent-scroll viewers got
no words on screen. This is the deterministic last mile. It runs on any machine
with ffmpeg, costs no Descript credits, and reads its look from one style file
(video-style.json) so every agent ships the same captions.

Usage:
    finish.py IN -o OUT [--profile video-style.json]
              [--trim-head] [--loudness]
              [--words words.json] [--srt captions.srt] [--burn | --sidecar]
              [--clip START-END] [--reframe 9:16 --focus-x 0.5]
              [--keywords "Dollar a Day,GCT"]

    --words takes word-level JSON (transcribe_words.py, ElevenLabs Scribe, or a
    faster-whisper dump). --srt takes a Descript export_transcript srt and spreads
    each cue's words evenly across the cue. Give BOTH and the captions use
    Descript's corrected words on the ASR's word clock (best of each). --clip
    edges snap to word boundaries so no cut lands inside a word.

Video is copied untouched when only --loudness is asked for; any trim or burn
re-encodes once with libx264 (preset veryfast unless the profile says otherwise).
Nothing is ever played aloud.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import video_qa  # noqa: E402

DEFAULT_STYLE = {
    "captions": {
        "font": "Inter", "bold": True, "uppercase": True,
        "max_words": 3, "max_chars": 18, "break_gap_s": 0.3, "min_cue_s": 0.35,
        "font_size_ratio": 0.055, "outline_ratio": 0.004, "margin_v_ratio": 0.22,
        "primary_bgr": "FFFFFF", "outline_bgr": "000000", "highlight_bgr": "00FFFF",
        "highlight_numbers": True, "keywords": [],
    },
    "finish": {"head_pad_s": 0.08, "fade_s": 0.03, "x264_preset": "veryfast",
               "x264_crf": 18, "audio_bitrate": "192k", "lra_target": 11.0,
               "true_peak_headroom_db": 0.5},
}

PUNCT_BREAK = re.compile(r"[.,!?;:\-—–]\"?$")
CROSSTALK = {"right", "yeah", "yes", "yep", "mhm", "mm", "hmm", "uh", "um",
             "uhhuh", "okay", "ok", "wow", "nice", "sure"}
NUMBERISH = re.compile(r"[\d$%]")


def load_style(path: str | None) -> dict:
    style = json.loads(json.dumps(DEFAULT_STYLE))
    qa_prof = video_qa.load_profile(None)
    if path:
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
        style = video_qa.deep_merge(style, {k: raw[k] for k in ("captions", "finish")
                                            if k in raw})
        qa_prof = video_qa.load_profile(path)
    style["qa"] = qa_prof
    return style


# ---------------------------------------------------------------- words in

def normalize_words(data) -> list[dict]:
    """Accept Scribe, faster-whisper or plain [{word,start,end}] JSON."""
    if isinstance(data, dict):
        if "words" in data:
            data = data["words"]
        elif "segments" in data:
            data = [w for seg in data["segments"] for w in seg.get("words", [])]
    words = []
    for w in data:
        if w.get("type") not in (None, "word"):
            continue  # Scribe spacing and audio_event entries
        text = str(w.get("word", w.get("text", ""))).strip()
        if not text:
            continue
        words.append({"word": text, "start": float(w["start"]), "end": float(w["end"])})
    words.sort(key=lambda w: w["start"])
    return words


def _ts(s: str) -> float:
    h, m, rest = s.strip().replace(".", ",").split(":")
    sec, ms = rest.split(",")
    return int(h) * 3600 + int(m) * 60 + int(sec) + int(ms) / 1000.0


def words_from_srt(text: str) -> list[dict]:
    words = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = [l for l in block.strip().splitlines() if l.strip()]
        timing = next((l for l in lines if "-->" in l), None)
        if not timing:
            continue
        a, b = (p.strip().split(" ")[0] for p in timing.split("-->"))
        start, end = _ts(a), _ts(b)
        body = " ".join(lines[lines.index(timing) + 1:])
        body = re.sub(r"<[^>]+>|\{[^}]+\}", "", body)
        body = re.sub(r"^\s*\[?[A-Z][\w .'-]{0,30}\]?:\s+", "", body)  # speaker label
        toks = body.split()
        if not toks or end <= start:
            continue
        step = (end - start) / len(toks)
        for i, tok in enumerate(toks):
            words.append({"word": tok, "start": round(start + i * step, 3),
                          "end": round(start + (i + 1) * step, 3)})
    return words


def _norm(tok: str) -> str:
    return re.sub(r"[^\w]", "", tok.lower())


def align_text_to_timing(text_words: list[dict], timed: list[dict]) -> list[dict]:
    """Keep the better TEXT (Descript's corrected transcript) and the better
    TIMING (word-level ASR). Matched and same-length replaced runs take the
    timed word's clock; other runs are spread across the span they replace.
    Returns text_words re-timed, limited to the window the timed words cover."""
    import difflib
    if not timed:
        return text_words
    lo, hi = timed[0]["start"] - 1.0, timed[-1]["end"] + 1.0
    text = [w for w in text_words if lo <= w["start"] <= hi]
    sm = difflib.SequenceMatcher(a=[_norm(w["word"]) for w in text],
                                 b=[_norm(w["word"]) for w in timed], autojunk=False)
    out: list[dict] = []
    for op, a0, a1, b0, b1 in sm.get_opcodes():
        span = text[a0:a1]
        if not span:
            continue
        if op in ("equal", "replace") and (a1 - a0) == (b1 - b0):
            out += [{"word": t["word"], "start": s["start"], "end": s["end"]}
                    for t, s in zip(span, timed[b0:b1])]
            continue
        if b1 > b0:
            s0, s1 = timed[b0]["start"], timed[b1 - 1]["end"]
        else:
            # Words the ASR never heard. A lone interjection ("Right", "Yeah") is
            # almost always another person's crosstalk: leave it out of the
            # speaker's captions. Anything else is squeezed, in order, into the
            # gap between its neighbours so word order can never scramble.
            span = [t for t in span if _norm(t["word"]) not in CROSSTALK]
            if not span:
                continue
            s0 = out[-1]["end"] if out else timed[0]["start"]
            s1 = timed[b0]["start"] if b0 < len(timed) else s0 + 0.2 * len(span)
            s1 = max(s1, s0)
        step = (s1 - s0) / len(span)
        out += [{"word": t["word"], "start": round(s0 + i * step, 3),
                 "end": round(s0 + (i + 1) * step, 3)} for i, t in enumerate(span)]
    return out


# ---------------------------------------------------------------- chunking

def chunk_words(words: list[dict], cap: dict) -> list[dict]:
    """Group words into 1–max_words cues; break on punctuation and pauses."""
    cues, cur = [], []

    def flush():
        if cur:
            cues.append({"words": list(cur), "start": cur[0]["start"],
                         "end": cur[-1]["end"]})
            cur.clear()

    for i, w in enumerate(words):
        if cur:
            gap = w["start"] - cur[-1]["end"]
            chars = sum(len(x["word"]) + 1 for x in cur) + len(w["word"])
            if (len(cur) >= cap["max_words"] or gap >= cap["break_gap_s"]
                    or chars > cap["max_chars"]):
                flush()
        cur.append(w)
        if PUNCT_BREAK.search(w["word"]):
            flush()
    flush()
    # Never flash a cue shorter than min_cue_s: stretch into the gap after it,
    # else merge into the next cue when there is room.
    merged: list[dict] = []
    for idx, cue in enumerate(cues):
        nxt = cues[idx + 1] if idx + 1 < len(cues) else None
        if cue["end"] - cue["start"] < cap["min_cue_s"]:
            limit = nxt["start"] if nxt else cue["start"] + cap["min_cue_s"]
            cue["end"] = min(cue["start"] + cap["min_cue_s"], max(limit, cue["end"]))
        if (merged and cue["end"] - cue["start"] < cap["min_cue_s"]
                and not re.search(r"[.!?]\"?$", merged[-1]["words"][-1]["word"])
                and len(merged[-1]["words"]) + len(cue["words"]) <= cap["max_words"]):
            merged[-1]["words"] += cue["words"]
            merged[-1]["end"] = cue["end"]
            continue
        merged.append(cue)
    for a, b in zip(merged, merged[1:]):
        a["end"] = min(a["end"], b["start"])  # cues never overlap
    return merged


def shift_cues(cues: list[dict], offset: float) -> list[dict]:
    out = []
    for c in cues:
        s, e = c["start"] - offset, c["end"] - offset
        if e <= 0:
            continue
        out.append({**c, "start": max(0.0, s), "end": e})
    return out


def _clean(word: str) -> str:
    return re.sub(r"[^\w$%'-]", "", word).lower()


def cue_text(cue: dict, cap: dict, ass: bool) -> str:
    keys = {_clean(k) for kw in cap.get("keywords", []) for k in kw.split()}
    parts = []
    for w in cue["words"]:
        txt = w["word"].upper() if cap["uppercase"] else w["word"]
        hot = _clean(w["word"]) in keys or (cap["highlight_numbers"]
                                           and NUMBERISH.search(w["word"]))
        if ass and hot:
            txt = "{\\c&H%s&}%s{\\r}" % (cap["highlight_bgr"], txt)
        parts.append(txt)
    return " ".join(parts)


def _ass_time(t: float) -> str:
    cs = int(round(t * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _srt_time(t: float) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build_ass(cues: list[dict], cap: dict, width: int, height: int) -> str:
    size = max(18, round(height * cap["font_size_ratio"]))
    outline = max(1, round(height * cap["outline_ratio"]))
    margin_v = round(height * cap["margin_v_ratio"])
    head = (
        "[Script Info]\nScriptType: v4.00+\nWrapStyle: 0\nScaledBorderAndShadow: yes\n"
        f"PlayResX: {width}\nPlayResY: {height}\n\n[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Cap,{cap['font']},{size},&H00{cap['primary_bgr']},&H00{cap['primary_bgr']},"
        f"&H00{cap['outline_bgr']},&H00000000,{-1 if cap['bold'] else 0},0,0,0,100,100,0,0,"
        f"1,{outline},0,2,{round(width * 0.06)},{round(width * 0.06)},{margin_v},1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, "
        "Effect, Text\n")
    rows = [f"Dialogue: 0,{_ass_time(c['start'])},{_ass_time(c['end'])},Cap,,0,0,0,,"
            f"{cue_text(c, cap, ass=True)}" for c in cues]
    return head + "\n".join(rows) + "\n"


def build_srt(cues: list[dict], cap: dict) -> str:
    return "\n".join(f"{i}\n{_srt_time(c['start'])} --> {_srt_time(c['end'])}\n"
                     f"{cue_text(c, cap, ass=False)}\n"
                     for i, c in enumerate(cues, 1))


def assert_font(family: str) -> str:
    """Fonts fail silently in libass; refuse to render in a fallback face."""
    if not shutil.which("fc-match"):
        return "unverified (fc-match missing)"
    res = subprocess.run(["fc-match", "-f", "%{family}", family],
                         capture_output=True, text=True)
    got = res.stdout.strip()
    if family.lower() not in got.lower():
        raise RuntimeError(f"caption font '{family}' not installed; fc-match gave "
                           f"'{got}'. Install it or change captions.font.")
    return got


# ---------------------------------------------------------------- media ops

def first_speech_s(path: str, threshold_db: float, offset: float = 0.0) -> float:
    """Seconds (on the source timeline) where speech first starts after offset."""
    res = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-ss", f"{offset:.3f}",
                          "-t", "30", "-i", path,
                          "-vn", "-af", f"silencedetect=noise={threshold_db}dB:d=0.25",
                          "-f", "null", "-"], capture_output=True, text=True,
                         errors="replace")
    sil = video_qa.parse_silences(res.stderr, 30.0)
    if sil and sil[0]["start"] <= 0.05:
        return offset + sil[0]["end"]
    return offset


def measure_loudnorm(path: str, start: float, style: dict,
                     duration: float | None = None) -> dict:
    lp = style["qa"]["loudness"]
    flt = (f"loudnorm=I={lp['target_lufs']}:TP={lp['true_peak_max_dbtp']}:"
           f"LRA={style['finish']['lra_target']}:print_format=json")
    cmd = ["ffmpeg", "-hide_banner", "-nostats"]
    if start > 0:
        cmd += ["-ss", f"{start:.3f}"]
    if duration:
        cmd += ["-t", f"{duration:.3f}"]
    cmd += ["-i", path, "-vn", "-af", flt, "-f", "null", "-"]
    res = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    blob = res.stderr[res.stderr.rfind("{"):res.stderr.rfind("}") + 1]
    if res.returncode != 0 or not blob:
        raise RuntimeError(f"loudnorm measure failed: {res.stderr[-400:]}")
    return json.loads(blob)


def snap_to_words(words: list[dict], start: float, end: float,
                  pad: float) -> tuple[float, float]:
    """Never cut inside a word: move clip edges to word boundaries, then pad."""
    inside = [w for w in words if w["end"] > start and w["start"] < end]
    if not inside:
        return start, end
    first = next((w for w in inside if w["start"] >= start - 0.02), inside[0])
    last = next((w for w in reversed(inside) if w["end"] <= end + 0.02), inside[-1])
    prev_end = max((w["end"] for w in words if w["end"] <= first["start"]), default=0.0)
    next_start = min((w["start"] for w in words if w["start"] >= last["end"]),
                     default=last["end"] + pad)
    s = max(prev_end, first["start"] - pad, 0.0)
    e = min(next_start, last["end"] + pad)
    return s, e


def active_area(path: str, start: float, seconds: float = 4.0) -> tuple[int, int, int, int]:
    """Find the picture inside any letterbox bars (Zoom and webinar exports often
    carry a few black rows), so a reframe never keeps a black strip."""
    res = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-ss", f"{start:.3f}",
                          "-t", f"{seconds:.3f}", "-i", path, "-an", "-vf",
                          "cropdetect=limit=24:round=2:reset=0", "-f", "null", "-"],
                         capture_output=True, text=True, errors="replace")
    found = re.findall(r"crop=(\d+):(\d+):(\d+):(\d+)", res.stderr)
    if not found:
        return (0, 0, 0, 0)
    w, h, x, y = (int(v) for v in max(set(found), key=found.count))
    return (w, h, x, y)


def reframe_filter(width: int, height: int, aspect: str, focus_x: float,
                   ox: int = 0, oy: int = 0):
    """Crop to aspect (e.g. 9:16) around focus_x (0 = left edge, 1 = right) of
    the active picture that starts at (ox, oy)."""
    aw, ah = (float(x) for x in aspect.split(":"))
    target = aw / ah
    if width / height > target:  # too wide: crop the sides
        cw, ch = int(round(height * target / 2) * 2), height
    else:  # too tall: crop top and bottom
        cw, ch = width, int(round(width / target / 2) * 2)
    x = ox + int(round(max(0, min(width - cw, focus_x * width - cw / 2))))
    y = oy + int((height - ch) / 2)
    out_h = 1920 if target < 1 else 1080
    out_w = int(round(out_h * target / 2) * 2)
    return f"crop={cw}:{ch}:{x}:{y},scale={out_w}:{out_h}:flags=lanczos", out_w, out_h


def finish(src: str, dst: str, style: dict, trim_head: bool, loudness: bool,
           words: list[dict] | None, burn: bool, keywords: list[str],
           reframe: str | None = None, focus_x: float = 0.5,
           clip: tuple[float, float] | None = None) -> dict:
    info = video_qa.probe(src)
    fin, cap = style["finish"], dict(style["captions"])
    cap["keywords"] = list(cap.get("keywords", [])) + keywords
    clip_start, clip_end = clip if clip else (0.0, info["duration_s"])
    snapped = None
    if clip and words:
        clip_start, clip_end = snap_to_words(words, clip_start, clip_end,
                                             fin["head_pad_s"])
        snapped = [round(clip_start, 3), round(clip_end, 3)]
    start = clip_start
    if trim_head:
        fs = first_speech_s(src, style["qa"]["pauses"]["silence_threshold_db"],
                            offset=clip_start)
        start = max(clip_start, fs - fin["head_pad_s"])
    duration = clip_end - start
    report = {"source": os.path.basename(src), "output": os.path.basename(dst),
              "trimmed_head_s": round(start, 3), "steps": []}
    if snapped:
        report["clip_snapped_to_words"] = snapped

    afilters = []
    if start > 0 or clip:
        afilters.append(f"afade=t=in:st=0:d={fin['fade_s']}")
    if clip:
        afilters.append(f"afade=t=out:st={max(0.0, duration - fin['fade_s']):.3f}"
                        f":d={fin['fade_s']}")
    if loudness:
        m = measure_loudnorm(src, start, style, duration if clip else None)
        lp = style["qa"]["loudness"]
        afilters.append(
            f"loudnorm=I={lp['target_lufs']}:"
            # AAC encoding adds inter-sample overs; aim under the QA ceiling.
            f"TP={lp['true_peak_max_dbtp'] - fin.get('true_peak_headroom_db', 0.5)}:"
            f"LRA={fin['lra_target']}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
            f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:"
            f"offset={m['target_offset']}:linear=true")
        afilters.append(f"aresample={info['audio']['sample_rate'] or 48000}")
        report["steps"].append({"loudness_in_lufs": float(m["input_i"]),
                                "true_peak_in_dbtp": float(m["input_tp"])})

    work = Path(tempfile.mkdtemp(prefix="finish-"))
    vfilters, sidecar = [], None
    out_w, out_h = info["video"]["width"], info["video"]["height"]
    if reframe:
        aw, ah, ax, ay = active_area(src, start, min(duration, 4.0))
        if aw >= out_w * 0.5 and ah >= out_h * 0.5:  # ignore a near-black frame
            out_w, out_h, offset = aw, ah, (ax, ay)
            report["active_area"] = [aw, ah, ax, ay]
        else:
            offset = (0, 0)
        crop, out_w, out_h = reframe_filter(out_w, out_h, reframe, focus_x, *offset)
        vfilters.append(crop)
        report["reframe"] = {"aspect": reframe, "focus_x": focus_x, "size": [out_w, out_h]}
    if words:
        inside = [w for w in words if w["start"] >= start - 0.05
                  and w["end"] <= start + duration + 0.05]
        cues = shift_cues(chunk_words(inside, cap), start)
        sidecar = Path(dst).with_suffix(".captions.srt")
        sidecar.write_text(build_srt(cues, cap), encoding="utf-8")
        report["steps"].append({"caption_cues": len(cues), "sidecar_srt": sidecar.name})
        if burn:
            report["caption_font"] = assert_font(cap["font"])
            (work / "cap.ass").write_text(
                build_ass(cues, cap, out_w, out_h),
                encoding="utf-8")
            vfilters.append("ass=cap.ass")  # LAST in the chain, after any overlay
    reencode = bool(vfilters) or start > 0 or bool(clip)
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
    if start > 0:
        cmd += ["-ss", f"{start:.3f}"]
    if clip:
        cmd += ["-t", f"{duration:.3f}"]
    cmd += ["-i", os.path.abspath(src), "-map", "0:v:0?", "-map", "0:a:0"]
    if vfilters:
        cmd += ["-vf", ",".join(vfilters)]
    cmd += (["-c:v", "libx264", "-preset", fin["x264_preset"], "-crf",
             str(fin["x264_crf"]), "-pix_fmt", "yuv420p"] if reencode else ["-c:v", "copy"])
    if afilters:
        cmd += ["-af", ",".join(afilters), "-c:a", "aac", "-b:a", fin["audio_bitrate"]]
    else:
        cmd += ["-c:a", "copy"]
    cmd += ["-movflags", "+faststart", os.path.abspath(dst)]
    res = subprocess.run(cmd, cwd=work, capture_output=True, text=True, errors="replace")
    shutil.rmtree(work, ignore_errors=True)
    if res.returncode != 0:
        raise RuntimeError(f"render failed: {res.stderr[-600:]}")
    report["video_reencoded"] = reencode
    report["expected_duration_s"] = round(duration, 3)
    return report


def load_words(args) -> list[dict] | None:
    timed = text = None
    if args.words:
        with open(args.words, encoding="utf-8") as fh:
            timed = normalize_words(json.load(fh))
    if args.srt:
        text = words_from_srt(Path(args.srt).read_text(encoding="utf-8"))
    if timed and text:
        return align_text_to_timing(text, timed)
    return timed or text


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("src")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--profile", help="video-style.json")
    ap.add_argument("--trim-head", action="store_true", help="cut dead air before the hook")
    ap.add_argument("--loudness", action="store_true", help="two-pass loudnorm to target")
    ap.add_argument("--words", help="word-level JSON (timing)")
    ap.add_argument("--srt", help="cue-level SRT, e.g. Descript export (text). "
                    "Give both to keep Descript's words on the ASR's clock.")
    m = ap.add_mutually_exclusive_group()
    m.add_argument("--burn", action="store_true", help="burn captions into the picture")
    m.add_argument("--sidecar", action="store_true", help="write captions.srt only")
    ap.add_argument("--keywords", default="", help="comma list to highlight")
    ap.add_argument("--reframe", help="crop to an aspect such as 9:16 or 1:1")
    ap.add_argument("--focus-x", type=float, default=0.5,
                    help="horizontal centre of the crop, 0-1 (default 0.5)")
    ap.add_argument("--clip", help="START-END seconds on the source, e.g. 3301.2-3342.8")
    ap.add_argument("--no-qa", action="store_true", help="skip the QA receipt")
    args = ap.parse_args(argv)
    style = load_style(args.profile)
    try:
        words = load_words(args)
        rep = finish(args.src, args.out, style, args.trim_head, args.loudness, words,
                     burn=bool(words) and not args.sidecar,
                     keywords=[k.strip() for k in args.keywords.split(",") if k.strip()],
                     reframe=args.reframe, focus_x=args.focus_x,
                     clip=tuple(float(x) for x in args.clip.split("-")) if args.clip
                     else None)
        if not args.no_qa:
            qa = video_qa.qa(args.out, style["qa"], Path(args.out + ".qa"))
            rep["qa_verdict"] = qa["verdict"]
            rep["qa_receipt"] = args.out + ".qa/qa-receipt.md"
            got = qa["probe"]["duration_s"]
            if abs(got - rep["expected_duration_s"]) > 0.25:
                rep["duration_mismatch_s"] = round(got - rep["expected_duration_s"], 3)
    except Exception as exc:
        print(f"finish failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(rep, indent=2))
    return 1 if rep.get("qa_verdict") == "FAIL" or "duration_mismatch_s" in rep else 0


if __name__ == "__main__":
    sys.exit(main())
