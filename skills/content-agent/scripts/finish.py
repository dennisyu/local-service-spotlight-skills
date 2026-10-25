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
    Descript's corrected words on the ASR's word clock (best of each). A --clip
    edge asked for at a pause (inside a level silence of 0.15 s or more, or
    within 0.25 s of one) stays in that pause, head_pad_s from the sound beside
    it, whatever the word clocks say: an ASR clocks words up to 1.4 s early
    into the pause before them. Under steady room noise the silence threshold
    rises and swallows a word's soft ending (and, less, its onset), so there
    the end keeps the checker's noise slack (0.025 s per dB of rise, at most
    0.5 s) or runs to the last word's own cue or clock end when that is
    nearer, and the start keeps up to 0.15 s: under fans, AC and hum 11 to 23
    dB under the talk, 0 of 30 clip ends lose talk (1, flagged, under the
    loudest fan), against 11 to 25 of 30 before (audit round 11). Words the
    ASR heard inside the level's "pause", on the clip's side of the edge, are
    talk the level missed (soft words under an AC read as silence; round 12):
    the pause starts after them (ends before them at the head), and with too
    little left the edge is treated as mid-phrase. A heard word there with no
    sound of its own (its loudest 10 ms within 5 dB of the pause's noise) is a
    clock error instead: when unheard talk sits just beyond the pause and the
    word's neighbour claims the sound on the clip's side, that talk is the
    word, the edge goes into the pause beyond it, and the report notes it
    (Whisper put "But" 0.6 s late into the silence after it was said, in the
    fresh sweep after round 12). The level itself is read
    with the words, as the receipt reads it, so a short word is not a click.
    When Descript's cue end (or, under noise, the ASR's word end) of the last
    word still lies more than 0.15 s past the cut, the report says so; without
    cue times the last word is never one that starts at or after the
    requested END. An edge asked for mid-phrase snaps to word
    boundaries, keeping whole a word it falls inside, then moves onto the sound
    itself (a word whose clock starts in 0.4 s or more of silence was stretched
    back over a pause and starts after it; a word clocked inside a pause, whose
    next word claims the sound after it, is the sound before it): the start
    into the pause of 0.15 s or more before the first word's sound, the end
    into the first pause after the last word's (never past a neighbouring
    word). Where talk runs on with no such pause, the edge stays on the word
    clock: a cut inside a heard word's clock, or in a gap between heard words
    under 0.25 s, is a warning; a cut in a clearer gap that a bed or room
    noise hides from the level goes to the middle of that gap (at most 0.5 s
    from the word: ASR clocks end words early) and is a note (`notes` in the
    report). The first
    and last caption land on the clip's sound, not a late or early clock.
    Every warning the report carries (all but the dynamic-mode note) also
    reaches the QA receipt (`finish_report`), so a PASS never hides a
    mid-phrase cut; the notes and the dynamic-mode note reach it as a
    `finish_note` NOTE. Captions are
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
    "Google Maps:" is not dropped, unless in a labelled file the next named
    cue opens with an established speaker (a second voice's single "Amy:
    Yeah."); sentence openers such as "Update:", "Pro Tip:", "Monday:" or
    "Price:" stay text however often they recur. A file whose first cue
    opens with any other capitalised word and a colon ("Bloomington:") reads as
    labelled, and that word is dropped where it opens a cue: the text alone
    cannot tell it from a speaker's name. Exporting the SRT with
    include_speaker_labels "off" avoids the question.

    The sidecar .captions.srt for long-form reads like sentences (up to 16 words,
    two lines of 42 characters, normal case); with --burn it matches what is on
    screen. When the picture is re-encoded, an HDR source (an iPhone's HLG, PQ)
    is tone-mapped to SDR BT.709 first and tagged that way (needs ffmpeg with
    zscale; without it the report warns). A burned caption with a token too
    wide for the frame (a domain name in 9:16) is shrunk until it fits.

    --loudness on a mono source writes two identical channels: ffmpeg's loudnorm
    lands 1.5-2 LU short on mono when it has to work in dynamic mode, and every
    player plays mono on both speakers anyway. A stereo source gets its louder
    channel copied to both when the other is 30 dB or more down (talk on one
    input), 15 dB or more down with no talk of its own (a wireless mic's -20 dB
    safety track, a camera's scratch mic), or the same voice polarity-inverted
    (it cancels when a phone plays mono); two channels that EACH carry a
    second or more of talk of their own (one lav per input, split mode) are
    folded to the centre. "Talk of its own" is phrases where that channel is at
    its talk level and the other sits 20 dB or more under its own
    (video_qa.channel_roles); in one channel only it is also what wide stereo
    music looks like, so that alone changes nothing. The loudness pass then measures the file it wrote and
    renders again, twice at most: over the true-peak ceiling (ffmpeg's own AAC
    encoder overshot transients by up to 2 dB at 192k), first at 320k, then
    with the overshoot plus 0.3 dB off the target; more than 0.5 LU from the
    target (loudnorm's dynamic mode lands short on peaky or one-sided audio),
    with the target raised by the shortfall, unless a raise did not bring it
    0.3 LU nearer. It keeps the render nearest the target under the ceiling, and says
    so when it still misses. AAC is 256k by default.

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
                 "the", "a", "my", "our", "your", "this", "that", "one", "two", "three",
                 # Audit round 11: "Monday:" and "Price:" opening two cues each were
                 # read as speakers. (April, May, June and August are names too.)
                 "monday", "tuesday", "wednesday", "thursday", "friday", "saturday",
                 "sunday", "january", "february", "march", "july", "september",
                 "october", "november", "december", "morning", "afternoon", "evening",
                 "tonight", "weekend", "price", "prices", "pricing", "cost", "costs",
                 "date", "time", "when", "where", "who", "location", "address", "phone",
                 "email", "website", "hours", "deadline", "budget", "total", "status",
                 "agenda", "topic", "q", "faq", "option", "options", "offer", "deal",
                 "sale", "discount", "free", "new", "also", "then", "later", "info",
                 "details", "contact", "warning", "tldr", "spoilers", "sponsor"}


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
    two or more cues (not a sentence opener such as "Update:", "Monday:" or
    "Price:"); and in a file whose first cue opens with a name label
    (Descript's default export labels the first cue and every change of
    speaker), that first name wherever it opens a cue, and a one- or two-word
    name opening a cue once when the next named cue opens with an established
    speaker (a second voice's "Amy: Yeah." between two "Dennis:" cues).
    "Remember:" or "Google:" at the start of one line of an unlabelled file
    stays text, and so does "Google Maps:" once where no established speaker
    follows."""
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
    openers: list = []  # (block index, name) for every cue that opens "Name:"
    first_label = None  # the name opening the file's first cue, "" when none
    for bi, block in enumerate(blocks):
        b = body_of(block)
        if b is None:
            continue
        m = LOOSE_LABEL.match(b)
        if m:
            key = m.group(1).strip().lower()
            seen[key] = seen.get(key, 0) + 1
            openers.append((bi, m.group(1).strip()))
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

    def established(name: str) -> bool:
        return (speaker(name) and seen.get(name.lower(), 0) >= 2) or \
            (labelled and name.lower() == first_label.lower())

    def label_end(body: str, bi: int) -> int:
        sure = SURE_LABEL.match(body)
        if sure:
            return sure.end()
        m = LOOSE_LABEL.match(body)
        if not m:
            return 0
        name = m.group(1).strip()
        if seen.get(name.lower(), 0) >= 2 and speaker(name):
            return m.end()
        # A labelled file's first-cue name is a label even where it opens a cue
        # once (Descript's default export labels cue 1 only). Any other name
        # must open two or more cues: "Google Maps:" once is text (audit round 9)
        # unless, in a labelled file, the next cue that opens with a name opens
        # with an established speaker: Descript labels every change of speaker,
        # so a second voice's one "Amy: Yeah." is followed by the first voice's
        # label coming back (audit round 11).
        if labelled and name.lower() == first_label.lower():
            return m.end()
        if labelled and speaker(name) and len(name.split()) <= 2:
            nxt = next((n for i, n in openers if i > bi), None)
            if nxt is not None and nxt.lower() != name.lower() and established(nxt):
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
        body = body[label_end(body, cue_id):]
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
            # (the SRT's cue times ride along: a gap between cues is where the
            # SRT heard nobody talk)
            out += [{"word": t["word"], "start": s["start"], "end": s["end"],
                     "timing": "word", "heard": True,
                     **({k: t[k] for k in ("cue_start", "cue_end") if k in t})}
                    for t, s in zip(span, timed[b0:b1])]
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


FOLD3 = "pan=3.0|c0=c0|c1=c1|c2=0.5*c0+0.5*c1"


def measure_loudnorm(path: str, start: float, style: dict,
                     duration: float | None = None, pre: str = "",
                     stereo: bool = False) -> dict:
    """loudnorm's first-pass measurement, plus per-channel peak and RMS from
    astats; for a stereo source also the mono fold-down's RMS, from which the
    correlation of the two channels follows (same voice, unrelated, inverted)."""
    lp = style["qa"]["loudness"]
    stats = f"{FOLD3},astats,pan=stereo|c0=c0|c1=c1" if stereo else "astats"
    flt = (f"{pre + ',' if pre else ''}{stats},loudnorm=I={lp['target_lufs']}:"
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
    ch = astats_channels(res.stderr)
    out["channel_peaks_db"] = [c["peak"] for c in ch[:2 if stereo else None]]
    out["channel_rms_db"] = [c["rms"] for c in ch[:2 if stereo else None]]
    if stereo and len(ch) == 3:
        out["channel_corr"] = channel_corr(ch[0]["rms"], ch[1]["rms"], ch[2]["rms"])
    return out


def astats_channels(stderr: str) -> list[dict]:
    """Per-channel peak and RMS dBFS from ffmpeg astats' summary (-120 for silence)."""
    out, cur = [], None
    for line in stderr.splitlines():
        if re.search(r"\bChannel: \d+", line):
            cur = {"peak": -120.0, "rms": -120.0}
            out.append(cur)
        elif re.search(r"\bOverall\b", line):
            cur = None
        elif cur is not None:
            m = re.search(r"(Peak|RMS) level dB: (\S+)", line)
            if m:
                v = m.group(2)
                cur["peak" if m.group(1) == "Peak" else "rms"] = \
                    -120.0 if "inf" in v else max(-120.0, float(v))
    return out


def astats_peaks(stderr: str) -> list[float]:
    """Per-channel peak dBFS from ffmpeg astats' summary (-120 for a silent channel)."""
    return [c["peak"] for c in astats_channels(stderr)]


def channel_corr(l_db: float, r_db: float, m_db: float) -> float | None:
    """Correlation of two channels from their RMS and the RMS of (L+R)/2:
    1 = the same signal at any gain (a backup track), 0 = unrelated, -1 = one
    channel polarity-inverted (it cancels when a phone plays mono)."""
    pl, pr, pm = (10 ** (x / 10.0) for x in (l_db, r_db, m_db))
    if pl <= 1e-12 or pr <= 1e-12:
        return None
    return max(-1.0, min(1.0, (4 * pm - pl - pr) / 2.0 / (pl * pr) ** 0.5))


class Runs(list):
    """Level runs [(kind, start, end)] plus where the silence threshold had to
    rise over room noise (`raised(t)`, dB over the stretch's base threshold)."""

    def __init__(self, runs=(), base: float = 0.0, thresholds=None, block_s: float = 0.0,
                 base_db: float | None = None, peaks=None, window_s: float = 0.01):
        super().__init__(runs)
        self.base, self.thresholds, self.block_s = base, list(thresholds or []), block_s
        self.base_db, self.peaks, self.window_s = base_db, list(peaks or []), window_s

    def floor(self, a: float, b: float) -> float | None:
        """The median 10 ms peak level inside [a, b]: the pause's own noise."""
        i = max(0, int(round((a - self.base) / self.window_s)))
        j = min(len(self.peaks), int(round((b - self.base) / self.window_s)))
        seg = sorted(self.peaks[i:j])
        return seg[len(seg) // 2] if seg else None

    def _span(self, a: float, b: float) -> range:
        i = max(0, int(round((a - self.base) / self.window_s)))
        j = min(len(self.peaks), max(i + 1, int(round((b - self.base) / self.window_s))))
        return range(i, j)

    def loudest(self, a: float, b: float) -> float | None:
        """The loudest 10 ms peak inside [a, b]."""
        seg = [self.peaks[k] for k in self._span(a, b)]
        return max(seg) if seg else None

    def floor_besides(self, a: float, b: float, spans: list[tuple]) -> float | None:
        """The pause [a, b]'s own noise (median 10 ms peak) outside `spans`."""
        skip = {k for x, y in spans for k in self._span(x, y)}
        seg = sorted(self.peaks[k] for k in self._span(a, b) if k not in skip)
        return seg[len(seg) // 2] if seg else None

    def raised(self, t: float) -> float:
        if not self.thresholds or self.base_db is None or self.block_s <= 0:
            return 0.0
        i = min(len(self.thresholds) - 1, max(0, int((t - self.base) / self.block_s)))
        return max(0.0, self.thresholds[i] - self.base_db)


def level_runs(path: str, style: dict, info: dict, a: float, b: float,
               words: list[dict] | None = None) -> "Runs":
    """Silence (0), sound (1) and unmeasurable (2) runs of [a, b] on the source
    clock, by the QA checker's level rules. With `words`, a short sound where
    a heard word sits is not a click, as in the receipt (audit round 12: a
    70 ms "do" under an AC was bridged into the pause after it)."""
    a = max(0.0, a)
    a_rel = 0.0
    if info["audio"] and info.get("video"):
        a_rel = max(0.0, info["audio"]["start_s"] - info["video"]["start_s"])
    base = max(a, a_rel)
    talk = [(max(0.0, x - base), y - base)
            for x, y in video_qa.pinned_talk(words, style["qa"]["pauses"])
            if y > a and x < b] if words else None
    loud = video_qa.measure_loudness(path, a, b - a)
    aud = video_qa.analyze_audio(path, style["qa"], a, b - a, info["audio"]["sample_rate"],
                                 loud.get("integrated_lufs"), talk=talk)
    return Runs([(k, base + x, base + y) for k, x, y in aud["runs"]], base,
                aud.get("thresholds"), (aud.get("block") or 1) * aud.get("window_s", 0.01),
                aud.get("noise", {}).get("base_threshold_db"), aud.get("peaks"),
                aud.get("window_s", 0.01))


def noise_slack(runs, t0: float, t1: float, style: dict) -> float:
    """How far a soft word end or start can hide under a threshold raised over
    room noise in the pause [t0, t1]: the checker's own slack (0.025 s per dB
    of rise, at most 0.5 s). Zero where the threshold did not rise, or where
    the pause itself is quiet (the rise came from music or talk next to it, and
    a soft word end shows plainly over a quiet pause)."""
    raised = getattr(runs, "raised", None)
    if raised is None or not style:
        return 0.0
    pp = style["qa"]["pauses"]
    r = max(raised(t0), raised(t1))
    fl = runs.floor(t0 + 0.02, t1 - 0.02) if hasattr(runs, "floor") else None
    if r <= 0.0 or fl is None or runs.base_db is None or fl < runs.base_db - 3.0:
        return 0.0
    return min(float(pp.get("noise_slack_max_s", 0.5)),
               float(pp.get("noise_slack_s_per_db", 0.025)) * r)


def cut_in_pause(x: float, y: float, side: str, pad: float, slack: float,
                 word: dict | None = None) -> float:
    """Where a cut goes in the pause [x, y] (the level's silence): pad after
    the sound before it (side "end") or before the sound after it ("start").
    Under room noise the threshold rises and swallows a word's soft ending
    (audit round 11: "this." lost under a fan 22 dB down, the receipt clean),
    so there the sound is taken to run `slack` into the pause, and to the
    edge word's own clock or cue end when that lies within reach; the cut
    still keeps clear of the sound on the far side, by the same margin."""
    if slack <= 0.0:
        return min(y, x + pad) if side == "end" else max(x, y - pad)
    mid = (x + y) / 2.0
    if side == "end":
        tail = x + slack
        for t in ((word or {}).get("cue_end"), (word or {}).get("end")):
            if t is not None and tail < t <= x + 2 * slack + 0.3:
                tail = t
        hi = max(mid, y - slack - pad)
        return min(y, max(x + pad, min(hi, tail + pad)))
    # A word's onset is sharper than its ending: a soft start hides under the
    # raised threshold for far less time (round 11: 0 to 3 of 30 starts lost
    # under fans, AC and hum, against 11 to 25 of 30 ends), and the slack before
    # it is dead air (or an intro's music) at the head of the clip.
    sl = min(slack, 0.15)
    lo = min(x + slack + pad, mid)
    return max(x, min(y - pad, max(lo, y - sl - pad)))


def settle_start(runs: list[tuple], fw: float, lo: float, start: float,
                 pad: float, min_sil: float = 0.15,
                 floor: float | None = None,
                 nxt: float | None = None, style: dict | None = None) -> tuple[float, bool]:
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
    before the pause. Under room noise (`style` given) the cut keeps the
    checker's noise slack before the sound (cut_in_pause). Returns (cut,
    found), found False when the word sits inside a second or more of
    unbroken sound."""
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
    sl = noise_slack(runs, x + 0.01, y - 0.01, style) if style else 0.0
    cut = max(cut_in_pause(x, y, "start", pad, sl), floor if floor is not None else x)
    in_sound = any(k != 0 and a <= start < b for k, a, b in runs)
    return (cut if cut < start or in_sound else start), True


def settle_end(runs: list[tuple], lw: float, hi: float, end: float, pad: float,
               min_sil: float = 0.15, style: dict | None = None) -> tuple[float, bool]:
    """Put a cut after the last word in the silence after its SOUND (an ASR ends
    a word early: "foundation." lost 0.6 s). The silence is the first one of
    min_sil or more that ends after the word's clock end (lw) and starts within
    a second after it or earlier, and before `hi` (the next word's start): the
    word's sound ends where it starts. The cut lands inside it, pad after that
    sound; a cut already in that silence stays. Under room noise (`style`
    given) the word's sound runs on by the checker's noise slack, or to its
    clock end when that lies within reach (cut_in_pause). Returns (cut,
    found)."""
    sil = [(x, y) for k, x, y in runs if k == 0 and y - x >= min_sil]
    cands = [(x, y) for x, y in sil
             if y >= lw - 0.02 and x <= min(lw + 1.0, hi + 0.05)]
    if not cands:
        return end, False
    x, y = min(cands, key=lambda s: s[0])
    sl = noise_slack(runs, x + 0.01, y - 0.01, style) if style else 0.0
    cut = cut_in_pause(x, y, "end", pad, sl, {"end": lw})
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

    def __init__(self, src: str, style: dict, info: dict, words: list[dict] | None = None):
        self.src, self.style, self.info = src, style, info
        self.words = words
        self.total = info["duration_s"]
        self.measured: list = []

    def near(self, t: float) -> list[tuple]:
        for a, b, r in self.measured:   # 1.5 s each side, or the file's own edge
            if (a + 1.5 <= t or a <= 0.0 <= t) and \
                    (t <= b - 1.5 or t <= b >= self.total - 0.01):
                return r
        a, b = max(0.0, t - 5.0), min(self.total, t + 5.0)
        r = level_runs(self.src, self.style, self.info, a, b, self.words)
        self.measured.append((a, b, r))
        return r


def edge_pause(runs: list[tuple], t: float, side: str, reach: float = 0.25,
               min_sil: float = 0.15) -> tuple[float, float] | None:
    """The level silence (min_sil or more) a requested clip edge sits in, or
    that ends within `reach` before a start (begins within `reach` after an
    end): the editor picked that pause. None when the edge is mid-phrase."""
    sil = [(x, y) for k, x, y in runs if k == 0 and y - x >= min_sil]
    if side == "start":
        c = [(x, y) for x, y in sil if x <= t + 0.02 and y >= t - reach]
        return max(c, key=lambda s: s[1]) if c else None
    c = [(x, y) for x, y in sil if y >= t - 0.02 and x <= t + reach]
    return min(c, key=lambda s: s[0]) if c else None


def misclocked_pause(runs, pause: tuple, held: list[dict], said: list[dict],
                     side: str, min_sil: float = 0.15):
    """Words the ASR heard inside a level pause are usually soft talk the raised
    threshold missed (place_clip's held words). But a word with no sound of
    its own there (its loudest 10 ms within 5 dB of the pause's noise) is a
    clock error: Whisper put "But" 0.6 s late into the silence after it was
    said (audit round 12's fresh sweep, nz_fan47 at 380.64, the clip opening
    after it). When an unheard talk-level sound sits right beside the pause,
    on the far side from the clip (before it at the head, after it at the
    tail, within 1.2 s of the word, no heard word on it), and the word's
    neighbour claims the sound on the clip's side, that sound is the word.
    Returns the pause beyond it (None when talk runs on there: the edge is
    then mid-phrase), or False when the words are not misclocked."""
    if not held or not getattr(runs, "peaks", None) or not hasattr(runs, "loudest"):
        return False
    x, y = pause
    spans = [(w["start"] - 0.05, w["end"] + 0.05) if w["end"] - w["start"] < 0.05
             else (w["start"], w["end"]) for w in held]
    fl = runs.floor_besides(x, y, spans)
    if fl is None:
        return False
    for a, b in spans:
        pk = runs.loudest(a, b)
        if pk is None or pk > fl + 5.0:
            return False            # sound of its own: soft talk, not a clock error
    others = [w for w in said if not any(w is h for h in held)]
    lo, hi = min(w["start"] for w in held), max(w["end"] for w in held)
    if side == "start":
        snd = [(a, b) for k, a, b in runs if k == 1 and abs(b - x) <= 0.02]
        if not snd:
            return False
        a, b = snd[-1]
        nxt = min((w["start"] for w in others if w["start"] >= hi - 0.02), default=None)
        if a < lo - 1.2 or nxt is None or nxt > y + 0.3:
            return False
    else:
        snd = [(a, b) for k, a, b in runs if k == 1 and abs(a - y) <= 0.02]
        if not snd:
            return False
        a, b = snd[0]
        prv = max((w["end"] for w in others if w["end"] <= lo + 0.02), default=None)
        if b > hi + 1.2 or prv is None or prv < x - 0.3:
            return False
    if b - a < 0.08 or (runs.loudest(a, b) or -120.0) < fl + 15.0:
        return False                # a click or a breath, not a word
    if any(w["start"] < b - 0.02 and w["end"] > a + 0.02 for w in others):
        return False                # a heard word already claims that sound
    sil = [(p, q) for k, p, q in runs if k == 0 and q - p >= min_sil]
    if side == "start":
        c = [(p, q) for p, q in sil if abs(q - a) <= 0.02]
        return max(c, key=lambda s: s[1]) if c else None
    c = [(p, q) for p, q in sil if abs(p - b) <= 0.02]
    return min(c, key=lambda s: s[0]) if c else None


def sound_edges(runs: list[tuple], start: float, end: float) -> tuple:
    """Where the cut's sound starts (the cut itself when it lands in sound) and
    where it stops (the same at the end)."""
    live = [(a, b) for k, a, b in runs if k != 0 and b > start and a < end]
    on = max(live[0][0], start) if live else None
    off = min(live[-1][1], end) if live else None
    return on, off


def place_clip(levels: LevelRuns, words: list[dict], start: float, end: float,
               pad: float, in_word: float, report: dict) -> tuple[list[dict], float, float]:
    """--clip edges. An edge asked for at a pause stays in that pause, pad from
    the sound beside it (audit round 10: the ASR clocks words up to 1.4 s early
    into the pause before them, so snapping to words dropped the first word of
    292 of 598 replay clips cut at a pause). An edge asked for mid-phrase snaps
    to word boundaries (a word the edge falls inside is kept whole), then moves
    onto the words' sound. Returns the words (stretched ones clamped) and the
    clip's start and end."""
    total = levels.total
    rs, re_ = levels.near(start), levels.near(end)
    # A word the ASR stretched back over a pause (its clock starts in in_word s
    # or more of level silence) starts after that silence (the replay's
    # "We're" ran 1.3 s back into the pause before it).
    words = clamp_stretched(words, rs + re_, in_word)
    s_w, e_w = snap_to_words(words, start, end, pad)
    report["clip_snapped_to_words"] = [round(s_w, 3), round(e_w, 3)]
    ps, pe = edge_pause(rs, start, "start"), edge_pause(re_, end, "end")
    # A level "pause" that holds words the ASR heard on the clip's side of the
    # edge is not the editor's pause: under room noise soft talk reads as
    # silence (audit round 12: "what you need to do" under an AC, the END on
    # "do", cut before "need"). The pause starts after those words (ends
    # before them at the head); with too little left, the edge is mid-phrase.
    said = [w for w in words if w.get("timing") != "cue" and w.get("heard", True)]
    heard = [w for w in said if w["end"] > w["start"]]

    def instant_at(w, t):   # Whisper times some words as an instant, on the edge
        return w["end"] - w["start"] < 0.01 and abs(w["start"] - t) <= 0.02
    if pe:
        held = [w for w in said if w["start"] >= pe[0] - 0.02
                and (w["start"] < end - 0.02 or instant_at(w, end))
                and w["end"] <= end + 0.15 and w["end"] > pe[0] + 0.05
                and not ("cue_start" in w and w["cue_start"] >= end - 0.05)]
        moved = misclocked_pause(re_, pe, held, said, "end") if held else False
        if moved is not False:
            # The word's clock ran early into the pause; its sound comes after.
            report.setdefault("notes", []).append(
                "the clip's last word is clocked in silence; its sound is the talk "
                "just after that pause, kept")
            pe = moved
        elif held:
            x2 = max(w["end"] for w in held)
            pe = (x2, pe[1]) if pe[1] - x2 >= 0.15 else None
    if ps:
        held = [w for w in said if w["end"] <= ps[1] + 0.02
                and (w["end"] > start + 0.02 or instant_at(w, start))
                and w["start"] >= start - 0.15 and w["start"] < ps[1] - 0.05
                and not ("cue_end" in w and w["cue_end"] <= start + 0.05)]
        moved = misclocked_pause(rs, ps, held, said, "start") if held else False
        if moved is not False:
            # The word's clock ran late into the pause; its sound came before.
            report.setdefault("notes", []).append(
                "the clip's first word is clocked in silence; its sound is the talk "
                "just before that pause, kept")
            ps = moved
        elif held:
            y2 = min(w["start"] for w in held)
            ps = (ps[0], y2) if y2 - ps[0] >= 0.15 else None
    if ps and ps[1] >= end - 0.1:
        ps = None                       # nothing but the pause would be left
    if pe and pe[0] <= start + 0.1:
        pe = None
    # Which words the clip holds, for its captions and its receipt.
    fw_, lw_ = edge_words(words, start, end)
    if ps:
        fw_ = word_after_pause(words, *ps) or fw_
    if pe:
        lw_ = word_before_pause(words, *pe, end=end) or lw_
    style = getattr(levels, "style", None)
    new_start = (cut_in_pause(*ps, "start", pad, noise_slack(rs, ps[0] + 0.01, ps[1] - 0.01, style),
                              fw_) if ps else s_w)
    new_end = (cut_in_pause(*pe, "end", pad, noise_slack(re_, pe[0] + 0.01, pe[1] - 0.01, style),
                            lw_) if pe else e_w)
    ok_s = ok_e = True
    kept = [w for w in words if w["start"] >= s_w - 0.02
            and w["end"] <= e_w + 0.02 and w["start"] <= e_w]
    if kept and (not ps or not pe):
        # Mid-phrase edges: onto the sound itself, the word clock can be most
        # of a second off. The words the snap kept, zero-length ones included
        # (Whisper times some words as an instant: "Helping." at 2063.12 was
        # spoken from 2062.9).
        fw, lw = min(w["start"] for w in kept), max(w["end"] for w in kept)
        if not ps:
            prev_end = max((w["end"] for w in words if w["end"] <= fw + 0.01
                            and w["start"] < fw), default=0.0)
            nxt = min((w["start"] for w in words if w["start"] > fw + 0.01), default=None)
            # A first word timed as an instant marks where its sound ENDS (the
            # nz fan47 "And" at 472.46 was said from 472.34): look for the
            # silence before that sound, not the one the instant touches.
            fw_s = fw - 0.1 if any(w["start"] == fw and w["end"] - w["start"] < 0.01
                                   for w in kept) else fw
            new_start, ok_s = settle_start(levels.near(fw_s), fw_s, prev_end, s_w, pad,
                                           nxt=nxt, style=style)
        if not pe:
            next_start = min((w["start"] for w in words if w["start"] >= lw - 0.01
                              and w["end"] > lw), default=total)
            new_end, ok_e = settle_end(levels.near(lw), lw, next_start, e_w, pad, style=style)
    for ok, where, moved, cut in ((ok_s, "starts", new_start - start, new_start),
                                  (ok_e, "ends", new_end - end, new_end)):
        if not ok:
            # No level pause, but the cut may still sit in a clear gap between the
            # words the ASR heard: a music bed or room noise hides the pause
            # (audit round 12: 16 of 17 such edges on real public videos kept
            # their words). That is a note; a cut inside a heard word's clock,
            # or in a gap under 0.25 s, is a warning.
            inside = any(w["start"] + 0.01 < cut < w["end"] - 0.01 for w in heard)
            before = max((w["end"] for w in heard if w["end"] <= cut + 0.01), default=None)
            after = min((w["start"] for w in heard if w["start"] >= cut - 0.01), default=None)
            gap = (after - before) if before is not None and after is not None else 0.0
            if not inside and gap >= 0.25:
                # The ASR's word ends run early and its starts late into such a
                # gap (round 12: under a music bed the cut on the clock end plus
                # pad left 0.06 to 0.27 s of the last word's tail out), so the
                # cut goes to the middle of the gap, at most 0.5 s from the word
                # and pad clear of the other.
                if where == "ends":
                    new_end = max(new_end, min(before + gap / 2.0, before + 0.5, after - pad))
                else:
                    new_start = min(new_start, max(after - gap / 2.0, after - 0.5, before + pad))
                report.setdefault("notes", []).append(
                    f"the level shows no pause where the clip {where} (a bed or room noise "
                    f"hides it); the cut sits in the middle of a {gap:.2f}s gap between "
                    "heard words")
                continue
            far = (f" (the cut sits {abs(moved):.2f}s {'after' if moved > 0 else 'before'} "
                   "the requested edge, on a word boundary)" if abs(moved) > 0.5 else "")
            report["warnings"].append(
                f"the clip {where} inside unbroken talk: the requested edge is not at a "
                "pause, and there is no pause of 0.15 s or more within a second of the "
                f"nearest word; the cut lands mid-phrase{far}. Pick an edge at a pause")
    new_start, new_end = max(0.0, new_start), min(total, new_end)
    if (new_start, new_end) != (s_w, e_w):
        report["clip_settled_on_sound"] = [round(new_start, 3), round(new_end, 3)]
    if fw_ is not None and lw_ is not None and lw_["end"] >= fw_["start"]:
        report["clip_word_span"] = [[fw_["word"], fw_["end"]], [lw_["word"], lw_["end"]]]
    if ps or pe:
        report["clip_edges_at_pause"] = [w for w, p in (("start", ps), ("end", pe)) if p]
    def opens_cue(w):   # a cue's own first word carries the cue's start
        return not any(o is not w and o.get("cue_start") == w.get("cue_start")
                       and o["start"] < w["start"] for o in words)

    def closes_cue(w):
        return not any(o is not w and o.get("cue_end") == w.get("cue_end")
                       and o["end"] > w["end"] for o in words)
    if fw_ is not None and fw_.get("cue_start") is not None and opens_cue(fw_) \
            and fw_["cue_start"] < new_start - 0.15 and fw_["end"] > new_start:
        # The mirror at the head: Descript's cue start well before the cut.
        early = new_start - fw_["cue_start"]
        report["clip_first_word_before_cut_s"] = round(early, 2)
        report["warnings"].append(
            f"the clip starts {early:.2f}s after its first word (\"{fw_['word']}\") begins by "
            "Descript's timing; the level shows a pause there, but the word may be cut "
            "short; listen to the start")
    if lw_ is not None:
        # Descript's cue end (and, under room noise, the ASR's word end) past the
        # cut: the last word may be cut short; the level alone cannot tell.
        ref = levels.near(new_end)
        x0 = pe[0] if pe else new_end
        noisy = noise_slack(ref, x0 + 0.01, (pe[1] if pe else new_end + 0.3) - 0.01, style) > 0
        marks = ([lw_.get("cue_end")] if closes_cue(lw_) else []) + \
            ([lw_["end"]] if noisy else [])
        over = max((m - new_end for m in marks if m is not None), default=0.0)
        if over > 0.15:
            report["clip_last_word_past_cut_s"] = round(over, 2)
            report["warnings"].append(
                f"the clip ends {over:.2f}s before its last word (\"{lw_['word']}\") ends by "
                "the transcript's timing; the level shows a pause there, but the word may be "
                "cut short; listen to the end")
    on, _ = sound_edges(levels.near(new_start), new_start, new_end)
    _, off = sound_edges(levels.near(new_end), new_start, new_end)
    report["clip_sound"] = [None if on is None else round(on, 3),
                            None if off is None else round(off, 3)]
    return words, new_start, new_end


def edge_words(words: list[dict], start: float, end: float) -> tuple:
    """The first and last word a cut [start, end] asked for mid-phrase keeps: a
    word the edge falls inside is kept whole (its clock may simply start early),
    one it barely touches (50 ms) is not."""
    def instant(w, t):   # a word timed as an instant, on the edge itself
        return w["end"] - w["start"] < 0.01 and abs(w["start"] - t) <= 0.02
    inside = [w for w in words if (w["end"] > start or instant(w, start))
              and (w["start"] < end or instant(w, end))]
    if not inside:
        return None, None
    first = next((w for w in inside if w["end"] > start + 0.05
                  or w["start"] >= start - 0.02), inside[0])
    last = next((w for w in reversed(inside) if w["start"] < end - 0.05
                 or w["end"] <= end + 0.02), inside[-1])
    # An edge on one of the SRT's cue boundaries (Descript's, the documented
    # way to pick a clip) means that cue's first or last word, wherever the
    # ASR's clock put it (the replay's "If" was clocked 0.25 s before its cue).
    # (not when the aligner put that word's clock more than a second away: it
    # squeezed "Jeff Bezos. Yeah" into the ASR's "2,357.", and the edge moved
    # 1.93 s; audit round 11)
    cue_first = [w for w in words if "cue_start" in w and abs(w["cue_start"] - start) <= 0.05
                 and abs(w["start"] - start) <= 1.0]
    if cue_first:
        first = min(cue_first, key=lambda w: w["start"])
    cue_last = [w for w in words if "cue_end" in w and abs(w["cue_end"] - end) <= 0.05
                and abs(w["end"] - end) <= 1.0]
    if cue_last:
        last = max(cue_last, key=lambda w: w["end"])
    return first, last


def word_after_pause(words: list[dict], x: float, y: float) -> dict | None:
    """The first word spoken after a pause [x, y]. The SRT's cue times say it
    best (an ASR's clocks ran 0.4 s early on the replay's "And so"): the first
    word of a cue starting in or just after the pause; else by the clock."""
    ws = sorted(words, key=lambda w: w["start"])
    cue = [w for w in ws if "cue_start" in w and x - 0.05 <= w["cue_start"] <= y + 0.5]
    if cue:
        return min(cue, key=lambda w: (w["cue_start"], w["start"]))
    return next((w for w in ws if w["end"] > y - 0.1), None)


def word_before_pause(words: list[dict], x: float, y: float,
                      end: float | None = None) -> dict | None:
    """The last word spoken before a pause [x, y] (mirror of word_after_pause).
    Without cue times, not a word that starts at or after the requested `end`:
    the ASR stretched the next sentence's "and" back over the pause (audit
    round 12), and it is not in the clip."""
    ws = sorted(words, key=lambda w: w["start"])
    cue = [w for w in ws if "cue_end" in w and x - 0.5 <= w["cue_end"] <= y + 0.05]
    if cue:
        return max(cue, key=lambda w: (w["cue_end"], w["end"]))
    if end is not None:
        ws = [w for w in ws if w["start"] < end - 0.02]
    return next((w for w in reversed(ws) if w["start"] < x + 0.1), None)


def snap_to_words(words: list[dict], start: float, end: float,
                  pad: float) -> tuple[float, float]:
    """Never cut inside a word: move clip edges to word boundaries, then pad. A
    word the edge falls inside is kept whole (its clock may simply start early)."""
    first, last = edge_words(words, start, end)
    if first is None:
        return start, end
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
    levels = LevelRuns(src, style, info, words)
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
                                          fin["head_pad_s"], floor=clip_start, nxt=nxt,
                                          style=style)
                if settled != start:
                    report["trim_head_settled_on_sound"] = round(settled, 3)
                start = settled
                on, _ = sound_edges(levels.near(fw), start, clip_end)
                report["clip_sound"] = [None if on is None else round(on, 3),
                                        (report.get("clip_sound") or [None, None])[1]]
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
    stereo = (info["audio"].get("channels") or 0) == 2
    upmix = UPMIX if mono else ""
    if loudness:
        span = duration if (clip or start > 0) else None
        m = measure_loudnorm(src, start, style, span, pre=upmix, stereo=stereo)
        pk, rms = m.get("channel_peaks_db") or [], m.get("channel_rms_db") or []
        rho = m.get("channel_corr")
        if stereo and len(pk) == 2 and len(rms) == 2 and max(pk) > -60.0:
            live = rms.index(max(rms))
            why = None
            # What each channel carries on its own (audit round 11: a camera's
            # scratch mic decorrelates to 0.09 by delay and room, so correlation
            # alone cannot call it a backup; a split-mode interview puts each
            # speaker in one ear).
            roles = video_qa.channel_roles(src, start, span, total=info["duration_s"])
            own = (roles or {}).get("own_talk_s") or [0.0, 0.0]
            if min(pk) < max(pk) - 30.0:
                # Talk in one channel only (a lav or a camera mic on one input):
                # one ear on earbuds, and loudness reads low (audit round 9).
                why = "one_channel_source"
            elif rho is not None and rho <= -0.8 and abs(rms[0] - rms[1]) < 6.0:
                # One channel polarity-inverted: the two cancel when a phone or a
                # speaker plays mono, and the transcriber hears nothing.
                why = "inverted_channel"
            elif rms[live] - rms[1 - live] >= 15.0 and roles and own[1 - live] < 1.0:
                # The quieter channel 15 dB or more down carries no talk of its
                # own: a backup or scratch track of the same voice (a wireless
                # mic's -20 dB safety channel, round 10; a camera mic beside a
                # lav, round 11), not a second speaker.
                why = "quiet_backup_channel"
            elif roles and min(own) >= 1.0:
                # Each channel carries talk of its own while the other sits 20 dB
                # or more under its own talk (one lav per input, split mode): each
                # voice in one ear, and loudnorm lands short. Both to the centre.
                # Own "talk" in one channel only is also what wide stereo music
                # looks like (audit round 12), so that alone folds nothing.
                why = "speakers_hard_panned"
            if why:
                upmix = (f"pan=stereo|c0=c{live}|c1=c{live}" if why != "speakers_hard_panned"
                         else "pan=stereo|c0=0.5*c0+0.5*c1|c1=0.5*c0+0.5*c1")
                step = {why: True, "channel_peaks_db": [round(x, 1) for x in pk],
                        "channel_rms_db": [round(x, 1) for x in rms],
                        "channel_corr": None if rho is None else round(rho, 2)}
                if roles:
                    step["own_talk_s"] = own
                if why == "speakers_hard_panned":
                    step["folded_to_centre"] = True
                else:
                    step["copied_channel"] = live + 1
                report["steps"].append(step)
                m = measure_loudnorm(src, start, style, span, pre=upmix)
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


def words_in(words: list[dict], a: float, b: float, sound: list | None = None,
             span: list | None = None) -> list[dict]:
    """The words a cut [a, b] keeps, clipped to it. `span` = [[first word, its
    clock end], [last word, its clock end]], as place_clip chose them, selects
    them exactly; without it, a word counts when most of its clock lies inside
    the cut. With `sound` = [onset, offset] of the cut's audio, head words clocked
    before the onset start on it, a late first clock moves back onto it (audit
    round 10: "LANDSCAPING" burned at 0.92 s for a word said from 0.07 s), and
    the tail mirrors that, all in order."""
    sel = None
    if span:
        # From the first word to the last, in clock order (a zero-length word
        # can share an instant with its neighbour), each found by its text and
        # its clock end (a clamp may move a start, never an end).
        order = [w for _, w in sorted(enumerate(words), key=lambda iw: (iw[1]["start"], iw[0]))]

        def find(key, last=False):
            hits = [i for i, w in enumerate(order)
                    if w["word"] == key[0] and abs(w["end"] - key[1]) < 1e-6]
            return (hits[-1] if last else hits[0]) if hits else None
        i0, i1 = find(span[0]), find(span[1], last=True)
        if i0 is not None and i1 is not None and i1 >= i0:
            sel = order[i0:i1 + 1]
    if sel is None:
        sel = []
        for w in words:
            lo, hi = max(w["start"], a), min(w["end"], b)
            dur = w["end"] - w["start"]
            if (dur <= 0 and a - 0.05 <= w["start"] <= b + 0.05) or \
                    (dur > 0 and hi - lo >= 0.5 * dur):
                sel.append(w)
    out = [dict(w, start=min(max(w["start"], a), b), end=min(max(w["end"], a), b))
           for w in sorted(sel, key=lambda w: w["start"])]
    on, off = (sound or [None, None])[:2]
    if out and on is not None:
        if 0.05 < out[0]["start"] - on < 1.0:
            out[0] = dict(out[0], start=on)
        for i, w in enumerate(out):        # early clocks: nothing starts before the sound
            if w["start"] >= on:
                break
            out[i] = dict(w, start=on, end=max(w["end"], on + 0.05))
    if out and off is not None:
        if 0.05 < off - out[-1]["end"] < 1.0:
            out[-1] = dict(out[-1], end=off)
        for i in range(len(out) - 1, -1, -1):
            w = out[i]
            if w["end"] <= off:
                break
            out[i] = dict(w, end=max(off, w["start"]), start=min(w["start"], off))
    return out


def _settle_loudness(cmd: list[str], work: Path, partial: str, res, style: dict,
                     report: dict, channels: int | None = None) -> tuple:
    """Measure the file the render wrote and render again (twice at most) until
    it sits within 0.5 LU of the target and under the true-peak ceiling.
    ffmpeg's own AAC encoder adds inter-sample peaks the filter chain never had
    (audit round 9: -0.1 dBTP at 192k from a -2.0 dBTP chain): first raise the
    bitrate to 320k, and lower the true-peak target only if that is not enough
    (audit round 10: lowering it at once cost 1.3-1.7 LU). loudnorm's dynamic
    mode lands up to 2 LU short on peaky or one-sided audio (audit round 10: a
    vlog at -15.9 LUFS): raise its target by the shortfall. The render closest
    to the target that is under the ceiling is kept. A raise that does not
    bring the result 0.3 LU nearer the target stops the ladder (audit round
    11: on a short clip under room noise two raises moved -15.1 LUFS to
    -15.2; on another, -15.3 to -15.7 and back to -15.1)."""
    lp = style["qa"]["loudness"]
    ceiling, target = lp["true_peak_max_dbtp"], lp["target_lufs"]
    ext = os.path.splitext(partial)[1]
    cands = [(partial, list(cmd), res, video_qa.measure_loudness(partial))]
    tries = []
    stalled = None
    for k in range(2):
        _, cur, _, mk = cands[-1]
        tp, li = mk.get("true_peak_dbtp"), mk.get("integrated_lufs")
        ai = cur.index("-af") + 1
        m = re.search(r"loudnorm=I=(-?[\d.]+):TP=(-?[\d.]+)", cur[ai])
        if not m or li is None:
            break
        nxt, step = list(cur), {}
        if tp is not None and tp > ceiling:
            step["reason"] = f"true peak {tp:g} dBTP over {ceiling:g}"
            bi = nxt.index("-b:a") + 1 if "-b:a" in nxt else None
            if bi and nxt[nxt.index("-c:a") + 1] == "aac" and _kbps(nxt[bi]) < 320:
                nxt[bi] = step["bitrate"] = "320k"
            else:
                tpt = round(float(m.group(2)) - (tp - ceiling) - 0.3, 2)
                nxt[ai] = nxt[ai][:m.start(2)] + f"{tpt}" + nxt[ai][m.end(2):]
                step["tp_target"] = tpt
        elif abs(li - target) > 0.5:
            step["reason"] = f"loudness {li:g} LUFS, {li - target:+.1f} LU from {target:g}"
            it = round(min(-5.0, max(-70.0, float(m.group(1)) + (target - li))), 2)
            nxt[ai] = nxt[ai][:m.start(1)] + f"{it}" + nxt[ai][m.end(1):]
            step["i_target"] = it
        else:
            break
        out = os.path.join(os.path.dirname(partial),
                           f".{os.path.basename(partial)}.{k + 1}{ext}")
        nxt[-1] = out
        r = _run_render(nxt, work, out)
        mn = video_qa.measure_loudness(out)
        step.update(lufs=mn.get("integrated_lufs"), dbtp=mn.get("true_peak_dbtp"))
        tries.append(step)
        cands.append((out, nxt, r, mn))
        if "i_target" in step and mn.get("integrated_lufs") is not None \
                and round((mn["integrated_lufs"] - li) * (1 if target > li else -1), 2) < 0.3:
            # Not 0.3 LU nearer the target (or further off): loudnorm's dynamic
            # mode is not steered by its target here; more renders are guesses.
            stalled = round(mn["integrated_lufs"] - li, 1)
            break

    def score(c):
        mm = c[3]
        tp, li = mm.get("true_peak_dbtp"), mm.get("integrated_lufs")
        return (tp is not None and tp > ceiling, abs(li - target) if li is not None else 99.0)
    best = min(cands, key=score)
    for c in cands:
        if c[0] != best[0] and os.path.exists(c[0]):
            os.remove(c[0])
    if tries:
        first = cands[0][3]
        report["loudness_passes"] = {
            "first": {"lufs": first.get("integrated_lufs"), "dbtp": first.get("true_peak_dbtp")},
            "retries": tries, "kept": cands.index(best)}
    if best[0] != partial:
        os.replace(best[0], partial)
    li = best[3].get("integrated_lufs")
    if li is not None and abs(li - target) > lp.get("pass_tolerance_lu", 1.0):
        why = (f"raising loudnorm's target moved it {stalled:+.1f} LU (its dynamic mode "
               "does not follow the target on this audio)" if stalled is not None else
               "ffmpeg's loudness pass cannot lift this audio further without clipping")
        if channels and channels > 2:
            why += "; talk in one channel of a multichannel mix lands short this way"
        report["warnings"].append(
            f"loudness lands at {li:g} LUFS, {li - target:+.1f} LU from {target:g}, after "
            f"{len(cands)} renders: {why}. A compressor or limiter in the editor lets it "
            "reach the target")
    return partial, best[2], best[3]


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
        sound = report.get("clip_sound") or [None, None]
        span = report.get("clip_word_span")
        inside = mark_keywords(words_in(words, start, start + duration, sound, span),
                               cap["keywords"])
        cues = shift_cues(chunk_words(inside, cap), start)
        everything = words_in(all_words or words, start, start + duration, sound, span)
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
        partial, res, out_loud = _settle_loudness(cmd, work, partial, res, style, report,
                                                  (info.get("audio") or {}).get("channels"))
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
                             words=out_words, loud=out_loud,
                             finish_warnings=rep.get("warnings"),
                             finish_notes=rep.get("notes"))
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
