#!/usr/bin/env python3
"""Word-level timestamps for captions, on this machine or via ElevenLabs Scribe.

WHY TWO BACKENDS (23 Oct 2026)
- `local` (faster-whisper, free, offline): good enough to place captions. Whisper
  quietly drops "um"/"uh" and smooths false starts, which makes clean captions
  and a WRONG basis for deciding where to cut. Never feed it to a filler pass.
- `scribe` (ElevenLabs Scribe v2, $0.22 per audio hour on elevenlabs.io/pricing/api,
  Oct 2026): a verbatim transcript that keeps fillers, which is what an agent
  needs when IT (not Descript) chooses the cuts. This script keeps only the word
  entries; Scribe's spacing and audio-event entries are dropped, and no speaker
  diarization is requested. Needs ELEVENLABS_API_KEY; never paste the key into
  chat or files. Untested here without a key: verify the first response.
Descript already transcribes everything it imports, and its export_transcript
srt has the right WORDS. It does not have word TIMES: an SRT spreads each cue's
words evenly. Give both to finish.py / video_qa.py (--srt descript.srt --words
words.json): captions keep Descript's words on this script's clock, and the QA
receipt can tell a breath or a cough inside dead air from a word (24 Oct 2026;
66 s for a 3-minute slice with small.en on two cores).

Usage:
    transcribe_words.py MEDIA -o words.json [--backend local|scribe]
                        [--model small.en] [--start 0 --end 0]

Output: {"backend": ..., "words": [{"word","start","end"}...]} with times on the
MEDIA timeline (offset by --start when a window is used). Cached: if -o exists
and was made from the same media + window, it is reused, never re-transcribed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile


def media_key(path: str, start: float, end: float) -> str:
    st = os.stat(path)
    return hashlib.sha256(f"{os.path.abspath(path)}|{st.st_size}|{int(st.st_mtime)}|"
                          f"{start}|{end}".encode()).hexdigest()[:16]


def extract_audio(path: str, start: float, end: float) -> str:
    fd, wav = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
    if start:
        cmd += ["-ss", str(start)]
    if end:
        cmd += ["-t", str(end - start)]
    cmd += ["-i", path, "-vn", "-ac", "1", "-ar", "16000", wav]
    subprocess.run(cmd, check=True)
    return wav


def local_words(wav: str, model_name: str) -> list[dict]:
    import wave

    import numpy as np
    from faster_whisper import WhisperModel  # optional dependency
    # Decode the 16 kHz mono wav ourselves: faster-whisper's own decoder depends on
    # a PyAV version that drifts (Oct 2026: open() rejected metadata_errors).
    with wave.open(wav, "rb") as fh:
        pcm = np.frombuffer(fh.readframes(fh.getnframes()), dtype=np.int16)
    audio = pcm.astype(np.float32) / 32768.0
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(audio, word_timestamps=True, vad_filter=True,
                                   condition_on_previous_text=False)
    return [{"word": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)}
            for seg in segments for w in (seg.words or []) if w.word.strip()]


def scribe_words(wav: str) -> list[dict]:
    import urllib.request
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        raise RuntimeError("ELEVENLABS_API_KEY is not set")
    boundary = "----lss" + hashlib.md5(wav.encode()).hexdigest()
    with open(wav, "rb") as fh:
        audio = fh.read()
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"model_id\"\r\n\r\n"
            f"scribe_v2\r\n--{boundary}\r\nContent-Disposition: form-data; "
            f"name=\"timestamps_granularity\"\r\n\r\nword\r\n--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"file\"; filename=\"a.wav\"\r\n"
            f"Content-Type: audio/wav\r\n\r\n").encode() + audio + \
        f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request("https://api.elevenlabs.io/v1/speech-to-text", data=body,
                                 headers={"xi-api-key": key, "Content-Type":
                                          f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=600) as resp:
        data = json.load(resp)
    return [{"word": w["text"].strip(), "start": w["start"], "end": w["end"]}
            for w in data.get("words", []) if w.get("type") == "word" and w["text"].strip()]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("media")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--backend", choices=["local", "scribe"], default="local")
    ap.add_argument("--model", default="small.en")
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float, default=0.0)
    args = ap.parse_args(argv)
    key = media_key(args.media, args.start, args.end)
    if os.path.exists(args.out):
        with open(args.out, encoding="utf-8") as fh:
            cached = json.load(fh)
        if cached.get("media_key") == key and cached.get("backend") == args.backend:
            print(f"cached: {args.out} ({len(cached['words'])} words)")
            return 0
    try:
        wav = extract_audio(args.media, args.start, args.end)
    except subprocess.CalledProcessError as exc:
        print(f"could not read audio from {args.media}: {exc}", file=sys.stderr)
        return 2
    try:
        words = local_words(wav, args.model) if args.backend == "local" else scribe_words(wav)
    except Exception as exc:  # network, key, model download: report, never pretend
        print(f"transcription failed ({args.backend}): {exc}", file=sys.stderr)
        return 2
    finally:
        os.unlink(wav)
    for w in words:
        w["start"] = round(w["start"] + args.start, 3)
        w["end"] = round(w["end"] + args.start, 3)
    out = {"backend": args.backend, "model": args.model if args.backend == "local"
           else "scribe_v2", "media_key": key, "window": [args.start, args.end],
           "verbatim_fillers": args.backend == "scribe", "words": words}
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(f"wrote {args.out} ({len(words)} words, backend {args.backend})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
