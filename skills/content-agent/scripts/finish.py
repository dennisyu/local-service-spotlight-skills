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
              [--words words.json] [--srt captions.srt] [--burn]
              [--clip START-END] [--reframe 9:16 --focus-x 0.5]
              [--keywords "Dollar a Day,GCT"]

    --words takes word-level JSON (transcribe_words.py, ElevenLabs Scribe, or a
    faster-whisper dump). --srt takes a Descript export_transcript srt and spreads
    each cue's words evenly across the cue. Give BOTH and the captions use
    Descript's corrected words on the ASR's word clock (best of each). --clip
    edges snap to word boundaries so no cut lands inside a word. Captions are
    written as a sidecar .captions.srt unless --burn is given (burning re-encodes
    the picture, so it is never the default). Caption text is cleaned of anything
    a player would read as a command ({\\b1}, \\N, <font>) in both outputs.

    --trim-head cuts to the first transcribed word when --words or --srt is given,
    otherwise to the first sustained sound (a record-button click followed by dead
    air is not a start). Bad input (a missing profile, a words file without times,
    a malformed --clip or --reframe) prints one plain line and exits 2.

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
               "true_peak_headroom_db": 1.0},
}

PUNCT_BREAK = re.compile(r"[.,!?;:\-—–]\"?$")
CROSSTALK = {"right", "yeah", "yes", "yep", "mhm", "mm", "hmm", "uh", "um",
             "uhhuh", "okay", "ok", "wow", "nice", "sure"}
NUMBERISH = re.compile(r"[\d$%]")
# "Dennis Yu: ..." or "[Speaker 2]: ..." — every word capitalised, so "Step one:"
# and "So here's the thing:" are left alone.
SPEAKER_LABEL = re.compile(r"^\s*(?:\[[^\]]{1,30}\]|[A-Z][\w.'-]*(?: [A-Z][\w.'-]*){0,2}):\s+")


def load_style(path: str | None) -> dict:
    """DEFAULT_STYLE merged with a video-style.json. Raises ValueError with a plain
    message (missing file, bad JSON) so main() can exit 2, never a traceback."""
    style = json.loads(json.dumps(DEFAULT_STYLE))
    qa_prof = video_qa.load_profile(None)
    if path:
        qa_prof = video_qa.load_profile(path)  # validates the file first
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
        style = video_qa.deep_merge(style, {k: raw[k] for k in ("captions", "finish")
                                            if k in raw})
    style["qa"] = qa_prof
    return style


# ---------------------------------------------------------------- words in

WORDS_SHAPE = ("expected ElevenLabs Scribe, faster-whisper, or a list of "
               "{word, start, end} objects with times in seconds")
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")


def normalize_words(data) -> list[dict]:
    """Accept Scribe, faster-whisper or plain [{word,start,end}] JSON.
    Whitespace inside a word (a stray newline from an editor) collapses to one
    space so a caption line can never split. Raises ValueError naming the entry
    when a time is missing or not a number."""
    if isinstance(data, dict):
        if "words" in data:
            data = data["words"]
        elif "segments" in data:
            data = [w for seg in data["segments"] for w in (seg.get("words") or [])]
    if not isinstance(data, list):
        raise ValueError(f"words file has no word list; {WORDS_SHAPE}")
    words = []
    for i, w in enumerate(data):
        if not isinstance(w, dict):
            raise ValueError(f"words entry {i} is not an object; {WORDS_SHAPE}")
        if w.get("type") not in (None, "word"):
            continue  # Scribe spacing and audio_event entries
        text = " ".join(_CONTROL.sub(" ", str(w.get("word", w.get("text", "")))).split())
        if not text:
            continue
        try:
            start, end = float(w["start"]), float(w["end"])
        except KeyError as exc:
            raise ValueError(f"words entry {i} ({text!r}) has no '{exc.args[0]}' time; "
                             f"{WORDS_SHAPE}") from None
        except (TypeError, ValueError):
            raise ValueError(f"words entry {i} ({text!r}) has a time that is not a "
                             f"number; {WORDS_SHAPE}") from None
        if start != start or end != end or end < start:
            raise ValueError(f"words entry {i} ({text!r}) ends before it starts")
        words.append({"word": text, "start": start, "end": end})
    words.sort(key=lambda w: w["start"])
    return words


