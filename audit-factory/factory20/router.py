"""Stage -> model routing with provider adapters and one-rung-at-a-time escalation.

One runner owns the whole audit. There are no "lanes" waiting on other agents: every
stage is a function call that reads files and writes files in the run folder. That is
the fix for the Oct 25 cheap-lane pipeline, whose Gemini and Cursor lanes were work
orders filed in a repo that no running process ever read.

Providers
  anthropic   Messages API            ANTHROPIC_API_KEY
  openrouter  OpenAI-compatible chat  OPENROUTER_API_KEY   (DeepSeek, Gemini, GPT via one key)
  openai      Chat Completions        OPENAI_API_KEY
  gemini      generateContent         GEMINI_API_KEY
  manual      writes prompts/<stage>.md and waits for outputs/<stage>.json — for an app
              session (Muse, ChatGPT, Claude.ai) running the factory itself
  fake        deterministic stub for tests
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import time
import urllib.request

from . import cost as K

ROOT = pathlib.Path(__file__).resolve().parent.parent
STAGES_DIR = ROOT / "stages"


class Pending(Exception):
    """A manual stage is waiting for its output file."""


def _post(url: str, headers: dict, body: dict, timeout: int = 600) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={**headers, "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def call(model: str, system: str, user: str, cfg: dict, max_tokens: int = 16000, run_dir: pathlib.Path | None = None,
         stage: str = "stage", fake=None) -> dict:
    """Return {"text", "usage": {"in","out","cache_read","cache_write"}, "model", "provider"}."""
    p = cfg["prices"][model]
    prov = p["provider"]
    if fake is not None:
        text = fake(stage, model, system, user)
        return {"text": text, "usage": {"in": len(user) // 4, "out": len(text) // 4, "cache_read": 0, "cache_write": 0},
                "model": model, "provider": "fake"}
    if prov == "anthropic":
        body = {"model": model, "max_tokens": max_tokens,
                "system": [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
                "messages": [{"role": "user", "content": user}]}
        r = _post("https://api.anthropic.com/v1/messages",
                  {"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"}, body)
        text = "".join(c.get("text", "") for c in r.get("content", []) if c.get("type") == "text")
        u = r.get("usage", {})
        usage = {"in": u.get("input_tokens", 0), "out": u.get("output_tokens", 0),
                 "cache_read": u.get("cache_read_input_tokens", 0), "cache_write": u.get("cache_creation_input_tokens", 0)}
    elif prov in ("openrouter", "openai"):
        url = "https://openrouter.ai/api/v1/chat/completions" if prov == "openrouter" else "https://api.openai.com/v1/chat/completions"
        key = os.environ["OPENROUTER_API_KEY" if prov == "openrouter" else "OPENAI_API_KEY"]
        body = {"model": p.get("route", model), "temperature": 0.3, "max_tokens": max_tokens,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        if prov == "openrouter":
            body["provider"] = {"data_collection": "deny"}
        r = _post(url, {"authorization": f"Bearer {key}"}, body)
        text = r["choices"][0]["message"]["content"]
        u = r.get("usage", {})
        usage = {"in": u.get("prompt_tokens", 0), "out": u.get("completion_tokens", 0), "cache_read": 0, "cache_write": 0}
    elif prov == "gemini":
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/{p.get('route', model)}:generateContent"
               f"?key={os.environ['GEMINI_API_KEY']}")
        body = {"systemInstruction": {"parts": [{"text": system}]}, "contents": [{"role": "user", "parts": [{"text": user}]}],
                "generationConfig": {"temperature": 0.3, "maxOutputTokens": max_tokens}}
        r = _post(url, {}, body)
        text = "".join(pt.get("text", "") for pt in r["candidates"][0]["content"]["parts"])
        u = r.get("usageMetadata", {})
        usage = {"in": u.get("promptTokenCount", 0), "out": u.get("candidatesTokenCount", 0), "cache_read": 0, "cache_write": 0}
    elif prov == "manual":
        assert run_dir is not None, "manual provider needs a run folder"
        (run_dir / "prompts").mkdir(parents=True, exist_ok=True)
        (run_dir / "outputs").mkdir(parents=True, exist_ok=True)
        out = run_dir / "outputs" / f"{stage}.json"
        if out.exists():
            return {"text": out.read_text(encoding="utf-8"), "usage": {"in": 0, "out": 0, "cache_read": 0, "cache_write": 0},
                    "model": model, "provider": "manual"}
        (run_dir / "prompts" / f"{stage}.md").write_text(f"# SYSTEM\n\n{system}\n\n# USER\n\n{user}\n", encoding="utf-8")
        raise Pending(f"answer {run_dir / 'prompts' / (stage + '.md')} and save the JSON to {out}")
    else:
        raise ValueError(f"no provider for {model}")
    return {"text": text, "usage": usage, "model": model, "provider": prov}


def usd(cfg: dict, model: str, usage: dict) -> float:
    p = cfg["prices"][model]
    fresh = max(usage["in"] - usage.get("cache_read", 0) - usage.get("cache_write", 0), 0)
    return round((fresh * p["in"] + usage.get("cache_read", 0) * p["cache_read"]
                  + usage.get("cache_write", 0) * p["cache_write"] + usage["out"] * p["out"]) / 1e6, 5)


def extract_json(text: str):
    """First JSON object/array in a model reply (fenced or bare)."""
    m = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", text, re.S)
    raw = m.group(1) if m else text[text.find("{"):text.rfind("}") + 1] if "{" in text else text
    return json.loads(raw)


def next_rung(cfg: dict, model: str) -> str | None:
    ladder = cfg["escalation"]
    if model not in ladder:
        return ladder[min(2, len(ladder) - 1)]
    i = ladder.index(model)
    return ladder[i + 1] if i + 1 < len(ladder) else None


def run_stage(stage_id: str, user: str, tier: str, run_dir: pathlib.Path, check=None, cfg: dict | None = None,
              fake=None, max_escalations: int = 1) -> dict:
    """Run one stage: call, parse, check; retry once with the error, then escalate one rung.

    check(obj) -> list of problems (empty = accepted). Every attempt is logged with tokens
    and cost to run.json so the per-audit attribution is measured, not estimated.
    """
    cfg = cfg or K.load_routing()
    st = next(s for s in cfg["stages"] if s["id"] == stage_id)
    system = (STAGES_DIR / st["card"]).read_text(encoding="utf-8")
    model = cfg["tiers"][tier]["models"][stage_id]
    log_path = run_dir / "run.json"
    log = json.loads(log_path.read_text()) if log_path.exists() else {"tier": tier, "attempts": []}
    escalations, prompt = 0, user
    for attempt in range(1, 6):
        t0 = time.time()
        res = call(model, system, prompt, cfg, run_dir=run_dir, stage=stage_id, fake=fake)
        cost_usd = usd(cfg, model, res["usage"])
        entry = {"stage": stage_id, "attempt": attempt, "model": model, "provider": res["provider"],
                 "usage": res["usage"], "usd": cost_usd, "seconds": round(time.time() - t0, 1)}
        try:
            obj = extract_json(res["text"])
            problems = check(obj) if check else []
        except (ValueError, json.JSONDecodeError) as e:
            obj, problems = None, [f"reply was not valid JSON: {e}"]
        entry["problems"] = problems[:20]
        log["attempts"].append(entry)
        log_path.write_text(json.dumps(log, indent=1))
        if not problems:
            (run_dir / f"{stage_id}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False))
            return {"ok": True, "model": model, "obj": obj, "attempts": attempt}
        feedback = "\n".join(f"- {p}" for p in problems[:20])
        prompt = f"{user}\n\n# YOUR PREVIOUS ANSWER FAILED THESE CHECKS — fix every one and answer again\n{feedback}"
        if attempt % 2 == 0:  # two tries per rung, then one rung up
            up = next_rung(cfg, model)
            if up is None or escalations >= max_escalations:
                break
            model, escalations = up, escalations + 1
    return {"ok": False, "model": model, "obj": None, "attempts": attempt}
