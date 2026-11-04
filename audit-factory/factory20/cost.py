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
    frontier = round(sum(r["usd"] for r in rows if is_frontier(r["model"])), 2)
    return {"tier": tier, "stages": rows, "total_usd": total, "frontier_usd": frontier}


def is_frontier(model: str) -> bool:
    """Opus or Fable, called directly or through OpenRouter."""
    return any(k in model for k in ("claude-opus-5", "claude-fable-5"))


def _call_usd(p: dict, n_in: float, n_out: float, cached: float = 0, first: bool = True) -> float:
    """One call: `cached` prompt tokens are written to the cache on the first call and read after."""
    fresh = max(n_in - cached, 0)
    return (fresh * p["in"] + cached * (p["cache_write"] if first else p["cache_read"]) + n_out * p["out"]) / 1e6


def measured_cost(tier: str, cfg: dict | None = None, fix_rounds: int = 1, review_passes: int = 1,
                  retry_share: float = 0.0) -> dict:
    """Cost of one audit from an existing ledger, from the measured profile (prompt and reply
    sizes of a real 20-page audit), at this tier's models and prices.

    Typical = one fix round and one review pass. Worst case = three fix rounds, the tier's
    full review passes and a retry allowance on top. Research (stages 10-20) is not included:
    it depends on how much there is to collect, and the planning estimate covers it."""
    cfg = cfg or load_routing()
    prof = cfg["measured_profile"]["stages"]
    t = cfg["tiers"][tier]
    rows = []
    for sid, s in prof.items():
        model = t["models"][sid]
        p = cfg["prices"][model]
        reps = {"review": review_passes, "fix": fix_rounds}.get(sid, 1)
        n = s["calls"] * reps
        pre = s.get("cached_prefix", 0)
        out_per_call = s["out"] / s["calls"]
        usd = sum(_call_usd(p, s["in"], out_per_call, pre, first=(k == 0)) for k in range(n)) if n else 0.0
        usd *= 1 + retry_share
        rows.append({"stage": sid, "model": model, "calls": n, "in": int(s["in"] * n), "out": int(out_per_call * n),
                     "usd": round(usd, 4), "assumed": s.get("assumed", [])})
    total = round(sum(r["usd"] for r in rows), 2)
    return {"tier": tier, "stages": rows, "total_usd": total,
            "frontier_usd": round(sum(r["usd"] for r in rows if is_frontier(r["model"])), 2)}


def measured_range(tier: str, cfg: dict | None = None) -> dict:
    """Typical and worst-case cost of one audit from an existing ledger."""
    cfg = cfg or load_routing()
    passes = cfg["tiers"][tier].get("review_passes", 1)
    return {"typical": measured_cost(tier, cfg), "worst": measured_cost(tier, cfg, fix_rounds=3,
                                                                        review_passes=passes, retry_share=0.25)}


def _class_cost(p: dict, tok: dict) -> float:
    return (tok.get("in", 0) * p["in"] + tok.get("cache_write", 0) * p["cache_write"]
            + tok.get("cache_read", 0) * p["cache_read"] + tok.get("out", 0) * p["out"]) / 1e6


def reference_cost(cfg: dict | None = None) -> dict:
    """List-price cost of the measured all-Claude Cowork run, from its own token counts.

    The run also built a website package; that part is reported separately so the audit
    comparison is like for like. The account bill was never read, so this is list price.
    """
    cfg = cfg or load_routing()
    ref = cfg["reference_run"]
    parts = {}
    for part, by_model in ref["measured"].items():
        parts[part] = round(sum(_class_cost(cfg["prices"][m], tok) for m, tok in by_model.items()), 2)
    return {"cache_read_share": ref.get("cache_read_share"), "audit_usd": parts.get("audit", 0.0),
            "parts": parts, "total_usd": round(sum(parts.values()), 2)}


def monthly(tier: str, audits_per_month: int, cfg: dict | None = None, batch: bool = False) -> float:
    return round(audit_cost(tier, cfg, batch)["total_usd"] * audits_per_month, 2)