def read_words_file(path: str) -> list[dict]:
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except OSError as exc:
        raise ValueError(f"could not read --words {path}: {exc.strerror or exc}") from None
    except json.JSONDecodeError as exc:
        raise ValueError(f"--words {path} is not valid JSON: {exc}") from None
    try:
        return normalize_words(data)
    except ValueError as exc:
        raise ValueError(f"--words {path}: {exc}") from None


def read_srt_file(path: str) -> list[dict]:
    try:
        return words_from_srt(Path(path).read_text(encoding="utf-8", errors="replace"))
    except OSError as exc:
        raise ValueError(f"could not read --srt {path}: {exc.strerror or exc}") from None


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
        body = SPEAKER_LABEL.sub("", body, count=1)
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
                and len(merged[-1]["words"]) + len(cue["words"]) <= cap["max_words"]
                and len(" ".join(x["word"] for x in merged[-1]["words"] + cue["words"]))
                <= cap["max_chars"]):
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


def _parts(text: str) -> list[str]:
    """'Dollar-a-Day' and 'Dollar a Day' both become ['dollar', 'a', 'day']."""
    out: list[str] = []
    for chunk in re.split(r"[\s\-—–]+", text):
        out += [p for p in _clean(chunk).split("-") if p]
    return out


def mark_keywords(words: list[dict], keywords: list[str]) -> list[dict]:
    """Flag words that belong to a WHOLE keyword phrase ("Dollar a Day" lights up
    only as three words in a row, never a lone "a"). Hyphens count as spaces on
    both sides, so "Dollar-a-Day" matches too; a match must start and end on a
    word boundary, so "a Day" never lights the whole of "Dollar-a-Day"."""
    phrases = [ph for ph in (_parts(kw) for kw in keywords) if ph]
    flat: list[tuple[int, str, bool, bool]] = []  # (word index, part, first, last)
    for wi, w in enumerate(words):
        parts = _parts(w["word"])
        for pi, part in enumerate(parts):
            flat.append((wi, part, pi == 0, pi == len(parts) - 1))
    toks = [f[1] for f in flat]
    out = [dict(w) for w in words]
    for ph in phrases:
        n = len(ph)
        for i in range(len(toks) - n + 1):
            if toks[i:i + n] == ph and flat[i][2] and flat[i + n - 1][3]:
                for j in range(i, i + n):
                    out[flat[j][0]]["hot"] = True
    return out


TAG_LIKE = re.compile(r"</?[A-Za-z][^<>]*>")


def _caption_safe(text: str) -> str:
    """Players read backslash sequences (\\N), {override tags} and <html tags> as
    commands in BOTH .ass and .srt (libass, VLC, YouTube). Strip them so a word is
    always shown as a word."""
    text = TAG_LIKE.sub("", text)
    return text.replace("\\", "").replace("{", "(").replace("}", ")")


_ass_safe = _caption_safe  # kept for callers of the round-1 name


def cue_text(cue: dict, cap: dict, ass: bool) -> str:
    parts = []
    for w in cue["words"]:
        txt = _caption_safe(w["word"].upper() if cap["uppercase"] else w["word"])
        txt = " ".join(txt.split())
        hot = w.get("hot") or (cap["highlight_numbers"] and NUMBERISH.search(w["word"]))
        if ass:
            if hot:
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

