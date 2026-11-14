"""Read the words inside an image, so the do-not-print gate sees what a screenshot shows.

Gate G74 checks the text of audit.json. A screenshot is pixels: on the 2026-11-11 Nik Halik
audit a Google panel screenshot on page 1 showed private family names that were on the
brief's do-not-print list, and G74 could not see them. Gate G75 reads every embedded photo
and screenshot with OCR and searches the words for the same list.

The engine is the Tesseract command line (`tesseract`, from `tesseract-ocr` on Linux or
`brew install tesseract` on a Mac). No Python package is needed. When it is not installed
`engine()` returns None and G75 warns instead of passing, because an unread image is not
a checked image.

OCR is not proof of absence: it misses stylised, tiny, rotated or low-contrast text and
handwriting. The rule stays "crop or redact private fields in screenshots before use";
the gate catches the screenshots where that step was skipped.
"""
from __future__ import annotations

import base64
import binascii
import pathlib
import re
import shutil
import subprocess
import tempfile
from typing import Callable

OcrFn = Callable[[pathlib.Path], str]

# Two page-segmentation passes: 3 reads ordinary blocks of text; 11 finds sparse text
# scattered across a panel (names, labels, buttons), which is what screenshots mostly hold.
PSM_PASSES = ("3", "11")
TIMEOUT_S = 60
_cache: dict[tuple, str] = {}


class OcrError(RuntimeError):
    """The engine ran but could not read this image."""


def engine() -> OcrFn | None:
    """The OCR function to use, or None when no engine is installed."""
    exe = shutil.which("tesseract")
    if not exe:
        return None

    def read(path: pathlib.Path) -> str:
        return tesseract(exe, path)
    read.name = f"tesseract ({exe})"
    return read


def tesseract(exe: str, path: pathlib.Path) -> str:
    """All words Tesseract finds in the image, both passes joined. Cached per file version,
    because the gates run on every draft and fix round."""
    st = path.stat()
    key = (str(path.resolve()), st.st_mtime_ns, st.st_size)
    if key in _cache:
        return _cache[key]
    texts, errors = [], []
    for psm in PSM_PASSES:
        try:
            r = subprocess.run([exe, str(path), "stdout", "--psm", psm], capture_output=True,
                               text=True, timeout=TIMEOUT_S, check=False)
        except subprocess.TimeoutExpired:
            errors.append(f"psm {psm}: timed out after {TIMEOUT_S}s")
            continue
        if r.returncode == 0:
            texts.append(r.stdout)
        else:
            last = (r.stderr or "").strip().splitlines()
            errors.append(f"psm {psm}: {last[-1] if last else f'exit {r.returncode}'}")
    if not texts:
        raise OcrError("; ".join(errors) or "no text pass succeeded")
    _cache[key] = "\n".join(texts)
    return _cache[key]


def materialise(src: str, base: pathlib.Path | None) -> tuple[pathlib.Path | None, str]:
    """The local file an image block's src points to, and a reason when there is none.

    Local paths resolve against the audit's folder, as the renderer does. A data: URI is
    decoded to a temporary file. An http(s) src is never embedded by the renderer (it prints
    an IMAGE NEEDED box), so there is nothing to read."""
    if not src:
        return None, "no src"
    if src.startswith(("http://", "https://")):
        return None, "remote src (the renderer does not embed it)"
    if src.startswith("data:"):
        m = re.match(r"data:image/([a-z0-9.+-]+)?(;[^,]*)?,(.*)$", src, re.I | re.S)
        if not m or "base64" not in (m.group(2) or ""):
            return None, "data: URI that is not base64 image data"
        try:
            raw = base64.b64decode(m.group(3), validate=False)
        except (binascii.Error, ValueError):
            return None, "data: URI that does not decode"
        ext = {"jpeg": ".jpg", "svg+xml": ".svg"}.get((m.group(1) or "png").lower(), "." + (m.group(1) or "png").lower())
        tmp = pathlib.Path(tempfile.mkdtemp()) / f"inline{ext}"
        tmp.write_bytes(raw)
        return tmp, ""
    p = ((base or pathlib.Path(".")) / src).resolve()
    return (p, "") if p.is_file() else (None, f"file not found under {base or '.'}")


def normalise(s: str) -> str:
    """Lower-case words separated by single spaces: OCR line breaks, punctuation and doubled
    spaces must not hide a match."""
    return " ".join(re.findall(r"[0-9a-z]+", s.lower()))


def contains(haystack: str, needle: str) -> bool:
    """True when the do-not-print item appears in the OCR text.

    Matches whole words in order across line breaks and punctuation, and also with every
    space removed, because OCR often merges or splits words set in tight type. The squeezed
    match needs at least six characters so a short item cannot match inside unrelated text."""
    n, h = normalise(needle), normalise(haystack)
    if not n:
        return False
    if f" {n} " in f" {h} ":
        return True
    squeezed = n.replace(" ", "")
    return len(squeezed) >= 6 and squeezed in h.replace(" ", "")
