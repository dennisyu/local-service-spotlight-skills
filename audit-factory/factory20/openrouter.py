"""Keep the OpenRouter routes honest: every model the kit routes through OpenRouter must
still exist on OpenRouter, at the price the cost model assumes.

`python -m factory20 openrouter-check` reads OpenRouter's public models list (no key, no
spend) and compares it with config/routing.json. It fails when a route has disappeared or a
price has drifted past the tolerance; `--write` updates the prices in place, keeping the
file's one-model-per-line layout so the diff shows exactly what moved.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import re
import urllib.request

from . import cost as K

MODELS_URL = "https://openrouter.ai/api/v1/models"
FIELDS = (("in", "prompt"), ("out", "completion"), ("cache_read", "input_cache_read"), ("cache_write", "input_cache_write"))


def fetch_models(url: str = MODELS_URL, timeout: int = 60) -> list[dict]:
    req = urllib.request.Request(url, headers={"User-Agent": "lss-audit-factory/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())["data"]


def load_models(path: str | pathlib.Path) -> list[dict]:
    d = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    return d["data"] if isinstance(d, dict) else d


def _per_million(v) -> float | None:
    try:
        return None if v in (None, "") else round(float(v) * 1e6, 6)
    except (TypeError, ValueError):
        return None


def check(cfg: dict, models: list[dict], tolerance: float = 0.10) -> dict:
    """One row per OpenRouter route: listed or missing, and every price that drifted."""
    live = {m["id"]: m for m in models}
    rows = []
    for key, p in cfg["prices"].items():
        if p.get("provider") != "openrouter":
            continue
        route = p.get("route", key)
        m = live.get(route)
        row = {"key": key, "route": route, "listed": m is not None, "drift": {}, "live": {}}
        if m:
            live_efforts = (m.get("reasoning") or {}).get("supported_efforts")
            if p.get("efforts") is not None and live_efforts is not None and set(p["efforts"]) != set(live_efforts):
                row["drift"]["efforts"] = {"ours": p["efforts"], "live": live_efforts}
            for ours, theirs in FIELDS:
                v = _per_million((m.get("pricing") or {}).get(theirs))
                if v is None:
                    continue
                row["live"][ours] = v
                have = float(p.get(ours, 0))
                if have == 0 and v == 0:
                    continue
                if have == 0 or abs(v - have) / max(have, 1e-12) > tolerance:
                    row["drift"][ours] = {"ours": have, "live": v}
        rows.append(row)
    missing = [r["key"] for r in rows if not r["listed"]]
    drifted = [r["key"] for r in rows if r["drift"]]
    used = {m for t in cfg["tiers"].values() for m in t["models"].values()}
    return {"rows": rows, "missing": missing, "drifted": drifted,
            "missing_in_use": sorted(set(missing) & used), "ok": not missing and not drifted}


def _fmt(v) -> str:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, int):
        return str(v)
    return f"{v:.2f}" if abs(v - round(v, 2)) < 1e-12 and v >= 0.1 else repr(round(v, 6))


SNAPSHOTS = K.ROOT / "fixtures" / "openrouter"


def save_snapshot(cfg: dict, models: list[dict], today: str | None = None, folder: pathlib.Path = SNAPSHOTS) -> pathlib.Path:
    """Keep the slice of OpenRouter's models list that the config relies on, dated, so tests can
    check the config against what OpenRouter actually listed rather than against itself."""
    today = today or dt.date.today().isoformat()
    routes = {p.get("route") for p in cfg["prices"].values() if p.get("provider") == "openrouter"}
    keep = [{"id": m["id"], "pricing": m.get("pricing"), "reasoning": m.get("reasoning")} for m in models if m["id"] in routes]
    folder.mkdir(parents=True, exist_ok=True)
    out = folder / f"models-{today}.json"
    out.write_text(json.dumps({"source": MODELS_URL, "read": today, "data": sorted(keep, key=lambda m: m["id"])},
                              indent=1) + "\n", encoding="utf-8")
    return out


def latest_snapshot(folder: pathlib.Path = SNAPSHOTS) -> pathlib.Path | None:
    files = sorted(folder.glob("models-*.json"))
    return files[-1] if files else None


def write_prices(report: dict, path: str | pathlib.Path = K.ROUTING, today: str | None = None) -> list[str]:
    """Rewrite the drifted price lines in routing.json in place. Returns the keys changed."""
    path = pathlib.Path(path)
    text = path.read_text(encoding="utf-8")
    today = today or dt.date.today().isoformat()
    changed = []
    for row in report["rows"]:
        if not row["drift"]:
            continue
        m = re.search(r'^(\s*' + re.escape(json.dumps(row["key"])) + r':\s*)(\{.*\})(,?)$', text, re.M)
        if not m:
            continue
        entry = json.loads(m.group(2))
        for field, d in row["drift"].items():
            entry[field] = d["live"]
        entry["source"] = re.sub(r"read \d{4}-\d{2}-\d{2}", f"read {today}", entry.get("source", "")) \
            if "read " in entry.get("source", "") else f"OpenRouter models API ({MODELS_URL}), read {today}"
        line = "{" + ", ".join(f"{json.dumps(k)}: {_fmt(v) if not isinstance(v, (dict, list)) else json.dumps(v)}"
                               for k, v in entry.items()) + "}"
        text = text[:m.start(2)] + line + text[m.end(2):]
        changed.append(row["key"])
    if changed:
        json.loads(text)                     # never write a file that no longer parses
        path.write_text(text, encoding="utf-8")
    return changed