def first_speech_s(path: str, style: dict, offset: float, window: float,
                   sample_rate: int | None = None) -> float | None:
    """Source-timeline seconds where SUSTAINED sound first starts inside
    [offset, offset+window]. The threshold follows the window's own loudness and
    clears its noise floor, so neither a quiet speaker nor room noise fools it;
    a click followed by dead air is skipped. None = no such sound (never trim)."""
    qa_prof = style["qa"]
    loud = video_qa.measure_loudness(path, offset, window)
    thr = video_qa.silence_threshold(qa_prof, loud.get("integrated_lufs"))
    guard = video_qa.noise_guard(qa_prof, thr, video_qa.window_peaks(
        path, offset, window, sample_rate))
    if not guard["measurable"]:
        return None
    hp = qa_prof["hook"]
    t = video_qa.first_sound_s(path, guard["threshold_db"], offset, window,
                               hp.get("min_sound_s", 0.15), hp.get("merge_gap_s", 0.25))
    return None if t is None else offset + t


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


active_area = video_qa.active_area  # letterbox finder lives with the QA checks


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


def parse_clip(text: str) -> tuple[float, float]:
    """'3301.2-3342.8' -> (3301.2, 3342.8); rejects reversed or empty windows."""
    m = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*", text or "")
    if not m:
        raise ValueError(f"--clip must look like START-END in seconds, got {text!r}")
    a, b = float(m.group(1)), float(m.group(2))
    if b <= a:
        raise ValueError(f"--clip end {b} is not after start {a}")
    return a, b


def _loudnorm_json(stderr: str) -> dict:
    blob = stderr[stderr.rfind("{"):stderr.rfind("}") + 1]
    try:
        return json.loads(blob) if blob else {}
    except json.JSONDecodeError:
        return {}


def audio_codec_args(dst: str, src_codec: str | None, bitrate: str,
                     copy_ok: bool) -> list[str]:
    """Pick the audio codec the OUTPUT container can hold. AAC written into a
    .wav is undecodable (found 23 Oct 2026: QA read it as -70 LUFS silence)."""
    ext = os.path.splitext(dst)[1].lower()
    src_codec = (src_codec or "").lower()
    if ext in (".wav", ".aif", ".aiff"):
        pcm = src_codec if src_codec.startswith("pcm_") else "pcm_s16le"
        if ext != ".wav" and pcm.endswith("le"):
            pcm = pcm[:-2] + "be"  # AIFF is big-endian
        return ["-c:a", pcm]
    if ext == ".flac":
        return ["-c:a", "flac"]
    if ext == ".mp3":
        return ["-c:a", "copy"] if copy_ok and src_codec == "mp3" else \
            ["-c:a", "libmp3lame", "-b:a", bitrate]
    if ext in (".ogg", ".opus", ".webm"):
        return ["-c:a", "copy"] if copy_ok and src_codec in ("opus", "vorbis") else \
            ["-c:a", "libopus", "-b:a", bitrate]
    if copy_ok and src_codec in ("aac", "mp3", "ac3", "eac3", "alac", "opus"):
        return ["-c:a", "copy"]
    return ["-c:a", "aac", "-b:a", bitrate]


