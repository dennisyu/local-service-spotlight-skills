"""audit.json: the structured audit every stage writes and the renderer reads.

The model never writes HTML. It writes typed blocks; code lays them out. That is what
lets a cheaper model produce a page that looks like the frontier one.
"""
from __future__ import annotations

import json
import pathlib
import re
from typing import Iterator

# Blueprint page types in default order (pages 1, 2 and 20 are invariant).
PAGE_TYPES = [
    "cover", "summary", "goal", "identity", "exams", "proof", "connections", "assets",
    "lighthouse", "offer", "dollar_a_day", "audience", "content_factory", "capture",
    "entity", "search_ai", "agents", "plan", "risks", "receipt",
]
FIXED = {1: "cover", 2: "summary", 20: "receipt"}

# Blocks that count as the page's meaningful visual (tables and plain prose do not).
VISUAL_BLOCKS = {
    "photo", "screenshot", "graph", "bars", "heatmap", "timeline", "swimlane", "matrix",
    "ladder", "flow", "topic_wheel", "qr", "finding_map", "donut", "scorebar",
}
TEXT_BLOCKS = {"prose", "cards", "stat_strip", "table", "callout", "checklist", "conflicts", "quote"}
ALL_BLOCKS = VISUAL_BLOCKS | TEXT_BLOCKS
BADGES = {"OBSERVED", "INFERRED", "UNKNOWN"}
ACTION_STATES = {"PROPOSED", "STAGED", "APPROVED", "IN PROGRESS", "BLOCKED", "COMPLETE", "VERIFIED"}
EXECUTORS = {"AGENT", "AGENT_AFTER_APPROVAL", "HUMAN"}
ACTION_FIELDS = ["id", "action", "evidence", "function", "skill", "dependency", "destination",
                 "due", "human_gate", "acceptance_test", "state"]

EVID_KEYS = ("evidence", "refs", "evidence_ids")
ACTION_KEYS = ("actions", "action_ids")


def load(path: str | pathlib.Path) -> dict:
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def walk(obj) -> Iterator:
    """Yield every dict in a nested structure."""
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk(v)


def refs_in(obj) -> list[str]:
    """All evidence ids referenced anywhere inside obj, in first-seen order."""
    seen: dict[str, None] = {}
    for d in walk(obj):
        for k in EVID_KEYS:
            v = d.get(k)
            if isinstance(v, str):
                v = [v]
            if isinstance(v, list):
                for x in v:
                    if isinstance(x, str) and x.strip():
                        seen.setdefault(x.strip(), None)
    return list(seen)


def action_refs_in(obj) -> list[str]:
    seen: dict[str, None] = {}
    for d in walk(obj):
        for k in ACTION_KEYS:
            v = d.get(k)
            if isinstance(v, str):
                v = [v]
            if isinstance(v, list):
                for x in v:
                    if isinstance(x, str) and x.strip():
                        seen.setdefault(x.strip(), None)
        if isinstance(d.get("action_id"), str):
            seen.setdefault(d["action_id"].strip(), None)
    return list(seen)


_SKIP_TEXT_KEYS = {"type", "span", "src", "url", "badge", "state", "kind", "tone", "id", "n",
                   "evidence", "refs", "actions", "action_id", "from", "to", "layout", "palette"}


def text_of(obj) -> str:
    """Reader-visible text inside obj (skips ids, urls and enum fields)."""
    out: list[str] = []

    def rec(o, key=None):
        if isinstance(o, str):
            if key not in _SKIP_TEXT_KEYS:
                out.append(o)
        elif isinstance(o, dict):
            for k, v in o.items():
                rec(v, k)
        elif isinstance(o, list):
            for v in o:
                rec(v, key)

    rec(obj)
    return "\n".join(out)


WORD = re.compile(r"[A-Za-z][A-Za-z'\-]+")
NUMBER = re.compile(r"(?<![A-Za-z])[\$#]?\d[\d,\.]*%?")


def words(s: str) -> int:
    return len(WORD.findall(s))


def numbers(s: str) -> int:
    return len(NUMBER.findall(s))


def page_by_type(audit: dict, t: str) -> dict | None:
    for p in audit.get("pages", []):
        if p.get("type") == t or t in (p.get("covers") or []):
            return p
    return None
