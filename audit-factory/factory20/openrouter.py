"""Keep the OpenRouter routes honest: every model the kit routes through OpenRouter must
still exist on OpenRouter, at the price the cost model assumes.

`python -m factory20 openrouter-check` reads OpenRouter's public models list (no key, no
spend) and compares it with config/routing.json. It fails when a route has disappeared or a
price has drifted past the tolerance; `--write` updates the prices in place, keeping the
file's one-model-per-line layout so the diff shows exactly what moved.

The models list gives one headline price per model, and for a model many providers serve it
is one provider's price. DeepSeek V4.1 Flash's headline moved three times between Nov 8 and
Nov 11 (input $0.051, $0.30, $0.051) while most of its providers kept charging $0.30. So the
check also reads each route's provider endpoints: when at least MIN_BACKING providers that are
up charge the configured input, output and cached-input price, a different headline is
reported but is not drift. Writing a one-provider headline into routing.json would shrink the
call's max_price ceiling to the few providers at or under it.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import re
import urllib.request

from . import cost as K

MODELS_URL = "https://openrouter.ai/api/v1/models"
ENDPOINTS_URL = "https://openrouter.ai/api/v1/models/{route}/endpoints"
MIN_BACKING = 3        # providers that are up and charge the configured price, so a headline move is not drift
FIELDS = (("in", "prompt"), ("out", "completion"), ("cache_read", "input_cache_read"), ("cache_write", "input_cache_write"))


def fetch_models(url: str = MODELS_URL, timeout: int = 60) -> list[dict]:
    req = urllib.request.Request(url, headers={"User-Agent": "lss-audit-factory/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())["data"]


def load_models(path: str | pathlib.Path) -> list[dict]:
    d = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    return d["data"] if isinstance(d, dict) else d


def fetch_endpoints(route: str, timeout: int = 60) -> list[dict]:
    req = urllib.request.Request(ENDPOINTS_URL.format(route=route), headers={"User-Agent": "lss-audit-factory/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return (json.loads(r.read().decode()).get("data") or {}).get("endpoints") or []


def fetch_all_endpoints(cfg: dict, fetch=fetch_endpoints) -> tuple[dict, list[str]]:
    """Every OpenRouter route's provider endpoints, and the routes whose list would not load
    (those are checked against the headline price alone, as before)."""
    out, failed = {}, []
    for route in sorted({p.get("route") for p in cfg["prices"].values() if p.get("provider") == "openrouter"}):
        try:
            out[route] = fetch(route)
        except Exception:  # noqa: BLE001 — a route whose endpoints will not load keeps the headline check
            failed.append(route)
    return out, failed


def load_endpoints(path: str | pathlib.Path) -> dict | None:
    """The endpoints saved beside a models snapshot (snapshots from before Nov 11 have none)."""
    d = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    return d.get("endpoints") if isinstance(d, dict) else None


def utc_today() -> str:
    """The date a price was read, in UTC like OpenRouter and the CI runner: a session on Pacific
    time wrote Nov 11's prices into Nov 10's file, over the one already there."""
    return dt.datetime.now(dt.timezone.utc).date().isoformat()


def _per_million(v) -> float | None:
    try:
        return None if v in (None, "") else round(float(v) * 1e6, 6)
    except (TypeError, ValueError):
        return None


def _live_long_context(pricing: dict) -> dict | None:
    """OpenRouter's long-context tier (pricing.overrides[].min_prompt_tokens), in our field names."""
    tiers = [o for o in (pricing.get("overrides") or []) if isinstance(o, dict) and o.get("min_prompt_tokens")]
    if not tiers:
        return None
    o = min(tiers, key=lambda x: x["min_prompt_tokens"])
    lc = {"over": int(o["min_prompt_tokens"])}
    for ours, theirs in FIELDS:
        v = _per_million(o.get(theirs))
        if v is not None:
            lc[ours] = v
    return lc


def _lc_drift(ours: dict | None, live: dict | None, tolerance: float) -> bool:
    if not ours and not live:
        return False
    if not ours or not live or int(ours.get("over", -1)) != int(live.get("over", -2)):
        return True
    for k, v in live.items():
        if k == "over":
            continue
        have = float(ours.get(k, 0) or 0)
        if have == 0 or abs(v - have) / max(have, 1e-12) > tolerance:
            return True
    return False


