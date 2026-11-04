"""Evidence ledger: load, normalize and summarize.

Accepted inputs
  * the JSON ledger our Claude runs produce (``items``, ``ambiguous``, ``conflicts``,
    ``unknowns``; optional ``insights``), and
  * a flat CSV with at least ``id`` and ``claim`` columns.

Every row becomes a normalized dict with stable keys so later stages never guess field
names. Conflicts (``C`` ids) and unknowns (``U`` ids) are referencable like evidence.
"""
from __future__ import annotations

import csv
import json
import pathlib
import re
from collections import Counter

# Evidence classes, strongest first. Unknown labels map to UNCLASSIFIED.
CLASS_STRENGTH = {
    "INDEPENDENTLY-CORROBORATED": 3,
    "THIRD-PARTY": 3,
    "PLATFORM-DATA": 2,
    "FIRM-UNATTRIBUTED": 1,
    "SELF-CLAIM": 1,
    "NOT-APPLICABLE": 0,
    "UNCLASSIFIED": 0,
}
STATES = {"OBSERVED", "INFERRED", "UNKNOWN", "REPORTED"}
# A row that proves something is broken, missing or lost is evidence AGAINST a high score.
NEGATIVE = re.compile(r"\b(no|not|none|never|missing|broken|404|expired|dead|fails?|failed|zero|lost|"
                      r"outside the top|silent|stale|absent|cannot|can't|error|down|without|unclaimed|"
                      r"misidentif\w*|confus\w*|wrong)\b|\b0 of\b", re.I)


def polarity(raw: dict) -> str:
    """'positive' | 'negative' | 'neutral' — explicit field wins, else a wording heuristic."""
    v = (raw.get("polarity") or "").strip().lower()
    if v in ("positive", "negative", "neutral"):
        return v
    text = f"{raw.get('claim', '')} {raw.get('value', '')}"
    return "negative" if NEGATIVE.search(text) else "positive"
STRIP_FOR_BLIND_TEST = ("insights", "lane_insights_raw", "load_bearing")


def _norm_item(raw: dict, kind: str = "evidence") -> dict:
    cls = (raw.get("evidence_class") or raw.get("class") or "UNCLASSIFIED").strip().upper()
    if cls not in CLASS_STRENGTH:
        cls = "UNCLASSIFIED"
    state = (raw.get("state") or raw.get("evidence_state") or "UNKNOWN").strip().upper()
    if state not in STATES:
        state = "UNKNOWN"
    return {
        "id": str(raw.get("id", "")).strip(),
        "kind": kind,
        "topic": raw.get("topic") or "",
        "claim": (raw.get("claim") or raw.get("unknown") or raw.get("metric") or "").strip(),
        "value": (raw.get("value") or raw.get("what_was_checked") or "").strip()
        if isinstance(raw.get("value") or raw.get("what_was_checked") or "", str) else str(raw.get("value")),
        "url": (raw.get("source_url") or raw.get("url") or "").strip(),
        "source": (raw.get("source_name") or raw.get("source") or "").strip(),
        "published": (raw.get("published") or "").strip(),
        "state": state,
        "cls": cls,
        "strength": CLASS_STRENGTH[cls],
        "match": (raw.get("subject_match") or "").strip().upper(),
        "notes": (raw.get("notes") or "").strip(),
        "polarity": polarity(raw),
    }


