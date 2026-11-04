"""Test helpers: replay a finished audit.json as if each stage's model had written it."""
from __future__ import annotations

import json
import pathlib


def split_fixture(audit: dict) -> dict:
    """The stage outputs that would have produced this audit."""
    pages = {p["n"]: p for p in audit["pages"]}
    meta = audit["meta"]
    return {
        "identity": {"identity": meta["identity"]},
        "score": {"brand_authority": audit["exams"]["brand_authority"], "separate": audit["exams"].get("separate", [])},
        "synthesis": {"positioning": {"state": "INFERRED"}, "storylines": [], "next_decision": meta.get("next_decision", ""),
                      "pages": [pages[1], pages[2]]},
        "pages": {"pages": [pages[n] for n in range(3, 20)]},
        "actions": {"actions": audit["actions"]},
    }


def fake_from_fixture(path: str):
    outs = split_fixture(json.loads(pathlib.Path(path).read_text(encoding="utf-8")))

    def fake(stage, model, system, user):
        return "```json\n" + json.dumps(outs[stage], ensure_ascii=False) + "\n```"
    return fake