def backing(p: dict, endpoints: list[dict] | None, tolerance: float = 0.10) -> int:
    """How many providers that are up charge the configured input, output and cached-input
    price, each within the tolerance. An endpoint lists 0 for a cache it does not offer, so a
    zero cached-input price neither counts for the configured one nor against it."""
    n = 0
    for e in endpoints or []:
        if e.get("status") != 0:
            continue
        pricing = e.get("pricing") or {}
        agree = True
        for ours, theirs in FIELDS[:3]:
            v = _per_million(pricing.get(theirs))
            if ours == "cache_read" and not v:
                continue
            have = float(p.get(ours, 0) or 0)
            if v is None or have == 0 or abs(v - have) / have > tolerance:
                agree = False
                break
        n += agree
    return n


def check(cfg: dict, models: list[dict], tolerance: float = 0.10, endpoints: dict | None = None) -> dict:
    """One row per OpenRouter route: listed or missing, and every price that drifted. With
    `endpoints` ({route: OpenRouter's endpoint list}), a headline input, output or cached-input
    price that differs from ours is not drift when MIN_BACKING providers that are up charge ours;
    the row keeps it under "headline" with the count under "backing"."""
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
            moved = [f for f in ("in", "out", "cache_read") if f in row["drift"]]
            if moved and endpoints is not None:
                row["backing"] = backing(p, endpoints.get(route), tolerance)
                if row["backing"] >= MIN_BACKING:
                    row["headline"] = {f: row["drift"].pop(f) for f in moved}
            # a long-context tier is a price too: missing it lets a long prompt cost 5x the cap's figure
            live_lc = _live_long_context(m.get("pricing") or {})
            if live_lc:
                row["live"]["long_context"] = live_lc
            if _lc_drift(p.get("long_context"), live_lc, tolerance):
                row["drift"]["long_context"] = {"ours": p.get("long_context"), "live": live_lc}
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


def save_snapshot(cfg: dict, models: list[dict], today: str | None = None, folder: pathlib.Path = SNAPSHOTS,
                  endpoints: dict | None = None) -> pathlib.Path:
    """Keep the slice of OpenRouter's models list that the config relies on, dated, so tests can
    check the config against what OpenRouter actually listed rather than against itself. With
    `endpoints`, each route's providers (name, status, prices) are kept too."""
    today = today or utc_today()
    routes = {p.get("route") for p in cfg["prices"].values() if p.get("provider") == "openrouter"}
    keep = [{"id": m["id"], "pricing": m.get("pricing"), "reasoning": m.get("reasoning")} for m in models if m["id"] in routes]
    snap = {"source": MODELS_URL, "read": today, "data": sorted(keep, key=lambda m: m["id"])}
    if endpoints is not None:
        snap["endpoints_source"] = ENDPOINTS_URL
        snap["endpoints"] = {r: [{"provider_name": e.get("provider_name"), "tag": e.get("tag"), "status": e.get("status"),
                                  "pricing": {k: (e.get("pricing") or {}).get(k) for _, k in FIELDS}}
                                 for e in eps] for r, eps in sorted(endpoints.items()) if r in routes}
    folder.mkdir(parents=True, exist_ok=True)
    out = folder / f"models-{today}.json"
    out.write_text(json.dumps(snap, indent=1) + "\n", encoding="utf-8")
    return out


def latest_snapshot(folder: pathlib.Path = SNAPSHOTS) -> pathlib.Path | None:
    files = sorted(folder.glob("models-*.json"))
    return files[-1] if files else None


def write_prices(report: dict, path: str | pathlib.Path = K.ROUTING, today: str | None = None) -> list[str]:
    """Rewrite the drifted price lines in routing.json in place. Returns the keys changed."""
    path = pathlib.Path(path)
    text = path.read_text(encoding="utf-8")
    today = today or utc_today()
    changed = []
    for row in report["rows"]:
        if not row["drift"]:
            continue
        m = re.search(r'^(\s*' + re.escape(json.dumps(row["key"])) + r':\s*)(\{.*\})(,?)$', text, re.M)
        if not m:
            continue
        entry = json.loads(m.group(2))
        for field, d in row["drift"].items():
            if field == "long_context" and d["live"] is None:
                entry.pop("long_context", None)
            else:
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
