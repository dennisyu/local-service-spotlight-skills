"""Brand Authority v1.0/1.1 arithmetic and calibration, in code so no tier can bend it.

Rules encoded from references/brand-authority-rubric.md:
  * ten rows, 0-10 each, equal weight, pass line 80; headline = arithmetic sum;
  * any UNKNOWN row -> INCOMPLETE, known subtotal shown, no pass verdict, never rescaled;
  * identity HOLD -> no number at all;
  * 7-8 needs strong, current, independently corroborated evidence (>= 2 independent rows);
  * 9-10 needs the high anchor across surfaces (>= 4 independent rows);
  * a row resting only on self-claims or unattributed firm copy cannot exceed 4;
  * 0 needs a named active harm, otherwise absence is 1;
  * only positive evidence supports a high number: a row scored >= 6 whose cited rows mostly
    show something broken or missing is contradicted by its own evidence.

The calibration flags are exactly the failure modes seen in the Oct 27 DeepSeek replay
(+5 generosity on rows 4, 5 and 7) and in Claude's own R1 review (57 -> 52).
"""
from __future__ import annotations

from .ledger import Ledger

ROWS = [
    "Entity home and name rank",
    "Media relationships and offline authority",
    "Content assets",
    "Social proof",
    "Monetizable positioning",
    "Consistency and schema hygiene",
    "Current-channel momentum",
    "Link authority to entity home",
    "Search visibility beyond name",
    "Knowledge Graph presence",
]
PASS_LINE = 80
INDEPENDENT = {"INDEPENDENTLY-CORROBORATED", "THIRD-PARTY"}
WEAK = {"SELF-CLAIM", "FIRM-UNATTRIBUTED"}


def compute(exam: dict, identity_status: str = "CONFIRMED") -> dict:
    rows = exam.get("rows", [])
    known = [r for r in rows if isinstance(r.get("score"), (int, float))]
    unknown = [r for r in rows if not isinstance(r.get("score"), (int, float))]
    subtotal = sum(r["score"] for r in known)
    if identity_status != "CONFIRMED":
        status, total, verdict = "HOLD", None, "NO NUMBER — identity not confirmed"
    elif unknown or len(rows) != 10:
        status, total = "INCOMPLETE", None
        verdict = f"INCOMPLETE — {subtotal} known of {10 * len(known)} checked; no pass verdict"
    else:
        status, total = "COMPLETE", subtotal
        verdict = "PASS" if subtotal >= exam.get("pass_line", PASS_LINE) else "BELOW PASS LINE"
    return {"status": status, "total": total, "known_subtotal": subtotal,
            "known_rows": len(known), "unknown_rows": len(unknown), "verdict": verdict,
            "pass_line": exam.get("pass_line", PASS_LINE)}


def calibration_flags(exam: dict, ledger: Ledger | None) -> list[dict]:
    """Per-row flags where the number outruns its evidence."""
    flags = []
    for r in exam.get("rows", []):
        s = r.get("score")
        n = r.get("n")
        ev = r.get("evidence") or []
        if not isinstance(s, (int, float)):
            continue
        if not (0 <= s <= 10):
            flags.append({"row": n, "level": "FAIL", "code": "RANGE", "msg": f"score {s} outside 0-10"})
            continue
        if not ev:
            flags.append({"row": n, "level": "FAIL", "code": "NO_EVIDENCE", "msg": "numeric row cites no evidence"})
            continue
        if ledger is None:
            continue
        items = [ledger.get(e) for e in ev if ledger.get(e)]
        indep = sum(1 for i in items if i["cls"] in INDEPENDENT and i["state"] == "OBSERVED"
                    and i.get("polarity", "positive") != "negative")
        negative = sum(1 for i in items if i.get("polarity") == "negative")
        weak_only = items and all(i["cls"] in WEAK or i["strength"] <= 1 for i in items)
        only_unknown = items and all(i["state"] == "UNKNOWN" for i in items)
        if only_unknown:
            flags.append({"row": n, "level": "FAIL", "code": "UNKNOWN_SUPPORT",
                          "msg": f"scored {s} but every cited row is UNKNOWN — score UNKNOWN instead"})
        if s >= 9 and indep < 4:
            flags.append({"row": n, "level": "FAIL", "code": "GENEROUS_9",
                          "msg": f"scored {s}; 9-10 needs >= 4 independent observed rows, found {indep}"})
        elif s >= 7 and indep < 2:
            flags.append({"row": n, "level": "FAIL", "code": "GENEROUS_7",
                          "msg": f"scored {s}; 7-8 needs >= 2 independent observed rows, found {indep}"})
        if s >= 6 and items and negative * 2 >= len(items):
            flags.append({"row": n, "level": "FAIL", "code": "CONTRADICTED",
                          "msg": f"scored {s} but {negative} of {len(items)} cited rows show something broken or missing"})
        if weak_only and s > 4:
            flags.append({"row": n, "level": "FAIL", "code": "SELF_CLAIM_CAP",
                          "msg": f"scored {s} on self-claims/unattributed copy only; cap is 4"})
        if s == 0 and not (r.get("harm") or "").strip():
            flags.append({"row": n, "level": "FAIL", "code": "ZERO_NEEDS_HARM",
                          "msg": "0 requires a named active harm; plain absence scores 1"})
        if not (r.get("why") or "").strip():
            flags.append({"row": n, "level": "WARN", "code": "NO_REASON",
                          "msg": "no one-sentence anchor reason recorded"})
    return flags
