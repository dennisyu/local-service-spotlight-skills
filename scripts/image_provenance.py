#!/usr/bin/env python3
"""Flag images whose own embedded provenance says they were generated. Offline.

    python3 scripts/image_provenance.py photo1.jpg portrait.png ...

Why this exists: an audit's real-media package may count only genuine photographs.
In a Nov 2026 audit, a portrait on a client's site looked photorealistic and a
research pass described it as a real headshot; its own C2PA manifest recorded it
as image-generator output. Read the file's provenance before calling it a photo.

What it checks (byte-level, no third-party libraries):
- a C2PA manifest store (PNG ``caBX`` chunk, JPEG APP11/JUMBF, or the ``c2pa`` label);
- IPTC digital source types for generated media
  (``trainedAlgorithmicMedia``, ``compositeWithTrainedAlgorithmicMedia``,
  ``algorithmicMedia``) in XMP or a manifest;
- a short list of generator names that manifests and XMP commonly carry.

Verdicts:
- GENERATED_LABELLED: the file itself declares generated or AI-composited media.
  Never present it as proof of what a person looks like or of real work.
- NO_LABEL_FOUND: nothing was declared. That is NOT proof of a real photo:
  metadata is easily stripped. Provenance still needs the source record,
  permission and a human look.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

SOURCE_TYPES = (b"compositeWithTrainedAlgorithmicMedia", b"trainedAlgorithmicMedia", b"algorithmicMedia")
GENERATOR_HINTS = (b"gpt-image", b"DALL-E", b"DALL\xc2\xb7E", b"OpenAI", b"Adobe Firefly", b"Midjourney",
                   b"Stable Diffusion", b"Imagen", b"Ideogram", b"Leonardo.Ai")


def has_c2pa(data: bytes) -> bool:
    if data[:8] == b"\x89PNG\r\n\x1a\n" and b"caBX" in data:
        return True
    if data[:2] == b"\xff\xd8" and b"\xff\xeb" in data and b"jumb" in data:
        return True
    return b"c2pa" in data


def inspect(path: Path) -> dict:
    data = path.read_bytes()
    c2pa = has_c2pa(data)
    sources = []
    for token in SOURCE_TYPES:
        if token in data and not any(token in longer for longer in SOURCE_TYPES if longer != token and longer in data):
            sources.append(token.decode())
    hints = sorted({h.decode("utf-8", "replace") for h in GENERATOR_HINTS if h in data})
    generated = bool(sources) or (c2pa and bool(hints))
    return {
        "file": str(path),
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "c2pa_manifest_present": c2pa,
        "digital_source_type": sources,
        "generator_hints": hints,
        "verdict": "GENERATED_LABELLED" if generated else "NO_LABEL_FOUND",
        "limits": "NO_LABEL_FOUND is not proof of a real photograph; metadata can be stripped.",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("images", nargs="+", type=Path)
    a = ap.parse_args()
    results = [inspect(p) for p in a.images]
    print(json.dumps(results, indent=1))
    return 1 if any(r["verdict"] == "GENERATED_LABELLED" for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