def finish(src: str, dst: str, style: dict, trim_head: bool, loudness: bool,
           words: list[dict] | None, burn: bool, keywords: list[str],
           reframe: str | None = None, focus_x: float = 0.5,
           clip: tuple[float, float] | None = None) -> dict:
    info = video_qa.probe(src)
    if info["audio"] is None:
        raise RuntimeError("source has no audio stream; nothing to normalise or caption")
    if info["video"] is None and (burn or reframe):
        raise RuntimeError("source has no video stream; --burn and --reframe need a picture")
    fin, cap = style["finish"], dict(style["captions"])
    cap["keywords"] = list(cap.get("keywords", [])) + keywords
    report = {"source": os.path.basename(src), "output": os.path.basename(dst),
              "steps": [], "warnings": []}

    total = info["duration_s"]
    clip_start, clip_end = clip if clip else (0.0, total)
    if clip and (clip_start >= total or clip_end <= clip_start):
        raise ValueError(f"--clip {clip_start}-{clip_end} is outside the "
                         f"{total:.2f}s source")
    clip_end = min(clip_end, total)
    if clip and words:
        clip_start, clip_end = snap_to_words(words, clip_start, clip_end,
                                             fin["head_pad_s"])
        report["clip_snapped_to_words"] = [round(clip_start, 3), round(clip_end, 3)]
    start = clip_start
    if trim_head:
        # The hook rule is about the first WORD: with a transcript, cut to it.
        first_word = next((w for w in (words or [])
                           if w["start"] >= clip_start - 0.02 and w["start"] < clip_end),
                          None)
        if first_word is not None:
            start = max(clip_start, first_word["start"] - fin["head_pad_s"])
            report["trim_head_to"] = "first word"
        else:
            fs = first_speech_s(src, style, clip_start,
                                min(clip_end - clip_start, 120.0),
                                info["audio"]["sample_rate"])
            if fs is None:
                report["warnings"].append(
                    "trim-head found no sustained sound it could tell from noise in "
                    "the window; nothing trimmed")
            else:
                start = max(clip_start, fs - fin["head_pad_s"])
                report["trim_head_to"] = "first sustained sound"
    duration = clip_end - start
    if duration <= 0.1:
        raise ValueError("nothing left to render after trimming; check --clip and "
                         "--trim-head")
    report["start_s"] = round(start, 3)

    afilters = []
    if start > 0 or clip:
        afilters.append(f"afade=t=in:st=0:d={fin['fade_s']}")
    if clip:
        afilters.append(f"afade=t=out:st={max(0.0, duration - fin['fade_s']):.3f}"
                        f":d={fin['fade_s']}")
    loud_on = False
    if loudness:
        m = measure_loudnorm(src, start, style, duration if (clip or start > 0) else None)
        try:
            in_i = float(m["input_i"])
        except (KeyError, ValueError):
            in_i = float("-inf")
        if in_i != in_i or in_i <= video_qa.SILENT_LUFS:
            report["warnings"].append("audio is silent or unmeasurable; loudness "
                                      "pass skipped")
        else:
            loud_on = True
            lp = style["qa"]["loudness"]
            afilters.append(
                f"loudnorm=I={lp['target_lufs']}:"
                # AAC encoding adds inter-sample overs and ffmpeg falls back to
                # dynamic mode when linear gain would clip: aim well under the
                # QA ceiling (1 dB measured enough on a 66-minute replay).
                f"TP={lp['true_peak_max_dbtp'] - fin.get('true_peak_headroom_db', 1.0)}:"
                f"LRA={fin['lra_target']}:measured_I={m['input_i']}:"
                f"measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
                f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:"
                f"linear=true:print_format=json")
            afilters.append(f"aresample={info['audio']['sample_rate'] or 48000}")
            report["steps"].append({"loudness_in_lufs": in_i,
                                    "true_peak_in_dbtp": float(m["input_tp"])})

    work = Path(tempfile.mkdtemp(prefix="finish-"))
    vfilters = []
    if info["video"]:
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
    out_words = None
    if words:
        inside = [w for w in words if w["start"] >= start - 0.05
                  and w["end"] <= start + duration + 0.05]
        inside = mark_keywords(inside, cap["keywords"])
        cues = shift_cues(chunk_words(inside, cap), start)
        out_words = [{**w, "start": max(0.0, w["start"] - start),
                      "end": w["end"] - start} for w in inside]
        sidecar = Path(dst).with_suffix(".captions.srt")
        sidecar.write_text(build_srt(cues, cap), encoding="utf-8")
        report["steps"].append({"caption_cues": len(cues), "sidecar_srt": sidecar.name,
                                "burned": bool(burn)})
        if burn:
            report["caption_font"] = assert_font(cap["font"])
            (work / "cap.ass").write_text(build_ass(cues, cap, out_w, out_h),
                                          encoding="utf-8")
            vfilters.append("ass=cap.ass")  # LAST in the chain, after any overlay
    elif burn:
        report["warnings"].append("--burn given without --words or --srt; no captions")
    has_video = info["video"] is not None
    reencode = has_video and (bool(vfilters) or start > 0 or bool(clip))
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-y"]
    if start > 0:
        cmd += ["-ss", f"{start:.3f}"]
    if clip or start > 0:
        cmd += ["-t", f"{duration:.3f}"]
    cmd += ["-i", os.path.abspath(src)]
    cmd += (["-map", "0:v:0", "-map", "0:a:0"] if has_video else ["-map", "0:a:0", "-vn"])
    if vfilters:
        cmd += ["-vf", ",".join(vfilters)]
    if has_video:
        cmd += (["-c:v", "libx264", "-preset", fin["x264_preset"], "-crf",
                 str(fin["x264_crf"]), "-pix_fmt", "yuv420p"] if reencode
                else ["-c:v", "copy"])
    if afilters:
        cmd += ["-af", ",".join(afilters)]
    cmd += audio_codec_args(dst, info["audio"].get("codec"), fin["audio_bitrate"],
                            copy_ok=not afilters)
    if has_video or dst.lower().endswith((".mp4", ".m4a", ".mov")):
        cmd += ["-movflags", "+faststart"]
    cmd += [os.path.abspath(dst)]
    res = subprocess.run(cmd, cwd=work, capture_output=True, text=True, errors="replace")
    shutil.rmtree(work, ignore_errors=True)
    if res.returncode != 0:
        tail = [l for l in res.stderr.splitlines() if l.strip()][-6:]
        raise RuntimeError("render failed: " + " | ".join(tail))
    if loud_on:
        ln = _loudnorm_json(res.stderr)
        report["loudnorm_mode"] = ln.get("normalization_type", "unknown")
        if report["loudnorm_mode"] != "linear":
            report["warnings"].append(
                "loudnorm fell back to dynamic mode (linear gain would have clipped); "
                "loudness range is slightly compressed")
    report["video_reencoded"] = reencode
    report["expected_duration_s"] = round(duration, 3)
    report["_out_words"] = out_words
    return report