class Ledger:
    """Normalized evidence ledger."""

    def __init__(self, subject: str, capture_date: str, rows: list[dict], insights: list | None = None,
                 meta: dict | None = None):
        self.subject = subject
        self.capture_date = capture_date
        self.rows = rows
        self.by_id = {r["id"]: r for r in rows if r["id"]}
        self.insights = insights or []
        self.meta = meta or {}

    # ---------- loading ----------
    @classmethod
    def load(cls, path: str | pathlib.Path) -> "Ledger":
        p = pathlib.Path(path)
        if p.suffix.lower() == ".csv":
            with p.open(newline="", encoding="utf-8") as f:
                rows = [_norm_item(r) for r in csv.DictReader(f)]
            return cls(subject=p.stem, capture_date="", rows=rows)
        data = json.loads(p.read_text(encoding="utf-8"))
        return cls.from_json(data)

    @classmethod
    def from_json(cls, data: dict) -> "Ledger":
        rows: list[dict] = []
        for it in data.get("items", []):
            rows.append(_norm_item(it, "evidence"))
        for it in data.get("ambiguous", []):
            r = _norm_item(it, "ambiguous")
            r["match"] = r["match"] or "AMBIGUOUS"
            rows.append(r)
        for it in data.get("conflicts", []):
            vals = [it.get("value_a"), it.get("value_b")] + list(it.get("other_values") or [])
            vals = [v for v in vals if v]
            rows.append({
                "id": it.get("id", ""), "kind": "conflict", "topic": "conflict",
                "claim": it.get("metric", ""),
                "value": " | ".join(f"{v.get('value')} ({v.get('source')})" for v in vals if isinstance(v, dict)),
                "url": "", "source": "conflict group", "published": "", "state": "OBSERVED",
                "cls": "NOT-APPLICABLE", "strength": 0, "match": "CONFIRMED",
                "notes": it.get("how_audit_must_present", ""),
                "related": it.get("related_items", []),
            })
        for it in data.get("unknowns", []):
            rows.append({
                "id": it.get("id", ""), "kind": "unknown", "topic": "unknown",
                "claim": it.get("unknown", ""), "value": it.get("what_was_checked", ""),
                "url": "", "source": "coverage limit", "published": "", "state": "UNKNOWN",
                "cls": "NOT-APPLICABLE", "strength": 0, "match": "",
                "notes": "", "related": it.get("related_items", []),
            })
        subj = data.get("subject")
        if isinstance(subj, dict):
            subj = subj.get("name", "")
        return cls(subject=subj or "", capture_date=data.get("capture_date", ""), rows=rows,
                   insights=data.get("insights", []),
                   meta={k: v for k, v in data.items() if k not in ("items", "ambiguous", "conflicts", "unknowns")})

    # ---------- queries ----------
    def has(self, eid: str) -> bool:
        return eid in self.by_id

    def get(self, eid: str) -> dict | None:
        return self.by_id.get(eid)

    def stats(self) -> dict:
        ev = [r for r in self.rows if r["kind"] == "evidence"]
        return {
            "subject": self.subject,
            "capture_date": self.capture_date,
            "evidence": len(ev),
            "ambiguous": sum(1 for r in self.rows if r["kind"] == "ambiguous"),
            "conflicts": sum(1 for r in self.rows if r["kind"] == "conflict"),
            "unknowns": sum(1 for r in self.rows if r["kind"] == "unknown"),
            "by_class": dict(Counter(r["cls"] for r in ev)),
            "by_state": dict(Counter(r["state"] for r in ev)),
            "with_url": sum(1 for r in ev if r["url"].startswith("http")),
        }

    def pack(self, max_value_chars: int = 220, include_notes: bool = False) -> str:
        """Compact, model-friendly evidence pack: one line per row.

        Keeps every id and the fields a writer needs, drops provenance noise. A 250-row
        ledger packs to roughly 20-30K tokens instead of 100K.
        """
        lines = []
        for r in self.rows:
            v = re.sub(r"\s+", " ", r["value"])[:max_value_chars]
            src = r["source"][:60]
            pub = r["published"][:20]
            line = f"{r['id']} | {r['kind']} | {r['state']} | {r['cls']} | {r['claim']} | {v} | {src} | {pub}"
            if include_notes and r["notes"]:
                line += " | note: " + re.sub(r"\s+", " ", r["notes"])[:160]
            lines.append(line)
        header = ("id | kind | state | evidence_class | claim | value | source | published\n"
                  f"# subject: {self.subject} · capture: {self.capture_date} · rows: {len(lines)}")
        return header + "\n" + "\n".join(lines)


def blind_copy(data: dict) -> dict:
    """Ledger JSON with prior synthesis removed — for testing a model's own synthesis."""
    return {k: v for k, v in data.items() if k not in STRIP_FOR_BLIND_TEST}
