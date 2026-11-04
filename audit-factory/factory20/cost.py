"""What an audit costs, by stage and tier, and what the frontier-only run cost.

Model: for a stage with input budget I (of which share c is a cached prefix re-read) and
output budget O on a model with prices (in, out, cache_read, cache_write):

    cost = I*(1-c)*in + I*c*cache_read + (I*c/calls)*cache_write + O*out        (per 1M)

The cached prefix is written once per stage and read on every call. Batch-eligible stages
can take the provider's batch discount. Haiku's long-context tier applies when the
per-call prompt exceeds its threshold.
"""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
ROUTING = ROOT / "config" / "routing.json"


def load_routing(path: str | pathlib.Path | None = None) -> dict:
    return json.loads(pathlib.Path(path or ROUTING).read_text(encoding="utf-8"))


def price(cfg: dict, model: str, prompt_per_call: float = 0) -> dict:
    p = dict(cfg["prices"][model])
    lc = p.get("long_context")
    if lc and prompt_per_call > lc["over"]:
        p.update({k: v for k, v in lc.items() if k != "over"})
    return p


def stage_cost(cfg: dict, stage: dict, model: str, batch: bool = False) -> dict:
    b = stage["budget"]
    calls = max(int(stage.get("calls", 1)), 1)
    I, O, c = float(b["in"]), float(b["out"]), float(b.get("cache_share", 0))
    p = price(cfg, model, I / calls)
    usd = (I * (1 - c) * p["in"] + I * c * p["cache_read"] + (I * c / calls) * p["cache_write"] + O * p["out"]) / 1e6
    if batch and not stage.get("judgment"):
        usd *= p.get("batch", 1.0)
    usd += float(stage.get("data_usd", 0))
    return {"stage": stage["id"], "model": model, "in": int(I), "out": int(O), "usd": round(usd, 4)}


def audit_cost(tier: str, cfg: dict | None = None, batch: bool = False) -> dict:
    cfg = cfg or load_routing()
    t = cfg["tiers"][tier]
    rows = []
    for st in cfg["stages"]:
        m = t["models"][st["id"]]
        r = stage_cost(cfg, st, m, batch)
        if st["id"] == "review":
            r["usd"] = round(r["usd"] * t.get("review_passes", 1) * 0.75 + r["usd"] * 0.25, 4)  # later passes re-read cache
            r["passes"] = t.get("review_passes", 1)
        rows.append(r)
    total = round(sum(r["usd"] for r in rows), 2)
    frontier = round(sum(r["usd"] for r in rows if cfg["prices"][r["model"]]["provider"] == "anthropic"
                         and r["model"] in ("claude-opus-5-5", "claude-fable-5-1")), 2)
    return {"tier": tier, "stages": rows, "total_usd": total, "frontier_usd": frontier}


def reference_cost(cfg: dict | None = None, cache_read_share: float = 0.97) -> dict:
    """API-equivalent of the measured all-Claude Cowork run under a cache-mix assumption."""
    cfg = cfg or load_routing()
    out = []
    for ln in cfg["reference_run"]["lanes"]:
        p = cfg["prices"][ln["model"]]
        I, O = ln["in"], ln["out"]
        usd = (I * cache_read_share * p["cache_read"] + I * (1 - cache_read_share) * p["cache_write"] + O * p["out"]) / 1e6
        out.append({**ln, "usd": round(usd, 2)})
    return {"cache_read_share": cache_read_share, "lanes": out, "total_usd": round(sum(x["usd"] for x in out), 2)}


def monthly(tier: str, audits_per_month: int, cfg: dict | None = None, batch: bool = False) -> float:
    return round(audit_cost(tier, cfg, batch)["total_usd"] * audits_per_month, 2)
