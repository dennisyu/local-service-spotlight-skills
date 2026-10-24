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
    edges snap to word boundaries, then onto the sound itself: an ASR word clock
    can run most of a second late or early (a word whose clock starts in 0.4 s
    or more of silence was stretched back over a pause and starts after it; a
    word clocked inside a pause, whose next word claims the sound after it, is
    the sound before it), so the start moves into the pause of 0.15 s or more
    before the first word's sound, and the end into the first pause after the
    last word's (never past a neighbouring word).
    Where talk runs on with no such pause, the edge stays on the word clock and
    the report warns that the clip starts or ends mid-phrase. Captions are
    written as a sidecar .captions.srt unless --burn is given (burning re-encodes
    the picture, so it is never the default). Caption text is cleaned of anything
    a player would read as a command ({\\b1}, \\N, <font>) in both outputs.

    --trim-head cuts to the first transcribed word when --words or --srt is given
    ("[Music]" and "♪" cues are not words), otherwise to the first real sound by
    the QA hook rule: clicks, noise-like typing and static do not count, and a
    short sound followed by 2 s of dead air (a cough) is skipped and reported.
    The cut to the first word lands in the pause before its sound, not on its
    clock. It never cuts talk the transcript missed: sound that runs into the first word
    without 2 s of silence is kept, and a bed or crowd as loud as talk before the
    first word means nothing is cut; both are reported (an intro running straight
    into the first word is then left for a person to cut). A lone short sound
    with a pause after it (a cough, a breath, a click) is not talk running into
    the word: it is cut, and reported. --srt also reads WebVTT; speaker labels
    are stripped ("Speaker 1:", "Name (Role):", a plain "Name:" that opens two or
    more cues, and the first cue's own "Name:" wherever it opens a cue, as in
    Descript's default export). A name that opens one cue only stays text, so
    "Google Maps:" is never dropped; exporting the SRT with
    include_speaker_labels "off" avoids the question.

    The sidecar .captions.srt for long-form reads like sentences (up to 16 words,
    two lines of 42 characters, normal case); with --burn it matches what is on
    screen. When the picture is re-encoded, an HDR source (an iPhone's HLG, PQ)
    is tone-mapped to SDR BT.709 first and tagged that way (needs ffmpeg with
    zscale; without it the report warns). A burned caption with a token too
    wide for the frame (a domain name in 9:16) is shrunk until it fits.

    --loudness on a mono source writes two identical channels: ffmpeg's loudnorm
    lands 1.5-2 LU short on mono when it has to work in dynamic mode, and every
    player plays mono on both speakers anyway. A stereo source with talk in one
    channel only (a lav or a camera mic on one input; the other 30 dB or more
    down) gets the live channel copied to both. The loudness pass measures the
    true peak of the file it wrote, because the AAC encode adds inter-sample
    peaks the filter chain never had; over the ceiling, it renders once more
    with the overshoot plus 0.3 dB off the target, at 320k. AAC is 256k by
    default: ffmpeg's own encoder overshot by up to 2 dB on transients at 192k.

    An audio-only output (.wav .mp3 .m4a .flac .ogg .opus .aif) drops the picture;
    the audio codec always matches the container. The render goes to a hidden
    temporary file beside the output and is renamed only on success, so a failure
    never leaves a stub. Bad input (a missing profile, a string where a number
    belongs, a words file without times, a malformed --clip or --reframe, .webm
    video) prints one plain line and exits 2.

Video is copied untouched when only --loudness is asked for; any trim or burn
re-encodes once with libx264 (preset veryfast unless the profile says otherwise).
Nothing is ever played aloud.
"""
from __future__ import annotations

import argparse
import html
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
    # The caption FILE uploaded beside a long-form video (YouTube, LinkedIn) reads
    # as sentences: sentence case, up to two 42-character lines. Burned shorts keep
    # the 2-3 word style above, and their sidecar matches what is on screen.
    "sidecar_captions": {"max_words": 16, "max_chars": 84, "line_chars": 42,
                         "uppercase": False, "break_gap_s": 0.7, "min_cue_s": 1.0,
                         "merge_sentences": True},
    "finish": {"head_pad_s": 0.08, "fade_s": 0.03, "x264_preset": "veryfast",
               "x264_crf": 18, "audio_bitrate": "256k", "lra_target": 11.0,
               "true_peak_headroom_db": 1.0},
}

PUNCT_BREAK = re.compile(r"[.,!?;:\-—–]\"?$")
CROSSTALK = {"right", "yeah", "yes", "yep", "mhm", "mm", "hmm", "uh", "um",
             "uhhuh", "okay", "ok", "wow", "nice", "sure"}
NUMBERISH = re.compile(r"[\d$%]")
# "Dennis Yu: ..." or "[Speaker 2]: ..." — every word capitalised (name particles
# such as "van" or "de" aside), so "Step one:" and "So here's the thing:" are
# left alone.
_PARTICLE = (r"(?:van|von|der|den|de|del|della|da|di|du|dos|das|la|le|bin|ibn|al|el|"
             r"ter|ten|zu|y)")
_CAP = r"[A-Z][\w.'-]*"
_NAME = (_CAP + r"(?: (?:" + _PARTICLE + r" ){0,2}" + _CAP + r"){0,2}"
         r"(?: \([^)]{1,24}\))?")
# The same shape in any case ("dennis yu:" from a Zoom export): a label only when
# it opens two or more cues, like a plain capitalised one.
_ANY_NAME = r"[^\W\d_][\w.'-]*(?: [^\W\d_][\w.'-]*){0,3}(?: \([^)]{1,24}\))?"
_SPEAKER_N = r"(?i:speaker) ?\d{1,2}"
SPEAKER_LABEL = re.compile(r"^\s*(?:\[[^\]]{1,30}\]|" + _SPEAKER_N + "|" + _NAME + r"):\s+")
LOOSE_LABEL = re.compile(r"^\s*(" + _ANY_NAME + r"):\s+")
# Unmistakable label forms: "[Speaker 2]:", "Speaker 1:", "SPEAKER 1:",
# "Dennis Yu (Host):".
SURE_LABEL = re.compile(r"^\s*(?:\[[^\]]{1,30}\]|" + _SPEAKER_N + "|" + _CAP +
                        r"(?: " + _CAP + r"){0,2} \([^)]{1,24}\)):\s+")
# ">> DENNIS:" or a bare ">>" marks a change of speaker anywhere in a cue.
SPEAKER_CHANGE = re.compile(r">>\s*(?:(?:" + _SPEAKER_N + "|" + _NAME + r"):\s*)?")
# Words that open a sentence with a colon ("Remember: ...") rather than name a
# speaker; the first-cue rule below never strips these.
NOT_A_SPEAKER = {"remember", "note", "tip", "step", "warning", "question", "answer",
                 "update", "important", "reminder", "rule", "lesson", "bonus", "fact",
                 "myth", "example", "problem", "solution", "goal", "why", "how", "what",
                 "first", "second", "third", "next", "finally", "plus", "ps", "edit",
                 "spoiler", "truth", "result", "results", "quote", "title", "chapter",
                 "part", "day", "week", "breaking", "listen", "look", "okay", "ok", "so",
                 "now", "here", "yes", "no", "well", "and", "but", "caution",
                 "hint", "summary", "recap", "takeaway", "today", "tomorrow", "yesterday",
                 # Audit round 9: "Pro Tip:", "Hot Take:" and "Disclaimer:" opening
                 # cue 1 made an unlabelled file read as labelled.
                 "pro", "hot", "disclaimer", "quick", "fun", "side", "bottom", "key",
                 "big", "news", "fyi", "heads", "notice", "reality", "secret",
                 "mistake", "pros", "cons", "case", "action",
                 "homework", "challenge", "story", "point", "takeaways", "translation",
                 "definition", "context", "background", "source", "sources", "caveat",
                 "the", "a", "my", "our", "your", "this", "that", "one", "two", "three"}


def load_style(path: str | None) -> dict:
    """DEFAULT_STYLE merged with a video-style.json. Raises ValueError with a plain
    message (missing file, bad JSON) so main() can exit 2, never a traceback."""
    style = json.loads(json.dumps(DEFAULT_STYLE))
    qa_prof = video_qa.load_profile(None)
    if path:
        qa_prof = video_qa.load_profile(path)  # validates the file first
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
        style = video_qa.deep_merge(style, {k: raw[k] for k in
                                            ("captions", "finish", "sidecar_captions")
                                            if k in raw})
        for block in ("captions", "finish", "sidecar_captions"):
            video_qa._check_types(style[block], DEFAULT_STYLE[block], block)
    style["qa"] = qa_prof
    return style


# ---------------------------------------------------------------- words in

# Caption conventions for sound, not speech: "[Music]", "[Applause]", "(laughs)",
# "♪ ♪". They are never the first word and never caption text.
_SOUND_WORDS = (r"music\w*|song|sing\w*|applau\w*|clap\w*|cheer\w*|laugh\w*|chuckl\w*|"
                r"giggl\w*|sigh\w*|cough\w*|sneez\w*|breath\w*|gasp\w*|inaudible|"
                r"crosstalk|silence|noise\w*|static|beep\w*|bell\w*|ring\w*|knock\w*|"
                r"door\w*|footstep\w*|phone|typing|click\w*|wind|rain|thunder|engine|"
                r"whoosh|background|foreign|speaking|speaks|whisper\w*|groan\w*|"
                r"音楽|拍手|笑")
SOUND_TAG = re.compile(
    r"\[[^\]]{0,40}\]|［[^］]{0,40}］|"
    r"[(（](?:[^)）]*(?:\b(?:" + _SOUND_WORDS + r")\b|音楽|拍手|笑)[^)）]*)[)）]|"
    r"\*(?:[^*]{0,30}\b(?:" + _SOUND_WORDS + r")\b[^*]{0,30})\*", re.I)
MUSIC_NOTES = re.compile(r"[♪♫♬♩🎵🎶]+")


def is_sound_tag(text: str) -> bool:
    """True for a token that is only a sound cue: "[Music]", "(applause)", "♪".
    A token with no cue in it at all ("&", "-") is text, not a cue."""
    if not SOUND_TAG.search(text) and not MUSIC_NOTES.search(text):
        return False
    rest = MUSIC_NOTES.sub("", SOUND_TAG.sub("", text)).strip()
    return not re.sub(r"[^\w$%]", "", rest)


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
        if not text or is_sound_tag(text):
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
        words.append({"word": text, "start": start, "end": end, "timing": "word"})
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


def _decode_text(raw: bytes) -> str:
    """Subtitle files arrive as UTF-8, UTF-8 with a BOM, or UTF-16 (Windows tools)."""
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16", errors="replace")
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw[3:].decode("utf-8", errors="replace")
    if len(raw) > 4 and raw[1:4:2] == b"\x00\x00" and raw[0] != 0:
        return raw.decode("utf-16-le", errors="replace")
    return raw.decode("utf-8", errors="replace")


def read_srt_file(path: str) -> list[dict]:
    try:
        return words_from_srt(_decode_text(Path(path).read_bytes()))
    except OSError as exc:
        raise ValueError(f"could not read --srt {path}: {exc.strerror or exc}") from None
    except ValueError as exc:
        raise ValueError(f"--srt {path}: {exc} (expected SRT or WebVTT)") from None


_TS = re.compile(r"(?:(\d+):)?(\d{1,2}):(\d{1,2})(?:[,.](\d{1,3}))?")


def _ts(s: str) -> float:
    """SRT "00:00:01,500", WebVTT "00:01.500" or "00:00:01.500"; "…,5" is 0.5 s."""
    m = _TS.fullmatch(s.strip())
    if not m:
        raise ValueError(f"not a subtitle time: {s.strip()!r}")
    h, mi, sec, frac = m.groups()
    return (int(h or 0) * 3600 + int(mi) * 60 + int(sec)
            + (int(frac.ljust(3, "0")) / 1000.0 if frac else 0.0))


def words_from_srt(text: str) -> list[dict]:
    """SRT or WebVTT cues -> words spread evenly across each cue. Sound cues
    ("[Music]", "♪") are dropped, and so are speaker labels: "[Speaker 2]:",
    "Speaker 1:", "SPEAKER 1:", "Name (Role):" and ">> NAME:" always; a plain
    "Name:", "Dennis Yu:", "Ludwig van Beethoven:" or "dennis yu:" when it opens
    two or more cues; and in a file whose first cue opens with a name label
    (Descript's default export labels the first cue and every change of
    speaker), any capitalised "Name:" opening a cue. "Remember:" or "Google:" at
    the start of one line of an unlabelled file stays text."""
    words = []
    text = text.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
    blocks = re.split(r"\n\s*\n", text.strip())

    def body_of(block: str) -> str | None:
        lines = [l for l in block.strip().splitlines() if l.strip()]
        timing = next((l for l in lines if "-->" in l), None)
        if not timing:
            return None
        body = " ".join(lines[lines.index(timing) + 1:])
        body = html.unescape(re.sub(r"<[^>]+>|\{[^}]+\}", "", body))
        return SPEAKER_CHANGE.sub(" ", MUSIC_NOTES.sub(" ", SOUND_TAG.sub(" ", body)))

    seen: dict = {}
    first_label = None  # the name opening the file's first cue, "" when none
    for block in blocks:
        b = body_of(block)
        if b is None:
            continue
        m = LOOSE_LABEL.match(b)
        if m:
            key = m.group(1).strip().lower()
            seen[key] = seen.get(key, 0) + 1
        if first_label is None and b.strip():
            first_label = (m.group(1).strip() if m and SPEAKER_LABEL.match(b)
                           and not SURE_LABEL.match(b) else
                           ("sure" if SURE_LABEL.match(b) else ""))

    def speaker(name: str) -> bool:
        return name.split()[0].lower().strip(".") not in NOT_A_SPEAKER
    # Descript's default SRT export ("changes") labels the first cue and every
    # change of speaker: a file that opens with a label uses labels (audit round 8:
    # "Dennis: So" on cue 1 only became the caption "So Dennis:").
    labelled = bool(first_label) and (first_label == "sure" or speaker(first_label))

    def label_end(body: str) -> int:
        sure = SURE_LABEL.match(body)
        if sure:
            return sure.end()
        m = LOOSE_LABEL.match(body)
        if not m:
            return 0
        name = m.group(1).strip()
        if seen.get(name.lower(), 0) >= 2:
            return m.end()
        # A labelled file's first-cue name is a label even where it opens a cue
        # once (Descript's default export labels cue 1 only). Any other name
        # must open two or more cues: "Google Maps:" once is text (audit round 9).
        if labelled and name.lower() == first_label.lower():
            return m.end()
        return 0

    for cue_id, block in enumerate(blocks):
        lines = [l for l in block.strip().splitlines() if l.strip()]
        timing = next((l for l in lines if "-->" in l), None)
        if not timing:
            continue  # WEBVTT header, NOTE and STYLE blocks
        parts = timing.split("-->")
        a, b = parts[0].strip().split()[-1], parts[1].strip().split()[0]
        start, end = _ts(a), _ts(b)
        # Sound cues first, then the speaker label they may hide ("[Music] Dennis Yu: …").
        body = body_of(block) or ""
        body = body[label_end(body):]
        toks = [t for t in body.split() if not is_sound_tag(t)]
        if not toks or end <= start:
            continue
        step = (end - start) / len(toks)
        for i, tok in enumerate(toks):
            words.append({"word": tok, "start": round(start + i * step, 3),
                          "end": round(start + (i + 1) * step, 3),
                          "timing": "cue", "cue": cue_id,
                          "cue_start": start, "cue_end": end})
    return words


def _norm(tok: str) -> str:
    return re.sub(r"[^\w]", "", tok.lower())


def align_text_to_timing(text_words: list[dict], timed: list[dict],
                         keep_unheard: bool = False) -> list[dict]:
    """Keep the better TEXT (Descript's corrected transcript) and the better
    TIMING (word-level ASR). Matched and same-length replaced runs take the
    timed word's clock; other runs are spread across the span they replace.
    Returns text_words re-timed, limited to the window the timed words cover.
    Words the ASR never heard are marked heard=False. A lone interjection the ASR
    never heard is left out of the captions; with keep_unheard it is returned
    anyway with caption=False and its cue's own timing, because for the QA
    receipt it is still talk (someone said "Yeah" there). keep_unheard also keeps
    the SRT's words outside the ASR's window, and the ones before the first heard
    word, on their cue timing (an ASR that missed an opening under room chatter
    must not erase it), and the ASR's own words the SRT lacks as caption=False
    talk (a second voice Descript left out)."""
    import difflib
    if not timed:
        return text_words
    lo, hi = timed[0]["start"] - 1.0, timed[-1]["end"] + 1.0
    text = [w for w in text_words if lo <= w["start"] <= hi]
    outside = ([dict(w, timing="cue", heard=False) for w in text_words
                if not lo <= w["start"] <= hi] if keep_unheard else [])
    sm = difflib.SequenceMatcher(a=[_norm(w["word"]) for w in text],
                                 b=[_norm(w["word"]) for w in timed], autojunk=False)
    out: list[dict] = []
    for op, a0, a1, b0, b1 in sm.get_opcodes():
        span = text[a0:a1]
        if not span:
            if keep_unheard:
                out += [{"word": s_["word"], "start": s_["start"], "end": s_["end"],
                         "timing": "word", "heard": True, "caption": False}
                        for s_ in timed[b0:b1]]
            continue
        if op in ("equal", "replace") and (a1 - a0) == (b1 - b0):
            out += [{"word": t["word"], "start": s["start"], "end": s["end"],
                     "timing": "word", "heard": True} for t, s in zip(span, timed[b0:b1])]
            continue
        if b1 > b0:
            s0, s1 = timed[b0]["start"], timed[b1 - 1]["end"]
        else:
            # Words the ASR never heard. A lone interjection ("Right", "Yeah") is
            # almost always another person's crosstalk: leave it out of the
            # speaker's captions. Anything else is squeezed, in order, into the
            # gap between its neighbours so word order can never scramble.
            if keep_unheard:
                out += [dict(t, timing="cue", heard=False, caption=False)
                        for t in span if _norm(t["word"]) in CROSSTALK]
            span = [t for t in span if _norm(t["word"]) not in CROSSTALK]
            if not span:
                continue
            if keep_unheard and not any(x.get("heard") for x in out):
                # Before the first word the ASR heard: keep the SRT's own times.
                out += [dict(t, timing="cue", heard=False) for t in span]
                continue
            s0 = out[-1]["end"] if out else timed[0]["start"]
            s1 = timed[b0]["start"] if b0 < len(timed) else s0 + 0.2 * len(span)
            s1 = max(s1, s0)
        step = (s1 - s0) / len(span)
        out += [{"word": t["word"], "start": round(s0 + i * step, 3),
                 "end": round(s0 + (i + 1) * step, 3), "timing": "word",
                 "heard": b1 > b0,
                 **({k: t[k] for k in ("cue_start", "cue_end") if k in t})}
                for i, t in enumerate(span)]
    if keep_unheard:
        out = sorted(out + outside, key=lambda w: w["start"])
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
            text = " ".join(x["word"] for x in cur + [w])
            if (len(cur) >= cap["max_words"] or gap >= cap["break_gap_s"]
                    or chars > cap["max_chars"] or not _fits(text, cap.get("line_chars", 0))):
                flush()
        cur.append(w)
        if PUNCT_BREAK.search(w["word"]):
            flush()
    flush()
    # Never flash a cue shorter than min_cue_s: stretch into the gap after it,
    # else merge into the next cue when there is room.
    merged: list[dict] = []
    carry = None
    for idx, cue in enumerate(cues):
        if carry is not None:  # a short cue held back to open this one
            cue = {"words": carry["words"] + cue["words"], "start": carry["start"],
                   "end": cue["end"]}
            carry = None
        nxt = cues[idx + 1] if idx + 1 < len(cues) else None
        if cue["end"] - cue["start"] < cap["min_cue_s"]:
            limit = nxt["start"] if nxt else cue["start"] + cap["min_cue_s"]
            cue["end"] = min(cue["start"] + cap["min_cue_s"], max(limit, cue["end"]))
        joined = " ".join(x["word"] for x in (merged[-1]["words"] if merged else [])
                          + cue["words"])
        if (merged and cue["end"] - cue["start"] < cap["min_cue_s"]
                and cue["words"][0]["start"] - merged[-1]["words"][-1]["end"] < cap["break_gap_s"]
                and (cap.get("merge_sentences")
                     or not re.search(r"[.!?]\"?$", merged[-1]["words"][-1]["word"]))
                and len(merged[-1]["words"]) + len(cue["words"]) <= cap["max_words"]
                and len(joined) <= cap["max_chars"]
                and _fits(joined, cap.get("line_chars", 0))):
            merged[-1]["words"] += cue["words"]
            merged[-1]["end"] = cue["end"]
            continue
        if (cap.get("merge_sentences") and nxt and cue["end"] - cue["start"] < cap["min_cue_s"]
                and nxt["start"] - cue["end"] < cap["break_gap_s"]
                and len(cue["words"]) + len(nxt["words"]) <= cap["max_words"]):
            both = " ".join(x["word"] for x in cue["words"] + nxt["words"])
            if len(both) <= cap["max_chars"] and _fits(both, cap.get("line_chars", 0)):
                carry = cue  # too short to stand alone: open the next cue with it
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


_HYPHENS = re.compile(r"[\u2010\u2011\u2012\u2013\u2014\u2015\u2212]")


def _clean(word: str) -> str:
    word = _HYPHENS.sub("-", word).replace("\u2019", "'").replace("\u2018", "'")
    return re.sub(r"[^\w$%'-]", "", word).lower()


def _parts(text: str) -> list[str]:
    """'Dollar-a-Day' and 'Dollar a Day' both become ['dollar', 'a', 'day']."""
    out: list[str] = []
    for chunk in re.split(r"\s+", _HYPHENS.sub("-", text)):
        out += [p for p in _clean(chunk).split("-") if p]
    return out


def _same(token: str, key: str) -> bool:
    """'day' matches "Day", "Day's", "Days" and "days'"; "GCT" matches "GCT's"."""
    t = token.strip("'")
    if t.endswith("'s"):
        t = t[:-2]
    return t == key or t in (key + "s", key + "es")


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
            if (all(toks[i + j] == ph[j] for j in range(n - 1))
                    and _same(toks[i + n - 1], ph[-1])
                    and flat[i][2] and flat[i + n - 1][3]):
                for j in range(i, i + n):
                    out[flat[j][0]]["hot"] = True
    return out


TAG_LIKE = re.compile(r"</?(?:b|i|u|s|font|c|v|ruby|rt|lang)\b[^<>]*>", re.I)
ASS_OVERRIDE = re.compile(r"\{\\[^}]*\}")


def _caption_safe(text: str) -> str:
    """Players read backslash sequences (\\N), {override tags} and the subtitle
    HTML tags (<b>, <i>, <font>…) as commands in BOTH .ass and .srt (libass, VLC,
    YouTube). Remove those; keep ordinary text ("a<b", "vector<int>", "C++")."""
    text = ASS_OVERRIDE.sub("", TAG_LIKE.sub("", text))
    # Only \N, \n and \h are commands outside braces: drop the backslash there and
    # keep every other one ("C:\path\to" stays readable).
    text = re.sub(r"\\(?=[Nnh])", "", text)
    return text.replace("{", "(").replace("}", ")")


def _srt_safe(line: str) -> str:
    """A '<' that meets a later '>' across two words ("x<b y>z") would open a tag
    in an SRT reader; show angle brackets as look-alike quotes instead."""
    return line.replace("<", "\u2039").replace(">", "\u203a")


_ass_safe = _caption_safe  # kept for callers of the round-1 name


def cue_text(cue: dict, cap: dict, ass: bool) -> str:
    parts = []
    for w in cue["words"]:
        clean = " ".join(_caption_safe(w["word"]).split())
        if not clean:
            continue  # a word that was only a tag
        txt = clean.upper() if cap["uppercase"] else clean
        hot = w.get("hot") or (cap["highlight_numbers"] and NUMBERISH.search(clean))
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


def _nonempty(cues: list[dict], cap: dict) -> list[dict]:
    """Cues whose words were only tags have nothing to show: drop them."""
    return [c for c in cues if cue_text(c, cap, ass=False).strip()]


def build_ass(cues: list[dict], cap: dict, width: int, height: int) -> str:
    cues = _nonempty(cues, cap)
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
    room = width - 2 * round(width * 0.06)
    rows = []
    for c in cues:
        # libass wraps only at spaces: one token wider than the frame (a domain
        # name, a URL) runs off both edges. Shrink that cue until its widest
        # token fits (audit round 8: "LOCALSERVICESPOTLIGHT.COM" on a 9:16 short).
        widest = max((_text_px(t, cap["font"], cap["bold"], size)
                      for t in cue_text(c, cap, ass=False).split()), default=0.0)
        fit = "" if widest <= room else "{\\fs%d}" % max(8, int(size * room / widest * 0.97))
        rows.append(f"Dialogue: 0,{_ass_time(c['start'])},{_ass_time(c['end'])},Cap,,0,0,0,,"
                    f"{fit}{cue_text(c, cap, ass=True)}")
    return head + "\n".join(rows) + "\n"


_FONTS: dict = {}


def _text_px(text: str, family: str, bold: bool, size: int) -> float:
    """Rendered width of text in pixels, from the font file fontconfig picks for
    the caption family (Pillow); without Pillow or fontconfig, a wide estimate
    (0.7 em a character, an uppercase bold face's widest average)."""
    key = (family, bool(bold), size)
    if key not in _FONTS:
        font = None
        try:
            from PIL import ImageFont
            path = subprocess.run(["fc-match", "-f", "%{file}",
                                   f"{family}:bold" if bold else family],
                                  capture_output=True, text=True).stdout.strip()
            if path:
                font = ImageFont.truetype(path, size)
        except Exception:  # Pillow or fontconfig missing, or an unreadable font
            font = None
        _FONTS[key] = font
    font = _FONTS[key]
    if font is not None:
        return float(font.getlength(text))
    return len(text) * size * 0.7


def _wrap(text: str, width: int) -> str:
    """Two lines when a cue is longer than one: the cut that keeps the longer
    line shortest (then the most balanced)."""
    if not width or len(text) <= width:
        return text
    cuts = [i for i, ch in enumerate(text) if ch == " "]
    if cuts:
        cut = min(cuts, key=lambda i: (max(i, len(text) - i - 1), abs(2 * i - len(text))))
        lines = [text[:cut], text[cut + 1:]]
    else:
        lines = [text]
    out = []
    for line in lines:
        # A single token longer than a line (a URL) breaks after / . - when it can.
        while len(line) > width:
            at = max((i + 1 for i, ch in enumerate(line[:width]) if ch in "/.-"), default=width)
            out.append(line[:at])
            line = line[at:]
        out.append(line)
    return "\n".join(out)


def _fits(text: str, width: int) -> bool:
    """Whether text fits on two lines of `width` characters."""
    if not width or len(text) <= width:
        return True
    return max(len(x) for x in _wrap(text, width).split("\n")) <= width


def build_srt(cues: list[dict], cap: dict) -> str:
    cues = _nonempty(cues, cap)
    return "\n".join(f"{i}\n{_srt_time(c['start'])} --> {_srt_time(c['end'])}\n"
                     f"{_wrap(_srt_safe(cue_text(c, cap, ass=False)), cap.get('line_chars', 0))}\n"
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
                   sample_rate: int | None = None, until: float | None = None
                   ) -> tuple[float | None, list[dict], str]:
    """Source-timeline seconds of the first real start inside [offset,
    offset+window], by the same rule as the QA hook check: the threshold follows
    the window's loudness and its local noise floor; clicks, typing and other
    sound with no voice in it do not count; a short sound followed by 2 s of
    dead air (a cough) is skipped.
    Returns (start or None, skipped sounds, reason when None)."""
    qa_prof = style["qa"]
    loud = video_qa.measure_loudness(path, offset, window)
    aud = video_qa.analyze_audio(path, qa_prof, offset, window, sample_rate,
                                 loud.get("integrated_lufs"))
    # The decoded audio starts at the window or at the audio's own first sample,
    # whichever is later (a recording whose sound starts after the picture).
    info = video_qa.probe(path)
    a_rel = 0.0
    if info["audio"] and info["video"]:
        a_rel = max(0.0, info["audio"]["start_s"] - info["video"]["start_s"])
    base = max(offset, a_rel)
    skipped = [dict(s, at_s=round(s["at_s"] + base, 3)) for s in aud["skipped"]]
    if aud["first_sound"] is None:
        reason = ("the start cannot be told from noise or music"
                  if not aud["noise"]["hook_measurable"] else "no sustained sound")
        return None, skipped, reason
    if until is not None:
        return base + aud["first_sound"], skipped, head_into_word(
            aud, base, base + aud["first_sound"], until, qa_prof)
    return base + aud["first_sound"], skipped, ""


def head_into_word(aud: dict, base: float, fs: float, fw: float, prof: dict) -> dict:
    """Sound before the first transcribed word (fw), from the first real start
    fs: where talk that runs on into the word begins, if anywhere. Bursts of
    sound (runs closer than merge_gap_s) shorter than max_skip_sound_s with
    warn_pause_s or more of silence after them are a cough, a breath or a click,
    not talk running into the word (audit round 8: a cough plus 1.4 s of dead
    air was kept at the open). Returns {"start": source seconds or None, "gap":
    longest silence from start to fw, "isolated": [(at, sound_s, silence_after)]}."""
    hp, pp = prof["hook"], prof["pauses"]
    join, short = hp.get("merge_gap_s", 0.25), hp.get("max_skip_sound_s", 0.6)
    quiet = pp.get("warn_pause_s", 0.6)
    bursts: list[list[float]] = []  # [start, end, sound seconds], source time
    for k, a, b in aud["runs"]:
        a, b = base + a, base + b
        if k == 0 or b <= fs - 1e-6 or a >= fw:
            continue
        a, b = max(a, fs), min(b, fw)
        if bursts and a - bursts[-1][1] < join:
            bursts[-1][1], bursts[-1][2] = b, bursts[-1][2] + b - a
        else:
            bursts.append([a, b, b - a])
    isolated, start = [], None
    for i, (a, b, snd) in enumerate(bursts):
        after = (bursts[i + 1][0] if i + 1 < len(bursts) else fw) - b
        if snd < short and after >= quiet:
            isolated.append((round(a, 3), round(snd, 3), round(after, 3)))
            continue
        start = a
        break
    gap = 0.0
    if start is not None:
        gap = max((base + x["end"] - max(base + x["start"], start) for x in aud["silences"]
                   if base + x["end"] > start and base + x["end"] <= fw + 0.05), default=0.0)
    return {"start": start, "gap": round(gap, 3), "isolated": isolated}


UPMIX = "pan=stereo|c0=c0|c1=c0"


def measure_loudnorm(path: str, start: float, style: dict,
                     duration: float | None = None, pre: str = "") -> dict:
    lp = style["qa"]["loudness"]
    flt = (f"{pre + ',' if pre else ''}astats,loudnorm=I={lp['target_lufs']}:"
           f"TP={lp['true_peak_max_dbtp']}:"
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
    out = json.loads(blob)
    out["channel_peaks_db"] = astats_peaks(res.stderr)
    return out


def astats_peaks(stderr: str) -> list[float]:
    """Per-channel peak dBFS from ffmpeg astats' summary (-120 for a silent channel)."""
    peaks, chan = [], None
    for line in stderr.splitlines():
        if re.search(r"\bChannel: \d+", line):
            chan = True
        elif re.search(r"\bOverall\b", line):
            chan = None
        elif chan:
            m = re.search(r"Peak level dB: (\S+)", line)
            if m:
                v = m.group(1)
                peaks.append(-120.0 if "inf" in v else max(-120.0, float(v)))
                chan = None
    return peaks


def level_runs(path: str, style: dict, info: dict, a: float, b: float) -> list[tuple]:
    """Silence (0), sound (1) and unmeasurable (2) runs of [a, b] on the source
    clock, by the QA checker's level rules."""
    a = max(0.0, a)
    loud = video_qa.measure_loudness(path, a, b - a)
    aud = video_qa.analyze_audio(path, style["qa"], a, b - a, info["audio"]["sample_rate"],
                                 loud.get("integrated_lufs"))
    a_rel = 0.0
    if info["audio"] and info.get("video"):
        a_rel = max(0.0, info["audio"]["start_s"] - info["video"]["start_s"])
    base = max(a, a_rel)
    return [(k, base + x, base + y) for k, x, y in aud["runs"]]


def settle_start(runs: list[tuple], fw: float, lo: float, start: float,
                 pad: float, min_sil: float = 0.15,
                 floor: float | None = None,
                 nxt: float | None = None) -> tuple[float, bool]:
    """Put a cut before the first word in the silence before its SOUND: an ASR
    word clock can start a word most of a second late (audit round 9: a short
    opened 0.77 s into "Landscaping") or early. The silence is the last one of
    min_sil or more that starts by the word's clock time (fw) and ends within a
    second before it or later, and after `lo` (the previous word's end, or the
    clip's own start): the word's sound begins where it ends. The cut lands
    inside it, pad before that sound, and not before `floor` when given; the
    previous word's end is a clock too, so it does not bound the cut. A cut
    already in that silence stays. When the clock sits inside a pause and the
    next word's clock (`nxt`) claims the sound after it, the word is the sound
    before the pause. Returns (cut, found), found False when the word sits
    inside a second or more of unbroken sound."""
    sil = [(x, y) for k, x, y in runs if k == 0 and y - x >= min_sil]
    cands = [(x, y) for x, y in sil
             if x <= fw + 0.02 and y >= max(fw - 1.0, lo - 0.05)]
    if not cands:
        return start, False
    x, y = max(cands, key=lambda s: s[0])
    if x <= fw <= y and nxt is not None and nxt <= y + 0.05:
        # The word's clock sits in a pause and the NEXT word claims the sound
        # after it: this word is the sound just before the pause, its clock ran
        # late (the replay's "And" was timed 0.57 s after it was said). Start
        # before that sound when no earlier word claims it.
        before = [(a, b) for a, b in sil if b <= x - 0.05]
        if before:
            a0, b0 = max(before, key=lambda s: s[1])
            if b0 >= max(fw - 1.0, lo - 0.05):
                x, y = a0, b0
    cut = max(x, y - pad, floor if floor is not None else x)
    in_sound = any(k != 0 and a <= start < b for k, a, b in runs)
    return (cut if cut < start or in_sound else start), True


def settle_end(runs: list[tuple], lw: float, hi: float, end: float, pad: float,
               min_sil: float = 0.15) -> tuple[float, bool]:
    """Put a cut after the last word in the silence after its SOUND (an ASR ends
    a word early: "foundation." lost 0.6 s). The silence is the first one of
    min_sil or more that ends after the word's clock end (lw) and starts within
    a second after it or earlier, and before `hi` (the next word's start): the
    word's sound ends where it starts. The cut lands inside it, pad after that
    sound; a cut already in that silence stays. Returns (cut, found)."""
    sil = [(x, y) for k, x, y in runs if k == 0 and y - x >= min_sil]
    cands = [(x, y) for x, y in sil
             if y >= lw - 0.02 and x <= min(lw + 1.0, hi + 0.05)]
    if not cands:
        return end, False
    x, y = min(cands, key=lambda s: s[0])
    cut = min(y, x + pad)
    in_sound = any(k != 0 and a < end <= b for k, a, b in runs)
    return (cut if cut > end or in_sound else end), True


def clamp_stretched(words: list[dict], runs: list[tuple], min_silence: float = 0.4,
                    lead: float = 0.1) -> list[dict]:
    """A heard word whose clock STARTS in a level silence of min_silence or more
    (within `lead` of its start) was stretched back over a pause: it starts
    where that silence ends (the replay's "We're" ran 1.3 s back). A word whose
    span starts in sound and runs on over a pause ("Wow" then 0.4 s of quiet)
    keeps its start: its sound is at the front, and moving it would cut it."""
    sil = [(x, y) for k, x, y in runs if k == 0 and y - x >= min_silence]
    out = []
    for w in words:
        if w.get("timing") != "cue" and w.get("heard", True):
            hit = [y for x, y in sil if x <= w["start"] + lead and w["start"] < y < w["end"]
                   and y - max(x, w["start"]) >= min_silence - 1e-6]
            if hit:
                w = dict(w, start=max(hit), clamped_from=w["start"])
        out.append(w)
    return out


class LevelRuns:
    """Level runs of a source around a moment: ten seconds, so the level rules
    see talk to compare it against, measured once per stretch."""

    def __init__(self, src: str, style: dict, info: dict):
        self.src, self.style, self.info = src, style, info
        self.total = info["duration_s"]
        self.measured: list = []

    def near(self, t: float) -> list[tuple]:
        for a, b, r in self.measured:   # 1.5 s each side, or the file's own edge
            if (a + 1.5 <= t or a <= 0.0 <= t) and \
                    (t <= b - 1.5 or t <= b >= self.total - 0.01):
                return r
        a, b = max(0.0, t - 5.0), min(self.total, t + 5.0)
        r = level_runs(self.src, self.style, self.info, a, b)
        self.measured.append((a, b, r))
        return r


def place_clip(levels: LevelRuns, words: list[dict], start: float, end: float,
               pad: float, in_word: float, report: dict) -> tuple[list[dict], float, float]:
    """--clip edges: on word boundaries, then on the words' sound. Returns the
    words (stretched ones clamped) and the clip's start and end."""
    total = levels.total
    # A word the ASR stretched back over a pause (its clock starts in in_word s
    # or more of level silence) starts after that silence; otherwise a clip
    # asked to start at the pause drops the word (the replay's "We're" ran
    # 1.3 s back into the pause before it).
    words = clamp_stretched(words, levels.near(start) + levels.near(end), in_word)
    start, end = snap_to_words(words, start, end, pad)
    report["clip_snapped_to_words"] = [round(start, 3), round(end, 3)]
    # Then onto the sound itself: the word clock can be most of a second off.
    # The words the snap kept, zero-length ones included (Whisper times some
    # words as an instant: "Helping." at 2063.12 was spoken from 2062.9).
    kept = [w for w in words if w["start"] >= start - 0.02
            and w["end"] <= end + 0.02 and w["start"] <= end]
    if not kept:
        return words, start, end
    fw, lw = min(w["start"] for w in kept), max(w["end"] for w in kept)
    prev_end = max((w["end"] for w in words if w["end"] <= fw + 0.01
                    and w["start"] < fw), default=0.0)
    next_start = min((w["start"] for w in words if w["start"] >= lw - 0.01
                      and w["end"] > lw), default=total)
    nxt = min((w["start"] for w in words if w["start"] > fw + 0.01), default=None)
    new_start, ok_s = settle_start(levels.near(fw), fw, prev_end, start, pad, nxt=nxt)
    new_end, ok_e = settle_end(levels.near(lw), lw, next_start, end, pad)
    if (new_start, new_end) != (start, end):
        report["clip_settled_on_sound"] = [round(new_start, 3), round(new_end, 3)]
    for ok, where in ((ok_s, "starts"), (ok_e, "ends")):
        if not ok:
            report["warnings"].append(
                f"the clip {where} inside unbroken talk (no pause of 0.15 s or more "
                "within a second of the word): the cut lands mid-phrase; pick an edge "
                "at a pause")
    return words, max(0.0, new_start), min(total, new_end)


def snap_to_words(words: list[dict], start: float, end: float,
                  pad: float) -> tuple[float, float]:
    """Never cut inside a word: move clip edges to word boundaries, then pad."""
    inside = [w for w in words if w["end"] > start and w["start"] < end]
    if not inside:
        return start, end
    first = next((w for w in inside if w["start"] >= start - 0.02), inside[0])
    last = next((w for w in reversed(inside) if w["end"] <= end + 0.02), inside[-1])
    # (not the edge word itself: a zero-length word would pin the edge to its
    # own instant, mid-word)
    prev_end = max((w["end"] for w in words if w["end"] <= first["start"]
                    and w is not first), default=0.0)
    next_start = min((w["start"] for w in words if w["start"] >= last["end"]
                      and w is not last), default=last["end"] + pad)
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
    can_copy = {".m4a": ("aac", "alac"), ".mp4": ("aac", "mp3", "ac3", "eac3", "alac",
                                                    "opus"),
                ".mov": ("aac", "alac", "mp3", "ac3"), ".mkv": None}.get(ext, ("aac",))
    if copy_ok and (can_copy is None or src_codec in can_copy):
        return ["-c:a", "copy"]
    return ["-c:a", "aac", "-b:a", bitrate]


AUDIO_ONLY_EXT = (".wav", ".aif", ".aiff", ".flac", ".mp3", ".ogg", ".opus", ".m4a",
                  ".aac")


def finish(src: str, dst: str, style: dict, trim_head: bool, loudness: bool,
           words: list[dict] | None, burn: bool, keywords: list[str],
           reframe: str | None = None, focus_x: float = 0.5,
           clip: tuple[float, float] | None = None) -> dict:
    info = video_qa.probe(src)
    if info["audio"] is None:
        raise RuntimeError("source has no audio stream; nothing to normalise or caption")
    ext = os.path.splitext(dst)[1].lower()
    if ext in AUDIO_ONLY_EXT:
        info = dict(info, video=None)  # an audio file out: drop the picture
    if info["video"] is None and (burn or reframe):
        raise RuntimeError("--burn and --reframe need a picture: the source has no "
                           "video, or the output is an audio-only file")
    if info["video"] is not None and ext == ".webm":
        raise ValueError("a .webm video needs a VP9 re-encode this script does not do; "
                         "write .mp4, .mov or .mkv (or .opus/.ogg for audio only)")
    fin, cap = style["finish"], dict(style["captions"])
    cap["keywords"] = list(cap.get("keywords", [])) + keywords
    report = {"source": os.path.basename(src), "output": os.path.basename(dst),
              "steps": [], "warnings": []}
    all_words = words
    if words:
        # Interjections nobody's ASR heard (another speaker's "Yeah") are talk for
        # the receipt but never caption text or a clip edge.
        words = [w for w in words if w.get("caption", True)] or None

    total = info["duration_s"]
    clip_start, clip_end = clip if clip else (0.0, total)
    if clip and (clip_start >= total or clip_end <= clip_start):
        raise ValueError(f"--clip {clip_start}-{clip_end} is outside the "
                         f"{total:.2f}s source")
    if clip and clip_end > total + 0.05:
        report["warnings"].append(f"--clip ends at {clip_end:g}s but the source is "
                                  f"{total:.2f}s long; the clip stops at the end")
    clip_end = min(clip_end, total)
    levels = LevelRuns(src, style, info)
    in_word = style["qa"]["pauses"].get("silence_in_word_s", 0.4)
    if clip and words:
        words, clip_start, clip_end = place_clip(levels, words, clip_start, clip_end,
                                                 fin["head_pad_s"], in_word, report)
    start = clip_start
    if trim_head:
        # The hook rule is about the first WORD: with a transcript, cut to it.
        def first_in(ws):
            return next((w for w in (ws or [])
                         if w["start"] >= clip_start - 0.02 and w["start"] < clip_end), None)
        first_word = first_in(words)
        if first_word is not None:
            # A first word stretched back over the dead air starts after it.
            words = clamp_stretched(words, levels.near(first_word["start"]), in_word)
            first_word = first_in(words)
        if first_word is not None:
            fw = first_word["start"]
            start = max(clip_start, fw - fin["head_pad_s"])
            report["trim_head_to"] = "first word"
            if fw - clip_start > 1.0:
                # Never cut talk the transcript missed (an opening under room
                # chatter): sound that starts earlier and runs into the first word
                # without 2 s of silence is kept and reported. A lone short sound
                # with a pause after it (a cough, a breath, a click) is not talk
                # running into the word: it is cut, and reported.
                # Measure with some talk after the first word in the window, so the
                # level rules have talk to compare the head against.
                fs, _, head = first_speech_s(src, style, clip_start,
                                             min(fw - clip_start + 5.0, clip_end - clip_start,
                                                 120.0),
                                             info["audio"]["sample_rate"], until=fw)
                pause = style["qa"]["pauses"]["fail_pause_s"]
                if isinstance(head, dict):
                    for at, snd, after in head["isolated"]:
                        report["warnings"].append(
                            f"trim-head cut a {snd:.2f}s sound at {at:.2f}s before the first "
                            f"word ({after:.1f}s of silence after it): a cough, a breath, a "
                            "click, or a lone word the transcript missed; listen")
                    ts = head["start"]
                else:
                    ts = None
                if fs is None and str(head).startswith("the start cannot be told"):
                    # A bed or crowd as loud as talk hides whether the speaker is
                    # already talking under it: cut nothing rather than guess.
                    start = clip_start
                    report["trim_head_to"] = "nothing (noise or music hides the start)"
                    report["warnings"].append(
                        f"trim-head cut nothing: sound as loud as talk runs from "
                        f"{clip_start:.2f}s to the first transcribed word at {fw:.2f}s, "
                        "so talk the transcript missed could be under it; listen")
                elif ts is not None and ts < fw - 0.5 and head["gap"] < pause:
                    start = max(clip_start, ts - fin["head_pad_s"])
                    report["trim_head_to"] = "first sustained sound before the first word"
                    report["warnings"].append(
                        f"trim-head kept {fw - ts:.1f}s of sound before the first "
                        f"transcribed word ({ts:.2f}s to {fw:.2f}s): talk the transcript "
                        "missed, or an intro; listen before publishing")
            if report["trim_head_to"] == "first word":
                # Onto the word's sound, not its clock (audit round 9: "Minnesota"
                # timed 0.24 s after it began; the cut landed inside it).
                nxt = min((w["start"] for w in words if w["start"] > fw + 0.01),
                          default=None)
                settled, _ = settle_start(levels.near(fw), fw, clip_start, start,
                                          fin["head_pad_s"], floor=clip_start, nxt=nxt)
                if settled != start:
                    report["trim_head_settled_on_sound"] = round(settled, 3)
                start = settled
        else:
            fs, skipped, why = first_speech_s(src, style, clip_start,
                                              min(clip_end - clip_start, 120.0),
                                              info["audio"]["sample_rate"])
            if fs is None:
                report["warnings"].append(f"trim-head: {why} in the window; nothing "
                                          "trimmed (give --words or --srt to cut to "
                                          "the first word)")
            else:
                start = max(clip_start, fs - fin["head_pad_s"])
                report["trim_head_to"] = "first sustained sound"
                for sk in skipped:
                    what = ("with no voice in it (typing, clicks or noise)"
                            if sk.get("no_voice") else
                            f"followed by {sk['silence_after_s']}s of silence")
                    report["warnings"].append(
                        f"trim-head skipped a {sk['sound_s']}s sound at {sk['at_s']}s "
                        f"{what}; if it was a word, rerun with --words or --srt")
    if levels.measured:
        # The captions and the receipt's words get the same clamped clocks as
        # the edges (else a word clamped onto its sound at the open is left out
        # of the receipt's words, and the hook reads the next one).
        heard_runs = [x for _, _, r in levels.measured for x in r]
        words = clamp_stretched(words, heard_runs, in_word) if words else words
        all_words = clamp_stretched(all_words, heard_runs, in_word) if all_words else all_words
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
    # ffmpeg's loudnorm lands 1.5-2 LU under target on mono when it has to work
    # in dynamic mode (audit round 8: -15.5 LUFS for a -14 target). Every player
    # plays mono on both speakers anyway, so the loudness pass writes that: two
    # identical channels, measured and normalised as stereo.
    mono = loudness and (info["audio"].get("channels") or 0) == 1
    upmix = UPMIX if mono else ""
    if loudness:
        m = measure_loudnorm(src, start, style, duration if (clip or start > 0) else None,
                             pre=upmix)
        pk = m.get("channel_peaks_db") or []
        if not mono and len(pk) == 2 and max(pk) > -60.0 and min(pk) < max(pk) - 30.0:
            # Talk in one channel only (a lav or a camera mic on one input): one
            # ear on earbuds, and loudness reads low (audit round 9). Copy the live
            # channel to both and measure again.
            live = pk.index(max(pk))
            upmix = f"pan=stereo|c0=c{live}|c1=c{live}"
            report["steps"].append({"one_channel_source": True,
                                    "channel_peaks_db": [round(x, 1) for x in pk],
                                    "copied_channel": live + 1})
            m = measure_loudnorm(src, start, style,
                                 duration if (clip or start > 0) else None, pre=upmix)
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
            if upmix:
                afilters.append(upmix)
                report["mono_to_stereo" if mono else "one_channel_to_both"] = True
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
    try:
        return _render(src, dst, style, info, report, fin, cap, words, all_words, burn,
                       reframe,
                       focus_x, clip, start, duration, afilters, loud_on, work, ext)
    finally:
        shutil.rmtree(work, ignore_errors=True)


HDR_TRANSFERS = ("arib-std-b67", "smpte2084")


def tonemap_filter(transfer: str) -> str | None:
    """An ffmpeg filter chain that tone-maps HLG or PQ (BT.2020) to 8-bit SDR
    BT.709, or None when this ffmpeg lacks zscale (libzimg) or tonemap."""
    if not (video_qa.has_filter("zscale") and video_qa.has_filter("tonemap")):
        return None
    return (f"zscale=tin={transfer}:pin=bt2020:min=bt2020nc:t=linear:npl=100,"
            "format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=mobius:desat=0,"
            "zscale=t=bt709:m=bt709:r=tv,format=yuv420p")


def _render(src, dst, style, info, report, fin, cap, words, all_words, burn, reframe,
            focus_x,
            clip, start, duration, afilters, loud_on, work, ext) -> dict:
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
        everything = [w for w in (all_words or words) if w["start"] >= start - 0.05
                      and w["end"] <= start + duration + 0.05]
        out_words = [{**w, "start": max(0.0, w["start"] - start), "end": w["end"] - start,
                      **({"cue_start": w["cue_start"] - start, "cue_end": w["cue_end"] - start}
                         if "cue_start" in w else {})} for w in everything]
        sidecar = Path(dst).with_suffix(".captions.srt")
        if burn:
            srt_text = build_srt(cues, cap)  # the file matches what is on screen
        else:
            side = dict(cap, **style.get("sidecar_captions", DEFAULT_STYLE["sidecar_captions"]))
            side["highlight_numbers"] = False
            srt_text = build_srt(shift_cues(chunk_words(inside, side), start), side)
        # written only after the render succeeds
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
    hdr = str(info["video"].get("transfer") or "") if has_video else ""
    sdr_tags = []
    if reencode and hdr in HDR_TRANSFERS:
        tm = tonemap_filter(hdr)
        if tm:
            # The re-encode is 8-bit H.264: tone-map HDR (an iPhone's HLG, PQ) down
            # to SDR first, so it plays right everywhere, and tag it as SDR.
            vfilters.insert(0, tm)
            sdr_tags = ["-color_primaries", "bt709", "-color_trc", "bt709",
                        "-colorspace", "bt709", "-color_range", "tv"]
            report["hdr_tonemapped"] = hdr
        else:
            report["warnings"].append(
                "HDR source (HLG/PQ) and this ffmpeg has no zscale/tonemap: the re-encode "
                "is 8-bit without tone mapping and may look washed out; export SDR from "
                "the editor first")
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
                 str(fin["x264_crf"]), "-pix_fmt", "yuv420p"] + sdr_tags if reencode
                else ["-c:v", "copy"])
    if afilters:
        cmd += ["-af", ",".join(afilters)]
    cmd += audio_codec_args(dst, info["audio"].get("codec"), fin["audio_bitrate"],
                            copy_ok=not afilters)
    if ext in (".mp4", ".m4a", ".mov"):
        cmd += ["-movflags", "+faststart"]
    # Render beside the destination, then rename: a failed render never leaves a
    # stub file where the finished one should be.
    final = os.path.abspath(dst)
    partial = os.path.join(os.path.dirname(final),
                           f".{os.path.basename(final)}.partial{ext}")
    cmd += [partial]
    res = _run_render(cmd, work, partial)
    out_loud = None
    if loud_on:
        # The AAC encode adds inter-sample peaks the PCM chain never had (audit
        # round 9: -0.1 dBTP on a short clip, +1.1 with a click in a pause, for a
        # -2 dBTP chain). Measure what was written; over the ceiling, render once
        # more with the overshoot plus 0.3 dB taken off the true-peak target.
        ceiling = style["qa"]["loudness"]["true_peak_max_dbtp"]
        out_loud = video_qa.measure_loudness(partial)
        tp = out_loud.get("true_peak_dbtp")
        if tp is not None and tp > ceiling:
            ai = cmd.index("-af") + 1
            m = re.search(r"loudnorm=I=[^:]+:TP=(-?[\d.]+)", cmd[ai])
            if m:
                target = round(float(m.group(1)) - (tp - ceiling) - 0.3, 2)
                cmd[ai] = cmd[ai][:m.start(1)] + f"{target}" + cmd[ai][m.end(1):]
                retry = {"first_dbtp": tp, "target_dbtp": target}
                # ffmpeg's own AAC encoder overshoots on transients at 192k and
                # under (rh_1872: -2.0 dBTP chain, -0.1 at 192k, -2.0 at 256k).
                if "-b:a" in cmd and cmd[cmd.index("-c:a") + 1] == "aac":
                    bi = cmd.index("-b:a") + 1
                    if _kbps(cmd[bi]) < 320:
                        retry["bitrate"] = cmd[bi] = "320k"
                res = _run_render(cmd, work, partial)
                out_loud = video_qa.measure_loudness(partial)
                retry.update(final_dbtp=out_loud.get("true_peak_dbtp"),
                             final_lufs=out_loud.get("integrated_lufs"))
                report["true_peak_retry"] = retry
    os.replace(partial, final)
    if words:
        sidecar.write_text(srt_text, encoding="utf-8")
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
    report["_out_loudness"] = out_loud
    return report


def _kbps(rate: str) -> float:
    m = re.fullmatch(r"(\d+(?:\.\d+)?)([kKmM]?)", rate.strip())
    if not m:
        return 0.0
    return float(m.group(1)) * {"": 0.001, "k": 1, "K": 1, "m": 1000, "M": 1000}[m.group(2)]


def _run_render(cmd: list[str], work: Path, partial: str) -> subprocess.CompletedProcess:
    res = subprocess.run(cmd, cwd=work, capture_output=True, text=True, errors="replace")
    if res.returncode != 0 or not os.path.exists(partial):
        if os.path.exists(partial):
            os.remove(partial)
        raise RuntimeError("render failed: " + video_qa.first_error(res.stderr))
    return res


def load_words(args) -> list[dict] | None:
    timed = text = None
    if args.words:
        timed = read_words_file(args.words)
        if not timed:
            raise ValueError(f"--words {args.words} holds no words")
    if args.srt:
        text = read_srt_file(args.srt)
        if not text:
            raise ValueError(f"--srt {args.srt} holds no words; check the file and "
                             "its encoding")
    if timed and text:
        return align_text_to_timing(text, timed, keep_unheard=True)
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
        if args.reframe and not (re.fullmatch(r"\d+(?:\.\d+)?:\d+(?:\.\d+)?", args.reframe)
                                 and all(float(x) > 0 for x in args.reframe.split(":"))):
            raise ValueError(f"--reframe must look like 9:16 with both sides above 0, "
                             f"got {args.reframe!r}")
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
        out_loud = rep.pop("_out_loudness", None)
        if not args.no_qa:
            qa = video_qa.qa(args.out, style["qa"], Path(args.out + ".qa"),
                             words=out_words, loud=out_loud)
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