def load_words(args) -> list[dict] | None:
    timed = text = None
    if args.words:
        timed = read_words_file(args.words)
    if args.srt:
        text = read_srt_file(args.srt)
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
    m.add_argument("--burn", action="store_true",
                   help="burn captions into the picture (re-encodes the video)")
    m.add_argument("--sidecar", action="store_true",
                   help="write captions.srt only (the default when --burn is absent)")
    ap.add_argument("--keywords", default="", help="comma list to highlight")
    ap.add_argument("--reframe", help="crop to an aspect such as 9:16 or 1:1")
    ap.add_argument("--focus-x", type=float, default=0.5,
                    help="horizontal centre of the crop, 0-1 (default 0.5)")
    ap.add_argument("--clip", help="START-END seconds on the source, e.g. 3301.2-3342.8")
    ap.add_argument("--no-qa", action="store_true", help="skip the QA receipt")
    args = ap.parse_args(argv)
    try:
        style = load_style(args.profile)
        if args.reframe and not re.fullmatch(r"\d+(?:\.\d+)?:\d+(?:\.\d+)?", args.reframe):
            raise ValueError(f"--reframe must look like 9:16, got {args.reframe!r}")
        if not 0.0 <= args.focus_x <= 1.0:
            raise ValueError(f"--focus-x must be between 0 and 1, got {args.focus_x}")
        if not os.path.exists(args.src):
            raise ValueError(f"source {args.src} does not exist")
        words = load_words(args)
        rep = finish(args.src, args.out, style, args.trim_head, args.loudness, words,
                     burn=args.burn,
                     keywords=[k.strip() for k in args.keywords.split(",") if k.strip()],
                     reframe=args.reframe, focus_x=args.focus_x,
                     clip=parse_clip(args.clip) if args.clip else None)
        out_words = rep.pop("_out_words", None)
        if not args.no_qa:
            qa = video_qa.qa(args.out, style["qa"], Path(args.out + ".qa"),
                             words=out_words)
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
