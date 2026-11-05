"""Test helpers: replay a finished audit.json as if each stage's model had written it."""
from __future__ import annotations

import json
import pathlib
import re


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


READY_REVIEW = {"verdict": "READY", "findings": [], "score_adjustments": [],
                "strongest": ["page 2 findings", "the dated action register", "evidence on every page"]}


def fake_from_fixture(path: str, review: dict | None = None):
    """Replay a fixture: each stage returns its slice; a fix returns one page; review is READY
    unless a review object is given (a list of them is consumed one per review pass)."""
    outs = split_fixture(json.loads(pathlib.Path(path).read_text(encoding="utf-8")))
    reviews = list(review) if isinstance(review, list) else [review or READY_REVIEW]

    def fake(stage, model, system, user):
        return "```json\n" + json.dumps(answer(stage, user), ensure_ascii=False) + "\n```"

    def answer(stage, user):
        if stage == "fix":
            return {"pages": outs["pages"]["pages"][:1]}
        if stage == "review":
            return reviews.pop(0) if len(reviews) > 1 else reviews[0]
        if stage == "pages":                      # pages come in batches: answer only the batch asked for
            m = re.search(r"Write pages (\d+)-(\d+) only", user)
            if m:
                a, b = int(m.group(1)), int(m.group(2))
                return {"pages": [p for p in outs["pages"]["pages"] if a <= p["n"] <= b]}
        return outs[stage]
    fake.answer = answer
    return fake
