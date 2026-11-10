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
# REPORTED is a ledger state (ledger.STATES) and the renderer already draws it; a card built on
# REPORTED evidence must be able to say so. Without it, the Nov 10 pilot's writers had to retry,
# climb the model ladder, or relabel reported evidence as INFERRED to pass G21.
BADGES = {"OBSERVED", "INFERRED", "UNKNOWN", "REPORTED"}
ACTION_STATES = {"PROPOSED", "STAGED", "APPROVED", "IN PROGRESS", "BLOCKED", "COMPLETE", "VERIFIED"}
EXECUTORS = {"AGENT", "AGENT_AFTER_APPROVAL", "HUMAN"}
ACTION_FIELDS = ["id", "action", "evidence", "function", "skill", "dependency", "destination",
                 "due", "human_gate", "acceptance_test", "state"]

EVID_KEYS = ("evidence", "refs", "evidence_ids")
ACTION_KEYS = ("actions", "action_ids")
# A table column with one of these names holds evidence ids; the renderer draws each id in it
# as a linked chip, so every check that counts or verifies citations reads it too.
EVIDENCE_COLUMNS = ("evidence", "refs", "source ids", "evidence ids")


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


# A ledger id: capitals and digits in hyphenated groups (E-012, V-E012, C-SPELL). Action ids (A5)
# have no hyphen, so an action id written into an Evidence cell stays text, not a broken chip.
ID_SHAPE = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+$")
_EDGE = "()[]{}<>.,;:!?\"'\u201c\u201d\u2018\u2019"


def split_cell(v) -> tuple[list[str], str]:
    """One table cell from an evidence column: the ids it cites, and the rest of it as words.
    A token is an id only when it has the ledger's id shape once surrounding punctuation is
    stripped; "see", "n/a", "(A5)", "-" and None stay text. The renderer draws the ids as chips
    and the words as words; every check counts the ids, and only the ids."""
    if v is None:
        return [], ""
    parts = [str(x) for x in v if x is not None] if isinstance(v, list) else re.split(r"[,;\s]+", str(v).strip())
    ids, rest = [], []
    for t in parts:
        core = t.strip().strip(_EDGE)
        if ID_SHAPE.match(core):
            ids.append(core)
        elif t.strip():
            rest.append(t.strip())
    return ids, " ".join(rest)


def cell_ids(v) -> list[str]:
    """The evidence ids one table cell cites (see split_cell)."""
    return split_cell(v)[0]


def evidence_columns(columns) -> list[int]:
    """Indexes of the table columns that hold evidence ids."""
    if not isinstance(columns, list):
        return []
    return [i for i, c in enumerate(columns) if str(c).strip().lower() in EVIDENCE_COLUMNS]


def table_refs(d: dict) -> list[str]:
    """Evidence ids in a table's evidence columns (a block {columns, rows}); [] for anything else."""
    idx = evidence_columns(d.get("columns"))
    rows = d.get("rows")
    if not idx or not isinstance(rows, list):
        return []
    out: list[str] = []
    for r in rows:
        if isinstance(r, list):
            for i in idx:
                if i < len(r):
                    out += cell_ids(r[i])
    return out


def refs_in(obj, tables: bool = True) -> list[str]:
    """All evidence ids referenced anywhere inside obj, in first-seen order: every evidence /
    refs / evidence_ids field, and (tables=True) every id in a table's evidence column. The
    renderer turns those into chips, so the checks must see them; until Nov 10 they did not, and
    a page that cited a dozen ids in its tables failed "cite at least 3 evidence ids"."""
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
        if tables:
            for x in table_refs(d):
                seen.setdefault(x, None)
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
